#!/usr/bin/env python3
"""
icam540_snap_socket_demo.py

Send telemetry to the IoTConnect Snap telemetry socket every N seconds and
listen for commands on the command socket. If a command includes an ack_id,
send an ACK back on the telemetry socket.

Defaults are aligned to the snap paths shown by `iotconnect.socket-debug`.
"""

import argparse
import json
import os
import random
import select
import socket
import sys
import threading
import time


def pick_socket(candidates):
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None


def now_ms():
    return int(time.time() * 1000)


def read_uptime_seconds():
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.read().strip().split()[0])
    except Exception:
        return None


def send_json_line(sock_path, payload):
    data = (json.dumps(payload) + "\n").encode()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(sock_path)
        s.sendall(data)


def command_thread(cmd_sock_path, tx_sock_path, stop_event):
    if not cmd_sock_path:
        print("[CMD] socket not found; command listener disabled")
        return

    print(f"[CMD] connecting to {cmd_sock_path}")
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(cmd_sock_path)
    except Exception as e:
        print(f"[CMD] connect failed: {e}")
        return

    s.setblocking(False)
    buf = b""

    while not stop_event.is_set():
        r, _, _ = select.select([s], [], [], 0.5)
        if not r:
            continue
        try:
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
                print(f"[CMD] recv: {raw[:200]}")
                try:
                    msg = json.loads(raw)
                except Exception:
                    msg = None

                ack_id = None
                if isinstance(msg, dict):
                    ack_id = msg.get("ack_id") or msg.get("ack")

                if ack_id:
                    ack = {
                        "ack": ack_id,
                        "status": "success",
                        "ts": int(time.time()),
                    }
                    try:
                        send_json_line(tx_sock_path, ack)
                        print(f"[CMD] ack sent: {ack_id}")
                    except Exception as e:
                        print(f"[CMD] ack send failed: {e}")
        except Exception as e:
            print(f"[CMD] read error: {e}")
            time.sleep(0.5)

    try:
        s.close()
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(description="iCAM540 IoTConnect Snap socket demo")
    ap.add_argument("--interval", type=float, default=5.0, help="telemetry interval seconds")
    ap.add_argument("--did", type=str, default=os.environ.get("IOTC_DID", "icam540-snap"))
    ap.add_argument("--iotc-sock", type=str, default=os.environ.get("IOTC_SOCKET", ""))
    ap.add_argument("--iotc-cmd-sock", type=str, default=os.environ.get("IOTC_CMD_SOCK", ""))
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

    print(f"[TX] using {tx_sock}")
    if cmd_sock:
        print(f"[CMD] using {cmd_sock}")
    else:
        print("[CMD] socket not found; will not listen for commands")

    stop_event = threading.Event()
    t = threading.Thread(
        target=command_thread,
        args=(cmd_sock, tx_sock, stop_event),
        daemon=True,
    )
    t.start()

    interval = max(0.5, float(args.interval))

    try:
        while True:
            uptime = read_uptime_seconds()
            payload = {
                "ts": now_ms(),
                "did": args.did,
                "telemetry": {
                    "uptime_s": uptime,
                    "temp_c": round(25.0 + random.random() * 5.0, 2),
                    "cpu_load": os.getloadavg()[0] if hasattr(os, "getloadavg") else None,
                },
                "meta": {
                    "example": "advantech-icam540-snap",
                    "interval_s": interval,
                },
            }
            send_json_line(tx_sock, payload)
            print(f"[TX] sent telemetry @ {payload['ts']}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_event.set()


if __name__ == "__main__":
    main()
