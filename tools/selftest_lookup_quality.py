# -*- coding: utf-8 -*-
"""针对「查重质量」的补充自检。

这两条是真实联网探针暴露出来的问题，必须有用例守住：
  1. **高星无关项目会带偏结论** —— 实测搜 "excel merge tool" 第一名是
     一个政治话题仓库（3250 星），只看星数就会说「建议用现成的」。
  2. **中文关键词在 GitHub 上搜不到** —— 整句中文当查询词返回 0 个。

用法: python tools/selftest_lookup_quality.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import github_lookup as gl  # noqa: E402

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


def repo(name, desc, stars):
    return {"full_name": name, "description": desc, "stars": stars,
            "license": "MIT", "updated": "2026-08-01", "archived": False}


print("=" * 62)
print("相关性过滤（防止高星无关项目带偏）")
print("=" * 62)

IRRELEVANT = repo("cirosantilli/china-dictatorship", "some unrelated topic", 3250)
RELEVANT = repo("skanmera/ExcelMerge", "GUI tool to merge excel files", 847)


def t_drops_irrelevant():
    kept, dropped = gl.rank_repos([IRRELEVANT, RELEVANT], ["excel", "merge"])
    assert dropped == 1, "应丢掉 1 个无关项目，实际 %d" % dropped
    assert len(kept) == 1 and kept[0]["full_name"] == "skanmera/ExcelMerge"


check("无关的高星项目被丢掉", t_drops_irrelevant)


def t_judge_uses_relevance():
    v = gl.judge([IRRELEVANT, RELEVANT], terms=["excel", "merge"])
    # 关键：结论必须基于相关项目（847 星、在维护、MIT），而不是 3250 星的无关项
    assert "已排除" in " ".join(v["reasons"]), "应说明排除过无关项: %s" % v["reasons"]
    joined = " ".join(v["reasons"])
    assert "3250" not in joined, "不该用无关项目的星数做判断: %s" % v["reasons"]


check("判重结论基于相关项目而非无关高星项", t_judge_uses_relevance)


def t_all_irrelevant():
    v = gl.judge([IRRELEVANT], terms=["excel", "merge"])
    assert v["verdict"] == "none", "全都不相关时应判为没找到，实际 %s" % v["verdict"]
    assert "自己做" in v["headline"]


check("结果全不相关 → 判为没找到、建议自己做", t_all_irrelevant)


def t_no_terms_keeps_all():
    kept, dropped = gl.rank_repos([IRRELEVANT, RELEVANT], [])
    assert dropped == 0, "没给关键词时不该过滤"


check("不给关键词时不过滤（向后兼容）", t_no_terms_keeps_all)


def t_relevance_prefers_related_over_stars():
    # 两个都相关时，星数多的在前
    a = repo("x/small-excel-merge", "excel merge tool", 10)
    b = repo("y/big-excel-merge", "excel merge tool", 999)
    kept, _ = gl.rank_repos([a, b], ["excel", "merge"])
    assert kept[0]["full_name"] == "y/big-excel-merge", "同等相关时星多的应在前"


check("同等相关时按星数排序", t_relevance_prefers_related_over_stars)

print()
print("=" * 62)
print("中文查询词 → GitHub 可搜的英文词")
print("=" * 62)


def t_en_query_excel():
    q, hits = gl.to_search_query("把每天三份销售 Excel 自动合并汇总的小工具")
    assert "excel" in q.lower() or "spreadsheet" in q.lower(), "应映射到 excel 相关词，实际 %r" % q
    assert hits, "应报告命中的中文词"


check("Excel 汇总 → 英文检索词", t_en_query_excel)


def t_en_query_various():
    cases = [
        ("帮我做个记账小工具记录每天花销", ("expense", "finance")),
        ("排班表生成，统计每人班次", ("shift", "schedul", "roster")),
        ("算工资和加班费", ("payroll", "overtime", "attendance")),
        ("两个表对账找差异", ("reconcil", "compare")),
        ("批量重命名整理文件", ("file", "rename", "organiz")),
    ]
    for text, wants in cases:
        q, hits = gl.to_search_query(text)
        low = q.lower()
        assert any(w in low for w in wants), "「%s」应映射到 %s 之一，实际 %r" % (text, wants, q)


check("记账/排班/工资/对账/文件整理 都能映射", t_en_query_various)


def t_en_query_fallback():
    q, hits = gl.to_search_query("一个很冷门的需求")
    assert q == "一个很冷门的需求", "没命中映射时应原样返回，实际 %r" % q
    assert hits == []


check("没有映射时原样返回（不编造）", t_en_query_fallback)


def t_build_queries_not_whole_sentence():
    a = {"what": "一个把每天三份销售 Excel 自动合并汇总的小工具"}
    q = gl.build_queries(a)
    # 关键回归：不能再出现「整句中文当一个词」
    for item in q:
        assert len(item) <= 40, "查询词过长，像是整句没切开: %r" % item
    joined = " ".join(q)
    assert "Excel" in joined, "应保留 Excel 这种关键信息: %s" % q


check("查询词不会把整句中文当一个词", t_build_queries_not_whole_sentence)

print()
print("=" * 62)
print("通过 %d 项，失败 %d 项" % (pass_n, fail_n))
print("=== 全部通过 ===" if fail_n == 0 else "=== 有失败项 ===")
sys.exit(0 if fail_n == 0 else 1)
