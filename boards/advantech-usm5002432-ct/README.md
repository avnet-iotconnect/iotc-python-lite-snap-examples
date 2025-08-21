# USM5002432-CT

- **Supplier:** Advantech
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** Medical mini‑tower / standalone AI box PC (USM‑500 family)
- **Description:** USM‑500-series medical AI computer; NVIDIA‑certified, supports RTX A6000 and dual video capture cards.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page:  https://www.advantech.com/en-us/products/a61f5423-4d9b-41db-aac4-2fc5f61d78fe/usm-500/mod_998946d1-edb0-435a-9a6a-b2fd98f78133

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=USM5002432-CT
- Buy on Newark: https://www.newark.com/search?st=USM5002432-CT

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
