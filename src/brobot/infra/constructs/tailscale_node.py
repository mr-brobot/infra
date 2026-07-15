from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent

from aws_cdk import Duration
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from constructs import Construct


@dataclass(frozen=True)
class TailscaleNodeProps:
    vpc: ec2.IVpc
    machine_image: ec2.IMachineImage
    instance_type: ec2.InstanceType
    hostname: str
    tailscale_client_id: str
    tailscale_tag: str
    root_volume_size_gb: int = 200
    idle_cpu_threshold_percent: float = 5.0
    idle_evaluation_minutes: int = 30


class TailscaleNode(Construct):
    """An EC2 instance that joins a tailnet via Workload Identity Federation.

    No static auth keys are stored. The instance role is granted
    sts:GetWebIdentityToken scoped to the configured Tailscale audience.
    The Tailscale client exchanges that token for an auth key on first boot.

    Inbound access is via Tailscale SSH only; the security group has no
    ingress rules. Session Manager is enabled as an emergency fallback.

    A CloudWatch alarm stops the instance when CPU is idle for the
    configured duration (default: <=5% for 30 minutes).
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        props: TailscaleNodeProps,
    ) -> None:
        super().__init__(scope, construct_id)

        audience = f"api.tailscale.com/{props.tailscale_client_id}"

        role = iam.Role(
            self,
            "Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description=f"EC2 role for {props.hostname} (Tailscale WIF + SSM)",
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

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            *self._user_data_commands(
                hostname=props.hostname,
                client_id=props.tailscale_client_id,
                audience=audience,
                tag=props.tailscale_tag,
            )
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
            ssm_session_permissions=True,
            detailed_monitoring=True,
            user_data=user_data,
            user_data_causes_replacement=True,
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/sda1",
                    volume=ec2.BlockDeviceVolume.ebs(
                        props.root_volume_size_gb,
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                        encrypted=True,
                        delete_on_termination=True,
                    ),
                )
            ],
        )

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

    @staticmethod
    def _user_data_commands(
        *,
        hostname: str,
        client_id: str,
        audience: str,
        tag: str,
    ) -> list[str]:
        script = dedent(
            f"""
            set -euxo pipefail

            hostnamectl set-hostname {hostname}

            if ! command -v tailscale >/dev/null 2>&1; then
                curl -fsSL https://tailscale.com/install.sh | sh
            fi

            systemctl enable --now tailscaled

            if ! tailscale status >/dev/null 2>&1; then
                tailscale up \\
                    --client-id='{client_id}?ephemeral=false&preauthorized=true' \\
                    --audience='{audience}' \\
                    --advertise-tags='{tag}' \\
                    --hostname='{hostname}' \\
                    --ssh \\
                    --accept-routes
            fi

            install -d -o ubuntu -g ubuntu /home/ubuntu/project
            """
        ).strip()
        return script.splitlines()
