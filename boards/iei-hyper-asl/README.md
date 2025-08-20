# HYPER-ASL (Pico-ITX)

- **Supplier:** IEI
- **Arch:** amd64
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.ieiworld.com/en/product/model.php?II=1100

### OS images & docs
- Datasheet: https://www.ieiworld.com/_pdf/product/jp/1100.pdf

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=HYPER-ASL%20%28Pico-ITX%29
- Buy on Newark: https://www.newark.com/search?st=HYPER-ASL%20%28Pico-ITX%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps
- If the IoTConnect socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```