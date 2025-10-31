
# Vision Smart‑Zone (YOLO) → /IOTCONNECT (Socket Bridge)

This starter demo runs Ultralytics YOLO on a Raspberry Pi and sends **fruit counts** every *N* seconds to the local `/IOTCONNECT` socket.
It also listens on the **command** socket and supports live control (pause/resume, send interval, line, etc.).

> Uses the same folder style as the Avnet demos: `raspberry-pi/starter-demo/<demo-name>`.

## Features
- Works on Pi OS or Ubuntu (64‑bit) with Pi 5 recommended
- Draws boxes, names and confidences (unless `--no-draw`)
- Sends structured counts: `apples/oranges/bananas_(left|right|total)` plus `other_left/right`
- Command support via `iotc_cmd.sock`: `pause`, `resume`, `send_interval <N>`, `line x1,y1,x2,y2`, `area_side left|right`, `classes csv`, `get_status`, `ping`

## Install dependencies
```bash
source ~/vision/venv/bin/activate
pip install -r starter-demo/vision-smart-zone/requirements.txt
```

## Run the demo
Terminal A (sockets):
```bash
snap run iotconnect.socket-debug
```
Terminal B (demo):
```bash
export IOTC_SOCK=/home/$USER/snap/iotconnect/common/iotc.sock
export IOTC_CMD_SOCK=/home/$USER/snap/iotconnect/common/iotc_cmd.sock

python starter-demo/vision-smart-zone/scripts/smart_zone_fruit_counts_cmd.py   --model yolov8n.pt --source 0   --conf 0.25 --classes ""   --line 80,380,560,380 --area-side left   --iotc-sock "$IOTC_SOCK"   --iotc-cmd-sock "$IOTC_CMD_SOCK"   --iotc-stream vision.fruit   --fps-limit 18 --send-interval 4   --log-jsonl starter-demo/vision-smart-zone/logs/fruit.jsonl
```

## Telemetry schema
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

## Commands
The demo accepts plain‑text (one command per line) **or** JSON envelopes like:
```json
{"name":"send_interval","args":["12"],"ack_id":"uuid-1234"}
```
Supported commands:
- `ping <id>` → responds `{ "type":"pong" }`
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

## Systemd user units (optional)
```bash
mkdir -p ~/.config/systemd/user
cp starter-demo/vision-smart-zone/systemd/*.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now iotc-socket.service
systemctl --user enable --now vision-fruit.service
```

## Media (links reused from Avnet repos/resources)
- Demos repo (structure reference): https://github.com/avnet-iotconnect/iotc-python-lite-sdk-demos
- /IOTCONNECT Training Library (videos): https://www.avnet.com/americas/solutions/iot/iotconnect/training/
- Ultralytics YOLO (docs and images): https://docs.ultralytics.com/guides/

> Replace or add board‑specific images as desired.
