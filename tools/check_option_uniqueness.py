# -*- coding: utf-8 -*-
"""检查：每题内部的「选项原文」是否唯一。

为什么必须唯一：翻译后勾选框的显示文字会变，但**记录的仍然是简体原文**
（这样存档跨语言都能还原）。如果同一题里有两项原文相同，
option_buttons[(key, 原文)] 就会互相覆盖 —— 丢掉一个勾选框、而且不报错。
"""

import os
# ★ 锁定界面语言（XBSH_LANG_LOCKED）：这些检查/自检脚本的输出与断言都基于简体中文，
#   而 i18n 会按系统区域自动探测语言 —— 在英文机器 / CI 上会探测成英文，
#   断言就全挂（GitHub runner 上真踩过：selftest_platform 11 项失败）。
#   ★ 用 = 不用 setdefault：环境里已有 XBSH_LANG 时 setdefault 不覆盖，锁会失效。
#   插在第一个模块级 import 之前，保证任何依赖 i18n 的 import 都在它之后。
os.environ["XBSH_LANG"] = "zh-CN"

import os
import sys

def _force_utf8_output():
    """让中文输出在 Windows 默认（GBK）控制台上也不乱码、不崩。

    不加这个的话，print 中文会变成乱码甚至 UnicodeEncodeError，
    而这类检查工具的用途就是给人看结论 —— 结论读不了等于没做。
    重定向到文件时同样是 UTF-8，输出一致。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001  老 Python 没有 reconfigure
            pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

import app  # noqa: E402

bad = 0
for q in app.QUESTIONS:
    opts = app._qopts(q)
    if len(opts) != len(set(opts)):
        seen = {}
        for o in opts:
            seen[o] = seen.get(o, 0) + 1
        dup = {k: v for k, v in seen.items() if v > 1}
        print("[X] %s 里有重复选项: %s" % (q["key"], dup))
        bad += 1
    if any(not isinstance(o, str) or not o.strip() for o in opts):
        print("[X] %s 里有空选项" % q["key"])
        bad += 1

best = 0
for q in app.QUESTIONS:
    opts = list(app._qopts(q)) + [str(app._qval(q, "example")), str(q.get("title", ""))]
    n = len(set(x for x in opts if x))
    best += 0
    if len(set(o for o in app._qopts(q) if o)) == 0 and app._qopts(q):
        print("[X] %s 选项全为空" % q["key"])
        bad += 1

total_opts = sum(len(app._qopts(q)) for q in app.QUESTIONS)
_force_utf8_output()   # 中文输出在 GBK 控制台上会乱码，先切 UTF-8
print("共 %d 题、%d 个选项" % (len(app.QUESTIONS), total_opts))
print("选项原文唯一性: %s" % ("全部唯一 OK" if bad == 0 else "有 %d 处问题" % bad))
sys.exit(1 if bad else 0)
