# R3T52B

- **Supplier:** Hewlett Packard
- **Arch:** amd64
- **Processor:** TBD
- **AI acceleration:** —
- **Form factor:** Rack server configuration (base SKU)
- **OS support:** Varies by server configuration
- **Description:** Reseller lists as 'SE H90‑V91 TPM DR Base Server' (exact platform unspecified).
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=R3T52B
- Buy on Newark: https://www.newark.com/search?st=R3T52B

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
