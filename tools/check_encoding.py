# -*- coding: utf-8 -*-
"""文本文件编码守卫。

为什么需要它：我（AI）用 PowerShell 的 Set-Content 改过几次源码，
而 PowerShell 5.1 不指定 -Encoding 时默认按 ANSI(GBK) 写，
会把中文源码写成乱码；还有几次写进了 BOM。
这类问题**不会报错**，只会静默产出坏文件，必须有一道自动检查。

检查内容：
  1. 严格 UTF-8 可解码（否则就是被按 GBK 写过）
  2. 无 BOM
  3. 无 U+FFFD 替换字符
  4. 无 mojibake 特征（扩展A区汉字、常见乱码块）
  5. Python 文件语法可编译
  6. 行尾统一（不混用 CRLF 与裸 LF）

用法:
  python tools/check_encoding.py            # 检查仓库里所有文本文件
  python tools/check_encoding.py <路径>...  # 检查指定文件/目录
退出码非 0 表示发现问题。
"""
import io
import os
import sys
import tempfile

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

CHECK_EXT = {".py", ".md", ".txt", ".json", ".yml", ".yaml", ".bat", ".cmd", ".mjs", ".js", ".ps1"}

# 常见 mojibake 落点：中文被按 GBK 破坏后常落在扩展A区
MOJIBAKE_BLOCKS = [
    (0x3400, 0x4DBF),   # CJK 扩展A
    (0xE000, 0xF8FF),   # 私用区
]


def looks_mojibake(text):
    hits = []
    for ch in text:
        o = ord(ch)
        for lo, hi in MOJIBAKE_BLOCKS:
            if lo <= o <= hi:
                hits.append(ch)
                break
        if len(hits) >= 5:
            break
    return hits


# 有意使用 utf-8-sig（BOM）的文件：给 Windows 记事本兼容用的输出文件。
# 这些 BOM 是设计的一部分，不该报错；源码里的 BOM 才是问题。
EXPECT_BOM = {
    "sample-output.txt",
}
# 存档目录是程序运行产物（用户保存的需求），不参与仓库检查
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "build", "dist", "_archive", "需求存档"}


def is_expected_bom(path):
    return os.path.basename(path) in EXPECT_BOM


def check_file(path):
    problems = []
    notices = []
    raw = open(path, "rb").read()

    has_bom = raw[:3] == b"\xef\xbb\xbf"
    if has_bom:
        if is_expected_bom(path):
            notices.append("含 BOM（此文件有意如此，为记事本兼容）")
        else:
            problems.append("含 BOM")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        problems.append("不是合法 UTF-8（很可能被按 ANSI/GBK 写过）: %s" % e)
        return problems, None, notices

    if "\ufffd" in text:
        n = text.count("\ufffd")
        problems.append("含 %d 个替换字符 U+FFFD（说明曾用错误编码读写）" % n)

    hits = looks_mojibake(text)
    if hits:
        problems.append("疑似 mojibake（扩展A区/私用区字符 %r）" % "".join(hits[:5]))

    crlf = raw.count(b"\r\n")
    lone_lf = raw.count(b"\n") - crlf
    if crlf and lone_lf:
        problems.append("行尾混用（CRLF %d 处、裸 LF %d 处）" % (crlf, lone_lf))

    if path.endswith(".py"):
        try:
            import py_compile

            with tempfile.TemporaryDirectory() as td:
                py_compile.compile(path, cfile=os.path.join(td, "x.pyc"), doraise=True)
        except py_compile.PyCompileError as e:
            problems.append("语法错误: %s" % str(e).split("\n")[0])
        except Exception as e:  # noqa: BLE001
            problems.append("编译检查失败: %r" % (e,))

    return problems, text, notices


def iter_targets(args):
    if not args:
        # 默认：本文件所在仓库的上一级
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        args = [root]
    for a in args:
        a = os.path.abspath(a)
        if os.path.isfile(a):
            yield a
            continue
        for base, dirs, names in os.walk(a):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for n in names:
                if os.path.splitext(n)[1].lower() in CHECK_EXT:
                    yield os.path.join(base, n)


def main():
    bad = 0
    total = 0
    for path in iter_targets(sys.argv[1:]):
        total += 1
        result = check_file(path)
        problems = result[0]
        notices = result[2] if len(result) > 2 else []
        if notices and not problems:
            print("·  %s" % os.path.basename(path))
            for n in notices:
                print("     - %s" % n)
        if problems:
            bad += 1
            print("[X] %s" % path)
            for p in problems:
                print("    - %s" % p)

    print()
    print("检查 %d 个文件，%d 个有问题" % (total, bad))
    if bad:
        print("提示：PowerShell 5.1 的 Set-Content 不指定 -Encoding 时默认 ANSI，")
        print("      会把中文源码写坏。改文本文件请用 Python 或编辑器，不要用它。")
    return 1 if bad else 0


if __name__ == "__main__":
    _force_utf8_output()
    sys.exit(main())
