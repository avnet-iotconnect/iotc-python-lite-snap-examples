# 99A5FC

- **Supplier:** INTEL
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** CPU (OEM tray code)
- **OS support:** OS‑dependent
- **Description:** Intel OEM/engineering part code; model determined by S‑Spec/stepping.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=99A5FC
- Buy on Newark: https://www.newark.com/search?st=99A5FC

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
