# 90AR00C1-M00090

- **Supplier:** ASUS COMPUTER
- **Arch:** 
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** Mini PC / Barebone PN
- **OS support:** Windows / Linux
- **Description:** ASUS system part number; details depend on SKU.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=90AR00C1-M00090
- Buy on Newark: https://www.newark.com/search?st=90AR00C1-M00090

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
