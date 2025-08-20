# MIO-2365 (3.5")

- **Supplier:** Advantech
- **Arch:** amd64
- **Processor:** Intel Alder Lake‑N
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.advantech.com/en-us/products/460a67de-a7c8-94dc-0809-336fd7570e46/mio-2364/mod_6e929c2c-6213-4586-b747-3c7b7fd0dabe

### OS images & docs
- (none)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=MIO-2365%20%283.5%22%29
- Buy on Newark: https://www.newark.com/search?st=MIO-2365%20%283.5%22%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
