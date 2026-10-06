# -*- coding: utf-8 -*-
"""页面映射回归测试。

守住这个真实 bug：新增「先查查」页时，插入位置在中间，
导致所有靠**索引**指页面的代码整体位移 ——
show_about() 里的 _select_page(2) 从「使用说明」变成了「历史记录」，
而且**不报错**、只是默默打开错的页（截图时才发现）。

这类问题的特征是"看起来都正常"，所以必须有断言盯住。

用法: python tools/selftest_pages.py
"""

import os
# ★ 锁定界面语言（XBSH_LANG_LOCKED）：这些检查/自检脚本的输出与断言都基于简体中文，
#   而 i18n 会按系统区域自动探测语言 —— 在英文机器 / CI 上会探测成英文，
#   断言就全挂（GitHub runner 上真踩过：selftest_platform 11 项失败）。
#   ★ 用 = 不用 setdefault：环境里已有 XBSH_LANG 时 setdefault 不覆盖，锁会失效。
#   插在第一个模块级 import 之前，保证任何依赖 i18n 的 import 都在它之后。
os.environ["XBSH_LANG"] = "zh-CN"

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import tkinter as tk  # noqa: E402

import app as A  # noqa: E402

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


A.apply_dpi_awareness()
root = tk.Tk()
A.init_ui_scale(root)
A.init_theme()
A.init_lang()
gui = A.App(root)
root.update_idletasks()

EXPECTED = ("fill", "lookup", "history", "about")


def shown_pages():
    return sorted(n for n, f in gui.pages.items() if f.winfo_manager())


print("=" * 62)
print("页面映射")
print("=" * 62)


def t_pages_exist():
    assert set(gui.pages.keys()) == set(EXPECTED), \
        "页面集合不对: %s" % sorted(gui.pages.keys())
    assert len(A.App.PAGES) == len(EXPECTED), \
        "PAGES 数量与页面数不一致: %s" % (A.App.PAGES,)


check("页面集合与数量一致", t_pages_exist)


def t_index_maps_to_same_key():
    """★ 核心断言：索引 i 选出来的页面必须正好是 EXPECTED[i]"""
    wrong = []
    for i, key in enumerate(EXPECTED):
        gui._select_page(i)
        root.update_idletasks()
        got = shown_pages()
        if got != [key]:
            wrong.append("index=%d 期望 %s 实际 %s" % (i, key, got))
    assert not wrong, "索引与页面错位：\n       " + "\n       ".join(wrong)


check("索引与页面对应关系正确", t_index_maps_to_same_key)


def t_select_by_key():
    wrong = []
    for key in EXPECTED:
        gui.select_page_by_key(key)
        root.update_idletasks()
        got = shown_pages()
        if got != [key]:
            wrong.append("key=%s 实际 %s" % (key, got))
    assert not wrong, "按名字选页错位：\n       " + "\n       ".join(wrong)


check("按名字选页正确", t_select_by_key)


def t_show_about():
    """★ 这个函数之前就是错的（打开成历史记录页）"""
    gui.show_about()
    root.update_idletasks()
    got = shown_pages()
    assert got == ["about"], "show_about() 应打开使用说明页，实际 %s" % got


check("show_about() 打开的是使用说明页", t_show_about)


def t_only_one_page_at_a_time():
    for i in range(len(EXPECTED)):
        gui._select_page(i)
        root.update_idletasks()
        n = len(shown_pages())
        assert n == 1, "index=%d 同时显示了 %d 个页面" % (i, n)


check("任何时刻只显示一个页面", t_only_one_page_at_a_time)


def t_out_of_range_falls_back():
    gui._select_page(99)
    root.update_idletasks()
    assert shown_pages() == ["fill"], "越界索引应退回首页，实际 %s" % shown_pages()


check("越界索引退回首页", t_out_of_range_falls_back)


def t_select_by_key_returns_bool():
    """★ 回归：select_page_by_key 必须**返回是否成功**，且认不出来时不改变页面。

    真事故（两回）：
      1. show_about() 用索引 2，插页后静默打开成「历史记录」
      2. 它内部把无法识别的名字**静默回退到第一页** ——
         于是调 select_page_by_key("先查查") 返回 None、停在首页；
         XBSH_PAGE 传页名时正是这样，截图截成了「填写需求」页。
    现在的约定：认不出来 → 返回 False 且**保持当前页不变**。
    """
    assert gui.select_page_by_key("about") is True
    root.update_idletasks()
    before = shown_pages()
    assert before == ["about"]
    for bad in ("nonexistent", "先查查查", ""):
        got = gui.select_page_by_key(bad)
        root.update_idletasks()
        assert got is False, "未知名字 %r 应返回 False，实际 %r" % (bad, got)
        assert shown_pages() == before, \
            "未知名字 %r 不该改变当前页（%s → %s）" % (bad, before, shown_pages())


check("未知页面名返回 False 且不改变当前页", t_select_by_key_returns_bool)


def t_select_by_chinese_display_name():
    """★ 回归：用**中文页名**也要能定位。

    为什么需要：截图脚本、自检、XBSH_PAGE 用中文名更自然；
    而界面切到英文后 PAGES 是英文显示名，容易踩「名字对不上、
    还静默回退到第一页」。
    """
    want = {"填写需求": "fill", "先查查": "lookup",
            "历史记录": "history", "使用说明": "about"}
    wrong = []
    for label, key in want.items():
        ok = gui.select_page_by_key(label)
        root.update_idletasks()
        got = shown_pages()
        if not ok or got != [key]:
            wrong.append("%s → 返回 %s，实际显示 %s（期望 %s）" % (label, ok, got, key))
    assert not wrong, "中文页名定位失败：\n       " + "\n       ".join(wrong)


check("用中文页名能定位到正确的页", t_select_by_chinese_display_name)


def t_page_keys_are_stable():
    """内部 key 与显示名必须分开：显示名随语言变，key 不能变。"""
    assert A.App.PAGE_KEYS == EXPECTED, \
        "PAGE_KEYS 变了：%s（会影响所有按 key 指页面的地方）" % (A.App.PAGE_KEYS,)
    assert len(A.App.PAGE_KEYS) == len(A.App.PAGES), "PAGE_KEYS 与 PAGES 数量不一致"
    # 任何语言的显示名都不该等于某个内部 key，否则用显示名会选错页
    saved = gui.page_index
    for loc in A.i18n.LANGS:
        A.i18n.set_lang(loc)
        for lb in A.App.PAGES:
            t_lb = A.i18n.t(lb)
            assert t_lb not in A.App.PAGE_KEYS, \
                "[%s] 显示名 %r 与内部 key 撞名，用显示名会选错页" % (loc, t_lb)
    A.i18n.set_lang("zh-CN")
    gui.page_index = saved


check("内部 key 稳定、任何语言的显示名都不与 key 撞名", t_page_keys_are_stable)


def t_nav_highlight_matches():
    """选中态要和实际显示的页一致（截图里就是这两者不一致才暴露了 bug）"""
    wrong = []
    for i in range(len(EXPECTED)):
        gui._select_page(i)
        root.update_idletasks()
        shown = shown_pages()[0]
        if shown != EXPECTED[i]:
            wrong.append("index=%d 显示 %s" % (i, shown))
        if gui.page_index != i:
            wrong.append("index=%d 但 page_index=%d" % (i, gui.page_index))
    assert not wrong, "选中态与显示不一致: %s" % wrong


check("侧栏选中态与实际页面一致", t_nav_highlight_matches)

root.destroy()
print()
print("=" * 62)
print("通过 %d 项，失败 %d 项" % (pass_n, fail_n))
print("=== 全部通过 ===" if fail_n == 0 else "=== 有失败项 ===")
sys.exit(0 if fail_n == 0 else 1)
