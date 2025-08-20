# ROM-5720 (SMARC)

- **Supplier:** Advantech
- **Arch:** arm64
- **Processor:** NXP i.MX8M Plus (SMARC)
- **AI acceleration:** Integrated NPU (~2.3 TOPS)
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.advantech.com/en-us/products/77b59009-31a9-4751-bee1-45827a844421/rom-5720/mod_4fbfe9fa-f5b2-4ba8-940e-e47585ad0fef

### OS images & docs
- Dev Kit: https://www.advantech.com/en-us/products/risc_evaluation_kit/rom-dk5720/mod_64c248c6-ede1-409b-a19e-59222a7f52da

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=ROM-5720%20%28SMARC%29
- Buy on Newark: https://www.newark.com/search?st=ROM-5720%20%28SMARC%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
