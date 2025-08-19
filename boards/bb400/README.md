# Brainboxes BB-400

    - **Arch:** armhf
    - **Recommended OS:** Debian / Raspbian
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://www.brainboxes.com/product/industrial-edge-controller/bb-400

    ### OS images & docs
    - BB-400 Quick Start Guide (PDF): https://www.brainboxes.com/files/catalog/product/BB/BB-400/documents/BB%20QSG%202019.pdf
- Networking configuration docs: https://www.brainboxes.com/faq/bb-400-networking-tab

    ## Known quirks
    - Older images may ship with outdated OpenSSL—`sudo apt update && sudo apt full-upgrade` before installing `snapd`.
- On Raspberry Pi OS (armhf), enable AppArmor (`sudo apt install apparmor`) and reboot before installing snaps.

    ## Notes
    - Link-out example
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.

### External reference
- Working BB-400 examples: https://github.com/mlamp99/iotc-python-lite-snap-examples
