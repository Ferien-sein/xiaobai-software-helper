# -*- coding: utf-8 -*-
"""把语言包里「写死题号」的键迁移成不带题号的版本。

## 为什么要做

问卷题号会随「做什么类型」变：做插件时「给谁用」是第 6 题，做程序时是第 3 题
（插件的核心问题插到了前面）。如果把题号写进键（"3. 给谁用？…"），
换个类型这条翻译就失效 —— 英文界面里冒出中文标题。

## 做法

对每个以「数字. 」开头的键，额外写一条**不带编号**的副本：
    "3. 给谁用？一共几个人用？"  →  也加 "给谁用？一共几个人用？"
老键**保留**（不删），这样：
  · 写死编号的老代码路径仍然能查到
  · 新代码 t("6. 给谁用？…") 会剥掉 "6. " 查到中性键，再把 "6. " 补回去

安全措施：写盘前 ast.parse + 条目数断言。
"""
import ast
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")

NUM = re.compile(r"^(\d+[.、]\s*)(.+)$", re.S)


def find_catalog(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            return node.value
    return None


def migrate(fname):
    path = os.path.join(SRC, fname)
    src = io.open(path, encoding="utf-8", newline=None).read()
    tree = ast.parse(src)
    cat = find_catalog(tree)
    if cat is None:
        print("  [X] %s 找不到 CATALOG" % fname)
        return 1

    existing = {k.value: v.value for k, v in zip(cat.keys, cat.values)}
    todo = {}
    for k, v in existing.items():
        m = NUM.match(k)
        if not m:
            continue
        neutral = m.group(2)
        if neutral not in existing and neutral not in todo:
            todo[neutral] = v

    if not todo:
        print("  %s: 无需迁移" % fname)
        return 0

    lines = src.splitlines(keepends=True)
    at = cat.values[-1].end_lineno
    block = ["\n\n    # ---- 由 tools/migrate_numbered_keys.py 补入：不带题号的键 ----\n",
             "    # 题号会随「做什么类型」变，所以键不能写死编号；\n",
             "    # i18n.t() 会剥掉编号查这里的键，再把原编号补回译文。\n"]
    for k, v in todo.items():
        block.append("    %s: %s,\n" % (json.dumps(k, ensure_ascii=False),
                                        json.dumps(v, ensure_ascii=False)))
    lines.insert(at, "".join(block))
    out = "".join(lines)
    t2 = ast.parse(out)          # 语法不过就抛，不写盘
    cat2 = find_catalog(t2)
    n2 = len(cat2.keys)
    assert n2 == len(existing) + len(todo), "%d != %d" % (n2, len(existing) + len(todo))
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    print("  %s: 补入 %d 条中性键（%d → %d）" % (fname, len(todo), len(existing), n2))
    return 0


def main():
    rc = 0
    for f in ("i18n_zh_tw.py", "i18n_en.py"):
        rc |= migrate(f)
    return rc


if __name__ == "__main__":
    sys.exit(main())
