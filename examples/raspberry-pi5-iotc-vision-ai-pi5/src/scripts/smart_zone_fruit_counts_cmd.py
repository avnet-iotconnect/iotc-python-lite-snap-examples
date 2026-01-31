#!/usr/bin/env python3
from __future__ import annotations

import argparse, os, sys, time, json, math, socket, errno, threading
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np
import cv2

# ---------------- Utilities ----------------

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def line_side(p, a, b):
    (x, y) = p; (x1, y1) = a; (x2, y2) = b
    return (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)

def parse_line(line_str: str | None):
    if not line_str:
        return None
    x1, y1, x2, y2 = map(int, line_str.split(","))
    return (x1, y1), (x2, y2)

# ---------------- Resilient Unix clients ----------------

class ResilientUnixClient:
    """Lazy-connect Unix socket that auto-reconnects on EPIPE/ECONNRESET.
       Set readable=True if you will call recv_lines().
    """
    def __init__(self, path: str, name="IOTC", reconnect_delay=1.0, readable=False):
        self.path = path
        self.name = name
        self.sock: socket.socket | None = None
        self.reconnect_delay = reconnect_delay
        self.readable = readable
        self.buf = b""
        self.last_connect_err_log = 0.0
        self.lock = threading.Lock()

    def _connect(self) -> bool:
        if not self.path:
            return False
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(self.path)
            s.setblocking(True)
            with self.lock:
                self.sock = s
            return True
        except Exception as e:
            now = time.time()
            if now - self.last_connect_err_log > 2.0:
                print(f"[{self.name}] connect failed: {e}", file=sys.stderr)
                self.last_connect_err_log = now
            with self.lock:
                self.sock = None
            return False

    def send_line(self, line: str):
        if not self.path:
            return
        data = (line + "\n").encode("utf-8")
        with self.lock:
            s = self.sock
        if s is None and not self._connect():
            return
        try:
            with self.lock:
                assert self.sock is not None
                self.sock.sendall(data)
            return
        except OSError as e:
            if e.errno in (errno.EPIPE, errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN):
                try:
                    with self.lock:
                        if self.sock: self.sock.close()
                        self.sock = None
                except: pass
                time.sleep(self.reconnect_delay)
                if self._connect():
                    try:
                        with self.lock:
                            assert self.sock is not None
                            self.sock.sendall(data)
                        return
                    except Exception as e2:
                        print(f"[{self.name}] send retry failed: {e2}", file=sys.stderr)
                        with self.lock:
                            if self.sock: self.sock.close()
                            self.sock = None
                        return
                else:
                    return
            else:
                print(f"[{self.name}] send error: {e}", file=sys.stderr)
                return

    def recv_lines(self):
        """Yield newline-delimited lines; auto-reconnects on disconnect (thread-safe)."""
        printed_up = False
        while True:
            # Ensure connected
            with self.lock:
                s = self.sock
            if s is None and not self._connect():
                time.sleep(self.reconnect_delay)
                continue

            if not printed_up:
                print(f"[{self.name}] recv_lines connected to {self.path}")
                printed_up = True

            try:
                # Hold lock while recv so sock can't flip to None mid-call
                with self.lock:
                    s = self.sock
                    if s is None:
                        printed_up = False
                        continue
                    chunk = s.recv(4096)

                if not chunk:
                    # peer closed
                    with self.lock:
                        if self.sock:
                            try: self.sock.close()
                            except: pass
                        self.sock = None
                    printed_up = False
                    time.sleep(self.reconnect_delay)
                    continue

                self.buf += chunk
                while b"\n" in self.buf:
                    line, self.buf = self.buf.split(b"\n", 1)
                    yield line.decode("utf-8", "replace")

            except OSError as e:
                if e.errno in (errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN):
                    with self.lock:
                        if self.sock:
                            try: self.sock.close()
                            except: pass
                        self.sock = None
                    printed_up = False
                    time.sleep(self.reconnect_delay)
                else:
                    print(f"[{self.name}] recv error: {e}", file=sys.stderr)
                    time.sleep(self.reconnect_delay)
            except AttributeError:
                # s turned None unexpectedly; loop will reconnect
                printed_up = False
                time.sleep(self.reconnect_delay)
                continue



    def close(self):
        with self.lock:
            try:
                if self.sock: self.sock.close()
            except: pass
            self.sock = None

# ---------------- Runtime state controlled by commands ----------------

class CommandState:
    def __init__(self, send_interval: float, classes: str, line, area_side: str, stream: str, paused=False):
        self.lock = threading.Lock()
        self.send_interval = max(0.5, float(send_interval))
        self.classes_raw = classes or ""
        self.classes = [c.strip().lower() for c in self.classes_raw.split(",") if c.strip()]
        self.line = line  # ((x1,y1),(x2,y2)) or None
        self.area_side = "left" if area_side not in ("left", "right") else area_side
        self.stream = stream
        self.paused = paused

    def set_field(self, path: str, value) -> bool:
        with self.lock:
            if path == "send_interval":
                self.send_interval = max(0.5, float(value))
            elif path == "classes":
                self.classes_raw = value or ""
                self.classes = [c.strip().lower() for c in self.classes_raw.split(",") if c.strip()]
            elif path == "line":
                self.line = parse_line(value) if value else None
            elif path == "area_side":
                self.area_side = "left" if str(value).lower() != "right" else "right"
            elif path == "stream":
                self.stream = str(value)
            else:
                return False
        return True

    def get_snapshot(self) -> dict:
        with self.lock:
            return {
                "send_interval": self.send_interval,
                "classes": self.classes_raw,
                "line": None if self.line is None else f"{self.line[0][0]},{self.line[0][1]},{self.line[1][0]},{self.line[1][1]}",
                "area_side": self.area_side,
                "stream": self.stream,
                "paused": self.paused,
            }

# ---------------- Command thread (top-level function) ----------------
def command_thread(cmd_client: ResilientUnixClient, state: CommandState, telemetry_client: ResilientUnixClient):
    """Accepts JSON (name/args/ack_id OR cmd/path/value) and plain text."""
    def reply(obj):
        try:
            cmd_client.send_line(json.dumps(obj))
        except Exception:
            pass

    print(f"[CMD] thread starting; waiting on {cmd_client.path}")
    DIRECT_FIELDS = {"send_interval","line","area_side","stream","classes"}

    while True:
        try:
            for raw in cmd_client.recv_lines():
                raw = (raw or "").strip()
                if not raw:
                    continue
                print(f"[CMD] recv: {raw[:200]}")

                # Parse three ways: JSON name/args, JSON cmd/..., or plain text
                msg = None
                try:
                    msg = json.loads(raw)
                except Exception:
                    pass

                ack_id = None
                tokens = None

                if isinstance(msg, dict):
                    if "name" in msg:  # <-- your sniffer format
                        cmd = str(msg["name"]).lower()
                        args = [str(x) for x in (msg.get("args") or [])]
                        ack_id = msg.get("ack_id") or msg.get("ack")
                    elif "cmd" in msg:
                        # Could be "pause" or "set ..."
                        tokens = str(msg.get("cmd","")).strip().split()
                        cmd = tokens[0].lower() if tokens else ""
                        args = tokens[1:]
                        ack_id = msg.get("ack") or msg.get("id")
                    else:
                        cmd, args = "", []
                else:
                    tokens = raw.split()
                    cmd = tokens[0].lower() if tokens else ""
                    args = tokens[1:]
                    ack_id = None

                if not cmd:
                    continue

                # ----- handlers -----
                if cmd == "ping":
                    reply({"type":"pong","id": ack_id or (args[0] if args else None),"ts": now_iso()})

                elif cmd == "pause":
                    with state.lock: state.paused = True
                    print("[CMD] action: PAUSE")
                    reply({"type":"ack","cmd":"pause","ok": True,"ack_id": ack_id,"ts": now_iso()})

                elif cmd == "resume":
                    with state.lock: state.paused = False
                    print("[CMD] action: RESUME")
                    reply({"type":"ack","cmd":"resume","ok": True,"ack_id": ack_id,"ts": now_iso()})

                elif cmd == "get_status":
                    print("[CMD] action: GET_STATUS")
                    reply({"type":"status", **state.get_snapshot(), "ack_id": ack_id, "ts": now_iso()})

                elif cmd == "set":
                    # JSON: {"cmd":"set","path":"send_interval","value":2}
                    # Text: set send_interval 2
                    if isinstance(msg, dict) and "path" in msg:
                        ok = state.set_field(str(msg.get("path","")), msg.get("value"))
                    else:
                        ok = False
                        if len(args) >= 2:
                            path = args[0]
                            value = " ".join(args[1:])
                            ok = state.set_field(path, value)
                    print(f"[CMD] action: SET -> ok={ok}")
                    reply({"type":"ack","cmd":"set","ok": bool(ok),"ack_id": ack_id,"ts": now_iso()})

                elif cmd in DIRECT_FIELDS:
                    # e.g., {"name":"send_interval","args":["12"]}  or  "send_interval 12"
                    value = " ".join(args) if args else None
                    ok = state.set_field(cmd, value)
                    print(f"[CMD] action: DIRECT_SET {cmd} -> ok={ok}")
                    reply({"type":"ack","cmd":"set","path": cmd,"ok": bool(ok),"ack_id": ack_id,"ts": now_iso()})

                else:
                    print(f"[CMD] action: UNKNOWN '{cmd}'")
                    reply({"type":"error","error": f"unknown cmd '{cmd}'","ack_id": ack_id,"ts": now_iso()})

        except Exception as e:
            print(f"[CMD] thread error: {e}", file=sys.stderr)
            time.sleep(1.0)
            continue




# ---------------- Main ----------------

def main():
    try:
        from ultralytics import YOLO
    except Exception as e:
        print("Ultralytics not installed. Run: pip install ultralytics", file=sys.stderr)
        raise

    ap = argparse.ArgumentParser(description="Fruit counts split by line → IoTConnect, with command support")
    ap.add_argument("--model", default="yolov8n.pt")
    ap.add_argument("--source", default="0")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--classes", type=str, default="")
    ap.add_argument("--fps-limit", type=float, default=0.0)
    ap.add_argument("--no-draw", action="store_true")
    ap.add_argument("--line", type=str, help="x1,y1,x2,y2")
    ap.add_argument("--area-side", choices=["left", "right"], default="left")
    ap.add_argument("--iotc-sock", type=str, default=os.environ.get("IOTC_SOCK", ""))
    ap.add_argument("--iotc-cmd-sock", type=str, default=os.environ.get("IOTC_CMD_SOCK", ""))
    ap.add_argument("--iotc-stream", type=str, default="vision.fruit")
    ap.add_argument("--log-jsonl", type=str)
    ap.add_argument("--send-interval", type=float, default=4.0)
    args = ap.parse_args()

    # Model
    model = YOLO(args.model)

    # Source
    def open_capture(source):
        # Accept either /dev/videoN or an integer index
        is_path = isinstance(source, str) and source.startswith("/dev/video")
        cap = cv2.VideoCapture(source, cv2.CAP_V4L2 if is_path else 0)
        # Try a safe resolution; do NOT force FOURCC
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        return cap

    src = args.source if (isinstance(args.source, str) and args.source.startswith("/dev/")) \
          else (int(args.source) if str(args.source).isdigit() else args.source)

    cap = open_capture(src)

    # Initial state
    state = CommandState(
        send_interval=args.send_interval,
        classes=args.classes,
        line=parse_line(args.line) if args.line else None,
        area_side=args.area_side,
        stream=args.iotc_stream,
        paused=False
    )

    # Sockets
    iotc = ResilientUnixClient(args.iotc_sock, name="IOTC", readable=False)
    cmdc = ResilientUnixClient(args.iotc_cmd_sock, name="CMD", readable=True)

    # Command thread (if cmd socket provided)
    if args.iotc_cmd_sock:
        t = threading.Thread(target=command_thread, args=(cmdc, state, iotc), daemon=True)
        t.start()
        # optional announce
        cmdc.send_line(json.dumps({"type":"hello","ts":now_iso()}))

    jsonl_fp = open(args.log_jsonl, "a", buffering=1) if args.log_jsonl else None
    prev_loop_t = time.time()
    last_emit_t = 0.0

    try:
        while True:
            # If the node vanished (like your errno=19 case), reopen gracefully
            if not cap.isOpened():
                cap.release()
                time.sleep(0.5)
                cap = open_capture(src)
                # try next loop iteration
                continue

            ok, frame = cap.read()
            if not ok:
                # If the /dev/videoX disappeared, try to reopen
                if isinstance(src, str) and src.startswith("/dev/") and not os.path.exists(src):
                    cap.release()
                    time.sleep(0.5)
                    cap = open_capture(src)
                    continue
                # Otherwise just skip this frame
                continue

            ok, frame = cap.read()
            if not ok:
                break

            # paused?
            with state.lock:
                if state.paused:
                    need_sleep = state.send_interval
                else:
                    need_sleep = 0.0
            if need_sleep:
                time.sleep(min(need_sleep, 0.2))
                continue

            # fps limit
            if args.fps_limit > 0:
                min_dt = 1.0 / args.fps_limit
                while True:
                    now = time.time()
                    if now - prev_loop_t >= min_dt:
                        break
                    time.sleep(0.001)

            snap = state.get_snapshot()
            line_cur = parse_line(snap["line"]) if snap["line"] else None
            left_is_positive = (snap["area_side"] == "left")
            classes_filter = [c.strip().lower() for c in (snap["classes"] or "").split(",") if c.strip()]

            # inference
            res = model(frame, conf=args.conf, verbose=False)[0]
            names = res.names if hasattr(res, "names") else {}

            detections = []
            if res.boxes is not None and len(res.boxes) > 0:
                xyxy = res.boxes.xyxy.cpu().numpy()
                cls_ids = res.boxes.cls.cpu().numpy().astype(int)
                confs = res.boxes.conf.cpu().numpy()
                for bb, ci, cf in zip(xyxy, cls_ids, confs):
                    label = names.get(ci, str(ci)).lower()
                    if classes_filter and label not in classes_filter:
                        continue
                    x1, y1, x2, y2 = float(bb[0]), float(bb[1]), float(bb[2]), float(bb[3])
                    cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                    detections.append({"name": label, "conf": float(cf), "xyxy": (x1,y1,x2,y2), "centroid": (cx,cy)})

            # counts
            counts = {
                "apples_left": 0, "oranges_left": 0, "bananas_left": 0,
                "apples_right": 0, "oranges_right": 0, "bananas_right": 0,
                "other_left": 0, "other_right": 0,
            }

            def is_left(pt):
                if line_cur is None: return None
                a, b = line_cur
                return line_side(pt, a, b) > 0

            for d in detections:
                name = d["name"]
                side_left = is_left(d["centroid"]) if line_cur is not None else None
                key = "apples" if name == "apple" else "oranges" if name == "orange" else "bananas" if name == "banana" else None
                if line_cur is None:
                    continue
                if side_left is True:
                    counts[f"{key}_left" if key else "other_left"] += 1
                elif side_left is False:
                    counts[f"{key}_right" if key else "other_right"] += 1

            totals = defaultdict(int)
            for d in detections:
                totals[d["name"]] += 1
            apples_total  = int(totals.get("apple", 0))
            oranges_total = int(totals.get("orange", 0))
            bananas_total = int(totals.get("banana", 0))

            # draw
            if not args.no_draw:
                if line_cur is not None:
                    a, b = line_cur
                    cv2.line(frame, a, b, (255,255,0), 2)
                for d in detections:
                    x1, y1, x2, y2 = map(int, d["xyxy"])
                    label_txt = f"{d['name']} {d['conf']:.2f}"
                    color = (0, 255, 0)
                    if line_cur is not None:
                        a, b = line_cur
                        color = (0,200,0) if line_side(d["centroid"], a, b) > 0 == left_is_positive else (0,165,255)
                    cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
                    cv2.putText(frame, label_txt, (x1, max(20, y1-6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

                cv2.imshow("Fruit Counts (IoTConnect + CMD)", frame)
                if cv2.waitKey(1) & 0xFF == 27: break
            # emit every N seconds
            now_t = time.time()
            if (now_t - last_emit_t) >= max(0.5, float(snap["send_interval"])):
                last_emit_t = now_t
                payload = {
                    "v": "1.0",
                    "type": "fruit_counts",
                    "stream": snap["stream"],
                    "ts": now_iso(),
                    "apples_left": int(counts["apples_left"]),
                    "oranges_left": int(counts["oranges_left"]),
                    "bananas_left": int(counts["bananas_left"]),
                    "apples_right": int(counts["apples_right"]),
                    "oranges_right": int(counts["oranges_right"]),
                    "bananas_right": int(counts["bananas_right"]),
                    "apples_total": apples_total,
                    "oranges_total": oranges_total,
                    "bananas_total": bananas_total,
                    "other_left": int(counts["other_left"]),
                    "other_right": int(counts["other_right"]),
                }
                line_json = json.dumps(payload)
                print(line_json)
                if jsonl_fp: jsonl_fp.write(line_json + "\n")
                iotc.send_line(line_json)

            prev_loop_t = time.time()

    finally:
        cap.release()
        if not args.no_draw:
            cv2.destroyAllWindows()
        if jsonl_fp:
            try: jsonl_fp.close()
            except: pass
        iotc.close()
        cmdc.close()

if __name__ == "__main__":
    main()

