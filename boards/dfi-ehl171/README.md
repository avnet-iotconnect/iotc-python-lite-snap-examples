# EHL171 (mITX)

- **Supplier:** DFI
- **Arch:** amd64
- **Processor:** Intel Elkhart Lake
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.dfi.com/product/index/1535

### OS images & docs
- (none)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=EHL171%20%28mITX%29
- Buy on Newark: https://www.newark.com/search?st=EHL171%20%28mITX%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
