#!/usr/bin/env python3
import os, json, socket, time

CANDIDATE_SOCKETS = [
    os.environ.get("IOTC_SOCKET"),
    "/var/snap/iotconnect/common/iotc.sock",
    "/var/snap/iotconnect/common/iotconnect.sock",
]

def find_socket():
    for p in CANDIDATE_SOCKETS:
        if p and os.path.exists(p):
            return p
    return None

def main():
    payload = {
        "ts": int(time.time() * 1000),
        "did": "demo-device",
        "telemetry": {"temp_c": 24.6, "humidity": 45.2},
        "meta": {"example": "hello-telemetry"}
    }

    sock_path = find_socket()
    if not sock_path:
        print("IoTConnect socket not found. Set IOTC_SOCKET=/var/snap/iotconnect/common/iotc.sock or start with 'iotconnect.socket-run'.")
        print("Payload that would have been sent:\n", json.dumps(payload))
        return

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(sock_path)
            s.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        print(f"Sent telemetry to {sock_path}: {payload}")
    except Exception as e:
        print(f"Failed to send telemetry: {e}\nPayload: {json.dumps(payload)}")

if __name__ == "__main__":
    main()