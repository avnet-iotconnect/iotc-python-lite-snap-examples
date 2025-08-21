# SYS-120C-TN10R-DC

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** Intel Xeon Scalable (Ice Lake/3rd Gen)
- **AI acceleration:** —
- **Form factor:** 1U rack server (DC power)
- **OS support:** Windows / Linux
- **Description:** SYS‑120C‑TN10R variant with DC PSUs.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SYS-120C-TN10R-DC
- Buy on Newark: https://www.newark.com/search?st=SYS-120C-TN10R-DC

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
