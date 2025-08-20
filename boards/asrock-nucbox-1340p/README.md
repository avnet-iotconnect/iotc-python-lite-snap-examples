# NUC BOX-1340P

- **Supplier:** ASRock Industrial
- **Arch:** amd64
- **Processor:** Intel Core i5‑1340P (13th Gen)
- **AI acceleration:** Intel Iris Xe GPU
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.asrockind.com/en-gb/NUC%20BOX-1340P/D4

### OS images & docs
- (none)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=NUC%20BOX-1340P
- Buy on Newark: https://www.newark.com/search?st=NUC%20BOX-1340P

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
