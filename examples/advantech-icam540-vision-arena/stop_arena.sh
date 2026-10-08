#!/usr/bin/env bash
# Stop the agent (which stops DeepStream) and the snap socket started by start_arena.sh.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR="$ROOT/logs"

kill_pid() {
  local pidfile="$1"
  if [[ -f "$pidfile" ]]; then
    local pid
    pid="$(cat "$pidfile" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" || true
      for _ in 1 2 3 4 5 6 7 8 9 10; do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
      done
    fi
    rm -f "$pidfile"
  fi
}

kill_pid "$LOGDIR/agent.pid"
pkill -f "icam540_arena.py" 2>/dev/null || true
# deepstream-app runs under sudo; make sure it is gone too
sudo pkill -f "deepstream-app -c $ROOT/generated/deepstream_arena.txt" 2>/dev/null || true
sudo tegrastats --stop >/dev/null 2>&1 || true
kill_pid "$LOGDIR/iotconnect.socket.pid"

echo "Stopped (if running)."
