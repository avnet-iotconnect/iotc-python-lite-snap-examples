# Avnet Embedded (MSC) SM2S-IMX95 + SMARC base

    - **Arch:** arm64
    - **Recommended OS:** Yocto/Ubuntu
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://embedded.avnet.com/product/msc-sm2s-imx95/

    ### OS images & docs
    - MSC SM2S‑IMX95 product page: https://embedded.avnet.com/product/msc-sm2s-imx95/
- Press release / overview: https://embedded.avnet.com/25707/avnet-introduces-high-performance-sm2s-imx95-smarc-module/

    ## Known quirks
    - SMARC Starter Kit images and BSP typically require Avnet access—request via your Avnet contact.
- Snap works best with Ubuntu 22.04 rootfs on the baseboard; on Yocto, use the Python SDK (pip).

    ## Notes
    - SMARC dev kit guide
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.