# PD10EHI (mITX Thin)

- **Supplier:** Mitac
- **Arch:** amd64
- **Processor:** Intel Elkhart Lake
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://ipc.mitacmdt.com/IndustrialMotherboard_PD10EHI_PD10EHI

### OS images & docs
- Datasheet: https://download.mitacmct.com/Files/datasheets/motherboards/PD10EHI.pdf

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=PD10EHI%20%28mITX%20Thin%29
- Buy on Newark: https://www.newark.com/search?st=PD10EHI%20%28mITX%20Thin%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
