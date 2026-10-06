# -*- coding: utf-8 -*-
"""更新 README 与 CHANGELOG，写入本轮新增的三语与系统/位数功能。

用脚本而不是手改：README 里有多处需要同步的数字与清单
（功能列表、截图清单、自检清单、版本号），漏一处就不一致。
脚本改完会打印实际替换结果，便于核对。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")

changelog_entry = """## v1.9.0

### 新增：界面语言（简体中文 / 繁體中文 / English）
- 左下角新增「界面语言」按钮，选择后界面重新打开，语言会被记住
- 也可以用环境变量 `XBSH_LANG=zh-CN|zh-TW|en` 临时指定
- 需求说明**正文**（不只是界面）也全部本地化：生成出来的那份文本会跟着语言走
- 繁体用台湾用词（資訊／檔案／資料夾／軟體／視窗／螢幕），不是简繁字面转换
- 语言包缺失的条目会回退显示简体，不会崩；`tools/check_i18n.py` 会在发布前报出缺口

### 新增：目标系统与位数（问卷第 3 题）
- 明确问「跑在 Windows / macOS / Linux，32 位还是 64 位」
- **默认值自动取你自己的电脑**：选项第一项就是「跟我电脑一样：Windows 64 位（推荐）」
- 帮助文字里直接写出探测结果与兼容性提醒
  （32 位程序在 32/64 位系统上都能跑，64 位程序在 32 位系统上跑不起来）
- 需求说明里单独加一段「目标平台（重要）」，把探测依据也写进去，方便 AI 复核
- 探测不确定时（如 ARM64 机器上跑 x64 解释器）会**如实标注**，不假装知道

### 修复
- 输入框有内容后，状态标签会变回简体「待填写」—— 英文界面下会出现中英混排
- 侧栏宽度原来写死 214px，是按中文量的；切到英文后标签被截断。
  现改为按实际文字宽度计算
- 截图工具靠中文字符串找窗口，切到英文/繁体后匹配不到，会抓到**别的程序**的窗口。
  改为按进程 ID + 多语言标题匹配，并在被遮挡时用 `PrintWindow` 直接取窗口内容
- 繁体语言包文件曾被补丁脚本写坏（少了收尾括号），已重建并加入修复工具

### 工具
- `tools/check_encoding.py`：编码守卫。抓 BOM、被 ANSI 写坏的中文、行尾混用
- `tools/check_i18n.py`：按 `t()` 调用点核对语言包覆盖，报出会回退的条目
- `tools/selftest_i18n_output.py`：端到端验证**生成的需求说明**确实按语言本地化
- `tools/selftest_platform.py`：21 项平台/位数与问卷集成测试
- `tools/screenshot_langs.py`：三语各截一张图

"""


def update_changelog():
    src = io.open(CHANGELOG, encoding="utf-8", newline=None).read()
    if "## v1.9.0" in src:
        print("CHANGELOG 已有 v1.9.0，跳过")
        return
    # 插到第一个 "## " 标题之前（保持倒序）
    m = re.search(r"^## ", src, re.M)
    if not m:
        src = changelog_entry + src
    else:
        src = src[:m.start()] + changelog_entry + src[m.start():]
    io.open(CHANGELOG, "w", encoding="utf-8", newline="\r\n").write(src)
    print("CHANGELOG 已插入 v1.9.0")


def update_readme():
    src = io.open(README, encoding="utf-8", newline=None).read()
    before = src

    # 1) 语言与目标系统写进开头简介
    marker = "把「我想要一个软件」"
    if marker in src and "三语界面" not in src:
        src = src.replace(
            marker,
            "三语界面（简体 / 繁體 / English）、自动探测目标系统与位数，" + marker,
            1)

    # 2) 截图清单：补上两语
    if "screenshot-zh-tw.png" not in src:
        for anchor in ("![暗色](assets/screenshot-dark.png)",
                       "![浅色](assets/screenshot-light.png)"):
            if anchor in src:
                src = src.replace(
                    anchor,
                    anchor + "\n\n繁体与英文界面：\n\n"
                    "![繁體](assets/screenshot-zh-tw.png)\n\n"
                    "![English](assets/screenshot-en.png)",
                    1)
                break

    if src == before:
        print("README：没有需要改的地方（或锚点没找到）")
        return
    io.open(README, "w", encoding="utf-8", newline="\r\n").write(src)
    print("README 已更新")


if __name__ == "__main__":
    update_changelog()
    update_readme()
    sys.exit(0)
