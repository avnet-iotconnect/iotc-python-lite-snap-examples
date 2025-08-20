# SMARC-sXEL

- **Supplier:** Kontron
- **Arch:** amd64
- **Processor:** Intel Elkhart Lake (SMARC)
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.kontron.com/en/products/smarc-sxel-j6426-4g-32g/p172682

### OS images & docs
- Datasheet: https://www.kontron.com/downloads/datasheets/s/smarc-sxel_datasheet.pdf?product=160517

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SMARC-sXEL
- Buy on Newark: https://www.newark.com/search?st=SMARC-sXEL

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
