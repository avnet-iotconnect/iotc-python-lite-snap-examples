# IOTCONNECT Snap – Example Applications

This repository collects **board-specific guides and examples** for deploying the `iotconnect` Snap across Avnet/Tria and partner platforms.  
The catalog is **continuously growing** as new boards are validated by the community.

## Quick start
```bash
sudo apt update && sudo apt install -y snapd
sudo snap install iotconnect
iotconnect.setup
python3 examples/00-hello-telemetry/hello_telemetry.py
```

## Board Catalog
| Supplier | Model | Arch | Folder |
|---|---|---:|---|
| Advantech | MIO-2365 (3.5") | amd64 | [boards/advantech-mio2365](boards/advantech-mio2365/) |
| Advantech | ROM-5620 (SMARC) | arm64 | [boards/advantech-rom5620](boards/advantech-rom5620/) |
| Advantech | ROM-5720 (SMARC) | arm64 | [boards/advantech-rom5720](boards/advantech-rom5720/) |
| Advantech | RSB-3720 (Pico-ITX) | arm64 | [boards/advantech-rsb3720](boards/advantech-rsb3720/) |
| Advantech | RSB-3810 (Pico-ITX) | arm64 | [boards/advantech-rsb3810](boards/advantech-rsb3810/) |
| ASRock Industrial | 4X4 BOX-7735U | amd64 | [boards/asrock-4x4-7735u](boards/asrock-4x4-7735u/) |
| ASRock Industrial | iBOX-1265UE | amd64 | [boards/asrock-ibox-1265ue](boards/asrock-ibox-1265ue/) |
| ASRock Industrial | IMB-ADLN (mITX) | amd64 | [boards/asrock-imb-adln](boards/asrock-imb-adln/) |
| ASRock Industrial | NUC BOX-1340P | amd64 | [boards/asrock-nucbox-1340p](boards/asrock-nucbox-1340p/) |
| ASUS IoT | Tinker Board 2S | arm64 | [boards/asus-tinker2s](boards/asus-tinker2s/) |
| ASUS IoT | Tinker Board 3N | arm64 | [boards/asus-tinker3n](boards/asus-tinker3n/) |
| ASUS IoT | Tinker Board S R2.0 | armhf | [boards/asus-tinker-s-r2](boards/asus-tinker-s-r2/) |
| ASUS IoT | Tinker Edge R | arm64 | [boards/asus-tinker-edge-r](boards/asus-tinker-edge-r/) |
| Avalue | ECM-ADLN (3.5") | amd64 | [boards/avalue-ecm-adln](boards/avalue-ecm-adln/) |
| Avalue | ECM-TGL (3.5") | amd64 | [boards/avalue-ecm-tgl](boards/avalue-ecm-tgl/) |
| Avalue | EPM-1727 (Pico-ITX) | amd64 | [boards/avalue-epm-1727](boards/avalue-epm-1727/) |
| Avalue | SOM-EHL (SMARC) | amd64 | [boards/avalue-som-ehl](boards/avalue-som-ehl/) |
| Brainboxes | BB-400 | armhf | [boards/bb400](boards/bb400/) |
| DFI | EHL171 (mITX) | amd64 | [boards/dfi-ehl171](boards/dfi-ehl171/) |
| DFI | EHL173 (mITX) | amd64 | [boards/dfi-ehl173](boards/dfi-ehl173/) |
| DFI | GHF51 (1.8" Femto-ITX) | amd64 | [boards/dfi-ghf51](boards/dfi-ghf51/) |
| Engicam | i.Core MX8M Plus SoM + carrier | arm64 | [boards/engicam-icore-imx8mp](boards/engicam-icore-imx8mp/) |
| Engicam | i.Core MX95 SoM + carrier | arm64 | [boards/engicam-icore-mx95](boards/engicam-icore-mx95/) |
| Engicam | i.Core STM32MP2 SoM + carrier | arm64 | [boards/engicam-icore-stm32mp2](boards/engicam-icore-stm32mp2/) |
| Engicam | SmarCore MX95 (SMARC) | arm64 | [boards/engicam-smarcore-mx95](boards/engicam-smarcore-mx95/) |
| GIGAIPC | PICO-N97A | amd64 | [boards/gigaipc-pico-n97a](boards/gigaipc-pico-n97a/) |
| iBASE | ET977 (COMe Type 6) | amd64 | [boards/ibase-et977](boards/ibase-et977/) |
| iBASE | IB836 (3.5") | amd64 | [boards/ibase-ib836](boards/ibase-ib836/) |
| iBASE | MI989 (mITX) | amd64 | [boards/ibase-mi989](boards/ibase-mi989/) |
| IEI | HYPER-ASL (Pico-ITX) | amd64 | [boards/iei-hyper-asl](boards/iei-hyper-asl/) |
| IEI | KINO-ADLN (mITX) | amd64 | [boards/iei-kino-adln](boards/iei-kino-adln/) |
| IEI | NANO-ADL-P (EPIC) | amd64 | [boards/iei-nano-adlp](boards/iei-nano-adlp/) |
| IEI | tKINO-ADLN (thin mITX) | amd64 | [boards/iei-tkino-adln](boards/iei-tkino-adln/) |
| IEI | WAFER-ADLN (3.5") | amd64 | [boards/iei-wafer-adln](boards/iei-wafer-adln/) |
| Kontron | 3.5"-SBC-EKL | amd64 | [boards/kontron-35-sbc-ekl](boards/kontron-35-sbc-ekl/) |
| Kontron | pITX-APL | amd64 | [boards/kontron-pitx-apl](boards/kontron-pitx-apl/) |
| Kontron | pITX-IMX8M | arm64 | [boards/kontron-pitx-imx8m](boards/kontron-pitx-imx8m/) |
| Kontron | SMARC-sXEL | amd64 | [boards/kontron-smarc-sxel](boards/kontron-smarc-sxel/) |
| Mitac | PD10EHI (mITX Thin) | amd64 | [boards/mitac-pd10ehi](boards/mitac-pd10ehi/) |
| Mitac | PH12CMI (mITX Thin) | amd64 | [boards/mitac-ph12cmi](boards/mitac-ph12cmi/) |
| MSI IPC | MS-98L9 (ATX) | amd64 | [boards/msi-ms98l9](boards/msi-ms98l9/) |
| MSI IPC | MS-98M3 (3.5") | amd64 | [boards/msi-ms98m3](boards/msi-ms98m3/) |
| Toradex | Apalis i.MX8 | arm64 | [boards/toradex-apalis-imx8](boards/toradex-apalis-imx8/) |
| Toradex | Colibri iMX6ULL | armhf | [boards/toradex-colibri-imx6ull](boards/toradex-colibri-imx6ull/) |
| Toradex | Verdin i.MX8M Plus | arm64 | [boards/toradex-verdin-imx8mp](boards/toradex-verdin-imx8mp/) |
| Toradex | Verdin i.MX95 EVK | arm64 | [boards/toradex-verdin-imx95](boards/toradex-verdin-imx95/) |
| Tria | C6C-RPL (COMe Type 6) | amd64 | [boards/avnet-msc-c6c-rpl](boards/avnet-msc-c6c-rpl/) |
| Tria | Q7-EL (Qseven) | amd64 | [boards/avnet-msc-q7-el](boards/avnet-msc-q7-el/) |
| Tria | SM2S-EL (SMARC) | amd64 | [boards/avnet-msc-sm2s-el](boards/avnet-msc-sm2s-el/) |
| Tria | SM2S-IMX95 + SMARC base | arm64 | [boards/avnet-msc-sm2s-imx95](boards/avnet-msc-sm2s-imx95/) |
