# -*- coding: utf-8 -*-
"""把 build_prompt() 里的需求说明文案包上 t()。

为什么单独写一个脚本：这一段是多段隐式拼接的长文本，
用正则替换容易改坏；这里用精确的「原文 -> 改写后」映射，
并在写回后做语法检查，坏了就回滚。
"""
import io
import os
import py_compile
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "src", "app.py")

REPL = [
    ('return v if v else PLACEHOLDER', 'return v if v else t(PLACEHOLDER)'),
    ('lines.append("【我完全不懂技术，下面是我的需求，请你帮我把这个软件做出来。】")',
     'lines.append(t("【我完全不懂技术，下面是我的需求，请你帮我把这个软件做出来。】"))'),
    ('lines.append("先说清楚我们的合作方式：")',
     'lines.append(t("先说清楚我们的合作方式："))'),
    ('''lines.append("1. 如果下面有哪里没写清楚、或者你觉得会影响结果，请先问我（一次问 2~5 个，"
                 "用大白话问，不要用技术名词考我），问清楚再动手。")''',
     '''lines.append(t("1. 如果下面有哪里没写清楚、或者你觉得会影响结果，请先问我（一次问 2~5 个，"
                   "用大白话问，不要用技术名词考我），问清楚再动手。"))'''),
    ('''lines.append("2. 技术方案（用什么语言、什么工具、怎么打包）你自己决定；"
                 "如果有影响我使用的取舍，告诉我两个选项各自的好处就行。")''',
     '''lines.append(t("2. 技术方案（用什么语言、什么工具、怎么打包）你自己决定；"
                   "如果有影响我使用的取舍，告诉我两个选项各自的好处就行。"))'''),
    ('''lines.append("3. 请你自己动手做完并自己测试通过，最后给我一个能直接双击打开、"
                 "或能直接打开的成品，并告诉我放在哪个路径、怎么再次打开。")''',
     '''lines.append(t("3. 请你自己动手做完并自己测试通过，最后给我一个能直接双击打开、"
                   "或能直接打开的成品，并告诉我放在哪个路径、怎么再次打开。"))'''),
    ('lines.append("4. 交付时请一并告诉我：怎么用、怎么备份数据、有哪些你没做到或做不到的地方。")',
     'lines.append(t("4. 交付时请一并告诉我：怎么用、怎么备份数据、有哪些你没做到或做不到的地方。"))'),
    ('lines.append("5. 不要只给我代码和说明书让我自己想办法运行，我看不懂。")',
     'lines.append(t("5. 不要只给我代码和说明书让我自己想办法运行，我看不懂。"))'),
    ('lines.append("我的需求")', 'lines.append(t("我的需求"))'),
    ('lines.append("  选择：" + val)', 'lines.append(t("  选择：") + val)'),
    ('lines.append("  " + PLACEHOLDER)', 'lines.append("  " + t(PLACEHOLDER))'),
    ('lines.append("目标平台（重要）")', 'lines.append(t("目标平台（重要）"))'),
    ('lines.append("补充情况")', 'lines.append(t("补充情况"))'),
    ('lines.append("· 我的水平：完全不懂编程，请用大白话解释，并一步一步教我怎么用。")',
     'lines.append(t("· 我的水平：完全不懂编程，请用大白话解释，并一步一步教我怎么用。"))'),
    ('lines.append("· 我希望你高度自主地完成：能自己决定的事就别问我，只在真正需要我选择时才问。")',
     'lines.append(t("· 我希望你高度自主地完成：能自己决定的事就别问我，只在真正需要我选择时才问。"))'),
    ('lines.append("· 做完请告诉我：结果文件在哪个文件夹、以后怎么再打开它。")',
     'lines.append(t("· 做完请告诉我：结果文件在哪个文件夹、以后怎么再打开它。"))'),
    ('lines.append("如果上面的信息还不够你做决定，请直接问我；信息够的话，请现在就开工。")',
     'lines.append(t("如果上面的信息还不够你做决定，请直接问我；信息够的话，请现在就开工。"))'),
    ('lines.append("=" * 46)', 'lines.append("=" * 46)'),   # 分隔线不翻
]


def compile_ok(path):
    try:
        with tempfile.TemporaryDirectory() as td:
            py_compile.compile(path, cfile=os.path.join(td, "x.pyc"), doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)


def main():
    src = io.open(PATH, encoding="utf-8", newline=None).read()
    backup = src
    applied, skipped = 0, []
    for old, new in REPL:
        if old == new:
            continue
        if new in src and old not in src:
            skipped.append("已是包好的")
            continue
        if old not in src:
            skipped.append("找不到: " + old[:60])
            continue
        src = src.replace(old, new)
        applied += 1

    if src == backup:
        print("没有需要改的地方")
        return 0

    io.open(PATH, "w", encoding="utf-8", newline="\r\n").write(src)
    ok, err = compile_ok(PATH)
    if not ok:
        io.open(PATH, "w", encoding="utf-8", newline="\r\n").write(backup)
        print("✘ 语法错误，已回滚：%s" % (err or "").split("\n")[0])
        return 1

    print("已包 t() 共 %d 处，语法通过" % applied)
    for s in skipped:
        print("  跳过: %s" % s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
