# SOM-9461ES0C-MA2E

- **Supplier:** Advantech
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** Computer‑on‑Module (Compact COM‑Express‑class SOM)
- **Description:** Low‑power SOM intended for embedded designs/carrier boards.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page:  https://www.avnet.com/americas/product/advantech/som-9461es0c-ma2e/evolve-56577168/

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SOM-9461ES0C-MA2E
- Buy on Newark: https://www.newark.com/search?st=SOM-9461ES0C-MA2E

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
