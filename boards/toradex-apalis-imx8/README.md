# Apalis i.MX8

- **Supplier:** Toradex
- **Arch:** arm64
- **Processor:** NXP i.MX8 (Apalis)
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=Apalis%20i.MX8
- Buy on Newark: https://www.newark.com/search?st=Apalis%20i.MX8

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
