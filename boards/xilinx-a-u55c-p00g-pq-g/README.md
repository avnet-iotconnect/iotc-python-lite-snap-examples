# A-U55C-P00G-PQ-G

- **Supplier:** Xilinx
- **Arch:** 
- **Processor:** TBD
- **AI acceleration:** TBD
- **Form factor:** PCIe accelerator card (FHHL, passive)
- **OS support:** Linux (RHEL/Ubuntu) with XRT/Vitis
- **Description:** Data‑center accelerator with HBM2; supported by XRT/Vitis runtime.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=A-U55C-P00G-PQ-G
- Buy on Newark: https://www.newark.com/search?st=A-U55C-P00G-PQ-G

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
