# SM2S-IMX95 + SMARC base

- **Supplier:** Tria
- **Arch:** arm64
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://embedded.avnet.com/product/msc-sm2s-imx95/

### OS images & docs
- (none)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SM2S-IMX95%20%2B%20SMARC%20base
- Buy on Newark: https://www.newark.com/search?st=SM2S-IMX95%20%2B%20SMARC%20base

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```