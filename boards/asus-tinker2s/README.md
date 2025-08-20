# Tinker Board 2S

- **Supplier:** ASUS IoT
- **Arch:** arm64
- **Processor:** Rockchip RK3399
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://tinker-board.asus.com/series/tinker-board-2s.html

### OS images & docs
- Downloads: https://tinker-board.asus.com/download-list.html?product=tinker-board-2s

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=Tinker%20Board%202S
- Buy on Newark: https://www.newark.com/search?st=Tinker%20Board%202S

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
