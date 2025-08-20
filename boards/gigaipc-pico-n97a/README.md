# PICO-N97A

- **Supplier:** GIGAIPC
- **Arch:** amd64
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.gigaipc.com/en/products-detail/pico-N97A/

### OS images & docs
- Datasheet: https://gigaipc-download-bucket.s3.ap-northeast-1.amazonaws.com/Datasheet%2C%2Buser%2Bmanual%2C%2Bproduct%2Bphoto/Boards/Pico%2BSeries/Pico-N97A/PICO-N97A_20241231.pdf

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps
- If the IoTConnect socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```