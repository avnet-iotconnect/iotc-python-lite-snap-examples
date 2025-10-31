# Verdin i.MX8M Plus

- **Supplier:** Toradex
- **Arch:** arm64
- **Processor:** NXP i.MX8M Plus (Verdin)
- **AI acceleration:** Integrated NPU (~2.3 TOPS)
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=Verdin%20i.MX8M%20Plus
- Buy on Newark: https://www.newark.com/search?st=Verdin%20i.MX8M%20Plus

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
