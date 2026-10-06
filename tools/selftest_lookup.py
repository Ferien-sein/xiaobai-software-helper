# -*- coding: utf-8 -*-
"""先查查模块的自检。

用 mock 的 opener 模拟 GitHub 返回，**不需要联网也能跑**，
这样才能在 CI 或没网的环境里验证逻辑。

真实联网另有一个脚本 tools/probe_github.py（手动跑，看接口是否真能用）。

用法: python tools/selftest_lookup.py
"""

import os
# ★ 锁定界面语言（XBSH_LANG_LOCKED）：这些检查/自检脚本的输出与断言都基于简体中文，
#   而 i18n 会按系统区域自动探测语言 —— 在英文机器 / CI 上会探测成英文，
#   断言就全挂（GitHub runner 上真踩过：selftest_platform 11 项失败）。
#   ★ 用 = 不用 setdefault：环境里已有 XBSH_LANG 时 setdefault 不覆盖，锁会失效。
#   插在第一个模块级 import 之前，保证任何依赖 i18n 的 import 都在它之后。
os.environ["XBSH_LANG"] = "zh-CN"

import io
import json
import os
import sys
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import github_lookup as gl  # noqa: E402

pass_n = fail_n = 0
failures = []


def check(name, fn):
    global pass_n, fail_n
    try:
        fn()
        pass_n += 1
        print("  OK   %s" % name)
    except AssertionError as e:
        fail_n += 1
        failures.append((name, str(e)))
        print("  FAIL %s\n       %s" % (name, e))
    except Exception as e:  # noqa: BLE001
        fail_n += 1
        failures.append((name, repr(e)))
        print("  FAIL %s\n       %r" % (name, e))


class FakeResp:
    def __init__(self, payload, status=200):
        self._data = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener_returning(payload):
    def op(req, timeout=None):
        return FakeResp(payload)
    return op


def opener_raising(exc):
    def op(req, timeout=None):
        raise exc
    return op


def fake_repo(name="owner/repo", stars=500, updated="2026-01-01",
              license_="MIT", archived=False, desc="一个很有用的工具"):
    # ★ 注意用 pushed_at：GitHub 返回的是这个字段，search_repos 也是读它。
    #   我第一次写成 updated，search_repos 里 it.get("pushed_at") 取到 None，
    #   结果 judge() 拿不到日期 —— 测试自己错了，不是模块的问题。
    return {
        "full_name": name,
        "html_url": "https://github.com/" + name,
        "description": desc,
        "stargazers_count": stars,
        "language": "Python",
        "license": {"spdx_id": license_},
        "pushed_at": updated,
        "updated_at": updated,
        "archived": archived,
        "open_issues_count": 3,
    }


print("=" * 64)
print("关键词生成")
print("=" * 64)


def t_queries_basic():
    a = {"what": "一个帮我把三份 Excel 合并的小工具", "input": "xlsx 文件", "output": "汇总表"}
    q = gl.build_queries(a)
    assert q, "应生成查询词"
    assert len(q) <= 6, "最多 6 条，实际 %d" % len(q)
    assert len(set(q)) == len(q), "不应重复: %s" % q
    # 组合那条应排在最前
    assert " " in q[0] or len(q) == 1, "第一条应是组合词: %r" % q[0]


check("从问卷生成查询词、去重、有上限", t_queries_basic)


def t_queries_empty():
    assert gl.build_queries({}) == [], "空答案应返回空列表"
    assert gl.build_queries({"what": "", "input": None}) == []


check("空答案不崩、返回空", t_queries_empty)


def t_queries_strip_punct():
    q = gl.build_queries({"what": "帮我做一个（很简单的）Excel、合并工具！"})
    joined = " ".join(q)
    for bad in "，。、；：！？（）":
        assert bad not in joined, "标点未清理: %r" % joined


check("查询词里不留标点", t_queries_strip_punct)

print()
print("=" * 64)
print("搜索与错误处理")
print("=" * 64)


def t_search_ok():
    op = opener_returning({"items": [fake_repo(), fake_repo("a/b", stars=10)]})
    repos, err = gl.search_repos("excel merge", opener=op)
    assert err is None, "不该报错: %r" % err
    assert len(repos) == 2
    r = repos[0]
    for k in ("full_name", "url", "stars", "license", "updated", "archived", "language"):
        assert k in r, "缺少字段 " + k
    assert r["full_name"] == "owner/repo"
    assert r["stars"] == 500
    assert r["license"] == "MIT"


check("正常返回时字段齐全", t_search_ok)


def t_search_empty_query():
    repos, err = gl.search_repos("")
    assert repos == []
    assert err and "空" in err


check("空查询词给出明确提示", t_search_empty_query)


def t_search_rate_limit():
    e = urllib.error.HTTPError("u", 403, "rate", {}, io.BytesIO(b""))
    repos, err = gl.search_repos("x", opener=opener_raising(e))
    assert repos == []
    assert "频率" in (err or ""), "403 应提示频率限制，实际 %r" % err


check("403 提示查询频率限制", t_search_rate_limit)


def t_search_offline():
    e = urllib.error.URLError("no network")
    repos, err = gl.search_repos("x", opener=opener_raising(e))
    assert repos == []
    assert "连不上" in (err or ""), "断网应给出人话提示，实际 %r" % err
    assert "让 AI 帮你查" in (err or ""), "断网时应引导到离线方案"


check("断网时提示改用「让 AI 帮你查」", t_search_offline)


def t_search_bad_payload():
    repos, err = gl.search_repos("x", opener=opener_returning({"items": None}))
    assert repos == [] and err is None, "items 为空应正常返回空列表"


check("items 为空不崩", t_search_bad_payload)


def t_search_weird_http():
    e = urllib.error.HTTPError("u", 422, "unprocessable", {}, io.BytesIO(b""))
    repos, err = gl.search_repos("x", opener=opener_raising(e))
    assert "不接受" in (err or ""), "422 应有专门提示，实际 %r" % err


check("422 有专门提示", t_search_weird_http)

print()
print("=" * 64)
print("判断逻辑")
print("=" * 64)


def t_judge_none():
    v = gl.judge([])
    assert v["verdict"] == "none"
    assert "自己做" in v["headline"]


check("没找到 → 建议自己做", t_judge_none)


def t_judge_reuse():
    # 星数高 + 近期更新 + 有许可证 → 建议用现成
    v = gl.judge([fake_repo(stars=800, updated="2026-08-01", license_="MIT")])
    assert v["verdict"] == "reuse", "应建议复用，实际 %s（%s）" % (v["verdict"], v["reasons"])
    assert v["reasons"], "应给出理由"


check("星数高 + 在维护 + 有许可证 → 建议用现成", t_judge_reuse)


def t_judge_archived_warns():
    v = gl.judge([fake_repo(stars=5000, updated="2026-08-01", archived=True)])
    assert any("归档" in r for r in v["reasons"]), "应提示已归档: %s" % v["reasons"]
    assert v["verdict"] != "reuse", "已归档不该直接建议复用，实际 %s" % v["verdict"]


check("已归档时给出警告且不直接建议复用", t_judge_archived_warns)


def t_judge_stale_warns():
    v = gl.judge([fake_repo(stars=900, updated="2019-01-01")])
    assert any("没更新" in r for r in v["reasons"]), "应提示久未更新: %s" % v["reasons"]
    assert v["verdict"] != "reuse"


check("长期未更新时给警告", t_judge_stale_warns)


def t_judge_low_stars():
    v = gl.judge([fake_repo(stars=2, updated="2026-08-01", license_="MIT")])
    assert v["verdict"] in ("build", "compare"), "星数很低不该建议复用，实际 %s" % v["verdict"]
    assert any("星数" in r for r in v["reasons"])


check("星数很低 → 不建议复用", t_judge_low_stars)


def t_judge_no_license_warns():
    v = gl.judge([fake_repo(stars=900, updated="2026-08-01", license_="")])
    assert any("许可证" in r for r in v["reasons"]), "应提示许可证不明: %s" % v["reasons"]


check("未标注许可证时给提醒", t_judge_no_license_warns)


def t_judge_bad_date():
    v = gl.judge([fake_repo(updated="")])
    assert v["verdict"], "日期缺失也不该崩"


check("日期缺失不崩", t_judge_bad_date)

print()
print("=" * 64)
print("输出与离线回退")
print("=" * 64)


def t_report():
    repos, _ = gl.search_repos("x", opener=opener_returning({"items": [fake_repo()]}))
    v = gl.judge(repos)
    text = gl.format_report(repos, v)
    assert "判断" in text and "找到 1 个" in text
    assert "owner/repo" in text
    assert "https://github.com/owner/repo" in text
    # 星数、更新时间、许可证都要出现
    assert "500" in text and "2026-01-01" in text and "MIT" in text


check("报告含判断、项目名、链接、星数、时间、许可证", t_report)


def t_report_empty():
    assert "没有找到" in gl.format_report([])


check("空结果报告不崩", t_report_empty)


def t_ai_instruction():
    text = gl.build_ai_instruction(["excel 合并", "汇总表"])
    assert "GitHub" in text
    assert "excel 合并" in text and "汇总表" in text
    # 必须要求给建议、而不是只丢链接
    assert "建议" in text, "应要求给出明确建议"
    assert "星数" in text and "许可证" in text, "应要求给出星数/许可证"
    assert "一步步" in text, "应要求一步步教怎么用（用户不懂技术）"


check("离线指令包含关键词并要求给建议与用法", t_ai_instruction)


def t_ai_instruction_empty():
    text = gl.build_ai_instruction([])
    assert text and "GitHub" in text, "没关键词时也要能用"


check("没有关键词时离线指令仍可用", t_ai_instruction_empty)

print()
print("=" * 64)
print("通过 %d 项，失败 %d 项" % (pass_n, fail_n))
if failures:
    print("\n失败详情：")
    for n, m in failures:
        print("  %s\n    %s" % (n, m))
print("=== 全部通过 ===" if fail_n == 0 else "=== 有失败项 ===")
sys.exit(0 if fail_n == 0 else 1)
