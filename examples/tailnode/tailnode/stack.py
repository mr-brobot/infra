import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from brobot.infra import Tailnode, TailnodeProps


class TailnodeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, "VPC", is_default=True)

        machine_image = ec2.MachineImage.latest_amazon_linux2023(
            cpu_type=ec2.AmazonLinuxCpuType.ARM_64,
        )

        hostname_param = cdk.CfnParameter(
            self, "Hostname", default="example", description="Tailnet hostname"
        )
        client_id_param = cdk.CfnParameter(
            self, "ClientId", description="Tailscale client ID"
        )
        tag_param = cdk.CfnParameter(
            self, "Tag", default="tag:compute", description="Tailscale tag"
        )

        Tailnode(
            self,
            "Node",
            props=TailnodeProps(
                vpc=vpc,
                machine_image=machine_image,
                instance_type=ec2.InstanceType("t4g.micro"),
                hostname=hostname_param.value_as_string,
                tailscale_client_id=client_id_param.value_as_string,
                tailscale_tag=tag_param.value_as_string,
            ),
        )
