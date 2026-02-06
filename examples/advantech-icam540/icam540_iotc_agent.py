#!/usr/bin/env python3
"""
iCAM540 IoTConnect agent:
- Sends periodic performance telemetry.
- Listens for IoTConnect commands.
- Starts/stops DeepStream demo on command.
"""

import argparse
import json
import os
import select
import shlex
import socket
import subprocess
import sys
import threading
import time


def pick_socket(candidates):
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None


def send_json_line(sock_path, payload):
    data = (json.dumps(payload) + "\n").encode()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(sock_path)
        s.sendall(data)


def read_uptime_seconds():
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.read().strip().split()[0])
    except Exception:
        return None


def read_meminfo():
    mem_total = None
    mem_avail = None
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_avail = int(line.split()[1])
    except Exception:
        pass
    return mem_total, mem_avail


def read_cpu_temp_c():
    base = "/sys/class/thermal"
    try:
        for name in os.listdir(base):
            path = os.path.join(base, name, "temp")
            if os.path.exists(path):
                with open(path, "r") as f:
                    v = f.read().strip()
                if v.isdigit():
                    return int(v) / 1000.0
    except Exception:
        pass
    return None




class DeepStreamManager:
    def __init__(self, cmd, config_path, log_path=None, prestart=None):
        self.cmd = cmd
        self.config_path = config_path
        self.log_path = log_path
        self.prestart = prestart
        self.proc = None
        self.logf = None
        self.lock = threading.Lock()

    def start(self, config_path=None):
        with self.lock:
            if self.proc and self.proc.poll() is None:
                return False, "already running"
            cfg = config_path or self.config_path
            if not cfg:
                return False, "config not set"
            cmd = list(self.cmd) + ["-c", cfg]
            stdout = stderr = None
            if self.log_path:
                self.logf = open(self.log_path, "ab", buffering=0)
                stdout = stderr = self.logf
            try:
                self.proc = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
            except Exception as e:
                if self.logf:
                    self.logf.close()
                    self.logf = None
                return False, str(e)
            return True, f"started pid={self.proc.pid}"

    def stop(self, timeout=10):
        with self.lock:
            if not self.proc or self.proc.poll() is not None:
                return False, "not running"
            proc = self.proc
        proc.terminate()
        try:
            proc.wait(timeout=timeout)
        except Exception:
            proc.kill()
            proc.wait()
        with self.lock:
            self.proc = None
            if self.logf:
                self.logf.close()
                self.logf = None
        return True, "stopped"

    def status(self):
        with self.lock:
            if self.proc and self.proc.poll() is None:
                return "running", self.proc.pid
        return "stopped", None


def command_thread(cmd_sock_path, tx_sock_path, ds_mgr, state, state_lock, stop_event):
    if not cmd_sock_path:
        print("[CMD] socket not found; command listener disabled")
        return

    while not stop_event.is_set():
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(cmd_sock_path)
            s.setblocking(False)
            print(f"[CMD] connected to {cmd_sock_path}")
        except Exception as e:
            print(f"[CMD] connect failed: {e}")
            time.sleep(2.0)
            continue

        buf = b""
        while not stop_event.is_set():
            try:
                r, _, _ = select.select([s], [], [], 0.5)
                if not r:
                    continue
                chunk = s.recv(4096)
                if not chunk:
                    print("[CMD] socket closed")
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    raw = line.decode(errors="ignore").strip()
                    if not raw:
                        continue
                    cmd, args, ack_id = parse_command(raw)
                    ok, msg, extra = handle_command(cmd, args, ds_mgr, state, state_lock)
                    if ack_id:
                        send_ack(tx_sock_path, ack_id, ok, msg, extra)
            except Exception as e:
                print(f"[CMD] error: {e}")
                time.sleep(1.0)
                break
        try:
            s.close()
        except Exception:
            pass


def parse_command(raw):
    cmd = ""
    args = []
    ack_id = None
    msg = None
    try:
        msg = json.loads(raw)
    except Exception:
        msg = None

    if isinstance(msg, dict):
        if "name" in msg:
            cmd = str(msg.get("name", "")).strip().lower()
            args = msg.get("args") or []
            if not isinstance(args, list):
                args = [args]
            ack_id = msg.get("ack_id") or msg.get("ack")
        elif "cmd" in msg:
            tokens = str(msg.get("cmd", "")).strip().split()
            cmd = tokens[0].lower() if tokens else ""
            args = tokens[1:]
            ack_id = msg.get("ack") or msg.get("id")
    else:
        tokens = raw.split()
        cmd = tokens[0].lower() if tokens else ""
        args = tokens[1:]
    return cmd, args, ack_id


def handle_command(cmd, args, ds_mgr, state, state_lock):
    if not cmd:
        return False, "empty command", {}

    # config override via short names
    if cmd in ("set_config", "config"):
        key = args[0] if args else ""
        if not key:
            return False, "config key required", {}
        with state_lock:
            cfg = state.get("config_map", {}).get(key)
            if cfg:
                state["active_config"] = cfg
                return True, f"config={key}", {"config": cfg}
        return False, f"unknown config key '{key}'", {}

    if cmd in ("start", "start_deepstream", "run"):
        cfg = args[0] if args else None
        if not cfg:
            with state_lock:
                cfg = state.get("active_config")
        ok, msg = ds_mgr.start(cfg)
        return ok, msg, {}

    if cmd in ("stop", "stop_deepstream"):
        ok, msg = ds_mgr.stop()
        return ok, msg, {}

    if cmd in ("restart", "restart_deepstream"):
        ds_mgr.stop()
        cfg = args[0] if args else None
        if not cfg:
            with state_lock:
                cfg = state.get("active_config")
        ok, msg = ds_mgr.start(cfg)
        return ok, msg, {}

    if cmd in ("status", "get_status"):
        status, pid = ds_mgr.status()
        return True, f"deepstream={status}", {"deepstream": {"status": status, "pid": pid}}

    if cmd in ("set_interval", "interval", "perf_interval"):
        try:
            val = float(args[0])
            if val <= 0:
                return False, "interval must be > 0", {}
        except Exception:
            return False, "invalid interval", {}
        with state_lock:
            state["perf_interval"] = val
        return True, f"perf_interval={val}", {}

    return False, f"unknown command '{cmd}'", {}


def send_ack(tx_sock_path, ack_id, ok, msg, extra):
    payload = {
        "ack": ack_id,
        "status": "success" if ok else "error",
        "message": msg,
        "ts": int(time.time()),
    }
    if extra:
        payload.update(extra)
    try:
        send_json_line(tx_sock_path, payload)
    except Exception:
        pass


def perf_loop(tx_sock_path, did, state, state_lock, stop_event):
    while not stop_event.is_set():
        with state_lock:
            interval = float(state.get("perf_interval", 5.0))

        telemetry = {
            "uptime_s": read_uptime_seconds(),
            "cpu_load1": os.getloadavg()[0] if hasattr(os, "getloadavg") else None,
            "mem_total_kb": None,
            "mem_avail_kb": None,
            "cpu_temp_c": read_cpu_temp_c(),
        }
        mem_total, mem_avail = read_meminfo()
        telemetry["mem_total_kb"] = mem_total
        telemetry["mem_avail_kb"] = mem_avail

        payload = {
            "ts": int(time.time() * 1000),
            "did": did,
            "telemetry": {"perf": telemetry},
        }
        try:
            send_json_line(tx_sock_path, payload)
        except Exception as e:
            print(f"[PERF] send failed: {e}")

        stop_event.wait(interval)


def main():
    ap = argparse.ArgumentParser(description="iCAM540 IoTConnect agent")
    ap.add_argument("--did", default=os.environ.get("IOTC_DID", "icam540-snap"))
    ap.add_argument("--perf-interval", type=float, default=5.0)
    ap.add_argument("--iotc-sock", default=os.environ.get("IOTC_SOCKET", ""))
    ap.add_argument("--iotc-cmd-sock", default=os.environ.get("IOTC_CMD_SOCK", ""))
    ap.add_argument(
        "--deepstream-cmd",
        default=os.environ.get("DEEPSTREAM_CMD", "deepstream-app"),
        help="Command to launch DeepStream (can include args, e.g. 'sudo -E deepstream-app')",
    )
    ap.add_argument(
        "--deepstream-config",
        default=os.environ.get(
            "DEEPSTREAM_CONFIG",
            "/home/icam-540/sample/repos/iotc-python-lite-snap-examples/examples/advantech-icam540/source1_icam540_v4l2_test_msg.txt",
        ),
    )
    ap.add_argument("--deepstream-log", default=os.environ.get("DEEPSTREAM_LOG", ""))
    ap.add_argument(
        "--auto-start",
        action="store_true",
        default=os.environ.get("DEEPSTREAM_AUTOSTART", "").lower() in ("1", "true", "yes"),
        help="Start DeepStream immediately on launch",
    )
    ap.add_argument(
        "--config-alias",
        action="append",
        default=[],
        help="Alias mapping: key=full_path (can be repeated)",
    )
    args = ap.parse_args()

    user = os.environ.get("USER", "")
    sock_candidates = [
        args.iotc_sock,
        f"/home/{user}/snap/iotconnect/common/iotc.sock" if user else "",
        "/var/snap/iotconnect/common/iotc.sock",
    ]
    cmd_candidates = [
        args.iotc_cmd_sock,
        f"/home/{user}/snap/iotconnect/common/iotc_cmd.sock" if user else "",
        "/var/snap/iotconnect/common/iotc_cmd.sock",
    ]

    tx_sock = pick_socket(sock_candidates)
    cmd_sock = pick_socket(cmd_candidates)
    if not tx_sock:
        print("Telemetry socket not found. Set IOTC_SOCKET or start the snap socket service.")
        sys.exit(1)

    ds_cmd = shlex.split(args.deepstream_cmd)
    ds_mgr = DeepStreamManager(ds_cmd, args.deepstream_config, args.deepstream_log or None)

    config_map = {}
    for item in args.config_alias:
        if "=" in item:
            k, v = item.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k and v:
                config_map[k] = v
    state = {
        "perf_interval": args.perf_interval,
        "active_config": args.deepstream_config,
        "config_map": config_map,
    }
    state_lock = threading.Lock()
    stop_event = threading.Event()

    t_cmd = threading.Thread(
        target=command_thread,
        args=(cmd_sock, tx_sock, ds_mgr, state, state_lock, stop_event),
        daemon=True,
    )
    t_cmd.start()

    t_perf = threading.Thread(
        target=perf_loop,
        args=(tx_sock, args.did, state, state_lock, stop_event),
        daemon=True,
    )
    t_perf.start()

    if args.auto_start:
        ok, msg = ds_mgr.start()
        print(f"[AGENT] deepstream auto-start: {ok} ({msg})")

    print("[AGENT] running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[AGENT] stopping...")
    finally:
        stop_event.set()
        ds_mgr.stop()


if __name__ == "__main__":
    main()
