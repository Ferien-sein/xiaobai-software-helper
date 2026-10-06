# AGENTS.md —— 给 AI 助手的工作约定

> 这个文件给**在这个仓库里干活的 AI 助手**看。
> 人（尤其是这个项目的作者）不一定懂编程，所以下面的规矩要**无条件遵守**，
> 不要因为「改动很小」「只是改个文案」就跳过。

---

## 注意事项

### 1、每次改动完成后，都必须创建一个对应的 GIT commit，以便后继追踪和回滚。

- 一次改动 = 一个 commit。改完就提交，不要攒着。
- commit 信息要写**改了什么、为什么改**，不要只写 "update"、"fix"。
- 提交前先看一眼 `git status`，确认没有把构建产物、缓存、临时文件带进去
  （`dist/`、`build/`、`installer/payload/`、`node_modules/`、`config.json`、
  `需求存档/` 都在 `.gitignore` 里，**不要用 `git add -f` 强行加它们**）。
- 如果一次改动包含了多个互不相关的事，拆成多个 commit。
- **反向也要遵守**：发现工作区有未提交的改动，先弄清楚那是谁的、
  该不该提交，不要直接在上面继续改。

### 2、每次改动后，都必须编写或更新相关测试，并在交付给用户前，确保所有测试和验证全部通过。

- 改了逻辑 → 补/改对应的自检脚本；改了文案 → 确认三语仍然 100% 覆盖。
- **不许说「应该没问题」**。跑完再说，并把真实结果贴出来（包括失败项）。
- 测试**失败或跳过**都要如实说，不要把它说成通过。
- 修 bug 时，**优先先写一个能复现它的测试**，再修 —— 这样以后不会再犯同一个错
  （这个项目里好几个真 bug 就是这么抓出来的：暗色主题文字看不见、
  换平台后拉窗口崩溃、换类型丢内容）。

#### 这个项目要跑哪些

程序本体（`xiaobai-software-helper`）：

```powershell
# 12 个自检，全部应 exit=0
python tools\selftest_adaptive.py      # 问卷自适应（类型 × 平台）
python tools\selftest_contrast.py      # 配色对比度（防「文字看不见」）
python tools\selftest_functional.py    # 主流程
python tools\selftest_platform.py      # 系统与位数探测
python tools\selftest_i18n_output.py   # 生成的需求说明是否按语言本地化
python tools\selftest_ui_scale.py      # 各缩放比例下的布局
python tools\selftest_scroll.py        # 滚动
python tools\selftest_pages.py         # 页面切换
python tools\selftest_lookup.py        # GitHub 查重
python tools\selftest_lookup_quality.py
python tools\selftest_lookup_ui.py
python tools\selftest_tooling.py       # 检查工具自身是否可靠

# 检查类
python tools\check_i18n.py             # 三语覆盖率（应为 100%）
python tools\check_encoding.py .       # 中文编码（应为 0 个有问题）
python tools\check_option_uniqueness.py
```

> Windows 控制台上跑这些脚本时建议加 `-X utf8`，
> 或者设 `$env:PYTHONIOENCODING = "utf-8"`，否则中文可能显示成乱码。

插件（`dsh-requirement-check`）：

```powershell
node test\run.mjs        # 71 项
node test\lookup.mjs     # 25 项（用 mock，不联网）
python tools\preflight.py
```

#### 交付前的最低要求

| 项目 | 要求 |
|---|---|
| 所有自检 | 全部 exit=0，**没有失败项** |
| 三语覆盖 | 100%（`check_i18n.py` 会报具体缺哪条） |
| 编码检查 | 0 个有问题 |
| 界面改动 | **真的启动界面看一眼**（自动化测试替代不了肉眼） |
| 打包产物 | 改了源码就要重新打包，并从**打包后的 exe** 验证一次 |

#### 为什么要「真的启动看一眼」

这个项目的作者反馈过两次问题，都是自动化测试没覆盖到的：

- 暗色主题下打完字看不见自己打了什么（硬编码了浅色主题的文字色）
- 想做手机 App，但后面的问题全在问 Windows 的事

所以：**测试通过 ≠ 用户能用**。界面相关的改动一定要实际跑起来看。

---

## 一些项目约定（避免改出问题）

- **别在 `THEMES` 之外写死颜色**。有自检盯着这条：写死颜色换主题后不会跟着变。
- **文案一律走 `t("简体中文原文")`**，简体原文就是键。语言包分三份
  （`i18n_zh_tw.py` / `i18n_en.py`），改文案要同步补两份，靠 `check_i18n.py` 兜住。
- **题号不要写死**。问卷的题号会随「做什么类型」「跑在什么平台」变，
  编号在 `questionnaire.questions_for()` 里按位置统一加。
- **`.bat` 文件必须是纯 ASCII**。cmd 按系统 ANSI 读 `.bat`，
  中文会变乱码、脚本直接坏掉。需要中文提示就放到 `.ps1` 或 Python 里。
- **改文本文件用编辑器工具或 Python，不要用 PowerShell 的 `Set-Content`**。
  它默认按 ANSI 写，会把中文写坏（这个坑踩过）。
- **不要删测试来让测试通过**。测试失败说明有问题，去修问题本身。
