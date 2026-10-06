# -*- coding: utf-8 -*-
"""给繁体语言包补上 3 条缺失的键。

背景：我后来重写了 _system_help()，产生了新的字符串，
繁体包里没有对应条目（英文包有，所以英文 100%）。这三条会回退成简体。

用脚本补而不是手改：繁体包是 46KB 的 dict 字面量，
手改容易碰坏语法；这里用 AST 定位 CATALOG 的结束位置再插入，
并在写回后做语法 + 条目数校验。
"""
import ast
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
PATH = os.path.join(SRC, "i18n_zh_tw.py")

# 键必须与 app.py 里 t(...) 的实参逐字一致
ADD = [
    (
        "为什么要问？\n"
        "  · 系统不同，做出来的东西完全不同：Windows 是 .exe，\n"
        "    Mac 是 .app，Linux 是 .AppImage/.deb，网页则都能打开。\n"
        "  · 位数也很关键：32 位程序在 32/64 位系统上都能跑，\n"
        "    但 64 位程序在 32 位系统上跑不起来。\n\n"
        "程序已经帮你探测过了：\n",
        "為什麼要問？\n"
        "  · 系統不同，做出來的東西完全不同：Windows 是 .exe，\n"
        "    Mac 是 .app，Linux 是 .AppImage/.deb，網頁則都能開啟。\n"
        "  · 位元數也很關鍵：32 位元的程式在 32／64 位元系統上都能跑，\n"
        "    但 64 位元的程式在 32 位元系統上跑不起來。\n\n"
        "程式已經幫你偵測過了：\n",
    ),
    (
        "\n⚠️ 探测结果可能不完全准确（",
        "\n⚠️ 偵測結果可能不完全準確（",
    ),
    ("）", "）"),
]


def main():
    src = io.open(PATH, encoding="utf-8", newline=None).read()
    tree = ast.parse(src)

    # 找到 CATALOG = { ... } 的字面量范围
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            target = node.value
            break
    if target is None:
        print("找不到 CATALOG")
        return 1

    existing = {k.value for k in target.keys}
    todo = [(k, v) for k, v in ADD if k not in existing]
    if not todo:
        print("三条都已存在，无需补")
        return 0

    # 在 CATALOG 的最后一个键值对之后插入。
    # 用 AST 给出的行号定位：最后一项的结束行
    lines = src.splitlines(keepends=True)
    last = target.values[-1]
    insert_at = last.end_lineno          # end_lineno 是 1-based，插到它后面

    block = []
    for k, v in todo:
        block.append("\n    # 由 tools/fix_i18n_zh_tw_gap.py 补入（我改文案后新增的键）")
        block.append("\n    %s:\n        %s," % (repr(k), repr(v)))
    lines.insert(insert_at, "".join(block))

    out = "".join(lines)
    # 校验语法与条目数
    try:
        t2 = ast.parse(out)
    except SyntaxError as e:
        print("✘ 插入后语法错误，未写入：%s" % e)
        return 1
    n2 = 0
    for node in ast.walk(t2):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            n2 = len(node.value.keys)
    io.open(PATH, "w", encoding="utf-8", newline="\r\n").write(out)
    print("已补 %d 条；CATALOG 条目数 %d -> %d" % (len(todo), len(existing), n2))
    for k, _ in todo:
        print("   + %r" % (k[:60],))
    return 0


if __name__ == "__main__":
    sys.exit(main())
