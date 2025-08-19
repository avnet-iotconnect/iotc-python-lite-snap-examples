#!/usr/bin/env bash
set -euo pipefail

echo "[1/3] Installing snapd (if missing)..."
if ! command -v snap >/dev/null 2>&1; then
  sudo apt update && sudo apt install -y snapd
fi

echo "[2/3] Installing IoTConnect snap..."
sudo snap install iotconnect || true

echo "[3/3] Running iotconnect.setup..."
iotconnect.setup || true

echo "Done. You can now run: iotconnect.socket-run"