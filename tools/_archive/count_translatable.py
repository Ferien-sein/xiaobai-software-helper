# -*- coding: utf-8 -*-
"""量化 app.py 的翻译工作量：哪些是用户可见字符串，哪些是注释/键名不需要翻。

结论用于判断 i18n 的工作量，避免拍脑袋估计。
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "src", "app.py")
src = io.open(PATH, encoding="utf-8").read()
lines = src.splitlines()

cn_re = re.compile(r"[\u4e00-\u9fff]")

# 分类
buckets = {
    "注释与文档字符串（不用翻）": [],
    "纯中文行但可能是 UI 文案": [],
    "含中文的赋值/调用": [],
    "含中文的其它": [],
}

in_doc = False
for i, ln in enumerate(lines, 1):
    if not cn_re.search(ln):
        continue
    s = ln.strip()
    if s.startswith("#"):
        buckets["注释与文档字符串（不用翻）"].append((i, s))
    elif s.startswith('"""') or s.startswith("'''") or in_doc:
        buckets["注释与文档字符串（不用翻）"].append((i, s))
        if s.count('"""') == 1:
            in_doc = not in_doc
    elif re.match(r'^(?:[a-zA-Z_]+\s*=|return|yield|raise|print\()', s) or '= "' in s or "= '" in s:
        buckets["含中文的赋值/调用"].append((i, s))
    elif s.startswith('"') or s.startswith("'"):
        buckets["纯中文行但可能是 UI 文案"].append((i, s))
    else:
        buckets["含中文的其它"].append((i, s))

print("文件总行数: %d" % len(lines))
print("含中文行数: %d" % len([l for l in lines if cn_re.search(l)]))
print("中文字符总数: %d" % len(cn_re.findall(src)))
print()
for k, v in buckets.items():
    chars = sum(len(cn_re.findall(s)) for _, s in v)
    print("%-28s %4d 行  %5d 个中文字" % (k, len(v), chars))

print()
print("=" * 70)
print("最占篇幅的「含中文的赋值/调用」（前 30 条按中文字数排序）")
print("=" * 70)
rank = sorted(buckets["含中文的赋值/调用"], key=lambda x: -len(cn_re.findall(x[1])))
for i, s in rank[:30]:
    print("  L%-5d %4d 字  %s" % (i, len(cn_re.findall(s)), s[:78]))

print()
print("=" * 70)
print("UI 相关字符串的分布（按函数/区块）")
print("=" * 70)
# 找出所有顶层 def/class 及其行号，统计每个区块里的中文字数
marks = [(i, ln.strip()) for i, ln in enumerate(lines, 1)
         if re.match(r"^(def |class |[A-Z_]+ = )", ln)]
for idx, (ln_no, name) in enumerate(marks):
    end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines) + 1
    seg = "\n".join(lines[ln_no - 1:end - 1])
    n = len(cn_re.findall(seg))
    if n > 40:
        print("  L%-5d %5d 个中文字   %s" % (ln_no, n, name[:70]))
