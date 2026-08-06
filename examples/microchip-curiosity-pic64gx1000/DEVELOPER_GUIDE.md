# Developer Guide: Curiosity PIC64GX1000 and the /IOTCONNECT Snap

Reference documentation for the PIC64GX1000 examples: how the pieces fit together, the exact socket contract, what each application publishes and accepts, and how to take the demo from a terminal session to a serviced, field-updatable deployment.

For a linear bring-up path, start with [QUICKSTART.md](./QUICKSTART.md). This guide assumes the board is already booted and provisioned.

## Contents

1. [Architecture](#1-architecture)
2. [The iotconnect Snap](#2-the-iotconnect-snap)
3. [Socket contract](#3-socket-contract)
4. [Device template and dashboard](#4-device-template-and-dashboard)
5. [Application reference](#5-application-reference)
6. [PHT Click (MS8607) hardware notes](#6-pht-click-ms8607-hardware-notes)
7. [Enabling I2C for mikroBUS](#7-enabling-i2c-for-mikrobus)
8. [Running as a service](#8-running-as-a-service)
9. [OTA updates](#9-ota-updates)
10. [Writing your own producer](#10-writing-your-own-producer)
11. [Troubleshooting](#11-troubleshooting)
12. [Reference](#12-reference)

---

## 1. Architecture

The Snap owns everything cloud-facing: identity, TLS, MQTT, reconnection, command dispatch and OTA. Applications own everything device-facing: sensors, cameras, control loops. The two halves meet at a pair of UNIX domain sockets.

```
Application process                 iotconnect Snap (strict confinement)      /IOTCONNECT
──────────────────                  ────────────────────────────────────      ───────────
read sensor / frame
       │
       ▼
 JSON line ──────── connect, write, close ──▶ iotc.sock ──▶ send_telemetry ──▶ MQTT (TLS 8883)
                                                                                    │
 handle command ◀── read newline-delimited ── iotc_cmd.sock ◀── on_command ◀─────────┘
                                                              (Snap acks to cloud)
```

Consequences of this split that matter when you design an application:

- The application never holds device credentials. Certificates live in the Snap's writable data area and survive Snap refreshes.
- The application can be written in any language that can open a UNIX socket, and can crash and restart without affecting the cloud connection.
- Attribute names are defined by the JSON keys the application emits. They must match the device template exactly.
- Telemetry is fire and forget. Delivery failures are visible in the Snap's log, not in the application's return value.

---

## 2. The iotconnect Snap

```bash
sudo snap install iotconnect
snap info iotconnect
```

The Snap is published for `riscv64`, `arm64`, `armhf` and `amd64`, so the same commands used here apply to the rest of the boards in this repository.

| Entry point | Mode | Purpose |
| --- | --- | --- |
| `iotconnect.setup` | Interactive | Onboarding wizard: manual credential entry or automated registration with a REST API key |
| `iotconnect.socket` | Service, disabled at install | Socket bridge. Start with `sudo snap start iotconnect.socket` |
| `iotconnect.socket-debug` | Foreground | Same bridge with logs on the terminal |
| `iotconnect.quickstart` | Service, disabled at install | Bundled sample application that publishes its own telemetry, no sockets involved |
| `iotconnect.quickstart-debug` | Foreground | Foreground variant of the above |
| `iotconnect.cli` | Command line | REST operations: configure, create template, register device |

Service control and logs:

```bash
snap services iotconnect
sudo snap start iotconnect.socket
sudo snap restart iotconnect.socket
sudo snap logs iotconnect.socket -f
```

To prove the cloud connection before any of your own code is involved, run `sudo snap run iotconnect.quickstart-debug`. It publishes `random` and `sdk_version` every ten seconds, both of which are present in the included device template. Stop it before starting the socket bridge.

Only one bridge instance may run at a time. Two instances connect twice with the same identity and the broker will disconnect them in turn; symptoms are repeated `[DISCONNECT]` lines. Check with `pgrep -af iotc_socket_service.py`.

### Where data lives

| Content | Path |
| --- | --- |
| Device configuration | `/var/snap/iotconnect/common/iotcDeviceConfig.json` |
| Device certificate and key | `/var/snap/iotconnect/common/device-cert.pem`, `device-pkey.pem` |
| Telemetry socket | `/var/snap/iotconnect/common/iotc.sock` |
| Command socket | `/var/snap/iotconnect/common/iotc_cmd.sock` |
| OTA extraction directory | `/var/snap/iotconnect/common/update/` |

This directory is `$SNAP_COMMON`. It persists across `snap refresh`, which is why OTA payloads and models belong here rather than inside the Snap, which is read-only.

---

## 3. Socket contract

### Path resolution

The bridge chooses its base directory from the effective user ID at startup:

| How the bridge is started | Base directory |
| --- | --- |
| `sudo snap start iotconnect.socket` (service, runs as root) | `$SNAP_COMMON` - `/var/snap/iotconnect/common` |
| `sudo snap run iotconnect.socket-debug` | `$SNAP_COMMON` - `/var/snap/iotconnect/common` |
| `snap run iotconnect.socket-debug` as a normal user | `$SNAP_USER_COMMON` - `~/snap/iotconnect/common` |

`pht_iotc_socket.py` and `perf_iotc_socket.py` hard-code the system paths, so run the bridge as root or edit the `SOCKET_TX` and `SOCKET_RX` constants. `vision_iotc_socket.py` accepts `--iotc-sock` and `--iotc-cmd-sock`, defaulting to the `IOTC_SOCK` and `IOTC_CMD_SOCK` environment variables.

Provisioning follows the same rule. Run `sudo snap run iotconnect.setup` so the configuration is written where the root service will read it.

Both sockets are created with mode `0666`, so unprivileged applications can use them.

### Telemetry, device to cloud

`iotc.sock` is a stream socket that handles **one message per connection**:

1. Connect.
2. Write one JSON object, at most 8192 bytes, terminated by a newline or by shutting down the write side.
3. The bridge reads a single line, publishes it, and closes the connection.

```python
import json, socket, time

def publish(payload, path="/var/snap/iotconnect/common/iotc.sock"):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(2.0)
        s.connect(path)
        s.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        s.shutdown(socket.SHUT_WR)

publish({"timestamp": int(time.time()), "PHT_temp": 22.4})
```

Rules that follow from the implementation:

- Do not hold the connection open and stream multiple objects; only the first line is read.
- Keep payloads flat. Keys become attribute names; nested objects are not expanded into attributes.
- Space messages out. `perf_iotc_socket.py` enforces a 150 ms minimum gap, which is a reasonable floor for any producer.
- Anything over 8192 bytes is truncated. For image or large-array data, use OTA or an object store and publish a reference.

### Commands, cloud to device

`iotc_cmd.sock` is a fan-out socket. Connect and read; every connected listener receives every command as one newline-terminated JSON object:

```json
{"name": "freq", "args": ["5"], "ack_id": "8a2f...-..."}
```

`args` is whatever the portal sent, normally a list of strings. The Snap acknowledges the command to /IOTCONNECT as soon as it forwards it, so the portal shows success even if your application ignores the command. Application-level results are your own telemetry, not the protocol acknowledgement:

```python
publish({"ack": ack_id, "status": "success", "ts": int(time.time())})   # perf application
publish({"type": "ack", "cmd": "set_conf", "ok": True, "ack_id": ack_id})  # vision application
```

Never write to `iotc_cmd.sock`. The bridge uses reads on that connection only to detect that a listener has gone away.

Reconnect on error. Both `perf_iotc_socket.py` and `vision_iotc_socket.py` run the reader in a background thread with a retry loop, which is the pattern to copy.

### Quick manual tests

```bash
# One-shot telemetry, no application involved
printf '{"random": 42}\n' | socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc.sock

# Watch commands arrive as you fire them from the portal
socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock
```

Install `socat` with `sudo apt-get install -y socat`.

---

## 4. Device template and dashboard

### Import order

The dashboard binds to attributes that must already exist, so import [`files/pic64gx1000-device-template.json`](./files/pic64gx1000-device-template.json) before [`files/pic64gx1000-dashboard-template.json`](./files/pic64gx1000-dashboard-template.json).

Template import lives under **Device** > **Templates** > **Create Template** > **Import**. The template uses code `PIC64GX`; change it if that code is already taken in your environment. The message code is assigned by the platform on import.

### Attribute reference

| Attribute | Type | Unit | Published by |
| --- | --- | --- | --- |
| `timestamp` | INTEGER | s | all |
| `source` | STRING | | `perf_iotc_socket.py` |
| `freq` | DECIMAL | s | `perf_iotc_socket.py` |
| `random`, `sdk_version` | INTEGER, STRING | | `iotconnect.quickstart`, the Snap's bundled smoke-test application |
| `PHT_temp` | DECIMAL | C | `pht_iotc_socket.py` |
| `PHT_pressure` | DECIMAL | hPa | `pht_iotc_socket.py` |
| `PHT_humidity` | DECIMAL | % | `pht_iotc_socket.py` |
| `PHT_die_temp` | DECIMAL | C | `pht_iotc_socket.py` |
| `osr` | INTEGER | | reserved for tuned PHT builds that expose the MS8607 oversampling ratio |
| `CPU_usage` | DECIMAL | % | `perf_iotc_socket.py` |
| `CPU_load1`, `CPU_load5`, `CPU_load15` | DECIMAL | | `perf_iotc_socket.py` |
| `CPU_cores` | INTEGER | | `perf_iotc_socket.py` |
| `CPU_freq_mhz`, `CPU_freq_min_mhz`, `CPU_freq_max_mhz` | DECIMAL | MHz | `perf_iotc_socket.py`, when the platform exposes cpufreq |
| `CPU_temp_c` | DECIMAL | C | `perf_iotc_socket.py`, when a thermal zone is exposed |
| `type`, `stream`, `status`, `model` | STRING | | `vision_iotc_socket.py` |
| `frame_index`, `detections` | INTEGER | | `vision_iotc_socket.py` |
| `infer_ms` | DECIMAL | ms | `vision_iotc_socket.py` |
| `object1`-`object3` | STRING | | `vision_iotc_socket.py` |
| `confidence1`-`confidence3` | DECIMAL | | `vision_iotc_socket.py` |

Attributes that an application never sends simply stay empty; one template covering all three applications avoids re-provisioning the device when you switch demos.

### Commands in the template

| Portal name | Command string | Parameter | Handled by |
| --- | --- | --- | --- |
| Set Publish Interval | `freq` | seconds | `perf_iotc_socket.py` |
| Start Inference | `start` | | `vision_iotc_socket.py` |
| Stop Inference | `stop` | | `vision_iotc_socket.py` |
| Resume Inference | `resume` | | `vision_iotc_socket.py` |
| Report Status | `status` | | `vision_iotc_socket.py` |
| Set Confidence | `set_conf` | 0.0-1.0 | `vision_iotc_socket.py` |
| Set FPS Limit | `set_fps` | frames per second, 0 for unlimited | `vision_iotc_socket.py` |
| Set Send Interval | `set_interval` | seconds | `vision_iotc_socket.py` |
| Set Source | `set_source` | camera index, path or URL | `vision_iotc_socket.py` |
| Set Model | `set_model` | model path or keyword | `vision_iotc_socket.py` |
| Reload Model | `reload` | | `vision_iotc_socket.py` |

### Dashboard anatomy

The export is a `ddType: 2` document with an `items` array; each entry pairs a `widgetProperties` block with a grid `properties` block using a 55-column layout.

| Widget | `widgetGuid` | Notes |
| --- | --- | --- |
| Image | `A8CB394D-...` | Two instances: product shot and Click board shot, both by URL |
| Gauge | `21A18C90-...` | Four instances. `minValue`, `maxValue` and the `zones` array define the coloured bands |
| Telemetry | `A0326788-...` | Attribute table, `dateToUse` is set to `Gateway Date` |
| OTAUpdates | `4EE53CD1-...` | Per-device OTA history |
| DeviceCommand | `E413CDFD-...` | Bound to a device template GUID, renders that template's command list |

Each widget carries `deviceGuid` and `deviceUniqueId` from the environment where it was exported (`mclPIC64GX1000`). After import, open each widget and re-select your device so the bindings resolve. Gauge ranges worth knowing:

| Gauge | Range | Bands |
| --- | --- | --- |
| Temperature | 0-45 C | cold to 15, comfortable to 25, warm to 35, hot to 45 |
| Pressure | 990-1040 hPa | low to 995, medium to 1010, comfortable to 1025, very high to 1040 |
| Humidity | 0-100 % | low to 20, medium to 40, comfortable to 60, humid to 80, very humid to 100 |
| Die temperature | 20-45 C | low to 30, medium to 40, hot to 45 |

---

## 5. Application reference

### 5.1 `pht_iotc_socket.py` - PHT Click telemetry

The reference sensor demo and the source of the data the shipped dashboard displays.

```bash
pip3 install --break-system-packages smbus2
python3 pht_iotc_socket.py
```

No arguments. The publish interval is a 10 second `time.sleep` and the I2C bus number is the `BUS` constant, default `0`. Edit both in place if you need different values.

Payload:

```json
{
  "timestamp": 1761000000,
  "PHT_temp": 22.41,
  "PHT_pressure": 995.22,
  "PHT_humidity": 41.63,
  "PHT_die_temp": 22.95
}
```

`PHT_temp` is the second-order compensated temperature from the pressure die; `PHT_die_temp` is the temperature reported by the humidity die. On a stable bench they track within a degree or so, and the difference is a useful demonstration of sensor fusion.

The application does not listen for commands.

### 5.2 `perf_iotc_socket.py` - CPU performance telemetry

Runs on any Linux target with no extra hardware, which makes it the right tool for proving connectivity and for load demonstrations.

```bash
python3 perf_iotc_socket.py --freq 5        # publish every 5 seconds
python3 perf_iotc_socket.py --once          # publish a single message and exit
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `--freq` | `5.0` | Publish period in seconds, must be greater than 0.2 |
| `--once` | off | Send one message and exit, useful in cron or smoke tests |

Payload:

```json
{
  "timestamp": 1761000000,
  "CPU_usage": 7.2,
  "CPU_load1": 0.11, "CPU_load5": 0.09, "CPU_load15": 0.08,
  "CPU_cores": 4,
  "CPU_freq_mhz": 600.0,
  "CPU_temp_c": 41.5,
  "freq": 5.0,
  "source": "cpu_perf"
}
```

`psutil` is used when installed; otherwise the application falls back to `/proc/stat`, `/proc/loadavg`, `/sys/devices/system/cpu/*/cpufreq/` and `/sys/class/thermal/`. The frequency and temperature keys are omitted entirely when the platform exposes neither, so do not build alerts that assume they are always present.

Command handling accepts three shapes, so it works whether commands come from the portal or from a local test harness:

```json
{"name": "freq", "args": ["2"], "ack_id": "..."}
{"freq": 2}
{"cmd": "freq, 2"}
```

An application-level acknowledgement is published on the telemetry socket when `ack_id` is present.

### 5.3 `vision_iotc_socket.py` - camera inference telemetry

Publishes the top three detections per interval and accepts runtime control. Operating procedure, model choices and streaming are covered in [OPERATOR_GUIDE.md](./OPERATOR_GUIDE.md); this section covers the interface.

On this board, use `--backend cv_only`. The PIC64GX1000 has no AI accelerator, and the OpenCV HOG and Haar paths run acceptably at a low frame rate. PyTorch and ONNX Runtime wheels for `riscv64` are not generally available.

```bash
sudo apt-get install -y python3-opencv
python3 vision_iotc_socket.py \
  --backend cv_only --model hog \
  --source /path/to/clip.mp4 \
  --auto-start --conf 0.35 --fps-limit 2 --send-interval 1 \
  --web --web-host 0.0.0.0 --web-port 8080
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `--backend` | `auto` | `auto`, `torch`, `onnx` or `cv_only` |
| `--model` | `yolov8n.pt` | Model path, or a keyword such as `hog` or `face` in `cv_only` mode |
| `--model-cfg`, `--labels` | none | Companion config and label files |
| `--source` | `0` | Camera index, video file, RTSP or HTTP URL, or a still image |
| `--conf` | `0.25` | Confidence threshold |
| `--send-interval` | `3.0` | Seconds between telemetry messages |
| `--fps-limit` | `0.0` | Processing cap, 0 for unlimited |
| `--stream` | `vision.objects` | Value published in the `stream` attribute |
| `--iotc-sock`, `--iotc-cmd-sock` | system paths | Socket overrides, also read from `IOTC_SOCK` and `IOTC_CMD_SOCK` |
| `--show` | off | Local preview window, requires a display session |
| `--web`, `--web-host`, `--web-port`, `--web-quality` | off, `0.0.0.0`, `8080`, `80` | MJPEG overlay stream at `http://<board-ip>:8080/` |
| `--auto-start` | off | Begin inference without waiting for a `start` command |

Payload:

```json
{
  "timestamp": 1761000000,
  "ts_utc": "2026-02-28T17:07:40.000Z",
  "type": "vision_inference",
  "stream": "vision.objects",
  "model": "haarcascade_frontalface_default.xml",
  "frame_index": 1284,
  "infer_ms": 96.4,
  "detections": 2,
  "object1": "person", "confidence1": 0.82,
  "object2": "person", "confidence2": 0.61,
  "object3": "", "confidence3": 0.0,
  "status": "running"
}
```

Commands are accepted as JSON (`{"name": "set_conf", "args": ["0.4"]}`), as a `cmd` string (`{"cmd": "set_conf 0.4"}`), or as bare text (`set_conf 0.4`). Full list: `start`, `stop`, `pause`, `resume`, `set_model`, `reload`, `set_source`, `set_conf`, `set_interval`, `send_interval`, `set_fps`, `show`, `hide`, `status`, `get_status`, `ping`.

---

## 6. PHT Click (MS8607) hardware notes

The [PHT Click](https://www.mikroe.com/pht-click) carries a TE Connectivity MS8607, which presents as two independent I2C devices:

| Address | Function |
| --- | --- |
| `0x40` | Relative humidity and humidity-die temperature |
| `0x76` | Pressure and temperature, with a 6-word calibration PROM |

The application reads humidity with hold-master commands `0xE5` and `0xE3`, resets the pressure die with `0x1E`, reads calibration words `0xA2`-`0xAC`, then converts D1 and D2 at OSR 4096 (`0x48` and `0x58`) with a 12 ms conversion wait. Second-order temperature compensation below 20 C is implemented per the datasheet.

Practical notes:

- Seat the Click with the notch matching the mikroBUS silkscreen and power the board down while doing so.
- `sudo i2cdetect -y 0` must show both `0x40` and `0x76`. One address only usually means a partially seated board.
- The board reports temperature roughly one to two degrees above ambient once it has been powered for a while. That is self-heating, not a calibration fault.
- If you move the Click to the second mikroBUS socket, change `BUS` in the script to match the bus number that appears in `/dev`.

---

## 7. Enabling I2C for mikroBUS

Some device trees for this board leave the mikroBUS I2C controllers disabled, in which case no `/dev/i2c-*` nodes exist. This overlay marks both controllers as available. It is a one-time step, and it is the only part of this documentation set that runs a compiler, so the quickstart avoids it.

```bash
sudo apt-get install -y i2c-tools device-tree-compiler

cat <<'DTS' | sudo tee /boot/enable-i2c-ab.dts >/dev/null
/dts-v1/;
/plugin/;
/ {
    compatible = "microchip,pic64gx1000", "riscv";
    fragment@0 { target-path = "/soc/i2c@2010a000"; __overlay__ { status = "okay"; clock-frequency = <100000>; }; };
    fragment@1 { target-path = "/soc/i2c@2010b000"; __overlay__ { status = "okay"; clock-frequency = <100000>; }; };
};
DTS

sudo dtc -@ -I dts -O dtb -o /boot/enable-i2c-ab.dtbo /boot/enable-i2c-ab.dts
sudo dtc -I fs -O dtb -o /boot/board-base.dtb /proc/device-tree
sudo fdtoverlay -i /boot/board-base.dtb -o /boot/board-i2c.dtb /boot/enable-i2c-ab.dtbo
echo 'devicetree /boot/board-i2c.dtb' | sudo tee /boot/grub/custom.cfg
sudo update-grub
sudo reboot
```

What each step does:

1. `dtc -@` compiles the overlay with symbol information.
2. `dtc -I fs` snapshots the device tree the board is running from `/proc/device-tree`.
3. `fdtoverlay` merges the overlay into that snapshot.
4. `custom.cfg` tells GRUB to hand the merged blob to the kernel at boot.

Verify after reboot:

```bash
ls -l /dev/i2c-*
sudo i2cdetect -y 0
dmesg | grep -i i2c
```

Regenerate `board-i2c.dtb` after any kernel or firmware update that ships a new base device tree, since the merged blob is a snapshot rather than a live overlay.

---

## 8. Running as a service

Systemd keeps a demo alive across reboots and process failures. Adjust `User`, `WorkingDirectory` and `ExecStart` to match your checkout.

```bash
sudo tee /etc/systemd/system/iotc-pht.service >/dev/null <<'UNIT'
[Unit]
Description=/IOTCONNECT PHT (MS8607) telemetry
After=network-online.target snap.iotconnect.socket.service
Wants=network-online.target
Requires=snap.iotconnect.socket.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/iotc-python-lite-snap-examples/examples/microchip-curiosity-pic64gx1000/applications
ExecStart=/usr/bin/python3 pht_iotc_socket.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now iotc-pht.service
systemctl status iotc-pht.service
journalctl -u iotc-pht.service -f
```

For the CPU application, copy the unit as `iotc-cpuperf.service` and set `ExecStart=/usr/bin/python3 perf_iotc_socket.py --freq 5`.

Points that save time later:

- Enable the bridge itself so it comes back after a reboot: `sudo snap start --enable iotconnect.socket`.
- Confirm the exact bridge unit name with `systemctl list-units 'snap.iotconnect*'` before referencing it in `After=` or `Requires=`; it varies with the Snap revision.
- `Restart=always` with `RestartSec=5` handles the case where the application starts before the sockets exist.
- If you use a virtual environment, point `ExecStart` at the interpreter inside it rather than sourcing `activate`.

---

## 9. OTA updates

OTA is how you change what runs on the board without touching the Snap, which is read-only.

Flow implemented by the bridge:

1. /IOTCONNECT sends an OTA message; the bridge acknowledges with `OTA_DOWNLOADING`.
2. Each file in the message is downloaded.
3. Any `.tar.gz` is extracted into `/var/snap/iotconnect/common/update/`.
4. If the archive contains `install.sh` at its root, the bridge runs it with `bash`, then deletes it.
5. The bridge acknowledges `OTA_DOWNLOAD_DONE` and restarts itself.

Package layout:

```
package.tar.gz
├── install.sh
├── pht_iotc_socket.py
└── models/
    └── face_v2.xml
```

```bash
#!/usr/bin/env bash
# install.sh - runs as root, from the extraction directory
set -euo pipefail

APP_DIR=/home/ubuntu/iotc-python-lite-snap-examples/examples/microchip-curiosity-pic64gx1000/applications
MODEL_DIR=/var/snap/iotconnect/common/models

install -d "$MODEL_DIR"
install -m 0644 models/*.xml "$MODEL_DIR"/
install -m 0755 pht_iotc_socket.py "$APP_DIR"/

systemctl restart iotc-pht.service
```

Build and upload:

```bash
tar czf package.tar.gz install.sh pht_iotc_socket.py models/
```

Upload under **Device** > **Firmware**, create a version, then push it to the device or template. The OTA Updates widget on the dashboard shows each attempt with its version and status, which is the panel visible in the screenshot in [README.md](./README.md#dashboard).

Guidance:

- Version model and script filenames (`face_v1.xml`, `face_v2.xml`) so rollback is a matter of pointing at the previous name.
- Keep `install.sh` idempotent. It may be re-run if a device retries.
- Store models under `/var/snap/iotconnect/common/models/` so they survive Snap refreshes.
- The bridge restarts after an OTA, so any application relying on the command socket must reconnect. The example applications already do.

---

## 10. Writing your own producer

The contract is small enough to implement in a few lines in most languages. This shell producer is a complete working example:

```bash
#!/usr/bin/env bash
set -euo pipefail
SOCK=/var/snap/iotconnect/common/iotc.sock

while true; do
  temp=$(awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp)
  printf '{"timestamp":%d,"CPU_temp_c":%s}\n' "$(date +%s)" "$temp" \
    | socat - UNIX-CONNECT:"$SOCK"
  sleep 10
done
```

A checklist for anything you write:

1. One JSON object per connection, newline terminated, 8192 bytes or fewer.
2. Flat keys that match device template attribute names exactly, including case.
3. At least 150 ms between messages.
4. Treat a missing socket as a normal condition at startup and retry, rather than exiting.
5. Read commands in a separate thread or process with a reconnect loop, and never write to the command socket.
6. Include `timestamp` so late-arriving data is still interpretable.

The generic examples in [`examples/generic/`](../generic/) show the same contract with less board-specific detail.

---

## 11. Troubleshooting

| Symptom | Diagnosis | Action |
| --- | --- | --- |
| `FileNotFoundError` on `iotc.sock` | Bridge not running, or running unprivileged so the socket is under `~/snap/` | `snap services iotconnect`, then `sudo snap start iotconnect.socket` |
| `ConnectionRefusedError` on a socket that exists | Stale socket file from an unclean shutdown | `sudo snap restart iotconnect.socket`, which removes and recreates both sockets |
| Bridge logs repeated `[DISCONNECT]` | Two bridge instances share one identity | `pgrep -af iotc_socket_service.py`, stop the extra one |
| Telemetry logged as sent, nothing in Live Data | Attribute names not on the device template | Compare published keys with the template; re-import `pic64gx1000-device-template.json` |
| Live Data populated, dashboard empty | Widgets still bound to the exported device | Edit each widget and select your device |
| Commands never reach the application | Reader not connected, or the portal command string does not match | `socat - UNIX-CONNECT:/var/snap/iotconnect/common/iotc_cmd.sock` and fire the command again |
| Portal shows a command succeeded but nothing happened | The Snap acknowledges on forward, not on execution | Check the application's own acknowledgement telemetry and log |
| No `/dev/i2c-*` | mikroBUS I2C controllers disabled in the device tree | [Section 7](#7-enabling-i2c-for-mikrobus) |
| `i2cdetect` shows neither `0x40` nor `0x76` | Click not seated, or no 3.3 V on mikroBUS | Reseat with the board powered down, confirm rail voltage |
| PHT values frozen at one reading | I2C read error swallowed by the retry path | Restart the application, check `dmesg` for bus errors |
| Vision application exits on import | OpenCV missing, or a wheel unavailable for riscv64 | `sudo apt-get install -y python3-opencv` and use `--backend cv_only` |
| Payload silently truncated | Message exceeds 8192 bytes | Publish a summary and move bulk data to OTA or an object store |

---

## 12. Reference

**Board**

- [Curiosity PIC64GX1000 Kit product page](https://www.microchip.com/en-us/development-tool/curiosity-pic64gx1000-kit)
- [Kit user guide (PDF)](https://ww1.microchip.com/downloads/aemDocuments/documents/MPU64/ProductDocuments/SupportingCollateral/PIC64GX_Curiosity_Kit_User_Guide.pdf)
- [Kit quickstart guide (PDF)](https://ww1.microchip.com/downloads/aemDocuments/documents/MPU64/ProductDocuments/UserGuides/production-kit-qsguide/Curiosity-PIC64GX1000-Kit_QSGuide.pdf)
- [Ubuntu for RISC-V](https://ubuntu.com/download/risc-v)
- [mikroE PHT Click (MS8607)](https://www.mikroe.com/pht-click)

**/IOTCONNECT**

- [`iotconnect` Snap](https://snapcraft.io/iotconnect)
- [Snap user and developer guide](../../IOTCONNECT_SNAP_User_Developer_Guide.md)
- [Board and supplier catalog](../../BOARD_CATALOG.md)
- [Python Lite SDK](https://github.com/avnet-iotconnect/iotc-python-lite-sdk)
- [Python Lite SDK demos, including the PIC64GX1000 SDK-only path](https://github.com/avnet-iotconnect/iotc-python-lite-sdk-demos)
- [Microchip partner guides](https://avnet-iotconnect.github.io/partners/microchip/)
- [Knowledge base](https://help.iotconnect.io/)
