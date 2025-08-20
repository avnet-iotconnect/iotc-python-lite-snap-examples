# MS-98L9 (ATX)

- **Supplier:** MSI IPC
- **Arch:** amd64
- **Processor:** Intel 12th Gen Alder Lake‑S
- **AI acceleration:** Intel UHD 770 GPU
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://ipc.msi.com/product_detail/Industrial-Motherboard/ATX/MS-98L9

### OS images & docs
- Downloads: https://ipc.msi.com/product_download/Industrial-Motherboard/ATX/MS-98L9

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=MS-98L9%20%28ATX%29
- Buy on Newark: https://www.newark.com/search?st=MS-98L9%20%28ATX%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.
- Confirm UEFI boot mode; CSM can complicate installs.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
