#!/usr/bin/env bash
# Puts the booth site on the internet through a Cloudflare quick tunnel (HTTPS, no account needed).
#   ./install_tunnel.sh         # installs cloudflared (arm64 deb) and booth-tunnel.service, prints the public URL
#   ./install_tunnel.sh url     # prints the current public URL (it changes at every tunnel restart)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
url() { sudo journalctl -u booth-tunnel --no-pager 2>/dev/null | grep -o -E 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1; }
if [ "${1:-}" = "url" ]; then url; exit 0; fi
if ! command -v cloudflared >/dev/null; then
  ARCH=$(dpkg --print-architecture)
  curl -sSL -o /tmp/cloudflared.deb "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}.deb"
  sudo dpkg -i /tmp/cloudflared.deb && rm -f /tmp/cloudflared.deb
fi
sudo install -m 644 "$HERE/systemd/booth-tunnel.service" /etc/systemd/system/booth-tunnel.service
sudo systemctl daemon-reload
sudo systemctl enable --now booth-tunnel
for i in $(seq 1 20); do sleep 2; U=$(url); [ -n "$U" ] && break; done
echo "[tunnel] public URL: ${U:-not yet in the log, try: $0 url}"
