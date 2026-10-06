#!/bin/bash

set -euxo pipefail

# TODO: split tailscale install and tailscale join into separate scripts

hostnamectl set-hostname "$TAILSCALE_HOSTNAME"

if ! command -v tailscale >/dev/null 2>&1; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi

if ! tailscale status >/dev/null 2>&1; then
    tailscale up \
        --client-id="$TAILSCALE_CLIENT_ID?ephemeral=true&preauthorized=true" \
        --audience="$TAILSCALE_AUDIENCE" \
        --advertise-tags="$TAILSCALE_TAG" \
        --hostname="$TAILSCALE_HOSTNAME" \
        --ssh \
        --accept-routes
fi

# Persist env vars for rejoin service after resume
cat > /etc/default/rejoin-tailnet << ENVEOF
TAILSCALE_HOSTNAME=${TAILSCALE_HOSTNAME}
TAILSCALE_CLIENT_ID=${TAILSCALE_CLIENT_ID}
TAILSCALE_AUDIENCE=${TAILSCALE_AUDIENCE}
TAILSCALE_TAG=${TAILSCALE_TAG}
ENVEOF

cat > /etc/systemd/system/rejoin-tailnet.service << 'SVCEOF'
[Unit]
Description=Rejoin Tailscale tailnet after resume
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'source /etc/default/rejoin-tailnet; tailscale up --client-id="$TAILSCALE_CLIENT_ID?ephemeral=true&preauthorized=true" --audience="$TAILSCALE_AUDIENCE" --advertise-tags="$TAILSCALE_TAG" --hostname="$TAILSCALE_HOSTNAME" --ssh --accept-routes || true'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable --now rejoin-tailnet.service || true

