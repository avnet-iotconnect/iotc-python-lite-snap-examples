#!/usr/bin/env python3
"""Vision AI demo for Ubuntu that sends inference telemetry via IoTConnect sockets.

Requirements:
  - OpenCV (cv2)
  - Optional runtime by backend:
    - ultralytics (YOLO .pt/.pth)
    - onnxruntime (.onnx)
    - OpenCV DNN / cv-only (.onnx/.pb/.prototxt/.caffemodel/.xml cascades)

Inputs supported:
  - webcam/index (e.g. 0)
  - USB camera / local video file
  - RTSP / HTTP stream URL
  - local image file (single-frame replay)

Control commands are read from /var/snap/iotconnect/common/iotc_cmd.sock
and support both JSON and plain-text forms:
  - {"name":"start","ack_id":"..."}
  - {"name":"set_model","args":["/path/model.pt"],"ack_id":"..."}
  - {"cmd":"set_model /path/model.pt"}
  - start
"""

import argparse
import json
import os
import select
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import cv2  # type: ignore
    _CV2_IMPORT_ERROR = None
except Exception as err:  # pragma: no cover
    cv2 = None
    _CV2_IMPORT_ERROR = f"{type(err).__name__}: {err}"


SOCKET_TX = "/var/snap/iotconnect/common/iotc.sock"
SOCKET_RX = "/var/snap/iotconnect/common/iotc_cmd.sock"

_tx_lock = threading.Lock()
_web_lock = threading.Lock()
_web_jpeg_frame: Optional[bytes] = None

COCO80_NAMES = (
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush"
)
DEFAULT_HAAR_CASCADE = "haarcascade_frontalface_default.xml"
CV_ONLY_DNN_PRESETS = {"ssd", "yolo", "auto"}
CV_ONLY_SPECIAL_MODELS = {
    "hog",
    "hog_person",
    "hog-person",
    "hog_people",
    "face",
    "haar",
    "haarcascade",
    "haarcascade_face",
    "face_haar",
}


def _require_package(name: str, instruction: str):
    try:
        __import__(name)
    except Exception as err:
        print(f"[ERR] Missing dependency: {name}")
        print(f"[ERR] import error: {type(err).__name__}: {err}")
        print(f"[ERR] Install with: {instruction}")
        raise SystemExit(3)


def iso_now():
    return datetime.now(timezone.utc).isoformat()


def _require_cv2():
    if cv2 is None:
        print("[ERR] Missing dependency: cv2 (OpenCV)")
        print(f"[ERR] import error: {_CV2_IMPORT_ERROR}")
        print("[ERR] Install one of the following (in the active environment):")
        print("      pip install opencv-python")
        print("      pip install opencv-python-headless  # headless fallback")
        print("      (or sudo apt install python3-opencv and use a venv with --system-site-packages)")
        raise SystemExit(2)


def socket_send(payload: Dict[str, Any], path: str = SOCKET_TX) -> bool:
    with _tx_lock:
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect(path)
            s.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            try:
                s.shutdown(socket.SHUT_WR)
            finally:
                s.close()
            return True
        except Exception as e:
            print(f"[TX] failed: {e} path={path}")
            return False


def _coerce_source(raw: str):
    if isinstance(raw, int):
        return raw
    raw = str(raw).strip()
    if raw.isdigit():
        return int(raw)
    return raw


def _norm_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return os.path.abspath(os.path.expanduser(str(path)))


def _is_image_file(path: str) -> bool:
    if not isinstance(path, str):
        return False
    lower = path.lower()
    return lower.endswith((
        ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".gif"
    ))


def _set_web_frame(frame, jpeg_quality: int = 80):
    if cv2 is None or frame is None:
        return
    quality = max(10, min(100, int(jpeg_quality)))
    ok, enc = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        return
    global _web_jpeg_frame
    with _web_lock:
        _web_jpeg_frame = enc.tobytes()


def _render_overlay_frame(frame, overlay, loaded_backend: str, stream: str, model_path: str, infer_ms: float):
    try:
        if loaded_backend == "torch":
            try:
                disp = overlay.plot()
            except Exception:
                disp = frame
        else:
            disp = frame.copy()
            for label, conf_score, box, _cls in overlay or []:
                x1, y1, x2, y2 = box
                _draw_box(disp, label, conf_score, x1, y1, x2, y2)
    except Exception:
        disp = frame
    cv2.putText(
        disp,
        f"{stream} | model={os.path.basename(model_path)} | {infer_ms:.1f}ms",
        (12, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 0),
        1,
        cv2.LINE_AA
    )
    return disp


class _WebStreamHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = (
                "<!doctype html><html><head><meta charset='utf-8'>"
                "<title>IoTC Vision Stream</title>"
                "<style>body{margin:0;background:#111;color:#eee;font-family:system-ui,sans-serif}"
                "h1{font-size:16px;margin:10px 12px}img{display:block;width:100%;max-width:1280px;margin:0 auto}"
                "</style></head><body><h1>IoTC Vision Overlay Stream</h1>"
                "<img src='/stream.mjpg' alt='stream'></body></html>"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if self.path not in ("/stream.mjpg", "/stream"):
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        try:
            while True:
                with _web_lock:
                    frame = _web_jpeg_frame
                if frame is None:
                    time.sleep(0.1)
                    continue
                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode("ascii"))
                self.wfile.write(frame)
                self.wfile.write(b"\r\n")
                time.sleep(0.05)
        except (BrokenPipeError, ConnectionResetError):
            return


def start_web_stream_server(host: str, port: int):
    server = ThreadingHTTPServer((host, int(port)), _WebStreamHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[WEB] stream ready: http://{host}:{port}/ (use device IP if host is 0.0.0.0)")
    return server


def extract_top_classes(results, names: Dict[int, str], k: int = 3):
    top = []
    boxes = getattr(results, "boxes", None)
    if boxes is None:
        return top
    for b in boxes:
        try:
            cls_id = int(b.cls[0])
            conf = float(b.conf[0])
            name = names.get(cls_id, str(cls_id))
            top.append((name, conf))
        except Exception:
            continue
    top.sort(key=lambda x: x[1], reverse=True)
    while len(top) < k:
        top.append(("", 0.0))
    return top[:k]


class ModelManager:
    def __init__(self, model_path: str, backend: str = "auto", labels: Optional[str] = None):
        raw_model_path = str(model_path) if model_path else model_path
        if raw_model_path and raw_model_path.strip().lower() in CV_ONLY_SPECIAL_MODELS:
            self.model_path = raw_model_path
        else:
            self.model_path = _norm_path(raw_model_path)
        self.backend_preference = backend
        self.backend = "auto"
        self.model = None
        self.names: Dict[int, str] = {}
        self.labels_path = _norm_path(labels)
        self.lock = threading.Lock()
        self.last_load_ts = 0.0
        self._onnx = None
        self._onnx_input_name = None
        self._onnx_input_size = (640, 640)
        self._model_cfg = None
        self._cv_variant = "none"
        self._cv_hog = None
        self._cv_face = None
        self._cv_dnn = None
        self._cv_dnn_cfg: Dict[str, Any] = {}
        self._cv_dnn_input_size = (300, 300)
        self._cv_dnn_scale = 1.0
        self._cv_dnn_mean = (0.0, 0.0, 0.0)
        self._cv_dnn_swap_rb = True
        self._cv_dnn_detection_type = "auto"

    def _load_names(self, model_path: str, backend: str, labels_path: Optional[str] = None):
        names = {}
        label_path = _norm_path(labels_path) if labels_path else _norm_path(self.labels_path)

        if backend in ("onnx", "cv_only"):
            if label_path and os.path.exists(label_path):
                try:
                    with open(label_path, "r", encoding="utf-8") as fp:
                        lines = [ln.strip() for ln in fp if ln.strip()]
                    names = {i: n for i, n in enumerate(lines)}
                except Exception as e:
                    print(f"[WARN] failed to load labels file {label_path}: {e}")
            if not names:
                names = {i: n for i, n in enumerate(COCO80_NAMES)}
            return names

        try:
            from ultralytics import YOLO  # noqa: PLC0415
            model = YOLO(model_path)
            raw_names = getattr(model.model, "names", {})
            if isinstance(raw_names, (list, tuple)):
                names = {i: str(v) for i, v in enumerate(raw_names)}
            elif isinstance(raw_names, dict):
                names = {int(k): str(v) for k, v in raw_names.items()}
            else:
                names = {}
            self.model = model
            return names
        except Exception as e:
            print(f"[ERR] failed loading torch model labels from {model_path}: {e}")
            return {}

    def _resolve_backend(self, requested: str, model_path: str) -> str:
        requested = (requested or "auto").lower()
        if requested in ("torch", "onnx", "cv_only"):
            return requested
        ext = os.path.splitext(model_path)[1].lower()
        if ext == ".onnx":
            return "onnx"
        if ext in (".pt", ".pth"):
            return "torch"
        if ext in (".xml", ".caffemodel", ".prototxt", ".pb", ".onnx", ".tflite"):
            return "cv_only"
        return "auto"

    def ensure_model(
        self,
        path: str,
        requested_backend: str = "auto",
        model_cfg: Optional[str] = None,
        labels_path: Optional[str] = None,
    ):
        with self.lock:
            raw_path = str(path) if path else path
            if raw_path and raw_path.strip().lower() in CV_ONLY_SPECIAL_MODELS:
                path = raw_path
            else:
                path = _norm_path(path) if path else path
            model_cfg = _norm_path(model_cfg) if model_cfg else None
            target_backend = self._resolve_backend(requested_backend, path)
            if labels_path is not None:
                self.labels_path = _norm_path(labels_path)
            if (
                self.model is None
                or path != self.model_path
                or self.backend != target_backend
                or self._model_cfg != model_cfg
            ):
                self._load(path, target_backend, model_cfg=model_cfg)
            elif target_backend == "auto":
                self.backend_preference = requested_backend
            return self.model, self.backend

    def _load(self, path: str, backend: str, model_cfg: Optional[str] = None):
        is_special_model = str(path).strip().lower() in CV_ONLY_SPECIAL_MODELS
        if backend == "cv_only" and is_special_model:
            pass
        elif not os.path.exists(path):
            raise FileNotFoundError(f"Model path does not exist: {path}")

        if backend == "onnx":
            self._load_onnx(path)
            self.backend = "onnx"
            self.names = self._load_names(path, self.backend, self.labels_path)
            self.model_path = path
            self._model_cfg = None
            self.backend_preference = "onnx"
            self.last_load_ts = time.time()
            return

        if backend == "cv_only":
            self._load_cv_only(path, model_cfg=model_cfg)
            self.backend = "cv_only"
            self.model_path = path
            self._model_cfg = model_cfg
            self.backend_preference = "cv_only"
            self.last_load_ts = time.time()
            return

        try:
            from ultralytics import YOLO  # noqa: PLC0415
            self.model = YOLO(path)
            self.backend = "torch"
            self.model_path = path
            self._model_cfg = None
            self.backend_preference = "torch"
            self.names = self._load_names(path, self.backend, self.labels_path)
            self.last_load_ts = time.time()
            print(f"[MODEL] loaded torch model: {path}")
            return
        except Exception as e:
            if backend == "torch":
                raise RuntimeError(
                    "Torch backend requested but not available. Install torch/ultralytics or use an ONNX model."
                ) from e
            print(f"[WARN] torch model load failed for {path}: {e}; falling back to ONNX if possible")
            if path.endswith(".onnx"):
                self._load_onnx(path)
                self.backend = "onnx"
            else:
                raise

    def _load_onnx(self, path: str):
        try:
            import onnxruntime as ort
        except Exception as e:
            raise RuntimeError("onnxruntime is not installed. Install with: python3 -m pip install onnxruntime") from e

        print(f"[MODEL] loading ONNX model {path}")
        self._onnx = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        inputs = self._onnx.get_inputs()
        if not inputs:
            raise RuntimeError(f"ONNX model missing input metadata: {path}")

        self._onnx_input_name = inputs[0].name
        shape = inputs[0].shape
        if len(shape) >= 4:
            h = int(shape[2]) if isinstance(shape[2], int) else 640
            w = int(shape[3]) if isinstance(shape[3], int) else 640
            self._onnx_input_size = (w, h)
        else:
            self._onnx_input_size = (640, 640)
        self.model = self._onnx
        self.names = self._load_names(path, "onnx", self.labels_path)
        self.last_load_ts = time.time()

    def _load_dnn_manifest(self, manifest_path: Optional[str]) -> Optional[Dict[str, Any]]:
        if not manifest_path or not os.path.exists(manifest_path):
            return None
        if not manifest_path.lower().endswith(".json"):
            return None
        try:
            with open(manifest_path, "r", encoding="utf-8") as fp:
                payload = json.loads(fp.read())
        except Exception as e:
            print(f"[WARN] failed to read cv_only manifest {manifest_path}: {e}")
            return None
        if not isinstance(payload, dict):
            print(f"[WARN] cv_only manifest must be JSON object: {manifest_path}")
            return None
        return payload

    def _load_cv_only(self, path: str, model_cfg: Optional[str] = None):
        self._cv_hog = None
        self._cv_face = None
        self._cv_dnn = None
        self._cv_dnn_cfg = {}
        self._cv_dnn_scale = 1.0
        self._cv_dnn_mean = (0.0, 0.0, 0.0)
        self._cv_dnn_swap_rb = True
        self._cv_dnn_detection_type = "auto"

        manifest = self._load_dnn_manifest(model_cfg)
        if manifest:
            if manifest.get("labels"):
                self.labels_path = _norm_path(str(manifest.get("labels")))
            dnn_name = str(manifest.get("detection", "auto")).lower()
            if dnn_name in CV_ONLY_DNN_PRESETS:
                self._cv_dnn_detection_type = dnn_name
            size = manifest.get("input_size")
            if isinstance(size, (list, tuple)) and len(size) >= 2:
                self._cv_dnn_input_size = (int(size[0]), int(size[1]))
            if manifest.get("scale") is not None:
                try:
                    self._cv_dnn_scale = float(manifest.get("scale"))
                except Exception:
                    pass
            if manifest.get("mean") is not None:
                mean = manifest.get("mean")
                if isinstance(mean, (list, tuple)) and len(mean) >= 3:
                    self._cv_dnn_mean = (float(mean[0]), float(mean[1]), float(mean[2]))
            swap_rb = manifest.get("swap_rb")
            if isinstance(swap_rb, (bool, int)):
                self._cv_dnn_swap_rb = bool(swap_rb)
            if manifest.get("model"):
                path = _norm_path(str(manifest.get("model"))) or path
            if manifest.get("cfg") and not model_cfg:
                model_cfg = _norm_path(str(manifest.get("cfg")))

        model_norm = str(path).strip().lower()
        if model_norm in ("hog", "hog_person", "hog-person", "hog_people"):
            self._cv_variant = "hog"
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            self._cv_hog = hog
            self.names = self._load_names(path, "cv_only", self.labels_path)
            if not self.names:
                self.names = {0: "person"}
            return

        if model_norm in ("face", "haar", "haarcascade", "haarcascade_face", "face_haar"):
            cascade_path = model_cfg or os.path.join(cv2.data.haarcascades, DEFAULT_HAAR_CASCADE)
            if not os.path.exists(cascade_path):
                raise RuntimeError(f"Haar cascade not found: {cascade_path}")
            cascade = cv2.CascadeClassifier(cascade_path)
            if cascade.empty():
                raise RuntimeError(f"failed to load Haar cascade: {cascade_path}")
            self._cv_variant = "face"
            self._cv_face = cascade
            self.names = {0: "face"}
            return

        if path.lower().endswith(".xml"):
            if not os.path.exists(path):
                raise RuntimeError(f"Model file not found: {path}")
            cascade = cv2.CascadeClassifier(path)
            if cascade.empty():
                raise RuntimeError(f"failed to load Haar cascade: {path}")
            self._cv_variant = "face"
            self._cv_face = cascade
            self.names = {0: "face"}
            return

        self._load_cv_dnn(path, model_cfg=model_cfg)
        self._cv_variant = "dnn"
        self.names = self._load_names(path, "cv_only", self.labels_path)

    def _load_cv_dnn(self, path: str, model_cfg: Optional[str] = None):
        ext = os.path.splitext(path)[1].lower()
        cfg_path = _norm_path(model_cfg)

        if ext == ".caffemodel":
            cfg_path = cfg_path or os.path.splitext(path)[0] + ".prototxt"
            if not cfg_path or not os.path.exists(cfg_path):
                raise FileNotFoundError(f"Caffe config not found: {cfg_path}")
            self._cv_dnn = cv2.dnn.readNetFromCaffe(cfg_path, path)
            self._cv_dnn_cfg.update({"format": "caffe", "config": cfg_path, "model": path})
            if self._cv_dnn_detection_type == "auto":
                self._cv_dnn_detection_type = "ssd"
            return

        if ext == ".prototxt":
            model_file = os.path.splitext(path)[0] + ".caffemodel"
            if not os.path.exists(model_file):
                raise FileNotFoundError(f"Caffe model not found: {model_file}")
            self._cv_dnn = cv2.dnn.readNetFromCaffe(path, model_file)
            self._cv_dnn_cfg.update({"format": "caffe", "config": path, "model": model_file})
            if self._cv_dnn_detection_type == "auto":
                self._cv_dnn_detection_type = "ssd"
            return

        if ext == ".pb":
            self._cv_dnn = cv2.dnn.readNetFromTensorflow(path, cfg_path or "")
            self._cv_dnn_cfg.update({"format": "tf", "config": cfg_path, "model": path})
            if self._cv_dnn_detection_type == "auto":
                self._cv_dnn_detection_type = "ssd"
            return

        if ext == ".onnx":
            self._cv_dnn = cv2.dnn.readNetFromONNX(path)
            self._cv_dnn_cfg.update({"format": "onnx", "model": path})
            if self._cv_dnn_detection_type == "auto":
                self._cv_dnn_detection_type = "yolo"
            return

        raise RuntimeError(f"Unsupported cv_only model format: {path}")

    def _preprocess_onnx(self, frame: Any):
        h, w = frame.shape[:2]
        target_w, target_h = self._onnx_input_size
        scale = min(target_w / w, target_h / h)
        nh = int(round(h * scale))
        nw = int(round(w * scale))
        resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
        pad_w = target_w - nw
        pad_h = target_h - nh
        left = pad_w // 2
        top = pad_h // 2
        right = pad_w - left
        bottom = pad_h - top
        padded = cv2.copyMakeBorder(
            resized, top, bottom, left, right,
            borderType=cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )
        rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
        tensor = rgb.astype(np.float32) / 255.0
        tensor = np.transpose(tensor, (2, 0, 1))[None, ...]
        return tensor, scale, left, top, w, h

    def _xyxy_from_xywh(self, box):
        x, y, bw, bh = [float(v) for v in box[:4]]
        return [
            x - bw / 2.0,
            y - bh / 2.0,
            x + bw / 2.0,
            y + bh / 2.0,
        ]

    def _restore_box(self, box, scale, left, top, src_w, src_h):
        x1, y1, x2, y2 = box
        x1 = max(0.0, min(src_w, (x1 - left) / scale))
        y1 = max(0.0, min(src_h, (y1 - top) / scale))
        x2 = max(0.0, min(src_w, (x2 - left) / scale))
        y2 = max(0.0, min(src_h, (y2 - top) / scale))
        return int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))

    def predict(self, frame, conf: float):
        if self.model is None and self._cv_dnn is None and self._cv_hog is None and self._cv_face is None:
            raise RuntimeError("No model loaded")

        if self.backend == "onnx":
            return self._predict_onnx(frame, conf)
        if self.backend == "cv_only":
            return self._predict_cv_only(frame, conf)

        results = self.model(frame, conf=conf, verbose=False)
        det = extract_top_classes(results[0], self.names, k=3)
        return det, results

    def _predict_onnx(self, frame, conf: float):
        tensor, scale, left, top, src_w, src_h = self._preprocess_onnx(frame)
        outputs = self._onnx.run(None, {self._onnx_input_name: tensor})
        if not outputs:
            return [], []
        pred = outputs[0]
        if isinstance(pred, (list, tuple)):
            pred = pred[0]
        if pred.ndim == 3 and pred.shape[0] == 1:
            pred = pred[0]
        if pred.ndim > 2:
            pred = pred.reshape(-1, pred.shape[-1])
        if pred.ndim != 2 or pred.shape[1] < 6:
            return [], []

        boxes = []
        for row in pred:
            if row[4] <= 0:
                continue
            scores = row[5:]
            cls_id = int(np.argmax(scores))
            score = float(row[4] * scores[cls_id])
            if score < conf:
                continue
            x1, y1, x2, y2 = self._xyxy_from_xywh(row[:4])
            x1, y1, x2, y2 = self._restore_box((x1, y1, x2, y2), scale, left, top, src_w, src_h)
            if x2 <= x1 or y2 <= y1:
                continue
            cls_id_name = self.names.get(cls_id, str(cls_id))
            boxes.append((cls_id_name, score, (x1, y1, x2, y2), cls_id))

        boxes.sort(key=lambda it: it[1], reverse=True)
        top3 = boxes[:3]
        send_entries = [(n, s) for (n, s, _, _) in top3]
        return send_entries, top3

    def _predict_cv_only(self, frame, conf: float):
        if self._cv_variant == "hog":
            return self._predict_hog(frame, conf)
        if self._cv_variant == "face":
            return self._predict_face(frame, conf)
        if self._cv_variant == "dnn":
            return self._predict_dnn(frame, conf)
        return [], []

    def _predict_hog(self, frame, conf: float):
        rects, weights = self._cv_hog.detectMultiScale(
            frame,
            winStride=(8, 8),
            padding=(8, 8),
            scale=1.05,
            useMeanshiftGrouping=False,
        )
        detections = []
        for i, (x, y, w, h) in enumerate(rects):
            score = 1.0
            if len(weights) > i:
                try:
                    score = float(weights[i][0])
                except Exception:
                    score = 1.0
            score = max(0.0, min(1.0, score))
            if score < conf:
                continue
            detections.append(("person", score, (x, y, x + w, y + h), 0))
        detections.sort(key=lambda it: it[1], reverse=True)
        top3 = detections[:3]
        send_entries = [(n, s) for (n, s, _, _) in top3]
        return send_entries, top3

    def _predict_face(self, frame, conf: float):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._cv_face.detectMultiScale(gray, 1.1, 4)
        detections = []
        for x, y, w, h in faces:
            score = 1.0
            if score < conf:
                continue
            detections.append(("face", score, (x, y, x + w, y + h), 0))
        detections.sort(key=lambda it: it[1], reverse=True)
        top3 = detections[:3]
        send_entries = [(n, s) for (n, s, _, _) in top3]
        return send_entries, top3

    def _predict_dnn(self, frame, conf: float):
        if self._cv_dnn is None:
            return [], []
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(
            frame,
            scalefactor=self._cv_dnn_scale,
            size=self._cv_dnn_input_size,
            mean=self._cv_dnn_mean,
            swapRB=self._cv_dnn_swap_rb,
            crop=False,
        )
        self._cv_dnn.setInput(blob)
        outputs = self._cv_dnn.forward()
        detections = self._parse_dnn_outputs(outputs, conf, w, h)
        detections.sort(key=lambda it: it[1], reverse=True)
        top3 = detections[:3]
        send_entries = [(n, s) for (n, s, _, _) in top3]
        return send_entries, top3

    def _parse_dnn_outputs(self, outputs, conf: float, frame_w: int, frame_h: int):
        detections = []
        out_list = outputs if isinstance(outputs, (list, tuple)) else [outputs]

        for out in out_list:
            arr = np.array(out)
            if arr.size == 0:
                continue
            arr = np.squeeze(arr)
            if arr.ndim == 4:
                if arr.shape[0] == 1:
                    arr = arr[0]
            if arr.ndim == 3:
                if arr.shape[0] == 1:
                    arr = arr[0]
                else:
                    arr = arr.reshape(-1, arr.shape[-1])
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)
            if arr.ndim != 2:
                continue

            for row in arr:
                row = np.asarray(row).astype(float)
                if row.size < 6:
                    continue

                # SSD-like format: [img_id, cls, conf, x1, y1, x2, y2]
                if self._cv_dnn_detection_type in ("auto", "ssd") and row.size >= 7:
                    cls_id = int(row[1])
                    score = float(row[2])
                    if score < conf:
                        continue
                    x1 = int(max(0.0, min(1.0, float(row[3]))) * frame_w)
                    y1 = int(max(0.0, min(1.0, float(row[4]))) * frame_h)
                    x2 = int(max(0.0, min(1.0, float(row[5]))) * frame_w)
                    y2 = int(max(0.0, min(1.0, float(row[6]))) * frame_h)
                    if x2 <= x1 or y2 <= y1:
                        continue
                    name = self.names.get(cls_id, str(cls_id))
                    detections.append((name, score, (x1, y1, x2, y2), cls_id))
                    if self._cv_dnn_detection_type == "ssd":
                        continue

                # YOLO-like format: [x, y, w, h, obj, c0, c1, ...]
                if row.size < 6:
                    continue
                if row.size == 6:
                    obj = float(row[4])
                    scores = row[5:]
                    cls_id = 0
                else:
                    obj = float(row[4])
                    scores = row[5:]
                    cls_id = int(np.argmax(scores)) if scores.size else 0
                if scores.size == 0:
                    continue
                cls_score = float(scores[cls_id]) if cls_id < scores.size else 0.0
                score = obj * cls_score
                if score < conf:
                    continue

                x, y, bw, bh = row[:4]
                x = float(x)
                y = float(y)
                bw = float(bw)
                bh = float(bh)
                if max(x, y, bw, bh) <= 1.0:
                    x1 = int(max(0.0, min(1.0, x - bw / 2.0)) * frame_w)
                    y1 = int(max(0.0, min(1.0, y - bh / 2.0)) * frame_h)
                    x2 = int(max(0.0, min(1.0, x + bw / 2.0)) * frame_w)
                    y2 = int(max(0.0, min(1.0, y + bh / 2.0)) * frame_h)
                else:
                    x1 = int(max(0.0, min(x, frame_w)))
                    y1 = int(max(0.0, min(y, frame_h)))
                    x2 = int(max(0.0, min(x + bw, frame_w)))
                    y2 = int(max(0.0, min(y + bh, frame_h)))
                if x2 <= x1 or y2 <= y1:
                    continue
                name = self.names.get(cls_id, str(cls_id))
                detections.append((name, score, (x1, y1, x2, y2), cls_id))

        return detections


def _draw_box(frame, label: str, conf: float, x1: int, y1: int, x2: int, y2: int):
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    text = f"{label}:{conf:.2f}"
    tsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
    x1t = x1
    y1t = max(0, y1 - 6)
    cv2.rectangle(frame, (x1t, y1t - tsize[1] - 4), (x1t + tsize[0] + 4, y1t), (0, 255, 0), -1)
    cv2.putText(
        frame,
        text,
        (x1t + 2, y1t - 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )


class CommandState:
    def __init__(
        self,
        model_path: str,
        backend: str,
        source: str,
        conf: float,
        send_interval: float,
        fps_limit: float,
        stream: str,
        show: bool,
        model_cfg: Optional[str] = None,
        labels: Optional[str] = None,
        web: bool = False,
        web_quality: int = 80,
    ):
        self.lock = threading.Lock()
        self.running = False
        raw_model_path = str(model_path) if model_path else model_path
        if raw_model_path and raw_model_path.strip().lower() in CV_ONLY_SPECIAL_MODELS:
            self.model_path = raw_model_path
        else:
            self.model_path = _norm_path(raw_model_path)
        self.backend = backend
        self.model_cfg = os.path.expanduser(model_cfg) if model_cfg else None
        self.labels_path = os.path.expanduser(labels) if labels else None
        self.source = source
        self.confidence = max(0.0, min(1.0, conf))
        self.send_interval = max(0.1, float(send_interval))
        self.fps_limit = max(0.0, float(fps_limit))
        self.stream = stream
        self.show = show
        self.web = bool(web)
        self.web_quality = max(10, min(100, int(web_quality)))

    def snapshot(self):
        with self.lock:
            return {
                "running": self.running,
                "model": self.model_path,
                "backend": self.backend,
                "model_cfg": self.model_cfg,
                "source": self.source,
                "confidence": self.confidence,
                "send_interval": self.send_interval,
                "fps_limit": self.fps_limit,
                "stream": self.stream,
                "show": self.show,
                "web": self.web,
                "web_quality": self.web_quality,
            }


def _send_ack(cmd: str, ok: bool, ack_id, message: str = ""):
    payload = {
        "type": "ack",
        "cmd": cmd,
        "ok": bool(ok),
        "ts": iso_now(),
    }
    if ack_id is not None:
        payload["ack_id"] = ack_id
    if message:
        payload["message"] = message
    socket_send(payload)


def _parse_command_payload(raw: str, addr: str = ""):
    raw = (raw or "").strip()
    if not raw:
        return None

    msg = None
    try:
        msg = json.loads(raw)
    except Exception:
        pass

    if isinstance(msg, dict):
        if "name" in msg:
            cmd = str(msg.get("name", "")).strip().lower()
            args = msg.get("args")
            if args is None:
                args = []
            elif isinstance(args, (str, int, float)):
                args = [args]
            elif not isinstance(args, list):
                args = [str(args)]
            args = [str(a) for a in args]
            ack_id = msg.get("ack_id") or msg.get("ack")
            return cmd, args, ack_id
        if "cmd" in msg:
            s = str(msg.get("cmd", "")).strip()
            parts = s.split()
            ack_id = msg.get("ack") or msg.get("id")
            if not parts:
                return None
            return parts[0].lower(), parts[1:], ack_id
        return None

    parts = raw.split()
    if not parts:
        return None
    return parts[0].lower(), parts[1:], None


def command_thread(stop_event: threading.Event, state: CommandState):
    print(f"[CMD] listening on {SOCKET_RX}")
    buffer = b""
    last_error = 0.0
    while not stop_event.is_set():
        s = None
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(4.0)
            s.connect(SOCKET_RX)

            while not stop_event.is_set():
                rlist, _, _ = select.select([s], [], [], 1.0)
                if not rlist:
                    continue
                chunk = s.recv(8192)
                if not chunk:
                    break
                buffer += chunk

                while b"\n" in buffer:
                    raw, buffer = buffer.split(b"\n", 1)
                    text = raw.decode("utf-8", errors="ignore").strip()
                    if not text:
                        continue
                    parsed = _parse_command_payload(text)
                    if not parsed:
                        continue
                    cmd, args, ack_id = parsed
                    ok = True
                    msg = ""

                    if cmd == "start":
                        with state.lock:
                            state.running = True
                        msg = "inference started"

                    elif cmd in ("stop", "pause"):
                        with state.lock:
                            state.running = False
                        msg = "inference stopped"

                    elif cmd == "resume":
                        with state.lock:
                            state.running = True
                        msg = "inference resumed"

                    elif cmd == "set_model":
                        if not args:
                            ok = False
                            msg = "set_model requires a model path"
                        else:
                            new_model = os.path.expanduser(args[0])
                            is_special_model = new_model.strip().lower() in CV_ONLY_SPECIAL_MODELS
                            new_model_cfg = os.path.expanduser(args[1]) if len(args) > 1 else None
                            new_labels = os.path.expanduser(args[2]) if len(args) > 2 else None
                            if (not is_special_model) and (not os.path.exists(new_model)):
                                ok = False
                                msg = f"model not found: {new_model}"
                            else:
                                ext = os.path.splitext(new_model)[1].lower()
                                with state.lock:
                                    # Keep explicit backend unless running in auto mode.
                                    if state.backend == "auto":
                                        if is_special_model:
                                            state.backend = "cv_only"
                                        elif ext == ".onnx":
                                            state.backend = "onnx"
                                        elif ext in (".pt", ".pth"):
                                            state.backend = "torch"
                                        elif ext in (".xml", ".caffemodel", ".prototxt", ".pb", ".onnx"):
                                            state.backend = "cv_only"
                                    if is_special_model:
                                        state.model_path = new_model
                                    else:
                                        state.model_path = os.path.abspath(new_model)
                                    state.model_cfg = new_model_cfg
                                    if new_labels is not None:
                                        state.labels_path = new_labels
                                msg = f"model set to {state.model_path}"

                    elif cmd == "reload":
                        msg = "model reload requested"

                    elif cmd == "set_source":
                        if not args:
                            ok = False
                            msg = "set_source requires a value"
                        else:
                            with state.lock:
                                state.source = str(args[0])
                            msg = f"source set to {state.source}"

                    elif cmd == "set_conf":
                        if not args:
                            ok = False
                            msg = "set_conf requires a float"
                        else:
                            try:
                                v = float(args[0])
                                with state.lock:
                                    state.confidence = max(0.0, min(1.0, v))
                                msg = f"conf set to {state.confidence:.3f}"
                            except Exception:
                                ok = False
                                msg = f"invalid confidence: {args[0]}"

                    elif cmd in ("send_interval", "set_interval"):
                        if not args:
                            ok = False
                            msg = "send_interval requires seconds"
                        else:
                            try:
                                v = float(args[0])
                                if v < 0.1:
                                    ok = False
                                    msg = "send_interval must be >= 0.1"
                                else:
                                    with state.lock:
                                        state.send_interval = v
                                    msg = f"send_interval set to {v}"
                            except Exception:
                                ok = False
                                msg = f"invalid send interval: {args[0]}"

                    elif cmd == "set_fps":
                        if not args:
                            ok = False
                            msg = "set_fps requires seconds"
                        else:
                            try:
                                v = float(args[0])
                                if v < 0:
                                    ok = False
                                    msg = "fps_limit must be >= 0"
                                else:
                                    with state.lock:
                                        state.fps_limit = v
                                    msg = f"fps_limit set to {v}"
                            except Exception:
                                ok = False
                                msg = f"invalid fps_limit: {args[0]}"

                    elif cmd == "show":
                        with state.lock:
                            state.show = True
                        msg = "show enabled"

                    elif cmd == "hide":
                        with state.lock:
                            state.show = False
                        msg = "show disabled"

                    elif cmd == "status":
                        snap = state.snapshot()
                        snap["type"] = "status"
                        snap["ts"] = iso_now()
                        if ack_id is not None:
                            snap["ack_id"] = ack_id
                        socket_send(snap)
                        continue

                    elif cmd == "ping":
                        socket_send({"type": "pong", "ts": iso_now(), "id": ack_id or (args[0] if args else "pong")})
                        continue

                    elif cmd == "get_status":
                        snap = state.snapshot()
                        snap["type"] = "status"
                        snap["ts"] = iso_now()
                        if ack_id is not None:
                            snap["ack_id"] = ack_id
                        socket_send(snap)
                        continue

                    else:
                        ok = False
                        msg = f"unknown command: {cmd}"

                    _send_ack(cmd, ok, ack_id=ack_id, message=msg)

        except Exception as e:
            now = time.time()
            if now - last_error > 1.5:
                print(f"[CMD] socket error: {e}")
                last_error = now
            time.sleep(1.0)
        finally:
            if s:
                try:
                    s.close()
                except Exception:
                    pass
            time.sleep(0.2)


def _draw_and_send(frame, detections, model_name: str, latency_ms: float, frame_ix: int, source: str, state: CommandState):
    names = [d[0] for d in detections]
    confs = [round(d[1], 4) for d in detections]
    now = time.time()
    return {
        "timestamp": int(now),
        "ts_utc": iso_now(),
        "type": "vision_inference",
        "stream": source,
        "model": model_name,
        "frame_index": frame_ix,
        "infer_ms": round(float(latency_ms), 2),
        "detections": len([n for n in names if n]),
        "object1": names[0] if len(names) > 0 else "",
        "confidence1": confs[0] if len(confs) > 0 else 0.0,
        "object2": names[1] if len(names) > 1 else "",
        "confidence2": confs[1] if len(confs) > 1 else 0.0,
        "object3": names[2] if len(names) > 2 else "",
        "confidence3": confs[2] if len(confs) > 2 else 0.0,
    }


def open_capture(source):
    cap = cv2.VideoCapture(source)
    return cap


def run_inference(state: CommandState, stop_event: threading.Event):
    print("[INF] inference thread starting")
    model_mgr = ModelManager(state.model_path, backend=state.backend, labels=state.labels_path)
    cap = None
    active_source = None
    is_image = False
    frame_idx = 0
    last_send = 0.0
    last_frame_time = 0.0
    window_name = "iotc_vision"

    def ensure_capture(src):
        nonlocal cap, active_source, is_image, frame_idx
        source_norm = src
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
            cap = None
        active_source = source_norm
        frame_idx = 0

        is_image = isinstance(source_norm, str) and _is_image_file(source_norm)
        if is_image:
            return
        cap = open_capture(source_norm)

    while not stop_event.is_set():
        with state.lock:
            running = state.running
            source = state.source
            conf = state.confidence
            send_interval = state.send_interval
            fps_limit = state.fps_limit
            show = state.show
            web = state.web
            web_quality = state.web_quality
            model_path = state.model_path
            model_cfg = state.model_cfg
            stream = state.stream
            backend = state.backend
            labels_path = state.labels_path

        try:
            if not running:
                time.sleep(0.2)
                if cap is not None:
                    try:
                        cap.release()
                    except Exception:
                        pass
                    cap = None
                active_source = None
                continue

            if source != active_source or cap is None and not is_image:
                ensure_capture(_coerce_source(source))

            model, loaded_backend = model_mgr.ensure_model(
                model_path,
                requested_backend=backend,
                model_cfg=model_cfg,
                labels_path=labels_path,
            )
            names = model_mgr.names

            frame = None
            if is_image:
                frame = cv2.imread(active_source)
                if frame is None:
                    print(f"[INF] cannot read image source: {active_source}")
                    time.sleep(1.0)
                    continue
            else:
                if cap is None or not cap.isOpened():
                    cap = open_capture(_coerce_source(source))
                    if cap is None or not cap.isOpened():
                        print(f"[INF] cannot open video source: {source}")
                        time.sleep(1.0)
                        continue
                ok, frame = cap.read()
                if not ok or frame is None:
                    print(f"[INF] no frame from source: {source}, retrying")
                    time.sleep(0.5)
                    continue

            now = time.time()
            if fps_limit and fps_limit > 0 and (now - last_frame_time) < (1.0 / fps_limit):
                time.sleep(max(0.0, (1.0 / fps_limit) - (now - last_frame_time)))
            last_frame_time = time.time()

            t0 = time.perf_counter()
            det, overlay = model_mgr.predict(frame, conf=conf)
            infer_ms = (time.perf_counter() - t0) * 1000.0
            if not isinstance(det, list):
                det = []

            frame_idx += 1
            if state.running and (time.time() - last_send) >= send_interval:
                payload = _draw_and_send(frame, det, os.path.basename(model_path), infer_ms, frame_idx, stream, state)
                payload["status"] = "running"
                socket_send(payload)
                last_send = time.time()

            disp = None
            if show or web:
                disp = _render_overlay_frame(frame, overlay, loaded_backend, stream, model_path, infer_ms)

            if web and disp is not None:
                _set_web_frame(disp, jpeg_quality=web_quality)

            if show and disp is not None:
                cv2.imshow(window_name, disp)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("x")):
                    with state.lock:
                        state.running = False
        except Exception as e:
            print(f"[INF] loop error: {e}")
            time.sleep(0.5)
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
                cap = None
            active_source = None
            continue


def main():
    ap = argparse.ArgumentParser(description="Simple vision inference + IoTConnect socket bridge")
    ap.add_argument("--model", default="yolov8n.pt", help="YOLO .pt model path")
    ap.add_argument("--backend", default="auto", choices=["auto", "torch", "onnx", "cv_only"], help="Model runtime backend")
    ap.add_argument("--model-cfg", default=None, help="Model metadata/config for cv_only and DNN backends")
    ap.add_argument("--labels", default=None, help="Class labels for cv_only/onnx inference")
    ap.add_argument("--source", default="0", help="Camera index, video path, RTSP URL or image file")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--send-interval", type=float, default=3.0, help="seconds")
    ap.add_argument("--fps-limit", type=float, default=0.0, help="0=unlimited")
    ap.add_argument("--stream", default="vision.objects")
    ap.add_argument("--iotc-sock", default=os.environ.get("IOTC_SOCK", SOCKET_TX))
    ap.add_argument("--iotc-cmd-sock", default=os.environ.get("IOTC_CMD_SOCK", SOCKET_RX))
    ap.add_argument("--show", action="store_true", help="Open preview window (HDMI/display)")
    ap.add_argument("--web", action="store_true", help="Serve overlay stream via HTTP on / and /stream.mjpg")
    ap.add_argument("--web-host", default="0.0.0.0", help="Web stream bind host")
    ap.add_argument("--web-port", type=int, default=8080, help="Web stream bind port")
    ap.add_argument("--web-quality", type=int, default=80, help="Web stream JPEG quality (10-100)")
    ap.add_argument("--auto-start", action="store_true", help="Start immediately without requiring a start command")
    args = ap.parse_args()

    _require_cv2()

    globals()["SOCKET_TX"] = args.iotc_sock
    globals()["SOCKET_RX"] = args.iotc_cmd_sock

    if not os.path.exists(SOCKET_TX):
        print(f"[WARN] TX socket not present yet: {SOCKET_TX}")
    if not os.path.exists(SOCKET_RX):
        print(f"[WARN] CMD socket not present yet: {SOCKET_RX}")

    if args.show and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        print("[WARN] --show requested but no display session found; disabling local preview")
        args.show = False

    if args.show:
        cv2.namedWindow("iotc_vision", cv2.WINDOW_NORMAL)

    web_server = None
    if args.web:
        try:
            web_server = start_web_stream_server(args.web_host, args.web_port)
        except Exception as e:
            print(f"[ERR] failed to start web stream server: {e}")
            raise SystemExit(5)

    state = CommandState(
        model_path=args.model,
        backend=args.backend,
        source=args.source,
        conf=args.conf,
        send_interval=args.send_interval,
        fps_limit=args.fps_limit,
        stream=args.stream,
        show=args.show,
        model_cfg=args.model_cfg,
        labels=args.labels,
        web=args.web,
        web_quality=args.web_quality,
    )
    if args.auto_start:
        state.running = True

    stop_event = threading.Event()
    t_cmd = threading.Thread(target=command_thread, args=(stop_event, state), daemon=False)
    t_inf = threading.Thread(target=run_inference, args=(state, stop_event), daemon=False)
    t_cmd.start()
    t_inf.start()

    if args.auto_start:
        print("[INFO] auto-start enabled")
    else:
        print("[INFO] waiting for start command on RX socket")

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        stop_event.set()
        with state.lock:
            state.running = False
        # Join worker threads to avoid abrupt interpreter teardown in OpenCV/C++ code.
        try:
            t_cmd.join(timeout=5.0)
        except Exception:
            pass
        try:
            t_inf.join(timeout=5.0)
        except Exception:
            pass
        if web_server is not None:
            try:
                web_server.shutdown()
                web_server.server_close()
            except Exception:
                pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass


if __name__ == "__main__":
    main()
