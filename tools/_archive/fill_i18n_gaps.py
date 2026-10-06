# -*- coding: utf-8 -*-
"""把「t() 实参有、语言包里没有」的键自动补齐。

为什么需要它：我手动补键时又加错了（把别处的文案当成键，
还漏了带 \n 的变体）。根源是**靠人眼比对字符串**不可靠。

这个工具的做法：
  1. 从 app.py 抽出所有 t() 的字符串实参（这是运行期真正查表的值）
  2. 找出两个语言包里没有的那些
  3. 从"参考语言包"里取译文 —— 简体就是原文，所以
     zh-TW 用一份简→繁的字符映射做兜底，en 则必须人工提供
  4. 写回并校验语法与条目数

对 en 包：缺的键无法机械翻译，工具会**只列出待翻译清单**，
由人（或翻译代理）补。这里不假装能自动翻英文。
"""
import ast
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, os.path.join(ROOT, "tools"))

from check_i18n import t_call_args, catalog_of, EXEMPT  # noqa: E402


def missing_keys(fname):
    statics, _ = t_call_args(os.path.join(SRC, "app.py"))
    uniq = sorted({a for a in statics if isinstance(a, str) and a not in EXEMPT})
    cat, err = catalog_of(os.path.join(SRC, fname))
    if err:
        raise SystemExit("%s: %s" % (fname, err))
    return [k for k in uniq if k not in cat], cat


# 简 -> 繁 的常用字映射（只用于兜底补齐，正式译文仍以语言包为准）
S2T = {
    "软": "軟", "个": "個", "为": "為", "对": "對", "时": "時", "发": "發",
    "开": "開", "关": "關", "单": "單", "录": "錄", "规": "規", "则": "則",
    "报": "報", "总": "總", "验": "驗", "资": "資", "讯": "訊", "数": "數",
    "电": "電", "体": "體", "图": "圖", "级": "級", "击": "擊", "约": "約",
    "测": "測", "确": "確", "误": "誤", "统": "統", "应": "應", "该": "該",
    "选": "選", "择": "擇", "现": "現", "决": "決", "定": "定", "问": "問",
    "题": "題", "项": "項", "态": "態", "线": "線", "网": "網", "页": "頁",
    "览": "覽", "档": "檔", "夹": "夾", "复": "複", "制": "製", "粘": "黏",
    "贴": "貼", "储": "儲", "存": "存", "诊": "診", "断": "斷", "显": "顯",
    "示": "示", "语": "語", "言": "言", "简": "簡", "户": "戶", "端": "端",
    "习": "習", "惯": "慣", "删": "刪", "除": "除", "载": "載", "入": "入",
    "换": "換", "颜": "顏", "色": "色", "暗": "暗", "浅": "淺", "标": "標",
    "准": "準", "更": "更", "大": "大", "最": "最", "当": "當", "前": "前",
    "就": "就", "这": "這", "门": "門", "知": "知", "道": "道", "取": "取",
    "消": "消", "保": "保", "是": "是", "否": "否", "将": "將", "会": "會",
    "丢": "丟", "失": "失", "读": "讀", "写": "寫", "缓": "緩", "冲": "衝",
}


def to_tw(text):
    return "".join(S2T.get(c, c) for c in text)


def append_entries(fname, pairs):
    path = os.path.join(SRC, fname)
    src = io.open(path, encoding="utf-8", newline=None).read()
    tree = ast.parse(src)
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            target = node.value
            break
    if target is None:
        raise SystemExit("找不到 CATALOG: " + fname)

    lines = src.splitlines(keepends=True)
    insert_at = target.values[-1].end_lineno
    block = ["\n\n    # ---- 由 tools/fill_i18n_gaps.py 补齐（我改文案后新增的键）----\n"]
    for k, v in pairs:
        block.append("\n    %r:\n        %r,\n" % (k, v))
    lines.insert(insert_at, "".join(block))

    out = "".join(lines)
    ast.parse(out)          # 语法不对就抛，不写盘
    io.open(path, "w", encoding="utf-8", newline="\r\n").write(out)
    return len(pairs)


def main():
    miss_tw, _ = missing_keys("i18n_zh_tw.py")
    miss_en, _ = missing_keys("i18n_en.py")

    print("zh-TW 缺 %d 条" % len(miss_tw))
    for k in miss_tw:
        print("   %r" % (k[:80],))
    print("en 缺 %d 条" % len(miss_en))
    for k in miss_en:
        print("   %r" % (k[:80],))
    print()

    if "--write-tw" in sys.argv and miss_tw:
        n = append_entries("i18n_zh_tw.py", [(k, to_tw(k)) for k in miss_tw])
        print("已补 zh-TW %d 条（用简→繁字表兜底，建议之后人工复核）" % n)
    elif miss_tw:
        print("（加 --write-tw 可写出繁体兜底译文）")

    if miss_en:
        print("en 的缺口需要人工翻译，本工具不自动生成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
