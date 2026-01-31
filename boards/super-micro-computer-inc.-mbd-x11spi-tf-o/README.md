# MBD-X11SPI-TF-O

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** Dual Intel Xeon Scalable (LGA3647)
- **AI acceleration:** —
- **Form factor:** SSI‑EEB server motherboard
- **OS support:** Windows / Linux
- **Description:** X11 Purley platform board with dual 10GbE (TF).
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=MBD-X11SPI-TF-O
- Buy on Newark: https://www.newark.com/search?st=MBD-X11SPI-TF-O

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
