# MI989 (mITX)

- **Supplier:** iBASE
- **Arch:** amd64
- **Processor:** Intel 12th Gen Alder Lake‑S (LGA1700)
- **AI acceleration:** Intel UHD 770 GPU
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=MI989%20(mITX)
- Buy on Newark: https://www.newark.com/search?st=MI989%20(mITX)

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
