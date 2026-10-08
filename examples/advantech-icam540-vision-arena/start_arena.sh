#!/usr/bin/env bash
# Start everything the Vision Arena needs: MQTT broker, /IOTCONNECT snap socket, agent.
# Usage: ./start_arena.sh [booth|stress|max] [extra agent args...]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR="$ROOT/logs"
mkdir -p "$LOGDIR"

PRESET="${PRESET:-booth}"
if [[ $# -gt 0 && "$1" != -* ]]; then
  PRESET="$1"
  shift
fi
case "$PRESET" in
  booth)  STREAMS=1 ;;
  stress) STREAMS=4 ;;
  max)    STREAMS=9 ;;
  *) echo "Usage: $0 [booth|stress|max] [agent args]"; exit 1 ;;
esac

# The iCAM-540 ships web UI services that hold the camera. Stop them if present.
for svc in web.service autoui.service; do
  if systemctl is-active --quiet "$svc" 2>/dev/null; then
    echo "[start] stopping $svc (holds /dev/video0)"
    sudo systemctl stop "$svc" || true
  fi
done

# MQTT broker for the DeepStream message sink
if command -v mosquitto >/dev/null 2>&1 || systemctl list-unit-files mosquitto.service >/dev/null 2>&1; then
  sudo systemctl enable --now mosquitto >/dev/null 2>&1 || true
fi

# /IOTCONNECT snap socket (one instance only, avoids duplicate device connections)
sudo snap stop iotconnect.socket >/dev/null 2>&1 || true
PIDS="$(pgrep -f "iotconnect.socket-debug" 2>/dev/null || true)"
if [[ -n "$PIDS" && "$(wc -w <<<"$PIDS")" -gt 1 ]]; then
  pkill -f "iotconnect.socket-debug" || true
  PIDS=""
fi
if [[ -z "$PIDS" ]]; then
  nohup snap run iotconnect.socket-debug >"$LOGDIR/iotconnect.socket.log" 2>&1 &
  echo $! > "$LOGDIR/iotconnect.socket.pid"
  echo "[start] snap socket started (log: $LOGDIR/iotconnect.socket.log)"
  sleep 2
fi

# Agent (auto-starts DeepStream)
if pgrep -f "icam540_arena.py" >/dev/null 2>&1; then
  echo "[start] agent already running"
else
  nohup "$ROOT/icam540_arena.py" --streams "$STREAMS" "$@" >"$LOGDIR/agent.log" 2>&1 &
  echo $! > "$LOGDIR/agent.pid"
  echo "[start] agent started with preset '$PRESET' (log: $LOGDIR/agent.log)"
fi

echo "[start] done. Watch: tail -f $LOGDIR/agent.log"
