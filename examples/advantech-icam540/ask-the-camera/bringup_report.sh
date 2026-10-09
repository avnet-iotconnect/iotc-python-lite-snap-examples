#!/usr/bin/env bash
# Collects everything needed to plan the VLM demo on this iCAM-540.
# Run on the camera:  bash bringup_report.sh | tee bringup_report.txt
# Paste the output back into the planning session (nothing here is secret).
set -uo pipefail

section() { echo; echo "=== $1"; }
try() { "$@" 2>&1 || echo "(not available: $*)"; }

section "Identity"
hostname
try cat /opt/version
try cat /etc/nv_tegra_release
try cat /etc/os-release | grep -E "^(PRETTY_NAME|VERSION_ID)="
uname -r
try cat /proc/device-tree/model | tr -d '\0'; echo

section "JetPack / CUDA / TensorRT"
try dpkg -l | grep -E "nvidia-jetpack |nvidia-l4t-core|nvidia-cuda |nvidia-tensorrt |tensorrt " | awk '{print $2, $3}'
try /usr/local/cuda/bin/nvcc --version | tail -1
try dpkg -l | grep -E "^ii +libnvinfer[0-9]* " | awk '{print $2, $3}'

section "DeepStream"
try deepstream-app --version
ls -d /opt/nvidia/deepstream/deepstream* 2>/dev/null
ls /opt/nvidia/deepstream/deepstream/samples/models/ 2>/dev/null
ls /opt/nvidia/deepstream/deepstream/samples/models/PeopleNet/ 2>/dev/null
ls /opt/nvidia/deepstream/deepstream/samples/streams/ 2>/dev/null | head -20
try ls /opt/nvidia/deepstream/deepstream/lib/libnvds_mqtt_proto.so
try gst-inspect-1.0 nvdsanalytics | head -3

section "Power and thermals"
try sudo -n nvpmodel -q
try sudo -n nvpmodel -p --verbose | head -40
try timeout 3 sudo -n tegrastats --interval 1000 | head -2

section "Memory and storage"
free -h
df -h / /home 2>/dev/null
try zramctl
swapon --show

section "Camera"
ls -l /dev/video* 2>/dev/null
try v4l2-ctl --list-devices
try v4l2-ctl -d /dev/video0 --list-formats-ext | head -40
systemctl is-active web.service autoui.service 2>/dev/null | paste - - | sed 's/^/web.service autoui.service: /'

section "Containers and Python"
try docker --version
try docker info 2>/dev/null | grep -i -A3 "Runtimes"
python3 --version
try python3 -c "import cv2; print('cv2', cv2.__version__)"
try python3 -c "import paho.mqtt; print('paho-mqtt', paho.mqtt.__version__)"
try pip3 --version

section "LLM runtimes already present"
try ollama --version
try ls -d ~/llama.cpp ~/jetson-containers /opt/llama.cpp 2>/dev/null
try which llama-server llama-mtmd-cli

section "/IOTCONNECT snap"
try snap list iotconnect
try snap services iotconnect
ls -l /var/snap/iotconnect/common/*.sock /home/*/snap/iotconnect/common/*.sock 2>/dev/null

section "Network"
ip -4 -brief addr
try getent hosts github.com | head -1

section "Display"
echo "DISPLAY=${DISPLAY:-unset}"
try loginctl list-sessions --no-legend
echo
echo "=== done"
