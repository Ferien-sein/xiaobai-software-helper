# -*- coding: utf-8 -*-
"""补充「先查查」页（GitHub 查重）在繁中 / 英文语言包里的缺失条目。

为什么用脚本而不是手写进语言包：
  键必须和 app.py 里 t(...) 的实参**逐字一致**（含 \\n、%s、%d、全角标点、emoji）。
  手写三次都对不上，所以这里：
    · 键的来源是 check_i18n.py 自己抽出来的「缺失清单」，不是我敲的
    · 译文来自 tools/_xbsh_lookup_i18n_data.py
    · 写盘前逐条断言：占位符签名一致、换行数一致、繁中值里没有简体专用字
    · 整份文件用 json.dumps 生成，转义由 json 保证
    · ast.parse 通过、条目数对得上、旧条目一条不少，才允许写盘

用法:
  python tools/_xbsh_add_lookup_i18n.py            # 只检查并打印计划，不写盘
  python tools/_xbsh_add_lookup_i18n.py --write    # 通过全部断言后写盘（先备份）

不改 src/app.py，只改两个语言包。辅助脚本，可随时删除。
"""
import ast
import io
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
ARCHIVE = os.path.join(HERE, "_archive")
sys.path.insert(0, HERE)

from check_i18n import EXEMPT, catalog_of, t_call_args  # noqa: E402

DATA = os.path.join(HERE, "_xbsh_lookup_i18n_data.json")
DATA_PY = os.path.join(HERE, "_xbsh_lookup_i18n_data.py")
PACKS = (("zh-TW", "i18n_zh_tw.py"), ("en", "i18n_en.py"))

# 页名「先查查」是在 t(name) 里查表的（实参是变量），check_i18n.py 看不见，
# 但它是界面上的导航文字，漏了就会显示简体。
EXTRA_RUNTIME_KEYS = ("先查查",)

# 这些条目「译文 == 原文」是正确的（分隔符 / 简繁同形），不是漏翻
ALLOW_SAME_AS_KEY = {"先查查", "——————", "正在查 GitHub…", "查完了：%s"}

# 繁中译文里不该出现的简体专用字。
# 先程序化地从 s2t.S2T 取「简繁不同形」的字，再补上映射表没收录的那些
# （映射表只收一对一安全的常用字，缺口不少）。
MANUAL_SIMPLIFIED_ONLY = (
    "没话让帮词询么两页来给并评对题项专开数无们东许证链结论观号继续"
    "软动现经劳从这么钮会联网发这线写个关键录办与时结断连点里说条"
)


def simplified_only_chars():
    bad = set(MANUAL_SIMPLIFIED_ONLY)
    try:
        from s2t import S2T
        for s, t in S2T.items():
            if s != t:
                bad.update(s)
    except Exception as exc:  # noqa: BLE001
        print("  (提示：没能载入 s2t.S2T，只用内置字表：%r)" % (exc,))
    return bad


def fmt_sig(text):
    """%s/%d/%% 的签名（顺序敏感）与换行个数。"""
    placeholders = []
    i = 0
    while i < len(text):
        if text[i] == "%" and i + 1 < len(text) and text[i + 1] in "sd%":
            placeholders.append(text[i:i + 2])
            i += 2
        else:
            i += 1
    return tuple(placeholders), text.count("\n")


def load_state():
    """当前两个语言包的内容（保持文件里的顺序）。"""
    state = {}
    for lang, fname in PACKS:
        path = os.path.join(SRC, fname)
        src = io.open(path, encoding="utf-8").read()
        pair_map, err = catalog_of(path)
        if err:
            raise SystemExit("语言包有问题：%s → %s" % (fname, err))
        tree = ast.parse(src)
        node = [n for n in ast.walk(tree)
                if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "CATALOG"][0]
        ordered = [(k.value, v.value) for k, v in zip(node.value.keys, node.value.values)]
        state[lang] = {"path": path, "src": src, "pairs": ordered,
                       "keys": [k for k, _ in ordered], "map": pair_map}
    return state


def authoritative_keys():
    statics, fstrings = t_call_args(os.path.join(SRC, "app.py"))
    if fstrings:
        raise SystemExit("app.py 里还有 f-string 实参的 t() 调用点：L%s" % fstrings)
    const = {a for a in statics if isinstance(a, str) and a not in EXEMPT}
    return const


def load_data():
    """译文数据。优先读 .py 数据模块（和本仓库 xbsh_i18n_tw_data.py 的做法一致），
    没有才读 .json。两个都是「辅助数据文件」，不参与程序运行。"""
    if os.path.exists(DATA_PY):
        tree = ast.parse(io.open(DATA_PY, encoding="utf-8").read())
        node = [n for n in tree.body
                if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "TR"]
        if not node:
            raise SystemExit("%s 里找不到 TR" % DATA_PY)
        data = ast.literal_eval(node[0].value)
    else:
        data = json.load(io.open(DATA, encoding="utf-8"))
    data.pop("_note", None)
    return data


def emit_data_py():
    """把 .json 数据源机械转成 .py 数据模块（JSON 的对象语法就是 Python 的 dict 语法，
    所以 json.dumps 的结果可以直接当 Python 常量读，转义也由 json 保证）。"""
    data = json.load(io.open(DATA, encoding="utf-8"))
    body = (
        "# -*- coding: utf-8 -*-\n"
        '"""「先查查」页新增条目的译文数据源（辅助文件，不参与程序运行）。\n\n'
        "键 = app.py 里的简体原文（逐字一致）；值 = 译文。\n"
        "由 tools/_xbsh_add_lookup_i18n.py --emit-data-py 从 .json 机械生成，\n"
        "转义由 json.dumps 保证，不要手写。\n"
        '"""\n\n'
        "TR = " + json.dumps(data, ensure_ascii=False, indent=4) + "\n"
    )
    ast.parse(body)  # 语法必须能过
    io.open(DATA_PY, "w", encoding="utf-8", newline="\n").write(body)
    print("已生成 %s（%d 条 × %d 语言）"
          % (os.path.relpath(DATA_PY, ROOT),
             len(data["zh-TW"]), len([k for k in data if k != "_note"])))
    return 0


def main():
    write = "--write" in sys.argv
    if "--emit-data-py" in sys.argv:
        return emit_data_py()
    data = load_data()
    state = load_state()
    need = authoritative_keys()

    print("app.py 的 t() 字符串实参（去重）：%d 个" % len(need))
    print()

    plan = {}
    for lang, fname in PACKS:
        have = state[lang]["map"]
        missing = sorted(k for k in need if k not in have)
        want = set(missing) | set(EXTRA_RUNTIME_KEYS)
        got = set(data[lang])
        if got != want:
            raise SystemExit("%s 的数据文件对不上：多 %r / 少 %r"
                             % (lang, sorted(got - want), sorted(want - got)))
        plan[lang] = missing
        print("%s: 缺失 %d 条 + 导航页名 %d 条 = 待补 %d 条"
              % (lang, len(missing), len(EXTRA_RUNTIME_KEYS), len(got)))

    # ---- 逐条校验译文 ----
    print()
    print("校验译文：")
    bad = simplified_only_chars()
    for lang, fname in PACKS:
        for key in sorted(data[lang]):
            val = data[lang][key]
            kp, kn = fmt_sig(key)
            vp, vn = fmt_sig(val)
            if kp != vp:
                raise SystemExit("[%s] 占位符不一致：%r → %r（%r vs %r）"
                                 % (lang, key, val, kp, vp))
            if kn != vn:
                raise SystemExit("[%s] 换行数不一致（%d vs %d）：%r"
                                 % (lang, kn, vn, key[:60]))
            if not val.strip():
                raise SystemExit("[%s] 译文是空的：%r" % (lang, key))
            if val == key and key not in ALLOW_SAME_AS_KEY:
                raise SystemExit("[%s] 译文和原文一样（疑似漏翻）：%r" % (lang, key))
            if lang == "zh-TW":
                hit = sorted({c for c in val if c in bad})
                if hit:
                    raise SystemExit("[%s] 译文里还有简体专用字 %s：%r"
                                     % (lang, "".join(hit), key[:60]))
        print("  %s  %d 条：占位符/换行/未漏翻/无简体残留 全部通过" % (lang, len(data[lang])))

    # ---- 生成新文件内容 ----
    print()
    output = {}
    for lang, fname in PACKS:
        st = state[lang]
        old_keys = st["keys"]
        merged = dict(st["pairs"])
        for key, val in data[lang].items():
            merged[key] = val
        new_keys = sorted(merged)
        if len(new_keys) != len(old_keys) + len(data[lang]):
            raise SystemExit("%s 条目数不对" % lang)

        if lang == "zh-TW":
            # 繁中包本来就是「按码点排序的扁平表」，而且是 sorted 重排后逐字节可复现的。
            # 所以整份重排，保证 diff 只有新增行。
            prefix = st["src"].split("CATALOG = {", 1)[0] + "CATALOG = {\n"
            rebuilt = prefix + "\n".join(
                "    %s: %s," % (json.dumps(k, ensure_ascii=False),
                                json.dumps(merged[k], ensure_ascii=False))
                for k in new_keys) + "\n}\n"
            old_expected = prefix + "\n".join(
                "    %s: %s," % (json.dumps(k, ensure_ascii=False),
                                json.dumps(merged[k], ensure_ascii=False))
                for k in old_keys) + "\n}\n"
            if old_expected != st["src"]:
                raise SystemExit("繁中包重排后与原文件不一致 —— 格式变了，停手")
            new_src = rebuilt
        else:
            # 英文包是按功能分组的、带注释的表，不能整份重排（会丢注释）。
            # 只在末尾插一节新条目，原有内容一个字节都不动。
            head, sep, tail = st["src"].rpartition("\n}\n")
            if not sep:
                raise SystemExit("英文包结尾不是 \\n}\\n，停手")
            lines = ["", "    # ---- 先查查页（动手前先看 GitHub 有没有现成的）----",
                     "    # app.py L1693-1841  ·  键 = 简体原文"]
            for key, val in data[lang].items():
                lines.append("    %s: %s," % (json.dumps(key, ensure_ascii=False),
                                              json.dumps(val, ensure_ascii=False)))
            new_src = head + "\n" + "\n".join(lines) + "\n}\n"
            if not new_src.startswith(head):
                raise SystemExit("英文包前缀被改动，停手")

        # ---- 写盘前的硬断言 ----
        tree = ast.parse(new_src)          # 语法必须能过
        node = [n for n in ast.walk(tree)
                if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "CATALOG"][0]
        cat = {k.value: v.value for k, v in zip(node.value.keys, node.value.values)}
        if len(cat) != len(new_keys):
            raise SystemExit("%s 生成后条目数 %d != 期望 %d" % (lang, len(cat), len(new_keys)))
        for k, v in st["pairs"]:           # 旧条目一条不能少、值不能变
            if cat.get(k) != v:
                raise SystemExit("[%s] 旧条目被改动或丢失：%r" % (lang, k))
        for k in new_keys:                 # 每一条都能查到
            if k not in cat:
                raise SystemExit("[%s] 生成后查不到：%r" % (lang, k))
        output[lang] = {"path": st["path"], "src": new_src, "cat": cat,
                        "count": len(cat)}

    # ---- 打印计划 ----
    for lang, fname in PACKS:
        st = state[lang]
        print("%s (%s)：%d → %d 条（+%d）"
              % (lang, fname, len(st["pairs"]), output[lang]["count"], len(data[lang])))
        print("   t() 实参覆盖：%d / %d"
              % (sum(1 for k in need if k in output[lang]["cat"]), len(need)))
        print("   导航页名「先查查」：%s" % ("已收录" if "先查查" in output[lang]["cat"] else "缺失"))

    if not write:
        print()
        print("（这是 dry run，没有写盘。加 --write 才写入。）")
        return 0

    if not os.path.isdir(ARCHIVE):
        os.makedirs(ARCHIVE)
    print()
    for lang, fname in PACKS:
        path = output[lang]["path"]
        bak = os.path.join(ARCHIVE, fname + ".bak")
        shutil.copyfile(path, bak)
        io.open(path, "w", encoding="utf-8", newline="\n").write(output[lang]["src"])
        print("已写入 %s（备份：%s）" % (os.path.relpath(path, ROOT), os.path.relpath(bak, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
