#!/usr/bin/env python3
"""
"Ask the camera": a vision-language narrator for the iCAM-540 on /IOTCONNECT.

Every N seconds it grabs a frame, sends it to a local VLM through any
OpenAI-compatible endpoint (Ollama, llama.cpp llama-server, vLLM) and publishes
a one-sentence scene caption plus structured fields to the /IOTCONNECT snap
socket. Cloud commands let a visitor ask the camera a free-text question or
define plain-English alert rules that are evaluated on every cycle.

Frame sources:
  v4l2:/dev/video0            direct camera (camera must be free; falls back to v4l2-ctl
                              when OpenCV cannot negotiate the format, as on the iCAM-540)
  rtsp://127.0.0.1:8554/ds-test   DeepStream RTSP output (needs OpenCV)
  file:///path/to/frame.jpg   a JPEG, re-read every cycle (desk testing)
  http://host/snapshot.jpg    any HTTP JPEG snapshot URL

Live view (--web PORT): the narrator serves http://<camera>:PORT/ with the live video
(MJPEG from the capture thread), the caption, answer, alerts and timing overlaid, and a
box to ask a question or add an alert rule. Open it in a browser on any PC on the LAN, or
on the camera's own screen: chromium --kiosk http://localhost:PORT/

Commands (snap command socket, JSON {"name":..,"args":[..],"ack_id":..} or text):
  ask <question>          one-shot question about the latest frame
  set_alert <rule>        add a yes/no rule, e.g. "someone is wearing a hard hat"
  clear_alerts            remove all rules
  vlm_interval <s>        seconds between cycles            (alias: set_interval)
  vlm_model <tag>         model name on the endpoint        (alias: set_model)
  vlm_max_tokens <n>                                        (alias: set_max_tokens)
  vlm_pause | vlm_resume | vlm_status | vlm_ping            (aliases: pause, resume, status, ping)
  focus auto | home | <0-2294> | +N | -N                    iCAM-540 lens (alias: vlm_focus)
  zoom <1-4> | + | -                                        digital zoom, centre crop (alias: vlm_zoom)

The vlm_* names are what the shared device template uses: the Vision Arena agent listens
on the same command socket and owns set_interval, set_model, status and ping there.
Commands this agent does not know are ignored without an ack, so the other agent's
commands do not get a second, conflicting ack from here.
"""

import argparse
import base64
import html
import json
import os
import re
import select
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

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
    """Frames for the VLM and for the live view.

    v4l2 and rtsp sources run a capture thread that always holds the latest frame, so the
    model sees "now" and the web view gets a continuous stream. file/http sources are read
    on demand.
    """

    def __init__(self, source, max_width=640, jpeg_quality=80, v4l2_size=(1920, 1080), v4l2_ctrls=""):
        self.source = source
        self.max_width = max_width
        self.jpeg_quality = jpeg_quality
        self.v4l2_size = tuple(int(x) for x in v4l2_size)
        self.v4l2_ctrls = v4l2_ctrls.strip()
        self.zoom = 1.0          # digital zoom: centre crop factor applied to every frame handed out
        self.rotate = 0          # 0 | 90 | 180 | 270, clockwise
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
        # capture thread state
        self.cond = threading.Condition()
        self.latest = None          # ("yuyv", bytes) or ("bgr", ndarray)
        self.latest_seq = 0
        self.latest_ts = 0.0
        self.fps = 0.0
        self.backend = ""
        self.stop_event = threading.Event()
        self.proc = None
        self.thread = None
        self.last_error = ""

    # ---------------- lifecycle ----------------
    def start(self):
        if self.kind in ("v4l2", "rtsp") and self.thread is None:
            self.thread = threading.Thread(target=self._capture_loop, name="capture", daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        p = self.proc
        if p is not None:
            try:
                p.kill()
            except Exception:
                pass

    def _v4l2_node(self):
        return self.source.split(":", 1)[1] or "/dev/video0"

    def _apply_v4l2_ctrls(self):
        """Best effort: the iCAM-540 sensor boots in manual exposure (exposure_time=50, gain 0)
        and gives a near-black frame until auto exposure and auto gain are switched on. Uncapped,
        auto exposure in a dim room picks ~200 ms exposures and the sensor runs at ~5 fps."""
        if not self.v4l2_ctrls:
            return
        r = subprocess.run(["v4l2-ctl", "-d", self._v4l2_node(), "-c", self.v4l2_ctrls],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            log("SRC", f"v4l2 controls set: {self.v4l2_ctrls}")
        else:
            log("SRC", f"v4l2 controls not applied ({r.stderr.strip()[:120]})")

    def _publish(self, item):
        with self.cond:
            self.latest = item
            self.latest_seq += 1
            now = time.time()
            if self.latest_ts:
                dt = now - self.latest_ts
                if dt > 0:
                    self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt) if self.fps else 1.0 / dt
            self.latest_ts = now
            self.cond.notify_all()

    def _capture_loop(self):
        while not self.stop_event.is_set():
            try:
                if self.kind == "v4l2":
                    self._apply_v4l2_ctrls()
                    node = self._v4l2_node()
                    w, h = self.v4l2_size
                    cap = cv2.VideoCapture(node, cv2.CAP_V4L2,
                                           [cv2.CAP_PROP_FRAME_WIDTH, w, cv2.CAP_PROP_FRAME_HEIGHT, h])
                    if cap.isOpened():
                        self.backend = "opencv"
                        self._opencv_stream(cap)
                    else:
                        # The iCAM-540's Tegra VI node rejects every VIDIOC_S_FMT OpenCV tries (EINVAL),
                        # while v4l2-ctl streams it fine: pipe raw YUYV frames from v4l2-ctl instead.
                        self.backend = "v4l2-ctl"
                        log("SRC", f"OpenCV cannot open {node}; streaming {w}x{h} YUYV through v4l2-ctl")
                        self._v4l2ctl_stream(node, w, h)
                else:
                    cap = cv2.VideoCapture(self.source)
                    if not cap.isOpened():
                        raise RuntimeError(f"cannot open {self.source}")
                    self.backend = "opencv"
                    self._opencv_stream(cap)
            except Exception as e:
                self.last_error = f"{type(e).__name__}: {e}"
                log("SRC", f"capture stopped: {self.last_error}; retry in 2 s")
                self.stop_event.wait(2.0)

    def _opencv_stream(self, cap):
        try:
            while not self.stop_event.is_set():
                ok, f = cap.read()
                if not ok:
                    raise RuntimeError("no frame from source")
                self._publish(("bgr", f))
        finally:
            cap.release()

    def _v4l2ctl_stream(self, node, w, h):
        cmd = ["v4l2-ctl", "-d", node, f"--set-fmt-video=width={w},height={h},pixelformat=YUYV",
               "--stream-mmap", "--stream-count=0", "--stream-to=-"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        n = w * h * 2
        buf = bytearray(n)
        view = memoryview(buf)
        try:
            while not self.stop_event.is_set():
                got = 0
                while got < n:
                    k = self.proc.stdout.readinto(view[got:])
                    if not k:
                        raise RuntimeError("v4l2-ctl stream ended")
                    got += k
                self._publish(("yuyv", bytes(buf)))
        finally:
            try:
                self.proc.kill()
            except Exception:
                pass
            self.proc = None

    # ---------------- frames ----------------
    def get_frame(self, timeout=10.0, min_seq=0):
        """Latest frame as BGR (waits for the capture thread; min_seq lets the caller skip
        the first frames while auto exposure settles)."""
        import numpy as np
        deadline = time.time() + timeout
        with self.cond:
            while self.latest is None or self.latest_seq < min_seq:
                left = deadline - time.time()
                if left <= 0:
                    if self.latest is None:
                        raise RuntimeError(f"no frame from {self.source} ({self.last_error or 'capture not started'})")
                    break
                self.cond.wait(min(left, 0.5))
            kind, data = self.latest
        if kind == "yuyv":
            w, h = self.v4l2_size
            frame = cv2.cvtColor(np.frombuffer(data, dtype=np.uint8).reshape(h, w, 2), cv2.COLOR_YUV2BGR_YUYV)
        else:
            frame = data
        return self.view(frame)

    def view(self, frame):
        """Apply rotation and digital zoom (centre crop) to a BGR frame."""
        if self.rotate:
            code = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}[self.rotate]
            frame = cv2.rotate(frame, code)
        z = self.zoom
        if z > 1.0:
            h, w = frame.shape[:2]
            cw, ch = int(w / z), int(h / z)
            x0, y0 = (w - cw) // 2, (h - ch) // 2
            frame = frame[y0:y0 + ch, x0:x0 + cw]
        return frame

    def grab(self):
        """Return JPEG bytes of the current frame (for the VLM)."""
        if self.kind == "file":
            with open(self.source, "rb") as f:
                data = f.read()
            return self._shrink(data)
        if self.kind == "http":
            with urllib.request.urlopen(self.source, timeout=5) as r:
                return self._shrink(r.read())
        # auto exposure converges over ~100 frames after stream-on: skip them on the first grab
        min_seq = 90 if (self.kind == "v4l2" and self.latest_seq < 90) else 0
        return self._encode(self.get_frame(timeout=15.0, min_seq=min_seq))

    def _encode(self, frame, max_width=None, quality=None):
        max_width = max_width or self.max_width
        h, w = frame.shape[:2]
        if w > max_width:
            scale = max_width / float(w)
            frame = cv2.resize(frame, (max_width, int(h * scale)))
        ok, enc = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality or self.jpeg_quality])
        if not ok:
            raise RuntimeError("jpeg encode failed")
        return enc.tobytes()

    def _shrink(self, data):
        if cv2 is None:
            return data
        import numpy as np  # cv2 depends on numpy, so it is present
        arr = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return self._encode(self.view(frame)) if frame is not None else data


class LensFocus:
    """Motorised focus of the iCAM-540's built-in lens, through the adv_icam500 V4L2 controls.

    Learned on the camera (the datasheet does not say): lens_home=1 homes the stepper to 0 and
    nothing moves until that has happened once per boot; focus_distance=N is a RELATIVE move of
    N steps; focus_zoom picks the direction (1 = toward 2294, 0 = toward 0); lens_position reads
    back the commanded target. The motor does ~2 ms per step, so a full sweep takes ~4.6 s.
    There is no optical zoom (12 mm fixed focal length): "zoom" in this demo is a digital crop.
    """
    MAX = 2294

    def __init__(self, node, frames):
        self.node = node
        self.frames = frames
        self.homed = False
        self.position = 0
        self.score = 0.0
        self.busy = False
        self.lock = threading.Lock()

    def _ctl(self, *args):
        r = subprocess.run(["v4l2-ctl", "-d", self.node, *args], capture_output=True, text=True, timeout=10)
        return r.stdout.strip()

    def read_position(self):
        out = self._ctl("--get-ctrl=lens_position")
        try:
            self.position = int(out.split()[-1])
        except (ValueError, IndexError):
            pass
        return self.position

    def home(self):
        self._ctl("-c", "lens_home=1")
        time.sleep(0.3 + self.MAX * 0.0025)
        self.homed = True
        self.read_position()
        log("LENS", f"homed, position {self.position}")

    def move_to(self, target):
        if not self.homed:
            self.home()
        target = max(0, min(self.MAX, int(target)))
        pos = self.read_position()
        delta = target - pos
        if delta == 0:
            return pos
        self._ctl("-c", f"focus_zoom={1 if delta > 0 else 0}")
        self._ctl("-c", f"focus_distance={abs(delta)}")
        time.sleep(0.25 + abs(delta) * 0.0025)
        return self.read_position()

    def sharpness(self, samples=2):
        """Tenengrad (Sobel gradient energy) over the centre half of the frame after a 2x
        downscale and a 3x3 blur. The blur matters: at the gain this sensor runs indoors,
        plain Laplacian variance measures the noise, not the focus (it was highest at the
        wrong end of the range), while this measure shows a sharp peak at the focus."""
        total = 0.0
        for _ in range(samples):
            f = self.frames.get_frame(timeout=3.0)
            h, w = f.shape[:2]
            c = f[h // 4: 3 * h // 4, w // 4: 3 * w // 4]
            if c.shape[1] > 960:
                c = cv2.resize(c, (960, int(c.shape[0] * 960 / c.shape[1])))
            g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
            g = cv2.GaussianBlur(cv2.resize(g, (g.shape[1] // 2, g.shape[0] // 2)), (3, 3), 0)
            gx = cv2.Sobel(g, cv2.CV_64F, 1, 0)
            gy = cv2.Sobel(g, cv2.CV_64F, 0, 1)
            total += float((gx * gx + gy * gy).mean())
            time.sleep(0.08)
        self.score = round(total / samples, 1)
        return self.score

    def autofocus(self, coarse=100, fine=20):
        """Sweep the whole range (the in-focus peak is only ~200 steps wide, so 100-step
        coarse moves), then refine in 20-step moves around the best. ~30 s."""
        with self.lock:
            self.busy = True
            try:
                if not self.homed:
                    self.home()
                best = (0, -1.0)
                for p in range(0, self.MAX + 1, coarse):
                    self.move_to(p)
                    time.sleep(0.2)
                    sc = self.sharpness()
                    log("LENS", f"coarse {p:4d}: {sc:8.1f}")
                    if sc > best[1]:
                        best = (p, sc)
                lo, hi = max(0, best[0] - coarse), min(self.MAX, best[0] + coarse)
                self.move_to(lo)
                for p in range(lo, hi + 1, fine):
                    self.move_to(p)
                    time.sleep(0.15)
                    sc = self.sharpness()
                    if sc > best[1]:
                        best = (p, sc)
                self.move_to(best[0])
                time.sleep(0.2)
                self.sharpness()
                log("LENS", f"autofocus done: position {best[0]}, sharpness {best[1]:.1f}")
                return best
            finally:
                self.busy = False


# --------------------------------------------------------------------------
# VLM client (OpenAI-compatible chat completions with an image)
# --------------------------------------------------------------------------

class VLMClient:
    """Talks to a VLM over either Ollama's native /api/chat or an OpenAI-compatible /v1.

    Ollama native is preferred when available: it lets us turn thinking off (Qwen3-VL
    thinks by default and spends the whole token budget on it), force JSON output, and
    get the prefill/decode timing breakdown for the dashboard.
    """

    def __init__(self, endpoint, model, max_tokens=120, timeout=60.0, api_key="", api="auto"):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.api_key = api_key
        self.base = re.sub(r"/v1$", "", self.endpoint)
        self.api = api if api != "auto" else self._detect_api()

    def _detect_api(self):
        try:
            with urllib.request.urlopen(self.base + "/api/version", timeout=3) as r:
                ver = json.loads(r.read().decode()).get("version", "?")
            log("VLM", f"Ollama {ver} detected, using native API (thinking off, JSON mode)")
            return "ollama"
        except Exception:
            return "openai"

    def ask(self, jpeg_bytes, prompt):
        """Return (text, usage dict, latency_s)."""
        b64 = base64.b64encode(jpeg_bytes).decode()
        if self.api == "ollama":
            return self._ask_ollama(b64, prompt)
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

    def _ask_ollama(self, b64, prompt):
        body = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": "json",
            "keep_alive": -1,
            "options": {"num_predict": int(self.max_tokens), "temperature": 0.2},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt, "images": [b64]},
            ],
        }
        req = urllib.request.Request(self.base + "/api/chat", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            resp = json.loads(r.read().decode())
        latency = time.time() - t0
        msg = resp.get("message") or {}
        text = (msg.get("content") or "").strip()
        if not text and msg.get("thinking"):
            # thinking variant of the model: the budget went to reasoning, nothing left for the answer
            log("VLM", "empty answer, model spent its tokens thinking; use an instruct model tag")
        usage = {
            "prompt_tokens": resp.get("prompt_eval_count") or 0,
            "completion_tokens": resp.get("eval_count") or 0,
            "load_s": (resp.get("load_duration") or 0) / 1e9,
            "prefill_s": (resp.get("prompt_eval_duration") or 0) / 1e9,
            "decode_s": (resp.get("eval_duration") or 0) / 1e9,
            "server_s": (resp.get("total_duration") or 0) / 1e9,
        }
        return text, usage, latency


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
# live view: MJPEG stream + state JSON + a page that overlays the narration
# --------------------------------------------------------------------------

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Ask the camera</title>
<style>
 html,body{margin:0;height:100%;background:#000;color:#fff;font-family:system-ui,sans-serif;overflow:hidden}
 #v{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#000}
 .ov{position:absolute;left:0;right:0;padding:16px 24px;background:linear-gradient(180deg,rgba(0,0,0,0),rgba(0,0,0,.85))}
 #cap{bottom:0;font-size:34px;line-height:1.25;text-shadow:0 2px 6px #000}
 #cap small{display:block;font-size:16px;opacity:.75;margin-top:6px}
 #top{top:0;background:linear-gradient(0deg,rgba(0,0,0,0),rgba(0,0,0,.8));display:flex;gap:10px;flex-wrap:wrap;align-items:center}
 .chip{background:rgba(255,255,255,.14);border-radius:8px;padding:6px 10px;font-size:16px;white-space:nowrap}
 .chip b{color:#9fd4ff}
 .alert{background:#7a1f1f}
 .alert.on{background:#e03131;animation:blink 1s infinite}
 @keyframes blink{50%{opacity:.5}}
 #qa{position:absolute;left:24px;right:24px;bottom:120px;font-size:24px;text-shadow:0 2px 6px #000}
 #qa .q{color:#ffd166}
 #qa .a{color:#b8f2a6}
 form{position:absolute;right:24px;bottom:130px;display:flex;gap:8px}
 input{font-size:18px;padding:8px 10px;border-radius:6px;border:1px solid #555;background:#111;color:#fff;width:380px}
 button{font-size:18px;padding:8px 12px;border-radius:6px;border:0;background:#2f6fed;color:#fff;cursor:pointer}
 button.alt{background:#d9480f}
 button.grey{background:#555}
 #title{font-weight:700;font-size:18px;color:#fff}
</style></head><body>
<img id="v" src="/stream.mjpg" alt="live" onerror="setTimeout(restream,2000)">
<div id="top" class="ov">
 <span id="title">ASK THE CAMERA</span>
 <span class="chip">model <b id="model">-</b></span>
 <span class="chip">narrator <b id="state">-</b></span>
 <span class="chip">cam <b id="fps">-</b> fps</span>
 <span class="chip">round trip <b id="lat">-</b> s</span>
 <span class="chip">prefill <b id="pre">-</b> s</span>
 <span class="chip">decode <b id="tok">-</b> tok/s</span>
 <span class="chip">cycle <b id="cyc">-</b></span>
 <span class="chip">people <b id="ppl">-</b></span>
 <span class="chip">engagement <b id="eng">-</b></span>
 <span class="chip">lens <b id="lens">-</b> sharp <b id="sharp">-</b></span>
 <span class="chip">zoom <b id="zoom">-</b>x</span>
 <span id="alerts"></span>
</div>
<div id="qa"><div class="q" id="q"></div><div class="a" id="a"></div></div>
<form onsubmit="return send('ask')">
 <input id="t" placeholder="ask the camera a question, or type an alert rule" autocomplete="off">
 <button type="submit">Ask</button>
 <button type="button" class="alt" onclick="send('set_alert')">Add alert</button>
 <button type="button" class="grey" onclick="send('clear_alerts')">Clear</button>
 <button type="button" class="grey" onclick="send('focus','auto')" title="sweep the lens for the sharpest image (~20 s)">Autofocus</button>
 <button type="button" class="grey" onclick="send('focus','-25')">Near</button>
 <button type="button" class="grey" onclick="send('focus','+25')">Far</button>
 <button type="button" class="grey" onclick="send('zoom','-')">Zoom &minus;</button>
 <button type="button" class="grey" onclick="send('zoom','+')">Zoom +</button>
</form>
<div id="cap" class="ov"><span id="caption">waiting for the first caption...</span><small id="msg"></small></div>
<script>
 const $=id=>document.getElementById(id);
 let boot=null, failed=false;
 function restream(){ $('v').src='/stream.mjpg?'+Date.now(); }
 async function tick(){
  try{
   const s=await (await fetch('/state.json',{cache:'no-store'})).json();
   // the MJPEG stream is a plain connection: reopen it when the narrator came back, and reload the
   // whole page when the narrator was restarted (it may be a newer page)
   if(boot!==null&&s.server_start!==boot){ location.reload(); return; }
   if(failed) restream();
   boot=s.server_start; failed=false;
   $('model').textContent=s.vlm_model; $('state').textContent=s.vlm_state; $('fps').textContent=(s.cam_fps||0).toFixed(0);
   $('lat').textContent=(s.vlm_latency_ms/1000).toFixed(1); $('pre').textContent=(s.vlm_prefill_ms/1000).toFixed(1);
   $('tok').textContent=s.vlm_tok_s; $('cyc').textContent=s.vlm_cycle; $('ppl').textContent=s.people_vlm; $('eng').textContent=s.engagement;
   $('lens').textContent=s.focusing?'focusing...':s.lens_pos; $('sharp').textContent=Math.round(s.focus_score); $('zoom').textContent=s.zoom;
   if(s.scene_caption) $('caption').textContent=s.scene_caption;
   $('msg').textContent=(s.unusual?('unusual: '+s.unusual+'   '):'')+(s.message||'');
   $('q').textContent=s.question?('Q: '+s.question):''; $('a').textContent=s.answer?('A: '+s.answer):'';
   $('alerts').innerHTML=(s.alerts||[]).map((r,i)=>'<span class="chip alert '+(s['alert_'+(i+1)]?'on':'')+'">'+(s['alert_'+(i+1)]?'&#9888; ':'')+r.replace(/</g,'&lt;')+'</span>').join(' ');
  }catch(e){ failed=true; }
 }
 async function send(cmd,arg){
  const t=(arg!==undefined)?arg:$('t').value.trim(); if(cmd!=='clear_alerts'&&!t) return false;
  await fetch('/cmd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd:cmd,text:t})});
  if(arg===undefined&&cmd!=='clear_alerts') $('t').value=''; tick(); return false;
 }
 setInterval(tick,1000); tick();
</script></body></html>
"""


class WebUI:
    def __init__(self, narrator, port, width=960, fps=12, quality=70):
        self.n = narrator
        self.port = int(port)
        self.width = width
        self.fps = fps
        self.quality = quality
        self.jpeg = b""
        self.seq = 0
        self.started = int(time.time())
        self.cond = threading.Condition()

    def start(self):
        threading.Thread(target=self._encode_loop, name="mjpeg", daemon=True).start()
        ui = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                path = urlparse(self.path).path
                if path in ("/", "/index.html"):
                    body = PAGE.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif path == "/state.json":
                    body = json.dumps(ui.state()).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif path == "/stream.mjpg":
                    self.send_response(200)
                    self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    last = 0
                    try:
                        while True:
                            with ui.cond:
                                while ui.seq == last:
                                    ui.cond.wait(1.0)
                                    if ui.seq == last and ui.n.stop_event.is_set():
                                        return
                                last, jpg = ui.seq, ui.jpeg
                            self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(jpg))
                            self.wfile.write(jpg)
                            self.wfile.write(b"\r\n")
                    except (BrokenPipeError, ConnectionResetError):
                        return
                elif path == "/snapshot.jpg":
                    with ui.cond:
                        jpg = ui.jpeg
                    self.send_response(200 if jpg else 503)
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(jpg)))
                    self.end_headers()
                    self.wfile.write(jpg)
                else:
                    self.send_error(404)

            def do_POST(self):
                if urlparse(self.path).path != "/cmd":
                    return self.send_error(404)
                n = int(self.headers.get("Content-Length") or 0)
                try:
                    req = json.loads(self.rfile.read(n).decode() or "{}")
                    cmd = str(req.get("cmd", "")).strip().lower()
                    text = str(req.get("text", "")).strip()
                    ok, msg, extra = ui.n.handle_command(cmd, text.split() if text else [])
                except Exception as e:
                    ok, msg = False, f"bad request: {e}"
                body = json.dumps({"ok": bool(ok), "message": msg}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        srv = ThreadingHTTPServer(("0.0.0.0", self.port), Handler)
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, name="http", daemon=True).start()
        log("WEB", f"live view on http://0.0.0.0:{self.port}/  (MJPEG {self.width}px @ {self.fps} fps)")

    def state(self):
        with self.n.lock:
            d = dict(self.n.state)
            d["alerts"] = list(self.n.alerts)
        d["cam_fps"] = round(self.n.frames.fps, 1)
        d["cam_backend"] = self.n.frames.backend
        d["server_start"] = self.started
        return d

    def _encode_loop(self):
        period = 1.0 / self.fps
        frames = self.n.frames
        while not self.n.stop_event.is_set():
            t0 = time.time()
            try:
                if frames.kind in ("v4l2", "rtsp"):
                    frame = frames.get_frame(timeout=2.0)
                    jpg = frames._encode(frame, max_width=self.width, quality=self.quality)
                else:
                    jpg = frames.grab()  # file/http: whatever the model sees
            except Exception:
                time.sleep(0.5)
                continue
            with self.cond:
                self.jpeg = jpg
                self.seq += 1
                self.cond.notify_all()
            time.sleep(max(0.0, period - (time.time() - t0)))


# --------------------------------------------------------------------------
# narrator
# --------------------------------------------------------------------------

class Narrator:
    def __init__(self, args):
        self.args = args
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.frames = FrameSource(args.source, max_width=args.max_width, v4l2_size=args.v4l2_size,
                                  v4l2_ctrls=args.v4l2_ctrls)
        self.vlm = VLMClient(args.endpoint, args.model, max_tokens=args.max_tokens, timeout=args.timeout,
                             api_key=os.environ.get("VLM_API_KEY", ""), api=args.api)
        self.frames.zoom = max(1.0, float(args.zoom))
        self.frames.rotate = int(args.rotate)
        self.lens = LensFocus(self.frames._v4l2_node(), self.frames) if self.frames.kind == "v4l2" else None
        self.interval = float(args.interval)
        self.paused = args.paused
        self.alerts = list(args.alert)
        self.last_jpeg = None
        self.state = {
            "type": "vlm", "vlm_state": "starting", "vlm_model": args.model,
            "scene_caption": "", "people_vlm": 0, "engagement": "none", "unusual": "",
            "question": "", "answer": "",
            "alert_rules": len(self.alerts), "alerts_active": 0, "alert_text": "",
            "vlm_latency_ms": 0, "vlm_prefill_ms": 0, "vlm_tok_s": 0.0, "vlm_prompt_tokens": 0, "vlm_completion_tokens": 0,
            "vlm_cycle": 0, "message": "",
            "lens_pos": 0, "focus_score": 0.0, "focusing": 0, "zoom": self.frames.zoom,
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
            self.state["vlm_prefill_ms"] = int(float(usage.get("prefill_s") or 0) * 1000)
            decode_s = float(usage.get("decode_s") or 0) or latency
            self.state["vlm_tok_s"] = round(comp / decode_s, 1) if decode_s > 0 and comp else 0.0
            self.state["vlm_prompt_tokens"] = int(usage.get("prompt_tokens") or 0)
            self.state["vlm_completion_tokens"] = comp
            self.state["vlm_cycle"] += 1
            self.state["message"] = ""
        log("VLM", f"{latency:.1f}s (server {usage.get('server_s', 0):.1f} load {usage.get('load_s', 0):.1f} "
                   f"prefill {usage.get('prefill_s', 0):.1f} decode {usage.get('decode_s', 0):.1f}) {comp} tok: {self.state['scene_caption']}")
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
            if self.paused or (self.lens is not None and self.lens.busy):
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
        if cmd in ("set_interval", "interval", "vlm_interval"):
            try:
                self.interval = max(2.0, float(args[0]))
            except (IndexError, ValueError):
                return False, "usage: set_interval <seconds>", {}
            return True, f"interval={self.interval}", {}
        if cmd in ("set_model", "model", "vlm_model"):
            if not text:
                return False, "usage: set_model <tag>", {}
            self.vlm.model = text
            with self.lock:
                self.state["vlm_model"] = text
            return True, f"model={text}", {}
        if cmd in ("set_max_tokens", "max_tokens", "vlm_max_tokens"):
            try:
                self.vlm.max_tokens = max(16, min(1024, int(args[0])))
            except (IndexError, ValueError):
                return False, "usage: set_max_tokens <n>", {}
            return True, f"max_tokens={self.vlm.max_tokens}", {}
        if cmd in ("pause", "vlm_pause"):
            self.paused = True
            with self.lock:
                self.state["vlm_state"] = "paused"
            self.publish()
            return True, "paused", {}
        if cmd in ("resume", "vlm_resume"):
            self.paused = False
            return True, "resumed", {}
        if cmd in ("status", "get_status", "vlm_status"):
            with self.lock:
                snap = dict(self.state)
                snap["alerts"] = list(self.alerts)
            return True, f"vlm_state={snap['vlm_state']}", {"state": snap}
        if cmd in ("ping", "vlm_ping"):
            return True, "pong", {}
        if cmd in ("focus", "vlm_focus"):
            if self.lens is None:
                return False, "focus needs a v4l2 source", {}
            if self.lens.busy:
                return False, "autofocus already running", {}
            arg = (args[0] if args else "auto").lower()
            if arg in ("auto", "af"):
                threading.Thread(target=self._focus_bg, args=("auto",), daemon=True).start()
                return True, "autofocus started (~20 s)", {}
            if arg == "home":
                threading.Thread(target=self._focus_bg, args=("home",), daemon=True).start()
                return True, "homing lens", {}
            try:
                if arg[0] in "+-":
                    target = self.lens.read_position() + int(arg)
                else:
                    target = int(arg)
            except ValueError:
                return False, "usage: focus auto | home | <0-2294> | +N | -N", {}
            threading.Thread(target=self._focus_bg, args=(target,), daemon=True).start()
            return True, f"moving lens to {max(0, min(LensFocus.MAX, target))}", {}
        if cmd in ("zoom", "vlm_zoom"):
            try:
                arg = args[0]
                z = self.frames.zoom * 1.25 if arg == "+" else self.frames.zoom / 1.25 if arg == "-" else float(arg)
            except (IndexError, ValueError):
                return False, "usage: zoom <1.0-4.0> | + | -", {}
            self.frames.zoom = round(max(1.0, min(4.0, z)), 2)
            with self.lock:
                self.state["zoom"] = self.frames.zoom
            return True, f"zoom={self.frames.zoom}x (digital, centre crop)", {}
        return None, f"not mine: '{cmd}'", {}

    def _focus_bg(self, what):
        with self.lock:
            self.state["focusing"] = 1
        try:
            if what == "auto":
                self.lens.autofocus()
            elif what == "home":
                self.lens.home()
            else:
                self.lens.move_to(what)
                time.sleep(0.2)
                self.lens.sharpness()
        except Exception as e:
            log("LENS", f"focus failed: {e}")
        finally:
            with self.lock:
                self.state["focusing"] = 0
                self.state["lens_pos"] = self.lens.position
                self.state["focus_score"] = self.lens.score

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
        if ok is None:
            # another agent on this device (the Vision Arena) owns it; stay silent so it gets one ack
            log("CMD", f"ignored: {msg}")
            return
        log("CMD", f"{'OK' if ok else 'ERR'}: {msg}")
        if ack_id:
            self.send_ack(ack_id, ok, msg, extra)

    # ---------------- main ----------------
    def run(self):
        log("TX", f"telemetry socket: {self.tx_sock or 'none (printing to stdout)'}")
        log("VLM", f"endpoint {self.vlm.endpoint} model {self.vlm.model} source {self.args.source}")
        self.frames.start()
        if self.args.web:
            WebUI(self, self.args.web).start()
        if self.lens is not None and self.args.focus:
            ok, msg, _ = self.handle_command("focus", [self.args.focus])
            log("LENS", msg)
        threading.Thread(target=self.command_loop, name="cmd", daemon=True).start()
        threading.Thread(target=self.narrate_loop, name="narrate", daemon=True).start()
        try:
            while not self.stop_event.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_event.set()
            self.frames.stop()
            log("AGENT", "stopped")


def main():
    env = os.environ.get
    ap = argparse.ArgumentParser(description="Ask-the-camera VLM narrator for the iCAM-540")
    ap.add_argument("--source", default=env("VLM_SOURCE", "rtsp://127.0.0.1:8554/ds-test"))
    ap.add_argument("--endpoint", default=env("VLM_ENDPOINT", "http://localhost:11434/v1"), help="OpenAI-compatible base URL")
    ap.add_argument("--model", default=env("VLM_MODEL", "qwen3-vl:2b-instruct"))
    ap.add_argument("--api", choices=["auto", "ollama", "openai"], default=env("VLM_API", "auto"),
                    help="auto: Ollama native if the endpoint answers /api/version, else OpenAI-compatible")
    ap.add_argument("--interval", type=float, default=float(env("VLM_INTERVAL", "8")))
    ap.add_argument("--max-tokens", type=int, default=int(env("VLM_MAX_TOKENS", "120")))
    ap.add_argument("--max-width", type=int, default=int(env("VLM_MAX_WIDTH", "640")), help="frame is downscaled to this width before upload")
    ap.add_argument("--v4l2-size", default=env("VLM_V4L2_SIZE", "1920x1080"), help="capture size for v4l2 sources, WxH (iCAM-540: 1920x1080, 1408x1080, 3840x2160)")
    ap.add_argument("--v4l2-ctrls", default=env("VLM_V4L2_CTRLS", "exposure_mode=1,sensor_gain_mode=1,auto_exposure_max=330"),
                    help="v4l2-ctl controls applied once at open. iCAM-540 default: auto exposure and gain, exposure capped "
                         "at one 30 fps frame (330 x 100 us) so a dim room does not drop the sensor to a few fps; '' to skip")
    ap.add_argument("--timeout", type=float, default=90.0)
    ap.add_argument("--alert", action="append", default=[], help="initial alert rule (repeatable, max 3)")
    ap.add_argument("--paused", action="store_true")
    ap.add_argument("--iotc-sock", default=env("IOTC_SOCKET", ""))
    ap.add_argument("--iotc-cmd-sock", default=env("IOTC_CMD_SOCK", ""))
    ap.add_argument("--focus", default=env("VLM_FOCUS", ""), metavar="auto|home|N",
                    help="iCAM-540 lens at start: 'auto' sweeps for the sharpest image (~20 s), or a position 0-2294")
    ap.add_argument("--zoom", type=float, default=float(env("VLM_ZOOM", "1.0")), help="digital zoom 1.0-4.0 (centre crop; the lens has no optical zoom)")
    ap.add_argument("--rotate", type=int, choices=[0, 90, 180, 270], default=int(env("VLM_ROTATE", "0")), help="rotate frames clockwise")
    ap.add_argument("--web", type=int, default=int(env("VLM_WEB", "0")), metavar="PORT",
                    help="serve the live view (video + narration + ask box) on this port, e.g. 8088; 0 = off")
    ap.add_argument("--print-telemetry", action="store_true")
    ap.add_argument("--once", action="store_true", help="run one cycle, print the result and exit")
    args = ap.parse_args()
    try:
        args.v4l2_size = tuple(int(x) for x in args.v4l2_size.lower().split("x"))
        assert len(args.v4l2_size) == 2
    except Exception:
        ap.error("--v4l2-size must look like 1920x1080")

    n = Narrator(args)
    if args.once:
        n.frames.start()
        try:
            n.cycle()
        finally:
            n.frames.stop()
        return 0
    n.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
