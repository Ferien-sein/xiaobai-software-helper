# -*- coding: utf-8 -*-
"""端到端演示：模拟一个小白填完 13 格，导出实际会发给 AI 的那段文字。"""
import os, sys, tkinter as tk
from tkinter import messagebox

# APP = 仓库根目录；源码在 src/ 里，导入要走那里
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(APP, "src"))
import importlib
mod = importlib.import_module("app")
messagebox.showinfo = lambda *a, **k: None
messagebox.askyesno = lambda *a, **k: False

DEMO = {
    "what": "一个帮我把每天的三份销售 Excel 自动合并汇总、并标出金额对不上行的小工具",
    "who": "只有我自己用，一台 Windows 11 电脑",
    "where": "在 Windows 电脑上双击打开，不用联网，数据必须留在本机",
    "pain": "每天下午我从系统导出 3 个表，手动复制粘贴到汇总表，再一个个核对客户名，"
            "一般要 40 分钟；月底经常发现有两行金额抄错了。",
    "flow": "1）双击打开，看到一个大按钮「选择文件」\n"
            "2）我把当天的 3 个 Excel 拖进去\n"
            "3）点「开始汇总」\n"
            "4）它显示一共多少条、有哪几行金额对不上\n"
            "5）点「导出结果」，在桌面得到一个汇总表",
    "input": "每天 3 个 .xlsx 文件放在「每日数据」文件夹，第一行是标题，"
             "列有 日期/客户/金额，每天约 200 行；文件名带日期。\n"
             "我会放一份样例文件在文件夹里给你参考。",
    "output": "屏幕显示总金额和异常行（红字）；导出 Excel 到桌面，"
              "文件名 汇总_当天日期.xlsx，金额保留两位小数、表头加粗。",
    "done": "拿上周的 3 个文件跑一遍，总金额和财务给的数字一模一样，"
            "异常行全部被标出来；以前 40 分钟的活现在 2 分钟内做完。",
    "limit": "不要动 D 盘的财务原始文件；数据绝对不能上传到网上；每次操作前先自动备份一份。",
    "ref": "没有参照，你设计一个简洁的",
    "install": "一个 exe 文件，双击打开，放到桌面方便我随时点开",
    "extra": "我不懂技术，请用大白话解释并一步步教我怎么用；先做最简单能用的版本，"
             "我试过再加功能；我怕数据丢了，请做好备份。",
}

root = tk.Tk(); root.withdraw()
app = mod.App(root)
for k, v in DEMO.items():
    b = app.widgets[k]
    b.configure(foreground="#1b1b1b")
    b.delete("1.0", "end")
    b.insert("1.0", v)
    app._on_typing(k)
app.refresh()

prompt = app.preview.get("1.0", "end").rstrip()
out = os.path.join(APP, "assets", "sample-output.txt")
with open(out, "w", encoding="utf-8-sig") as f:
    f.write(prompt + "\n")

print("进度:", app.progress_label["text"])
print("生成字数:", len(prompt))
print("已写出示范文件:", out)
print("=" * 60)
print(prompt[:900])
print("...\n（后面就是 13 格内容的完整罗列，此处省略）")
root.destroy()
