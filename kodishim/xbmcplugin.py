# -*- coding: utf-8 -*-
"""xbmcplugin - הפריטים שהתוסף מוסיף לרשימה נאספים, והכתובת שהוא פותר לניגון נשמרת."""
import kodishim as _shim

SORT_METHOD_NONE, SORT_METHOD_LABEL, SORT_METHOD_LABEL_IGNORE_THE, SORT_METHOD_DATE = 0, 1, 2, 3
SORT_METHOD_SIZE, SORT_METHOD_FILE, SORT_METHOD_DRIVE_TYPE, SORT_METHOD_TRACKNUM = 4, 5, 6, 7
SORT_METHOD_DURATION, SORT_METHOD_TITLE, SORT_METHOD_TITLE_IGNORE_THE, SORT_METHOD_ARTIST = 8, 9, 10, 11
SORT_METHOD_ALBUM, SORT_METHOD_GENRE, SORT_METHOD_VIDEO_YEAR, SORT_METHOD_VIDEO_RATING = 14, 16, 18, 19
SORT_METHOD_PROGRAM_COUNT, SORT_METHOD_PLAYLIST_ORDER, SORT_METHOD_EPISODE = 22, 23, 24
SORT_METHOD_VIDEO_TITLE, SORT_METHOD_VIDEO_SORT_TITLE, SORT_METHOD_UNSORTED = 25, 26, 40
SORT_METHOD_LABEL_IGNORE_FOLDERS, SORT_METHOD_LASTPLAYED, SORT_METHOD_PLAYCOUNT, SORT_METHOD_DATEADDED = 36, 37, 38, 21


def addDirectoryItem(handle, url, listitem, isFolder=False, totalItems=0):
    _shim._add_item(url, listitem, bool(isFolder))
    return True


def addDirectoryItems(handle, items, totalItems=0):
    for it in items:
        url, listitem = it[0], it[1]
        is_folder = it[2] if len(it) > 2 else False
        _shim._add_item(url, listitem, bool(is_folder))
    return True


def endOfDirectory(handle, succeeded=True, updateListing=False, cacheToDisc=True):
    pass


def setResolvedUrl(handle, succeeded, listitem):
    _shim._set_resolved(bool(succeeded), listitem)


def setContent(handle, content):
    _shim._set_content(content)


def addSortMethod(handle, sortMethod, label2Mask=""):
    pass


def setPluginCategory(handle, category):
    pass


def setPluginFanart(handle, image=None, color1=None, color2=None, color3=None):
    pass


def setProperty(handle, key, value):
    pass


def getSetting(handle, key):
    import xbmcaddon
    return xbmcaddon.Addon().getSetting(key)


def setSetting(handle, key, value):
    import xbmcaddon
    return xbmcaddon.Addon().setSetting(key, value)
