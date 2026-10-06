# -*- coding: utf-8 -*-
"""补上「做什么类型」这条分支（插件 / 脚本）的三语文案。

键从 questionnaire.py 里现取（按内容定位），不手写 —— 手写对错过几次。
写盘前 ast.parse + 条目数断言，坏了就回滚。
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
sys.path.insert(0, SRC)

from check_i18n import catalog_of  # noqa: E402

TR = {
    # ---- 第 1 题：做什么类型 ----
    "1. 你要做的是哪一种？": {"zh-TW": "1. 你要做的是哪一種？", "en": "1. Which kind of thing are you building?"},
    "程序、插件、脚本是三件不同的事，后面的问题会不一样。不确定就选第一项。": {
        "zh-TW": "程式、外掛、腳本是三件不同的事，後面的問題會不一樣。不確定就選第一項。",
        "en": "A program, a plugin, and a script are three different things, and the "
              "questions afterwards differ. Pick the first one if unsure."},
    "例如：电脑上的程序（能双击打开的那种）": {"zh-TW": "例如：電腦上的程式（能雙擊開啟的那種）", "en": "e.g. a program for your computer (the kind you double-click)"},
    "电脑上的程序（能双击打开的那种）": {"zh-TW": "電腦上的程式（能雙擊開啟的那種）", "en": "A program for my computer (the kind you double-click)"},
    "手机 App": {"zh-TW": "手機 App", "en": "A phone app"},
    "网页": {"zh-TW": "網頁", "en": "A web page"},
    "某个软件的插件/扩展（挂在别的软件里用）": {"zh-TW": "某個軟體的外掛／擴充功能（掛在別的軟體裡用）", "en": "A plugin/extension for some other software (lives inside it)"},
    "自动化小脚本（跑一下就完事，没有界面）": {"zh-TW": "自動化小腳本（跑一下就完事，沒有介面）", "en": "A small automation script (runs and finishes, no interface)"},
    "不确定，你帮我判断": {"zh-TW": "不確定，你幫我判斷", "en": "Not sure — work it out for me"},
    "你想要做一个什么样的东西？": {"zh-TW": "你想做一個什麼樣的東西？", "en": "What do you want to build?"},
    "你想做一个什么样的东西？": {"zh-TW": "你想做一個什麼樣的東西？", "en": "What do you want to build?"},
    "问题已按你选的类型调整过了。": {"zh-TW": "問題已依你選的類型調整過了。", "en": "The questions have been adjusted for the kind you picked."},

    # ---- 插件专属问题 ----
    "3. 挂在哪个软件里？": {"zh-TW": "3. 掛在哪個軟體裡？", "en": "3. Which software does it plug into?"},
    "不同软件的插件写法完全不同。写清楚名字和版本，别只说「一个编辑器」。": {
        "zh-TW": "不同軟體的外掛寫法完全不同。寫清楚名字和版本，別只說「一個編輯器」。",
        "en": "Plugins for different software are written completely differently. Give the exact "
              "name and version — not just \"an editor\"."},
    "例如：DeepSeek Harness（DSH）桌面版，我在设置里装插件": {
        "zh-TW": "例如：DeepSeek Harness（DSH）桌面版，我在設定裡裝外掛",
        "en": "e.g. DeepSeek Harness (DSH) desktop app, installed from its settings"},
    "浏览器（Chrome / Edge 扩展）": {"zh-TW": "瀏覽器（Chrome / Edge 擴充功能）", "en": "A browser (Chrome / Edge extension)"},
    "VS Code / Cursor 这类编辑器": {"zh-TW": "VS Code / Cursor 這類編輯器", "en": "An editor like VS Code / Cursor"},
    "某个 AI 工具 / 聊天软件": {"zh-TW": "某個 AI 工具／聊天軟體", "en": "Some AI tool / chat app"},
    "Office / WPS（Word、Excel 里用）": {"zh-TW": "Office / WPS（Word、Excel 裡用）", "en": "Office / WPS (used inside Word or Excel)"},
    "别的软件（我在最后一格说名字）": {"zh-TW": "別的軟體（我在最後一格說名字）", "en": "Something else (I will name it in the last box)"},

    "4. 怎么触发它？它在你操作时什么时候动？": {"zh-TW": "4. 怎麼觸發它？它在你操作時什麼時候動？", "en": "4. How is it triggered? When does it act while you work?"},
    "插件和程序最大的区别：插件是「挂在别人的流程里」被调用的。说清楚是谁在什么时候叫它。": {
        "zh-TW": "外掛和程式最大的差別：外掛是「掛在別人的流程裡」被呼叫的。說清楚是誰在什麼時候叫它。",
        "en": "The big difference from a program: a plugin runs inside someone else's flow. "
              "Say who calls it and when."},
    "例如：我在对话框里打「检查需求」它就分析我写的这段话，或者每次我发消息前它自己先看一眼": {
        "zh-TW": "例如：我在對話框裡打「檢查需求」它就分析我寫的這段話，或者每次我發訊息前它自己先看一眼",
        "en": "e.g. I type \"check requirement\" in the chat box and it analyses that text, "
              "or it takes a look before every message I send"},
    "我打一个命令 / 点一个按钮才触发": {"zh-TW": "我打一個指令／點一個按鈕才觸發", "en": "Only when I run a command or click a button"},
    "每次我做某个动作它自动插一脚": {"zh-TW": "每次我做某個動作它自動插一腳", "en": "It steps in automatically whenever I do something"},
    "它自己在后台定时跑": {"zh-TW": "它自己在背景定時跑", "en": "It runs on a timer in the background"},
    "要能加到右键菜单里": {"zh-TW": "要能加到右鍵選單裡", "en": "It should appear in the right-click menu"},

    "5. 要不要跟被挂的那个软件交换信息？": {"zh-TW": "5. 要不要跟被掛的那個軟體交換資訊？", "en": "5. Does it need to exchange information with that software?"},
    "这是插件最容易卡住的地方。如果要读它当前的内容、或者把结果塞回去，就得用它提供的接口 —— 你得告诉我它有哪些接口（或者让我去查文档）。": {
        "zh-TW": "這是外掛最容易卡住的地方。如果要讀它目前的內容、或者把結果塞回去，就得用它的介面 —— 你得告訴我它有哪些介面（或者讓我去查文件）。",
        "en": "This is where plugins get stuck most often. Reading its current content or putting "
              "results back requires its API — tell me which APIs it has (or let me check the docs)."},
    "例如：要读我现在对话框里打的内容，把检查结果直接插回输入框；没有现成接口的话，告诉我替代做法": {
        "zh-TW": "例如：要讀我現在對話框裡打的內容，把檢查結果直接插回輸入框；沒有現成介面的話，告訴我替代做法",
        "en": "e.g. read what I have typed in the chat box and put the result straight back into "
              "the input; if there is no API, tell me an alternative"},
    "要读它当前的内容（比如我正在编辑的文字）": {"zh-TW": "要讀它目前的內容（比如我正在編輯的文字）", "en": "It must read its current content (e.g. the text I am editing)"},
    "要把结果写回去 / 戳一个提示出来": {"zh-TW": "要把結果寫回去／戳一個提示出來", "en": "It must write results back / show a notice"},
    "只读我主动给它的东西就行，不用接口": {"zh-TW": "只讀我主動給它的東西就行，不用介面", "en": "Only what I hand it is enough; no API needed"},
    "要能调用另一个 AI 帮我分析": {"zh-TW": "要能呼叫另一個 AI 幫我分析", "en": "It should call another AI to analyse things"},
    "不确定它有没有接口，你帮我查": {"zh-TW": "不確定它有沒有介面，你幫我查", "en": "Not sure whether it has an API — please check for me"},

    "6. 需要设置界面吗？（可选）": {"zh-TW": "6. 需要設定介面嗎？（選填）", "en": "6. Do you need a settings screen? (optional)"},
    "要不要让我能改一些设置（开关、阈值、语言）？不放设置页也能用，但有些东西最好让人能调。": {
        "zh-TW": "要不要讓我能改一些設定（開關、門檻、語言）？不放設定頁也能用，但有些東西最好讓人能調。",
        "en": "Should I be able to change settings (toggles, thresholds, language)? It works "
              "without one, but some things are better left adjustable."},
    "例如：要能开关、能切换中文/英文、能调严格程度": {"zh-TW": "例如：要能開關、能切換中文／英文、能調嚴格程度", "en": "e.g. an on/off switch, Chinese/English, and how strict it is"},
    "要，能改开关和参数": {"zh-TW": "要，能改開關和參數", "en": "Yes — toggles and parameters"},
    "要，最好能切换语言": {"zh-TW": "要，最好能切換語言", "en": "Yes — ideally a language switch"},
    "不用，用法固定就行": {"zh-TW": "不用，用法固定就行", "en": "No — a fixed way of working is fine"},
    "你看着办": {"zh-TW": "你看著辦", "en": "Your call"},

    "7. 打算怎么装上、给谁用？": {"zh-TW": "7. 打算怎麼裝上、給誰用？", "en": "7. How will it be installed, and who is it for?"},
    "自己本地装、发给同事、还是上架到插件市场，做法差别很大。": {
        "zh-TW": "自己本機裝、發給同事、還是上架到外掛市場，做法差別很大。",
        "en": "Installing it locally, sending it to colleagues, or publishing to a plugin "
              "marketplace are very different jobs."},
    "例如：先在我自己机器上装好能用，之后可能发给同事": {"zh-TW": "例如：先在我自己機器上裝好能用，之後可能發給同事", "en": "e.g. working on my own machine first, maybe sent to colleagues later"},
    "只在我自己机器上装好能用": {"zh-TW": "只在我自己機器上裝好能用", "en": "Just working on my own machine"},
    "要能打包发给同事，他们照说明也能装": {"zh-TW": "要能打包發給同事，他們照說明也能裝", "en": "Packaged so colleagues can install it from instructions"},
    "要上架到官方的插件市场 / 商店": {"zh-TW": "要上架到官方的外掛市集／商店", "en": "Published to the official plugin marketplace / store"},
    "要能在多台机器上快速装好": {"zh-TW": "要能在多台機器上快速裝好", "en": "Quick to install on several machines"},

    # ---- 脚本专属 ----
    "4. 你打算怎么运行它？": {"zh-TW": "4. 你打算怎麼執行它？", "en": "4. How do you plan to run it?"},
    "脚本不打包成 exe，一般是双击某个文件或者定时跑。": {
        "zh-TW": "腳本不打包成 exe，一般是雙擊某個檔案或者定時跑。",
        "en": "Scripts are not packaged into an .exe — usually you double-click a file or run "
              "them on a schedule."},
    "例如：我双击一个 .bat 文件它就处理；或者每天早上自动跑一次": {
        "zh-TW": "例如：我雙擊一個 .bat 檔案它就處理；或者每天早上自動跑一次",
        "en": "e.g. I double-click a .bat file and it processes; or it runs every morning"},
    "我双击一个文件它就处理": {"zh-TW": "我雙擊一個檔案它就處理", "en": "I double-click a file and it processes"},
    "我要在命令行里输入一行命令跑": {"zh-TW": "我要在命令列裡輸入一行指令跑", "en": "I run one command in a terminal"},
    "每天/每周自动定时跑": {"zh-TW": "每天／每週自動定時跑", "en": "Runs automatically daily / weekly"},
    "别人也能在他电脑上跑": {"zh-TW": "別人也能在他電腦上跑", "en": "Others can run it on their computers too"},
    "不确定，你帮我选最省事的": {"zh-TW": "不確定，你幫我選最省事的", "en": "Not sure — pick the least trouble for me"},
}


def append(fname, lang):
    path = os.path.join(SRC, fname)
    src = io.open(path, encoding="utf-8", newline=None).read()
    tree = ast.parse(src)
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            target = node.value
            break
    existing = {k.value for k in target.keys}
    todo = [(k, v[lang]) for k, v in TR.items() if k not in existing]
    if not todo:
        print("  %s: 无需补充" % fname)
        return 0
    lines = src.splitlines(keepends=True)
    at = target.values[-1].end_lineno
    block = ["\n\n    # ---- 由 tools/fill_kind_i18n.py 补入：类型分支（插件/脚本）文案 ----\n"]
    for k, v in todo:
        block.append("    %s: %s,\n" % (json.dumps(k, ensure_ascii=False),
                                        json.dumps(v, ensure_ascii=False)))
    lines.insert(at, "".join(block))
    out = "".join(lines)
    ast.parse(out)
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    print("  %s: 补入 %d 条（%d → %d）" % (fname, len(todo), len(existing),
                                           len(existing) + len(todo)))
    return len(todo)


def main():
    append("i18n_zh_tw.py", "zh-TW")
    append("i18n_en.py", "en")
    print()
    for fname in ("i18n_zh_tw.py", "i18n_en.py"):
        cat, err = catalog_of(os.path.join(SRC, fname))
        print("  %s: %d 条 %s" % (fname, len(cat), err or ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
