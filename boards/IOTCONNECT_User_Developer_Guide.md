# IoTConnect Snap — User Guide (plus Build‑Your‑Own Notes)

Connect your Linux edge device to **IOTCONNECT** with a secure, update‑friendly Snap. The `IOTCONNECT` Snap supports device provisioning, telemetry streaming, cloud‑to-device commands, and OTA delivery of models/scripts on both `amd64` and `arm64`. fileciteturn0file1

> **Who is this for?**  
> - **Snap users** who want to install and run the published `IOTCONNECT` Snap from Snapcraft and start sending telemetry / receiving commands.  
> - **Developers** (optional section at the end) who want to **build their own** Snap as a reference or for local/private distribution—**not** the public Snap Store listing for `IOTCONNECT`. fileciteturn0file2

---

## Quick Start (Snap Users)

### 1) Install the Snap
```bash
sudo snap install iotconnect
```
This installs the published `IOTCONNECT` package from the Snap Store. fileciteturn0file2

### 2) Provision your device
Run the onboarding wizard:
```bash
iotconnect.setup
# …or with elevated privileges if needed:
sudo snap run IOTCONNECT.setup
```
The wizard supports **Manual** (generate/paste credentials) and **Automated** (use a REST API key) provisioning flows. fileciteturn0file1

### 3) Choose one integration path

#### Option A — Built‑in quickstart app
Run the sample app that connects to IOTCONNECT, sends JSON telemetry on an interval (e.g., 10s), and handles cloud‑to‑device commands:
```bash
iotconnect.run    # or: snap run iotconnect.run
# Stop with Ctrl+C
```
This is a self‑contained example—no UNIX socket required. fileciteturn0file1

#### Option B — Bridge your own app via UNIX socket
Start the UNIX-socket bridge so **any external app** can push telemetry to the Snap (and read C2D commands):

**Start the socket entry:**
- **Foreground (debug):**
  ```bash
  snap run iotconnect.socket
  ```
  (Shows logs in the foreground; stop with Ctrl+C.) fileciteturn0file1
- **Background (service):**
  ```bash
  sudo snap start iotconnect.socket
  # sudo snap stop iotconnect.socket
  # sudo snap restart iotconnect.socket
  ```
  (Manage it like a daemon if your build exposes it as a service.) fileciteturn0file2

**Socket paths** (canonical):
- **Telemetry (write JSON here):** `/var/snap/iotconnect/common/iotc.sock`  
- **Commands (read JSON here):** `/var/snap/iotconnect/common/iotc_cmd.sock` fileciteturn0file1

> Tip: Some systems expose a convenience path under `~/snap/iotconnect/...`, but the canonical writable area is **`$SNAP_COMMON`** → typically `/var/snap/iotconnect/common`. fileciteturn0file2

**Send telemetry (Python example):**
```python
import socket, json

sock_path = "/var/snap/iotconnect/common/iotc.sock"
payload = {"temperature": 23.5, "status": "ok", "model_version": "v1.0.2"}

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
    s.connect(sock_path)
    s.sendall(json.dumps(payload).encode())
```
This mirrors the recommended pattern for external producers writing to the Snap’s telemetry socket. fileciteturn0file1

> There’s also a simple example script in this repo that sends telemetry to a Snap socket. If yours points to a user path (e.g., `/home/<user>/snap/iotconnect/common/iotc.sock`), swap it for the canonical `/var/snap/iotconnect/common/iotc.sock` on your system. fileciteturn0file0

**Receive commands (Python example):**
```python
import socket, json

cmd_sock_path = "/var/snap/iotconnect/common/iotc_cmd.sock"

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
    s.connect(cmd_sock_path)
    data = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        data += chunk

if data:
    command = json.loads(data.decode())
    print("Received command:", command)  # {"name": "...", "args": {...}, "ack_id": "..."}
```

---

## Where things live (persistence)

- **`$SNAP_COMMON`** (typically `/var/snap/iotconnect/common`): device configuration, certificates, OTA downloads, unpacked models/scripts, and other runtime assets.  
- This area **persists across Snap refreshes**; the application code inside the Snap itself is read‑only. fileciteturn0file2

---

## OTA updates (models/scripts)

The Snap is read‑only, so use IOTCONNECT’s OTA flows to update runtime assets:

1. Your OTA package (.tar.gz) is downloaded into **`$SNAP_COMMON`**.  
2. It’s extracted there; if present, **`install.sh`** is executed to apply the update (e.g., move models, restart processes).  
3. You’ll see logs indicating **Downloading / Extracting / Running install.sh**. fileciteturn0file1

This lets you swap models or scripts **without rebuilding the Snap**. For core application changes, build and install a new `.snap`. fileciteturn0file1

---

## Commands reference

| Command               | What it does                                                                                          |
|-----------------------|--------------------------------------------------------------------------------------------------------|
| `iotconnect.setup`    | Interactive device provisioning (Manual or Automated via REST API key).                               |
| `iotconnect.run`      | Quickstart app: connects, sends sample telemetry on an interval, handles commands; Ctrl+C to stop.    |
| `iotconnect.socket`   | UNIX‑socket bridge for external apps (telemetry in; commands out). Foreground or service mode.        |
| `iotconnect.cli`      | CLI for device/template mgmt via REST (e.g., `configure`, `create-template`, `register-device`).      |
| `iotconnect.daemon`   | Main telemetry + command handler (equivalent to running the bundled app).                              |

Descriptions above are consolidated from the original guides and examples. For CLI details, see the referenced REST CLI repo noted in the original docs. fileciteturn0file1 fileciteturn0file2

---

## Troubleshooting

- **See what’s running**
  ```bash
  snap services iotconnect
  ```
- **Tail logs**
  ```bash
  snap logs iotconnect.run -f
  snap logs iotconnect.socket -f
  ```
- **Socket path mismatch**  
  If your sample code uses a home‑dir path like `/home/<user>/snap/iotconnect/common/iotc.sock`, prefer the canonical `/var/snap/iotconnect/common/iotc.sock`. fileciteturn0file0
- **JSON payloads**  
  Ensure you send **valid JSON** over the telemetry socket; the Snap forwards well‑formed payloads upstream. fileciteturn0file1

---

# Developer Notes — Build **your** own IOTCONNECT Snap (optional)

> This section is for **developers** who want to treat this repository as a reference for building a Snap for **local use** or **your own store/namespace**. It is **not** guidance for publishing to the existing `IOTCONNECT` listing in the public Snap Store. fileciteturn0file2

## Why Snap?
- Read‑only, reproducible packaging with a persistent, writable data area (`$SNAP_COMMON`) for configs, certs, and OTA assets.  
- Works across `amd64` and `arm64`. fileciteturn0file2

## What’s in the reference repo?
A Snapcraft recipe and a quickstart demo illustrating the SDK and socket approach (use this as a pattern for your own app). fileciteturn0file2

## Build steps

1) **Clone the reference** (replace with your own origin as needed):
```bash
git clone https://github.com/avnet-iotconnect/iotc-python-lite-sdk
cd iotc-python-lite-sdk
```
2) **Edit** `snapcraft.yaml` (dependencies, plugs, apps), and add code under `src/` (e.g., your own `app.py` or a socket‑based feeder). fileciteturn0file2

3) **Build**
```bash
make build
# or
snapcraft
```
4) **Install locally**
```bash
sudo snap install iotconnect_*.snap --dangerous
```
This side‑loads your build for local testing. fileciteturn0file1 fileciteturn0file2

> **Publishing (optional)**  
> If you operate a **private/brand store** (or use a different Snap name), you may upload your build to **your** store; otherwise, keep using local side‑loads. Avoid uploading a package called `IOTCONNECT` to the public Snap Store. fileciteturn0file1

## Runtime update strategy
- Use **IOTCONNECT OTA** to deliver models/scripts into `$SNAP_COMMON` and apply via `install.sh`.  
- For core changes to the Snap itself, rebuild and reinstall your `.snap`. fileciteturn0file1

## REST CLI (optional)
The Snap exposes a CLI for REST‑level tasks such as configuring endpoints, creating templates, and registering devices (e.g., `iotconnect.cli configure`, `create-template`, `register-device`). See the reference noted in the original guide for full CLI coverage. fileciteturn0file1

---

## Publicise your Snap (badges, buttons, cards)

Snapcraft provides built‑in widgets you can embed in GitHub READMEs, docs sites, and blogs to drive installs and show release status.

### GitHub badge (stable channel)

Add this **at the top of your GitHub `README.md`**, directly under the H1 line:

```md
[![iotconnect](https://snapcraft.io/iotconnect/badge.svg)](https://snapcraft.io/iotconnect)
```

> In Snapcraft **Publicise → GitHub badges**, check **Stable channel from default track** (Trending is optional).

### Snap Store buttons (dark / light)

Use **one** of these in your README’s **Installing** section or on a website:

**Dark button (for light backgrounds):**
```md
[![Get it from the Snap Store](https://snapcraft.io/en/dark/install.svg)](https://snapcraft.io/iotconnect)
```

**Light button (for dark backgrounds):**
```md
[![Get it from the Snap Store](https://snapcraft.io/en/light/install.svg)](https://snapcraft.io/iotconnect)
```

(HTML versions are fine if your site requires `<a><img/></a>`.)

### Embeddable card (rich preview)

Use this **on a docs site or blog** (if iframes are allowed). It shows channels, version, summary, and a screenshot.

```html
<iframe
  title="Publicise card"
  src="https://snapcraft.io/iotconnect/embedded?button=black&channels=true&summary=true&screenshots=true"
  style="width: 100%; max-width: 900px; height: 600px; border: 1px solid #CCC; border-radius: 2px;"
  loading="lazy">
</iframe>
```

Options correspond to the toggles you saw:
- `button=black|white`
- `channels=true`
- `summary=true`
- `screenshots=true`

**Placement checklist**
- **README.md (GitHub):** badge at top; one Snap Store button in “Installing”.
- **Docs/blog:** button on “Install” page; embeddable card on product/overview pages.
- **Release notes / changelog posts:** include the badge or button inline.

---

## License & Support

- **License:** See the repository’s LICENSE file. fileciteturn0file2  
- **Help:** Visit IOTCONNECT online or contact Avnet support as indicated in the original guide. fileciteturn0file1

---

### Appendix: Minimal telemetry sender (example)

If you prefer a minimal stand‑alone script to push JSON to the Snap over the UNIX socket, adapt the sample below (use the **canonical** socket path on your system):

```python
import socket, json

SOCKET_PATH = "/var/snap/iotconnect/common/iotc.sock"
telemetry = {"source": "external-script", "temperature": 72.4, "status": "ok"}

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
    s.connect(SOCKET_PATH)
    s.sendall(json.dumps(telemetry).encode())

print("✅ Telemetry sent to Snap via socket.")
```

The repository’s original example uses a home‑directory path—update it to `/var/snap/iotconnect/common/iotc.sock` as shown above. fileciteturn0file0
