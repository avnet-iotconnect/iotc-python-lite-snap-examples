# Contributing

Thanks for your interest in contributing!

## How to add a new board

1. Create a folder under `boards/<vendor>-<model>/` and add a `README.md` with:
   - CPU/arch, OS image link, kernel version
   - Network steps (Ethernet/Wi‑Fi/5G)
   - Steps to install the `IOTCONNECT` snap and run `IOTCONNECT.setup`
   - How to run one or more exampfles from `/examples`
   - Known issues / quirks

2. If you add code, prefer small, focused examples in the new folder, or contribute to `/examples`.

3. Update `boards.yml` with your board’s metadata (optional but encouraged).

4. Submit a Pull Request. Include logs/screenshots if you mark a board “validated.”