# tKINO-ADLN (thin mITX)

- **Supplier:** IEI
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
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=tKINO-ADLN%20(thin%20mITX)
- Buy on Newark: https://www.newark.com/search?st=tKINO-ADLN%20(thin%20mITX)

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
