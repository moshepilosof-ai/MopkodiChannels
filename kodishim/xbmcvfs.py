# -*- coding: utf-8 -*-
"""xbmcvfs - נתיבי special:// של Kodi ממופים לתיקיות ליד ה-EXE, ופעולות קבצים בסיסיות."""
import os
import shutil

import kodishim as _shim


def translatePath(path):
    p = str(path)
    if p.startswith("special://"):
        rest = p[len("special://"):]
        head, _, tail = rest.partition("/")
        if head in ("profile", "userdata", "masterprofile", "home", "xbmc", "database"):
            base = _shim.PROFILE_DIR[0]
        elif head == "temp":
            base = _shim.TEMP_DIR[0]
        else:
            base = _shim.PROFILE_DIR[0]
        return os.path.join(base, *[x for x in tail.split("/") if x]) if tail else base
    return p


def exists(path):
    p = translatePath(path)
    return os.path.exists(p)


def mkdir(path):
    try:
        os.mkdir(translatePath(path))
        return True
    except OSError:
        return False


def mkdirs(path):
    try:
        os.makedirs(translatePath(path), exist_ok=True)
        return True
    except OSError:
        return False


def listdir(path):
    p = translatePath(path)
    try:
        names = os.listdir(p)
    except OSError:
        return [], []
    dirs = [n for n in names if os.path.isdir(os.path.join(p, n))]
    files = [n for n in names if not os.path.isdir(os.path.join(p, n))]
    return dirs, files


def delete(path):
    try:
        os.remove(translatePath(path))
        return True
    except OSError:
        return False


def rmdir(path, force=False):
    try:
        if force:
            shutil.rmtree(translatePath(path))
        else:
            os.rmdir(translatePath(path))
        return True
    except OSError:
        return False


def copy(src, dst):
    try:
        shutil.copyfile(translatePath(src), translatePath(dst))
        return True
    except OSError:
        return False


def rename(src, dst):
    try:
        os.replace(translatePath(src), translatePath(dst))
        return True
    except OSError:
        return False


def makeLegalFilename(name):
    return name


def validatePath(path):
    return path


class File:
    def __init__(self, path, mode="r"):
        self._f = open(translatePath(path), "rb" if "w" not in mode else "wb")

    def read(self, n=-1):
        data = self._f.read(n)
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data

    def readBytes(self, n=-1):
        return self._f.read(n)

    def write(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self._f.write(data)
        return True

    def size(self):
        pos = self._f.tell()
        self._f.seek(0, 2)
        n = self._f.tell()
        self._f.seek(pos)
        return n

    def seek(self, pos, whence=0):
        return self._f.seek(pos, whence)

    def tell(self):
        return self._f.tell()

    def close(self):
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


class Stat:
    def __init__(self, path):
        self._st = os.stat(translatePath(path))

    def st_size(self):
        return self._st.st_size

    def st_mtime(self):
        return self._st.st_mtime
