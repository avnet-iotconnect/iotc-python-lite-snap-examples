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

## Board Catalog (with official product URLs attached)
| Supplier | Model | Arch | Processor | AI acceleration | Folder |
|---|---|---:|---|---|---|
| AAEON | BOXER-8221AI |  | NVIDIA Jetson Nano | TBD | [boards/aaeon-boxer-8221ai](boards/aaeon-boxer-8221ai/) |
| ADLINK | DLAP-211-JT2 |  | NVIDIA Jetson TX2 NX | TBD | [boards/adlink-httpswww.adlinktech.comproductsdeep_learning_accelerator_platform_and_serverinference_platformdlap-211-jt2](boards/adlink-httpswww.adlinktech.comproductsdeep_learning_accelerator_platform_and_serverinference_platformdlap-211-jt2/) |
| Advantech | MIC-733-AO |  | NVIDIA Jetson AGX Orin | TBD | [boards/advantech-httpswww.advantech.comen-usproducts965e4edb-fb98-429e-89ed-9a0a8435a7bemic-733mod_09861425-4950-46ab-ad39-1b5522881218](boards/advantech-httpswww.advantech.comen-usproducts965e4edb-fb98-429e-89ed-9a0a8435a7bemic-733mod_09861425-4950-46ab-ad39-1b5522881218/) |
| Advantech | SOM-9461ES0C-MA2E | amd64 | Intel Atom x5-E8000 | TBD | [boards/advantech-som-9461es0c-ma2e](boards/advantech-som-9461es0c-ma2e/) |
| Advantech | SOM-C350C5R-U9A1 | amd64 | Intel 13th Gen Core (Raptor Lake) | Intel Iris Xe (integrated) | [boards/advantech-som-c350c5r-u9a1](boards/advantech-som-c350c5r-u9a1/) |
| Advantech | UNO137E13BA2103-T | amd64 | Intel Atom E3940 | TBD | [boards/advantech-uno137e13ba2103-t](boards/advantech-uno137e13ba2103-t/) |
| Advantech | USM5002311-CT | amd64 | TBD | TBD | [boards/advantech-usm5002311-ct](boards/advantech-usm5002311-ct/) |
| Advantech | USM5002432-CT | amd64 | TBD | TBD | [boards/advantech-usm5002432-ct](boards/advantech-usm5002432-ct/) |
| ASUS IoT | PE3000G |  | TBD | TBD | [boards/asus-iot-pe3000g](boards/asus-iot-pe3000g/) |
