# -*- coding: utf-8 -*-
"""
"קודי מזויף": המודולים xbmc / xbmcaddon / xbmcgui / xbmcplugin / xbmcvfs שהתוסף של פישנזון מייבא,
ממומשים כאן בלי Kodi. במקום להציג רשימה על המסך, כל פריט שהתוסף מוסיף (addDirectoryItem) נאסף
לרשימה, וכתובת הניגון שהתוסף פותר (setResolvedUrl) נשמרת. השרת המקומי קורא אותם ומחזיר לדף.

ההתקנה: shim.install(addon_dir, profile_dir) מוסיף את התיקייה הזו ל-sys.path לפני כל import של התוסף.
"""
import os
import sys
import threading

ADDON_DIR = [""]      # תיקיית התוסף שחולץ (plugin.video.idanplus)
PROFILE_DIR = [""]    # תיקיית הנתונים של התוסף (הגדרות, מטמון, ערוצים)
TEMP_DIR = [""]

_tls = threading.local()


def begin():
    """פותח איסוף חדש לקריאה הנוכחית (לכל thread בנפרד)."""
    _tls.items = []
    _tls.resolved = None
    _tls.notifications = []
    _tls.content = ""
    _tls.builtins = []


def items():
    return getattr(_tls, "items", [])


def resolved():
    return getattr(_tls, "resolved", None)


def notifications():
    return getattr(_tls, "notifications", [])


def content():
    return getattr(_tls, "content", "")


def _add_item(url, listitem, is_folder):
    if not hasattr(_tls, "items"):
        _tls.items = []
    _tls.items.append((url, listitem, is_folder))


def _set_resolved(succeeded, listitem):
    _tls.resolved = (succeeded, listitem)


def _notify(text):
    if not hasattr(_tls, "notifications"):
        _tls.notifications = []
    _tls.notifications.append(text)


def _set_content(text):
    _tls.content = text


def install(addon_dir, profile_dir):
    ADDON_DIR[0] = addon_dir
    PROFILE_DIR[0] = profile_dir
    TEMP_DIR[0] = os.path.join(profile_dir, "temp")
    for d in (profile_dir, TEMP_DIR[0]):
        os.makedirs(d, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    # Kodi מוסיף ל-path את תיקיית התוסף ואת ה-python.module extensions שלו (resources/, resources/lib/)
    for p in (addon_dir, os.path.join(addon_dir, "resources"), os.path.join(addon_dir, "resources", "lib")):
        if p not in sys.path:
            sys.path.insert(0, p)
