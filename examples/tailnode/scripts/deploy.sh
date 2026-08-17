#!/bin/bash

set -euo pipefail

# TODO: externalize config
cdk deploy \
  --parameters Hostname=example \
  --parameters ClientId=TP1uGAFAxp11CNTRL-kQ3oNuDCvu11CNTRL \
  --parameters Tag=tag:compute

