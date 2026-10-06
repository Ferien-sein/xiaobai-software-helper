# -*- coding: utf-8 -*-
"""抢救被写坏的繁体语言包。

现场：文件尾部少了 CATALOG 的收尾 `}`，且补丁注释被插进了键值对中间，
导致 AST 直接解析失败（IndentationError）。

做法：
  1. **不靠 AST**，改成逐行容错解析 —— 只认「键行 = 4 空格缩进的 'xxx':」，
     下一行是「8 空格缩进的 'yyy',」。这样坏掉的尾部也不会影响已好的条目。
  2. 把解析出的条目与 app.py 里 t() 的实参核对，缺的补上。
  3. 用 json.dumps 重新生成整个文件（转义由 json 保证，不会再手写出错），
     并做语法 + 条目数校验后才写盘。
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, HERE)

from check_i18n import t_call_args, EXEMPT  # noqa: E402

PATH = os.path.join(SRC, "i18n_zh_tw.py")

KEY_RE = re.compile(r"^    (\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'):\s*$")
VAL_RE = re.compile(r"^        (\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')\s*,?\s*\}?\s*$")


def salvage(text):
    """逐行抽出 (键, 值)，跳过注释与坏行。"""
    pairs = {}
    pending_key = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = KEY_RE.match(line)
        if m:
            pending_key = m.group(1)
            continue
        if pending_key is not None:
            m2 = VAL_RE.match(line)
            if m2:
                try:
                    k = json.loads(pending_key) if pending_key.startswith('"') else eval(pending_key)  # noqa: S307
                    v = json.loads(m2.group(1)) if m2.group(1).startswith('"') else eval(m2.group(1))  # noqa: S307
                except Exception:
                    pending_key = None
                    continue
                pairs[k] = v
            pending_key = None
    return pairs


def main():
    raw = io.open(PATH, encoding="utf-8", newline=None).read()
    pairs = salvage(raw)
    print("抢救出 %d 条" % len(pairs))

    # 与 app.py 的 t() 实参核对，补缺口
    statics, _ = t_call_args(os.path.join(SRC, "app.py"))
    uniq = sorted({a for a in statics if isinstance(a, str) and a not in EXEMPT})
    missing = [k for k in uniq if k not in pairs]
    print("对照 t() 实参：缺 %d 条" % len(missing))

    S2T = {
        "测": "測", "确": "確", "误": "誤", "统": "統", "应": "應", "该": "該",
        "选": "選", "择": "擇", "现": "現", "决": "決", "问": "問", "题": "題",
        "项": "項", "态": "態", "线": "線", "网": "網", "页": "頁", "览": "覽",
        "档": "檔", "夹": "夾", "复": "複", "制": "製", "粘": "黏", "贴": "貼",
        "储": "儲", "诊": "診", "断": "斷", "显": "顯", "语": "語", "简": "簡",
        "户": "戶", "习": "習", "惯": "慣", "删": "刪", "载": "載", "换": "換",
        "颜": "顏", "浅": "淺", "标": "標", "准": "準", "当": "當", "这": "這",
        "门": "門", "将": "將", "会": "會", "丢": "丟", "读": "讀", "写": "寫",
        "缓": "緩", "冲": "衝", "软": "軟", "个": "個", "为": "為", "对": "對",
        "时": "時", "发": "發", "开": "開", "关": "關", "单": "單", "录": "錄",
        "规": "規", "则": "則", "报": "報", "总": "總", "验": "驗", "资": "資",
        "讯": "訊", "数": "數", "电": "電", "体": "體", "图": "圖", "级": "級",
        "击": "擊", "约": "約",
    }

    def to_tw(s):
        return "".join(S2T.get(c, c) for c in s)

    for k in missing:
        pairs[k] = to_tw(k)
        print("   + %r -> %r" % (k[:50], pairs[k][:50]))

    # 用 json.dumps 重新生成：转义交给 json，杜绝手写错
    out = [
        "# -*- coding: utf-8 -*-",
        '"""繁體中文語言包。',
        "",
        "鍵 = app.py 裡的簡體中文原文（逐字一致）",
        "值 = 繁體中文譯文",
        "",
        "未收錄的條目會原樣顯示簡體 —— 漏翻不會崩，",
        "但 tools/check_i18n.py 會在發布前報出來。",
        '"""',
        "",
        "CATALOG = {",
    ]
    for k in sorted(pairs):
        out.append("    %s: %s," % (json.dumps(k, ensure_ascii=False),
                                    json.dumps(pairs[k], ensure_ascii=False)))
    out.append("}")
    out.append("")
    text = "\n".join(out)

    import ast
    tree = ast.parse(text)          # 语法不过就不写盘
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            n = len(node.value.keys)
    assert n == len(pairs), "条目数不符: %d != %d" % (n, len(pairs))

    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("\n已重写 %s：%d 条，语法通过" % (os.path.basename(PATH), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
