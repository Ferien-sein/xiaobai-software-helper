# -*- coding: utf-8 -*-
"""从代理保留的原始数据源重建繁体语言包。

为什么需要重建：我上一个补丁脚本把 i18n_zh_tw.py 的尾部写坏了
（少了字典收尾的 `}`、注释插进了键值对中间），容错抢救只找回 100 条，
另外 220 多条译文丢了。

好在翻译代理把**原始译文数据**留在了
  E:\\APP\\DeepSeek工作区\\xbsh_i18n_tw_data.py
形式是 TR["简体原文"] = "繁體譯文" 的赋值语句 —— 导入即可拿到全部。

这个脚本：
  1. 导入数据源，拿到全部繁体译文
  2. 与 app.py 里 t() 的实参核对，列出缺口
  3. 用 json.dumps 重新生成 i18n_zh_tw.py（转义交给 json，杜绝手写出错）
  4. 写盘前做语法 + 条目数校验
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

DATA = r"E:\APP\DeepSeek工作区\xbsh_i18n_tw_data.py"
OUT = os.path.join(SRC, "i18n_zh_tw.py")


def load_tr():
    spec = importlib.util.spec_from_file_location("_xbsh_tw_data", DATA)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tr = dict(getattr(mod, "TR", {}))
    return tr


def main():
    if not os.path.exists(DATA):
        print("找不到数据源: %s" % DATA)
        return 1

    tr = load_tr()
    print("数据源里的译文: %d 条" % len(tr))

    statics, _ = t_call_args(os.path.join(SRC, "app.py"))
    need = sorted({a for a in statics if isinstance(a, str) and a not in EXEMPT})
    print("app.py 需要的 t() 实参: %d 个" % len(need))

    missing = [k for k in need if k not in tr]
    print("数据源缺少: %d 条" % len(missing))
    for k in missing:
        print("   缺 %r" % (k[:78],))

    # 数据源可能多于当前需要的（比如旧文案），都保留但标注
    extra = [k for k in tr if k not in need]
    print("数据源里当前用不到的: %d 条（保留，可能以后用得上）" % len(extra))

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
        "本檔由 tools/rebuild_i18n_zh_tw.py 從原始譯文資料重建",
        "（json.dumps 產生，轉義由 json 保證），請勿手改縮排。",
        '"""',
        "",
        "CATALOG = {",
    ]
    for k in sorted(tr):
        out.append("    %s: %s," % (json.dumps(k, ensure_ascii=False),
                                    json.dumps(tr[k], ensure_ascii=False)))
    out.append("}")
    out.append("")
    text = "\n".join(out)

    tree = ast.parse(text)          # 语法不过就不写盘
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            n = len(node.value.keys)
    assert n == len(tr), "条目数不符 %d != %d" % (n, len(tr))

    io.open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print()
    print("已重建 %s：%d 条，语法通过" % (os.path.basename(OUT), n))

    # 复查：需要的键是否都能查到
    spec = importlib.util.spec_from_file_location("_tw", OUT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cat = mod.CATALOG
    still = [k for k in need if k not in cat]
    print("重建后仍缺: %d 条 %s" % (len(still), still[:5]))
    return 0 if not still else 1


if __name__ == "__main__":
    sys.exit(main())
