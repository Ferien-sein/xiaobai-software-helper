# -*- coding: utf-8 -*-
"""把 QUESTIONS 里所有 title 的编号按出现顺序重排为 1..N。

为什么用「重排」而不是「替换 num→num+1」：
前一次我用后者，结果 `title="4. ` 先命中了新插入的那个问题，
导致出现两个 5、缺一个 4。按顺序赋值不会受替换顺序影响。

用 Python 读写（不用 PowerShell：它的 Set-Content 默认 ANSI 会写坏中文）。
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "src", "app.py")

src = io.open(PATH, encoding="utf-8", newline=None).read()

start = src.index("QUESTIONS = [")
end = src.index("ABOUT_TEXT = ")
seg = src[start:end]

# 找到所有 title= 的位置
pattern = re.compile(r'(title=")(\d+)(\. )')
matches = list(pattern.finditer(seg))
print("找到 %d 个 title 编号" % len(matches))
old = [int(m.group(2)) for m in matches]
print("原编号:", old)

# 从后往前替换，避免位移影响
parts = []
last = 0
for i, m in enumerate(matches):
    parts.append(seg[last:m.start()])
    parts.append("%s%d%s" % (m.group(1), i + 1, m.group(3)))
    last = m.end()
parts.append(seg[last:])
new_seg = "".join(parts)

new = [int(m.group(2)) for m in pattern.finditer(new_seg)]
print("新编号:", new)
assert new == list(range(1, len(new) + 1)), "重排失败: %s" % new

src = src[:start] + new_seg + src[end:]
io.open(PATH, "w", encoding="utf-8", newline="\r\n").write(src)

# 复查写回结果
back = io.open(PATH, encoding="utf-8", newline=None).read()
seg2 = back[back.index("QUESTIONS = ["):back.index("ABOUT_TEXT = ")]
final = [int(m.group(2)) for m in pattern.finditer(seg2)]
print("写回后复查:", final)
print("OK" if final == list(range(1, len(final) + 1)) else "仍有问题")
