# AS-2114S-WN24RT-OTO

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** AMD EPYC (single‑socket)
- **AI acceleration:** —
- **Form factor:** 2U rack server (24× NVMe)
- **OS support:** Windows / Linux
- **Description:** AS‑2114S‑WN24RT: 2U with 24x hot‑swap NVMe.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=AS-2114S-WN24RT-OTO
- Buy on Newark: https://www.newark.com/search?st=AS-2114S-WN24RT-OTO

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
