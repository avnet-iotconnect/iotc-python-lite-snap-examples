# HIT-BX2SN-CPH1E

- **Supplier:** Advantech
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** Medical box PC (HIT‑BX2S series)
- **OS support:** Windows (drivers available from Advantech); Linux not documented
- **Description:** Healthcare‑grade box PC configuration (i5/4GB/500GB; TPM/antenna options vary by suffix).
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=HIT-BX2SN-CPH1E
- Buy on Newark: https://www.newark.com/search?st=HIT-BX2SN-CPH1E

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
