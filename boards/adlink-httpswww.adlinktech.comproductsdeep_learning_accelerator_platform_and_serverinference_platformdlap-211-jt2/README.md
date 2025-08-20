# https://www.adlinktech.com/Products/Deep_Learning_Accelerator_Platform_and_Server/Inference_Platform/DLAP-211-JT2

- **Supplier:** ADLINK
- **Arch:** 
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** https://www.adlinktech.com/Products/Deep_Learning_Accelerator_Platform_and_Server/Inference_Platform/DLAP-211-JT2
- **OS support:** nan
- **Description:** nan
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=https%3A//www.adlinktech.com/Products/Deep_Learning_Accelerator_Platform_and_Server/Inference_Platform/DLAP-211-JT2
- Buy on Newark: https://www.newark.com/search?st=https%3A//www.adlinktech.com/Products/Deep_Learning_Accelerator_Platform_and_Server/Inference_Platform/DLAP-211-JT2

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
