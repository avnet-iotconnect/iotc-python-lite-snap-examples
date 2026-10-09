#!/usr/bin/env bash
# Installs booth-site.service (the /IOTCONNECT-fed booth web page on port 8090).
#   ./install_booth.sh            # installs the unit and a settings template, then edit the credentials:
#   sudo nano /etc/default/booth-site ; sudo systemctl enable --now booth-site ; journalctl -u booth-site -f
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
sudo install -m 644 "$HERE/systemd/booth-site.service" /etc/systemd/system/booth-site.service
sudo sed -i "s#^WorkingDirectory=.*#WorkingDirectory=$HERE#; s#^User=.*#User=${SUDO_USER:-$(id -un)}#" /etc/systemd/system/booth-site.service
if [ ! -f /etc/default/booth-site ]; then
  sudo install -m 600 -o root -g root "$HERE/systemd/booth-site.env" /etc/default/booth-site
  echo "[booth] wrote /etc/default/booth-site with placeholder credentials: edit it before starting"
fi
sudo systemctl daemon-reload
echo "[booth] installed. Then:  sudo systemctl enable --now booth-site   and open http://$(hostname -I | awk '{print $1}'):8090/"
