# ECM-ADLN (3.5")

- **Supplier:** Avalue
- **Arch:** amd64
- **Processor:** Intel Alder Lake‑N
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (add docs)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=ECM-ADLN%20%283.5%22%29
- Buy on Newark: https://www.newark.com/search?st=ECM-ADLN%20%283.5%22%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
