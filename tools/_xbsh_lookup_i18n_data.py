# -*- coding: utf-8 -*-
"""「先查查」页新增条目的译文数据源（辅助文件，不参与程序运行）。

键 = app.py 里的简体原文（逐字一致）；值 = 译文。
由 tools/_xbsh_add_lookup_i18n.py --emit-data-py 从 .json 机械生成，
转义由 json.dumps 保证，不要手写。
"""

TR = {
    "_note": "先查查（GitHub 查重页）新增条目的译文数据源。键 = app.py 里的简体原文（逐字一致）。本文件由 tools/_xbsh_add_lookup_i18n.py 读取，不直接进程序。",
    "zh-TW": {
        "先查查": "先查查",
        "动手做之前，先看看 GitHub 上有没有现成的": "動手做之前，先看看 GitHub 上有沒有現成的",
        "很多需求已经有成熟方案了。先查一眼，能省掉大量重复劳动；如果有能用的，拿现成的改通常比从零做更可靠。": "很多需求已經有成熟方案了。先查一眼，能省掉大量重複勞動；如果有能用的，拿現成的改通常比從零做更可靠。",
        "查什么（可以自己改）：": "查什麼（可以自己改）：",
        "🔄 从我的答案生成": "🔄 從我的答案產生",
        "点下面按钮才会联网（只把上面这行字发给 GitHub，你填的需求正文不会发出去）；不点就一直离线。": "點下面按鈕才會連網（只把上面這行字發給 GitHub，你填的需求正文不會發出去）；不點就一直離線。",
        "🔍 查一下 GitHub（会联网）": "🔍 查一下 GitHub（會連網）",
        "📋 复制「让 AI 帮我查」的指令（不联网）": "📋 複製「讓 AI 幫我查」的指令（不連網）",
        "还没有查询词": "還沒有查詢詞",
        "先点「从我的答案生成」，或者自己写几个关键词。": "先點「從我的答案產生」，或者自己寫幾個關鍵詞。",
        "要联网了": "要連網了",
        "接下来会把这一行字发给 GitHub 搜索：\n\n%s\n\n• 你填的需求正文**不会**发出去\n• 只搜公开项目，不登录、不提交任何东西\n\n要继续吗？": "接下來會把這一行字發給 GitHub 搜尋：\n\n%s\n\n• 你填的需求正文**不會**發出去\n• 只搜公開專案，不登入、不提交任何東西\n\n要繼續嗎？",
        "正在查 GitHub…": "正在查 GitHub…",
        "没查成": "沒查成",
        "可以用下面的办法：点「复制让 AI 帮我查的指令」，粘给 AI 让它帮你搜。": "可以用下面的辦法：點「複製讓 AI 幫我查的指令」，貼給 AI 讓它幫你搜。",
        "（搜到 %d 个，其中 %d 个与你的需求明显无关，已排除 —— GitHub 按星数排时经常把无关的高星项目排在最前）": "（搜到 %d 個，其中 %d 個與你的需求明顯無關，已排除 —— GitHub 按星數排時經常把無關的高星專案排在最前）",
        "——————": "——————",
        "这个结论只看客观信号（相关性、星数、是否还在更新、许可证），不替你做判断。拿不准就把上面的链接发给 AI 让它帮你评估。": "這個結論只看客觀訊號（相關性、星數、是否還在更新、授權條款），不替你做判斷。拿不準就把上面的連結發給 AI 讓它幫你評估。",
        "查完了：%s": "查完了：%s",
        "点「从我的答案生成」得到查询词，再点「查一下 GitHub」。\n\n连不上网也没关系：用「复制让 AI 帮我查的指令」，把那段话粘给 AI，它会帮你搜并评估能不能用。": "點「從我的答案產生」得到查詢詞，再點「查一下 GitHub」。\n\n連不上網也沒關係：用「複製讓 AI 幫我查的指令」，把那段話貼給 AI，它會幫你搜並評估能不能用。",
        "查询词已填好：%s\n\n点「查一下 GitHub」开始搜。\n搜之前可以自己改这行字。": "查詢詞已填好：%s\n\n點「查一下 GitHub」開始搜。\n搜之前可以自己改這行字。",
        "还没填「你想做什么」那一格，所以生成不出查询词。\n\n回到「填写需求」页填一两格再回来。": "還沒填「你想做什麼」那一格，所以產生不出查詢詞。\n\n回到「填寫需求」頁填一兩格再回來。",
        "（先回到「填写需求」页填一两格，再回来生成关键词）": "（先回到「填寫需求」頁填一兩格，再回來產生關鍵詞）",
        "指令已复制。切到 AI 对话框，按 Ctrl+V 粘贴发送就行。": "指令已複製。切到 AI 對話框，按 Ctrl+V 貼上送出就行。",
        "复制失败，可以直接从下面框里选中复制。": "複製失敗，可以直接從下面框裡選取複製。"
    },
    "en": {
        "先查查": "Check first",
        "动手做之前，先看看 GitHub 上有没有现成的": "Before you build, check whether it already exists on GitHub",
        "很多需求已经有成熟方案了。先查一眼，能省掉大量重复劳动；如果有能用的，拿现成的改通常比从零做更可靠。": "Many needs already have ready-made solutions. One quick look can save a lot of repeated work — and if something fits, adapting it is usually more reliable than building from scratch.",
        "查什么（可以自己改）：": "What to search for (you can edit this):",
        "🔄 从我的答案生成": "🔄 Generate from my answers",
        "点下面按钮才会联网（只把上面这行字发给 GitHub，你填的需求正文不会发出去）；不点就一直离线。": "The program only goes online when you click the button below (it sends just the line of text above to GitHub — the requirement text you typed is not sent). If you never click it, it stays offline the whole time.",
        "🔍 查一下 GitHub（会联网）": "🔍 Search GitHub (goes online)",
        "📋 复制「让 AI 帮我查」的指令（不联网）": "📋 Copy the “ask an AI to search for me” instruction (no internet)",
        "还没有查询词": "No search words yet",
        "先点「从我的答案生成」，或者自己写几个关键词。": "Click “Generate from my answers” first, or just type a few keywords yourself.",
        "要联网了": "About to go online",
        "接下来会把这一行字发给 GitHub 搜索：\n\n%s\n\n• 你填的需求正文**不会**发出去\n• 只搜公开项目，不登录、不提交任何东西\n\n要继续吗？": "This line of text will now be sent to GitHub to search:\n\n%s\n\n• The requirement text you typed will **not** be sent\n• Only public projects are searched — no login, and nothing is submitted\n\nContinue?",
        "正在查 GitHub…": "Searching GitHub…",
        "没查成": "The search didn't work",
        "可以用下面的办法：点「复制让 AI 帮我查的指令」，粘给 AI 让它帮你搜。": "You can use the button below: click “ask an AI to search for me”, paste that to your AI, and it will search for you.",
        "（搜到 %d 个，其中 %d 个与你的需求明显无关，已排除 —— GitHub 按星数排时经常把无关的高星项目排在最前）": "(Found %d results; %d of them are clearly unrelated to what you need and were filtered out — when GitHub sorts by star count, unrelated high-star projects often come out on top)",
        "——————": "——————",
        "这个结论只看客观信号（相关性、星数、是否还在更新、许可证），不替你做判断。拿不准就把上面的链接发给 AI 让它帮你评估。": "This conclusion is based only on objective signals (how relevant it is, star count, whether it is still updated, and its licence) — it does not make the judgement for you. If you are unsure, send the links above to your AI and let it help you judge.",
        "查完了：%s": "Search finished: %s",
        "点「从我的答案生成」得到查询词，再点「查一下 GitHub」。\n\n连不上网也没关系：用「复制让 AI 帮我查的指令」，把那段话粘给 AI，它会帮你搜并评估能不能用。": "Click “Generate from my answers” to get the search words, then click “Search GitHub”.\n\nNo internet? That's fine: click the “ask an AI to search for me” button instead, paste that text to your AI, and it will search for you and judge whether anything is usable.",
        "查询词已填好：%s\n\n点「查一下 GitHub」开始搜。\n搜之前可以自己改这行字。": "Search words filled in: %s\n\nClick “Search GitHub” to start.\nYou can edit this line before you search.",
        "还没填「你想做什么」那一格，所以生成不出查询词。\n\n回到「填写需求」页填一两格再回来。": "The “What kind of software do you want to make?” box is still empty, so no search words can be generated.\n\nGo back to the “Fill in the form” page, fill in one or two boxes, then come back.",
        "（先回到「填写需求」页填一两格，再回来生成关键词）": "(First go back to the “Fill in the form” page, fill in one or two boxes, then come back to generate the keywords)",
        "指令已复制。切到 AI 对话框，按 Ctrl+V 粘贴发送就行。": "Instruction copied. Switch to your AI chat, press Ctrl+V to paste it, and send.",
        "复制失败，可以直接从下面框里选中复制。": "Copying failed — you can select the text in the box below and copy it yourself."
    }
}
