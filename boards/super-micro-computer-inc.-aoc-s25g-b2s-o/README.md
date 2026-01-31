# AOC-S25G-B2S-O

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** 
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** PCIe network adapter
- **OS support:** Windows / Linux
- **Description:** Supermicro 25G SFP28 NIC.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=AOC-S25G-B2S-O
- Buy on Newark: https://www.newark.com/search?st=AOC-S25G-B2S-O

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
