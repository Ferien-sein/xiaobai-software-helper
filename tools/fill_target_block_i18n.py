# -*- coding: utf-8 -*-
"""补上「目标平台段」新增的 2 条文案（三语）。

键从 app.py 现取（按片段定位），不手写 —— 手写对错过三次。
"""
import ast
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, HERE)
sys.path.insert(0, SRC)

from check_i18n import t_call_args, runtime_keys, catalog_of, EXEMPT  # noqa: E402

FINDERS = [
    ("跟做我这台电脑上的程序不是一回事", {
        "zh-TW": "目標是手機或網頁，跟做我這台電腦上的程式不是一回事，請照上面的平台來做。",
        "en": "The target is a phone or a web page, which is not the same thing as a program "
              "for this computer of mine — please build for the platform above.",
    }),
    ("并说明在目标设备上第一次打开需要做什么", {
        "zh-TW": "交付要求：請給出該平台上可以直接開啟使用的成品，"
                 "並說明在目標裝置上第一次開啟需要做什麼。",
        "en": "Delivery requirement: provide something that opens and works directly on that "
              "platform, and explain what has to be done the first time it is opened on the "
              "target device.",
    }),
]


def all_keys():
    statics, _ = t_call_args(os.path.join(SRC, "app.py"))
    const = {a for a in statics if isinstance(a, str) and a not in EXEMPT}
    rt, _ = runtime_keys(SRC)
    return sorted(const | {k for k in rt if k not in EXEMPT})


def resolve():
    keys = all_keys()
    out = []
    for needle, trans in FINDERS:
        hits = [k for k in keys if needle in k]
        if len(hits) != 1:
            print("  [X] 片段 %r 命中 %d 个" % (needle, len(hits)))
            for h in hits:
                print("       %r" % (h[:100],))
            return None
        out.append((hits[0], trans))
    return out


def append(fname, pairs, lang):
    path = os.path.join(SRC, fname)
    src = io.open(path, encoding="utf-8", newline=None).read()
    tree = ast.parse(src)
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            target = node.value
            break
    existing = {k.value for k in target.keys}
    todo = [(k, t[lang]) for k, t in pairs if k not in existing]
    if not todo:
        print("  %s: 无需补充" % fname)
        return
    lines = src.splitlines(keepends=True)
    at = target.values[-1].end_lineno
    block = ["\n\n    # ---- 由 tools/fill_target_block_i18n.py 补入：目标平台段新文案 ----\n"]
    for k, v in todo:
        block.append("    %s: %s,\n" % (json.dumps(k, ensure_ascii=False),
                                        json.dumps(v, ensure_ascii=False)))
    lines.insert(at, "".join(block))
    out = "".join(lines)
    t2 = ast.parse(out)
    n2 = 0
    for node in ast.walk(t2):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            n2 = len(node.value.keys)
    assert n2 == len(existing) + len(todo), "%d != %d" % (n2, len(existing) + len(todo))
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    print("  %s: 补入 %d 条（%d → %d）" % (fname, len(todo), len(existing), n2))


def main():
    pairs = resolve()
    if pairs is None:
        return 1
    print("定位到 %d 条：" % len(pairs))
    for k, _ in pairs:
        print("   %r" % (k[:92],))
    append("i18n_zh_tw.py", pairs, "zh-TW")
    append("i18n_en.py", pairs, "en")
    print()
    for fname in ("i18n_zh_tw.py", "i18n_en.py"):
        cat, err = catalog_of(os.path.join(SRC, fname))
        miss = [k for k, _ in pairs if k not in cat]
        print("  %s: %d 条，本次缺失 %d %s" % (fname, len(cat), len(miss), miss or ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
