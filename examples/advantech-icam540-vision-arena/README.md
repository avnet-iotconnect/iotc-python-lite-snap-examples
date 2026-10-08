# iCAM-540 Vision Arena - DeepStream multi-stream analytics on /IOTCONNECT

A booth demo for the **Advantech iCAM-540** (NVIDIA Jetson Orin) that does two things at once:

1. **Booth analytics on the live camera.** PeopleNet + the NvDCF tracker count people crossing a virtual line into the booth, how many are in the booth zone right now, how long they stay (dwell), how many are "engaged" (stayed longer than N seconds), where the crowd is standing, and when the zone is overcrowded. The zone and line are drawn on the HDMI output by `nvdsanalytics` and can be moved from the cloud.
2. **A load dial for the Orin.** From the /IOTCONNECT dashboard you add looping 1080p video streams to the same DeepStream batch (1, 4 or 9 tiles), switch models (PeopleNet / ResNet10), switch TensorRT precision (FP32 / FP16 / INT8) and skip frames. The dashboard shows per-stream FPS, total FPS, GPU load, GPU clock, memory bandwidth, module power and temperatures from `tegrastats`, so visitors watch the Jetson fill up as you push it.

Everything runs in one always-on Python agent (`icam540_arena.py`) that talks to the /IOTCONNECT Snap over its UNIX sockets. No SDK code, no cloud credentials in the app.

```
 camera + N looping videos --> deepstream-app (PeopleNet/ResNet10 + NvDCF + nvdsanalytics)
                                   |  nvmsgbroker (MQTT, every 3rd frame)      | **PERF lines (pty)
                                   v                                           v
 tegrastats ------------->  icam540_arena.py  (zone/line/dwell analytics, FPS parser, Jetson metrics)
                                   |  flat JSON every 3 s          ^ commands + acks
                                   v                               |
                       /IOTCONNECT snap   iotc.sock  /  iotc_cmd.sock
```

---

## The 3-minute booth script

1. **"This camera is a Jetson Orin."** Point at the HDMI output: live PeopleNet boxes, tracker IDs, the booth zone polygon and the counting line drawn on the frame.
2. **Walk across the line.** *Visitors In* ticks up on the dashboard, *At Booth Now* rises, the *Last Event* tile flashes `visitor_in`. Stand still for five seconds: *Engaged* goes to 1 and *Avg Dwell* starts climbing. Walk out: `visitor_out`.
3. **"Now let's see what the Orin can really do."** Press **Stress** on the dashboard. The screen tiles to 2x2 (camera + three 1080p videos), *Total FPS* jumps, *GPU Load* climbs, *Power* rises. Press **9 streams**: 3x3 tiles, GPU pinned, per-stream FPS drops. The booth counters keep working on the camera tile the whole time.
4. **"Precision is a cloud setting."** Press **FP16**: same nine streams, FPS roughly doubles, power per inference drops. Press **Every 3rd** to skip frames and watch FPS and load move again.
5. **"And the model is just a config."** Press **ResNet10**: the 4-class detector (car, bicycle, person, road sign) replaces PeopleNet in a few seconds. Press **Booth** to go back to the clean single-camera view and **Reset** the counters for the next visitor.

Every press is a /IOTCONNECT command; the device acks it, regenerates the DeepStream config and restarts the pipeline (3 to 8 seconds with a cached TensorRT engine).

---

## Files

| File | Purpose |
| --- | --- |
| `icam540_arena.py` | The agent: config generator, DeepStream supervisor, FPS parser, tegrastats reader, MQTT consumer, booth analytics, snap telemetry and command handling |
| `config_infer_peoplenet_base.txt` | PeopleNet nvinfer config. Batch size, precision and engine path are rewritten into `generated/` at every start |
| `zones.json` | Booth zone polygon, counting line and thresholds (normalised 0..1). Updated by `set_roi` / `set_line` commands |
| `cfg_mqtt.txt` | nvmsgbroker MQTT settings (credentials if your broker needs them) |
| `start_arena.sh` / `stop_arena.sh` | One-command start (broker, snap socket, agent) and stop |
| `preflight.sh` | Booth-morning checklist: DeepStream, models, engines, sample streams, camera, broker, sudo, snap |
| `files/icam540-arena-device-template.json` | /IOTCONNECT device template: 47 attributes, 23 commands |
| `files/icam540-arena-dashboard-template.json` | /IOTCONNECT dashboard export (45 widgets) |
| `tools/make_templates.py` | Regenerates both template files |
| `tools/mock_deepstream_mqtt.py` | Publishes synthetic DeepStream messages (simulated visitors) for desk testing |
| `tools/iotc_sock_sniffer.py` | Stand-in for the snap sockets: prints telemetry, forwards typed commands |
| `generated/`, `logs/` | Created at runtime (git-ignored) |

---

## 1. Device prerequisites

The iCAM-540 ships with JetPack and DeepStream (the existing `advantech-icam540` example in this repository runs on the stock image). On top of that:

```bash
sudo apt-get update
sudo apt-get install -y mosquitto libmosquitto1 python3-pip
sudo systemctl enable --now mosquitto
pip3 install paho-mqtt
```

Passwordless `sudo` for your login is assumed (the stock `icam-540` user has it). `deepstream-app` and `tegrastats` are launched with `sudo -n`; pass `--no-sudo` to the agent if you run it as root or your user can open the camera and the GPU counters directly.

Install and provision the snap if you have not already:

```bash
sudo snap install iotconnect
iotconnect.setup
```

Clone this repository on the device (any path works; the scripts locate themselves):

```bash
git clone https://github.com/avnet-iotconnect/iotc-python-lite-snap-examples.git
cd iotc-python-lite-snap-examples/examples/advantech-icam540-vision-arena
./preflight.sh
```

Fix anything `preflight.sh` reports as `FAIL`. `WARN` lines are fine for a first run.

### Build the TensorRT engines before the show

The first start of any model/precision/batch combination makes TensorRT build an engine, which takes minutes on an Orin NX. Do it the day before, not at the booth:

```bash
# fp32 batch 1 is what the stock image already has; fp16 is the one you want for the "precision" button
./icam540_arena.py --warmup peoplenet:fp16:1
# optional: batched engines for 4 and 9 streams (higher throughput than running a batch-1 engine N times)
./icam540_arena.py --warmup peoplenet:fp16:4,9
./icam540_arena.py --warmup resnet10:auto:1
```

Warmup runs headless with a sample video and exits when the engine file appears under `/opt/nvidia/deepstream/deepstream/samples/models/...`. Start the agent with `--batched` to use the batched engines when they exist (the agent falls back to batch 1 automatically when they do not).

---

## 2. Import the device template and dashboard

Both files are in [files/](./files/).

**Device template** (first, the dashboard binds to its attributes):

1. /IOTCONNECT > **Device** > **Templates** > **Create Template** > **Import** > `icam540-arena-device-template.json`.
2. Create or edit your device and assign the template. The dashboard export assumes the unique ID `mclICAM540arena`; any ID works, you re-select it below.

**Dashboard:**

1. **Dashboard** > **Create Dashboard** > **Import** > `icam540-arena-dashboard-template.json`.
2. Edit each widget and select your device (and template on the control widgets). Layout, gauge ranges, colour bands and titles are kept.

If a control button sends the opposite command to its label, swap the left/right command in that widget; the mapping of the two halves differs between portal versions.

---

## 3. Run

```bash
./start_arena.sh            # booth preset: camera only, PeopleNet, overlay on
./start_arena.sh stress     # camera + 3 looping videos (2x2)
./start_arena.sh max        # camera + 8 looping videos (3x3)
tail -f logs/agent.log
```

`start_arena.sh` stops the iCAM-540 web UI services that hold the camera, starts mosquitto and the snap socket, then the agent. The agent auto-starts DeepStream. Stop everything with `./stop_arena.sh`.

Run the agent by hand to see all options:

```bash
./icam540_arena.py --help
./icam540_arena.py --streams 1 --precision fp16 --batched --display both --print-telemetry
```

Useful options:

| Option | Default | Notes |
| --- | --- | --- |
| `--streams N` / `--max-streams` | 1 / 9 | Initial and maximum stream count |
| `--model` | peoplenet | `peoplenet` or `resnet10` |
| `--precision` | auto | `auto` keeps the base config (fp32 for PeopleNet, int8 for ResNet10) |
| `--batched` | off | Use a batch-N engine when cached; see warmup |
| `--camera` | `v4l2:/dev/video0` | `file:///path/clip.mp4` or `rtsp://...` for a desk demo |
| `--display` | screen | `rtsp` publishes the tiled output on `rtsp://<device>:8554/ds-test`; `both`; `none` |
| `--extra-stream FILE` | | Your own looping clips, used before the DeepStream samples |
| `--msg-frame-interval` | 3 | DeepStream message every N frames per stream (10 msg/s at 30 fps) |
| `--telemetry-interval` | 3 | Seconds between cloud payloads |
| `--no-osd-analytics` | | Skip the nvdsanalytics overlay (analytics still computed in the agent) |
| `--dry-run` | | Write the generated DeepStream configs and print them |

If the agent is started from SSH, `DISPLAY=:0` and the user's `.Xauthority` are supplied to `deepstream-app` so the HDMI sink still works.

---

## 4. What the device publishes

One flat JSON object every `telemetry_interval` seconds. All names match the device template.

**Booth analytics (camera stream only)**

| Attribute | Meaning |
| --- | --- |
| `visitors_in`, `visitors_out` | Line crossings in each direction since the last reset |
| `occupancy`, `occupancy_peak` | People whose feet are inside the booth polygon now / peak |
| `people_now` | Tracked people anywhere in the camera frame |
| `engaged` | People in the zone longer than `engage_s` (default 5 s) |
| `dwell_avg_s`, `dwell_max_s`, `dwell_last_s` | Time spent in the zone, from completed visits |
| `tracks_total` | Unique tracker IDs seen since reset |
| `hot_zone` | `left`, `center` or `right` third of the frame with most people |
| `event` | `visitor_in`, `visitor_out` or `overcrowded`, cleared after 30 s |

**Pipeline and throughput**

| Attribute | Meaning |
| --- | --- |
| `pipeline` | `stopped`, `starting`, `running`, `restarting`, `error` |
| `streams`, `streams_active`, `model`, `precision`, `batch`, `infer_interval`, `osd_analytics` | Running configuration |
| `fps_cam`, `fps_total`, `fps_min`, `fps_avg`, `fps_streams` | Parsed from deepstream-app `**PERF` lines every 2 s |
| `infer_mpx_s` | Megapixels inferred per second (`fps_total` x 1280x720) |
| `msgs_per_s`, `objects_total`, `persons_total`, `vehicles_total` | Detection message rate and object counts across all streams |
| `message` | Status text (configuration summary or the last DeepStream error) |

**Jetson counters** (from `tegrastats`, sysfs fallback)

`gpu_load_pct`, `gpu_freq_mhz`, `gpu_temp_c`, `cpu_load_pct`, `cpu_temp_c`, `soc_temp_c`, `power_w` (VDD_IN), `power_gpu_w`, `ram_used_mb`, `ram_total_mb`, `emc_pct`, `nvdec_mhz`, `uptime_s`, `pipeline_uptime_s`.

---

## 5. Commands

Send from the dashboard buttons, the **Command Console** widget, or **Device** > **Devices** > *device* > **Commands**. The snap forwards them as `{"name": ..., "args": [...], "ack_id": ...}`; plain text such as `set_streams 4` also works. Every command is acknowledged.

| Command | Argument | Effect |
| --- | --- | --- |
| `start`, `stop`, `restart`, `status` | | Pipeline control. `status` returns the full telemetry snapshot in the ack |
| `preset` | `booth` / `stress` / `max` | 1 / 4 / 9 streams |
| `set_streams` | 1..9 | Camera + N-1 looping videos, tiled |
| `set_model` | `peoplenet` / `resnet10` | |
| `set_precision` | `auto` / `fp32` / `fp16` / `int8` | First use of a new precision builds an engine (minutes) unless warmed up |
| `set_interval` | 0..10 | nvinfer frame skip |
| `set_batched` | on / off | Use batched engines when cached |
| `set_osd` | 1 / 0 | nvdsanalytics overlay on the HDMI output |
| `set_roi` | `x,y;x,y;x,y[;x,y]` | Booth polygon, normalised 0..1, saved to `zones.json` |
| `set_line` | `x1,y1;x2,y2` | Counting line, normalised. Entry direction is the left side of p1 to p2 |
| `flip_line` | | Swap in/out direction |
| `set_engage` | seconds | Engagement threshold |
| `set_overcrowd` | count | Overcrowding threshold (also drawn by the overlay) |
| `reset_counts` | | Zero the booth counters |
| `set_telemetry_interval` | seconds | |
| `ping` | | |

Commands that change the pipeline ack immediately with "restarting pipeline"; `pipeline` goes `restarting` > `starting` > `running` in telemetry.

---

## 6. Desk testing without the camera or DeepStream

The analytics and cloud path can be exercised on any Linux box (the mock below was used to validate this example):

```bash
pip3 install paho-mqtt
sudo apt-get install -y mosquitto                      # or any MQTT broker on localhost:1883
./tools/iotc_sock_sniffer.py --dir /tmp/iotc           # terminal 1: fake snap sockets, type commands here
./icam540_arena.py --no-deepstream --iotc-sock /tmp/iotc/iotc.sock --iotc-cmd-sock /tmp/iotc/iotc_cmd.sock   # terminal 2
./tools/mock_deepstream_mqtt.py --streams 4            # terminal 3: simulated visitors on 4 streams
```

In terminal 1 type `preset stress`, `set_roi 0.1,0.3;0.9,0.3;0.9,0.95;0.1,0.95`, `reset_counts`, and watch the telemetry lines and acks.

Without `--no-deepstream` but with a video file instead of the camera (`--camera file:///opt/nvidia/deepstream/deepstream/samples/streams/sample_walk.mov`) the full pipeline runs on any Jetson with DeepStream.

---

## 7. How it works

- **Config generation.** `generate_app_config()` writes `generated/deepstream_arena.txt` from the current state: one `[sourceN]` per stream (camera first, then DeepStream sample clips looped with `file-loop=1`), `[streammux]` batch = N, `[tiled-display]` rows/cols = ceil(sqrt(N)), `[primary-gie]` pointing at a generated nvinfer config with the right batch/precision/engine path, `[tracker]` NvDCF, `[nvds-analytics]` with the booth polygon, overcrowding ROI and the counting line converted to streammux pixels, and the MQTT `[sink]` publishing every 3rd frame.
- **Detections.** `nvmsgconv` with `msg2p-new-api=1` emits one message per frame per stream with `objects` as `id|left|top|right|bottom|label` strings. The agent also accepts the per-object dictionary schema. Only stream 0 feeds the booth analytics; all streams feed the object counters.
- **Booth analytics** run in Python on the tracked foot point (bottom-centre of each box): point-in-polygon for the zone, a signed-side test with hysteresis for the line, per-track dwell accumulation, 1.5 s staleness expiry. The same geometry is given to `nvdsanalytics` so the overlay matches the numbers.
- **FPS** comes from `deepstream-app`'s own `**PERF:` output. The process is started on a pseudo-terminal so the output is line-buffered.
- **Resilience.** If DeepStream exits within 25 s with the overlay enabled, the agent restarts without the overlay; if a batched engine fails, it retries with batch 1; later crashes auto-restart up to three times with the reason in `message`. `SIGTERM` to the agent stops DeepStream and tegrastats cleanly.

---

## 8. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `pipeline` stays `starting`, no FPS | Check `logs/deepstream.log`. Camera busy: `sudo systemctl stop web.service autoui.service`. No X display: start with `--display rtsp` or set `DISPLAY` |
| First `set_precision fp16` takes minutes | Expected: TensorRT engine build. Run `--warmup peoplenet:fp16:1` beforehand |
| Counters never move but FPS is fine | No MQTT messages: `mosquitto_sub -t icam540/arena -v`. Check `libmosquitto1` is installed and `cfg_mqtt.txt` credentials |
| `visitors_in` counts people leaving | `flip_line` |
| Zone does not match the floor | `set_roi` with four normalised points, e.g. `0.2,0.35;0.8,0.35;0.95,0.98;0.05,0.98` (top edge first). The overlay shows the result after the restart |
| No GPU metrics | `tegrastats` needs `sudo -n`; the agent falls back to sysfs (GPU load and temperatures only) |
| `set_streams 9` fails with "no sample video streams" | Install the DeepStream samples or pass `--extra-stream /path/clip.mp4` |
| Duplicate device connections | Only one snap socket may run: `sudo snap stop iotconnect.socket` before `start_arena.sh` |

---

## 9. Pushing it further

Ideas that fit this agent without changing the cloud side:

- **Secondary classifiers.** Add a `[secondary-gie]` (vehicle type / colour, or PeopleNet + a gaze/age model) and publish the classifier labels, which already arrive after the `|#|` separator in the object strings.
- **Tracker precision as a cloud toggle.** Switch between `config_tracker_NvDCF_perf.yml` and `config_tracker_NvDCF_accuracy.yml` (`--tracker-config`) to show the accuracy/throughput trade-off on the same stream.
- **OTA model drop.** Ship a new nvinfer config plus engine as an /IOTCONNECT OTA package into `$SNAP_COMMON`, and point `MODELS` at it; the pipeline restart is already a command.
- **RTSP in the dashboard.** With `--display rtsp` the tiled output is at `rtsp://<device>:8554/ds-test`; a small WebRTC/HLS relay on the device lets the **Embedded** widget show the live tiles next to the gauges.
