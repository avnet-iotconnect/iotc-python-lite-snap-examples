# GHF51 (1.8" Femto-ITX)

- **Supplier:** DFI
- **Arch:** amd64
- **Processor:** AMD Ryzen Embedded R1000
- **AI acceleration:** Radeon Vega GPU
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.dfi.com/product/index/1455

### OS images & docs
- (none)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=GHF51%20%281.8%22%20Femto-ITX%29
- Buy on Newark: https://www.newark.com/search?st=GHF51%20%281.8%22%20Femto-ITX%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
