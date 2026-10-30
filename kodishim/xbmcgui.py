# -*- coding: utf-8 -*-
"""xbmcgui - ListItem (פריט ברשימה), Dialog (חלונות; כאן תמיד "ביטול"), חלונות (ריקים)."""
import kodishim as _shim

NOTIFICATION_INFO, NOTIFICATION_WARNING, NOTIFICATION_ERROR = "info", "warning", "error"
INPUT_ALPHANUM, INPUT_NUMERIC, INPUT_DATE, INPUT_TIME, INPUT_IPADDRESS, INPUT_PASSWORD = 0, 1, 2, 3, 4, 5
ACTION_PREVIOUS_MENU, ACTION_NAV_BACK, ACTION_PARENT_DIR, ACTION_SELECT_ITEM = 10, 92, 9, 7
ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP, ACTION_MOVE_DOWN = 1, 2, 3, 4
ACTION_CONTEXT_MENU, ACTION_SHOW_INFO, ACTION_STOP, ACTION_PAUSE = 117, 11, 13, 12


class _InfoTag:
    """תגית מידע של וידאו/מוזיקה: כל set* נשמר במילון, כל get* מחזיר מה שנשמר."""

    def __init__(self, store):
        self._s = store

    def __getattr__(self, name):
        if name.startswith("set"):
            key = name[3:].lower()

            def _set(*args, **kw):
                if len(args) == 1:
                    self._s[key] = args[0]
                elif args:
                    self._s[key] = args
                return None
            return _set
        if name.startswith("get"):
            key = name[3:].lower()
            return lambda *a, **k: self._s.get(key, "")
        raise AttributeError(name)


class ListItem:
    def __init__(self, label="", label2="", path="", offscreen=False, iconImage=None, thumbnailImage=None):
        self.label = label
        self.label2 = label2
        self.path = path
        self.art = {}
        if iconImage:
            self.art["icon"] = iconImage
        if thumbnailImage:
            self.art["thumb"] = thumbnailImage
        self.info = {}
        self.info_type = ""
        self.properties = {}
        self.context = []
        self.mimetype = ""
        self.subtitles = []
        self.streams = {}
        self._tag = {}

    def setLabel(self, label):
        self.label = label

    def getLabel(self):
        return self.label

    def setLabel2(self, label):
        self.label2 = label

    def getLabel2(self):
        return self.label2

    def setPath(self, path):
        self.path = path

    def getPath(self):
        return self.path

    def setArt(self, art):
        self.art.update(art or {})

    def getArt(self, key):
        return self.art.get(key, "")

    def setInfo(self, type, infoLabels):  # noqa: A002
        self.info_type = type
        self.info.update({str(k).lower(): v for k, v in (infoLabels or {}).items()})

    def setProperty(self, key, value):
        self.properties[key] = value

    def getProperty(self, key):
        return self.properties.get(key, "")

    def setProperties(self, props):
        self.properties.update(props or {})

    def addContextMenuItems(self, items, replaceItems=False):
        self.context = list(items or []) if replaceItems else self.context + list(items or [])

    def setMimeType(self, mt):
        self.mimetype = mt

    def setContentLookup(self, enable):
        pass

    def setSubtitles(self, subs):
        self.subtitles = list(subs or [])

    def addStreamInfo(self, kind, values):
        self.streams[kind] = values

    def setIsFolder(self, is_folder):
        pass

    def getVideoInfoTag(self):
        return _InfoTag(self._tag)

    def getMusicInfoTag(self):
        return _InfoTag(self._tag)

    def select(self, selected):
        pass

    def isSelected(self):
        return False


class Dialog:
    """כל חלון מחזיר "ביטול": אין משתמש מול החלון. הודעות (notification/ok) נאספות ומוצגות בדף."""

    def notification(self, heading, message, icon="", time=5000, sound=True):
        _shim._notify("{0}: {1}".format(heading, message) if heading else message)

    def ok(self, heading, message="", *a):
        _shim._notify("{0}: {1}".format(heading, message) if heading else message)
        return True

    def yesno(self, heading, message="", *a, **k):
        return False

    def yesnocustom(self, *a, **k):
        return -1

    def select(self, heading, items, autoclose=0, preselect=-1, useDetails=False):
        return -1

    def multiselect(self, *a, **k):
        return None

    def contextmenu(self, items):
        return -1

    def input(self, heading, defaultt="", type=0, option=0, autoclose=0):  # noqa: A002
        return ""

    def numeric(self, type, heading, defaultt="", *a):  # noqa: A002
        return ""

    def browse(self, *a, **k):
        return ""

    def browseSingle(self, *a, **k):
        return ""

    def browseMultiple(self, *a, **k):
        return []

    def textviewer(self, heading, text, usemono=False):
        pass

    def info(self, item):
        return False


class DialogProgress:
    def create(self, heading, message=""):
        pass

    def update(self, percent, message=""):
        pass

    def close(self):
        pass

    def iscanceled(self):
        return False


class DialogProgressBG(DialogProgress):
    def isFinished(self):
        return True


class Window:
    def __init__(self, existing=None):
        self._props = {}

    def setProperty(self, key, value):
        self._props[key] = value

    def getProperty(self, key):
        return self._props.get(key, "")

    def clearProperty(self, key):
        self._props.pop(key, None)

    def doModal(self):
        pass

    def show(self):
        pass

    def close(self):
        pass

    def getFocusId(self):
        return 0

    def getControl(self, cid):
        return _Control()

    def setFocusId(self, cid):
        pass


class _Control:
    def __getattr__(self, name):
        return lambda *a, **k: None


class WindowDialog(Window):
    pass


class WindowXML(Window):
    def __init__(self, *a, **k):
        Window.__init__(self)


class WindowXMLDialog(WindowXML):
    pass


def getCurrentWindowId():
    return 10000


def getCurrentWindowDialogId():
    return 9999


def getScreenHeight():
    return 1080


def getScreenWidth():
    return 1920
