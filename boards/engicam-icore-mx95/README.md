# Engicam i.Core MX95 SoM + carrier

    - **Arch:** arm64
    - **Recommended OS:** Yocto/Ubuntu rootfs
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://www.engicam.com/vis-prod/iCore-MX95/iCore-MX95

    ### OS images & docs
    - i.Core MX95 product page: https://www.engicam.com/vis-prod/iCore-MX95/iCore-MX95
- SmarCore MX95 (SMARC) – docs & starter kit: https://www.engicam.com/vis-prod/SmarCore-MX95/SmarCore-iMX95

    ## Known quirks
    - Yocto BSP is typical; for snap usage, consider an Ubuntu 22.04 arm64 rootfs on the carrier (advanced).
- If staying on vendor Yocto, prefer the Python `pip install iotconnect` path instead of snap.

    ## Notes
    - Edge AI + telemetry guide
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.