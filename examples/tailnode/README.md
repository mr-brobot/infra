# Example Tailnet Stack

Creates a single `Tailnode` instance in the default VPC.

## Prerequisites

- AWS CLI configured
- Environment bootstrapped (`cdk bootstrap`).

## Configuration

1. **Credentials**: This CDK stack uses the [standard credential provider chain](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html#credentialProviderChain).
2. **Parameters**: Supply Tailscale parameters (hostname, client ID, tag) at deploy time (`cdk deploy --parameters ...`).

## Deployment

```bash
cdk deploy --parameters Hostname=example --parameters ClientId=... --parameters Tag=tag:compute
```

