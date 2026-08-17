#!/bin/bash

set -euxo pipefail

VERSION="${MUTAGEN_VERSION:-v0.18.1}"
ARCH="$(uname -m)"

case "$ARCH" in
  x86_64) PLATFORM="amd64" ;;
  aarch64) PLATFORM="arm64" ;;
  *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

TARGET_USER=ec2-user
TARGET_DIR=/home/$TARGET_USER/.mutagen/agents/"$VERSION"

RELEASE_URL="https://github.com/mutagen-io/mutagen/releases/download/${VERSION}/mutagen_linux_${PLATFORM}_${VERSION}.tar.gz"

curl -L -o /tmp/mutagen_release.tar.gz "$RELEASE_URL"

mkdir -p /tmp/mutagen_agents
tar -xzf /tmp/mutagen_release.tar.gz -C /tmp/ mutagen-agents.tar.gz
tar -xzf /tmp/mutagen-agents.tar.gz -C /tmp/mutagen_agents linux_${PLATFORM}
chmod +x /tmp/mutagen_agents/linux_${PLATFORM}

mkdir -p $TARGET_DIR
cp /tmp/mutagen_agents/linux_${PLATFORM} $TARGET_DIR/mutagen-agent
chown $TARGET_USER:$TARGET_USER $TARGET_DIR/mutagen-agent

