# -*- coding: utf-8 -*-
"""系统与位数功能的针对性验证。

不启动界面：直接 import app，检查问卷选项、答案解析、需求说明生成。
用法: python tools/selftest_platform.py
"""

import os
# ★ 锁定界面语言（XBSH_LANG_LOCKED）：这些检查/自检脚本的输出与断言都基于简体中文，
#   而 i18n 会按系统区域自动探测语言 —— 在英文机器 / CI 上会探测成英文，
#   断言就全挂（GitHub runner 上真踩过：selftest_platform 11 项失败）。
#   ★ 用 = 不用 setdefault：环境里已有 XBSH_LANG 时 setdefault 不覆盖，锁会失效。
#   插在第一个模块级 import 之前，保证任何依赖 i18n 的 import 都在它之后。
os.environ["XBSH_LANG"] = "zh-CN"

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import platform_info  # noqa: E402
import app  # noqa: E402

pass_n = 0
fail_n = 0
failures = []


def check(name, fn):
    global pass_n, fail_n
    try:
        fn()
        pass_n += 1
        print("  OK   %s" % name)
    except AssertionError as e:
        fail_n += 1
        failures.append((name, str(e)))
        print("  FAIL %s" % name)
        print("       %s" % e)
    except Exception as e:  # noqa: BLE001
        fail_n += 1
        failures.append((name, repr(e)))
        print("  FAIL %s" % name)
        print("       %r" % (e,))


print("=" * 64)
print("平台探测")
print("=" * 64)

det = platform_info.detect_platform()


def t_detect():
    assert det["os"] in ("win", "mac", "linux"), det
    assert det["bits"] in (32, 64), det
    assert det["os_label"] in ("Windows", "macOS", "Linux"), det
    assert isinstance(det["certain"], bool), det


check("detect_platform 结构合法", t_detect)


def t_target():
    tgt = platform_info.platform_to_target(det)
    assert tgt in platform_info.TARGETS, tgt
    assert tgt != "auto", "本机应能推出具体目标，实际 " + tgt
    # 本机是 Windows x64 时应推出 windows-64
    if det["os"] == "win" and det["arch"] == "x64":
        assert tgt == "windows-64", tgt


check("platform_to_target 推出具体目标", t_target)


def t_labels():
    for key in platform_info.TARGETS:
        for loc in ("zh-CN", "zh-TW", "en"):
            s = platform_info.describe_target(key, loc)
            assert isinstance(s, str) and len(s) > 1, (key, loc, s)
            assert s != key, "应是人话而不是原值: %s" % key


check("每个目标三语都有人话标签", t_labels)


def t_targets_have_all_os():
    joined = " ".join(platform_info.TARGETS)
    for want in ("windows-32", "windows-64", "windows-arm64",
                 "macos-64", "macos-arm64", "linux-64", "linux-arm64", "web"):
        assert want in platform_info.TARGETS, "缺少 " + want


check("Windows/macOS/Linux × 32/64 位都在选项里", t_targets_have_all_os)


def t_targets_have_mobile():
    """手机 App 必须在选项里 —— 不是所有人都是给自己电脑做的"""
    joined = " ".join(platform_info.TARGETS)
    for want in ("android-arm64", "android-32", "ios", "harmony"):
        assert want in platform_info.TARGETS, "缺少手机目标 " + want
    # 帮助里必须讲清楚手机的两个现实门槛
    for lang in ("zh-CN", "zh-TW", "en"):
        android = platform_info.DELIVERABLE_HINT["android"][lang]
        ios = platform_info.DELIVERABLE_HINT["ios"][lang]
        assert "apk" in android.lower() or ".apk" in android, \
            "%s 的安卓交付说明没提 apk: %s" % (lang, android)
        assert "99" in ios or "developer" in ios.lower() or "開發者" in ios or "开发者" in ios, \
            "%s 的 iOS 说明没提开发者账号门槛: %s" % (lang, ios)


check("手机目标（安卓/iOS/鸿蒙）齐全，且交付门槛写清楚", t_targets_have_mobile)

print()


def t_sentence():
    for loc in ("zh-CN", "zh-TW", "en"):
        s = platform_info.default_target_sentence(det, loc)
        assert det["os_label"] in s, (loc, s)
        assert str(det["bits"]) in s, (loc, s)
    for loc in ("zh-CN", "zh-TW", "en"):
        c = platform_info.compat_note(loc)
        assert "32" in c and "64" in c, (loc, c)


check("三语默认句与兼容提醒含系统名与位数", t_sentence)

print()
print("=" * 64)
print("问卷")
print("=" * 64)

q_system = None
for q in app.QUESTIONS:
    if q["key"] == "system":
        q_system = q


def t_has_question():
    assert q_system is not None, "没有 system 问题"
    assert "32" in q_system["title"] and "64" in q_system["title"], q_system["title"]


check("问卷里有「系统与位数」问题", t_has_question)


def t_options():
    opts = app._qopts(q_system)
    assert isinstance(opts, list) and len(opts) >= 5, opts
    assert opts[0].startswith("跟我电脑一样"), "第一项应是本机默认: %s" % opts[0]
    # 三个系统和两种位数都要能选到
    joined = " ".join(opts)
    for want in ("Windows", "macOS", "Linux", "32 位", "64 位"):
        assert want in joined, "选项里缺少 %s" % want
    assert any("ARM" in o or "Apple" in o for o in opts), "缺少 Apple 芯片/ARM 选项"


check("选项覆盖三系统与两种位数，首项为本机", t_options)


def t_mobile_options_in_question():
    """系统那一题的实际选项里要能看到手机 App（不只是电脑软件）"""
    opts = app._qopts(q_system)
    joined = " ".join(opts)
    for want in ("安卓", "iPhone", "鸿蒙"):
        assert want in joined, "系统题的选项里缺少 %s:\n%s" % (want, "\n".join(opts))
    assert "网页" in joined, "缺少网页选项"
    for want in ("Windows", "macOS", "Linux"):
        assert want in joined, "缺少 %s 选项" % want
    # 安卓要有位数之分（旧手机是 32 位）
    assert any("32" in o for o in opts), "安卓应该区分 32 位老手机:\n%s" % "\n".join(opts)


check("系统题选项覆盖 电脑 + 手机 + 网页", t_mobile_options_in_question)


def t_example():
    ex = app._qval(q_system, "example")
    assert ex and ex.startswith("例如："), ex
    assert det["os_label"] in ex, ex


check("示例按本机生成", t_example)


def t_help():
    h = app._qval(q_system, "help")
    assert det["os_label"] in h, "帮助里应写本机系统"
    assert "32 位" in h and "64 位" in h, "帮助里应讲位数兼容"
    assert ".exe" in h and ".app" in h, "帮助里应讲清各系统的成品形式"


check("帮助里含本机探测结果与兼容提醒", t_help)


def t_numbering():
    """题号必须按**当前题集**连续。

    ★ 题号不再写在基础标题里：它会随「做什么类型」变
      （插件集里「给谁用」是第 6 题，程序集里是第 3 题），
      编号在 questionnaire.questions_for() 里按位置统一加。
      所以这里检查的是**组装后**的结果，三语三类型都要对。
    """
    import re as _re
    for loc in app.i18n.LANGS:
        for kind in ("program", "plugin", "script"):
            qs = app.questions_for_current.__globals__["questionnaire"].questions_for(
                app.QUESTIONS, kind, loc)
            nums = []
            for q in qs:
                m = _re.match(r"^(\d+)[.、]", q["title"])
                assert m, "%s/%s 有题目没编号: %r" % (loc, kind, q["title"])
                nums.append(int(m.group(1)))
            assert nums == list(range(1, len(nums) + 1)), \
                "%s/%s 编号不连续: %s" % (loc, kind, nums)
    # 基础表的标题不该自带编号（否则组装时会双重编号）
    for q in app.QUESTIONS:
        assert not _re.match(r"^\d+[.、]", q["title"]), \
            "基础标题不该写死编号: %r" % q["title"]


check("题号按当前题集连续（三语三类型）", t_numbering)


def t_unique_keys():
    keys = [q["key"] for q in app.QUESTIONS]
    assert len(keys) == len(set(keys)), "key 重复: %s" % keys


check("问题 key 不重复", t_unique_keys)

print()
print("=" * 64)
print("答案解析")
print("=" * 64)


def t_resolve_own():
    opt = app._qopts(q_system)[0]
    target, note = app.resolve_system_answer(opt)
    assert target == app.current_target(), (target, app.current_target())
    assert note and det["os_label"] in note, note


check("选「跟我电脑一样」展开成明确系统", t_resolve_own)


def t_resolve_unsure():
    opt = [o for o in app._qopts(q_system) if o.startswith(app.t("不确定"))][0]
    target, note = app.resolve_system_answer(opt)
    assert target == app.current_target(), target
    assert note, "应给出探测说明"


check("选「不确定」也落到本机默认", t_resolve_unsure)


def t_resolve_explicit():
    # 找一个不是本机的选项，验证能反查
    for label in platform_info.TARGET_LABELS.values():
        pass
    for key in ("windows-32", "macos-arm64", "linux-64"):
        label = platform_info.describe_target(key)
        if label in app._qopts(q_system):
            target, note = app.resolve_system_answer(label)
            assert target == key, (label, target, key)
            assert "用户指定" in note, note
            return
    raise AssertionError("找不到可反查的选项")


check("选具体系统能反查回目标值", t_resolve_explicit)


def t_resolve_empty():
    target, note = app.resolve_system_answer("")
    assert target is None and note == "", (target, note)
    target, note = app.resolve_system_answer("我随便写的一句话")
    assert target is None, target
    assert "我随便写的一句话" in note, note


check("空值与自由文本不崩", t_resolve_empty)

print()
print("=" * 64)
print("需求说明生成")
print("=" * 64)


def t_prompt_has_block():
    answers = {q["key"]: "" for q in app.QUESTIONS}
    answers["system"] = app._qopts(q_system)[0]
    answers["what"] = "一个帮我把三份 Excel 合并的小工具"
    text = app.build_prompt(answers)
    assert "目标平台（重要）" in text, "需求说明里应有目标平台段"
    assert det["os_label"] in text, "应写本机系统"
    assert "32 位" in text and "64 位" in text, "应讲位数"
    # 选了「跟我电脑一样」应展开，不能只留一句话
    assert platform_info.describe_target(app.current_target()) in text, "应展开成明确平台"


check("需求说明含目标平台段并展开默认值", t_prompt_has_block)


def t_prompt_explicit():
    answers = {q["key"]: "" for q in app.QUESTIONS}
    label = platform_info.describe_target("linux-64")
    answers["system"] = label
    text = app.build_prompt(answers)
    assert "Linux 64" in text, "应写用户选的 Linux"


check("选 Linux 时需求说明写 Linux", t_prompt_explicit)


def t_prompt_empty():
    answers = {q["key"]: "" for q in app.QUESTIONS}
    text = app.build_prompt(answers)
    # 没填也要给出默认值 + 提醒，而不是留空
    assert "目标平台（重要）" in text, "没填时也应给目标平台段"
    assert det["os_label"] in text


check("完全没填时仍给出默认目标平台", t_prompt_empty)


def t_mobile_target_no_desktop_talk():
    """★ 回归：选了手机时，需求说明里**不能再讲本机电脑**。

    真 bug：目标平台段原本写死「你的电脑是 Windows 64 位 …」
    「Windows 上可能要解除锁定」—— 选了安卓之后还在讲 Windows，
    对手机用户完全是错的。现在按所选平台给说明。
    """
    for tgt, must, forbid in (
        ("android-arm64", ("apk", "安卓"), (det["os_label"],)),
        ("ios", ("开发者账号", "iPhone"), ("32 位程序",)),
        ("harmony", ("鸿蒙",), ()),
        ("web", ("网页",), ()),
    ):
        answers = {q["key"]: "" for q in app.QUESTIONS}
        answers["system"] = platform_info.describe_target(tgt, "zh-CN")
        text = app.build_prompt(answers)
        for m in must:
            assert m in text, "选了 %s 的说明里应提到 %r" % (tgt, m)
        for f in forbid:
            assert f not in text, "选了 %s 的说明里不该出现 %r" % (tgt, f)


check("选手机/网页时不再套用本机电脑的说法", t_mobile_target_no_desktop_talk)


def t_desktop_target_keeps_machine_info():
    """反面对照：选桌面时仍要写本机信息（不然用户不知道默认值从哪来）"""
    answers = {q["key"]: "" for q in app.QUESTIONS}
    answers["system"] = platform_info.describe_target(app.current_target(), "zh-CN")
    text = app.build_prompt(answers)
    assert det["os_label"] in text, "桌面目标应写本机系统作为默认依据"
    assert "32 位程序在 32/64 位系统上" in text, "桌面目标应讲位数兼容"


check("选桌面时仍写出本机默认依据", t_desktop_target_keeps_machine_info)


def t_prompt_free_text():
    answers = {q["key"]: "" for q in app.QUESTIONS}
    answers["system"] = "要能在我们车间那台老电脑上跑"
    text = app.build_prompt(answers)
    assert "我们车间那台老电脑" in text, "用户自由描述应原样带出"


check("自由文本原样带出", t_prompt_free_text)


def t_prompt_other_questions_intact():
    answers = {q["key"]: "" for q in app.QUESTIONS}
    answers["what"] = "测试用"
    answers["pain"] = "手动做很慢"
    text = app.build_prompt(answers)
    # ★ 比对**当前生效题集**的标题正文（题号会随「做什么类型」变，
    #   生成说明里写的是不带编号的正文）。
    import re as _re
    for q in app.questions_for_current(answers):
        body = _re.sub(r"^\d+[.、]\s*", "", str(q["title"]))
        assert body in text, "需求说明里缺少问题标题: " + body
    assert "测试用" in text and "手动做很慢" in text


check("其余问题的内容仍正常输出", t_prompt_other_questions_intact)

print()
print("=" * 64)
print("打包注意事项")
print("=" * 64)


def t_platform_info_importable():
    # 打包时静态可分析：app.py 顶层必须有直接的 import 语句
    src = io.open(os.path.join(ROOT, "src", "app.py"), encoding="utf-8").read()
    assert "\nimport platform_info" in src, "缺少顶层直接的 import platform_info（PyInstaller 分析不到）"
    assert "from . import platform_info" not in src, "相对导入在直接运行时会失败"


check("platform_info 用可直接静态分析的 import", t_platform_info_importable)

print()
print("=" * 64)
print("通过 %d 项，失败 %d 项" % (pass_n, fail_n))
if failures:
    print("\n失败详情：")
    for n, m in failures:
        print("  %s\n    %s" % (n, m))
print("=== 全部通过 ===" if fail_n == 0 else "=== 有失败项 ===")
sys.exit(0 if fail_n == 0 else 1)
