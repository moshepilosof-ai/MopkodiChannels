# -*- coding: utf-8 -*-
"""xbmc - לוג, פקודות מובנות, מידע מערכת. בלי Kodi: לוג לקונסול, פקודות נרשמות, הודעות Notification נאספות."""
import os
import re
import sys
import time

import kodishim as _shim

LOGDEBUG, LOGINFO, LOGNOTICE, LOGWARNING, LOGERROR, LOGSEVERE, LOGFATAL, LOGNONE = 0, 1, 2, 3, 3, 4, 4, 5
PLAYLIST_MUSIC, PLAYLIST_VIDEO = 0, 1

LOG_LINES = []          # הלוג האחרון של התוסף (ל-/api/log)
_LOG_KEEP = 400
VERBOSE = [False]


def log(msg, level=LOGDEBUG):
    line = "[{0}] {1}".format(("D", "I", "N", "E", "F", "-")[min(level, 5)], msg)
    LOG_LINES.append(line)
    del LOG_LINES[:-_LOG_KEEP]
    if level >= LOGWARNING or VERBOSE[0]:
        try:
            print("addon: " + line, file=sys.stderr, flush=True)
        except Exception:  # noqa: BLE001
            pass


def executebuiltin(command, wait=False):
    m = re.match(r"\s*Notification\((.*)\)\s*$", command, re.S)
    if m:
        parts = [p.strip() for p in m.group(1).split(",")]
        _shim._notify(parts[1] if len(parts) > 1 else m.group(1))
        log("Notification: " + m.group(1), LOGINFO)
        return
    m = re.match(r"\s*Extract\((.*?),\s*(.*)\)\s*$", command, re.S)
    if m:
        # Kodi מחלץ ZIP לתיקייה; התוסף משתמש בזה לרשימת התוכניות (series.json) וללוח השידורים (epg.json)
        import zipfile
        src, dest = m.group(1).strip().strip('"'), m.group(2).strip().strip('"')
        try:
            with zipfile.ZipFile(src) as z:
                for member in z.infolist():
                    if ".." in member.filename or member.filename.startswith(("/", "\\")):
                        continue
                    z.extract(member, dest)
        except Exception as ex:  # noqa: BLE001
            log("Extract failed: {0}".format(ex), LOGERROR)
        return
    log("executebuiltin: " + command)


def executeJSONRPC(request):
    return '{"id":1,"jsonrpc":"2.0","result":{}}'


def getInfoLabel(label):
    if label == "System.BuildVersion":
        return "19.5 (19.5.0) Git:20221119"
    return ""


def getCondVisibility(cond):
    return False


def getLanguage(fmt=0, region=False):
    return "he_il" if fmt else "Hebrew"


def getRegion(what):
    return "%d/%m/%Y" if what == "dateshort" else "%H:%M"


def getSkinDir():
    return "skin.estuary"


def sleep(ms):
    time.sleep(min(ms, 5000) / 1000.0)


def translatePath(path):
    import xbmcvfs
    return xbmcvfs.translatePath(path)


def getLocalizedString(sid):
    return ""


class Player:
    def __init__(self, *a, **k):
        pass

    def play(self, item="", listitem=None, windowed=False, startpos=-1):
        import xbmcgui
        li = listitem if listitem is not None else xbmcgui.ListItem(path=item)
        if item and not li.getPath():
            li.setPath(item)
        _shim._set_resolved(True, li)

    def isPlaying(self):
        return False

    def isPlayingVideo(self):
        return False

    def isPlayingAudio(self):
        return False

    def stop(self):
        pass

    def getTime(self):
        return 0.0

    def getTotalTime(self):
        return 0.0

    def getPlayingFile(self):
        return ""

    def seekTime(self, t):
        pass


class Monitor:
    def __init__(self, *a, **k):
        pass

    def abortRequested(self):
        return False

    def waitForAbort(self, timeout=0):
        time.sleep(min(timeout, 1))
        return False

    def onSettingsChanged(self):
        pass


class Keyboard:
    def __init__(self, default="", heading="", hidden=False):
        self._text = default

    def doModal(self, autoclose=0):
        pass

    def setDefault(self, text):
        self._text = text

    def isConfirmed(self):
        return False

    def getText(self):
        return self._text


class PlayList:
    def __init__(self, kind=PLAYLIST_VIDEO):
        self._items = []

    def clear(self):
        self._items = []

    def add(self, url, listitem=None, index=-1):
        self._items.append(url)

    def size(self):
        return len(self._items)
