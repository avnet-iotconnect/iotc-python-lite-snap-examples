#!/usr/bin/env python3
import argparse, onnx, ast, re, json, sys, pathlib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="Path to ONNX model")
    ap.add_argument("--out", required=True, help="labels.txt to write")
    args = ap.parse_args()

    m = onnx.load(args.model)
    raw = None
    for p in getattr(m, "metadata_props", []):
        if "names" in p.key.lower() or "labels" in p.key.lower():
            raw = p.value; break
    if raw is None:
        print("No embedded names found in", args.model); sys.exit(2)

    s = re.sub(r"(\d+)\s*:", r'"\1":', raw)
    try: d = json.loads(s)
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

    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(labels) + "\n")
    print(f"Wrote {args.out} with {len(labels)} labels. First/last:", labels[0], "/", labels[-1])

if __name__ == "__main__":
    main()
