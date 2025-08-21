# 30BQS0E300

- **Supplier:** LENOVO
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** Desktop / Tiny / SFF (ThinkCentre/ThinkStation)
- **OS support:** Windows 10/11 (some Linux support)
- **Description:** Lenovo desktop/Tiny model SKU; configuration varies.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=30BQS0E300
- Buy on Newark: https://www.newark.com/search?st=30BQS0E300

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
