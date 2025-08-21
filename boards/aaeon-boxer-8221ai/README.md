# BOXER-8221AI

- **Supplier:** AAEON
- **Arch:** 
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** BOXER-8221AI
- **Description:** nan
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page:  https://www.aaeon.com/en/product/detail/nvidia-jetson-nano-embedded-box-pc-boxer-8221ai

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=BOXER-8221AI
- Buy on Newark: https://www.newark.com/search?st=BOXER-8221AI

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
