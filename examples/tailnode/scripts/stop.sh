#!/bin/bash

set -euo pipefail

INSTANCE_NAME=ExampleTailnodeStack/Node/Instance

INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=$INSTANCE_NAME" "Name=instance-state-name,Values=running,stopped" \
  --query 'Reservations[*].Instances[*].InstanceId' --output text)

if [ -z "$INSTANCE_ID" ]; then
  echo "No Tailnode instance found."
  exit 1
fi

INSTANCE_STATE=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[*].Instances[*].State.Name' --output text)

if [ "$INSTANCE_STATE" = "running" ]; then
  aws ec2 stop-instances --instance-ids "$INSTANCE_ID" > /dev/null
	aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID"
fi

