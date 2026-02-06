#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540"
LOGDIR="$ROOT/logs"

kill_pid() {
  local pidfile="$1"
  if [[ -f "$pidfile" ]]; then
    local pid
    pid=$(cat "$pidfile" || true)
    if [[ -n "${pid}" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" || true
    fi
    rm -f "$pidfile"
  fi
}

kill_pid "$LOGDIR/forwarder.pid"
kill_pid "$LOGDIR/agent.pid"
kill_pid "$LOGDIR/iotconnect.socket.pid"

echo "Stopped (if running)."
