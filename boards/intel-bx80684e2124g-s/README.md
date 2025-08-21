# BX80684E2124G S

- **Supplier:** INTEL
- **Arch:** amd64
- **Processor:** Intel Xeon
- **AI acceleration:** —
- **Form factor:** CPU (boxed)
- **OS support:** OS‑dependent
- **Description:** Boxed Xeon E‑2100 series processor with iGPU.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=BX80684E2124G%20S
- Buy on Newark: https://www.newark.com/search?st=BX80684E2124G%20S

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
