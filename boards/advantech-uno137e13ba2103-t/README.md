# UNO137E13BA2103-T

- **Supplier:** Advantech
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** Compact DIN‑rail IoT controller
- **OS support:** Windows 10 IoT Enterprise 2019 LTSC; AdvLinux (Ubuntu 20.04)
- **Description:** UNO‑137 small‑size integrated DIN‑rail IPC with isolated DI/DO and dual DP.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=UNO137E13BA2103-T
- Buy on Newark: https://www.newark.com/search?st=UNO137E13BA2103-T

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
