# -*- coding: utf-8 -*-
"""问卷自适应：根据前面选的「目标平台」，让后面的问题更有针对性。

## 为什么需要

用户反馈的原话是：想做手机 App，但后面好多问题都不适配
（第 4 题问「在哪里打开」给的却是 Windows 电脑的选项）。

## 做法：声明式，不写死在界面里

每个问题可以在 `ADAPT` 表里声明：
  · families    —— 这一题在哪些平台族下出现（不出现就隐藏，别让用户白填）
  · options_by  —— 平台族 → 该显示哪些选项
  · title_by / hint_by / example_by / help_by —— 按平台族换文案

**宽泛选项一律保留**：每个平台族的选项列表最后都会拼上 `BROAD`
（「不确定，你帮我选」这类）。这是用户明确要求的「保留一些宽泛的选项」。

## 平台族怎么定

由第 3 题（system）的选项反查出来，见 `family_of_prompt_answer()`。
分四族：desktop / mobile / web / unknown。手机那一族内部再细分
（安卓、iOS、鸿蒙），因为交付方式差别很大。
"""

import re

# 平台族
FAM_DESKTOP = "desktop"
FAM_ANDROID = "android"
FAM_IOS = "ios"
FAM_HARMONY = "harmony"
FAM_WEB = "web"
FAM_UNKNOWN = "unknown"

ALL_FAMS = (FAM_DESKTOP, FAM_ANDROID, FAM_IOS, FAM_HARMONY, FAM_WEB, FAM_UNKNOWN)


def family_of_target(target):
    """一个 TARGETS 取值 → 平台族。"""
    s = str(target or "")
    if s.startswith("windows") or s.startswith("macos") or s.startswith("linux"):
        return FAM_DESKTOP
    if s.startswith("android"):
        return FAM_ANDROID
    if s == "ios":
        return FAM_IOS
    if s == "harmony":
        return FAM_HARMONY
    if s == "web":
        return FAM_WEB
    return FAM_UNKNOWN


def _family_of_one(v):
    """单行文字 → 平台族（匹配不到返回 None，便于调用方区分「没匹配」）。"""
    low = v.lower()
    if "android" in low or "安卓" in v:
        return FAM_ANDROID
    if "ios" in low or "iphone" in low or "ipad" in low:
        return FAM_IOS
    if "harmony" in low or "鸿蒙" in v:
        return FAM_HARMONY
    if "网页" in v or "web page" in low or "浏览器" in v or "browser" in low:
        return FAM_WEB
    if ("windows" in low or "macos" in low or "mac" in low or "linux" in low
            or "电脑" in v or "computer" in low or "跟我电脑一样" in v
            or "same as my computer" in low):
        return FAM_DESKTOP
    return None


# 具体程度：手机三族和网页比「桌面」更具体。
# 用户可能勾了多个（选项是多选），取最具体的那个。
_SPECIFICITY = {
    FAM_ANDROID: 3, FAM_IOS: 3, FAM_HARMONY: 3,
    FAM_WEB: 2, FAM_DESKTOP: 1,
}


def family_of_prompt_answer(value):
    """第 3 题用户选的那一项 → 平台族。

    那一项是「跟我电脑一样：Windows 64 位（推荐）」或
    「安卓手机 App（ARM64，现在的手机基本都是）」这样的文字，
    所以按关键词判断，而不是精确匹配（选项文案会随语言变）。

    ★ 选项是**多选**的，用户可能同时勾了「跟我电脑一样」和「安卓手机 App」。
      这种情况取**最具体**的那个（手机 > 网页 > 桌面），
      否则会因为「跟我电脑一样」排在前而一直当成桌面 —— 实测踩过。
    """
    v = str(value or "")
    if not v.strip():
        return FAM_UNKNOWN
    if "不确定" in v or "not sure" in v.lower():
        return FAM_UNKNOWN

    best, best_rank = None, -1
    for line in v.splitlines():
        fam = _family_of_one(line)
        if fam is None:
            continue
        rank = _SPECIFICITY.get(fam, 0)
        if rank > best_rank:
            best, best_rank = fam, rank
    if best is not None:
        return best
    # 整句里没换行的情况也试一次（用户自己写的一串文字）
    fam = _family_of_one(v)
    return fam or FAM_UNKNOWN


def is_mobile(fam):
    return fam in (FAM_ANDROID, FAM_IOS, FAM_HARMONY)


# 手机三族共用的一个「虚拟族」键：安卓/iOS/鸿蒙在文案上可以共用一套说法，
# 需要细分时再单独列（如 install 的交付方式）。
FAM_MOBILE = "mobile"


def family_chain(fam):
    """一个平台族 → 查表时要依次尝试的键。

    先查具体族（android / ios / harmony），再查共用的 "mobile"，
    最后查 "all"。这样「手机通用文案」只写一份，特例再单独覆盖。
    """
    if fam in (FAM_ANDROID, FAM_IOS, FAM_HARMONY):
        return [fam, FAM_MOBILE, "all"]
    return [fam, "all"]


# ---------------------------------------------------------------------------
# 每个问题在「非桌面」环境下怎么变
# ---------------------------------------------------------------------------
# 只写需要变的；没列出的问题（what / who / pain / input / output /
# ref / extra）在哪个平台下都一样，保持通用。

ADAPT = {
    # ---- 第 3 题：系统与位数 ----
    # ★ 这一题自己也要自适应：选了手机 App 之后，标题还写「32 位还是 64 位？」
    #   是**误导**（手机用户不关心这个）。截图验证时发现的。
    "system": {
        "title": "3. 这个软件要跑在什么系统上？32 位还是 64 位？",
        "title_by": {
            FAM_MOBILE: {
                "zh-CN": "3. 手机 App 做给哪种手机用？",
                "zh-TW": "3. 手機 App 做給哪種手機用？",
                "en": "3. Which kind of phone is the app for?",
            },
            FAM_WEB: {
                "zh-CN": "3. 这个网页给谁用、在什么设备上打开？",
                "zh-TW": "3. 這個網頁給誰用、在什麼裝置上開啟？",
                "en": "3. Who is the web page for, and on what devices?",
            },
        },
        "hint_by": {
            FAM_MOBILE: {
                "zh-CN": "选错手机类型会导致装不上。安卓、苹果、鸿蒙是完全不同的做法。",
                "zh-TW": "選錯手機類型會導致裝不上。安卓、蘋果、鴻蒙是完全不同的做法。",
                "en": "Picking the wrong phone type means it will not install. "
                      "Android, iPhone, and HarmonyOS are built in completely different ways.",
            },
            FAM_WEB: {
                "zh-CN": "网页本身什么设备都能开，主要看给谁用、要不要放到网上。",
                "zh-TW": "網頁本身什麼裝置都能開，主要看給誰用、要不要放到網路上。",
                "en": "A web page opens on any device; what matters is who it is for "
                      "and whether it goes online.",
            },
        },
        # 示例也要换：选了安卓还显示「例如：Windows 64 位…」是自相矛盾的
        "example_by": {
            FAM_MOBILE: {
                "zh-CN": "例如：安卓手机 App（现在的手机基本都是安卓）",
                "zh-TW": "例如：安卓手機 App（現在的手機幾乎都是安卓）",
                "en": "e.g. an Android app (almost every current phone is Android)",
            },
            FAM_WEB: {
                "zh-CN": "例如：网页，电脑和手机都能打开",
                "zh-TW": "例如：網頁，電腦和手機都能開啟",
                "en": "e.g. a web page that opens on both a computer and a phone",
            },
        },
    },

    # ---- 第 4 题：在哪里打开 / 要不要联网 ----
    # 桌面环境下问「做窗口程序还是网页」很有意义；
    # 手机 App 已经确定了平台，再问这个就自相矛盾 —— 改成问「手机上怎么打开」。
    "where": {
        "title_by": {
            FAM_MOBILE: {
                "zh-CN": "4. 手机上打算怎么用它？要不要联网？",
                "zh-TW": "4. 手機上打算怎麼用它？要不要連網？",
                "en": "4. How will it be used on the phone? Does it need the internet?",
            },
            FAM_WEB: {
                "zh-CN": "4. 这个网页怎么用？要不要联网？",
                "zh-TW": "4. 這個網頁怎麼用？要不要連網？",
                "en": "4. How will the web page be used? Does it need the internet?",
            },
        },
        "options_by": {
            FAM_MOBILE: [
                "装成 App，点桌面图标打开",
                "在手机浏览器里打开网址就行",
                "微信里能打开/分享（小程序或链接）",
                "要给不特定的人下载用",
            ],
            FAM_WEB: [
                "电脑和手机都要能打开",
                "只给内部的人用，不想放到公网",
                "要放到网上，别人能直接访问",
                "只要能在我自己电脑上跑就行",
            ],
        },
        "hint_by": {
            FAM_MOBILE: {
                "zh-CN": "手机上装 App 和用浏览器打开，做法和门槛差别很大。",
                "zh-TW": "手機上裝 App 和用瀏覽器開啟，做法和門檻差別很大。",
                "en": "Installing an app and opening a web page on a phone are very different.",
            },
        },
    },

    # ---- 第 12 题：怎么交付 / 怎么再打开 ----
    # 这一题最需要按平台变：安卓给 apk、iOS 走 App Store、桌面给 exe。
    "install": {
        "title_by": {
            FAM_MOBILE: {
                "zh-CN": "12. 希望怎么装到手机上、怎么再打开？（怎么交付）",
                "zh-TW": "12. 希望怎麼裝到手機上、怎麼再開啟？（怎麼交付）",
                "en": "12. How should it be installed on the phone and reopened? (delivery)",
            },
            FAM_WEB: {
                "zh-CN": "12. 这个网页放在哪、怎么再打开？（怎么交付）",
                "zh-TW": "12. 這個網頁放在哪、怎麼再開啟？（怎麼交付）",
                "en": "12. Where should the web page live and how is it reopened? (delivery)",
            },
        },
        "options_by": {
            FAM_ANDROID: [
                "一个 apk 安装包，我传到手机点一下装",
                "要能上架应用商店（安卓）",
                "我自己装就行，不用上架",
            ],
            FAM_IOS: [
                "先做出来能在我自己手机上试（需要有苹果开发者账号）",
                "要上架 App Store 给别人下载",
                "其实用网页版也行（不用苹果账号）",
            ],
            FAM_HARMONY: [
                "一个 hap 安装包，我传到手机装",
                "需要开开发者模式才能装，我可以接受",
            ],
            FAM_WEB: [
                "给我一个网址，我用浏览器打开",
                "放到我自己电脑上，只有我能访问",
                "要放到服务器上给别人访问",
            ],
        },
    },

    # ---- 第 9 题「怎么算做好了」：手机/网页的验收标准不一样 ----
    "done": {
        "example_by": {
            FAM_MOBILE: {
                "zh-CN": "例如：在我自己的手机上装好，打开后能完成主要操作，不闪退",
                "zh-TW": "例如：在我自己的手機上裝好，開啟後能完成主要操作，不會閃退",
                "en": "e.g. installed on my own phone, opens and completes the main task without crashing",
            },
            FAM_WEB: {
                "zh-CN": "例如：用手机和电脑各打开一次，主要功能都能用，刷新不丢数据",
                "zh-TW": "例如：用手機和電腦各開啟一次，主要功能都能用，重新整理不丟資料",
                "en": "e.g. opened once on a phone and once on a desktop, all main features work, "
                      "a refresh does not lose data",
            },
        },
        "options_by": {
            FAM_MOBILE: [
                "在我自己的手机上能装能开",
                "主要功能点一遍都正常，不闪退",
                "发给别人也能装能开",
            ],
            FAM_WEB: [
                "手机和电脑打开都正常",
                "换台设备/换个时间打开，数据还在",
                "别人打开也能用",
            ],
        },
    },

    # ---- 第 10 题「不能做什么」：手机/网页各有专属红线 ----
    "limit": {
        "options_by": {
            FAM_MOBILE: [
                "不要偷偷上传我的通讯录/相册/位置",
                "不要要求一堆用不上的权限",
                "不要有广告和推送",
            ],
            FAM_WEB: [
                "不要公开我的数据，只能我自己看到",
                "不要收集访问者的个人信息",
            ],
        },
    },
}

# 每个平台族**额外追加**的宽泛选项 —— 用户明确要求「保留一些宽泛的选项」。
# 它们和该族专属选项拼在一起显示。
BROAD = {
    "where": [
        "不确定，你帮我选",
    ],
    "install": [
        "你决定就好",
        "先做一个最简单的版本给我看看",
    ],
}


# ---------------------------------------------------------------------------
# 解析：给一个问题的 key + 当前平台族 + 语言 → 该显示什么
# ---------------------------------------------------------------------------

def _pick(table, fam, locale):
    """从 {族: {语言: 文案}} 里按族链取值。取不到返回 None。

    ★ 最后一定要试 "all"：那是「所有平台通用」的文案，
      不试的话 such 条目永远不生效（第 2 题标题就踩过这个）。
    """
    if not table:
        return None
    for key in family_chain(fam) + ["all"]:
        entry = table.get(key)
        if isinstance(entry, dict):
            v = entry.get(locale) or entry.get("zh-CN")
            if v:
                return v
        elif isinstance(entry, str) and key == "all":
            return entry
    return None


def _uniq(seq):
    out, seen = [], set()
    for x in seq:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def adapt(key, fam, locale, base):
    """把基础问题定义按平台族调整。

    @param key    问题 key（如 'install'）
    @param fam    平台族（family_of_prompt_answer 的结果）
    @param locale 语言
    @param base   基础 dict，含 title/hint/example/help/options（options 可为可调用）
    @returns dict，含 key/title/hint/example/help/options/adapted
      adapted=True 表示这一题按平台变过（界面可以给个提示）
    """
    rule = ADAPT.get(key) or {}
    fam = fam or FAM_UNKNOWN

    def base_val(field):
        v = base.get(field)
        if callable(v):
            try:
                v = v()
            except Exception:  # noqa: BLE001
                v = None
        return v

    out = {
        "key": key,
        "title": _pick(rule.get("title_by"), fam, locale) or base_val("title") or "",
        "hint": _pick(rule.get("hint_by"), fam, locale) or base_val("hint") or "",
        "example": _pick(rule.get("example_by"), fam, locale) or base_val("example") or "",
        "help": _pick(rule.get("help_by"), fam, locale) or base_val("help") or "",
        "options": [],
        "adapted": False,
        "required": bool(base.get("required")),
        "multiline": bool(base.get("multiline")),
        "dynamic": bool(base.get("dynamic")),
    }

    # 选项：该族的专属选项 + 宽泛选项
    own = None
    opts_by = rule.get("options_by") or {}
    for cand in family_chain(fam):
        if cand in opts_by:
            own = opts_by[cand]
            break
    base_opts = base_val("options") or []
    if not isinstance(base_opts, (list, tuple)):
        base_opts = []

    if own:
        opts = _uniq(list(own) + list(BROAD.get(key, [])))
        out["adapted"] = True
    else:
        # 没有专属规则 → 用基础选项；但如果这个族没有专属规则而基础选项是
        # 「桌面视角」写的，也不要紧：这些题本来就是通用的。
        opts = _uniq(list(base_opts) + list(BROAD.get(key, [])))
    out["options"] = opts

    # 标出哪些字段被改过（便于界面提示 + 测试断言）
    changed = []
    for field in ("title", "hint", "example", "help"):
        if _pick(rule.get(field + "_by"), fam, locale):
            changed.append(field)
    if own:
        changed.append("options")
    out["changed"] = _uniq(changed)
    if out["changed"]:
        out["adapted"] = True
    return out


def options_for(key, fam, locale, base):
    """只要选项列表（界面里最常用的）"""
    return adapt(key, fam, locale, base)["options"]


# ===========================================================================
# 第三层维度：「做什么类型的东西」
# ===========================================================================
# 平台自适应（上面那套）回答的是「跑在哪」。但还有更根本的一层：
# **做的是程序，还是插件，还是脚本？**
#
# 用户反馈：想给 DSH 做一个插件，但后面全在问 exe / 32 位 / apk ——
# 完全不同的一件事。做插件该问的是「挂在哪个软件上、怎么被调用、
# 要不要调它的接口、要不要设置界面」。

KIND_PROGRAM = "program"
KIND_PLUGIN = "plugin"
KIND_SCRIPT = "script"

# 类型题（放在问卷最前面，其余题号顺移）
KIND_QUESTION = {
    "key": "kind",
    "required": True,
    "multiline": False,
    "dynamic": True,          # 会改变后面出现哪些题
    "title": "1. 你要做的是哪一种？",
    "hint": "程序、插件、脚本是三件不同的事，后面的问题会不一样。不确定就选第一项。",
    "example": "例如：电脑上的程序（能双击打开的那种）",
    "options": [
        "电脑上的程序（能双击打开的那种）",
        "手机 App",
        "网页",
        "某个软件的插件/扩展（挂在别的软件里用）",
        "自动化小脚本（跑一下就完事，没有界面）",
        "不确定，你帮我判断",
    ],
}


def kind_of_prompt_answer(value):
    """类型题用户选的文字 → 类型。"""
    v = str(value or "").strip()
    if not v:
        return KIND_PROGRAM          # 没答就按最普遍的「程序」处理，不阻断
    low = v.lower()
    if "插件" in v or "扩展" in v or "plugin" in low or "extension" in low:
        return KIND_PLUGIN
    if "脚本" in v or "script" in low:
        return KIND_SCRIPT
    return KIND_PROGRAM


# 插件专属的问题（替换掉「系统与位数」「在哪里打开」「怎么交付」那几题）
PLUGIN_QUESTIONS = [
    {
        "key": "plugin_host",
        "required": True,
        "multiline": False,
        "title": "3. 挂在哪个软件里？",
        "hint": "不同软件的插件写法完全不同。写清楚名字和版本，别只说「一个编辑器」。",
        "example": "例如：DeepSeek Harness（DSH）桌面版，我在设置里装插件",
        "options": [
            "浏览器（Chrome / Edge 扩展）",
            "VS Code / Cursor 这类编辑器",
            "某个 AI 工具 / 聊天软件",
            "Office / WPS（Word、Excel 里用）",
            "别的软件（我在最后一格说名字）",
        ],
    },
    {
        "key": "plugin_trigger",
        "required": True,
        "multiline": True,
        "title": "4. 怎么触发它？它在你操作时什么时候动？",
        "hint": "插件和程序最大的区别：插件是「挂在别人的流程里」被调用的。"
                "说清楚是谁在什么时候叫它。",
        "example": "例如：我在对话框里打「检查需求」它就分析我写的这段话，"
                   "或者每次我发消息前它自己先看一眼",
        "options": [
            "我打一个命令 / 点一个按钮才触发",
            "每次我做某个动作它自动插一脚",
            "它自己在后台定时跑",
            "要能加到右键菜单里",
        ],
    },
    {
        "key": "plugin_interface",
        "required": True,
        "multiline": True,
        "title": "5. 要不要跟被挂的那个软件交换信息？",
        "hint": "这是插件最容易卡住的地方。如果要读它当前的内容、或者把结果塞回去，"
                "就得用它提供的接口 —— 你得告诉我它有哪些接口（或者让我去查文档）。",
        "example": "例如：要读我现在对话框里打的内容，把检查结果直接插回输入框；"
                   "没有现成接口的话，告诉我替代做法",
        "options": [
            "要读它当前的内容（比如我正在编辑的文字）",
            "要把结果写回去 / 戳一个提示出来",
            "只读我主动给它的东西就行，不用接口",
            "要能调用另一个 AI 帮我分析",
            "不确定它有没有接口，你帮我查",
        ],
    },
    {
        "key": "plugin_ui",
        "required": False,
        "multiline": False,
        "title": "6. 需要设置界面吗？（可选）",
        "hint": "要不要让我能改一些设置（开关、阈值、语言）？不放设置页也能用，"
                "但有些东西最好让人能调。",
        "example": "例如：要能开关、能切换中文/英文、能调严格程度",
        "options": [
            "要，能改开关和参数",
            "要，最好能切换语言",
            "不用，用法固定就行",
            "你看着办",
        ],
    },
    {
        "key": "plugin_install",
        "required": True,
        "multiline": False,
        "title": "7. 打算怎么装上、给谁用？",
        "hint": "自己本地装、发给同事、还是上架到插件市场，做法差别很大。",
        "example": "例如：先在我自己机器上装好能用，之后可能发给同事",
        "options": [
            "只在我自己机器上装好能用",
            "要能打包发给同事，他们照说明也能装",
            "要上架到官方的插件市场 / 商店",
            "要能在多台机器上快速装好",
            "你决定就好",
        ],
    },
]

# 插件类型下**不再需要**的题（它们是「做程序」才要问的）
PROGRAM_ONLY_KEYS = ("system", "where", "install")

# 脚本类型下不需要的题（脚本没有交付物、也不讲怎么双击打开）
SCRIPT_SKIP_KEYS = ("system", "where", "install")

# 脚本专属的补充问题（比插件简单，只要能跑、怎么跑）
SCRIPT_QUESTIONS = [
    {
        "key": "script_run",
        "required": True,
        "multiline": False,
        "title": "4. 你打算怎么运行它？",
        "hint": "脚本不打包成 exe，一般是双击某个文件或者定时跑。",
        "example": "例如：我双击一个 .bat 文件它就处理；或者每天早上自动跑一次",
        "options": [
            "我双击一个文件它就处理",
            "我要在命令行里输入一行命令跑",
            "每天/每周自动定时跑",
            "别人也能在他电脑上跑",
            "不确定，你帮我选最省事的",
        ],
    },
]


def _adapt_static(q, locale):
    """把「不依赖平台族」的固定文案换掉，并按位置重新编号。

    ★ 为什么合并成一步：早先 adapt() 和编号是分开做的，调用方很容易只做一步 ——
      实际就漏过一次（生成说明里编号变了但文案没换，测试也漏了）。

      这里只处理**固定文案**（值为 {语言: 文案} 的那种，不分平台）。
      依赖平台族的文案（如第 4/12 题）没法在这里定，因为没有平台信息 ——
      那部分留给运行时带 fam 调 adapt()；好在那种情况下基础标题本来
      就不用换（平台也没定，等于桌面）。
    """
    out = dict(q)
    for field in ("title", "hint", "example"):
        tbl = (ADAPT.get(out.get("key")) or {}).get(field + "_by")
        if not tbl:
            continue
        fixed = tbl.get("all")
        if isinstance(fixed, dict):
            v = fixed.get(locale) or fixed.get("zh-CN")
            if v:
                out[field] = v
    return out


def questions_for(base_questions, kind, locale="zh-CN"):
    """按「做什么类型」组装这一次要问的问题列表。

    ★ 这是第三层维度。平台自适应改的是**单个题的选项和措辞**；
      这里改的是**出现哪些题** —— 因为做插件和做程序根本是两件事，
      不是把「在哪里打开」换几个选项就能覆盖的。

    规则：
      · 程序 / 手机 App / 网页  → 原来的题目（再由平台自适应细化）
      · 插件                    → 去掉「系统与位数/在哪里打开/怎么交付」，
                                  在**靠前的位置**插入插件专属问题
      · 脚本                    → 去掉交付类问题，加一题「怎么运行」

    ★ 顺序很重要：插件的核心问题是「挂在哪个软件里」，
      必须紧跟第 2 题（做什么），不能塞到最后。
      一个人填到第 12 题才被问到「你在做插件吗」早就放弃了。
      实测发现塞在最后时，核心三题排到了 12~14 位。

    ★ 返回前会做两件事：换固定文案（_adapt_static）+ 按位置重新编号。
      这样任何调用方（界面、生成说明、测试）拿到的都是最终成品，
      不会出现「编号变了但文案没换」。规则里带平台族的部分由 adapt() 补。

    宽泛原则：不确定 / 你决定就好 这类选项一律保留。
    """
    kind = kind or KIND_PROGRAM
    kind_q = dict(KIND_QUESTION)
    base = [q for q in base_questions if q["key"] != kind_q["key"]]

    if kind == KIND_PLUGIN:
        skip = set(PROGRAM_ONLY_KEYS)
        head = [q for q in base if q["key"] in ("what",)]
        plugin_core = [q for q in PLUGIN_QUESTIONS if q["key"] in
                       ("plugin_host", "plugin_trigger", "plugin_interface")]
        plugin_rest = [q for q in PLUGIN_QUESTIONS if q["key"] not in
                       ("plugin_host", "plugin_trigger", "plugin_interface")]
        rest = [q for q in base if q["key"] not in ("what",)]
        out = [kind_q] + head + plugin_core + [q for q in rest if q["key"] not in skip] \
            + plugin_rest
        new_keys = {"kind"} | {q["key"] for q in PLUGIN_QUESTIONS}
    elif kind == KIND_SCRIPT:
        skip = set(SCRIPT_SKIP_KEYS)
        head = [q for q in base if q["key"] == "what"]
        rest = [q for q in base if q["key"] != "what"]
        out = [kind_q] + head + list(SCRIPT_QUESTIONS) + \
            [q for q in rest if q["key"] not in skip]
        new_keys = {"kind"} | {q["key"] for q in SCRIPT_QUESTIONS}
    else:
        out = [kind_q] + base
        new_keys = {"kind"}

    result = []
    for i, q in enumerate(out, 1):
        aq = _with_number(_adapt_static(q, locale), i)
        # 标出「这一题是按类型新加/换过的」，让界面能给出准确提示
        aq["kind_theme"] = q["key"] in new_keys
        result.append(aq)
    return result




# 原始标题里开头的题号，需要按新顺序重写（"3. 这个软件…" → "4. 这个软件…"）
_NUM_RE = re.compile(r"^(\d+)([.、])\s*")


def _strip_number(title):
    """去掉标题开头的题号。"""
    return _NUM_RE.sub("", str(title or "")).strip()


def _with_number(q, n):
    """把题目的标题改成按当前位置编号。

    ★ 为什么要在渲染时重写编号：插件的题集和程序的不同，
      插进去以后原来的「3. 4. 5.」就乱了。
      与其维护三套写死编号的标题（三语 × 多套 = 容易对不上），
      不如存**不带编号**的原文，编号在组装时统一加。
    """
    out = dict(q)
    out["title"] = "%d. %s" % (n, _strip_number(q.get("title")))
    return out
