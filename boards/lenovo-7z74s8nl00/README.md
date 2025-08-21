# 7Z74S8NL00

- **Supplier:** LENOVO
- **Arch:** amd64
- **Processor:** x86 (Intel Xeon/AMD EPYC, varies)
- **AI acceleration:** —
- **Form factor:** Rack/Tower Server (ThinkSystem/ThinkAgile)
- **OS support:** Windows Server / Linux (RHEL/Ubuntu/SLES)
- **Description:** Lenovo ThinkSystem/ThinkAgile server system SKU.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=7Z74S8NL00
- Buy on Newark: https://www.newark.com/search?st=7Z74S8NL00

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
