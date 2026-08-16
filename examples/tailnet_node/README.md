# Example Tailnet Stack

Creates a single `TailnetNode` instance in the default VPC.

## Configuration

1. **AWS CLI profile / `env` vars** (simplest if auth'd): omit `env=` entirely; CDK uses `AWS_PROFILE` / `AWS_DEFAULT_REGION` / `sts` identity automatically (`aws sts get-caller-identity`). Deploy with `cdk deploy --profile default`.
2. **`cdk.json` context** (recommended for multi-account stacks): set `"context": { "account": "...", "region": "..." }` in `cdk.json`.
3. **`env` from environment variables** (`os.environ.get` in `app.py`).
4. **`CfnParameter`**: pass at deploy time (`cdk deploy --parameters ...`).
5. **Hardcoded** (current): `env=cdk.Environment(account=..., region=...)` in `app.py`.

Note: `Vpc.from_lookup` caches results in `cdk.context.json` (per-account/per-region). Change account/region requires deleting/regenerating that file.

## Deployment

Prerequisites: AWS toolchain configured, environment bootstrapped (`cdk bootstrap`).

```bash
cdk deploy --parameters Hostname=example --parameters ClientId=... --parameters Tag=tag:compute
```

