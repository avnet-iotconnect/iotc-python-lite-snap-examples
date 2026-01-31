# Kontron 3.5"-SBC-RPL

    - **Arch:** amd64
    - **Recommended OS:** Ubuntu/Debian
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://www.kontron.com/en/products/3.5--sbc-rpl/p182552

    ### OS images & docs
    - 3.5"-SBC-RPL product page: https://www.kontron.com/en/products/3.5--sbc-rpl/p182552
- Datasheet (PDF): https://www.kontron.com/downloads/datasheets/3/3d5-sbc-rpl-datasheet-20250410.pdf?product=182552

    ## Known quirks
    - For 13th‑Gen Intel Core U‑Series, use Ubuntu 24.04 or a HWE kernel on 22.04 for full iGPU/NIC support.
- Disable Secure Boot if you run custom kernels or unsigned DKMS Wi‑Fi drivers.

    ## Notes
    - x86 gateway guide
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.