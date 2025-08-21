# SSG-631E-E1CR16H-6

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** 3U storage server (16× 3.5")
- **OS support:** Windows / Linux
- **Description:** SSG‑631E with E1CR16H expander backplane; 3U high‑capacity storage.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SSG-631E-E1CR16H-6
- Buy on Newark: https://www.newark.com/search?st=SSG-631E-E1CR16H-6

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
