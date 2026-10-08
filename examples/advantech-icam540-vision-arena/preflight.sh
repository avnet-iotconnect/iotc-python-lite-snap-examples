#!/usr/bin/env bash
# Booth-morning checklist for the Vision Arena. Exit 0 = ready, 2 = something to fix.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DS="${DS_ROOT:-/opt/nvidia/deepstream/deepstream}"
ok=1
warn() { echo "  WARN: $*"; }
fail() { echo "  FAIL: $*"; ok=0; }
pass() { echo "  OK:   $*"; }

echo "[preflight] DeepStream"
command -v deepstream-app >/dev/null 2>&1 && pass "deepstream-app: $(deepstream-app --version 2>/dev/null | head -1 || echo found)" || fail "deepstream-app not in PATH"
[[ -f "$DS/lib/libnvds_mqtt_proto.so" ]] && pass "libnvds_mqtt_proto.so" || fail "missing $DS/lib/libnvds_mqtt_proto.so"
[[ -f "$DS/lib/libnvds_nvmultiobjecttracker.so" ]] && pass "libnvds_nvmultiobjecttracker.so" || fail "missing tracker library"
if command -v ldd >/dev/null 2>&1 && [[ -f "$DS/lib/libnvds_mqtt_proto.so" ]]; then
  missing="$(ldd "$DS/lib/libnvds_mqtt_proto.so" 2>/dev/null | awk '/not found/{print $1}')"
  [[ -z "$missing" ]] && pass "mqtt proto dependencies" || fail "missing libs: $missing  (sudo apt-get install -y libmosquitto1)"
fi
if command -v gst-inspect-1.0 >/dev/null 2>&1; then
  gst-inspect-1.0 nvdsanalytics >/dev/null 2>&1 && pass "nvdsanalytics plugin (zone/line overlay)" || warn "nvdsanalytics plugin not found; agent falls back to no overlay"
fi

echo "[preflight] Models"
[[ -f "$DS/samples/models/PeopleNet/resnet34_peoplenet_int8.onnx" ]] && pass "PeopleNet ONNX" || fail "PeopleNet ONNX missing under $DS/samples/models/PeopleNet"
[[ -f "$DS/samples/models/PeopleNet/labels.txt" ]] && pass "PeopleNet labels" || warn "PeopleNet labels.txt missing"
ls "$DS"/samples/models/PeopleNet/*.engine >/dev/null 2>&1 && pass "PeopleNet engine(s): $(ls "$DS"/samples/models/PeopleNet/*.engine | xargs -n1 basename | tr '\n' ' ')" || warn "no cached PeopleNet engine; first start builds one (minutes). Run: ./icam540_arena.py --warmup peoplenet:auto:1"
[[ -f "$DS/samples/configs/deepstream-app/config_infer_primary.txt" ]] && pass "ResNet10 infer config" || warn "ResNet10 config missing (set_model resnet10 unavailable)"

echo "[preflight] Sample streams for stress mode"
n=0
for f in "$DS"/samples/streams/*.mp4 "$DS"/samples/streams/*.mov; do [[ -f "$f" ]] && n=$((n+1)); done
[[ $n -gt 0 ]] && pass "$n sample video(s) in $DS/samples/streams" || warn "no sample videos; set_streams > 1 will fail (use --extra-stream)"

echo "[preflight] Camera"
if [[ -e /dev/video0 ]]; then
  pass "/dev/video0 present"
  for svc in web.service autoui.service; do
    systemctl is-active --quiet "$svc" 2>/dev/null && warn "$svc is running and may hold the camera (start_arena.sh stops it)"
  done
else
  fail "/dev/video0 missing (or pass --camera file:///path/to/clip.mp4 for a desk demo)"
fi

echo "[preflight] MQTT broker"
if timeout 2 bash -c ">/dev/tcp/localhost/1883" 2>/dev/null; then pass "broker reachable on localhost:1883"; else fail "no broker on localhost:1883 (sudo apt-get install -y mosquitto && sudo systemctl enable --now mosquitto)"; fi
python3 -c "import paho.mqtt.client" 2>/dev/null && pass "python paho-mqtt" || fail "python paho-mqtt missing (pip3 install paho-mqtt)"

echo "[preflight] Jetson metrics"
command -v tegrastats >/dev/null 2>&1 && pass "tegrastats" || warn "tegrastats not found; sysfs fallback (fewer GPU metrics)"
sudo -n true 2>/dev/null && pass "passwordless sudo (needed for deepstream-app/tegrastats)" || warn "sudo needs a password; run the agent with --no-sudo or configure NOPASSWD"

echo "[preflight] /IOTCONNECT snap"
command -v snap >/dev/null 2>&1 && snap list iotconnect >/dev/null 2>&1 && pass "iotconnect snap installed" || fail "iotconnect snap not installed (sudo snap install iotconnect)"
SOCK="$(ls "/home/${SUDO_USER:-$USER}/snap/iotconnect/common/iotc.sock" /var/snap/iotconnect/common/iotc.sock 2>/dev/null | head -1)"
[[ -n "$SOCK" ]] && pass "telemetry socket $SOCK" || warn "snap socket not running yet (start_arena.sh starts it)"

echo "[preflight] Files"
for f in icam540_arena.py config_infer_peoplenet_base.txt cfg_mqtt.txt zones.json; do
  [[ -f "$ROOT/$f" ]] && pass "$f" || fail "missing $ROOT/$f"
done

if [[ $ok -eq 1 ]]; then echo "[preflight] PASS"; exit 0; else echo "[preflight] FAIL"; exit 2; fi
