# Curiosity PIC64GX1000 Kit

- **Supplier:** Microchip
- **Arch:** riscv64
- **Processor:** PIC64GX1000, quad-core 64-bit RISC-V application processor
- **AI acceleration:** —
- **Expansion:** mikroBUS (Click boards), MIPI CSI-2, HDMI
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `sudo snap run iotconnect.setup`

## Documentation

The full example for this board lives in [examples/microchip-curiosity-pic64gx1000](../../../examples/microchip-curiosity-pic64gx1000):

- [Overview and dashboard](../../../examples/microchip-curiosity-pic64gx1000/README.md)
- [Quickstart, no compilation required](../../../examples/microchip-curiosity-pic64gx1000/QUICKSTART.md)
- [Developer guide](../../../examples/microchip-curiosity-pic64gx1000/DEVELOPER_GUIDE.md)
- [Vision demo operator guide](../../../examples/microchip-curiosity-pic64gx1000/OPERATOR_GUIDE.md)
- [Device template and dashboard import files](../../../examples/microchip-curiosity-pic64gx1000/files)

The scripts under [`applications/`](./applications) in this folder are copies of the ones in the example. Treat the example folder as canonical.

## Official links

- Product page: https://www.microchip.com/en-us/development-tool/curiosity-pic64gx1000-kit
- Kit user guide: https://ww1.microchip.com/downloads/aemDocuments/documents/MPU64/ProductDocuments/SupportingCollateral/PIC64GX_Curiosity_Kit_User_Guide.pdf
- Kit quickstart guide: https://ww1.microchip.com/downloads/aemDocuments/documents/MPU64/ProductDocuments/UserGuides/production-kit-qsguide/Curiosity-PIC64GX1000-Kit_QSGuide.pdf

### OS images & docs

- Ubuntu for RISC-V: https://ubuntu.com/download/risc-v

## Buy

- Buy on Newark: https://www.newark.com/microchip/curiosity-pic64gx1000-kit/curiosity-kit-64bit-risc-v-quad/dp/46AM3917
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=Curiosity%20PIC64GX1000

## Known quirks

- The default `apt` sources on the preinstalled image do not serve riscv64 packages. Replace them with `ports.ubuntu.com` before the first `apt-get update`.
- Install `snapd` and reboot before installing the Snap.
- Run the socket bridge as root (`sudo snap start iotconnect.socket`) so the sockets are created under `/var/snap/iotconnect/common/`, which is where the example applications expect them.
- The mikroBUS I2C controllers are disabled in some device trees. See [Enabling I2C for mikroBUS](../../../examples/microchip-curiosity-pic64gx1000/DEVELOPER_GUIDE.md#7-enabling-i2c-for-mikrobus).
- No PyTorch or ONNX Runtime wheels for riscv64. Use `--backend cv_only` for the vision example.

## Quick test

```bash
python3 ../../../examples/microchip-curiosity-pic64gx1000/applications/perf_iotc_socket.py --once
```
