# -*- coding: utf-8 -*-
"""辅助脚本：核对「非静态实参」的 t() 调用点是否也覆盖到了。

check_i18n.py 只看 t("字面量")，像 t(name) / t(q["title"]) 这类
只能运行时才知道值的调用点它看不见。本脚本把这些调用点列出来，
并把 app.py 里相关的字面量集合（PAGES、QUESTIONS 的 title/hint/help/
example/options）逐个拿去语言包里核对，报告运行时才会暴露的漏翻。

用法: python tools/_xbsh_check_runtime_keys.py
只读，不修改任何文件。
"""
import ast
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, HERE)

from check_i18n import catalog_of  # noqa: E402

EXEMPT = {
    "需求存档", "使用说明.txt", "提示词模板.txt", "显示诊断.txt",
    "===== 原始答案（给程序自己看，不用管） =====", "===== 原始答案结束 =====",
    "小白造软件助手", "微软雅黑", "zh-CN", "zh-TW", "en",
}


def static_str_list(node):
    """取出一个字面量列表里的字符串（PAGES 那种）。"""
    out = []
    if isinstance(node, (ast.List, ast.Tuple)):
        for e in node.elts:
            if isinstance(e, ast.Constant) and isinstance(e.value, str):
                out.append(e.value)
    return out


def questions_values(tree):
    """取出 QUESTIONS 里所有会被 t() 拿到的字符串值。"""
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        name = getattr(node.targets[0], "id", "")
        if name == "QUESTIONS" and isinstance(node.value, ast.List):
            for item in node.value.elts:
                if not isinstance(item, ast.Call):
                    continue
                for kw in item.keywords:
                    if kw.arg in ("title", "hint", "help", "example"):
                        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            out.append(kw.value.value)
                    elif kw.arg == "options":
                        out.extend(static_str_list(kw.value))
    return out


def other_assigns(tree):
    """PAGES 之类的模块级字面量列表。"""
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            name = getattr(node.targets[0], "id", "")
            if name in ("PAGES", "LANGS"):
                out[name] = static_str_list(node.value)
    return out


def main():
    src = os.path.join(SRC, "app.py")
    tree = ast.parse(io.open(src, encoding="utf-8").read())
    text = io.open(src, encoding="utf-8").read().splitlines()

    print("== 非静态实参的 t() 调用点（check_i18n.py 看不到）==")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not (isinstance(fn, ast.Name) and fn.id == "t") or not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            continue
        print("  L%-5d %s" % (node.lineno, text[node.lineno - 1].strip()[:90]))

    runtime_keys = []
    assigns = other_assigns(tree)
    runtime_keys.extend(assigns.get("PAGES", []))
    runtime_keys.extend(questions_values(tree))
    seen = set()
    runtime_keys = [k for k in runtime_keys if k not in EXEMPT and not (k in seen or seen.add(k))]

    print()
    print("== 运行时才会查表的字面量（PAGES + QUESTIONS）: %d 个 ==" % len(runtime_keys))
    bad = 0
    for lang, fname in (("zh-TW", "i18n_zh_tw.py"), ("en", "i18n_en.py")):
        cat, err = catalog_of(os.path.join(SRC, fname))
        if err:
            print("  %s: %s" % (lang, err))
            bad += 1
            continue
        missing = [k for k in runtime_keys if k not in cat]
        print("  %s: 缺 %d 条" % (lang, len(missing)))
        for k in missing:
            print("      %r" % (k[:80],))
        bad += len(missing)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
