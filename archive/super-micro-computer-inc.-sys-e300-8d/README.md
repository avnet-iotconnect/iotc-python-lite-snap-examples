# SYS-E300-8D

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** Intel Xeon D‑1500 series
- **AI acceleration:** —
- **Form factor:** Short‑depth mini‑server
- **OS support:** Windows / Linux
- **Description:** SuperServer E300‑8D build (variant 04).
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SYS-E300-8D
- Buy on Newark: https://www.newark.com/search?st=SYS-E300-8D

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
