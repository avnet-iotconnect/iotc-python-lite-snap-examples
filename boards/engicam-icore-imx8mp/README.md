# i.Core MX8M Plus SoM + carrier

- **Supplier:** Engicam
- **Arch:** arm64
- **Processor:** NXP i.MX8M Plus
- **AI acceleration:** Integrated NPU (~2.3 TOPS)
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=i.Core%20MX8M%20Plus%20SoM%20%2B%20carrier
- Buy on Newark: https://www.newark.com/search?st=i.Core%20MX8M%20Plus%20SoM%20%2B%20carrier

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
