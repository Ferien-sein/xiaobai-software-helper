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
    gui.select_page_by_key("nonexistent")
    root.update_idletasks()
    assert shown_pages() == ["fill"], "未知页面名应退回首页"


check("越界索引 / 未知页面名退回首页", t_out_of_range_falls_back)


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
