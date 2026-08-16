#!/bin/bash

set -euxo pipefail

hostnamectl set-hostname "$TAILSCALE_HOSTNAME"

if ! command -v tailscale >/dev/null 2>&1; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi

systemctl enable --now tailscaled

if ! tailscale status >/dev/null 2>&1; then
    tailscale up \
        --client-id="$TAILSCALE_CLIENT_ID?ephemeral=false&preauthorized=true" \
        --audience="$TAILSCALE_AUDIENCE" \
        --advertise-tags="$TAILSCALE_TAG" \
        --hostname="$TAILSCALE_HOSTNAME" \
        --ssh \
        --accept-routes
fi

