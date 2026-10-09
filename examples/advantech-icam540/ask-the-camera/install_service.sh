#!/usr/bin/env bash
# Installs vlm-narrator.service so the narrator starts at boot, after Ollama and the /IOTCONNECT snap
# socket, stops the stock web UI (it holds the sensor) and serves the live view on port 8088.
#
#   ./install_service.sh            # install + enable + start
#   sudo systemctl stop vlm-narrator   # take the sensor back to run vlm_narrator.py by hand
#   journalctl -u vlm-narrator -f      # logs
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
sudo install -m 644 "$HERE/systemd/vlm-narrator.service" /etc/systemd/system/vlm-narrator.service
sudo sed -i "s#^WorkingDirectory=.*#WorkingDirectory=$HERE#" /etc/systemd/system/vlm-narrator.service
sudo sed -i "s#^User=.*#User=${SUDO_USER:-$(id -un)}#" /etc/systemd/system/vlm-narrator.service
[ -f /etc/default/vlm-narrator ] || sudo install -m 644 "$HERE/systemd/vlm-narrator.env" /etc/default/vlm-narrator
# The snap's socket service must run too, or the narrator falls back to printing telemetry. Enable it
# as a service unless someone is already running "snap run iotconnect.socket-debug" in a terminal.
if pgrep -f iotc_socket_service.py >/dev/null; then
  echo "[install] snap socket already running (socket-debug?); not enabling the service. For boot: sudo snap start --enable iotconnect.socket"
else
  sudo snap start --enable iotconnect.socket
fi
# At boot the snap's socket service can start before DNS is up, fail its discovery call five times in a
# row and be given up on by systemd ("start request repeated too quickly"): wait for the network, retry forever.
sudo mkdir -p /etc/systemd/system/snap.iotconnect.socket.service.d
printf '[Unit]\nAfter=network-online.target\nWants=network-online.target\nStartLimitIntervalSec=0\n[Service]\nRestart=always\nRestartSec=10\n' | sudo tee /etc/systemd/system/snap.iotconnect.socket.service.d/boot.conf >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now vlm-narrator
sleep 3
systemctl --no-pager status vlm-narrator | head -5
echo "live view: http://$(hostname -I | awk '{print $1}'):$(grep -E '^VLM_WEB=' /etc/default/vlm-narrator | cut -d= -f2)/"
