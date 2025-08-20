# ROM-5620 (SMARC)

- **Supplier:** Advantech
- **Arch:** arm64
- **Processor:** NXP i.MX8M Mini/Nano (SMARC)
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.advantech.com/en/products/77b59009-31a9-4751-bee1-45827a844421/rom-5620/mod_af8aa75b-54fb-4890-8ea6-a927fe0ea2e1

### OS images & docs
- Datasheet: https://advdownload.advantech.com/productfile/PIS/ROM-5620/file/ROM-5620_DS%28061622%2920220616202643.pdf

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=ROM-5620%20%28SMARC%29
- Buy on Newark: https://www.newark.com/search?st=ROM-5620%20%28SMARC%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
