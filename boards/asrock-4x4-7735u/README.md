# 4X4 BOX-7735U

- **Supplier:** ASRock Industrial
- **Arch:** amd64
- **Processor:** AMD Ryzen 7 7735U
- **AI acceleration:** Radeon 680M (RDNA2)
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.asrockind.com/en-gb/4X4%20BOX-7735U/D5

### OS images & docs
- (none)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=4X4%20BOX-7735U
- Buy on Newark: https://www.newark.com/search?st=4X4%20BOX-7735U

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
