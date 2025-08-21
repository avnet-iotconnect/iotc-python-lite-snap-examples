# PK8071305120102S

- **Supplier:** INTEL
- **Arch:** amd64
- **Processor:** Intel Xeon
- **AI acceleration:** —
- **Form factor:** CPU (Xeon)
- **OS support:** OS‑dependent
- **Description:** Packaged CPU; S‑Spec RMGF.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=PK8071305120102S
- Buy on Newark: https://www.newark.com/search?st=PK8071305120102S

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
