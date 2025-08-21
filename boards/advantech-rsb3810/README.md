# RSB-3810 (Pico-ITX)

- **Supplier:** Advantech
- **Arch:** arm64
- **Processor:** MediaTek Genio 1200
- **AI acceleration:** MediaTek APU (~4.8 TOPS)
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=RSB-3810%20%28Pico-ITX%29
- Buy on Newark: https://www.newark.com/search?st=RSB-3810%20%28Pico-ITX%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
