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

`vision_iotc_socket.py` accepts `--iotc-sock` and `--iotc-cmd-sock`, defaulting to the `IOTC_SOCK` and `IOTC_CMD_SOCK` environment variables. `pht_iotc_socket.py` reads `IOTC_SOCK`. `perf_iotc_socket.py` hard-codes the system paths, so run the bridge as root or edit its `SOCKET_TX` and `SOCKET_RX` constants.

Only a root bridge can start at boot, so a deployment that must survive a power cycle uses the system paths.

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

The SDK splits the delivered command string on whitespace: the first token becomes `command_name` and the rest become `command_args`. A template command can therefore carry its own argument, which turns a parameterised action into a one-click button. `set_model hog` with no parameter arrives at the application exactly as `set_model` with the parameter `hog` would.

The template uses both forms. Prefixes group them in the portal's dropdown, which sorts alphabetically.

| Portal name | Command string | Parameter | Handled by |
| --- | --- | --- | --- |
| Vision: Start | `start` | | vision |
| Vision: Stop | `stop` | | vision |
| Vision: Resume | `resume` | | vision |
| Vision: Status | `status` | | vision |
| Model: HOG People | `set_model hog` | | vision |
| Model: Haar Face | `set_model face` | | vision |
| Model: OTA Face v2 | `set_model /var/snap/iotconnect/common/models/face_v2.xml` | | vision |
| Model: Set Path | `set_model` | model path or keyword | vision |
| Source: Camera 0 | `set_source 0` | | vision |
| Source: Demo Clip | `set_source /home/ubuntu/ppl-walking-640x360-5fps.mp4` | | vision |
| Source: Set | `set_source` | camera index, path or URL | vision |
| Confidence: Low 0.25 | `set_conf 0.25` | | vision |
| Confidence: High 0.60 | `set_conf 0.6` | | vision |
| Confidence: Set | `set_conf` | 0.0-1.0 | vision |
| FPS Limit: Set | `set_fps` | frames per second, 0 for unlimited | vision |
| Vision Interval: Set | `set_interval` | seconds | vision |
| Preview: Show | `show` | | vision |
| Preview: Hide | `hide` | | vision |
| CPU: Publish Interval | `freq` | seconds | perf |

Constraints on baked-in arguments:

- Whitespace is the separator, so paths in a command string cannot contain spaces.
- Relative paths resolve against the service `WorkingDirectory`, so use absolute paths.
- Adjust `Model: OTA Face v2` and `Source: Demo Clip` to the paths that exist on your board, or delete them.

Two commands are deliberately absent. `reload` parses and acknowledges but has no effect, so a button for it would report success while doing nothing. `pause` is an alias for `stop`.

Behaviour worth understanding before you demonstrate this:

- Every command reaches every connected listener. Sending `freq` for the CPU application also reaches the vision application, which acknowledges it as unknown. That is harmless, but you will see it in the journal.
- The Snap acknowledges to the cloud when it forwards, not when the application acts, so the portal shows success even for a command nothing handled. The real outcome is in the application's own acknowledgement telemetry and in `journalctl`.
- `show` and `hide` only do something with a display session attached. On a headless board they succeed and change nothing visible; the browser stream is controlled by `--web`, not by these.

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

No command-line arguments. Three environment variables cover the settings the systemd unit needs:

| Variable | Default | Meaning |
| --- | --- | --- |
| `IOTC_SOCK` | `/var/snap/iotconnect/common/iotc.sock` | Telemetry socket path |
| `PHT_I2C_BUS` | `0` | I2C bus for the mikroBUS socket in use |
| `PHT_INTERVAL` | `10` | Seconds between samples |

The application retries rather than exits when the socket is missing or the sensor does not answer, so it can start before the bridge and survive a Click board that is seated late.

Payload:

```json
{
  "timestamp": 1761000000,
  "PHT_temp": 26.92,
  "PHT_pressure": 995.95,
  "PHT_humidity": 41.32,
  "PHT_die_temp": 26.92
}
```

`PHT_temp` is the second-order compensated temperature from the pressure die. `PHT_die_temp` carries the same value; see [section 6](#6-pht-click-ms8607-hardware-notes) for why.

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
| `--loop` | off | Reopen a video file source when it reaches the end. Ignored for camera indexes and stream URLs |

Without `--loop`, a finite clip ends and the log fills with `no frame from source, retrying`. Sending `stop` then `start` also rewinds it, because `stop` releases the capture; `set_source` with the path it already has does not, and `reload` is only an acknowledgement.

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
| `0x40` | Relative humidity |
| `0x76` | Pressure and temperature, with a 6-word calibration PROM |

The application reads humidity with hold-master command `0xE5`, resets the pressure die with `0x1E`, reads calibration words `0xA2`-`0xAC`, then converts D1 and D2 at OSR 4096 (`0x48` and `0x58`) with a 12 ms conversion wait. Second-order temperature compensation below 20 C is implemented per the datasheet.

Two results of the raw conversion are easy to get wrong, and both were verified against hardware:

- **Units.** The compensated outputs are in hundredths: `TEMP` is 0.01 C and `P` is 0.01 mbar. Both need dividing by 100 to reach C and hPa. Publishing `P` unscaled sends about `99590`, which silently pins the dashboard's 990-1040 hPa gauge.
- **There is only one temperature source.** The MS8607 resembles an HTU21 on the humidity side, but its humidity die has no temperature command. `0xE3` returns `00 00` under hold-master and `0xF3` returns the same under no-hold, so any conversion of that reading yields the constant -46.85 C, the floor of the formula. `PHT_die_temp` therefore mirrors `PHT_temp`, which is what the reference dashboard shows. If a second distinct temperature would be more useful than a duplicate, rebind that gauge to `CPU_temp_c` from the performance application.

Practical notes:

- Seat the Click with the notch matching the mikroBUS silkscreen and power the board down while doing so.
- `sudo i2cdetect -y 0` must show both `0x40` and `0x76`. One address only usually means a partially seated board.
- `/dev/i2c-*` is `root:i2c` mode 660. Add your user to the `i2c` group to run the application by hand; the systemd unit uses `SupplementaryGroups=i2c` instead.
- The board reports temperature roughly one to two degrees above ambient once it has been powered for a while. That is self-heating, not a calibration fault.
- If you move the Click to the second mikroBUS socket, set `PHT_I2C_BUS` to the bus number that appears in `/dev`.

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

The [`systemd/`](./systemd/) folder installs the PHT and vision applications as boot-time services that publish through the same bridge at the same time. Running both is the clearest demonstration that the socket is a shared bus rather than a single-application channel.

```bash
cd examples/microchip-curiosity-pic64gx1000/systemd
sudo ./install-services.sh
```

The installer:

1. Confirms the bridge can find device credentials in `/var/snap/iotconnect/common/`, copying them from `~/snap/iotconnect/common/` if the device was provisioned unprivileged. Only a root bridge can start at boot, so the credentials have to be on the root side.
2. Runs `snap start --enable iotconnect.socket` so the bridge itself comes back after a power cycle.
3. Writes `/etc/default/iotc-examples`, detecting the Python interpreter (a `~/iotc-vision-venv` is preferred over the system one) and a video source (first `.mp4` in the home directory, otherwise `/dev/video0` as camera index `0`).
4. Installs both units with `User`, `Group` and `WorkingDirectory` set to the invoking user and this checkout, then enables and starts them.

Re-running is safe. An existing `/etc/default/iotc-examples` is preserved, so local edits survive an upgrade of the checkout.

| File | Role |
| --- | --- |
| [`iotc-pht.service`](./systemd/iotc-pht.service) | MS8607 telemetry, 10 second interval |
| [`iotc-vision.service`](./systemd/iotc-vision.service) | Inference telemetry plus the MJPEG overlay on port 8080 |
| [`iotc-examples.env`](./systemd/iotc-examples.env) | Shared settings, installed to `/etc/default/iotc-examples` |
| [`install-services.sh`](./systemd/install-services.sh) | Installer described above |

Day-to-day operation:

```bash
journalctl -u iotc-pht.service -u iotc-vision.service -f
sudo systemctl restart iotc-vision.service          # after editing the env file
sudo systemctl disable --now iotc-vision.service    # drop back to one producer
```

To change the camera, clip, confidence or publish rates, edit `/etc/default/iotc-examples` and restart the services. `VISION_EXTRA` is appended to the vision command line verbatim; it defaults to `--loop`, which restarts a video file when it reaches the end and is ignored for cameras and RTSP sources.

For the CPU application, copy `iotc-pht.service` to `iotc-cpuperf.service` and set `ExecStart=/usr/bin/python3 perf_iotc_socket.py --freq 5`. Note that `perf_iotc_socket.py` does not read `IOTC_SOCK`; its paths are constants.

Details worth knowing if you write your own units:

- systemd will not accept a variable as the first token of `ExecStart`. The vision unit calls the interpreter through `/usr/bin/env` so `${VISION_PYTHON}` can come from the environment file.
- `${VAR}` is one argument; `$VAR` is split on whitespace. That is why `VISION_EXTRA` uses the unbraced form.
- The vision unit sets `KillSignal=SIGINT`. The application joins its worker threads on `SIGINT` but not on the default `SIGTERM`, which can leave port 8080 held for a few seconds.
- Both units use `After=` on `snap.iotconnect.socket.service` but not `Requires=`. The unit name varies with the Snap revision, and `Requires=` on a name that does not exist fails the whole unit. Confirm yours with `systemctl list-units 'snap.iotconnect*'`.
- Ordering is a hint, not a guarantee that the sockets exist. Both applications retry a missing socket rather than exiting, so the startup race resolves itself.

### Multiple producers on one bridge

Nothing in the bridge is per-application. Each publish is an independent connect, write and close, so any number of processes can share it:

- The listen backlog is 5 and telemetry is processed one connection at a time. Two applications at 1 and 10 second intervals are nowhere near that. Hundreds of messages per second are not what this design is for.
- Keep the 150 ms minimum spacing per producer. Coordinated bursts from several producers are what will fill the backlog.
- Every connected command listener receives every command. The vision application acts on the ones it recognises and acknowledges the rest as unknown; the PHT application does not open the command socket at all.
- All producers publish into one device, so their attributes share a device template. The included template covers all three applications for exactly this reason, which is why PHT gauges and vision detections can appear on the same dashboard with no re-provisioning.
- Telemetry from different producers arrives as separate messages, not a merged record. Widgets bound to `PHT_temp` and to `object1` update independently.

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
| `PermissionError: /dev/i2c-0` | `/dev/i2c-*` is `root:i2c` mode 660 and your user is not in the group | `sudo usermod -aG i2c $USER` then re-login, or run under the systemd unit, which sets `SupplementaryGroups=i2c` |
| A service runs but its journal only shows `Started ...` | Python buffers stdout when it is not a terminal | Set `Environment=PYTHONUNBUFFERED=1`; the shipped units already do |
| Pressure reads near 99590 | Raw value is 0.01 mbar and was published unscaled | Divide by 100; fixed in the current script |
| `PHT_die_temp` is -46.85 | The humidity die returned zeros; it has no temperature command | Expected on stock code before the fix; the current script mirrors `PHT_temp` |
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
