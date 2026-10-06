# -*- coding: utf-8 -*-
"""补上「系统与位数」那题帮助文字里新增的 5 条文案（三语）。

为什么键要从 app.py 现取、不手写：
  这个项目里我手写键对错过三次（少一个「本机」、漏一个前导 \\n 之类），
  而且错了不报错 —— 只是那条翻译永远不生效。
  这里改成：按**内容特征**从真实键集合里找出目标键，译文跟着键走。

写盘前做三件事的断言：语法、条目数、每个目标键都能查到。
"""
import ast
import importlib.util
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

# 每条新文案：用「键里必定包含的片段」定位 + 三语译文
# （不写完整键，避免手抄出错；完整键从 app.py 现取）
FINDERS = [
    ("做电脑软件、手机 App、还是网页", {
        "zh-TW": (
            "為什麼要問？\n"
            "  · 做電腦軟體、手機 App、還是網頁，做法完全不同，成品也完全不一樣：\n"
            "      Windows 是 .exe，Mac 是 .app，Linux 是 .AppImage/.deb，\n"
            "      安卓是 .apk，iPhone 是 App Store 裡的 App，網頁只有一個網址。\n"
            "  · 電腦還要分 32 位元 / 64 位元：32 位元的程式在 32／64 位元系統上都能跑，\n"
            "    但 64 位元的程式在 32 位元系統上跑不起來。\n\n"
            "程式已經幫你偵測過了：\n"),
        "en": (
            "Why does this matter?\n"
            "  · A desktop program, a phone app, and a web page are built in completely\n"
            "    different ways and produce completely different results:\n"
            "      Windows uses .exe, Mac uses .app, Linux uses .AppImage/.deb,\n"
            "      Android uses .apk, iPhone apps come from the App Store, and a web page\n"
            "      is just a URL.\n"
            "  · On desktop, 32-bit vs 64-bit also matters: a 32-bit program runs on both\n"
            "    32- and 64-bit systems, but a 64-bit program will NOT run on a 32-bit system.\n\n"
            "I have already checked your machine:\n"),
    }),
    ("如果你要做**手机 App**", {
        "zh-TW": "\n如果你要做**手機 App**，先知道兩件事：\n",
        "en": "\nIf you want a **phone app**, know these two things first:\n",
    }),
    ("网页版通常最省事", {
        "zh-TW": "  · 如果只是想要「手機上也能用」，網頁版通常最省事："
                 "不用安裝、不用審核、電腦手機都能開。\n",
        "en": "  · If you only want it to \"also work on a phone\", the web version is usually "
              "the least trouble: nothing to install, no review process, and it opens on "
              "both desktop and phone.\n",
    }),
    ("请直接选对方的系统", {
        "zh-TW": "），\n   如果做出來是給別的電腦或手機用，請直接選對方的系統。\n",
        "en": "),\n   and if the result is meant for someone else's computer or phone, "
              "just pick their system instead.\n",
    }),
    ("不确定对方的设备", {
        "zh-TW": "\n只有當你做出來是給別人用時，才需要換成對方的系統。\n"
                 "如果不確定對方的裝置，就選第一項，並在最後一格補充說明。",
        "en": "\nYou only need to switch to someone else's system when the result is for them. "
              "If you are not sure what device they use, pick the first option and explain "
              "in the last box.\n",
    }),
]


def all_keys():
    statics, _ = t_call_args(os.path.join(SRC, "app.py"))
    const = {a for a in statics if isinstance(a, str) and a not in EXEMPT}
    rt, _ = runtime_keys(SRC)
    return sorted(const | {k for k in rt if k not in EXEMPT})


def resolve_pairs():
    """按片段定位真实键，返回 [(key, {'zh-TW':..., 'en':...})]"""
    keys = all_keys()
    out = []
    for needle, trans in FINDERS:
        hits = [k for k in keys if needle in k]
        if len(hits) != 1:
            print("  [X] 片段 %r 命中 %d 个键，无法唯一定位" % (needle, len(hits)))
            for h in hits:
                print("       %r" % (h[:90],))
            return None
        out.append((hits[0], trans))
    return out


def append_to_pack(fname, pairs, lang):
    path = os.path.join(SRC, fname)
    src = io.open(path, encoding="utf-8", newline=None).read()
    tree = ast.parse(src)
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            target = node.value
            break
    if target is None:
        raise SystemExit("找不到 CATALOG: " + fname)

    existing = {k.value for k in target.keys}
    todo = [(k, t[lang]) for k, t in pairs if k not in existing]
    if not todo:
        print("  %s: 无需补充" % fname)
        return 0

    # 用 json.dumps 产出，转义交给 json（手写多行字面量曾把包写坏两次）
    lines = src.splitlines(keepends=True)
    at = target.values[-1].end_lineno
    block = ["\n\n    # ---- 由 tools/fill_mobile_i18n.py 补入：手机 App 相关文案 ----\n"]
    for k, v in todo:
        block.append("    %s: %s,\n" % (json.dumps(k, ensure_ascii=False),
                                        json.dumps(v, ensure_ascii=False)))
    lines.insert(at, "".join(block))

    out = "".join(lines)
    t2 = ast.parse(out)                     # 语法不过就抛，不写盘
    n2 = 0
    for node in ast.walk(t2):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            n2 = len(node.value.keys)
    assert n2 == len(existing) + len(todo), "条目数不对: %d != %d" % (n2, len(existing) + len(todo))

    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    print("  %s: 补入 %d 条（%d → %d）" % (fname, len(todo), len(existing), n2))
    return len(todo)


def main():
    pairs = resolve_pairs()
    if pairs is None:
        return 1
    print("定位到 %d 条新文案：" % len(pairs))
    for k, _ in pairs:
        print("   %r" % (k[:88],))
    print()
    append_to_pack("i18n_zh_tw.py", pairs, "zh-TW")
    append_to_pack("i18n_en.py", pairs, "en")

    # 复查：重新导入并核对每个键都能查到
    print()
    ok = True
    for fname, lang in (("i18n_zh_tw.py", "zh-TW"), ("i18n_en.py", "en")):
        cat, err = catalog_of(os.path.join(SRC, fname))
        miss = [k for k, _ in pairs if k not in cat]
        print("  %s: 条目 %d，本次新增缺失 %d %s" % (fname, len(cat), len(miss), miss or ""))
        if miss or err:
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
