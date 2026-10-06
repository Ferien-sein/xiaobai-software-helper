# -*- coding: utf-8 -*-
"""把「先查查」页的界面文案按三种语言渲染出来，方便肉眼校对。

顺带把 github_lookup.py 里**没走 t()** 的可见文本也打出来 ——
那些不在语言包里，check_i18n.py 也管不到，属于已知的残留缺口。

用法: python tools/_xbsh_show_lookup_strings.py
只读，不修改任何文件。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import github_lookup  # noqa: E402
import i18n  # noqa: E402

SAMPLES = [
    "先查查",
    "动手做之前，先看看 GitHub 上有没有现成的",
    "很多需求已经有成熟方案了。先查一眼，能省掉大量重复劳动；如果有能用的，拿现成的改通常比从零做更可靠。",
    "查什么（可以自己改）：",
    "🔄 从我的答案生成",
    "点下面按钮才会联网（只把上面这行字发给 GitHub，你填的需求正文不会发出去）；不点就一直离线。",
    "🔍 查一下 GitHub（会联网）",
    "📋 复制「让 AI 帮我查」的指令（不联网）",
    "还没有查询词",
    "先点「从我的答案生成」，或者自己写几个关键词。",
    "要联网了",
    "接下来会把这一行字发给 GitHub 搜索：\n\n%s\n\n• 你填的需求正文**不会**发出去\n"
    "• 只搜公开项目，不登录、不提交任何东西\n\n要继续吗？",
    "正在查 GitHub…",
    "没查成",
    "可以用下面的办法：点「复制让 AI 帮我查的指令」，粘给 AI 让它帮你搜。",
    "（搜到 %d 个，其中 %d 个与你的需求明显无关，已排除 —— GitHub 按星数排时经常把无关的高星项目排在最前）",
    "——————",
    "这个结论只看客观信号（相关性、星数、是否还在更新、许可证），不替你做判断。"
    "拿不准就把上面的链接发给 AI 让它帮你评估。",
    "查完了：%s",
    "点「从我的答案生成」得到查询词，再点「查一下 GitHub」。\n\n连不上网也没关系："
    "用「复制让 AI 帮我查的指令」，把那段话粘给 AI，它会帮你搜并评估能不能用。",
    "查询词已填好：%s\n\n点「查一下 GitHub」开始搜。\n搜之前可以自己改这行字。",
    "还没填「你想做什么」那一格，所以生成不出查询词。\n\n回到「填写需求」页填一两格再回来。",
    "（先回到「填写需求」页填一两格，再回来生成关键词）",
    "指令已复制。切到 AI 对话框，按 Ctrl+V 粘贴发送就行。",
    "复制失败，可以直接从下面框里选中复制。",
]

ARGS = {"%s": "excel merge", "%d": 8}


def render(text):
    for k, v in ARGS.items():
        text = text.replace(k, str(v))
    return text


def main():
    for lang in ("zh-CN", "zh-TW", "en"):
        i18n.reload_packs()
        i18n.set_lang(lang)
        print("=" * 70)
        print(lang)
        print("=" * 70)
        for s in SAMPLES:
            print("  %s" % render(i18n.t(s)).replace("\n", "\n  | "))
        print()

    print("=" * 70)
    print("github_lookup.py 里没走 t() 的可见文本（语言包管不到，已知缺口）")
    print("=" * 70)
    repos = [{"full_name": "foo/bar", "url": "https://github.com/foo/bar", "description": "d",
              "stars": 500, "language": "Python", "license": "MIT", "updated": "2026-01-02",
              "archived": False, "issues": 1}]
    verdict = github_lookup.judge(repos, terms=["excel", "merge"])
    print("  judge() headline         = %s" % verdict["headline"])
    print("  judge() reasons[0]       = %s" % verdict["reasons"][0])
    print("  format_report 首行        = %s" % github_lookup.format_report(repos, verdict).splitlines()[0])
    print("  search_repos('') 的 err   = %s" % github_lookup.search_repos("")[1])
    print("  build_ai_instruction 首行 = %s" % github_lookup.build_ai_instruction(["a b"]).splitlines()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
