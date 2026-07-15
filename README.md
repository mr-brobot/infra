# Infrastructure

## Constructs

### `TailscaleNode`

An EC2 instance that joins a tailnet via [Tailscale Workload Identity Federation](https://tailscale.com/docs/features/workload-identity-federation).
The instance role is granted `sts:GetWebIdentityToken` scoped to a Tailscale audience;
the Tailscale client exchanges that token for an auth key on first boot.

- Security group has **zero ingress** — Tailscale SSH is the only inbound path
- IMDSv2 required, detailed (1-minute) CloudWatch metrics
- Session Manager enabled as an emergency fallback (TODO: disable this if it is purely a fallback)
- Idle auto-stop: CloudWatch alarm on `CPUUtilization` below a configurable threshold for a configurable duration → native EC2 `stop` action

```python
from brobot.infra import TailscaleNode, TailscaleNodeProps

TailscaleNode(
    self,
    "GpuDev",
    props=TailscaleNodeProps(
        vpc=vpc,
        machine_image=machine_image,
        instance_type=ec2.InstanceType("g6.2xlarge"),
        hostname="my-project-gpu-dev",
        tailscale_client_id="...",
        tailscale_tag="tag:compute",
    ),
)
```

### `dlami_machine_image`

Resolves the latest AWS Deep Learning AMI (Ubuntu 22.04, NVIDIA driver) via its SSM parameter
— a convenient default `machine_image` for GPU/ML training and inference nodes.

```python
from brobot.infra import dlami_machine_image

machine_image = dlami_machine_image()
```

## Prerequisites

### AWS Outbound Identity Federation

[Outbound identity federation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_outbound.html) enables an AWS account to perform outbound identity federation. This allows AWS workloads to authenticate with external services, such as Tailscale, using the AWS IAM role as the credential.

If Outbound Identity Federation is enabled, the following AWS CLI command should return successfully:

```sh
aws iam get-outbound-web-identity-federation-info | jq
```

To enable Outbound Identity Federation, run the following:

```sh
aws iam enable-outbound-web-identity-federation | jq
```

### Tailscale Tags

Create [Tailscale tags](https://tailscale.com/docs/features/tags) to associate with compute nodes. This document uses the tag `tag:compute`.

### Tailscale Workload Identity Federation

[Tailscale Workload Identity Federation](https://tailscale.com/docs/features/workload-identity-federation) requires an admin to establish trust between Tailscale an AWS identity. This requires the AWS Issuer URL and Subject format.

The AWS account issuer URL can be retrieved with the following AWS CLI command:

```sh
aws iam get-outbound-web-identity-federation-info | jq -r .IssuerIdentifier
```

The [subject is the AWS role ARN](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_outbound_token_claims.html), so the subject format for the EC2 instance is of the following form:

```
arn:aws:iam:<aws-region>:<aws-account-id>:role/*-compute-role*
```

Only the `auth_keys` (write) scope is required, associated with `tag:compute`.

> The workload identity credential must have the `auth_keys` scope and the tags passed to `--advertise-tags` must match the tags you selected when you configured the federated identity.

- [Tailscale WIF docs](https://tailscale.com/docs/features/workload-identity-federation#register-new-nodes-using-workload-identity)

Once the federated identity is created, a client ID will be generated. Pass
it as `tailscale_client_id` in `TailscaleNodeProps`.

### Update Tailscale ACL policy

Open the policy editor (Admin Console → Access Controls). Add:

```hujson
{
  "tagOwners": {
    "tag:compute": ["autogroup:admin"],
  },
  "ssh": [
    {
      "action": "accept",
      "src":    ["autogroup:member"],
      "dst":    ["tag:compute"],
      "users":  ["ubuntu", "root"],
    },
  ],
}
```

(Merge into existing `acls`, `tagOwners`, `ssh` blocks rather than replacing.)

## Development

```bash
uv sync
make ci
```
