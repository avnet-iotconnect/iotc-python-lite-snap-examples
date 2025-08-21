# 621C-TN12R-OTO

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** Intel Xeon Scalable
- **AI acceleration:** —
- **Form factor:** 2U rack server (integration code)
- **OS support:** Windows / Linux
- **Description:** Supermicro 621C‑TN12R pre‑integrated configuration.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=621C-TN12R-OTO
- Buy on Newark: https://www.newark.com/search?st=621C-TN12R-OTO

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
