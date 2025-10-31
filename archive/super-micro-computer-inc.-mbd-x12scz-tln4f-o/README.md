# MBD-X12SCZ-TLN4F-O

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** Intel Xeon W‑1200 / 10th Gen Core; W480 chipset
- **AI acceleration:** —
- **Form factor:** ATX server/workstation motherboard
- **OS support:** Windows / Linux
- **Description:** Board with 10GbE LAN (TLN4F), IPMI BMC.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=MBD-X12SCZ-TLN4F-O
- Buy on Newark: https://www.newark.com/search?st=MBD-X12SCZ-TLN4F-O

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
