# https://www.advantech.com/en-us/products/965e4edb-fb98-429e-89ed-9a0a8435a7be/mic-733/mod_09861425-4950-46ab-ad39-1b5522881218

- **Supplier:** Advantech
- **Arch:** 
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** https://www.advantech.com/en-us/products/965e4edb-fb98-429e-89ed-9a0a8435a7be/mic-733/mod_09861425-4950-46ab-ad39-1b5522881218
- **OS support:** nan
- **Description:** nan
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=https%3A//www.advantech.com/en-us/products/965e4edb-fb98-429e-89ed-9a0a8435a7be/mic-733/mod_09861425-4950-46ab-ad39-1b5522881218
- Buy on Newark: https://www.newark.com/search?st=https%3A//www.advantech.com/en-us/products/965e4edb-fb98-429e-89ed-9a0a8435a7be/mic-733/mod_09861425-4950-46ab-ad39-1b5522881218

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
