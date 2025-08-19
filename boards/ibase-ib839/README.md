# iBASE IB839 (3.5")

    - **Arch:** amd64
    - **Recommended OS:** Ubuntu/Debian
    - **Snap install:** `sudo snap install iotconnect`
    - **Setup:** `iotconnect.setup`

    ## Test telemetry

    ```bash
    python3 ../../examples/00-hello-telemetry/hello_telemetry.py
    ```

    ## Official links
    - Product page: https://www.ibase.com.tw/en/product/category/Embedded_Computing/Single_Board_Computer/x86_based_3_5_Single_Board_Computer/IB839

    ### OS images & docs
    - IB839 product page (TW site): https://www.ibase.com.tw/en/product/category/Embedded_Computing/Single_Board_Computer/x86_based_3_5_Single_Board_Computer/IB839
- IB839 product page (US site): https://www.ibase-usa.com/en/product/category/Embedded_Computing/Single_Board_Computer/x86_based_3_5_Single_Board_Computer/IB839

    ## Known quirks
    - If using Intel x7000RE NICs, stay on a recent kernel (Ubuntu 24.04 recommended).
- Install `snapd` then reboot before installing the IoTConnect snap.

    ## Notes
    - x86 gateway guide
    - If the script cannot find the IoTConnect socket, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock` and re-run.