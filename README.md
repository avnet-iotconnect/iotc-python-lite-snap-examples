# IoTConnect Snap – Example Applications

This bundle contains 50 per-board guides and a simple telemetry example for the IoTConnect Snap.

## Quick start
```bash
sudo apt update && sudo apt install -y snapd
sudo snap install iotconnect
iotconnect.setup
python3 examples/00-hello-telemetry/hello_telemetry.py
```

## Board Catalog (50)
| Supplier | Model | Arch | Folder |
|---|---|---:|---|
| Advantech | RSB-3810 (Pico-ITX) | arm64 | `boards/advantech-rsb3810` |
| ASUS IoT | Tinker Board 3N | arm64 | `boards/asus-tinker3n` |
| IEI | HYPER-ASL (Pico-ITX) | amd64 | `boards/iei-hyper-asl` |
| GIGAIPC | PICO-N97A | amd64 | `boards/gigaipc-pico-n97a` |
| Engicam | i.Core MX95 SoM + carrier | arm64 | `boards/engicam-icore-mx95` |
| Avnet Embedded (MSC) | SM2S-IMX95 + SMARC base | arm64 | `boards/avnet-msc-sm2s-imx95` |
| Toradex | Verdin i.MX95 EVK | arm64 | `boards/toradex-verdin-imx95` |
| Brainboxes | BB-400 | armhf | `boards/bb400` |
| Advantech | RSB-3720 (Pico-ITX) | arm64 | `boards/advantech-rsb3720` |
| Advantech | MIO-2365 (3.5") | amd64 | `boards/advantech-mio2365` |
| Advantech | ROM-5720 (SMARC) | arm64 | `boards/advantech-rom5720` |
| Advantech | ROM-5620 (SMARC) | arm64 | `boards/advantech-rom5620` |
| ASUS IoT | Tinker Board 2S | arm64 | `boards/asus-tinker2s` |
| ASUS IoT | Tinker Edge R | arm64 | `boards/asus-tinker-edge-r` |
| ASUS IoT | Tinker Board S R2.0 | armhf | `boards/asus-tinker-s-r2` |
| IEI | WAFER-ADLN (3.5") | amd64 | `boards/iei-wafer-adln` |
| IEI | KINO-ADLN (mITX) | amd64 | `boards/iei-kino-adln` |
| IEI | NANO-ADL-P (EPIC) | amd64 | `boards/iei-nano-adlp` |
| IEI | tKINO-ADLN (thin mITX) | amd64 | `boards/iei-tkino-adln` |
| Avalue | ECM-ADLN (3.5") | amd64 | `boards/avalue-ecm-adln` |
| Avalue | EPM-1727 (Pico-ITX) | amd64 | `boards/avalue-epm-1727` |
| Avalue | SOM-EHL (SMARC) | amd64 | `boards/avalue-som-ehl` |
| Avalue | ECM-TGL (3.5") | amd64 | `boards/avalue-ecm-tgl` |
| Engicam | SmarCore MX95 (SMARC) | arm64 | `boards/engicam-smarcore-mx95` |
| Engicam | i.Core STM32MP2 SoM + carrier | arm64 | `boards/engicam-icore-stm32mp2` |
| Engicam | i.Core MX8M Plus SoM + carrier | arm64 | `boards/engicam-icore-imx8mp` |
| Kontron | 3.5"-SBC-EKL | amd64 | `boards/kontron-35-sbc-ekl` |
| Kontron | SMARC-sXEL | amd64 | `boards/kontron-smarc-sxel` |
| Kontron | pITX-IMX8M | arm64 | `boards/kontron-pitx-imx8m` |
| Kontron | pITX-APL | amd64 | `boards/kontron-pitx-apl` |
| MSI IPC | MS-98M3 (3.5") | amd64 | `boards/msi-ms98m3` |
| MSI IPC | MS-98L9 (ATX) | amd64 | `boards/msi-ms98l9` |
| Mitac | PD10EHI (mITX Thin) | amd64 | `boards/mitac-pd10ehi` |
| Mitac | PH12CMI (mITX Thin) | amd64 | `boards/mitac-ph12cmi` |
| ASRock Industrial | 4X4 BOX-7735U | amd64 | `boards/asrock-4x4-7735u` |
| ASRock Industrial | IMB-ADLN (mITX) | amd64 | `boards/asrock-imb-adln` |
| ASRock Industrial | iBOX-1265UE | amd64 | `boards/asrock-ibox-1265ue` |
| ASRock Industrial | NUC BOX-1340P | amd64 | `boards/asrock-nucbox-1340p` |
| DFI | GHF51 (1.8" Femto-ITX) | amd64 | `boards/dfi-ghf51` |
| DFI | EHL171 (mITX) | amd64 | `boards/dfi-ehl171` |
| DFI | EHL173 (mITX) | amd64 | `boards/dfi-ehl173` |
| iBASE | IB836 (3.5") | amd64 | `boards/ibase-ib836` |
| iBASE | ET977 (COMe Type 6) | amd64 | `boards/ibase-et977` |
| iBASE | MI989 (mITX) | amd64 | `boards/ibase-mi989` |
| Avnet Embedded (MSC) | SM2S-EL (SMARC) | amd64 | `boards/avnet-msc-sm2s-el` |
| Avnet Embedded (MSC) | C6C-RPL (COMe Type 6) | amd64 | `boards/avnet-msc-c6c-rpl` |
| Avnet Embedded (MSC) | Q7-EL (Qseven) | amd64 | `boards/avnet-msc-q7-el` |
| Toradex | Verdin i.MX8M Plus | arm64 | `boards/toradex-verdin-imx8mp` |
| Toradex | Apalis i.MX8 | arm64 | `boards/toradex-apalis-imx8` |
| Toradex | Colibri iMX6ULL | armhf | `boards/toradex-colibri-imx6ull` |