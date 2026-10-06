# -*- coding: utf-8 -*-
"""產生 src/i18n_zh_tw.py，並校驗鍵是否與 app.py 逐字一致。

用法：
    python tools/_gen_i18n_zh_tw.py --check   # 只校驗，不寫檔
    python tools/_gen_i18n_zh_tw.py           # 寫檔
"""
import ast
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "src", "app.py")
OUT = os.path.join(ROOT, "src", "i18n_zh_tw.py")
DATA_DIR = r"E:\APP\DeepSeek工作区"
sys.path.insert(0, DATA_DIR)
import xbsh_i18n_tw_data as D  # noqa: E402

TR = D.TR
han_re = re.compile(r"[\u4e00-\u9fff]")

# 不進語言包的字面量：檔名/路徑/存檔標記/程式內部字串
SKIP_EXACT = {
    "需求存档",          # 資料夾名（實際路徑，改了會找不到既有存檔）
    "使用说明.txt",      # 檔名
    "提示词模板.txt",    # 檔名
    "显示诊断.txt",      # 檔名
    "===== 原始答案（给程序自己看，不用管） =====",   # 存檔格式標記
    "===== 原始答案结束 =====",                       # 存檔格式標記
    "小白造软件助手",    # APP_NAME：產品名，簡繁相同且用於視窗標題/存檔名
    "简体中文",          # i18n.LANG_NAMES 自帶
    "繁體中文",
    "English",
}


def app_strings():
    src = io.open(APP, encoding="utf-8").read()
    tree = ast.parse(src)
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docs.add(id(body[0].value))
    seen = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in docs:
                continue
            v = node.value
            if han_re.search(v):
                seen.setdefault(v, node.lineno)
    return seen


def main():
    strings = app_strings()
    print("app.py 含中文的字面量：%d 條" % len(strings))

    missing = [v for v in strings if v not in TR and v not in SKIP_EXACT]
    unused = [k for k in TR if k not in strings]

    print("翻譯條目：%d" % len(TR))
    print("跳過（檔名/標記/產品名）：%d 條" % len([v for v in strings if v in SKIP_EXACT]))
    print("未覆蓋：%d 條" % len(missing))
    for v in missing:
        print("   MISSING L%s: %r" % (strings[v], v))
    print("語言包裡多餘（app.py 找不到）：%d 條" % len(unused))
    for k in unused:
        print("   EXTRA: %r" % k)

    if "--check" in sys.argv:
        return 1 if missing else 0

    # 產生檔案：沿用 app.py 的出現順序
    order = sorted(strings.items(), key=lambda kv: kv[1])
    lines = [
        "# -*- coding: utf-8 -*-",
        '"""繁體中文語言包。',
        "",
        "鍵是简体中文原文（与 app.py 里的字符串**逐字一致**），值是繁體中文譯文。",
        "",
        "由 tools/_gen_i18n_zh_tw.py 產生（翻譯資料在該腳本內），請勿手改鍵。",
        '"""',
        "",
        "CATALOG = {",
    ]
    n = 0
    for v, ln in order:
        if v not in TR:
            continue
        lines.append("    %r: %r," % (v, TR[v]))
        n += 1
    lines.append("}")
    lines.append("")
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("已寫入 %s：%d 條" % (OUT, n))


if __name__ == "__main__":
    sys.exit(main())
