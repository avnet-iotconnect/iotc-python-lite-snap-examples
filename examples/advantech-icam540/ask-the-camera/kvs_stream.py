#!/usr/bin/env python3
"""
Stream the camera's live video to /IOTCONNECT's Video Streaming tab (AWS Kinesis Video Streams, PutMedia).

Runs next to the /IOTCONNECT snap, which owns the MQTT connection: everything KVS needs comes from
HTTPS calls, not MQTT. Discovery and identity (public) give the KVS credentials endpoint, the stream
name (the device's AWS IoT thing name) and the template's auto-start flag; the credentials endpoint
(mutual TLS with the snap's device certificate) gives temporary AWS keys. GStreamer then pushes H.264
into kvssink, reading the keys from a credential file this script keeps fresh.

Video comes from the narrator's live view by default (it owns the sensor), so this works while the
VLM demo runs; --source v4l2:/dev/video0 reads the sensor directly when the narrator is not running.

  ./kvs_stream.py                       # stream until stopped (Ctrl+C)
  ./kvs_stream.py --check               # identity + credentials only, print what the device is provisioned with
  ./kvs_stream.py --source v4l2:/dev/video0 --width 1280 --fps 15 --bitrate 2000

Limits: the snap (SDK 1.1) does not forward the portal's Start/Stop video messages, so this streams
whenever it runs; use the kvs-stream.service to run it at boot, or start/stop it with systemctl.
"""

import argparse
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone

SNAP_COMMON = "/var/snap/iotconnect/common"


def log(tag, msg):
    print(f"[{tag}] {time.strftime('%H:%M:%S')} {msg}", flush=True)


# --------------------------------------------------------------------------
# /IOTCONNECT device REST API (discovery, identity, KVS credentials)
# --------------------------------------------------------------------------

def load_device(common):
    try:
        from avnet.iotconnect.sdk.sdklib.config import DeviceProperties, DeviceTlsCredentials
        from avnet.iotconnect.sdk.sdklib.dra import DeviceRestApi
    except ImportError:
        raise SystemExit("needs the /IOTCONNECT lib: pip3 install --user iotconnect-lib")
    cfg_path = os.path.join(common, "iotcDeviceConfig.json")
    with open(cfg_path) as f:
        cfg = json.load(f)
    duid = cfg.get("uid") or cfg.get("duid")
    props = DeviceProperties(duid=duid, cpid=cfg["cpid"], env=cfg["env"], platform=cfg.get("pf", "aws"))
    tls = DeviceTlsCredentials(device_cert_path=os.path.join(common, "device-cert.pem"),
                               device_pkey_path=os.path.join(common, "device-pkey.pem"))
    return DeviceRestApi(props, tls, verbose=False), duid


class KvsCredentials:
    """Keeps a kvssink credential file fresh: 'CREDENTIALS <key> <expiry ISO8601> <secret> <token>'."""

    def __init__(self, dra, path):
        self.dra = dra
        self.path = path
        self.expiry = None

    def refresh(self):
        creds = self.dra.get_aws_credentials_kvs()
        exp = creds.expiration
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        self.expiry = exp
        line = "CREDENTIALS\t%s\t%s\t%s\t%s\n" % (
            creds.access_key_id, exp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            creds.secret_access_key, creds.session_token)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path), prefix=".creds.")
        with os.fdopen(fd, "w") as f:
            f.write(line)
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.path)
        log("CREDS", f"refreshed, expire {exp.isoformat()} ({self.secs_left() // 60} min)")

    def secs_left(self):
        return int((self.expiry - datetime.now(timezone.utc)).total_seconds()) if self.expiry else 0


def region_from_endpoint(url, default="us-east-1"):
    m = re.search(r"\.iot\.([a-z0-9-]+)\.amazonaws\.com", url or "")
    return m.group(1) if m else default


# --------------------------------------------------------------------------
# GStreamer pipeline
# --------------------------------------------------------------------------

def have_element(name):
    return subprocess.run(["gst-inspect-1.0", name], capture_output=True).returncode == 0


def build_pipeline(args, stream_name, cred_path, region):
    w, h, fps = args.width, args.height, args.fps
    if args.source.startswith("v4l2:"):
        node = args.source.split(":", 1)[1] or "/dev/video0"
        src = (f"v4l2src device={node} do-timestamp=true ! video/x-raw,format=YUY2,width=1920,height=1080 ! "
               f"videoscale ! video/x-raw,width={w},height={h} ! videorate ! video/x-raw,framerate={fps}/1 ! videoconvert")
    elif args.source.startswith("rtsp://"):
        src = f"rtspsrc location={args.source} latency=200 ! decodebin ! videoscale ! video/x-raw,width={w},height={h} ! videoconvert"
    else:  # the narrator's MJPEG live view
        src = (f"souphttpsrc location={args.source} is-live=true do-timestamp=true ! multipartdemux ! jpegdec ! "
               f"videoscale ! video/x-raw,width={w},height={h} ! videorate ! video/x-raw,framerate={fps}/1 ! videoconvert")
    if args.encoder == "auto":
        args.encoder = "nvv4l2h264enc" if have_element("nvv4l2h264enc") and have_element("nvvidconv") else "x264enc"
    if args.encoder == "nvv4l2h264enc":
        enc = (f"video/x-raw,format=I420 ! nvvidconv ! video/x-raw(memory:NVMM),format=NV12 ! "
               f"nvv4l2h264enc bitrate={args.bitrate * 1000} iframeinterval={fps * 2} insert-sps-pps=true idrinterval={fps * 2} ! "
               f"h264parse")
    else:
        enc = (f"video/x-raw,format=I420 ! x264enc bframes=0 key-int-max={fps * 2} bitrate={args.bitrate} "
               f"speed-preset=ultrafast tune=zerolatency ! h264parse")
    sink = (f"video/x-h264,stream-format=avc,alignment=au ! kvssink stream-name={stream_name} storage-size=128 "
            f"credential-path={cred_path} aws-region={region} framerate={fps}")
    return f"{src} ! {enc} ! {sink}"


class Streamer:
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.proc = None

    def start(self):
        cmd = ["gst-launch-1.0", "-q"] + shlex.split(self.pipeline)
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid, text=True)
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        for line in self.proc.stdout:
            line = line.rstrip()
            if line and not line.startswith("Setting pipeline") and "Redistribute latency" not in line:
                log("GST", line[:200])

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGINT)
                self.proc.wait(timeout=8)
            except Exception:
                try:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                except Exception:
                    pass
        self.proc = None


# --------------------------------------------------------------------------

def main():
    env = os.environ.get
    ap = argparse.ArgumentParser(description="Stream video to /IOTCONNECT KVS (PutMedia)")
    ap.add_argument("--source", default=env("KVS_SOURCE", "http://127.0.0.1:8088/stream.mjpg"),
                    help="narrator live view URL (default), v4l2:/dev/videoN, or rtsp://...")
    ap.add_argument("--width", type=int, default=int(env("KVS_WIDTH", "960")))
    ap.add_argument("--height", type=int, default=int(env("KVS_HEIGHT", "540")))
    ap.add_argument("--fps", type=int, default=int(env("KVS_FPS", "12")))
    ap.add_argument("--bitrate", type=int, default=int(env("KVS_BITRATE", "1200")), help="kbit/s")
    ap.add_argument("--encoder", choices=["auto", "x264enc", "nvv4l2h264enc"], default=env("KVS_ENCODER", "auto"))
    ap.add_argument("--region", default=env("KVS_REGION", ""), help="AWS region; default: from the credentials endpoint")
    ap.add_argument("--stream-name", default=env("KVS_STREAM_NAME", ""), help="default: the device's client id (thing name)")
    ap.add_argument("--snap-common", default=env("IOTC_SNAP_COMMON", SNAP_COMMON))
    ap.add_argument("--check", action="store_true", help="only fetch identity and credentials, then exit")
    ap.add_argument("--ignore-autostart", action="store_true", help="stream even if the template's Auto Start Video Stream is off")
    args = ap.parse_args()

    if not shutil.which("gst-launch-1.0"):
        raise SystemExit("gst-launch-1.0 not found")
    dra, duid = load_device(args.snap_common)
    ident = dra.get_identity_data()
    vs = ident.vs
    if not vs or not vs.url:
        raise SystemExit(f"device {duid}: Video Streaming is not enabled in its /IOTCONNECT template "
                         f"(the identity response has no 'vs' block). It has to be set when the device is created.")
    stream_name = args.stream_name or ident.client_id
    region = args.region or region_from_endpoint(vs.url)
    log("IOTC", f"device {duid}  thing/stream {stream_name}  region {region}  auto-start {vs.as_}  webrtc channel {bool(vs.carn)}")
    log("IOTC", f"credentials endpoint {vs.url}")

    cred_dir = os.path.join(tempfile.gettempdir(), f"kvs-{duid}")
    os.makedirs(cred_dir, mode=0o700, exist_ok=True)
    creds = KvsCredentials(dra, os.path.join(cred_dir, "credentials"))
    creds.refresh()
    if args.check:
        log("IOTC", "credentials OK; not streaming (--check)")
        return 0
    if vs.as_ is False and not args.ignore_autostart:
        log("IOTC", "template has Auto Start Video Stream off; streaming anyway because the snap cannot deliver "
                    "the portal's Start command to this process (use --ignore-autostart to silence this)")

    if not have_element("kvssink"):
        raise SystemExit("kvssink not found: build the KVS producer SDK (install_kvs.sh) or set GST_PLUGIN_PATH")
    pipeline = build_pipeline(args, stream_name, creds.path, region)
    log("GST", f"encoder {args.encoder}  {args.width}x{args.height}@{args.fps} {args.bitrate} kbit/s  source {args.source}")
    log("GST", pipeline)

    st = Streamer(pipeline)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *a: stop.set())
    signal.signal(signal.SIGINT, lambda *a: stop.set())
    backoff = 3
    try:
        while not stop.is_set():
            if not st.alive():
                log("GST", "starting pipeline")
                st.start()
                time.sleep(3)
                if not st.alive():
                    log("GST", f"pipeline exited (rc={st.proc.returncode if st.proc else '?'}); retry in {backoff} s")
                    st.proc = None
                    stop.wait(backoff)
                    backoff = min(60, backoff * 2)
                    continue
                backoff = 3
                log("GST", "streaming")
            if creds.secs_left() < 300:
                try:
                    creds.refresh()
                except Exception as e:
                    log("CREDS", f"refresh failed: {e}")
            stop.wait(5)
    finally:
        st.stop()
        log("GST", "stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
