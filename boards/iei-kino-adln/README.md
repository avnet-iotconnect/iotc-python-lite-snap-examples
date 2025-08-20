# KINO-ADLN (mITX)

- **Supplier:** IEI
- **Arch:** amd64
- **Processor:** Intel Alder Lake‑N
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.ieiworld.com/en/product/model.php?II=1053

### OS images & docs
- Downloads: https://download.ieiworld.com/?model=KINO-ADL-N

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=KINO-ADLN%20%28mITX%29
- Buy on Newark: https://www.newark.com/search?st=KINO-ADLN%20%28mITX%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.
- Disable Secure Boot on some BIOS versions to ease Ubuntu installs.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
