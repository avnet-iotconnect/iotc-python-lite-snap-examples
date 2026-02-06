#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540"
LOGDIR="$ROOT/logs"
mkdir -p "$LOGDIR"

MODEL="${MODEL:-default}"
if [[ $# -gt 0 ]]; then
  MODEL="$1"
fi
if [[ "$MODEL" != "default" && "$MODEL" != "peoplenet" ]]; then
  echo "Usage: $0 [default|peoplenet]"
  exit 1
fi

# Start MQTT broker
sudo systemctl enable --now mosquitto

# Start IoTConnect socket (background)
# Avoid duplicate device connections
sudo snap stop iotconnect.socket >/dev/null 2>&1 || true

PIDS="$(pgrep -f "iotconnect.socket-debug" 2>/dev/null || true)"
if [[ -n "$PIDS" ]]; then
  if [[ "$(wc -w <<<"$PIDS")" -gt 1 ]]; then
    pkill -f "iotconnect.socket-debug" || true
    PIDS=""
  fi
fi

if [[ -z "$PIDS" ]]; then
  nohup snap run iotconnect.socket-debug >"$LOGDIR/iotconnect.socket.log" 2>&1 &
  echo $! > "$LOGDIR/iotconnect.socket.pid"
fi

# Start agent (background)
if ! pgrep -f "icam540_iotc_agent.py" >/dev/null 2>&1; then
  nohup "$ROOT/agent.sh" "$MODEL" >"$LOGDIR/agent.log" 2>&1 &
  echo $! > "$LOGDIR/agent.pid"
fi

# Start forwarder (background)
LABELS_OPT=()
if [[ -n "${FORWARDER_LABELS:-}" ]]; then
  LABELS_OPT=(--labels "$FORWARDER_LABELS")
elif [[ "$MODEL" == "peoplenet" ]]; then
  LABELS_OPT=(--labels "/opt/nvidia/deepstream/deepstream/samples/models/PeopleNet/labels.txt")
fi

if ! pgrep -f "mqtt_to_iotc_socket.py" >/dev/null 2>&1; then
  nohup "$ROOT/mqtt_to_iotc_socket.py" \
    --host localhost --port 1883 --topic icam540/ds \
    --did mclICAM540snap \
    --iotc-sock /home/icam-540/snap/iotconnect/common/iotc.sock \
    --min-interval 4 \
    "${LABELS_OPT[@]}" \
    >"$LOGDIR/forwarder.log" 2>&1 &
  echo $! > "$LOGDIR/forwarder.pid"
fi

echo "Started. Logs in $LOGDIR"
