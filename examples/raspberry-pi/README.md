
# Raspberry Pi – Getting Started with /IOTCONNECT Python Lite SDK

This guide follows the style and flow of the Avnet demos’ Raspberry Pi quickstart and adds notes for the **socket bridge** workflow used by the Vision Smart‑Zone demo.

> **References**
> - Demos repo (structure & examples): https://github.com/avnet-iotconnect/iotc-python-lite-sdk-demos
> - Python Lite SDK (PIP-based): https://github.com/avnet-iotconnect/iotc-python-lite-sdk
> - Ultralytics YOLO guides: https://docs.ultralytics.com/guides/  (Raspberry Pi deployment)  
> - Avnet /IOTCONNECT training library: https://www.avnet.com/americas/solutions/iot/iotconnect/training/

---

## 1. Prerequisites

- Raspberry Pi 5 (recommended) with 64‑bit Raspberry Pi OS or Ubuntu 24.x
- Camera (Pi Camera via libcamera or USB UVC webcam)
- Internet access
- An /IOTCONNECT account with a **Company (CPID)** and a **Device (UID)**

> Tip: Use a heatsink/fan on Pi 5 for the best sustained inference performance.

---

## 2. /IOTCONNECT Onboarding (portal)

1. Create or locate your **Company** (CPID) and **Device** (UID) in the /IOTCONNECT portal.
2. For the **Lite SDK Socket** workflow, we’ll use the *`iotconnect`* Snap which maintains two Unix sockets:
   - Telemetry: `.../iotc.sock`
   - Commands: `.../iotc_cmd.sock`
3. Make a note of your device identity as configured in the portal; your device will authenticate when the Snap connects the bridge to the cloud.

> SDK repository (for reference): https://github.com/avnet-iotconnect/iotc-python-lite-sdk

---

## 3. Install base packages

```bash
sudo apt update
sudo apt install -y python3-venv git curl v4l-utils ffmpeg libgtk-3-0t64 libgl1
```

If you are on Raspberry Pi OS and using **libcamera**, OpenCV’s `VideoCapture(0)` works fine for most USB/UVC cameras. For CSI camera via libcamera, GStreamer pipelines may be needed.

---

## 4. Install and run the /IOTCONNECT socket bridge

```bash
sudo snap install iotconnect --channel=stable
# For verbose console output during development:
snap run iotconnect.socket-debug
```
This creates user‑writable sockets (watch for the exact paths printed):
```
/home/<user>/snap/iotconnect/common/iotc.sock
/home/<user>/snap/iotconnect/common/iotc_cmd.sock
```

Verify:
```bash
ss -xl | grep iotc
ls -l ~/snap/iotconnect/common/iotc*.sock
```

---

## 5. Create a workspace and Python env

```bash
mkdir -p ~/vision && cd ~/vision
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

---

## 6. Choose a starter demo

The baseline Raspberry Pi starter demo in this repo is **Vision Smart‑Zone**, which runs YOLO and periodically posts counts over the local socket. See:  
**[`starter-demo/vision-smart-zone/`](starter-demo/vision-smart-zone/)**

To install its Python dependencies:
```bash
pip install -r starter-demo/vision-smart-zone/requirements.txt
```

> If you prefer the **PIP SDK** approach used in other Avnet demos, follow the SDK repo’s README to connect directly via the Python SDK instead of the sockets. The structure here mirrors the Avnet demos to make both approaches consistent.

---

## 7. Optional: enable user services

This repository includes systemd **user** units for convenience. After you’ve validated the demo interactively:

```bash
mkdir -p ~/.config/systemd/user
cp starter-demo/vision-smart-zone/systemd/*.service ~/.config/systemd/user/
systemctl --user daemon-reload

# Start the socket bridge first:
systemctl --user enable --now iotc-socket.service

# Then the vision demo:
systemctl --user enable --now vision-fruit.service

# Check logs:
journalctl --user -u vision-fruit.service -f
```

---

## 8. Troubleshooting

- **No camera feed**: try a smaller resolution, or switch to a USB UVC webcam first.  
- **Broken pipe on telemetry**: ensure only one `iotconnect.socket[-debug]` instance is running; long‑lived sockets can drop on inactivity—our client auto‑reconnects.  
- **Commands not applied**: use the included command sniffer in the demo README to confirm the exact JSON from the CMD socket.  
- **Performance**: prefer `yolov8n.pt` or YOLO11 nano models; cap FPS via `--fps-limit`.

---

## Media (links reused from Avnet resources)

- /IOTCONNECT overview: https://www.avnet.com/americas/solutions/iot/iotconnect/  
- /IOTCONNECT training library: https://www.avnet.com/americas/solutions/iot/iotconnect/training/  
- Ultralytics guides: https://docs.ultralytics.com/guides/
