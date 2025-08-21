# SOM-C350C5R-U9A1

- **Supplier:** Advantech
- **Arch:** amd64
- **Processor:** Intel 13th Gen Core (Raptor Lake)
- **AI acceleration:** Intel Iris Xe (integrated)
- **Form factor:** COM‑HPC Client Size C module (160 × 120 mm)
- **OS support:** Not specified (depends on BSP/carrier image)
- **Description:** High‑performance COM‑HPC module; supports QFCS 2.0 active cooler.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SOM-C350C5R-U9A1
- Buy on Newark: https://www.newark.com/search?st=SOM-C350C5R-U9A1

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
