# Vision Smart-Zone (YOLO) -> /IOTCONNECT (Socket Bridge)

This demo runs YOLOv8 object detection on a Raspberry Pi 5 (Ubuntu 24 Desktop), shows an optional live preview, and publishes detection telemetry to IoTConnect via the IoTConnect Python Lite socket (`iotc.sock`) and listens for commands via `iotc_cmd.sock`.

It runs Ultralytics YOLO on a Raspberry Pi and sends **fruit counts** every *N* seconds to the local `/IOTCONNECT` socket. It also listens on the **command** socket and supports live control (pause/resume, send interval, line, etc.).
This package intentionally provides **two scripts**:

## A) Full Smart Zone Demo
**`src/scripts/smart_zone_fruit_counts_cmd.py`**
- Business logic (zones, pricing, profit)
- Uses the Smart Zone Fruit Counter template
  - `files/RPi_Smart_Zone_Fruit_Counter_template_WITH_top3.json`

## B) Minimal YOLO Telemetry Demo
**`src/scripts/iotc_yolo_simple.py`**
- Pure object detection
- No domain assumptions
- Sends only:
  - `v`, `type`, `stream`, `ts`
  - `object1..3`, `confidence1..3`

This script is ideal for:
- First-time bring-up
- Performance benchmarking
- Generic object detection demos
- Reuse across verticals

---

## Features
- Works on Pi OS or Ubuntu (64-bit) with Pi 5 recommended
- Draws boxes, names and confidences (unless `--no-draw`)
- Sends structured counts: `apples/oranges/bananas_(left|right|total)` plus `other_left/right`
- Command support via `iotc_cmd.sock`: `pause`, `resume`, `send_interval <N>`, `line x1,y1,x2,y2`, `area_side left|right`, `classes csv`, `get_status`, `ping`

## Hardware / OS Assumptions
- Raspberry Pi 5
- Ubuntu 24 Desktop (GNOME / Wayland is common)
- USB camera (UVC) or CSI camera
- Internet access for package installs and model download

## Dashboard Preview

![IoTConnect dashboard preview](media/dasboard-img.png)

## 0) Optional: Clean up Ubuntu installation
If this Pi is dedicated to demos, removing default desktop apps can reduce storage and update noise.

```bash
sudo apt remove --purge -y thunderbird libreoffice* \
  rhythmbox shotwell simple-scan gnome-calendar gnome-weather \
  gnome-maps gnome-contacts gnome-clocks cheese totem \
  transmission-gtk remmina aisleriot gnome-mahjongg gnome-mines \
  gnome-sudoku gnome-calculator

sudo apt autoremove --purge -y
sudo apt clean
sudo snap remove thunderbird
```

## 1) Create and activate a Virtual Environment

Ubuntu 24 blocks installing random packages into the system Python via pip (PEP 668).
Use a virtual environment for Ultralytics and OpenCV.

```bash
sudo apt update
sudo apt install -y python3-full python3-venv
python3 -m venv ~/vision/venv
source ~/vision/venv/bin/activate
pip install --upgrade pip
```

## 2) Install Ultralytics (YOLOv8) + OpenCV

Recommended (pip OpenCV inside the venv)
```bash
pip install ultralytics opencv-python
```

## 3) Quick test: YOLO webcam detection

```bash
yolo detect predict source=0 model=yolov8n.pt show=True
```

If you don't want a preview window (headless), use:
```bash
yolo detect predict source=0 model=yolov8n.pt show=False
```

## 4) OpenCV Qt fonts directory fix

```bash
sudo apt update
sudo apt install -y fontconfig fonts-dejavu-core

mkdir -p ~/vision/venv/lib/python3.12/site-packages/cv2/qt/fonts
cp -v /usr/share/fonts/truetype/dejavu/DejaVuSans*.ttf \
  ~/vision/venv/lib/python3.12/site-packages/cv2/qt/fonts/
```

## 5) Install and setup IoTConnect Snap

```bash
sudo snap install iotconnect
snap run iotconnect.setup
```

Follow the prompts to onboard the device.

## 6) Start the IoTConnect sockets

Open a terminal and run:

```bash
snap run iotconnect.socket-debug
```

You should see it connect to MQTT and then log paths similar to:

  /home/$USER/snap/iotconnect/common/iotc.sock
  /home/$USER/snap/iotconnect/common/iotc_cmd.sock

## 7) Run the demo (from this repo)

Open a second terminal and discover your socket locations.
```bash
source ~/vision/venv/bin/activate

export IOTC_SOCK=/home/$USER/snap/iotconnect/common/iotc.sock
export IOTC_CMD_SOCK=/home/$USER/snap/iotconnect/common/iotc_cmd.sock
```

From the repo root:
```bash
cd ~/iotc-python-lite-snap-examples/examples/raspberry-pi5-iotc-vision-ai-pi5
pip install -r src/requirements.txt
```

### Smart Zone Fruit Counter
```bash
python src/scripts/smart_zone_fruit_counts_cmd.py \
  --model yolov8n.pt --source 0 \
  --conf 0.25 --classes "" \
  --line 80,380,560,380 --area-side left \
  --iotc-sock "$IOTC_SOCK" \
  --iotc-cmd-sock "$IOTC_CMD_SOCK" \
  --iotc-stream vision.fruit \
  --fps-limit 18 --send-interval 4
```

## IoTConnect Template
To visualize `object1..3` and `confidence1..3`, import:

- `files/RPi_Smart_Zone_Fruit_Counter_template_WITH_top3.json`

---

### Minimal YOLO Demo - Run
```bash
source ~/vision/venv/bin/activate
export QT_QPA_PLATFORM=wayland

cd ~/iotc-python-lite-snap-examples/examples/raspberry-pi5-iotc-vision-ai-pi5
python3 src/scripts/iotc_yolo_simple.py \
  --model yolov8n.pt \
  --source 0 \
  --iotc-sock /home/$USER/snap/iotconnect/common/iotc.sock \
  --iotc-stream vision.objects \
  --send-interval 3 \
  --fps-limit 18 \
  --show
```

---

### Telemetry schema
```json
{
  "v": "1.0",
  "type": "fruit_counts",
  "stream": "vision.fruit",
  "ts": "2025-01-01T00:00:00.000Z",
  "apples_left": 0, "oranges_left": 0, "bananas_left": 0,
  "apples_right": 0, "oranges_right": 0, "bananas_right": 0,
  "apples_total": 0, "oranges_total": 0, "bananas_total": 0,
  "other_left": 0, "other_right": 0
}
```

### Commands
The demo accepts plain-text (one command per line) **or** JSON envelopes like:
```json
{"name":"send_interval","args":["12"],"ack_id":"uuid-1234"}
```
Supported commands:
- `ping <id>` -> responds `{ "type":"pong" }`
- `pause` / `resume`
- `get_status`
- `send_interval <seconds>`
- `line x1,y1,x2,y2`
- `area_side left|right`
- `classes apple,orange,banana` (filter labels)
- `set <field> <value>` (generic setter)


### Local test
```bash
python - <<'PY'
import os,socket,time,json
p=os.environ.get("IOTC_CMD_SOCK", f"/home/{os.environ['USER']}/snap/iotconnect/common/iotc_cmd.sock")
s=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect(p)
s.sendall((json.dumps({"name":"ping","args":["local"],"ack_id":"test"})+"\n").encode()); time.sleep(0.3)
for line in ["pause","resume","send_interval 2","line 100,300,600,300","area_side right"]:
    s.sendall((line+"\n").encode()); time.sleep(0.3)
s.close()
PY
```

## 8) Run the demo (wget-only, no repo clone)

If you do not want to clone the repo, download just the required files.

```bash
mkdir -p ~/iotc-vision-ai-pi5/src/scripts ~/iotc-vision-ai-pi5/files ~/iotc-vision-ai-pi5/src/systemd
cd ~/iotc-vision-ai-pi5

wget -O src/requirements.txt \
  https://raw.githubusercontent.com/avnet-iotconnect/iotc-python-lite-snap-examples/main/examples/raspberry-pi5-iotc-vision-ai-pi5/src/requirements.txt

wget -O src/scripts/smart_zone_fruit_counts_cmd.py \
  https://raw.githubusercontent.com/avnet-iotconnect/iotc-python-lite-snap-examples/main/examples/raspberry-pi5-iotc-vision-ai-pi5/src/scripts/smart_zone_fruit_counts_cmd.py

wget -O src/scripts/iotc_yolo_simple.py \
  https://raw.githubusercontent.com/avnet-iotconnect/iotc-python-lite-snap-examples/main/examples/raspberry-pi5-iotc-vision-ai-pi5/src/scripts/iotc_yolo_simple.py

wget -O files/RPi_Smart_Zone_Fruit_Counter_template_WITH_top3.json \
  https://raw.githubusercontent.com/avnet-iotconnect/iotc-python-lite-snap-examples/main/examples/raspberry-pi5-iotc-vision-ai-pi5/files/RPi_Smart_Zone_Fruit_Counter_template_WITH_top3.json
```

Then run:

```bash
cd ~/iotc-vision-ai-pi5
pip install -r src/requirements.txt
```

Now run the commands in Step 7 from `~/iotc-vision-ai-pi5` (skip the repo-clone path).

## 9) Systemd user units (optional)
```bash
mkdir -p ~/.config/systemd/user
cp src/systemd/*.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now iotc-socket.service
systemctl --user enable --now vision-fruit.service
```

If you cloned the repo to a different path, update the `ExecStart` line in `vision-fruit.service` to point at your local checkout.

## 10) Troubleshooting
**Camera not opening**

Confirm device exists:
```bash
ls -l /dev/video*
v4l2-ctl --list-devices 2>/dev/null || true
```

Make sure your user has access:
```bash
groups
sudo usermod -aG video $USER
# log out/in (or reboot)
```

**Socket telemetry not showing up**

Verify the socket paths exist:
```bash
ls -l /home/avnet/snap/iotconnect/common/iotc*.sock
```

Ensure you passed the correct --iotc-sock path (do not rely on unset env vars).

If you use env vars, confirm they are set:
```bash
echo "IOTC_SOCK=$IOTC_SOCK"
echo "IOTC_CMD_SOCK=$IOTC_CMD_SOCK"
```

**Telemetry format (typical)**

Telemetry is sent as newline-delimited JSON objects over the Unix socket.
Example:

{
  "v":"1.0",
  "type":"yolo_detections",
  "stream":"vision.yolo",
  "ts":"2026-01-30T20:48:21Z",
  "source":0,
  "counts":{"person":1,"chair":2},
  "top":[{"cls":"person","conf":0.91,"xyxy":[12,35,240,460]}]
}

## 11) References (links reused from Avnet repos/resources)
- Demos repo (structure reference): https://github.com/avnet-iotconnect/iotc-python-lite-sdk-demos
- /IOTCONNECT Training Library (videos): https://www.avnet.com/americas/solutions/iot/iotconnect/training/
- Ultralytics YOLO (docs and images): https://docs.ultralytics.com/guides/

## 12) Raspberry Pi 5 Setup Links (public)
- Raspberry Pi 5 documentation: https://www.raspberrypi.com/documentation/computers/raspberry-pi-5.html
- Raspberry Pi OS installation (Raspberry Pi Imager): https://www.raspberrypi.com/software/
- Getting started with Raspberry Pi OS: https://www.raspberrypi.com/documentation/computers/getting-started.html
- Camera documentation (libcamera): https://www.raspberrypi.com/documentation/computers/camera_software.html
- Ubuntu for Raspberry Pi: https://ubuntu.com/download/raspberry-pi

> Replace or add board-specific images as desired.
