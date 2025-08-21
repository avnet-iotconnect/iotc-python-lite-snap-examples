# MS-98M3 (3.5")

- **Supplier:** MSI IPC
- **Arch:** amd64
- **Processor:** Intel Tiger Lake‑UP3
- **AI acceleration:** Intel Iris Xe GPU
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=MS-98M3%20%283.5%22%29
- Buy on Newark: https://www.newark.com/search?st=MS-98M3%20%283.5%22%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
