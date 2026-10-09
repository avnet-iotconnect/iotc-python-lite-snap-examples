#!/usr/bin/env python3
"""
Live video into /IOTCONNECT's Video Streaming tab over Kinesis Video Streams WebRTC (sub-second latency).

For a device created with the WebRTC stream resource (the identity response carries a signaling
channel ARN). The device is the WebRTC "master": it waits on the KVS signaling channel and answers
every viewer the portal's Video Streaming tab opens. Like kvs_stream.py it runs next to the
/IOTCONNECT snap and needs no MQTT: discovery + identity give the channel and the credentials
endpoint; the credentials endpoint (mutual TLS with the snap's device certificate) gives temporary
AWS keys, refreshed before they expire.

Frames come from the narrator's live view (MJPEG) by default, so it works while the VLM demo owns
the sensor. Pure Python (aiortc + av + boto3 + websockets), no C++ build.

  ./kvs_webrtc.py                 # run until stopped; open the device's Video Streaming tab to watch
  ./kvs_stream.py --check         # prints "webrtc channel True" when this device is provisioned for it
"""

import argparse
import os
import queue
import re
import signal
import sys
import threading
import time
import urllib.request

import numpy as np

try:
    import cv2
except ImportError:
    raise SystemExit("needs OpenCV: pip3 install opencv-python-headless")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kvs_stream import load_device, region_from_endpoint, log  # noqa: E402
import iotc_kvs_webrtc as webrtc  # noqa: E402


class MjpegFrames(threading.Thread):
    """Reads an MJPEG stream and keeps the queue topped up with I420 frames at the wanted rate."""

    def __init__(self, url, q, width, height, fps):
        super().__init__(name="mjpeg", daemon=True)
        self.url, self.q, self.w, self.h, self.fps = url, q, width, height, fps
        self.stop_event = threading.Event()
        self.count = 0
        self.last = 0.0
        self.error = ""

    def run(self):
        while not self.stop_event.is_set():
            try:
                with urllib.request.urlopen(self.url, timeout=10) as r:
                    buf = b""
                    while not self.stop_event.is_set():
                        chunk = r.read(65536)
                        if not chunk:
                            raise RuntimeError("stream ended")
                        buf += chunk
                        while True:
                            h = buf.find(b"\r\n\r\n")
                            if h < 0:
                                break
                            m = re.search(rb"Content-Length:\s*(\d+)", buf[:h], re.I)
                            if not m:
                                buf = buf[h + 4:]
                                continue
                            n, start = int(m.group(1)), h + 4
                            if len(buf) < start + n:
                                break
                            self._push(buf[start:start + n])
                            buf = buf[start + n:]
            except Exception as e:
                self.error = f"{type(e).__name__}: {e}"
                log("SRC", f"{self.error}; retry in 2 s")
                self.stop_event.wait(2.0)

    def _push(self, jpg):
        now = time.time()
        if now - self.last < 1.0 / self.fps - 0.004:
            return
        img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return
        if (img.shape[1], img.shape[0]) != (self.w, self.h):
            img = cv2.resize(img, (self.w, self.h))
        i420 = cv2.cvtColor(img, cv2.COLOR_BGR2YUV_I420)  # (h*3/2, w), what av wants for yuv420p
        try:
            self.q.put_nowait(i420)
        except queue.Full:
            try:
                self.q.get_nowait()
                self.q.put_nowait(i420)
            except queue.Empty:
                pass
        self.last = now
        self.count += 1
        self.error = ""


def main():
    env = os.environ.get
    ap = argparse.ArgumentParser(description="Stream video to /IOTCONNECT over KVS WebRTC (device = master)")
    ap.add_argument("--source", default=env("KVS_SOURCE", "http://127.0.0.1:8088/stream.mjpg"), help="MJPEG URL (the narrator's live view)")
    ap.add_argument("--width", type=int, default=int(env("KVS_WIDTH", "960")))
    ap.add_argument("--height", type=int, default=int(env("KVS_HEIGHT", "540")))
    ap.add_argument("--fps", type=int, default=int(env("KVS_FPS", "12")))
    ap.add_argument("--region", default=env("KVS_REGION", ""), help="AWS region; default: from the credentials endpoint")
    ap.add_argument("--snap-common", default=env("IOTC_SNAP_COMMON", "/var/snap/iotconnect/common"))
    args = ap.parse_args()
    if args.width % 2 or args.height % 2:
        ap.error("--width and --height must be even (I420)")

    dra, duid = load_device(args.snap_common)
    ident = dra.get_identity_data()
    vs = ident.vs
    if not vs or not vs.url:
        raise SystemExit(f"device {duid}: Video Streaming is not enabled in its /IOTCONNECT template")
    if not vs.carn:
        raise SystemExit(f"device {duid}: no WebRTC signaling channel. The device was created with the Video Stream "
                         f"(PutMedia) resource: use kvs_stream.py instead")
    region = args.region or region_from_endpoint(vs.url)
    creds = dra.get_aws_credentials_kvs()
    log("IOTC", f"device {duid}  channel {vs.carn}  region {region}  auto-start {vs.as_}")
    log("IOTC", f"credentials until {creds.expiration.isoformat()}")

    q = queue.Queue(maxsize=4)
    frames = MjpegFrames(args.source, q, args.width, args.height, args.fps)
    frames.start()

    def master_loop():
        while True:
            c = creds_box[0]
            webrtc.start_webrtc(region, vs.carn, c.access_key_id, c.secret_access_key, c.session_token, q, args.fps)
            log("RTC", "master loop ended; restarting in 5 s")
            time.sleep(5)

    creds_box = [creds]
    threading.Thread(target=master_loop, name="webrtc", daemon=True).start()
    log("RTC", f"master waiting for viewers ({args.width}x{args.height}@{args.fps} from {args.source}); "
               f"open the device's Video Streaming tab in /IOTCONNECT")

    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *a: stop.set())
    signal.signal(signal.SIGINT, lambda *a: stop.set())
    last_count, last_report = 0, time.time()
    while not stop.is_set():
        stop.wait(10)
        c = creds_box[0]
        secs = (c.expiration - __import__("datetime").datetime.now(__import__("datetime").timezone.utc)).total_seconds()
        if secs < 600:
            try:
                c = dra.get_aws_credentials_kvs()
                creds_box[0] = c
                if webrtc.webrtc_client is not None:
                    webrtc.webrtc_client.refresh_credentials(c.access_key_id, c.secret_access_key, c.session_token)
                log("IOTC", f"credentials refreshed, until {c.expiration.isoformat()}")
            except Exception as e:
                log("IOTC", f"credential refresh failed: {e}")
        if time.time() - last_report >= 30:
            wc = webrtc.webrtc_client
            peers = {k: v.connectionState for k, v in wc.PCMap.items()} if wc else {}
            fps = (frames.count - last_count) / (time.time() - last_report)
            log("RTC", f"frames {fps:.1f}/s  viewers {len(peers)} {peers}" + (f"  source error: {frames.error}" if frames.error else ""))
            last_count, last_report = frames.count, time.time()
    frames.stop_event.set()
    log("RTC", "stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
