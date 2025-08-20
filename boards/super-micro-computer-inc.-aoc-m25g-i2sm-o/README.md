# AOC-M25G-I2SM-O

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** 
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** Mezzanine/OCP NIC
- **OS support:** Windows / Linux
- **Description:** 25G mezzanine NIC for Supermicro servers.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=AOC-M25G-I2SM-O
- Buy on Newark: https://www.newark.com/search?st=AOC-M25G-I2SM-O

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
