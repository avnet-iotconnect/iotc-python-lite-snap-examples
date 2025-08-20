# AOC-S3108L-H8IR

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** 
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** PCIe RAID adapter
- **OS support:** Windows / Linux
- **Description:** Hardware RAID (RAID 0/1/5/6/10/50/60) with cache.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=AOC-S3108L-H8IR
- Buy on Newark: https://www.newark.com/search?st=AOC-S3108L-H8IR

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
