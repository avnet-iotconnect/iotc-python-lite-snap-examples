# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Michael Lamp <michael.lamp@avnet.com> et al.

// manager.js (Cockpit package) — with IoTConnect envelope format
(function () {
  "use strict";

  const SOCKET_PATH = "/var/snap/iotconnect/common/iotc.sock";
  const IO_EVENTS_URLS = [
    "http://127.0.0.1:9000/events",
    "http://localhost:9000/events",
    "/events",
    "http://127.0.0.1/events",
    "http://127.0.0.1:9000/api/events",
    "/api/events",
  ];

  const { spawn } = cockpit;

  const state = {
    cpu_percent: { val: null, alias: "cpu_percent" },
    mem_percent: { val: null, alias: "mem_percent" },
    disk_percent: { val: null, alias: "disk_percent" }
  };

  let sending = false;
  let timerId = null;
  let IO_URL_SELECTED = null;

  // ---------- DOM helpers ----------
  const $ = (id) => document.getElementById(id);
  const log = (s) => { const el = $("log"); if (!el) return; el.textContent += s + "\n"; el.scrollTop = el.scrollHeight; };

  // ---------- spawn with capture+live log ----------
  async function runSpawn(argv, opts = {}) {
    const eff = { err: "out", pty: false, ...opts };
    log(`$ ${argv.join(" ")}`);
    const p = cockpit.spawn(argv, eff);
    let buf = "";
    p.stream?.(chunk => {
      if (typeof chunk === "string") {
        buf += chunk;
        const t = chunk.trim();
        if (t) log(t);
      }
    });
    try { await p; log("[exit 0]"); return buf; }
    catch (e) { const s = (typeof e.exit_status === "number") ? e.exit_status : "unknown"; log(`[exit ${s}] ${e.problem || e.message || String(e)}`); return buf; }
  }

  // ---------- render table ----------
  function renderRows(st) {
    const tbody = $("rows");
    if (!tbody) return;
    tbody.innerHTML = "";

    const fixedOrder = ["cpu_percent", "mem_percent", "disk_percent"];
    const idxSet = new Set();
    Object.keys(st).forEach(k => {
      let m;
      if ((m = k.match(/^cnt(\d+)$/))) idxSet.add(+m[1]);
      if ((m = k.match(/^dio(\d+)_in$/))) idxSet.add(+m[1]);
      if ((m = k.match(/^dio(\d+)_out$/))) idxSet.add(+m[1]);
    });
    const indices = [...idxSet].sort((a,b)=>a-b);

    const orderedKeys = [];
    fixedOrder.forEach(k => { if (st[k]) orderedKeys.push(k); });
    indices.forEach(i => {
      const a = `cnt${i}`, b = `dio${i}_in`, c = `dio${i}_out`;
      if (st[a]) orderedKeys.push(a);
      if (st[b]) orderedKeys.push(b);
      if (st[c]) orderedKeys.push(c);
    });

    orderedKeys.forEach(k => {
      const raw = st[k]?.val;
      const pretty = (raw && typeof raw === "object") ? JSON.stringify(raw) : (raw ?? "");
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><input type="checkbox" data-k="${k}" class="chk"></td>
        <td><code>${k}</code></td>
        <td><input type="text" data-k="${k}" class="alias" value="${st[k].alias || ""}" placeholder="${k}" style="width:100%"></td>
        <td><span id="val-${k}">${pretty}</span></td>
      `;
      tbody.appendChild(tr);
    });
  }

  function updateValueCell(key, value) {
    const el = $(`val-${key}`);
    if (!el) return;
    el.textContent = (value && typeof value === "object") ? JSON.stringify(value) : (value ?? "");
  }

  function buildPayloadFromState(st) {
    const payload = {};
    document.querySelectorAll('input.chk[data-k]').forEach(chk => {
      if (!chk.checked) return;
      const k = chk.getAttribute("data-k");
      const a = document.querySelector(`input.alias[data-k="${k}"]`);
      const alias = (a?.value || a?.placeholder || k).trim() || k;
      payload[alias] = st[k]?.val ?? null;
    });
    return payload;
  }

  // ---------- buffer → first JSON object ----------
  function firstJsonObjectFromBuffer(buf) {
    let depth = 0, start = -1;
    for (let i = 0; i < buf.length; i++) {
      const ch = buf[i];
      if (ch === '{') { if (depth === 0) start = i; depth++; }
      else if (ch === '}') {
        depth--;
        if (depth === 0 && start !== -1) {
          const slice = buf.slice(start, i + 1);
          try { return JSON.parse(slice); } catch(_) {}
        }
      }
    }
    for (const line of buf.split(/\r?\n/)) {
      const s = line.trim(); if (!s) continue;
      try { return JSON.parse(s); } catch(_) {}
    }
    return null;
  }

  async function readIOOnce(url) {
    const buf = await runSpawn(["/usr/bin/env", "curl", "-fsSL", "--max-time", "2", url], { superuser: "try" });
    const obj = firstJsonObjectFromBuffer(buf);
    if (!obj) throw new Error("no complete JSON object found");
    const io = (obj.io && typeof obj.io === "object") ? obj.io : obj;
    return {
      ins:  Array.isArray(io.inputs)  ? io.inputs  : [],
      outs: Array.isArray(io.outputs) ? io.outputs : [],
      cnts: Array.isArray(io.counts)  ? io.counts  : []
    };
  }

  async function scanIO() {
    const override = document.getElementById("io-url")?.value?.trim();
    const urls = (override && override.length) ? [override] : IO_EVENTS_URLS;
    let lastErr;
    for (const url of urls) {
      try {
        log(`fetching IO via curl from ${url} ...`);
        const { ins, outs, cnts } = await readIOOnce(url);
        const n = Math.max(ins.length, outs.length, cnts.length);
        for (let i = 0; i < n; i++) {
          const keys = [
            ["cnt"+i,       (i < cnts.length) ? cnts[i] : null],
            ["dio"+i+"_in", (i < ins.length)  ? ins[i]  : null],
            ["dio"+i+"_out",(i < outs.length) ? outs[i] : null],
          ];
          keys.forEach(([k, v]) => {
            if (!state[k]) state[k] = { val: v, alias: k };
            else state[k].val = v;
          });
        }
        IO_URL_SELECTED = url;
        renderRows(state);
        log(`IO imported from ${url}`);
        return;
      } catch (e) {
        lastErr = e;
        log(`IO import failed from ${url}: ${e.message}`);
      }
    }
    throw lastErr || new Error("Unable to scan IO from any candidate URL");
  }

  async function refreshIO() {
    const url = IO_URL_SELECTED || document.getElementById("io-url")?.value?.trim();
    if (!url) return;
    try {
      const { ins, outs, cnts } = await readIOOnce(url);
      const n = Math.max(ins.length, outs.length, cnts.length);
      for (let i = 0; i < n; i++) {
        const upd = [
          ["cnt"+i,       (i < cnts.length) ? cnts[i] : null],
          ["dio"+i+"_in", (i < ins.length)  ? ins[i]  : null],
          ["dio"+i+"_out",(i < outs.length) ? outs[i] : null],
        ];
        upd.forEach(([k, v]) => {
          if (!state[k]) state[k] = { val: null, alias: k };
          state[k].val = v;
          updateValueCell(k, v);
        });
      }
    } catch (e) {
      log("refreshIO error: " + e.message);
    }
  }

  async function probe() {
    const py = [
      "import json, os, time",
      "def cpu_percent():",
      "  try:",
      "    import psutil",
      "    return psutil.cpu_percent(interval=0.05)",
      "  except Exception:",
      "    def rd():",
      "      with open('/proc/stat','r') as f:",
      "        for ln in f:",
      "          if ln.startswith('cpu '):",
      "            p=[int(x) for x in ln.split()[1:8]]; return p[3], sum(p)",
      "    i1,t1 = rd(); time.sleep(0.05); i2,t2 = rd()",
      "    idle=i2-i1; tot=t2-t1; return 0.0 if tot<=0 else 100.0*(1.0-idle/tot)",
      "def mem_percent():",
      "  try:",
      "    import psutil",
      "    return psutil.virtual_memory().percent",
      "  except Exception:",
      "    info = {}",
      "    with open('/proc/meminfo','r') as f:",
      "      for ln in f:",
      "        k,v = ln.split(':',1); info[k.strip()] = int(v.strip().split()[0])",
      "    total = info.get('MemTotal',0); avail = info.get('MemAvailable',0)",
      "    return 0.0 if total<=0 else (100.0 * (1.0 - (avail/total)))",
      "def disk_percent():",
      "  try:",
      "    import psutil",
      "    return psutil.disk_usage('/').percent",
      "  except Exception:",
      "    st = os.statvfs('/')",
      "    total = st.f_frsize * st.f_blocks",
      "    free  = st.f_frsize * st.f_bfree",
      "    used  = total - free",
      "    return 0.0 if total<=0 else (100.0 * used / total)",
      "out = {",
      "  'cpu_percent': round(cpu_percent(),1),",
      "  'mem_percent': round(mem_percent(),1),",
      "  'disk_percent': round(disk_percent(),1),",
      "}",
      "print(json.dumps(out))"
    ].join("\n");

    const out = await runSpawn(["/usr/bin/env", "python3", "-c", py], { superuser: "try" });
    try { return JSON.parse(out); }
    catch (e) { throw new Error("probe JSON parse error: " + e.message); }
  }

  // --- Send to IoTConnect socket (normalize to SINGLE envelope) ---------------
  async function sendToSocket(payloadObj) {
    // If someone accidentally passed an envelope, unwrap it to flat once.
    let flat = payloadObj;
    if (flat && typeof flat === "object" && "d" in flat) {
      try {
        if (Array.isArray(flat.d) && flat.d.length && flat.d[0] && typeof flat.d[0].d === "object") {
          flat = flat.d[0].d;
        } else if (flat.d && typeof flat.d === "object" && !Array.isArray(flat.d)) {
          flat = flat.d;
        }
      } catch { /* ignore */ }
    }

    const nowIso = new Date().toISOString();
    const envelope = { dt: nowIso, d: [{ dt: nowIso, d: flat }] };

    const wire = JSON.stringify(envelope);  // no trailing newline
    const b64 = btoa(unescape(encodeURIComponent(wire)));

    const py = [
      "import socket, sys, traceback, base64",
      "try:",
      "  wire = base64.b64decode(sys.argv[1])",
      "  s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)",
      "  s.settimeout(2.0)",
      `  s.connect('${SOCKET_PATH}')`,
      "  s.sendall(wire)",
      "  s.shutdown(socket.SHUT_WR)",
      "  s.close()",
      "  print('sent')",
      "except Exception as e:",
      "  print('PYERR:', e); traceback.print_exc(); sys.exit(1)"
    ].join("\n");

    await runSpawn(["/usr/bin/python3", "-c", py, b64], { superuser: "try" });
  }

  async function testSend() {
    log("testSend(): sending fixed payload to socket…");
    try {
      await sendToSocket({ cpu_percent: 33.3, mem_percent: 40.0, disk_percent: 22.0 });
      log("testSend(): OK");
    } catch (e) {
      log("testSend(): FAILED -> " + (e.problem || e.message));
    }
  }

  async function tick() {
    if (sending) return;
    sending = true;
    try {
      const sys = await probe();
      Object.keys(sys).forEach(k => {
        if (!state[k]) state[k] = { val: null, alias: k };
        state[k].val = sys[k];
        updateValueCell(k, sys[k]);
      });

      await refreshIO();

      const payload = buildPayloadFromState(state);
      if (Object.keys(payload).length === 0) { log("no selected signals; skipping send"); return; }

      log("sending (iotc flat): " + JSON.stringify(payload));
      await sendToSocket(payload);
      log("sent");
    } catch (e) {
      log("send/probe error: " + (e.problem || e.message || String(e)));
    } finally {
      sending = false;
    }
  }

  // ---------- Wire UI ----------
  window.addEventListener("DOMContentLoaded", () => {
    renderRows(state);
    log("iotc-manager loaded (cockpit)");

    $("btn-scan")?.addEventListener("click", async () => {
      try { await scanIO(); }
      catch (e) { log("scan error: " + e.message); }
    });

    $("btn-start")?.addEventListener("click", async () => {
      if (timerId) return;
      const sec = parseFloat($("interval")?.value || "1");
      const ms = Math.max(250, isFinite(sec) ? Math.round(sec * 1000) : 1000);
      log(`starting at ${ms} ms`);
      await tick();
      timerId = window.setInterval(tick, ms);
    });

    $("btn-stop")?.addEventListener("click", () => {
      if (!timerId) return;
      clearInterval(timerId);
      timerId = null;
      log("stopped");
    });

    $("btn-test")?.addEventListener("click", testSend);

    document.addEventListener("input", (ev) => {
      const t = ev.target;
      if (t?.classList?.contains("alias")) {
        const k = t.getAttribute("data-k");
        if (k && state[k]) state[k].alias = t.value;
      }
    });
  });
})();
