#!/usr/bin/env bash
# Installs Ollama on the iCAM-540 and pulls the default VLM for the demo.
# Works on JetPack 5 and 6 (Ollama ships CUDA runners for both; it needs the
# JETSON_JETPACK hint to pick the right one on some images).
#
#   ./setup_vlm.sh                 # Ollama + qwen3-vl:2b-instruct
#   ./setup_vlm.sh gemma3:4b       # a different model tag
#
# Not yet validated on the camera: run it, then paste the output back.
set -euo pipefail

MODEL="${1:-qwen3-vl:2b-instruct}"   # the plain :2b tag is the thinking variant and spends its whole token budget reasoning

if grep -q "R36" /etc/nv_tegra_release 2>/dev/null; then JP=6; else JP=5; fi
echo "[setup] detected JetPack major version: $JP"

if ! command -v ollama >/dev/null 2>&1; then
  echo "[setup] installing Ollama"
  curl -fsSL https://ollama.com/install.sh | sh
fi

# Make the systemd service pick the right CUDA runner and keep the model loaded.
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/jetson.conf >/dev/null <<EOF
[Service]
Environment="JETSON_JETPACK=${JP}"
Environment="OLLAMA_KEEP_ALIVE=-1"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
# The narrator sends ~1250 prompt tokens and asks for 120; the 4096 default wastes KV-cache memory on an 8 GB board.
Environment="OLLAMA_CONTEXT_LENGTH=2048"
# RAM is shared with the GPU. Keep the OOM killer away from the model server (it is the largest process,
# so it is the default victim); a browser tab on the desktop dies first instead.
OOMScoreAdjust=-900
# llama-server keeps a RAM cache of recent prompts (~135 MB of KV per image prompt) up to an 8 GB default cap;
# with a new image every cycle it grew the runner from 1 GB to 3.2 GB and OOM-killed the box. Off.
Environment="LLAMA_ARG_CACHE_RAM=0"
EOF
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl restart ollama   # the installer already started it; restart so the drop-in env applies
sleep 3

echo "[setup] pulling $MODEL (several GB; needs the network)"
ollama pull "$MODEL"

echo "[setup] smoke test"
export OLLAMA_KEEP_ALIVE=-1    # the CLI sends its own keep_alive; keep the model resident like the agent does
ollama run "$MODEL" "Reply with the single word READY." --verbose 2>&1 | tail -8
echo
echo "[setup] confirm the GPU is in use (expect '100% GPU' in the PROCESSOR column):"
ollama ps
echo
echo "[setup] endpoint for vlm_narrator.py: http://localhost:11434/v1  model: $MODEL"
