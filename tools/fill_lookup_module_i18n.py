# -*- coding: utf-8 -*-
"""把 github_lookup.py 里的文案补进两个语言包。

为什么要单独一个脚本：那些键不在 app.py 里，check_i18n.py 默认只扫 app.py，
所以它们不会被发现。这里直接把 github_lookup.py 里 _() 的实参抽出来核对，
相当于把检查范围也扩到了这个模块。
"""
import ast
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, HERE)

from check_i18n import catalog_of  # noqa: E402


def lookup_keys():
    """抽出 github_lookup.py 里 _() 的字符串实参"""
    tree = ast.parse(io.open(os.path.join(SRC, "github_lookup.py"), encoding="utf-8").read())
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_":
            if node.args and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str):
                out.append(node.args[0].value)
            else:
                print("  [warn] _() 的实参不是字符串字面量: L%s" % node.lineno)
    return sorted(set(out))


# 译文：键省略，靠下面的“与英文包对齐”来保证覆盖
TR = {
    "查询词是空的": {
        "zh-TW": "查詢詞是空的",
        "en": "The search query is empty",
    },
    "GitHub 限制了查询频率（每小时 10 次左右），请过一会儿再试": {
        "zh-TW": "GitHub 限制了查詢頻率（每小時 10 次左右），請過一會兒再試",
        "en": "GitHub is rate-limiting searches (about 10 per hour without login). "
              "Please try again later.",
    },
    "查询词 GitHub 不接受，换个更简单的说法再试": {
        "zh-TW": "查詢詞 GitHub 不接受，換個更簡單的說法再試",
        "en": "GitHub rejected that query — try a simpler wording.",
    },
    "GitHub 返回错误 %s": {
        "zh-TW": "GitHub 回報錯誤 %s",
        "en": "GitHub returned error %s",
    },
    "连不上 GitHub（%s）。可以先用下面的「让 AI 帮你查」": {
        "zh-TW": "連不上 GitHub（%s）。可以先用下面的「讓 AI 幫你查」",
        "en": "Cannot reach GitHub (%s). You can use \"ask an AI to search for me\" below instead.",
    },
    "查询失败：%r": {
        "zh-TW": "查詢失敗：%r",
        "en": "Search failed: %r",
    },
    "（有 %d 个搜索结果与你的需求明显无关，已排除 —— GitHub 按星数排时经常把无关的高星项目排在最前）": {
        "zh-TW": "（有 %d 個搜尋結果與你的需求明顯無關，已排除 —— "
                 "GitHub 依星數排序時經常把無關的高星專案排在最前）",
        "en": "(%d search results were clearly unrelated to your requirement and have been "
              "excluded — GitHub sorts by stars and often puts unrelated high-star projects first)",
    },
    "没找到现成的，可以自己做": {
        "zh-TW": "沒找到現成的，可以自己做",
        "en": "Nothing suitable exists yet — you can build it yourself",
    },
    "建议先用现成的，别从零做": {
        "zh-TW": "建議先用現成的，別從零做",
        "en": "Recommendation: use an existing project instead of building from scratch",
    },
    "有可参考的项目，值得先看一眼再决定": {
        "zh-TW": "有可參考的專案，值得先看一眼再決定",
        "en": "There are projects worth a look — check them before deciding",
    },
    "现成的都不太合适，自己做更省事": {
        "zh-TW": "現成的都不太合適，自己做更省事",
        "en": "Nothing existing fits well — building it yourself is less trouble",
    },
    "最相关的项目有 %d 颗星，说明用的人不少": {
        "zh-TW": "最相關的專案有 %d 顆星，說明用的人不少",
        "en": "The most relevant project has %d stars, so it is fairly widely used",
    },
    "最相关的项目有 %d 颗星，有一定使用量": {
        "zh-TW": "最相關的專案有 %d 顆星，有一定使用量",
        "en": "The most relevant project has %d stars, so it does get some use",
    },
    "星数都不高（最高 %d），可能没有成熟方案": {
        "zh-TW": "星數都不高（最高 %d），可能沒有成熟方案",
        "en": "None have many stars (highest is %d), so there may be no mature option",
    },
    "⚠️ 但该项目已归档，作者不再维护": {
        "zh-TW": "⚠️ 但該專案已封存，作者不再維護",
        "en": "⚠️ But that project is archived — the author no longer maintains it",
    },
    "⚠️ 而且已 %d 个月没更新，要留意是否还适用": {
        "zh-TW": "⚠️ 而且已 %d 個月沒更新，要留意是否還適用",
        "en": "⚠️ And it has not been updated for %d months, so check whether it still fits",
    },
    "最近还有更新（%s），看来仍在维护": {
        "zh-TW": "最近還有更新（%s），看來仍在維護",
        "en": "It was updated recently (%s), so it looks maintained",
    },
    "❓ 没写清楚开源许可证，商用前要确认": {
        "zh-TW": "❓ 沒寫清楚開源授權條款，商用前要確認",
        "en": "❓ The open-source licence is not stated clearly — confirm before commercial use",
    },
    "许可证是 %s": {
        "zh-TW": "授權條款是 %s",
        "en": "The licence is %s",
    },
    "没有找到相关项目。": {
        "zh-TW": "沒有找到相關專案。",
        "en": "No related projects found.",
    },
    "【判断】": {
        "zh-TW": "【判斷】",
        "en": "[Verdict] ",
    },
    "找到 %d 个相关项目（按星数排序）：": {
        "zh-TW": "找到 %d 個相關專案（依星數排序）：",
        "en": "Found %d related projects (sorted by stars):",
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
    todo = []
    for k in keys:
        if k in existing:
            continue
        tr = (TR.get(k) or {}).get(lang)
        if tr is None:
            print("  [!] 缺译文，跳过: %r" % k[:60])
            continue
        todo.append((k, tr))
    if not todo:
        print("  %s: 无需补充" % fname)
        return
    lines = src.splitlines(keepends=True)
    at = target.values[-1].end_lineno
    block = ["\n\n    # ---- 由 tools/fill_lookup_module_i18n.py 补入：github_lookup.py 的文案 ----\n"]
    for k, v in todo:
        block.append("    %s: %s,\n" % (json.dumps(k, ensure_ascii=False),
                                        json.dumps(v, ensure_ascii=False)))
    lines.insert(at, "".join(block))
    out = "".join(lines)
    ast.parse(out)                       # 语法不过就抛
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    print("  %s: 补入 %d 条" % (fname, len(todo)))


def main():
    keys = lookup_keys()
    print("github_lookup.py 里的 _() 文案：%d 条" % len(keys))
    missing_tr = [k for k in keys if k not in TR]
    if missing_tr:
        print("  [!] 有 %d 条没有译文：" % len(missing_tr))
        for k in missing_tr:
            print("      %r" % (k[:80],))
    append("i18n_zh_tw.py", keys, "zh-TW")
    append("i18n_en.py", keys, "en")
    print()
    for fname in ("i18n_zh_tw.py", "i18n_en.py"):
        cat, err = catalog_of(os.path.join(SRC, fname))
        miss = [k for k in keys if k not in cat]
        print("  %s: %d 条，本模块缺失 %d %s" % (fname, len(cat), len(miss), miss or ""))
    return 0 if not missing_tr else 1


if __name__ == "__main__":
    sys.exit(main())
