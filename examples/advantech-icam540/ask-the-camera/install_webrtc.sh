#!/usr/bin/env bash
# Installs the WebRTC path (device created with the WebRTC stream resource): pure Python, no C++ build.
#   ./install_webrtc.sh                 # python packages + kvs-webrtc.service
#   ./kvs_stream.py --check             # "webrtc channel True" = this device can use it
#   sudo systemctl enable --now kvs-webrtc ; journalctl -u kvs-webrtc -f
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
pip3 install --user -q iotconnect-lib boto3 websockets aiortc av
python3 -c "import aiortc, av, boto3, websockets, cv2" && echo "[webrtc] python packages OK"
sudo install -m 644 "$HERE/systemd/kvs-webrtc.service" /etc/systemd/system/kvs-webrtc.service
sudo sed -i "s#^WorkingDirectory=.*#WorkingDirectory=$HERE#; s#^User=.*#User=${SUDO_USER:-$(id -un)}#" /etc/systemd/system/kvs-webrtc.service
[ -f /etc/default/kvs-webrtc ] || sudo install -m 644 "$HERE/systemd/kvs-webrtc.env" /etc/default/kvs-webrtc
sudo systemctl daemon-reload
echo "[webrtc] installed:  sudo systemctl enable --now kvs-webrtc"
