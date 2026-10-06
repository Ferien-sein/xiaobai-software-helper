# -*- coding: utf-8 -*-
"""补上最后几处漏翻译的界面文案。

其中 L2351 是个真 bug：输入框有内容时状态标签会写回硬编码的「待填写」，
所以英文界面下「填了」反而变成中文 —— 只有实际看界面才会发现。
"""
import io
import os
import py_compile
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "src", "app.py")

REPL = [
    # 状态标签（真 bug：填内容后变回中文）
    ('status.configure(text="待填写", style="QHint.TLabel")',
     'status.configure(text=t("待填写"), style="QHint.TLabel")'),
    # 顶部三步说明
    ('ttk.Label(head, text="① 左边填一填   →   ② 右边自动生成   →   ③ 点「复制需求」粘贴给 AI"',
     'ttk.Label(head, text=t("① 左边填一填   →   ② 右边自动生成   →   ③ 点「复制需求」粘贴给 AI")'),
    ('"　·　每题下面有「看例子」，标着「可选」的可以不填",',
     't("　·　每题下面有「看例子」，标着「可选」的可以不填"),'),
    # 历史记录页说明
    ('ttk.Label(bar, text="你点过「保存到文件」的需求都收在这里，随时可以找回来改。",',
     'ttk.Label(bar, text=t("你点过「保存到文件」的需求都收在这里，随时可以找回来改。"),'),
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
    n = 0
    for old, new in REPL:
        if new in src and old not in src:
            print("  跳过（已处理）: %s" % old[:50])
            continue
        if old not in src:
            print("  ✘ 找不到: %s" % old[:70])
            continue
        src = src.replace(old, new, 1)
        n += 1

    if src == backup:
        print("没有改动")
        return 0

    io.open(PATH, "w", encoding="utf-8", newline="\r\n").write(src)
    ok, err = compile_ok(PATH)
    if not ok:
        io.open(PATH, "w", encoding="utf-8", newline="\r\n").write(backup)
        print("✘ 语法错误，已回滚: %s" % (err or "").split("\n")[0])
        return 1
    print("已修 %d 处，语法通过" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
