# -*- coding: utf-8 -*-
"""MopChannels: builds my own live-channel list from the channel table of the Fishenzon "Idan+" Kodi addon.

Source:  https://github.com/Fishenzon/repo  (plugin.video.idanplus/channels.json, 84 TV + radio channels)
Output:  channels.json  - every channel with its resolved stream URL, headers, logo and status
         channel.json   - the same channels in the MopTV format (categories > sub_categories > channels)

Each channel in the source carries a "module" that says how its link is obtained. This script re-implements the
read-only part of each module (open a page or an API and pick the stream URL out of it). Channels of the "keshet"
module (mako.co.il) need a per-view ticket from mako and are kept with status "needs_ticket", unresolved.

Run:  python mopchannels.py            (GitHub Actions runs it on a schedule and on demand)
      python mopchannels.py --offline  (rebuild channel.json from the existing channels.json, no network)
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_URL = "https://raw.githubusercontent.com/Fishenzon/repo/master/plugin.video.idanplus/channels.json"
FULL_FILE = os.path.join(HERE, "channels.json")
MOPTV_FILE = os.path.join(HERE, "channel.json")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"
TIMEOUT = 20
ISRAEL = timezone(timedelta(hours=2))

session = requests.Session()
session.headers["User-Agent"] = UA


def log(msg):
    print(msg, flush=True)


def get(url, headers=None, kind="text"):
    """GET `url`; text / json / the final URL after redirects. None on any failure."""
    try:
        r = session.get(url, headers=headers or {}, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code >= 400:
            log("    HTTP {0} for {1}".format(r.status_code, url))
            return None
        if kind == "json":
            return r.json()
        if kind == "url":
            return r.url
        return r.text
    except Exception as ex:
        log("    error for {0}: {1}".format(url, ex))
        return None


def check_stream(url, headers):
    """True when the stream URL answers (any 2xx/3xx). Streams may be geo-locked for the runner, so a failure here
    marks the channel 'unreachable' but never drops it."""
    try:
        r = session.get(url, headers=headers, timeout=TIMEOUT, stream=True)
        r.close()
        return r.status_code < 400
    except Exception:
        return False


def fix_scheme(link):
    if link.startswith("//"):
        return "http:" + link
    if "://" not in link:
        return "http://" + link
    return link


# ---------------------------------------------------------------- resolvers (one per source module) ----------

def resolve_tv(ld):
    headers = {"User-Agent": UA}
    link = ld["link"]
    if ld.get("regex"):
        text = get(link, headers)
        found = re.compile(ld["regex"], ld.get("flags", 0)).findall(text or "")
        link = found[0] if found else ld.get("direct", link)
    if ld.get("referer"):
        headers["Referer"] = ld["referer"]
    return fix_scheme(link), headers


def resolve_radio(ld):
    headers = {"User-Agent": UA}
    link = ld["link"]
    if ld.get("regex"):
        text = get(link, headers)
        found = re.compile(ld["regex"], ld.get("flags", 0)).findall(text or "")
        if not found:
            raise ValueError("regex found nothing")
        link = found[0]
    return fix_scheme(link), headers


def resolve_kan(ld):
    return ld["link"], {"User-Agent": UA, "Referer": "https://www.kan.org.il"}


def resolve_reshet(ld):
    headers = {"User-Agent": UA}
    if ld.get("referer"):
        headers["Referer"] = ld["referer"]
    return ld["link"], headers


def resolve_14tv(ld):
    link = ld["link"]
    data = get(ld["ch"], {"x-tenant-id": "channel14", "User-Agent": UA}, "json")
    if isinstance(data, dict) and (data.get("vod") or {}).get("hlsStream"):
        link = data["vod"]["hlsStream"]
    return link, {"User-Agent": UA, "Referer": "https://vod.c14.co.il/"}


def resolve_hidabroot(ld):
    headers = {"User-Agent": UA}
    text = get(ld["link"], headers)
    found = re.compile(r'<source\s*?src="(.*?)"', re.S).findall(text or "")
    if not found:
        raise ValueError("no <source> on the page")
    return found[0], headers


def resolve_glz(ld):
    headers = {"User-Agent": UA}
    link = ld["live"]
    data = get("https://glz.co.il/umbraco/api/player/getplayerdata?rootId={0}".format(ld["rootId"]), headers, "json")
    file_url = ((data or {}).get("liveBroadcast") or {}).get("fileUrl") if isinstance(data, dict) else None
    if file_url:
        final = get(file_url, headers, "url")
        if final:
            link = final
    return link, headers


def resolve_sport5(ld):
    radio = "https://radio.sport5.co.il"
    headers = {"User-Agent": UA, "Referer": radio}
    link = ld["link"]
    data = get("{0}/data/data.json?v={1}".format(radio, int(time.time() * 1000)), headers, "json")
    if isinstance(data, dict) and data.get(ld["ch"]):
        link = str(data[ld["ch"]]).replace("https://nekot.sport5.co.il:10000?", "")
    return link, headers


def resolve_99fm(ld):
    return ld["link"], {"User-Agent": UA}


def resolve_100fm(ld):
    headers = {"User-Agent": UA}
    link = ld["link"]
    data = get(ld["ch"], headers, "json")
    try:
        link = data["stations"][0]["audio"]
    except Exception:
        pass
    return link, headers


def resolve_1064fm(ld):
    headers = {"User-Agent": UA}
    link = ld["link"]
    text = get(ld["ch"], headers)
    found = re.compile(r'"webapp\.broadcast_link":"(.*?)"').findall(text or "")
    if found:
        link = found[0].replace("\\u002F", "/")
    return link, headers


def resolve_keshet(ld):
    """mako.co.il streams play only with a short-lived ticket that mako issues per view; not resolved here."""
    host = ld.get("host", "https://mako-streaming.akamaized.net")
    link = ld["link"] if ld["link"].startswith("http") else host + ld["link"]
    return link, {"User-Agent": UA}


RESOLVERS = {
    "tv": resolve_tv, "radio": resolve_radio, "kan": resolve_kan, "reshet": resolve_reshet, "14tv": resolve_14tv,
    "hidabroot": resolve_hidabroot, "glz": resolve_glz, "sport5": resolve_sport5, "99fm": resolve_99fm,
    "100fm": resolve_100fm, "1064fm": resolve_1064fm, "keshet": resolve_keshet,
}
NEEDS_TICKET = {"keshet"}


# ---------------------------------------------------------------- build ---------------------------------------

def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def resolve_all(source, previous):
    """Every channel of `source` with its resolved URL. A channel whose resolution fails keeps the URL it had in the
    previous run (status 'stale'), so one bad run never empties the list."""
    prev = {c["id"]: c for c in (previous or {}).get("channels", [])}
    now = datetime.now(ISRAEL).strftime("%d.%m.%Y %H:%M")
    out = []
    for cid, ch in source.items():
        ld = ch.get("linkDetails") or {}
        module = ch.get("module", "tv")
        entry = {
            "id": cid, "name": ch.get("name", cid), "type": ch.get("type", "tv"), "module": module,
            "logo": ch.get("image", ""), "tvg_id": ch.get("tvgID", ""), "index": ch.get("index", 0),
            "source_link": ld.get("link", ""), "url": "", "headers": {}, "status": "", "checked": now,
        }
        resolver = RESOLVERS.get(module, resolve_tv)
        log("{0:16} {1:9} {2}".format(cid, module, ch.get("name", "")))
        try:
            url, headers = resolver(ld)
            entry["url"], entry["headers"] = url, headers
            if module in NEEDS_TICKET:
                entry["status"] = "needs_ticket"
            elif check_stream(url, headers):
                entry["status"] = "ok"
            else:
                entry["status"] = "unreachable"
        except Exception as ex:
            log("    resolve failed: {0}".format(ex))
            old = prev.get(cid)
            if old and old.get("url"):
                entry["url"], entry["headers"], entry["status"] = old["url"], old.get("headers", {}), "stale"
                entry["checked"] = old.get("checked", now)
            else:
                entry["url"], entry["headers"], entry["status"] = ld.get("link", ""), {"User-Agent": UA}, "failed"
        log("    -> {0}  {1}".format(entry["status"], entry["url"][:100]))
        out.append(entry)
    return out


def moptv_format(channels):
    """The MopTV channel.json layout: categories > sub_categories > channels {name, logo, url}.
    Ticket-only channels (mako) are left out because the URL alone does not play."""
    def items(kind):
        return [{"name": c["name"], "logo": c["logo"], "url": c["url"]}
                for c in channels if c["type"] == kind and c["status"] not in ("needs_ticket", "failed") and c["url"]]
    return {"categories": [
        {"id": "tv", "name": "טלוויזיה", "sub_categories": [{"id": "tv_israel", "name": "ישראל", "channels": items("tv")}]},
        {"id": "radio", "name": "רדיו", "sub_categories": [{"id": "radio_israel", "name": "ישראל", "channels": items("radio")}]},
    ]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="rebuild channel.json from channels.json without network")
    args = ap.parse_args()

    previous = load_json(FULL_FILE)
    if args.offline:
        if not previous:
            sys.exit("no channels.json to rebuild from")
        channels = previous["channels"]
    else:
        source = get(SOURCE_URL, kind="json")
        if not isinstance(source, dict) or not source:
            sys.exit("could not download the source channel list")
        channels = resolve_all(source, previous)
        summary = {}
        for c in channels:
            summary[c["status"]] = summary.get(c["status"], 0) + 1
        save_json(FULL_FILE, {
            "updated": datetime.now(ISRAEL).strftime("%d.%m.%Y %H:%M"),
            "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": SOURCE_URL, "count": len(channels), "summary": summary, "channels": channels,
        })
        log("\n{0} channels: {1}".format(len(channels), summary))
    save_json(MOPTV_FILE, moptv_format(channels))
    log("wrote channels.json and channel.json")


if __name__ == "__main__":
    main()
