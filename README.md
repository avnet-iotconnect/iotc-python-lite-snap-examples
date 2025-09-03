# IOTCONNECT Snap – Example Applications

This repository collects **board-specific guides and examples** for deploying the `iotconnect` Snap across platforms supporting the IOTCONNECT Snapcraft Snap.  
The catalog is **continuously growing** as new boards are validated by the community.

## Quick start
```bash
sudo apt update && sudo apt install -y snapd
sudo snap install iotconnect
iotconnect.setup
python3 examples/00-hello-telemetry/hello_telemetry.py
```

## Board Catalog (with official product URLs attached)
| Supplier              | Model                          |  Arch | Processor                                | AI acceleration                             | Folder                                                                    |
| --------------------- | ------------------------------ | ----: | ---------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------- |
| **AAEON**             | BOXER-8221AI                   | arm64 | NVIDIA Jetson Nano                       | NVIDIA Maxwell GPU                          | [boards/aaeon-boxer-8221ai](boards/aaeon-boxer-8221ai/)                   |
| **ADLINK**            | DLAP-211-JT2                   | arm64 | NVIDIA Jetson TX2 NX                     | NVIDIA Pascal GPU                           | [boards/adlink-dlap-211-jt2](boards/adlink-dlap-211-jt2/)                 |
| **Advantech**         | MIC-733-AO                     | arm64 | NVIDIA Jetson AGX Orin                   | NVIDIA Ampere GPU + DLA (up to 275 TOPS)    | [boards/advantech-mic-733-ao](boards/advantech-mic-733-ao/)               |
| **Advantech**         | MIO-2365 (3.5")                | amd64 | Intel Processor N100 (Alder Lake-N)      | —                                           | [boards/advantech-mio2365](boards/advantech-mio2365/)                     |
| **Advantech**         | ROM-5620 (SMARC)               | arm64 | NXP i.MX8M Mini/Nano (SMARC)             | —                                           | [boards/advantech-rom5620](boards/advantech-rom5620/)                     |
| **Advantech**         | ROM-5720 (SMARC)               | arm64 | NXP i.MX8M Plus (SMARC)                  | Integrated NPU (\~2.3 TOPS)                 | [boards/advantech-rom5720](boards/advantech-rom5720/)                     |
| **Advantech**         | RSB-3720 (Pico-ITX)            | arm64 | NXP i.MX8M Plus                          | Integrated NPU (\~2.3 TOPS)                 | [boards/advantech-rsb3720](boards/advantech-rsb3720/)                     |
| **Advantech**         | RSB-3810 (Pico-ITX)            | arm64 | MediaTek Genio 1200                      | MediaTek APU (\~4.8 TOPS)                   | [boards/advantech-rsb3810](boards/advantech-rsb3810/)                     |
| **Advantech**         | SOM-9461ES0C-MA2E (COM-HPC)    | amd64 | Intel Atom x5-E8000                      | —                                           | [boards/advantech-som-9461es0c-ma2e](boards/advantech-som-9461es0c-ma2e/) |
| **ASRock Industrial** | 4X4 BOX-7735U                  | amd64 | AMD Ryzen 7 7735U                        | Radeon 680M (RDNA2)                         | [boards/asrock-4x4-7735u](boards/asrock-4x4-7735u/)                       |
| **ASRock Industrial** | iBOX-1265UE                    | amd64 | Intel Core i7-1265UE (12th Gen)          | Intel Iris Xe GPU                           | [boards/asrock-ibox-1265ue](boards/asrock-ibox-1265ue/)                   |
| **ASRock Industrial** | IMB-ADLN (mITX)                | amd64 | Intel Processor N100 (options: N97/N200) | —                                           | [boards/asrock-imb-adln](boards/asrock-imb-adln/)                         |
| **ASRock Industrial** | NUC BOX-1340P                  | amd64 | Intel Core i5-1340P (13th Gen)           | Intel Iris Xe GPU                           | [boards/asrock-nucbox-1340p](boards/asrock-nucbox-1340p/)                 |
| **ASUS IoT**          | PE3000G                        | amd64 | Intel 12th Gen Core (Alder Lake)         | MXM GPU (NVIDIA Ampere/Turing or Intel Arc) | [boards/asus-pe3000g](boards/asus-pe3000g/)                               |
| **ASUS IoT**          | Tinker Board 2S                | arm64 | Rockchip RK3399                          | —                                           | [boards/asus-tinker2s](boards/asus-tinker2s/)                             |
| **ASUS IoT**          | Tinker Board 3N                | arm64 | Rockchip RK3568                          | —                                           | [boards/asus-tinker3n](boards/asus-tinker3n/)                             |
| **ASUS IoT**          | Tinker Board S R2.0            | armhf | Rockchip RK3288                          | —                                           | [boards/asus-tinker-s-r2](boards/asus-tinker-s-r2/)                       |
| **ASUS IoT**          | Tinker Edge R                  | arm64 | Rockchip RK3399Pro                       | Integrated NPU (\~3 TOPS)                   | [boards/asus-tinker-edge-r](boards/asus-tinker-edge-r/)                   |
| **Brainboxes**        | BB-400                         | armhf | Broadcom BCM2837 (CM3+)                  | —                                           | [boards/bb400](boards/bb400/)                                             |
| **DFI**               | EHL171 (mITX)                  | amd64 | Intel Elkhart Lake (Atom x6000)          | —                                           | [boards/dfi-ehl171](boards/dfi-ehl171/)                                   |
| **DFI**               | EHL173 (mITX)                  | amd64 | Intel Elkhart Lake (Atom x6000)          | —                                           | [boards/dfi-ehl173](boards/dfi-ehl173/)                                   |
| **DFI**               | GHF51 (1.8" Femto-ITX)         | amd64 | AMD Ryzen Embedded R1000                 | Radeon Vega GPU                             | [boards/dfi-ghf51](boards/dfi-ghf51/)                                     |
| **Engicam**           | i.Core MX8M Plus SoM + carrier | arm64 | NXP i.MX8M Plus                          | Integrated NPU (\~2.3 TOPS)                 | [boards/engicam-icore-imx8mp](boards/engicam-icore-imx8mp/)               |
| **Engicam**           | i.Core MX95 SoM + carrier      | arm64 | NXP i.MX95                               | Integrated NPU (Arm Ethos-U85 class)        | [boards/engicam-icore-mx95](boards/engicam-icore-mx95/)                   |
| **Engicam**           | i.Core STM32MP2 SoM + carrier  | arm64 | ST STM32MP2 series                       | Integrated NPU                              | [boards/engicam-icore-stm32mp2](boards/engicam-icore-stm32mp2/)           |
| **Engicam**           | SmarCore MX95 (SMARC)          | arm64 | NXP i.MX95 (SMARC)                       | Integrated NPU (Arm Ethos-U85 class)        | [boards/engicam-smarcore-mx95](boards/engicam-smarcore-mx95/)             |
| **GIGAIPC**           | PICO-N97A                      | amd64 | Intel Processor N97                      | —                                           | [boards/gigaipc-pico-n97a](boards/gigaipc-pico-n97a/)                     |
| **iBASE**             | ET977 (COMe Type 6)            | amd64 | Intel 12th/13th Gen Core (COMe)          | Intel Iris Xe / UHD (varies)                | [boards/ibase-et977](boards/ibase-et977/)                                 |
| **iBASE**             | IB836 (3.5")                   | amd64 | Intel Elkhart Lake                       | —                                           | [boards/ibase-ib836](boards/ibase-ib836/)                                 |
| **iBASE**             | MI989 (mITX)                   | amd64 | Intel 12th Gen Alder Lake-S (LGA1700)    | Intel UHD 770 GPU                           | [boards/ibase-mi989](boards/ibase-mi989/)                                 |
| **IEI**               | HYPER-ASL (Pico-ITX)           | amd64 | Intel Processor N100 (options: N97/N200) | —                                           | [boards/iei-hyper-asl](boards/iei-hyper-asl/)                             |
| **IEI**               | KINO-ADLN (mITX)               | amd64 | Intel Processor N100 (options: N97/N200) | —                                           | [boards/iei-kino-adln](boards/iei-kino-adln/)                             |
| **IEI**               | NANO-ADL-P (EPIC)              | amd64 | Intel Alder Lake-P                       | Intel Iris Xe GPU                           | [boards/iei-nano-adlp](boards/iei-nano-adlp/)                             |
| **IEI**               | tKINO-ADLN (thin mITX)         | amd64 | Intel Processor N100 (options: N97/N200) | —                                           | [boards/iei-tkino-adln](boards/iei-tkino-adln/)                           |
| **IEI**               | WAFER-ADLN (3.5")              | amd64 | Intel Processor N100 (options: N97/N200) | —                                           | [boards/iei-wafer-adln](boards/iei-wafer-adln/)                           |
| **Kontron**           | pITX-APL                       | amd64 | Intel Apollo Lake                        | —                                           | [boards/kontron-pitx-apl](boards/kontron-pitx-apl/)                       |
| **Kontron**           | pITX-IMX8M                     | arm64 | NXP i.MX8M (Quad)                        | —                                           | [boards/kontron-pitx-imx8m](boards/kontron-pitx-imx8m/)                   |
| **Kontron**           | SMARC-sXEL                     | amd64 | Intel Atom x6425E / x6414RE (options)    | —                                           | [boards/kontron-smarc-sxel](boards/kontron-smarc-sxel/)                   |
| **MiTAC**             | PD10EHI (mITX Thin)            | amd64 | Intel Elkhart Lake                       | —                                           | [boards/mitac-pd10ehi](boards/mitac-pd10ehi/)                             |
| **MiTAC**             | PH12CMI (mITX Thin)            | amd64 | Intel 12th Gen Alder Lake-S              | Intel UHD 770 GPU                           | [boards/mitac-ph12cmi](boards/mitac-ph12cmi/)                             |
| **MSI IPC**           | MS-98L9 (ATX)                  | amd64 | Intel 12th Gen Alder Lake-S              | Intel UHD 770 GPU                           | [boards/msi-ms98l9](boards/msi-ms98l9/)                                   |
| **MSI IPC**           | MS-98M3 (3.5")                 | amd64 | Intel Tiger Lake-UP3                     | Intel Iris Xe GPU                           | [boards/msi-ms98m3](boards/msi-ms98m3/)                                   |
| **Toradex**           | Apalis i.MX8                   | arm64 | NXP i.MX8 (Apalis)                       | —                                           | [boards/toradex-apalis-imx8](boards/toradex-apalis-imx8/)                 |
| **Toradex**           | Colibri iMX6ULL                | armhf | NXP i.MX6ULL (Colibri)                   | —                                           | [boards/toradex-colibri-imx6ull](boards/toradex-colibri-imx6ull/)         |
| **Toradex**           | Verdin i.MX8M Plus             | arm64 | NXP i.MX8M Plus (Verdin)                 | Integrated NPU (\~2.3 TOPS)                 | [boards/toradex-verdin-imx8mp](boards/toradex-verdin-imx8mp/)             |
| **Toradex**           | Verdin i.MX95 EVK              | arm64 | NXP i.MX95 (Verdin)                      | Integrated NPU                              | [boards/toradex-verdin-imx95](boards/toradex-verdin-imx95/)               |
| **Tria**              | C6C-RPL (COMe Type 6)          | amd64 | Intel 13th Gen Core (Raptor Lake, COMe)  | —                                           | [boards/avnet-msc-c6c-rpl](boards/avnet-msc-c6c-rpl/)                     |
| **Tria**              | Q7-EL (Qseven)                 | amd64 | Intel Elkhart Lake (Qseven)              | —                                           | [boards/avnet-msc-q7-el](boards/avnet-msc-q7-el/)                         |
| **Tria**              | SM2S-EL (SMARC)                | amd64 | Intel Elkhart Lake (SMARC)               | —                                           | [boards/avnet-msc-sm2s-el](boards/avnet-msc-sm2s-el/)                     |
| **Tria**              | SM2S-IMX95 + SMARC base        | arm64 | NXP i.MX95 (SMARC)                       | Integrated NPU                              | [boards/avnet-msc-sm2s-imx95](boards/avnet-msc-sm2s-imx95/)               |
| **Avalue**            | ECM-ADLN (3.5")                | amd64 | Intel Alder Lake-N                       | —                                           | [boards/avalue-ecm-adln](boards/avalue-ecm-adln/)                         |
| **Avalue**            | ECM-TGL (3.5")                 | amd64 | Intel Tiger Lake-U                       | Intel Iris Xe GPU                           | [boards/avalue-ecm-tgl](boards/avalue-ecm-tgl/)                           |
| **Avalue**            | EPM-1727 (Pico-ITX)            | amd64 | Intel Elkhart Lake (Atom x6000)          | —                                           | [boards/avalue-epm-1727](boards/avalue-epm-1727/)                         |
| **Avalue**            | SOM-EHL (SMARC)                | amd64 | Intel Elkhart Lake (SMARC)               | —                                           | [boards/avalue-som-ehl](boards/avalue-som-ehl/)                           |
