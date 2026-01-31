# AS-1114S-WN10T

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** AMD EPYC (single‑socket)
- **AI acceleration:** —
- **Form factor:** 1U rack server (10× NVMe)
- **OS support:** Windows / Linux
- **Description:** AS‑1114S‑WN10T platform, QC‑verified build.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=AS-1114S-WN10T
- Buy on Newark: https://www.newark.com/search?st=AS-1114S-WN10T

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
