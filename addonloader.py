# -*- coding: utf-8 -*-
"""
טעינת התוסף "עידן+" של Fishenzon והרצתו בלי Kodi.

- ensure_addon(): מוריד מהריפו של Fishenzon ב-GitHub את הגרסה האחרונה של plugin.video.idanplus (לפי addons.xml)
  ומחלץ אותה לתיקייה addon\\ ליד ה-EXE. אם כבר יש את הגרסה הזו, לא מוריד שוב. בלי אינטרנט - משתמש במה שיש.
- Addon.run(query): מריץ את ניתוב התוסף (resources.main.route) עם שאילתת Kodi ("?mode=2" וכדומה),
  ומחזיר את הפריטים שהתוסף הוסיף לרשימה, או את כתובת הניגון שפתר.

הקוד של התוסף רץ כמו שהוא, מול "קודי מזויף" (kodishim). כל קריאה לתוסף נעולה: הקוד שלו משתמש ב-sys.argv
ובמשתנים גלובליים, ולא נכתב לריצה מקבילה.
"""
import io
import json
import os
import re
import shutil
import sys
import threading
import time
import traceback
import urllib.parse
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kodishim  # noqa: E402

ADDON_ID = "plugin.video.idanplus"
REPO_RAW = "https://raw.githubusercontent.com/Fishenzon/repo/master/"
PLUGIN_URL = "plugin://{0}/".format(ADDON_ID)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

_TAG_RE = re.compile(r"\[/?(?:COLOR[^\]]*|B|I|UPPERCASE|LOWERCASE|CAPITALIZE|LIGHT)\]", re.I)


def clean_label(text):
    """טקסט בלי תגיות העיצוב של Kodi ([COLOR ...], [B], [CR])."""
    if not text:
        return ""
    text = str(text).replace("[CR]", "\n")
    return _TAG_RE.sub("", text).strip()


def _fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def latest_version():
    """הגרסה האחרונה של התוסף לפי addons.xml בריפו של Fishenzon, או None בלי רשת."""
    try:
        text = _fetch(REPO_RAW + "addons.xml").decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return None
    m = re.search(r'<addon\s+id="{0}"[^>]*\bversion="([^"]+)"'.format(re.escape(ADDON_ID)), text)
    return m.group(1) if m else None


def installed_version(addon_dir):
    try:
        with open(os.path.join(addon_dir, "addon.xml"), encoding="utf-8") as f:
            m = re.search(r'<addon\s[^>]*\bversion="([^"]+)"', f.read(), re.S)
        return m.group(1) if m else None
    except OSError:
        return None


def ensure_addon(base_dir, force=False, log=print):
    """מוודא שתיקיית התוסף קיימת ומעודכנת. מחזיר (addon_dir, version, status) כאשר status הוא
    'updated' / 'current' / 'offline' / 'missing'."""
    addons_root = os.path.join(base_dir, "addon")
    addon_dir = os.path.join(addons_root, ADDON_ID)
    have = installed_version(addon_dir)
    latest = latest_version()
    if latest is None:
        return addon_dir, have, ("offline" if have else "missing")
    if have == latest and not force:
        return addon_dir, have, "current"
    log("downloading {0} {1} from Fishenzon repo...".format(ADDON_ID, latest))
    zip_url = "{0}zips/{1}/{1}-{2}.zip".format(REPO_RAW, ADDON_ID, latest)
    try:
        data = _fetch(zip_url, timeout=120)
        tmp_dir = addon_dir + ".new"
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(addons_root, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            root = ADDON_ID + "/"
            for member in z.infolist():
                name = member.filename
                if not name.startswith(root) or ".." in name:
                    continue
                target = os.path.join(tmp_dir, *name[len(root):].split("/"))
                if member.is_dir() or name.endswith("/"):
                    os.makedirs(target, exist_ok=True)
                    continue
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with z.open(member) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        if not os.path.isfile(os.path.join(tmp_dir, "addon.xml")):
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise ValueError("zip without addon.xml")
        if os.path.isdir(addon_dir):
            shutil.rmtree(addon_dir)
        os.replace(tmp_dir, addon_dir)
        return addon_dir, latest, "updated"
    except Exception as ex:  # noqa: BLE001
        log("addon download failed: {0}".format(ex))
        return addon_dir, have, ("offline" if have else "missing")


def _parse_resolved(listitem):
    """כתובת ניגון של Kodi: 'url|Header=value&Header2=value' -> כתובת + כותרות."""
    path = listitem.getPath() or ""
    headers = {}
    url = path
    if "|" in path:
        url, _, tail = path.rpartition("|")
        for k, v in urllib.parse.parse_qsl(tail, keep_blank_values=True):
            headers[k] = v
    kind = "direct"
    low = url.lower().split("?")[0]
    if ".m3u8" in low or "/livehls/" in low or "playlist.m3u8" in low or "/hls/" in low:
        kind = "hls"
    elif ".mpd" in low or "/livedash/" in low or "/dash/" in low:
        kind = "dash"
    elif listitem.getProperty("inputstream") == "inputstream.adaptive" and ".m3u8" not in low:
        kind = "dash" if ".livx" in low else kind
    return {
        "url": url, "headers": headers, "kind": kind,
        "name": clean_label(listitem.getLabel()), "icon": listitem.getArt("thumb") or listitem.getArt("icon") or "",
        "plot": clean_label(listitem.info.get("plot", "")),
        "adaptive": listitem.getProperty("inputstream") == "inputstream.adaptive",
    }


def _parse_item(url, listitem, is_folder):
    q = url[url.find("?"):] if "?" in url else ""
    params = dict(urllib.parse.parse_qsl(q[1:], keep_blank_values=True))
    info = listitem.info
    date = info.get("aired") or info.get("date") or info.get("premiered") or ""
    return {
        "name": clean_label(listitem.getLabel()),
        "q": q,
        "mode": params.get("mode", ""),
        "module": params.get("module", ""),
        "icon": listitem.getArt("thumb") or listitem.getArt("icon") or "",
        "plot": clean_label(info.get("plot", "")),
        "date": str(date) if date else "",
        "folder": bool(is_folder),
        "playable": listitem.getProperty("IsPlayable") == "true",
    }


class Addon:
    def __init__(self, addon_dir, profile_dir):
        self.addon_dir = addon_dir
        self.profile_dir = profile_dir
        self.lock = threading.Lock()
        self.main = None
        self.load_error = ""
        self.version = installed_version(addon_dir) or ""

    def load(self):
        kodishim.install(self.addon_dir, self.profile_dir)
        sys.argv = [PLUGIN_URL, "1", ""]
        try:
            import resources.main as main  # noqa: PLC0415  (הקוד של התוסף)
            self.main = main
            self.load_error = ""
        except Exception:  # noqa: BLE001
            self.load_error = traceback.format_exc()
            print("addon import failed:\n" + self.load_error, file=sys.stderr)
        return self.main is not None

    def run(self, query, timeout_note=""):
        """מריץ שאילתת Kodi של התוסף ומחזיר {'items': [...], 'resolved': {...} | None, 'notifications': [...]}."""
        if self.main is None and not self.load():
            return {"items": [], "resolved": None, "notifications": ["התוסף לא נטען: " + self.load_error.splitlines()[-1] if self.load_error else "התוסף לא נטען"], "error": self.load_error}
        if not query.startswith("?"):
            query = "?" + query
        with self.lock:
            kodishim.begin()
            sys.argv = [PLUGIN_URL, "1", query]
            started = time.time()
            error = ""
            try:
                self.main.route(query)
            except SystemExit:
                pass
            except Exception:  # noqa: BLE001
                error = traceback.format_exc()
                print("addon route failed for {0}:\n{1}".format(query, error), file=sys.stderr)
            items = [_parse_item(u, li, f) for (u, li, f) in kodishim.items()]
            res = kodishim.resolved()
            resolved = _parse_resolved(res[1]) if res and res[0] and res[1] is not None else None
            return {
                "items": items, "resolved": resolved, "notifications": list(kodishim.notifications()),
                "content": kodishim.content(), "seconds": round(time.time() - started, 2),
                "error": error.splitlines()[-1] if error else "",
            }


if __name__ == "__main__":
    # בדיקה מהשורה: python addonloader.py "?mode=2"   /   python addonloader.py "?url=ch_11&mode=10&module=kan"
    base = os.path.dirname(HERE)
    addon_dir, ver, status = ensure_addon(base)
    print("addon", ver, status, addon_dir)
    a = Addon(addon_dir, os.path.join(base, "addon-data"))
    out = a.run(sys.argv[1] if len(sys.argv) > 1 else "?mode=-1")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:6000])
