# AC

- **Supplier:** AMPERE COMPUTING LLC
- **Arch:** arm64
- **Processor:** Ampere Altra / Altra Max
- **AI acceleration:** —
- **Form factor:** CPU (server processor) – details TBD
- **OS support:** Linux (AArch64), *varies by platform*
- **Description:** Ampere Computing part code; likely an Altra/Max CPU kit used by OEMs.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=AC
- Buy on Newark: https://www.newark.com/search?st=AC

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
