# -*- coding: utf-8 -*-
"""辅助脚本：导出语言包缺失条目（供本次补词使用）。

用法: python tools/_xbsh_dump_missing.py [out.json]
仅读取，不修改任何语言包。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from check_i18n import catalog_of, t_call_args  # noqa: E402

SRC = os.path.join(ROOT, "src")
EXEMPT = {
    "需求存档", "使用说明.txt", "提示词模板.txt", "显示诊断.txt",
    "===== 原始答案（给程序自己看，不用管） =====", "===== 原始答案结束 =====",
    "小白造软件助手", "微软雅黑", "zh-CN", "zh-TW", "en",
}


def main():
    statics, fstrings = t_call_args(os.path.join(SRC, "app.py"))
    const_args = [a for a in statics if isinstance(a, str) and a not in EXEMPT]
    uniq = sorted(set(const_args))

    out = {"total_unique": len(uniq), "packs": {}}
    for lang, fname in (("zh-TW", "i18n_zh_tw.py"), ("en", "i18n_en.py")):
        cat, err = catalog_of(os.path.join(SRC, fname))
        missing = [k for k in uniq if k not in cat]
        out["packs"][lang] = {"file": fname, "entries": len(cat), "missing": missing}

    text = json.dumps(out, ensure_ascii=False, indent=2)
    print(text)
    if len(sys.argv) > 1:
        with io.open(sys.argv[1], "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
