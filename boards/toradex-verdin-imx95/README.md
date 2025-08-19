# Toradex Verdin i.MX95 EVK

    - **Arch:** arm64
    - **Recommended OS:** TorizonCore / Debian
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://www.toradex.com/computer-on-modules/verdin-arm-family/nxp-imx95-evaluation-kit

    ### OS images & docs
    - TorizonCore download links (Toradex Easy Installer): https://developer.toradex.com/software/toradex-embedded-software/toradex-download-links-torizon-linux-bsp-wince-and-partner-demos/

    ## Known quirks
    - TorizonCore is container-focused; `snapd` is not installed by default. Prefer running your app in a Debian container using `pip install iotconnect`.
- If you require snaps, use a vanilla Ubuntu Server arm64 image (experimental) or containerize the Python SDK instead.

    ## Notes
    - OTA + telemetry guide
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.