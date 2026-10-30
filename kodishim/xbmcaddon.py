# -*- coding: utf-8 -*-
"""xbmcaddon.Addon - מידע על התוסף והגדרותיו. ההגדרות: ברירות המחדל מ-resources/settings.xml,
ושינויים שהתוסף שומר (setSetting) נכתבים ל-settings.json בתיקיית הנתונים, ליד ה-EXE."""
import json
import os
import re
import threading

import kodishim as _shim

_lock = threading.Lock()
_cache = {}


def _settings_file():
    return os.path.join(_shim.PROFILE_DIR[0], "settings.json")


def _defaults():
    if "defaults" in _cache:
        return _cache["defaults"]
    defaults = {}
    path = os.path.join(_shim.ADDON_DIR[0], "resources", "settings.xml")
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for tag in re.findall(r"<setting\s[^>]*>", text):
            sid = re.search(r'\bid="([^"]+)"', tag)
            if not sid:
                continue
            default = re.search(r'\bdefault="([^"]*)"', tag)
            defaults[sid.group(1)] = default.group(1) if default else ""
    except OSError:
        pass
    _cache["defaults"] = defaults
    return defaults


def _user():
    if "user" in _cache:
        return _cache["user"]
    try:
        with open(_settings_file(), encoding="utf-8") as f:
            _cache["user"] = json.load(f)
    except (OSError, ValueError):
        _cache["user"] = {}
    return _cache["user"]


def _strings():
    """המחרוזות של התוסף לפי מזהה: msgctxt "#30400" -> msgid (הטקסט העברי נמצא ב-msgid)."""
    if "strings" in _cache:
        return _cache["strings"]
    strings = {}
    lang_dir = os.path.join(_shim.ADDON_DIR[0], "resources", "language")
    for sub in ("resource.language.he_il", "resource.language.en_gb", "English"):
        for name in ("strings.po",):
            path = os.path.join(lang_dir, sub, name)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                continue
            for m in re.finditer(r'msgctxt "#(\d+)"\s*\nmsgid "((?:[^"\\]|\\.)*)"\s*\nmsgstr "((?:[^"\\]|\\.)*)"', text):
                sid = int(m.group(1))
                if sid not in strings:
                    val = m.group(3) or m.group(2)
                    strings[sid] = val.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8") if "\\" in val else val
    _cache["strings"] = strings
    return strings


def _addon_xml():
    if "xml" in _cache:
        return _cache["xml"]
    info = {"version": "", "name": "", "id": "plugin.video.idanplus"}
    try:
        with open(os.path.join(_shim.ADDON_DIR[0], "addon.xml"), encoding="utf-8") as f:
            text = f.read()
        m = re.search(r'<addon\s[^>]*\bid="([^"]+)"[^>]*\bname="([^"]+)"[^>]*\bversion="([^"]+)"', text, re.S)
        if m:
            info = {"id": m.group(1), "name": m.group(2), "version": m.group(3)}
    except OSError:
        pass
    _cache["xml"] = info
    return info


class Addon:
    def __init__(self, id=None):  # noqa: A002
        self._id = id or _addon_xml()["id"]

    def getAddonInfo(self, key):
        key = key.lower()
        if key == "path":
            return _shim.ADDON_DIR[0]
        if key == "profile":
            return _shim.PROFILE_DIR[0]
        if key == "icon":
            return os.path.join(_shim.ADDON_DIR[0], "icon.png")
        if key == "fanart":
            return os.path.join(_shim.ADDON_DIR[0], "fanart.jpg")
        if key in ("version", "name", "id"):
            return _addon_xml()[key]
        if key == "author":
            return "Fishenzon"
        if key == "type":
            return "xbmc.python.pluginsource"
        return ""

    def getSetting(self, key):
        with _lock:
            user = _user()
            if key in user:
                return str(user[key])
            return _defaults().get(key, "")

    def getSettingBool(self, key):
        return self.getSetting(key).lower() == "true"

    def getSettingInt(self, key):
        try:
            return int(float(self.getSetting(key) or 0))
        except ValueError:
            return 0

    def getSettingNumber(self, key):
        try:
            return float(self.getSetting(key) or 0)
        except ValueError:
            return 0.0

    def getSettingString(self, key):
        return self.getSetting(key)

    def setSetting(self, id, value):  # noqa: A002
        if isinstance(value, bool):
            value = "true" if value else "false"
        with _lock:
            user = _user()
            user[id] = str(value)
            try:
                os.makedirs(_shim.PROFILE_DIR[0], exist_ok=True)
                with open(_settings_file(), "w", encoding="utf-8") as f:
                    json.dump(user, f, ensure_ascii=False, indent=1)
            except OSError:
                pass
        return True

    def setSettingBool(self, id, value):  # noqa: A002
        return self.setSetting(id, "true" if value else "false")

    def setSettingInt(self, id, value):  # noqa: A002
        return self.setSetting(id, str(int(value)))

    def setSettingNumber(self, id, value):  # noqa: A002
        return self.setSetting(id, str(value))

    def setSettingString(self, id, value):  # noqa: A002
        return self.setSetting(id, value)

    def getLocalizedString(self, sid):
        return _strings().get(int(sid), "")

    def openSettings(self):
        pass

    OpenSettings = openSettings
