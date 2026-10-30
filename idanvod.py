# -*- coding: utf-8 -*-
"""idanvod.py: VOD catalogs (programs, seasons, episodes, play URLs) built by running the Fishenzon "Idan+" Kodi addon
itself, without Kodi, on GitHub Actions.

How: addonloader.py downloads the newest addon from github.com/Fishenzon/repo, kodishim/ fakes the Kodi API, and this
script walks the addon's VOD menus exactly as Kodi would (folder -> folder -> playable item). Every list the addon
produces becomes JSON in the MopVOD format, so a TV app can read it straight from GitHub:

  vod.json            index: one entry per program {name, file, provider, episodes, seasons, updated}
  vod/<prov>_<id>.json  program: {categories:[{name, type:'vod', source, sub_categories:[{name, channels:[episodes]}]}]}
  episode: {name, logo, url, date, plot, id}

Play URLs: taken from the addon's own item when it is already a stream (Channel 14 / 9 / i24 master.m3u8, Sport5 src=),
built as a permanent Kaltura URL for Reshet 13 (the addon's resolved URL carries a signature that expires in a day),
and resolved by running the addon's play route for the rest (Sport1), remembering the result so it is not asked again.

Not crawled: mako (Keshet 12 / Channel 24: per-view ticket) and Kan (kan.org.il is already covered by the MopVOD repo).

Run:  python idanvod.py [--limit N] [--providers reshet,14tv,...] [--workers 1]
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import addonloader  # noqa: E402

INDEX_FILE = os.path.join(HERE, "vod.json")
VOD_DIR = os.path.join(HERE, "vod")
ISRAEL = timezone(timedelta(hours=2))
MAX_DEPTH = 5

# entry points inside the addon, per provider. "kinds" says how an episode's play URL is obtained.
PROVIDERS = {
    "reshet": {"name": "רשת 13", "start": "?mode=0&module=reshet&url=" + urllib.parse.quote("https://13tv.co.il/allshows/screen/1170108/", safe=""), "play": "kaltura"},
    "14tv": {"name": "עכשיו 14", "start": "?mode=0&module=14tv", "play": "param"},
    "9tv": {"name": "ערוץ 9", "start": "?mode=0&module=9tv", "play": "param"},
    "i24news": {"name": "i24news", "start": "?url=" + urllib.parse.quote("action=catalog&language=he", safe="") + "&mode=-1&module=i24news", "play": "param"},
    "sport5": {"name": "ספורט 5", "start": "?mode=0&module=sport5", "play": "sport5"},
    "sport1": {"name": "ספורט 1", "start": "?mode=0&module=sport1", "play": "resolve"},
}
KALTURA_URL = "https://cdnapisec.kaltura.com/p/2748741/sp/274874100/playManifest/entryId/{0}/format/applehttp/protocol/https/a.m3u8"


def log(msg):
    print(msg, flush=True)


def now_str():
    return datetime.now(ISRAEL).strftime("%Y-%m-%d %H:%M")


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def params(item):
    return dict(urllib.parse.parse_qsl(item["q"][1:], keep_blank_values=True))


def slug(text, n=60):
    text = re.sub(r"[^\w\-]+", "_", str(text), flags=re.U).strip("_")
    return text[:n] or "x"


def norm_date(text):
    """'25/10/2026' or '2026-10-25' -> '2026-10-25'; '' when unknown."""
    if not text:
        return ""
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if m:
        return "{0}-{1:0>2}-{2:0>2}".format(m.group(3), m.group(2), m.group(1))
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    return m.group(0) if m else ""


def date_from_name(name):
    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{2,4})", name or "")
    if not m:
        return ""
    y = m.group(3)
    y = ("20" + y) if len(y) == 2 else y
    return "{0}-{1:0>2}-{2:0>2}".format(y, m.group(2), m.group(1))


class Crawler:
    def __init__(self, addon, workers=1):
        self.addon = addon
        self.stats = {"requests": 0, "episodes": 0, "resolved": 0, "failed": 0}

    def run(self, q):
        self.stats["requests"] += 1
        return self.addon.run(q)

    # ---------------------------------------------------------------- play url per provider
    def play_url(self, provider, item, known):
        p = params(item)
        raw = urllib.parse.unquote_plus(p.get("url", ""))   # the addon quotes the value before urlencode: decode twice
        key = raw
        if key in known and known[key]:
            return known[key], key
        kind = PROVIDERS[provider]["play"]
        url = ""
        if kind == "kaltura":
            m = re.search(r"--kaltura--([^=]+)", raw)
            if m:
                url = KALTURA_URL.format(m.group(1))
        elif kind == "param":
            if raw.startswith("http"):
                url = raw
        elif kind == "sport5":
            m = re.search(r"[?&]src=([^&]+)", raw)
            url = urllib.parse.unquote(m.group(1)) if m else (raw if ".m3u8" in raw else "")
            if not url:
                kind = "resolve"
        if kind == "resolve" and not url:
            out = self.run(item["q"] + ("" if "moredata=" in item["q"] else "&moredata=best"))
            res = out.get("resolved")
            if res and res.get("url"):
                url = res["url"]
                self.stats["resolved"] += 1
        if not url:
            self.stats["failed"] += 1
        return url, key

    # ---------------------------------------------------------------- walk one program
    def episodes_of(self, items, provider, known, season_name):
        out = []
        for it in items:
            if not it["playable"]:
                continue
            url, key = self.play_url(provider, it, known)
            if not url:
                continue
            p = params(it)
            out.append({
                "name": it["name"], "logo": it["icon"] if it["icon"].startswith("http") else "",
                "url": url, "date": norm_date(it.get("date")) or date_from_name(it["name"]),
                "plot": it.get("plot", ""), "page": "", "id": key[:200], "season": season_name,
            })
            self.stats["episodes"] += 1
        return out

    def walk_program(self, provider, series_item, known):
        """Seasons (sub_categories) of one program. Folders under the program are seasons; a folder whose children are
        folders again (year > month, category > series) is flattened with a combined name."""
        subs = []
        root = self.run(series_item["q"])
        direct = self.episodes_of(root["items"], provider, known, "")
        if direct:
            subs.append({"name": "פרקים", "channels": direct})
        folders = [it for it in root["items"] if it["folder"]]
        stack = [(f, f["name"], 1) for f in folders]
        while stack:
            folder, title, depth = stack.pop(0)
            lv = self.run(folder["q"])
            eps = self.episodes_of(lv["items"], provider, known, title)
            if eps:
                subs.append({"name": title, "channels": eps})
            if depth < MAX_DEPTH:
                for sub in lv["items"]:
                    if sub["folder"]:
                        stack.append((sub, "{0} - {1}".format(title, sub["name"]), depth + 1))
        return subs

    def crawl_provider(self, provider, limit=None):
        cfg = PROVIDERS[provider]
        top = self.run(cfg["start"])
        series = [it for it in top["items"] if it["folder"]]
        if provider == "sport5":   # the module's first screen is "all programs" / "radio shows"; take the programs
            allp = [it for it in series if "כל התכניות" in it["name"]]
            if allp:
                series = [it for it in self.run(allp[0]["q"])["items"] if it["folder"]]
        if provider == "sport1":
            allp = [it for it in series if "כל התכניות" in it["name"]]
            if allp:
                series = [it for it in self.run(allp[0]["q"])["items"] if it["folder"]]
        if limit:
            series = series[:limit]
        log("{0}: {1} programs".format(cfg["name"], len(series)))
        if not series:
            raise RuntimeError("the site returned no programs (blocked for this server, or changed)")
        entries = []
        for i, s in enumerate(series, 1):
            p = params(s)
            sid = slug(p.get("url") or s["name"])
            fname = "vod/{0}_{1}.json".format(provider, sid)
            path = os.path.join(HERE, fname)
            old = load_json(path, {})
            known = {}
            for cat in old.get("categories", []):
                for sub in cat.get("sub_categories", []):
                    for ch in sub.get("channels", []):
                        if ch.get("id") and ch.get("url"):
                            known[ch["id"]] = ch["url"]
            try:
                subs = self.walk_program(provider, s, known)
            except Exception as ex:  # noqa: BLE001
                log("  ! {0}: {1}".format(s["name"], ex))
                subs = []
            if not subs and old:
                subs = old["categories"][0].get("sub_categories", [])   # keep what we had when the site answers nothing
            n_eps = sum(len(x["channels"]) for x in subs)
            if not subs:
                log("  - {0}: no episodes".format(s["name"]))
                continue
            data = {"categories": [{
                "name": "{0} - {1}".format(cfg["name"], s["name"]), "type": "vod", "source": provider, "program_url": p.get("url", ""),
                "series_id": sid, "logo": s["icon"] if s["icon"].startswith("http") else "", "plot": s.get("plot", ""),
                "updated": now_str(), "sub_categories": subs,
            }]}
            save_json(path, data)
            dates = sorted(ch["date"] for x in subs for ch in x["channels"] if ch.get("date"))
            entries.append({"name": s["name"], "provider": provider, "provider_name": cfg["name"], "file": fname, "logo": data["categories"][0]["logo"],
                            "episodes": n_eps, "seasons": len(subs), "updated": now_str(), "newest": dates[-1] if dates else "", "oldest": dates[0] if dates else ""})
            log("  {0}/{1} {2}: {3} seasons, {4} episodes".format(i, len(series), s["name"], len(subs), n_eps))
        return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="programs per provider (testing)")
    ap.add_argument("--providers", default=",".join(PROVIDERS), help="comma list of providers")
    args = ap.parse_args()
    addon_dir, ver, status = addonloader.ensure_addon(HERE, log=log)
    log("addon {0} ({1})".format(ver, status))
    if status == "missing":
        sys.exit("no addon available")
    addon = addonloader.Addon(addon_dir, os.path.join(HERE, "addon-data"))
    if not addon.load():
        sys.exit("addon failed to load")
    crawler = Crawler(addon)
    index = load_json(INDEX_FILE, {"name": "MopkodiChannels VOD", "sources": []})
    wanted = [p.strip() for p in args.providers.split(",") if p.strip() in PROVIDERS]
    kept = [s for s in index.get("sources", []) if s.get("provider") not in wanted]
    started = time.time()
    for prov in wanted:
        try:
            kept += crawler.crawl_provider(prov, args.limit or None)
        except Exception as ex:  # noqa: BLE001
            log("provider {0} failed: {1}".format(prov, ex))
            kept += [s for s in index.get("sources", []) if s.get("provider") == prov]
    order = list(PROVIDERS)
    kept.sort(key=lambda s: (order.index(s["provider"]) if s["provider"] in order else 99, s["name"]))
    save_json(INDEX_FILE, {"name": "MopkodiChannels VOD", "updated": now_str(), "addon_version": ver, "sources": kept})
    log("done in {0:.0f}s: {1} programs, {2}".format(time.time() - started, len(kept), crawler.stats))


if __name__ == "__main__":
    main()
