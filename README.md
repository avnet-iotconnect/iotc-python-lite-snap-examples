# Avnet /IOTCONNECT Snap – Example Applications

This repository contains working example applications for the Avnet **`iotconnect` Snap**, which bundles the /IOTCONNECT Python Lite SDK and REST CLI into a single, portable package for Linux systems that support Snapcraft.

Use these examples to:

- Onboard devices to /IOTCONNECT using the `iotconnect` Snap.
- Send and receive telemetry and commands.
- Stream custom telemetry from external applications via a UNIX socket.
- Experiment with OTA-delivered models and scripts in the Snap’s persistent data area.

The catalog is designed to grow over time as new boards and suppliers are validated.

## 1. Prerequisites

Before running any examples you should have:

1. **A Linux system with `snapd` enabled**

2. **The Avnet `iotconnect` Snap installed**
   ```bash
   sudo apt update && sudo apt install -y snapd
   sudo snap install iotconnect
   ```

3. **An /IOTCONNECT account**

## 2. Quick Start: Hello Telemetry
```bash
git clone https://github.com/avnet-iotconnect/iotc-python-lite-snap-examples.git
cd iotc-python-lite-snap-examples
git checkout master
iotconnect.setup
python3 examples/00-hello-telemetry/hello_telemetry.py
```

## 3. Repository Layout
- `examples/` – runnable examples by board  
- `scripts/` – utilities  
- `archive/` – older samples  
- `LICENSE`

## 4. Board & Supplier Catalog
Full catalog is in `BOARD_CATALOG.md`.

## 5. How to Use Examples
Each example has its own README and instructions.

## 6. Related /IOTCONNECT Repositories
- `iotc-python-lite-sdk`
- `iotc-python-lite-sdk-demos`
- `iotc-python-sdk`
- `iotc-python-rest-api`
- `avnet-iotconnect.github.io`

## 7. Contributing
- Add board-specific details to example folders  
- Update board catalog when adding new platforms

## 8. License
MIT License  
