import importlib.resources
from pathlib import Path

import aws_cdk.aws_iam as iam
from aws_cdk import aws_ec2 as ec2
from aws_cdk.aws_s3_assets import Asset
from constructs import Construct

SCRIPTS_DIR = importlib.resources.files("brobot.infra") / "scripts"


class UserDataBuilder:
    scope: Construct
    user_data: ec2.UserData
    assets: list[Asset]

    def __init__(self, scope: Construct):
        self.scope = scope
        self.user_data = ec2.UserData.for_linux()
        self.assets = []

    def with_tailnet(
        self,
        hostname: str,
        tailscale_client_id: str,
        tailscale_tag: str,
        audience: str,
    ) -> "UserDataBuilder":
        self.user_data.add_commands(
            f"export TAILSCALE_HOSTNAME={hostname!r}",
            f"export TAILSCALE_CLIENT_ID={tailscale_client_id!r}",
            f"export TAILSCALE_AUDIENCE={audience!r}",
            f"export TAILSCALE_TAG={tailscale_tag!r}",
        )

        script_name = "tailnet_join.sh"
        source_path = SCRIPTS_DIR / script_name
        target_path = Path("/") / "tmp" / script_name
        init_script = Asset(
            self.scope,
            "TailnetJoinScript",
            path=str(source_path),
        )
        self.assets.append(init_script)

        self.user_data.add_s3_download_command(
            bucket=init_script.bucket,
            bucket_key=init_script.s3_object_key,
            local_file=str(target_path),
        )
        self.user_data.add_commands(f"bash {target_path!s}")
        return self

    def with_finch(self) -> "UserDataBuilder":
        script_name = "finch_install.sh"
        source_path = SCRIPTS_DIR / script_name
        target_path = Path("/") / "tmp" / script_name
        init_script = Asset(
            self.scope,
            "FinchInitScript",
            path=str(source_path),
        )
        self.assets.append(init_script)

        self.user_data.add_s3_download_command(
            bucket=init_script.bucket,
            bucket_key=init_script.s3_object_key,
            local_file=str(target_path),
        )
        self.user_data.add_commands(f"bash {target_path!s}")
        return self

    def grant_read(self, grantee: iam.IGrantable) -> "UserDataBuilder":
        for asset in self.assets:
            asset.grant_read(grantee)
        return self

    def build(self) -> ec2.UserData:
        return self.user_data
