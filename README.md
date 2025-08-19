# IOTCONNECT Snap – Example Applications

[![arch-arm64](https://img.shields.io/badge/arm-arm64-informational)](#)
[![arch-amd64](https://img.shields.io/badge/x86_64-amd64-informational)](#)
[![arch-armhf](https://img.shields.io/badge/arm-armhf-informational)](#)

Sample apps and reference snippets for the **IOTCONNECT Snap**  
→ Snap repo: https://github.com/avnet-IOTCONNECT/iotc-python-lite-snap

These examples show how to send telemetry, receive commands, and perform OTA updates with **Avnet IOTCONNECT** on Linux edge devices.

---

## Why this repo?

- **Architecture-first:** Works on **arm64 / amd64 / armhf** (Ubuntu/Debian with snapd).
- **Hardware-friendly:** Validated on a growing set of **Avnet Embedded ecosystem** boards, but designed to work broadly on compatible devices.
- **Copy-pasteable samples:** Minimal code you can reuse in your own apps (Python and shell).

---

## Quick start

```bash
# 1) Ensure snapd is installed
sudo apt update && sudo apt install -y snapd

# 2) Install the IOTCONNECT Snap
sudo snap install iotconnect

# 3) One-time setup (provide your IOTCONNECT credentials/config)
IOTCONNECT.setup

# 4) Run the socket service or a sample
iotconnect.socket-run   # start the socket listener
# or:
python3 examples/00-hello-telemetry/hello_telemetry.py
```
> The snap includes CLI helpers like `iotconnect.run`, `iotconnect.setup`, `iotconnect.socket`, and `iotconnect.socket-run`.

---

## Examples

```
examples/
  00-hello-telemetry/        # smallest JSON telemetry sender
  01-command-listener/       # listens for IoTConnect commands (stub)
  02-ota-script-update/      # simulate OTA file/script update workflow (guide)
  boards/
    bb400/                   # Brainboxes BB-400: link-out + notes
    advantech-rsb3810/       # RSB-3810: network + simple sensor demo (guide)
    asus-tinker3n/           # Tinker Board 3N: telemetry + command demo (guide)
    engicam-icore-mx95/      # i.MX95 SoM: minimal edge-AI + telemetry (guide)
    toradex-verdin-imx95/    # Verdin i.MX95: OTA + telemetry (guide)
    iei-hyper-asl/           # HYPER-ASL: x86 gateway (guide)
    gigaipc-pico-n97a/       # PICO-N97A: x86 gateway (guide)
    avnet-msc-sm2s-imx95/    # MSC SM2S-IMX95 + SMARC base (guide)
    dfi-adn171/              # ADN171/ADN173 Mini-ITX (guide)
    ibase-ib839/             # IB839 3.5" (guide)
    avalue-ecm-ehl3/         # ECM-EHL3 3.5" (guide)
    kontron-35-sbc-rpl/      # 3.5"-SBC-RPL (guide)
```

---

## Supported OS & architectures

- **Architectures:** `arm64`, `amd64`, `armhf`  
- **Recommended OS:** Ubuntu 22.04/24.04 LTS, Debian 12 (Bookworm), Raspberry Pi OS (armhf) with `snapd` enabled

> If your device runs one of the above and has internet connectivity, you can usually run the IoTConnect Snap.

---

## Validated boards (growing list)

| Brand (Avnet Embedded ecosystem) | Model | Arch | Status | Notes |
|---|---|---:|---|---|
| Advantech | [RSB-3810 (Pico-ITX)](https://www.advantech.com/en-us/products/5912096e-f242-4b17-993a-1acdcaada6f6/rsb-3810/mod_5e027854-f47d-45e5-bac2-0413929f345d) | arm64 | ✅ Validated | Ubuntu/Debian; snap + pip OK |
| ASUS IoT | [Tinker Board 3N](https://tinker-board.asus.com/series/tinker-board-3N.html) | arm64 | ✅ Validated | Debian; dual LAN gateway demos |
| IEI | [HYPER-ASL (Pico-ITX)](https://www.ieiworld.com/en/product/model.php?II=1100) | amd64 | ✅ Validated | x86; smooth snap install |
| GIGAIPC | [PICO-N97A](https://www.gigaipc.com/en/products-detail/pico-N97A/) | amd64 | ✅ Validated | Intel N97; field gateway |
| Engicam | [i.Core MX95 SoM + carrier](https://www.engicam.com/vis-prod/iCore-MX95/iCore-MX95) | arm64 | 🧪 In progress | Yocto/Ubuntu rootfs |
| Avnet Embedded (MSC) | [SM2S-IMX95 + SMARC base](https://embedded.avnet.com/product/msc-sm2s-imx95/) | arm64 | 🧪 In progress | SMARC dev kit |
| Toradex | [Verdin i.MX95 EVK](https://www.toradex.com/computer-on-modules/verdin-arm-family/nxp-imx95-evaluation-kit) | arm64 | 🧪 In progress | TorizonCore / Debian |
| Brainboxes | [BB-400](https://www.brainboxes.com/product/industrial-edge-controller/bb-400) | armhf | ✅ Validated | Example in `boards/bb400/` |

> Don’t see your board? It may still work. Try the Quick Start and open an issue or PR to add it below.

---

## Hardware partners (Avnet Embedded suppliers)

*Advantech, IEI, Avalue, Engicam, Kontron, MSI Rugged Tablet, GIGAIPC, ASRock Industrial, ASUS IoT, DFI, iBASE, Mitac*  
This repo prioritizes examples for the Avnet Embedded ecosystem. Contributions covering additional boards are welcome.

---

## Add your board (easy path)

1. Create `boards/<vendor>-<model>/README.md` with:
   - CPU/arch, OS image link, tested kernel
   - Network steps (Ethernet/Wi‑Fi/5G)
   - How you ran `IOTCONNECT.setup`, and which examples you used
   - Any quirks

2. Add a minimal demo script in that folder (copy from `00-hello-telemetry`).

3. Append a new row to the **Validated boards** table above.

**Optional:** Add your board to `boards.yml` so we can auto-render the table later.

```yaml
- vendor: Advantech
  model: RSB-3810
  arch: arm64
  os: Ubuntu 22.04
  status: validated
  examples:
    - path: boards/advantech-rsb3810
      features: [telemetry, commands]
```

---

## Troubleshooting

- **snapd not found** → `sudo apt install snapd`  
- **No telemetry visible** → check device credentials in `iotconnect.setup` and ensure outbound HTTPS/MQTT are open  
- **armhf Python deps** → prefer the **Snap** path; if you use `pip`, make sure Python ≥3.8 and OpenSSL are available

---

## Contributing

PRs welcome! Please:
- Keep examples small and focused.
- Include a `README.md` in each board folder.
- Share logs or screenshots when marking a board “validated.”

---

## License

MIT — see [LICENSE](LICENSE).