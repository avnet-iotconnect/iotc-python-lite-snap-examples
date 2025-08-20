# RSB-3810 (Pico-ITX)

- **Supplier:** Advantech
- **Arch:** arm64
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.advantech.com/en-us/products/5912096e-f242-4b17-993a-1acdcaada6f6/rsb-3810/mod_5e027854-f47d-45e5-bac2-0413929f345d

### OS images & docs
- Ubuntu Certification: https://canonical.com/blog/advantech-rsb-3810-mediatek-genio-ubuntu-certified

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=RSB-3810%20%28Pico-ITX%29
- Buy on Newark: https://www.newark.com/search?st=RSB-3810%20%28Pico-ITX%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps
- If the IoTConnect socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```