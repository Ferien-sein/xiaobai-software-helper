# -*- coding: utf-8 -*-
"""抓「换类型丢内容」的真实堆栈。"""
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import tkinter as tk  # noqa: E402

import app as A  # noqa: E402
import questionnaire as Q  # noqa: E402

A.init_lang()
A.apply_dpi_awareness()
root = tk.Tk()
A.init_ui_scale(root)
A.init_theme()
gui = A.App(root)
root.update_idletasks()


def click_kind(label_contains):
    opts = gui._options_of("kind")
    target = [o for o in opts if label_contains in o]
    assert target, "找不到 %r：%s" % (label_contains, opts)
    for o in opts:
        gui.option_buttons[("kind", o)][0].set(False)
    gui.selected["kind"] = set()
    opt = target[0]
    gui.option_buttons[("kind", opt)][0].set(True)
    print("  _toggle(kind, %r)" % opt[:26])
    gui._toggle("kind", opt)
    root.update_idletasks()


box = gui.widgets["what"]
box.delete("1.0", "end")
box.insert("1.0", "给 DSH 做一个需求检查插件")
gui._on_typing("what")
print("  写入后:", repr(gui.widgets["what"].get("1.0", "end").strip())[:50])
print("  collect()['what'] =", repr(gui.collect().get("what"))[:50])
print("  前景色:", gui.widgets["what"].cget("foreground"), " 占位符色:", A.PLACEHOLDER_FG)

print()
print("  === 点插件 ===")
try:
    click_kind("插件")
except Exception:
    traceback.print_exc()
print("  点插件后 what =", repr(gui.widgets["what"].get("1.0", "end").strip())[:50])

print()
print("  === 点脚本 ===")
try:
    click_kind("脚本")
except Exception:
    traceback.print_exc()
print("  点脚本后 what =", repr(gui.widgets["what"].get("1.0", "end").strip())[:50])
print("  前景色:", gui.widgets["what"].cget("foreground"))
print("  collect()['what'] =", repr(gui.collect().get("what"))[:50])

root.destroy()
