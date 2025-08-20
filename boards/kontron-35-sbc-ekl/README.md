# 3.5"-SBC-EKL

- **Supplier:** Kontron
- **Arch:** amd64
- **Processor:** Intel Elkhart Lake (Atom x6000)
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.kontron.com/en/products/3.5--sbc-ekl/p162920

### OS images & docs
- User Guide: https://www.kontron.com/downloads/manuals/k/kontron-3d5-sbc-ekl-user-guide-rev-2d5-2025-02-03.pdf?product=174160

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=3.5%22-SBC-EKL
- Buy on Newark: https://www.newark.com/search?st=3.5%22-SBC-EKL

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
