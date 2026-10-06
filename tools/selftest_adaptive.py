# -*- coding: utf-8 -*-
"""问卷自适应自检：第 3 题选不同平台时，后面的问题必须跟着变。

覆盖三件事：
  1. 规则层：同一个问题在不同平台族下，标题/选项确实不同（questionnaire.py）
  2. 界面层：真的点第 3 题的选项后，后面的题目会重建并换成对应选项
  3. 不丢数据：重建表单时已填内容、已勾选项要保住

**注意**：模拟点击时必须先把勾选框变量设为 True 再调 _toggle，
否则 _toggle 会按「全部未选中」处理，把选项清掉 ——
这是本测试第一版自身的 bug（不是产品的），踩过一次所以写在这里。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import tkinter as tk  # noqa: E402

import app as A  # noqa: E402
import questionnaire as Q  # noqa: E402

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
        # 非断言类异常（KeyError/TclError 之类）光看信息不够，
        # 但不必一直打全栈 —— 设 XBSH_TRACE=1 才打。
        if os.environ.get("XBSH_TRACE"):
            import traceback as _tb
            _tb.print_exc()


def q_of(key):
    return [x for x in A.QUESTIONS if x["key"] == key][0]


print("=" * 66)
print("规则层：同一题在不同平台下是否不同")
print("=" * 66)

A.init_lang()
A.apply_dpi_awareness()
root = tk.Tk()
A.init_ui_scale(root)
A.init_theme()
gui = A.App(root)
root.update_idletasks()

CASES = [
    ("跟我电脑一样：Windows 64 位（推荐）", Q.FAM_DESKTOP, "桌面"),
    ("安卓手机 App（ARM64，现在的手机基本都是）", Q.FAM_ANDROID, "安卓"),
    ("iPhone / iPad App（iOS）", Q.FAM_IOS, "iPhone"),
    ("鸿蒙手机 App（HarmonyOS）", Q.FAM_HARMONY, "鸿蒙"),
    ("网页（浏览器打开，电脑手机都能用）", Q.FAM_WEB, "网页"),
]


def t_family_detection():
    for ans, want, label in CASES:
        got = Q.family_of_prompt_answer(ans)
        assert got == want, "%s 应识别为 %s，实际 %s" % (label, want, got)
    # 空值 / 乱写也要有兜底，不能崩
    assert Q.family_of_prompt_answer("") == Q.FAM_UNKNOWN
    assert Q.family_of_prompt_answer("随便写的") == Q.FAM_UNKNOWN


check("平台族识别（含空值与乱写兜底）", t_family_detection)


def t_options_differ_per_family():
    """不同平台下，第 12 题（交付方式）的选项必须明显不同"""
    got = {}
    for ans, fam, label in CASES:
        r = Q.adapt("install", fam, "zh-CN", q_of("install"))
        got[label] = r["options"]
        assert r["options"], "%s 下不该没有选项" % label

    # 安卓要提 apk；iOS 要提开发者账号/App Store；桌面要提 exe
    assert any("apk" in o for o in got["安卓"]), "安卓应给 apk 选项: %s" % got["安卓"]
    assert any(("App Store" in o or "开发者账号" in o) for o in got["iPhone"]), \
        "iPhone 应提开发者账号/App Store: %s" % got["iPhone"]
    assert any("exe" in o for o in got["桌面"]), "桌面应给 exe 选项: %s" % got["桌面"]
    assert any("网址" in o for o in got["网页"]), "网页应给网址选项: %s" % got["网页"]

    # 桌面和安卓的选项不能是同一套
    assert got["桌面"] != got["安卓"], "桌面与安卓的选项不该相同"


check("交付方式选项按平台区分（apk/exe/网址）", t_options_differ_per_family)


def t_broad_options_kept():
    """用户明确要求「保留一些宽泛的选项」"""
    for ans, fam, label in CASES:
        for key in ("where", "install"):
            opts = Q.adapt(key, fam, "zh-CN", q_of(key))["options"]
            broad = Q.BROAD.get(key, [])
            for b in broad:
                assert b in opts, "%s 的 %s 缺宽泛选项 %r\n%s" % (label, key, b, opts)


check("每个平台下都保留了宽泛选项", t_broad_options_kept)


def t_title_changes_for_mobile():
    """第 4 题在手机下不该再问「做窗口程序还是网页」"""
    desktop = Q.adapt("where", Q.FAM_DESKTOP, "zh-CN", q_of("where"))
    mobile = Q.adapt("where", Q.FAM_ANDROID, "zh-CN", q_of("where"))
    assert "手机" in mobile["title"], "手机下标题该提手机: %s" % mobile["title"]
    assert "手机" not in desktop["title"], "桌面下标题不该提手机: %s" % desktop["title"]
    assert mobile["title"] != desktop["title"]


check("手机下第 4 题标题改名", t_title_changes_for_mobile)


def t_unadapted_questions_unchanged():
    """通用题（给谁用/痛点/输入/输出等）在任何平台下都该保持原样。

    ★ 例外：第 2 题「做什么」的正文**故意**会说「东西」而不是「软件」——
      因为类型可能是插件或脚本，说「软件」会别扭。
      所以它既不是平台相关、也不算「没变」，这里单独放行。
      题号也不要比（题号由题集组装时统一加，不是平台自适应的事）。
    """
    import re as _re

    ALLOWED_ADAPTED = {"what"}
    for key in ("who", "pain", "input", "output", "ref", "extra", "flow",
                "done", "limit"):
        base = q_of(key)
        want = _re.sub(r"^\d+[.、]\s*", "", str(A._qval(base, "title")))
        for ans, fam, label in CASES:
            r = Q.adapt(key, fam, "zh-CN", base)
            got = _re.sub(r"^\d+[.、]\s*", "", r["title"])
            # done 在手机/网页下会换验收标准，属于「按平台变」，跳过
            if key == "done" and fam in (Q.FAM_ANDROID, Q.FAM_IOS, Q.FAM_HARMONY, Q.FAM_WEB):
                continue
            assert got == want, \
                "%s 的 %s 在 %s 下不该变（%r → %r）" % (key, "title", label, want, got)
    assert "what" in ALLOWED_ADAPTED


check("通用题不受平台影响（保持宽泛）", t_unadapted_questions_unchanged)


def t_three_locales():
    """三语下都要有结果，不能出现空标题"""
    for loc in A.i18n.LANGS:
        for ans, fam, label in CASES:
            for key in ("where", "install", "done", "limit"):
                r = Q.adapt(key, fam, loc, q_of(key))
                assert r["title"], "%s/%s/%s 标题为空" % (loc, label, key)
                assert r["options"], "%s/%s/%s 没有选项" % (loc, label, key)


check("三语下都有标题与选项（无空缺）", t_three_locales)


print()
print("=" * 66)
print("界面层：点第 3 题后，后面的题要真的跟着变")
print("=" * 66)


def click_system(label_contains):
    """模拟真实点击：先让勾选框变量为 True，再调 _toggle。"""
    key = "system"
    opts = gui._options_of(key)
    target = [o for o in opts if label_contains in o]
    assert target, "找不到含 %r 的选项：%s" % (label_contains, opts)
    opt = target[0]
    var = gui.option_buttons[(key, opt)][0]
    var.set(True)                    # ← 这一步不能省，否则 _toggle 会当作取消勾选
    gui._toggle(key, opt)
    root.update_idletasks()
    return opt


def t_click_changes_family():
    click_system("网页")
    fam = gui._fam_built
    assert fam == Q.FAM_WEB, "点了网页后平台族应是 web，实际 %s" % fam


check("点『网页』后平台族变成 web", t_click_changes_family)


def t_click_updates_later_questions():
    click_system("安卓手机 App（ARM64")
    aq = gui.adapted.get("install")
    assert aq is not None, "install 题没被重建"
    assert any("apk" in o for o in aq["options"]), \
        "选安卓后第 12 题该给 apk 选项，实际: %s" % aq["options"]
    where = gui.adapted.get("where")
    assert "手机" in where["title"], "选安卓后第 4 题标题该提手机: %s" % where["title"]


check("选安卓后，第 4/12 题真的换成了手机版", t_click_updates_later_questions)


def t_content_preserved_across_rebuild():
    # 先填点内容
    box = gui.widgets["what"]
    box.delete("1.0", "end")
    box.insert("1.0", "我的测试内容")
    gui._on_typing("what")
    # 勾一个选项
    key = "who"
    opt = gui._options_of(key)[0]
    gui.option_buttons[(key, opt)][0].set(True)
    gui._toggle(key, opt)
    root.update_idletasks()

    # 切换平台（会重建表单）
    click_system("网页")

    kept = gui.widgets["what"].get("1.0", "end").strip()
    assert kept == "我的测试内容", "重建后已填内容丢了：%r" % kept
    assert opt in gui.selected.get("who", set()), \
        "重建后已勾选的选项丢了：%s" % gui.selected.get("who")


check("重建表单时已填内容与勾选都保住", t_content_preserved_across_rebuild)


def t_generated_prompt_uses_adapted_options():
    """生成的说明里，第 4/12 题的标题也该是 调整 后的版本"""
    click_system("安卓手机 App（ARM64")
    text = A.build_prompt(gui.collect())
    assert "手机上打算怎么用它" in text, "生成说明里第 4 题标题没跟着变"
    assert "怎么装到手机上" in text, "生成说明里第 12 题标题没跟着变"


check("生成的说明里也用了自适应后的标题", t_generated_prompt_uses_adapted_options)


print()
print("=" * 66)
print("第三层：按「做什么类型」换整套题（做插件 vs 做程序）")
print("=" * 66)


def click_kind(label_contains):
    """点第 1 题的类型选项（模拟真实点击：先把变量设为 True）。"""
    opts = gui._options_of("kind")
    target = [o for o in opts if label_contains in o]
    assert target, "找不到含 %r 的类型选项：%s" % (label_contains, opts)
    for o in opts:
        gui.option_buttons[("kind", o)][0].set(False)
    gui.selected["kind"] = set()
    opt = target[0]
    gui.option_buttons[("kind", opt)][0].set(True)
    gui._toggle("kind", opt)
    root.update_idletasks()
    return opt


def t_kind_detection():
    for text, want in (
        ("电脑上的程序（能双击打开的那种）", Q.KIND_PROGRAM),
        ("手机 App", Q.KIND_PROGRAM),
        ("网页", Q.KIND_PROGRAM),
        ("某个软件的插件/扩展（挂在别的软件里用）", Q.KIND_PLUGIN),
        ("自动化小脚本（跑一下就完事，没有界面）", Q.KIND_SCRIPT),
        ("不确定，你帮我判断", Q.KIND_PROGRAM),
        ("", Q.KIND_PROGRAM),
    ):
        got = Q.kind_of_prompt_answer(text)
        assert got == want, "%r 应识别为 %s，实际 %s" % (text, want, got)


check("类型识别（含空值与「不确定」兜底）", t_kind_detection)


def t_plugin_has_no_program_questions():
    """★ 核心诉求：做插件时不该被问 exe / 32 位 / apk。

    用户原话：「想创建一个新的 DSH 插件，之后的问题好多都不适配」。
    """
    qs = Q.questions_for(A.QUESTIONS, Q.KIND_PLUGIN, "zh-CN")
    keys = {q["key"] for q in qs}
    for gone in ("system", "where", "install"):
        assert gone not in keys, "插件类型不该出现「%s」题" % gone
    # 换成插件专属的
    for want in ("plugin_host", "plugin_trigger", "plugin_interface"):
        assert want in keys, "插件类型缺少「%s」题" % want


check("插件类型去掉了程序专属题，换成了插件题", t_plugin_has_no_program_questions)


def t_plugin_core_questions_are_early():
    """插件最核心的问题必须靠前，不能塞到最后"""
    qs = Q.questions_for(A.QUESTIONS, Q.KIND_PLUGIN, "zh-CN")
    order = [q["key"] for q in qs]
    assert order[0] == "kind", "第 1 题应该是「做什么类型」"
    assert order[1] == "what", "第 2 题应该是「做什么」"
    for key in ("plugin_host", "plugin_trigger", "plugin_interface"):
        pos = order.index(key)
        assert pos <= 5, "「%s」排在第 %d 位，太靠后了" % (key, pos + 1)
    # 挂在哪个软件里是第一个核心问题
    assert order[2] == "plugin_host", "第 3 题应该是「挂在哪个软件里」"


check("插件核心问题排在第 3~5 位（不塞到最后）", t_plugin_core_questions_are_early)


def t_numbers_are_sequential_in_every_kind():
    """每种类型下，题号必须与位置一致（换题集最容易在这里出错）"""
    import re as _re
    for loc in A.i18n.LANGS:
        for kind in (Q.KIND_PROGRAM, Q.KIND_PLUGIN, Q.KIND_SCRIPT):
            qs = Q.questions_for(A.QUESTIONS, kind, loc)
            for i, q in enumerate(qs, 1):
                m = _re.match(r"^(\d+)[.、]", q["title"])
                assert m, "%s/%s 第 %d 题没有题号: %r" % (loc, kind, i, q["title"])
                assert int(m.group(1)) == i, \
                    "%s/%s 第 %d 题题号是 %s" % (loc, kind, i, m.group(1))


check("三语三类型下题号都连续正确", t_numbers_are_sequential_in_every_kind)


def t_click_kind_swaps_question_set():
    click_kind("插件")
    keys = [q["key"] for q in gui._active_questions()]
    assert "plugin_host" in keys, "点了插件后应出现「挂在哪个软件里」"
    assert "system" not in keys, "点了插件后不该还有「系统与位数」"
    assert gui._kind == Q.KIND_PLUGIN
    # 控件也真的换了
    assert "plugin_host" in gui.widgets, "界面没有建出 plugin_host 的输入框"
    assert gui.widgets.get("system") is None, "界面还留着 system 的输入框"


check("点『插件』后整套题真的换掉（含控件）", t_click_kind_swaps_question_set)


def t_plugin_content_preserved_across_kind_switch():
    # ★ 走 _set_box_text：光 insert 不够，前景色还停在占位符色，
    #   collect() 会把内容当成「还没填」丢掉（这是测试第一版踩到的坑，
    #   真实用户不会遇到 —— 点进输入框会触发 FocusIn）。
    gui._set_box_text("what", "给 DSH 做一个需求检查插件")
    assert gui.collect()["what"] == "给 DSH 做一个需求检查插件", \
        "写进去之后 collect 就该读到，不能还是空的"
    opt = gui._options_of("who")[0]
    gui.option_buttons[("who", opt)][0].set(True)
    gui._toggle("who", opt)
    root.update_idletasks()

    click_kind("脚本")     # 换到脚本，再换回插件
    after_script = gui.widgets["what"].get("1.0", "end").strip()
    assert after_script == "给 DSH 做一个需求检查插件", \
        "换成脚本后已填内容就丢了：%r" % after_script

    click_kind("插件")
    kept = gui.widgets["what"].get("1.0", "end").strip()
    assert kept == "给 DSH 做一个需求检查插件", "换类型后已填内容丢了：%r" % kept
    assert opt in gui.selected.get("who", set()), \
        "换类型后已勾选项丢了：%s" % gui.selected.get("who")


check("换类型时已填内容与勾选都保住", t_plugin_content_preserved_across_kind_switch)


def t_prompt_for_plugin_has_no_exe_talk():
    """生成的说明里也不能出现「做程序」的说法"""
    click_kind("插件")
    a = gui.collect()
    a["what"] = "给 DSH 做一个需求检查插件"
    text = A.build_prompt(a)
    for gone in ("3. 这个软件要跑在什么系统上", "在哪里打开它", "一个 exe 文件",
                 "怎么交付给你"):
        assert gone not in text, "插件说明里不该出现「%s」" % gone
    for want in ("挂在哪个软件里", "怎么触发它", "交换信息"):
        assert want in text, "插件说明里缺少「%s」" % want


check("插件生成的需求说明里没有 exe/系统位数", t_prompt_for_plugin_has_no_exe_talk)


def t_script_kind_works():
    click_kind("脚本")
    keys = [q["key"] for q in gui._active_questions()]
    assert "script_run" in keys, "脚本类型应有「怎么运行」"
    assert "system" not in keys, "脚本类型不该问系统与位数"
    assert gui._kind == Q.KIND_SCRIPT
    # 回到程序，避免影响后面的检查
    click_kind("电脑上的程序")


check("脚本类型也能正常换题集", t_script_kind_works)

def t_repeated_switching_is_safe():
    """★ 回归：反复切换平台时，重建表单 + 画布重绘不能报错。

    真 bug：每建一张卡片都往 canvas 上 bind 一个折行 lambda，
    重建表单后旧控件已销毁，回调还指着它们 —— 一拉窗口就
    TclError: invalid command name "....!label"。
    而且每重建一次就多注册一批回调（13 → 26 → …）。

    现在改成统一回调 + 只登记活着的控件，这条测试盯住它。
    """
    n = len(gui._active_questions())
    assert len(gui.hint_labels) == n, \
        "初始说明 Label 数应等于题数 %d，实际 %d" % (n, len(gui.hint_labels))

    for i in range(14):
        opts = gui._options_of("system")
        if not opts:
            break       # 换到某类型后可能没有 system 题
        opt = opts[i % len(opts)]
        var = gui.option_buttons[("system", opt)][0]
        var.set(True)
        gui._toggle("system", opt)
        root.update_idletasks()
        # 模拟画布尺寸变化（就是当初报错的那条路径）
        gui._reflow_hints(type("E", (), {"width": 700 + i * 90})())

    n2 = len(gui._active_questions())
    assert len(gui.hint_labels) == n2, \
        "反复重建后说明 Label 数量漂移了：%d（应为 %d）" % (len(gui.hint_labels), n2)
    alive = [lb for lb in gui.hint_labels if lb.winfo_exists()]
    assert len(alive) == len(gui.hint_labels), "hint_labels 里还留着已销毁的控件"


check("反复切换平台 14 次：不报错、控件数不漂移", t_repeated_switching_is_safe)


def t_all_families_reachable_by_click():
    """每个平台选项单独点一次，都要能正常重建（不能有某个族崩）。

    注意：真实用户点第二个选项时，界面上的勾选是「替换」效果
    （_sync_options_to_box 每次按当前所有勾选重写）。
    所以每次测试前要把该题其他勾选清掉，否则会变成多选，
    平台族会按「最具体」解析 —— 第一版测试漏了这步，得到 unknown。
    """
    seen = set()
    opts = list(gui._options_of("system"))
    for opt in opts:
        for o in opts:
            gui.option_buttons[("system", o)][0].set(False)
        gui.selected["system"] = set()
        gui.option_buttons[("system", opt)][0].set(True)
        gui._toggle("system", opt)
        root.update_idletasks()
        fam = gui._fam_built
        seen.add(fam)
        aq = gui.adapted.get("install")
        assert aq and aq["options"], "平台族 %s（点了 %r）下第 12 题没有选项" % (fam, opt)
    assert len(seen) >= 5, "应该覆盖到 5 个以上平台族，实际 %s" % seen
    print("       覆盖到的平台族: %s" % sorted(seen))


check("逐个点完所有平台选项都能正常重建", t_all_families_reachable_by_click)




root.destroy()
print()
print("=" * 66)
print("通过 %d 项，失败 %d 项" % (pass_n, fail_n))
print("=== 全部通过 ===" if fail_n == 0 else "=== 有失败项 ===")
sys.exit(0 if fail_n == 0 else 1)
