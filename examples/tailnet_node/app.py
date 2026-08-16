import os

import aws_cdk as cdk
from tailnet_node.stack import TailnetNodeStack

app = cdk.App()
TailnetNodeStack(
    app,
    "ExampleTailnetNodeStack",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT") or "898546127587",
        region=os.environ.get("CDK_DEFAULT_REGION") or "us-west-2",
    ),
)

app.synth()
