# -*- coding: utf-8 -*-
"""截图**打包后的 exe**（不是源码），验证产物真的能用。

为什么必须单独做：源码能跑不代表打包产物能跑。
PyInstaller 常见问题是模块没打进去（语言包缺失会静默回退成中文）、
或有数据文件缺失（提示词模板）。这些只有真跑 exe 才看得出来。

用法: python tools/screenshot_exe.py [zh-CN|zh-TW|en] [输出路径]
"""
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
import time

from PIL import ImageGrab

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "dist", "xiaobai-software-helper",
                   "xiaobai-software-helper.exe")

lang = sys.argv[1] if len(sys.argv) > 1 else "zh-CN"
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "assets", "exe-%s.png" % lang)
if not os.path.isabs(out):
    out = os.path.join(ROOT, out)
os.makedirs(os.path.dirname(out), exist_ok=True)

if not os.path.exists(EXE):
    print("找不到 exe: %s" % EXE)
    sys.exit(1)

u = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
u.SetProcessDPIAware()

env = dict(os.environ)
env["XBSH_LANG"] = lang
# 独立配置文件：不污染用户真实 config.json
env["XBSH_CONFIG"] = os.path.join(ROOT, ".exe-test-config.json")
env["XBSH_THEME"] = "dark"

print("启动 exe（语言=%s）" % lang)
proc = subprocess.Popen([EXE], env=env)

TITLE_HINTS = ("小白造", "Little White", "Software Helper")


def is_ours(h):
    pid = wt.DWORD()
    u.GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value != proc.pid:
        # exe 可能有子进程，这里放宽：只要标题像就算
        pass
    n = u.GetWindowTextLengthW(h)
    if not n:
        return False
    buf = ctypes.create_unicode_buffer(n + 1)
    u.GetWindowTextW(h, buf, n + 1)
    return any(hint in buf.value for hint in TITLE_HINTS)


hwnd = 0
for _ in range(80):
    time.sleep(0.5)
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(h, _l):
        if u.IsWindowVisible(h) and is_ours(h):
            found.append(h)
        return True

    u.EnumWindows(cb, None)
    if found:
        hwnd = found[0]
        break

if not hwnd:
    proc.terminate()
    print("没找到 exe 的窗口 —— 产物可能起不来")
    sys.exit(1)

# 取标题（能间接确认语言包是否生效）
n = u.GetWindowTextLengthW(hwnd)
buf = ctypes.create_unicode_buffer(n + 1)
u.GetWindowTextW(hwnd, buf, n + 1)
print("窗口标题: %r" % buf.value)


def grab_direct(h):
    r = wt.RECT()
    u.GetWindowRect(h, ctypes.byref(r))
    w, hh = r.right - r.left, r.bottom - r.top
    if w <= 0 or hh <= 0:
        return None
    hdc = u.GetWindowDC(h)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, hh)
    old = gdi32.SelectObject(mem, bmp)
    ok = False
    for flag in (2, 0):
        if u.PrintWindow(h, mem, flag):
            ok = True
            break
    from PIL import Image

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
    buf2 = ctypes.create_string_buffer(w * hh * 4)
    got = gdi32.GetDIBits(mem, bmp, 0, hh, buf2, ctypes.byref(bmi), 0) if ok else 0
    gdi32.SelectObject(mem, old)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    u.ReleaseDC(h, hdc)
    if not got:
        return None
    return Image.frombuffer("RGBA", (w, hh), buf2, "raw", "BGRA", 0, 1).convert("RGB")


img = grab_direct(hwnd)
if img is None:
    r = wt.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom))
img.save(out)
print("已保存:", out, img.size)

proc.terminate()
try:
    proc.wait(timeout=5)
except Exception:
    proc.kill()
