# -*- coding: utf-8 -*-
"""验证滚轮路由：指针停在输入框 / 勾选框 / 提示文字 / 预览框上时，该滚哪个区域。"""

import os
# ★ 锁定界面语言（XBSH_LANG_LOCKED）：这些检查/自检脚本的输出与断言都基于简体中文，
#   而 i18n 会按系统区域自动探测语言 —— 在英文机器 / CI 上会探测成英文，
#   断言就全挂（GitHub runner 上真踩过：selftest_platform 11 项失败）。
#   ★ 用 = 不用 setdefault：环境里已有 XBSH_LANG 时 setdefault 不覆盖，锁会失效。
#   插在第一个模块级 import 之前，保证任何依赖 i18n 的 import 都在它之后。
os.environ["XBSH_LANG"] = "zh-CN"

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import importlib
m = importlib.import_module("app")

root = tk.Tk()
root.geometry("1600x1000+0+0")
m.FONT_FAMILY = m.choose_font_family(root)
app = m.App(root)
root.update()
root.update_idletasks()


class FakeWheel:
    def __init__(self, widget, delta=-120):
        self.widget = widget
        self.delta = delta


def probe(label, target, expect=None):
    """在 target 控件上发一次滚轮，返回 (表单是否动了, 预览是否动了)。"""
    c0, p0 = app.canvas.canvasy(0), app.preview.yview()[0]
    # 表单滚到中间，保证上下都能滚
    app.canvas.yview_moveto(0.4)
    app.preview.yview_moveto(0.0)
    root.update()
    c0, p0 = app.canvas.canvasy(0), app.preview.yview()[0]
    ret = app._route_wheel(FakeWheel(target))
    root.update()
    dc = app.canvas.canvasy(0) - c0
    dp = app.preview.yview()[0] - p0
    moved = []
    if abs(dc) > 1:
        moved.append("表单(%+.0f)" % dc)
    if abs(dp) > 0.001:
        moved.append("预览(%+.3f)" % dp)
    got = "+".join(moved) or "都没动"
    ok = "✔" if (expect is None or expect in got) else "✘"
    print("  %-28s → %-22s 期望含「%s」 %s" % (label, got, expect, ok))
    return ok == "✔"


ok = True
print("滚轮路由测试（delta=-120 即向下滚一格）：\n")

# 1) 指针在表单里的输入框上
box = app.widgets["what"]
box.yview_moveto(0.0)          # 输入框内容不满一屏，应该让外层表单滚
root.update()
ok &= probe("输入框（内容不满一屏）", box, "表单")

# 2) 指针在勾选框上
cb = list(app.option_buttons.values())[0][1]
ok &= probe("勾选框", cb, "表单")

# 3) 指针在提示文字上
hint = None
for card in app.inner.winfo_children():
    for c in card.winfo_children():
        try:
            if str(c.cget("style")) == "QHint.TLabel":
                hint = c
                break
        except Exception:
            pass
    if hint:
        break
ok &= probe("提示文字标签", hint, "表单")

# 4) 指针在卡片空白处
ok &= probe("卡片 Frame", app.inner.winfo_children()[0], "表单")

# 5) 指针在右边预览框上 → 应该滚预览，不动表单
ok &= probe("右侧预览框", app.preview, "预览")

# 6) 输入框内容够长时，应该滚输入框自己而不是外层
long_box = app.widgets["pain"]
long_box.delete("1.0", "end")
long_box.insert("1.0", "\n".join("第 %d 行内容测试" % i for i in range(40)))
root.update()
c0 = app.canvas.canvasy(0)
b0 = long_box.yview()[0]
app._route_wheel(FakeWheel(long_box))
root.update()
dc = app.canvas.canvasy(0) - c0
db = long_box.yview()[0] - b0
got = []
if abs(dc) > 1:
    got.append("表单")
if abs(db) > 0.001:
    got.append("输入框自己")
res = "+".join(got) or "都没动"
good = "输入框自己" in res and "表单" not in res
ok &= good
print("  %-28s → %-22s 期望滚「输入框自己」 %s" % ("输入框（内容超一屏）", res, "✔" if good else "✘"))

print("\n向上滚一格（delta=+120）应能往回滚：")
app.canvas.yview_moveto(0.5)
root.update()
c0 = app.canvas.canvasy(0)
app._route_wheel(FakeWheel(app.inner.winfo_children()[0], delta=120))
root.update()
dc = app.canvas.canvasy(0) - c0
good = dc < -1
ok &= good
print("  表单位移 %+.0f px（应为负）%s" % (dc, "✔" if good else "✘"))

print("\n全局绑定是否装好（bind_all）：")
b = app.root.bind_all("<MouseWheel>")
print("  bind_all('<MouseWheel>') =", b)

print("\n%s" % ("=== 滚轮路由验证通过 ===" if ok else "=== 有项目未通过 ✘ ==="))
root.destroy()
