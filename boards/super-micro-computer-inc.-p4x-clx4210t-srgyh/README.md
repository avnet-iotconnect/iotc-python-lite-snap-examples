# P4X-CLX4210T-SRGYH

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** CPU kit
- **OS support:** OS‑dependent
- **Description:** Supermicro boxed CPU option (S‑Spec SRGYH).
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=P4X-CLX4210T-SRGYH
- Buy on Newark: https://www.newark.com/search?st=P4X-CLX4210T-SRGYH

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
