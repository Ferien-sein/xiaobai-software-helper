# -*- coding: utf-8 -*-
"""单独复现「点插件后 KeyError('system')」。"""
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
    assert target, "找不到 %r" % label_contains
    for o in opts:
        gui.option_buttons[("kind", o)][0].set(False)
    gui.selected["kind"] = set()
    opt = target[0]
    gui.option_buttons[("kind", opt)][0].set(True)
    gui._toggle("kind", opt)
    root.update_idletasks()


try:
    click_kind("插件")
    keys = [q["key"] for q in gui._active_questions()]
    print("  keys 里有 plugin_host:", "plugin_host" in keys)
    print("  keys 里有 system:", "system" in keys)
    print("  gui._kind =", gui._kind)
    print("  widgets 里有 plugin_host:", "plugin_host" in gui.widgets)
    print("  widgets 里有 system:", "system" in gui.widgets)
    print("  selected 的键:", sorted(gui.selected))
    assert "plugin_host" in gui.widgets, "没有建出 plugin_host"
    assert gui.widgets.get("system") is None, "还留着 system"
    print("  >>> 这个测试应当通过")
except Exception:
    traceback.print_exc()

root.destroy()
