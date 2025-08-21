# I350T4V2

- **Supplier:** INTEL
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** PCIe NIC (1 GbE)
- **OS support:** Windows / Linux
- **Description:** Quad‑port 1GbE server adapter.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=I350T4V2
- Buy on Newark: https://www.newark.com/search?st=I350T4V2

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
