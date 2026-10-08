#!/usr/bin/env python3
"""
Generate the /IOTCONNECT device template and dashboard export for the Vision Arena.

  ./tools/make_templates.py            # writes files/icam540-arena-*.json

The dashboard JSON follows the same export format as the other examples in this
repository (ddType 2 + widget items). Device/template GUIDs are placeholders:
after importing, edit each widget and re-select your device.
"""

import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = os.path.join(os.path.dirname(HERE), "files")

DEVICE_ID = "mclICAM540arena"
DEVICE_GUID = "00000000-0000-4000-8000-00000000A540"
TEMPLATE_GUID = "00000000-0000-4000-8000-00000000AA11"
FONT = "Proxima Nova"

# ---------------------------------------------------------------- attributes
A = []


def attr(name, display, typ, desc, unit="", color=None):
    d = {"name": name, "displayName": display, "type": typ, "description": desc, "unit": unit, "aggregateTypes": []}
    if color:
        d["attributeColor"] = color
    A.append(d)


attr("ts", "Sample Time", "INTEGER", "Unix epoch seconds when the payload was built", "s")
attr("type", "Message Type", "STRING", "Payload discriminator (arena)")
attr("pipeline", "Pipeline State", "STRING", "stopped | starting | running | restarting | error")
attr("message", "Status Message", "STRING", "Human readable pipeline status / last error")
attr("streams", "Streams", "INTEGER", "Video streams in the DeepStream batch (camera + looping videos)")
attr("streams_active", "Streams Reporting", "INTEGER", "Streams that produced detections in the last 3 s")
attr("model", "Model", "STRING", "peoplenet | resnet10")
attr("precision", "Precision", "STRING", "TensorRT precision of the running engine (fp32/fp16/int8)")
attr("batch", "Engine Batch", "INTEGER", "nvinfer batch size of the running engine")
attr("infer_interval", "Inference Interval", "INTEGER", "Frames skipped between inferences (0 = every frame)")
attr("osd_analytics", "Overlay", "STRING", "on when the zone/line overlay is drawn by nvdsanalytics")
attr("uptime_s", "Device Uptime", "DECIMAL", "Linux uptime", "s")
attr("pipeline_uptime_s", "Pipeline Uptime", "DECIMAL", "Seconds since deepstream-app was (re)started", "s")

attr("fps_cam", "Camera FPS", "DECIMAL", "Frames per second on the camera stream", "fps", "#76b900")
attr("fps_total", "Total FPS", "DECIMAL", "Sum of FPS across all streams (inference throughput)", "fps", "#76b900")
attr("fps_min", "Slowest Stream FPS", "DECIMAL", "Minimum FPS across streams", "fps")
attr("fps_avg", "Average Stream FPS", "DECIMAL", "Mean FPS across streams", "fps")
attr("fps_streams", "Streams With FPS", "INTEGER", "Streams present in the last PERF report")
attr("infer_mpx_s", "Megapixels Inferred / s", "DECIMAL", "fps_total x streammux resolution", "Mpx/s")
attr("msgs_per_s", "Detection Messages / s", "DECIMAL", "DeepStream metadata messages received over MQTT", "msg/s")
attr("objects_total", "Objects Tracked", "INTEGER", "Objects in the latest message of every stream")
attr("persons_total", "Persons (all streams)", "INTEGER", "Person detections across all streams")
attr("vehicles_total", "Vehicles (all streams)", "INTEGER", "Vehicle detections across all streams")

attr("visitors_in", "Visitors In", "INTEGER", "Line crossings into the booth since reset", "", "#7ed321")
attr("visitors_out", "Visitors Out", "INTEGER", "Line crossings out of the booth since reset", "", "#f5a623")
attr("occupancy", "At Booth Now", "INTEGER", "People inside the booth zone right now", "", "#4a90e2")
attr("occupancy_peak", "Peak Occupancy", "INTEGER", "Highest booth occupancy since reset")
attr("people_now", "People In View", "INTEGER", "Tracked people anywhere in the camera frame")
attr("engaged", "Engaged", "INTEGER", "People in the zone longer than the engage threshold", "", "#7b64ff")
attr("dwell_avg_s", "Avg Dwell", "DECIMAL", "Average time spent in the booth zone", "s", "#7b64ff")
attr("dwell_max_s", "Max Dwell", "DECIMAL", "Longest time spent in the booth zone", "s")
attr("dwell_last_s", "Last Dwell", "DECIMAL", "Dwell time of the last person who left the zone", "s")
attr("tracks_total", "Unique Tracks", "INTEGER", "Unique tracker IDs seen on the camera since reset")
attr("hot_zone", "Hot Zone", "STRING", "left | center | right third of the frame with most people")
attr("event", "Last Event", "STRING", "visitor_in | visitor_out | overcrowded (cleared after 30 s)")

attr("gpu_load_pct", "GPU Load", "DECIMAL", "GR3D utilisation from tegrastats", "%", "#76b900")
attr("gpu_freq_mhz", "GPU Clock", "DECIMAL", "GR3D frequency", "MHz")
attr("gpu_temp_c", "GPU Temperature", "DECIMAL", "GPU thermal zone", "C", "#d0021b")
attr("cpu_load_pct", "CPU Load", "DECIMAL", "Aggregate CPU utilisation", "%")
attr("cpu_temp_c", "CPU Temperature", "DECIMAL", "CPU thermal zone", "C")
attr("soc_temp_c", "SoC Temperature", "DECIMAL", "SoC / junction thermal zone", "C")
attr("power_w", "Module Power", "DECIMAL", "VDD_IN from tegrastats", "W", "#f5a623")
attr("power_gpu_w", "GPU Rail Power", "DECIMAL", "VDD_CPU_GPU_CV rail", "W")
attr("ram_used_mb", "RAM Used", "INTEGER", "Memory in use", "MB")
attr("ram_total_mb", "RAM Total", "INTEGER", "Memory installed", "MB")
attr("emc_pct", "Memory Bandwidth", "DECIMAL", "EMC utilisation", "%")
attr("nvdec_mhz", "NVDEC Clock", "DECIMAL", "Hardware decoder clock (0/absent when idle)", "MHz")

# ---------------------------------------------------------------- commands
C = []


def cmd(name, command, param=False, ack=True):
    C.append({"name": name, "command": command, "requiredParam": param, "requiredAck": ack, "isOTACommand": False})


cmd("Pipeline: Start", "start")
cmd("Pipeline: Stop", "stop")
cmd("Pipeline: Restart", "restart")
cmd("Pipeline: Status", "status")
cmd("Preset: Booth (1 stream)", "preset booth")
cmd("Preset: Stress (4 streams)", "preset stress")
cmd("Preset: Max (9 streams)", "preset max")
cmd("Set Streams (1-9)", "set_streams", param=True)
cmd("Model: PeopleNet", "set_model peoplenet")
cmd("Model: ResNet10 4-class", "set_model resnet10")
cmd("Set Precision (fp32|fp16|int8)", "set_precision", param=True)
cmd("Set Inference Interval (0-10)", "set_interval", param=True)
cmd("Batched Engine (on|off)", "set_batched", param=True)
cmd("Overlay: On", "set_osd 1")
cmd("Overlay: Off", "set_osd 0")
cmd("Set Booth Zone (x,y;x,y;x,y;...)", "set_roi", param=True)
cmd("Set Count Line (x1,y1;x2,y2)", "set_line", param=True)
cmd("Flip Count Line Direction", "flip_line")
cmd("Set Engage Seconds", "set_engage", param=True)
cmd("Set Overcrowd Threshold", "set_overcrowd", param=True)
cmd("Reset Counters", "reset_counts")
cmd("Set Telemetry Interval (s)", "set_telemetry_interval", param=True)
cmd("Ping", "ping")

device_template = {
    "code": "ICAM540A",
    "name": "Advantech iCAM-540 Vision Arena",
    "authType": 2,
    "attributes": A,
    "commands": C,
    "messageVersion": "2.1",
    "capability": "0",
    "properties": {
        "description": "DeepStream multi-stream vision analytics on the Advantech iCAM-540 (NVIDIA Jetson Orin) via the /IOTCONNECT Snap",
        "dataFrequency": "3",
        "fileSupport": False,
    },
    "_meta": {"version": "2.0"},
}

# ---------------------------------------------------------------- dashboard
ATTR_TYPES = {a["name"]: a["type"] for a in A}


def guid():
    return str(uuid.uuid4()).upper()


def attr_entry(name, checked):
    return {
        "attributeGuid": name,
        "attributeName": name,
        "displayName": name,
        "checked": "true" if checked else "false",
        "dataType": ATTR_TYPES[name],
        "attributeLatestValue": "",
        "deviceUpdatedDate": "1900-01-01T00:00:00.000Z",
        "gatewayUpdatedDate": "NA",
        "attributeValue": "NA",
    }


def attr_list(checked_names):
    return [attr_entry(a["name"], a["name"] in checked_names) for a in A]


def device_ref():
    return {"deviceGuid": DEVICE_GUID, "deviceUniqueId": DEVICE_ID}


def widget(kind, title, x, y, w, h, contents, bg="#ffffff", fg="#343434", size="18", extra_props=None, align=""):
    props = {"x": str(x), "y": str(y), "w": str(w), "h": str(h), "i": kind, "isStatic": "false"}
    props.update(extra_props or {})
    return {
        "widgetGuid": guid(),
        "widgetProperties": {
            "i": kind, "background": bg, "fontColor": fg, "fontFamily": FONT, "fontSize": size,
            "title": title, "titleAlign": align, "contents": contents,
        },
        "properties": props,
    }


def label(title, x, y, w, h=2, bg="#0b1226", fg="#ffffff", size="22"):
    return widget("Label", title, x, y, w, h, "", bg=bg, fg=fg, size=size,
                  extra_props={"minW": "6", "minH": "2", "maxH": "2"})


def gauge(title, name, x, y, w, h, vmax, zones, vmin=0):
    contents = {"gauge": {
        "device": device_ref(),
        "attributes": {"attribute": attr_entry(name, True)},
        "minValue": str(vmin), "maxValue": str(vmax), "version": "2.0",
        "zones": [{"zoneColor": c, "zoneName": n, "upToValue": str(v)} for n, v, c in zones],
        "attrType": "1", "key": "gauge",
    }}
    return widget("gauge", title, x, y, w, h, contents, bg="#000000", fg="#ffffff",
                  extra_props={"minW": "10", "minH": "9", "maxH": "15", "maxW": "16"})


def live(title, name, x, y, w, h=4, fg="#00aa88", size="22"):
    contents = {
        "attributeValue": {"attributeName": name, "key": "attributeValue"},
        "attributeTime": {"attributeName": name, "key": "attributeTime"},
        "live": {"device": device_ref(), "attributes": {"attribute": attr_entry(name, True)},
                 "rules": "", "attrType": "1", "key": "live"},
    }
    return widget("Live", title, x, y, w, h, contents, bg="#ffffff", fg=fg, size=size,
                  extra_props={"minW": "7", "minH": "4", "maxH": "4", "maxW": "20"})


def chart(title, names, x, y, w, h, color):
    contents = {"liveChart": {
        "device": device_ref(), "attributes": {"attribute": attr_list(set(names))},
        "lineColor": color, "barColor": color, "barCount": "10", "attrType": "1", "key": "line",
        "recentEndPoints": "30",
    }}
    return widget("LiveLineChart", title, x, y, w, h, contents,
                  extra_props={"minW": "12", "minH": "12", "maxH": "30", "maxW": "60"})


def control(title, x, y, left, right, w=10, h=6):
    """left/right: (text, command, param, color)"""
    contents = {"control": {
        "device": DEVICE_ID, "deviceGuid": DEVICE_GUID, "controlType": "button",
        "leftText": left[0], "leftCommand": left[1], "leftSwitchColor": left[3], "leftBackgroundColor": "", "leftParam": left[2],
        "rightText": right[0], "rightCommand": right[1], "rightSwitchColor": right[3], "rightBackgroundColor": "", "rightParam": right[2],
        "showStatus": "true", "template": TEMPLATE_GUID, "key": "control",
    }}
    return widget("Control", title, x, y, w, h, contents, bg="#fff",
                  extra_props={"minW": "9", "minH": "6", "maxH": "15", "maxW": "15"})


def device_command(title, x, y, w, h):
    contents = {"deviceCommand": {"template": TEMPLATE_GUID, "device": DEVICE_ID, "deviceGuid": DEVICE_GUID}}
    return widget("DeviceCommand", title, x, y, w, h, contents, bg="#fff", fg="#000",
                  extra_props={"minW": "22", "minH": "10", "maxH": "20", "maxW": "35"})


GREEN, BLUE, AMBER, RED, PURPLE = "#7ed321", "#4a90e2", "#f5a623", "#d0021b", "#7b64ff"
NV = "#76b900"

items = []
items.append(label("ADVANTECH iCAM-540  |  NVIDIA JETSON ORIN  |  /IOTCONNECT VISION ARENA", 0, 0, 103, bg="#0b1226", size="26"))
items.append(label("BOOTH ANALYTICS - PeopleNet + NvDCF tracker on the live camera", 0, 2, 52, bg="#EE2E24"))
items.append(label("JETSON LIVE LOAD - crank the streams from the cloud and watch the Orin work", 52, 2, 51, bg=NV, fg="#000000"))

# booth gauges
items.append(gauge("Visitors In", "visitors_in", 0, 4, 13, 9, 100, [("Quiet", 10, BLUE), ("Busy", 40, GREEN), ("Packed", 100, AMBER)]))
items.append(gauge("At Booth Now", "occupancy", 13, 4, 13, 9, 8, [("Empty", 1, BLUE), ("Good", 4, GREEN), ("Crowded", 8, RED)]))
items.append(gauge("Engaged (>5 s)", "engaged", 26, 4, 13, 9, 8, [("None", 1, BLUE), ("Some", 4, GREEN), ("Many", 8, PURPLE)]))
items.append(gauge("Avg Dwell (s)", "dwell_avg_s", 39, 4, 13, 9, 60, [("Glance", 5, BLUE), ("Interested", 20, GREEN), ("Hooked", 60, PURPLE)]))
# jetson gauges
items.append(gauge("GPU Load (%)", "gpu_load_pct", 52, 4, 12, 9, 100, [("Idle", 30, BLUE), ("Working", 80, GREEN), ("Maxed", 100, RED)]))
items.append(gauge("Total FPS", "fps_total", 64, 4, 12, 9, 300, [("1 stream", 35, BLUE), ("Multi", 150, GREEN), ("Max", 300, NV)]))
items.append(gauge("Module Power (W)", "power_w", 76, 4, 12, 9, 30, [("Low", 10, BLUE), ("Mid", 20, GREEN), ("High", 30, AMBER)]))
items.append(gauge("GPU Temp (C)", "gpu_temp_c", 88, 4, 12, 9, 90, [("Cool", 50, BLUE), ("Warm", 70, AMBER), ("Hot", 90, RED)]))

# live tiles
items.append(live("Visitors Out", "visitors_out", 0, 13, 13, fg=AMBER))
items.append(live("Peak Occupancy", "occupancy_peak", 13, 13, 13, fg=BLUE))
items.append(live("Last Event", "event", 26, 13, 13, fg=RED, size="18"))
items.append(live("Hot Zone", "hot_zone", 39, 13, 13, fg=PURPLE, size="18"))
items.append(live("Streams", "streams", 52, 13, 12, fg=NV))
items.append(live("Model", "model", 64, 13, 12, fg="#343434", size="18"))
items.append(live("Precision / Batch", "precision", 76, 13, 12, fg="#343434", size="18"))
items.append(live("Pipeline", "pipeline", 88, 13, 12, fg=GREEN, size="18"))

# charts
items.append(chart("Booth - people in view / at booth / engaged", ["people_now", "occupancy", "engaged"], 0, 17, 52, 12, BLUE))
items.append(chart("Jetson - GPU load, total FPS, power", ["gpu_load_pct", "fps_total", "power_w"], 52, 17, 51, 12, NV))

# controls
items.append(label("CLOUD CONTROLS - every button regenerates the DeepStream pipeline on the device (restart takes a few seconds)", 0, 29, 103, bg="#343434", size="18"))
items.append(control("Preset", 0, 31, ("Booth", "preset", "booth", GREEN), ("Stress", "preset", "stress", AMBER)))
items.append(control("Max Load", 10, 31, ("9 streams", "preset", "max", RED), ("4 streams", "preset", "stress", AMBER)))
items.append(control("Model", 20, 31, ("PeopleNet", "set_model", "peoplenet", GREEN), ("ResNet10", "set_model", "resnet10", BLUE)))
items.append(control("Precision", 30, 31, ("FP16", "set_precision", "fp16", NV), ("FP32", "set_precision", "fp32", BLUE)))
items.append(control("Skip Frames", 40, 31, ("Every frame", "set_interval", "0", GREEN), ("Every 3rd", "set_interval", "2", AMBER)))
items.append(control("Pipeline", 50, 31, ("Restart", "restart", "", GREEN), ("Stop", "stop", "", RED)))
items.append(control("Counters", 0, 37, ("Reset", "reset_counts", "", AMBER), ("Status", "status", "", BLUE)))
items.append(control("Overlay", 10, 37, ("On", "set_osd", "1", GREEN), ("Off", "set_osd", "0", "#9b9b9b")))
items.append(control("Count Line", 20, 37, ("Flip dir", "flip_line", "", PURPLE), ("Ping", "ping", "", BLUE)))
items.append(live("Status Message", "message", 30, 37, 30, fg="#343434", size="16"))
items.append(live("Msgs / s", "msgs_per_s", 30, 41, 15, fg="#343434", size="18"))
items.append(live("Objects Tracked", "objects_total", 45, 41, 15, fg="#343434", size="18"))
items.append(device_command("Command Console (set_streams 1-9, set_roi, set_line ...)", 60, 31, 33, 12))

# secondary metrics row
items.append(label("MORE JETSON COUNTERS", 0, 45, 103, bg="#0b1226", size="18"))
items.append(gauge("CPU Load (%)", "cpu_load_pct", 0, 47, 12, 9, 100, [("Idle", 30, BLUE), ("Busy", 80, GREEN), ("Maxed", 100, RED)]))
items.append(gauge("Memory BW (%)", "emc_pct", 12, 47, 12, 9, 100, [("Low", 30, BLUE), ("Mid", 70, GREEN), ("Saturated", 100, RED)]))
items.append(gauge("Camera FPS", "fps_cam", 24, 47, 12, 9, 35, [("Slow", 10, RED), ("OK", 25, AMBER), ("Full", 35, GREEN)]))
items.append(gauge("Slowest Stream FPS", "fps_min", 36, 47, 12, 9, 35, [("Slow", 10, RED), ("OK", 25, AMBER), ("Full", 35, GREEN)]))
items.append(chart("Per-run FPS - camera vs slowest stream", ["fps_cam", "fps_min"], 48, 47, 55, 12, AMBER))
items.append(live("RAM Used (MB)", "ram_used_mb", 0, 56, 12, fg="#343434", size="18"))
items.append(live("GPU Clock (MHz)", "gpu_freq_mhz", 12, 56, 12, fg="#343434", size="18"))
items.append(live("Mpx inferred / s", "infer_mpx_s", 24, 56, 12, fg=NV, size="18"))
items.append(live("Unique Tracks", "tracks_total", 36, 56, 12, fg="#343434", size="18"))

dashboard = {"ddType": 2, "items": items}


def main():
    os.makedirs(FILES, exist_ok=True)
    with open(os.path.join(FILES, "icam540-arena-device-template.json"), "w") as f:
        json.dump(device_template, f, indent=2)
    with open(os.path.join(FILES, "icam540-arena-dashboard-template.json"), "w") as f:
        json.dump(dashboard, f, indent=2)
    print(f"device template: {len(A)} attributes, {len(C)} commands")
    print(f"dashboard: {len(items)} widgets")


if __name__ == "__main__":
    main()
