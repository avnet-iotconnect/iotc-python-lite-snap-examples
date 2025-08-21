# ET977 (COMe Type 6)

- **Supplier:** iBASE
- **Arch:** amd64
- **Processor:** Intel 12th/13th Gen Core (COMe Type 6)
- **AI acceleration:** Intel Iris Xe / UHD (varies)
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=ET977%20(COMe%20Type%206)
- Buy on Newark: https://www.newark.com/search?st=ET977%20(COMe%20Type%206)

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
