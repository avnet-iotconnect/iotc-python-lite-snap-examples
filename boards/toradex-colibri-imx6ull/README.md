# Colibri iMX6ULL

- **Supplier:** Toradex
- **Arch:** armhf
- **Processor:** NXP i.MX6ULL (Colibri)
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.toradex.com/computer-on-modules/colibri-arm-family/nxp-imx6ull

### OS images & docs
- Developer: https://developer.toradex.com/hardware/colibri-som-family/modules/colibri-imx6ull/

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=Colibri%20iMX6ULL
- Buy on Newark: https://www.newark.com/search?st=Colibri%20iMX6ULL

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
