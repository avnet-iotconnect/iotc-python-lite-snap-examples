# SYS-2029BT-HNTASD3-PI021

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** 2U BigTwin 4‑node server
- **OS support:** Windows / Linux
- **Description:** HNTASD3 variant, all‑SSD third revision.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SYS-2029BT-HNTASD3-PI021
- Buy on Newark: https://www.newark.com/search?st=SYS-2029BT-HNTASD3-PI021

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
