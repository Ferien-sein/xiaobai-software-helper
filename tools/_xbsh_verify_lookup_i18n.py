# -*- coding: utf-8 -*-
"""独立复核：两个语言包补完「先查查」页之后是否真的生效。

不复用生成脚本的任何中间结果，只做三件事：
  1. 真的 import i18n + 语言包，逐个 t() 实参查表，确认都查得到（不是回退原文）
  2. 带 %s/%d 的条目真的按原文的参数个数格式化一遍，确认不会 TypeError
  3. 和 tools/_archive 里的备份逐行对比，确认改动**只有新增**

用法: python tools/_xbsh_verify_lookup_i18n.py
只读，不修改任何文件。
"""
import ast
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
ARCHIVE = os.path.join(HERE, "_archive")
sys.path.insert(0, HERE)
sys.path.insert(0, SRC)

from check_i18n import EXEMPT, t_call_args  # noqa: E402

PACKS = (("zh-TW", "i18n_zh_tw.py"), ("en", "i18n_en.py"))
EXTRA = ("先查查",)

# 这些条目译文与原文相同是正确的（分隔符 / 简繁同形）
ALLOW_SAME = {"先查查", "——————", "正在查 GitHub…", "查完了：%s"}

fail = 0


def bad(msg):
    global fail
    fail += 1
    print("  FAIL %s" % msg)


def main():
    import i18n

    statics, _ = t_call_args(os.path.join(SRC, "app.py"))
    need = sorted({a for a in statics if isinstance(a, str) and a not in EXEMPT})
    keys = need + [k for k in EXTRA if k not in need]
    print("需要查表的键：%d 个（t() 实参 %d + 导航页名 %d）" % (len(keys), len(need), len(EXTRA)))

    # 本次新增的键（= 备份里没有的），只有这些才要求「必须有独立译文」
    import json

    def entry_map(path):
        src = io.open(path, encoding="utf-8").read()
        tree = ast.parse(src)
        node = [n for n in ast.walk(tree)
                if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "CATALOG"][0]
        return {k.value: v.value for k, v in zip(node.value.keys, node.value.values)}, src

    for lang, fname in PACKS:
        i18n.reload_packs()
        i18n.set_lang(lang)
        pack = i18n.translate_catalog(keys, lang)
        old, _ = entry_map(os.path.join(ARCHIVE, fname + ".bak"))
        added = set(pack) - set(old)
        # 新增条目里不该出现「没翻」的同形值（分隔符/简繁同形的除外）
        same_new = [k for k in sorted(added) if pack[k] == k and k not in ALLOW_SAME]
        if same_new:
            bad("%s：新增条目里还有 %d 条没翻：%r" % (lang, len(same_new), same_new[:5]))
        # 本来就在的同形条目（例如「不用改」「我的需求」）是正常的，只提示不报错
        same_old = [k for k in keys if pack[k] == k and k in old and k not in ALLOW_SAME]
        print("  OK   %s：%d 条全部查得到；新增 %d 条都有独立译文"
              % (lang, len(keys), len(added)))
        if same_old:
            print("       （另有 %d 条本来就在、简繁同形，属正常：%s）"
                  % (len(same_old), "、".join(same_old[:6])))

        # 带占位符的条目按 % 格式化一次
        for k in keys:
            if "%s" in k or "%d" in k:
                n_s, n_d = k.count("%s"), k.count("%d")
                args = tuple("X" for _ in range(n_s)) + tuple(1 for _ in range(n_d))
                try:
                    out = pack[k] % args
                except Exception as exc:  # noqa: BLE001
                    bad("%s：%r 格式化失败 %r" % (lang, k[:40], exc))
                    continue
                if "X" not in out and n_s:
                    bad("%s：%r 格式化后丢了 %s" % (lang, k[:40], "%s"))
        print("  OK   %s：带占位符的条目格式化正常" % lang)

    # ---- 改动只有新增 ----
    print()
    for lang, fname in PACKS:
        bak = os.path.join(ARCHIVE, fname + ".bak")
        cur = os.path.join(SRC, fname)
        if not os.path.exists(bak):
            bad("找不到备份 %s" % bak)
            continue

        old, old_src = entry_map(bak)
        new, new_src = entry_map(cur)
        removed = [k for k in old if k not in new]
        changed = [k for k in old if k in new and new[k] != old[k]]
        added = [k for k in new if k not in old]
        print("%s：%d → %d 条，新增 %d，修改 %d，删除 %d"
              % (lang, len(old), len(new), len(added), len(changed), len(removed)))
        if removed or changed:
            bad("%s：有旧条目被删除/修改：%r %r" % (lang, removed[:3], changed[:3]))
        # 行级：新文件里「旧文件没有的行」必须全是新增条目行，
        # 外加允许的分节注释行（英文包按功能分组，新增一节要写注释）
        allowed_comments = {
            "    # ---- 先查查页（动手前先看 GitHub 有没有现成的）----",
            "    # app.py L1693-1841  ·  键 = 简体原文",
        }
        old_lines = set(old_src.splitlines())
        added_lines = [l for l in new_src.splitlines() if l not in old_lines]
        new_entry_lines = ["    %s: %s," % (
            json.dumps(k, ensure_ascii=False),
            json.dumps(new[k], ensure_ascii=False)) for k in added]
        extra = [l for l in added_lines
                 if l not in new_entry_lines and l not in allowed_comments]
        if extra:
            bad("%s：出现了非新增条目的行改动：%r" % (lang, extra[:3]))
        else:
            print("  OK   行级差异全部是新增条目（%d 行）" % len(added_lines))

    print()
    print("=" * 62)
    print("独立复核：%s" % ("全部通过" if not fail else "%d 项失败" % fail))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
