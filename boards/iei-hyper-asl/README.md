# IEI HYPER-ASL (Pico-ITX)

    - **Arch:** amd64
    - **Recommended OS:** Ubuntu/Debian
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://www.ieiworld.com/en/product/model.php?II=1100

    ### OS images & docs
    - Product datasheet (PDF): https://www.ieiworld.com/_pdf/product/jp/1100.pdf

    ## Known quirks
    - On some BIOS versions, Secure Boot may block unsigned bootloaders; disable Secure Boot for easiest Ubuntu installs.
- Verify Intel i226/i219 LAN driver versions on Ubuntu 22.04/24.04; update kernel if link issues occur.

    ## Notes
    - x86 gateway guide
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.