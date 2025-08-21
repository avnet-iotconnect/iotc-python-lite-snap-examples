# 38034-0000-27-7US1

- **Supplier:** Kontron
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** Industrial computer / assembly code
- **OS support:** Windows / Linux (by image)
- **Description:** Kontron assembly/kit code; public spec not found.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=38034-0000-27-7US1
- Buy on Newark: https://www.newark.com/search?st=38034-0000-27-7US1

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
