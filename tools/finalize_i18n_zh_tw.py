# -*- coding: utf-8 -*-
"""重建繁体语言包（最终版）。

为什么重写第三遍：我前两次都靠**手写键字符串**去补缺口，
结果三次都对不上 —— 键里少一个「本机」、漏一个前导 `\\n` 之类，
肉眼几乎看不出来，而后果是那条翻译永远不生效。

这次的做法是**不手写键**：
  1. 从 app.py 的 t() 调用点直接取出确切实参（运行期真正查表的值）
  2. 数据源里有译文就用数据源的
  3. 没有的用**完整的简→繁映射表**生成，而不是手敲
  4. 写盘前逐个断言：每个实参都能在生成结果里查到

顺带把生成逻辑里那份简繁映射抽出来复用（tools/s2t.py）。
"""
import ast
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, HERE)

from check_i18n import t_call_args, EXEMPT  # noqa: E402
from s2t import to_traditional  # noqa: E402

DATA = r"E:\APP\DeepSeek工作区\xbsh_i18n_tw_data.py"
OUT = os.path.join(SRC, "i18n_zh_tw.py")


def main():
    spec = importlib.util.spec_from_file_location("_tw_data", DATA)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    src_tr = dict(getattr(mod, "TR", {}))
    print("数据源译文: %d 条" % len(src_tr))

    statics, _ = t_call_args(os.path.join(SRC, "app.py"))
    need = sorted({a for a in statics if isinstance(a, str) and a not in EXEMPT})
    print("app.py 需要: %d 个 t() 实参" % len(need))

    # 合并：数据源优先，缺的用映射表兜底
    cat = dict(src_tr)
    filled = []
    for k in need:
        if k not in cat:
            cat[k] = to_traditional(k)
            filled.append(k)
    print("用映射表兜底补齐: %d 条" % len(filled))
    for k in filled:
        print("   + %r" % (k[:70],))

    # 关键断言：所有实参都必须能查到
    missing = [k for k in need if k not in cat]
    assert not missing, "仍有缺失: %r" % missing[:3]

    out = [
        "# -*- coding: utf-8 -*-",
        '"""繁體中文語言包。',
        "",
        "鍵 = app.py 裡的簡體中文原文（逐字一致）",
        "值 = 繁體中文譯文",
        "",
        "未收錄的條目會原樣顯示簡體 —— 漏翻不會崩，",
        "但 tools/check_i18n.py 會在發布前報出來。",
        "",
        "本檔由 tools/finalize_i18n_zh_tw.py 產生：",
        "  · 鍵直接從 app.py 的 t() 呼叫點抽出，不手寫（手寫對不上過三次）",
        "  · 收錄翻譯代理的原始譯文，缺口用 tools/s2t.py 的映射表補",
        "  · json.dumps 寫出，轉義由 json 保證",
        '"""',
        "",
        "CATALOG = {",
    ]
    for k in sorted(cat):
        out.append("    %s: %s," % (json.dumps(k, ensure_ascii=False),
                                    json.dumps(cat[k], ensure_ascii=False)))
    out.append("}")
    out.append("")
    text = "\n".join(out)

    tree = ast.parse(text)
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            n = len(node.value.keys)
    assert n == len(cat), "条目数 %d != %d" % (n, len(cat))

    io.open(OUT, "w", encoding="utf-8", newline="\n").write(text)

    # 复查：重新导入并逐个核对
    spec2 = importlib.util.spec_from_file_location("_tw_out", OUT)
    m2 = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(m2)
    still = [k for k in need if k not in m2.CATALOG]
    print()
    print("已写出 %s：%d 条，语法通过" % (os.path.basename(OUT), n))
    print("复查：需要 %d 条，缺失 %d 条" % (len(need), len(still)))
    return 0 if not still else 1


if __name__ == "__main__":
    sys.exit(main())
