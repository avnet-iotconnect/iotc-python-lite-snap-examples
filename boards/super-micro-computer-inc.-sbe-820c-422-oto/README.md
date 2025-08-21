# SBE-820C-422-OTO

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** SBE platform (integration code)
- **OS support:** Windows / Linux
- **Description:** SBE 820C build; details depend on BOM.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SBE-820C-422-OTO
- Buy on Newark: https://www.newark.com/search?st=SBE-820C-422-OTO

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
