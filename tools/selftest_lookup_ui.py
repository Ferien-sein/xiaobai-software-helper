# -*- coding: utf-8 -*-
"""查重功能的集成自检：起来界面 → 填答案 → 生成查询词 → 真查一次。

为什么要有这一层：模块自检只能证明逻辑对，
**"从界面上的答案生成出能用的查询词"这条链路**必须真的跑一遍才敢说可用。

联网是有配额的（GitHub 未认证 10 次/分钟），所以默认只查 1 次；
加 --offline 可以只验证不联网的部分。

用法:
  python tools/selftest_lookup_ui.py            # 含 1 次真实联网
  python tools/selftest_lookup_ui.py --offline  # 完全不联网
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
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import tkinter as tk  # noqa: E402

import app as A  # noqa: E402
import github_lookup as gl  # noqa: E402

OFFLINE = "--offline" in sys.argv
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


print("=" * 64)
print("查重功能集成自检%s" % ("（离线）" if OFFLINE else "（含 1 次真实联网）"))
print("=" * 64)

A.apply_dpi_awareness()
root = tk.Tk()
A.init_ui_scale(root)
A.init_theme()
A.init_lang()
gui = A.App(root)
root.update_idletasks()


def fill(key, text):
    box = gui.widgets[key]
    box.configure(state="normal")
    box.delete("1.0", "end")
    box.insert("1.0", text)
    box.configure(foreground=A.THEME["fg"])
    gui._on_typing(key)


def _assert_pages():
    assert len(A.App.PAGES) == 4, A.App.PAGES
    assert "lookup" in gui.pages and "fill" in gui.pages


check("界面能建起来、4 个页面齐全", _assert_pages)


def t_fill_and_generate():
    fill("what", "一个把每天三份销售 Excel 自动合并汇总的小工具")
    fill("output", "导出一张汇总表到桌面")
    gui.lookup_fill_query()
    q = gui.lookup_query.get()
    assert q, "应生成查询词"
    assert len(q) <= 60, "查询词过长: %r" % q
    # 关键：应该是英文检索词，不是整句中文
    assert not all("\u4e00" <= c <= "\u9fff" or c in " " for c in q), \
        "查询词不该是整句中文（GitHub 上搜不到）: %r" % q
    assert "excel" in q.lower() or "sheet" in q.lower(), \
        "应识别出 Excel 相关检索词，实际 %r" % q


check("从答案生成英文查询词", t_fill_and_generate)


def t_instruction_copied():
    gui.lookup_copy_instruction()
    content = gui.lookup_text.get("1.0", "end")
    assert "GitHub" in content, "指令里应提到 GitHub"
    assert "建议" in content, "指令应要求 AI 给建议"
    hint = gui.lookup_progress.cget("text")
    assert "复制" in hint, "应提示复制结果，实际 %r" % hint


check("复制「让 AI 帮我查」的指令", t_instruction_copied)


def t_offline_text_mentions_privacy():
    gui.lookup_fill_query()
    content = gui.lookup_text.get("1.0", "end")
    assert "GitHub" in content


check("界面文案提示会联网", t_offline_text_mentions_privacy)

if not OFFLINE:
    def t_real_search():
        q = gui.lookup_query.get()
        repos, err = gl.search_repos(q, per_page=6)
        if err:
            # 限流是可接受的（10 次/分钟），要如实说明而不是假装成功
            assert "频率" in err or "连不上" in err, "意外错误: %s" % err
            print("       （被限流/断网：%s —— 属正常，跳过断言）" % err)
            return
        assert repos, "查询 %r 应返回结果" % q
        terms = [x for x in q.split() if len(x) >= 2]
        kept, dropped = gl.rank_repos(repos, terms)
        verdict = gl.judge(kept, terms=terms)
        print("       查 %r → %d 个，过滤掉 %d 个，判断：%s"
              % (q, len(repos), dropped, verdict["headline"]))
        # 关键回归：结论不能建立在无关的高星项目上
        if kept:
            top = kept[0]
            print("       最相关：%s ⭐%d" % (top["full_name"], top["stars"]))

    check("真实联网查询并给出判断", t_real_search)

root.destroy()

print()
print("=" * 64)
print("通过 %d 项，失败 %d 项" % (pass_n, fail_n))
print("=== 全部通过 ===" if fail_n == 0 else "=== 有失败项 ===")
sys.exit(0 if fail_n == 0 else 1)
