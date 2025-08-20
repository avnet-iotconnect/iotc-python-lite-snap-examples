# pITX-APL

- **Supplier:** Kontron
- **Arch:** amd64
- **Processor:** Intel Apollo Lake
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.kontron.com/en/products/pitx-apl-e3940/p146763

### OS images & docs
- Datasheet: https://www.kontron.com/downloads/datasheets/p/pitx-apl_20190225_datasheet.pdf

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=pITX-APL
- Buy on Newark: https://www.newark.com/search?st=pITX-APL

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
