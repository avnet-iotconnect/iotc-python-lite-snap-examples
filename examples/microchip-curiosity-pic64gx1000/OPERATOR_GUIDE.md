# Operator Guide: Vision Demo

Runbook for presenting [`applications/vision_iotc_socket.py`](./applications/vision_iotc_socket.py) live: starting the demo, tuning it while it runs, streaming the overlay to a browser, and demonstrating an OTA model swap.

For first-time bring-up see [QUICKSTART.md](./QUICKSTART.md); for the command and telemetry interface see [DEVELOPER_GUIDE.md, section 5.3](./DEVELOPER_GUIDE.md#53-vision_iotc_socketpy---camera-inference-telemetry).

All commands below run from the `applications/` directory of this example.

## 1. Prerequisites

- Python 3
- OpenCV (`cv2`) installed: `sudo apt-get install -y python3-opencv`
- The /IOTCONNECT socket bridge running as root, so both sockets exist:
  - `/var/snap/iotconnect/common/iotc.sock`
  - `/var/snap/iotconnect/common/iotc_cmd.sock`
- Optional tools:
  - `socat` for sending runtime commands

Install helpers (if missing):

```bash
sudo apt update
sudo apt install -y socat
```

On the PIC64GX1000 always use `--backend cv_only`. The board has no AI accelerator, and PyTorch and ONNX Runtime wheels are not generally available for `riscv64`.

## 2. Start The Demo

Headless + browser overlay stream (recommended):

```bash
python3 vision_iotc_socket.py \
  --backend cv_only \
  --model hog \
  --source /path/to/video.mp4 \
  --auto-start \
  --send-interval 1 \
  --conf 0.5 \
  --fps-limit 2 \
  --web --web-host 0.0.0.0 --web-port 8080
```

Open from host browser on same network:

```text
http://<board-ip>:8080/
```

Notes:

- Use `--show` only when a local display session exists.
- In headless mode, skip `--show` and use `--web`.

## 3. Runtime Control Commands

Send commands over the command socket:

```bash
printf 'status\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
```

Common commands:

- `start`
- `stop` or `pause`
- `resume`
- `status`
- `set_conf <0.0..1.0>`
- `set_fps <value>` (`0` means unlimited)
- `set_interval <seconds>` (alias: `send_interval <seconds>`)
- `set_source <camera|file|rtsp-url>`
- `set_model <model_path> [model_cfg] [labels]`

Examples:

```bash
printf 'set_conf 0.35\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
printf 'set_fps 4\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
printf 'set_interval 0.5\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
printf 'set_source 0\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
```

## 4. Confidence, FPS, and Telemetry Cadence

- `--conf` / `set_conf`: detection confidence threshold.
  - Higher = fewer detections, lower false positives.
  - Lower = more detections, higher false positives.
- `--fps-limit` / `set_fps`: processing rate cap.
  - Lower values reduce CPU usage.
- `--send-interval` / `set_interval`: telemetry publish frequency.
  - Lower values send more often.

Recommended demo baseline for CPU-constrained boards:

- `--conf 0.35`
- `--fps-limit 2`
- `--send-interval 1`

## 5. Model Options (OpenCV-Only)

Supported with `--backend cv_only`:

- Built-in keywords (no file required):
  - `hog` (person detector)
  - `face`, `haar`, `haarcascade`, `haarcascade_face`, `face_haar`
- Model files:
  - `.xml` (cascade)
  - `.onnx`, `.pb`, `.prototxt`, `.caffemodel` (DNN path)

Startup examples:

```bash
python3 vision_iotc_socket.py --backend cv_only --model hog --source /path/to/video.mp4 --auto-start
python3 vision_iotc_socket.py --backend cv_only --model face --source /path/to/video.mp4 --auto-start
python3 vision_iotc_socket.py --backend cv_only --model /path/to/haarcascade_frontalface_default.xml --source /path/to/video.mp4 --auto-start
```

Runtime model switch example:

```bash
printf 'set_model /var/snap/iotconnect/common/models/face_v2.xml\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
```

## 6. OTA Strategy (What To Ship)

Include in OTA payload:

- App script updates (`vision_iotc_socket.py`)
- Model artifacts in versioned filenames:
  - Example: `face_v1.xml`, `face_v2.xml`
- Optional labels/config files:
  - `labels.txt`, `model_cfg.json`
- Service/launcher updates if startup args changed

Recommended model storage location:

```text
/var/snap/iotconnect/common/models/
```

Why versioned names:

- Makes roll-forward/rollback deterministic.
- Easy operator verification of active model path.

## 7. OTA Demo Procedure

1. Start demo with baseline model (`face_v1.xml` or `hog`).
2. Apply OTA package that drops a new model (for example `face_v2.xml`) into `/var/snap/iotconnect/common/models/`.
3. Switch model at runtime:

```bash
printf 'set_model /var/snap/iotconnect/common/models/face_v2.xml\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
```

4. Validate with status:

```bash
printf 'status\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
```

5. Confirm overlays/telemetry behavior in browser and /IOTCONNECT telemetry feed.

## 8. Safe Shutdown and Restart

Stop with `Ctrl+C` once and wait a few seconds for clean thread join.

If restart fails, clear stale instances/port holders:

```bash
pgrep -af vision_iotc_socket.py
ss -ltnp | grep ':8080'
pkill -f vision_iotc_socket.py
```

Check auto-restart services (if process keeps coming back):

```bash
systemctl list-units --type=service | grep -Ei 'iotc|vision'
snap services | grep -Ei 'iot'
```

## 9. Troubleshooting

- No browser video:
  - Verify `--web` enabled.
  - Verify port open: `ss -ltnp | grep ':8080'`.
  - Verify URL uses board IP, not localhost from another machine.
- No detections:
  - Lower confidence (`set_conf 0.2`).
  - Use a source with clear persons/faces.
  - Try `face` model for frontal face clips.
- TX warnings (`[TX] failed`):
  - Confirm the /IOTCONNECT TX socket exists.
- Crash on stop:
  - Ensure you are running latest script containing non-daemon worker threads and `join(timeout=5.0)` on shutdown.

## 10. Operator Quick Commands

```bash
# Start
python3 vision_iotc_socket.py --backend cv_only --model hog --source /path/to/video.mp4 --auto-start --web --web-host 0.0.0.0 --web-port 8080

# Status
printf 'status\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock

# Tune threshold/FPS/interval
printf 'set_conf 0.35\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
printf 'set_fps 3\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
printf 'set_interval 1\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock

# Swap model
printf 'set_model /var/snap/iotconnect/common/models/face_v2.xml\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
```
