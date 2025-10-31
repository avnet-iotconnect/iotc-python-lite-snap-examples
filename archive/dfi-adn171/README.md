# DFI ADN171/ADN173 (Mini-ITX)

    - **Arch:** amd64
    - **Recommended OS:** Ubuntu/Debian
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://www.dfi.com/product/index/1626

    ### OS images & docs
    - DFI ADN171/ADN173 product page: https://www.dfi.com/product/index/1626
- DFI America eStore (ADN171 SKU listings): https://dfi-america.com/estore/product-category/our-store/page/2/?filtering=1&highlight_filter=on_sale&max_price=740&min_price=370

    ## Known quirks
    - Enable `snapd` on Debian and ensure UEFI boot mode is set (CSM can cause install hiccups).
- Dual 2.5GbE NICs may require newer kernels for optimal performance on Ubuntu 22.04.

    ## Notes
    - x86 gateway guide
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.