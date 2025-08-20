# IB836 (3.5")

- **Supplier:** iBASE
- **Arch:** amd64
- **Processor:** Intel Elkhart Lake
- **AI acceleration:** —
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: https://www.ibase.com.tw/en/product/category/Embedded_Computing/Single_Board_Computer/x86_based_3_5_Single_Board_Computer/IB836

### OS images & docs
- User Manual: https://www.ibase.com.tw/english/download/USER%27S%20Manual/IB836_UserManual_V1.0.pdf

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=IB836%20%283.5%22%29
- Buy on Newark: https://www.newark.com/search?st=IB836%20%283.5%22%29

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
