# Tinker Edge R

- **Supplier:** ASUS IoT
- **Arch:** arm64
- **Processor:** Rockchip RK3399Pro
- **AI acceleration:** Integrated NPU (~3 TOPS)
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=Tinker%20Edge%20R
- Buy on Newark: https://www.newark.com/search?st=Tinker%20Edge%20R

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
