# -*- coding: utf-8 -*-
"""缩放自检：验证 UI_SCALE 是否真的把界面上所有尺寸都放大了。

用法（可传多个缩放值）：
    python _缩放自检.py 1.0 1.5 2.0
每一步都在独立子进程里跑，因为缩放要在建窗口之前定好。
"""
import os
import subprocess
import sys

APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
PY = sys.executable

CHILD = r'''
import os, sys, json, tkinter as tk
sys.path.insert(0, r"$APPDIR")
import importlib
m = importlib.import_module("app")

root = tk.Tk()
scale, rec, why = m.init_ui_scale(root)
m.FONT_FAMILY = m.choose_font_family(root)
app = m.App(root)
# 必须让布局真正跑完，否则 winfo_* 量到的是还没确定的值
root.geometry("{}x{}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
root.update_idletasks()
root.update()

data = {
    "scale": scale,
    "recommended": rec,
    "why": why,
    "screen": list(m.screen_size(root)),
    "win": [root.winfo_width(), root.winfo_height()],
    "box_multi": app.widgets["what"].winfo_reqheight(),
    "box_single": app.widgets["who"].winfo_reqheight(),
    "box_multi_cfg": int(app.widgets["what"].cget("height")),
    "box_single_cfg": int(app.widgets["who"].cget("height")),
    "checkbutton": len(app.option_buttons),
    "tabs": len(getattr(app, "pages", {})),   # 现在是叠放 Frame，不再是 Notebook
}

# 真实字体：从界面上真正用到的具名字体量出真实行高（像素），
# 这是"字到底变没变大"的硬指标。注意字号档位会改变具名字体的名字，
# 所以不能写死名字，要按同一套公式算出来。
import tkinter.font as tkfont
data["qtitle_font"] = None
data["linespace"] = None
data["font_boost"] = m.FONT_BOOST
want_name = "dsh_-%d_b" % max(7, int(round(m.ui(11) * m.FONT_BOOST)))
try:
    fnt = tkfont.nametofont(want_name)
    data["qtitle_font"] = [fnt.cget("family"), fnt.cget("size"), fnt.actual("size")]
    data["linespace"] = fnt.metrics("linespace")
except Exception as e:
    data["font_error"] = "%s (找 %s；现有 %s)" % (
        e, want_name, sorted(n for n in tkfont.names(root) if n.startswith("dsh_")))
data["tk_scaling"] = float(root.tk.call("tk", "scaling"))
root.destroy()
print("RESULT:" + json.dumps(data, ensure_ascii=False))
'''
from string import Template
CHILD = Template(CHILD).substitute(APPDIR=APP_DIR)


def run_one(scale, screen=None):
    env = dict(os.environ)
    env["XBSH_UI_SCALE"] = str(scale)
    env["PYTHONIOENCODING"] = "utf-8"
    if screen:
        env["XBSH_UI_SCREEN"] = screen
    p = subprocess.run([PY, "-X", "utf8", "-c", CHILD],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    for line in (p.stdout or "").splitlines():
        if line.startswith("RESULT:"):
            import json
            return json.loads(line[len("RESULT:"):])
    print("  ✘ 子进程失败（这一步不能算通过）")
    print("    " + "\n    ".join((p.stderr or "无 stderr").strip().splitlines()[-6:]))
    return None


if __name__ == "__main__":
    want = [float(a) for a in sys.argv[1:]] or [1.0, 1.25, 1.5, 2.0, 2.5]
    SIM = os.environ.get("XBSH_TEST_SCREEN", "3840x2160")   # 模拟 4K，检查窗口是否放得下
    import tkinter as tk
    sys.path.insert(0, APP_DIR)
    import importlib
    m = importlib.import_module("app")
    rec, why = m.detect_recommended_scale()
    r = tk.Tk(); r.withdraw()
    real = (r.winfo_screenwidth(), r.winfo_screenheight())
    r.destroy()
    print(f"  Windows 推荐缩放 = {rec:.3f}  ({why})")
    print(f"  实测系统 DPI      = {m._windows_dpi()}")
    print(f"  本会话真实屏幕    = {real[0]} x {real[1]}")
    print(f"  缩放测试模拟屏幕  = {SIM}（用 XBSH_UI_SCREEN 模拟，验证 4K 表现）")

    print("\n%6s | %10s | %7s | %8s | %8s | %9s | %9s" %
          ("缩放", "窗口尺寸", "标题字号px", "多行框请求高", "单行框请求高", "多行height", "单行height"))
    print("-" * 84)
    base = None
    rows = []
    failures = 0
    for s in want:
        d = run_one(s, SIM)
        if d is None:
            failures += 1
            continue
        rows.append((s, d))
        if s == 1.0:
            base = d
        qf = d.get("qtitle_font")
        print("%5d%% | %10s | %7s | %8d | %8d | %9d | %9d" % (
            int(round(s * 100)),
            "%dx%d" % tuple(d["win"]),
            qf[1] if qf else "?",
            d["box_multi"], d["box_single"], d["box_multi_cfg"], d["box_single_cfg"]))

    if base is None:
        print("\n没有 100% 基准，无法做等比检查")
        failures += 1

    print("\n输入框尺寸检查（可见行数固定，框高随字体等比增长）：")
    checked = 0
    if base:
        for s, d in rows:
            if abs(s - 1.0) < 1e-9:
                continue
            for name, key, cfg in (("多行框", "box_multi", "box_multi_cfg"),
                                   ("单行框", "box_single", "box_single_cfg")):
                fixed = 12                                    # 边框 2 + pady 10，固定不缩放
                # 以「实测字体行高」为基准：框内每行像素应当永远等于字体行高
                per_line = (d[key] - fixed) / max(1, d[cfg])
                got = per_line / (d.get("linespace") or 16)
                good = abs(got - 1.0) <= 0.20
                checked += 1
                if not good:
                    failures += 1
                same_lines = d[cfg] == base[cfg]
                print("    %-6s %4d%%: 框内每行 %.1fpx / 字体行高 %dpx = %.2f  行数%s  %s"
                      % (name, int(s * 100), per_line, d.get("linespace") or 0, got,
                         "不变(%d)" % d[cfg] if same_lines else "变了(%d→%d)" % (base[cfg], d[cfg]),
                         "✔" if (good and same_lines) else "✘"))

    print("\n字号检查（标题文字的真实行高，应随缩放成正比）：")
    base_ls = None
    for s, d in rows:
        ls = d.get("linespace")
        if not ls:
            failures += 1
            print("  %4d%%: ✘ 量不到行高 (%s)" % (int(s * 100), d.get("font_error")))
            continue
        if abs(s - 1.0) < 1e-9:
            base_ls = ls
        if base_ls:
            got = ls / base_ls
            good = abs(got - s) / s <= 0.20
            checked += 1
            if not good:
                failures += 1
            print("  %4d%%: 行高 %dpx = x%.2f  期望 x%.2f  %s"
                  % (int(s * 100), ls, got, s, "✔" if good else "✘"))

    print("\n屏幕边界检查（窗口必须放得下 %s）：" % SIM)
    sw, sh = (int(x) for x in SIM.lower().split("x"))
    for s, d in rows:
        w, h = d["win"]
        fits = w <= sw and h <= sh
        if not fits:
            failures += 1
        print("  %4d%%: 窗口 %dx%d  %s" % (int(s * 100), w, h, "✔" if fits else "✘ 超出屏幕"))

    print("\n功能检查：")
    # 勾选框期望值从问卷动态算，不写死数字 ——
    # 以前写死 64，新增一个问题（9 个选项）后就全部失败。
    #
    # ★ 必须从**真实的 App 实例**上算，不能用 _qopts(q) 或全局 QUESTIONS：
    #   1) 问卷会按平台族自适应（第 12 题多出「你决定就好」这类宽泛选项）
    #   2) 问卷还会按「做什么类型」换整套题（程序/插件/脚本题数不同，
    #      而且最前面多了一题「你要做的是哪一种」）
    #   界面实际渲染的是这两层调整之后的结果。
    try:
        import tkinter as _tk
        import app as _app

        _root = _tk.Tk()
        _app.apply_dpi_awareness()
        _app.init_ui_scale(_root)
        _app.init_theme()
        _app.init_lang()
        _gui = _app.App(_root)
        _root.update_idletasks()
        expect_cb = sum(len(_gui._options_of(q["key"]))
                        for q in _gui._active_questions())
        _root.destroy()
    except Exception as e:  # noqa: BLE001
        expect_cb = None
        print("  （无法从问卷推算勾选框数量：%r）" % (e,))

    for s, d in rows:
        bad = []
        if expect_cb is not None and d["checkbutton"] != expect_cb:
            bad.append("勾选框数量=%d(应为%d)" % (d["checkbutton"], expect_cb))
        # 页签数从问卷/页面定义动态取，不写死 ——
        # 新增「先查查」页后写死的 3 就失效了。
        expect_tabs = len(_app.App.PAGES) if expect_cb is not None else None
        if expect_tabs is not None and d["tabs"] != expect_tabs:
            bad.append("页签=%d(应为%d)" % (d["tabs"], expect_tabs))
        if bad:
            failures += 1
        print("  %4d%%: %s" % (int(s * 100), "✔ 正常" if not bad else "✘ " + "；".join(bad)))

    print("\n" + ("=== 缩放自检全部通过（检查了 %d 项等比，%d 种缩放）===" % (checked, len(rows))
                  if failures == 0 else
                  "=== 有 %d 项未通过，看上面 ✘ ===" % failures))
    sys.exit(0 if failures == 0 else 1)
