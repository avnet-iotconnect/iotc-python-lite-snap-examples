# MC0014 - PIO-E100-12T-IA

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** Short‑depth embedded server (integration)
- **OS support:** Windows / Linux
- **Description:** Factory build of E100‑12T platform.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=MC0014%20-%20PIO-E100-12T-IA
- Buy on Newark: https://www.newark.com/search?st=MC0014%20-%20PIO-E100-12T-IA

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
