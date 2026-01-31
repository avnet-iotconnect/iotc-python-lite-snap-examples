# BNUC11TNKI3000099A8A2

- **Supplier:** INTEL
- **Arch:** amd64
- **Processor:** Intel 11th Gen Core (Tiger Lake)
- **AI acceleration:** Intel Iris Xe (integrated)
- **Form factor:** Mini PC (NUC 11)
- **OS support:** Windows / Linux
- **Description:** Intel NUC 11 Performance Kit, i3 model.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=BNUC11TNKI3000099A8A2
- Buy on Newark: https://www.newark.com/search?st=BNUC11TNKI3000099A8A2

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
