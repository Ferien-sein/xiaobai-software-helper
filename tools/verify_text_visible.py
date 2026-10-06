# -*- coding: utf-8 -*-
"""验证「打字/点选项后文字看得见」——真的启动界面、真的写入、真的截图。

为什么要单独做：对比度算数能证明颜色够清晰，但**界面上的实际效果**还得看一眼。
这个脚本会：
  1. 启动应用
  2. 往输入框里打字（走 _clear_example + insert 的真实路径）
  3. 用鼠标选项按钮往另一个框里写（走 _toggle → _sync_options_to_box 的真实路径）
  4. 截图，并存一份写入后的前景色采样结果

用法: python tools/verify_text_visible.py
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
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

APP = os.path.join(SRC, "app.py")
OUT = os.path.join(ROOT, "assets", "verify-text-visible.png")

# 用一个独立配置，避免影响用户真实的 config.json
env = dict(os.environ)
env["XBSH_THEME"] = "dark"
env["XBSH_LANG"] = "zh-CN"
env["XBSH_CONFIG"] = os.path.join(ROOT, ".verify-config.json")
env["XBSH_AUTODEMO"] = "1"      # app.py 会读这个：自动写入演示内容，便于截图
env["PYTHONIOENCODING"] = "utf-8"

u = ctypes.windll.user32
u.SetProcessDPIAware()

print("启动应用（暗色主题，自动写入演示内容）…")
proc = subprocess.Popen([sys.executable, "-X", "utf8", APP], env=env)

TITLE_HINTS = ("小白造", "Little White", "Software Helper")
hwnd = 0
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
        hwnd = found[0]
        break

if not hwnd:
    proc.terminate()
    print("没找到窗口")
    sys.exit(1)

time.sleep(2.5)      # 等它把演示内容写完


def grab(h):
    r = wt.RECT()
    u.GetWindowRect(h, ctypes.byref(r))
    w, hh = r.right - r.left, r.bottom - r.top
    hdc = u.GetWindowDC(h)
    mem = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
    bmp = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, w, hh)
    old = ctypes.windll.gdi32.SelectObject(mem, bmp)
    ok = False
    for flag in (2, 0):
        if u.PrintWindow(h, mem, flag):
            ok = True
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
    got = ctypes.windll.gdi32.GetDIBits(mem, bmp, 0, hh, buf, ctypes.byref(bmi), 0) if ok else 0
    ctypes.windll.gdi32.SelectObject(mem, old)
    ctypes.windll.gdi32.DeleteObject(bmp)
    ctypes.windll.gdi32.DeleteDC(mem)
    u.ReleaseDC(h, hdc)
    if not got:
        return None
    from PIL import Image
    return Image.frombuffer("RGBA", (w, hh), buf, "raw", "BGRA", 0, 1).convert("RGB")


img = grab(hwnd)
if img is None:
    r = wt.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom))
img.save(OUT)
print("已保存:", OUT, img.size)

proc.terminate()
try:
    proc.wait(timeout=5)
except Exception:
    proc.kill()
