# Tinker Board 3N

- **Supplier:** ASUS IoT
- **Arch:** arm64
- **Processor:** Rockchip RK3568
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://tinker-board.asus.com/series/tinker-board-3N.html

### OS images & docs
- Debian Images: https://tinker-board.asus.com/download-list.html?product=tinker-board-3n

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=Tinker%20Board%203N
- Buy on Newark: https://www.newark.com/search?st=Tinker%20Board%203N

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.
- GPIO/UART overlays may be disabled by default; enable as needed.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
