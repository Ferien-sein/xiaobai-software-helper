# -*- coding: utf-8 -*-
"""把 github_lookup.py 里的用户可见文案包上 _()（翻译钩子）。

为什么用脚本 + 精确映射：
  手改 20 多处容易漏；正则批量包又会碰坏 f-string 或嵌套引号。
  这里列出每一处「原文 → 改写后」，逐条替换，写盘前 ast.parse，坏了回滚。

注意 f-string：_() 里的字符串**不能是 f-string**（插值后就查不到表了，
这是本项目踩过的坑）。所以 f"..." 要改写成 _("...") % (...) 或 _("...").format()。
"""
import io
import os
import py_compile
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PATH = os.path.join(ROOT, "src", "github_lookup.py")

REPL = [
    # ---- search_repos 的错误文案 ----
    ('return [], "查询词是空的"',
     'return [], _("查询词是空的")'),
    ('return [], "GitHub 限制了查询频率（每小时 10 次左右），请过一会儿再试"',
     'return [], _("GitHub 限制了查询频率（每小时 10 次左右），请过一会儿再试")'),
    ('return [], "查询词 GitHub 不接受，换个更简单的说法再试"',
     'return [], _("查询词 GitHub 不接受，换个更简单的说法再试")'),
    ('return [], "GitHub 返回错误 %s" % e.code',
     'return [], _("GitHub 返回错误 %s") % e.code'),
    ('return [], "连不上 GitHub（%s）。可以先用下面的「让 AI 帮你查」" % (e.reason,)',
     'return [], _("连不上 GitHub（%s）。可以先用下面的「让 AI 帮你查」") % (e.reason,)'),
    ('return [], "查询失败：%r" % (e,)',
     'return [], _("查询失败：%r") % (e,)'),

    # ---- judge() 的理由与结论 ----
    ('reasons.append("（有 %d 个搜索结果与你的需求明显无关，已排除 —— "\n                       "GitHub 按星数排时经常把无关的高星项目排在最前）" % dropped)',
     'reasons.append(_("（有 %d 个搜索结果与你的需求明显无关，已排除 —— "\n                         "GitHub 按星数排时经常把无关的高星项目排在最前）") % dropped)'),
    ('"headline": "没找到现成的，可以自己做",',
     '"headline": _("没找到现成的，可以自己做"),'),
    ('reasons.append("最相关的项目有 %d 颗星，说明用的人不少" % stars)',
     'reasons.append(_("最相关的项目有 %d 颗星，说明用的人不少") % stars)'),
    ('reasons.append("最相关的项目有 %d 颗星，有一定使用量" % stars)',
     'reasons.append(_("最相关的项目有 %d 颗星，有一定使用量") % stars)'),
    ('reasons.append("星数都不高（最高 %d），可能没有成熟方案" % stars)',
     'reasons.append(_("星数都不高（最高 %d），可能没有成熟方案") % stars)'),
    ('reasons.append("⚠️ 但该项目已归档，作者不再维护")',
     'reasons.append(_("⚠️ 但该项目已归档，作者不再维护"))'),
    ('reasons.append("⚠️ 而且已 %d 个月没更新，要留意是否还适用" % (days // 30))',
     'reasons.append(_("⚠️ 而且已 %d 个月没更新，要留意是否还适用") % (days // 30))'),
    ('reasons.append("最近还有更新（%s），看来仍在维护" % updated)',
     'reasons.append(_("最近还有更新（%s），看来仍在维护") % updated)'),
    ('reasons.append("❓ 没写清楚开源许可证，商用前要确认")',
     'reasons.append(_("❓ 没写清楚开源许可证，商用前要确认"))'),
    ('reasons.append("许可证是 %s" % license_)',
     'reasons.append(_("许可证是 %s") % license_)'),

    # ---- format_report ----
    ('return "没有找到相关项目。"',
     'return _("没有找到相关项目。")'),
    ('lines.append("【判断】" + verdict["headline"])',
     'lines.append(_("【判断】") + verdict["headline"])'),
    ('lines.append("找到 %d 个相关项目（按星数排序）：" % len(repos))',
     'lines.append(_("找到 %d 个相关项目（按星数排序）：") % len(repos))'),
]


def compile_ok(path):
    try:
        with tempfile.TemporaryDirectory() as td:
            py_compile.compile(path, cfile=os.path.join(td, "x.pyc"), doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)


def main():
    src = io.open(PATH, encoding="utf-8", newline=None).read()
    backup = src
    applied, missing, already = 0, [], 0
    for old, new in REPL:
        if new in src and old not in src:
            already += 1
            continue
        if old not in src:
            missing.append(old[:70])
            continue
        src = src.replace(old, new, 1)
        applied += 1

    if src == backup:
        print("没有需要改的地方（already=%d missing=%d）" % (already, len(missing)))
        for m in missing:
            print("  找不到: %s" % m)
        return 1 if missing else 0

    io.open(PATH, "w", encoding="utf-8", newline="\n").write(src)
    ok, err = compile_ok(PATH)
    if not ok:
        io.open(PATH, "w", encoding="utf-8", newline="\n").write(backup)
        print("✘ 语法错误，已回滚: %s" % (err or "").split("\n")[0])
        return 1

    print("已包 _() 共 %d 处（已是 %d 处）" % (applied, already))
    if missing:
        print("以下 %d 处没匹配到：") if False else print("以下 %d 处没匹配到：" % len(missing))
        for m in missing:
            print("   %s" % m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
