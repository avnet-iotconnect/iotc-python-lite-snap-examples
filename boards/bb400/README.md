# BB-400

- **Supplier:** Brainboxes
- **Arch:** armhf
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.brainboxes.com/product/industrial-edge-controller/bb-400

### OS images & docs
- Quick Start: https://www.brainboxes.com/files/catalog/product/BB/BB-400/documents/BB%20QSG%202019.pdf

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=BB-400
- Buy on Newark: https://www.newark.com/search?st=BB-400

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps
- If the IoTConnect socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```