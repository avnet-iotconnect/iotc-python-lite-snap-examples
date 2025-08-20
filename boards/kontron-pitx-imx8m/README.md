# pITX-IMX8M

- **Supplier:** Kontron
- **Arch:** arm64
- **Processor:** NXP i.MX8M (Quad)
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.kontron.com/en/products/pitx-imx8m-quad-industry-/p160549

### OS images & docs
- Datasheet: https://www.kontron.com/downloads/datasheets/p/pitx-imx8m_datasheet.pdf?product=155258

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=pITX-IMX8M
- Buy on Newark: https://www.newark.com/search?st=pITX-IMX8M

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
