# RSB-3720 (Pico-ITX)

- **Supplier:** Advantech
- **Arch:** arm64
- **Processor:** NXP i.MX8M Plus
- **AI acceleration:** Integrated NPU (~2.3 TOPS)
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.advantech.com/en-us/products/5912096e-f242-4b17-993a-1acdcaada6f6/rsb-3720/mod_d2f1b0bc-650b-449a-8ef7-b65ce4f69949

### OS images & docs
- eStore/Downloads: https://buy.advantech.com/Buy-Online/bymodel-RSB-3720.htm

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=RSB-3720%20%28Pico-ITX%29
- Buy on Newark: https://www.newark.com/search?st=RSB-3720%20%28Pico-ITX%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
