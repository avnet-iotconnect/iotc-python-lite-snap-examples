# Verdin i.MX95 EVK

- **Supplier:** Toradex
- **Arch:** arm64
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.toradex.com/computer-on-modules/verdin-arm-family/nxp-imx95-evaluation-kit

### OS images & docs
- Torizon downloads: https://developer.toradex.com/software/toradex-embedded-software/toradex-download-links-torizon-linux-bsp-wince-and-partner-demos/

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps
- If the IoTConnect socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```