# SM2S-EL (SMARC)

- **Supplier:** Tria
- **Arch:** amd64
- **Processor:** Intel Elkhart Lake (SMARC)
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SM2S-EL%20%28SMARC%29
- Buy on Newark: https://www.newark.com/search?st=SM2S-EL%20%28SMARC%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
