#!/usr/bin/env python3
"""
iotc_yolo_simple.py

Minimal YOLOv8 → IoTConnect telemetry.
NO domain logic. NO left/right. NO fruit assumptions.

Telemetry sent:
- v
- type
- stream
- ts
- object1, confidence1
- object2, confidence2
- object3, confidence3
"""

import argparse
import json
import socket
import time
from datetime import datetime, timezone

import cv2
from ultralytics import YOLO


def iso_now():
    return datetime.now(timezone.utc).isoformat()


class IOTCSocket:
    def __init__(self, path):
        self.path = path
        self.sock = None
        self._warned = False

    def send(self, payload):
        if not self.path:
            return
        try:
            if self.sock is None:
                self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.sock.connect(self.path)
            self.sock.sendall((json.dumps(payload) + '\n').encode())
        except Exception:
            if not self._warned:
                print(f"[IOTC] send failed to {self.path}; will retry on next send.")
                self._warned = True
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="yolov8n.pt")
    ap.add_argument("--source", default="0")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--iotc-sock", required=True)
    ap.add_argument("--iotc-stream", default="vision.objects")
    ap.add_argument("--send-interval", type=float, default=3.0)
    ap.add_argument("--fps-limit", type=float, default=18.0)
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    src = int(args.source) if args.source.isdigit() else args.source
    model = YOLO(args.model)
    names = model.model.names

    iotc = IOTCSocket(args.iotc_sock)
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise SystemExit(f"Cannot open source: {src}")

    last_send = 0.0
    frame_delay = 1.0 / max(1.0, args.fps_limit)

    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.1)
            continue

        results = model(frame, conf=args.conf, verbose=False)
        r0 = results[0]

        dets = []
        boxes = getattr(r0, "boxes", None)
        if boxes is not None:
            for b in boxes:
                cls_id = int(b.cls[0])
                cls_name = names.get(cls_id, str(cls_id))
                conf = float(b.conf[0])
                dets.append((cls_name, conf))

        dets.sort(key=lambda x: x[1], reverse=True)
        top = dets[:3]
        while len(top) < 3:
            top.append(("", 0.0))

        payload = {
            "v": "1.0",
            "type": "yolo_objects",
            "stream": args.iotc_stream,
            "ts": iso_now(),
            "object1": top[0][0], "confidence1": round(top[0][1], 4),
            "object2": top[1][0], "confidence2": round(top[1][1], 4),
            "object3": top[2][0], "confidence3": round(top[2][1], 4),
        }

        if args.show:
            cv2.imshow("YOLO", r0.plot())
            if cv2.waitKey(1) & 0xFF == 27:
                break

        now = time.time()
        if now - last_send >= args.send_interval:
            last_send = now
            iotc.send(payload)

        time.sleep(frame_delay)

    cap.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass


if __name__ == "__main__":
    main()
