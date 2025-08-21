# C-OLY01-USM5002

- **Supplier:** Advantech
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** Medical mini‑tower (USM‑500 family, custom bundle)
- **OS support:** Windows / Linux (family support)
- **Description:** Customer/OEM‑specific USM‑500 configuration; public details limited.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=C-OLY01-USM5002
- Buy on Newark: https://www.newark.com/search?st=C-OLY01-USM5002

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
