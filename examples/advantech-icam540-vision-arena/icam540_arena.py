#!/usr/bin/env python3
"""
iCAM-540 Vision Arena agent for the /IOTCONNECT Snap.

One always-on process that:
  * generates a DeepStream pipeline config on the fly (camera + N looping
    video streams, PeopleNet or ResNet10, NvDCF tracker, nvdsanalytics overlay)
  * launches/stops deepstream-app and parses its per-stream FPS output
  * reads Jetson GPU/EMC/power/thermal counters from tegrastats
  * consumes DeepStream detections from MQTT and computes booth analytics
    (line-crossing visitor counts, zone occupancy, dwell/engagement time)
  * publishes flat telemetry to the snap telemetry socket
  * executes cloud commands from the snap command socket

Everything the cloud can change (stream count, model, precision, inference
interval, zone/line geometry) is applied by regenerating the config and
restarting the pipeline. The TensorRT engine is cached so a restart is seconds.
"""

import argparse
import glob
import json
import math
import os
import pty
import re
import select
import shlex
import signal
import socket
import subprocess
import sys
import threading
import time
from collections import Counter, deque

HERE = os.path.dirname(os.path.abspath(__file__))
DS_ROOT_DEFAULT = "/opt/nvidia/deepstream/deepstream"
DS_ROOT = os.environ.get("DS_ROOT", DS_ROOT_DEFAULT).rstrip("/") or DS_ROOT_DEFAULT


def ds_path(path):
    """Honour a DS_ROOT override for paths written against the stock install prefix."""
    if DS_ROOT != DS_ROOT_DEFAULT and path.startswith(DS_ROOT_DEFAULT + "/"):
        return DS_ROOT + path[len(DS_ROOT_DEFAULT):]
    return path

SAMPLE_STREAM_CANDIDATES = [
    "samples/streams/sample_1080p_h264.mp4",
    "samples/streams/sample_walk.mov",
    "samples/streams/sample_720p.mp4",
    "samples/streams/sample_ride_bike.mov",
    "samples/streams/sample_run.mov",
    "samples/streams/sample_push.mov",
    "samples/streams/sample_cam6.mp4",
    "samples/streams/sample_qHD.mp4",
    "samples/streams/sample_1080p_h265.mp4",
]

TRACKER_CONFIG_CANDIDATES = [
    "samples/configs/deepstream-app/config_tracker_NvDCF_perf.yml",
    "samples/configs/deepstream-app/config_tracker_NvDCF_max_perf.yml",
    "samples/configs/deepstream-app/config_tracker_IOU.yml",
]

MODELS = {
    "peoplenet": {
        "title": "PeopleNet (TAO ResNet-34)",
        "infer_base": os.path.join(HERE, "config_infer_peoplenet_base.txt"),
        "labels": os.path.join(DS_ROOT, "samples/models/PeopleNet/labels.txt"),
    },
    "resnet10": {
        "title": "ResNet-10 4-class (Car/Bicycle/Person/Roadsign)",
        "infer_base": os.path.join(DS_ROOT, "samples/configs/deepstream-app/config_infer_primary.txt"),
        "labels": os.path.join(DS_ROOT, "samples/models/Primary_Detector/labels.txt"),
    },
}

PRECISION_MODE = {"fp32": "0", "int8": "1", "fp16": "2"}
MODE_PRECISION = {v: k for k, v in PRECISION_MODE.items()}

PERSON_LABELS = {"person", "people", "pedestrian"}
VEHICLE_LABELS = {"car", "vehicle", "bicycle", "bus", "truck", "motorbike", "motorcycle", "van"}

PRESETS = {
    "booth": {"streams": 1},
    "stress": {"streams": 4},
    "max": {"streams": 9},
}

DEFAULT_ZONES = {
    "roi": [[0.20, 0.35], [0.80, 0.35], [0.95, 0.98], [0.05, 0.98]],
    "line": {"p1": [0.05, 0.55], "p2": [0.95, 0.55], "dir": 1},
    "engage_s": 5.0,
    "overcrowd": 4,
}


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def log(tag, msg):
    print(f"[{tag}] {msg}", flush=True)


def pick_socket(candidates):
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None


_tx_lock = threading.Lock()


def send_json_line(sock_path, payload, timeout=2.0):
    data = (json.dumps(payload) + "\n").encode()
    with _tx_lock:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect(sock_path)
            s.sendall(data)
            try:
                s.shutdown(socket.SHUT_WR)
            except Exception:
                pass


def first_existing(paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


def read_uptime_seconds():
    try:
        with open("/proc/uptime") as f:
            return float(f.read().split()[0])
    except Exception:
        return None


def read_meminfo_mb():
    total = avail = None
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    total = int(line.split()[1]) // 1024
                elif line.startswith("MemAvailable:"):
                    avail = int(line.split()[1]) // 1024
    except Exception:
        pass
    return total, avail


def read_thermal_zones():
    """Return {type_name_lower: temp_c} from /sys/class/thermal."""
    out = {}
    for zone in glob.glob("/sys/class/thermal/thermal_zone*"):
        try:
            with open(os.path.join(zone, "type")) as f:
                name = f.read().strip().lower()
            with open(os.path.join(zone, "temp")) as f:
                raw = f.read().strip()
            val = float(raw)
            if abs(val) > 1000:
                val /= 1000.0
            out[name] = val
        except Exception:
            continue
    return out


def pick_temp(zones, *needles):
    for needle in needles:
        for name, val in zones.items():
            if needle in name:
                return round(val, 1)
    return None


class CpuLoad:
    """CPU utilisation from /proc/stat deltas."""

    def __init__(self):
        self.prev = None

    def sample(self):
        try:
            with open("/proc/stat") as f:
                parts = f.readline().split()
            vals = [int(x) for x in parts[1:]]
        except Exception:
            return None
        idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
        total = sum(vals)
        if self.prev is None:
            self.prev = (idle, total)
            return None
        d_idle = idle - self.prev[0]
        d_total = total - self.prev[1]
        self.prev = (idle, total)
        if d_total <= 0:
            return None
        return round(100.0 * (1.0 - d_idle / d_total), 1)


def spawn_pty_reader(cmd, on_line, tag, stop_event, env=None):
    """Run cmd with a pseudo-terminal for stdout/stderr so the child line-buffers.

    Returns the Popen handle. Reader thread invokes on_line(str) per line.
    """
    master, slave = pty.openpty()
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=slave,
        stderr=slave,
        close_fds=True,
        env=env,
        preexec_fn=os.setsid,
    )
    os.close(slave)

    def reader():
        buf = b""
        while not stop_event.is_set():
            try:
                r, _, _ = select.select([master], [], [], 0.5)
            except Exception:
                break
            if not r:
                if proc.poll() is not None:
                    break
                continue
            try:
                chunk = os.read(master, 4096)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                try:
                    on_line(line.decode(errors="ignore").rstrip("\r"))
                except Exception as e:  # never let a parser kill the reader
                    log(tag, f"line handler error: {e}")
        try:
            os.close(master)
        except Exception:
            pass

    t = threading.Thread(target=reader, name=f"{tag}-reader", daemon=True)
    t.start()
    return proc


def kill_process_group(proc, timeout=10.0):
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass
    try:
        proc.wait(timeout=timeout)
        return
    except Exception:
        pass
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    try:
        proc.wait(timeout=5)
    except Exception:
        pass


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            x_int = (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi
            if x < x_int:
                inside = not inside
        j = i
    return inside


def line_side(p1, p2, x, y, eps=0.004):
    """+1 if (x,y) is left of p1->p2, -1 if right, 0 if within eps of the line."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy) or 1e-9
    cross = (dx * (y - p1[1]) - dy * (x - p1[0])) / length
    if cross > eps:
        return 1
    if cross < -eps:
        return -1
    return 0


def parse_points(text):
    """'x,y;x,y;...' (normalised 0..1) -> [[x,y],...]"""
    pts = []
    for chunk in str(text).replace(" ", "").split(";"):
        if not chunk:
            continue
        xs, ys = chunk.split(",")
        x, y = float(xs), float(ys)
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            raise ValueError("coordinates must be normalised 0..1")
        pts.append([x, y])
    return pts


# --------------------------------------------------------------------------
# booth analytics (zone occupancy, dwell, line crossing)
# --------------------------------------------------------------------------

class BoothAnalytics:
    def __init__(self, zones, stale_s=1.5):
        self.lock = threading.Lock()
        self.stale_s = stale_s
        self.set_zones(zones)
        self.reset()

    def set_zones(self, zones):
        self.roi = [list(map(float, p)) for p in zones.get("roi", DEFAULT_ZONES["roi"])]
        line = zones.get("line", DEFAULT_ZONES["line"])
        self.line_p1 = list(map(float, line["p1"]))
        self.line_p2 = list(map(float, line["p2"]))
        self.line_dir = 1 if int(line.get("dir", 1)) >= 0 else -1
        self.engage_s = float(zones.get("engage_s", DEFAULT_ZONES["engage_s"]))
        self.overcrowd = int(zones.get("overcrowd", DEFAULT_ZONES["overcrowd"]))

    def zones(self):
        return {
            "roi": self.roi,
            "line": {"p1": self.line_p1, "p2": self.line_p2, "dir": self.line_dir},
            "engage_s": self.engage_s,
            "overcrowd": self.overcrowd,
        }

    def reset(self):
        with self.lock:
            self.tracks = {}
            self.visitors_in = 0
            self.visitors_out = 0
            self.occupancy_peak = 0
            self.tracks_total = 0
            self.dwells = deque(maxlen=200)
            self.last_event = ""
            self.last_event_ts = 0.0
            self.overcrowded = False
            self.untracked = False

    def _event(self, name, ts):
        self.last_event = name
        self.last_event_ts = ts

    def ingest(self, objects, ts):
        """objects: iterable of (track_id, x_norm, y_norm, label)."""
        with self.lock:
            for tid, x, y, label in objects:
                if label and label.lower() not in PERSON_LABELS:
                    continue
                if tid is None:
                    self.untracked = True
                    continue
                tr = self.tracks.get(tid)
                if tr is None:
                    tr = {"first": ts, "last": ts, "side": 0, "inside": False, "in_since": None, "x": x}
                    self.tracks[tid] = tr
                    self.tracks_total += 1
                side = line_side(self.line_p1, self.line_p2, x, y)
                if side != 0 and tr["side"] != 0 and side != tr["side"]:
                    moved = 1 if side > 0 else -1
                    if moved == self.line_dir:
                        self.visitors_in += 1
                        self._event("visitor_in", ts)
                    else:
                        self.visitors_out += 1
                        self._event("visitor_out", ts)
                if side != 0:
                    tr["side"] = side
                inside = point_in_poly(x, y, self.roi)
                if inside and tr["in_since"] is None:
                    tr["in_since"] = ts
                elif not inside and tr["in_since"] is not None:
                    self._finish_dwell(tr, ts)
                tr["inside"] = inside
                tr["last"] = ts
                tr["x"] = x
            self._expire(ts)
            occ = self._occupancy(ts)
            if occ > self.occupancy_peak:
                self.occupancy_peak = occ
            if occ >= self.overcrowd and not self.overcrowded:
                self.overcrowded = True
                self._event("overcrowded", ts)
            elif occ < self.overcrowd:
                self.overcrowded = False

    def _finish_dwell(self, tr, ts):
        if tr["in_since"] is not None:
            d = max(0.0, ts - tr["in_since"])
            if d >= 0.5:
                self.dwells.append(d)
            tr["in_since"] = None

    def _expire(self, ts):
        dead = [tid for tid, tr in self.tracks.items() if ts - tr["last"] > self.stale_s]
        for tid in dead:
            self._finish_dwell(self.tracks[tid], self.tracks[tid]["last"])
            del self.tracks[tid]

    def _fresh(self, ts):
        return [tr for tr in self.tracks.values() if ts - tr["last"] <= self.stale_s]

    def _occupancy(self, ts):
        return sum(1 for tr in self._fresh(ts) if tr["inside"])

    def snapshot(self, ts):
        with self.lock:
            self._expire(ts)
            fresh = self._fresh(ts)
            inside = [tr for tr in fresh if tr["inside"]]
            engaged = sum(1 for tr in inside if tr["in_since"] is not None and ts - tr["in_since"] >= self.engage_s)
            ongoing = [ts - tr["in_since"] for tr in inside if tr["in_since"] is not None]
            completed = list(self.dwells)
            pool = completed if completed else ongoing
            dwell_avg = round(sum(pool) / len(pool), 1) if pool else 0.0
            dwell_max = round(max(completed + ongoing), 1) if (completed or ongoing) else 0.0
            dwell_last = round(completed[-1], 1) if completed else 0.0
            hot = "none"
            if fresh:
                thirds = Counter("left" if tr["x"] < 1 / 3 else "center" if tr["x"] < 2 / 3 else "right" for tr in fresh)
                hot = thirds.most_common(1)[0][0]
            return {
                "visitors_in": self.visitors_in,
                "visitors_out": self.visitors_out,
                "occupancy": len(inside),
                "occupancy_peak": self.occupancy_peak,
                "people_now": len(fresh),
                "engaged": engaged,
                "dwell_avg_s": dwell_avg,
                "dwell_max_s": dwell_max,
                "dwell_last_s": dwell_last,
                "tracks_total": self.tracks_total,
                "hot_zone": hot,
                "event": self.last_event if ts - self.last_event_ts < 30 else "",
            }


# --------------------------------------------------------------------------
# DeepStream message parsing
# --------------------------------------------------------------------------

_META_FIELDS = {
    "id", "speed", "direction", "orientation", "bbox", "bbox2d", "rect", "location",
    "coordinate", "trackingId", "classId", "class_id", "classid", "confidence",
}


def _source_from_sensor(value):
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    m = re.search(r"(\d+)\s*$", str(value))
    return int(m.group(1)) if m else 0


def _parse_pipe_object(text):
    # "<track id>|<left>|<top>|<right>|<bottom>|<label>|#|<classifier labels...>"
    parts = text.split("|")
    if len(parts) < 6:
        return None
    try:
        tid = int(float(parts[0]))
        left, top, right, bottom = (float(v) for v in parts[1:5])
    except ValueError:
        return None
    label = parts[5].strip()
    if tid < 0 or tid >= 2 ** 63:
        tid = None
    return {"id": tid, "label": label, "bbox": (left, top, right, bottom)}


def _parse_dict_object(obj):
    label = None
    for k, v in obj.items():
        if k in _META_FIELDS:
            continue
        if isinstance(v, dict):
            label = k
            break
    if label is None:
        label = obj.get("label") or obj.get("class") or obj.get("class_name") or "unknown"
    tid = obj.get("id", obj.get("trackingId"))
    try:
        tid = int(tid) if tid is not None else None
    except (TypeError, ValueError):
        tid = None
    if tid is not None and (tid < 0 or tid >= 2 ** 63):
        tid = None
    bbox = obj.get("bbox") or obj.get("bbox2d") or obj.get("rect") or {}
    try:
        box = (
            float(bbox.get("topleftx", bbox.get("left", 0))),
            float(bbox.get("toplefty", bbox.get("top", 0))),
            float(bbox.get("bottomrightx", bbox.get("right", 0))),
            float(bbox.get("bottomrighty", bbox.get("bottom", 0))),
        )
    except Exception:
        box = (0.0, 0.0, 0.0, 0.0)
    return {"id": tid, "label": str(label), "bbox": box}


def parse_deepstream_message(msg):
    """Return (source_id, [ {id,label,bbox} ]) for any DeepStream schema variant."""
    if not isinstance(msg, dict):
        return 0, []
    source = None
    if "sensorId" in msg:
        source = _source_from_sensor(msg.get("sensorId"))
    elif isinstance(msg.get("sensor"), dict):
        source = _source_from_sensor(msg["sensor"].get("id"))
    if source is None:
        source = _source_from_sensor(msg.get("source_id", msg.get("sourceId", 0)))
    objects = []
    items = msg.get("objects")
    if isinstance(items, list):
        for it in items:
            if isinstance(it, str):
                o = _parse_pipe_object(it)
            elif isinstance(it, dict):
                o = _parse_dict_object(it)
            else:
                o = None
            if o:
                objects.append(o)
    elif isinstance(msg.get("object"), dict):
        objects.append(_parse_dict_object(msg["object"]))
    return source, objects


# --------------------------------------------------------------------------
# per-stream detection stats
# --------------------------------------------------------------------------

class StreamStats:
    def __init__(self, window_s=5.0):
        self.lock = threading.Lock()
        self.window_s = window_s
        self.msgs = deque()  # (ts, source)
        self.latest = {}  # source -> (ts, n_objects, Counter(labels))

    def ingest(self, source, objects, ts):
        labels = Counter(o["label"].lower() for o in objects)
        with self.lock:
            self.msgs.append((ts, source))
            self.latest[source] = (ts, len(objects), labels)
            cutoff = ts - self.window_s
            while self.msgs and self.msgs[0][0] < cutoff:
                self.msgs.popleft()

    def snapshot(self, ts):
        with self.lock:
            cutoff = ts - self.window_s
            while self.msgs and self.msgs[0][0] < cutoff:
                self.msgs.popleft()
            rate = round(len(self.msgs) / self.window_s, 1)
            objects = persons = vehicles = 0
            active = 0
            for src, (t, n, labels) in self.latest.items():
                if ts - t > 3.0:
                    continue
                active += 1
                objects += n
                persons += sum(c for l, c in labels.items() if l in PERSON_LABELS)
                vehicles += sum(c for l, c in labels.items() if l in VEHICLE_LABELS)
            return {
                "msgs_per_s": rate,
                "objects_total": objects,
                "persons_total": persons,
                "vehicles_total": vehicles,
                "streams_active": active,
            }


# --------------------------------------------------------------------------
# Jetson metrics (tegrastats with sysfs fallback)
# --------------------------------------------------------------------------

class JetsonMetrics:
    RE_RAM = re.compile(r"RAM (\d+)/(\d+)MB")
    RE_CPU = re.compile(r"CPU \[([^\]]*)\]")
    RE_EMC = re.compile(r"EMC_FREQ (\d+)%")
    RE_GR3D = re.compile(r"GR3D_FREQ (\d+)%(?:@\[?(\d+))?")
    RE_GPU_T = re.compile(r"\bGPU@([\d.]+)C")
    RE_CPU_T = re.compile(r"\bCPU@([\d.]+)C")
    RE_SOC_T = re.compile(r"\b(?:SOC0|soc0|tj|Tboard|thermal)@([\d.]+)C")
    RE_VDD_IN = re.compile(r"\b(?:VDD_IN|POM_5V_IN) (\d+)mW")
    RE_VDD_GPU = re.compile(r"\b(?:VDD_CPU_GPU_CV|VDD_GPU_SOC|POM_5V_GPU|VDD_GPU) (\d+)mW")
    RE_NVDEC = re.compile(r"NVDEC (\d+)")

    def __init__(self, use_sudo=True, stop_event=None):
        self.lock = threading.Lock()
        self.data = {}
        self.ts = 0.0
        self.proc = None
        self.use_sudo = use_sudo
        self.stop_event = stop_event or threading.Event()
        self.cpu = CpuLoad()
        self.source = "none"

    def start(self):
        exe = first_existing(["/usr/bin/tegrastats", "/usr/local/bin/tegrastats"])
        if exe:
            cmd = (["sudo", "-n"] if self.use_sudo and os.geteuid() != 0 else []) + [exe, "--interval", "1000"]
            try:
                self.proc = spawn_pty_reader(cmd, self._on_line, "TEGRA", self.stop_event)
                self.source = "tegrastats"
                log("TEGRA", f"started: {' '.join(cmd)}")
                threading.Thread(target=self._watchdog, name="tegra-watchdog", daemon=True).start()
                return
            except Exception as e:
                log("TEGRA", f"tegrastats failed ({e}); using sysfs fallback")
        self._start_sysfs()

    def _start_sysfs(self):
        self.source = "sysfs"
        threading.Thread(target=self._sysfs_loop, name="sysfs-metrics", daemon=True).start()

    def _watchdog(self):
        """tegrastats exiting early (sudo password prompt, unsupported board) -> sysfs."""
        self.stop_event.wait(6.0)
        if self.stop_event.is_set():
            return
        if self.proc is not None and self.proc.poll() is not None and self.ts == 0.0:
            log("TEGRA", f"tegrastats exited (code {self.proc.returncode}); using sysfs fallback")
            self.proc = None
            self._start_sysfs()

    def stop(self):
        if self.proc:
            kill_process_group(self.proc, timeout=3)
            self.proc = None
            try:
                subprocess.run(["tegrastats", "--stop"], timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def _on_line(self, line):
        if "RAM" not in line:
            return
        d = {}
        m = self.RE_RAM.search(line)
        if m:
            d["ram_used_mb"], d["ram_total_mb"] = int(m.group(1)), int(m.group(2))
        m = self.RE_CPU.search(line)
        if m:
            loads = [int(x.split("%")[0]) for x in m.group(1).split(",") if "%" in x and x.split("%")[0].isdigit()]
            if loads:
                d["cpu_load_pct"] = round(sum(loads) / len(loads), 1)
        m = self.RE_EMC.search(line)
        if m:
            d["emc_pct"] = float(m.group(1))
        m = self.RE_GR3D.search(line)
        if m:
            d["gpu_load_pct"] = float(m.group(1))
            if m.group(2):
                d["gpu_freq_mhz"] = float(m.group(2))
        m = self.RE_GPU_T.search(line)
        if m:
            d["gpu_temp_c"] = float(m.group(1))
        m = self.RE_CPU_T.search(line)
        if m:
            d["cpu_temp_c"] = float(m.group(1))
        m = self.RE_SOC_T.search(line)
        if m:
            d["soc_temp_c"] = float(m.group(1))
        m = self.RE_VDD_IN.search(line)
        if m:
            d["power_w"] = round(int(m.group(1)) / 1000.0, 2)
        m = self.RE_VDD_GPU.search(line)
        if m:
            d["power_gpu_w"] = round(int(m.group(1)) / 1000.0, 2)
        m = self.RE_NVDEC.search(line)
        if m:
            d["nvdec_mhz"] = float(m.group(1))
        with self.lock:
            self.data.update(d)
            self.ts = time.time()

    def _sysfs_loop(self):
        gpu_load_paths = [
            "/sys/devices/gpu.0/load",
            "/sys/devices/platform/gpu.0/load",
        ] + glob.glob("/sys/devices/platform/*.gpu/load") + glob.glob("/sys/devices/platform/bus@0/*.gpu/load")
        while not self.stop_event.is_set():
            d = {}
            p = first_existing(gpu_load_paths)
            if p:
                try:
                    with open(p) as f:
                        d["gpu_load_pct"] = round(int(f.read().strip()) / 10.0, 1)
                except Exception:
                    pass
            zones = read_thermal_zones()
            t = pick_temp(zones, "gpu")
            if t is not None:
                d["gpu_temp_c"] = t
            t = pick_temp(zones, "cpu")
            if t is not None:
                d["cpu_temp_c"] = t
            t = pick_temp(zones, "soc", "tj", "board", "x86_pkg")
            if t is not None:
                d["soc_temp_c"] = t
            for label_path in glob.glob("/sys/bus/i2c/drivers/ina3221/*/hwmon/hwmon*/in*_label"):
                try:
                    with open(label_path) as f:
                        name = f.read().strip()
                    idx = re.search(r"in(\d+)_label", label_path).group(1)
                    base = os.path.dirname(label_path)
                    with open(os.path.join(base, f"in{idx}_input")) as f:
                        mv = float(f.read().strip())
                    with open(os.path.join(base, f"curr{idx}_input")) as f:
                        ma = float(f.read().strip())
                    watts = round(mv * ma / 1e6, 2)
                    if name in ("VDD_IN", "POM_5V_IN"):
                        d["power_w"] = watts
                    elif name in ("VDD_CPU_GPU_CV", "VDD_GPU_SOC", "POM_5V_GPU"):
                        d["power_gpu_w"] = watts
                except Exception:
                    continue
            with self.lock:
                self.data.update(d)
                self.ts = time.time()
            self.stop_event.wait(1.0)

    def snapshot(self):
        with self.lock:
            d = dict(self.data)
            fresh = (time.time() - self.ts) < 5.0
        cpu = self.cpu.sample()
        if cpu is not None:
            d["cpu_load_pct"] = cpu
        total, avail = read_meminfo_mb()
        if total:
            d["ram_total_mb"] = total
            if avail is not None:
                d["ram_used_mb"] = total - avail
        if not fresh:
            for k in ("gpu_load_pct", "emc_pct"):
                d.pop(k, None)
        if "gpu_temp_c" not in d or "cpu_temp_c" not in d:
            zones = read_thermal_zones()
            for key, needles in (("gpu_temp_c", ("gpu",)), ("cpu_temp_c", ("cpu",)), ("soc_temp_c", ("soc", "tj", "x86_pkg"))):
                if key not in d:
                    t = pick_temp(zones, *needles)
                    if t is not None:
                        d[key] = t
        d["metrics_source"] = self.source
        return d


# --------------------------------------------------------------------------
# DeepStream config generation
# --------------------------------------------------------------------------

_PATH_KEYS = {
    "model-file", "proto-file", "model-engine-file", "int8-calib-file", "labelfile-path",
    "onnx-file", "tlt-encoded-model", "custom-lib-path", "mean-file", "uff-file",
}


def _read_kv_file(path):
    with open(path) as f:
        return f.read().splitlines()


def _engine_name(model_path, batch, mode):
    return f"{os.path.basename(model_path)}_b{batch}_gpu0_{MODE_PRECISION.get(mode, 'fp32')}.engine"


def generate_infer_config(model_key, batch, precision, out_dir):
    """Rewrite the base infer config with absolute paths, batch and precision.

    Returns (path, info) where info has the effective precision/engine path.
    """
    base = MODELS[model_key]["infer_base"]
    if not os.path.exists(base):
        raise FileNotFoundError(f"infer config not found: {base}")
    base_dir = os.path.dirname(os.path.abspath(base))
    lines = _read_kv_file(base)
    kv = {}
    for ln in lines:
        s = ln.strip()
        if "=" in s and not s.startswith("#") and not s.startswith("["):
            k, v = s.split("=", 1)
            kv[k.strip()] = v.strip()

    mode = kv.get("network-mode", "0")
    if precision != "auto":
        mode = PRECISION_MODE.get(precision, mode)
    calib = kv.get("int8-calib-file")
    if mode == "1":
        calib_abs = calib if (calib and os.path.isabs(calib)) else (os.path.join(base_dir, calib) if calib else None)
        if not calib_abs or not os.path.exists(calib_abs):
            log("CFG", "int8 requested but no calibration cache; using fp16")
            mode = "2"

    model_path = kv.get("onnx-file") or kv.get("model-file") or kv.get("tlt-encoded-model") or kv.get("uff-file") or "model"
    if not os.path.isabs(model_path):
        model_path = os.path.normpath(os.path.join(base_dir, model_path))
    model_path = ds_path(model_path)
    engine_path = os.path.join(os.path.dirname(model_path), _engine_name(model_path, batch, mode))

    out = []
    seen = set()
    in_property = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("["):
            if in_property:
                for k, v in (("batch-size", str(batch)), ("network-mode", mode), ("model-engine-file", engine_path)):
                    if k not in seen:
                        out.append(f"{k}={v}")
                out.append("")
            in_property = s.lower() == "[property]"
            out.append(ln)
            continue
        if "=" in s and not s.startswith("#"):
            k, v = s.split("=", 1)
            k = k.strip()
            v = v.strip()
            if in_property:
                if k == "batch-size":
                    v = str(batch)
                elif k == "network-mode":
                    v = mode
                elif k == "model-engine-file":
                    v = engine_path
                elif k == "int8-calib-file" and mode != "1":
                    continue  # only meaningful (and only validated) in int8 mode
                elif k in _PATH_KEYS and v:
                    if not os.path.isabs(v):
                        v = os.path.normpath(os.path.join(base_dir, v))
                    v = ds_path(v)
                seen.add(k)
            out.append(f"{k}={v}")
            continue
        out.append(ln)
    if in_property:
        for k, v in (("batch-size", str(batch)), ("network-mode", mode), ("model-engine-file", engine_path)):
            if k not in seen:
                out.append(f"{k}={v}")

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"infer_{model_key}_{MODE_PRECISION.get(mode, 'fp32')}_b{batch}.txt")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    return path, {"precision": MODE_PRECISION.get(mode, "fp32"), "engine": engine_path, "batch": batch}


def generate_msgconv_config(n_streams, out_dir):
    parts = []
    for i in range(n_streams):
        parts.append(
            f"[sensor{i}]\nenable=1\ntype=Camera\nid=ICAM540_SRC_{i}\nlocation=0;0;0\n"
            f"description=iCAM-540 {'camera' if i == 0 else 'stream ' + str(i)}\ncoordinate=0;0;0\n"
        )
    parts.append("[place0]\nenable=1\nid=0\ntype=booth\nname=ICAM540_BOOTH\nlocation=0;0;0\ncoordinate=0;0;0\n")
    parts.append("[analytics0]\nenable=1\nid=ICAM540_ARENA\ndescription=Vision Arena\nsource=DeepStream\nversion=1.0\n")
    path = os.path.join(out_dir, "msgconv.txt")
    with open(path, "w") as f:
        f.write("\n".join(parts))
    return path


def generate_analytics_config(zones, width, height, out_dir):
    roi = ";".join(f"{int(x * width)};{int(y * height)}" for x, y in zones["roi"])
    p1 = zones["line"]["p1"]
    p2 = zones["line"]["p2"]
    direction = 1 if int(zones["line"].get("dir", 1)) >= 0 else -1
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy) or 1e-9
    nx, ny = -dy / length, dx / length  # left normal of p1->p2 (positive side)
    k = 0.12
    a = (mx - nx * k * direction, my - ny * k * direction)
    b = (mx + nx * k * direction, my + ny * k * direction)
    px = lambda p: f"{int(max(0, min(1, p[0])) * width)};{int(max(0, min(1, p[1])) * height)}"
    line = f"{px(a)};{px(b)};{px(p1)};{px(p2)}"
    text = (
        "[property]\nenable=1\n"
        f"config-width={width}\nconfig-height={height}\nosd-mode=2\ndisplay-font-size=14\n\n"
        "[roi-filtering-stream-0]\nenable=1\n"
        f"roi-Booth={roi}\ninverse-roi=0\nclass-id=-1\n\n"
        "[overcrowding-stream-0]\nenable=1\n"
        f"roi-Crowd={roi}\nobject-threshold={int(zones.get('overcrowd', 4))}\nclass-id=-1\n\n"
        "[line-crossing-stream-0]\nenable=1\n"
        f"line-crossing-Entry={line}\nclass-id=-1\nextended=0\nmode=loose\n"
    )
    path = os.path.join(out_dir, "analytics.txt")
    with open(path, "w") as f:
        f.write(text)
    return path


def find_sample_streams(extra):
    streams = [s for s in extra if s]
    for rel in SAMPLE_STREAM_CANDIDATES:
        p = os.path.join(DS_ROOT, rel)
        if os.path.exists(p):
            streams.append(p)
    return streams


def generate_app_config(state, out_dir, headless=False):
    """Build the deepstream-app config for the current state. Returns (path, info)."""
    n = max(1, int(state["streams"]))
    width, height = state["mux_width"], state["mux_height"]
    os.makedirs(out_dir, exist_ok=True)

    engine_batch = 1
    if n > 1 and state.get("batched"):
        engine_batch = n
    infer_path, info = generate_infer_config(state["model"], engine_batch, state["precision"], out_dir)
    if engine_batch > 1 and not os.path.exists(info["engine"]) and not state.get("build_engines"):
        log("CFG", f"no cached engine for batch {n} ({os.path.basename(info['engine'])}); using batch 1. "
                   f"Run --warmup to build it.")
        infer_path, info = generate_infer_config(state["model"], 1, state["precision"], out_dir)
    msgconv_path = generate_msgconv_config(n, out_dir)
    analytics_path = generate_analytics_config(state["zones"], width, height, out_dir) if state.get("osd_analytics") else None
    tracker_cfg = first_existing([state.get("tracker_config")] + [os.path.join(DS_ROOT, c) for c in TRACKER_CONFIG_CANDIDATES])

    cols = int(math.ceil(math.sqrt(n)))
    rows = int(math.ceil(n / cols))
    tile_w, tile_h = state["display_width"], state["display_height"]

    s = []
    s.append("# Generated by icam540_arena.py - do not edit, it is overwritten on every restart\n")
    s.append("[application]\nenable-perf-measurement=1\nperf-measurement-interval-sec=2\n")
    s.append(f"[tiled-display]\nenable=1\nrows={rows}\ncolumns={cols}\nwidth={tile_w}\nheight={tile_h}\n")

    samples = find_sample_streams(state.get("extra_streams", []))
    cam = state["camera"]
    if headless and samples:
        cam = "file://" + samples[0]  # warmup must not depend on the camera
    if cam.startswith("v4l2:"):
        node = cam.split(":", 1)[1] or "/dev/video0"
        m = re.search(r"(\d+)$", node)
        idx = m.group(1) if m else "0"
        s.append(
            "[source0]\nenable=1\ntype=1\n"
            f"uri=file://{node}\ncamera-v4l2-dev-node={idx}\n"
            f"camera-width={state['cam_width']}\ncamera-height={state['cam_height']}\n"
            f"camera-fps-n={state['cam_fps']}\ncamera-fps-d=1\n"
        )
    else:
        uri = cam if "://" in cam else "file://" + os.path.abspath(cam)
        s.append(f"[source0]\nenable=1\ntype=2\nuri={uri}\ncudadec-memtype=0\n")

    if n > 1 and not samples:
        raise FileNotFoundError("no sample video streams found under " + os.path.join(DS_ROOT, "samples/streams"))
    for i in range(1, n):
        uri = "file://" + samples[(i - 1) % len(samples)]
        s.append(f"[source{i}]\nenable=1\ntype=2\nuri={uri}\ncudadec-memtype=0\n")

    display = "none" if headless else state.get("display", "screen")
    if display in ("screen", "both"):
        s.append("[sink0]\nenable=1\ntype=2\nsync=0\nsource-id=0\n")
    if display in ("rtsp", "both"):
        s.append(
            "[sink1]\nenable=1\ntype=4\ncodec=1\nenc-type=0\nsync=0\nbitrate=4000000\nprofile=2\n"
            "source-id=0\nrtsp-port=8554\nudp-port=5400\n"
        )
    if display == "none":
        s.append("[sink0]\nenable=1\ntype=1\nsync=0\n")
    if not headless:
        s.append(
            "[sink2]\nenable=1\ntype=6\n"
            f"msg-conv-config={msgconv_path}\nmsg-conv-payload-type=0\nmsg-conv-msg2p-new-api=1\n"
            f"msg-conv-frame-interval={int(state['msg_frame_interval'])}\n"
            f"msg-broker-proto-lib={os.path.join(DS_ROOT, 'lib/libnvds_mqtt_proto.so')}\n"
            f"msg-broker-conn-str={state['mqtt_host']};{state['mqtt_port']};{state['mqtt_topic']}\n"
            f"topic={state['mqtt_topic']}\n"
            f"msg-broker-config={state['mqtt_cfg']}\n"
        )
    s.append(
        "[osd]\nenable=1\nborder-width=3\ntext-size=15\ntext-color=1;1;1;1;\ntext-bg-color=0.1;0.1;0.1;0.8\n"
        "font=Sans\nshow-clock=0\n"
    )
    s.append(
        f"[streammux]\nlive-source=1\nbatch-size={n}\nbatched-push-timeout=40000\n"
        f"width={width}\nheight={height}\n"
    )
    s.append(
        "[primary-gie]\nenable=1\ngie-unique-id=1\n"
        f"config-file={infer_path}\nbatch-size={info['batch']}\ninterval={int(state['interval'])}\n"
        f"model-engine-file={info['engine']}\n"
        "bbox-border-color0=0;1;0;1\nbbox-border-color1=1;0.5;0;1\nbbox-border-color2=0;0.6;1;1\nbbox-border-color3=1;1;0;1\n"
    )
    tr = "[tracker]\nenable=1\ntracker-width=640\ntracker-height=384\ngpu-id=0\n" \
         f"ll-lib-file={os.path.join(DS_ROOT, 'lib/libnvds_nvmultiobjecttracker.so')}\n"
    if tracker_cfg:
        tr += f"ll-config-file={tracker_cfg}\n"
    s.append(tr)
    if analytics_path:
        s.append(f"[nvds-analytics]\nenable=1\nconfig-file={analytics_path}\n")
    s.append("[tests]\nfile-loop=1\n")

    path = os.path.join(out_dir, "deepstream_arena.txt")
    with open(path, "w") as f:
        f.write("\n".join(s))
    info.update({"streams": n, "rows": rows, "cols": cols, "osd_analytics": bool(analytics_path),
                 "tracker": tracker_cfg or "default", "config": path})
    return path, info


# --------------------------------------------------------------------------
# DeepStream process manager
# --------------------------------------------------------------------------

class DeepStream:
    RE_PERF_VALUES = re.compile(r"([\d.]+)\s*\(([\d.]+)\)")

    def __init__(self, cmd, log_path, stop_event, use_sudo=True):
        self.cmd = list(cmd)
        self.log_path = log_path
        self.stop_event = stop_event
        self.use_sudo = use_sudo
        self.lock = threading.Lock()
        self.proc = None
        self.started_at = 0.0
        self.fps = []  # per-stream current fps
        self.fps_avg = []
        self.fps_ts = 0.0
        self.last_error = ""
        self.state = "stopped"
        self.logf = None
        self.config = None

    @staticmethod
    def child_env():
        """deepstream-app's display sink needs X; fill in defaults when started from SSH."""
        env = dict(os.environ)
        if not env.get("DISPLAY"):
            env["DISPLAY"] = ":0"
        if not env.get("XAUTHORITY"):
            user = env.get("SUDO_USER") or env.get("USER", "")
            for cand in (os.path.expanduser("~/.Xauthority"), f"/home/{user}/.Xauthority" if user else ""):
                if cand and os.path.exists(cand):
                    env["XAUTHORITY"] = cand
                    break
        return env

    def _ensure_dead(self, config_path):
        """sudo may die before relaying SIGKILL; make sure no deepstream-app with our config survives."""
        if not config_path:
            return
        pattern = f"deepstream-app -c {config_path}"
        try:
            alive = subprocess.run(["pgrep", "-f", pattern], stdout=subprocess.PIPE, timeout=3).returncode == 0
        except Exception:
            alive = False
        if alive:
            cmd = (["sudo", "-n"] if self.use_sudo and os.geteuid() != 0 else []) + ["pkill", "-KILL", "-f", pattern]
            try:
                subprocess.run(cmd, timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def start(self, config_path):
        with self.lock:
            if self.proc and self.proc.poll() is None:
                return False, "already running"
            self._ensure_dead(config_path)
            cmd = self.cmd + ["-c", config_path]
            try:
                self.logf = open(self.log_path, "ab", buffering=0)
            except Exception:
                self.logf = None
            try:
                self.proc = spawn_pty_reader(cmd, self._on_line, "DS", self.stop_event, env=self.child_env())
            except Exception as e:
                self.state = "error"
                self.last_error = str(e)
                return False, str(e)
            self.config = config_path
            self.started_at = time.time()
            self.fps, self.fps_avg, self.fps_ts = [], [], 0.0
            self.last_error = ""
            self.state = "starting"
            log("DS", f"started pid={self.proc.pid}: {' '.join(shlex.quote(c) for c in cmd)}")
            return True, f"started pid={self.proc.pid}"

    def stop(self, timeout=10.0):
        with self.lock:
            proc = self.proc
            self.proc = None
        if proc is None or proc.poll() is not None:
            self.state = "stopped"
            self.fps = []
            if self.logf:
                try:
                    self.logf.close()
                except Exception:
                    pass
                self.logf = None
            return False, "not running"
        kill_process_group(proc, timeout=timeout)
        self._ensure_dead(self.config)
        self.state = "stopped"
        self.fps = []
        if self.logf:
            try:
                self.logf.close()
            except Exception:
                pass
            self.logf = None
        return True, "stopped"

    def running(self):
        with self.lock:
            return self.proc is not None and self.proc.poll() is None

    def exit_code(self):
        with self.lock:
            if self.proc is None:
                return None
            return self.proc.poll()

    def uptime(self):
        return time.time() - self.started_at if self.running() else 0.0

    def _on_line(self, line):
        if self.logf:
            try:
                self.logf.write((line + "\n").encode())
            except Exception:
                pass
        if line.startswith("**PERF"):
            if "FPS" in line:
                return
            vals = self.RE_PERF_VALUES.findall(line)
            if vals:
                self.fps = [float(a) for a, _ in vals]
                self.fps_avg = [float(b) for _, b in vals]
                self.fps_ts = time.time()
                if self.state == "starting":
                    self.state = "running"
            return
        low = line.lower()
        if "error" in low and "no error" not in low:
            self.last_error = line.strip()[:200]

    def fps_snapshot(self):
        fresh = (time.time() - self.fps_ts) < 8.0 and self.running()
        fps = self.fps if fresh else []
        total = round(sum(fps), 1) if fps else 0.0
        return {
            "fps_cam": round(fps[0], 1) if fps else 0.0,
            "fps_total": total,
            "fps_min": round(min(fps), 1) if fps else 0.0,
            "fps_avg": round(total / len(fps), 1) if fps else 0.0,
            "fps_streams": len(fps),
        }


# --------------------------------------------------------------------------
# the agent
# --------------------------------------------------------------------------

class Agent:
    def __init__(self, args):
        self.args = args
        self.stop_event = threading.Event()
        self.state_lock = threading.Lock()
        self.gen_dir = args.generated_dir
        os.makedirs(self.gen_dir, exist_ok=True)
        os.makedirs(os.path.dirname(args.deepstream_log) or ".", exist_ok=True)

        zones = self._load_zones(args.zones_file)
        self.booth = BoothAnalytics(zones)
        self.streams = StreamStats()
        self.metrics = JetsonMetrics(use_sudo=not args.no_sudo, stop_event=self.stop_event)

        model = args.model if args.model in MODELS else "peoplenet"
        self.state = {
            "streams": max(1, min(args.max_streams, args.streams)),
            "model": model,
            "precision": args.precision,
            "interval": args.interval,
            "camera": args.camera,
            "cam_width": args.camera_width,
            "cam_height": args.camera_height,
            "cam_fps": args.camera_fps,
            "mux_width": 1280,
            "mux_height": 720,
            "display_width": args.display_width,
            "display_height": args.display_height,
            "msg_frame_interval": args.msg_frame_interval,
            "mqtt_host": args.mqtt_host,
            "mqtt_port": args.mqtt_port,
            "mqtt_topic": args.mqtt_topic,
            "mqtt_cfg": args.mqtt_cfg,
            "osd_analytics": not args.no_osd_analytics,
            "display": args.display,
            "batched": args.batched,
            "build_engines": args.build_engines,
            "extra_streams": args.extra_stream,
            "tracker_config": args.tracker_config,
            "zones": zones,
            "telemetry_interval": args.telemetry_interval,
        }
        self.pipeline_info = {}
        self.restart_lock = threading.Lock()
        self.restart_pending = False
        self.crash_count = 0
        self.message = ""
        self.last_pipeline_event = ""

        ds_cmd = shlex.split(args.deepstream_cmd)
        if not args.no_sudo and os.geteuid() != 0 and ds_cmd and ds_cmd[0] != "sudo":
            ds_cmd = ["sudo", "-n", "-E"] + ds_cmd
        self.ds = DeepStream(ds_cmd, args.deepstream_log, self.stop_event, use_sudo=not args.no_sudo)

        user = os.environ.get("SUDO_USER") or os.environ.get("USER", "")
        self.tx_sock = pick_socket([
            args.iotc_sock,
            f"/home/{user}/snap/iotconnect/common/iotc.sock" if user else "",
            "/var/snap/iotconnect/common/iotc.sock",
        ])
        self.cmd_sock = pick_socket([
            args.iotc_cmd_sock,
            f"/home/{user}/snap/iotconnect/common/iotc_cmd.sock" if user else "",
            "/var/snap/iotconnect/common/iotc_cmd.sock",
        ])

    # ---------------- zones ----------------
    def _load_zones(self, path):
        zones = json.loads(json.dumps(DEFAULT_ZONES))
        if path and os.path.exists(path):
            try:
                with open(path) as f:
                    zones.update(json.load(f))
                log("ZONES", f"loaded {path}")
            except Exception as e:
                log("ZONES", f"failed to load {path}: {e}; using defaults")
        return zones

    def _save_zones(self):
        zones = self.booth.zones()
        with self.state_lock:
            self.state["zones"] = zones
        if self.args.zones_file:
            try:
                with open(self.args.zones_file, "w") as f:
                    json.dump(zones, f, indent=2)
            except Exception as e:
                log("ZONES", f"save failed: {e}")

    # ---------------- pipeline ----------------
    def apply_pipeline(self, reason="", headless=False):
        """Regenerate the config and (re)start DeepStream. Runs in a worker thread."""
        if self.args.no_deepstream:
            self.message = "deepstream disabled (--no-deepstream)"
            return True, self.message
        if not self.restart_lock.acquire(blocking=False):
            self.restart_pending = True
            return True, "restart queued"
        try:
            self.restart_pending = False
            self.ds.stop()
            self.ds.state = "restarting"
            with self.state_lock:
                state = json.loads(json.dumps(self.state))
            try:
                cfg, info = generate_app_config(state, self.gen_dir, headless=headless)
            except Exception as e:
                self.ds.state = "error"
                self.message = f"config error: {e}"
                log("CFG", self.message)
                return False, self.message
            self.pipeline_info = info
            self.last_pipeline_event = reason
            ok, msg = self.ds.start(cfg)
            if ok:
                self.message = (f"{info['streams']} stream{'s' if info['streams'] > 1 else ''} | "
                                f"{MODELS[state['model']]['title']} | {info['precision']} batch {info['batch']}")
            else:
                self.message = f"start failed: {msg}"
            log("DS", f"{reason}: {msg} (streams={info['streams']} model={state['model']} "
                      f"precision={info['precision']} batch={info['batch']} osd_analytics={info['osd_analytics']})")
            return ok, msg
        finally:
            self.restart_lock.release()
            if self.restart_pending:
                threading.Thread(target=self.apply_pipeline, args=("queued restart",), daemon=True).start()

    def apply_async(self, reason):
        threading.Thread(target=self.apply_pipeline, args=(reason,), daemon=True).start()

    def supervisor_loop(self):
        """Fallback + crash recovery for the DeepStream process."""
        while not self.stop_event.is_set():
            self.stop_event.wait(2.0)
            if self.args.no_deepstream or self.ds.state in ("stopped", "restarting", "error") or self.restart_lock.locked():
                continue
            code = self.ds.exit_code()
            if code is None:
                if self.ds.uptime() > 60:
                    self.crash_count = 0
                continue
            uptime = time.time() - self.ds.started_at
            err = self.ds.last_error
            log("DS", f"exited code={code} after {uptime:.0f}s; last error: {err or 'n/a'}")
            self.ds.stop()  # clears the handle so this exit is handled once
            with self.state_lock:
                osd = self.state["osd_analytics"]
                batched = self.state["batched"]
            if uptime < 25 and osd and self.pipeline_info.get("osd_analytics"):
                with self.state_lock:
                    self.state["osd_analytics"] = False
                self.message = "analytics overlay failed to load; restarted without it"
                self.apply_async("retry without analytics overlay")
                continue
            if uptime < 25 and batched and self.pipeline_info.get("batch", 1) > 1:
                with self.state_lock:
                    self.state["batched"] = False
                self.message = "batched engine failed; restarted with batch 1"
                self.apply_async("retry with batch 1")
                continue
            self.crash_count += 1
            if self.crash_count <= 3:
                self.message = f"pipeline exited (code {code}); auto-restart {self.crash_count}/3"
                self.stop_event.wait(min(10, 2 * self.crash_count))
                self.apply_async("auto-restart after exit")
            else:
                self.ds.state = "error"
                self.message = f"pipeline keeps exiting (code {code}): {err or 'see deepstream log'}"

    # ---------------- MQTT ----------------
    def mqtt_loop(self):
        try:
            import paho.mqtt.client as mqtt  # type: ignore
        except Exception:
            log("MQTT", "paho-mqtt missing: pip install paho-mqtt   (detections disabled)")
            return

        def on_connect(client, userdata, flags, rc, properties=None):
            log("MQTT", f"connected rc={rc}; subscribing {self.args.mqtt_topic}")
            client.subscribe(self.args.mqtt_topic)

        def on_message(client, userdata, msg):
            try:
                parsed = json.loads(msg.payload.decode(errors="ignore"))
            except Exception:
                return
            self.handle_detection(parsed)

        while not self.stop_event.is_set():
            try:
                try:
                    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                except Exception:
                    client = mqtt.Client()
                client.on_connect = on_connect
                client.on_message = on_message
                client.connect(self.args.mqtt_host, self.args.mqtt_port, 60)
                client.loop_forever(retry_first_connection=True)
            except Exception as e:
                log("MQTT", f"connection error: {e}; retrying in 3s")
                self.stop_event.wait(3.0)

    def handle_detection(self, parsed):
        ts = time.time()
        source, objects = parse_deepstream_message(parsed)
        self.streams.ingest(source, objects, ts)
        if source != 0:
            return
        with self.state_lock:
            w, h = self.state["mux_width"], self.state["mux_height"]
        pts = []
        for o in objects:
            left, top, right, bottom = o["bbox"]
            # foot point: bottom-centre of the box, normalised to the mux resolution
            x = max(0.0, min(1.0, ((left + right) / 2.0) / w))
            y = max(0.0, min(1.0, bottom / h))
            pts.append((o["id"], x, y, o["label"]))
        self.booth.ingest(pts, ts)

    # ---------------- telemetry ----------------
    def build_telemetry(self):
        ts = time.time()
        with self.state_lock:
            st = dict(self.state)
        info = dict(self.pipeline_info)
        t = {
            "ts": int(ts),
            "type": "arena",
            "pipeline": "disabled" if self.args.no_deepstream else self.ds.state,
            "streams": info.get("streams", st["streams"]),
            "model": st["model"],
            "precision": info.get("precision", st["precision"]),
            "batch": info.get("batch", 1),
            "infer_interval": int(st["interval"]),
            "osd_analytics": "on" if info.get("osd_analytics", st["osd_analytics"]) else "off",
            "uptime_s": round(read_uptime_seconds() or 0.0, 0),
            "pipeline_uptime_s": round(self.ds.uptime(), 0),
            "message": (self.message or "")[:200],
        }
        t.update(self.ds.fps_snapshot())
        t["infer_mpx_s"] = round(t["fps_total"] * st["mux_width"] * st["mux_height"] / 1e6, 1)
        t.update(self.streams.snapshot(ts))
        t.update(self.booth.snapshot(ts))
        m = self.metrics.snapshot()
        for k in ("gpu_load_pct", "gpu_freq_mhz", "gpu_temp_c", "cpu_load_pct", "cpu_temp_c", "soc_temp_c",
                  "power_w", "power_gpu_w", "ram_used_mb", "ram_total_mb", "emc_pct", "nvdec_mhz"):
            if k in m:
                t[k] = m[k]
        if self.ds.last_error and self.ds.state == "error":
            t["message"] = self.ds.last_error[:200]
        return t

    def telemetry_loop(self):
        while not self.stop_event.is_set():
            with self.state_lock:
                interval = float(self.state["telemetry_interval"])
            payload = self.build_telemetry()
            if self.args.print_telemetry:
                print(json.dumps(payload), flush=True)
            if self.tx_sock:
                try:
                    send_json_line(self.tx_sock, payload)
                except Exception as e:
                    log("TX", f"send failed: {e}")
            self.stop_event.wait(max(0.5, interval))

    # ---------------- commands ----------------
    def send_ack(self, ack_id, ok, msg, extra=None):
        if not self.tx_sock:
            return
        payload = {
            "type": "ack",
            "ack": ack_id,
            "ack_id": ack_id,
            "ok": bool(ok),
            "status": "success" if ok else "error",
            "message": msg,
            "ts": int(time.time()),
        }
        if extra:
            payload.update(extra)
        try:
            send_json_line(self.tx_sock, payload)
        except Exception as e:
            log("CMD", f"ack send failed: {e}")

    @staticmethod
    def parse_command(raw):
        cmd, args, ack_id = "", [], None
        try:
            msg = json.loads(raw)
        except Exception:
            msg = None
        if isinstance(msg, dict):
            if "name" in msg:
                cmd = str(msg.get("name", "")).strip().lower()
                args = msg.get("args") or []
                if isinstance(args, dict):
                    args = list(args.values())
                if not isinstance(args, list):
                    args = [args]
                ack_id = msg.get("ack_id") or msg.get("ack")
            elif "cmd" in msg or "command" in msg:
                tokens = str(msg.get("cmd") or msg.get("command") or "").strip().split()
                cmd = tokens[0].lower() if tokens else ""
                args = tokens[1:]
                ack_id = msg.get("ack_id") or msg.get("ack") or msg.get("id")
        else:
            tokens = raw.split()
            cmd = tokens[0].lower() if tokens else ""
            args = tokens[1:]
        # a command name with embedded args, e.g. "set_streams 4"
        if " " in cmd:
            tokens = cmd.split()
            cmd, args = tokens[0], tokens[1:] + [str(a) for a in args]
        return cmd, [str(a) for a in args], ack_id

    def handle_command(self, cmd, args):
        """Returns (ok, message, extra)."""
        a0 = args[0].strip().lower() if args else ""
        if cmd in ("start", "start_deepstream", "run"):
            self.crash_count = 0
            self.apply_async("start command")
            return True, "starting pipeline", {}
        if cmd in ("stop", "stop_deepstream"):
            ok, msg = self.ds.stop()
            return True, msg, {}
        if cmd in ("restart", "restart_deepstream"):
            self.crash_count = 0
            self.apply_async("restart command")
            return True, "restarting pipeline", {}
        if cmd in ("status", "get_status"):
            return True, f"pipeline={self.ds.state}", {"state": self.build_telemetry()}
        if cmd in ("set_streams", "streams"):
            try:
                n = int(float(a0))
            except ValueError:
                return False, "usage: set_streams <1..%d>" % self.args.max_streams, {}
            n = max(1, min(self.args.max_streams, n))
            with self.state_lock:
                self.state["streams"] = n
            self.apply_async(f"set_streams {n}")
            return True, f"streams={n}; restarting pipeline", {}
        if cmd in ("preset", "mode", "demo_mode"):
            if a0 not in PRESETS:
                return False, "usage: preset <%s>" % "|".join(PRESETS), {}
            with self.state_lock:
                self.state["streams"] = min(self.args.max_streams, PRESETS[a0]["streams"])
            self.apply_async(f"preset {a0}")
            return True, f"preset={a0}; restarting pipeline", {}
        if cmd in ("set_model", "model"):
            if a0 not in MODELS:
                return False, "usage: set_model <%s>" % "|".join(MODELS), {}
            with self.state_lock:
                self.state["model"] = a0
            self.apply_async(f"set_model {a0}")
            return True, f"model={a0}; restarting pipeline", {}
        if cmd in ("set_precision", "precision"):
            if a0 not in ("auto", "fp32", "fp16", "int8"):
                return False, "usage: set_precision <auto|fp32|fp16|int8>", {}
            with self.state_lock:
                self.state["precision"] = a0
            self.apply_async(f"set_precision {a0}")
            return True, f"precision={a0}; restarting (first run builds a TensorRT engine)", {}
        if cmd in ("set_interval", "interval", "infer_interval"):
            try:
                n = max(0, min(10, int(float(a0))))
            except ValueError:
                return False, "usage: set_interval <0..10>", {}
            with self.state_lock:
                self.state["interval"] = n
            self.apply_async(f"set_interval {n}")
            return True, f"infer_interval={n}; restarting pipeline", {}
        if cmd in ("set_batched", "batched"):
            on = a0 in ("1", "true", "on", "yes")
            with self.state_lock:
                self.state["batched"] = on
            self.apply_async(f"set_batched {on}")
            return True, f"batched={on}; restarting pipeline", {}
        if cmd in ("set_osd", "osd", "set_osd_analytics"):
            on = a0 in ("1", "true", "on", "yes")
            with self.state_lock:
                self.state["osd_analytics"] = on
            self.apply_async(f"set_osd {on}")
            return True, f"osd_analytics={on}; restarting pipeline", {}
        if cmd in ("set_roi", "roi"):
            try:
                pts = parse_points(" ".join(args))
                if len(pts) < 3:
                    raise ValueError("need at least 3 points")
            except Exception as e:
                return False, f"usage: set_roi x,y;x,y;x,y[;x,y] (normalised) - {e}", {}
            z = self.booth.zones()
            z["roi"] = pts
            self.booth.set_zones(z)
            self._save_zones()
            self.apply_async("set_roi")
            return True, f"roi={pts}", {}
        if cmd in ("set_line", "line"):
            try:
                pts = parse_points(" ".join(args))
                if len(pts) != 2:
                    raise ValueError("need exactly 2 points")
            except Exception as e:
                return False, f"usage: set_line x1,y1;x2,y2 (normalised) - {e}", {}
            z = self.booth.zones()
            z["line"] = {"p1": pts[0], "p2": pts[1], "dir": z["line"]["dir"]}
            self.booth.set_zones(z)
            self._save_zones()
            self.apply_async("set_line")
            return True, f"line={pts}", {}
        if cmd in ("flip_line", "flip"):
            z = self.booth.zones()
            z["line"]["dir"] = -int(z["line"]["dir"])
            self.booth.set_zones(z)
            self._save_zones()
            self.apply_async("flip_line")
            return True, f"line direction={z['line']['dir']}", {}
        if cmd in ("set_engage", "engage"):
            try:
                v = max(0.5, float(a0))
            except ValueError:
                return False, "usage: set_engage <seconds>", {}
            z = self.booth.zones()
            z["engage_s"] = v
            self.booth.set_zones(z)
            self._save_zones()
            return True, f"engage_s={v}", {}
        if cmd in ("set_overcrowd", "overcrowd"):
            try:
                v = max(1, int(float(a0)))
            except ValueError:
                return False, "usage: set_overcrowd <count>", {}
            z = self.booth.zones()
            z["overcrowd"] = v
            self.booth.set_zones(z)
            self._save_zones()
            self.apply_async("set_overcrowd")
            return True, f"overcrowd={v}", {}
        if cmd in ("reset_counts", "reset"):
            self.booth.reset()
            return True, "counters reset", {}
        if cmd in ("set_telemetry_interval", "telemetry_interval", "set_telemetry", "freq"):
            try:
                v = max(1.0, float(a0))
            except ValueError:
                return False, "usage: set_telemetry_interval <seconds>", {}
            with self.state_lock:
                self.state["telemetry_interval"] = v
            return True, f"telemetry_interval={v}", {}
        if cmd == "ping":
            return True, "pong", {}
        return False, f"unknown command '{cmd}'", {}

    def command_loop(self):
        if not self.cmd_sock:
            log("CMD", "command socket not found; command listener disabled")
            return
        while not self.stop_event.is_set():
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(self.cmd_sock)
                s.setblocking(False)
                log("CMD", f"connected to {self.cmd_sock}")
            except Exception as e:
                log("CMD", f"connect failed: {e}; retry in 2s")
                self.stop_event.wait(2.0)
                continue
            buf = b""
            while not self.stop_event.is_set():
                try:
                    r, _, _ = select.select([s], [], [], 0.5)
                    if not r:
                        continue
                    chunk = s.recv(4096)
                    if not chunk:
                        log("CMD", "socket closed; reconnecting")
                        break
                    buf += chunk
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        raw = line.decode(errors="ignore").strip()
                        if raw:
                            self._dispatch(raw)
                    if buf and not buf.endswith(b"\n"):
                        # a single JSON object without trailing newline
                        try:
                            json.loads(buf.decode(errors="ignore"))
                        except Exception:
                            continue
                        raw = buf.decode(errors="ignore").strip()
                        buf = b""
                        if raw:
                            self._dispatch(raw)
                except Exception as e:
                    log("CMD", f"error: {e}")
                    self.stop_event.wait(1.0)
                    break
            try:
                s.close()
            except Exception:
                pass

    # Commands owned by the ask-the-camera VLM narrator (../advantech-icam540/ask-the-camera), which
    # shares this device, template and command socket. Ignored here without an ack so the cloud
    # gets exactly one ack per command.
    VLM_COMMANDS = {"ask", "set_alert", "alert", "add_alert", "clear_alerts", "clear_alert"}

    def _dispatch(self, raw):
        cmd, args, ack_id = self.parse_command(raw)
        log("CMD", f"recv: {cmd} {args} ack={ack_id}")
        if cmd in self.VLM_COMMANDS or cmd.startswith("vlm_"):
            log("CMD", f"ignored: '{cmd}' belongs to the VLM narrator")
            return
        try:
            ok, msg, extra = self.handle_command(cmd, args)
        except Exception as e:
            ok, msg, extra = False, f"command failed: {e}", {}
        log("CMD", f"{'OK' if ok else 'ERR'}: {msg}")
        if ack_id:
            self.send_ack(ack_id, ok, msg, extra)

    # ---------------- warmup ----------------
    def warmup(self, spec):
        """Build TensorRT engines ahead of time. spec: model:precision:streams,streams,..."""
        model, precision, counts = spec.split(":")
        counts = [int(c) for c in counts.split(",") if c]
        with self.state_lock:
            self.state.update({"model": model, "precision": precision, "batched": True, "build_engines": True})
        for n in counts:
            with self.state_lock:
                self.state["streams"] = n
                state = json.loads(json.dumps(self.state))
            cfg, info = generate_app_config(state, self.gen_dir, headless=True)
            if os.path.exists(info["engine"]):
                log("WARMUP", f"engine exists: {info['engine']}")
                continue
            log("WARMUP", f"building {info['engine']} (this can take several minutes)")
            ok, msg = self.ds.start(cfg)
            if not ok:
                log("WARMUP", f"start failed: {msg}")
                return 1
            t0 = time.time()
            while time.time() - t0 < 1200:
                if os.path.exists(info["engine"]) and self.ds.state == "running":
                    break
                if not self.ds.running():
                    break
                time.sleep(2)
            self.ds.stop()
            if os.path.exists(info["engine"]):
                log("WARMUP", f"built {info['engine']} in {time.time() - t0:.0f}s")
            else:
                log("WARMUP", f"engine not produced; check {self.args.deepstream_log}")
                return 1
        return 0

    # ---------------- main ----------------
    def run(self):
        if not self.tx_sock:
            log("TX", "telemetry socket not found; set --iotc-sock or start the snap socket (telemetry will only print)")
            if not self.args.print_telemetry:
                log("TX", "hint: add --print-telemetry to see payloads on stdout")
        else:
            log("TX", f"using {self.tx_sock}")
        self.metrics.start()
        threading.Thread(target=self.command_loop, name="cmd", daemon=True).start()
        threading.Thread(target=self.mqtt_loop, name="mqtt", daemon=True).start()
        threading.Thread(target=self.telemetry_loop, name="telemetry", daemon=True).start()
        threading.Thread(target=self.supervisor_loop, name="supervisor", daemon=True).start()
        if self.args.auto_start:
            self.apply_async("auto-start")

        def on_signal(signum, frame):
            log("AGENT", f"signal {signum}; stopping...")
            self.stop_event.set()

        signal.signal(signal.SIGTERM, on_signal)
        signal.signal(signal.SIGHUP, on_signal)
        log("AGENT", "running; Ctrl+C to stop")
        try:
            while not self.stop_event.is_set():
                time.sleep(1.0)
        except KeyboardInterrupt:
            log("AGENT", "stopping...")
        finally:
            self.stop_event.set()
            self.ds.stop()
            self.metrics.stop()
            log("AGENT", "stopped")


def build_parser():
    ap = argparse.ArgumentParser(description="iCAM-540 Vision Arena agent for the /IOTCONNECT snap")
    env = os.environ.get
    ap.add_argument("--streams", type=int, default=int(env("ARENA_STREAMS", "1")), help="initial stream count (camera + N-1 videos)")
    ap.add_argument("--max-streams", type=int, default=int(env("ARENA_MAX_STREAMS", "9")))
    ap.add_argument("--model", default=env("ARENA_MODEL", "peoplenet"), choices=sorted(MODELS))
    ap.add_argument("--precision", default=env("ARENA_PRECISION", "auto"), choices=["auto", "fp32", "fp16", "int8"])
    ap.add_argument("--interval", type=int, default=int(env("ARENA_INTERVAL", "0")), help="nvinfer interval (frames skipped between inferences)")
    ap.add_argument("--batched", action="store_true", default=env("ARENA_BATCHED", "").lower() in ("1", "true", "yes"),
                    help="use a batch-N engine when one is cached (see --warmup)")
    ap.add_argument("--build-engines", action="store_true", help="allow nvinfer to build missing batched engines on start (slow)")
    ap.add_argument("--camera", default=env("ARENA_CAMERA", "v4l2:/dev/video0"), help="v4l2:/dev/videoN, file:///path.mp4 or rtsp://...")
    ap.add_argument("--camera-width", type=int, default=1920)
    ap.add_argument("--camera-height", type=int, default=1080)
    ap.add_argument("--camera-fps", type=int, default=30)
    ap.add_argument("--display-width", type=int, default=int(env("ARENA_DISPLAY_WIDTH", "1920")))
    ap.add_argument("--display-height", type=int, default=int(env("ARENA_DISPLAY_HEIGHT", "1080")))
    ap.add_argument("--extra-stream", action="append", default=[], help="extra looping video file(s) used before the DeepStream samples")
    ap.add_argument("--tracker-config", default=env("ARENA_TRACKER_CONFIG", ""))
    ap.add_argument("--no-osd-analytics", action="store_true", help="do not draw the zone/line overlay with nvdsanalytics")
    ap.add_argument("--display", default=env("ARENA_DISPLAY", "screen"), choices=["screen", "rtsp", "both", "none"],
                    help="screen = HDMI/X window, rtsp = rtsp://<device>:8554/ds-test, both, none = headless")
    ap.add_argument("--msg-frame-interval", type=int, default=int(env("ARENA_MSG_FRAME_INTERVAL", "3")), help="DeepStream message every N frames")
    ap.add_argument("--mqtt-host", default=env("MQTT_HOST", "localhost"))
    ap.add_argument("--mqtt-port", type=int, default=int(env("MQTT_PORT", "1883")))
    ap.add_argument("--mqtt-topic", default=env("MQTT_TOPIC", "icam540/arena"))
    ap.add_argument("--mqtt-cfg", default=env("ARENA_MQTT_CFG", os.path.join(HERE, "cfg_mqtt.txt")))
    ap.add_argument("--zones-file", default=env("ARENA_ZONES", os.path.join(HERE, "zones.json")))
    ap.add_argument("--generated-dir", default=env("ARENA_GENERATED", os.path.join(HERE, "generated")))
    ap.add_argument("--deepstream-cmd", default=env("DEEPSTREAM_CMD", "deepstream-app"))
    ap.add_argument("--deepstream-log", default=env("DEEPSTREAM_LOG", os.path.join(HERE, "logs", "deepstream.log")))
    ap.add_argument("--no-sudo", action="store_true", help="do not prefix deepstream-app/tegrastats with sudo")
    ap.add_argument("--no-deepstream", action="store_true", help="agent only (desk testing with tools/mock_deepstream_mqtt.py)")
    ap.add_argument("--auto-start", action="store_true", default=env("ARENA_AUTOSTART", "1").lower() in ("1", "true", "yes"))
    ap.add_argument("--no-auto-start", dest="auto_start", action="store_false")
    ap.add_argument("--telemetry-interval", type=float, default=float(env("ARENA_TELEMETRY_INTERVAL", "3")))
    ap.add_argument("--iotc-sock", default=env("IOTC_SOCKET", ""))
    ap.add_argument("--iotc-cmd-sock", default=env("IOTC_CMD_SOCK", ""))
    ap.add_argument("--print-telemetry", action="store_true", help="also print every telemetry payload to stdout")
    ap.add_argument("--dry-run", action="store_true", help="generate the DeepStream configs and exit")
    ap.add_argument("--warmup", default="", metavar="MODEL:PRECISION:N,N,...",
                    help="build TensorRT engines ahead of the show, e.g. peoplenet:fp16:1,4,9")
    return ap


def main():
    args = build_parser().parse_args()
    agent = Agent(args)
    if args.dry_run:
        with agent.state_lock:
            state = json.loads(json.dumps(agent.state))
        cfg, info = generate_app_config(state, agent.gen_dir)
        print(json.dumps(info, indent=2))
        print(f"\n--- {cfg} ---")
        with open(cfg) as f:
            print(f.read())
        return 0
    if args.warmup:
        agent.metrics.start()
        try:
            return agent.warmup(args.warmup)
        finally:
            agent.stop_event.set()
            agent.metrics.stop()
    agent.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
