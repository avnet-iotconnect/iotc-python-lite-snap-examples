#!/usr/bin/env python3
"""
Subscribe to DeepStream MQTT messages and forward them to IoTConnect snap socket.
"""

import argparse
import json
import os
import socket
import sys
import threading
import time


def pick_socket(candidates):
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None


def send_json_line(sock_path, payload):
    data = (json.dumps(payload) + "\n").encode()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(sock_path)
        s.sendall(data)


def check_broker_reachable(host, port, timeout=2.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def load_labels(path):
    labels = []
    if not path:
        return labels
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    labels.append(line)
    except Exception:
        pass
    return labels


def extract_objects(ds_msg, labels):
    objects = []
    if not isinstance(ds_msg, dict):
        return objects

    if isinstance(ds_msg.get("objects"), list):
        items = ds_msg.get("objects") or []
    elif "object" in ds_msg:
        items = [ds_msg.get("object")]
    else:
        return objects

    meta_fields = {
        "id",
        "speed",
        "direction",
        "orientation",
        "bbox",
        "bbox2d",
        "rect",
        "location",
        "coordinate",
        "trackingId",
        "classId",
        "class_id",
        "classid",
        "confidence",
    }

    for obj in items:
        if not isinstance(obj, dict):
            continue
        label = None
        conf = None

        for k, v in obj.items():
            if k in meta_fields:
                continue
            if isinstance(v, dict):
                label = k
                if isinstance(v.get("confidence"), (int, float)):
                    conf = v.get("confidence")
                elif isinstance(v.get("probability"), (int, float)):
                    conf = v.get("probability")
                break

        if label is None:
            label = obj.get("label") or obj.get("class") or obj.get("class_name")

        if label is None:
            class_id = obj.get("classId") or obj.get("class_id") or obj.get("classid")
            try:
                class_id = int(class_id)
                if 0 <= class_id < len(labels):
                    label = labels[class_id]
            except Exception:
                pass

        if conf is None and isinstance(obj.get("confidence"), (int, float)):
            conf = obj.get("confidence")

        bbox = obj.get("bbox") or obj.get("bbox2d") or obj.get("rect")

        objects.append(
            {
                "label": label or "unknown",
                "confidence": conf,
                "bbox": bbox,
            }
        )

    return objects


def main():
    ap = argparse.ArgumentParser(description="MQTT -> IoTConnect socket forwarder")
    ap.add_argument("--host", default=os.environ.get("MQTT_HOST", "localhost"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("MQTT_PORT", "1883")))
    ap.add_argument("--topic", default=os.environ.get("MQTT_TOPIC", "icam540/ds"))
    ap.add_argument("--did", default=os.environ.get("IOTC_DID", "icam540-snap"))
    ap.add_argument("--iotc-sock", default=os.environ.get("IOTC_SOCKET", ""))
    ap.add_argument("--min-interval", type=float, default=float(os.environ.get("IOTC_MIN_INTERVAL", "4")))
    ap.add_argument(
        "--labels",
        default=os.environ.get(
            "DS_LABELS",
            "/opt/nvidia/deepstream/deepstream/samples/models/Primary_Detector/labels.txt",
        ),
        help="Labels file used to map class_id to name when label is missing",
    )
    ap.add_argument(
        "--summary-only",
        action="store_true",
        default=os.environ.get("IOTC_SUMMARY_ONLY", "").lower() in ("1", "true", "yes"),
        help="Send only summary (count/labels/bboxes) instead of full DeepStream payload",
    )
    args = ap.parse_args()

    try:
        import paho.mqtt.client as mqtt  # type: ignore
    except Exception:
        print("Missing dependency: paho-mqtt. Install with: pip install paho-mqtt", file=sys.stderr)
        sys.exit(1)

    user = os.environ.get("USER", "")
    sock_candidates = [
        args.iotc_sock,
        f"/home/{user}/snap/iotconnect/common/iotc.sock" if user else "",
        "/var/snap/iotconnect/common/iotc.sock",
    ]
    tx_sock = pick_socket(sock_candidates)
    if not tx_sock:
        print("Telemetry socket not found. Set IOTC_SOCKET or start the snap socket service.")
        sys.exit(1)

    if not check_broker_reachable(args.host, args.port):
        print(
            f"MQTT broker not reachable at {args.host}:{args.port}. "
            "Start a broker (e.g., mosquitto) or change --host/--port.",
            file=sys.stderr,
        )
        sys.exit(2)

    labels = load_labels(args.labels)
    min_interval = max(0.1, float(args.min_interval))
    summary_only = bool(args.summary_only)
    state = {
        "last_sent": 0.0,
        "pending": None,  # (topic, parsed, summary)
        "timer": None,
    }
    state_lock = threading.Lock()

    def send_to_iotc(topic, parsed, summary):
        telemetry = {"summary": summary, "topic": topic}
        if not summary_only:
            telemetry["deepstream"] = parsed
        payload = {
            "ts": int(time.time() * 1000),
            "did": args.did,
            "telemetry": telemetry,
        }
        send_json_line(tx_sock, payload)
        print(f"[IOTC] forwarded message from {topic}")

    def flush_pending():
        with state_lock:
            state["timer"] = None
            pending = state["pending"]
            state["pending"] = None
        if not pending:
            return
        topic, parsed, summary = pending
        try:
            send_to_iotc(topic, parsed, summary)
        except Exception as e:
            print(f"[IOTC] send failed: {e}")
            return
        with state_lock:
            state["last_sent"] = time.time()

    def on_connect(client, userdata, flags, rc, properties=None):
        print(f"[MQTT] connected rc={rc}, subscribing to {args.topic}")
        client.subscribe(args.topic)

    def on_message(client, userdata, msg):
        raw = msg.payload.decode(errors="ignore").strip()
        if not raw:
            return
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}

        summary_objects = extract_objects(parsed, labels)
        summary = {
            "count": len(summary_objects),
            "labels": sorted({o.get("label") for o in summary_objects if o.get("label")}),
            "objects": summary_objects,
        }

        now = time.time()
        with state_lock:
            if now - state["last_sent"] >= min_interval:
                state["last_sent"] = now
                send_now = True
            else:
                state["pending"] = (msg.topic, parsed, summary)
                if state["timer"] is None:
                    delay = max(0.01, min_interval - (now - state["last_sent"]))
                    t = threading.Timer(delay, flush_pending)
                    t.daemon = True
                    state["timer"] = t
                    t.start()
                send_now = False

        if send_now:
            try:
                send_to_iotc(msg.topic, parsed, summary)
            except Exception as e:
                print(f"[IOTC] send failed: {e}")

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except Exception:
        client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.host, args.port, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
