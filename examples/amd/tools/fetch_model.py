#!/usr/bin/env python3
import argparse, os, sys, shutil, tempfile, urllib.request, subprocess

def ensure_ultralytics():
    try:
        import ultralytics  # noqa
    except Exception:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ultralytics"])

def download_if_url(src, dest_dir):
    if src.startswith(("http://","https://")):
        fn = os.path.join(dest_dir, os.path.basename(src))
        print("[INFO] Downloading weights:", src)
        urllib.request.urlretrieve(src, fn)
        return fn
    return src

def export_to_onnx(pt_path, imgsz=640, opset=12):
    from ultralytics import YOLO
    model = YOLO(pt_path)
    onnx_path = model.export(format="onnx", imgsz=imgsz, opset=opset, dynamic=False)
    if os.path.isdir(onnx_path):
        import glob
        c = glob.glob(os.path.join(onnx_path, "*.onnx"))
        if not c: raise RuntimeError("ONNX export dir did not contain .onnx")
        onnx_path = c[0]
    if not os.path.exists(onnx_path):
        raise RuntimeError("Export did not produce an ONNX file.")
    models_dir = os.path.join("src","models")
    os.makedirs(models_dir, exist_ok=True)
    dest = os.path.join(models_dir, "cards.onnx")
    shutil.move(onnx_path, dest)
    print("[OK] Saved:", dest)
    return dest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pt", required=True, help="Path or URL to YOLOv8 .pt weights")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--opset", type=int, default=12)
    args = ap.parse_args()

    ensure_ultralytics()
    with tempfile.TemporaryDirectory() as td:
        pt_local = download_if_url(args.pt, td)
        if not os.path.exists(pt_local):
            print("[ERROR] Weights not found:", pt_local); sys.exit(1)
        export_to_onnx(pt_local, imgsz=args.imgsz, opset=args.opset)

if __name__ == "__main__":
    main()
