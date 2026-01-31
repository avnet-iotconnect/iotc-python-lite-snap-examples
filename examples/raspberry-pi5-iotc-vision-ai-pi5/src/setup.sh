
#!/usr/bin/env bash
set -euo pipefail

# Derive repo root no matter where this script is run from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../../" && pwd)"

echo "[*] Repo root: ${REPO_ROOT}"
echo "[*] Installing base packages..."
sudo apt update
sudo apt install -y python3-venv git curl v4l-utils ffmpeg libgtk-3-0t64 libgl1

echo "[*] Creating ~/vision venv and installing Python deps..."
mkdir -p ~/vision
cd ~/vision
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r "${SCRIPT_DIR}/requirements.txt"

echo "[*] Copying systemd user units (optional)..."
mkdir -p ~/.config/systemd/user
cp "${SCRIPT_DIR}/systemd/"*.service ~/.config/systemd/user/
systemctl --user daemon-reload

echo "Done."
echo "Start the socket bridge:   systemctl --user enable --now iotc-socket.service"
echo "Start the demo:            systemctl --user enable --now vision-fruit.service"
