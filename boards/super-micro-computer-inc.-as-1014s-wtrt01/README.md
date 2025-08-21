# AS -1014S-WTRT01

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** AMD EPYC 7002 (Rome)
- **AI acceleration:** —
- **Form factor:** 1U rack server
- **OS support:** Windows / Linux
- **Description:** AS‑1014S‑WTRT: 1U with 10×2.5" bays; NVMe‑ready.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=AS%20-1014S-WTRT01
- Buy on Newark: https://www.newark.com/search?st=AS%20-1014S-WTRT01

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
