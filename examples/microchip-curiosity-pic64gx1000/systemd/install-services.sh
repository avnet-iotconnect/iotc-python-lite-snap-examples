#!/usr/bin/env bash
# Install the PIC64GX1000 example services so the PHT and vision applications
# both start at boot and publish through the same /IOTCONNECT socket bridge.
#
#   sudo ./install-services.sh
#
# Re-running is safe. An existing /etc/default/iotc-examples is left alone so
# local edits survive; delete it first if you want the detected defaults back.
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "This script must run as root: sudo $0" >&2
  exit 1
fi

UNIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${UNIT_DIR}/../applications" && pwd)"
RUN_USER="${SUDO_USER:-ubuntu}"
RUN_HOME="$(getent passwd "${RUN_USER}" | cut -d: -f6)"
ENV_FILE=/etc/default/iotc-examples
SNAP_COMMON=/var/snap/iotconnect/common
USER_COMMON="${RUN_HOME}/snap/iotconnect/common"

echo "user:        ${RUN_USER}"
echo "application: ${APP_DIR}"

# --- 1. Device credentials must be readable by the root bridge ---------------
# Only a root bridge can start at boot, and it reads its configuration from
# $SNAP_COMMON. A device provisioned unprivileged has it under ~/snap instead.
if [[ ! -f "${SNAP_COMMON}/iotcDeviceConfig.json" ]]; then
  if [[ -f "${USER_COMMON}/iotcDeviceConfig.json" ]]; then
    echo "Copying device credentials from ${USER_COMMON} to ${SNAP_COMMON}"
    install -d -m 755 "${SNAP_COMMON}"
    for f in iotcDeviceConfig.json device-cert.pem device-pkey.pem; do
      [[ -f "${USER_COMMON}/${f}" ]] && install -m 600 "${USER_COMMON}/${f}" "${SNAP_COMMON}/${f}"
    done
  else
    echo "No device configuration found in ${SNAP_COMMON} or ${USER_COMMON}." >&2
    echo "Provision the device first:  sudo snap run iotconnect.setup" >&2
    exit 2
  fi
fi

# --- 2. Bridge starts at boot ------------------------------------------------
echo "Enabling the /IOTCONNECT socket bridge"
snap start --enable iotconnect.socket

# --- 3. Environment file -----------------------------------------------------
if [[ -f "${ENV_FILE}" ]]; then
  echo "Keeping existing ${ENV_FILE}"
else
  VISION_PYTHON=/usr/bin/python3
  [[ -x "${RUN_HOME}/iotc-vision-venv/bin/python3" ]] && VISION_PYTHON="${RUN_HOME}/iotc-vision-venv/bin/python3"

  # The default model is the HOG person detector, so prefer a clip that
  # actually contains people over whatever sorts first in the home directory.
  VISION_SOURCE=""
  for pattern in '*ppl*.mp4' '*people*.mp4' '*person*.mp4' '*walk*.mp4' '*.mp4'; do
    for candidate in "${RUN_HOME}"/${pattern}; do
      [[ -f "${candidate}" ]] && VISION_SOURCE="${candidate}" && break 2
    done
  done
  if [[ -z "${VISION_SOURCE}" ]]; then
    if [[ -e /dev/video0 ]]; then
      VISION_SOURCE=0
    else
      VISION_SOURCE="${RUN_HOME}/ppl-walking-640x360-5fps.mp4"
      echo "WARNING: no video file or camera found; set VISION_SOURCE in ${ENV_FILE}" >&2
    fi
  fi

  echo "Writing ${ENV_FILE}"
  sed -e "s|^VISION_PYTHON=.*|VISION_PYTHON=${VISION_PYTHON}|" \
      -e "s|^VISION_SOURCE=.*|VISION_SOURCE=${VISION_SOURCE}|" \
      "${UNIT_DIR}/iotc-examples.env" > "${ENV_FILE}"
  chmod 644 "${ENV_FILE}"
  echo "  VISION_PYTHON=${VISION_PYTHON}"
  echo "  VISION_SOURCE=${VISION_SOURCE}"
fi

# --- 4. Units ----------------------------------------------------------------
for unit in iotc-pht.service iotc-vision.service; do
  echo "Installing ${unit}"
  sed -e "s|^User=.*|User=${RUN_USER}|" \
      -e "s|^Group=.*|Group=${RUN_USER}|" \
      -e "s|^WorkingDirectory=.*|WorkingDirectory=${APP_DIR}|" \
      "${UNIT_DIR}/${unit}" > "/etc/systemd/system/${unit}"
  chmod 644 "/etc/systemd/system/${unit}"
done

systemctl daemon-reload
systemctl enable --now iotc-pht.service iotc-vision.service

echo
systemctl --no-pager --lines=0 status iotc-pht.service iotc-vision.service || true
echo
echo "Both services are enabled and will start at boot."
echo "  journalctl -u iotc-pht.service -u iotc-vision.service -f"
echo "  http://\$(hostname -I | awk '{print \$1}'):8080/"
