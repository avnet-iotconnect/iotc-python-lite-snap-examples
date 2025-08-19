# Advantech RSB-3810

    - **Arch:** arm64
    - **Recommended OS:** Ubuntu/Debian
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://www.advantech.com/en-us/products/5912096e-f242-4b17-993a-1acdcaada6f6/rsb-3810/mod_5e027854-f47d-45e5-bac2-0413929f345d

    ### OS images & docs
    - Ubuntu Certified (22.04 LTS) announcement: https://canonical.com/blog/advantech-rsb-3810-mediatek-genio-ubuntu-certified
- Advantech eStore listing (Ubuntu support noted): https://buy.advantech.com/Boards-Cards/ARM-RISC-Solutions-RISC-Boards/model-RSB-3810CO-FCA1E.htm

    ## Known quirks
    - Wi‑Fi depends on the M.2 E‑key module you choose; install matching firmware (e.g., `linux-firmware` packages).
- If using Debian instead of Ubuntu, install `snapd` explicitly and reboot before running the snap.

    ## Notes
    - Gateway demo guide
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.