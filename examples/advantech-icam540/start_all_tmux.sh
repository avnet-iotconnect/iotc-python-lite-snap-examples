#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540"
SESSION="icam540"
MODEL="${MODEL:-default}"
if [[ $# -gt 0 ]]; then
  MODEL="$1"
fi
if [[ "$MODEL" != "default" && "$MODEL" != "peoplenet" ]]; then
  echo "Usage: $0 [default|peoplenet]"
  exit 1
fi

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux not found. Install with: sudo apt-get install -y tmux"
  exit 1
fi

# Start MQTT broker (requires sudo)
sudo systemctl enable --now mosquitto

# Avoid duplicate device connections
sudo snap stop iotconnect.socket >/dev/null 2>&1 || true

LABELS_OPT=""
if [[ -n "${FORWARDER_LABELS:-}" ]]; then
  LABELS_OPT="--labels ${FORWARDER_LABELS}"
elif [[ "$MODEL" == "peoplenet" ]]; then
  LABELS_OPT="--labels /opt/nvidia/deepstream/deepstream/samples/models/PeopleNet/labels.txt"
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Session '$SESSION' already running. Attaching..."
  tmux attach -t "$SESSION"
  exit 0
fi

# Create empty windows so the session stays alive even if a command exits.
tmux new-session -d -s "$SESSION" -n socket
tmux new-window -t "$SESSION" -n agent
tmux new-window -t "$SESSION" -n forwarder

# Launch commands inside each window.
tmux send-keys -t "$SESSION":socket "pkill -f iotconnect.socket-debug >/dev/null 2>&1 || true" C-m
tmux send-keys -t "$SESSION":socket "while true; do snap run iotconnect.socket-debug; echo \"[socket] exited, restarting in 2s\"; sleep 2; done" C-m

tmux send-keys -t "$SESSION":agent "$ROOT/agent.sh $MODEL" C-m

tmux send-keys -t "$SESSION":forwarder "$ROOT/mqtt_to_iotc_socket.py --host localhost --port 1883 --topic icam540/ds --did mclICAM540snap --iotc-sock /home/icam-540/snap/iotconnect/common/iotc.sock --min-interval 4 $LABELS_OPT" C-m

tmux select-window -t "$SESSION":0

echo "tmux session '$SESSION' started."
echo "Use Ctrl-b then d to detach."
echo "Reattach with: tmux attach -t $SESSION"

tmux attach -t "$SESSION"
