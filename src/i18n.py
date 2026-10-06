# -*- coding: utf-8 -*-
"""多语言支持：简体中文 / 繁體中文 / English

设计（沿用插件 dsh-requirement-check 里验证过的做法）：

  · **简体中文的原文就是键**。不引入 msgid/msgstr 那套间接层，
    因为原文本身已经是人话，代码里读起来仍然清楚：
        t("复制需求")  →  "複製需求" / "Copy requirement"
    代价是改简体原文时要同步另外两份 —— 用 tools/check_i18n.py 兜住。

  · 语言包分开放：zh-TW 在 i18n_zh_tw.py，en 在 i18n_en.py。
    三个文件可以各写各的，不会互相踩。

  · 查不到就把原文原样返回。所以**漏翻不会崩**，只会显示简体，
    再由 tools/check_i18n.py 在发布前报出来。

  · 语言优先级：显式参数 > 环境变量 XBSH_LANG/DSH_LANG > config.json > 系统区域 > 简中。

为什么不用 gettext：本项目是单文件桌面小工具，gettext 要额外编译 .mo、
装目录结构，对「双击 exe」的分发方式太重了，也会让打包更麻烦。
"""
import os
import sys

LANGS = ("zh-CN", "zh-TW", "en")
DEFAULT_LANG = "zh-CN"

LANG_NAMES = {
    "zh-CN": "简体中文",
    "zh-TW": "繁體中文",
    "en": "English",
}

# 当前语言（由 set_lang 设置；模块级缓存，避免每次查表都走一遍优先级判断）
_CURRENT = None

# 语言包延迟导入：没装英文包时应用仍要能跑
_PACKS = None


def _load_packs():
    global _PACKS
    if _PACKS is not None:
        return _PACKS
    packs = {}
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    for lang, modname in (("zh-TW", "i18n_zh_tw"), ("en", "i18n_en")):
        try:
            mod = __import__(modname)
            packs[lang] = getattr(mod, "CATALOG", {}) or {}
        except Exception:  # noqa: BLE001  语言包缺失/损坏都不该让程序起不来
            packs[lang] = {}
    _PACKS = packs
    return packs


def normalize_lang(value):
    """把各种写法归一化：zh_tw / zh-Hant / 繁體 / english / en-US …"""
    if not value:
        return None
    v = str(value).strip().lower().replace("_", "-")
    if v.startswith("en"):
        return "en"
    if v in ("zh-tw", "zh-hk", "zh-mo") or "hant" in v or "繁" in v:
        return "zh-TW"
    if v in ("zh-cn", "zh-sg", "zh") or "hans" in v or "简" in v or "简" in v:
        return "zh-CN"
    return None


def detect_lang():
    """按环境变量 → 系统区域 的顺序猜一个语言"""
    for var in ("XBSH_LANG", "DSH_LANG", "LANG", "LC_ALL", "LC_MESSAGES"):
        got = normalize_lang(os.environ.get(var))
        if got:
            return got

    # Windows 控制台代码页：950 = 繁体，936 = 简体
    if sys.platform == "win32":
        try:
            cp = int(os.environ.get("CP") or os.environ.get("OEMCP") or 0)
            if cp == 950:
                return "zh-TW"
            if cp in (936, 54936):
                return "zh-CN"
        except (TypeError, ValueError):
            pass

    # 再退一步：让 Python 自己判断（locale.getdefaultlocale 在 3.15 会移除，
    # 所以包在 try 里，失败就用默认值）
    try:
        import locale

        loc = locale.getlocale()[0] or ""
        got = normalize_lang(loc)
        if got:
            return got
    except Exception:  # noqa: BLE001
        pass

    return DEFAULT_LANG


def resolve_lang(explicit=None, saved=None):
    """语言优先级：显式参数 > 环境变量 > 已保存的偏好 > 系统区域 > 默认"""
    return (
        normalize_lang(explicit)
        or normalize_lang(os.environ.get("XBSH_LANG"))
        or normalize_lang(os.environ.get("DSH_LANG"))
        or normalize_lang(saved)
        or detect_lang()
        or DEFAULT_LANG
    )


def set_lang(lang):
    """设置当前语言并返回实际生效的值"""
    global _CURRENT
    _CURRENT = resolve_lang(lang)
    return _CURRENT


def get_lang():
    global _CURRENT
    if _CURRENT is None:
        _CURRENT = resolve_lang()
    return _CURRENT


_NUM_PREFIX = None


def _num_re():
    global _NUM_PREFIX
    if _NUM_PREFIX is None:
        import re
        _NUM_PREFIX = re.compile(r"^(\d+[.、]\s*)(.*)$", re.S)
    return _NUM_PREFIX


def _lookup(catalog, text):
    """查译文，带一层「题号无关」的回退。

    ★ 为什么需要：问卷的题号会变 —— 做插件时「给谁用」是第 6 题，
      做程序时是第 3 题（插件的核心问题插到了前面）。
      如果把题号写进语言包的键（"3. 给谁用？…"），那换个类型这条翻译就失效，
      英文界面里会冒出中文标题。

      所以：键一律存**不带题号**的版本（"给谁用？一共几个人用？"），
      查表时把编号剥掉再查、查到后把原编号补回去。
      写死编号的老键仍然保留兼容（先精确匹配）。
    """
    if text in catalog:
        return catalog[text]
    m = _num_re().match(text)
    if not m:
        return text
    body = m.group(2)
    hit = catalog.get(body)
    if hit:
        # ★ 补回去的编号要用**传入的那个**，不能用 catalog 里的键 ——
        #   中性键本身没编号，但万一命中的是「写死旧编号」的老键，
        #   用它的编号会张冠李戴（实测出现过「6. 给谁用」显示成「2. 給誰用」）。
        #   交回调用方前把旧编号剥掉，由 t() 用原始前缀拼。
        stripped = _num_re().match(str(hit).lstrip())
        if stripped:
            hit = stripped.group(2)
        return hit
    return text


def _lookup2(catalog, text):
    """查译文，返回 (是否命中, 正文)。正文里**不含**题号。

    ★ 为什么单独一个函数、还要明确返回「有没有命中」：
      只靠比较字符串是分不清「查到译文」和「没查到、原样返回」的
      （_lookup 会 lstrip，结果必然不等）。早先就是这么写错，
      把没有编号的句子也当成命中，第 2 题的编号因此丢了。
    """
    s = str(text)
    if s in catalog:
        v = str(catalog[s]).lstrip()
        # 老键可能自带编号，剥掉交给调用方用「传入的那个编号」重拼
        m = _num_re().match(v)
        return True, (m.group(2).lstrip() if m else v)
    m = _num_re().match(s)
    if not m:
        return False, s
    body = m.group(2)
    hit = catalog.get(body)
    if hit is None:
        return False, s
    v = str(hit).lstrip()
    m2 = _num_re().match(v)
    return True, (m2.group(2).lstrip() if m2 else v)


def _lookup(catalog, text):
    """查译文（把题号拼回去的完整版）。给不关心命中情况的调用方用。"""
    hit, body = _lookup2(catalog, text)
    if not hit:
        return text
    m = _num_re().match(str(text))
    return (m.group(1) + body) if m else body


def t(text, **fmt):
    """取当前语言的译文。查不到就返回原文（所以漏翻只是显示简体，不会崩）。

    支持简单占位替换：t("已填 {n}/{m} 格", n=1, m=2)

    ★ 题号会随「做什么类型」变，所以键不带编号：
      t("6. 给谁用？一共几个人用？") 会剥掉 "6. " 查到中性键，
      再把**传入的那个 "6. "** 拼回译文前面（不是老键里的编号）。

    ★ 判断「有没有命中」不能靠 `out != text`：_lookup 里做了 .lstrip()，
      返回的字符串和原文必然不等，于是每一句都会被当成「命中了中性键」——
      连带着把「本来就没有编号」的句子的原编号判断搞错，第 2 题的编号就是这么丢的。
      改成让 _lookup 明确告诉调用方「命中的是哪种情况」。
    """
    lang = get_lang()
    out = text
    if lang != DEFAULT_LANG:
        catalog = _load_packs().get(lang) or {}
        hit, body = _lookup2(catalog, text)
        if hit:
            m = _num_re().match(text)
            if m:
                # 用**传入的编号**，不是老键里的
                out = m.group(1) + body
            else:
                out = body
        else:
            out = text
    if fmt:
        try:
            out = out.format(**fmt)
        except (KeyError, IndexError, ValueError):
            pass
    return out


def translate_catalog(texts, lang):
    """批量取某个语言的译文（给自检/导出用），返回 {原文: 译文}"""
    catalog = _load_packs().get(lang) or {}
    return {s: _lookup(catalog, s) for s in texts}


def reload_packs():
    """清掉语言包缓存（改完语言包后不用重启）"""
    global _PACKS
    _PACKS = None
