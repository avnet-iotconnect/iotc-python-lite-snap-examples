
#!/usr/bin/env python3
import os, socket, sys
p=os.environ.get("IOTC_CMD_SOCK", f"/home/{os.environ.get('USER','')}/snap/iotconnect/common/iotc_cmd.sock")
print("Connecting to:", p)
s=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect(p)
try:
    while True:
        buf = s.recv(4096)
        if not buf: break
        sys.stdout.write(buf.decode(errors="replace"))
        sys.stdout.flush()
finally:
    s.close()
