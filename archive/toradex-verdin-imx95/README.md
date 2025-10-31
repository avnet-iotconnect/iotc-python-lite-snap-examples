# Verdin i.MX95 EVK

- **Supplier:** Toradex
- **Arch:** arm64
- **Processor:** NXP i.MX95 (Verdin)
- **AI acceleration:** Integrated NPU (Arm Ethos‑U85 class)
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=Verdin%20i.MX95%20EVK
- Buy on Newark: https://www.newark.com/search?st=Verdin%20i.MX95%20EVK

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
