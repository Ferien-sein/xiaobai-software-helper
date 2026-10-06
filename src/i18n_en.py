# -*- coding: utf-8 -*-
"""English language pack.

Keys are the Simplified Chinese source strings (verbatim as they appear in app.py);
values are the English translations.
"""

# Internal values left untranslated on purpose (never shown as UI text):
#   需求存档
#   使用说明.txt
#   提示词模板.txt
#   ===== 原始答案（给程序自己看，不用管） =====
#   ===== 原始答案结束 =====
#   微软雅黑
#   显示诊断.txt
# Strings that no longer exist in app.py (no catalog entry needed):
#   已填 
#    格

CATALOG = {
    # ---- <module> ----
    # app.py L27
    "小白造软件助手": "Little White's Software Helper",
    # app.py L54
    "（这一格还没填，请你直接问我）": "(This box isn't filled in yet — please ask me directly)",

    # ---- _system_options ----
    # app.py L88
    "（推荐）": " (recommended)",
    # app.py L88
    "跟我电脑一样：": "Same as my computer: ",
    # app.py L96
    "不确定，你帮我选最合适的": "Not sure — please pick the best one for me",

    # ---- _system_example ----
    # app.py L105
    "（我自己的电脑就是": " (my own computer is ",
    # app.py L105
    "例如：": "e.g. ",

    # ---- _system_help ----
    # app.py L114
    "为什么要问？\n  · 系统不同，做出来的东西完全不同：Windows 是 .exe，\n    Mac 是 .app，Linux 是 .AppImage/.deb，网页则都能打开。\n  · 位数也很关键：32 位程序在 32/64 位系统上都能跑，\n    但 64 位程序在 32 位系统上跑不起来。\n\n程序已经帮你探测过了：\n": "Why do we ask?\n  · Different systems produce completely different builds: Windows uses .exe,\n    Mac uses .app, Linux uses .AppImage/.deb, and a web page opens anywhere.\n  · 32-bit vs 64-bit matters too: a 32-bit program runs on both 32-bit and 64-bit\n    systems, but a 64-bit program will not run on a 32-bit system.\n\nThe program has already checked your machine:\n",
    # app.py L124
    "），\n   如果做出来是给别的电脑用，请直接选对方的系统。\n": "),\n   if it is being built for someone else's computer, just pick their system.\n",
    # app.py L124
    "\n⚠️ 探测结果可能不完全准确（": "\n⚠️ The detection result may not be completely accurate (",
    # app.py L126
    "\n只有当你做出来是给别人用时，才需要换成对方的系统。\n如果不确定对方的电脑，就选第一项，并在最后一格补充说明。": "\nYou only need to switch to someone else's system if you are making this for them.\nIf you are not sure about their computer, pick the first option and explain in the last box.",

    # ---- resolve_system_answer ----
    # app.py L167
    "跟我电脑一样": "Same as my computer",
    # app.py L167
    "不确定，你帮我选": "Not sure, you choose",
    # app.py L173
    "用户指定：": "User specified: ",

    # ---- <module> ----
    # app.py L186
    "标准": "Standard",
    # app.py L187
    "大一点（推荐）": "Larger (recommended)",
    # app.py L188
    "更大": "Even larger",
    # app.py L189
    "最大": "Largest",
    # app.py L206
    "暗色": "Dark",
    # app.py L230
    "浅色": "Light",
    # app.py L365
    "1. 你想做一个什么样的软件？": "1. What kind of software do you want to make?",
    # app.py L366
    "用你自己的话说清楚「这是个干什么的东西」，不用管技术词。": "Describe in your own words what this thing does — don't worry about technical terms.",
    # app.py L368
    "怎么说才算清楚？只要让一个完全不懂你工作的人听懂就行。\n\n✅ 好的说法：\n  · 一个帮我算装修报价的小工具\n  · 一个把三个 Excel 自动合并汇总的程序\n  · 一个记录每天花销、月底出图的记账小软件\n\n❌ 太含糊的说法：\n  · 一个管理系统（管理什么？给谁用？）\n  · 一个像抖音那样的软件（做不到，也太大了）\n\n提示：一次只做一件小事，做完能用、你满意了，再让我加功能。": "How clear is clear enough? If someone who knows nothing about your work can follow it, that's enough.\n\n✅ Good examples:\n  · A small tool that works out renovation quotes for me\n  · A program that merges and summarises three Excel files automatically\n  · A little expense tracker that records daily spending and charts it at month's end\n\n❌ Too vague:\n  · “A management system” (managing what? for whom?)\n  · “Something like TikTok” (not doable, and far too big)\n\nTip: do one small thing at a time. Once it works and you're happy with it, ask me to add more.",
    # app.py L378
    "例如：一个帮我把每天的三份销售 Excel 自动合并汇总、并标出金额对不上行的小工具": "e.g. A small tool that merges the three sales Excel files I get every day, summarises them, and flags the rows whose amounts don't match",
    # app.py L380
    "数据汇总/整理类（把文件或表格自动合并、统计）": "Data gathering/cleanup (merge and total up files or spreadsheets automatically)",
    # app.py L381
    "自动生成文件类（自动出 Excel/Word/PDF/图片）": "Auto-generated files (produce Excel/Word/PDF/images for you)",
    # app.py L382
    "日常记录/管理类（记账、客户、库存、待办）": "Everyday records/management (expenses, customers, stock, to-dos)",
    # app.py L383
    "计算/换算类（报价、工资、用料、单位换算）": "Calculations/conversions (quotes, wages, materials, unit conversion)",
    # app.py L384
    "娱乐/小工具类（随机、抽签、定时提醒）": "Fun/little utilities (random picks, draws, timed reminders)",
    # app.py L385
    "网页应用（浏览器里打开，可多人用）": "Web app (opens in a browser, several people can use it)",
    # app.py L392
    "2. 给谁用？一共几个人用？": "2. Who will use it? How many people in total?",
    # app.py L393
    "只有你自己用和给同事用，做法完全不同（要不要登录、要不要联网）。": "Software just for you and software shared with colleagues are built completely differently (logins, networking).",
    # app.py L395
    "为什么要问？\n  · 只有你自己用 → 最简单，不用账号、不用联网，双击就能跑。\n  · 几个同事用 → 需要考虑文件放哪、能不能同时改。\n  · 很多人/外部客户用 → 得做成网页或服务器程序，成本高很多。\n\n顺便说一句你的电脑水平也没关系，我会讲得通俗。": "Why do we ask?\n  · Just you → simplest: no accounts, no internet needed, double-click and it runs.\n  · A few colleagues → we need to think about where the files live and whether people edit them at the same time.\n  · Many people / outside customers → it has to be a web page or a server program, which costs a lot more.\n\nBy the way, it doesn't matter how much you know about computers — I'll keep it plain.",
    # app.py L401
    "例如：只有我自己用，一台 Windows 11 电脑": "e.g. Just me, on one Windows 11 computer",
    # app.py L403
    "只有我自己用": "Just me",
    # app.py L404
    "我和几个同事（2~10 人）": "Me and a few colleagues (2~10 people)",
    # app.py L405
    "整个部门/公司很多人": "A whole department/company — lots of people",
    # app.py L406
    "要给外部客户或手机上用": "For outside customers, or to use on a phone",
    # app.py L413
    "3. 这个软件要跑在什么系统上？32 位还是 64 位？": "3. What system should this software run on? 32-bit or 64-bit?",
    # app.py L414
    "选错了会导致「你这边做好了，在别人电脑上打不开」。默认按你自己的电脑来。": "The wrong choice means “it works on your machine but won't open on theirs”. Default is your own computer.",
    # app.py L428
    "4. 在哪里打开它？要不要联网？": "4. Where will you open it? Does it need the internet?",
    # app.py L429
    "决定做成桌面程序还是网页，以及数据存本地还是网上。": "This decides whether it becomes a desktop program or a web page, and whether the data lives on your PC or online.",
    # app.py L431
    "常见三种：\n  · 桌面程序（双击打开一个窗口）→ 最简单、最快、数据在自己电脑上。\n  · 本地网页（浏览器打开 127.0.0.1 之类的地址）→ 界面好看，仍在本机。\n  · 联网网站（别人也能访问）→ 需要服务器和域名，要花钱、也复杂。\n\n另外请说明数据敏不敏感：能上传到网上吗？还是必须留在本机？\n不确定就写「你帮我选」。": "There are three common kinds:\n  · Desktop program (double-click to open a window) → simplest and fastest; the data stays on your own computer.\n  · Local web page (opened in a browser at an address like 127.0.0.1) → nicer interface, still on your own machine.\n  · Online website (other people can visit it) → needs a server and a domain name; costs money and is more complex.\n\nAlso tell me how sensitive the data is: may it be uploaded to the internet, or must it stay on this computer?\nIf you're not sure, write “you choose for me”.",
    # app.py L438
    "例如：在 Windows 电脑上双击打开，不用联网，数据必须留在本机": "e.g. Double-click to open on a Windows computer, no internet needed, and the data must stay on this machine",
    # app.py L440
    "Windows 电脑上双击打开的窗口程序": "A window program that opens by double-clicking on a Windows computer",
    # app.py L441
    "浏览器里打开的本地网页": "A local web page opened in a browser",
    # app.py L442
    "手机上也能用": "I want to use it on my phone too",
    # app.py L443
    "要联网 / 别人也能访问": "Needs the internet / other people must be able to visit it",
    # app.py L444
    "数据不允许上传，必须留在本机": "The data may not be uploaded; it must stay on this computer",
    # app.py L452
    "5. 它帮你解决什么麻烦？（现在你是怎么手动做的）": "5. What hassle does it save you? (How do you do it by hand today?)",
    # app.py L453
    "把现在的真实做法写一遍，这比任何抽象描述都有用。": "Write down how you really do it now — that is worth more than any abstract description.",
    # app.py L455
    "这是最重要的一格。请像讲故事一样写清楚：\n  现在做这件事，你要点开什么、点什么、复制到哪里、容易在哪里出错、\n  大概要花多长时间。\n\n✅ 例子：\n  「每天下午我从系统导出 3 个 Excel，手动复制粘贴到汇总表，\n   再一个个核对客户名，一般要 40 分钟，月底经常发现有两行金额抄错。」\n\n你写得越具体，我做出来的东西就越贴合你的实际工作，而不是一个空壳。": "This is the most important box. Please write it like a story:\n  When you do this today, what do you open, what do you click, where do you paste,\n  where do mistakes usually happen, and roughly how long does it take?\n\n✅ Example:\n  “Every afternoon I export 3 Excel files from the system and copy-paste them into a summary sheet by hand,\n   then check the customer names one by one. It usually takes 40 minutes, and at the end of the month I often\n   find two rows with the wrong amount.”\n\nThe more specific you are, the more the thing I build will fit your real work instead of being an empty shell.",
    # app.py L463
    "例如：现在每天手动复制粘贴三个表，约 40 分钟，客户名不一致时经常漏行": "e.g. Right now I copy and paste three sheets by hand every day, about 40 minutes, and rows go missing when the customer names don't match",
    # app.py L465
    "重复复制粘贴，太花时间": "Repeated copy-pasting takes too much time",
    # app.py L466
    "人工计算/核对，容易出错": "Working it out/checking by hand — easy to get wrong",
    # app.py L467
    "文件太多、太乱，找不到": "Too many messy files — I can't find anything",
    # app.py L468
    "格式/格式转换很烦（如 PDF、图片、Word 互转）": "Converting formats is a pain (PDF, images, Word back and forth)",
    # app.py L469
    "要按时提醒或被催": "I need reminders on time, or I'm always being chased",
    # app.py L476
    "6. 你希望怎么操作它？（从打开到结束，一步步说）": "6. How do you want to operate it? (Step by step, from opening to finishing)",
    # app.py L477
    "你描述步骤，我照着做界面，不用懂任何设计。": "You describe the steps and I'll build the interface to match. You don't need to know anything about design.",
    # app.py L479
    "写成编号步骤最清楚，比如：\n  1）双击打开，看到一个大按钮「选择文件」\n  2）我把当天的 3 个 Excel 拖进去\n  3）点「开始汇总」\n  4）它显示一共多少条、哪几行金额对不上\n  5）点「导出结果」，在桌面得到一个汇总表\n\n想不出界面细节也没关系，写「你看着办，越简单越好」就行。": "Numbered steps are clearest, for example:\n  1) I double-click to open it and see one big “Choose files” button\n  2) I drag in the day's 3 Excel files\n  3) I click “Start merging”\n  4) It shows how many rows there are and which rows' amounts don't match\n  5) I click “Export results” and get a summary sheet on my desktop\n\nIf you can't picture the details, that's fine — just write “your call, as simple as possible”.",
    # app.py L487
    "例如：1）拖入文件 2）点汇总 3）看异常提示 4）点导出，桌面得到结果表": "e.g. 1) Drag files in 2) Click merge 3) Read the warnings 4) Click export and get the result sheet on my desktop",
    # app.py L489
    "越简单越好，最好一键完成": "As simple as possible — ideally one click",
    # app.py L490
    "拖文件进去，点一下按钮": "Drag files in, click one button",
    # app.py L491
    "填几个数字/短句，点计算": "Type a few numbers/short phrases, click calculate",
    # app.py L492
    "先选设置，再批量处理很多文件": "Pick the settings first, then process many files in one go",
    # app.py L493
    "你看着办": "Your call",
    # app.py L500
    "7. 输入从哪来？（数据/文件从哪来，长什么样）": "7. Where does the input come from? (Where the data/files come from and what they look like)",
    # app.py L501
    "告诉我输入什么样，我才能保证读得进、读得对。": "Tell me what the input looks like so I can be sure it reads the right things correctly.",
    # app.py L503
    "说清楚：\n  · 手动打字？还是已有文件？\n  · 什么格式：Excel(.xlsx)/CSV/Word/PDF/图片/网页/微信记录？\n  · 文件长什么样：第一行是标题吗？大概多少行多少列？有哪些列？\n  · 有几个文件、放在哪个文件夹、文件名有规律吗？\n\n⭐ 最有用的一招：直接放一份真实的（或脱敏的）样例文件到工作文件夹里，\n   并在这里写上文件名，我就能照着真实数据做。\n   如果格式比较怪（合并单元格、多个工作表、图片里的表格），一定要说。": "Be clear about:\n  · Do you type it in by hand, or does a file already exist?\n  · What format: Excel(.xlsx)/CSV/Word/PDF/image/web page/chat records?\n  · What the file looks like: is the first row a heading? Roughly how many rows and columns? Which columns?\n  · How many files, in which folder, and do the file names follow a pattern?\n\n⭐ The single most useful trick: put a real (or anonymised) sample file in the working folder,\n   write its file name here, and I can build against real data.\n   If the format is odd (merged cells, several worksheets, tables inside images), you must say so.",
    # app.py L512
    "例如：我手动从系统导出 3 个 .xlsx 文件放到「每日数据」文件夹，第一行是标题，列有 日期/客户/金额，每天约 200 行；样例文件：样例.xlsx": "e.g. I export 3 .xlsx files from the system by hand into a “Daily data” folder; the first row is the heading, the columns are Date/Customer/Amount, about 200 rows a day; sample file: sample.xlsx",
    # app.py L515
    "手动打字输入": "I type it in by hand",
    # app.py L516
    "Excel 文件（.xlsx/.xls）": "Excel files (.xlsx/.xls)",
    # app.py L517
    "CSV 文本表格": "CSV text tables",
    # app.py L518
    "Word / PDF / 图片（需要识别文字）": "Word / PDF / images (text has to be recognised)",
    # app.py L519
    "复制粘贴一段文字给你": "I'll copy and paste some text to you",
    # app.py L520
    "我会放一份样例文件在文件夹里": "I'll put a sample file in the folder",
    # app.py L521
    "格式比较特殊（合并单元格/多表/扫描件）": "The format is unusual (merged cells / several sheets / scanned pages)",
    # app.py L528
    "8. 输出/结果要长什么样？": "8. What should the output/result look like?",
    # app.py L529
    "你要看到什么、拿到什么文件，这决定了我做成什么样才算完成。": "What you want to see and which files you want to get — that's how I know when it's finished.",
    # app.py L531
    "从这些角度说：\n  · 屏幕上要看到什么（数字、列表、红字提醒、图表？）\n  · 要生成文件吗？格式和文件名？保存到哪个文件夹（桌面？）\n  · 需要打印、发微信、发邮件吗？\n\n✅ 例子：「屏幕上显示总金额和异常行数，导出 Excel 到桌面，\n   文件名带当天日期，表头加粗、金额保留两位小数。」": "Answer from these angles:\n  · What should appear on screen (numbers, a list, red warnings, a chart?)\n  · Should it create a file? Which format and file name? Which folder (the desktop?)\n  · Do you need to print it, send it by chat, or email it?\n\n✅ Example: “Show the total amount and the number of problem rows on screen, export an Excel file to the desktop,\n   put today's date in the file name, make the heading bold and keep two decimal places.”",
    # app.py L538
    "例如：屏幕显示汇总结果和异常行；导出 Excel 到桌面，文件名 = 汇总_日期.xlsx": "e.g. Show the summary and the problem rows on screen; export Excel to the desktop with the file name = Summary_date.xlsx",
    # app.py L540
    "屏幕上显示结果就行": "Showing the result on screen is enough",
    # app.py L541
    "导出 Excel 表格": "Export an Excel spreadsheet",
    # app.py L542
    "导出 Word 文档": "Export a Word document",
    # app.py L543
    "导出 PDF": "Export PDF",
    # app.py L544
    "生成图片（可发微信/打印）": "Create an image (to send in a chat or print)",
    # app.py L545
    "要打印": "I need to print it",
    # app.py L546
    "要有图表/统计图": "I need charts/graphs",
    # app.py L547
    "要能一键复制结果文字": "I need one-click copying of the result text",
    # app.py L554
    "9. 怎么算做好了？（成功的标准）": "9. How do we know it's done? (What counts as success)",
    # app.py L555
    "给我一个你自己能验证的标准，我才能自己测到对为止。": "Give me a standard you can check yourself, so I can keep testing until it meets it.",
    # app.py L557
    "最好写成「拿什么数据跑一遍，看到什么结果，就算成功」，例如：\n  · 拿上周的 3 个文件跑一遍，总金额和财务给的数字一模一样；\n  · 把 x 输入进去，输出的结果等于 y；\n  · 以前 40 分钟的活，现在 2 分钟做完，且不再需要人工核对。\n\n这样我会自己反复测试到达标，而不是做出个「看起来能用」的东西交给你。": "The best wording is “run it on this data, see this result, and that counts as success”, for example:\n  · Run the 3 files from last week: the total matches the number Finance gave, exactly;\n  · Put x in and the result comes out as y;\n  · A job that used to take 40 minutes now takes 2, with no manual checking.\n\nThat way I can test it over and over until it meets the bar, instead of handing you something that merely looks usable.",
    # app.py L563
    "例如：拿上周 3 个文件跑一遍，总金额与财务数一致，异常行全部标出": "e.g. Run last week's 3 files: the total matches Finance's number and every problem row is flagged",
    # app.py L565
    "数据结果和人工算的完全一致": "The results match what I work out by hand, exactly",
    # app.py L566
    "以前要 X 分钟，现在 1 分钟内完成": "Work that used to take X minutes now finishes within 1 minute",
    # app.py L567
    "生成的表格/文档我能直接发给客户或打印": "The spreadsheet/document it produces can go straight to a customer or to the printer",
    # app.py L568
    "不用我再去核对，出错它会提示": "I don't have to check it again — it warns me when something is wrong",
    # app.py L575
    "10. 有什么不能做 / 必须遵守的规矩？": "10. What must it not do / what rules must it follow?",
    # app.py L576
    "这一格能防止我做出来的东西碰你不该碰的数据，或者白做。": "This box keeps what I build away from data it shouldn't touch — and stops me wasting effort.",
    # app.py L578
    "请说明：\n  · 不可以动哪些文件、文件夹、系统设置？\n  · 数据能不能上传到网上？（公司机密、客户隐私很关键）\n  · 要不要保留操作记录、要不要每次先备份？\n  · 电脑上有没有杀毒/权限限制，不能装东西？\n  · 有没有截止时间或必须用某种工具（比如只能用 Excel）？\n\n没有特别要求就写「没有特别要求」。": "Please say:\n  · Which files, folders or system settings must it leave alone?\n  · May the data be uploaded to the internet? (Company secrets and customer privacy really matter here)\n  · Should it keep a log of what it did? Should it back things up first every time?\n  · Does the computer have antivirus/permission limits that stop new software being installed?\n  · Is there a deadline, or a tool it must use (for example, Excel only)?\n\nIf there is nothing special, just write “nothing special”.",
    # app.py L586
    "例如：不要动 D 盘财务原始文件；数据绝对不能上传；每次先备份一份": "e.g. Don't touch the original finance files on drive D:; the data must never be uploaded; always back up first",
    # app.py L588
    "没有特别要求": "Nothing special",
    # app.py L589
    "数据绝对不能上传到网上": "The data must never be uploaded to the internet",
    # app.py L590
    "不要修改/删除我的原始文件": "Don't change or delete my original files",
    # app.py L591
    "每次操作前自动备份一份": "Back up automatically before every operation",
    # app.py L592
    "电脑不能安装新软件": "I can't install new software on this computer",
    # app.py L593
    "只能用 Office/Excel 实现": "It has to be done with Office/Excel only",
    # app.py L594
    "有截止时间": "There is a deadline",
    # app.py L601
    "11. 有没有想模仿的参照物？（可选）": "11. Is there anything you want to copy? (optional)",
    # app.py L602
    "给我一个参照，比你形容半天界面都准确。": "One reference point is more accurate than any amount of describing the interface.",
    # app.py L604
    "可以写：某个软件/网站的某一部分（截图、网址、名字都行），\n或者「上面的按钮位置」「表格样式像那样」。\n\n如果要模仿某个收费软件的全部功能，要提前说清预算和范围，我会告诉你哪些能实现、哪些建议先不做。": "You can write: a part of some program/website (a screenshot, a link or just the name),\nor “the buttons go up there”, “the table looks like that”.\n\nIf you want to copy every feature of some paid program, tell me your budget and scope up front, and I'll tell you which parts are doable and which I'd suggest leaving out for now.",
    # app.py L609
    "例如：界面像微信电脑版那种左边列表、右边内容就行": "e.g. An interface like WeChat for Windows — a list on the left, content on the right",
    # app.py L611
    "没有参照，你设计一个简洁的": "No reference — you design something clean",
    # app.py L612
    "我有截图/网址，等下单独发给你": "I have screenshots/links; I'll send them to you separately",
    # app.py L613
    "要像 Excel 那样的表格界面": "A spreadsheet-style interface like Excel",
    # app.py L620
    "12. 你希望怎么用它、怎么再打开？（怎么交付给你）": "12. How do you want to use it and open it again? (How should it be delivered to you)",
    # app.py L621
    "这决定我最终交给你的是 exe、网页还是一堆文件。": "This decides whether what I hand you is an exe, a web page, or a pile of files.",
    # app.py L623
    "常见选择：\n  · 一个 exe，双击就打开（最省事，推荐小白）\n  · 一个文件夹，双击里面的 启动.bat 打开\n  · 一个本地网址，浏览器打开\n\n另外说说：要不要做桌面快捷方式？以后想加功能怎么办？\n写「你决定」完全可以，我会挑最省事的方案。": "The usual choices:\n  · One exe file — double-click and it opens (easiest; best if you're not technical)\n  · One folder — double-click the 启动.bat inside it\n  · A local web address, opened in a browser\n\nAlso say: do you want a desktop shortcut? What about adding features later?\nWriting “you decide” is perfectly fine — I'll pick the least troublesome route.",
    # app.py L630
    "例如：给我一个 exe 放桌面，双击就打开": "e.g. Give me one exe on the desktop that opens when I double-click it",
    # app.py L632
    "一个 exe 文件，双击打开（推荐）": "One exe file, opened by double-clicking (recommended)",
    # app.py L633
    "一个文件夹，双击 启动.bat": "One folder; double-click 启动.bat inside it",
    # app.py L634
    "浏览器打开本地网址": "Open a local web address in a browser",
    # app.py L635
    "要放到桌面，方便我随时点开": "Put it on the desktop so I can open it any time",
    # app.py L636
    "你决定就好": "You decide",
    # app.py L643
    "13. 还想补充什么？（可选，想到什么写什么）": "13. Anything else to add? (optional — write down whatever comes to mind)",
    # app.py L644
    "零散的想法、担心的地方、以后想加的功能，都写在这里。": "Scattered ideas, worries, features you might want later — put them all here.",
    # app.py L646
    "这里可以写得很随意，比如：\n  · 「我不懂技术，你要多解释几句」\n  · 「先做最简单的版本，我试过再加功能」\n  · 「以后想加个手机端」\n  · 「我怕数据丢了」\n\n这些都会写进需求说明里，我会照着办。": "You can be as casual as you like here, for example:\n  · “I'm not technical, so please explain things a bit more”\n  · “Build the simplest version first; I'll ask for more once I've tried it”\n  · “I might want a phone version later”\n  · “I'm afraid of losing data”\n\nAll of this goes into the requirement brief, and I'll follow it.",
    # app.py L653
    "例如：我不懂技术，做完请告诉我怎么打开、怎么备份；先做最简版本": "e.g. I'm not technical — when it's done, tell me how to open it and how to back it up; start with the simplest version",
    # app.py L655
    "我不懂技术，请用大白话解释并一步步教我": "I'm not technical — please explain in plain words and teach me step by step",
    # app.py L656
    "先做最简单能用的版本，我试过再加功能": "Build the simplest usable version first; I'll add features after I've tried it",
    # app.py L657
    "以后可能还要加功能，代码请留好扩展余地": "I may want more features later, so please leave the code easy to extend",
    # app.py L658
    "我怕数据丢失，请做好备份": "I'm worried about losing data — please handle backups properly",
    # app.py L665
    "{app} v{ver}\n\n它是干什么的？\n  你按它列的 12 个问题填一填（能点选项就点，不用会打字），\n  右边会自动拼出一段「需求说明」。\n  点「复制需求」，粘贴给 AI，它就能开始给你做软件。\n\n为什么问这些？\n  不是因为流程麻烦，而是这几条正好是决定「做出来能不能用」的关键：\n  给谁用、输入长什么样、什么算做好了。\n  少一条，AI 就可能做出一个你不满意的东西。\n\n三件小事\n  · 每题下面的「看例子」会告诉你该怎么写，写着「可选」的可以不填。\n  · 写错了、写少了都没关系，以后随时改，改完重新复制一次就行。\n  · 「保存到文件」会在 需求存档 文件夹里留一份。之后可以在「历史记录」\n    这一页里找回来：双击就能整份还原到填写页继续改，不用重填。\n    建议每次跟 AI 提需求前都先保存一下。\n\n界面太小 / 太大 / 有点糊怎么办\n  · 程序会自动读 Windows 的缩放（你这台机器是 225%），按同样比例显示，\n    这样字最清晰 —— 不要手动把「显示大小」调到比 Windows 缩放差太多的值，\n    那种情况下 Windows 只能把界面当图片拉伸，字就会发糊。\n  · 点左下角「🔍 显示大小」可以调整（100%~250%）。它会先告诉你：\n    Windows 是多少、推荐用多少。\n  · 如果觉得字发糊，点左下角「🩺 显示诊断」，它会生成一份报告并直接给出\n    结论（在哪被拉伸了、字体是什么、DPI 是多少），把报告发出去就能排查。\n  · 想彻底改观感，也可以在 Windows 里调：\n    设置 → 系统 → 屏幕 → 缩放与布局；以及 ClearType 文本调谐器。\n": "{app} v{ver}\n\nWhat is it for?\n  Fill in the 12 questions it lists (click the options where you can — no typing needed),\n  and the right-hand side puts together a “requirement brief” for you.\n  Click “Copy requirement”, paste it to your AI, and it can start making your software.\n\nWhy ask all this?\n  Not because the process is fussy, but because these few things decide whether what gets\n  built is usable: who it's for, what the input looks like, and what counts as done.\n  Miss one and the AI may build something you're not happy with.\n\nThree small things\n  · “See examples” under each question tells you how to write it. Anything marked “optional”\n    can be left blank.\n  · It doesn't matter if you write something wrong or too short — you can change it any time,\n    and copying it again is enough.\n  · “Save to file” keeps a copy in the 需求存档 folder. Later you can find it again on the\n    “History” page: double-click to restore the whole thing to the form and keep editing,\n    with nothing to retype. It's worth saving before every request you make to the AI.\n\nThe interface is too small / too big / a bit blurry — what now?\n  · The program reads your Windows scaling automatically (this machine is 225%) and displays at\n    the same ratio, which keeps text sharpest — don't set “Display size” by hand to something far\n    from your Windows scaling; in that case Windows can only stretch the interface like a picture,\n    and the text goes blurry.\n  · Click “🔍 Display size” at the bottom left to adjust it (100%~250%). It first tells you what\n    Windows uses and what it recommends.\n  · If the text looks blurry, click “🩺 Display diagnostics” at the bottom left. It writes a report\n    and gives you the conclusion straight away (where it's being stretched, which font, what DPI);\n    send that report on and the problem can be tracked down.\n  · If you want to change the look for good, you can also adjust it in Windows:\n    Settings → System → Display → Scale & layout, and the ClearType Text Tuner.\n",

    # ---- _target_block_for_prompt ----
    # app.py L728
    "不确定": "Not sure",
    # app.py L730
    "用户填写：": "User wrote: ",
    # app.py L736
    "请把它做成能在下列平台上直接运行：": "Please build it so it runs directly on the following platform: ",
    # app.py L741
    "），如果你判断目标平台不是上面这个，请先问我。": "), and if you judge that the target platform is not the one above, ask me first.",
    # app.py L740
    "⚠️ 本机探测结果可能不准确（": "⚠️ The detection result for this machine may be inaccurate (",
    # app.py L743
    "交付要求：请给出该平台上可以直接打开使用的成品，并说明在目标电脑上第一次打开需要做什么（例如 Windows 上可能要「解除锁定」）。": "Delivery: please provide something that can be opened and used straight away on that platform, and explain what has to be done the first time it is opened on the target computer (for example, on Windows you may need to “unblock” it).",

    # ---- build_prompt ----
    # app.py L759
    "【我完全不懂技术，下面是我的需求，请你帮我把这个软件做出来。】": "[I know nothing about technology. Below is my requirement — please help me get this software made.]",
    # app.py L761
    "先说清楚我们的合作方式：": "First, let's be clear about how we'll work together:",
    # app.py L762
    "1. 如果下面有哪里没写清楚、或者你觉得会影响结果，请先问我（一次问 2~5 个，用大白话问，不要用技术名词考我），问清楚再动手。": "1. If anything below isn't clear, or you think it will affect the result, ask me first (2~5 questions at a time, in plain language — don't test me with technical terms), and only start once it's clear.",
    # app.py L764
    "2. 技术方案（用什么语言、什么工具、怎么打包）你自己决定；如果有影响我使用的取舍，告诉我两个选项各自的好处就行。": "2. The technical choices (which language, which tools, how to package it) are up to you; if there's a trade-off that affects how I use it, just tell me the benefit of each option.",
    # app.py L766
    "3. 请你自己动手做完并自己测试通过，最后给我一个能直接双击打开、或能直接打开的成品，并告诉我放在哪个路径、怎么再次打开。": "3. Please do the work yourself and test it yourself until it passes, then give me something I can open by double-clicking (or open directly), and tell me where it is and how to open it again.",
    # app.py L768
    "4. 交付时请一并告诉我：怎么用、怎么备份数据、有哪些你没做到或做不到的地方。": "4. When you deliver it, also tell me: how to use it, how to back up the data, and anything you didn't do or couldn't do.",
    # app.py L769
    "5. 不要只给我代码和说明书让我自己想办法运行，我看不懂。": "5. Don't just give me code and a manual and leave me to work out how to run it — I won't understand it.",
    # app.py L772
    "我的需求": "My requirement",
    # app.py L783
    "  选择：": "  Choice: ",
    # app.py L799
    "目标平台（重要）": "Target platform (important)",
    # app.py L806
    "补充情况": "Additional notes",
    # app.py L808
    "· 我的水平：完全不懂编程，请用大白话解释，并一步一步教我怎么用。": "· My level: I know nothing about programming. Please explain in plain language and teach me how to use it step by step.",
    # app.py L809
    "· 我希望你高度自主地完成：能自己决定的事就别问我，只在真正需要我选择时才问。": "· I'd like you to work as independently as possible: don't ask me about things you can decide yourself — only ask when I really have to choose.",
    # app.py L810
    "· 做完请告诉我：结果文件在哪个文件夹、以后怎么再打开它。": "· When it's done, tell me which folder the result files are in, and how to open it again later.",
    # app.py L812
    "如果上面的信息还不够你做决定，请直接问我；信息够的话，请现在就开工。": "If the information above isn't enough for you to decide, just ask me; if it is enough, please start now.",

    # ---- <module> ----
    # app.py L830
    "(还没声明)": "(not declared yet)",
    # app.py L832
    "还没探测": "not detected yet",

    # ---- detect_recommended_scale ----
    # app.py L885
    "Windows 缩放设置（注册表 LogPixels=%s）": "Windows scaling setting (registry LogPixels=%s)",
    # app.py L889
    "系统实测 DPI = %s": "Measured system DPI = %s",

    # ---- apply_dpi_awareness ----
    # app.py L1060
    "ctypes 不可用: %r": "ctypes unavailable: %r",
    # app.py L1071
    "SetProcessDpiAwarenessContext(-4) 返回 %s，GetLastError=%s": "SetProcessDpiAwarenessContext(-4) returned %s, GetLastError=%s",
    # app.py L1077
    "SetProcessDpiAwarenessContext(-4) 异常: %r": "SetProcessDpiAwarenessContext(-4) raised: %r",
    # app.py L1082
    "SetProcessDpiAwareness(2) 返回 HRESULT=%s": "SetProcessDpiAwareness(2) returned HRESULT=%s",
    # app.py L1087
    "SetProcessDpiAwareness(2) 异常: %r": "SetProcessDpiAwareness(2) raised: %r",
    # app.py L1092
    "SetProcessDPIAware() 返回 %s": "SetProcessDPIAware() returned %s",
    # app.py L1097
    "SetProcessDPIAware() 异常: %r": "SetProcessDPIAware() raised: %r",
    # app.py L1099
    "三种方式都没成功，进程仍是 DPI 未声明状态": "None of the three methods worked; the process is still DPI-unaware",

    # ---- run_diagnostics ----
    # app.py L1113
    "手动触发": "triggered manually",
    # app.py L1118
    "界面显示诊断报告": "Interface display diagnostics report",
    # app.py L1118
    "触发原因：%s": "Triggered by: %s",
    # app.py L1119
    "时间：%s": "Time: %s",
    # app.py L1123
    "【DPI 感知】（这一段是判断字糊不糊的关键）": "[DPI awareness] (this section is what decides whether text is blurry)",
    # app.py L1124
    "  声明结果(本进程启动时)  : %s": "  Declaration result (at process start): %s",
    # app.py L1128
    "  GetProcessDpiAwareness : %s  (0=未声明 1=系统 2=每显示器)": "  GetProcessDpiAwareness : %s  (0=unaware 1=system 2=per-monitor)",
    # app.py L1131
    "  GetProcessDpiAwareness : 读取失败 %s": "  GetProcessDpiAwareness : read failed %s",
    # app.py L1133
    "  GetDpiForSystem         : %s   (=96 且屏幕是 4K 就说明没声明成功)": "  GetDpiForSystem         : %s   (=96 with a 4K screen means the declaration did not succeed)",
    # app.py L1140
    "  当前线程感知上下文      : %s": "  Current thread awareness context: %s",
    # app.py L1146
    "  → 实际相当于           : %s": "  → Effectively            : %s",
    # app.py L1151
    "  线程上下文读取失败: %s": "  Failed to read thread context: %s",
    # app.py L1153
    "【Windows 缩放设置】": "[Windows scaling settings]",
    # app.py L1162
    "  %-14s = (读不到)": "  %-14s = (cannot read)",
    # app.py L1164
    "【屏幕】": "[Screen]",
    # app.py L1166
    "  屏幕尺寸(Tk 报告)       : %d x %d": "  Screen size (Tk report)  : %d x %d",
    # app.py L1167
    "  屏幕尺寸(系统物理)      : %s x %s": "  Screen size (physical)   : %s x %s",
    # app.py L1169
    "  Windows 推荐缩放        : %d%%   (依据：%s)": "  Windows recommended scale : %d%%   (based on: %s)",
    # app.py L1171
    "  程序实际使用缩放        : %d%%": "  Scale actually in use     : %d%%",
    # app.py L1172
    "  字号档位(FONT_BOOST)    : %.2f": "  Font size step (FONT_BOOST) : %.2f",
    # app.py L1174
    "【窗口与字体】": "[Window and fonts]",
    # app.py L1178
    "  窗口句柄                : %s": "  Window handle            : %s",
    # app.py L1184
    "  窗口尺寸                : %d x %d": "  Window size              : %d x %d",
    # app.py L1186
    "  窗口位置                : +%d+%d": "  Window position          : +%d+%d",
    # app.py L1193
    "  ⚠ 判定：窗口 DPI(%s) > 进程 DPI(%s)，Windows 在拉伸这个窗口 → 字会发糊": "  ⚠ Verdict: window DPI (%s) > process DPI (%s); Windows is stretching this window → text will look blurry",
    # app.py L1197
    "  ✔ 判定：进程 DPI(%s) 与窗口 DPI(%s) 一致，按真实像素渲染，字应当清晰": "  ✔ Verdict: process DPI (%s) matches window DPI (%s); rendering at real pixels, text should be sharp",
    # app.py L1199
    "  实际使用字体            : %s": "  Font actually used       : %s",
    # app.py L1202
    "  系统里是否有雅黑        : %s": "  Microsoft YaHei present  : %s",
    # app.py L1208
    "  %-10s 请求=%s 实际=%s 行高=%spx": "  %-10s requested=%s actual=%s linespace=%spx",
    # app.py L1212
    "  读取窗口信息失败: %s": "  Failed to read window info: %s",
    # app.py L1214
    "  （启动阶段调用，还没有窗口）": "  (called at startup — no window yet)",
    # app.py L1216
    "【怎么读这份报告】": "[How to read this report]",
    # app.py L1217
    "  · 先看「→ 实际相当于」那行，应该是 per-monitor-v2 或 per-monitor。": "  · First look at the “→ Effectively” line; it should be per-monitor-v2 or per-monitor.",
    # app.py L1218
    "  · 再看「判定」那行。如果出现 ⚠，字糊是 Windows 拉伸造成的。": "  · Then look at the “Verdict” line. If it shows ⚠, the blur comes from Windows stretching.",
    # app.py L1219
    "  · 若 GetDpiForSystem = 96 但屏幕物理尺寸是 3840x2160，": "  · If GetDpiForSystem = 96 but the physical screen size is 3840x2160,",
    # app.py L1220
    "    说明进程没声明成功，Windows 只能把界面当图片放大。": "    the process never declared its awareness, so Windows can only blow the interface up like a picture.",
    # app.py L1223
    "诊断过程出错：%s": "Diagnostics failed: %s",
    # app.py L1231
    "（写不进去：%s）": "(cannot write: %s)",

    # ---- App.__init__ ----
    # app.py L1283
    " —— 把想法变成给 AI 的需求说明": " —— turning an idea into a requirement brief for your AI",

    # ---- App.warn_tiny_screen ----
    # app.py L1333
    "界面可能太小": "The interface may be too small",
    # app.py L1334
    "检测到你的屏幕是 4K（或更高），但 Windows 的缩放仍是 100%，\n所以这个界面看起来会偏小。\n\n要现在把界面放大到 150% 吗？\n（会重启这个小工具；不喜欢可以随时点右下角「显示大小」改回来）": "Your screen appears to be 4K (or higher), but Windows scaling is still 100%,\nso this interface will look rather small.\n\nWould you like to enlarge the interface to 150% now?\n(This restarts the little tool; if you don't like it, click “Display size” to change it back.)",

    # ---- App ----
    # app.py L1469
    "填写需求": "Fill in the form",
    # app.py L1469
    "历史记录": "History",
    # app.py L1469
    "使用说明": "How to use",

    # ---- App._build_sidebar ----
    # app.py L1490
    "小白造软件": "Little White's Software",
    # app.py L1493
    "助手": "Helper",
    # app.py L1511
    "◐  切换主题（%s）": "◐  Switch theme (%s)",
    # app.py L1513
    "🔍  显示大小 %d%%": "🔍  Display size %d%%",
    # app.py L1514
    "🩺  显示诊断": "🩺  Display diagnostics",
    # app.py L1515
    "✕  退出": "✕  Quit",

    # ---- App._build_body ----
    # app.py L1641
    "把想法说清楚，剩下的交给 AI": "Say what you want clearly — let the AI do the rest",
    # app.py L1643
    "① 左边填一填   →   ② 右边自动生成   →   ③ 点「复制需求」粘贴给 AI　·　每题下面有「看例子」，标着「可选」的可以不填": "① Fill it in on the left   →   ② It's generated on the right   →   ③ Click “Copy requirement” and paste it to your AI　·　Every question has “See examples”, and anything marked “optional” can be left blank",

    # ---- App._build_history ----
    # app.py L1690
    "你点过「保存到文件」的需求都收在这里，随时可以找回来改。": "Every requirement you saved with “Save to file” is kept here, ready to bring back and edit.",
    # app.py L1692
    "🔄 刷新": "🔄 Refresh",
    # app.py L1693
    "📂 打开存档文件夹": "📂 Open archive folder",
    # app.py L1703
    "存档列表（双击可载入）": "Saved items (double-click to load)",
    # app.py L1720
    "内容预览": "Content preview",
    # app.py L1731
    "↩ 载入到填写页修改": "↩ Load into the form to edit",
    # app.py L1734
    "📋 复制这份内容": "📋 Copy this content",
    # app.py L1735
    "🗑 删除这份存档": "🗑 Delete this saved item",

    # ---- App.read_archive ----
    # app.py L1747
    "（读取失败：": "(read failed: ",

    # ---- App._parse_legacy ----
    # app.py L1775
    "（这一格还没填": "(this box isn't filled in",

    # ---- App.refresh_history ----
    # app.py L1799
    "未命名": "Untitled",
    # app.py L1801
    "还没有存档": "No saved items yet",
    # app.py L1801
    "共 ": "Total ",
    # app.py L1801
    " 份存档": " saved items",
    # app.py L1803
    "这里还是空的。\n\n回到「填写需求」那页，填好之后点左下角「💾 保存到文件」，\n以后就能在这里找回、修改、重新复制了。": "This is still empty.\n\nGo back to the “Fill in the form” page, and when you're done click “💾 Save to file” at the bottom left;\nafter that you can find it, edit it and copy it again here.",

    # ---- App.on_history_select ----
    # app.py L1830
    "\n（这份存档带有原始答案，可以点「载入到填写页修改」整份还原）": "\n(This saved item carries the original answers — click “Load into the form to edit” to restore the whole thing)",
    # app.py L1832
    "\n（有 ": "\n(",
    # app.py L1832
    " 格当时没填，我会让 AI 直接问你）": " boxes were left blank at the time; I'll have the AI ask you directly)",

    # ---- App.copy_history ----
    # app.py L1839
    "还没有选中": "Nothing selected",
    # app.py L1839
    "请先在左边列表里点一份存档。": "Click one of the saved items in the list on the left first.",
    # app.py L1845
    "已复制这份内容 ✔": "Copied this content ✔",

    # ---- App.load_history ----
    # app.py L1854
    "无法完整还原": "Can't fully restore",
    # app.py L1855
    "这份存档是旧版本保存的，认不出原始答案。\n\n你可以点「复制这份内容」把它发给 AI。": "This saved item was written by an old version, so the original answers can't be recognised.\n\nYou can click “Copy this content” and send it to your AI.",
    # app.py L1886
    "已载入存档，改完再点「复制需求」发给 AI 就行。": "Saved item loaded. Edit it if you like, then click “Copy requirement” and send it to your AI.",

    # ---- App.open_archive_dir ----
    # app.py L1893
    "打不开文件夹": "Can't open the folder",

    # ---- App.delete_history ----
    # app.py L1900
    "确认删除": "Confirm delete",
    # app.py L1901
    "要把这份存档删掉吗？删了就找不回来了。\n\n": "Delete this saved item? Once it's gone, it can't be brought back.\n\n",
    # app.py L1907
    "删除失败": "Delete failed",
    # app.py L1910
    "（已删除，请在左边另选一份）": "(Deleted — please pick another one on the left)",

    # ---- App._build_card ----
    # app.py L2090
    "   （可选）": "   (optional)",
    # app.py L2093
    "看例子": "See examples",
    # app.py L2096
    "待填写": "Not filled in",
    # app.py L2127
    "快速点选（可多选，点了会写进上面的框）": "Quick picks (choose as many as you like — they're written into the box above)",

    # ---- App._build_preview ----
    # app.py L2206
    "自动生成的需求说明": "Your requirement brief",
    # app.py L2208
    "点「复制需求」后粘贴给 AI 就行": "Click “Copy requirement” and paste it to your AI",

    # ---- App._build_footer ----
    # app.py L2233
    "📋 复制需求": "📋 Copy requirement",
    # app.py L2235
    "💾 保存到文件": "💾 Save to file",
    # app.py L2237
    "🧹 清空重填": "🧹 Clear and start over",
    # app.py L2239
    "填写任意内容都会自动生成，随时可以复制。": "Anything you type is generated automatically, ready to copy at any time.",

    # ---- App.toggle_theme ----
    # app.py L2252
    "已记住，请手动重开": "Saved — please reopen manually",
    # app.py L2253
    "主题已改成「%s」。\n\n这个程序没能自动重开，请关掉它再打开一次。": "The theme has been changed to “%s”.\n\nThis program couldn't restart itself, so please close it and open it again.",

    # ---- App.show_lang_dialog ----
    # app.py L2261
    "界面语言": "Language",
    # app.py L2268
    "选择界面语言": "Choose language",
    # app.py L2270
    "切换后界面会重新打开一次。语言会被记住，下次启动仍然生效。": "Switching reopens the interface once. The language is remembered and stays in effect next time you start.",

    # ---- App.show_lang_dialog.apply_lang ----
    # app.py L2282
    "不用改": "No change needed",
    # app.py L2282
    "当前就是这门语言。": "That's already the current language.",
    # app.py L2291
    "界面语言已改成「%s」。\n\n这个程序没能自动重开，请关掉它再打开一次。": "The interface language has been changed to “%s”.\n\nThis program couldn't restart itself, so please close it and open it again.",

    # ---- App.show_lang_dialog ----
    # app.py L2296
    "关闭": "Close",
    # app.py L2297
    "确定并重新打开": "Apply and reopen",

    # ---- App._on_typing ----
    # app.py L2346
    "✔ 已填写": "✔ Filled in",

    # ---- App.refresh ----
    # app.py L2374
    "；还建议补上：": "; you may also want to fill in: ",
    # app.py L2376
    "；必填都填好了，可以复制了 ✔": "; every required box is done — you can copy it now ✔",

    # ---- App.copy_prompt ----
    # app.py L2385
    "已复制 ✔  现在切到 AI 对话框，按 Ctrl+V 粘贴，发送就行了。": "Copied ✔  Now switch to your AI chat, press Ctrl+V to paste, and send it.",
    # app.py L2386
    "复制成功": "Copied",
    # app.py L2387
    "需求说明已经复制到剪贴板。\n\n下一步：打开和 AI 的对话框，按 Ctrl+V 粘贴，然后发送。\n\n（这个窗口可以留着，AI 问你问题时回来改一改再复制一次）": "The requirement brief has been copied to the clipboard.\n\nNext: open your chat with the AI, press Ctrl+V to paste, then send it.\n\n(You can leave this window open — when the AI asks you something, come back, edit it and copy it again)",

    # ---- App.save_prompt ----
    # app.py L2393
    "软件需求": "Software requirement",
    # app.py L2407
    "已保存：": "Saved: ",
    # app.py L2408
    "已保存": "Saved",
    # app.py L2409
    "已保存到：\n\n": "Saved to:\n\n",
    # app.py L2410
    "\n\n可以在「历史记录」这一页里随时找回来、重新载入修改。": "\n\nYou can find it again on the “History” page at any time and reload it to edit.",

    # ---- App.clear_all ----
    # app.py L2413
    "确认清空": "Confirm clear",
    # app.py L2413
    "要把所有填写内容清空，重新开始吗？": "Clear everything you've filled in and start over?",
    # app.py L2425
    "已清空，可以从第 1 格重新填。": "Cleared — you can start again from box 1.",

    # ---- App.show_help ----
    # app.py L2441
    "知道了": "Got it",

    # ---- App.show_scale_dialog ----
    # app.py L2450
    "显示大小 / 分辨率自适应": "Display size / resolution scaling",
    # app.py L2457
    "这个界面当前按 %d%% 显示，字号档位「%s」": "This interface is currently displayed at %d%% with font size step “%s”",
    # app.py L2460
    "屏幕分辨率：": "Screen resolution: ",
    # app.py L2460
    "\nWindows 报告的系统 DPI：": "\nSystem DPI reported by Windows: ",
    # app.py L2461
    "（96 = 100%）   Windows 推荐缩放：": "(96 = 100%)   Windows recommended scaling: ",
    # app.py L2462
    "%（依据：": "% (based on: ",
    # app.py L2462
    "）\n程序当前使用：": ")\nCurrently used by the program: ",
    # app.py L2463
    "%\n\n两个旋钮，作用不同：\n  · 「界面整体大小」改的是整个界面（字和间距一起变）。\n  · 「字号档位」只把字放大，间距基本不动 —— 觉得字偏小就调这个，\n    不用去动 Windows 的缩放（动那个会影响其他所有程序）。\n\n想找回来：选择会记在程序目录的 config.json 里，删掉即可恢复默认。": "%\n\nTwo knobs, two different jobs:\n  · “Overall interface size” changes the whole interface (text and spacing together).\n  · “Font size step” only makes the text bigger and leaves the spacing alone — if the text feels\n    small, turn this one instead of touching Windows scaling (that affects every other program).\n\nTo get back here: your choices are stored in config.json in the program folder; delete it to go back to the defaults.",
    # app.py L2474
    "字号档位：": "Font size step: ",
    # app.py L2479
    "（正文实际 %d 像素）": "(body text is actually %d pixels)",
    # app.py L2484
    "界面整体大小：": "Overall interface size: ",
    # app.py L2491
    "更细的：": "Fine-tune: ",
    # app.py L2498
    "用这个数": "Use this value",
    # app.py L2500
    "建议：界面整体大小保持和 Windows 一致；字偏小就用上面的字号档位。": "Tip: keep “overall interface size” the same as Windows; if the text feels small, use the font size step above.",

    # ---- App.change_font_boost ----
    # app.py L2515
    "当前就是这个字号。": "That's the current font size.",
    # app.py L2523
    "字号档位已改。\n\n这个程序没法自动重开，请关掉它再打开一次，就会生效。": "The font size step has been changed.\n\nThis program can't restart itself, so please close it and open it again for the change to take effect.",

    # ---- App.change_ui_scale ----
    # app.py L2533
    "当前就是这个显示大小。": "That's the current display size.",
    # app.py L2541
    "显示大小已记成 %d%%。\n\n这个程序没法自动重开，请关掉它再打开一次，就会生效。\n（用桌面的快捷方式重新打开即可）": "Display size saved as %d%%.\n\nThis program can't restart itself, so please close it and open it again for the change to take effect.\n(Just open it again from the desktop shortcut.)",

    # ---- App.show_diagnostics ----
    # app.py L2547
    "点击「显示诊断」按钮": "clicked the “Display diagnostics” button",
    # app.py L2552
    "（报告已生成但读不出来）": "(the report was generated but can't be read)",
    # app.py L2554
    "显示诊断": "Display diagnostics",
    # app.py L2559
    "已生成诊断报告：": "Diagnostics report generated: ",
    # app.py L2562
    "如果你要找人帮忙看字太小/字发糊的问题，把这份文件发过去就行。": "If you want someone to help with text that is too small or blurry, just send them this file.",
    # app.py L2576
    "打开报告所在文件夹": "Open the folder containing the report",

    # ---- main ----
    # app.py L2630
    " 实测DPI=": " measured DPI=",
    # app.py L2630
    " 推荐缩放=": " recommended scale=",
    # app.py L2631
    ") 实际使用=": ") in use=",
    # app.py L2631
    " 字体=": " font=",
    # app.py L2632
    " 主题=": " theme=",
    # app.py L2632
    " 屏幕=": " screen=",
    # app.py L2636
    "显示大小 %d%%（Windows 推荐 %d%%；侧栏底部可调大小、可看诊断）": "Display size %d%% (Windows recommends %d%%; use the bottom of the sidebar to change the size or view diagnostics)",
    # app.py L2638
    "；字号「%s」": "; font size “%s”",
    # app.py L2642
    "环境变量 XBSH_UI_DIAGNOSE=1": "environment variable XBSH_UI_DIAGNOSE=1",
    # app.py L2644
    "诊断报告已生成：": "Diagnostics report generated: ",

    # ---- <f-string templates / later additions> ----
    "已填 {n}/{m} 格": "Filled {n}/{m} boxes",
    "共 {n} 份存档": "Total {n} saved items",
    "（读取失败：{e}）": "(read failed: {e})",
    "\n（有 {n} 格当时没填，我会让 AI 直接问你）": "\n({n} boxes were left blank at the time; I'll have the AI ask you directly)",
    "\n（有 {len(missing)} 格当时没填，我会让 AI 直接问你）": "\n({len(missing)} boxes were left blank at the time; I'll have the AI ask you directly)",
    "已填 {filled}/{len(QUESTIONS)} 格": "Filled {filled}/{len(QUESTIONS)} boxes",
    "🌐  界面语言（%s）": "🌐  Language (%s)",
    " 语言=": " language=",
    "）": ")",
    "、": ", ",

    # ---- 先查查页（动手前先看 GitHub 有没有现成的）----
    # app.py L1693-1841  ·  键 = 简体原文
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
    "复制失败，可以直接从下面框里选中复制。": "Copying failed — you can select the text in the box below and copy it yourself.",


    # ---- 由 tools/fill_mobile_i18n.py 补入：手机 App 相关文案 ----
    "为什么要问？\n  · 做电脑软件、手机 App、还是网页，做法完全不同，成品也完全不一样：\n      Windows 是 .exe，Mac 是 .app，Linux 是 .AppImage/.deb，\n      安卓是 .apk，iPhone 是 App Store 里的 App，网页只有一个网址。\n  · 电脑还要分 32 位 / 64 位：32 位程序在 32/64 位系统上都能跑，\n    但 64 位程序在 32 位系统上跑不起来。\n\n程序已经帮你探测过了：\n": "Why does this matter?\n  · A desktop program, a phone app, and a web page are built in completely\n    different ways and produce completely different results:\n      Windows uses .exe, Mac uses .app, Linux uses .AppImage/.deb,\n      Android uses .apk, iPhone apps come from the App Store, and a web page\n      is just a URL.\n  · On desktop, 32-bit vs 64-bit also matters: a 32-bit program runs on both\n    32- and 64-bit systems, but a 64-bit program will NOT run on a 32-bit system.\n\nI have already checked your machine:\n",
    "\n如果你要做**手机 App**，先知道两件事：\n": "\nIf you want a **phone app**, know these two things first:\n",
    "  · 如果只是想「手机上也能用」，网页版通常最省事：不用安装、不用审核、电脑手机都能开。\n": "  · If you only want it to \"also work on a phone\", the web version is usually the least trouble: nothing to install, no review process, and it opens on both desktop and phone.\n",
    "），\n   如果做出来是给别的电脑或手机用，请直接选对方的系统。\n": "),\n   and if the result is meant for someone else's computer or phone, just pick their system instead.\n",
    "\n只有当你做出来是给别人用时，才需要换成对方的系统。\n如果不确定对方的设备，就选第一项，并在最后一格补充说明。": "\nYou only need to switch to someone else's system when the result is for them. If you are not sure what device they use, pick the first option and explain in the last box.\n",


    # ---- 由 tools/fill_target_block_i18n.py 补入：目标平台段新文案 ----
    "目标是手机或网页，跟做我这台电脑上的程序不是一回事，请按上面的平台来做。": "The target is a phone or a web page, which is not the same thing as a program for this computer of mine — please build for the platform above.",
    "交付要求：请给出该平台上可以直接打开使用的成品，并说明在目标设备上第一次打开需要做什么。": "Delivery requirement: provide something that opens and works directly on that platform, and explain what has to be done the first time it is opened on the target device.",


    # ---- 由 tools/fill_lookup_module_i18n.py 补入：github_lookup.py 的文案 ----
    "GitHub 返回错误 %s": "GitHub returned error %s",
    "GitHub 限制了查询频率（每小时 10 次左右），请过一会儿再试": "GitHub is rate-limiting searches (about 10 per hour without login). Please try again later.",
    "⚠️ 但该项目已归档，作者不再维护": "⚠️ But that project is archived — the author no longer maintains it",
    "⚠️ 而且已 %d 个月没更新，要留意是否还适用": "⚠️ And it has not been updated for %d months, so check whether it still fits",
    "❓ 没写清楚开源许可证，商用前要确认": "❓ The open-source licence is not stated clearly — confirm before commercial use",
    "【判断】": "[Verdict] ",
    "找到 %d 个相关项目（按星数排序）：": "Found %d related projects (sorted by stars):",
    "星数都不高（最高 %d），可能没有成熟方案": "None have many stars (highest is %d), so there may be no mature option",
    "最相关的项目有 %d 颗星，有一定使用量": "The most relevant project has %d stars, so it does get some use",
    "最相关的项目有 %d 颗星，说明用的人不少": "The most relevant project has %d stars, so it is fairly widely used",
    "最近还有更新（%s），看来仍在维护": "It was updated recently (%s), so it looks maintained",
    "查询失败：%r": "Search failed: %r",
    "查询词 GitHub 不接受，换个更简单的说法再试": "GitHub rejected that query — try a simpler wording.",
    "查询词是空的": "The search query is empty",
    "没找到现成的，可以自己做": "Nothing suitable exists yet — you can build it yourself",
    "没有找到相关项目。": "No related projects found.",
    "许可证是 %s": "The licence is %s",
    "连不上 GitHub（%s）。可以先用下面的「让 AI 帮你查」": "Cannot reach GitHub (%s). You can use \"ask an AI to search for me\" below instead.",
    "（有 %d 个搜索结果与你的需求明显无关，已排除 —— GitHub 按星数排时经常把无关的高星项目排在最前）": "(%d search results were clearly unrelated to your requirement and have been excluded — GitHub sorts by stars and often puts unrelated high-star projects first)",


    # ---- 由 tools/fill_lookup_module_i18n.py 补入：github_lookup.py 的文案 ----
    "建议先用现成的，别从零做": "Recommendation: use an existing project instead of building from scratch",
    "有可参考的项目，值得先看一眼再决定": "There are projects worth a look — check them before deciding",
    "现成的都不太合适，自己做更省事": "Nothing existing fits well — building it yourself is less trouble",


    # ---- 由 tools/fill_ai_instruction_i18n.py 补入：离线指令全文 ----
    "在动手做之前，请先帮我查一下 GitHub 上有没有现成的软件或插件。": "Before starting to build, please first check whether GitHub already has existing software or a plugin for this.",
    "请搜索这些关键词（可以自己扩展同义词、英文词）：": "Search for these keywords (feel free to add synonyms and English terms):",
    "查完请按下面的格式回答，不要只丢链接：": "After searching, answer in this format — do not just drop links:",
    "1. 有没有现成的？如果有，列出最相关的 3~5 个，每个给出：": "1. Does anything exist already? If so, list the 3-5 most relevant, each with:",
    "   项目名 / 链接 / 星数 / 最近更新时间 / 许可证 / 一句话说明它能不能满足我的需求": "   project name / link / stars / last updated / licence / one line on whether it actually meets my need",
    "2. 这些项目**能不能直接满足我的需求**？缺哪些部分？": "2. Can any of them **actually meet my need as-is**? What is missing?",
    "3. 给我一个明确建议：直接用现成的、拿现成的改、还是自己做？并说明理由。": "3. Give me a clear recommendation: use one as-is, adapt one, or build it myself — and explain why.",
    "4. 如果用现成的，告诉我怎么装、怎么用（我不懂技术，请一步步说）。": "4. If I should use one, tell me how to install and use it (I am not technical — explain step by step).",
    "如果确实没有合适的，再动手做；不要因为搜索麻烦就跳过这一步。": "Only start building if nothing suitable exists — do not skip this step just because searching is a hassle.",


    # ---- 由 tools/fill_ai_instruction_i18n.py 补入：离线指令全文 ----
    "（把你的需求填进上面几格，这里会自动生成查询词）": "(fill in the boxes above and the search terms are generated here)",


    # ---- 由 tools/fill_adaptive_i18n.py 补入：问卷自适应相关文案 ----
    "· 已按你的平台调整": "· adjusted for your platform",
    "12. 希望怎么装到手机上、怎么再打开？（怎么交付）": "12. How should it be installed on the phone and reopened? (delivery)",
    "12. 这个网页放在哪、怎么再打开？（怎么交付）": "12. Where should the web page live and how is it reopened? (delivery)",
    "4. 手机上打算怎么用它？要不要联网？": "4. How will it be used on the phone? Does it need the internet?",
    "4. 这个网页怎么用？要不要联网？": "4. How will the web page be used? Does it need the internet?",
    "一个 apk 安装包，我传到手机点一下装": "An .apk I copy to the phone and tap to install",
    "一个 hap 安装包，我传到手机装": "A .hap package I copy to the phone",
    "不要偷偷上传我的通讯录/相册/位置": "Do not secretly upload my contacts, photos, or location",
    "不要公开我的数据，只能我自己看到": "Do not expose my data — only I should see it",
    "不要收集访问者的个人信息": "Do not collect visitors' personal information",
    "不要有广告和推送": "No ads and no push notifications",
    "不要要求一堆用不上的权限": "Do not ask for a pile of permissions it does not need",
    "主要功能点一遍都正常，不闪退": "Every main feature works once through, with no crashes",
    "例如：在我自己的手机上装好，打开后能完成主要操作，不闪退": "e.g. installed on my own phone, opens and completes the main task without crashing",
    "例如：用手机和电脑各打开一次，主要功能都能用，刷新不丢数据": "e.g. opened once on a phone and once on a desktop, all main features work, a refresh does not lose data",
    "先做一个最简单的版本给我看看": "Build the simplest possible version first so I can look at it",
    "先做出来能在我自己手机上试（需要有苹果开发者账号）": "First make it runnable on my own phone (needs an Apple Developer account)",
    "其实用网页版也行（不用苹果账号）": "Actually a web version is fine too (no Apple account needed)",
    "别人打开也能用": "Others can open it and use it",
    "发给别人也能装能开": "Sending it to someone else also installs and opens",
    "只给内部的人用，不想放到公网": "Internal use only, not on the public internet",
    "只要能在我自己电脑上跑就行": "Running on my own computer is enough",
    "在我自己的手机上能装能开": "Installs and opens on my own phone",
    "在手机浏览器里打开网址就行": "Just open a URL in the phone browser",
    "微信里能打开/分享（小程序或链接）": "Openable/shareable inside WeChat (mini program or link)",
    "我自己装就行，不用上架": "I will install it myself, no store needed",
    "手机上装 App 和用浏览器打开，做法和门槛差别很大。": "Installing an app and opening a web page on a phone are very different.",
    "手机和电脑打开都正常": "Opens correctly on both phone and computer",
    "换台设备/换个时间打开，数据还在": "Open it on another device or later, and the data is still there",
    "放到我自己电脑上，只有我能访问": "Host it on my own computer, only I can access it",
    "电脑和手机都要能打开": "Must open on both computers and phones",
    "给我一个网址，我用浏览器打开": "Give me a URL and I will open it in a browser",
    "装成 App，点桌面图标打开": "Install it as an app and tap the icon on the home screen",
    "要上架 App Store 给别人下载": "Publish to the App Store for others to download",
    "要放到服务器上给别人访问": "Host it on a server for others to access",
    "要放到网上，别人能直接访问": "Host it online so others can access it directly",
    "要给不特定的人下载用": "Should be downloadable by anyone",
    "要能上架应用商店（安卓）": "Should be publishable to an app store (Android)",
    "需要开开发者模式才能装，我可以接受": "Needs developer mode enabled to install — that is fine",


    # ---- 由 tools/fill_adaptive_i18n.py 补入：问卷自适应相关文案 ----
    "3. 手机 App 做给哪种手机用？": "3. Which kind of phone is the app for?",
    "3. 这个网页给谁用、在什么设备上打开？": "3. Who is the web page for, and on what devices?",
    "例如：安卓手机 App（现在的手机基本都是安卓）": "e.g. an Android app (almost every current phone is Android)",
    "例如：网页，电脑和手机都能打开": "e.g. a web page that opens on both a computer and a phone",
    "网页本身什么设备都能开，主要看给谁用、要不要放到网上。": "A web page opens on any device; what matters is who it is for and whether it goes online.",
    "选错手机类型会导致装不上。安卓、苹果、鸿蒙是完全不同的做法。": "Picking the wrong phone type means it will not install. Android, iPhone, and HarmonyOS are built in completely different ways.",


    # ---- 由 tools/fill_adaptive_i18n.py 补入：问卷自适应相关文案 ----
    "存档保存在哪": "Where is my data?",
    "📁  存档保存在哪": "📁  Where is my data?",
    "存档和设置保存在程序旁边：": "Saved files and settings are stored next to the program: ",
    "存档和设置保存在：": "Saved files and settings are stored in: ",
    "（程序装在只读位置，所以放到你的用户目录）": " (the program folder is read-only, so they go to your user folder)",
    "打开这个文件夹": "Open this folder",


    # ---- 由 tools/fill_kind_i18n.py 补入：类型分支（插件/脚本）文案 ----
    "1. 你要做的是哪一种？": "1. Which kind of thing are you building?",
    "程序、插件、脚本是三件不同的事，后面的问题会不一样。不确定就选第一项。": "A program, a plugin, and a script are three different things, and the questions afterwards differ. Pick the first one if unsure.",
    "例如：电脑上的程序（能双击打开的那种）": "e.g. a program for your computer (the kind you double-click)",
    "电脑上的程序（能双击打开的那种）": "A program for my computer (the kind you double-click)",
    "手机 App": "A phone app",
    "网页": "A web page",
    "某个软件的插件/扩展（挂在别的软件里用）": "A plugin/extension for some other software (lives inside it)",
    "自动化小脚本（跑一下就完事，没有界面）": "A small automation script (runs and finishes, no interface)",
    "不确定，你帮我判断": "Not sure — work it out for me",
    "你想要做一个什么样的东西？": "What do you want to build?",
    "你想做一个什么样的东西？": "What do you want to build?",
    "问题已按你选的类型调整过了。": "The questions have been adjusted for the kind you picked.",
    "3. 挂在哪个软件里？": "3. Which software does it plug into?",
    "不同软件的插件写法完全不同。写清楚名字和版本，别只说「一个编辑器」。": "Plugins for different software are written completely differently. Give the exact name and version — not just \"an editor\".",
    "例如：DeepSeek Harness（DSH）桌面版，我在设置里装插件": "e.g. DeepSeek Harness (DSH) desktop app, installed from its settings",
    "浏览器（Chrome / Edge 扩展）": "A browser (Chrome / Edge extension)",
    "VS Code / Cursor 这类编辑器": "An editor like VS Code / Cursor",
    "某个 AI 工具 / 聊天软件": "Some AI tool / chat app",
    "Office / WPS（Word、Excel 里用）": "Office / WPS (used inside Word or Excel)",
    "别的软件（我在最后一格说名字）": "Something else (I will name it in the last box)",
    "4. 怎么触发它？它在你操作时什么时候动？": "4. How is it triggered? When does it act while you work?",
    "插件和程序最大的区别：插件是「挂在别人的流程里」被调用的。说清楚是谁在什么时候叫它。": "The big difference from a program: a plugin runs inside someone else's flow. Say who calls it and when.",
    "例如：我在对话框里打「检查需求」它就分析我写的这段话，或者每次我发消息前它自己先看一眼": "e.g. I type \"check requirement\" in the chat box and it analyses that text, or it takes a look before every message I send",
    "我打一个命令 / 点一个按钮才触发": "Only when I run a command or click a button",
    "每次我做某个动作它自动插一脚": "It steps in automatically whenever I do something",
    "它自己在后台定时跑": "It runs on a timer in the background",
    "要能加到右键菜单里": "It should appear in the right-click menu",
    "5. 要不要跟被挂的那个软件交换信息？": "5. Does it need to exchange information with that software?",
    "这是插件最容易卡住的地方。如果要读它当前的内容、或者把结果塞回去，就得用它提供的接口 —— 你得告诉我它有哪些接口（或者让我去查文档）。": "This is where plugins get stuck most often. Reading its current content or putting results back requires its API — tell me which APIs it has (or let me check the docs).",
    "例如：要读我现在对话框里打的内容，把检查结果直接插回输入框；没有现成接口的话，告诉我替代做法": "e.g. read what I have typed in the chat box and put the result straight back into the input; if there is no API, tell me an alternative",
    "要读它当前的内容（比如我正在编辑的文字）": "It must read its current content (e.g. the text I am editing)",
    "要把结果写回去 / 戳一个提示出来": "It must write results back / show a notice",
    "只读我主动给它的东西就行，不用接口": "Only what I hand it is enough; no API needed",
    "要能调用另一个 AI 帮我分析": "It should call another AI to analyse things",
    "不确定它有没有接口，你帮我查": "Not sure whether it has an API — please check for me",
    "6. 需要设置界面吗？（可选）": "6. Do you need a settings screen? (optional)",
    "要不要让我能改一些设置（开关、阈值、语言）？不放设置页也能用，但有些东西最好让人能调。": "Should I be able to change settings (toggles, thresholds, language)? It works without one, but some things are better left adjustable.",
    "例如：要能开关、能切换中文/英文、能调严格程度": "e.g. an on/off switch, Chinese/English, and how strict it is",
    "要，能改开关和参数": "Yes — toggles and parameters",
    "要，最好能切换语言": "Yes — ideally a language switch",
    "不用，用法固定就行": "No — a fixed way of working is fine",
    "7. 打算怎么装上、给谁用？": "7. How will it be installed, and who is it for?",
    "自己本地装、发给同事、还是上架到插件市场，做法差别很大。": "Installing it locally, sending it to colleagues, or publishing to a plugin marketplace are very different jobs.",
    "例如：先在我自己机器上装好能用，之后可能发给同事": "e.g. working on my own machine first, maybe sent to colleagues later",
    "只在我自己机器上装好能用": "Just working on my own machine",
    "要能打包发给同事，他们照说明也能装": "Packaged so colleagues can install it from instructions",
    "要上架到官方的插件市场 / 商店": "Published to the official plugin marketplace / store",
    "要能在多台机器上快速装好": "Quick to install on several machines",
    "4. 你打算怎么运行它？": "4. How do you plan to run it?",
    "脚本不打包成 exe，一般是双击某个文件或者定时跑。": "Scripts are not packaged into an .exe — usually you double-click a file or run them on a schedule.",
    "例如：我双击一个 .bat 文件它就处理；或者每天早上自动跑一次": "e.g. I double-click a .bat file and it processes; or it runs every morning",
    "我双击一个文件它就处理": "I double-click a file and it processes",
    "我要在命令行里输入一行命令跑": "I run one command in a terminal",
    "每天/每周自动定时跑": "Runs automatically daily / weekly",
    "别人也能在他电脑上跑": "Others can run it on their computers too",
    "不确定，你帮我选最省事的": "Not sure — pick the least trouble for me",


    # ---- 由 tools/migrate_numbered_keys.py 补入：不带题号的键 ----
    # 题号会随「做什么类型」变，所以键不能写死编号；
    # i18n.t() 会剥掉编号查这里的键，再把原编号补回译文。
    "你想做一个什么样的软件？": "1. What kind of software do you want to make?",
    "给谁用？一共几个人用？": "2. Who will use it? How many people in total?",
    "这个软件要跑在什么系统上？32 位还是 64 位？": "3. What system should this software run on? 32-bit or 64-bit?",
    "在哪里打开它？要不要联网？": "4. Where will you open it? Does it need the internet?",
    "它帮你解决什么麻烦？（现在你是怎么手动做的）": "5. What hassle does it save you? (How do you do it by hand today?)",
    "你希望怎么操作它？（从打开到结束，一步步说）": "6. How do you want to operate it? (Step by step, from opening to finishing)",
    "输入从哪来？（数据/文件从哪来，长什么样）": "7. Where does the input come from? (Where the data/files come from and what they look like)",
    "输出/结果要长什么样？": "8. What should the output/result look like?",
    "怎么算做好了？（成功的标准）": "9. How do we know it's done? (What counts as success)",
    "有什么不能做 / 必须遵守的规矩？": "10. What must it not do / what rules must it follow?",
    "有没有想模仿的参照物？（可选）": "11. Is there anything you want to copy? (optional)",
    "你希望怎么用它、怎么再打开？（怎么交付给你）": "12. How do you want to use it and open it again? (How should it be delivered to you)",
    "还想补充什么？（可选，想到什么写什么）": "13. Anything else to add? (optional — write down whatever comes to mind)",
    "如果下面有哪里没写清楚、或者你觉得会影响结果，请先问我（一次问 2~5 个，用大白话问，不要用技术名词考我），问清楚再动手。": "1. If anything below isn't clear, or you think it will affect the result, ask me first (2~5 questions at a time, in plain language — don't test me with technical terms), and only start once it's clear.",
    "技术方案（用什么语言、什么工具、怎么打包）你自己决定；如果有影响我使用的取舍，告诉我两个选项各自的好处就行。": "2. The technical choices (which language, which tools, how to package it) are up to you; if there's a trade-off that affects how I use it, just tell me the benefit of each option.",
    "请你自己动手做完并自己测试通过，最后给我一个能直接双击打开、或能直接打开的成品，并告诉我放在哪个路径、怎么再次打开。": "3. Please do the work yourself and test it yourself until it passes, then give me something I can open by double-clicking (or open directly), and tell me where it is and how to open it again.",
    "交付时请一并告诉我：怎么用、怎么备份数据、有哪些你没做到或做不到的地方。": "4. When you deliver it, also tell me: how to use it, how to back up the data, and anything you didn't do or couldn't do.",
    "不要只给我代码和说明书让我自己想办法运行，我看不懂。": "5. Don't just give me code and a manual and leave me to work out how to run it — I won't understand it.",
    "有没有现成的？如果有，列出最相关的 3~5 个，每个给出：": "1. Does anything exist already? If so, list the 3-5 most relevant, each with:",
    "这些项目**能不能直接满足我的需求**？缺哪些部分？": "2. Can any of them **actually meet my need as-is**? What is missing?",
    "给我一个明确建议：直接用现成的、拿现成的改、还是自己做？并说明理由。": "3. Give me a clear recommendation: use one as-is, adapt one, or build it myself — and explain why.",
    "如果用现成的，告诉我怎么装、怎么用（我不懂技术，请一步步说）。": "4. If I should use one, tell me how to install and use it (I am not technical — explain step by step).",
    "希望怎么装到手机上、怎么再打开？（怎么交付）": "12. How should it be installed on the phone and reopened? (delivery)",
    "这个网页放在哪、怎么再打开？（怎么交付）": "12. Where should the web page live and how is it reopened? (delivery)",
    "手机上打算怎么用它？要不要联网？": "4. How will it be used on the phone? Does it need the internet?",
    "这个网页怎么用？要不要联网？": "4. How will the web page be used? Does it need the internet?",
    "手机 App 做给哪种手机用？": "3. Which kind of phone is the app for?",
    "这个网页给谁用、在什么设备上打开？": "3. Who is the web page for, and on what devices?",
    "你要做的是哪一种？": "1. Which kind of thing are you building?",
    "挂在哪个软件里？": "3. Which software does it plug into?",
    "怎么触发它？它在你操作时什么时候动？": "4. How is it triggered? When does it act while you work?",
    "要不要跟被挂的那个软件交换信息？": "5. Does it need to exchange information with that software?",
    "需要设置界面吗？（可选）": "6. Do you need a settings screen? (optional)",
    "打算怎么装上、给谁用？": "7. How will it be installed, and who is it for?",
    "你打算怎么运行它？": "4. How do you plan to run it?",


    # ---- 类型分支的界面提示 ----
    "· 已按你的类型调整": "· adjusted for the kind you picked",
}
