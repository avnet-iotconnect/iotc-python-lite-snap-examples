# Tinker Board 3N

- **Supplier:** ASUS IoT
- **Arch:** arm64
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://tinker-board.asus.com/series/tinker-board-3N.html

### OS images & docs
- Debian Images: https://tinker-board.asus.com/download-list.html?product=tinker-board-3n

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps
- If the IoTConnect socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```