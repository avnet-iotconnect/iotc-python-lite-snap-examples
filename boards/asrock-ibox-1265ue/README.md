# iBOX-1265UE

- **Supplier:** ASRock Industrial
- **Arch:** amd64
- **Processor:** Intel Core i7‑1265UE (12th Gen)
- **AI acceleration:** Intel Iris Xe GPU
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.asrockind.com/en-gb/iBOX-1265UE

### OS images & docs
- (none)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=iBOX-1265UE
- Buy on Newark: https://www.newark.com/search?st=iBOX-1265UE

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.
- Use recent kernels for best Intel iGPU/NIC support.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
