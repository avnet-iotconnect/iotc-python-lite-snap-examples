# i.Core STM32MP2 SoM + carrier

- **Supplier:** Engicam
- **Arch:** arm64
- **Processor:** ST STM32MP2 series
- **AI acceleration:** Integrated NPU (Arm Ethos‑U85 class)
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.engicam.com/vis-prod/iCore-STM32MP2/iCore-STM32MP2

### OS images & docs
- (none)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=i.Core%20STM32MP2%20SoM%20%2B%20carrier
- Buy on Newark: https://www.newark.com/search?st=i.Core%20STM32MP2%20SoM%20%2B%20carrier

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
