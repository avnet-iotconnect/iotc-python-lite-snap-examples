# PIO-229BT-SR5-NODE-PI021

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** Intel Xeon Scalable
- **AI acceleration:** —
- **Form factor:** BigTwin node only (integration order)
- **OS support:** Windows / Linux
- **Description:** Factory node for 2029BT/229BT BigTwin chassis.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=PIO-229BT-SR5-NODE-PI021
- Buy on Newark: https://www.newark.com/search?st=PIO-229BT-SR5-NODE-PI021

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
