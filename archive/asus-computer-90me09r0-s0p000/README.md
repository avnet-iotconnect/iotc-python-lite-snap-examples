# 90ME09R0-S0P000

- **Supplier:** ASUS COMPUTER
- **Arch:** 
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** Motherboard (OEM PN)
- **OS support:** Windows / Linux
- **Description:** ASUS motherboard part number; exact model not specified.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=90ME09R0-S0P000
- Buy on Newark: https://www.newark.com/search?st=90ME09R0-S0P000

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
