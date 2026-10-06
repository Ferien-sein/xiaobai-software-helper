# -*- coding: utf-8 -*-
"""
小白造软件助手 —— 把「我想要一个软件」翻译成 AI 能直接开工的完整需求说明。

用法：双击 启动.bat（或打包后的 exe）。
填完左侧的问题 → 右侧自动生成一段完整需求 → 点「复制需求」→ 粘贴给 AI。
"""

import os
import re
import sys
import json
import time
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# 平台/位数探测（同目录，打包时会被一起收进去）
# 用「直接 import + 兜底查路径」的写法而不是 try/except 多层包裹：
# 静态 import 语句才容易被 PyInstaller 的分析器发现，包进产物里。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import platform_info  # noqa: E402  (必须在 sys.path 处理之后)
import i18n  # noqa: E402
from i18n import t  # noqa: E402  界面文案统一走这个短名字
import github_lookup  # noqa: E402  先查查：动手前看 GitHub 有没有现成的
import questionnaire  # noqa: E402  问卷自适应：按平台调整后面的问题

APP_NAME = "小白造软件助手"
APP_VERSION = "1.14.0"


def _pick_app_dir():
    """确定「程序目录」，也就是存档、配置该放在哪里。

    坑：PyInstaller 打包成文件夹版之后，__file__ 指向的是 _internal 里面的
    模块，而用 _MEIPASS 也会落进 _internal —— 存档会被埋进内层文件夹里，
    用户在 exe 旁边根本找不到。所以打包运行时要用 exe 自己所在的目录。

    ★ 另一个坑（做安装器时踩到）：装到 C:\\Program Files 之后，
      普通用户**没有权限**往程序目录写文件，存档和配置会全部失败。
      所以这里先探测能不能写；不能写就退到用户目录（%APPDATA%），
      保证「装在哪都能用」。
    """
    if getattr(sys, "frozen", False):
        cand = os.path.dirname(os.path.abspath(sys.executable))
    else:
        cand = os.path.dirname(os.path.abspath(__file__))
    return cand if _writable(cand) else _user_data_dir()


def data_location_note():
    """告诉用户「东西存在哪」的一句话。

    为什么需要：装到 C:\\Program Files 时程序目录不可写，
    数据会自动退到 %APPDATA%\\小白造软件助手 —— 那个路径用户猜不到，
    所以必须显示出来，不能让他找不到自己的存档。
    """
    if os.path.normcase(APP_DIR) == os.path.normcase(os.path.dirname(os.path.abspath(__file__))):
        return ""        # 源码运行，不啰嗦
    frozen_beside_exe = bool(getattr(sys, "frozen", False)) and _writable(
        os.path.dirname(os.path.abspath(sys.executable)))
    if frozen_beside_exe:
        return t("存档和设置保存在程序旁边：") + APP_DIR
    return t("存档和设置保存在：") + APP_DIR + t("（程序装在只读位置，所以放到你的用户目录）")


def _writable(path):
    """这个目录能不能新建文件？试探一下，别等用户存盘时才报错。"""
    probe = os.path.join(path, ".write-test.tmp")
    try:
        os.makedirs(path, exist_ok=True)
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return True
    except OSError:
        return False


def _user_data_dir():
    """用户可写的数据目录（装到 Program Files 时用）。

    Windows 用 %APPDATA%\\小白造软件助手，其它系统用 ~/.xiaobai-software-helper。
    """
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        d = os.path.join(base, "小白造软件助手")
    else:
        d = os.path.join(os.path.expanduser("~"), ".xiaobai-software-helper")
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        d = os.path.expanduser("~")
    return d


APP_DIR = _pick_app_dir()
ARCHIVE_DIR = os.path.join(APP_DIR, "需求存档")
HELP_FILE = os.path.join(APP_DIR, "使用说明.txt")
CONFIG_FILE = os.environ.get("XBSH_CONFIG") or os.path.join(APP_DIR, "config.json")
# 可用环境变量 XBSH_CONFIG 指向别的配置文件。
# 截图/自检脚本靠它做到「多语言互不干扰、且不动用户真实配置」——
# 否则截英文图要和真实 config.json 抢写，实测出现过后启动的进程把语言改回去。

# 生成的提示词模板文件（打包后随程序一起分发）
TEMPLATE_CANDIDATES = [
    os.path.join(APP_DIR, "提示词模板.txt"),
    os.path.join(getattr(sys, "_MEIPASS", APP_DIR), "提示词模板.txt"),
]

PLACEHOLDER = "（这一格还没填，请你直接问我）"


# ---------------------------------------------------------------------------
# 「跑在什么系统、32 位还是 64 位」
# ---------------------------------------------------------------------------
# 为什么这一格值得单独问：它是需求里最常漏、又最容易导致
# 「你这边做好了，在别人电脑上打不开」的一项。
# 默认值按使用者自己的电脑来 —— 探测逻辑在 platform_info.py，可独立测试。
#
# 探测结果只算一次（模块级缓存）：这几张表要在导入时构造，反复探测没必要。
_PLATFORM = None


def current_platform():
    """本机平台（缓存）"""
    global _PLATFORM
    if _PLATFORM is None:
        _PLATFORM = platform_info.detect_platform()
    return _PLATFORM


def current_target():
    """本机对应的目标平台值，例如 'windows-64'"""
    return platform_info.platform_to_target(current_platform())


# ---------------------------------------------------------------------------
# 问卷自适应：按第 3 题选的平台，让后面的问题更有针对性
# ---------------------------------------------------------------------------
# 规则表在 questionnaire.py（纯逻辑、可单独测）。这里只做两件事：
#   1. 从当前答案读出平台族
#   2. 把问题定义按族调整后交给界面
#
# 为什么要做：用户反馈「想做手机 App，但后面好多问题都不适配」——
# 第 4 题问「在哪里打开」，给的却是 Windows 电脑的选项。

def current_family(answers=None):
    """当前答案对应的平台族。

    读第 3 题（system）选了什么；没选就按本机推。
    用户选的是「跟我电脑一样：Windows 64 位（推荐）」这种整句，
    所以走 questionnaire 的关键词判断（选项文案会随语言变，不能精确匹配）。
    """
    val = ""
    if answers:
        val = (answers.get("system") or "").strip()
    if not val:
        return questionnaire.family_of_target(current_target())
    return questionnaire.family_of_prompt_answer(val)


def current_kind(answers=None):
    """当前答案对应的「做什么类型」（程序 / 插件 / 脚本）。

    ★ 这是第三层维度：类型决定**出现哪些题**，
      而平台族（current_family）只决定单个题的选项和措辞。
    """
    val = (answers or {}).get("kind") if answers else ""
    return questionnaire.kind_of_prompt_answer(val or "")


def adapted_question(q, fam, locale):
    """把一个基础问题定义按平台族调整成界面要显示的样子。"""
    return questionnaire.adapt(q["key"], fam, locale, q)


def questions_for_current(answers=None):
    """当前这一组问题（按类型组装 + 平台调整），供自检和脚本调用。"""
    kind = current_kind(answers or {})
    fam = current_family(answers or {})
    loc = i18n.get_lang()
    out = []
    for q in questionnaire.questions_for(QUESTIONS, kind, loc):
        aq = questionnaire.adapt(q["key"], fam, loc, q)
        aq["key"] = q["key"]
        out.append(aq)
    return out


def _system_options():
    """系统与位数的可选项。第一项按本机探测结果生成，直接就是默认答案。"""
    det = current_platform()
    # ★ 语言必须显式传进去：platform_info 的函数默认 locale='zh-CN'，
    #   不传就会在英文/繁体界面里显示简体（这是实测发现的漏洞）。
    lang = i18n.get_lang()
    own = platform_info.describe_target(current_target(), lang)
    opts = [t("跟我电脑一样：") + own + t("（推荐）")]
    # 顺序：先桌面（多数场景），再手机 App，最后网页。
    # 手机那几项是「不是给自己电脑做」的主要场景，不能漏。
    for key in ("windows-64", "windows-32", "windows-arm64",
                "macos-64", "macos-arm64",
                "linux-64", "linux-arm64",
                "android-arm64", "android-32",
                "ios", "harmony",
                "web"):
        label = platform_info.describe_target(key, lang)
        if label == own:
            continue      # 已经在第一项里了
        opts.append(label)
    opts.append(t("不确定，你帮我选最合适的"))
    return opts


def _system_example():
    """按本机生成的示例答案"""
    det = current_platform()
    lang = i18n.get_lang()
    own = platform_info.describe_target(current_target(), lang)
    return (t("例如：") + own + t("（我自己的电脑就是")
            + det["os_label"] + " " + platform_info.bits_word(det["bits"], lang) + t("）"))


def _system_help():
    """帮助文本：把本机探测结果、各平台交付物、兼容性提醒都写进去"""
    det = current_platform()
    lang = i18n.get_lang()
    base = (
        t("为什么要问？\n"
          "  · 做电脑软件、手机 App、还是网页，做法完全不同，成品也完全不一样：\n"
          "      Windows 是 .exe，Mac 是 .app，Linux 是 .AppImage/.deb，\n"
          "      安卓是 .apk，iPhone 是 App Store 里的 App，网页只有一个网址。\n"
          "  · 电脑还要分 32 位 / 64 位：32 位程序在 32/64 位系统上都能跑，\n"
          "    但 64 位程序在 32 位系统上跑不起来。\n\n"
          "程序已经帮你探测过了：\n")
        + "  " + platform_info.default_target_sentence(det, lang) + "\n"
        + "  " + platform_info.compat_note(lang) + "\n"
    )

    # 手机 App 的两个现实门槛，很多人不知道，必须提前讲清楚
    base += t("\n如果你要做**手机 App**，先知道两件事：\n")
    base += "  · " + platform_info.DELIVERABLE_HINT["android"][lang] + "\n"
    base += "  · " + platform_info.DELIVERABLE_HINT["ios"][lang] + "\n"
    base += t("  · 如果只是想「手机上也能用」，网页版通常最省事："
              "不用安装、不用审核、电脑手机都能开。\n")

    if not det["certain"]:
        base += t("\n⚠️ 探测结果可能不完全准确（") + det["detail"] + t("），\n"
                  "   如果做出来是给别的电脑或手机用，请直接选对方的系统。\n")
    base += t("\n只有当你做出来是给别人用时，才需要换成对方的系统。\n"
              "如果不确定对方的设备，就选第一项，并在最后一格补充说明。")
    return base


def _qval(q, field, default=""):
    """取一个问题的某个字段值。

    有些字段（system 题的 options/example/help）是**函数**，
    因为它们要按"当前语言 + 本机探测结果"在渲染时才算得出来。
    统一走这个函数取，调用方不用关心是值还是函数。
    """
    v = q.get(field, default)
    if callable(v):
        try:
            return v()
        except Exception:  # noqa: BLE001  动态字段算不出来也不该让界面起不来
            return default
    return v if v is not None else default


def _qopts(q):
    """取某个问题的选项列表（同样支持函数形式）"""
    opts = _qval(q, "options", [])
    return list(opts) if opts else []


def resolve_system_answer(value):
    """把用户选的那一项翻译成明确的目标平台，供需求说明里使用。

    返回 (target, 说明文本)。用户选「跟我电脑一样…」时要把探测结果
    展开成明确的系统与位数 —— 否则对方 AI 无法确定。
    """
    text = (value or "").strip()
    det = current_platform()
    lang = i18n.get_lang()
    own_target = current_target()

    if not text:
        return None, ""
    # 首项是「跟我电脑一样：<具体平台>（推荐）」，前缀走 t()，所以前缀要用译文比
    if text.startswith(t("跟我电脑一样")) or text.startswith(t("不确定，你帮我选")):
        return own_target, platform_info.default_target_sentence(det, lang)
    for key in platform_info.TARGETS:
        if key == "auto":
            continue
        if platform_info.describe_target(key, lang) == text:
            return key, t("用户指定：") + text
    return None, text


# ---------------------------------------------------------------------------
# 字号档位：只改「字多大」，不动窗口尺寸
# ---------------------------------------------------------------------------
# 0.95 = 比第一版还小一档（一般用不上）
# 1.00 = 我原本的设定（实测偏小）
# 1.15 = 默认值，相当于正文 11.5px
# 1.30 = 大字版
FONT_BOOST = 1.15
FONT_BOOST_CHOICES = (
    ("标准", 1.00),
    ("大一点（推荐）", 1.15),
    ("更大", 1.30),
    ("最大", 1.45),
)

# ---------------------------------------------------------------------------
# 配色：自己定义的一套前端色板（亮 / 暗双主题）
# ---------------------------------------------------------------------------
# 设计意图：低饱和中性灰 + 一个强调色（亮色下用蓝 #2f6fed，暗色下提亮到 #5b8cff）。
# 命名不用任何第三方软件的别名，直接用语义：surface 面、text 文字、border 边框。
#
# 对比度自检（WCAG 相对亮度）：
#   暗色 text #f2f3f5 on surface #17181a  ≈ 15:1
#   暗色 text2 #c2c6cc on surface #17181a  ≈ 10:1
#   暗色 text3 #9aa0a7 on surface #17181a  ≈ 6.4:1   ← 仍高于 4.5:1 标准
#   浅色 text #16181d on surface #ffffff   ≈ 17:1
#   浅色 text3 #737980 on surface #ffffff  ≈ 4.8:1
THEMES = {
    "dark": {
        "name": "暗色",
        "bg": "#17181a",             # 页面底
        "sidebar": "#17181a",        # 侧栏底（与页面同色，靠一条竖线分隔）
        "card": "#212226",           # 卡片 / 抬升面
        "card_hover": "#2a2b2f",     # 卡片更上一层
        "inset": "#1d1e21",          # 输入框内陷底
        "border1": "#242629",        # 一级边框（最淡，用于卡片轮廓）
        "border2": "#323438",        # 二级边框（输入框）
        "border3": "#3d4045",        # 三级边框（分隔线、按钮描边）
        "fg": "#f2f3f5",             # 主文字
        "fg2": "#c2c6cc",            # 次要文字
        "fg3": "#9aa0a7",            # 三级文字（说明、提示）
        "on_brand": "#ffffff",       # 强调色上的文字
        "brand": "#5b8cff",          # 强调色（暗色下提亮，保证对比度）
        "hover": "#212226",          # 悬停底
        "hover_solid": "#2a2b2f",    # 悬停底（实色，用于按钮）
        "active_nav": "#26282c",     # 导航选中底
        "ok": "#3ecf72",             # 成功
        "warn": "#e0a33a",           # 警告
        "err": "#f2706f",            # 错误
        "sel": "#33363b",            # 选中 / 选区底
        "placeholder": "#7b8188",    # 示例灰字（比三级文字更淡）
    },
    "light": {
        "name": "浅色",
        "bg": "#ffffff",
        "sidebar": "#f7f8fa",
        "card": "#ffffff",
        "card_hover": "#f2f4f7",
        "inset": "#ffffff",
        "border1": "#eceef1",
        "border2": "#e2e5ea",
        "border3": "#d6dae1",
        "fg": "#16181d",
        "fg2": "#565c64",
        "fg3": "#737980",
        "on_brand": "#ffffff",
        "brand": "#2f6fed",
        "hover": "#f1f3f6",
        "hover_solid": "#e9ecf1",
        "active_nav": "#eceff4",
        "ok": "#1f9d55",
        "warn": "#b7791f",
        "err": "#d64545",
        "sel": "#dfe7fb",
        # 示例灰字：原来 #a3a9b0 在纯白上对比度只有 2.37，偏淡得看不清（实测算出来的）。
        # 调到 #767e86 → 约 3.9，既保持「这是示例、不是已填内容」的观感，又能读清。
        "placeholder": "#767e86",
    },
}
PLACEHOLDER_FG = "#7b8188"   # 示例灰字，由 init_theme() 从主题同步
THEME_MODE = "dark"
THEME = THEMES["dark"]      # 由 init_theme() 在启动时确定


def init_theme():
    """确定用哪套主题：环境变量 > config.json > 默认暗色。"""
    global THEME_MODE, THEME, PLACEHOLDER_FG
    for cand in (os.environ.get("XBSH_THEME"), _saved_theme()):
        if isinstance(cand, str) and cand.lower() in THEMES:
            THEME_MODE = cand.lower()
            break
    THEME = THEMES[THEME_MODE]
    PLACEHOLDER_FG = THEME["placeholder"]
    return THEME_MODE, THEME


def _saved_theme():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if isinstance(cfg, dict):
            return cfg.get("theme")
    except (OSError, ValueError):
        pass
    return None


def save_theme(mode):
    cfg = {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            old = json.load(f)
        if isinstance(old, dict):
            cfg = old
    except (OSError, ValueError):
        pass
    cfg["theme"] = mode
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# 界面语言：简体中文 / 繁體中文 / English
# ---------------------------------------------------------------------------
# 优先级：环境变量 XBSH_LANG > config.json 里记住的选择 > 系统区域 > 简体中文。
# 切换语言后需要重启界面（所有文字都是建界面时取好的），
# 跟「切换主题」一样处理，理由是重启最不容易漏掉某个没重画的控件。


def _read_config():
    """读 config.json；坏了就当空字典，绝不抛。"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_config(**patch):
    """把若干键写回 config.json，保留其它键。

    注意：config.json 里还存着表单草稿和显示大小，不能整体覆盖。
    """
    cfg = _read_config()
    cfg.update(patch)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def init_lang():
    """启动时确定界面语言。"""
    lang = i18n.resolve_lang(saved=_read_config().get("lang"))
    i18n.set_lang(lang)
    # 把翻译器交给纯逻辑模块（它不硬依赖 i18n，这样能被单独 import 和测试）
    github_lookup.set_translator(i18n.t)
    return lang


def save_lang(lang):
    """记住语言选择（重启后仍生效）"""
    _save_config(lang=lang)


def lang_display_name(lang=None):
    """当前语言的显示名"""
    return i18n.LANG_NAMES.get(lang or i18n.get_lang(), i18n.get_lang())

# 存档文件里用来携带「12 格原始答案」的标记（普通用户不需要理会）
DATA_MARK = "===== 原始答案（给程序自己看，不用管） ====="
DATA_END = "===== 原始答案结束 ====="

# ---------------------------------------------------------------------------
# 引导问题定义
#   key        存档用的字段名
#   title      界面上的问题标题
#   hint       为什么必须回答（给小白解释清楚，消除"怕填错"的心理）
#   help       点「看例子」时弹出的详细说明和范例
#   example    输入框里的灰字示例
#   options    可一键点选的常见情况（可多选，点到输入框里）
#   multiline  是否多行输入
#   required   是否算「必填」（只影响进度提示，不阻止生成）
# ---------------------------------------------------------------------------
QUESTIONS = [
    dict(
        key="what",
        title="你想做一个什么样的东西？",
        hint="用你自己的话说清楚「这是个干什么的东西」，不用管技术词。",
        help=(
            "怎么说才算清楚？只要让一个完全不懂你工作的人听懂就行。\n\n"
            "✅ 好的说法：\n"
            "  · 一个帮我算装修报价的小工具\n"
            "  · 一个把三个 Excel 自动合并汇总的程序\n"
            "  · 一个记录每天花销、月底出图的记账小软件\n\n"
            "❌ 太含糊的说法：\n"
            "  · 一个管理系统（管理什么？给谁用？）\n"
            "  · 一个像抖音那样的软件（做不到，也太大了）\n\n"
            "提示：一次只做一件小事，做完能用、你满意了，再让我加功能。"
        ),
        example="例如：一个帮我把每天的三份销售 Excel 自动合并汇总、并标出金额对不上行的小工具",
        options=[
            "数据汇总/整理类（把文件或表格自动合并、统计）",
            "自动生成文件类（自动出 Excel/Word/PDF/图片）",
            "日常记录/管理类（记账、客户、库存、待办）",
            "计算/换算类（报价、工资、用料、单位换算）",
            "娱乐/小工具类（随机、抽签、定时提醒）",
            "网页应用（浏览器里打开，可多人用）",
        ],
        multiline=True,
        required=True,
    ),
    dict(
        key="who",
        title="给谁用？一共几个人用？",
        hint="只有你自己用和给同事用，做法完全不同（要不要登录、要不要联网）。",
        help=(
            "为什么要问？\n"
            "  · 只有你自己用 → 最简单，不用账号、不用联网，双击就能跑。\n"
            "  · 几个同事用 → 需要考虑文件放哪、能不能同时改。\n"
            "  · 很多人/外部客户用 → 得做成网页或服务器程序，成本高很多。\n\n"
            "顺便说一句你的电脑水平也没关系，我会讲得通俗。"
        ),
        example="例如：只有我自己用，一台 Windows 11 电脑",
        options=[
            "只有我自己用",
            "我和几个同事（2~10 人）",
            "整个部门/公司很多人",
            "要给外部客户或手机上用",
        ],
        multiline=False,
        required=True,
    ),
    dict(
        key="system",
        title="这个软件要跑在什么系统上？32 位还是 64 位？",
        hint="选错了会导致「你这边做好了，在别人电脑上打不开」。默认按你自己的电脑来。",
        # ★ 这三项写成**可调用对象**，在渲染时才求值。
        #   写成 options=_system_options() 会在模块导入时就算好，
        #   而那时语言还没设置（init_lang 在 main 里才调用），
        #   于是运行时切换语言后选项与示例仍是导入时的语言 —— 实测踩到过。
        help=_system_help,
        example=_system_example,
        options=_system_options,
        multiline=False,
        required=True,
        dynamic=True,
    ),
    dict(
        key="where",
        title="在哪里打开它？要不要联网？",
        hint="决定做成桌面程序还是网页，以及数据存本地还是网上。",
        help=(
            "常见三种：\n"
            "  · 桌面程序（双击打开一个窗口）→ 最简单、最快、数据在自己电脑上。\n"
            "  · 本地网页（浏览器打开 127.0.0.1 之类的地址）→ 界面好看，仍在本机。\n"
            "  · 联网网站（别人也能访问）→ 需要服务器和域名，要花钱、也复杂。\n\n"
            "另外请说明数据敏不敏感：能上传到网上吗？还是必须留在本机？\n"
            "不确定就写「你帮我选」。"
        ),
        example="例如：在 Windows 电脑上双击打开，不用联网，数据必须留在本机",
        options=[
            "Windows 电脑上双击打开的窗口程序",
            "浏览器里打开的本地网页",
            "手机上也能用",
            "要联网 / 别人也能访问",
            "数据不允许上传，必须留在本机",
            "不确定，你帮我选",
        ],
        multiline=False,
        required=True,
    ),
    dict(
        key="pain",
        title="它帮你解决什么麻烦？（现在你是怎么手动做的）",
        hint="把现在的真实做法写一遍，这比任何抽象描述都有用。",
        help=(
            "这是最重要的一格。请像讲故事一样写清楚：\n"
            "  现在做这件事，你要点开什么、点什么、复制到哪里、容易在哪里出错、\n"
            "  大概要花多长时间。\n\n"
            "✅ 例子：\n"
            "  「每天下午我从系统导出 3 个 Excel，手动复制粘贴到汇总表，\n"
            "   再一个个核对客户名，一般要 40 分钟，月底经常发现有两行金额抄错。」\n\n"
            "你写得越具体，我做出来的东西就越贴合你的实际工作，而不是一个空壳。"
        ),
        example="例如：现在每天手动复制粘贴三个表，约 40 分钟，客户名不一致时经常漏行",
        options=[
            "重复复制粘贴，太花时间",
            "人工计算/核对，容易出错",
            "文件太多、太乱，找不到",
            "格式/格式转换很烦（如 PDF、图片、Word 互转）",
            "要按时提醒或被催",
        ],
        multiline=True,
        required=True,
    ),
    dict(
        key="flow",
        title="你希望怎么操作它？（从打开到结束，一步步说）",
        hint="你描述步骤，我照着做界面，不用懂任何设计。",
        help=(
            "写成编号步骤最清楚，比如：\n"
            "  1）双击打开，看到一个大按钮「选择文件」\n"
            "  2）我把当天的 3 个 Excel 拖进去\n"
            "  3）点「开始汇总」\n"
            "  4）它显示一共多少条、哪几行金额对不上\n"
            "  5）点「导出结果」，在桌面得到一个汇总表\n\n"
            "想不出界面细节也没关系，写「你看着办，越简单越好」就行。"
        ),
        example="例如：1）拖入文件 2）点汇总 3）看异常提示 4）点导出，桌面得到结果表",
        options=[
            "越简单越好，最好一键完成",
            "拖文件进去，点一下按钮",
            "填几个数字/短句，点计算",
            "先选设置，再批量处理很多文件",
            "你看着办",
        ],
        multiline=True,
        required=True,
    ),
    dict(
        key="input",
        title="输入从哪来？（数据/文件从哪来，长什么样）",
        hint="告诉我输入什么样，我才能保证读得进、读得对。",
        help=(
            "说清楚：\n"
            "  · 手动打字？还是已有文件？\n"
            "  · 什么格式：Excel(.xlsx)/CSV/Word/PDF/图片/网页/微信记录？\n"
            "  · 文件长什么样：第一行是标题吗？大概多少行多少列？有哪些列？\n"
            "  · 有几个文件、放在哪个文件夹、文件名有规律吗？\n\n"
            "⭐ 最有用的一招：直接放一份真实的（或脱敏的）样例文件到工作文件夹里，\n"
            "   并在这里写上文件名，我就能照着真实数据做。\n"
            "   如果格式比较怪（合并单元格、多个工作表、图片里的表格），一定要说。"
        ),
        example="例如：我手动从系统导出 3 个 .xlsx 文件放到「每日数据」文件夹，"
                "第一行是标题，列有 日期/客户/金额，每天约 200 行；样例文件：样例.xlsx",
        options=[
            "手动打字输入",
            "Excel 文件（.xlsx/.xls）",
            "CSV 文本表格",
            "Word / PDF / 图片（需要识别文字）",
            "复制粘贴一段文字给你",
            "我会放一份样例文件在文件夹里",
            "格式比较特殊（合并单元格/多表/扫描件）",
        ],
        multiline=True,
        required=True,
    ),
    dict(
        key="output",
        title="输出/结果要长什么样？",
        hint="你要看到什么、拿到什么文件，这决定了我做成什么样才算完成。",
        help=(
            "从这些角度说：\n"
            "  · 屏幕上要看到什么（数字、列表、红字提醒、图表？）\n"
            "  · 要生成文件吗？格式和文件名？保存到哪个文件夹（桌面？）\n"
            "  · 需要打印、发微信、发邮件吗？\n\n"
            "✅ 例子：「屏幕上显示总金额和异常行数，导出 Excel 到桌面，\n"
            "   文件名带当天日期，表头加粗、金额保留两位小数。」"
        ),
        example="例如：屏幕显示汇总结果和异常行；导出 Excel 到桌面，文件名 = 汇总_日期.xlsx",
        options=[
            "屏幕上显示结果就行",
            "导出 Excel 表格",
            "导出 Word 文档",
            "导出 PDF",
            "生成图片（可发微信/打印）",
            "要打印",
            "要有图表/统计图",
            "要能一键复制结果文字",
        ],
        multiline=True,
        required=True,
    ),
    dict(
        key="done",
        title="怎么算做好了？（成功的标准）",
        hint="给我一个你自己能验证的标准，我才能自己测到对为止。",
        help=(
            "最好写成「拿什么数据跑一遍，看到什么结果，就算成功」，例如：\n"
            "  · 拿上周的 3 个文件跑一遍，总金额和财务给的数字一模一样；\n"
            "  · 把 x 输入进去，输出的结果等于 y；\n"
            "  · 以前 40 分钟的活，现在 2 分钟做完，且不再需要人工核对。\n\n"
            "这样我会自己反复测试到达标，而不是做出个「看起来能用」的东西交给你。"
        ),
        example="例如：拿上周 3 个文件跑一遍，总金额与财务数一致，异常行全部标出",
        options=[
            "数据结果和人工算的完全一致",
            "以前要 X 分钟，现在 1 分钟内完成",
            "生成的表格/文档我能直接发给客户或打印",
            "不用我再去核对，出错它会提示",
        ],
        multiline=True,
        required=True,
    ),
    dict(
        key="limit",
        title="有什么不能做 / 必须遵守的规矩？",
        hint="这一格能防止我做出来的东西碰你不该碰的数据，或者白做。",
        help=(
            "请说明：\n"
            "  · 不可以动哪些文件、文件夹、系统设置？\n"
            "  · 数据能不能上传到网上？（公司机密、客户隐私很关键）\n"
            "  · 要不要保留操作记录、要不要每次先备份？\n"
            "  · 电脑上有没有杀毒/权限限制，不能装东西？\n"
            "  · 有没有截止时间或必须用某种工具（比如只能用 Excel）？\n\n"
            "没有特别要求就写「没有特别要求」。"
        ),
        example="例如：不要动 D 盘财务原始文件；数据绝对不能上传；每次先备份一份",
        options=[
            "没有特别要求",
            "数据绝对不能上传到网上",
            "不要修改/删除我的原始文件",
            "每次操作前自动备份一份",
            "电脑不能安装新软件",
            "只能用 Office/Excel 实现",
            "有截止时间",
        ],
        multiline=True,
        required=True,
    ),
    dict(
        key="ref",
        title="有没有想模仿的参照物？（可选）",
        hint="给我一个参照，比你形容半天界面都准确。",
        help=(
            "可以写：某个软件/网站的某一部分（截图、网址、名字都行），\n"
            "或者「上面的按钮位置」「表格样式像那样」。\n\n"
            "如果要模仿某个收费软件的全部功能，要提前说清预算和范围，"
            "我会告诉你哪些能实现、哪些建议先不做。"
        ),
        example="例如：界面像微信电脑版那种左边列表、右边内容就行",
        options=[
            "没有参照，你设计一个简洁的",
            "我有截图/网址，等下单独发给你",
            "要像 Excel 那样的表格界面",
        ],
        multiline=False,
        required=False,
    ),
    dict(
        key="install",
        title="你希望怎么用它、怎么再打开？（怎么交付给你）",
        hint="这决定我最终交给你的是 exe、网页还是一堆文件。",
        help=(
            "常见选择：\n"
            "  · 一个 exe，双击就打开（最省事，推荐小白）\n"
            "  · 一个文件夹，双击里面的 启动.bat 打开\n"
            "  · 一个本地网址，浏览器打开\n\n"
            "另外说说：要不要做桌面快捷方式？以后想加功能怎么办？\n"
            "写「你决定」完全可以，我会挑最省事的方案。"
        ),
        example="例如：给我一个 exe 放桌面，双击就打开",
        options=[
            "一个 exe 文件，双击打开（推荐）",
            "一个文件夹，双击 启动.bat",
            "浏览器打开本地网址",
            "要放到桌面，方便我随时点开",
            "你决定就好",
        ],
        multiline=False,
        required=False,
    ),
    dict(
        key="extra",
        title="还想补充什么？（可选，想到什么写什么）",
        hint="零散的想法、担心的地方、以后想加的功能，都写在这里。",
        help=(
            "这里可以写得很随意，比如：\n"
            "  · 「我不懂技术，你要多解释几句」\n"
            "  · 「先做最简单的版本，我试过再加功能」\n"
            "  · 「以后想加个手机端」\n"
            "  · 「我怕数据丢了」\n\n"
            "这些都会写进需求说明里，我会照着办。"
        ),
        example="例如：我不懂技术，做完请告诉我怎么打开、怎么备份；先做最简版本",
        options=[
            "我不懂技术，请用大白话解释并一步步教我",
            "先做最简单能用的版本，我试过再加功能",
            "以后可能还要加功能，代码请留好扩展余地",
            "我怕数据丢失，请做好备份",
        ],
        multiline=True,
        required=False,
    ),
]

ABOUT_TEXT = """{app} v{ver}

它是干什么的？
  你按它列的 12 个问题填一填（能点选项就点，不用会打字），
  右边会自动拼出一段「需求说明」。
  点「复制需求」，粘贴给 AI，它就能开始给你做软件。

为什么问这些？
  不是因为流程麻烦，而是这几条正好是决定「做出来能不能用」的关键：
  给谁用、输入长什么样、什么算做好了。
  少一条，AI 就可能做出一个你不满意的东西。

三件小事
  · 每题下面的「看例子」会告诉你该怎么写，写着「可选」的可以不填。
  · 写错了、写少了都没关系，以后随时改，改完重新复制一次就行。
  · 「保存到文件」会在 需求存档 文件夹里留一份。之后可以在「历史记录」
    这一页里找回来：双击就能整份还原到填写页继续改，不用重填。
    建议每次跟 AI 提需求前都先保存一下。

界面太小 / 太大 / 有点糊怎么办
  · 程序会自动读 Windows 的缩放（你这台机器是 225%），按同样比例显示，
    这样字最清晰 —— 不要手动把「显示大小」调到比 Windows 缩放差太多的值，
    那种情况下 Windows 只能把界面当图片拉伸，字就会发糊。
  · 点左下角「🔍 显示大小」可以调整（100%~250%）。它会先告诉你：
    Windows 是多少、推荐用多少。
  · 如果觉得字发糊，点左下角「🩺 显示诊断」，它会生成一份报告并直接给出
    结论（在哪被拉伸了、字体是什么、DPI 是多少），把报告发出去就能排查。
  · 想彻底改观感，也可以在 Windows 里调：
    设置 → 系统 → 屏幕 → 缩放与布局；以及 ClearType 文本调谐器。
"""


# ---------------------------------------------------------------------------
# 提示词模板
# ---------------------------------------------------------------------------
#
# 说明：除了程序内置的「提问框架」，你还可以在程序目录下放一个
# 「提示词模板.txt」（UTF-8 编码）。如果存在，会在生成结果的最前面加上它的内容，
# 方便固定一些你常说的要求（例如「先给我看方案再动手」）。
# 文件不存在也不影响使用。
def load_template():
    for p in TEMPLATE_CANDIDATES:
        try:
            with open(p, "r", encoding="utf-8") as f:
                t = f.read()
            if t.strip():
                return t.strip()
        except OSError:
            continue
    return None


def _target_block_for_prompt(answers):
    """生成需求说明里那段「目标平台」。

    ★ 内容必须按**所选目标**给，不能一律拿本机说事。
      早先写死成「你的电脑是 Windows 64 位 …」「Windows 上可能要解除锁定」，
      选了安卓之后还在讲 Windows 的 32/64 位 —— 对手机用户完全是错的。
      现在：目标是手机/网页时不再提本机电脑，改讲该平台自己的注意事项。
    """
    det = current_platform()
    lang = i18n.get_lang()
    value = (answers.get("system") or "").strip()
    target, _note = resolve_system_answer(value) if value else (None, "")

    if target is None and value and not value.startswith((t("跟我电脑一样"), t("不确定"))):
        # 用户写了别的文字（比如自己描述），原样带出去
        return t("用户填写：") + value

    if target is None:
        target = current_target()

    label = platform_info.describe_target(target, lang)
    is_desktop = str(target).startswith(("windows", "macos", "linux"))

    lines = [t("请把它做成能在下列平台上直接运行：") + label, ""]
    if is_desktop:
        lines.append("· " + platform_info.default_target_sentence(det, lang))
    else:
        # 手机/网页：不能拿本机电脑冒充「目标平台」，如实说明
        lines.append("· " + t("目标是手机或网页，跟做我这台电脑上的程序不是一回事，"
                              "请按上面的平台来做。"))
    lines.append("· " + platform_info.compat_note(lang, target))
    if not det["certain"]:
        lines.append("· " + t("⚠️ 本机探测结果可能不准确（") + det["detail"]
                     + t("），如果你判断目标平台不是上面这个，请先问我。"))
    lines.append("")
    lines.append(t("交付要求：请给出该平台上可以直接打开使用的成品，"
                   "并说明在目标设备上第一次打开需要做什么。"))
    return "\n".join(lines)


def build_prompt(answers, ai_name="AI"):
    """把答案拼成一段可直接粘贴给 AI 的完整需求说明。"""
    def get(key):
        v = (answers.get(key) or "").strip()
        return v if v else t(PLACEHOLDER)

    lines = []
    head = load_template()
    if head:
        lines.append(head)
        lines.append("")
    lines.append(t("【我完全不懂技术，下面是我的需求，请你帮我把这个软件做出来。】"))
    lines.append("")
    lines.append(t("先说清楚我们的合作方式："))
    lines.append(t("1. 如果下面有哪里没写清楚、或者你觉得会影响结果，请先问我（一次问 2~5 个，"
                   "用大白话问，不要用技术名词考我），问清楚再动手。"))
    lines.append(t("2. 技术方案（用什么语言、什么工具、怎么打包）你自己决定；"
                   "如果有影响我使用的取舍，告诉我两个选项各自的好处就行。"))
    lines.append(t("3. 请你自己动手做完并自己测试通过，最后给我一个能直接双击打开、"
                   "或能直接打开的成品，并告诉我放在哪个路径、怎么再次打开。"))
    lines.append(t("4. 交付时请一并告诉我：怎么用、怎么备份数据、有哪些你没做到或做不到的地方。"))
    lines.append(t("5. 不要只给我代码和说明书让我自己想办法运行，我看不懂。"))
    lines.append("")
    lines.append("=" * 46)
    lines.append(t("我的需求"))
    lines.append("=" * 46)
    lines.append("")

    # 生成说明时也要用**按平台调整后**的标题 ——
    # 否则界面上写「手机上打算怎么用它」，生成出来的却是「在哪里打开它」，
    # 两边对不上（这个问题被 selftest_adaptive 抓出来过）。
    # 题集也要按「做什么类型」组装：插件没有「系统与位数」那几题。
    fam = current_family(answers)
    kind = current_kind(answers)
    active = questionnaire.questions_for(QUESTIONS, kind, i18n.get_lang())
    for i, q in enumerate(active, 1):
        aq = adapted_question(q, fam, i18n.get_lang())
        lines.append("### " + t(aq["title"]))
        val = (answers.get(q["key"]) or "").strip()
        # 系统那一格：用户选的可能是「跟我电脑一样」，要展开成明确的系统与位数，
        # 否则对方 AI 无法确定到底做哪个平台。
        if q.get("dynamic") and q["key"] == "system" and val:
            _target, note = resolve_system_answer(val)
            lines.append(t("  选择：") + val)
            if note:
                for ln in note.splitlines():
                    lines.append("  " + ln if ln.strip() else "")
        elif val:
            for ln in val.splitlines():
                lines.append("  " + ln if ln.strip() else "")
        else:
            lines.append("  " + t(PLACEHOLDER))
        lines.append("")

    # 目标平台单独再明确一段：放在这里是因为它最容易被忽略，
    # 而且一旦搞错，前面所有工作都白做。
    target_line = _target_block_for_prompt(answers)
    if target_line:
        lines.append("=" * 46)
        lines.append(t("目标平台（重要）"))
        lines.append("=" * 46)
        for ln in target_line.splitlines():
            lines.append(ln)
        lines.append("")

    lines.append("=" * 46)
    lines.append(t("补充情况"))
    lines.append("=" * 46)
    lines.append(t("· 我的水平：完全不懂编程，请用大白话解释，并一步一步教我怎么用。"))
    lines.append(t("· 我希望你高度自主地完成：能自己决定的事就别问我，只在真正需要我选择时才问。"))
    lines.append(t("· 做完请告诉我：结果文件在哪个文件夹、以后怎么再打开它。"))
    lines.append("")
    lines.append(t("如果上面的信息还不够你做决定，请直接问我；信息够的话，请现在就开工。"))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 分辨率自适应（4K / 高 DPI 屏幕）
# ---------------------------------------------------------------------------
# 现状：这里所有界面尺寸原来都按 96 DPI（100% 缩放）写死，在 4K 屏上
# （Windows 常用 150%~200%）就会小得看不清。现在统一走 ui() 换算：
#   Windows 推荐缩放 150%  →  UI_SCALE = 1.5  →  字号 10 变 15、间距 12 变 18
# 缩放值来源优先级：命令行 --ui-scale > config.json 里记住的选择 >
#                  Windows 推荐值（注册表）> 实测系统 DPI。
BASE_DPI = 96.0
UI_SCALE = 1.0          # 由 init_ui_scale() 设置
FONT_FAMILY = "Microsoft YaHei UI"
FONT_FALLBACKS = ("Microsoft YaHei UI", "Microsoft YaHei", "微软雅黑", "SimHei", "SimSun")
# 下面几个只在启动时填一次，供「显示诊断」回读
_AWARENESS_RESULT = "(还没声明)"
_AWARENESS_NOTES = []
_RECOMMENDED = (1.0, "还没探测")
_WINDOWS_DPI = 96


def ui(v):
    """界面主尺寸（间距、宽高、字号）按缩放换算。

    ★ 注意：字号必须用这个换算，而 ttk 的 padding/width 这类「像素」属性不要用。
      原因是 tkinter 里点值是像素值的 1/1.333 倍，两边同时乘一遍就会
      变成平方级放大（实测 250% 时输入框会涨到 13 倍而不是 2.5 倍）。
      因此策略是：字体亲手放大，其余交给 Tk 自己按 DPI 缩放。
    """
    return max(1, int(round(v * UI_SCALE)))


def _winreg_values(root, path, name):
    """读注册表里的 Windows 缩放设置，读不到就返回 None。"""
    try:
        import winreg
        with winreg.OpenKey(root, path) as k:
            val, _ = winreg.QueryValueEx(k, name)
            return val
    except Exception:
        return None


def _windows_dpi():
    """实测系统 DPI（96 = 100%）。"""
    try:
        from ctypes import windll
        try:
            return int(windll.user32.GetDpiForSystem()) or 96
        except Exception:
            hdc = windll.user32.GetDC(0)
            dpi = windll.gdi32.GetDeviceCaps(hdc, 88)   # LOGPIXELSX
            windll.user32.ReleaseDC(0, hdc)
            return int(dpi) or 96
    except Exception:
        return 96


def detect_recommended_scale():
    """推断 Windows 自己推荐的缩放比例。

    优先读 HKCU 的 LogPixels（Windows「更改文本大小」就是写这里，
    实测存在），否则用系统 DPI。返回 (缩放值, 说明文字)。
    """
    import winreg
    lp = _winreg_values(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "LogPixels")
    if lp:
        try:
            s = float(lp) / 96.0
            if 0.5 <= s <= 6.0:
                return s, "Windows 缩放设置（注册表 LogPixels=%s）" % lp
        except (TypeError, ValueError):
            pass
    dpi = _windows_dpi()
    return max(1.0, dpi / BASE_DPI), "系统实测 DPI = %s" % dpi


def _pick_scale(*candidates):
    """从若干候选里挑第一个能用的缩放值。"""
    for c in candidates:
        if c is None:
            continue
        try:
            s = float(c)
        except (TypeError, ValueError):
            continue
        if 0.5 <= s <= 6.0:
            return round(s, 3)
    return None


def _cli_scale():
    """支持命令行指定缩放：程序.exe --ui-scale 1.75"""
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--ui-scale" and i + 1 < len(args):
            return args[i + 1]
        if a.startswith("--ui-scale="):
            return a.split("=", 1)[1]
    return None


def _saved_scale():
    """读上次在程序里选过的缩放（config.json）。"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if isinstance(cfg, dict):
            return cfg.get("ui_scale")
    except (OSError, ValueError):
        pass
    return None


def _saved_font_boost():
    """读上次选过的字号档位。"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if isinstance(cfg, dict):
            return cfg.get("font_boost")
    except (OSError, ValueError):
        pass
    return None


def init_font_boost():
    """确定全局字号倍数。命令行/环境变量 > config.json > 默认值。"""
    global FONT_BOOST
    cli = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--font-boost" and i + 1 < len(args):
            cli = args[i + 1]
        elif a.startswith("--font-boost="):
            cli = a.split("=", 1)[1]
    for cand in (os.environ.get("XBSH_FONT_BOOST"), cli, _saved_font_boost()):
        if cand is None:
            continue
        try:
            v = float(cand)
        except (TypeError, ValueError):
            continue
        if 0.7 <= v <= 2.0:
            FONT_BOOST = round(v, 3)
            break
    return FONT_BOOST


def save_font_boost(v):
    cfg = {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            old = json.load(f)
        if isinstance(old, dict):
            cfg = old
    except (OSError, ValueError):
        pass
    cfg["font_boost"] = round(float(v), 3)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def save_ui_scale(scale):
    """把缩放选择记进 config.json，下次打开继续用。"""
    cfg = {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            old = json.load(f)
        if isinstance(old, dict):
            cfg = old
    except (OSError, ValueError):
        pass
    cfg["ui_scale"] = round(float(scale), 3)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def screen_size(root=None):
    """屏幕尺寸（像素）。支持用 XBSH_UI_SCREEN=3840x2160 模拟，方便在别的机器上验证 4K 表现。"""
    env = os.environ.get("XBSH_UI_SCREEN")
    if env and "x" in env:
        try:
            w, h = env.lower().split("x", 1)
            return int(w), int(h)
        except ValueError:
            pass
    try:
        if root is not None:
            return int(root.winfo_screenwidth()), int(root.winfo_screenheight())
        from ctypes import windll
        return int(windll.user32.GetSystemMetrics(0)), int(windll.user32.GetSystemMetrics(1))
    except Exception:
        return 1920, 1080


def likely_misconfigured():
    """4K 屏但界面缩放仍是 100% —— 这种机器上界面必然很小。"""
    w, h = screen_size()
    return max(w, h) >= 3000 and UI_SCALE < 1.25


def init_ui_scale(root=None):
    """确定全局 UI_SCALE。必须在建窗口/建控件之前调用。"""
    global UI_SCALE, _RECOMMENDED, _WINDOWS_DPI
    recommended, why = detect_recommended_scale()
    _RECOMMENDED = (recommended, why)
    _WINDOWS_DPI = _windows_dpi()
    chosen = _pick_scale(
        os.environ.get("XBSH_UI_SCALE"),   # 临时覆盖，方便排查
        _cli_scale(),
        _saved_scale(),
        recommended,
    )
    UI_SCALE = chosen if chosen else 1.0
    # ★ 这里故意【不】改 tk scaling。
    #   Tk 默认按 72dpi 换算点值，会把 padding/width 这类像素属性也一起放大；
    #   而我们字号已经用像素单位（负数）自己算好了，再让它放大就成了双倍。
    #   保持出厂值 = 界面上每个像素都由 ui() 决定，行为最可控。
    return UI_SCALE, recommended, why


def apply_dpi_awareness():
    """告诉 Windows「我自己会缩放」。必须在创建 Tk 之前调用，否则白设。

    这一步做不做，直接决定字清不清楚：
      · 做了   → 窗口按真实像素渲染，Windows 不再拉伸，字是清晰的；
      · 没做   → Windows 会把整个窗口当成 96dpi 的图放大到 225%，
                 相当于把图片拉大，字就糊了（老花眼那种感觉）。

    ★ 坑：SetProcessDpiAwarenessContext 失败时【返回 False 而不是抛异常】。
      如果只靠 try/except 判断，会把失败当成成功（我就踩了这个坑）。
      所以这里必须检查返回值，并把过程记进 notes 供诊断查看。
    """
    global _AWARENESS_NOTES
    notes = []
    try:
        from ctypes import windll
    except Exception as e:
        _AWARENESS_NOTES = ["ctypes 不可用: %r" % e]
        return "none"

    u = windll.user32
    # 1) Win10 1703+：per-monitor v2（多屏不同缩放最准）
    try:
        u.SetProcessDpiAwarenessContext.restype = ctypes.c_bool
        u.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        ctypes.set_last_error(0)
        ok = u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        err = ctypes.get_last_error()
        notes.append("SetProcessDpiAwarenessContext(-4) 返回 %s，GetLastError=%s"
                     % (ok, err))
        if ok:
            _AWARENESS_NOTES = notes
            return "per-monitor-v2"
    except Exception as e:
        notes.append("SetProcessDpiAwarenessContext(-4) 异常: %r" % e)

    # 2) Win8.1+：per-monitor（HRESULT 0 = S_OK）
    try:
        hr = windll.shcore.SetProcessDpiAwareness(2)
        notes.append("SetProcessDpiAwareness(2) 返回 HRESULT=%s" % hr)
        if hr == 0:
            _AWARENESS_NOTES = notes
            return "per-monitor"
    except Exception as e:
        notes.append("SetProcessDpiAwareness(2) 异常: %r" % e)

    # 3) 老系统：system aware
    try:
        ok = u.SetProcessDPIAware()
        notes.append("SetProcessDPIAware() 返回 %s" % ok)
        if ok:
            _AWARENESS_NOTES = notes
            return "system"
    except Exception as e:
        notes.append("SetProcessDPIAware() 异常: %r" % e)

    notes.append("三种方式都没成功，进程仍是 DPI 未声明状态")
    _AWARENESS_NOTES = notes
    return "none"


def current_awareness():
    """回读当前进程的 DPI 感知状态，用来确认声明到底生效没有。"""
    try:
        from ctypes import windll
        return int(windll.shcore.GetProcessDpiAwareness(None))
    except Exception:
        return -1


def run_diagnostics(app=None, reason="手动触发"):
    """把界面相关的真实数据写成文件，方便排查「字小 / 字糊」这类问题。

    不弹黑窗口，结果写到程序目录下的 显示诊断.txt。app 可以为 None（只测启动前信息）。
    """
    lines = ["界面显示诊断报告", "=" * 40, "触发原因：%s" % reason,
             "时间：%s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""]
    try:
        from ctypes import windll
        u, sh = windll.user32, windll.shcore
        lines.append("【DPI 感知】（这一段是判断字糊不糊的关键）")
        lines.append("  声明结果(本进程启动时)  : %s" % _AWARENESS_RESULT)
        for n in _AWARENESS_NOTES:
            lines.append("    · %s" % n)
        try:
            lines.append("  GetProcessDpiAwareness : %s  (0=未声明 1=系统 2=每显示器)"
                         % sh.GetProcessDpiAwareness(None))
        except Exception as e:
            lines.append("  GetProcessDpiAwareness : 读取失败 %s" % e)
        try:
            lines.append("  GetDpiForSystem         : %s   (=96 且屏幕是 4K 就说明没声明成功)"
                         % u.GetDpiForSystem())
        except Exception:
            pass
        # 这两项才是真正的判据
        try:
            cur = u.GetThreadDpiAwarenessContext()
            lines.append("  当前线程感知上下文      : %s" % cur)
            for label, val in (("per-monitor-v2", -4), ("per-monitor", -3),
                               ("system", -2), ("unaware", -1)):
                try:
                    if u.AreDpiAwarenessContextsEqual(
                            cur, ctypes.c_void_p(val)):
                        lines.append("  → 实际相当于           : %s" % label)
                        break
                except Exception:
                    pass
        except Exception as e:
            lines.append("  线程上下文读取失败: %s" % e)
        lines.append("")
        lines.append("【Windows 缩放设置】")
        import winreg
        for path, key in ((r"Control Panel\Desktop", "LogPixels"),
                          (r"Control Panel\Desktop\WindowMetrics", "AppliedDPI"),
                          (r"Control Panel\Desktop", "Win8DpiScaling")):
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as k:
                    lines.append("  %-14s = %s" % (key, winreg.QueryValueEx(k, key)[0]))
            except Exception:
                lines.append("  %-14s = (读不到)" % key)
        lines.append("")
        lines.append("【屏幕】")
        sw, sh_ = screen_size(app.root if app else None)
        lines.append("  屏幕尺寸(Tk 报告)       : %d x %d" % (sw, sh_))
        lines.append("  屏幕尺寸(系统物理)      : %s x %s" % (
            u.GetSystemMetrics(0), u.GetSystemMetrics(1)))
        lines.append("  Windows 推荐缩放        : %d%%   (依据：%s)"
                     % (int(round(_RECOMMENDED[0] * 100)), _RECOMMENDED[1]))
        lines.append("  程序实际使用缩放        : %d%%" % int(round(UI_SCALE * 100)))
        lines.append("  字号档位(FONT_BOOST)    : %.2f" % FONT_BOOST)
        lines.append("")
        lines.append("【窗口与字体】")
        if app is not None:
            try:
                hwnd = app.root.winfo_id()
                lines.append("  窗口句柄                : %s" % hwnd)
                try:
                    lines.append("  GetDpiForWindow         : %s"
                                 % u.GetDpiForWindow(hwnd))
                except Exception:
                    pass
                lines.append("  窗口尺寸                : %d x %d"
                             % (app.root.winfo_width(), app.root.winfo_height()))
                lines.append("  窗口位置                : +%d+%d"
                             % (app.root.winfo_rootx(), app.root.winfo_rooty()))
                try:
                    win_dpi = u.GetDpiForWindow(hwnd)
                except Exception:
                    win_dpi = _WINDOWS_DPI
                if win_dpi and _WINDOWS_DPI and win_dpi > _WINDOWS_DPI:
                    lines.append("  ⚠ 判定：窗口 DPI(%s) > 进程 DPI(%s)，"
                                 "Windows 在拉伸这个窗口 → 字会发糊"
                                 % (win_dpi, _WINDOWS_DPI))
                else:
                    lines.append("  ✔ 判定：进程 DPI(%s) 与窗口 DPI(%s) 一致，"
                                 "按真实像素渲染，字应当清晰" % (_WINDOWS_DPI, win_dpi))
                lines.append("  实际使用字体            : %s" % FONT_FAMILY)
                try:
                    import tkinter.font as tkfont
                    lines.append("  系统里是否有雅黑        : %s"
                                 % ("Microsoft YaHei UI" in set(tkfont.families(app.root))))
                except Exception:
                    pass
                for key in sorted(getattr(app, "named_fonts", {})):
                    f = app.named_fonts[key]
                    lines.append("  %-10s 请求=%s 实际=%s 行高=%spx"
                                 % (key, f.cget("size"), f.actual("size"),
                                    f.metrics("linespace")))
            except Exception as e:
                lines.append("  读取窗口信息失败: %s" % e)
        else:
            lines.append("  （启动阶段调用，还没有窗口）")
        lines.append("")
        lines.append("【怎么读这份报告】")
        lines.append("  · 先看「→ 实际相当于」那行，应该是 per-monitor-v2 或 per-monitor。")
        lines.append("  · 再看「判定」那行。如果出现 ⚠，字糊是 Windows 拉伸造成的。")
        lines.append("  · 若 GetDpiForSystem = 96 但屏幕物理尺寸是 3840x2160，")
        lines.append("    说明进程没声明成功，Windows 只能把界面当图片放大。")
    except Exception as e:
        import traceback
        lines.append("诊断过程出错：%s" % e)
        lines.append(traceback.format_exc())

    path = os.path.join(APP_DIR, "显示诊断.txt")
    try:
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("\n".join(lines) + "\n")
    except OSError as e:
        path = "（写不进去：%s）" % e
    return path


def choose_font_family(root):
    """挑一个本机真正有的中文字体，避免出现方框。"""
    try:
        from tkinter import font as tkfont
        have = {f.lower() for f in tkfont.families(root)}
    except Exception:
        return FONT_FAMILY
    for f in FONT_FALLBACKS:
        if f.lower() in have:
            return f
    return FONT_FAMILY


def restart_app():
    """按新的缩放重新启动自己（缩放必须在新进程里才生效）。"""
    try:
        if getattr(sys, "frozen", False):
            exe, args = sys.executable, sys.argv[1:]
        else:
            exe, args = sys.executable, [os.path.abspath(__file__)] + sys.argv[1:]
        os.spawnv(os.P_NOWAIT, exe, [exe] + list(args))
        return True
    except OSError:
        try:
            import subprocess
            subprocess.Popen([exe] + list(args), close_fds=True)
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# 界面
# ---------------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        self.answers = {}
        self.widgets = {}
        self.selected = {}       # key -> set(已选选项)
        self.option_buttons = {} # (key, option) -> Checkbutton
        self.opt_grids = {}      # key -> 选项所在的 grid 容器
        self.opt_boxes = {}      # key -> 该题所有勾选框
        self.optional = set()
        # 问卷自适应相关的状态，必须在 _build_body() 之前初始化 ——
        # 建卡片时会往里写（早先放在后面，直接 AttributeError）。
        self.adapted = {}        # 键 → 按平台族调整后的问题定义
        self.cards = {}          # 键 → 卡片 Frame（平台变了要重建）
        self.hint_labels = []    # 每题说明 Label，统一做折行（避免重复绑定）
        self._fam_built = None   # 建表单时用的平台族
        self._kind = None        # 当前「做什么类型」（程序/插件/脚本）
        self.scale = UI_SCALE
        self.font = FONT_FAMILY
        self.page_index = 0

        root.title(f"{t(APP_NAME)} v{APP_VERSION}" + t(" —— 把想法变成给 AI 的需求说明"))
        root.configure(bg=THEME["bg"])
        self._fit_window()

        self._setup_style()
        self._build_body()
        self._build_footer()
        self._select_page(0)

        # 可选题的集合也要按当前题集算：插件题集里有些程序题不存在了
        self.optional = {q["key"] for q in self._active_questions()
                         if not q.get("required")}
        self.refresh()
        self.refresh_history()

        # ★ 选项列数必须等窗口真正布局完再算：构建阶段 canvas 宽度还是 1，
        #   量不到可用宽度，只能瞎估，估多了选项文字就被截断。
        root.update_idletasks()
        self._layout_options()
        root.bind("<Configure>", lambda e: self._on_root_resize(), add="+")

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind("<Control-Return>", lambda e: self.copy_prompt())
        root.bind("<F1>", lambda e: self.show_about())
        if likely_misconfigured():
            root.after(700, self.warn_tiny_screen)

    def _active_questions(self):
        """这一次实际要问哪些题（按「做什么类型」组装）。

        ★ 类型改了题集就变（做插件比做程序多几题、少几题），
          所以不能直接用全局 QUESTIONS。
        """
        kind = getattr(self, "_kind", None) or current_kind(self._saved_answers())
        return questionnaire.questions_for(QUESTIONS, kind, i18n.get_lang())

    def _saved_answers(self):
        """从配置里读上次的草稿（构建阶段 collect() 还不能用 —— 输入框还没建）。"""
        try:
            d = _read_config().get("draft")
            return d if isinstance(d, dict) else {}
        except Exception:  # noqa: BLE001
            return {}

    def _adapted(self, q):
        """取这一题「按当前平台族调整后」的版本。

        没建过就现算（show_help / 生成需求说明也会用到）。
        """
        fam = self._fam_built
        if fam is None:
            # 构建阶段：collect() 还不能用，改从存档草稿里读平台
            fam = current_family(self._saved_answers())
            self._fam_built = fam
        return adapted_question(q, fam, i18n.get_lang())

    def _on_system_changed(self):
        """第 3 题的平台选变了吗？变了就重建表单，让后面的题跟着适配。"""
        want = current_family(self.collect())
        if self._fam_built is None or want == self._fam_built:
            return
        self._fam_built = want
        self._rebuild_form()

    def _on_kind_changed(self):
        """第 1 题「做什么类型」变了吗？变了就**换整套题**。

        做插件和做程序根本是两件事：插件不该被问 exe / 32 位 / apk，
        而该被问「挂在哪个软件里、怎么被调用、要不要调它的接口」。
        """
        answers = self.collect()
        want = current_kind(answers)
        if getattr(self, "_kind", None) == want:
            return
        self._kind = want
        # 类型变了，平台族也可能连带变（旧的 system 题可能已经不在了）
        self._fam_built = current_family(answers)
        self._rebuild_form()
        self.set_status(t("问题已按你选的类型调整过了。"))

    def _rebuild_form(self):
        """按新的平台族 / 类型重建整个表单，并保留用户已填的答案与勾选。"""
        answers = self.collect()
        picked = {k: set(v) for k, v in self.selected.items()}
        # 重建前先把当前类型记下来（重建后题集由它决定）
        self._kind = current_kind(answers)

        for child in list(self.inner.winfo_children()):
            child.destroy()
        self.widgets.clear()
        self.option_buttons.clear()
        self.opt_grids.clear()
        self.opt_boxes.clear()
        self.adapted.clear()
        # ★ 必须一起清掉：只登记新控件的引用，否则旧 Label 会一直累积
        #   （13 → 26 → 39；实测过）
        self.hint_labels = []
        active = self._active_questions()
        self.selected = {q["key"]: set() for q in active}

        for q in active:
            self._build_card(q)

        # 把内容填回去（走 _set_box_text，它会正确切掉占位符状态）
        for q in active:
            key = q["key"]
            val = (answers.get(key) or "").strip()
            if val:
                self._set_box_text(key, val)
        self._restore_selection(picked)

        self.root.update_idletasks()
        self._layout_options()
        self.refresh()

    def _restore_selection(self, picked):
        """重建表单后把勾选状态恢复回去，并按需同步到输入框。

        重建后 option_buttons 是新建的，所以要看**新的**控件里有没有这个选项
        （平台族变了以后，某些选项可能不再存在，那就跳过）。

        ★ 还要跳过**这一轮已经不存在**的题：换「做什么类型」时题集会变
          （插件模式没有「系统与位数」题），但 picked 里还留着它上一轮的勾选。
          直接调 _sync_options_to_box 会 KeyError: 'system' —— 实测就是这个崩的。
        """
        active_keys = {q["key"] for q in self._active_questions()}
        for key, chosen in (picked or {}).items():
            if not chosen or key not in active_keys or key not in self.widgets:
                continue
            for opt in list(chosen):
                entry = self.option_buttons.get((key, opt))
                if entry is None:
                    continue        # 新平台/新类型下没有这个选项了，跳过
                var = entry[0]
                var.set(True)
                self.selected.setdefault(key, set()).add(opt)
            if self.selected.get(key):
                self._sync_options_to_box(key)

    def _reflow_hints(self, event=None):
        """画布宽度变了就重设所有说明文字的折行宽度。

        ★ 必须容错：问卷自适应会重建表单，重建瞬间可能还有旧回调在跑，
          此时控件已销毁，configure 会抛 TclError: invalid command name。
          这里 skip 掉不存在的控件，而不是让异常冒出去。
        """
        width = max(ui(300), (getattr(event, "width", 0) or self.canvas.winfo_width())
                    - ui(120))
        alive = []
        for lb in getattr(self, "hint_labels", []):
            try:
                if lb.winfo_exists():
                    lb.configure(wraplength=width)
                    alive.append(lb)
            except tk.TclError:
                continue        # 已被销毁，丢掉
        self.hint_labels = alive

    def _on_root_resize(self):
        """窗口大小变了就重排选项（防抖，避免拖动窗口时反复重算）。"""
        if getattr(self, "_reflow_job", None) is not None:
            return
        self._reflow_job = self.root.after(180, self._do_reflow)

    def _do_reflow(self):
        self._reflow_job = None
        try:
            self._layout_options()
        except tk.TclError:
            pass

    def _fit_window(self):
        """按缩放和屏幕大小决定窗口尺寸，保证不会超出屏幕。"""
        w, h = ui(1240), ui(800)
        sw, sh = screen_size(self.root)
        w = min(w, int(sw * 0.94))
        h = min(h, int(sh * 0.92))
        self.root.geometry("%dx%d+%d+%d" % (w, h, max(0, (sw - w) // 2), max(0, (sh - h) // 3)))
        self.root.minsize(min(ui(1000), w), min(ui(640), h))

    def warn_tiny_screen(self):
        """4K 屏但系统缩放还是 100%：主动提醒并让用户一键放大。"""
        if messagebox.askyesno(
                "界面可能太小",
                "检测到你的屏幕是 4K（或更高），但 Windows 的缩放仍是 100%，\n"
                "所以这个界面看起来会偏小。\n\n"
                "要现在把界面放大到 150% 吗？\n"
                "（会重启这个小工具；不喜欢可以随时点右下角「显示大小」改回来）"):
            self.change_ui_scale(1.5)

    # ---------------- 样式（配色见文件顶部的 THEMES） ----------------
    def _setup_style(self):
        T = THEME
        self.T = T
        style = ttk.Style()
        # ★ 必须用 clam：Windows 的 vista 主题会忽略自定义颜色，
        #   那样这几套配色根本贴不上去。
        try:
            style.theme_use("clam")
            theme = "clam"
        except tk.TclError:
            theme = style.theme_use()
        f = self.font
        # ★ 字号 = 设计值 × 分辨率缩放(ui) × 用户字号档位(FONT_BOOST)
        # ★ 字号用「像素」（负数）：写正数（点）会被 Tk 按 DPI 再放大一次，
        #   和 ui() 叠加成平方级（实测 250% 时输入框涨到 13 倍而不是 2.5 倍）。
        # 同时做成「具名字体」，方便排查和用 font.metrics 量出真实行高。
        import tkinter.font as tkfont
        self.named_fonts = {}

        def F(px, bold=False):
            size = -max(7, int(round(ui(px) * FONT_BOOST)))
            key = "dsh_%d%s" % (size, "_b" if bold else "")
            if key in self.named_fonts:
                self.named_fonts[key].configure(family=f, size=size,
                                                weight="bold" if bold else "normal")
                return key
            self.named_fonts[key] = tkfont.Font(root=self.root, name=key, family=f,
                                                size=size,
                                                weight="bold" if bold else "normal")
            return key

        base = F(10)
        style.configure(".", font=base, background=T["bg"], foreground=T["fg"])

        # ---- 基础控件 ----
        style.configure("TFrame", background=T["bg"])
        style.configure("TLabel", background=T["bg"], foreground=T["fg"])
        style.configure("TEntry", fieldbackground=T["inset"], foreground=T["fg"],
                        bordercolor=T["border2"], lightcolor=T["border2"],
                        darkcolor=T["border2"], insertcolor=T["fg"])
        style.configure("TCheckbutton", background=T["card"], foreground=T["fg2"],
                        focuscolor=T["card"])
        style.map("TCheckbutton",
                  background=[("active", T["card"])],
                  foreground=[("active", T["fg"])])
        style.configure("TNotebook", background=T["bg"], borderwidth=0, tabmargins=0)
        style.configure("TNotebook.Tab", font=F(10), padding=(ui(12), ui(6)),
                        background=T["bg"], foreground=T["fg2"], borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", T["bg"])],
                  foreground=[("selected", T["fg"])])
        style.configure("Vertical.TScrollbar", background=T["border3"],
                        troughcolor=T["bg"], bordercolor=T["bg"],
                        arrowcolor=T["fg3"], borderwidth=0, width=ui(12))
        style.map("Vertical.TScrollbar", background=[("active", T["fg3"])])
        style.configure("TPanedwindow", background=T["bg"])
        style.configure("Sash", background=T["border2"], gripcount=0)
        style.configure("TProgressbar", background=T["brand"],
                        troughcolor=T["inset"], borderwidth=0, thickness=ui(5))

        # ---- 文字层级 ----
        style.configure("Title.TLabel", font=F(15, True),
                        background=T["bg"], foreground=T["fg"])
        style.configure("Sub.TLabel", font=F(9),
                        background=T["bg"], foreground=T["fg3"])
        style.configure("QTitle.TLabel", font=F(11, True),
                        background=T["card"], foreground=T["fg"])
        style.configure("QHint.TLabel", font=F(9),
                        background=T["card"], foreground=T["fg3"])
        style.configure("Ok.TLabel", font=F(9),
                        background=T["card"], foreground=T["ok"])
        style.configure("Card.TLabel", background=T["card"], foreground=T["fg"])
        style.configure("CardSub.TLabel", font=F(9),
                        background=T["card"], foreground=T["fg3"])

        # ---- 按钮：主按钮＝黑底白字（品牌色就是近黑），次按钮＝描边 ----
        style.configure("TButton", font=base, padding=(ui(10), ui(5)),
                        background=T["card"], foreground=T["fg"],
                        bordercolor=T["border3"], lightcolor=T["card"],
                        darkcolor=T["card"], focuscolor=T["card"])
        style.map("TButton",
                  background=[("active", T["hover_solid"]), ("pressed", T["hover"])],
                  foreground=[("active", T["fg"])],
                  bordercolor=[("active", T["border3"])])
        style.configure("Big.TButton", font=F(11, True), padding=(ui(18), ui(9)),
                        background=T["brand"], foreground=T["on_brand"],
                        bordercolor=T["brand"], lightcolor=T["brand"],
                        darkcolor=T["brand"], focuscolor=T["brand"])
        style.map("Big.TButton",
                  background=[("active", T["hover_solid"]), ("pressed", T["hover"])],
                  foreground=[("active", T["on_brand"])])
        style.configure("Small.TButton", font=F(9), padding=(ui(8), ui(4)),
                        background=T["bg"], foreground=T["fg2"],
                        bordercolor=T["border2"], lightcolor=T["bg"],
                        darkcolor=T["bg"], focuscolor=T["bg"])
        style.map("Small.TButton",
                  background=[("active", T["hover_solid"])],
                  foreground=[("active", T["fg"])],
                  bordercolor=[("active", T["border3"])])

        self.ui_font = base
        self.style_theme = theme

    def _entry(self, parent, **kw):
        """一个带主题色的多行输入框（Tk 的 Text 不吃 ttk 样式，只能手设）。"""
        T = THEME
        opts = dict(wrap="word", relief="flat", borderwidth=0, highlightthickness=1,
                    highlightbackground=T["border2"], highlightcolor=T["fg3"],
                    bg=T["inset"], fg=T["fg"], insertbackground=T["fg"],
                    selectbackground=T["sel"], selectforeground=T["fg"],
                    font=(self.font, -int(round(ui(10) * FONT_BOOST))),
                    padx=ui(8), pady=ui(6))
        opts.update(kw)
        return tk.Text(parent, **opts)

    def _readonly_text(self, parent, **kw):
        """只读展示区（内容、预览、诊断报告共用）。"""
        T = THEME
        opts = dict(wrap="word", relief="flat", borderwidth=0, highlightthickness=1,
                    highlightbackground=T["border1"], highlightcolor=T["border1"],
                    bg=T["card"], fg=T["fg"], insertbackground=T["fg"],
                    selectbackground=T["sel"], selectforeground=T["fg"],
                    font=(self.font, -int(round(ui(9) * FONT_BOOST))),
                    padx=ui(10), pady=ui(8), state="disabled")
        opts.update(kw)
        return tk.Text(parent, **opts)

    # ---------------- 左侧栏：导航 + 底部操作 ----------------
    PAGES = ("填写需求", "先查查", "历史记录", "使用说明")

    def _build_sidebar(self, parent):
        T = THEME
        # 宽度先给一个初值，建完内容后由 _fit_sidebar_width() 按实际文字量重算。
        #
        # 为什么必须算：原来写死 214px，那是按中文量的。切到英文后
        # 「Language (English)」「Display diagnostics」这类标签更长，
        # 会被 pack_propagate(False) 直接截断（截图里能看到 "I" 这种断头）。
        bar = tk.Frame(parent, bg=T["sidebar"], width=ui(214))
        bar.pack(side="left", fill="y")
        bar.pack_propagate(False)
        # 右侧 1px 分隔线，对应它的 border-l3
        tk.Frame(parent, bg=T["border3"], width=1).pack(side="left", fill="y")
        self.sidebar = bar

        # 品牌行
        brand = tk.Frame(bar, bg=T["sidebar"])
        brand.pack(fill="x", padx=ui(14), pady=(ui(14), ui(10)))
        tk.Label(brand, text="◈", bg=T["sidebar"], fg=T["fg"],
                 font=(self.font, -int(round(ui(15) * FONT_BOOST)))).pack(side="left")
        tk.Label(brand, text=t("小白造软件"), bg=T["sidebar"], fg=T["fg"],
                 font=(self.font, -int(round(ui(11) * FONT_BOOST)), "bold")
                 ).pack(side="left", padx=(ui(8), 0))
        tk.Label(brand, text=t("助手"), bg=T["sidebar"], fg=T["fg3"],
                 font=(self.font, -int(round(ui(11) * FONT_BOOST)))
                 ).pack(side="left", padx=(ui(3), 0))
        self._side_brand = (t("小白造软件"), t("助手"))

        tk.Frame(bar, bg=T["sidebar"], height=ui(4)).pack()

        # 导航项
        self.nav_rows = {}
        self.nav_labels = {}
        self._side_texts = [t(name) for name in self.PAGES]
        for i, name in enumerate(self.PAGES):
            self.nav_rows[i] = self._nav_row(bar, i, t(name))

        # 底部：主题、语言、显示大小、存档位置、诊断、退出
        foot = tk.Frame(bar, bg=T["sidebar"])
        foot.pack(side="bottom", fill="x", padx=ui(10), pady=ui(10))
        foot_texts = [
            t("◐  切换主题（%s）") % THEME["name"],
            t("🌐  界面语言（%s）") % lang_display_name(),
            t("🔍  显示大小 %d%%") % int(round(UI_SCALE * 100)),
            t("📁  存档保存在哪"),
            t("🩺  显示诊断"),
            t("✕  退出"),
        ]
        self._side_texts.extend(foot_texts)
        for text, cmd in zip(foot_texts,
                             (self.toggle_theme, self.show_lang_dialog,
                              self.show_scale_dialog, self.show_data_location,
                              self.show_diagnostics, self.on_close)):
            self._side_btn(foot, text, cmd)

        self._fit_sidebar_width()

    def _fit_sidebar_width(self):
        """按侧栏里最宽的那条文字算出侧栏宽度，避免任何语言被截断。

        用 tkfont 实测（不是估算字符数）：中文和英文的字宽差别很大，
        估算法在混排（如「Language (English)」）时会明显偏。
        """
        try:
            import tkinter.font as tkfont

            nav_font = tkfont.Font(font=(self.font, -int(round(ui(10) * FONT_BOOST))))
            btn_font = tkfont.Font(font=(self.font, -int(round(ui(9.5) * FONT_BOOST))))
            brand_font = tkfont.Font(font=(self.font, -int(round(ui(11) * FONT_BOOST)), "bold"))

            nav_w = max([nav_font.measure(s) for s in self._side_texts[:len(self.PAGES)]] or [0])
            foot_w = max([btn_font.measure(s) for s in self._side_texts[len(self.PAGES):]] or [0])
            # 底部按钮有左右内边距，实际更宽
            foot_w += ui(22)
            brand_w = brand_font.measure(self._side_brand[0]) + nav_font.measure(self._side_brand[1])
            brand_w += ui(15 + 8 + 3 + 28)      # 图标 + 间距 + 左右内边距

            need = max(nav_w, foot_w, brand_w) + ui(30)
            width = max(ui(200), min(ui(360), need))
            self.sidebar.configure(width=width)
            self.sidebar_width = width
        except Exception:  # noqa: BLE001  量宽度失败不该影响启动
            self.sidebar_width = ui(214)

    def _nav_row(self, parent, index, text):
        """一个导航项：鼠标悬停有底色，选中态有左侧色条和强调底色。"""
        T = THEME
        row = tk.Frame(parent, bg=T["sidebar"])
        row.pack(fill="x", padx=ui(6), pady=ui(1))
        accent = tk.Frame(row, bg=T["sidebar"], width=ui(3))
        accent.pack(side="left", fill="y")
        label = tk.Label(row, text=text, bg=T["sidebar"], fg=T["fg2"], anchor="w",
                         padx=ui(8), pady=ui(8),
                         font=(self.font, -int(round(ui(10) * FONT_BOOST))))
        label.pack(side="left", fill="x", expand=True)
        self.nav_labels[index] = label

        holder = {"accent": accent, "row": row, "label": label}

        def paint(active=False, hover=False):
            bg = T["active_nav"] if active else (T["hover"] if hover else T["sidebar"])
            fg = T["fg"] if (active or hover) else T["fg2"]
            row.configure(bg=bg)
            label.configure(bg=bg, fg=fg)
            accent.configure(bg=T["brand"] if active else bg)

        def enter(_e):
            if self.page_index != index:
                paint(hover=True)
            return None

        def leave(_e):
            paint(active=(self.page_index == index))
            return None

        def click(_e):
            self._select_page(index)
            return None

        for w in (row, label, accent):
            w.bind("<Button-1>", click)
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
        holder["paint"] = paint
        return holder

    def _side_btn(self, parent, text, command):
        """侧栏底部的一枚按钮。"""
        T = THEME
        btn = tk.Label(parent, text=text, bg=T["sidebar"], fg=T["fg2"], anchor="w",
                       padx=ui(9), pady=ui(6), cursor="hand2",
                       font=(self.font, -int(round(ui(9) * FONT_BOOST))))
        btn.pack(fill="x")
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(bg=T["hover"], fg=T["fg"]))
        btn.bind("<Leave>", lambda e: btn.configure(bg=T["sidebar"], fg=T["fg2"]))
        return btn

    def _select_page(self, index):
        """切换右侧显示哪一页，并同步侧栏选中态。"""
        self.page_index = index
        keys = ("fill", "lookup", "history", "about")
        key = keys[index] if 0 <= index < len(keys) else "fill"
        self._show_page(key, index)

    def select_page_by_key(self, key):
        """按页面名切换。

        为什么要有这个入口：**索引会随插页而位移**。
        新增「先查查」页后，原来 show_about() 里的 _select_page(2)
        就从「使用说明」变成了「历史记录」，而且不报错、只是打开错的页。
        凡是"指到某一页"的地方都应按名字来。
        """
        keys = ("fill", "lookup", "history", "about")
        if key not in keys:
            key = "fill"
        idx = keys.index(key)
        self.page_index = idx
        self._show_page(key, idx)

    def _show_page(self, key, index):
        for name, frame in getattr(self, "pages", {}).items():
            if name == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        for i, holder in self.nav_rows.items():
            holder["paint"](active=(i == index))

    # ---------------- 主体 ----------------
    def _build_body(self):
        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)

        main = ttk.Frame(body)
        main.pack(side="left", fill="both", expand=True)
        self.main_col = main

        # ★ 不用 ttk.Notebook：它的页签条没法可靠隐藏（试过改 ttk 布局也没用，
        #   截图里那排页签依然在）。改用「叠放 Frame，只显示其中一个」，
        #   结构更简单，也不会留下多余的一条。
        p1 = ttk.Frame(main)
        p1.pack(fill="both", expand=True)
        self.pages = {"fill": p1}

        # 标题行
        head = ttk.Frame(p1)
        head.pack(fill="x")
        ttk.Label(head, text=t("把想法说清楚，剩下的交给 AI"),
                  style="Title.TLabel").pack(anchor="w", padx=ui(18), pady=(ui(14), ui(2)))
        ttk.Label(head, text=t("① 左边填一填   →   ② 右边自动生成   →   ③ 点「复制需求」粘贴给 AI"
                               "　·　每题下面有「看例子」，标着「可选」的可以不填"),
                  style="Sub.TLabel").pack(anchor="w", padx=ui(18), pady=(0, ui(8)))

        cols = ttk.Frame(p1, padding=(ui(14), 0, ui(14), 0))
        cols.pack(fill="both", expand=True)

        left = ttk.Frame(cols)
        left.pack(side="left", fill="both", expand=True)

        # 右侧预览栏宽度跟着缩放走，窄屏上最多占 45%
        right_w = ui(470)
        right_w = min(right_w, int(screen_size(self.root)[0] * 0.45))
        right = ttk.Frame(cols, width=right_w)
        right.pack(side="right", fill="both", expand=False, padx=(ui(10), 0))
        right.pack_propagate(False)

        self._build_form(left)
        self._build_preview(right)

        # ---- 另外两页：先建好但不显示 ----
        self._build_history_pages(main)

    def _build_history_pages(self, main):
        """历史记录页和使用说明页：都建好，切换时只显示其中一个。"""
        hist = ttk.Frame(main)
        self.pages["history"] = hist
        self._build_history(hist)

        about = ttk.Frame(main)
        self.pages["about"] = about
        txt = self._readonly_text(about, font=(self.font, -int(round(ui(11) * FONT_BOOST))),
                                  padx=ui(18), pady=ui(14))
        sb = ttk.Scrollbar(about, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True, padx=ui(14), pady=ui(10))
        txt.configure(state="normal")
        txt.insert("1.0", ABOUT_TEXT.format(app=APP_NAME, ver=APP_VERSION))
        txt.configure(state="disabled")
        self.about_text = txt

        look = ttk.Frame(main)
        self.pages["lookup"] = look
        self._build_lookup(look)

    # ---------------- 先查查页（动手前看 GitHub 有没有现成的）----------------
    def _build_lookup(self, p):
        """查重页。

        ★ 联网只在这一页、且只在点「查一下」时发生。
          启动程序、填问卷、生成需求说明的过程一律不碰网络 ——
          这是「填的内容不会自动上传」这句承诺的前提。
        """
        T = THEME
        head = ttk.Frame(p)
        head.pack(fill="x", pady=(0, 6))
        ttk.Label(head, text=t("动手做之前，先看看 GitHub 上有没有现成的"),
                  style="QTitle.TLabel").pack(anchor="w")
        ttk.Label(head,
                  text=t("很多需求已经有成熟方案了。先查一眼，能省掉大量重复劳动；"
                         "如果有能用的，拿现成的改通常比从零做更可靠。"),
                  style="Sub.TLabel", justify="left",
                  wraplength=ui(760)).pack(anchor="w", pady=(ui(2), ui(8)))

        # 查询词
        row = ttk.Frame(p)
        row.pack(fill="x", pady=(0, 4))
        ttk.Label(row, text=t("查什么（可以自己改）：")).pack(side="left")
        self.lookup_query = tk.StringVar()
        ttk.Entry(row, textvariable=self.lookup_query).pack(side="left", fill="x",
                                                           expand=True, padx=(6, 6))
        ttk.Button(row, text=t("🔄 从我的答案生成"), command=self.lookup_fill_query
                   ).pack(side="left")

        # 说明：网络行为必须讲清楚，不能偷偷联网
        ttk.Label(p,
                  text=t("点下面按钮才会联网（只把上面这行字发给 GitHub，"
                         "你填的需求正文不会发出去）；不点就一直离线。"),
                  style="Sub.TLabel", justify="left",
                  wraplength=ui(760)).pack(anchor="w", pady=(0, 8))

        btns = ttk.Frame(p)
        btns.pack(fill="x", pady=(0, 8))
        ttk.Button(btns, text=t("🔍 查一下 GitHub（会联网）"),
                   style="Big.TButton", command=self.lookup_search).pack(side="left")
        ttk.Button(btns, text=t("📋 复制「让 AI 帮我查」的指令（不联网）"),
                   command=self.lookup_copy_instruction).pack(side="left", padx=8)

        self.lookup_progress = ttk.Label(p, text="", style="Sub.TLabel")
        self.lookup_progress.pack(anchor="w", pady=(0, 4))

        box = ttk.Frame(p)
        box.pack(fill="both", expand=True)
        self.lookup_text = self._readonly_text(
            box, font=(self.font, -int(round(ui(10.5) * FONT_BOOST))),
            padx=ui(12), pady=ui(10))
        sb = ttk.Scrollbar(box, command=self.lookup_text.yview)
        self.lookup_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.lookup_text.pack(fill="both", expand=True)
        self._lookup_set_text(
            t("点「从我的答案生成」得到查询词，再点「查一下 GitHub」。\n\n"
              "连不上网也没关系：用「复制让 AI 帮我查的指令」，"
              "把那段话粘给 AI，它会帮你搜并评估能不能用。"))

    # ---------------- 查重页的动作 ----------------
    def _lookup_set_text(self, content):
        """写只读展示区（只读控件要先临时解锁）"""
        self.lookup_text.configure(state="normal")
        self.lookup_text.delete("1.0", "end")
        self.lookup_text.insert("1.0", content)
        self.lookup_text.configure(state="disabled")

    def lookup_fill_query(self):
        """从当前答案生成查询词，填进输入框（不联网）"""
        answers = self.collect()
        queries = github_lookup.build_queries(answers)
        if not queries:
            self.lookup_query.set("")
            self._lookup_set_text(
                t("还没填「你想做什么」那一格，所以生成不出查询词。\n\n"
                  "回到「填写需求」页填一两格再回来。"))
            return
        # 用英文检索词：GitHub 上中文关键词命中率很低（实测整句中文返回 0 个）
        raw, hits = github_lookup.to_search_query(queries[0])
        self.lookup_query.set(raw)
        note = ""
        if hits:
            note = t("\n\n（从你的描述里识别到：%s，已转成 GitHub 上更好搜的英文词）"
                     % "、".join(hits[:5]))
        self._lookup_set_text(
            t("查询词已填好：%s\n\n点「查一下 GitHub」开始搜。\n"
              "搜之前可以自己改这行字。") % raw + note)

    def lookup_copy_instruction(self):
        """把「让 AI 帮你查」的指令复制走（不联网）"""
        answers = self.collect()
        queries = github_lookup.build_queries(answers)
        if not queries:
            queries = [t("（先回到「填写需求」页填一两格，再回来生成关键词）")]
        text = github_lookup.build_ai_instruction(queries)
        ok = self._copy(text)
        self._lookup_set_text(text)
        if ok:
            self.lookup_progress.configure(
                text=t("指令已复制。切到 AI 对话框，按 Ctrl+V 粘贴发送就行。"))
        else:
            self.lookup_progress.configure(text=t("复制失败，可以直接从下面框里选中复制。"))

    def lookup_search(self):
        """联网查 GitHub。★ 这是整个程序里唯一会联网的动作，且由用户点击触发。"""
        query = (self.lookup_query.get() or "").strip()
        if not query:
            messagebox.showinfo(t("还没有查询词"),
                                t("先点「从我的答案生成」，或者自己写几个关键词。"),
                                parent=self.root)
            return
        # 明确告知会联网 —— 隐私上不能含糊
        if not messagebox.askyesno(
                t("要联网了"),
                t("接下来会把这一行字发给 GitHub 搜索：\n\n%s\n\n"
                  "• 你填的需求正文**不会**发出去\n"
                  "• 只搜公开项目，不登录、不提交任何东西\n\n要继续吗？") % query,
                parent=self.root):
            return

        self.lookup_progress.configure(text=t("正在查 GitHub…"))
        self.root.update_idletasks()
        repos, err = github_lookup.search_repos(query, per_page=8)
        if err:
            self.lookup_progress.configure(text=t("没查成"))
            self._lookup_set_text(
                err + "\n\n" + t("可以用下面的办法：点「复制让 AI 帮我查的指令」，"
                                 "粘给 AI 让它帮你搜。"))
            return

        terms = [x for x in query.split() if len(x) >= 2]
        kept, dropped = github_lookup.rank_repos(repos, terms)
        verdict = github_lookup.judge(kept, terms=terms)

        parts = []
        if dropped:
            parts.append(t("（搜到 %d 个，其中 %d 个与你的需求明显无关，已排除 —— "
                           "GitHub 按星数排时经常把无关的高星项目排在最前）")
                         % (len(repos), dropped))
            parts.append("")
        parts.append(github_lookup.format_report(kept or repos, verdict))
        parts.append("")
        parts.append(t("——————"))
        parts.append(t("这个结论只看客观信号（相关性、星数、是否还在更新、许可证），"
                       "不替你做判断。拿不准就把上面的链接发给 AI 让它帮你评估。"))
        self._lookup_set_text("\n".join(parts))
        self.lookup_progress.configure(
            text=t("查完了：%s") % verdict["headline"])

    # ---------------- 历史记录页 ----------------
    def _build_history(self, p):
        T = THEME
        bar = ttk.Frame(p)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text=t("你点过「保存到文件」的需求都收在这里，随时可以找回来改。"),
                  style="Sub.TLabel").pack(side="left")
        ttk.Button(bar, text=t("🔄 刷新"), command=self.refresh_history).pack(side="right")
        ttk.Button(bar, text=t("📂 打开存档文件夹"), command=self.open_archive_dir).pack(side="right", padx=6)

        panes = ttk.PanedWindow(p, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes, padding=(0, 0, 6, 0))
        right = ttk.Frame(panes)
        panes.add(left, weight=1)
        panes.add(right, weight=2)

        ttk.Label(left, text=t("存档列表（双击可载入）")).pack(anchor="w")
        lf = ttk.Frame(left)
        lf.pack(fill="both", expand=True, pady=(ui(4), 0))
        # Listbox 不是 ttk 控件，颜色得一个个给，否则底色会跟主题打架
        self.hist_list = tk.Listbox(
            lf, activestyle="none", selectmode="browse", exportselection=False,
            relief="flat", borderwidth=0, highlightthickness=1,
            highlightbackground=T["border1"], highlightcolor=T["border2"],
            bg=T["card"], fg=T["fg"], selectbackground=T["sel"],
            selectforeground=T["fg"], font=(self.font, -int(round(ui(10) * FONT_BOOST))))
        hsb = ttk.Scrollbar(lf, orient="vertical", command=self.hist_list.yview)
        self.hist_list.configure(yscrollcommand=hsb.set)
        hsb.pack(side="right", fill="y")
        self.hist_list.pack(side="left", fill="both", expand=True)
        self.hist_list.bind("<<ListboxSelect>>", self.on_history_select)
        self.hist_list.bind("<Double-Button-1>", lambda e: self.load_history())

        ttk.Label(right, text=t("内容预览")).pack(anchor="w")
        rf = ttk.Frame(right)
        rf.pack(fill="both", expand=True, pady=(ui(4), 0))
        self.hist_text = self._readonly_text(rf)
        rsb = ttk.Scrollbar(rf, command=self.hist_text.yview)
        self.hist_text.configure(yscrollcommand=rsb.set)
        rsb.pack(side="right", fill="y")
        self.hist_text.pack(side="left", fill="both", expand=True)

        hb = ttk.Frame(p)
        hb.pack(fill="x", pady=(6, 0))
        self.btn_load = ttk.Button(hb, text=t("↩ 载入到填写页修改"), style="Big.TButton",
                                   command=self.load_history, state="disabled")
        self.btn_load.pack(side="left")
        ttk.Button(hb, text=t("📋 复制这份内容"), command=self.copy_history).pack(side="left", padx=8)
        ttk.Button(hb, text=t("🗑 删除这份存档"), command=self.delete_history).pack(side="left")
        self.hist_status = ttk.Label(hb, text="", style="Sub.TLabel")
        self.hist_status.pack(side="right")

        self.hist_paths = []

    def read_archive(self, path):
        """读取一份存档。返回 (给AI看的正文, 原始答案dict 或 None)。"""
        try:
            with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
                raw = f.read()
        except OSError as e:
            return f"（读取失败：{e}）", None
        answers = None
        if DATA_MARK in raw:
            body, _, tail = raw.partition(DATA_MARK)
            tail = tail.split(DATA_END)[0]
            try:
                answers = json.loads(tail.strip())
            except (ValueError, TypeError):
                answers = None
            if answers is not None:
                return body.rstrip(), answers
        # 老版本存档：按生成的标题结构尽力还原
        answers = self._parse_legacy(raw)
        return raw.rstrip(), answers

    def _parse_legacy(self, raw):
        """从旧存档的 Markdown 结构里反推 12 格内容；识别不出就返回 None 或部分。"""
        heads = {}
        for q in self._active_questions():
            heads[q["title"]] = q["key"]
        answers, current = {}, None
        for ln in raw.splitlines():
            s = ln.strip()
            if s.startswith("### "):
                current = heads.get(s[4:].strip())
                if current:
                    answers.setdefault(current, "")
            elif current:
                if s and not s.startswith("（这一格还没填"):
                    body = ln.strip()
                    if body.startswith("✔ "):
                        body = body[2:]
                    answers[current] = (answers[current] + "\n" + body).strip()
        return answers or None

    def refresh_history(self):
        self.hist_paths = []
        self.hist_list.delete(0, "end")
        try:
            files = [os.path.join(ARCHIVE_DIR, n) for n in os.listdir(ARCHIVE_DIR)
                     if n.lower().endswith(".txt")]
        except OSError:
            files = []
        files.sort(key=os.path.getmtime, reverse=True)
        for p in files:
            self.hist_paths.append(p)
            base = os.path.basename(p)
            stamp, _, title = base.partition("_")
            try:
                when = datetime.strptime(stamp, "%Y%m%d_%H%M%S").strftime("%m-%d %H:%M")
            except ValueError:
                when = stamp
            self.hist_list.insert("end", f"{when}   {title[:-4] or '未命名'}")
        n = len(self.hist_paths)
        self.hist_status.configure(text=f"共 {n} 份存档" if n else "还没有存档")
        if not n:
            self._set_hist_text("这里还是空的。\n\n"
                                "回到「填写需求」那页，填好之后点左下角「💾 保存到文件」，\n"
                                "以后就能在这里找回、修改、重新复制了。")
            self.btn_load.configure(state="disabled")

    def _set_hist_text(self, s):
        self.hist_text.configure(state="normal")
        self.hist_text.delete("1.0", "end")
        self.hist_text.insert("1.0", s)
        self.hist_text.configure(state="disabled")

    def _selected_history_path(self):
        sel = self.hist_list.curselection()
        if not sel:
            return None
        i = int(sel[0])
        return self.hist_paths[i] if 0 <= i < len(self.hist_paths) else None

    def on_history_select(self, event=None):
        path = self._selected_history_path()
        if not path:
            return
        body, answers = self.read_archive(path)
        shown = body
        if answers:
            missing = [k for k in (q["key"] for q in self._active_questions()) if k not in answers]
            shown += ("\n\n" + "-" * 40 +
                      "\n（这份存档带有原始答案，可以点「载入到填写页修改」整份还原）")
            if missing:
                shown += f"\n（有 {len(missing)} 格当时没填，我会让 AI 直接问你）"
        self._set_hist_text(shown)
        self.btn_load.configure(state="normal")

    def copy_history(self):
        path = self._selected_history_path()
        if not path:
            messagebox.showinfo(t("还没有选中"), t("请先在左边列表里点一份存档。"))
            return
        body, _ = self.read_archive(path)
        self.root.clipboard_clear()
        self.root.clipboard_append(body)
        self.root.update_idletasks()
        self.hist_status.configure(text="已复制这份内容 ✔")

    def load_history(self):
        path = self._selected_history_path()
        if not path:
            messagebox.showinfo(t("还没有选中"), t("请先在左边列表里点一份存档。"))
            return
        _, answers = self.read_archive(path)
        if not answers:
            messagebox.showwarning(t("无法完整还原"),
                                   "这份存档是旧版本保存的，认不出原始答案。\n\n"
                                   "你可以点「复制这份内容」把它发给 AI。")
            return
        for q in self._active_questions():
            key = q["key"]
            box = self.widgets[key]
            box.delete("1.0", "end")
            val = (answers.get(key) or "").strip()
            if val:
                # ★ 必须用主题色，不能写死深色。
                #   原来这里硬编码 "#1b1b1b"（浅色主题的正文色），
                #   暗色主题下背景是 #1d1e21，文字几乎和背景一样黑 ——
                #   表现就是「打完字看不见自己打了什么」。实测复现过。
                box.configure(foreground=THEME["fg"])
                box.insert("1.0", val)
            else:
                box.configure(foreground=PLACEHOLDER_FG)
                box.insert("1.0", t(_qval(q, "example")))
        # 输入的答案里可能带着点选产生的勾号行，勾选框状态要同步
        marked = set()
        for q in self._active_questions():
            for ln in (answers.get(q["key"]) or "").splitlines():
                ln = ln.strip()
                if ln.startswith("✔ "):
                    marked.add(ln)
        for key in [q["key"] for q in self._active_questions()]:
            self.selected[key].clear()
        for (key, opt), (var, cb, o) in self.option_buttons.items():
            on = ("✔ " + opt) in marked
            var.set(on)
            if on:
                self.selected[key].add(opt)
        for q in self._active_questions():
            self._on_typing(q["key"])
        self._select_page(0)
        self.set_status(t("已载入存档，改完再点「复制需求」发给 AI 就行。"))

    def open_archive_dir(self):
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        try:
            os.startfile(ARCHIVE_DIR)
        except OSError as e:
            messagebox.showwarning(t("打不开文件夹"), str(e))

    def show_data_location(self):
        """把数据位置完整显示出来，并给一个「打开文件夹」的入口。"""
        note = data_location_note() or (t("存档和设置保存在程序旁边：") + APP_DIR)
        top = tk.Toplevel(self.root)
        top.title(t("存档保存在哪"))
        top.geometry("%dx%d" % (ui(620), ui(240)))
        top.transient(self.root)
        frame = ttk.Frame(top, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=note, style="QHint.TLabel", justify="left",
                  wraplength=ui(560)).pack(anchor="w")
        txt = tk.Text(frame, height=3, wrap="char", relief="solid", borderwidth=1,
                      highlightthickness=0, padx=ui(8), pady=ui(6),
                      font=(self.font, -int(round(ui(9) * FONT_BOOST))))
        txt.pack(fill="x", pady=(ui(6), ui(8)))
        txt.insert("1.0", ARCHIVE_DIR)
        txt.configure(state="disabled")
        btns = ttk.Frame(frame)
        btns.pack(fill="x")
        ttk.Button(btns, text=t("打开这个文件夹"),
                   command=self.open_archive_dir).pack(side="left")
        ttk.Button(btns, text=t("知道了"), command=top.destroy).pack(side="right")
        top.bind("<Escape>", lambda e: top.destroy())

    def delete_history(self):
        path = self._selected_history_path()
        if not path:
            messagebox.showinfo(t("还没有选中"), t("请先在左边列表里点一份存档。"))
            return
        if not messagebox.askyesno("确认删除",
                                   "要把这份存档删掉吗？删了就找不回来了。\n\n"
                                   + os.path.basename(path)):
            return
        try:
            os.remove(path)
        except OSError as e:
            messagebox.showerror(t("删除失败"), str(e))
            return
        self.refresh_history()
        self._set_hist_text("（已删除，请在左边另选一份）")
        self.btn_load.configure(state="disabled")

    def _build_form(self, parent):
        T = THEME
        # 记住建表单时用的平台族和类型：第 1/3 题改了以后要靠它们判断要不要重建。
        # 注意不能调 collect()：这里输入框还没建出来。
        _saved = self._saved_answers()
        self._fam_built = current_family(_saved)
        self._kind = current_kind(_saved)
        self.hint_labels = []
        wrap = ttk.Frame(parent)
        wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(wrap, highlightthickness=0, bg=T["bg"])
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self._on_scrollbar)
        # ★ 不用 canvas 自带的 yscrollcommand：改成走 _scroll_set，
        #   这样滚动条位置和画面滚动都经过同一套「合并重绘」逻辑。
        self.canvas.configure(yscrollcommand=self._scroll_set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb = vsb

        self.inner = ttk.Frame(self.canvas)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfigure(self.inner_id, width=e.width))
        # 统一的折行回调：只注册一次，遍历当前活着的说明 Label（见 _reflow_hints）。
        # ★ 必须放在 self.canvas 创建之后。
        self.canvas.bind("<Configure>", self._reflow_hints, add="+")

        # ★ 残影的根因：这个表单区有 185 个控件，一次完整重绘要 6~11ms。
        #   快速拖滚动条时每个像素都触发一次 yview，重绘请求堆积起来就出现残影。
        #   这里把滚动请求合并：一帧只真正重绘一次。
        self._scroll_job = None
        self._scroll_frac = 0.0
        self._scroll_last = 0.0
        self._scroll_drawn = -1.0

        def _wheel(event):
            # 一格滚轮滚 3 个单位，比默认 1 个单位顺手
            delta = -3 * (event.delta // 120) if event.delta else 0
            self.canvas.yview_scroll(delta, "units")
        for w in (self.canvas, self.inner):
            w.bind("<MouseWheel>", _wheel)
        # ★ 但只绑这两个是不够的：鼠标停在输入框 / 勾选框 / 提示文字上时，
        #   事件落在那些子控件上，根本传不到 canvas，滚轮就"失灵"。
        #   所以再加一层全局路由：无论指针在哪，自动判断该滚哪个区域。
        self.root.bind_all("<MouseWheel>", self._route_wheel, add="+")
        # 键盘翻页 / 上下键
        self.canvas.configure(takefocus=1)
        for seq, amount in (("<Prior>", -1), ("<Next>", 1)):
            self.canvas.bind(seq, lambda e, a=amount: self._scroll_pages(a))
        self.canvas.bind("<Up>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Down>", lambda e: self.canvas.yview_scroll(1, "units"))

        for q in self._active_questions():
            self._build_card(q)

    # ---- 滚轮路由：指针在哪个可滚区域上，就滚哪个 ----
    @staticmethod
    def _is_inside(widget, ancestor):
        """widget 是否在 ancestor 里面（widget 本身也算）。"""
        w = widget
        while w is not None:
            if w == ancestor:
                return True
            w = getattr(w, "master", None)
        return False

    def _route_wheel(self, event):
        """全局滚轮处理。

        必须自己处理并 break：因为一旦接管了滚轮，Tk 默认的
        「焦点在 Text 上才滚」那套逻辑就不可靠了，
        输入框/预览框的滚轮也要靠这里分发。
        """
        w = event.widget
        if w is None or w.winfo_toplevel() is not self.root:
            return None                     # 弹窗里的滚轮不归我管
        delta = (event.delta // 120) if event.delta else 0
        if not delta:
            return "break"

        # 1) 指针在右边预览框上 → 滚预览
        if self._is_inside(w, self.preview):
            self.preview.yview_scroll(-delta, "units")
            return "break"
        # 2) 指针在某个输入框上 → 那个输入框自己内容超过一屏才滚它，
        #    否则让外层表单跟着滚（用户就是想翻页）
        if isinstance(w, tk.Text) and w is not self.preview:
            try:
                first, last = w.yview()
            except tk.TclError:
                first, last = 0.0, 1.0
            if not (first <= 0.0 and last >= 1.0):
                w.yview_scroll(-delta, "units")
                return "break"
        # 3) 指针在表单区（含卡片、勾选框、提示文字）→ 滚外层表单
        if self._is_inside(w, self.canvas):
            self.canvas.yview_scroll(-3 * delta, "units")
            return "break"
        return None

    # ---- 滚动（限流重绘，消除残影）----
    # 残影的根因：这个表单区有 185 个控件，一次完整重绘要 6~7ms。
    # 快速拖滚动条时事件来得比画面刷得还快，重绘请求堆积 → 看到残影。
    # 实测（100 个拖拽事件）：
    #     限流 18ms → 重绘 47 次，耗时 1084ms
    #     限流 33ms → 重绘 23 次，耗时  863ms  ← 采用
    #     限流 50ms → 重绘 14 次，耗时  764ms（但画面开始发滞）
    # 三种情况下落点误差都是 0（拖到底就停到底）。
    SCROLL_MIN_REDRAW_MS = 33      # ≈30fps：重绘次数减半，又不会发滞

    def _scroll_set(self, first, last):
        """canvas 滚动变化时回调：更新滚动条位置。"""
        try:
            self.vsb.set(first, last)
        except tk.TclError:
            pass

    def _on_scrollbar(self, *args):
        """滚动条被拖动/点击时：记住目标位置，按限流节奏重绘。"""
        try:
            if args and args[0] == "moveto":
                self._scroll_frac = float(args[1])
            elif args and args[0] == "scroll":
                delta = int(args[1])
                page = self.canvas.winfo_height() or 1
                total = max(1, self.inner.winfo_reqheight())
                self._scroll_frac += (delta * page / 10.0) / total
            else:
                return
        except (ValueError, IndexError):
            return
        self._scroll_frac = min(1.0, max(0.0, self._scroll_frac))
        self._throttled_scroll()

    def _throttled_scroll(self):
        if self._scroll_job is not None:
            return                       # 已经排好一次，等它执行
        # 关键：距上次重绘已超过限流间隔时（例如刚开始拖），用 after(1) 尽快执行，
        # 保证「一按滚动条马上有反应」；只有连续拖动才会被压到 18ms 一次。
        elapsed = (time.monotonic() - self._scroll_last) * 1000.0
        wait = 1 if elapsed >= self.SCROLL_MIN_REDRAW_MS else max(
            1, int(self.SCROLL_MIN_REDRAW_MS - elapsed))
        self._scroll_job = self.canvas.after(wait, self._do_scroll)

    def _do_scroll(self):
        self._scroll_job = None
        target = self._scroll_frac
        try:
            self.canvas.yview_moveto(target)
        except tk.TclError:
            return
        self._scroll_drawn = target          # ★ 记录「真正画到哪」，不是目标值
        self._scroll_last = time.monotonic()
        # 用 update() 而不是 update_idletasks()：前者会把重绘也一并处理完，
        # 保证这一帧是「画完整」的，减少半截画面的残留。
        try:
            self.canvas.update()
        except tk.TclError:
            return
        # 限流期间用户又拖到别处了 → 再排一次，保证最终停在用户要的位置。
        # 注意要和 _scroll_drawn（已画位置）比，不能和 target 比，否则永远不相等、死循环。
        if abs(self._scroll_drawn - self._scroll_frac) > 1e-9:
            self._throttled_scroll()

    def _scroll_pages(self, direction):
        page = self.canvas.winfo_height() or 1
        total = max(1, self.inner.winfo_reqheight())
        self._on_scrollbar("moveto", str(min(1.0, max(0.0,
                          self.canvas.canvasy(0) / total + direction * page / total))))

    def _build_card(self, q):
        T = THEME
        # 每个题号都要有 selected 表项（即使没有选项），否则载入/清空会漏
        self.selected.setdefault(q["key"], set())

        # ★ 按当前平台族把这一题调整一遍（标题/说明/示例/选项都可能变）
        #   规则在 questionnaire.py，这里只取结果。
        aq = self._adapted(q)
        self.adapted[q["key"]] = aq

        # 整张卡片是一个平面 + 1px 细边框（对齐它的 bg-layer-1 / border-l1）
        card = tk.Frame(self.inner, bg=T["card"], highlightbackground=T["border1"],
                        highlightthickness=1)
        card.pack(fill="x", expand=True, padx=(0, ui(6)), pady=(0, ui(8)))

        head = tk.Frame(card, bg=T["card"])
        head.pack(fill="x", padx=ui(12), pady=(ui(10), 0))

        title = t(aq["title"]) + ("" if q.get("required") else t("   （可选）"))
        ttk.Label(head, text=title, style="QTitle.TLabel").pack(side="left")

        # 给个准确的小提示，让用户知道「问题会跟着我的选择变」：
        #   · 按「做什么类型」新加/换过的题 → 说类型
        #   · 按「跑在什么平台」改过措辞的题 → 说平台
        # （早先一律写「已按你的平台调整」，对因类型而变的题是错的 —— 截图时发现）
        if aq["key"] != "kind":
            if aq.get("kind_theme"):
                ttk.Label(head, text=t("· 已按你的类型调整"), style="QHint.TLabel"
                          ).pack(side="left", padx=(ui(8), 0))
            elif aq.get("adapted"):
                ttk.Label(head, text=t("· 已按你的平台调整"), style="QHint.TLabel"
                          ).pack(side="left", padx=(ui(8), 0))

        ttk.Button(head, text=t("看例子"), style="Small.TButton",
                   command=lambda qq=q: self.show_help(qq)).pack(side="right")

        status = ttk.Label(head, text=t("待填写"), style="QHint.TLabel")
        status.pack(side="right", padx=(0, ui(8)))
        self.widgets[q["key"] + "__status"] = status

        hint = ttk.Label(card, text=t(aq["hint"]), style="QHint.TLabel",
                         wraplength=ui(680), justify="left")
        hint.pack(anchor="w", padx=ui(12), pady=(ui(3), 0))
        # 窗口拉宽时自动折行。
        #
        # ★ 这里只**登记**控件，不绑事件：
        #   原来每建一张卡片就往 canvas 上 bind 一个 lambda，有 2 个问题 ——
        #   1) 13 张卡片 = 13 个回调，重复注册
        #   2) 问卷自适应重建表单后，旧控件已销毁，回调还指着它们，
        #      一拉窗口就 TclError: invalid command name ...
        #   改成 _build_form 里注册**一个**统一回调，遍历这张表。
        self.hint_labels.append(hint)

        # ★ Text 的 height 是「字符行数」，负值在 Tk 里不生效（实测会变成 1 行）。
        #   但【只要字体是具名字体】，Tk 的请求高度就会随字号严格等比放大
        #   （实测：字号 10 → 每行 16px，字号 25 → 每行 32px）。
        #   所以这里保持「可见行数」不变，框高自然跟着缩放走，不需要再乘一遍，
        #   否则会和字体放大叠加成平方级，屏幕上大得离谱。
        lines = 5 if q.get("multiline") else 2
        box = self._entry(card, height=lines)
        box.pack(fill="x", expand=True, padx=ui(12), pady=(ui(7), 0))
        box.insert("1.0", t(aq["example"]))
        box.configure(foreground=PLACEHOLDER_FG)
        box.bind("<FocusIn>", lambda e, b=box: self._clear_example(b))
        box.bind("<KeyRelease>", lambda e, k=q["key"]: self._on_typing(k))
        self.widgets[q["key"]] = box

        # 选项也用自适应后的那一份（手机/网页环境下和桌面不同）
        opts = aq["options"] or []
        if opts:
            of = tk.Frame(card, bg=T["card"])
            of.pack(fill="x", padx=ui(12), pady=(ui(6), ui(12)))
            tk.Label(of, text=t("快速点选（可多选，点了会写进上面的框）"), bg=T["card"],
                     fg=T["fg3"], font=(self.font, -int(round(ui(9) * FONT_BOOST)))
                     ).pack(anchor="w", pady=(0, ui(2)))
            # 注意：勾选框必须放在自己的子框里用 grid，
            # 不能在 of 里跟上面那个 pack 的 Label 混用（tkinter 会直接报错）
            grid = tk.Frame(of, bg=T["card"])
            grid.pack(fill="x", anchor="w")
            # ★ 列数必须按「真实文字宽度」算，而且必须等布局完成后再算 ——
            #   构建阶段 canvas 还没尺寸（量到的是 1），只能瞎估，
            #   估多了就出现被截断的「整个部」「手机上」（截图里能看到）。
            #   这里先单列排好，等窗口布局完由 _layout_options() 重排。
            self.opt_grids[q["key"]] = grid
            self.opt_boxes.setdefault(q["key"], [])
            for i, o in enumerate(opts):
                var = tk.BooleanVar(value=False)
                # ★ 显示的是译文，但**记录用的键始终是简体原文**：
                #   self.option_buttons[(key, o)] 和 self.selected 里都存原文，
                #   这样存档里的选项在切到英文/繁中后仍能正确还原。
                #   前提是同题内原文唯一 —— 由 tools/check_option_uniqueness.py 保证。
                cb = ttk.Checkbutton(grid, text=t(o), variable=var,
                                     command=lambda k=q["key"], oo=o: self._toggle(k, oo))
                cb.grid(row=i, column=0, sticky="w", padx=(0, ui(14)), pady=ui(3))
                self.option_buttons[(q["key"], o)] = (var, cb, o)
                self.opt_boxes[q["key"]].append(cb)
        else:
            tk.Frame(card, bg=T["card"], height=ui(10)).pack()

    def _layout_options(self):
        """按真实可用宽度决定每题选项排几列（必须布局完成后调用）。"""
        avail = max(ui(300), self._form_width() - ui(72))
        for key, cbs in getattr(self, "opt_boxes", {}).items():
            grid = self.opt_grids.get(key)
            if grid is None or not cbs:
                continue
            cols = min(4, len(cbs))
            while cols > 1:
                per = avail // cols
                fits = sum(1 for cb in cbs
                           if self._option_text_px(str(cb.cget("text"))) + ui(30) <= per)
                if fits >= len(cbs) - 1:      # 最多容忍一个放不下
                    break
                cols -= 1
            for i, cb in enumerate(cbs):
                cb.grid_configure(row=i // cols, column=i % cols)
            for c in range(cols):
                grid.grid_columnconfigure(c, weight=1, minsize=avail // cols)
            for c in range(cols, 6):
                try:
                    grid.grid_columnconfigure(c, weight=0, minsize=0)
                except tk.TclError:
                    pass

    def _form_width(self):
        """表单区能用的宽度（逻辑像素），用来算选项该排几列。"""
        try:
            w = self.canvas.winfo_width()
            if w > 1:
                return w
        except tk.TclError:
            pass
        # 还没布局完：按窗口宽度估算（减去侧栏、预览栏和滚动条）
        total = int(screen_size(self.root)[0])
        right = min(ui(470), int(total * 0.45))
        return max(ui(420), total - ui(214) - right - ui(60))

    def _option_text_px(self, text):
        """用真实字体量一段文字多宽（像素）—— 估算字宽不准，会截断。"""
        try:
            import tkinter.font as tkfont
            key = "dsh_opt_meas"
            f = tkfont.nametofont(key) if key in tkfont.names(self.root) else tkfont.Font(
                root=self.root, name=key, family=self.font,
                size=-max(7, int(round(ui(9) * FONT_BOOST))))
            return f.measure(text)
        except Exception:
            return len(text) * ui(10)

    def _build_preview(self, parent):
        T = THEME
        ttk.Label(parent, text=t("自动生成的需求说明"),
                  style="QTitle.TLabel").pack(anchor="w")
        ttk.Label(parent, text=t("点「复制需求」后粘贴给 AI 就行"), style="Sub.TLabel"
                  ).pack(anchor="w", pady=(ui(1), ui(6)))

        self.progress = ttk.Progressbar(parent, mode="determinate", maximum=len(self._active_questions()))
        self.progress.pack(fill="x", pady=(ui(4), ui(2)))
        self.progress_label = ttk.Label(parent, text="", style="Sub.TLabel")
        self.progress_label.pack(anchor="w")

        box = ttk.Frame(parent)
        box.pack(fill="both", expand=True, pady=(ui(6), 0))
        self.preview = self._readonly_text(box)
        self.preview.configure(state="normal")
        psb = ttk.Scrollbar(box, command=self.preview.yview)
        self.preview.configure(yscrollcommand=psb.set)
        psb.pack(side="right", fill="y")
        self.preview.pack(side="left", fill="both", expand=True)

    def _build_footer(self):
        T = THEME
        # 底栏挂在右侧内容列下面（左侧栏不受影响），并在上方加一条细分割线
        tk.Frame(self.main_col, bg=T["border2"], height=1).pack(fill="x", side="bottom")
        f = ttk.Frame(self.main_col, padding=(ui(14), ui(8), ui(14), ui(10)))
        f.pack(fill="x", side="bottom")
        self.status_bar = f

        ttk.Button(f, text=t("📋 复制需求"), style="Big.TButton",
                   command=self.copy_prompt).pack(side="left")
        ttk.Button(f, text=t("💾 保存到文件"), command=self.save_prompt
                   ).pack(side="left", padx=ui(8))
        ttk.Button(f, text=t("🧹 清空重填"), command=self.clear_all).pack(side="left")

        self.status = ttk.Label(f, text=t("填写任意内容都会自动生成，随时可以复制。"),
                                style="Sub.TLabel")
        self.status.pack(side="left", padx=(ui(14), 0))

    # ---------------- 主题 ----------------
    def toggle_theme(self):
        """在亮/暗之间切换并重启（配色在建控件时就定死了，必须重开）。"""
        target = "light" if THEME_MODE == "dark" else "dark"
        save_theme(target)
        if restart_app():
            self.root.destroy()
        else:
            messagebox.showinfo(
                t("已记住，请手动重开"),
                t("主题已改成「%s」。\n\n这个程序没能自动重开，请关掉它再打开一次。")
                % THEMES[target]["name"])

    # ---------------- 界面语言 ----------------
    def show_lang_dialog(self):
        """语言选择对话框（沿用其它对话框的 ttk 风格）。"""
        cur = i18n.get_lang()
        top = tk.Toplevel(self.root)
        top.title(t("界面语言"))
        top.geometry("%dx%d" % (ui(520), ui(260)))
        top.transient(self.root)
        top.grab_set()

        frame = ttk.Frame(top, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=t("选择界面语言"), style="QTitle.TLabel").pack(anchor="w")
        ttk.Label(frame,
                  text=t("切换后界面会重新打开一次。语言会被记住，下次启动仍然生效。"),
                  style="Sub.TLabel", justify="left", wraplength=ui(460)
                  ).pack(anchor="w", pady=(6, 12))

        picked = tk.StringVar(value=cur)
        for code in i18n.LANGS:
            ttk.Radiobutton(frame, text=i18n.LANG_NAMES[code],
                            value=code, variable=picked).pack(anchor="w", pady=ui(2))

        def apply_lang():
            chosen = picked.get()
            if chosen == cur:
                messagebox.showinfo(t("不用改"), t("当前就是这门语言。"), parent=top)
                return
            save_lang(chosen)
            top.destroy()
            if restart_app():
                self.root.destroy()
            else:
                messagebox.showinfo(
                    t("已记住，请手动重开"),
                    t("界面语言已改成「%s」。\n\n这个程序没能自动重开，请关掉它再打开一次。")
                    % i18n.LANG_NAMES.get(chosen, chosen), parent=self.root)

        btns = ttk.Frame(frame)
        btns.pack(side="bottom", fill="x", pady=(14, 0))
        ttk.Button(btns, text=t("关闭"), command=top.destroy).pack(side="right")
        ttk.Button(btns, text=t("确定并重新打开"), command=apply_lang).pack(side="right", padx=(0, 8))
        top.bind("<Escape>", lambda e: top.destroy())

    # ---------------- 输入处理 ----------------
    def _clear_example(self, box):
        if box.cget("foreground") == PLACEHOLDER_FG:
            box.delete("1.0", "end")
            box.configure(foreground=THEME["fg"])

    def _toggle(self, key, option):
        # 以勾选框实际状态为准，同步到 self.selected（避免调用顺序造成状态不同步）
        for o in self._options_of(key):
            var = self.option_buttons[(key, o)][0]
            if var.get():
                self.selected[key].add(o)
            else:
                self.selected[key].discard(o)
        self._sync_options_to_box(key)
        # ★ 第 1 题（类型）改了 → 换整套题；第 3 题（平台）改了 → 换选项
        if key == "kind":
            self._on_kind_changed()
        elif key == "system":
            self._on_system_changed()

    def _sync_options_to_box(self, key):
        box = self.widgets[key]
        current = box.get("1.0", "end").strip()
        if box.cget("foreground") == PLACEHOLDER_FG:
            current = ""
            # 同上：用主题色。写死深色会让暗色主题下的文字看不见。
            box.configure(foreground=THEME["fg"])
        # 去掉上一次自动写入的选项行（以 "✔ " 开头）
        manual = "\n".join(ln for ln in current.splitlines() if not ln.startswith("✔ "))
        manual = manual.strip()
        picked = [o for o in (self._options_of(key)) if o in self.selected[key]]
        auto = "\n".join("✔ " + o for o in picked)
        joined = (manual + ("\n" if manual and auto else "") + auto).strip()
        box.delete("1.0", "end")
        box.insert("1.0", joined)
        self._on_typing(key)

    def _options_of(self, key):
        """这一题**界面上实际显示**的选项。

        ★ 必须返回自适应后的那一份，不能返回基础选项：
          它是「有哪些选项」的唯一真相来源（_toggle 同步状态、重建表单时
          恢复勾选都靠它）。早先这里返回基础选项，而卡片渲染用的是自适应选项，
          两边不一致 —— 表现是界面上多出一个选项却同步不到，
          自检里也报「勾选框数量=78(应为77)」。
        """
        aq = self.adapted.get(key)
        if aq and aq.get("options"):
            return list(aq["options"])
        for q in self._active_questions():
            if q["key"] == key:
                return list(_qopts(q))
        return []

    def _set_box_text(self, key, text):
        """程序化往输入框写内容（会正确切掉占位符状态）。

        ★ 为什么要单独一个方法：光 insert 是不够的 ——
          前景色还停在占位符色，于是 collect()/_on_typing 会把内容当成
          「用户还没填」丢掉（实测踩过：换类型后已填内容消失）。

          真实用户不会遇到，因为点进输入框会触发 FocusIn → _clear_example。
          但程序化写入（重建表单、载入存档、演示填充）必须自己处理这一步。
        """
        box = self.widgets.get(key)
        if box is None:
            return
        box.delete("1.0", "end")
        if str(text or ""):
            box.configure(foreground=THEME["fg"])
            box.insert("1.0", text)
        else:
            box.configure(foreground=PLACEHOLDER_FG)
        self._on_typing(key)

    def _on_typing(self, key):
        box = self.widgets[key]
        val = box.get("1.0", "end").strip()
        if box.cget("foreground") == PLACEHOLDER_FG:
            val = ""
        self.answers[key] = val
        status = self.widgets[key + "__status"]
        if val:
            status.configure(text="✔ 已填写", style="Ok.TLabel")
        else:
            status.configure(text=t("待填写"), style="QHint.TLabel")
        self.refresh()

    # ---------------- 生成 ----------------
    def collect(self):
        data = {}
        for q in self._active_questions():
            box = self.widgets.get(q["key"])
            if box is None:
                continue
            val = box.get("1.0", "end").strip()
            if box.cget("foreground") == PLACEHOLDER_FG:
                val = ""
            data[q["key"]] = val
        return data

    def refresh(self):
        data = self.collect()
        text = build_prompt(data)
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)

        active = self._active_questions()
        filled = sum(1 for q in active if data.get(q["key"], "").strip())
        self.progress.configure(value=filled)
        left = [q for q in active if q.get("required") and not data.get(q["key"], "").strip()]
        msg = t("已填 {n}/{m} 格").format(n=filled, m=len(active))
        if left:
            msg += t("；还建议补上：") + "、".join(t(q["title"]).split(".", 1)[0] for q in left[:3])
        else:
            msg += t("；必填都填好了，可以复制了 ✔")
        self.progress_label.configure(text=msg)

    # ---------------- 动作 ----------------
    def _copy(self, text):
        """写剪贴板。成功返回 True；失败不抛（有些环境没有剪贴板）。"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update_idletasks()
            return True
        except tk.TclError:
            return False

    def copy_prompt(self):
        text = self.preview.get("1.0", "end").rstrip()
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update_idletasks()
        self.set_status(t("已复制 ✔  现在切到 AI 对话框，按 Ctrl+V 粘贴，发送就行了。"))
        messagebox.showinfo(t("复制成功"),
                            "需求说明已经复制到剪贴板。\n\n"
                            "下一步：打开和 AI 的对话框，按 Ctrl+V 粘贴，然后发送。\n\n"
                            "（这个窗口可以留着，AI 问你问题时回来改一改再复制一次）")

    def save_prompt(self):
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        name = self.answers.get("what", "") or "软件需求"
        name = name.replace("✔", " ")                     # 去掉点选产生的勾号
        name = re.sub(r"[\\/:*?\"<>|\r\n\t]", "", name)   # 去掉文件名非法字符
        name = re.sub(r"\s+", "", name)                   # 去掉空格，文件名更整齐
        name = re.sub(r"^[0-9]+[.、)]?", "", name.strip())  # 去掉开头的题号
        name = name[:24].strip() or "软件需求"
        path = os.path.join(ARCHIVE_DIR, f"{datetime.now():%Y%m%d_%H%M%S}_{name}.txt")
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write(self.preview.get("1.0", "end").rstrip() + "\n")
            # 把 12 格原始答案藏在文件末尾，方便以后在「历史记录」里一键还原
            f.write("\n" + DATA_MARK + "\n")
            f.write(json.dumps(self.collect(), ensure_ascii=False, indent=1))
            f.write("\n" + DATA_END + "\n")
        self.refresh_history()
        self.set_status(t("已保存：") + path)
        messagebox.showinfo(t("已保存"),
                            "已保存到：\n\n" + path +
                            "\n\n可以在「历史记录」这一页里随时找回来、重新载入修改。")

    def clear_all(self):
        if not messagebox.askyesno(t("确认清空"), t("要把所有填写内容清空，重新开始吗？")):
            return
        for q in self._active_questions():
            box = self.widgets[q["key"]]
            box.delete("1.0", "end")
            box.insert("1.0", t(_qval(q, "example")))
            box.configure(foreground=PLACEHOLDER_FG)
        for key in self.selected:
            self.selected[key].clear()
        for (key, opt), (var, cb, o) in self.option_buttons.items():
            var.set(False)
        self.refresh()
        self.set_status(t("已清空，可以从第 1 格重新填。"))

    def show_help(self, q):
        # 用自适应后的版本：手机/网页环境下，说明文字也该跟着变
        aq = self._adapted(q)
        top = tk.Toplevel(self.root)
        top.title(t(aq["title"]))
        top.geometry("%dx%d" % (ui(640), ui(460)))
        top.transient(self.root)
        frame = ttk.Frame(top, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=t(aq["hint"]), style="QHint.TLabel",
                  wraplength=600, justify="left").pack(anchor="w")
        inner = tk.Text(frame, wrap="word", relief="solid", borderwidth=1,
                        highlightthickness=0,
                        font=(self.font, -int(round(ui(10) * FONT_BOOST))), padx=8, pady=8)
        inner.pack(fill="both", expand=True, pady=8)
        inner.insert("1.0", t(aq["help"]))
        inner.configure(state="disabled")
        ttk.Button(frame, text=t("知道了"), command=top.destroy).pack(anchor="e")
        top.bind("<Escape>", lambda e: top.destroy())

    # ---------------- 显示大小（分辨率自适应） ----------------
    def show_scale_dialog(self):
        sw, sh = screen_size(self.root)
        rec, why = detect_recommended_scale()
        dpi = _windows_dpi()
        top = tk.Toplevel(self.root)
        top.title(t("显示大小 / 分辨率自适应"))
        top.geometry("%dx%d" % (ui(620), ui(430)))
        top.transient(self.root)
        top.grab_set()

        frame = ttk.Frame(top, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="这个界面当前按 %d%% 显示，字号档位「%s」"
                  % (int(round(self.scale * 100)), self._boost_label()),
                  style="QTitle.TLabel").pack(anchor="w")
        info = (f"屏幕分辨率：{sw} × {sh}\n"
                f"Windows 报告的系统 DPI：{dpi}（96 = 100%）   Windows 推荐缩放："
                f"{int(round(rec * 100))}%（依据：{why}）\n"
                f"程序当前使用：{int(round(self.scale * 100))}%\n\n"
                "两个旋钮，作用不同：\n"
                "  · 「界面整体大小」改的是整个界面（字和间距一起变）。\n"
                "  · 「字号档位」只把字放大，间距基本不动 —— 觉得字偏小就调这个，\n"
                "    不用去动 Windows 的缩放（动那个会影响其他所有程序）。\n\n"
                "想找回来：选择会记在程序目录的 config.json 里，删掉即可恢复默认。")
        ttk.Label(frame, text=info, style="Sub.TLabel", justify="left").pack(anchor="w", pady=(6, 10))

        # ---- 字号档位（重点：解决「字偏小」但不影响布局）----
        frow = ttk.Frame(frame)
        frow.pack(fill="x", pady=(0, 8))
        ttk.Label(frow, text=t("字号档位："), style="QTitle.TLabel").pack(side="left")
        for label, val in FONT_BOOST_CHOICES:
            mark = "● " if abs(val - FONT_BOOST) < 0.001 else ""
            ttk.Button(frow, text=mark + t(label), style="Small.TButton",
                       command=lambda v=val: self.change_font_boost(v)).pack(side="left", padx=3)
        ttk.Label(frow, text=t("（正文实际 %d 像素）") % ui(10 * FONT_BOOST),
                  style="Sub.TLabel").pack(side="left", padx=8)

        row = ttk.Frame(frame)
        row.pack(fill="x", pady=(0, 10))
        ttk.Label(row, text=t("界面整体大小：")).pack(side="left")
        for pct in (100, 125, 150, 175, 200, 250):
            ttk.Button(row, text=f"{pct}%", style="Small.TButton",
                       command=lambda p=pct: self.change_ui_scale(p / 100.0)).pack(side="left", padx=3)

        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=(0, 10))
        ttk.Label(row2, text=t("更细的：")).pack(side="left")
        self.scale_var = tk.DoubleVar(value=self.scale * 100.0)
        ttk.Scale(row2, from_=70, to=300, variable=self.scale_var,
                  command=lambda v: self.scale_hint.configure(
                      text="%.0f%%" % float(v))).pack(side="left", fill="x", expand=True, padx=8)
        self.scale_hint = ttk.Label(row2, text="%.0f%%" % (self.scale * 100), style="Sub.TLabel")
        self.scale_hint.pack(side="left")
        ttk.Button(row2, text=t("用这个数"), command=self._apply_slider_scale).pack(side="left", padx=6)

        ttk.Label(frame, text="建议：界面整体大小保持和 Windows 一致；字偏小就用上面的字号档位。",
                  style="Sub.TLabel", justify="left").pack(anchor="w", pady=(4, 12))
        ttk.Button(frame, text="关闭", command=top.destroy).pack(side="right")
        top.bind("<Escape>", lambda e: top.destroy())

    def _boost_label(self):
        for label, val in FONT_BOOST_CHOICES:
            if abs(val - FONT_BOOST) < 0.001:
                return t(label)
        return "%.0f%%" % (FONT_BOOST * 100)

    def change_font_boost(self, val):
        """只改字号档位并重启（字号在启动时定好，必须重开才生效）。"""
        val = max(0.7, min(2.0, round(float(val), 3)))
        if abs(val - FONT_BOOST) < 0.001:
            messagebox.showinfo(t("不用改"), t("当前就是这个字号。"))
            return
        save_font_boost(val)
        if restart_app():
            self.root.destroy()
        else:
            messagebox.showinfo(
                "已记住，请手动重开",
                "字号档位已改。\n\n"
                "这个程序没法自动重开，请关掉它再打开一次，就会生效。")

    def _apply_slider_scale(self):
        self.change_ui_scale(float(self.scale_var.get()) / 100.0)

    def change_ui_scale(self, scale):
        """记住新缩放并重启自己（缩放必须在新进程里生效）。"""
        scale = max(0.7, min(3.0, round(float(scale), 3)))
        if abs(scale - self.scale) < 0.001:
            messagebox.showinfo(t("不用改"), t("当前就是这个显示大小。"))
            return
        save_ui_scale(scale)
        if restart_app():
            self.root.destroy()
        else:
            messagebox.showinfo(
                "已记住，请手动重开",
                "显示大小已记成 %d%%。\n\n"
                "这个程序没法自动重开，请关掉它再打开一次，就会生效。\n"
                "（用桌面的快捷方式重新打开即可）" % int(round(scale * 100)))

    def show_diagnostics(self):
        """把显示相关真实数据写成文件，并直接告诉用户结论。"""
        path = run_diagnostics(self, "点击「显示诊断」按钮")
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                report = f.read()
        except OSError:
            report = "（报告已生成但读不出来）"
        top = tk.Toplevel(self.root)
        top.title(t("显示诊断"))
        top.geometry("%dx%d" % (ui(700), ui(520)))
        top.transient(self.root)
        frame = ttk.Frame(top, padding=10)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="已生成诊断报告：" + path,
                  style="QTitle.TLabel", wraplength=ui(660),
                  justify="left").pack(anchor="w")
        ttk.Label(frame, text="如果你要找人帮忙看字太小/字发糊的问题，把这份文件发过去就行。",
                  style="Sub.TLabel").pack(anchor="w", pady=(4, 8))
        box = ttk.Frame(frame)
        box.pack(fill="both", expand=True)
        t = tk.Text(box, wrap="word", relief="solid", borderwidth=1, highlightthickness=0,
                    font=(self.font, -int(round(ui(9) * FONT_BOOST))), padx=8, pady=8)
        sb = ttk.Scrollbar(box, command=t.yview)
        t.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        t.pack(side="left", fill="both", expand=True)
        t.insert("1.0", report)
        t.configure(state="disabled")
        bar = ttk.Frame(frame)
        bar.pack(fill="x", pady=(8, 0))
        ttk.Button(bar, text=t("打开报告所在文件夹"),
                   command=self.open_app_dir).pack(side="left")
        ttk.Button(bar, text="关闭", command=top.destroy).pack(side="right")
        top.bind("<Escape>", lambda e: top.destroy())

    def open_app_dir(self):
        try:
            os.startfile(APP_DIR)
        except OSError as e:
            messagebox.showwarning(t("打不开文件夹"), str(e))

    def show_about(self):
        # ★ 按名字选，不写索引。
        #   原来写的是 _select_page(2)，在插入「先查查」页之后
        #   索引 2 从「使用说明」变成了「历史记录」—— 这类错位不会报错，
        #   只会打开错的页面。用名字就再也不会因为插页而错。
        self.select_page_by_key("about")

    def set_status(self, msg):
        self.status.configure(text=msg)

    def on_close(self):
        # config.json 里同时存表单草稿和显示大小，两样都不能丢
        cfg = {}
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                old = json.load(f)
            if isinstance(old, dict):
                cfg = old
        except (OSError, ValueError):
            pass
        try:
            cfg["ui_scale"] = round(float(UI_SCALE), 3)
            cfg["font_boost"] = round(float(FONT_BOOST), 3)
            cfg["draft"] = self.collect()
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
        self.root.destroy()


def main():
    global FONT_FAMILY, _AWARENESS_RESULT
    # ★ 顺序很重要：必须先告诉 Windows「我自己会缩放」，再创建窗口。
    #   原来这两步是反的（先建窗口后设 DPI），所以等于没设，
    #   在 4K 屏上 Windows 会按 100% 出图，界面就小得看不清。
    _AWARENESS_RESULT = apply_dpi_awareness()

    root = tk.Tk()
    scale, recommended, why = init_ui_scale(root)
    boost = init_font_boost()
    theme_mode, _theme = init_theme()      # ★ 配色必须在建任何控件之前定好
    lang = init_lang()                     # ★ 语言也要在建控件之前定好
    FONT_FAMILY = choose_font_family(root)
    root.configure(bg=THEME["bg"])

    if os.environ.get("XBSH_UI_DEBUG"):
        print(f"[DPI] awareness={_AWARENESS_RESULT} 实测DPI={_WINDOWS_DPI} "
              f"推荐缩放={recommended:.2f}({why}) 实际使用={scale:.2f} "
              f"字体={FONT_FAMILY} 主题={theme_mode} 语言={lang} "
              f"屏幕={root.winfo_screenwidth()}x{root.winfo_screenheight()}")

    app = App(root)
    # 允许用环境变量指定打开哪一页（截图脚本用；正常启动不受影响）
    _page = os.environ.get("XBSH_PAGE")
    if _page is not None:
        try:
            app._select_page(max(0, min(len(App.PAGES) - 1, int(_page))))
        except (TypeError, ValueError):
            pass
    app.set_status(t("显示大小 %d%%（Windows 推荐 %d%%；侧栏底部可调大小、可看诊断）")
                   % (int(round(scale * 100)), int(round(recommended * 100))))
    app.set_status(app.status.cget("text") + t("；字号「%s」") % app._boost_label())
    # 允许用环境变量直接生成诊断报告（排查用，不弹窗）
    if os.environ.get("XBSH_UI_DIAGNOSE"):
        root.update_idletasks()
        path = run_diagnostics(app, "环境变量 XBSH_UI_DIAGNOSE=1")
        try:
            app.set_status(t("诊断报告已生成：") + path)
        except tk.TclError:
            pass
    # 允许用环境变量写入演示内容（截图/目视验证用；正常启动不受影响）
    #
    # 为什么要这个：验证「打字后文字看得见」必须真的往框里写字，
    # 否则截出来是空的，看不出修复效果。
    # 它会走**和真实操作完全相同的两条路径**：
    #   手动输入 → _clear_example + insert（跟用户敲键盘一样）
    #   点选项   → _toggle → _sync_options_to_box（跟用鼠标点一样）
    if os.environ.get("XBSH_AUTODEMO"):
        demo_manual = {
            "what": "一个帮我把每天三份销售 Excel 自动合并汇总的小工具",
            "pain": "现在每天手动复制粘贴，约 40 分钟，客户名不一致时经常漏行",
        }
        for key, text in demo_manual.items():
            box = app.widgets.get(key)
            if box is None:
                continue
            box.delete("1.0", "end")
            app._clear_example(box)        # 走真实的「换掉占位符色」路径
            box.insert("1.0", text)
            app._on_typing(key)
        # 点选项那条路（相当于用户用鼠标点了勾选框）
        for key in ("who", "where"):
            opts = app._options_of(key)
            if opts:
                app._toggle(key, opts[0])
        root.update_idletasks()

    # 允许用环境变量预设选项（截图验证自适应用）
    #   XBSH_AUTOADAPT=安卓      → 预设第「系统」题的平台
    #   XBSH_AUTOKIND=插件       → 预设第 1 题的类型
    _kind = os.environ.get("XBSH_AUTOKIND")
    if _kind:
        for opt in app._options_of("kind"):
            if _kind in opt:
                app.option_buttons[("kind", opt)][0].set(True)
                app._toggle("kind", opt)
                break
        root.update_idletasks()
    _auto = os.environ.get("XBSH_AUTOADAPT")
    if _auto and app._options_of("system"):
        for opt in app._options_of("system"):
            if _auto in opt:
                app.option_buttons[("system", opt)][0].set(True)
                app._toggle("system", opt)
                break
        root.update_idletasks()
    root.mainloop()


if __name__ == "__main__":
    main()
