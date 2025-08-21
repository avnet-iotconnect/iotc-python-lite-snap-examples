# SSG-947HE1C

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** 4U high‑density storage server (SSG‑947)
- **OS support:** Windows Server / Linux
- **Description:** High‑capacity storage server; E1C expander backplane variant.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SSG-947HE1C
- Buy on Newark: https://www.newark.com/search?st=SSG-947HE1C

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
