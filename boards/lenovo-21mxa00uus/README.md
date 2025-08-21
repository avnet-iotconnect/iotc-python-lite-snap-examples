# 21MXA00UUS

- **Supplier:** LENOVO
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** Laptop (ThinkPad family)
- **OS support:** Windows 10/11 (Linux supported on many models)
- **Description:** ThinkPad system SKU; configuration/CPU/RAM/storage vary by build.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=21MXA00UUS
- Buy on Newark: https://www.newark.com/search?st=21MXA00UUS

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
