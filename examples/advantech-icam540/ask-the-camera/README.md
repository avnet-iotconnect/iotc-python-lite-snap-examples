# Ask the camera - a VLM narrator for the iCAM-540 on /IOTCONNECT

Status: **scaffold, not yet run on the camera.** The agent and scripts here were written against the published behaviour of Ollama, llama.cpp and the /IOTCONNECT snap, and the narrator was exercised locally against a stand-in endpoint. The next step is the bring-up on the real iCAM-540 (section 2).

## 1. What the demo does

A 2B-parameter vision-language model (VLM) runs on the camera's Jetson Orin NX next to the DeepStream pipeline from [advantech-icam540-vision-arena](../../advantech-icam540-vision-arena/). Every few seconds it looks at the current frame and publishes to /IOTCONNECT:

- `scene_caption`: one sentence describing the booth ("Two people are looking at the camera on the table, one is pointing at the screen").
- `people_vlm`, `engagement`, `unusual`: structured fields parsed from the model's JSON reply.
- `alert_1..3`: yes/no evaluation of plain-English rules a visitor types on the dashboard ("someone is wearing a hard hat", "a laptop is unattended").
- `question` / `answer`: a free-text question sent from the dashboard, answered against the latest frame.
- `vlm_latency_ms`, `vlm_tok_s`, token counts: the "how hard is the Orin working" numbers.

Talk track: show the live caption updating, type a question on the dashboard, then type an alert rule and have someone trigger it. Each round trip is a few seconds on an Orin NX 8GB with a 2B model.

```
 frame (RTSP from DeepStream, or /dev/video0) --> vlm_narrator.py --> OpenAI-compatible endpoint
                                                        |                (Ollama / llama-server)
                                                        v
                                          /IOTCONNECT snap  iotc.sock / iotc_cmd.sock
```

## 2. Bring-up on the camera (do this first)

```bash
git clone -b icam540-ask-the-camera https://github.com/avnet-iotconnect/iotc-python-lite-snap-examples.git
cd iotc-python-lite-snap-examples/examples/advantech-icam540/ask-the-camera
bash bringup_report.sh | tee bringup_report.txt
```

`bringup_report.txt` captures the BSP version, JetPack/L4T, DeepStream, power mode, memory, camera node, snap state and whether Ollama or llama.cpp is already present. Everything below depends on two lines of it: the L4T release (R35 = JetPack 5, R36 = JetPack 6) and free memory.

## 3. Install a VLM runtime

Default path, works on JetPack 5 and 6:

```bash
./setup_vlm.sh                # installs Ollama, pulls qwen3-vl:2b, smoke-tests it
ollama ps                     # must show 100% GPU; if it says CPU, see troubleshooting
```

Alternatives, in order of preference once JetPack is known:

| Runtime | When | Endpoint |
| --- | --- | --- |
| Ollama | simplest; official JetPack 5 and 6 support | `http://localhost:11434/v1` |
| llama.cpp `llama-server --mmproj` | lowest memory, fastest to first token on 8 GB | `http://localhost:8080/v1` |
| TensorRT Edge-LLM | NVIDIA's own runtime, best decode speed; JetPack 6.2+ only, engine export on an x86 host | its OpenAI-compatible server |

Model choice: `qwen3-vl:2b` first. `gemma3:4b` or Gemma 4 E2B as the "newest model" alternative if memory allows. Keep `max_tokens` around 120; the dashboard only needs a sentence.

## 4. Run the narrator

Desk test without the camera, against any image:

```bash
./vlm_narrator.py --source file:///path/to/photo.jpg --once
```

On the camera, next to the Vision Arena (which owns `/dev/video0`), take frames from DeepStream's RTSP output:

```bash
# in the arena folder: start with the RTSP sink enabled
./start_arena.sh booth --display both
# here:
./vlm_narrator.py --source rtsp://127.0.0.1:8554/ds-test --interval 8 --print-telemetry
```

Without the arena, read the camera directly: `--source v4l2:/dev/video0` (stop `web.service` and `autoui.service` first, they hold the sensor).

Options: `--endpoint`, `--model`, `--interval`, `--max-tokens`, `--max-width` (frame is downscaled before upload, 640 px is plenty for a 2B model), `--alert "<rule>"` (repeatable), `--paused`.

## 5. Commands and telemetry

Commands arrive on the snap command socket, as JSON `{"name": "ask", "args": ["is anyone wearing red"], "ack_id": "..."}` or plain text `ask is anyone wearing red`.

| Command | Effect |
| --- | --- |
| `ask <question>` | one-shot answer about the latest frame, published as `question` / `answer` |
| `set_alert <rule>` | add a yes/no rule (max 3), evaluated every cycle into `alert_1..3` |
| `clear_alerts` | remove all rules |
| `set_interval <s>` | seconds between cycles (min 2) |
| `set_model <tag>` | switch model on the endpoint |
| `set_max_tokens <n>` | |
| `pause` / `resume` / `status` / `ping` | |

Telemetry is one flat JSON object per cycle (and after each `ask`): `type=vlm`, `vlm_state`, `vlm_model`, `scene_caption`, `people_vlm`, `engagement`, `unusual`, `question`, `answer`, `alert_rules`, `alerts_active`, `alert_text`, `alert_1`, `alert_2`, `alert_3`, `vlm_latency_ms`, `vlm_tok_s`, `vlm_prompt_tokens`, `vlm_completion_tokens`, `vlm_cycle`, `message`.

Device template and dashboard widgets for these attributes are the next item once the bring-up confirms the stack (they will be added to the arena's template so one device carries both demos).

## 6. Memory budget on the 8 GB Orin NX

Rough expectations, to be measured during bring-up:

| Component | Memory |
| --- | --- |
| Ubuntu desktop + snap + agent | ~1.5 GB |
| DeepStream PeopleNet, 1 stream, tracker | ~1.5 to 2 GB |
| qwen3-vl:2b in Ollama (Q4, 2k context) | ~3 to 3.5 GB |

That fits in booth mode. It does not fit with 9 DeepStream streams, so pause the narrator before `preset max` (the arena agent will get an automatic hook for this once both run on the device). If memory is tight, drop the desktop (`sudo systemctl set-default multi-user.target`) and run the display sink only.

## 7. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ollama ps` shows CPU | `sudo systemctl edit ollama` and set `JETSON_JETPACK=5` or `6` to match the L4T release, then restart; `journalctl -u ollama` shows which CUDA runner loaded |
| first cycle takes 30 s+ | model load; `OLLAMA_KEEP_ALIVE=-1` (set by `setup_vlm.sh`) keeps it resident |
| `vlm_state=error`, "endpoint unreachable" | `curl localhost:11434/v1/models` |
| caption is empty, `scene_caption` holds raw text | the model did not return JSON; lower temperature is already set, try `set_max_tokens 200` or a different model |
| RTSP source gives stale frames | the grabber drains 5 frames per cycle; raise it in `FrameSource.grab` if latency is still visible |
| GPU contention drops DeepStream FPS during a cycle | expected and demo-visible; lengthen `--interval` or lower `--max-width` |

## 8. Files

| File | Purpose |
| --- | --- |
| `bringup_report.sh` | one-shot inventory of the camera's software stack |
| `setup_vlm.sh` | Ollama install, JetPack runner hint, model pull, smoke test |
| `vlm_narrator.py` | the agent: frame grab, VLM call, JSON parsing, snap telemetry and commands |
