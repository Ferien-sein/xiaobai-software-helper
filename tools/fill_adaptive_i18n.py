# -*- coding: utf-8 -*-
"""补上「问卷自适应」带来的新文案译文，并让 checker 覆盖自适应选项。

要补的：
  · 「· 已按你的平台调整」—— 界面上标出这一题按平台变过
  · 自适应在各平台族下产生的**所有选项**（安卓/iOS/鸿蒙/网页的专属选项、
    以及宽泛选项）—— 这些不在 QUESTIONS 的基础选项里，原来的 checker 看不到。

做法：直接用 questionnaire.adapt() 把每个问题在**每个平台族**下解析一遍，
把结果里的标题/说明/示例/帮助/选项全收进来当检查目标。
这样以后往规则表里加选项，checker 也会自动跟上。
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
sys.path.insert(0, SRC)

from check_i18n import catalog_of  # noqa: E402

# 新增文案的译文
TR = {
    "· 已按你的平台调整": {
        "zh-TW": "· 已依你的平台調整",
        "en": "· adjusted for your platform",
    },
    # ---- 存档位置（装到 Program Files 时数据会退到用户目录，必须让用户找得到）----
    "存档保存在哪": {"zh-TW": "存檔儲存在哪", "en": "Where is my data?"},
    "📁  存档保存在哪": {"zh-TW": "📁  存檔儲存在哪", "en": "📁  Where is my data?"},
    "存档和设置保存在程序旁边：": {"zh-TW": "存檔和設定儲存在程式旁邊：", "en": "Saved files and settings are stored next to the program: "},
    "存档和设置保存在：": {"zh-TW": "存檔和設定儲存在：", "en": "Saved files and settings are stored in: "},
    "（程序装在只读位置，所以放到你的用户目录）": {"zh-TW": "（程式裝在唯讀位置，所以放到你的使用者目錄）", "en": " (the program folder is read-only, so they go to your user folder)"},
    "打开这个文件夹": {"zh-TW": "開啟這個資料夾", "en": "Open this folder"},
}

# 自适应选项的译文：{原文: {语言: 译文}}
# 只列平台专属的（宽泛选项通常已在基础表里）
OPT_TR = {
    # ---- where ----
    "装成 App，点桌面图标打开": {"zh-TW": "裝成 App，點桌面圖示開啟", "en": "Install it as an app and tap the icon on the home screen"},
    "在手机浏览器里打开网址就行": {"zh-TW": "用手機瀏覽器開啟網址就行", "en": "Just open a URL in the phone browser"},
    "微信里能打开/分享（小程序或链接）": {"zh-TW": "微信裡能開啟／分享（小程式或連結）", "en": "Openable/shareable inside WeChat (mini program or link)"},
    "要给不特定的人下载用": {"zh-TW": "要給不特定的人下載用", "en": "Should be downloadable by anyone"},
    "电脑和手机都要能打开": {"zh-TW": "電腦和手機都要能開啟", "en": "Must open on both computers and phones"},
    "只给内部的人用，不想放到公网": {"zh-TW": "只給內部的人用，不想放到公網", "en": "Internal use only, not on the public internet"},
    "要放到网上，别人能直接访问": {"zh-TW": "要放到網路上，別人能直接存取", "en": "Host it online so others can access it directly"},
    "只要能在我自己电脑上跑就行": {"zh-TW": "只要能在我自己電腦上跑就行", "en": "Running on my own computer is enough"},
    # ---- install ----
    "一个 apk 安装包，我传到手机点一下装": {"zh-TW": "一個 apk 安裝檔，我傳到手機點一下裝", "en": "An .apk I copy to the phone and tap to install"},
    "要能上架应用商店（安卓）": {"zh-TW": "要能上架應用程式商店（安卓）", "en": "Should be publishable to an app store (Android)"},
    "我自己装就行，不用上架": {"zh-TW": "我自己裝就行，不用上架", "en": "I will install it myself, no store needed"},
    "先做出来能在我自己手机上试（需要有苹果开发者账号）": {"zh-TW": "先做出來能在我自己手機上試（需要有蘋果開發者帳號）", "en": "First make it runnable on my own phone (needs an Apple Developer account)"},
    "要上架 App Store 给别人下载": {"zh-TW": "要上架 App Store 給別人下載", "en": "Publish to the App Store for others to download"},
    "其实用网页版也行（不用苹果账号）": {"zh-TW": "其實用網頁版也行（不用蘋果帳號）", "en": "Actually a web version is fine too (no Apple account needed)"},
    "一个 hap 安装包，我传到手机装": {"zh-TW": "一個 hap 安裝檔，我傳到手機裝", "en": "A .hap package I copy to the phone"},
    "需要开开发者模式才能装，我可以接受": {"zh-TW": "需要開開發者模式才能裝，我可以接受", "en": "Needs developer mode enabled to install — that is fine"},
    "给我一个网址，我用浏览器打开": {"zh-TW": "給我一個網址，我用瀏覽器開啟", "en": "Give me a URL and I will open it in a browser"},
    "放到我自己电脑上，只有我能访问": {"zh-TW": "放到我自己電腦上，只有我能存取", "en": "Host it on my own computer, only I can access it"},
    "要放到服务器上给别人访问": {"zh-TW": "要放到伺服器上給別人存取", "en": "Host it on a server for others to access"},
    "先做一个最简单的版本给我看看": {"zh-TW": "先做一個最簡單的版本給我看看", "en": "Build the simplest possible version first so I can look at it"},
    # ---- done ----
    "在我自己的手机上能装能开": {"zh-TW": "在我自己的手機上能裝能開", "en": "Installs and opens on my own phone"},
    "主要功能点一遍都正常，不闪退": {"zh-TW": "主要功能點一遍都正常，不會閃退", "en": "Every main feature works once through, with no crashes"},
    "发给别人也能装能开": {"zh-TW": "發給別人也能裝能開", "en": "Sending it to someone else also installs and opens"},
    "手机和电脑打开都正常": {"zh-TW": "手機和電腦開啟都正常", "en": "Opens correctly on both phone and computer"},
    "换台设备/换个时间打开，数据还在": {"zh-TW": "換台裝置／換個時間開啟，資料還在", "en": "Open it on another device or later, and the data is still there"},
    "别人打开也能用": {"zh-TW": "別人開啟也能用", "en": "Others can open it and use it"},
    # ---- limit ----
    "不要偷偷上传我的通讯录/相册/位置": {"zh-TW": "不要偷偷上傳我的通訊錄／相簿／位置", "en": "Do not secretly upload my contacts, photos, or location"},
    "不要要求一堆用不上的权限": {"zh-TW": "不要要求一堆用不上的權限", "en": "Do not ask for a pile of permissions it does not need"},
    "不要有广告和推送": {"zh-TW": "不要有廣告和推送", "en": "No ads and no push notifications"},
    "不要公开我的数据，只能我自己看到": {"zh-TW": "不要公開我的資料，只能我自己看到", "en": "Do not expose my data — only I should see it"},
    "不要收集访问者的个人信息": {"zh-TW": "不要收集訪問者的個人資訊", "en": "Do not collect visitors' personal information"},
    # ---- 第 3 题自己的自适应（选了手机还问「32 位还是 64 位」是误导）----
    "3. 手机 App 做给哪种手机用？": {"zh-TW": "3. 手機 App 做給哪種手機用？", "en": "3. Which kind of phone is the app for?"},
    "3. 这个网页给谁用、在什么设备上打开？": {"zh-TW": "3. 這個網頁給誰用、在什麼裝置上開啟？", "en": "3. Who is the web page for, and on what devices?"},
    "选错手机类型会导致装不上。安卓、苹果、鸿蒙是完全不同的做法。": {"zh-TW": "選錯手機類型會導致裝不上。安卓、蘋果、鴻蒙是完全不同的做法。", "en": "Picking the wrong phone type means it will not install. Android, iPhone, and HarmonyOS are built in completely different ways."},
    "网页本身什么设备都能开，主要看给谁用、要不要放到网上。": {"zh-TW": "網頁本身什麼裝置都能開，主要看給誰用、要不要放到網路上。", "en": "A web page opens on any device; what matters is who it is for and whether it goes online."},
    "例如：安卓手机 App（现在的手机基本都是安卓）": {"zh-TW": "例如：安卓手機 App（現在的手機幾乎都是安卓）", "en": "e.g. an Android app (almost every current phone is Android)"},
    "例如：网页，电脑和手机都能打开": {"zh-TW": "例如：網頁，電腦和手機都能開啟", "en": "e.g. a web page that opens on both a computer and a phone"},
    # ---- 自适应标题 / 说明 / 示例 ----
    "4. 手机上打算怎么用它？要不要联网？": {"zh-TW": "4. 手機上打算怎麼用它？要不要連網？", "en": "4. How will it be used on the phone? Does it need the internet?"},
    "4. 这个网页怎么用？要不要联网？": {"zh-TW": "4. 這個網頁怎麼用？要不要連網？", "en": "4. How will the web page be used? Does it need the internet?"},
    "12. 希望怎么装到手机上、怎么再打开？（怎么交付）": {"zh-TW": "12. 希望怎麼裝到手機上、怎麼再開啟？（怎麼交付）", "en": "12. How should it be installed on the phone and reopened? (delivery)"},
    "12. 这个网页放在哪、怎么再打开？（怎么交付）": {"zh-TW": "12. 這個網頁放在哪、怎麼再開啟？（怎麼交付）", "en": "12. Where should the web page live and how is it reopened? (delivery)"},
    "手机上装 App 和用浏览器打开，做法和门槛差别很大。": {"zh-TW": "手機上裝 App 和用瀏覽器開啟，做法和門檻差別很大。", "en": "Installing an app and opening a web page on a phone are very different."},
    "例如：在我自己的手机上装好，打开后能完成主要操作，不闪退": {"zh-TW": "例如：在我自己的手機上裝好，開啟後能完成主要操作，不會閃退", "en": "e.g. installed on my own phone, opens and completes the main task without crashing"},
    "例如：用手机和电脑各打开一次，主要功能都能用，刷新不丢数据": {"zh-TW": "例如：用手機和電腦各開啟一次，主要功能都能用，重新整理不丟資料", "en": "e.g. opened once on a phone and once on a desktop, all main features work, a refresh does not lose data"},
}


def adaptive_keys():
    """把每题在每个平台族下解析一遍，收集所有会显示出来的文案与选项。"""
    import app as A
    import questionnaire as Q

    out = set()
    for q in A.QUESTIONS:
        for fam in (Q.FAM_DESKTOP, Q.FAM_ANDROID, Q.FAM_IOS, Q.FAM_HARMONY,
                    Q.FAM_WEB, Q.FAM_UNKNOWN):
            r = Q.adapt(q["key"], fam, "zh-CN", q)
            for field in ("title", "hint", "example", "help"):
                v = r.get(field)
                if isinstance(v, str) and v.strip():
                    out.add(v)
            for o in r.get("options") or []:
                if isinstance(o, str) and o.strip():
                    out.add(o)
    # BROAD 里的宽泛选项
    for seq in Q.BROAD.values():
        for o in seq:
            out.add(o)
    return sorted(out)


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

    # 1) 单个新文案
    todo = [(k, v[lang]) for k, v in TR.items() if k not in existing]
    # 2) 自适应选项
    for k in adaptive_keys():
        if k in existing:
            continue
        tr = (OPT_TR.get(k) or {}).get(lang)
        if tr:
            todo.append((k, tr))

    if not todo:
        print("  %s: 无需补充" % fname)
        return
    lines = src.splitlines(keepends=True)
    at = target.values[-1].end_lineno
    block = ["\n\n    # ---- 由 tools/fill_adaptive_i18n.py 补入：问卷自适应相关文案 ----\n"]
    for k, v in todo:
        block.append("    %s: %s,\n" % (json.dumps(k, ensure_ascii=False),
                                        json.dumps(v, ensure_ascii=False)))
    lines.insert(at, "".join(block))
    out = "".join(lines)
    t2 = ast.parse(out)
    n2 = 0
    for node in ast.walk(t2):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            n2 = len(node.value.keys)
    assert n2 == len(existing) + len(todo), "%d != %d" % (n2, len(existing) + len(todo))
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    print("  %s: 补入 %d 条（%d → %d）" % (fname, len(todo), len(existing), n2))


def main():
    keys = adaptive_keys()
    print("自适应会显示出来的文案共 %d 条" % len(keys))
    missing_tr = [k for k in keys if k not in OPT_TR and k not in TR]
    print("其中没有译文可补的：%d 条（多半已存在于基础表）" % len(missing_tr))
    append("i18n_zh_tw.py", "zh-TW")
    append("i18n_en.py", "en")
    print()
    for fname in ("i18n_zh_tw.py", "i18n_en.py"):
        cat, err = catalog_of(os.path.join(SRC, fname))
        miss = [k for k in keys if k not in cat]
        print("  %s: %d 条，自适应文案缺失 %d" % (fname, len(cat), len(miss)))
        for k in miss[:12]:
            print("      %r" % (k[:78],))
    return 0


if __name__ == "__main__":
    sys.exit(main())
