# -*- coding: utf-8 -*-
"""配色对比度自检：确保任何文字都能被看见、以及代码里没有写死的颜色。

为什么需要：
  真 bug —— 输入框写内容时用了硬编码的 "#1b1b1b"（浅色主题的正文色），
  暗色主题背景是 #1d1e21，文字几乎和背景一样黑。
  用户的实际反馈就是「打完字看不见自己打了什么」。
  这类问题**不会报错**，只会静默让人看不见 —— 必须用算的，不能靠肉眼。

检查三件事：
  1. 主题里每对「前景/背景」的对比度达到可读标准（WCAG）
  2. 界面控件实际用的前景/背景色也对得上（覆盖刚才那个 bug 的路径）
  3. 源码里没有写死的十六进制颜色（除了 THEMES 定义本身）

用法: python tools/selftest_contrast.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

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


# ---------------- WCAG 对比度 ----------------
def _srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hexcolor):
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb_to_lin(r) + 0.7152 * _srgb_to_lin(g) + 0.0722 * _srgb_to_lin(b)


def contrast(fg, bg):
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


print("=" * 66)
print("配色对比度（WCAG：正文 ≥ 4.5 可读，≥ 3.0 勉强可辨）")
print("=" * 66)

# 允许的模块级颜色常量：它们会在 init_theme() 里被换成当前主题的颜色，
# 不是「写死不变」的颜色，所以不该算成问题。
ALLOWED_MODULE_COLORS = {"PLACEHOLDER_FG"}

# 「大号文字」的前景/背景对：主按钮上是 11 号加粗，按 WCAG 大号标准（≥3.0）衡量。
# 用 4.5 去卡按钮过严 —— 白字蓝底是常见且可接受的组合。
LARGE_PAIRS = {("on_brand", "brand")}

# 每个主题里「哪种文字画在哪种背景上」
PAIRS = [
    # (前景键, 背景键, 叫什么, 最低要求)
    ("fg", "inset", "输入框正文 / 输入框底", 4.5),
    ("fg", "card", "卡片正文 / 卡片底", 4.5),
    ("fg", "bg", "页面正文 / 页面底", 4.5),
    ("fg2", "sidebar", "侧栏文字 / 侧栏底", 4.5),
    ("fg2", "card", "次级文字 / 卡片底", 4.5),
    ("fg3", "card", "三级文字 / 卡片底", 3.0),
    ("placeholder", "inset", "示例灰字 / 输入框底", 3.0),   # 故意淡，3.0 即可
    ("on_brand", "brand", "主按钮文字 / 主按钮底", 4.5),
]

# 按「大号文字」标准放宽的那几对
PAIRS = [
    (fg_k, bg_k, label, (3.0 if (fg_k, bg_k) in LARGE_PAIRS else need))
    for fg_k, bg_k, label, need in PAIRS
]

for mode, theme in A.THEMES.items():
    print()
    print("  【%s】%s" % (theme.get("name", mode), mode))
    for fg_k, bg_k, label, need in PAIRS:
        fg, bg = theme.get(fg_k), theme.get(bg_k)
        if not fg or not bg:
            continue
        ratio = contrast(fg, bg)
        ok = ratio >= need
        print("    %-26s %s on %s  对比度 %5.2f  %s" % (
            label, fg, bg, ratio, "OK" if ok else "★ 偏低（需 %.1f）" % need))


def t_all_pairs_readable():
    bad = []
    for mode, theme in A.THEMES.items():
        for fg_k, bg_k, label, need in PAIRS:
            fg, bg = theme.get(fg_k), theme.get(bg_k)
            if not fg or not bg:
                continue
            ratio = contrast(fg, bg)
            if ratio < need:
                bad.append("%s 主题的「%s」对比度只有 %.2f（需 ≥%.1f）"
                           % (mode, label, ratio, need))
    assert not bad, "\n       ".join(bad)


check("所有主题的常用前景/背景组合都够清晰", t_all_pairs_readable)

# ---------------- 实测界面控件的真实颜色 ----------------
print()
print("=" * 66)
print("界面控件实际颜色（覆盖那个真 bug 的路径）")
print("=" * 66)

A.init_lang()
A.apply_dpi_awareness()
root = tk.Tk()
A.init_ui_scale(root)
A.init_theme()
gui = A.App(root)
root.update_idletasks()


def box_colors(key):
    b = gui.widgets[key]
    return b.cget("foreground"), b.cget("background")


def t_empty_box_is_placeholder():
    """空框应显示占位符灰（不能是正文色，否则像已填）"""
    fg, bg = box_colors("what")
    assert fg.lower() == A.PLACEHOLDER_FG.lower(), \
        "空框前景应是占位符色 %s，实际 %s" % (A.PLACEHOLDER_FG, fg)
    ratio = contrast(fg, bg)
    assert ratio >= 3.0, "占位符灰在背景上对比度只有 %.2f，太淡了" % ratio


check("空输入框用占位符灰（且看得见）", t_empty_box_is_placeholder)


def t_typing_makes_text_readable():
    """★ 这条就是用户反馈的 bug：打完字必须看得见"""
    b = gui.widgets["what"]
    gui._clear_example(b)
    gui._clear_example(b)
    b.insert("1.0", "我打的字")
    fg, bg = box_colors("what")
    ratio = contrast(fg, bg)
    assert ratio >= 4.5, \
        "打完字后对比度只有 %.2f（前景 %s / 背景 %s）—— 就是「看不见自己打的字」" % (ratio, fg, bg)


check("打字后正文对比度 ≥ 4.5（原本的 bug）", t_typing_makes_text_readable)


def t_option_click_makes_text_readable():
    """★ 点选项按钮也会往框里写字，这条路也要够清晰"""
    for key in ("who", "what", "output"):
        b = gui.widgets[key]
        b.delete("1.0", "end")
        b.configure(foreground=A.PLACEHOLDER_FG)
        b.insert("1.0", A._qval([q for q in A.QUESTIONS if q["key"] == key][0], "example"))
        opts = gui._options_of(key)
        assert opts, "%s 应该有选项" % key
        gui._toggle(key, opts[0])
        root.update_idletasks()
        fg, bg = box_colors(key)
        ratio = contrast(fg, bg)
        assert ratio >= 4.5, \
            "%s 点选项后对比度只有 %.2f（前景 %s / 背景 %s）" % (key, ratio, fg, bg)


check("点选项写入后对比度 ≥ 4.5", t_option_click_makes_text_readable)


def t_no_hardcoded_colors_outside_themes():
    """源码里除 THEMES 之外不该有写死的十六进制颜色。

    这个 bug 的根因就是写死颜色 —— 换主题后它不跟着变。
    例外：ALLOWED_MODULE_COLORS 里的常量会被 init_theme() 覆盖成主题色，
    不算写死（PLACEHOLDER_FG 就是这种）。
    """
    src = io.open(os.path.join(SRC, "app.py"), encoding="utf-8").read()
    lines = src.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("THEMES = {"))
    end = next(i for i in range(start, len(lines)) if lines[i].startswith("}"))
    bad = []
    for i, l in enumerate(lines, 1):
        if start < i <= end:
            continue        # 主题定义本身，允许
        if l.strip().startswith("#"):
            continue        # 注释
        if any(name in l for name in ALLOWED_MODULE_COLORS):
            continue        # 这些会在 init_theme() 里被替换成主题色
        for m in re.finditer(r'["\'](#[0-9a-fA-F]{6})["\']', l):
            bad.append("L%d: %s" % (i, l.strip()[:80]))
            break
    assert not bad, "源码里有写死的颜色（换主题不会跟着变）：\n       " + "\n       ".join(bad)


check("源码里没有 THEMES 之外的写死颜色", t_no_hardcoded_colors_outside_themes)


def t_placeholder_is_theme_driven():
    """反向确认：PLACEHOLDER_FG 确实会跟着主题变（所以它不算写死）"""
    seen = set()
    for mode in A.THEMES:
        A.THEME_MODE = mode
        A.THEME = A.THEMES[mode]
        A.PLACEHOLDER_FG = A.THEME["placeholder"]
        seen.add(A.PLACEHOLDER_FG)
    assert len(seen) == len(A.THEMES), \
        "PLACEHOLDER_FG 在两套主题下应该不同，实际都是 %s" % seen


check("占位符色确实跟随主题（不是写死的）", t_placeholder_is_theme_driven)


def t_both_themes_have_same_keys():
    keys = set(A.THEMES["dark"].keys())
    for mode, theme in A.THEMES.items():
        missing = keys - set(theme.keys())
        assert not missing, "%s 主题缺少颜色键: %s" % (mode, missing)


check("两套主题的颜色键一致", t_both_themes_have_same_keys)

root.destroy()
print()
print("=" * 66)
print("通过 %d 项，失败 %d 项" % (pass_n, fail_n))
print("=== 全部通过 ===" if fail_n == 0 else "=== 有失败项 ===")
sys.exit(0 if fail_n == 0 else 1)
