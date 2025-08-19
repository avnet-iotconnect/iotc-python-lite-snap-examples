# GIGAIPC PICO-N97A

    - **Arch:** amd64
    - **Recommended OS:** Ubuntu/Debian
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://www.gigaipc.com/en/products-detail/pico-N97A/

    ### OS images & docs
    - Product page (specs, manuals): https://www.gigaipc.com/en/products-detail/pico-N97A/

    ## Known quirks
    - If using M.2 Wi‑Fi, ensure the module’s Linux drivers are present; Realtek chipsets may require DKMS packages.
- For Debian 12, install `snapd` and reboot once before installing the IoTConnect snap.

    ## Notes
    - x86 gateway guide
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.