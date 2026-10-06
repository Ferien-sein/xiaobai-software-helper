# -*- coding: utf-8 -*-
"""更新 README：问题表改成 13 题（含新的系统/位数题），并补上三语说明与截图。"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")

NEW_TABLE = """| # | 问题 | 为什么必须问 |
|---|---|---|
| 1 | 你想做一个什么样的软件 | 定方向 |
| 2 | 给谁用、几个人用 | 决定要不要登录 / 联网 |
| **3** | **跑在什么系统、32 位还是 64 位** | **选错会导致「你这边做好了，别人打不开」；默认自动取你的电脑** |
| 4 | 在哪里打开、要不要联网 | 决定做成桌面程序还是网页 |
| 5 | 现在你是怎么手动做的 | 最有用的一格，越具体越贴合实际 |
| 6 | 你希望怎么操作它 | 你描述步骤，我照做界面 |
| 7 | 输入从哪来、长什么样 | 保证读得进、读得对 |
| 8 | 输出要长什么样 | 定验收标准 |
| 9 | 怎么算做好了 | 让我能自己测到对为止 |
| 10 | 什么不能做 / 什么规矩 | 防止动到不该动的数据 |
| 11 | 有没有参照物（可选） | 一个参照胜过形容半天 |
| 12 | 希望怎么交付（可选） | exe / 文件夹 / 网页 |
| 13 | 还想补充什么（可选） | 零散想法和担心 |
"""


def main():
    src = io.open(README, encoding="utf-8", newline=None).read()
    before = src

    # 1) 问题表：整块替换
    m = re.search(r"\| # \| 问题 \| 为什么必须问 \|\n\|[-\|]+\|\n(?:\|.*\n)+", src)
    if m:
        src = src[:m.start()] + NEW_TABLE + src[m.end():]
        print("问题表已替换为 13 题")
    else:
        print("✘ 找不到问题表")

    # 2) 简介：题数与语言、系统探测
    src = src.replace(
        "> 它问你 12 个问题（能点选项就点，不必会打字），自动拼出一段完整的需求说明，",
        "> 它问你 13 个问题（能点选项就点，不必会打字），自动拼出一段完整的需求说明，")
    src = src.replace(
        "> 一个帮你**把\"我想做个软件\"说清楚**的 Windows 桌面小工具。",
        "> 一个帮你**把\"我想做个软件\"说清楚**的 Windows 桌面小工具。\n"
        "> 三语界面（简体 / 繁體 / English）；自动探测你的系统与位数作为默认目标。")

    # 3) 12 个问题 → 13 个
    src = src.replace("12 个问题覆盖了", "13 个问题覆盖了")
    src = src.replace("填入 12 格", "填入 13 格")

    # 4) 截图：补两语
    if "screenshot-zh-tw.png" not in src:
        anchor = "![浅色主题](assets/screenshot-light.png)"
        if anchor in src:
            src = src.replace(
                anchor,
                anchor + "\n\n繁体与英文界面：\n\n"
                "![繁體中文](assets/screenshot-zh-tw.png)\n\n"
                "![English](assets/screenshot-en.png)",
                1)
            print("已补三语截图")

    # 5) 功能清单末尾补两条
    if "界面语言" not in src:
        anchor = "## 功能\n"
        if anchor in src:
            src = src.replace(
                anchor,
                anchor + "\n- **三语界面**：左下角可切换简体 / 繁體 / English，"
                "需求说明正文也跟着语言走\n"
                "- **目标系统与位数**：自动探测你的电脑（Windows/macOS/Linux × 32/64 位）"
                "并作为默认值，写明后 AI 不会做错平台\n",
                1)
            print("已补功能说明")

    if src == before:
        print("没有改动")
        return 0
    io.open(README, "w", encoding="utf-8", newline="\r\n").write(src)
    print("README 已更新")
    return 0


if __name__ == "__main__":
    sys.exit(main())
