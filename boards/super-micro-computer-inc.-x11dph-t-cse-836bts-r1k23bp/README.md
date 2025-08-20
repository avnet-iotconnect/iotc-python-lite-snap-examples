# X11DPH-T, CSE-836BTS-R1K23BP

- **Supplier:** Super Micro Computer  Inc.
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** Motherboard + 3U chassis bundle
- **OS support:** Windows / Linux
- **Description:** X11DPH‑T board in CSE‑836BTS 3U/16‑bay chassis (1200W redundant PSU).
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=X11DPH-T%2C%20CSE-836BTS-R1K23BP
- Buy on Newark: https://www.newark.com/search?st=X11DPH-T%2C%20CSE-836BTS-R1K23BP

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
