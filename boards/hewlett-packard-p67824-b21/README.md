# P67824-B21

- **Supplier:** Hewlett Packard
- **Arch:** amd64
- **Processor:** Intel® Xeon® Silver 4510, 12‑core, 2.4 GHz (Intel 7), 150 W; FCLGA4677
- **AI acceleration:** —
- **Form factor:** CPU kit (for HPE servers)
- **OS support:** OS‑dependent (x86‑64 CPU)
- **Description:** Processor option kit for Gen11 platforms.
- **Snap install:** `sudo snap install iotconnect`
- **Setup:** `iotconnect.setup`

## Official links
- Product page: (add link)

### OS images & docs
- (none listed)

## Buy
- Buy on Avnet: https://www.avnet.com/shop/us/search/?text=P67824-B21
- Buy on Newark: https://www.newark.com/search?st=P67824-B21

## Known quirks
- Install `snapd` (and `apparmor` on Debian/armhf), then reboot before installing snaps.
- If the IOTCONNECT socket path differs, set `IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock`.

## Quick test
```bash
python3 ../../examples/00-hello-telemetry/hello_telemetry.py
```
