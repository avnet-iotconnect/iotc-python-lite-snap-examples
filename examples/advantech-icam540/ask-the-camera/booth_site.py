#!/usr/bin/env python3
"""
Booth site for the iCAM-540 "Ask the camera" demo, fed by /IOTCONNECT.

A small server that holds the /IOTCONNECT credentials, keeps a session alive, polls the device's
latest telemetry and recent history through the REST API, sends commands through the cloud, and
serves a single-page dashboard. The browser only ever talks to this server: the solution key and
password never reach a web page.

Configuration (environment, usually /etc/default/booth-site):
  IOTC_USERNAME, IOTC_PASSWORD, IOTC_SOLUTION_KEY      portal login + solution key (REST API access)
  IOTC_PLATFORM=aws  IOTC_ENV=poc                        from Settings > Key Vault in the portal
  IOTC_DEVICE_IDS=mclAdvICAM540b                         device unique ids to show (comma separated)
  BOOTH_PORT=8090  BOOTH_TITLE="..."  BOOTH_SUBTITLE="..."
  BOOTH_LIVE_VIEW=http://127.0.0.1:8088                  the narrator's live view, proxied as /live/...
  BOOTH_POLL_S=3
  BOOTH_TZ=America/Chicago                               the booth's time zone: "today" and the times on the page

  ./booth_site.py                                        # then open http://<host>:8090/
"""

import collections
import datetime
import hashlib
import hmac
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
try:
    from zoneinfo import ZoneInfo
except ImportError:  # very old python: fall back to UTC
    ZoneInfo = None

HERE = os.path.dirname(os.path.abspath(__file__))


def log(tag, msg):
    print(f"[{tag}] {time.strftime('%H:%M:%S')} {msg}", flush=True)


# --------------------------------------------------------------------------
# /IOTCONNECT REST API client (discovery -> basic token -> login -> bearer)
# --------------------------------------------------------------------------

class IotcApi:
    def __init__(self, username, password, skey, platform="aws", env="poc"):
        self.username, self.password, self.skey = username, password, skey
        self.platform, self.env = platform, env
        self.urls = {}
        self.token = None
        self.refresh_token = None
        self.token_expiry = 0.0
        self.lock = threading.Lock()

    def _call(self, url, body=None, headers=None, method=None, timeout=30):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method,
                                     headers={**({"Content-Type": "application/json"} if data else {}), **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read().decode())
            except Exception:
                return e.code, {}

    def discover(self):
        st, resp = self._call(f"https://discovery.iotconnect.io/api/uisdk/solutionkey/{self.skey}/env/{self.env}"
                              f"?version=2.1&pf={self.platform}")
        if st != 200 or not resp.get("data"):
            raise RuntimeError(f"discovery failed ({st}): {resp.get('message')}")
        self.urls = resp["data"]
        return self.urls

    def login(self):
        if not self.urls:
            self.discover()
        auth = self.urls["authBaseUrl"]
        st, bt = self._call(auth + "/Auth/basic-token")
        if st != 200 or not bt.get("data"):
            raise RuntimeError(f"basic-token failed ({st})")
        st, resp = self._call(auth + "/Auth/login", {"username": self.username, "password": self.password},
                              {"solution-key": self.skey, "Authorization": "Basic " + bt["data"]})
        if st != 200 or not resp.get("access_token"):
            raise RuntimeError(f"login failed ({st}): {resp.get('message')}")
        with self.lock:
            self.token = resp["access_token"]
            self.refresh_token = resp.get("refresh_token")
            self.token_expiry = time.time() + float(resp.get("expires_in") or 3600)
        log("IOTC", f"logged in as {self.username}, token valid {int((self.token_expiry - time.time()) / 3600)} h")

    def refresh(self):
        if not self.refresh_token:
            return self.login()
        st, resp = self._call(self.urls["authBaseUrl"] + "/Auth/refresh-token", {"refreshtoken": self.refresh_token})
        if st == 200 and resp.get("access_token"):
            with self.lock:
                self.token = resp["access_token"]
                self.refresh_token = resp.get("refresh_token") or self.refresh_token
                self.token_expiry = time.time() + float(resp.get("expires_in") or 3600)
            log("IOTC", "token refreshed")
        else:
            log("IOTC", f"refresh failed ({st}), logging in again")
            self.login()

    def ensure(self):
        if not self.token or time.time() > self.token_expiry - 1800:
            if self.token:
                self.refresh()
            else:
                self.login()

    def get(self, service, path, body=None, method=None):
        """Authenticated call; one retry after a fresh login on 401."""
        self.ensure()
        for attempt in (1, 2):
            st, resp = self._call(self.urls[service] + path, body, {"Authorization": "Bearer " + self.token}, method)
            if st == 401 and attempt == 1:
                log("IOTC", "401, re-login")
                self.login()
                continue
            return st, resp
        return st, resp

    # ---- the calls the site needs
    def device(self, duid):
        st, r = self.get("deviceBaseUrl", "/Device/uniqueId/" + urllib.parse.quote(duid))
        d = r.get("data") or []
        return (d[0] if isinstance(d, list) and d else d) if st == 200 else None

    def _check(self, what, st, r):
        if st != 200:
            log("IOTC", f"{what} -> {st} {str(r.get('message') if isinstance(r, dict) else r)[:120]}")

    def latest(self, device_guid):
        st, r = self.get("telemetryBaseUrl", f"/Telemetry/device/{device_guid}")
        self._check("latest", st, r)
        return r.get("data") or [] if st == 200 else []

    def recent(self, duid, attrs, points=40):
        st, r = self.get("telemetryBaseUrl", f"/Telemetry/device/{urllib.parse.quote(duid)}/recent/{points}",
                         {"filterAttrs": list(attrs)})
        self._check("recent", st, r)
        return ((r.get("data") or {}).get("feed") or []) if st == 200 else []

    def history(self, duid, attrs, from_utc, to_utc, max_pages=40):
        """Today's messages from /IOTCONNECT (attribute-history, newest first, 500 per page)."""
        out, token = [], None
        for _ in range(max_pages):
            body = {"fromDate": from_utc.strftime("%Y-%m-%d %H:%M:%S"), "toDate": to_utc.strftime("%Y-%m-%d %H:%M:%S"),
                    "attributes": list(attrs), "pageSize": 500}
            if token:
                body["continuationToken"] = token
            st, r = self.get("telemetryBaseUrl", f"/Telemetry/device/{urllib.parse.quote(duid)}/attribute-history", body, method="POST")
            self._check("history", st, r)
            if st != 200:
                break
            data = r.get("data") or {}
            feed = data.get("feed") or []
            out.extend(feed)
            token = data.get("continuationToken")
            if not token or not feed:
                break
        return out

    def commands(self, template_guid):
        st, r = self.get("deviceBaseUrl", f"/template-command/{template_guid}?pageSize=200")
        return r.get("data") or [] if st == 200 else []

    def streaming_kit(self, duid):
        """The viewer kit for the device's KVS WebRTC channel: what the portal's Video Streaming tab uses."""
        st, r = self.get("deviceBaseUrl", "/Device/client-streaming-url?" + urllib.parse.urlencode({"uniqueId": duid, "isWebRTC": "true"}))
        return ((r.get("data") or {}).get("webRtcChannelDetailsResponse") if st == 200 else None) or None

    def send(self, device_guid, command_guid, param):
        st, r = self.get("deviceBaseUrl", f"/template-command/device/{device_guid}/send",
                         {"commandGuid": command_guid, "parameterValue": param or ""}, method="POST")
        return st, r.get("message") or ("sent" if st == 200 else f"error {st}")


def presign_kvs_wss(wss_endpoint, region, channel_arn, client_id, creds, expires=299):
    """SigV4 query-string presign of the KVS signaling WebSocket URL for a viewer (what the KVS
    WebRTC JS SDK's SigV4RequestSigner does), with the standard library only."""
    host = urllib.parse.urlparse(wss_endpoint).netloc
    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date, datestamp = now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y%m%d")
    scope = f"{datestamp}/{region}/kinesisvideo/aws4_request"
    params = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-ChannelARN": channel_arn,
        "X-Amz-ClientId": client_id,
        "X-Amz-Credential": f"{creds['accessKeyId']}/{scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires),
        "X-Amz-Security-Token": creds["sessionToken"],
        "X-Amz-SignedHeaders": "host",
    }
    q = lambda v: urllib.parse.quote(str(v), safe="-_.~")
    canonical_qs = "&".join(f"{q(k)}={q(v)}" for k, v in sorted(params.items()))
    empty_hash = hashlib.sha256(b"").hexdigest()
    canonical_request = f"GET\n/\n{canonical_qs}\nhost:{host}\n\nhost\n{empty_hash}"
    string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    k = ("AWS4" + creds["secretAccessKey"]).encode()
    for part in (datestamp, region, "kinesisvideo", "aws4_request"):
        k = hmac.new(k, part.encode(), hashlib.sha256).digest()
    signature = hmac.new(k, string_to_sign.encode(), hashlib.sha256).hexdigest()
    return f"wss://{host}/?{canonical_qs}&X-Amz-Signature={signature}"


# --------------------------------------------------------------------------
# state: polled telemetry per device
# --------------------------------------------------------------------------

HISTORY_ATTRS = ["vlm_latency_ms", "vlm_prefill_ms", "vlm_tok_s", "people_vlm", "alerts_active", "occupancy", "visitors_in", "gpu_load_pct"]
DAY_ATTRS = ["ts", "scene_caption", "people_vlm", "engagement", "question", "answer", "alerts_active", "alert_text", "vlm_cycle"]
DAY_QUESTION = re.compile(r"\b(today|so far|earlier|history|have you seen|did you see|have seen|how many (people|visitors|questions)|busiest|this morning|this afternoon|since)\b", re.I)


class DayLog:
    """What the camera reported today, rebuilt from /IOTCONNECT's history and kept current from the
    polling. The VLM only ever sees one frame, so "what have you seen today" is answered here."""

    def __init__(self, tz):
        self.tz = tz
        self.lock = threading.Lock()
        self.frames = []        # (ts, caption, people, engagement)
        self.questions = []     # (ts, question, answer)
        self.alerts = []        # (ts, alert_text)
        self.seen_ts = set()
        self.day = None
        self.loaded = False

    def local(self, ts):
        return datetime.datetime.fromtimestamp(ts, self.tz)

    def day_start(self, now=None):
        now = now or datetime.datetime.now(self.tz)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    def reset_if_new_day(self):
        today = self.day_start().date()
        if self.day != today:
            with self.lock:
                self.frames, self.questions, self.alerts, self.seen_ts = [], [], [], set()
                self.day, self.loaded = today, False
            return True
        return False

    def add(self, attr, when_iso=None):
        """One telemetry message's attributes (dict). Deduplicated on the device's ts."""
        try:
            ts = int(float(attr.get("ts") or 0))
        except (TypeError, ValueError):
            ts = 0
        if not ts and when_iso:
            ts = int(datetime.datetime.fromisoformat(when_iso.replace("Z", "+00:00")).timestamp())
        if not ts or attr.get("type") == "ack":
            return
        with self.lock:
            if ts in self.seen_ts or self.local(ts) < self.day_start():
                return
            self.seen_ts.add(ts)
            cap = str(attr.get("scene_caption") or "").strip()
            if cap:
                try:
                    people = int(attr.get("people_vlm") or 0)
                except (TypeError, ValueError):
                    people = 0
                self.frames.append((ts, cap, people, str(attr.get("engagement") or "")))
            q, a = str(attr.get("question") or "").strip(), str(attr.get("answer") or "").strip()
            if q and (not self.questions or self.questions[-1][1] != q or (a and self.questions[-1][2] != a)):
                if self.questions and self.questions[-1][1] == q:
                    self.questions[-1] = (self.questions[-1][0], q, a)
                else:
                    self.questions.append((ts, q, a))
            try:
                active = int(attr.get("alerts_active") or 0)
            except (TypeError, ValueError):
                active = 0
            if active and (not self.alerts or ts - self.alerts[-1][0] > 60 or self.alerts[-1][1] != attr.get("alert_text")):
                self.alerts.append((ts, str(attr.get("alert_text") or "")))

    def _sorted(self):
        return sorted(self.frames), sorted(self.questions), sorted(self.alerts)

    def report(self):
        with self.lock:
            frames, questions, alerts = self._sorted()
        fmt = lambda ts: self.local(ts).strftime("%H:%M")
        n = len(frames)
        if not n:
            return {"loaded": self.loaded, "looks": 0, "summary": "Nothing recorded yet today.", "scenes": [], "questions": [], "alerts": [], "hours": [], "visits": []}
        first, last = frames[0][0], frames[-1][0]
        with_people = [f for f in frames if f[2] > 0]
        peak = max(frames, key=lambda f: f[2])
        # visits: runs of frames with people, split by gaps over 2 minutes
        visits = []
        for f in with_people:
            if visits and f[0] - visits[-1]["end"] <= 120:
                visits[-1]["end"] = f[0]
                visits[-1]["max"] = max(visits[-1]["max"], f[2])
                visits[-1]["frames"] += 1
            else:
                visits.append({"start": f[0], "end": f[0], "max": f[2], "frames": 1})
        # scenes: consecutive runs of the same caption (what the day looked like)
        scenes = []
        for ts, cap, people, eng in frames:
            key = re.sub(r"[^a-z ]", "", cap.lower())[:60]
            if scenes and scenes[-1]["key"] == key:
                scenes[-1]["end"] = ts
                scenes[-1]["n"] += 1
                scenes[-1]["people"] = max(scenes[-1]["people"], people)
            else:
                scenes.append({"key": key, "caption": cap, "start": ts, "end": ts, "n": 1, "people": people})
        # the recurring scenes of the day, by time spent
        by_key = collections.Counter()
        label = {}
        for sc in scenes:
            by_key[sc["key"]] += sc["n"]
            label.setdefault(sc["key"], sc["caption"])
        top = [(label[k], c) for k, c in by_key.most_common(3)]
        hours = collections.OrderedDict()
        for h in range(self.local(first).hour, self.local(last).hour + 1):
            hours[h] = {"hour": h, "looks": 0, "people": 0}
        for ts, cap, people, eng in frames:
            h = self.local(ts).hour
            hours.setdefault(h, {"hour": h, "looks": 0, "people": 0})
            hours[h]["looks"] += 1
            hours[h]["people"] += 1 if people > 0 else 0
        busiest = max(hours.values(), key=lambda x: x["people"]) if hours else None
        parts = [f"Since {fmt(first)} I have looked {n} times."]
        if with_people:
            parts.append(f"I saw people in {len(with_people)} of them ({100 * len(with_people) // n}%), in {len(visits)} separate visit{'s' if len(visits) != 1 else ''}, "
                         f"at most {peak[2]} at once ({fmt(peak[0])}).")
            if busiest and busiest["people"]:
                parts.append(f"The busiest hour was {busiest['hour']:02d}:00 to {busiest['hour'] + 1:02d}:00.")
        else:
            parts.append("I have not seen anyone yet.")
        if questions:
            parts.append(f"Visitors asked {len(questions)} question{'s' if len(questions) != 1 else ''}, the last one: \"{questions[-1][1]}\".")
        if alerts:
            parts.append(f"Alert rules fired {len(alerts)} time{'s' if len(alerts) != 1 else ''}.")
        if top:
            parts.append("Most of the day looked like: " + "; ".join(f"\"{c}\"" for c, _ in top[:2]) + ".")
        return {
            "loaded": self.loaded, "looks": n, "first": fmt(first), "last": fmt(last),
            "with_people": len(with_people), "peak": peak[2], "peak_at": fmt(peak[0]),
            "visits": [{"start": fmt(v["start"]), "end": fmt(v["end"]), "max": v["max"], "minutes": max(1, (v["end"] - v["start"]) // 60)} for v in visits[-12:]],
            "scenes": [{"start": fmt(sc["start"]), "end": fmt(sc["end"]), "caption": sc["caption"], "n": sc["n"], "people": sc["people"]} for sc in scenes[-40:]][::-1],
            "top": [{"caption": c, "n": k} for c, k in top],
            "questions": [{"at": fmt(ts), "q": q, "a": a} for ts, q, a in questions[-20:]][::-1],
            "alerts": [{"at": fmt(ts), "text": t} for ts, t in alerts[-20:]][::-1],
            "hours": list(hours.values()),
            "summary": " ".join(parts),
        }

    def answer(self, question):
        """A plain answer about the day, for questions the camera itself cannot answer."""
        r = self.report()
        q = question.lower()
        if not r["looks"]:
            return "I have not recorded anything yet today."
        if re.search(r"how many (people|visitors|persons)|anyone|anybody|seen people", q):
            if not r["with_people"]:
                return f"Nobody yet. I have looked {r['looks']} times since {r['first']} and have not seen a person."
            return (f"I saw people in {r['with_people']} of my {r['looks']} looks since {r['first']}, in {len(r['visits'])} separate visits, "
                    f"at most {r['peak']} at once at {r['peak_at']}.")
        if re.search(r"question", q):
            return (f"{len(r['questions'])} questions today. " + " ".join(f"At {x['at']}: \"{x['q']}\" ({x['a'] or 'no answer'})." for x in r["questions"][:3])) if r["questions"] else "No questions yet today."
        if re.search(r"alert", q):
            return (f"Alerts fired {len(r['alerts'])} times today, last at {r['alerts'][0]['at']}: {r['alerts'][0]['text'] or 'rule matched'}.") if r["alerts"] else "No alert has fired today."
        if re.search(r"busiest|busy|peak", q):
            h = max(r["hours"], key=lambda x: x["people"]) if r["hours"] else None
            return f"The busiest hour was {h['hour']:02d}:00 to {h['hour'] + 1:02d}:00, with people in {h['people']} of {h['looks']} looks." if h and h["people"] else "No busy period yet; I have not seen people."
        return r["summary"]
ALLOWED_COMMANDS = {"ask", "set_alert", "clear_alerts", "vlm_pause", "vlm_resume", "vlm_status", "vlm_ping",
                    "vlm_interval", "vlm_max_tokens", "vlm_zoom", "vlm_focus", "status", "ping", "reset_counts", "preset booth"}


class Booth:
    def __init__(self, api, duids, poll_s=3.0):
        self.api = api
        self.duids = duids
        self.poll_s = poll_s
        self.lock = threading.Lock()
        self.devices = {d: {"id": d, "info": {}, "attrs": {}, "latest": {}, "names": [], "history": [], "commands": {}, "error": "", "polled": 0} for d in duids}
        self.events = []   # recent commands sent / answers, shown on the page
        self.started = int(time.time())
        self.kits = {}     # duid -> (fetched_at, kit) for the KVS viewer
        self.tz = ZoneInfo(os.environ.get("BOOTH_TZ", "America/Chicago")) if ZoneInfo else datetime.timezone.utc
        self.days = {d: DayLog(self.tz) for d in duids}
        self.local_qa = {}  # duid -> {"q","a","t"} answered from the day log

    def start(self):
        threading.Thread(target=self._loop, name="poll", daemon=True).start()

    def _loop(self):
        n = 0
        while True:
            for duid in self.duids:
                try:
                    self._poll(duid, full=(n % 10 == 0))
                except Exception as e:
                    with self.lock:
                        self.devices[duid]["error"] = f"{type(e).__name__}: {e}"
                    log("POLL", f"{duid}: {e}")
            n += 1
            time.sleep(self.poll_s)

    def _backfill(self, duid):
        """Today's messages from /IOTCONNECT, once per day (and after a restart)."""
        day = self.days[duid]
        start = day.day_start().astimezone(datetime.timezone.utc)
        now = datetime.datetime.now(datetime.timezone.utc)
        items = self.api.history(duid, DAY_ATTRS, start, now)
        for it in items:
            day.add(it.get("attr") or {}, it.get("dTime"))
        day.loaded = True
        log("DAY", f"{duid}: {len(items)} messages since local midnight, {len(day.frames)} looks, {len(day.questions)} questions")

    def _poll(self, duid, full):
        dev = self.devices[duid]
        day = self.days[duid]
        if day.reset_if_new_day() or not day.loaded:
            try:
                self._backfill(duid)
            except Exception as e:
                log("DAY", f"backfill failed: {e}")
        if full or not dev["info"]:
            info = self.api.device(duid)
            if info:
                keep = {k: info.get(k) for k in ("guid", "uniqueId", "displayName", "deviceTemplateGuid", "deviceTemplateName",
                                                   "isConnected", "lastActivityDate", "isActive")}
                with self.lock:
                    dev["info"] = keep
                if not dev["commands"] or full:   # commands can be added to the template while we run
                    cmds = self.api.commands(keep["deviceTemplateGuid"])
                    with self.lock:
                        dev["commands"] = {c["command"]: {"guid": c["guid"], "name": c["name"], "param": c.get("requiredParam")} for c in cmds}
        guid = dev["info"].get("guid")
        if not guid:
            return
        # The "latest telemetry" endpoint returns inconsistent, minutes-old snapshots for this device
        # (each attribute from whichever message a cache processed last), while the recent-history
        # feed is in order and within a second of the device. So: attribute names and a fallback
        # value from "latest" (refreshed slowly), the live state from the newest history message,
        # chosen by the device's own timestamp.
        if full or not dev.get("names"):
            latest = {}
            for a in self.api.latest(guid):
                latest[a["attributeName"]] = {"v": a.get("attributeValue"), "t": a.get("deviceUpdatedDate"), "name": a.get("displayName") or a["attributeName"]}
            with self.lock:
                dev["names"] = sorted(latest)
                dev["latest"] = latest
        names = dev.get("names") or []
        attrs = dict(dev.get("latest") or {})
        newest, newest_ts = None, -1.0
        for item in self.api.recent(duid, names, 10):   # the endpoint accepts 10 to 500 points
            d = (item.get("data") or {}).get("d") or {}
            day.add(d, item.get("time"))
            try:
                ts = float(d.get("ts") or 0)
            except (TypeError, ValueError):
                ts = 0.0
            if not ts:
                ts = time.mktime(time.strptime(item.get("time", "")[:19], "%Y-%m-%dT%H:%M:%S")) if item.get("time") else 0.0
            if ts > newest_ts and d.get("type") != "ack":
                newest, newest_ts = (item, d), ts
        if newest:
            item, d = newest
            for k, v in d.items():
                attrs[k] = {"v": v, "t": item.get("time"), "name": (attrs.get(k) or {}).get("name") or k}
        with self.lock:
            dev["attrs"] = attrs
            dev["error"] = ""
            dev["polled"] = int(time.time())
        if full:
            feed = self.api.recent(duid, HISTORY_ATTRS, 60)
            hist = []
            for item in reversed(feed):
                d = ((item.get("data") or {}).get("d") or {})
                d["t"] = item.get("time")
                hist.append(d)
            with self.lock:
                dev["history"] = hist

    def today(self, duid):
        day = self.days.get(duid)
        return day.report() if day else {}

    def state(self):
        with self.lock:
            devs = json.loads(json.dumps(self.devices))
            ev = list(self.events[-12:])
            local_qa = dict(self.local_qa)
        for duid, d in devs.items():
            d["local_qa"] = local_qa.get(duid)
        for d in devs.values():
            d["commands"] = sorted(c for c in d["commands"] if c in ALLOWED_COMMANDS)
            d.pop("latest", None)
            d.pop("names", None)
        return {"devices": devs, "events": ev, "now": int(time.time()), "started": self.started}

    def kvs_viewer(self, duid):
        """Everything a browser needs to watch the device's KVS WebRTC channel, from /IOTCONNECT's
        client-streaming-url: a presigned signaling URL (the viewer credentials stay here) and the
        TURN servers. Cached briefly; the TURN passwords have a 5-minute life."""
        now = time.time()
        with self.lock:
            cached = self.kits.get(duid)
        if not cached or now - cached[0] > 120:
            kit = self.api.streaming_kit(duid)
            if not kit or not kit.get("channelARN") or not kit.get("viewerCredentials"):
                return None
            with self.lock:
                self.kits[duid] = (now, kit)
        else:
            kit = cached[1]
        region = re.search(r"arn:aws:kinesisvideo:([a-z0-9-]+):", kit["channelARN"]).group(1)
        client_id = "BOOTH_" + hashlib.sha1(os.urandom(8)).hexdigest()[:8]
        ice = [{"urls": [f"stun:stun.kinesisvideo.{region}.amazonaws.com:443"]}]
        for srv in kit.get("iceServers") or []:
            ice.append({"urls": srv.get("uris") or srv.get("urls") or [], "username": srv.get("username"), "credential": srv.get("password")})
        return {"wss": presign_kvs_wss(kit["wssEndpoint"], region, kit["channelARN"], client_id, kit["viewerCredentials"]),
                "iceServers": ice, "clientId": client_id, "channel": kit["channelARN"].split("/")[-2]}

    def command(self, duid, command, param):
        dev = self.devices.get(duid)
        if not dev:
            return 404, "unknown device"
        if command not in ALLOWED_COMMANDS:
            return 403, f"command '{command}' is not enabled on the booth page"
        if command == "ask" and DAY_QUESTION.search(param or ""):
            # about the day, not the frame: answered from the log of what went to /IOTCONNECT
            ans = self.days[duid].answer(param)
            with self.lock:
                self.local_qa[duid] = {"q": param, "a": ans, "t": int(time.time())}
                self.events.append({"t": int(time.time()), "cmd": "ask", "param": param, "ok": True, "msg": "answered from today's log"})
                self.events = self.events[-50:]
            log("CMD", f"{duid} ask (day log) {param!r}")
            return 200, "answered from today's log"
        c = dev["commands"].get(command)
        if not c:
            return 404, f"command '{command}' is not in the device template"
        st, msg = self.api.send(dev["info"]["guid"], c["guid"], param)
        with self.lock:
            self.events.append({"t": int(time.time()), "cmd": command, "param": param, "ok": st == 200, "msg": msg})
            self.events = self.events[-50:]
        log("CMD", f"{duid} {command} {param!r} -> {st} {msg}")
        return st, msg


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def make_handler(booth, cfg):
    page = open(os.path.join(HERE, "booth_site.html"), "rb").read()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, ctype, body, extra=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            p = urllib.parse.urlparse(self.path).path
            if p in ("/", "/index.html"):
                return self._send(200, "text/html; charset=utf-8", page)
            if p == "/api/state":
                s = booth.state()
                s["title"], s["subtitle"], s["live"] = cfg["title"], cfg["subtitle"], bool(cfg["live"])
                return self._send(200, "application/json", json.dumps(s).encode())
            if p == "/api/today":
                duid = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("device", [booth.duids[0]])[0]
                return self._send(200, "application/json", json.dumps(booth.today(duid)).encode())
            if p == "/api/kvs":
                duid = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("device", [booth.duids[0]])[0]
                try:
                    kit = booth.kvs_viewer(duid)
                except Exception as e:
                    log("KVS", f"viewer kit failed: {e}")
                    kit = None
                return self._send(200, "application/json", json.dumps(kit or {"error": "no KVS WebRTC channel for this device"}).encode())
            if p == "/api/config.json":
                return self._send(200, "application/json", json.dumps({"title": cfg["title"], "subtitle": cfg["subtitle"], "live": bool(cfg["live"])}).encode())
            if p.startswith("/live/") and cfg["live"]:
                return self._proxy(cfg["live"].rstrip("/") + "/" + p[len("/live/"):])
            self.send_error(404)

        def _proxy(self, url):
            """Stream the narrator's live view (MJPEG / snapshot / state) through this server."""
            try:
                with urllib.request.urlopen(url, timeout=10) as r:
                    self.send_response(200)
                    self.send_header("Content-Type", r.headers.get("Content-Type", "application/octet-stream"))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    while True:
                        chunk = r.read(16384)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as e:
                try:
                    self.send_error(502, f"live view unavailable: {e}")
                except Exception:
                    pass

        def do_POST(self):
            p = urllib.parse.urlparse(self.path).path
            if p != "/api/cmd":
                return self.send_error(404)
            n = int(self.headers.get("Content-Length") or 0)
            try:
                req = json.loads(self.rfile.read(n).decode() or "{}")
                duid = req.get("device") or booth.duids[0]
                cmd = str(req.get("command", "")).strip()
                param = str(req.get("param", "")).strip()[:300]
                st, msg = booth.command(duid, cmd, param)
            except Exception as e:
                st, msg = 400, f"bad request: {e}"
            return self._send(200, "application/json", json.dumps({"ok": st == 200, "status": st, "message": msg}).encode())

    return H


def main():
    env = os.environ.get
    for k in ("IOTC_USERNAME", "IOTC_PASSWORD", "IOTC_SOLUTION_KEY"):
        if not env(k):
            raise SystemExit(f"{k} is not set (see the docstring / /etc/default/booth-site)")
    cfg = {"title": env("BOOTH_TITLE", "Ask the camera"),
           "subtitle": env("BOOTH_SUBTITLE", "Advantech iCAM-540 + NVIDIA Jetson Orin + /IOTCONNECT"),
           "live": env("BOOTH_LIVE_VIEW", "http://127.0.0.1:8088"),
           "port": int(env("BOOTH_PORT", "8090"))}
    duids = [d.strip() for d in env("IOTC_DEVICE_IDS", "").split(",") if d.strip()]
    if not duids:
        raise SystemExit("IOTC_DEVICE_IDS is not set")
    api = IotcApi(env("IOTC_USERNAME"), env("IOTC_PASSWORD"), env("IOTC_SOLUTION_KEY"), env("IOTC_PLATFORM", "aws"), env("IOTC_ENV", "poc"))
    api.login()
    booth = Booth(api, duids, float(env("BOOTH_POLL_S", "3")))
    booth.start()
    srv = ThreadingHTTPServer(("0.0.0.0", cfg["port"]), make_handler(booth, cfg))
    srv.daemon_threads = True
    log("WEB", f"booth site on http://0.0.0.0:{cfg['port']}/  devices {duids}  live view {cfg['live'] or 'off'}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
