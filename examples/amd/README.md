# Ryzen AI Playing Cards Demo (Ubuntu) — Flat Telemetry + ONNX Labels Autodetect

Turnkey **camera demo** that recognizes **playing cards** with a YOLO-style ONNX model
and sends **flat** telemetry to an IoTConnect socket (no arrays, no nested objects).
Defaults to **CPU** for reliability after reboot. Autodetects **class names from ONNX metadata**.

## Features
- **Flat telemetry only** (single-level JSON keys)
- **Labels autodetect** from ONNX metadata (`names`), with 1-based indexing handled automatically
- **CPU-only by default** for stability; you can change execution providers later
- Hotkeys: `q`/`Esc` quit, `r` reset unique set, `+`/`-` tweak confidence threshold

## Quick Start
```bash
git clone <your-fork-url>.git
cd ryzenai-cards-demo-gh

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r src/requirements.txt

cp src/iotc_config.example.json src/iotc_config.json
mkdir -p src/models

# Put your ONNX at: src/models/cards.onnx
# (optional) write labels.txt from model metadata if needed
python3 tools/extract_labels.py --model src/models/cards.onnx --out src/labels.txt

python3 src/card_demo.py --config src/iotc_config.json
