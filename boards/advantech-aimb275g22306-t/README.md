# AIMB275G22306-T

- **Supplier:** Advantech
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** micro‑ATX industrial motherboard (AIMB‑275)
- **OS support:** Windows 10; Windows 7 (KBL‑S supports Win10 only)
- **Description:** Industrial micro‑ATX board; PCIe, multiple I/O; long‑life supply.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=AIMB275G22306-T
- Buy on Newark: https://www.newark.com/search?st=AIMB275G22306-T

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
