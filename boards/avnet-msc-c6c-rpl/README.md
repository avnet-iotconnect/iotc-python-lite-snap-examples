# C6C-RPL (COMe Type 6)

- **Supplier:** Tria
- **Arch:** amd64
- **Processor:** Intel 13th Gen Core (Raptor Lake, COMe Type 6)
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=C6C-RPL%20%28COMe%20Type%206%29
- Buy on Newark: https://www.newark.com/search?st=C6C-RPL%20%28COMe%20Type%206%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
