# -*- coding: utf-8 -*-
"""去掉指定文件/目录下文本文件的 BOM。

用 Python 而不是 PowerShell —— PowerShell 5.1 的 Set-Content 默认按 ANSI 写，
会把中文写坏（这正是本项目踩过的坑），改文本文件一律走 Python。
"""
import os
import sys

EXT = {".py", ".md", ".txt", ".json", ".yml", ".yaml", ".bat", ".cmd", ".mjs", ".js", ".ps1"}
BOM = b"\xef\xbb\xbf"


def iter_files(paths):
    for p in paths:
        p = os.path.abspath(p)
        if os.path.isfile(p):
            yield p
            continue
        for base, dirs, names in os.walk(p):
            dirs[:] = [d for d in dirs if d not in
                       {"node_modules", ".git", "__pycache__", "build", "dist"}]
            for n in names:
                if os.path.splitext(n)[1].lower() in EXT:
                    yield os.path.join(base, n)


def main():
    args = sys.argv[1:]
    if not args:
        args = [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    fixed = 0
    for path in iter_files(args):
        raw = open(path, "rb").read()
        if raw[:3] == BOM:
            open(path, "wb").write(raw[3:])
            print("去 BOM: %s" % path)
            fixed += 1
    print("\n处理 %d 个文件" % fixed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
