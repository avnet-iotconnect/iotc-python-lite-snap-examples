# SmarCore MX95 (SMARC)

- **Supplier:** Engicam
- **Arch:** arm64
- **Processor:** NXP i.MX95 (SMARC)
- **AI acceleration:** Integrated NPU (Arm Ethos‑U85 class)
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.engicam.com/vis-prod/SmarCore-MX95/SmarCore-iMX95

### OS images & docs
- (none)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=SmarCore%20MX95%20%28SMARC%29
- Buy on Newark: https://www.newark.com/search?st=SmarCore%20MX95%20%28SMARC%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
