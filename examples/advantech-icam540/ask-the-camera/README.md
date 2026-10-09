# Ask the camera - a VLM narrator for the iCAM-540 on /IOTCONNECT

Status: **validated on the iCAM-540 (Orin NX 8 GB, JetPack 6.2) on 2026-10-09.** Ollama runs `qwen3-vl:2b-instruct` fully on the GPU, the narrator captions the live sensor every ~10 s and publishes the telemetry below. The /IOTCONNECT snap was not installed on the unit yet (needs an account, section 5), so the agent printed its telemetry to stdout. The bring-up findings that changed the scaffold are in section 2.

## 1. What the demo does

A 2B-parameter vision-language model (VLM) runs on the camera's Jetson Orin NX next to the DeepStream pipeline from [advantech-icam540-vision-arena](../../advantech-icam540-vision-arena/). Every few seconds it looks at the current frame and publishes to /IOTCONNECT:

- `scene_caption`: one sentence describing the booth ("Two people are looking at the camera on the table, one is pointing at the screen").
- `people_vlm`, `engagement`, `unusual`: structured fields parsed from the model's JSON reply.
- `alert_1..3`: yes/no evaluation of plain-English rules a visitor types on the dashboard ("someone is wearing a hard hat", "a laptop is unattended").
- `question` / `answer`: a free-text question sent from the dashboard, answered against the latest frame.
- `vlm_latency_ms`, `vlm_prefill_ms`, `vlm_tok_s`, token counts: the "how hard is the Orin working" numbers.

Talk track: show the live caption updating, type a question on the dashboard, then type an alert rule and have someone trigger it. Each round trip is about 10 s on the Orin NX 8 GB with the 2B model (section 6).

```
 frame (/dev/video0 via v4l2-ctl, or RTSP from DeepStream) --> vlm_narrator.py --> Ollama /api/chat (or any OpenAI-compatible /v1)
                                                                      |
                                                                      v
                                                        /IOTCONNECT snap  iotc.sock / iotc_cmd.sock
```

## 2. Bring-up on the camera

```bash
git clone -b icam540-ask-the-camera https://github.com/avnet-iotconnect/iotc-python-lite-snap-examples.git
cd iotc-python-lite-snap-examples/examples/advantech-icam540/ask-the-camera
bash bringup_report.sh | tee bringup_report.txt
```

`bringup_report.txt` (checked in, from the unit used for bring-up) captures the BSP version, JetPack/L4T, DeepStream, power mode, memory, camera node, snap state and whether Ollama or llama.cpp is already present. What it showed, and what it changed:

| Finding on the iCAM-540 | Consequence |
| --- | --- |
| Advantech image 3.1.8.2, L4T R36.4.3 (JetPack 6.2), CUDA 12.6, TensorRT 10.3, Ubuntu 22.04, 7.4 GB RAM, 15 W power mode with 4 of 6 cores online | Ollama's JetPack 6 runner; the 2B model is the right size |
| SSH is not enabled out of the box | on the HDMI console: `sudo apt install -y openssh-server && sudo ssh-keygen -A && sudo systemctl enable --now ssh` (the stock image ships without host keys, so `ssh.service` fails until `ssh-keygen -A`). Default login `icam-540` / `icam-540`, change it |
| `web.service` (the stock web UI, `/opt/advantech/web/app.py`) holds `/dev/video0` exclusively | `sudo systemctl stop web.service autoui.service` before any direct capture; `sudo systemctl start web.service` restores the UI (it is enabled, so it comes back on reboot) |
| OpenCV's V4L2 backend cannot open the Tegra VI node at all: every `VIDIOC_S_FMT` returns `EINVAL`, even with the exact 1920x1080 YUYV the driver advertises. `v4l2-ctl --stream-mmap` streams it fine | `vlm_narrator.py` falls back to single-frame grabs through `v4l2-ctl` (YUYV, decoded with OpenCV); `--v4l2-size` picks 1920x1080, 1408x1080 or 3840x2160 |
| The sensor boots in manual exposure (`exposure_time=50`, gain 0): a near-black frame, captioned as "a dark blurry image" | the narrator sets `exposure_mode=1,sensor_gain_mode=1,auto_exposure_max=330` once at open (`--v4l2-ctrls`) and skips 120 frames on the first grab so auto exposure settles; the converged state survives stream stop/start, later grabs skip 3 frames |
| Uncapped auto exposure in a dim room picks ~216 ms exposures and the sensor drops to ~4.6 fps | `auto_exposure_max=330` (units of 100 µs, one frame at 30 fps) keeps 30 fps and lets auto gain compensate |
| `qwen3-vl:2b` on Ollama is the thinking variant: it spends the entire `max_tokens` budget inside `<think>` and returns an empty answer, and `think:false` is ignored by that tag | default model is now `qwen3-vl:2b-instruct`; the narrator talks to Ollama's native `/api/chat` with `think:false` and `format:"json"` (JSON mode costs nothing measurable) |
| `setup_vlm.sh` wrote the systemd drop-in after the installer had already started Ollama, so `OLLAMA_KEEP_ALIVE`, `OLLAMA_MAX_LOADED_MODELS` never applied: the model was loaded twice, one copy split 80/20 CPU/GPU at 2.4 tok/s | the script now restarts Ollama after writing the drop-in |
| `deepstream-app` fails to load `libnvdla_compiler.so` on this image, so the Vision Arena (and its RTSP output) does not run yet | the narrator reads the sensor directly; fix for the arena: `sudo apt install nvidia-l4t-dla-compiler` (not yet verified) |
| No Docker, no snap, no paho-mqtt; Python 3.10 with OpenCV 4.11 (pip wheel, no GStreamer) and numpy 2.2 | nothing else to install for the narrator |

## 3. Install a VLM runtime

Default path, validated on JetPack 6.2:

```bash
./setup_vlm.sh                # installs Ollama, pulls qwen3-vl:2b-instruct, smoke-tests it
ollama ps                     # must show 100% GPU and UNTIL Forever; if it says CPU, see troubleshooting
```

Alternatives, in order of preference:

| Runtime | When | Endpoint |
| --- | --- | --- |
| Ollama | simplest; official JetPack 5 and 6 support; native API gives thinking control and timing | `http://localhost:11434` (`/v1` also accepted) |
| llama.cpp `llama-server --mmproj` | lowest memory, fastest to first token on 8 GB | `http://localhost:8080/v1` |
| TensorRT Edge-LLM | NVIDIA's own runtime, best decode speed; JetPack 6.2+ only, engine export on an x86 host | its OpenAI-compatible server |

Model choice: `qwen3-vl:2b-instruct` first (not the plain `:2b` tag, see section 2). `gemma3:4b` or Gemma 4 E2B as the "newest model" alternative if memory allows. Keep `max_tokens` around 120; the dashboard only needs a sentence and the instruct model answers the cycle prompt in 40 to 60 tokens.

## 4. Run the narrator

Desk test without the camera, against any image:

```bash
./vlm_narrator.py --source file:///opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.jpg --once
```

On the camera, reading the sensor directly (the validated path):

```bash
sudo systemctl stop web.service autoui.service        # they hold the sensor
./vlm_narrator.py --source v4l2:/dev/video0 --interval 8 --print-telemetry
```

Next to the Vision Arena once it runs on this image (it owns `/dev/video0`), take frames from DeepStream's RTSP output instead:

```bash
# in the arena folder: start with the RTSP sink enabled
./start_arena.sh booth --display both
# here:
./vlm_narrator.py --source rtsp://127.0.0.1:8554/ds-test --interval 8 --print-telemetry
```

Options: `--endpoint`, `--model`, `--api auto|ollama|openai`, `--interval`, `--max-tokens`, `--max-width` (frame is downscaled before upload; 640 px is plenty, see section 6), `--v4l2-size`, `--v4l2-ctrls`, `--alert "<rule>"` (repeatable), `--paused`, `--once`.

## 5. Commands and telemetry

Commands arrive on the snap command socket, as JSON `{"name": "ask", "args": ["is anyone wearing red"], "ack_id": "..."}` or plain text `ask is anyone wearing red`.

| Command | Effect |
| --- | --- |
| `ask <question>` | one-shot answer about the latest frame, published as `question` / `answer` |
| `set_alert <rule>` | add a yes/no rule (max 3), evaluated every cycle into `alert_1..3` |
| `clear_alerts` | remove all rules |
| `vlm_interval <s>` | seconds between cycles (min 2); alias `set_interval` |
| `vlm_model <tag>` | switch model on the endpoint; alias `set_model` |
| `vlm_max_tokens <n>` | alias `set_max_tokens` |
| `vlm_pause` / `vlm_resume` / `vlm_status` / `vlm_ping` | aliases `pause` / `resume` / `status` / `ping` |

The `vlm_` names exist because the narrator shares the device, the command socket and the template with the Vision Arena agent, which owns `set_interval`, `set_model`, `status` and `ping`. Each agent ignores, without an ack, the commands it does not own, so the cloud gets exactly one ack per command. `ts`, `type` (`vlm` here, `arena` there) and `message` are the shared attributes.

Telemetry is one flat JSON object per cycle (and after each `ask`): `type=vlm`, `vlm_state`, `vlm_model`, `scene_caption`, `people_vlm`, `engagement`, `unusual`, `question`, `answer`, `alert_rules`, `alerts_active`, `alert_text`, `alert_1`, `alert_2`, `alert_3`, `vlm_latency_ms`, `vlm_prefill_ms`, `vlm_tok_s`, `vlm_prompt_tokens`, `vlm_completion_tokens`, `vlm_cycle`, `message`.

Without the snap the narrator prints the same objects to stdout and disables the command listener. To connect it: `sudo snap install iotconnect`, then `iotconnect.setup` with the account's device credentials (see the repository README); the narrator finds `iotc.sock` / `iotc_cmd.sock` on its own.

**Device template and dashboard.** One device carries both demos, so the attributes and commands above live in the Vision Arena's template, and the dashboard export has an "ASK THE CAMERA" section (caption, answer, alerts, latency gauges, buttons for ask / set_alert / pause / interval, and a console for free-text questions):

| File | Purpose |
| --- | --- |
| [`../../advantech-icam540-vision-arena/files/icam540-arena-device-template.json`](../../advantech-icam540-vision-arena/files/icam540-arena-device-template.json) | device template, arena + VLM attributes and commands |
| [`../../advantech-icam540-vision-arena/files/icam540-arena-dashboard-template.json`](../../advantech-icam540-vision-arena/files/icam540-arena-dashboard-template.json) | dashboard export with the VLM section at the bottom |
| [`../../advantech-icam540-vision-arena/tools/make_templates.py`](../../advantech-icam540-vision-arena/tools/make_templates.py) | regenerates both |

Import steps are in the [arena README, section 2](../../advantech-icam540-vision-arena/README.md): template first, then the dashboard, then re-select your device in each widget. The narrator alone (arena not running) works with the same template; the arena widgets just stay empty.

## 6. Measured on the 8 GB Orin NX (15 W mode)

| What | Measured |
| --- | --- |
| Memory with Ollama + model loaded, narrator running, desktop up, `web.service` stopped | 6.3 GB used of 7.4 GB, 1.1 GB available (plus 3.7 GB zram swap, unused) |
| Model load (first request) | ~5.5 s |
| Image prefill, any width from 448 to 1280 px | ~1050 to 1200 prompt tokens, 6.0 to 6.5 s (Ollama pads small images up to its minimum, so smaller uploads do not help) |
| Image prefill at 1920 px | 2052 tokens, 17 s (do not) |
| Decode | 13.8 tok/s, 40 to 60 tokens per cycle, ~3 s |
| Cycle, model warm | 9 to 10 s wall clock, plus ~0.5 s for the frame grab |
| First grab after start | ~4 s (120 skipped frames at 30 fps for auto exposure to settle) |

The rough budget from the scaffold still holds: desktop + agent ~1.5 GB, DeepStream PeopleNet 1 stream ~1.5 to 2 GB, the 2B model ~2 GB plus runtime. That fits in booth mode. It does not fit with 9 DeepStream streams, so pause the narrator before `preset max`. If memory is tight, drop the desktop (`sudo systemctl set-default multi-user.target`).

## 7. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ollama ps` shows CPU or two copies of the model | `systemctl show ollama -p Environment` must list `JETSON_JETPACK`, `OLLAMA_KEEP_ALIVE=-1`, `OLLAMA_MAX_LOADED_MODELS=1`; if not, `sudo systemctl restart ollama` (the drop-in is only read on restart) |
| `ollama ps` says UNTIL "4 minutes from now" | the CLI sent its own keep-alive; harmless, the narrator's requests pin the model with `keep_alive:-1` |
| caption is empty, `vlm_completion_tokens` = `max_tokens` | thinking model (`qwen3-vl:2b`): switch to `qwen3-vl:2b-instruct` |
| `vlm_state=error`, "endpoint unreachable" | `curl localhost:11434/api/version` |
| `vlm_state=error`, `v4l2-ctl ... timed out` or "cannot open /dev/video0" | `sudo fuser -v /dev/video0`: stop `web.service` / `autoui.service` or the arena; a timeout on the first grab means auto exposure is uncapped and the sensor is running at a few fps, check `v4l2-ctl -d /dev/video0 --get-ctrl=auto_exposure_max` |
| caption says "dark" or "black image" | `v4l2-ctl -d /dev/video0 --get-ctrl=exposure_mode,sensor_gain_mode` must both be 1; the narrator sets them unless `--v4l2-ctrls ''` |
| `vlm_prefill_ms` above ~7000 | frame is uploaded too large (`--max-width` above 1280) or the GPU is shared with a DeepStream preset; expected and demo-visible |
| RTSP source gives stale frames | the grabber drains 5 frames per cycle; raise it in `FrameSource.grab` if latency is still visible |

## 8. Files

| File | Purpose |
| --- | --- |
| `bringup_report.sh` | one-shot inventory of the camera's software stack |
| `bringup_report.txt` | the inventory from the bring-up unit (2026-10-09) |
| `setup_vlm.sh` | Ollama install, JetPack runner hint, model pull, smoke test |
| `vlm_narrator.py` | the agent: frame grab, VLM call, JSON parsing, snap telemetry and commands |
