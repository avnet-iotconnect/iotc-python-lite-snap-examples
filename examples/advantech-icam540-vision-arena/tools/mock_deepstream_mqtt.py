#!/usr/bin/env python3
"""
Publish synthetic DeepStream-schema messages so the Vision Arena agent can be
exercised on a desk without the camera or DeepStream (run the agent with
--no-deepstream). Simulated people walk across the counting line, linger in
the booth zone and leave; extra "streams" carry random traffic.

Usage:
  ./tools/mock_deepstream_mqtt.py [--host localhost] [--topic icam540/arena] [--streams 4] [--format pipe|dict]
"""

import argparse
import json
import math
import random
import time
from datetime import datetime, timezone

W, H = 1280, 720


class Walker:
    def __init__(self, tid, t0):
        self.tid = tid
        self.t0 = t0
        self.enter_from_top = random.random() < 0.7
        self.x = random.uniform(0.2, 0.8)
        self.linger = random.uniform(4, 14)
        self.speed = random.uniform(0.08, 0.15)  # normalised units per second

    def position(self, t):
        """Return (x, y_foot) normalised, or None when the walker is gone."""
        dt = t - self.t0
        walk_in = 0.45 / self.speed
        if self.enter_from_top:
            if dt < walk_in:
                return self.x, 0.30 + self.speed * dt
            if dt < walk_in + self.linger:
                return self.x + 0.02 * math.sin(dt), 0.75 + 0.03 * math.cos(dt / 2)
            back = dt - walk_in - self.linger
            y = 0.75 - self.speed * back
            return (self.x, y) if y > 0.25 else None
        else:
            if dt < walk_in:
                return self.x, 0.95 - self.speed * dt
            if dt < walk_in + self.linger:
                return self.x, 0.50
            back = dt - walk_in - self.linger
            y = 0.50 + self.speed * back
            return (self.x, y) if y < 0.98 else None


def bbox_from_foot(x, y):
    bw, bh = 0.08, 0.30
    left = max(0.0, x - bw / 2) * W
    right = min(1.0, x + bw / 2) * W
    bottom = y * H
    top = max(0.0, y - bh) * H
    return left, top, right, bottom


def build_message(source, objs, frame, fmt):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    if fmt == "pipe":
        return {
            "version": "4.0",
            "id": str(frame),
            "@timestamp": ts,
            "sensorId": f"ICAM540_SRC_{source}",
            "objects": [f"{tid}|{l:.1f}|{t:.1f}|{r:.1f}|{b:.1f}|{label}" for tid, (l, t, r, b), label in objs],
        }
    return {
        "version": "4.0",
        "id": str(frame),
        "@timestamp": ts,
        "sensorId": f"ICAM540_SRC_{source}",
        "objects": [
            {
                "id": str(tid),
                label.lower(): {"confidence": 0.9},
                "bbox": {"topleftx": int(l), "toplefty": int(t), "bottomrightx": int(r), "bottomrighty": int(b)},
            }
            for tid, (l, t, r, b), label in objs
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--topic", default="icam540/arena")
    ap.add_argument("--streams", type=int, default=1)
    ap.add_argument("--rate", type=float, default=10.0, help="messages per second per stream")
    ap.add_argument("--format", choices=["pipe", "dict"], default="pipe")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    import paho.mqtt.client as mqtt

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except Exception:
        client = mqtt.Client()
    client.connect(args.host, args.port, 60)
    client.loop_start()

    walkers = []
    next_tid = 1
    next_spawn = time.time()
    frame = 0
    period = 1.0 / max(0.5, args.rate)
    print(f"[mock] publishing to {args.host}:{args.port} topic={args.topic} streams={args.streams} format={args.format}")
    try:
        while True:
            now = time.time()
            if now >= next_spawn and len(walkers) < 5:
                walkers.append(Walker(next_tid, now))
                next_tid += 1
                next_spawn = now + random.uniform(2, 7)
            objs = []
            alive = []
            for wk in walkers:
                pos = wk.position(now)
                if pos is None:
                    continue
                alive.append(wk)
                objs.append((wk.tid, bbox_from_foot(*pos), "Person"))
            walkers = alive
            client.publish(args.topic, json.dumps(build_message(0, objs, frame, args.format)))
            for src in range(1, args.streams):
                extra = []
                for k in range(random.randint(0, 6)):
                    label = random.choice(["Person", "Person", "Car", "Bicycle"])
                    extra.append((1000 * src + k, bbox_from_foot(random.random(), random.uniform(0.3, 1.0)), label))
                client.publish(args.topic, json.dumps(build_message(src, extra, frame, args.format)))
            frame += 3
            time.sleep(period)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()


if __name__ == "__main__":
    main()
