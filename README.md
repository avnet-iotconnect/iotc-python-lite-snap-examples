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

## Board Catalog (servers removed; TBDs filled)
| Supplier | Model | Arch | Processor | AI acceleration | Folder |
|---|---|---:|---|---|---|
| AAEON | BOXER-8221AI |  | TBD | TBD | [boards/aaeon-boxer-8221ai](boards/aaeon-boxer-8221ai/) |
| ADLINK | https://www.adlinktech.com/Products/Deep_Learning_Accelerator_Platform_and_Server/Inference_Platform/DLAP-211-JT2 |  | TBD | TBD | [boards/adlink-httpswww.adlinktech.comproductsdeep_learning_accelerator_platform_and_serverinference_platformdlap-211-jt2](boards/adlink-httpswww.adlinktech.comproductsdeep_learning_accelerator_platform_and_serverinference_platformdlap-211-jt2/) |
| Advantech | AIMB275G22306-T | amd64 | TBD | TBD | [boards/advantech-aimb275g22306-t](boards/advantech-aimb275g22306-t/) |
| Advantech | C-OLY01-USM5002 | amd64 | Intel Xeon | — | [boards/advantech-c-oly01-usm5002](boards/advantech-c-oly01-usm5002/) |
| Advantech | C-OLY01-USM5003 | amd64 | Intel Xeon | — | [boards/advantech-c-oly01-usm5003](boards/advantech-c-oly01-usm5003/) |
| Advantech | EPC-A2225G2-EFA2 |  | TBD | TBD | [boards/advantech-epc-a2225g2-efa2](boards/advantech-epc-a2225g2-efa2/) |
| Advantech | HIT-BX2SN-CPH1E | amd64 | TBD | TBD | [boards/advantech-hit-bx2sn-cph1e](boards/advantech-hit-bx2sn-cph1e/) |
| Advantech | HIT-BX2SN-CPH2E | amd64 | TBD | TBD | [boards/advantech-hit-bx2sn-cph2e](boards/advantech-hit-bx2sn-cph2e/) |
| Advantech | https://www.advantech.com/en-us/products/965e4edb-fb98-429e-89ed-9a0a8435a7be/mic-733/mod_09861425-4950-46ab-ad39-1b5522881218 |  | TBD | TBD | [boards/advantech-httpswww.advantech.comen-usproducts965e4edb-fb98-429e-89ed-9a0a8435a7bemic-733mod_09861425-4950-46ab-ad39-1b5522881218](boards/advantech-httpswww.advantech.comen-usproducts965e4edb-fb98-429e-89ed-9a0a8435a7bemic-733mod_09861425-4950-46ab-ad39-1b5522881218/) |
| Advantech | MIO-2365 (3.5") | amd64 | Intel Alder Lake‑N | — | [boards/advantech-mio2365](boards/advantech-mio2365/) |
| Advantech | PCIE-1674E-AE |  | TBD | TBD | [boards/advantech-pcie-1674e-ae](boards/advantech-pcie-1674e-ae/) |
| Advantech | ROM-5620 (SMARC) | arm64 | NXP i.MX8M Mini/Nano (SMARC) | — | [boards/advantech-rom5620](boards/advantech-rom5620/) |
| Advantech | ROM-5720 (SMARC) | arm64 | NXP i.MX8M Plus (SMARC) | Integrated NPU (~2.3 TOPS) | [boards/advantech-rom5720](boards/advantech-rom5720/) |
| Advantech | RSB-3720 (Pico-ITX) | arm64 | NXP i.MX8M Plus | Integrated NPU (~2.3 TOPS) | [boards/advantech-rsb3720](boards/advantech-rsb3720/) |
| Advantech | RSB-3810 (Pico-ITX) | arm64 | MediaTek Genio 1200 | MediaTek APU (~4.8 TOPS) | [boards/advantech-rsb3810](boards/advantech-rsb3810/) |
| Advantech | SOM-9461ES0C-MA2E | amd64 | TBD | TBD | [boards/advantech-som-9461es0c-ma2e](boards/advantech-som-9461es0c-ma2e/) |
| Advantech | SOM-C350C5R-U9A1 | amd64 | Intel 13th Gen Core (Raptor Lake) | Intel Iris Xe (integrated) | [boards/advantech-som-c350c5r-u9a1](boards/advantech-som-c350c5r-u9a1/) |
| Advantech | UNO137E13BA2103-T | amd64 | Intel Atom (Apollo Lake) | — | [boards/advantech-uno137e13ba2103-t](boards/advantech-uno137e13ba2103-t/) |
| Advantech | USM5002311-CT | amd64 | Intel Xeon | — | [boards/advantech-usm5002311-ct](boards/advantech-usm5002311-ct/) |
| Advantech | USM5002432-CT | amd64 | Intel Xeon | — | [boards/advantech-usm5002432-ct](boards/advantech-usm5002432-ct/) |
| AMPERE COMPUTING LLC | AC | arm64 | TBD | TBD | [boards/ampere-computing-llc-ac](boards/ampere-computing-llc-ac/) |
| ASRock Industrial | 4X4 BOX-7735U | amd64 | AMD Ryzen 7 7735U | Radeon 680M (RDNA2) | [boards/asrock-4x4-7735u](boards/asrock-4x4-7735u/) |
| ASRock Industrial | iBOX-1265UE | amd64 | Intel Core i7‑1265UE (12th Gen) | Intel Iris Xe GPU | [boards/asrock-ibox-1265ue](boards/asrock-ibox-1265ue/) |
| ASRock Industrial | IMB-ADLN (mITX) | amd64 | Intel Alder Lake‑N | — | [boards/asrock-imb-adln](boards/asrock-imb-adln/) |
| ASRock Industrial | NUC BOX-1340P | amd64 | Intel Core i5‑1340P (13th Gen) | Intel Iris Xe GPU | [boards/asrock-nucbox-1340p](boards/asrock-nucbox-1340p/) |
| ASUS COMPUTER | 90AR00C1-M00090 |  | TBD | TBD | [boards/asus-computer-90ar00c1-m00090](boards/asus-computer-90ar00c1-m00090/) |
| ASUS COMPUTER | 90AR00Q2-M001P0 |  | TBD | TBD | [boards/asus-computer-90ar00q2-m001p0](boards/asus-computer-90ar00q2-m001p0/) |
| ASUS COMPUTER | 90ME09R0-S0P000 |  | TBD | TBD | [boards/asus-computer-90me09r0-s0p000](boards/asus-computer-90me09r0-s0p000/) |
| ASUS COMPUTER | PB63-BB5000XTL | amd64 | TBD | TBD | [boards/asus-computer-pb63-bb5000xtl](boards/asus-computer-pb63-bb5000xtl/) |
| ASUS COMPUTER | PB63-BB500X0TL-O | amd64 | TBD | TBD | [boards/asus-computer-pb63-bb500x0tl-o](boards/asus-computer-pb63-bb500x0tl-o/) |
| ASUS COMPUTER | PB63-BBC000XTL | amd64 | TBD | TBD | [boards/asus-computer-pb63-bbc000xtl](boards/asus-computer-pb63-bbc000xtl/) |
| ASUS COMPUTER | PB63-BBC00X0TL-O | amd64 | TBD | TBD | [boards/asus-computer-pb63-bbc00x0tl-o](boards/asus-computer-pb63-bbc00x0tl-o/) |
| ASUS IoT | PE3000G |  | TBD | TBD | [boards/asus-iot-pe3000g](boards/asus-iot-pe3000g/) |
| ASUS IoT | Tinker Board 2S | arm64 | Rockchip RK3399 | — | [boards/asus-tinker2s](boards/asus-tinker2s/) |
| ASUS IoT | Tinker Board 3N | arm64 | Rockchip RK3568 | — | [boards/asus-tinker3n](boards/asus-tinker3n/) |
| ASUS IoT | Tinker Board S R2.0 | armhf | Rockchip RK3288 | — | [boards/asus-tinker-s-r2](boards/asus-tinker-s-r2/) |
| ASUS IoT | Tinker Edge R | arm64 | Rockchip RK3399Pro | Integrated NPU (~3 TOPS) | [boards/asus-tinker-edge-r](boards/asus-tinker-edge-r/) |
| Avalue | ECM-ADLN (3.5") | amd64 | Intel Alder Lake‑N | — | [boards/avalue-ecm-adln](boards/avalue-ecm-adln/) |
| Avalue | ECM-TGL (3.5") | amd64 | Intel Tiger Lake‑U | Intel Iris Xe GPU | [boards/avalue-ecm-tgl](boards/avalue-ecm-tgl/) |
| Avalue | EPM-1727 (Pico-ITX) | amd64 | Intel Elkhart Lake (Atom x6000) | — | [boards/avalue-epm-1727](boards/avalue-epm-1727/) |
| Avalue | SOM-EHL (SMARC) | amd64 | Intel Elkhart Lake (SMARC) | — | [boards/avalue-som-ehl](boards/avalue-som-ehl/) |
| Brainboxes | BB-400 | armhf | Broadcom BCM2837 (CM3+) | — | [boards/bb400](boards/bb400/) |
| DFI | EHL171 (mITX) | amd64 | Intel Elkhart Lake | — | [boards/dfi-ehl171](boards/dfi-ehl171/) |
| DFI | EHL173 (mITX) | amd64 | Intel Elkhart Lake | — | [boards/dfi-ehl173](boards/dfi-ehl173/) |
| DFI | GHF51 (1.8" Femto-ITX) | amd64 | AMD Ryzen Embedded R1000 | Radeon Vega GPU | [boards/dfi-ghf51](boards/dfi-ghf51/) |
| Engicam | i.Core MX8M Plus SoM + carrier | arm64 | NXP i.MX8M Plus | Integrated NPU (~2.3 TOPS) | [boards/engicam-icore-imx8mp](boards/engicam-icore-imx8mp/) |
| Engicam | i.Core MX95 SoM + carrier | arm64 | NXP i.MX95 | Integrated NPU (Arm Ethos‑U85 class) | [boards/engicam-icore-mx95](boards/engicam-icore-mx95/) |
| Engicam | i.Core STM32MP2 SoM + carrier | arm64 | ST STM32MP2 series | Integrated NPU (Arm Ethos‑U85 class) | [boards/engicam-icore-stm32mp2](boards/engicam-icore-stm32mp2/) |
| Engicam | SmarCore MX95 (SMARC) | arm64 | NXP i.MX95 (SMARC) | Integrated NPU (Arm Ethos‑U85 class) | [boards/engicam-smarcore-mx95](boards/engicam-smarcore-mx95/) |
| GIGAIPC | PICO-N97A | amd64 | Intel Alder Lake‑N N97 | — | [boards/gigaipc-pico-n97a](boards/gigaipc-pico-n97a/) |
| iBASE | ET977 (COMe Type 6) | amd64 | Intel 12th/13th Gen Core (COMe Type 6) | Intel Iris Xe / UHD (varies) | [boards/ibase-et977](boards/ibase-et977/) |
| iBASE | IB836 (3.5") | amd64 | Intel Elkhart Lake | — | [boards/ibase-ib836](boards/ibase-ib836/) |
| iBASE | MI989 (mITX) | amd64 | Intel 12th Gen Alder Lake‑S (LGA1700) | Intel UHD 770 GPU | [boards/ibase-mi989](boards/ibase-mi989/) |
| IEI | HYPER-ASL (Pico-ITX) | amd64 | Intel Alder Lake‑N | — | [boards/iei-hyper-asl](boards/iei-hyper-asl/) |
| IEI | KINO-ADLN (mITX) | amd64 | Intel Alder Lake‑N | — | [boards/iei-kino-adln](boards/iei-kino-adln/) |
| IEI | NANO-ADL-P (EPIC) | amd64 | Intel Alder Lake‑P | Intel Iris Xe GPU | [boards/iei-nano-adlp](boards/iei-nano-adlp/) |
| IEI | tKINO-ADLN (thin mITX) | amd64 | Intel Alder Lake‑N | — | [boards/iei-tkino-adln](boards/iei-tkino-adln/) |
| IEI | WAFER-ADLN (3.5") | amd64 | Intel Alder Lake‑N | — | [boards/iei-wafer-adln](boards/iei-wafer-adln/) |
| INTEL | 999NAF | amd64 | TBD | TBD | [boards/intel-999naf](boards/intel-999naf/) |
| INTEL | 99A5FC | amd64 | TBD | TBD | [boards/intel-99a5fc](boards/intel-99a5fc/) |
| INTEL | 99A5FC-REV1 | amd64 | TBD | TBD | [boards/intel-99a5fc-rev1](boards/intel-99a5fc-rev1/) |
| INTEL | 99C6RZ | amd64 | TBD | TBD | [boards/intel-99c6rz](boards/intel-99c6rz/) |
| INTEL | BKNUC8I3PNB | amd64 | TBD | TBD | [boards/intel-bknuc8i3pnb](boards/intel-bknuc8i3pnb/) |
| INTEL | BNUC11TNKI3000099A8A2 | amd64 | Intel 11th Gen Core (Tiger Lake) | Intel Iris Xe (integrated) | [boards/intel-bnuc11tnki3000099a8a2](boards/intel-bnuc11tnki3000099a8a2/) |
| INTEL | BNUC11TNKI3000199A8A3 | amd64 | TBD | TBD | [boards/intel-bnuc11tnki3000199a8a3](boards/intel-bnuc11tnki3000199a8a3/) |
| INTEL | BX80684E2124G S | amd64 | Intel Xeon | — | [boards/intel-bx80684e2124g-s](boards/intel-bx80684e2124g-s/) |
| INTEL | BX80684E2134 S | amd64 | Intel Xeon | — | [boards/intel-bx80684e2134-s](boards/intel-bx80684e2134-s/) |
| INTEL | BX80684E2136 S | amd64 | Intel Xeon | — | [boards/intel-bx80684e2136-s](boards/intel-bx80684e2136-s/) |
| INTEL | CD8067303535700S | amd64 | Intel Xeon | — | [boards/intel-cd8067303535700s](boards/intel-cd8067303535700s/) |
| INTEL | CD8067303536100S | amd64 | Intel Xeon | — | [boards/intel-cd8067303536100s](boards/intel-cd8067303536100s/) |
| INTEL | CD8067303567703S | amd64 | Intel Xeon | — | [boards/intel-cd8067303567703s](boards/intel-cd8067303567703s/) |
| INTEL | CD8067303645300S | amd64 | Intel Xeon | — | [boards/intel-cd8067303645300s](boards/intel-cd8067303645300s/) |
| INTEL | CD8067303645400S | amd64 | Intel Xeon | — | [boards/intel-cd8067303645400s](boards/intel-cd8067303645400s/) |
| INTEL | CD8068904655303S | amd64 | Intel Xeon | — | [boards/intel-cd8068904655303s](boards/intel-cd8068904655303s/) |
| INTEL | CD8068904656703S | amd64 | Intel Xeon | — | [boards/intel-cd8068904656703s](boards/intel-cd8068904656703s/) |
| INTEL | CD8068904657901S | amd64 | Intel Xeon | — | [boards/intel-cd8068904657901s](boards/intel-cd8068904657901s/) |
| INTEL | CD8069503956302S | amd64 | Intel Xeon | — | [boards/intel-cd8069503956302s](boards/intel-cd8069503956302s/) |
| INTEL | CD8069503956900S | amd64 | Intel Xeon | — | [boards/intel-cd8069503956900s](boards/intel-cd8069503956900s/) |
| INTEL | CD8069504212701S | amd64 | Intel Xeon | — | [boards/intel-cd8069504212701s](boards/intel-cd8069504212701s/) |
| INTEL | CD8069504283204S | amd64 | Intel Xeon | — | [boards/intel-cd8069504283204s](boards/intel-cd8069504283204s/) |
| INTEL | CD8069504283704S | amd64 | Intel Xeon | — | [boards/intel-cd8069504283704s](boards/intel-cd8069504283704s/) |
| INTEL | CD8069504444900S | amd64 | Intel Xeon | — | [boards/intel-cd8069504444900s](boards/intel-cd8069504444900s/) |
| INTEL | CD8069504448800S | amd64 | Intel Xeon | — | [boards/intel-cd8069504448800s](boards/intel-cd8069504448800s/) |
| INTEL | CD8069504449200S | amd64 | Intel Xeon | — | [boards/intel-cd8069504449200s](boards/intel-cd8069504449200s/) |
| INTEL | E810CQDA2 | amd64 | TBD | TBD | [boards/intel-e810cqda2](boards/intel-e810cqda2/) |
| INTEL | PK8071305120102S | amd64 | Intel Xeon | — | [boards/intel-pk8071305120102s](boards/intel-pk8071305120102s/) |
| INTEL | RS3DC080 | amd64 | TBD | TBD | [boards/intel-rs3dc080](boards/intel-rs3dc080/) |
| Kontron | 3.5"-SBC-EKL | amd64 | Intel Elkhart Lake (Atom x6000) | — | [boards/kontron-35-sbc-ekl](boards/kontron-35-sbc-ekl/) |
| Kontron | 38034-0000-27-7US1 | amd64 | TBD | TBD | [boards/kontron-38034-0000-27-7us1](boards/kontron-38034-0000-27-7us1/) |
| Kontron | 68010-0000-51-3MC1 | amd64 | TBD | TBD | [boards/kontron-68010-0000-51-3mc1](boards/kontron-68010-0000-51-3mc1/) |
| Kontron | pITX-APL | amd64 | Intel Apollo Lake | — | [boards/kontron-pitx-apl](boards/kontron-pitx-apl/) |
| Kontron | pITX-IMX8M | arm64 | NXP i.MX8M (Quad) | — | [boards/kontron-pitx-imx8m](boards/kontron-pitx-imx8m/) |
| Kontron | SMARC-sXEL | amd64 | Intel Elkhart Lake (SMARC) | — | [boards/kontron-smarc-sxel](boards/kontron-smarc-sxel/) |
| LENOVO | 11AMS0FX00 | amd64 | TBD | TBD | [boards/lenovo-11ams0fx00](boards/lenovo-11ams0fx00/) |
| LENOVO | 11USS0B700 | amd64 | TBD | TBD | [boards/lenovo-11uss0b700](boards/lenovo-11uss0b700/) |
| LENOVO | 11V1S04H00 | amd64 | TBD | TBD | [boards/lenovo-11v1s04h00](boards/lenovo-11v1s04h00/) |
| LENOVO | 21L2S0M600 | amd64 | TBD | TBD | [boards/lenovo-21l2s0m600](boards/lenovo-21l2s0m600/) |
| LENOVO | 21M4S61400 | amd64 | TBD | TBD | [boards/lenovo-21m4s61400](boards/lenovo-21m4s61400/) |
| LENOVO | 21MX0006US | amd64 | TBD | TBD | [boards/lenovo-21mx0006us](boards/lenovo-21mx0006us/) |
| LENOVO | 21MXA00UUS | amd64 | TBD | TBD | [boards/lenovo-21mxa00uus](boards/lenovo-21mxa00uus/) |
| LENOVO | 30BQS08Q00 | amd64 | TBD | TBD | [boards/lenovo-30bqs08q00](boards/lenovo-30bqs08q00/) |
| LENOVO | 30BQS0E300 | amd64 | TBD | TBD | [boards/lenovo-30bqs0e300](boards/lenovo-30bqs0e300/) |
| LENOVO | 30BQS0ET00 | amd64 | TBD | TBD | [boards/lenovo-30bqs0et00](boards/lenovo-30bqs0et00/) |
| LENOVO | 30F8S08B00 | amd64 | TBD | TBD | [boards/lenovo-30f8s08b00](boards/lenovo-30f8s08b00/) |
| LENOVO | 30F8S0NY00 | amd64 | TBD | TBD | [boards/lenovo-30f8s0ny00](boards/lenovo-30f8s0ny00/) |
| LENOVO | 30G0S0QB00 | amd64 | TBD | TBD | [boards/lenovo-30g0s0qb00](boards/lenovo-30g0s0qb00/) |
| LENOVO | 30G9S8KV00 | amd64 | TBD | TBD | [boards/lenovo-30g9s8kv00](boards/lenovo-30g9s8kv00/) |
| LENOVO | 30GBS0DS00 | amd64 | TBD | TBD | [boards/lenovo-30gbs0ds00](boards/lenovo-30gbs0ds00/) |
| Mitac | PD10EHI (mITX Thin) | amd64 | Intel Elkhart Lake | — | [boards/mitac-pd10ehi](boards/mitac-pd10ehi/) |
| Mitac | PH12CMI (mITX Thin) | amd64 | Intel 12th Gen Alder Lake‑S | Intel UHD 770 GPU | [boards/mitac-ph12cmi](boards/mitac-ph12cmi/) |
| MSI IPC | MS-98L9 (ATX) | amd64 | Intel 12th Gen Alder Lake‑S | Intel UHD 770 GPU | [boards/msi-ms98l9](boards/msi-ms98l9/) |
| MSI IPC | MS-98M3 (3.5") | amd64 | Intel Tiger Lake‑UP3 | Intel Iris Xe GPU | [boards/msi-ms98m3](boards/msi-ms98m3/) |
| Toradex | Apalis i.MX8 | arm64 | NXP i.MX8 (Apalis) | — | [boards/toradex-apalis-imx8](boards/toradex-apalis-imx8/) |
| Toradex | Colibri iMX6ULL | armhf | NXP i.MX6ULL (Colibri) | — | [boards/toradex-colibri-imx6ull](boards/toradex-colibri-imx6ull/) |
| Toradex | Verdin i.MX8M Plus | arm64 | NXP i.MX8M Plus (Verdin) | Integrated NPU (~2.3 TOPS) | [boards/toradex-verdin-imx8mp](boards/toradex-verdin-imx8mp/) |
| Toradex | Verdin i.MX95 EVK | arm64 | NXP i.MX95 (Verdin) | Integrated NPU (Arm Ethos‑U85 class) | [boards/toradex-verdin-imx95](boards/toradex-verdin-imx95/) |
| Tria | C6C-RPL (COMe Type 6) | amd64 | Intel 13th Gen Core (Raptor Lake, COMe Type 6) | — | [boards/avnet-msc-c6c-rpl](boards/avnet-msc-c6c-rpl/) |
| Tria | Q7-EL (Qseven) | amd64 | Intel Elkhart Lake (Qseven) | — | [boards/avnet-msc-q7-el](boards/avnet-msc-q7-el/) |
| Tria | SM2S-EL (SMARC) | amd64 | Intel Elkhart Lake (SMARC) | — | [boards/avnet-msc-sm2s-el](boards/avnet-msc-sm2s-el/) |
| Tria | SM2S-IMX95 + SMARC base | arm64 | NXP i.MX95 (SMARC) | Integrated NPU (Arm Ethos‑U85 class) | [boards/avnet-msc-sm2s-imx95](boards/avnet-msc-sm2s-imx95/) |
| Xilinx | A-U55C-P00G-PQ-G |  | TBD | TBD | [boards/xilinx-a-u55c-p00g-pq-g](boards/xilinx-a-u55c-p00g-pq-g/) |
