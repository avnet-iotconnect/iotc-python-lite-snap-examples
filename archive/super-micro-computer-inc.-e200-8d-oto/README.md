# E200-8D-OTO

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** Intel Xeon D‑1518/D‑1528 (SoC)
- **AI acceleration:** —
- **Form factor:** Short‑depth mini‑server
- **OS support:** Windows Server / Linux
- **Description:** SuperServer E200‑8D integrated build.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=E200-8D-OTO
- Buy on Newark: https://www.newark.com/search?st=E200-8D-OTO

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
