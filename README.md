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
| Supplier | Model | Arch | Processor | AI acceleration | Folder |
|---|---|---:|---|---|---|
| AAEON | BOXER-8221AI |  | TBD | TBD | [boards/aaeon-boxer-8221ai](boards/aaeon-boxer-8221ai/) |
| ADLINK | https://www.adlinktech.com/Products/Deep_Learning_Accelerator_Platform_and_Server/Inference_Platform/DLAP-211-JT2 |  | TBD | TBD | [boards/adlink-httpswww.adlinktech.comproductsdeep_learning_accelerator_platform_and_serverinference_platformdlap-211-jt2](boards/adlink-httpswww.adlinktech.comproductsdeep_learning_accelerator_platform_and_serverinference_platformdlap-211-jt2/) |
| Advantech | AIMB275G22306-T | amd64 | TBD | TBD | [boards/advantech-aimb275g22306-t](boards/advantech-aimb275g22306-t/) |
| Advantech | C-OLY01-USM5002 | amd64 | TBD | TBD | [boards/advantech-c-oly01-usm5002](boards/advantech-c-oly01-usm5002/) |
| Advantech | C-OLY01-USM5003 | amd64 | TBD | TBD | [boards/advantech-c-oly01-usm5003](boards/advantech-c-oly01-usm5003/) |
| Advantech | EPC-A2225G2-EFA2 |  | TBD | TBD | [boards/advantech-epc-a2225g2-efa2](boards/advantech-epc-a2225g2-efa2/) |
| Advantech | HIT-BX2SN-CPH1E | amd64 | TBD | TBD | [boards/advantech-hit-bx2sn-cph1e](boards/advantech-hit-bx2sn-cph1e/) |
| Advantech | HIT-BX2SN-CPH2E | amd64 | TBD | TBD | [boards/advantech-hit-bx2sn-cph2e](boards/advantech-hit-bx2sn-cph2e/) |
| Advantech | https://www.advantech.com/en-us/products/965e4edb-fb98-429e-89ed-9a0a8435a7be/mic-733/mod_09861425-4950-46ab-ad39-1b5522881218 |  | TBD | TBD | [boards/advantech-httpswww.advantech.comen-usproducts965e4edb-fb98-429e-89ed-9a0a8435a7bemic-733mod_09861425-4950-46ab-ad39-1b5522881218](boards/advantech-httpswww.advantech.comen-usproducts965e4edb-fb98-429e-89ed-9a0a8435a7bemic-733mod_09861425-4950-46ab-ad39-1b5522881218/) |
| Advantech | PCIE-1674E-AE |  | TBD | TBD | [boards/advantech-pcie-1674e-ae](boards/advantech-pcie-1674e-ae/) |
| Advantech | SKY | amd64 | TBD | TBD | [boards/advantech-sky](boards/advantech-sky/) |
| Advantech | SOM-9461ES0C-MA2E | amd64 | TBD | TBD | [boards/advantech-som-9461es0c-ma2e](boards/advantech-som-9461es0c-ma2e/) |
| Advantech | SOM-C350C5R-U9A1 | amd64 | TBD | TBD | [boards/advantech-som-c350c5r-u9a1](boards/advantech-som-c350c5r-u9a1/) |
| Advantech | UNO137E13BA2103-T | amd64 | TBD | TBD | [boards/advantech-uno137e13ba2103-t](boards/advantech-uno137e13ba2103-t/) |
| Advantech | USM5002311-CT | amd64 | TBD | TBD | [boards/advantech-usm5002311-ct](boards/advantech-usm5002311-ct/) |
| Advantech | USM5002432-CT | amd64 | TBD | TBD | [boards/advantech-usm5002432-ct](boards/advantech-usm5002432-ct/) |
| AMPERE COMPUTING LLC | AC | arm64 | TBD | TBD | [boards/ampere-computing-llc-ac](boards/ampere-computing-llc-ac/) |
| ASUS COMPUTER | 90AR00C1-M00090 |  | TBD | TBD | [boards/asus-computer-90ar00c1-m00090](boards/asus-computer-90ar00c1-m00090/) |
| ASUS COMPUTER | 90AR00Q2-M001P0 |  | TBD | TBD | [boards/asus-computer-90ar00q2-m001p0](boards/asus-computer-90ar00q2-m001p0/) |
| ASUS COMPUTER | 90ME09R0-S0P000 |  | TBD | TBD | [boards/asus-computer-90me09r0-s0p000](boards/asus-computer-90me09r0-s0p000/) |
| ASUS COMPUTER | PB63-BB5000XTL | amd64 | TBD | TBD | [boards/asus-computer-pb63-bb5000xtl](boards/asus-computer-pb63-bb5000xtl/) |
| ASUS COMPUTER | PB63-BB500X0TL-O | amd64 | TBD | TBD | [boards/asus-computer-pb63-bb500x0tl-o](boards/asus-computer-pb63-bb500x0tl-o/) |
| ASUS COMPUTER | PB63-BBC000XTL | amd64 | TBD | TBD | [boards/asus-computer-pb63-bbc000xtl](boards/asus-computer-pb63-bbc000xtl/) |
| ASUS COMPUTER | PB63-BBC00X0TL-O | amd64 | TBD | TBD | [boards/asus-computer-pb63-bbc00x0tl-o](boards/asus-computer-pb63-bbc00x0tl-o/) |
| ASUS IoT | PE3000G |  | TBD | TBD | [boards/asus-iot-pe3000g](boards/asus-iot-pe3000g/) |
| Hewlett Packard | 871681-B21 | amd64 | TBD | TBD | [boards/hewlett-packard-871681-b21](boards/hewlett-packard-871681-b21/) |
| Hewlett Packard | P67824-B21 | amd64 | TBD | TBD | [boards/hewlett-packard-p67824-b21](boards/hewlett-packard-p67824-b21/) |
| Hewlett Packard | R3T52B | amd64 | TBD | TBD | [boards/hewlett-packard-r3t52b](boards/hewlett-packard-r3t52b/) |
| INTEL | 999NAF | amd64 | TBD | TBD | [boards/intel-999naf](boards/intel-999naf/) |
| INTEL | 99A5FC | amd64 | TBD | TBD | [boards/intel-99a5fc](boards/intel-99a5fc/) |
| INTEL | 99A5FC-REV1 | amd64 | TBD | TBD | [boards/intel-99a5fc-rev1](boards/intel-99a5fc-rev1/) |
| INTEL | 99C6RZ | amd64 | TBD | TBD | [boards/intel-99c6rz](boards/intel-99c6rz/) |
| INTEL | BKNUC8I3PNB | amd64 | TBD | TBD | [boards/intel-bknuc8i3pnb](boards/intel-bknuc8i3pnb/) |
| INTEL | BNUC11TNKI3000099A8A2 | amd64 | TBD | TBD | [boards/intel-bnuc11tnki3000099a8a2](boards/intel-bnuc11tnki3000099a8a2/) |
| INTEL | BNUC11TNKI3000199A8A3 | amd64 | TBD | TBD | [boards/intel-bnuc11tnki3000199a8a3](boards/intel-bnuc11tnki3000199a8a3/) |
| INTEL | BX80684E2124G S | amd64 | TBD | TBD | [boards/intel-bx80684e2124g-s](boards/intel-bx80684e2124g-s/) |
| INTEL | BX80684E2134 S | amd64 | TBD | TBD | [boards/intel-bx80684e2134-s](boards/intel-bx80684e2134-s/) |
| INTEL | BX80684E2136 S | amd64 | TBD | TBD | [boards/intel-bx80684e2136-s](boards/intel-bx80684e2136-s/) |
| INTEL | CD8067303535700S | amd64 | TBD | TBD | [boards/intel-cd8067303535700s](boards/intel-cd8067303535700s/) |
| INTEL | CD8067303536100S | amd64 | TBD | TBD | [boards/intel-cd8067303536100s](boards/intel-cd8067303536100s/) |
| INTEL | CD8067303567703S | amd64 | TBD | TBD | [boards/intel-cd8067303567703s](boards/intel-cd8067303567703s/) |
| INTEL | CD8067303645300S | amd64 | TBD | TBD | [boards/intel-cd8067303645300s](boards/intel-cd8067303645300s/) |
| INTEL | CD8067303645400S | amd64 | TBD | TBD | [boards/intel-cd8067303645400s](boards/intel-cd8067303645400s/) |
| INTEL | CD8068904655303S | amd64 | TBD | TBD | [boards/intel-cd8068904655303s](boards/intel-cd8068904655303s/) |
| INTEL | CD8068904656703S | amd64 | TBD | TBD | [boards/intel-cd8068904656703s](boards/intel-cd8068904656703s/) |
| INTEL | CD8068904657901S | amd64 | TBD | TBD | [boards/intel-cd8068904657901s](boards/intel-cd8068904657901s/) |
| INTEL | CD8069503956302S | amd64 | TBD | TBD | [boards/intel-cd8069503956302s](boards/intel-cd8069503956302s/) |
| INTEL | CD8069503956900S | amd64 | TBD | TBD | [boards/intel-cd8069503956900s](boards/intel-cd8069503956900s/) |
| INTEL | CD8069504212701S | amd64 | TBD | TBD | [boards/intel-cd8069504212701s](boards/intel-cd8069504212701s/) |
| INTEL | CD8069504283204S | amd64 | TBD | TBD | [boards/intel-cd8069504283204s](boards/intel-cd8069504283204s/) |
| INTEL | CD8069504283704S | amd64 | TBD | TBD | [boards/intel-cd8069504283704s](boards/intel-cd8069504283704s/) |
| INTEL | CD8069504444900S | amd64 | TBD | TBD | [boards/intel-cd8069504444900s](boards/intel-cd8069504444900s/) |
| INTEL | CD8069504448800S | amd64 | TBD | TBD | [boards/intel-cd8069504448800s](boards/intel-cd8069504448800s/) |
| INTEL | CD8069504449200S | amd64 | TBD | TBD | [boards/intel-cd8069504449200s](boards/intel-cd8069504449200s/) |
| INTEL | E810CQDA2 | amd64 | TBD | TBD | [boards/intel-e810cqda2](boards/intel-e810cqda2/) |
| INTEL | I350T4V2 | amd64 | TBD | TBD | [boards/intel-i350t4v2](boards/intel-i350t4v2/) |
| INTEL | PK8071305120102S | amd64 | TBD | TBD | [boards/intel-pk8071305120102s](boards/intel-pk8071305120102s/) |
| INTEL | RS3DC080 | amd64 | TBD | TBD | [boards/intel-rs3dc080](boards/intel-rs3dc080/) |
| Kontron | 38034-0000-27-7US1 | amd64 | TBD | TBD | [boards/kontron-38034-0000-27-7us1](boards/kontron-38034-0000-27-7us1/) |
| Kontron | 68010-0000-51-3MC1 | amd64 | TBD | TBD | [boards/kontron-68010-0000-51-3mc1](boards/kontron-68010-0000-51-3mc1/) |
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
| LENOVO | 7D4FS1Q900 | amd64 | TBD | TBD | [boards/lenovo-7d4fs1q900](boards/lenovo-7d4fs1q900/) |
| LENOVO | 7D73SDG500 | amd64 | TBD | TBD | [boards/lenovo-7d73sdg500](boards/lenovo-7d73sdg500/) |
| LENOVO | 7D73SHDX00 | amd64 | TBD | TBD | [boards/lenovo-7d73shdx00](boards/lenovo-7d73shdx00/) |
| LENOVO | 7D73SV3J00 | amd64 | TBD | TBD | [boards/lenovo-7d73sv3j00](boards/lenovo-7d73sv3j00/) |
| LENOVO | 7D73TDP800 | amd64 | TBD | TBD | [boards/lenovo-7d73tdp800](boards/lenovo-7d73tdp800/) |
| LENOVO | 7D73TDP900 | amd64 | TBD | TBD | [boards/lenovo-7d73tdp900](boards/lenovo-7d73tdp900/) |
| LENOVO | 7D73TDPA00 | amd64 | TBD | TBD | [boards/lenovo-7d73tdpa00](boards/lenovo-7d73tdpa00/) |
| LENOVO | 7D76S73L00 | amd64 | TBD | TBD | [boards/lenovo-7d76s73l00](boards/lenovo-7d76s73l00/) |
| LENOVO | 7D76UMWR00 | amd64 | TBD | TBD | [boards/lenovo-7d76umwr00](boards/lenovo-7d76umwr00/) |
| LENOVO | 7D7AS2X700 | amd64 | TBD | TBD | [boards/lenovo-7d7as2x700](boards/lenovo-7d7as2x700/) |
| LENOVO | 7D96S12R00 | amd64 | TBD | TBD | [boards/lenovo-7d96s12r00](boards/lenovo-7d96s12r00/) |
| LENOVO | 7D9ES04A00 | amd64 | TBD | TBD | [boards/lenovo-7d9es04a00](boards/lenovo-7d9es04a00/) |
| LENOVO | 7D9ES4LB00 | amd64 | TBD | TBD | [boards/lenovo-7d9es4lb00](boards/lenovo-7d9es4lb00/) |
| LENOVO | 7D9ES4QJ00 | amd64 | TBD | TBD | [boards/lenovo-7d9es4qj00](boards/lenovo-7d9es4qj00/) |
| LENOVO | 7DE4S2PT00 | amd64 | TBD | TBD | [boards/lenovo-7de4s2pt00](boards/lenovo-7de4s2pt00/) |
| LENOVO | 7DE4S3M900 | amd64 | TBD | TBD | [boards/lenovo-7de4s3m900](boards/lenovo-7de4s3m900/) |
| LENOVO | 7DGDS09R00 | amd64 | TBD | TBD | [boards/lenovo-7dgds09r00](boards/lenovo-7dgds09r00/) |
| LENOVO | 7Y63S1PK00 | amd64 | TBD | TBD | [boards/lenovo-7y63s1pk00](boards/lenovo-7y63s1pk00/) |
| LENOVO | 7Y74S5S800 | amd64 | TBD | TBD | [boards/lenovo-7y74s5s800](boards/lenovo-7y74s5s800/) |
| LENOVO | 7Y77S2YM00 | amd64 | TBD | TBD | [boards/lenovo-7y77s2ym00](boards/lenovo-7y77s2ym00/) |
| LENOVO | 7Z01S37T00 | amd64 | TBD | TBD | [boards/lenovo-7z01s37t00](boards/lenovo-7z01s37t00/) |
| LENOVO | 7Z74S5AD00 | amd64 | TBD | TBD | [boards/lenovo-7z74s5ad00](boards/lenovo-7z74s5ad00/) |
| LENOVO | 7Z74S8NL00 | amd64 | TBD | TBD | [boards/lenovo-7z74s8nl00](boards/lenovo-7z74s8nl00/) |
| Super Micro Computer  Inc. | 1029P-WTRT-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-1029p-wtrt-oto](boards/super-micro-computer-inc.-1029p-wtrt-oto/) |
| Super Micro Computer  Inc. | 111AD-HN2-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-111ad-hn2-oto](boards/super-micro-computer-inc.-111ad-hn2-oto/) |
| Super Micro Computer  Inc. | 111TS-605WBP-AM047-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-111ts-605wbp-am047-oto](boards/super-micro-computer-inc.-111ts-605wbp-am047-oto/) |
| Super Micro Computer  Inc. | 120C-TR-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-120c-tr-oto](boards/super-micro-computer-inc.-120c-tr-oto/) |
| Super Micro Computer  Inc. | 121C-TN2R-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-121c-tn2r-oto](boards/super-micro-computer-inc.-121c-tn2r-oto/) |
| Super Micro Computer  Inc. | 421GE-TNRT | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-421ge-tnrt](boards/super-micro-computer-inc.-421ge-tnrt/) |
| Super Micro Computer  Inc. | 5019P-WTR-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-5019p-wtr-oto](boards/super-micro-computer-inc.-5019p-wtr-oto/) |
| Super Micro Computer  Inc. | 610C-TR-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-610c-tr-oto](boards/super-micro-computer-inc.-610c-tr-oto/) |
| Super Micro Computer  Inc. | 621C-TN12R-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-621c-tn12r-oto](boards/super-micro-computer-inc.-621c-tn12r-oto/) |
| Super Micro Computer  Inc. | AOC-A25G-B2SM-O |  | TBD | TBD | [boards/super-micro-computer-inc.-aoc-a25g-b2sm-o](boards/super-micro-computer-inc.-aoc-a25g-b2sm-o/) |
| Super Micro Computer  Inc. | AOC-CX766003N-SQ0 |  | TBD | TBD | [boards/super-micro-computer-inc.-aoc-cx766003n-sq0](boards/super-micro-computer-inc.-aoc-cx766003n-sq0/) |
| Super Micro Computer  Inc. | AOC-M25G-I2SM-O |  | TBD | TBD | [boards/super-micro-computer-inc.-aoc-m25g-i2sm-o](boards/super-micro-computer-inc.-aoc-m25g-i2sm-o/) |
| Super Micro Computer  Inc. | AOC-MCX556A-ECAT |  | TBD | TBD | [boards/super-micro-computer-inc.-aoc-mcx556a-ecat](boards/super-micro-computer-inc.-aoc-mcx556a-ecat/) |
| Super Micro Computer  Inc. | AOC-S25G-B2S-O |  | TBD | TBD | [boards/super-micro-computer-inc.-aoc-s25g-b2s-o](boards/super-micro-computer-inc.-aoc-s25g-b2s-o/) |
| Super Micro Computer  Inc. | AOC-S3108L-H8IR |  | TBD | TBD | [boards/super-micro-computer-inc.-aoc-s3108l-h8ir](boards/super-micro-computer-inc.-aoc-s3108l-h8ir/) |
| Super Micro Computer  Inc. | AOC-SGP-I4 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-aoc-sgp-i4](boards/super-micro-computer-inc.-aoc-sgp-i4/) |
| Super Micro Computer  Inc. | AOC-STGF-I2S-O | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-aoc-stgf-i2s-o](boards/super-micro-computer-inc.-aoc-stgf-i2s-o/) |
| Super Micro Computer  Inc. | AS -1014S-WTRT01 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-as-1014s-wtrt01](boards/super-micro-computer-inc.-as-1014s-wtrt01/) |
| Super Micro Computer  Inc. | AS-1114S-WN10T | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-as-1114s-wn10t](boards/super-micro-computer-inc.-as-1114s-wn10t/) |
| Super Micro Computer  Inc. | AS-1115HS-TNR-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-as-1115hs-tnr-oto](boards/super-micro-computer-inc.-as-1115hs-tnr-oto/) |
| Super Micro Computer  Inc. | AS-1115S-FWTRT-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-as-1115s-fwtrt-oto](boards/super-micro-computer-inc.-as-1115s-fwtrt-oto/) |
| Super Micro Computer  Inc. | AS-2114S-WN24RT-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-as-2114s-wn24rt-oto](boards/super-micro-computer-inc.-as-2114s-wn24rt-oto/) |
| Super Micro Computer  Inc. | AS-2115HS-TNR-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-as-2115hs-tnr-oto](boards/super-micro-computer-inc.-as-2115hs-tnr-oto/) |
| Super Micro Computer  Inc. | E100-9W-H-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-e100-9w-h-oto](boards/super-micro-computer-inc.-e100-9w-h-oto/) |
| Super Micro Computer  Inc. | E200-8D-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-e200-8d-oto](boards/super-micro-computer-inc.-e200-8d-oto/) |
| Super Micro Computer  Inc. | F629P3-RTB-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-f629p3-rtb-oto](boards/super-micro-computer-inc.-f629p3-rtb-oto/) |
| Super Micro Computer  Inc. | MBD-H11SSL-I-B | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-h11ssl-i-b](boards/super-micro-computer-inc.-mbd-h11ssl-i-b/) |
| Super Micro Computer  Inc. | MBD-H12SSW-NTL-O | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-h12ssw-ntl-o](boards/super-micro-computer-inc.-mbd-h12ssw-ntl-o/) |
| Super Micro Computer  Inc. | MBD-X11DDW-NT-B | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x11ddw-nt-b](boards/super-micro-computer-inc.-mbd-x11ddw-nt-b/) |
| Super Micro Computer  Inc. | MBD-X11SCH-LN4F-B | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x11sch-ln4f-b](boards/super-micro-computer-inc.-mbd-x11sch-ln4f-b/) |
| Super Micro Computer  Inc. | MBD-X11SCW-F | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x11scw-f](boards/super-micro-computer-inc.-mbd-x11scw-f/) |
| Super Micro Computer  Inc. | MBD-X11SPA-T-B | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x11spa-t-b](boards/super-micro-computer-inc.-mbd-x11spa-t-b/) |
| Super Micro Computer  Inc. | MBD-X11SPI-TF-O | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x11spi-tf-o](boards/super-micro-computer-inc.-mbd-x11spi-tf-o/) |
| Super Micro Computer  Inc. | MBD-X11SSV-LVDS-B | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x11ssv-lvds-b](boards/super-micro-computer-inc.-mbd-x11ssv-lvds-b/) |
| Super Micro Computer  Inc. | MBD-X11SSV-Q-B | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x11ssv-q-b](boards/super-micro-computer-inc.-mbd-x11ssv-q-b/) |
| Super Micro Computer  Inc. | MBD-X11SSV-Q-O | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x11ssv-q-o](boards/super-micro-computer-inc.-mbd-x11ssv-q-o/) |
| Super Micro Computer  Inc. | MBD-X12SCZ-TLN4F-O | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x12scz-tln4f-o](boards/super-micro-computer-inc.-mbd-x12scz-tln4f-o/) |
| Super Micro Computer  Inc. | MBD-X12SPL-F-O | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x12spl-f-o](boards/super-micro-computer-inc.-mbd-x12spl-f-o/) |
| Super Micro Computer  Inc. | MBD-X12STL-F-O | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x12stl-f-o](boards/super-micro-computer-inc.-mbd-x12stl-f-o/) |
| Super Micro Computer  Inc. | MBD-X13SAE-F-O | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x13sae-f-o](boards/super-micro-computer-inc.-mbd-x13sae-f-o/) |
| Super Micro Computer  Inc. | MBD-X13SCH-F-B | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x13sch-f-b](boards/super-micro-computer-inc.-mbd-x13sch-f-b/) |
| Super Micro Computer  Inc. | MBD-X13SCL-F-O | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mbd-x13scl-f-o](boards/super-micro-computer-inc.-mbd-x13scl-f-o/) |
| Super Micro Computer  Inc. | MC0014 - PIO-E100-12T-IA | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-mc0014-pio-e100-12t-ia](boards/super-micro-computer-inc.-mc0014-pio-e100-12t-ia/) |
| Super Micro Computer  Inc. | P4X-CLX4209T-SRFBQ | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-p4x-clx4209t-srfbq](boards/super-micro-computer-inc.-p4x-clx4209t-srfbq/) |
| Super Micro Computer  Inc. | P4X-CLX4210-SRFBL | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-p4x-clx4210-srfbl](boards/super-micro-computer-inc.-p4x-clx4210-srfbl/) |
| Super Micro Computer  Inc. | P4X-CLX4210T-SRGYH | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-p4x-clx4210t-srgyh](boards/super-micro-computer-inc.-p4x-clx4210t-srgyh/) |
| Super Micro Computer  Inc. | P4X-CLX4214R-SRG1W | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-p4x-clx4214r-srg1w](boards/super-micro-computer-inc.-p4x-clx4214r-srg1w/) |
| Super Micro Computer  Inc. | P4X-CLX5218T-SRFPM | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-p4x-clx5218t-srfpm](boards/super-micro-computer-inc.-p4x-clx5218t-srfpm/) |
| Super Micro Computer  Inc. | P4X-CLX6226-SRFPP | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-p4x-clx6226-srfpp](boards/super-micro-computer-inc.-p4x-clx6226-srfpp/) |
| Super Micro Computer  Inc. | P4X-CLX6238-SRFPL | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-p4x-clx6238-srfpl](boards/super-micro-computer-inc.-p4x-clx6238-srfpl/) |
| Super Micro Computer  Inc. | P4X-CLX6248R-SRGZG | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-p4x-clx6248r-srgzg](boards/super-micro-computer-inc.-p4x-clx6248r-srgzg/) |
| Super Micro Computer  Inc. | PIO-119C-EYED | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-119c-eyed](boards/super-micro-computer-inc.-pio-119c-eyed/) |
| Super Micro Computer  Inc. | PIO-119C-FES | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-119c-fes](boards/super-micro-computer-inc.-pio-119c-fes/) |
| Super Micro Computer  Inc. | PIO-119C-HRTS | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-119c-hrts](boards/super-micro-computer-inc.-pio-119c-hrts/) |
| Super Micro Computer  Inc. | PIO-119C-TCS | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-119c-tcs](boards/super-micro-computer-inc.-pio-119c-tcs/) |
| Super Micro Computer  Inc. | PIO-128R-FMS-4 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-128r-fms-4](boards/super-micro-computer-inc.-pio-128r-fms-4/) |
| Super Micro Computer  Inc. | PIO-128R-W-FES-4 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-128r-w-fes-4](boards/super-micro-computer-inc.-pio-128r-w-fes-4/) |
| Super Micro Computer  Inc. | PIO-128R-W-HRTS-4 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-128r-w-hrts-4](boards/super-micro-computer-inc.-pio-128r-w-hrts-4/) |
| Super Micro Computer  Inc. | PIO-229BT-ASD-NODE-PI021 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-229bt-asd-node-pi021](boards/super-micro-computer-inc.-pio-229bt-asd-node-pi021/) |
| Super Micro Computer  Inc. | PIO-229BT-HNTSR5-2-PI021 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-229bt-hntsr5-2-pi021](boards/super-micro-computer-inc.-pio-229bt-hntsr5-2-pi021/) |
| Super Micro Computer  Inc. | PIO-229BT-SR5-NODE-PI021 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-229bt-sr5-node-pi021](boards/super-micro-computer-inc.-pio-229bt-sr5-node-pi021/) |
| Super Micro Computer  Inc. | PIO-6029BT-H168-01-PI021 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-6029bt-h168-01-pi021](boards/super-micro-computer-inc.-pio-6029bt-h168-01-pi021/) |
| Super Micro Computer  Inc. | PIO-619P-WTR | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-619p-wtr](boards/super-micro-computer-inc.-pio-619p-wtr/) |
| Super Micro Computer  Inc. | PIO-E50-9AP | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-e50-9ap](boards/super-micro-computer-inc.-pio-e50-9ap/) |
| Super Micro Computer  Inc. | PIO-F629P3-RTB-NODE-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-pio-f629p3-rtb-node-oto](boards/super-micro-computer-inc.-pio-f629p3-rtb-node-oto/) |
| Super Micro Computer  Inc. | SBE-820C-422-OTO | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-sbe-820c-422-oto](boards/super-micro-computer-inc.-sbe-820c-422-oto/) |
| Super Micro Computer  Inc. | SSG-6039P-E1CR16H | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-ssg-6039p-e1cr16h](boards/super-micro-computer-inc.-ssg-6039p-e1cr16h/) |
| Super Micro Computer  Inc. | SSG-6049SP | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-ssg-6049sp](boards/super-micro-computer-inc.-ssg-6049sp/) |
| Super Micro Computer  Inc. | SSG-6119P-ACR12N-1 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-ssg-6119p-acr12n-1](boards/super-micro-computer-inc.-ssg-6119p-acr12n-1/) |
| Super Micro Computer  Inc. | SSG-631E-E1CR16H-6 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-ssg-631e-e1cr16h-6](boards/super-micro-computer-inc.-ssg-631e-e1cr16h-6/) |
| Super Micro Computer  Inc. | SSG-631E-E1CR16H-7 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-ssg-631e-e1cr16h-7](boards/super-micro-computer-inc.-ssg-631e-e1cr16h-7/) |
| Super Micro Computer  Inc. | SSG-947HE1C | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-ssg-947he1c](boards/super-micro-computer-inc.-ssg-947he1c/) |
| Super Micro Computer  Inc. | SYS-1028R-WC1R | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-sys-1028r-wc1r](boards/super-micro-computer-inc.-sys-1028r-wc1r/) |
| Super Micro Computer  Inc. | SYS-111AD-HN2 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-sys-111ad-hn2](boards/super-micro-computer-inc.-sys-111ad-hn2/) |
| Super Micro Computer  Inc. | SYS-120C-TN10R-AC | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-sys-120c-tn10r-ac](boards/super-micro-computer-inc.-sys-120c-tn10r-ac/) |
| Super Micro Computer  Inc. | SYS-120C-TN10R-DC | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-sys-120c-tn10r-dc](boards/super-micro-computer-inc.-sys-120c-tn10r-dc/) |
| Super Micro Computer  Inc. | SYS-2029BT-HNT-ASD-PI021 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-sys-2029bt-hnt-asd-pi021](boards/super-micro-computer-inc.-sys-2029bt-hnt-asd-pi021/) |
| Super Micro Computer  Inc. | SYS-2029BT-HNTASD1-PI021 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-sys-2029bt-hntasd1-pi021](boards/super-micro-computer-inc.-sys-2029bt-hntasd1-pi021/) |
| Super Micro Computer  Inc. | SYS-2029BT-HNTASD3-PI021 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-sys-2029bt-hntasd3-pi021](boards/super-micro-computer-inc.-sys-2029bt-hntasd3-pi021/) |
| Super Micro Computer  Inc. | SYS-521AD-TN2 | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-sys-521ad-tn2](boards/super-micro-computer-inc.-sys-521ad-tn2/) |
| Super Micro Computer  Inc. | SYS-E300-8D | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-sys-e300-8d](boards/super-micro-computer-inc.-sys-e300-8d/) |
| Super Micro Computer  Inc. | X11DPH-T, CSE-836BTS-R1K23BP | amd64 | TBD | TBD | [boards/super-micro-computer-inc.-x11dph-t-cse-836bts-r1k23bp](boards/super-micro-computer-inc.-x11dph-t-cse-836bts-r1k23bp/) |
| Xilinx | A-U55C-P00G-PQ-G |  | TBD | TBD | [boards/xilinx-a-u55c-p00g-pq-g](boards/xilinx-a-u55c-p00g-pq-g/) |
