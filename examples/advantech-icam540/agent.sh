#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540"

MODEL="${MODEL:-default}"
if [[ $# -gt 0 && "$1" != -* ]]; then
  MODEL="$1"
  shift
fi

DEFAULT_CFG="${ROOT}/source1_icam540_v4l2_test_msg.txt"
PEOPLENET_CFG="${ROOT}/source1_icam540_peoplenet_tracker_rtsp_msg.txt"

case "$MODEL" in
  default) CFG="$DEFAULT_CFG" ;;
  peoplenet) CFG="$PEOPLENET_CFG" ;;
  *)
    echo "Unknown model '$MODEL'. Use 'default' or 'peoplenet'."
    exit 1
    ;;
esac

exec "${ROOT}/icam540_iotc_agent.py" \
  --did mclICAM540snap \
  --perf-interval 5 \
  --deepstream-config "$CFG" \
  --config-alias "default=${DEFAULT_CFG}" \
  --config-alias "peoplenet=${PEOPLENET_CFG}" \
  --deepstream-cmd "sudo deepstream-app" \
  --auto-start \
  "$@"
