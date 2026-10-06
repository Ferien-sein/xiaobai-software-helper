# -*- coding: utf-8 -*-
"""自动化测试：不弹人工窗口，验证界面构建、选项联动、提示词生成、剪贴板、存档。"""
import os, sys, tkinter as tk
from tkinter import messagebox

# APP = 仓库根目录（用于找 需求存档 等产物）；源码在 src/ 里，导入要走那里
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(APP, "src"))
import importlib
mod = importlib.import_module("app")

# 屏蔽弹窗，改成记录
calls = []
messagebox.showinfo = lambda t, m, **k: calls.append(("info", t, m))
messagebox.askyesno = lambda t, m, **k: (calls.append(("ask", t, m)) or True)

root = tk.Tk()
root.withdraw()
app = mod.App(root)
print("[1] 窗口构建成功，题目数量 =", len(mod.QUESTIONS))
print("[2] 输入框控件 =", sum(1 for k in app.widgets if not k.endswith('__status')))
print("[3] 选项按钮 =", len(app.option_buttons))

# --- 测试选项点选联动（模拟真实点击：勾选框状态先变，再触发 command） ---
def click_option(key, option):
    var = app.option_buttons[(key, option)][0]
    var.set(not var.get())
    app._toggle(key, option)

click_option("what", "数据汇总/整理类（把文件或表格自动合并、统计）")
click_option("where", "数据不允许上传，必须留在本机")
box_what = app.widgets["what"]
txt_what = box_what.get("1.0", "end").strip()
print("[4] 点选后写入输入框 =>", repr(txt_what))
assert "数据汇总/整理类" in txt_what, "点选内容没有写入输入框"

# --- 手动输入（模拟用户打字：先清掉示例灰字） ---
def type_into(key, text):
    b = app.widgets[key]
    b.configure(foreground="#1b1b1b")
    b.delete("1.0", "end")
    b.insert("1.0", text)
    app._on_typing(key)

type_into("who", "只有我自己用，一台 Windows 11 电脑")
type_into("pain", "每天从系统导出 3 个 Excel，手动复制粘贴汇总，约 40 分钟，常抄错")
type_into("flow", "1）拖入 3 个文件 2）点开始汇总 3）看异常提示 4）点导出到桌面")
type_into("input", "每天 3 个 .xlsx 放「每日数据」文件夹，第一行标题，列：日期/客户/金额，约 200 行")
type_into("output", "屏幕显示总额与异常行；导出 Excel 到桌面，文件名 汇总_日期.xlsx")

# --- 生成提示词 ---
app.refresh()
prompt = app.preview.get("1.0", "end").rstrip()
print("[5] 提示词长度 =", len(prompt), "行数 =", len(prompt.splitlines()))

# 题号不要写死：新增问题后编号会变，按 key 取标题才稳。
# ★ 而且要从**当前生效的题集**取（_active_questions）：问卷会按「做什么类型」
#   和「跑在什么平台」换文案，用全局 QUESTIONS 会拿到没调整过的基础标题。
title_of = {q["key"]: q["title"] for q in app._active_questions()}
# ★ 生成说明里的标题是**不带题号**的正文（题号会随「做什么类型」变），
#   所以比对前统一剥掉编号。
import re as _re
title_body = {k: _re.sub(r"^\d+[.、]\s*", "", v) for k, v in title_of.items()}
must = ["我完全不懂技术", title_body["what"],
        "数据汇总/整理类", "只有我自己用", title_body["done"],
        "请你直接问我", "现在就开工"]
for m in must:
    assert m in prompt, "提示词缺少：" + m
print("[6] 必含内容校验通过")

# 目标平台段（新增功能）：默认值必须被展开成明确的系统与位数
assert "目标平台（重要）" in prompt, "提示词缺少目标平台段"
assert mod.current_platform()["os_label"] in prompt, "目标平台段没写本机系统"
assert "32 位" in prompt and "64 位" in prompt, "目标平台段没讲位数"
print("[6b] 目标平台段正常（含本机系统与位数说明）")

# 未填的格子应该出现占位提示
assert mod.PLACEHOLDER in prompt, "未填格子没有占位提示"
print("[7] 空白格占位提示正常")

# --- 剪贴板 ---
app.copy_prompt()
root.update()
clip = root.clipboard_get()
assert clip.strip() == prompt.strip(), "剪贴板内容与预览不一致"
print("[8] 剪贴板写入成功，长度 =", len(clip))

# --- 保存存档 ---
app.save_prompt()
# ★ 不要自己拼路径：开发模式下数据在 src/ 下，打包后跟着 exe 走。
#   一律用程序自己汇报的目录，免得以后改了布局这个测试就坏。
archive = mod.ARCHIVE_DIR
files = sorted(os.listdir(archive))
print("[9] 存档目录文件 =", files)
assert files, "存档目录为空"
p = os.path.join(archive, files[-1])
with open(p, encoding="utf-8-sig") as f:
    saved = f.read()
assert prompt in saved, "存档正文与预览不一致"
print("[10] 存档内容一致，路径 =", p)
saved_answers = dict(app.collect())   # 供后面历史还原比对

# --- 进度统计 ---
print("[11] 进度条值 =", app.progress["value"], "/", len(mod.QUESTIONS))
print("[12] 进度文字 =", app.progress_label["text"])

# --- 清空 ---
app.clear_all()
app.refresh()
empty_prompt = app.preview.get("1.0", "end").rstrip()
print("[13] 清空后预览长度 =", len(empty_prompt))
assert app.progress["value"] == 0, "清空后进度未归零"
assert box_what.get("1.0", "end").strip().startswith("例如"), "清空后示例未恢复"

# --- 帮助弹窗数据完整性 ---
for q in mod.QUESTIONS:
    assert q["title"] and q["hint"] and q["help"], "题目缺字段：" + q["key"]
print("[14] 所有题目的标题/理由/示例说明齐全")

# ==================== 历史记录功能 ====================
print("\n--- 历史记录 ---")
app.refresh_history()
print("[15] 存档列表条数 =", app.hist_list.size(), "| 状态栏 =", app.hist_status["text"])
assert app.hist_list.size() >= 1, "历史记录列表是空的"

# 载入第一份存档，检查能否精确还原
app.hist_list.selection_clear(0, "end")
app.hist_list.selection_set(0)
app.on_history_select()
preview_shown = app.hist_text.get("1.0", "end")
assert "载入到填写页修改" in preview_shown, "历史预览没提示可载入"
print("[16] 历史预览长度 =", len(preview_shown))

app.load_history()
restored = app.collect()
mismatch = [k for k, v in saved_answers.items() if restored.get(k, "") != v]
print("[17] 载入后与原答案不一致的格子 =", mismatch or "无")
assert not mismatch, "载入还原不精确：" + str(mismatch)

# 还原后重新生成的提示词应当与当初保存的一致
app.refresh()
regen = app.preview.get("1.0", "end").rstrip()
print("[18] 还原后重新生成 == 原存档正文:", regen == prompt)
assert regen == prompt, "还原后生成的内容与原存档不一致"

# 勾选框状态是否跟着还原
what_key = "what"
checked = [o for o in app._options_of(what_key)
           if app.option_buttons[(what_key, o)][0].get()]
print("[19] 还原后 'what' 勾选中的选项 =", checked)
assert "数据汇总/整理类（把文件或表格自动合并、统计）" in checked, "点选状态没还原"

# 复制历史内容
app.copy_history()
root.update()
assert root.clipboard_get().strip() == prompt.strip(), "历史复制内容不一致"
print("[20] 历史内容复制成功")

# 删除一份存档（另存一份再删，别破坏原数据）
app.save_prompt()
app.refresh_history()
n_before = app.hist_list.size()
app.hist_list.selection_clear(0, "end")
app.hist_list.selection_set(0)          # 最新那份
app.delete_history()
app.refresh_history()
print(f"[21] 删除前 {n_before} 份 → 删除后 {app.hist_list.size()} 份")
assert app.hist_list.size() == n_before - 1, "删除没有生效"

# 打开存档文件夹（不真的弹窗，只验证路径存在）
os.makedirs(mod.ARCHIVE_DIR, exist_ok=True)
assert os.path.isdir(mod.ARCHIVE_DIR)
print("[22] 存档文件夹存在:", mod.ARCHIVE_DIR)

# 旧版存档兼容性：手工造一个没有原始答案标记的文件。
# 标题必须用**当前**问卷里的原文 —— 解析是按标题匹配的，
# 写死旧题号（如 ### 6.）在新增问题后会失效。
legacy = os.path.join(mod.ARCHIVE_DIR, "20200101_000000_旧版存档测试.txt")
with open(legacy, "w", encoding="utf-8-sig") as f:
    f.write("【我完全不懂技术，下面是我的需求】\n\n"
            "### " + title_of["what"] + "\n  一个记账小工具\n\n"
            "### " + title_of["pain"] + "\n  手写记在本子上\n")
body, ans = app.read_archive(legacy)
print("[23] 旧版存档正文长度 =", len(body), "| 识别出格子 =", sorted(ans.keys()) if ans else None)
assert ans and ans.get("what") == "一个记账小工具", "旧版存档解析失败"
assert ans.get("pain") == "手写记在本子上", "旧版存档解析不完整"
os.remove(legacy)
print("[24] 旧版存档解析与清理正常")

root.destroy()
print("\n弹窗记录：", [c[1] for c in calls])
print("\n=== 全部测试通过 ===")
