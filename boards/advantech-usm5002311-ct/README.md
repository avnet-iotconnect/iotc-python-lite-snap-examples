# USM5002311-CT

- **Supplier:** Advantech
- **Arch:** amd64
- **Processor:** Intel Xeon
- **AI acceleration:** —
- **Form factor:** Medical mini‑tower (USM‑500 family)
- **OS support:** Windows 10 or Linux
- **Description:** USM‑500-series medical AI computer variant.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=USM5002311-CT
- Buy on Newark: https://www.newark.com/search?st=USM5002311-CT

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
