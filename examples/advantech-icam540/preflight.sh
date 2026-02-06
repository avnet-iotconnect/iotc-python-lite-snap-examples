#!/usr/bin/env bash
set -euo pipefail

CFG="/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/source1_icam540_v4l2_test_msg.txt"
MSGCONV="/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/dstest5_msgconv_sample_config.txt"
MQTT_CFG="/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/cfg_mqtt.txt"
PROTO="/opt/nvidia/deepstream/deepstream/lib/libnvds_mqtt_proto.so"
INFER_CFG="/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_infer_primary.txt"
ENGINE="/opt/nvidia/deepstream/deepstream/samples/models/Primary_Detector/resnet10.caffemodel_b1_gpu0_int8.engine"

ok=1

echo "[preflight] checking files..."
for f in "$CFG" "$MSGCONV" "$MQTT_CFG" "$PROTO" "$INFER_CFG" "$ENGINE"; do
  if [[ ! -f "$f" ]]; then
    echo "  MISSING: $f"
    ok=0
  else
    echo "  OK: $f"
  fi
done

echo "[preflight] checking mqtt proto dependencies..."
if command -v ldd >/dev/null 2>&1; then
  missing=$(ldd "$PROTO" 2>/dev/null | awk '/not found/{print $1}')
  if [[ -n "$missing" ]]; then
    echo "  MISSING LIBS:"
    echo "$missing" | sed 's/^/   - /'
    echo "  Hint: sudo apt-get install -y libmosquitto1"
    ok=0
  else
    echo "  OK: all dependencies found"
  fi
else
  echo "  WARN: ldd not found; skipping dependency check"
fi

echo "[preflight] checking MQTT broker reachability..."
HOST="localhost"
PORT="1883"
if grep -q "msg-broker-conn-str" "$CFG"; then
  conn=$(grep -m1 "msg-broker-conn-str" "$CFG" | awk -F= '{print $2}' | tr -d ' ')
  host=$(echo "$conn" | awk -F';' '{print $1}')
  port=$(echo "$conn" | awk -F';' '{print $2}')
  if [[ -n "$host" ]]; then HOST="$host"; fi
  if [[ -n "$port" ]]; then PORT="$port"; fi
fi
if timeout 2 bash -c ">/dev/tcp/$HOST/$PORT" 2>/dev/null; then
  echo "  OK: broker reachable at $HOST:$PORT"
else
  echo "  FAIL: broker not reachable at $HOST:$PORT"
  ok=0
fi

echo "[preflight] checking IoTConnect socket..."
SOCK="/home/${USER:-icam-540}/snap/iotconnect/common/iotc.sock"
if [[ -S "$SOCK" ]]; then
  echo "  OK: $SOCK"
else
  echo "  WARN: $SOCK not found (socket may not be running)"
fi

if [[ "$ok" -eq 1 ]]; then
  echo "[preflight] PASS"
  exit 0
else
  echo "[preflight] FAIL"
  exit 2
fi
