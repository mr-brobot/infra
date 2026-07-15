from __future__ import annotations

from aws_cdk import aws_ec2 as ec2

DLAMI_SSM_PARAMETER = (
    "/aws/service/deeplearning/ami/x86_64/"
    "base-oss-nvidia-driver-gpu-ubuntu-22.04/latest/ami-id"
)


def dlami_machine_image() -> ec2.IMachineImage:
    """The latest AWS Deep Learning AMI (Ubuntu 22.04, NVIDIA driver), resolved via SSM."""
    return ec2.MachineImage.from_ssm_parameter(
        DLAMI_SSM_PARAMETER,
        os=ec2.OperatingSystemType.LINUX,
        user_data=ec2.UserData.for_linux(),
    )
