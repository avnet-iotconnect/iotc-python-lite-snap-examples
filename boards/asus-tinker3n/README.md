# ASUS IoT Tinker Board 3N

    - **Arch:** arm64
    - **Recommended OS:** Debian
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://tinker-board.asus.com/series/tinker-board-3N.html

    ### OS images & docs
    - Official Debian 11 images (Tinker Board 3N): https://tinker-board.asus.com/download-list.html?product=tinker-board-3n
- Support portal (drivers & tools): https://www.asus.com/networking-iot-servers/aiot-industrial-solutions/tinker-board-series/tinker-board-3n/helpdesk_download?model2Name=Tinker-Board-3N

    ## Known quirks
    - Enable `snapd` on Debian (`sudo apt install snapd apparmor`), then reboot to activate AppArmor.
- Some GPIO/serial overlays may be disabled by default; check device tree overlays if you need UART or I2C.

    ## Notes
    - Telemetry + command demo
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.