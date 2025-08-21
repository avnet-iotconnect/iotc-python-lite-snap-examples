# SYS-521AD-TN2

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** Intel Xeon
- **AI acceleration:** —
- **Form factor:** 1U rack server (Intel 4th/5th Gen Xeon)
- **OS support:** Windows / Linux
- **Description:** SYS‑521AD‑TN2 platform; next‑gen 1U with NVMe bays.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SYS-521AD-TN2
- Buy on Newark: https://www.newark.com/search?st=SYS-521AD-TN2

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
