# iCAM540 DeepStream → /IOTCONNECT Snap (MQTT Bridge)

This demo enables DeepStream message output (nvmsgconv + nvmsgbroker), publishes detections to MQTT, and forwards those messages into the /IOTCONNECT snap socket.

---

## Prerequisites

- /IOTCONNECT snap running (socket service)
- DeepStream installed (as provided on the device)
- An MQTT broker reachable from this device (example: mosquitto on localhost)
- Python 3 with `paho-mqtt`
- MQTT protocol library dependency for DeepStream (`libmosquitto.so.1`)

---

## Files In This Folder

- `source1_icam540_v4l2_test_msg.txt`  
  DeepStream config based on the iCAM540 V4L2 demo, with MQTT message sink enabled.
- `source1_icam540_peoplenet_tracker_rtsp_msg.txt`  
  PeopleNet config (camera + PeopleNet), with MQTT message sink enabled.
- `config_infer_primary_peoplenet_onnx.txt`  
  PeopleNet infer config with `labelfile-path` set (enables on-screen labels).
- `dstest5_msgconv_sample_config.txt`  
  Msgconv metadata config (minimal).
- `cfg_mqtt.txt`  
  MQTT broker auth settings (username/password).
- `mqtt_to_iotc_socket.py`  
  MQTT → /IOTCONNECT snap socket forwarder.
- `icam540_iotc_agent.py`  
  Always-on agent: perf telemetry + command listener + DeepStream control.
- `preflight.sh`  
  Checks files, MQTT dependencies, broker reachability, and socket presence.

---

## 1. Start The /IOTCONNECT Snap Socket

Make sure the snap socket is running:

```bash
snap run iotconnect.socket-debug
```

You should see:
- `/home/icam-540/snap/iotconnect/common/iotc.sock`
- `/home/icam-540/snap/iotconnect/common/iotc_cmd.sock`

---

## Fresh Boot Quick Start (Recommended Order)

One‑command startup (recommended):

```bash
cd /home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540 && ./start_all.sh
```

Start PeopleNet instead of default:

```bash
cd /home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540 && ./start_all.sh peoplenet
```

Interactive (separate terminal panes with live logs):

```bash
cd /home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540 && ./start_all_tmux.sh
```

Interactive PeopleNet:

```bash
cd /home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540 && ./start_all_tmux.sh peoplenet
```

If `tmux` is missing:

```bash
sudo apt-get install -y tmux
```

Notes:
- If the tmux session already exists, the script attaches instead of exiting.
- The socket window auto‑restarts if the /IOTCONNECT socket process exits.

If you want PeopleNet label mapping, run:

```bash
FORWARDER_LABELS=/opt/nvidia/deepstream/deepstream/samples/models/PeopleNet/labels.txt \
  /home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/start_all.sh
```

Stop everything started by the script:

```bash
cd /home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540 && ./stop_all.sh
```

Logs are written to:

```
examples/advantech-icam540/logs
```

Manual sequence after a fresh reboot:

1. Start the MQTT broker:
   ```bash
   sudo systemctl enable --now mosquitto
   ```
2. Start the /IOTCONNECT snap socket:
   ```bash
   snap run iotconnect.socket-debug
   ```
3. Start the always‑on agent (auto‑starts DeepStream with default config):
   ```bash
   cd /home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540 && ./agent.sh
   ```
4. Start the MQTT → /IOTCONNECT forwarder (summary every 4 seconds):
   ```bash
   /home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/mqtt_to_iotc_socket.py \
     --host localhost --port 1883 --topic icam540/ds \
     --did mclICAM540snap \
     --iotc-sock /home/icam-540/snap/iotconnect/common/iotc.sock \
     --min-interval 4
   ```

If you want PeopleNet label mapping, add:
```
--labels /opt/nvidia/deepstream/deepstream/samples/models/PeopleNet/labels.txt
```

---

## 2. Configure MQTT Settings

Edit the DeepStream config to match your broker and topic:

File: `examples/advantech-icam540/source1_icam540_v4l2_test_msg.txt`

```
[sink2]
enable=1
type=6
msg-conv-config=/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/dstest5_msgconv_sample_config.txt
msg-conv-payload-type=0
msg-broker-proto-lib=/opt/nvidia/deepstream/deepstream/lib/libnvds_mqtt_proto.so
msg-broker-conn-str=localhost;1883;icam540/ds
topic=icam540/ds
msg-broker-config=/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/cfg_mqtt.txt
```

If your broker requires credentials, edit:
`examples/advantech-icam540/cfg_mqtt.txt`

```
[message-broker]
username = user
password = password
```

---

## 3. Run DeepStream With Message Output Enabled

Optional preflight check:

```bash
/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/preflight.sh
```

Then run DeepStream:

```bash
sudo -E deepstream-app \
  -c /home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/source1_icam540_v4l2_test_msg.txt
```

---

## 4. Install The MQTT Python Dependency

```bash
pip install paho-mqtt
```

---

## 4.1 Install Required System Dependencies

DeepStream’s MQTT protocol adaptor requires `libmosquitto.so.1`:

```bash
sudo apt-get update
sudo apt-get install -y libmosquitto1
```

---

## 4.2 Start An MQTT Broker (If Not Already Running)

If you see `ConnectionRefusedError: [Errno 111] Connection refused`, it usually means no broker is listening on the host/port.

Example (mosquitto on localhost):

```bash
sudo apt-get update
sudo apt-get install -y mosquitto
sudo systemctl enable --now mosquitto
```

Then verify it is listening:

```bash
sudo systemctl status mosquitto
```

---

## 5. Start The MQTT → /IOTCONNECT Forwarder

```bash
/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/mqtt_to_iotc_socket.py \
  --host localhost \
  --port 1883 \
  --topic icam540/ds \
  --did mclICAM540snap \
  --iotc-sock /home/icam-540/snap/iotconnect/common/iotc.sock \
  --min-interval 4
```

The forwarder subscribes to the MQTT topic, builds a summary, and writes it to the /IOTCONNECT snap socket every N seconds (default 4).

**Forwarder telemetry**

`telemetry.summary`
- `count` (int): number of objects detected in the most recent DeepStream message.
- `labels` (string[]): unique label names detected (e.g., `Person`, `Car`).
- `objects` (object[]): one entry per object.
  - `label` (string): class label name.
  - `confidence` (float|null): model confidence when provided.
  - `bbox` (object): bounding box object from DeepStream (usually `topleftx`, `toplefty`, `bottomrightx`, `bottomrighty`).

`telemetry.deepstream` (optional)
- Full DeepStream message payload. Use `--summary-only` if you do not want this included.

Summary fields include:
- `count` (number of objects)
- `labels` (set of detected labels)
- `objects` (label, confidence, and bounding box)

To send only the summary (omit raw DeepStream payload):

```bash
/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/mqtt_to_iotc_socket.py \
  --summary-only
```

To change the interval, use `--min-interval` or set `IOTC_MIN_INTERVAL=4`.

---

## 6. Run The Always-On Agent (Optional)

This agent keeps running, sends performance telemetry, and listens for commands from /IOTCONNECT (to start/stop DeepStream).

The agent does not change camera settings. If the camera is busy, stop the UI services manually:

```bash
sudo systemctl stop web.service
sudo systemctl stop autoui.service
```

Short launcher (recommended if command length is limited):

```bash
cd /home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540 && ./agent.sh
```

Full command:

```bash
/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/icam540_iotc_agent.py \
  --did mclICAM540snap \
  --perf-interval 5 \
  --deepstream-config /home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/source1_icam540_v4l2_test_msg.txt
```

If your DeepStream run requires sudo, start the agent with sudo or set:

```
--deepstream-cmd "sudo -E deepstream-app"
```

Supported commands (/IOTCONNECT command payloads):

```
{"name":"start_deepstream","args":["/path/to/config"],"ack_id":"123"}
{"name":"stop_deepstream","ack_id":"124"}
{"name":"restart_deepstream","ack_id":"125"}
{"name":"status","ack_id":"126"}
{"name":"perf_interval","args":[4],"ack_id":"127"}
{"name":"set_config","args":["default"],"ack_id":"128"}
```

**Command descriptions**

- `start_deepstream`  
  Starts DeepStream using the active config. If an argument is provided, it overrides the active config for this start.  
  Example: `{"name":"start_deepstream","ack_id":"1"}` or `{"name":"start_deepstream","args":["/path/to/config"],"ack_id":"2"}`

- `stop_deepstream`  
  Stops the running DeepStream process (if any).  
  Example: `{"name":"stop_deepstream","ack_id":"3"}`

- `restart_deepstream`  
  Stops and immediately starts DeepStream (uses active config unless an argument is provided).  
  Example: `{"name":"restart_deepstream","ack_id":"4"}`

- `status`  
  Returns whether DeepStream is running and the PID in the ACK payload.  
  Example: `{"name":"status","ack_id":"5"}`

- `perf_interval`  
  Changes the agent’s performance telemetry interval (seconds).  
  Example: `{"name":"perf_interval","args":[4],"ack_id":"6"}`

- `set_config`  
  Sets the active DeepStream config using a short alias (configured via `--config-alias`).  
  Example: `{"name":"set_config","args":["default"],"ack_id":"7"}`

**Agent telemetry**

`telemetry.perf`
- `uptime_s` (float): system uptime in seconds.
- `cpu_load1` (float): 1‑minute load average.
- `mem_total_kb` (int): total memory (kB).
- `mem_avail_kb` (int): available memory (kB).
- `cpu_temp_c` (float|null): CPU temperature in °C when available.

If your /IOTCONNECT UI limits command args length, use config aliases:

Start the agent with:

```
--config-alias "default=/full/path/to/source1_icam540_v4l2_test_msg.txt"
--config-alias "peoplenet=/full/path/to/source1_icam540_peoplenet_tracker_rtsp_msg.txt"
```

Then send:

```
{"name":"set_config","args":["default"],"ack_id":"200"}
{"name":"start_deepstream","ack_id":"201"}
```

To use the PeopleNet config:

```
{"name":"set_config","args":["peoplenet"],"ack_id":"210"}
{"name":"start_deepstream","ack_id":"211"}
```

**Model switching examples**

- Start default model (Primary_Detector):
  ```
  {"name":"set_config","args":["default"],"ack_id":"300"}
  {"name":"restart_deepstream","ack_id":"301"}
  ```
- Start PeopleNet:
  ```
  {"name":"set_config","args":["peoplenet"],"ack_id":"310"}
  {"name":"restart_deepstream","ack_id":"311"}
  ```

When using PeopleNet, set the label file for the forwarder:

```bash
/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/mqtt_to_iotc_socket.py \
  --labels /opt/nvidia/deepstream/deepstream/samples/models/PeopleNet/labels.txt
```

---

## Troubleshooting

- **No MQTT messages**: Verify DeepStream is running and the MQTT broker is reachable on the configured host/port.
- **No /IOTCONNECT telemetry**: Confirm the socket file exists and permissions allow write access.
- **Different socket paths**: Override with `--iotc-sock` or set `IOTC_SOCKET`.
- **Broker library load error** (`unable to open shared library`): On Jetson, `libnvds_mqtt_proto.so` depends on `libmosquitto.so.1`. Install it:
  ```bash
  sudo apt-get update
  sudo apt-get install -y libmosquitto1
  ```
- **Duplicate ID / multiple connections**: Ensure only one /IOTCONNECT socket process is running.
  ```bash
  sudo snap stop iotconnect.socket
  pkill -f iotconnect.socket-debug
  snap run iotconnect.socket-debug
  ```

---

## Notes

- The DeepStream message payload uses the default DeepStream schema (`msg-conv-payload-type=0`).
- Labels for the sample Primary_Detector model are: `Car`, `Bicycle`, `Person`, `Roadsign`.
- PeopleNet labels file: `/opt/nvidia/deepstream/deepstream/samples/models/PeopleNet/labels.txt`.
- If you want Kafka instead of MQTT, the broker section can be swapped and a Kafka config added.
