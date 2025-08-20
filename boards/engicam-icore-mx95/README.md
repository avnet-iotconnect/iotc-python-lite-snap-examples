# i.Core MX95 SoM + carrier

- **Supplier:** Engicam
- **Arch:** arm64
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.engicam.com/vis-prod/iCore-MX95/iCore-MX95

### OS images & docs
- (none)

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps
- If the IoTConnect socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```