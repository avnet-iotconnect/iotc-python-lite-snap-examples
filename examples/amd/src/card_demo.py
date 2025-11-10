#!/usr/bin/env python3
# Cards Demo: CPU-only default, flat telemetry, ONNX labels autodetect

import argparse, json, os, socket, time, sys
from pathlib import Path
import numpy as np, cv2, psutil

try:
    import onnxruntime as ort
except Exception:
    ort = None

def extract_labels_from_onnx(model_path):
    """
    Returns a list of class names from ONNX metadata ('names' or 'labels').
    If the dict is 1-based (keys start at 1), inserts a 'background' at index 0.
    """
    try:
        import onnx, ast, re, json as _json
        m = onnx.load(model_path)
        raw=None
        for p in getattr(m,"metadata_props",[]):
            if "names" in p.key.lower() or "labels" in p.key.lower():
                raw=p.value; break
        if raw is None: return None
        s = re.sub(r"(\d+)\s*:", r'"\1":', raw)
        try: d = _json.loads(s)
        except Exception: d = ast.literal_eval(s)
        keys = sorted(d.keys(), key=lambda k:int(k))
        labels = []
        if int(keys[0]) == 1:
            labels.append("background")
            for i in range(1, len(keys)+1):
                labels.append(str(d[str(i)] if str(i) in d else d[i]))
        else:
            for i in range(len(keys)):
                labels.append(str(d[str(i)] if str(i) in d else d[i]))
        return labels
    except Exception:
        return None

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def open_iotc_socket(sock_path):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect(sock_path); return s

def send_flat(sock_path, payload_dict):
    try:
        s = open_iotc_socket(sock_path)
        s.sendall((json.dumps(payload_dict)+"\n").encode("utf-8")); s.close(); return True
    except Exception as e:
        print(f"[WARN] Telemetry send failed: {e}"); return False

def letterbox(im, new_shape=(640,640), color=(114,114,114)):
    h,w = im.shape[:2]; nh,nw = new_shape
    r = min(nh/h, nw/w)
    new_unpad = (int(round(w*r)), int(round(h*r)))
    dw, dh = nw-new_unpad[0], nh-new_unpad[1]; dw/=2; dh/=2
    if (w,h) != new_unpad:
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top,bottom,left,right = int(round(dh-0.1)), int(round(dh+0.1)), int(round(dw-0.1)), int(round(dw+0.1))
    im = cv2.copyMakeBorder(im,top,bottom,left,right,cv2.BORDER_CONSTANT, value=color)
    return im, r, (dw, dh)

def nms_boxes(boxes, scores, iou=0.45):
    idxs = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=0.0, nms_threshold=iou)
    keep = set([int(i) for i in np.array(idxs).reshape(-1)]) if len(boxes) else set()
    return [boxes[i] for i in keep], [scores[i] for i in keep], list(keep)

def parse_yolo(outs, img_shape, conf=0.15, iou=0.45, labels_len=1):
    H,W = img_shape[:2]
    a = np.array(outs[0])
    if a.ndim==3 and a.shape[0]==1 and a.shape[1]>=6: a=np.squeeze(a,0).transpose(1,0)
    elif a.ndim==3 and a.shape[0]==1 and a.shape[2]>=6: a=np.squeeze(a,0)
    dets=[]
    if a.ndim==2 and a.shape[1]==6:
        for x1,y1,x2,y2,cf,cl in a:
            if cf<conf: continue
            x1,y1,x2,y2 = map(int,(x1,y1,x2,y2))
            x1=max(0,min(W-1,x1)); y1=max(0,min(H-1,y1)); x2=max(0,min(W-1,x2)); y2=max(0,min(H-1,y2))
            c=int(cl); c=max(0,min(labels_len-1,c))
            dets.append({'xyxy':(x1,y1,x2,y2),'conf':float(cf),'cls':c})
        return dets
    if not (a.ndim==2 and a.shape[1]>=6): return dets
    xywh=a[:,:4].astype(np.float32); obj=a[:,4:5].astype(np.float32); cls=a[:,5:].astype(np.float32)
    sig=lambda x:1.0/(1.0+np.exp(-x))
    if np.nanmax(obj)>1.0 or np.nanmin(obj)<0.0: obj=sig(obj)
    if cls.size and (np.nanmax(cls)>1.0 or np.nanmin(cls)<0.0): cls=sig(cls)
    if np.nanmax(xywh[:,:2])<=1.5 and np.nanmax(xywh[:,2:])<=1.5:
        xywh[:,0]*=W; xywh[:,1]*=H; xywh[:,2]*=W; xywh[:,3]*=H
    cls_ids=np.argmax(cls,1) if cls.size else np.zeros((a.shape[0],),dtype=int)
    cls_conf=cls[np.arange(cls.shape[0]),cls_ids] if cls.size else np.ones((a.shape[0],),dtype=np.float32)
    scores = cls_conf if (np.nanstd(obj)<1e-6 or np.nanmean(obj)<0.05) else (obj.flatten()*cls_conf)
    keep=np.where(scores>=conf)[0]
    boxes=[]; sc=[]
    for i in keep:
        x,y,w,h=xywh[i]; x1=int(x-w/2); y1=int(y-h/2); x2=int(x+w/2); y2=int(y+h/2)
        x1=max(0,min(W-1,x1)); y1=max(0,min(H-1,y1)); x2=max(0,min(W-1,x2)); y2=max(0,min(H-1,y2))
        boxes.append([x1,y1,x2-x1,y2-y1]); sc.append(float(scores[i]))
    if not boxes: return dets
    _,_,kidx=nms_boxes(boxes,sc,iou)
    for i in kidx:
        x1,y1,w,h=boxes[i]; x2=x1+w; y2=y1+h
        c=int(cls_ids[keep[i]]); c=max(0,min(labels_len-1,c))
        dets.append({'xyxy':(x1,y1,x2,y2),'conf':sc[i],'cls':c})
    return dets

def blackjack_from_csv(names_str):
    if not names_str: return 0
    total=0; aces=0
    for name in names_str.split(","):
        name=name.strip()
        if not name or name=="card": continue
        rank=name[:-1]
        if rank in ("J","Q","K"): total+=10
        elif rank=="A": aces+=1; total+=11
        else:
            try: total+=int(rank)
            except: pass
    while total>21 and aces>0: total-=10; aces-=1
    return total

def main():
    ap=argparse.ArgumentParser(description="Cards Demo (flat telemetry)")
    ap.add_argument("--config", default="iotc_config.json")
    args=ap.parse_args()

    cfg=load_config(args.config)
    script_dir=Path(__file__).parent

    model_path=cfg.get("model_path","models/cards.onnx")
    if not Path(model_path).is_absolute():
        model_path=str((script_dir/model_path).resolve())
    labels_path=cfg.get("labels_path","labels.txt")
    if not Path(labels_path).is_absolute():
        labels_path=str((script_dir/labels_path).resolve())

    labels=extract_labels_from_onnx(model_path)
    if labels:
        print(f"[INFO] Using labels from ONNX ({len(labels)}). First/last: {labels[0]} / {labels[-1]}")
    else:
        if Path(labels_path).exists():
            labels=[l.strip() for l in open(labels_path,"r",encoding="utf-8").read().splitlines() if l.strip()]
            print(f"[INFO] Using labels file: {labels_path} ({len(labels)})")
        else:
            labels=["card"]; print("[WARN] No ONNX labels and no labels.txt; defaulting to ['card']")

    if ort is None: print("[ERROR] onnxruntime not installed."); sys.exit(1)
    if not Path(model_path).exists(): print("[ERROR] Model not found:", model_path); sys.exit(1)

    so=ort.SessionOptions(); so.enable_profiling=False
    session=ort.InferenceSession(model_path, sess_options=so, providers=["CPUExecutionProvider"])
    input_name=session.get_inputs()[0].name
    print(f"[INFO] Model loaded: {model_path} | input={input_name}")

    simulate=bool(cfg.get("simulate",False))
    cap=None
    if not simulate:
        src=int(cfg.get("video_source",0))
        cap=cv2.VideoCapture(src)
        if not cap.isOpened(): print("[ERROR] Cannot open video source:", src); sys.exit(1)

    sock_path=cfg.get("socket_path","/var/snap/iotconnect/common/iotc.sock")
    send_iv=int(cfg.get("send_interval_sec",4))
    iw=int(cfg.get("model_input_w",640)); ih=int(cfg.get("model_input_h",640))
    conf=float(cfg.get("conf_threshold",0.15)); iou=float(cfg.get("iou_threshold",0.6))
    show=bool(cfg.get("video_display",True)); draw=bool(cfg.get("video_draw_boxes",True))

    last=0.0; seen=set()
    try:
        while True:
            t0=time.time()
            if simulate:
                frame=np.zeros((480,640,3),dtype=np.uint8); dets=[]
            else:
                ok,frame=cap.read()
                if not ok: print("[WARN] camera read fail"); break
                img,r,(dw,dh)=letterbox(frame,(ih,iw))
                blob=img[:,:,::-1].transpose(2,0,1).astype(np.float32)/255.0
                blob=np.ascontiguousarray(blob)[None,...]
                outs=session.run(None,{input_name:blob})
                dets=parse_yolo(outs,img.shape,conf,iou,len(labels))
                def unletter(x1,y1,x2,y2,r,dw,dh):
                    x1=int((x1-dw)/r); y1=int((y1-dh)/r); x2=int((x2-dw)/r); y2=int((y2-dh)/r); return x1,y1,x2,y2
                dets=[{'xyxy':unletter(*d['xyxy'],r,dw,dh),'conf':d['conf'],'cls':d['cls']} for d in dets]

            names=[]; boxes=[]; confs=[]
            for d in dets:
                nm=labels[d['cls']] if 0<=d['cls']<len(labels) else "card"
                names.append(nm)
                x1,y1,x2,y2=d['xyxy']; boxes.append(f"{x1}:{y1}:{x2}:{y2}")
                confs.append(f"{d['conf']:.2f}")
                if nm!="card": seen.add(nm)

            names_str=",".join(names) if names else ""
            boxes_str=";".join(boxes) if boxes else ""
            confs_str=",".join(confs) if confs else ""
            seen_str=",".join(sorted(seen)) if seen else ""
            bj=blackjack_from_csv(names_str)

            dt=time.time()-t0; fps=(1.0/dt) if dt>0 else 0.0
            cpu=psutil.cpu_percent(None); mem=psutil.virtual_memory().percent
            now=time.time()
            if now-last>=send_iv:
                payload={"v":"1.0","type":"cards_demo_flat","ts":int(now),
                         "cards_seen_this_frame":names_str,"boxes_this_frame":boxes_str,"confs_this_frame":confs_str,
                         "cards_seen_unique":seen_str,"blackjack_value":bj,"perf_fps":round(fps,2),
                         "perf_cpu_percent":cpu,"perf_mem_percent":mem}
                ok=send_flat(sock_path,payload)
                print("[TX]", json.dumps({"perf_fps":round(fps,2),"sent":ok}))
                last=now

            if show:
                vis=frame if not simulate else np.zeros((480,640,3),dtype=np.uint8)
                if draw:
                    for d in dets:
                        x1,y1,x2,y2=d['xyxy']; label=labels[d['cls']] if 0<=d['cls']<len(labels) else "card"
                        cv2.rectangle(vis,(x1,y1),(x2,y2),(0,255,0),2)
                        cv2.putText(vis,label,(x1,max(0,y1-6)),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),1,cv2.LINE_AA)
                cv2.putText(vis,f"Unique:{len(seen)} | FPS:{fps:.1f} | BJ:{bj}",(10,20),
                            cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),2,cv2.LINE_AA)
                k=cv2.waitKey(1)&0xFF
                if k in (27,ord('q')): break
                if k==ord('r'): seen.clear(); print("[RESET] cleared unique")
                if k in (ord('+'),ord('=')): conf=min(conf+0.05,1.0); print(f"[TUNE] conf -> {conf:.2f}")
                if k in (ord('-'),ord('_')): conf=max(conf-0.05,0.0); print(f"[TUNE] conf -> {conf:.2f}")
    finally:
        if cap is not None: cap.release()
        cv2.destroyAllWindows()

if __name__=="__main__":
    main()
