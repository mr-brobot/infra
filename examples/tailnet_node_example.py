"""Example CDK stack demonstrating TailnetNode usage."""

from aws_cdk import App, Stack
from aws_cdk import aws_ec2 as ec2

from brobot.infra import TailnetNode, TailnetNodeProps, dlami_machine_image


class TailnetNodeExampleStack(Stack):
    def __init__(self, scope, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Use the default VPC (no new VPC created)
        vpc = ec2.Vpc.from_lookup(self, "VPC", is_default=True)
        machine_image = dlami_machine_image()

        TailnetNode(
            self,
            "DevNode",
            props=TailnetNodeProps(
                vpc=vpc,
                machine_image=machine_image,
                instance_type=ec2.InstanceType("g6.2xlarge"),
                hostname="my-project-gpu-dev",
                tailscale_client_id="...",
                tailscale_tag="tag:compute",
            ),
        )


app = App()
TailnetNodeExampleStack(app, "TailnetNodeExample")
app.synth()
