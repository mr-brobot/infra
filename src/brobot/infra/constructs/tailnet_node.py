import importlib.resources
from dataclasses import dataclass

from aws_cdk import Duration
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk.aws_s3_assets import Asset
from constructs import Construct


@dataclass(frozen=True)
class TailnetNodeProps:
    vpc: ec2.IVpc
    machine_image: ec2.IMachineImage
    instance_type: ec2.InstanceType
    hostname: str
    tailscale_client_id: str
    tailscale_tag: str
    root_volume: ec2.BlockDeviceVolume | None = None
    idle_cpu_threshold_percent: float = 5.0
    idle_evaluation_minutes: int = 30


class TailnetNode(Construct):
    """An EC2 instance that joins a tailnet via Workload Identity Federation.

    The instance role is granted `sts:GetWebIdentityToken` scoped to the configured Tailscale audience.

    Inbound access is via Tailscale SSH only; the security group has no ingress rules.

    A CloudWatch alarm stops the instance when CPU is idle for the configured duration.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        props: TailnetNodeProps,
    ) -> None:
        super().__init__(scope, construct_id)

        audience = f"api.tailscale.com/{props.tailscale_client_id}"

        role = iam.Role(
            self,
            "Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description=f"EC2 role for {props.hostname} (Tailscale WIF)",
            # TODO: what tags might be useful here?
        )

        role.add_to_policy(
            iam.PolicyStatement(
                sid="TailscaleWorkloadIdentityFederation",
                actions=["sts:GetWebIdentityToken"],
                resources=["*"],
                conditions={
                    "ForAnyValue:StringEquals": {
                        "sts:IdentityTokenAudience": audience,
                    },
                    "NumericLessThanEquals": {
                        "sts:DurationSeconds": "300",
                    },
                },
            )
        )

        security_group = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=props.vpc,
            description=(f"{props.hostname}: no ingress; Tailscale SSH handles access"),
            allow_all_outbound=True,
        )

        script_path = (
            importlib.resources.files("brobot.infra") / "scripts" / "tailnet_join.sh"
        )
        init_script = Asset(
            self,
            "InitScript",
            path=str(script_path),
        )

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            f"export TAILSCALE_HOSTNAME={props.hostname!r}",
            f"export TAILSCALE_CLIENT_ID={props.tailscale_client_id!r}",
            f"export TAILSCALE_AUDIENCE={audience!r}",
            f"export TAILSCALE_TAG={props.tailscale_tag!r}",
        )
        user_data.add_s3_download_command(
            bucket=init_script.bucket,
            bucket_key=init_script.s3_object_key,
            local_file="/tmp/userdata.sh",
        )
        user_data.add_commands("bash /tmp/userdata.sh")

        root_volume = props.root_volume or ec2.BlockDeviceVolume.ebs(
            128,
            volume_type=ec2.EbsDeviceVolumeType.GP3,
            encrypted=True,
            delete_on_termination=True,
        )

        instance = ec2.Instance(
            self,
            "Instance",
            vpc=props.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            instance_type=props.instance_type,
            machine_image=props.machine_image,
            role=role,
            security_group=security_group,
            require_imdsv2=True,
            detailed_monitoring=True,
            user_data=user_data,
            user_data_causes_replacement=True,
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/sda1",
                    volume=root_volume,
                )
            ],
        )

        init_script.grant_read(instance.role)

        period = Duration.minutes(5)
        evaluation_periods = max(
            1, props.idle_evaluation_minutes // int(period.to_minutes())
        )
        idle_alarm = cw.Alarm(
            self,
            "IdleCpuAlarm",
            alarm_description=(
                f"Stop {props.hostname} when CPU <= "
                f"{props.idle_cpu_threshold_percent}% for "
                f"{props.idle_evaluation_minutes} minutes"
            ),
            metric=cw.Metric(
                namespace="AWS/EC2",
                metric_name="CPUUtilization",
                dimensions_map={"InstanceId": instance.instance_id},
                period=period,
                statistic="Average",
            ),
            threshold=props.idle_cpu_threshold_percent,
            evaluation_periods=evaluation_periods,
            datapoints_to_alarm=evaluation_periods,
            comparison_operator=cw.ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        idle_alarm.add_alarm_action(
            cw_actions.Ec2Action(cw_actions.Ec2InstanceAction.STOP)
        )

        self.role = role
        self.security_group = security_group
        self.instance = instance
        self.idle_alarm = idle_alarm
