# -*- coding: utf-8 -*-
"""看第 3 题（system）自己的字段，以及自适应后各处显示。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import app as A  # noqa: E402
import i18n  # noqa: E402
import questionnaire as Q  # noqa: E402

i18n.set_lang("zh-CN")
q = [x for x in A.QUESTIONS if x["key"] == "system"][0]
print("  system 题的字段:", sorted(q.keys()))
print("  example 是函数吗:", callable(q.get("example")))
print("  example 值:", repr(str(A._qval(q, "example"))[:90]))
print("  help 是函数吗:", callable(q.get("help")))
print()
for fam in (Q.FAM_DESKTOP, Q.FAM_ANDROID, Q.FAM_IOS, Q.FAM_WEB):
    r = Q.adapt("system", fam, "zh-CN", q)
    print("  [%-8s]" % fam)
    print("     title  :", r["title"])
    print("     hint   :", (r["hint"] or "")[:78])
    print("     example:", (r["example"] or "")[:78])
    print("     选项数 :", len(r["options"]))
    print()
