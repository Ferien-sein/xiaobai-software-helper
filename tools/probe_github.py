# -*- coding: utf-8 -*-
"""真实联网探针：确认 GitHub 搜索接口在这台机器上真的能通。

自检用的是 mock，只能证明逻辑对；**接口是否可用必须真连一次**。
这个脚本手动跑，不进 CI（CI 里没网或会被限流）。

用法: python tools/probe_github.py
"""
import io
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import github_lookup as gl  # noqa: E402


def run_pipeline(query, per_page=8):
    """完整流程：搜索 → 按相关性过滤排序 → 判重。

    必须走完整流程 —— GitHub 的多词搜索是 **OR 语义**，
    搜 "excel merge tool" 会返回任何带 excel / merge / tool 之一的仓库，
    其中常有高星但与需求无关的项目。只调 judge(repos) 会被它们带偏，
    给出完全错误的「建议用现成的」（实测踩到过）。
    """
    terms = [t for t in str(query).split() if len(t) >= 2]
    repos, err = gl.search_repos(query, per_page=per_page)
    if err:
        return None, None, err, 0, 0
    kept, dropped = gl.rank_repos(repos, terms)
    verdict = gl.judge(kept, terms=terms) if kept else gl.judge([], terms=terms)
    return repos, verdict, None, len(kept), dropped


def main():
    cases = [
        "excel merge",
        "shift schedule",
    ]
    fails = 0
    for q in cases:
        print("=" * 66)
        print("查询: %r" % q)
        print("=" * 66)
        t0 = time.time()
        raw, verdict, err, kept_n, dropped = run_pipeline(q)
        dt = time.time() - t0
        if err:
            print("  ✘ 失败：%s" % err)
            fails += 1
            continue
        print("  ✔ 接口可用，返回 %d 个，过滤掉 %d 个无关的，用时 %.1f 秒"
              % (len(raw), dropped, dt))
        print("  判断：%s" % verdict["headline"])
        for r in verdict.get("reasons", []):
            print("     · " + r)
        kept, _ = gl.rank_repos(raw, [t for t in q.split() if len(t) >= 2])
        for r in (kept or raw)[:3]:
            print("     - %-38s ⭐%-7d %s %s" % (r["full_name"], r["stars"],
                                                 r["language"] or "-", r["updated"]))
        # 关键回归：结论不能建立在无关项目上
        if dropped and not kept:
            print("      （全部结果都判定为不相关 → 结论是「自己做」，符合预期）")
    print()
    print("=" * 66)
    # 顺带验证「从问卷生成查询词 → 真查一次」的完整链路
    answers = {
        "what": "一个把每天三份销售 Excel 自动合并汇总的小工具",
        "input": "每天 3 个 xlsx 文件",
        "output": "一张汇总表",
    }
    queries = gl.build_queries(answers)
    print("从问卷生成的查询词: %s" % queries)
    if queries:
        repos, err = gl.search_repos(queries[0], per_page=3)
        if err:
            print("  ✘ 用生成的词查失败：%s" % err)
            fails += 1
        else:
            print("  ✔ 用生成的词查到 %d 个" % len(repos))
            if repos:
                print("     最相关：%s ⭐%d" % (repos[0]["full_name"], repos[0]["stars"]))

    print()
    print("探针结果：%s" % ("全部通过" if not fails else "%d 项失败" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
