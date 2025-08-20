# PB63-BB500X0TL-O

- **Supplier:** ASUS COMPUTER
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** Mini PC barebone (PB63)
- **OS support:** Windows / Linux
- **Description:** ASUS Mini PC PB63 barebone kit (O‑SKU).
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=PB63-BB500X0TL-O
- Buy on Newark: https://www.newark.com/search?st=PB63-BB500X0TL-O

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
