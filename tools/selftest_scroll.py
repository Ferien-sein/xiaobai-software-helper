# -*- coding: utf-8 -*-
"""验证滚动限流：真实拖拽场景下重绘次数、落点准确性、有无残影。

注意：计数用的 spy 必须转发到真正的 yview_moveto，
      否则画面不会动，测出来的落点全是假的（上一版就踩了这个坑）。
"""
import os
import sys
import time
import tkinter as tk

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import importlib
m = importlib.import_module("app")

root = tk.Tk()
root.geometry("1600x1000+0+0")
m.FONT_FAMILY = m.choose_font_family(root)
app = m.App(root)
root.update()

real = app.canvas.yview_moveto
draws = [0]


def spy(*a, **k):
    draws[0] += 1
    return real(*a, **k)          # ★ 必须真的转发，否则画面不动


app.canvas.yview_moveto = spy
total = app.inner.winfo_reqheight()
view = app.canvas.winfo_height()
print("内容高 %d px，视口高 %d px，可滚动 %d px\n" % (total, view, total - view))


def burst(fn, n, idle_every, label):
    draws[0] = 0
    t0 = time.time()
    for i in range(n):
        fn(i / float(n))
        if idle_every and (i + 1) % idle_every == 0:
            root.update()
    for _ in range(12):
        root.update()
        time.sleep(0.006)
    dt = (time.time() - t0) * 1000
    print("  %-30s %3d 事件 → 重绘 %3d 次，耗时 %5.0f ms" % (label, n, draws[0], dt))
    return draws[0]


print("场景一：拖着滚动条快速拉到底（事件突发，每 20 个事件处理一次队列）")
old = burst(lambda f: real(f), 120, 20, "旧路径 直接 moveto")
new = burst(lambda f: app._on_scrollbar("moveto", str(f)), 120, 20, "新路径 限流")
print("  → %d 次 → %d 次，减少 %.0f%%\n" % (old, new, (1 - new / max(1, old)) * 100))

print("场景二：拖动中每个事件都处理一次队列（最坏情况）")
old2 = burst(lambda f: real(f), 120, 1, "旧路径 直接 moveto")
new2 = burst(lambda f: app._on_scrollbar("moveto", str(f)), 120, 1, "新路径 限流")
print("  → %d 次 → %d 次，减少 %.0f%%\n" % (old2, new2, (1 - new2 / max(1, old2)) * 100))

# 恢复真函数，之后测准确性
app.canvas.yview_moveto = real

print("落点准确性（应精确停在拖到的位置）：")
ok_all = True
for frac in (0.0, 0.13, 0.37, 0.5, 0.66, 0.88, 1.0):
    app._on_scrollbar("moveto", str(frac))
    for _ in range(15):
        root.update()
        time.sleep(0.006)
    got = app.canvas.canvasy(0)
    want = max(0.0, min(frac * total, total - view))
    ok = abs(got - want) <= 2
    ok_all = ok_all and ok
    print("  moveto %.2f → canvasy=%.0f（期望 %.0f）%s" % (frac, got, want, "✔" if ok else "✘"))

print("\n残影检查（滚动中每张卡片「实际屏幕位置」与「应有位置」的偏差）：")
worst = 0
for i in range(60):
    app._on_scrollbar("moveto", str(i / 60.0))
    for _ in range(8):
        root.update()
        time.sleep(0.004)
    y0 = app.canvas.canvasy(0)
    ctop = app.canvas.winfo_rooty()
    for c in app.inner.winfo_children():
        if not c.winfo_ismapped():
            continue
        drift = abs(c.winfo_rooty() - (ctop + int(c.winfo_y() - y0)))
        worst = max(worst, drift)
print("  最大偏差 = %d px  %s" % (worst, "✔ 无残影" if worst <= 1 else "✘ 有错位"))

print("\n合计：落点%s，残影%s"
      % ("准确 ✔" if ok_all else "不准 ✘", "无 ✔" if worst <= 1 else "有 ✘"))
print("=== 滚动验证通过 ===" if ok_all and worst <= 1 else "=== 有问题，看上面 ✘ ===")
root.destroy()
