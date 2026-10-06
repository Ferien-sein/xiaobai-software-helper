# -*- coding: utf-8 -*-
"""插入「锁定界面语言」——定稿版（插在第一个模块级 import 之前）。

## 为什么必须做

真事故：CI（runner 是 en-US）上 selftest_platform.py 11 项失败，
报「系统题的选项里缺少 安卓」，列出来的选项**全是英文**。
`i18n.detect_lang()` 按系统区域探测成英文，而自检硬编码中文断言。
本机一直是中文，所以从来没暴露。

## 前三版的教训（都真踩过，写在这里免得以后再犯）

1. 第一版按「第一处 import app」插入 → 4 个文件没匹配到，且留下重复注释
2. 第二版的「删旧块」逻辑有 bug，**把 docstring 删坏**（已从 git 恢复）
3. 第三版仍按「第一处依赖 import」→ 对 check_i18n.py 会插进**函数内部的 try 里**
   （模块级缩进的语句插进缩进块 → 语法错误；守卫拦住了没写坏）
   对 check_encoding.py / selftest_tooling.py 又匹配不到（它们用 importlib /
   函数内 import）

## 定稿做法

插在**第一个模块级（第 0 列）import 之前**。
理由：依赖 i18n 的 import 必然排在它之后；而且模块级插入永远不会破坏缩进结构。
道理简单、不会出错。行数只增不减（安全闸）。

先决条件：文件是干净的（无旧标记）。有旧标记直接报错，不做删除。
"""
import ast
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")

MARK = "XBSH_LANG_LOCKED"
BLOCK = (
    "# ★ 锁定界面语言（" + MARK + "）：这些检查/自检脚本的输出与断言都基于简体中文，\n"
    "#   而 i18n 会按系统区域自动探测语言 —— 在英文机器 / CI 上会探测成英文，\n"
    "#   断言就全挂（GitHub runner 上真踩过：selftest_platform 11 项失败）。\n"
    "#   ★ 用 = 不用 setdefault：环境里已有 XBSH_LANG 时 setdefault 不覆盖，锁会失效。\n"
    "#   插在第一个模块级 import 之前，保证任何依赖 i18n 的 import 都在它之后。\n"
    'os.environ["XBSH_LANG"] = "zh-CN"\n'
)

TARGETS = [
    "check_encoding.py", "check_i18n.py", "check_option_uniqueness.py",
    "selftest_adaptive.py", "selftest_contrast.py", "selftest_functional.py",
    "selftest_lookup.py", "selftest_lookup_quality.py", "selftest_lookup_ui.py",
    "selftest_pages.py", "selftest_platform.py", "selftest_scroll.py",
    "selftest_tooling.py", "selftest_ui_scale.py", "selftest_wheel.py",
]

MODULE_IMPORT = re.compile(r'^(?:import|from)\s+\w', re.M)
# 只匹配**代码**里的依赖 import：
# 必须顶格、且行尾不能是文档字符串的收尾（避免匹配到
# 「不启动界面：直接 import app，检查…」这种写在 docstring 里的说明 —— 真踩过）
CODE_IMPORT = re.compile(r'^(?:import|from)\s+\w[\w.]*', re.M)


def insert_point(src, tree):
    """算出该插到哪一行之前。

    ★ 用 AST 找文档字符串的结束位置，而不是正则找第一行 import：
      selftest_platform.py 的 docstring 里有一句「不启动界面：直接 import app，…」，
      正则会把那句当成代码，把锁插进 docstring 里面 —— 真踩过。

      规则：有 docstring 就插在它之后；再跳过紧随其后的连续 import 之前插入，
      实际上就是「docstring 之后、第一行代码之前」。
    """
    lines = src.splitlines(keepends=True)
    start = 0
    body = getattr(tree, "body", [])
    if body and isinstance(body[0], ast.Expr) and isinstance(
            getattr(body[0], "value", None), ast.Constant) and isinstance(
                getattr(body[0].value, "value", None), str):
        start = body[0].end_lineno          # docstring 的结束行（1-based）
    # 从 docstring 之后往下找第一个**代码**行（跳过注释与空行）
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if not s or s.startswith("#"):
            continue
        return i
    return len(lines)


def patch(fname):
    path = os.path.join(TOOLS, fname)
    if not os.path.exists(path):
        return "不存在", 0
    src = io.open(path, encoding="utf-8", newline=None).read()
    if MARK in src:
        return "已有标记（跳过，不删任何东西）", 0

    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return "原文件语法就有问题: %s" % e, 0

    idx = insert_point(src, tree)
    lines = src.splitlines(keepends=True)
    head = "".join(lines[:idx])

    block = BLOCK
    if not re.search(r'^(?:import\s+os\b|from\s+os\s+import\b)', head, re.M):
        block = "import os\n" + BLOCK
    out = head + ("\n" if head and not head.endswith("\n\n") else "") + \
        block + "\n" + "".join(lines[idx:])

    try:
        ast.parse(out)
    except SyntaxError as e:
        return "语法错误，跳过: %s" % e, 0
    added = out.count("\n") - src.count("\n")
    if added < 1:
        return "行数没增加（异常），跳过", 0
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    return "已加（第 %d 行前，+%d 行）" % (idx + 1, added), added


bad = 0
for f in TARGETS:
    r, _ = patch(f)
    if "跳过" in r or "找不到" in r or "不存在" in r:
        bad += 1
    print("  %-32s %s" % (f, r))

print()
print("=== 复查：标记必须在所有依赖 i18n 的 import 之前 ===")
DEP = re.compile(r'(import\s+app\b|import\s+github_lookup\b|import\s+i18n\b'
                 r'|import\s+platform_info\b|import\s+questionnaire\b)')
for f in TARGETS:
    src = io.open(os.path.join(TOOLS, f), encoding="utf-8").read()
    mi = src.find(MARK)
    m = DEP.search(src)
    di = m.start() if m else None
    ok = mi >= 0 and (di is None or mi < di)
    if not ok:
        bad += 1
    print("    %s %-32s 标记@%s  首个依赖 import@%s" % (
        "✔" if ok else "★", f, mi if mi >= 0 else "-", di if di is not None else "-"))

print()
print("  仍有问题: %d 个" % bad)
sys.exit(1 if bad else 0)
