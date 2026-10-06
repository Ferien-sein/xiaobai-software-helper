# -*- coding: utf-8 -*-
"""为三种界面语言各截一张图，存到 assets/。

用法: python tools/screenshot_langs.py
产出:
  assets/screenshot-dark.png      （简体，暗色）
  assets/screenshot-light.png     （简体，浅色）
  assets/screenshot-zh-tw.png     （繁体，暗色）
  assets/screenshot-en.png        （English，暗色）
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT = os.path.join(ROOT, "tools", "screenshot.py")

JOBS = [
    ("zh-CN", "dark", "assets/screenshot-dark.png"),
    ("zh-CN", "light", "assets/screenshot-light.png"),
    ("zh-TW", "dark", "assets/screenshot-zh-tw.png"),
    ("en", "dark", "assets/screenshot-en.png"),
]

fail = 0
for lang, theme, out in JOBS:
    env = dict(os.environ)
    env["XBSH_LANG"] = lang
    env["PYTHONIOENCODING"] = "utf-8"
    print("--- %s / %s -> %s" % (lang, theme, out))
    r = subprocess.run([sys.executable, "-X", "utf8", SHOT, theme, out],
                       env=env, capture_output=True, text=True, encoding="utf-8")
    tail = (r.stdout or "").strip().splitlines()[-1:] or ["(无输出)"]
    print("    " + tail[0])
    if r.returncode != 0:
        fail += 1
        print("    ✘ 失败: " + (r.stderr or "")[-300:])

print()
print("完成 %d/%d" % (len(JOBS) - fail, len(JOBS)))
sys.exit(1 if fail else 0)
