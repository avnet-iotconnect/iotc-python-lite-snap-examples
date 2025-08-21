# AS-1115HS-TNR-OTO

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** AMD EPYC (dual‑socket HS series)
- **AI acceleration:** —
- **Form factor:** 1U/2U rack server
- **OS support:** Windows / Linux
- **Description:** Assembled system code.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=AS-1115HS-TNR-OTO
- Buy on Newark: https://www.newark.com/search?st=AS-1115HS-TNR-OTO

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
