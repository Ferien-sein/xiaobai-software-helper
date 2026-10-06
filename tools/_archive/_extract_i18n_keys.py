# -*- coding: utf-8 -*-
"""临时工具：从 app.py 抽出所有含中文的字符串字面量（供制作语言包用）。

- 用 AST，所以 ("a" "b") 隐式拼接、跨行拼接都会被拼成完整字符串。
- 文档字符串（模块/函数/类 docstring）不算，它们不进语言包。
- 输出 TSV：行号 TAB 字符串（repr 形式），方便逐条翻译。
"""
import ast
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "src", "app.py")

src = io.open(PATH, encoding="utf-8").read()
tree = ast.parse(src)

cn_re = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")
han_re = re.compile(r"[\u4e00-\u9fff]")

# 收集 docstring 节点
docstrings = set()
for node in ast.walk(tree):
    if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            docstrings.add(id(body[0].value))

found = []          # (lineno, value)
seen = {}
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if id(node) in docstrings:
            continue
        v = node.value
        if not han_re.search(v):
            continue
        found.append((node.lineno, v))
        seen.setdefault(v, node.lineno)

found.sort(key=lambda x: x[0])

out = []
out.append("# 含中文的字符串字面量（按出现顺序，去重）")
out.append("# 共 %d 处，%d 条唯一" % (len(found), len(seen)))
out.append("")
for v, ln in sorted(seen.items(), key=lambda kv: kv[1]):
    out.append("=== L%d ===" % ln)
    out.append(v)
    out.append("")

text = "\n".join(out)
dest = os.path.join(ROOT, "tools", "_strings_dump.txt")
io.open(dest, "w", encoding="utf-8", newline="\n").write(text)
sys.stdout.write("wrote %s : %d unique strings\n" % (dest, len(seen)))

# 另外输出一份 JSON（供生成语言包用）
import json  # noqa: E402

dest_json = os.path.join(ROOT, "tools", "_strings.json")
with io.open(dest_json, "w", encoding="utf-8", newline="\n") as f:
    json.dump(sorted(seen.items(), key=lambda kv: kv[1]),
              f, ensure_ascii=False, indent=1)
sys.stdout.write("wrote %s\n" % dest_json)
