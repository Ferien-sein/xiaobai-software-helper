# -*- coding: utf-8 -*-
"""语言包有效性检查（按 t() 调用点核对）。

为什么不用「字面量 vs 目录」比对：
  app.py 里大量文案是多段拼接出来的，字面量被 AST 拆成碎片。
  拿「字面量集合」和「目录键集合」互相做子串比较，报出来的
  「孤儿键」几乎全是假警报（实测 79 个里 0 个是真的），
  这种检查等于没有。

正确的判据是：**每一个 t(...) 调用点的实参，都能在语言包里查到**。
因为那才是运行期真正拿去查表的值。

本工具做三件事：
  1. 找出 app.py 里全部 t(...) 调用点，抽出实参
  2. f-string 形参要特别处理：t(f"...{x}...") 在查表前就已经插值，
     永远匹配不到 —— 这类必须改写成 t("...{x}...").format(x=...) 的形式，
     工具会直接报出来
  3. 统计每个语言包的覆盖情况，并列出缺失的实参

用法: python tools/check_i18n.py
"""

import os
# ★ 锁定界面语言（XBSH_LANG_LOCKED）：这些检查/自检脚本的输出与断言都基于简体中文，
#   而 i18n 会按系统区域自动探测语言 —— 在英文机器 / CI 上会探测成英文，
#   断言就全挂（GitHub runner 上真踩过：selftest_platform 11 项失败）。
#   ★ 用 = 不用 setdefault：环境里已有 XBSH_LANG 时 setdefault 不覆盖，锁会失效。
#   插在第一个模块级 import 之前，保证任何依赖 i18n 的 import 都在它之后。
os.environ["XBSH_LANG"] = "zh-CN"

import ast
import io
import os
import re
import sys

def _force_utf8_output():
    """让中文输出在 Windows 默认（GBK）控制台上也不乱码、不崩。

    不加这个的话，print 中文会变成乱码甚至 UnicodeEncodeError，
    而这类检查工具的用途就是给人看结论 —— 结论读不了等于没做。
    重定向到文件时同样是 UTF-8，输出一致。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001  老 Python 没有 reconfigure
            pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

# 这些不是文案，而是路径/文件名/格式标记，不该进语言包
EXEMPT = {
    "需求存档", "使用说明.txt", "提示词模板.txt", "显示诊断.txt",
    "===== 原始答案（给程序自己看，不用管） =====", "===== 原始答案结束 =====",
    "小白造软件助手",      # APP_NAME，简繁同形，英文品牌名保持
    "微软雅黑",
    "zh-CN", "zh-TW", "en",
}


def t_call_args(path):
    """抽出所有 t(...) 调用点的实参。

    返回 (静态参数列表, f-string 调用点行号列表)
    """
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    statics = []
    fstrings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not (isinstance(fn, ast.Name) and fn.id == "t"):
            continue
        if not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            statics.append(arg.value)
        elif isinstance(arg, ast.JoinedStr):
            fstrings.append(node.lineno)
        elif isinstance(arg, ast.Name):
            statics.append(("__VAR__", arg.id, node.lineno))
        elif isinstance(arg, ast.BinOp):
            statics.append(("__EXPR__", ast.dump(arg)[:60], node.lineno))
        else:
            statics.append(("__OTHER__", ast.dump(arg)[:60], node.lineno))
    return statics, fstrings


def runtime_keys(src_dir):
    """找出**运行时才查表**、静态看不出来的键。

    ⚠️ 这是 check_i18n.py 原来的盲区，由一次真实事故暴露：
       导航页名是 `t(name)`，name 来自 PAGES 元组 ——
       只静态扫 t("字面量") 永远看不见这几条。
       结果：补完 checker 报的全部缺失后，英文/繁体模式下
       **左侧导航的「先查查」仍然是简体**，而 checker 显示 100%。

    这里把这类键补上：PAGES 的每一项，以及 QUESTIONS 里
    会被渲染成字符串的字段（title/hint/example/help 与 options 列表）。

    ★ 但有一类要**排除**：由 platform_info 自己本地化的平台标签。
      那些值（Windows 32 位 / macOS Intel（x64）…）是
      describe_target(key, lang) 产出的，走的是另一套机制，
      不在语言包里、也不该强求进语言包 —— 否则清单里会一直有
      8 条永远"缺"的假警报，把真的漏翻淹掉。
    """
    import importlib.util

    keys = []
    try:
        spec = importlib.util.spec_from_file_location(
            "_app_for_keys", os.path.join(src_dir, "app.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001  拿不到就退回静态结果，不阻断检查
        print("  [warn] 无法导入 app.py 取运行时键: %r" % (e,))
        return keys, []

    # 由 platform_info 负责本地化的那些标签，先收集起来
    own_i18n = set()
    try:
        pm = __import__("platform_info")
        for key in getattr(pm, "TARGETS", []) or []:
            for loc in ("zh-CN", "zh-TW", "en"):
                own_i18n.add(pm.describe_target(key, loc))
    except Exception:  # noqa: BLE001
        pass

    def keep(v):
        """判断这个运行时字符串算不算"该由语言包负责"。

        含平台标签的一律排除 —— 它们是**拼接出来的整句**
        （「跟我电脑一样：Windows 64 位（推荐）」「例如：Windows 64 位（我自己的电脑就是Windows 64 位）」），
        而且随运行机器而变，不可能预先写进语言包。
        这些句子的固定部分已经分别被翻译了，机器名部分由
        platform_info 自己本地化。
        """
        if not isinstance(v, str) or not v.strip():
            return False
        if v in own_i18n:
            return False
        for label in own_i18n:
            if label and label in v:
                return False
        return True

    # 页名
    for name in getattr(getattr(mod, "App", object), "PAGES", ()) or ():
        if keep(name):
            keys.append(name)

    # 问卷里会被渲染的字符串
    qkeys = []
    for q in getattr(mod, "QUESTIONS", []) or []:
        for field in ("title", "hint", "example", "help"):
            v = q.get(field)
            if callable(v):
                try:
                    v = v()
                except Exception:  # noqa: BLE001
                    v = None
            if keep(v):
                keys.append(v)
                qkeys.append(v)
        opts = q.get("options")
        if callable(opts):
            try:
                opts = opts()
            except Exception:  # noqa: BLE001
                opts = None
        for o in (opts or []):
            if keep(o):
                keys.append(o)
                qkeys.append(o)

    # 主题名、字号档位名也会被渲染
    for tpl in (getattr(mod, "THEMES", {}) or {}).values():
        if isinstance(tpl, dict) and keep(tpl.get("name")):
            keys.append(tpl["name"])
    for item in getattr(mod, "FONT_BOOST_CHOICES", ()) or ():
        if isinstance(item, (list, tuple)) and item and keep(item[0]):
            keys.append(item[0])

    return keys, qkeys


def own_i18n_strings():
    """由 platform_info 自己本地化的字符串（平台标签及其拼接句）。

    这些**不该**强求进语言包 —— 它们在别处翻译。
    收集出来供各处过滤用（运行时键、自适应文案都要用同一套口径，
    否则不同检查项的口径不一致，会互相打架）。
    """
    out = set()
    try:
        sys.path.insert(0, SRC)
        pm = __import__("platform_info")
        for key in getattr(pm, "TARGETS", []) or []:
            for loc in ("zh-CN", "zh-TW", "en"):
                out.add(pm.describe_target(key, loc))
    except Exception:  # noqa: BLE001
        pass
    return out


_NUM = re.compile(r"^(\d+[.、]\s*)(.+)$", re.S)


def _covered(key, cat):
    """这个键在语言包里算「有译文」吗？

    ★ 必须和 i18n.t() 的查找逻辑一致：先精确匹配，再剥掉题号匹配。
      题号会随「做什么类型」变（插件集里「给谁用」是第 6 题、程序集是第 3 题），
      所以语言包存的是不带编号的键。
    """
    if key in cat:
        return True
    m = _NUM.match(str(key))
    return bool(m and m.group(2) in cat)


def keep_for_pack(v, own=None):
    """这个字符串是否该由语言包负责（False = 别的地方翻译，豁免）。"""
    if not isinstance(v, str) or not v.strip():
        return False
    own = own_i18n_strings() if own is None else own
    if v in own:
        return False
    for label in own:
        if label and label in v:
            return False
    return True


def adaptive_keys():
    """问卷自适应会显示出来的所有文案（标题/说明/示例/帮助/选项）。

    ★ 为什么要扫这里：问卷按平台族会派生出**另一套选项**
      （安卓给 apk、iOS 给 App Store、网页给网址……）。
      这些选项不在 QUESTIONS 的基础 options 里，只扫基础表就看不见 ——
      于是「英文界面里第 12 题冒出中文选项」这种情况 checker 会报 100%。
      这是第三个盲区（前两个：运行时页名、github_lookup 的 _()）。

    派生规则在 questionnaire.py，这里把每题在每个平台族下都解析一遍，
    以后往规则表里加选项，checker 会自动跟上。
    """
    try:
        sys.path.insert(0, SRC)
        import app as A
        import questionnaire as Q
    except Exception as e:  # noqa: BLE001
        print("  [!] 无法导入 app/questionnaire，跳过自适应文案检查: %r" % (e,))
        return []

    out = []
    own = own_i18n_strings()
    fams = (Q.FAM_DESKTOP, Q.FAM_ANDROID, Q.FAM_IOS, Q.FAM_HARMONY,
            Q.FAM_WEB, Q.FAM_UNKNOWN)

    # ★ 还要覆盖「按做什么类型组装出来的题集」：
    #   插件/脚本有自己的题目（挂在哪个软件里、怎么触发…），
    #   这些题**不在** A.QUESTIONS 里，只扫基础表就看不见它们，
    #   checker 会报 100% 而英文界面里冒出中文题。
    #   这是第四个盲区（前三个：运行时页名、github_lookup 的 _()、平台自适应选项）。
    kinds = []
    for name in ("KIND_PROGRAM", "KIND_PLUGIN", "KIND_SCRIPT"):
        v = getattr(Q, name, None)
        if v:
            kinds.append(v)

    question_sets = [list(getattr(A, "QUESTIONS", []) or [])]
    for k in kinds:
        try:
            question_sets.append(Q.questions_for(A.QUESTIONS, k, "zh-CN"))
        except Exception:  # noqa: BLE001
            pass

    for qs in question_sets:
        for q in qs:
            for fam in fams:
                try:
                    r = Q.adapt(q["key"], fam, "zh-CN", q)
                except Exception:  # noqa: BLE001
                    continue
                for field in ("title", "hint", "example", "help"):
                    v = r.get(field)
                    if keep_for_pack(v, own):
                        out.append(v)
                for o in r.get("options") or []:
                    if keep_for_pack(o, own):
                        out.append(o)

    # 类型题本身（它不在基础 QUESTIONS 里，是组装时插进去的）
    for fam in fams:
        try:
            r = Q.adapt(Q.KIND_QUESTION["key"], fam, "zh-CN", Q.KIND_QUESTION)
        except Exception:  # noqa: BLE001
            continue
        for field in ("title", "hint", "example"):
            if keep_for_pack(r.get(field), own):
                out.append(r[field])
        for o in r.get("options") or []:
            if keep_for_pack(o, own):
                out.append(o)

    for seq in getattr(Q, "BROAD", {}).values():
        for o in seq:
            if keep_for_pack(o, own):
                out.append(o)
    return out


def module_keys(fname, call_names=("t",)):
    """抽出某个模块里 `t(...)` / `_(...)` 的字符串实参。

    ★ 为什么要扫别的模块：github_lookup.py 是纯逻辑模块，
      为了能被单独 import 和测试，它用**可注入的翻译钩子** `_()`，
      而不是直接 import i18n（那样会带上整串 UI 依赖）。
      只扫 app.py 的话，这 19 条文案永远不在检查范围内 ——
      结果就是英文/繁体模式下「查一下 GitHub」的结论仍是中文，
      而 checker 显示 100%。这是继「页名看不见」之后发现的第二个盲区。
    """
    path = os.path.join(SRC, fname)
    if not os.path.exists(path):
        return []
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in call_names:
            if node.args and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str):
                v = node.args[0].value
                if v not in EXEMPT:
                    out.append(v)
    return out


def catalog_of(path):
    if not os.path.exists(path):
        return {}, "文件不存在"
    try:
        tree = ast.parse(io.open(path, encoding="utf-8").read())
    except SyntaxError as e:
        return {}, "语法错误: %s" % e
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CATALOG":
            return {k.value: v.value for k, v in zip(node.value.keys, node.value.values)}, None
    return {}, "找不到 CATALOG"


def main():
    # 输出改成 ASCII 标记 + 强制 UTF-8：
    #   编码不了，脚本会直接崩（UnicodeEncodeError，exit 1），
    #   而且**任何覆盖率下都跑不完整** —— 验证工具自己不可靠最要命。
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001  老 Python 没有 reconfigure
        pass

    app_path = os.path.join(SRC, "app.py")
    statics, fstrings = t_call_args(app_path)

    const_args = [a for a in statics if isinstance(a, str) and a not in EXEMPT]
    var_args = [a for a in statics if not isinstance(a, str)]
    rt_keys, _ = runtime_keys(SRC)
    rt_keys = [k for k in rt_keys if k not in EXEMPT]

    # 也是纯逻辑模块，用可注入的翻译钩子 _()（见 module_keys 的说明）
    mod_keys = module_keys("github_lookup.py", call_names=("_",))

    # 问卷自适应派生出来的文案（按平台族的另一套选项）
    ad_keys = [k for k in adaptive_keys() if k not in EXEMPT]

    uniq = sorted(set(const_args) | set(rt_keys) | set(mod_keys) | set(ad_keys))

    print("app.py 的 t() 调用点：%d 处" % len(statics))
    print("  字符串实参（去重）：%d 个" % len(set(const_args)))
    print("  运行时才查表的键（页名/问卷字段/主题名等）：%d 个" % len(set(rt_keys)))
    print("  其它模块（github_lookup.py 的 _()）：%d 个" % len(set(mod_keys)))
    print("  问卷自适应派生文案：%d 个" % len(set(ad_keys)))
    print("  合计需覆盖：%d 个" % len(uniq))
    print("  非字符串实参（无法静态核对）：%d 个" % len(var_args))
    print("  f-string 实参：%d 处" % len(fstrings))
    if fstrings:
        print("    [!] f-string 会先插值再查表，永远匹配不到，必须改写成模板形式：")
        for ln in sorted(set(fstrings)):
            print("       L%d" % ln)

    bad = 0
    if fstrings:
        bad += 1

    for lang, fname in (("zh-TW", "i18n_zh_tw.py"), ("en", "i18n_en.py")):
        cat, err = catalog_of(os.path.join(SRC, fname))
        print()
        print("=" * 62)
        print("%s  (%s)" % (lang, fname))
        print("=" * 62)
        if err:
            print("  [X] %s" % err)
            bad += 1
            continue
        # ★ 覆盖判定要和 i18n.t() 用**同一套口径**：题号会随「做什么类型」变，
        #   所以键不带编号。t() 会剥掉编号再查，这里也必须认中性键 ——
        #   否则 checker 会把「其实能翻译」的键报成缺失（或反过来放过真缺失）。
        missing = [k for k in uniq if not _covered(k, cat)]
        used = len(uniq) - len(missing)
        pct = 100.0 * used / len(uniq) if uniq else 100.0
        print("  条目数: %d" % len(cat))
        print("  覆盖: %d / %d = %.1f%%" % (used, len(uniq), pct))
        if missing:
            bad += 1
            print("  [X] 未覆盖 %d 条（这些会回退成简体）:" % len(missing))
            for k in missing[:20]:
                print("      %r" % (k[:86],))
        else:
            print("  [OK] 全部有译文")

    print()
    print("=" * 62)
    if bad:
        print("有 %d 类问题" % bad)
    else:
        print("语言包与代码一致，无回退项")
    return 1 if bad else 0


if __name__ == "__main__":
    _force_utf8_output()
    sys.exit(main())
