
#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, sys, time, json, math, socket, errno, threading
from collections import defaultdict
from datetime import datetime, timezone
import cv2
from ultralytics import YOLO

def now_iso(): return datetime.now(timezone.utc).isoformat()
def line_side(p,a,b):
    (x,y)=p;(x1,y1)=a;(x2,y2)=b
    return (x-x1)*(y2-y1)-(y-y1)*(x2-x1)
def parse_line(s):
    if not s: return None
    x1,y1,x2,y2=map(int,s.split(",")); return (x1,y1),(x2,y2)

class ResilientUnixClient:
    def __init__(self, path, name="IOTC", reconnect_delay=1.0, readable=False):
        self.path=path; self.name=name; self.sock=None; self.lock=threading.Lock()
        self.reconnect_delay=reconnect_delay; self.readable=readable; self.buf=b""; self.last_log=0.0
    def _connect(self):
        if not self.path: return False
        try:
            s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.connect(self.path); s.setblocking(True)
            with self.lock: self.sock=s
            return True
        except Exception as e:
            now=time.time()
            if now-self.last_log>2.0:
                print(f"[{self.name}] connect failed: {e}", file=sys.stderr); self.last_log=now
            with self.lock: self.sock=None
            return False
    def send_line(self, line:str):
        if not self.path: return
        data=(line+"\n").encode()
        with self.lock: s=self.sock
        if s is None and not self._connect(): return
        try:
            with self.lock:
                assert self.sock is not None
                self.sock.sendall(data); return
        except OSError as e:
            if e.errno in (errno.EPIPE, errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN):
                with self.lock:
                    try: self.sock and self.sock.close()
                    except: pass
                    self.sock=None
                time.sleep(self.reconnect_delay)
                if self._connect():
                    try:
                        with self.lock: self.sock.sendall(data); return
                    except Exception as e2:
                        print(f"[{self.name}] send retry failed: {e2}", file=sys.stderr)
                        with self.lock:
                            try: self.sock and self.sock.close()
                            except: pass
                            self.sock=None
            else:
                print(f"[{self.name}] send error: {e}", file=sys.stderr)
    def recv_lines(self):
        printed=False
        while True:
            with self.lock: s=self.sock
            if s is None and not self._connect():
                time.sleep(self.reconnect_delay); continue
            if not printed:
                print(f"[{self.name}] recv_lines connected to {self.path}"); printed=True
            try:
                with self.lock:
                    s=self.sock
                    if s is None: printed=False; continue
                    chunk=s.recv(4096)
                if not chunk:
                    with self.lock:
                        try: self.sock and self.sock.close()
                        except: pass
                        self.sock=None
                    printed=False; time.sleep(self.reconnect_delay); continue
                self.buf+=chunk
                while b"\n" in self.buf:
                    line,self.buf=self.buf.split(b"\n",1)
                    yield line.decode("utf-8","replace")
            except OSError as e:
                with self.lock:
                    try: self.sock and self.sock.close()
                    except: pass
                    self.sock=None
                printed=False; time.sleep(self.reconnect_delay)
    def close(self):
        with self.lock:
            try: self.sock and self.sock.close()
            except: pass
            self.sock=None

class CommandState:
    def __init__(self, send_interval, classes, line, area_side, stream):
        self.lock=threading.Lock()
        self.send_interval=max(0.5,float(send_interval))
        self.classes_raw=classes or ""
        self.classes=[c.strip().lower() for c in self.classes_raw.split(",") if c.strip()]
        self.line=line
        self.area_side="left" if area_side not in ("left","right") else area_side
        self.stream=stream
        self.paused=False
    def set_field(self, path, value):
        with self.lock:
            if path=="send_interval":
                self.send_interval=max(0.5,float(value))
            elif path=="classes":
                self.classes_raw=value or ""
                self.classes=[c.strip().lower() for c in self.classes_raw.split(",") if c.strip()]
            elif path=="line":
                self.line=parse_line(value) if value else None
            elif path=="area_side":
                self.area_side="left" if str(value).lower()!="right" else "right"
            elif path=="stream":
                self.stream=str(value)
            else:
                return False
        return True
    def snap(self):
        with self.lock:
            return dict(send_interval=self.send_interval, classes=self.classes_raw,
                        line=None if self.line is None else f"{self.line[0][0]},{self.line[0][1]},{self.line[1][0]},{self.line[1][1]}",
                        area_side=self.area_side, stream=self.stream, paused=self.paused)

def command_thread(cmd_client:ResilientUnixClient, state:CommandState, telemetry_client:ResilientUnixClient):
    print(f"[CMD] thread starting; waiting on {cmd_client.path}")
    DIRECT={"send_interval","line","area_side","stream","classes"}
    def reply(obj):
        try: cmd_client.send_line(json.dumps(obj))
        except: pass
    while True:
        try:
            for raw in cmd_client.recv_lines():
                raw=(raw or "").strip()
                if not raw: continue
                print(f"[CMD] recv: {raw[:200]}")
                msg=None
                try: msg=json.loads(raw)
                except: pass
                ack_id=None
                if isinstance(msg,dict) and "name" in msg:  # {"name":"pause","args":[...],"ack_id":...}
                    cmd=str(msg["name"]).lower()
                    args=[str(x) for x in (msg.get("args") or [])]
                    ack_id=msg.get("ack_id") or msg.get("ack")
                elif isinstance(msg,dict) and "cmd" in msg:
                    tokens=str(msg.get("cmd","")).strip().split()
                    cmd=tokens[0].lower() if tokens else ""
                    args=tokens[1:]
                    ack_id=msg.get("ack") or msg.get("id")
                else:
                    tokens=raw.split()
                    cmd=tokens[0].lower() if tokens else ""
                    args=tokens[1:] if tokens else []
                if not cmd: continue
                if cmd=="ping":
                    reply({"type":"pong","id":ack_id or (args[0] if args else None),"ts":now_iso()}); continue
                if cmd=="pause":
                    with state.lock: state.paused=True
                    print("[CMD] action: PAUSE"); reply({"type":"ack","cmd":"pause","ok":True,"ack_id":ack_id,"ts":now_iso()}); continue
                if cmd=="resume":
                    with state.lock: state.paused=False
                    print("[CMD] action: RESUME"); reply({"type":"ack","cmd":"resume","ok":True,"ack_id":ack_id,"ts":now_iso()}); continue
                if cmd=="get_status":
                    print("[CMD] action: GET_STATUS"); reply({"type":"status", **state.snap(), "ack_id":ack_id,"ts":now_iso()}); continue
                if cmd=="set":
                    ok=False
                    if isinstance(msg,dict) and "path" in msg:
                        ok=state.set_field(str(msg.get("path","")), msg.get("value"))
                    else:
                        if len(args)>=2:
                            ok=state.set_field(args[0], " ".join(args[1:]))
                    print(f"[CMD] action: SET -> ok={ok}"); reply({"type":"ack","cmd":"set","ok":bool(ok),"ack_id":ack_id,"ts":now_iso()}); continue
                if cmd in DIRECT:
                    ok=state.set_field(cmd, " ".join(args) if args else None)
                    print(f"[CMD] action: DIRECT_SET {cmd} -> ok={ok}"); reply({"type":"ack","cmd":"set","path":cmd,"ok":bool(ok),"ack_id":ack_id,"ts":now_iso()}); continue
                print(f"[CMD] action: UNKNOWN '{cmd}'"); reply({"type":"error","error":f"unknown cmd '{cmd}'","ack_id":ack_id,"ts":now_iso()})
        except Exception as e:
            print(f"[CMD] thread error: {e}", file=sys.stderr); time.sleep(1.0); continue

def main():
    ap=argparse.ArgumentParser(description="Vision Smart-Zone Fruit Counts → /IOTCONNECT (with CMD)")
    ap.add_argument("--model", default="yolov8n.pt")
    ap.add_argument("--source", default="0")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--classes", type=str, default="")
    ap.add_argument("--fps-limit", type=float, default=0.0)
    ap.add_argument("--no-draw", action="store_true")
    ap.add_argument("--line", type=str, help="x1,y1,x2,y2")
    ap.add_argument("--area-side", choices=["left","right"], default="left")
    ap.add_argument("--iotc-sock", type=str, default=os.environ.get("IOTC_SOCK",""))
    ap.add_argument("--iotc-cmd-sock", type=str, default=os.environ.get("IOTC_CMD_SOCK",""))
    ap.add_argument("--iotc-stream", type=str, default="vision.fruit")
    ap.add_argument("--log-jsonl", type=str)
    ap.add_argument("--send-interval", type=float, default=4.0)
    args=ap.parse_args()

    print(f"[CMD] path: {args.iotc_cmd_sock}")

    model=YOLO(args.model)
    src=int(args.source) if args.source.isdigit() else args.source
    cap=cv2.VideoCapture(src)
    if isinstance(src,int):
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    state=CommandState(args.send_interval, args.classes, parse_line(args.line) if args.line else None, args.area_side, args.iotc_stream)

    iotc=ResilientUnixClient(args.iotc_sock, name="IOTC", readable=False)
    cmdc=ResilientUnixClient(args.iotc_cmd_sock, name="CMD", readable=True)

    if args.iotc_cmd_sock:
        t=threading.Thread(target=command_thread, args=(cmdc, state, iotc), daemon=True); t.start()
        cmdc.send_line(json.dumps({"type":"hello","ts":now_iso()}))

    jsonl_fp=open(args.log_jsonl,"a", buffering=1) if args.log_jsonl else None
    prev=time.time(); last_emit=0.0

    try:
        while True:
            ok,frame=cap.read()
            if not ok: break
            with state.lock:
                if state.paused: time.sleep(min(state.send_interval,0.2)); continue
            if args.fps_limit>0:
                min_dt=1.0/args.fps_limit
                while True:
                    now=time.time()
                    if now-prev>=min_dt: break
                    time.sleep(0.001)

            snap=state.snap()
            line_cur=parse_line(snap["line"]) if snap["line"] else None
            left_pos=(snap["area_side"]=="left")
            classes_filter=[c.strip().lower() for c in (snap["classes"] or "").split(",") if c.strip()]

            res=model(frame, conf=args.conf, verbose=False)[0]
            names=getattr(res,"names",{})

            det=[]
            if res.boxes is not None and len(res.boxes)>0:
                xyxy=res.boxes.xyxy.cpu().numpy()
                cls_ids=res.boxes.cls.cpu().numpy().astype(int)
                confs=res.boxes.conf.cpu().numpy()
                for bb,ci,cf in zip(xyxy,cls_ids,confs):
                    label=names.get(ci,str(ci)).lower()
                    if classes_filter and label not in classes_filter: continue
                    x1,y1,x2,y2=map(float,bb); cx,cy=(x1+x2)/2.0,(y1+y2)/2.0
                    det.append({"name":label,"conf":float(cf),"xyxy":(x1,y1,x2,y2),"centroid":(cx,cy)})

            counts={"apples_left":0,"oranges_left":0,"bananas_left":0,"apples_right":0,"oranges_right":0,"bananas_right":0,"other_left":0,"other_right":0}
            def is_left(pt):
                if line_cur is None: return None
                a,b=line_cur; return line_side(pt,a,b)>0
            for d in det:
                name=d["name"]; side_left=is_left(d["centroid"]) if line_cur is not None else None
                key="apples" if name=="apple" else "oranges" if name=="orange" else "bananas" if name=="banana" else None
                if line_cur is None: continue
                if side_left is True: counts[f"{key}_left" if key else "other_left"]+=1
                elif side_left is False: counts[f"{key}_right" if key else "other_right"]+=1

            totals=defaultdict(int)
            for d in det: totals[d["name"]]+=1
            apples_total=int(totals.get("apple",0)); oranges_total=int(totals.get("orange",0)); bananas_total=int(totals.get("banana",0))

            if not args.no_draw:
                if line_cur is not None:
                    a,b=line_cur; cv2.line(frame,a,b,(255,255,0),2)
                for d in det:
                    x1,y1,x2,y2=map(int,d["xyxy"]); label=f"{d['name']} {d['conf']:.2f}"
                    color=(0,255,0)
                    if line_cur is not None:
                        a,b=line_cur; color=(0,200,0) if (line_side(d["centroid"],a,b)>0)==left_pos else (0,165,255)
                    cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
                    cv2.putText(frame,label,(x1,max(20,y1-6)),cv2.FONT_HERSHEY_SIMPLEX,0.5,color,1,cv2.LINE_AA)
                cv2.imshow("Vision Fruit (IoTConnect+CMD)",frame)
                if cv2.waitKey(1)&0xFF==27: break

            now=time.time()
            if (now-last_emit)>=max(0.5,float(snap["send_interval"])):
                last_emit=now
                payload={"v":"1.0","type":"fruit_counts","stream":snap["stream"],"ts":now_iso(),
                         "apples_left":int(counts["apples_left"]),"oranges_left":int(counts["oranges_left"]),"bananas_left":int(counts["bananas_left"]),
                         "apples_right":int(counts["apples_right"]),"oranges_right":int(counts["oranges_right"]),"bananas_right":int(counts["bananas_right"]),
                         "apples_total":apples_total,"oranges_total":oranges_total,"bananas_total":bananas_total,
                         "other_left":int(counts["other_left"]),"other_right":int(counts["other_right"])}
                line_json=json.dumps(payload); print(line_json)
                if jsonl_fp: jsonl_fp.write(line_json+"\n")
                iotc.send_line(line_json)

            prev=time.time()
    finally:
        cap.release()
        if not args.no_draw: cv2.destroyAllWindows()
        if jsonl_fp: 
            try: jsonl_fp.close()
            except: pass
        iotc.close()
        cmdc.close()

if __name__=="__main__":
    main()
