#!/bin/bash


set -euxo pipefail

# https://runfinch.com/docs/managing-finch/linux/installation/#amazon-linux
if ! command -v finch >/dev/null 2>&1; then
    sudo dnf install -y runfinch-finch
fi

finch --version

