#!/usr/bin/env python3
"""
"Ask the camera": a vision-language narrator for the iCAM-540 on /IOTCONNECT.

Every N seconds it grabs a frame, sends it to a local VLM through any
OpenAI-compatible endpoint (Ollama, llama.cpp llama-server, vLLM) and publishes
a one-sentence scene caption plus structured fields to the /IOTCONNECT snap
socket. Cloud commands let a visitor ask the camera a free-text question or
define plain-English alert rules that are evaluated on every cycle.

Frame sources:
  v4l2:/dev/video0            direct camera (needs OpenCV; camera must be free)
  rtsp://127.0.0.1:8554/ds-test   DeepStream RTSP output (needs OpenCV)
  file:///path/to/frame.jpg   a JPEG, re-read every cycle (desk testing)
  http://host/snapshot.jpg    any HTTP JPEG snapshot URL

Commands (snap command socket, JSON {"name":..,"args":[..],"ack_id":..} or text):
  ask <question>          one-shot question about the latest frame
  set_alert <rule>        add a yes/no rule, e.g. "someone is wearing a hard hat"
  clear_alerts            remove all rules
  set_interval <s>        seconds between cycles
  set_model <tag>         model name on the endpoint
  set_max_tokens <n>
  pause | resume | status | ping
"""

import argparse
import base64
import json
import os
import re
import select
import socket
import sys
import threading
import time
import urllib.request
import urllib.error

try:
    import cv2  # type: ignore
except Exception:  # OpenCV is only needed for v4l2 / rtsp sources
    cv2 = None

HERE = os.path.dirname(os.path.abspath(__file__))

SYSTEM_PROMPT = (
    "You are the narrator of an industrial AI camera at a trade-show booth. "
    "You see one still frame at a time. Answer briefly, factually, and never invent "
    "details you cannot see. Reply with a single JSON object and nothing else."
)

# __ALERTS__ and __QUESTION__ are replaced at call time (not str.format: the JSON braces would break it)
CYCLE_PROMPT = (
    "Look at this frame and reply with JSON of the form "
    '{"caption": "<one sentence, max 25 words>", "people": <integer>, '
    '"engagement": "<none|low|medium|high>", "unusual": "<short phrase or empty>"'
    "__ALERTS__}."
)

ASK_PROMPT = (
    'Answer the question about this frame in at most 30 words. Reply with JSON '
    '{"answer": "<text>"}. Question: __QUESTION__'
)

_tx_lock = threading.Lock()


def log(tag, msg):
    print(f"[{tag}] {msg}", flush=True)


def pick_socket(candidates):
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None


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


# --------------------------------------------------------------------------
# frame grabbing
# --------------------------------------------------------------------------

class FrameSource:
    def __init__(self, source, max_width=640, jpeg_quality=80):
        self.source = source
        self.max_width = max_width
        self.jpeg_quality = jpeg_quality
        self.cap = None
        self.kind = "file"
        if source.startswith("v4l2:"):
            self.kind = "v4l2"
        elif source.startswith("rtsp://"):
            self.kind = "rtsp"
        elif source.startswith(("http://", "https://")):
            self.kind = "http"
        elif source.startswith("file://"):
            self.source = source[len("file://"):]
        if self.kind in ("v4l2", "rtsp") and cv2 is None:
            raise SystemExit("OpenCV (cv2) is required for v4l2/rtsp sources: pip3 install opencv-python-headless")

    def _open(self):
        if self.kind == "v4l2":
            node = self.source.split(":", 1)[1] or "/dev/video0"
            m = re.search(r"(\d+)$", node)
            self.cap = cv2.VideoCapture(int(m.group(1)) if m else node, cv2.CAP_V4L2)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        else:
            self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            self.cap = None
            raise RuntimeError(f"cannot open {self.source}")

    def grab(self):
        """Return JPEG bytes of the current frame."""
        if self.kind == "file":
            with open(self.source, "rb") as f:
                data = f.read()
            return self._shrink(data)
        if self.kind == "http":
            with urllib.request.urlopen(self.source, timeout=5) as r:
                return self._shrink(r.read())
        if self.cap is None:
            self._open()
        # drain buffered frames so the VLM sees "now", not a stale RTSP frame
        frame = None
        for _ in range(5):
            ok, f = self.cap.read()
            if ok:
                frame = f
        if frame is None:
            self.cap.release()
            self.cap = None
            raise RuntimeError("no frame from source")
        return self._encode(frame)

    def _encode(self, frame):
        h, w = frame.shape[:2]
        if w > self.max_width:
            scale = self.max_width / float(w)
            frame = cv2.resize(frame, (self.max_width, int(h * scale)))
        ok, enc = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
        if not ok:
            raise RuntimeError("jpeg encode failed")
        return enc.tobytes()

    def _shrink(self, data):
        if cv2 is None:
            return data
        import numpy as np  # cv2 depends on numpy, so it is present
        arr = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return self._encode(frame) if frame is not None else data


# --------------------------------------------------------------------------
# VLM client (OpenAI-compatible chat completions with an image)
# --------------------------------------------------------------------------

class VLMClient:
    def __init__(self, endpoint, model, max_tokens=120, timeout=60.0, api_key=""):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.api_key = api_key

    def ask(self, jpeg_bytes, prompt):
        """Return (text, usage dict, latency_s)."""
        b64 = base64.b64encode(jpeg_bytes).decode()
        body = {
            "model": self.model,
            "max_tokens": int(self.max_tokens),
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ]},
            ],
        }
        req = urllib.request.Request(
            self.endpoint + "/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json",
                     **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})},
        )
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            resp = json.loads(r.read().decode())
        latency = time.time() - t0
        text = ""
        try:
            text = resp["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            pass
        return text.strip(), resp.get("usage") or {}, latency


def extract_json(text):
    """Best-effort: pull the first {...} object out of a model reply."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, flags=re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


# --------------------------------------------------------------------------
# narrator
# --------------------------------------------------------------------------

class Narrator:
    def __init__(self, args):
        self.args = args
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.frames = FrameSource(args.source, max_width=args.max_width)
        self.vlm = VLMClient(args.endpoint, args.model, max_tokens=args.max_tokens, timeout=args.timeout,
                             api_key=os.environ.get("VLM_API_KEY", ""))
        self.interval = float(args.interval)
        self.paused = args.paused
        self.alerts = list(args.alert)
        self.last_jpeg = None
        self.state = {
            "type": "vlm", "vlm_state": "starting", "vlm_model": args.model,
            "scene_caption": "", "people_vlm": 0, "engagement": "none", "unusual": "",
            "question": "", "answer": "",
            "alert_rules": len(self.alerts), "alerts_active": 0, "alert_text": "",
            "vlm_latency_ms": 0, "vlm_tok_s": 0.0, "vlm_prompt_tokens": 0, "vlm_completion_tokens": 0,
            "vlm_cycle": 0, "message": "",
        }
        for i in range(1, 4):
            self.state[f"alert_{i}"] = 0
        user = os.environ.get("SUDO_USER") or os.environ.get("USER", "")
        self.tx_sock = pick_socket([args.iotc_sock, f"/home/{user}/snap/iotconnect/common/iotc.sock" if user else "",
                                    "/var/snap/iotconnect/common/iotc.sock"])
        self.cmd_sock = pick_socket([args.iotc_cmd_sock, f"/home/{user}/snap/iotconnect/common/iotc_cmd.sock" if user else "",
                                     "/var/snap/iotconnect/common/iotc_cmd.sock"])

    # ---------------- publishing ----------------
    def publish(self, extra=None):
        with self.lock:
            payload = dict(self.state)
        payload["ts"] = int(time.time())
        if extra:
            payload.update(extra)
        if self.args.print_telemetry or not self.tx_sock:
            print(json.dumps(payload), flush=True)
        if self.tx_sock:
            try:
                send_json_line(self.tx_sock, payload)
            except Exception as e:
                log("TX", f"send failed: {e}")

    def send_ack(self, ack_id, ok, msg, extra=None):
        if not self.tx_sock:
            log("ACK", f"{ack_id}: {'ok' if ok else 'error'} {msg}")
            return
        payload = {"type": "ack", "ack": ack_id, "ack_id": ack_id, "ok": bool(ok),
                   "status": "success" if ok else "error", "message": msg, "ts": int(time.time())}
        if extra:
            payload.update(extra)
        try:
            send_json_line(self.tx_sock, payload)
        except Exception as e:
            log("ACK", f"send failed: {e}")

    # ---------------- VLM cycle ----------------
    def _alerts_clause(self):
        with self.lock:
            rules = list(self.alerts)
        if not rules:
            return ""
        parts = ", ".join(f'"alert_{i + 1}": <true if {json.dumps(r)} else false>' for i, r in enumerate(rules))
        return ", " + parts

    def cycle(self):
        jpeg = self.frames.grab()
        self.last_jpeg = jpeg
        prompt = CYCLE_PROMPT.replace("__ALERTS__", self._alerts_clause())
        text, usage, latency = self.vlm.ask(jpeg, prompt)
        data = extract_json(text) or {}
        comp = int(usage.get("completion_tokens") or 0)
        with self.lock:
            rules = list(self.alerts)
            self.state["vlm_state"] = "running" if not self.paused else "paused"
            self.state["scene_caption"] = str(data.get("caption") or text)[:240]
            try:
                self.state["people_vlm"] = int(data.get("people", 0))
            except (TypeError, ValueError):
                self.state["people_vlm"] = 0
            self.state["engagement"] = str(data.get("engagement") or "none")[:16]
            self.state["unusual"] = str(data.get("unusual") or "")[:120]
            active = 0
            texts = []
            for i in range(1, 4):
                val = data.get(f"alert_{i}")
                hit = 1 if (val is True or str(val).lower() in ("true", "yes", "1")) else 0
                self.state[f"alert_{i}"] = hit if i <= len(rules) else 0
                if hit and i <= len(rules):
                    active += 1
                    texts.append(rules[i - 1])
            self.state["alert_rules"] = len(rules)
            self.state["alerts_active"] = active
            self.state["alert_text"] = "; ".join(texts)[:200]
            self.state["vlm_latency_ms"] = int(latency * 1000)
            self.state["vlm_tok_s"] = round(comp / latency, 1) if latency > 0 and comp else 0.0
            self.state["vlm_prompt_tokens"] = int(usage.get("prompt_tokens") or 0)
            self.state["vlm_completion_tokens"] = comp
            self.state["vlm_cycle"] += 1
            self.state["message"] = ""
        log("VLM", f"{latency:.1f}s {comp} tok: {self.state['scene_caption']}")
        self.publish()

    def answer(self, question):
        jpeg = self.last_jpeg or self.frames.grab()
        text, usage, latency = self.vlm.ask(jpeg, ASK_PROMPT.replace("__QUESTION__", question))
        data = extract_json(text) or {}
        ans = str(data.get("answer") or text)[:240]
        with self.lock:
            self.state["question"] = question[:200]
            self.state["answer"] = ans
            self.state["vlm_latency_ms"] = int(latency * 1000)
        log("ASK", f"{question} -> {ans}")
        self.publish()
        return ans

    def narrate_loop(self):
        while not self.stop_event.is_set():
            if self.paused:
                self.stop_event.wait(1.0)
                continue
            t0 = time.time()
            try:
                self.cycle()
            except urllib.error.URLError as e:
                self._error(f"VLM endpoint unreachable: {e.reason}")
            except Exception as e:
                self._error(f"{type(e).__name__}: {e}")
            elapsed = time.time() - t0
            self.stop_event.wait(max(0.5, self.interval - elapsed))

    def _error(self, msg):
        log("ERR", msg)
        with self.lock:
            self.state["vlm_state"] = "error"
            self.state["message"] = msg[:200]
        self.publish()
        self.stop_event.wait(3.0)

    # ---------------- commands ----------------
    @staticmethod
    def parse_command(raw):
        cmd, args, ack_id = "", [], None
        try:
            msg = json.loads(raw)
        except Exception:
            msg = None
        if isinstance(msg, dict):
            if "name" in msg:
                cmd = str(msg.get("name", "")).strip()
                args = msg.get("args") or []
                if isinstance(args, dict):
                    args = list(args.values())
                if not isinstance(args, list):
                    args = [args]
                ack_id = msg.get("ack_id") or msg.get("ack")
            elif "cmd" in msg or "command" in msg:
                cmd = str(msg.get("cmd") or msg.get("command") or "").strip()
                ack_id = msg.get("ack_id") or msg.get("ack") or msg.get("id")
        else:
            cmd = raw.strip()
        tokens = cmd.split()
        if tokens:
            cmd, args = tokens[0].lower(), tokens[1:] + [str(a) for a in args]
        return cmd, [str(a) for a in args], ack_id

    def handle_command(self, cmd, args):
        text = " ".join(args).strip()
        if cmd == "ask":
            if not text:
                return False, "usage: ask <question>", {}
            threading.Thread(target=self._ask_bg, args=(text,), daemon=True).start()
            return True, "asking the camera", {}
        if cmd in ("set_alert", "alert", "add_alert"):
            if not text:
                return False, "usage: set_alert <plain-English condition>", {}
            with self.lock:
                if len(self.alerts) >= 3:
                    return False, "max 3 alert rules; clear_alerts first", {}
                self.alerts.append(text)
                n = len(self.alerts)
            return True, f"alert_{n} = {text}", {}
        if cmd in ("clear_alerts", "clear_alert"):
            with self.lock:
                self.alerts = []
                for i in range(1, 4):
                    self.state[f"alert_{i}"] = 0
                self.state["alert_rules"] = 0
                self.state["alerts_active"] = 0
                self.state["alert_text"] = ""
            return True, "alerts cleared", {}
        if cmd in ("set_interval", "interval"):
            try:
                self.interval = max(2.0, float(args[0]))
            except (IndexError, ValueError):
                return False, "usage: set_interval <seconds>", {}
            return True, f"interval={self.interval}", {}
        if cmd in ("set_model", "model"):
            if not text:
                return False, "usage: set_model <tag>", {}
            self.vlm.model = text
            with self.lock:
                self.state["vlm_model"] = text
            return True, f"model={text}", {}
        if cmd in ("set_max_tokens", "max_tokens"):
            try:
                self.vlm.max_tokens = max(16, min(1024, int(args[0])))
            except (IndexError, ValueError):
                return False, "usage: set_max_tokens <n>", {}
            return True, f"max_tokens={self.vlm.max_tokens}", {}
        if cmd == "pause":
            self.paused = True
            with self.lock:
                self.state["vlm_state"] = "paused"
            self.publish()
            return True, "paused", {}
        if cmd == "resume":
            self.paused = False
            return True, "resumed", {}
        if cmd in ("status", "get_status"):
            with self.lock:
                snap = dict(self.state)
                snap["alerts"] = list(self.alerts)
            return True, f"vlm_state={snap['vlm_state']}", {"state": snap}
        if cmd == "ping":
            return True, "pong", {}
        return False, f"unknown command '{cmd}'", {}

    def _ask_bg(self, question):
        try:
            self.answer(question)
        except Exception as e:
            self._error(f"ask failed: {e}")

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
                        break
                    buf += chunk
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        if line.strip():
                            self._dispatch(line.decode(errors="ignore"))
                    if buf:
                        try:
                            json.loads(buf.decode(errors="ignore"))
                        except Exception:
                            continue
                        raw, buf = buf.decode(errors="ignore"), b""
                        self._dispatch(raw)
                except Exception as e:
                    log("CMD", f"error: {e}")
                    break
            try:
                s.close()
            except Exception:
                pass

    def _dispatch(self, raw):
        cmd, args, ack_id = self.parse_command(raw)
        log("CMD", f"recv: {cmd} {args}")
        try:
            ok, msg, extra = self.handle_command(cmd, args)
        except Exception as e:
            ok, msg, extra = False, f"command failed: {e}", {}
        log("CMD", f"{'OK' if ok else 'ERR'}: {msg}")
        if ack_id:
            self.send_ack(ack_id, ok, msg, extra)

    # ---------------- main ----------------
    def run(self):
        log("TX", f"telemetry socket: {self.tx_sock or 'none (printing to stdout)'}")
        log("VLM", f"endpoint {self.vlm.endpoint} model {self.vlm.model} source {self.args.source}")
        threading.Thread(target=self.command_loop, name="cmd", daemon=True).start()
        threading.Thread(target=self.narrate_loop, name="narrate", daemon=True).start()
        try:
            while not self.stop_event.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_event.set()
            log("AGENT", "stopped")


def main():
    env = os.environ.get
    ap = argparse.ArgumentParser(description="Ask-the-camera VLM narrator for the iCAM-540")
    ap.add_argument("--source", default=env("VLM_SOURCE", "rtsp://127.0.0.1:8554/ds-test"))
    ap.add_argument("--endpoint", default=env("VLM_ENDPOINT", "http://localhost:11434/v1"), help="OpenAI-compatible base URL")
    ap.add_argument("--model", default=env("VLM_MODEL", "qwen3-vl:2b"))
    ap.add_argument("--interval", type=float, default=float(env("VLM_INTERVAL", "8")))
    ap.add_argument("--max-tokens", type=int, default=int(env("VLM_MAX_TOKENS", "120")))
    ap.add_argument("--max-width", type=int, default=int(env("VLM_MAX_WIDTH", "640")), help="frame is downscaled to this width before upload")
    ap.add_argument("--timeout", type=float, default=90.0)
    ap.add_argument("--alert", action="append", default=[], help="initial alert rule (repeatable, max 3)")
    ap.add_argument("--paused", action="store_true")
    ap.add_argument("--iotc-sock", default=env("IOTC_SOCKET", ""))
    ap.add_argument("--iotc-cmd-sock", default=env("IOTC_CMD_SOCK", ""))
    ap.add_argument("--print-telemetry", action="store_true")
    ap.add_argument("--once", action="store_true", help="run one cycle, print the result and exit")
    args = ap.parse_args()

    n = Narrator(args)
    if args.once:
        n.cycle()
        return 0
    n.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
