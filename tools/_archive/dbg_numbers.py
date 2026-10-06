# -*- coding: utf-8 -*-
"""查题号为什么丢了：所有题集里每题的编号是否与位置一致。"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import app as A  # noqa: E402
import questionnaire as Q  # noqa: E402

NUM = re.compile(r"^(\d+)[.、]\s*(.*)$", re.S)

for kind in (Q.KIND_PROGRAM, Q.KIND_PLUGIN, Q.KIND_SCRIPT):
    qs = Q.questions_for(A.QUESTIONS, kind, "zh-CN")
    print("== %s ==" % kind)
    for i, q in enumerate(qs, 1):
        m = NUM.match(q["title"])
        got = int(m.group(1)) if m else None
        flag = "" if got == i else "   <<< 编号不对（应为 %d）" % i
        print("  位置%2d  key=%-18s 标题=%s%s" % (i, q["key"], q["title"][:44], flag))
    print()
