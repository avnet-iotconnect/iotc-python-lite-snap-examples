# PCIE-1674E-AE

- **Supplier:** Advantech
- **Arch:** 
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** PCIe expansion card (half‑height/low‑profile)
- **OS support:** Windows and Linux drivers provided
- **Description:** 4‑port isolated RS‑422/485 PCIe card with surge/ESD protection.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=PCIE-1674E-AE
- Buy on Newark: https://www.newark.com/search?st=PCIE-1674E-AE

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
