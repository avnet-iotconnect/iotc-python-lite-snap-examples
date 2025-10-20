# PIC64GX1000 Curiosity Kit + /IOTCONNECT Snap — End-to-End Guide

This guide takes a first-time user from unboxing the **Microchip PIC64GX1000 Curiosity board** to:

* Booting Ubuntu and connecting it to **/IOTCONNECT** via the official Snap.
* Adding a **mikroBUS™ PHT Click (MS8607 sensor)** and streaming its telemetry to **/IOTCONNECT**.

Everything below is **copy-paste friendly**. When in doubt, confirm jumper/DIP positions against the PCB silkscreen and your board’s user guide.

---

## 0️⃣ What You Need

* PIC64GX1000 Curiosity Kit (USB-C cable included)
* Host PC (Linux/macOS/Windows) with USB-C and an SD card reader (if using microSD)
* Ubuntu image for PIC64GX (e.g. `ubuntu-24.04.x-preinstalled-server-riscv64+pic64gx.img.xz`)
* Ethernet with DHCP
* *(Optional)* microSD card (≥16 GB) for SD boot
* *(Optional)* mikroE PHT Click (MS8607) for humidity/pressure/temperature

---

## 1️⃣ Board Setup (Power, Console, Boot Source)

### Power & USB-C

* Use the **DEBUG/PROG USB-C connector** for both power and console.
* If powering from a barrel jack (J7), set jumper J47 accordingly — do **not** power via USB-C simultaneously.

### Serial Console

On your PC, open a serial terminal at **115200 8N1**:

```bash
sudo apt install -y screen
screen /dev/ttyACM0 115200
```

(Your port may appear as `/dev/ttyUSB*` or `/dev/ttyACM*`.)

### Networking

* Connect Ethernet (RJ-45). DHCP is recommended.

### DIP & Jumpers

* Factory defaults are fine for Ubuntu boot.
* If booting from SD, match the silkscreen legend for BOOT source.
* Ensure **HSS Bootloader 2024.06+** is installed.

---

## 2️⃣ Put Ubuntu on the Board

You can boot from **eMMC** or **microSD**.

### Option A — eMMC via HSS USB Mass-Storage

Plug the board into your host; the HSS presents a USB disk (`/dev/sdX`).

```bash
xzcat ubuntu-24.04.x-preinstalled-server-riscv64+pic64gx.img.xz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
sudo eject /dev/sdX
```

Then power-cycle the board and keep the console open.

### Option B — microSD

Flash the same image to your microSD card:

```bash
xzcat ubuntu-24.04.x-preinstalled-server-riscv64+pic64gx.img.xz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
```

Set **BOOT to SD**, power-cycle, and watch the console.

### First Boot

* Login as `ubuntu` and set your password.
* Verify networking with `ip a` (should show `eth0`).

---

## 3️⃣ Update Ubuntu & Install Basics

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

Optional but useful:

```bash
sudo apt install -y i2c-tools device-tree-compiler python3-pip
```

---

## 4️⃣ Install and Provision the /IOTCONNECT Snap

### Install

```bash
sudo snap install iotconnect
```

### Provision

```bash
iotconnect.setup
# or, if needed
sudo snap run iotconnect.setup
```

Choose **Manual** (paste credentials) or **Automated** (API key).

Device config/certs are stored under `$SNAP_COMMON` (typically `/var/snap/iotconnect/common`).

### Start the Socket Bridge

```bash
# Foreground (debug)
snap run iotconnect.socket

# Background (service)
sudo snap start iotconnect.socket
sudo snap logs iotconnect.socket -f
```

**Expected log:**

```
[IOTCONNECT] SDK Connected.
[SOCKET] Listening on /var/snap/iotconnect/common/iotc.sock
[COMMAND-SOCKET] Listening on /var/snap/iotconnect/common/iotc_cmd.sock
```

**Socket Paths:**

* TX (telemetry): `/var/snap/iotconnect/common/iotc.sock`
* RX (commands): `/var/snap/iotconnect/common/iotc_cmd.sock`

---

## 5️⃣ (Optional) Enable I²C for mikroBUS

If your image doesn’t already expose `/dev/i2c-*`, enable it with an overlay.

```bash
sudo apt install -y i2c-tools device-tree-compiler python3-pip python3-smbus2

# 1) Overlay to mark I2C A/B "okay"
cat <<'DTS' | sudo tee /boot/enable-i2c-ab.dts >/dev/null
/dts-v1/;
/plugin/;
/ {
    compatible = "microchip,pic64gx1000", "riscv";
    fragment@0 { target-path = "/soc/i2c@2010a000"; __overlay__ { status = "okay"; clock-frequency = <100000>; }; };
    fragment@1 { target-path = "/soc/i2c@2010b000"; __overlay__ { status = "okay"; clock-frequency = <100000>; }; };
};
DTS

sudo dtc -@ -I dts -O dtb -o /boot/enable-i2c-ab.dtbo /boot/enable-i2c-ab.dts
sudo dtc -I fs -O dtb -o /boot/board-base.dtb /proc/device-tree
sudo fdtoverlay -i /boot/board-base.dtb -o /boot/board-i2c.dtb /boot/enable-i2c-ab.dtbo
echo 'devicetree /boot/board-i2c.dtb' | sudo tee /boot/grub/custom.cfg
sudo update-grub
sudo reboot
```

**Verify:**

```bash
ls -l /dev/i2c-*
sudo i2cdetect -y 0
```

You should see `0x40` and `0x76` once the PHT Click is attached.

---

## 6️⃣ Add the PHT Click (MS8607) and Stream Telemetry

### 6.1 Hardware

* Power off, seat the PHT Click in mikroBUS (A or B) with correct orientation.
* Power on and verify I²C addresses:

```bash
sudo i2cdetect -y 0
```

You should see `0x40` and `0x76`.

### 6.2 Install Runtime Libs

```bash
pip3 install --break-system-packages smbus2
```

### 6.3 Telemetry Bridge Script

Create `/home/ubuntu/pht_iotc_socket.py` and paste the full Python script from the guide.

Run it:

```bash
sudo snap start iotconnect.socket
python3 pht_iotc_socket.py
```

You should see output like:

```
TX: {'timestamp': 1700000000, 'PHT_temp': 30.8, 'PHT_pressure': 995.2, 'PHT_humidity': 24.6, 'PHT_die_temp': 31.1}
```

Check the **/IOTCONNECT portal** for live telemetry.

---

## 7️⃣ Troubleshooting

| Issue                         | Fix                                                                          |              |     |       |
| ----------------------------- | ---------------------------------------------------------------------------- | ------------ | --- | ----- |
| No serial                     | Try another USB-C cable/port; `dmesg                                         | grep -E 'tty | ACM | USB'` |
| HSS USB disk shows `/dev/sg*` | Write to `/dev/sdX` (not `/dev/sgY`) — use `lsblk`                           |              |     |       |
| No `/dev/i2c-*`               | Redo overlay + reboot; `sudo dmesg                                           | grep -i i2c` |     |       |
| No `0x40`/`0x76`              | Reseat Click; verify 3.3 V on mikroBUS                                       |              |     |       |
| Socket errors                 | Ensure `iotconnect.socket` is running; `sudo snap logs iotconnect.socket -f` |              |     |       |

---

## Appendix — Minimal Telemetry Test (No Sensor)

```python
import socket, json, time
sock = "/var/snap/iotconnect/common/iotc.sock"
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
    s.connect(sock)
    s.sendall(json.dumps({"hello": "IOTCONNECT", "ts": int(time.time())}).encode())
    s.shutdown(1)
print("sent")
```
