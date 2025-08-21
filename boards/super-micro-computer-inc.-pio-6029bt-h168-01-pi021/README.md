# PIO-6029BT-H168-01-PI021

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** x86 (Intel Xeon Scalable, 2‑node)
- **AI acceleration:** —
- **Form factor:** 2U BigTwin node (integration order)
- **OS support:** Windows / Linux
- **Description:** PIO build for SYS‑2029BT/6029BT BigTwin platform.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=PIO-6029BT-H168-01-PI021
- Buy on Newark: https://www.newark.com/search?st=PIO-6029BT-H168-01-PI021

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
