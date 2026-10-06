# -*- coding: utf-8 -*-
"""验证需求说明（build_prompt）真的按语言翻译了。

这是「端到端」的一层：不检查有没有包 t()，而是**真的生成一遍**，
看输出里还有没有残留的简体专有字。

为什么要单独做：上一版整段 build_prompt 都没走 t()，
界面是繁体、生成的需求说明却是简体 —— 界面截图能看出来，
但功能自检完全测不到。这个脚本把「生成的正文是否本地化」变成可验证的事。

用法: python tools/selftest_i18n_output.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import i18n  # noqa: E402
import app  # noqa: E402

# 只在简体里出现、繁体/英文里不该出现的字（用于判断「还有简体残留」）
SIMPLIFIED_ONLY = "软体软件个为对时发开关单录规则报总验账资讯数电"
# 更可靠的做法：比对「繁体专有字」是否出现
TRAD_ONLY = "個為對時發開關單錄規則報總驗帳資訊數電"
EN_MARKERS = ["requirement", "software", "build", "please"]


def make_answers(lang="zh-CN"):
    """造一份答案。

    ★ 用户自己填的内容要按语言给：用户数据不会被翻译（也不该被翻译），
      所以用简体数据去测繁体输出，会把"用户写的简体"误判成"漏翻"。
      这正是我第一次跑这个测试时的误报原因。
    """
    a = {q["key"]: "" for q in app.QUESTIONS}
    user_text = {
        "zh-CN": ("一个帮我把三份 Excel 合并的小工具", "只有我自己用",
                  "现在手动复制粘贴，约 40 分钟", "总数和财务一致", "数据不能上传"),
        "zh-TW": ("一個幫我把三份 Excel 合併的小工具", "只有我自己用",
                  "現在手動複製貼上，約 40 分鐘", "總數和財務一致", "資料不能上傳"),
        "en": ("a small tool to merge three Excel files", "just me",
               "I copy and paste by hand, about 40 minutes", "the totals match finance",
               "the data must not be uploaded"),
    }[lang]
    a["what"], a["who"], a["pain"], a["done"], a["limit"] = user_text
    qsys = app.QUESTIONS[[q["key"] for q in app.QUESTIONS].index("system")]
    a["system"] = app._qopts(qsys)[0]
    return a


pass_n = fail_n = 0


def check(name, fn):
    global pass_n, fail_n
    try:
        fn()
        pass_n += 1
        print("  OK   %s" % name)
    except AssertionError as e:
        fail_n += 1
        print("  FAIL %s\n       %s" % (name, e))
    except Exception as e:  # noqa: BLE001
        fail_n += 1
        print("  FAIL %s\n       %r" % (name, e))


print("=" * 62)
print("生成的需求说明是否按语言本地化")
print("=" * 62)

texts = {}
for lang in i18n.LANGS:
    i18n.set_lang(lang)
    texts[lang] = app.build_prompt(make_answers(lang))

for lang, text in texts.items():
    print("  %-6s 生成 %d 字、%d 行" % (lang, len(text), len(text.splitlines())))


def t_cn_has_cn():
    text = texts["zh-CN"]
    assert "我的需求" in text, "简中应含「我的需求」"
    assert "目标平台（重要）" in text, "简中应含目标平台段"


check("简中：含预期中文段", t_cn_has_cn)


def t_tw_translated():
    text = texts["zh-TW"]
    # 简繁差异字：这些字在繁体里写法不同，出现即说明没翻到。
    # （比"猜哪个简体词会出现"可靠 —— 上一版我写了句恒为假的断言，误报了一次）
    simp_only = "软个为对时发开关单录规则报总验账资讯数电体图级击约"
    hit = [c for c in simp_only if c in text]
    assert not hit, "繁体输出里出现简体专用字: %s" % "".join(hit)
    # 繁体用字应出现
    assert any(c in text for c in "軟個為對時發開關單錄規則報總驗帳資訊數電體圖級擊約"), \
        "繁体输出里找不到繁体用字，可能整段没翻译"


check("繁中：无简体残留、有繁体用字", t_tw_translated)


def t_en_translated():
    text = texts["en"]
    for bad in ["我的需求", "软件", "需求", "目标平台"]:
        assert bad not in text, "英文输出里出现了中文 %r" % bad
    low = text.lower()
    assert any(m in low for m in EN_MARKERS), "英文输出不像英文"
    # ★ 题目标题也应是英文。不写死某一句话（文案会随「做什么类型」和
    #   「跑在什么平台」变），改成**实时取当前题集的英文标题**再比对 ——
    #   这样换文案时测试不会假失败，但真漏翻一定会被抓住。
    import re as _re
    import app as _app
    import i18n as _i18n
    _i18n.set_lang("en")
    try:
        for q in _app.App.PAGES:      # 顺带确认页面名也是英文
            tt = _i18n.t(q)
            assert not _re.search(r"[\u4e00-\u9fff]", tt), \
                "英文下页面名仍有中文: %r" % tt
        for q in _app.questions_for_current():
            tt = _i18n.t(q["title"])
            assert not _re.search(r"[\u4e00-\u9fff]", tt), \
                "英文下题目标题仍有中文: %r" % tt
    finally:
        _i18n.set_lang("zh-CN")


check("英文：无中文残留、内容为英文", t_en_translated)


def t_platform_block_localized():
    for lang, marker in (("zh-CN", "目标平台（重要）"), ("zh-TW", "目標平台（重要）"),
                         ("en", "Target platform")):
        text = texts[lang]
        assert marker in text, "%s 的目标平台段标题不对（找不到 %r）" % (lang, marker)


check("目标平台段三语标题各自正确", t_platform_block_localized)


def t_system_answer_expanded():
    # 「跟我电脑一样」必须被展开成明确的系统与位数
    for lang in i18n.LANGS:
        det = app.current_platform()
        assert det["os_label"] in texts[lang], "%s 里没写本机系统" % lang
        assert "32" in texts[lang] or "64" in texts[lang], "%s 里没写位数" % lang


check("三语都展开了本机系统与位数", t_system_answer_expanded)


def t_titles_translated():
    i18n.set_lang("en")
    a = app.build_prompt(make_answers("en"))
    for q in app.QUESTIONS:
        src_title = q["title"]
        assert src_title not in a, "英文输出里还有简体题目标题: %s" % src_title


check("英文：所有题目标题都翻译了", t_titles_translated)

print()
print("=" * 62)
print("通过 %d 项，失败 %d 项" % (pass_n, fail_n))
print("=== 全部通过 ===" if fail_n == 0 else "=== 有失败项 ===")
sys.exit(0 if fail_n == 0 else 1)
