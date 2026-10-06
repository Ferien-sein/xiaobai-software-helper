# -*- coding: utf-8 -*-
"""补上 github_lookup.py 离线指令那一整段的译文（约 10 条）。

这一段的键是**逐行**的（build_ai_instruction 里每行一个 _()），
所以不好跟前面那批放一个表里，单独写。
"""
import ast
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, HERE)

from check_i18n import catalog_of, module_keys  # noqa: E402

TR = {
    "（把你的需求填进上面几格，这里会自动生成查询词）": {
        "zh-TW": "（把你的需求填進上面幾格，這裡會自動產生查詢詞）",
        "en": "(fill in the boxes above and the search terms are generated here)",
    },
    "在动手做之前，请先帮我查一下 GitHub 上有没有现成的软件或插件。": {
        "zh-TW": "在動手做之前，請先幫我查一下 GitHub 上有沒有現成的軟體或外掛。",
        "en": "Before starting to build, please first check whether GitHub already has "
              "existing software or a plugin for this.",
    },
    "请搜索这些关键词（可以自己扩展同义词、英文词）：": {
        "zh-TW": "請搜尋這些關鍵詞（可以自己擴充同義詞、英文詞）：",
        "en": "Search for these keywords (feel free to add synonyms and English terms):",
    },
    "查完请按下面的格式回答，不要只丢链接：": {
        "zh-TW": "查完請照下面的格式回答，不要只丟連結：",
        "en": "After searching, answer in this format — do not just drop links:",
    },
    "1. 有没有现成的？如果有，列出最相关的 3~5 个，每个给出：": {
        "zh-TW": "1. 有沒有現成的？如果有，列出最相關的 3~5 個，每個給出：",
        "en": "1. Does anything exist already? If so, list the 3-5 most relevant, each with:",
    },
    "   项目名 / 链接 / 星数 / 最近更新时间 / 许可证 / 一句话说明它能不能满足我的需求": {
        "zh-TW": "   專案名稱 / 連結 / 星數 / 最近更新時間 / 授權條款 / 一句話說明它能不能滿足我的需求",
        "en": "   project name / link / stars / last updated / licence / one line on whether it "
              "actually meets my need",
    },
    "2. 这些项目**能不能直接满足我的需求**？缺哪些部分？": {
        "zh-TW": "2. 這些專案**能不能直接滿足我的需求**？缺哪些部分？",
        "en": "2. Can any of them **actually meet my need as-is**? What is missing?",
    },
    "3. 给我一个明确建议：直接用现成的、拿现成的改、还是自己做？并说明理由。": {
        "zh-TW": "3. 給我一個明確建議：直接用現成的、拿現成的改、還是自己做？並說明理由。",
        "en": "3. Give me a clear recommendation: use one as-is, adapt one, or build it myself — "
              "and explain why.",
    },
    "4. 如果用现成的，告诉我怎么装、怎么用（我不懂技术，请一步步说）。": {
        "zh-TW": "4. 如果用現成的，告訴我怎麼裝、怎麼用（我不懂技術，請一步步說）。",
        "en": "4. If I should use one, tell me how to install and use it "
              "(I am not technical — explain step by step).",
    },
    "如果确实没有合适的，再动手做；不要因为搜索麻烦就跳过这一步。": {
        "zh-TW": "如果確實沒有合適的，再動手做；不要因為搜尋麻煩就跳過這一步。",
        "en": "Only start building if nothing suitable exists — do not skip this step just "
              "because searching is a hassle.",
    },
}


def append(fname, keys, lang):
    path = os.path.join(SRC, fname)
    src = io.open(path, encoding="utf-8", newline=None).read()
    tree = ast.parse(src)
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            target = node.value
            break
    existing = {k.value for k in target.keys}
    todo = [(k, TR[k][lang]) for k in keys if k not in existing and k in TR]
    if not todo:
        print("  %s: 无需补充" % fname)
        return
    lines = src.splitlines(keepends=True)
    at = target.values[-1].end_lineno
    block = ["\n\n    # ---- 由 tools/fill_ai_instruction_i18n.py 补入：离线指令全文 ----\n"]
    for k, v in todo:
        block.append("    %s: %s,\n" % (json.dumps(k, ensure_ascii=False),
                                        json.dumps(v, ensure_ascii=False)))
    lines.insert(at, "".join(block))
    out = "".join(lines)
    ast.parse(out)
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    print("  %s: 补入 %d 条" % (fname, len(todo)))


def main():
    keys = module_keys("github_lookup.py", call_names=("_",))
    print("github_lookup.py 的 _() 文案：%d 条" % len(keys))
    unknown = [k for k in keys if k not in TR]
    # 只关心新增的这批：用「在动手做之前」等特征判断
    new_batch = [k for k in keys if k in TR]
    append("i18n_zh_tw.py", new_batch, "zh-TW")
    append("i18n_en.py", new_batch, "en")
    print()
    for fname in ("i18n_zh_tw.py", "i18n_en.py"):
        cat, err = catalog_of(os.path.join(SRC, fname))
        miss = [k for k in keys if k not in cat]
        print("  %s: %d 条，本模块缺失 %d" % (fname, len(cat), len(miss)))
        for k in miss:
            print("      %r" % (k[:80],))
    return 0


if __name__ == "__main__":
    sys.exit(main())
