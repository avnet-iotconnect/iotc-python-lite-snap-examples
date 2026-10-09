#!/usr/bin/env bash
# Builds the AWS Kinesis Video Streams producer SDK with its GStreamer plugin (kvssink), installs the
# /IOTCONNECT lib for the device REST API, and installs kvs-stream.service.
#
#   ./install_kvs.sh                 # ~15-25 min the first time (C++ build, 1 job to spare the 8 GB)
#   ./kvs_stream.py --check          # verify the device is provisioned for Video Streaming
#   sudo systemctl start kvs-stream  # stream; journalctl -u kvs-stream -f
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
SDK=${KVS_SDK_DIR:-/opt/kvs-producer-sdk-cpp}
JOBS=${JOBS:-1}   # the build at -j3 drove the camera into swap next to the model server

sudo apt-get install -y -qq cmake git pkg-config m4 byacc curl libssl-dev libcurl4-openssl-dev liblog4cplus-dev \
  libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base-apps gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-tools
pip3 install --user -q iotconnect-lib

if [ ! -f "$SDK/build/libgstkvssink.so" ]; then
  echo "[kvs] building the producer SDK in $SDK with $JOBS job(s)"
  sudo mkdir -p "$SDK" && sudo chown "$(id -un)" "$SDK"
  [ -d "$SDK/.git" ] || git clone --depth 1 https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git "$SDK"
  mkdir -p "$SDK/build" && cd "$SDK/build"
  cmake .. -DBUILD_GSTREAMER_PLUGIN=ON -DBUILD_DEPENDENCIES=OFF -DBUILD_JNI=OFF -DBUILD_TEST=OFF -DCMAKE_BUILD_TYPE=Release   # system libcurl/openssl/log4cplus: lighter than building them
  nice -n 10 make -j"$JOBS"
  cd "$HERE"
fi
echo "$SDK/build" | sudo tee /etc/ld.so.conf.d/kvs-producer-sdk.conf >/dev/null && sudo ldconfig
PLUG=$(pkg-config --variable=pluginsdir gstreamer-1.0 2>/dev/null || echo /usr/lib/aarch64-linux-gnu/gstreamer-1.0)
sudo ln -sf "$SDK/build/libgstkvssink.so" "$PLUG/libgstkvssink.so"
printf 'export GST_PLUGIN_PATH=%s/build\n' "$SDK" | sudo tee /etc/profile.d/kvs-gstreamer.sh >/dev/null
gst-inspect-1.0 kvssink >/dev/null 2>&1 && echo "[kvs] kvssink OK" || { echo "[kvs] kvssink not found after build"; exit 1; }

sudo install -m 644 "$HERE/systemd/kvs-stream.service" /etc/systemd/system/kvs-stream.service
sudo sed -i "s#^WorkingDirectory=.*#WorkingDirectory=$HERE#; s#^User=.*#User=${SUDO_USER:-$(id -un)}#; s#^Environment=GST_PLUGIN_PATH=.*#Environment=GST_PLUGIN_PATH=$SDK/build#" /etc/systemd/system/kvs-stream.service
[ -f /etc/default/kvs-stream ] || sudo install -m 644 "$HERE/systemd/kvs-stream.env" /etc/default/kvs-stream
sudo systemctl daemon-reload
echo "[kvs] installed. Check provisioning:  ./kvs_stream.py --check   then:  sudo systemctl enable --now kvs-stream"
