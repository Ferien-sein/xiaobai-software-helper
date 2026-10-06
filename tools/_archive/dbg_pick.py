# -*- coding: utf-8 -*-
"""调试 _pick 为什么没取到「all」条目。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import questionnaire as Q  # noqa: E402

print("ADAPT 里有 what 吗:", "what" in Q.ADAPT)
print("what 的规则:", Q.ADAPT.get("what"))
print()
tbl = (Q.ADAPT.get("what") or {}).get("title_by")
print("title_by =", tbl)
print()
for fam in (Q.FAM_DESKTOP, Q.FAM_ANDROID, Q.FAM_PLUGIN if hasattr(Q, "FAM_PLUGIN") else "all"):
    print("  fam=%-9s family_chain=%s" % (fam, Q.family_chain(fam)))
print()
for loc in ("zh-CN", "zh-TW", "en"):
    got = Q._pick(tbl, Q.FAM_DESKTOP, loc)
    print("  _pick(%s) = %r" % (loc, got))
print()
base = {"key": "what", "title": "1. 你想做一个什么样的软件？", "hint": "x",
        "example": "y", "help": "z", "options": ["a"], "required": True}
r = Q.adapt("what", Q.FAM_DESKTOP, "zh-CN", base)
print("adapt 结果 title =", repr(r["title"]))
print("adapt 结果 changed =", r["changed"])
