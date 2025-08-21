# PIO-119C-EYED

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** 1U server (integration code)
- **OS support:** Windows / Linux
- **Description:** Factory build EYED variant for 119C chassis.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=PIO-119C-EYED
- Buy on Newark: https://www.newark.com/search?st=PIO-119C-EYED

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
