#!/usr/bin/env python3
"""
CPU performance → IOTCONNECT socket bridge

- Collects CPU performance metrics on Linux:
    * Overall CPU utilization (%) via /proc/stat (psutil if available)
    * 1/5/15-min load averages
    * CPU frequency (MHz) (psutil or /sys/cpufreq or /proc/cpuinfo)
    * CPU temperature (°C) when exposed (psutil or /sys/class/thermal)
    * Logical core count

- Sends telemetry JSON over the IOTCONNECT Snap TX socket:
      /var/snap/iotconnect/common/iotc.sock
- Listens (read-only) on the command socket:
      /var/snap/iotconnect/common/iotc_cmd.sock

Accepted commands (same spirit as your example):
    * {"name":"freq","args":<seconds>,"ack_id":"..."}   (SNAP wrapper)
    * Fallbacks also supported: {"freq":5}, {"cmd":"freq, 5"}

Notes:
- Matches the non-invasive RX behavior from your PHT bridge: never writes to RX.
- Optional ACKs are emitted on TX when 'ack_id' is present.
"""

import argparse, json, os, socket, threading, time, select, re, glob
from typing import Dict, Any, Tuple, Optional
from json import JSONDecoder

# ---- Socket behavior mirrored from your example ----
SOCKET_TX = "/var/snap/iotconnect/common/iotc.sock"
SOCKET_RX = "/var/snap/iotconnect/common/iotc_cmd.sock"
_tx_last = 0.0
_tx_min_gap = 0.15  # 150 ms spacing between messages
_tx_lock = threading.Lock()

json_decoder = JSONDecoder()

class CPUPerf:
    """Collect CPU metrics with psutil if available; otherwise pure /proc + /sys fallback."""
    def __init__(self):
        self._prev_stat = None  # (idle, non_idle, total)
        self._psutil = None
        try:
            import psutil  # type: ignore
            self._psutil = psutil
            # Prime psutil's internal counters so the first cpu_percent isn't 0.0
            psutil.cpu_percent(interval=None)
        except Exception:
            self._psutil = None

    # ---------- CPU % ----------
    @staticmethod
    def _read_proc_stat_line(cpu_label: str = "cpu") -> Tuple[int, int, int]:
        # Returns (idle_all, non_idle, total)
        with open("/proc/stat", "r") as f:
            for line in f:
                if line.startswith(cpu_label + " "):
                    parts = line.split()
                    vals = list(map(int, parts[1:]))
                    # user nice system idle iowait irq softirq steal guest guest_nice
                    user, nice, system, idle, iowait, irq, softirq, steal = (vals + [0]*8)[:8]
                    idle_all = idle + iowait
                    non_idle = user + nice + system + irq + softirq + steal
                    total = idle_all + non_idle
                    return idle_all, non_idle, total
        raise RuntimeError("Unable to read /proc/stat")

    def _cpu_percent_fallback(self) -> float:
        # Compute % via /proc/stat deltas
        if self._prev_stat is None:
            a = self._read_proc_stat_line()
            time.sleep(0.01)  # small gap to get a measurable delta on first call
            b = self._read_proc_stat_line()
        else:
            a = self._prev_stat
            b = self._read_proc_stat_line()
        idle_a, non_a, total_a = a
        idle_b, non_b, total_b = b
        totald = total_b - total_a
        idled  = idle_b - idle_a
        self._prev_stat = b
        if totald <= 0:
            return 0.0
        usage = (totald - idled) / float(totald) * 100.0
        return max(0.0, min(100.0, usage))

    def cpu_percent(self) -> float:
        if self._psutil:
            try:
                val = float(self._psutil.cpu_percent(interval=None))
                # Occasionally first call after boot can be 0.0; fallback if suspicious and no prev_stat
                if val == 0.0 and self._prev_stat is None:
                    return self._cpu_percent_fallback()
                return val
            except Exception:
                pass
        return self._cpu_percent_fallback()

    # ---------- Load averages ----------
    @staticmethod
    def loadavg() -> Tuple[float, float, float]:
        try:
            import os as _os
            a, b, c = _os.getloadavg()
            return float(a), float(b), float(c)
        except Exception:
            # Fallback to /proc/loadavg
            try:
                with open("/proc/loadavg", "r") as f:
                    parts = f.read().strip().split()
                return float(parts[0]), float(parts[1]), float(parts[2])
            except Exception:
                return 0.0, 0.0, 0.0

    # ---------- CPU frequency (MHz) ----------
    def cpu_freq_mhz(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        # returns (current, min, max)
        if self._psutil:
            try:
                fr = self._psutil.cpu_freq()
                if fr:
                    return float(fr.current), (float(fr.min) if fr.min else None), (float(fr.max) if fr.max else None)
            except Exception:
                pass
        # sysfs (kHz)
        cur_vals, min_vals, max_vals = [], [], []
        for path in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq"):
            try:
                with open(path, "r") as f:
                    cur_vals.append(float(f.read().strip()) / 1000.0)
            except Exception:
                pass
        for path in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_min_freq"):
            try:
                with open(path, "r") as f:
                    min_vals.append(float(f.read().strip()) / 1000.0)
            except Exception:
                pass
        for path in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_max_freq"):
            try:
                with open(path, "r") as f:
                    max_vals.append(float(f.read().strip()) / 1000.0)
            except Exception:
                pass
        if cur_vals:
            cur = sum(cur_vals) / len(cur_vals)
            mn = (sum(min_vals) / len(min_vals)) if min_vals else None
            mx = (sum(max_vals) / len(max_vals)) if max_vals else None
            return cur, mn, mx

        # /proc/cpuinfo (may be less precise on some platforms)
        mhz = []
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.lower().startswith("cpu mhz"):
                        try:
                            mhz.append(float(line.split(":")[1].strip()))
                        except Exception:
                            pass
        except Exception:
            pass
        if mhz:
            return sum(mhz) / len(mhz), None, None
        return None, None, None

    # ---------- CPU temperature (°C) ----------
    def cpu_temp_c(self) -> Optional[float]:
        # psutil first
        if self._psutil and hasattr(self._psutil, "sensors_temperatures"):
            try:
                temps = self._psutil.sensors_temperatures(fahrenheit=False) or {}
                # Prefer labels that look like CPU/package/core
                candidates = []
                for name, entries in temps.items():
                    for e in entries:
                        lbl = (e.label or name or "").lower()
                        if any(k in lbl for k in ("cpu", "package", "core", "soc")):
                            if e.current is not None:
                                candidates.append(float(e.current))
                if not candidates:
                    for entries in temps.values():
                        for e in entries:
                            if e.current is not None:
                                candidates.append(float(e.current))
                if candidates:
                    return max(candidates)  # report the hottest reading
            except Exception:
                pass
        # sysfs generic fallback
        try:
            best = None
            for tdir in glob.glob("/sys/class/thermal/thermal_zone*"):
                try:
                    ttype = ""
                    ttype_path = os.path.join(tdir, "type")
                    temp_path  = os.path.join(tdir, "temp")
                    if os.path.exists(ttype_path):
                        with open(ttype_path, "r") as f:
                            ttype = (f.read().strip() or "").lower()
                    if not os.path.exists(temp_path):
                        continue
                    with open(temp_path, "r") as f:
                        raw = f.read().strip()
                    # values are usually millidegrees
                    val = float(raw)
                    if val > 1000.0:
                        val = val / 1000.0
                    if ("cpu" in ttype) or ("pkg" in ttype) or ("x86_pkg_temp" in ttype) or ("soc" in ttype):
                        best = max(best, val) if best is not None else val
                    elif best is None:
                        # keep first generic as last resort
                        best = val
                except Exception:
                    continue
            return best
        except Exception:
            return None

    def read_all(self) -> Dict[str, Any]:
        usage = round(self.cpu_percent(), 2)
        la1, la5, la15 = self.loadavg()
        cur, mn, mx = self.cpu_freq_mhz()
        temp = self.cpu_temp_c()
        cores = os.cpu_count() or 1

        payload = {
            "CPU_usage": usage,                         # %
            "CPU_load1": round(la1, 2),
            "CPU_load5": round(la5, 2),
            "CPU_load15": round(la15, 2),
            "CPU_cores": int(cores),
        }
        if cur is not None:
            payload["CPU_freq_mhz"] = round(cur, 1)
        if mn is not None:
            payload["CPU_freq_min_mhz"] = round(mn, 1)
        if mx is not None:
            payload["CPU_freq_max_mhz"] = round(mx, 1)
        if temp is not None:
            payload["CPU_temp_c"] = round(temp, 1)
        return payload


# ---- Socket helpers (mirrored behavior) ----
def socket_send(payload: dict) -> None:
    global _tx_last
    with _tx_lock:
        now = time.time()
        wait = _tx_min_gap - (now - _tx_last)
        if wait > 0:
            time.sleep(wait)
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect(SOCKET_TX)
        s.sendall(json.dumps(payload).encode("utf-8"))
        try:
            s.shutdown(socket.SHUT_WR)
        finally:
            s.close()
        _tx_last = time.time()


def socket_recv_loop(on_message, stop_event):
    while not stop_event.is_set():
        s = None
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(None)
            s.connect(SOCKET_RX)  # READ-ONLY

            buf = b""
            while not stop_event.is_set():
                rlist, _, _ = select.select([s], [], [], 60.0)
                if not rlist:
                    continue
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk
                try:
                    txt = buf.decode("utf-8", errors="ignore")
                    obj, end = json_decoder.raw_decode(txt)
                    on_message(obj)
                    txt = txt[end:].lstrip()
                    buf = txt.encode("utf-8")
                except json.JSONDecodeError:
                    if len(buf) > 1_000_000:
                        print("[CMD] dropping oversized buffer"); buf = b""
                    continue
        except Exception as e:
            print(f"[SOCKET][RX] error: {e}; retrying in 2s")
            time.sleep(2.0)
        finally:
            if s:
                try: s.close()
                except: pass


def main():
    ap = argparse.ArgumentParser(description="CPU performance → IOTCONNECT socket bridge")
    ap.add_argument("--freq", type=float, default=5.0, help="Telemetry period in seconds (>0.2)")
    ap.add_argument("--once", action="store_true", help="Collect and send one message then exit")
    args = ap.parse_args()

    cpu = CPUPerf()
    context = {"cpu": cpu}
    state = {"freq": args.freq}
    state_lock = threading.Lock()

    def _norm_arg(v):
        if isinstance(v, (list, tuple)) and v:
            v = v[0]
        if isinstance(v, str):
            v = v.strip()
        return v

    def send_ack_on_tx(ack_id: str, ok: bool, msg: str = ""):
        payload = {"ack": ack_id, "status": "success" if ok else "error", "ts": int(time.time())}
        if msg: payload["message"] = msg
        socket_send(payload)

    def apply_kv(key: str, val) -> Tuple[bool, str]:
        if key == "freq":
            try: v = float(val)
            except: return False, "freq must be a number"
            if v <= 0.2: return False, "freq must be > 0.2"
            with state_lock: state["freq"] = v
            print(f"[CMD] freq -> {v}s (applied)"); return True, ""
        return False, "unknown command"

    CMD_RE = re.compile(r'^\s*(freq)\s*(?:,|\s+)\s*([0-9.]+)\s*$', re.IGNORECASE)

    def handle_message(msg: Dict[str, Any]):
        try:
            if not isinstance(msg, dict):
                print(f"[CMD] non-dict ignored: {msg!r}"); return

            name = (msg.get("name") or "").strip().lower()
            argsv = _norm_arg(msg.get("args"))
            if name in ("freq",):
                ok, err = apply_kv(name, argsv)
                ack_id = msg.get("ack_id")
                if ack_id:
                    send_ack_on_tx(ack_id, ok, "" if ok else err)
                return

            updated = False
            if "freq" in msg or "frequency" in msg:
                ok, err = apply_kv("freq", _norm_arg(msg.get("freq", msg.get("frequency")))); updated |= ok

            if not updated and isinstance(msg.get("cmd"), str):
                m = CMD_RE.match(msg["cmd"])
                if m:
                    key, sval = m.group(1).lower(), _norm_arg(m.group(2))
                    ok, err = apply_kv(key, sval); updated |= ok

            if not updated:
                print(f"[CMD] unrecognized payload: {msg}")
        except Exception as e:
            print(f"[CMD] parse/apply error: {e} | msg={msg!r}")

    stop_event = threading.Event()
    rx_thread = threading.Thread(target=socket_recv_loop, args=(handle_message, stop_event), daemon=True)
    rx_thread.start()

    try:
        last = 0.0
        while True:
            now = time.time()
            with state_lock:
                period = state["freq"]
            if args.once or (now - last) >= period:
                try:
                    readings = context["cpu"].read_all()
                    payload = {
                        "timestamp": int(now),
                        **readings,
                        "freq": period,
                        "source": "cpu_perf"
                    }
                    socket_send(payload)
                    print(f"[TX] {payload}")
                except Exception as e:
                    print(f"[READ/TX] {e}")
                last = now
                if args.once:
                    break
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        time.sleep(0.2)


if __name__ == "__main__":
    if not os.path.exists(SOCKET_TX) or not os.path.exists(SOCKET_RX):
        print(f"[WARN] Data socket exists? {os.path.exists(SOCKET_TX)} -> {SOCKET_TX}")
        print(f"[WARN] Cmd  socket exists? {os.path.exists(SOCKET_RX)} -> {SOCKET_RX}")
    main()

