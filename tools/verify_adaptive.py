# -*- coding: utf-8 -*-
"""截图验证「问卷自适应」：选不同平台，后面的题真的跟着变。

跑法: python tools/verify_adaptive.py
输出: assets/verify-adaptive-<族>.png
"""
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
import time

from PIL import ImageGrab

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
APP = os.path.join(ROOT, "src", "app.py")

u = ctypes.windll.user32
u.SetProcessDPIAware()
TITLE_HINTS = ("小白造", "Little White", "Software Helper")


def _find_hwnd(pid):
    for _ in range(80):
        time.sleep(0.5)
        found = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def cb(h, _l):
            if u.IsWindowVisible(h):
                n = u.GetWindowTextLengthW(h)
                if n:
                    b = ctypes.create_unicode_buffer(n + 1)
                    u.GetWindowTextW(h, b, n + 1)
                    if any(x in b.value for x in TITLE_HINTS):
                        found.append(h)
            return True

        u.EnumWindows(cb, None)
        if found:
            return found[0]
    return 0


def grab(h):
    from PIL import Image
    r = wt.RECT()
    u.GetWindowRect(h, ctypes.byref(r))
    w, hh = r.right - r.left, r.bottom - r.top
    hdc = u.GetWindowDC(h)
    mem = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
    bmp = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, w, hh)
    old = ctypes.windll.gdi32.SelectObject(mem, bmp)
    for flag in (2, 0):
        if u.PrintWindow(h, mem, flag):
            break

    class BIH(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                    ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                    ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                    ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
                    ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]

    bmi = BIH()
    bmi.biSize = ctypes.sizeof(BIH)
    bmi.biWidth = w
    bmi.biHeight = -hh
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    buf = ctypes.create_string_buffer(w * hh * 4)
    got = ctypes.windll.gdi32.GetDIBits(mem, bmp, 0, hh, buf, ctypes.byref(bmi), 0)
    ctypes.windll.gdi32.SelectObject(mem, old)
    ctypes.windll.gdi32.DeleteObject(bmp)
    ctypes.windll.gdi32.DeleteDC(mem)
    u.ReleaseDC(h, hdc)
    if not got:
        return None
    return Image.frombuffer("RGBA", (w, hh), buf, "raw", "BGRA", 0, 1).convert("RGB")


# 每个平台用 XBSH_AUTOADAPT 让 app 自动选好第 3 题（便于截图）
CASES = [
    ("desktop", "跟我电脑一样"),
    ("android", "安卓手机 App（ARM64"),
    ("web", "网页（浏览器"),
]

for fam, label in CASES:
    env = dict(os.environ)
    env["XBSH_THEME"] = "dark"
    env["XBSH_LANG"] = "zh-CN"
    env["XBSH_CONFIG"] = os.path.join(ROOT, ".verify-config.json")
    env["XBSH_AUTOADAPT"] = label
    proc = subprocess.Popen([sys.executable, "-X", "utf8", APP], env=env)
    hwnd = _find_hwnd(proc.pid)
    if not hwnd:
        proc.terminate()
        print("  [%s] 没找到窗口" % fam)
        continue
    time.sleep(3)
    img = grab(hwnd)
    if img is None:
        r = wt.RECT()
        u.GetWindowRect(hwnd, ctypes.byref(r))
        img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom))
    out = os.path.join(ROOT, "assets", "verify-adaptive-%s.png" % fam)
    img.save(out)
    print("  [%s] 已保存 %s" % (fam, out))
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    time.sleep(1)

cfg = os.path.join(ROOT, ".verify-config.json")
if os.path.exists(cfg):
    os.remove(cfg)
