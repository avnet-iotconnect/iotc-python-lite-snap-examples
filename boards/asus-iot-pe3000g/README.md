# PE3000G

- **Supplier:** ASUS IoT
- **Arch:** 
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** PE3000G
- **Description:** nan
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page:  https://www.asus.com/us/networking-iot-servers/aiot-industrial-solutions/embedded-computers-edge-ai-systems/pe3000g/

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=PE3000G
- Buy on Newark: https://www.newark.com/search?st=PE3000G

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
