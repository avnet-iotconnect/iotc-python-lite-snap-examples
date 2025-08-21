# UNO137E13BA2103-T

- **Supplier:** Advantech
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** Compact DIN‑rail IoT controller
- **Description:** UNO‑137 small‑size integrated DIN‑rail IPC with isolated DI/DO and dual DP.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page:  https://www.advantech.com/en-us/products/gf-bvl2/uno-137/mod_8e73989f-0c2b-42a1-918d-741b8d983245

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
