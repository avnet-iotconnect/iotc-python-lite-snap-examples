# Avalue ECM-EHL3 (3.5")

    - **Arch:** amd64
    - **Recommended OS:** Ubuntu/Debian
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://www.avalue.com/en/product/Industrial-Embedded-Motherboard/35-SBC/ECM-EHL3

    ### OS images & docs
    - ECM-EHL3 product page (EN): https://www.avalue.com/en/product/Industrial-Embedded-Motherboard/35-SBC/ECM-EHL3
- ECM-EHL3 User's Manual (PDF): https://www.avalue.com/upload/2024_05_08/14_202405081454549qddcmw3K0.pdf

    ## Known quirks
    - Triple LAN (incl. 2.5GbE) may benefit from Ubuntu 24.04 for best driver coverage.
- Install `snapd` on Debian; confirm AppArmor is enabled for snaps.

    ## Notes
    - x86 gateway guide
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.