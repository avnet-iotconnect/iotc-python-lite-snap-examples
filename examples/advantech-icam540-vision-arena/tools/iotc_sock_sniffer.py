#!/usr/bin/env python3
"""
Stand-in for the /IOTCONNECT snap sockets, for desk testing without the snap.

Creates a telemetry socket (prints every JSON line the agent sends) and a
command socket (forwards lines typed on stdin to the connected agent).

Usage:
  ./tools/iotc_sock_sniffer.py --dir /tmp/iotc
  ./icam540_arena.py --no-deepstream --iotc-sock /tmp/iotc/iotc.sock --iotc-cmd-sock /tmp/iotc/iotc_cmd.sock
  then type e.g.   {"name":"set_streams","args":["4"],"ack_id":"1"}   or   preset stress
"""

import argparse
import json
import os
import select
import socket
import sys
import threading


def telemetry_server(path):
    if os.path.exists(path):
        os.unlink(path)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(path)
    srv.listen(8)
    while True:
        conn, _ = srv.accept()
        data = b""
        while True:
            chunk = conn.recv(65536)
            if not chunk:
                break
            data += chunk
        conn.close()
        for line in data.decode(errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                tag = "ACK " if obj.get("type") == "ack" or "ack" in obj else "TELE"
                print(f"[{tag}] {json.dumps(obj, sort_keys=True)}", flush=True)
            except Exception:
                print(f"[RAW ] {line}", flush=True)


def command_server(path):
    if os.path.exists(path):
        os.unlink(path)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(path)
    srv.listen(4)
    clients = []
    print("[cmd] type a command line and press Enter (JSON or plain text)", flush=True)
    while True:
        r, _, _ = select.select([srv, sys.stdin], [], [], 0.5)
        if srv in r:
            conn, _ = srv.accept()
            clients.append(conn)
            print(f"[cmd] agent connected ({len(clients)})", flush=True)
        if sys.stdin in r:
            line = sys.stdin.readline()
            if not line:
                return
            line = line.strip()
            if not line:
                continue
            if not line.startswith("{"):
                parts = line.split()
                line = json.dumps({"name": parts[0], "args": parts[1:], "ack_id": "cli"})
            dead = []
            for c in clients:
                try:
                    c.sendall((line + "\n").encode())
                except Exception:
                    dead.append(c)
            for c in dead:
                clients.remove(c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/tmp/iotc")
    args = ap.parse_args()
    os.makedirs(args.dir, exist_ok=True)
    tx = os.path.join(args.dir, "iotc.sock")
    cmd = os.path.join(args.dir, "iotc_cmd.sock")
    print(f"[sniffer] telemetry socket: {tx}\n[sniffer] command socket:   {cmd}", flush=True)
    threading.Thread(target=telemetry_server, args=(tx,), daemon=True).start()
    try:
        command_server(cmd)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
