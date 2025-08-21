# PIO-119C-HRTS

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** 1U server (HRTS variant)
- **OS support:** Windows / Linux
- **Description:** Factory integration for 119C HRTS.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=PIO-119C-HRTS
- Buy on Newark: https://www.newark.com/search?st=PIO-119C-HRTS

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
