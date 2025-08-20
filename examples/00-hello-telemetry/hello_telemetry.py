#!/usr/bin/env python3
import os, json, socket, time
CANDS=[os.environ.get("IOTC_SOCKET"),
       "/var/snap/iotconnect/common/iotc.sock",
       "/var/snap/iotconnect/common/iotconnect.sock"]
sock=next((p for p in CANDS if p and os.path.exists(p)), None)
payload={"ts":int(time.time()*1000),"did":"demo-device","telemetry":{"temp_c":24.6,"humidity":45.2},"meta":{"example":"hello-telemetry"}}
if not sock:
    print("Socket not found. Set IOTC_SOCKET or run `iotconnect.socket-run`.\nPayload:", json.dumps(payload)); exit(0)
s=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect(sock); s.sendall((json.dumps(payload)+"\n").encode()); s.close()
print("Sent to", sock)