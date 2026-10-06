# -*- coding: utf-8 -*-
"""把 app.py 里剩余的界面文案用 t() 包起来。

为什么要脚本 + 验证：这是几十处机械改写，手改容易漏、也容易改坏语法。
脚本每次都做三件事：改 → 语法检查 → 汇报改了几处；语法坏了就回滚。

只处理**整句文案**（值本身就是完整的一句话），
不碰下面几类：
  · docstring / 注释
  · 多段拼接出来的长文（那些已经分别在别处翻过了，逐段包会失效）
  · 调试输出（XBSH_UI_DEBUG 那几行，只有排错时才看）
  · 文件名常量（需求存档 / 使用说明.txt 这类是路径，不能翻）
"""
import io
import os
import py_compile
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "src", "app.py")

# 精确的「原文 -> 改写后」映射。不做模糊正则替换，避免误伤。
REPLACEMENTS = [
    # --- 动作按钮 ---
    ('text="🔄 刷新"', 'text=t("🔄 刷新")'),
    ('text="📂 打开存档文件夹"', 'text=t("📂 打开存档文件夹")'),
    ('text="↩ 载入到填写页修改"', 'text=t("↩ 载入到填写页修改")'),
    ('text="📋 复制这份内容"', 'text=t("📋 复制这份内容")'),
    ('text="🗑 删除这份存档"', 'text=t("🗑 删除这份存档")'),
    ('text="📋 复制需求"', 'text=t("📋 复制需求")'),
    ('text="💾 保存到文件"', 'text=t("💾 保存到文件")'),
    ('text="🧹 清空重填"', 'text=t("🧹 清空重填")'),
    ('text="知道了"', 'text=t("知道了")'),
    ('text="用这个数"', 'text=t("用这个数")'),
    ('text="关闭"', 'text=t("关闭")'),
    ('text="打开报告所在文件夹"', 'text=t("打开报告所在文件夹")'),

    # --- 标签与标题 ---
    ('text="小白造软件"', 'text=t("小白造软件")'),
    ('text="助手"', 'text=t("助手")'),
    ('text="把想法说清楚，剩下的交给 AI"', 'text=t("把想法说清楚，剩下的交给 AI")'),
    ('text="快速点选（可多选，点了会写进上面的框）"', 'text=t("快速点选（可多选，点了会写进上面的框）")'),
    ('text="自动生成的需求说明"', 'text=t("自动生成的需求说明")'),
    ('text="点「复制需求」后粘贴给 AI 就行"', 'text=t("点「复制需求」后粘贴给 AI 就行")'),
    ('text="填写任意内容都会自动生成，随时可以复制。"', 'text=t("填写任意内容都会自动生成，随时可以复制。")'),
    ('text="存档列表（双击可载入）"', 'text=t("存档列表（双击可载入）")'),
    ('text="内容预览"', 'text=t("内容预览")'),
    ('text="字号档位："', 'text=t("字号档位：")'),
    ('text="界面整体大小："', 'text=t("界面整体大小：")'),
    ('text="更细的："', 'text=t("更细的：")'),

    # --- 单行状态栏 ---
    ('self.set_status("已载入存档，改完再点「复制需求」发给 AI 就行。")',
     'self.set_status(t("已载入存档，改完再点「复制需求」发给 AI 就行。"))'),
    ('self.set_status("已复制 ✔  现在切到 AI 对话框，按 Ctrl+V 粘贴，发送就行了。")',
     'self.set_status(t("已复制 ✔  现在切到 AI 对话框，按 Ctrl+V 粘贴，发送就行了。"))'),
    ('self.set_status("已清空，可以从第 1 格重新填。")',
     'self.set_status(t("已清空，可以从第 1 格重新填。"))'),
    ('self.set_status("已保存：" + path)',
     'self.set_status(t("已保存：") + path)'),
    ('app.set_status("诊断报告已生成：" + path)',
     'app.set_status(t("诊断报告已生成：") + path)'),

    # --- 弹窗标题与正文（单句）---
    ('messagebox.showinfo("还没有选中", "请先在左边列表里点一份存档。")',
     'messagebox.showinfo(t("还没有选中"), t("请先在左边列表里点一份存档。"))'),
    ('messagebox.showinfo("复制成功",', 'messagebox.showinfo(t("复制成功"),'),
    ('messagebox.showinfo("已保存",', 'messagebox.showinfo(t("已保存"),'),
    ('messagebox.askyesno("确认清空", "要把所有填写内容清空，重新开始吗？")',
     'messagebox.askyesno(t("确认清空"), t("要把所有填写内容清空，重新开始吗？"))'),
    ('messagebox.showinfo("不用改", "当前就是这个字号。")',
     'messagebox.showinfo(t("不用改"), t("当前就是这个字号。"))'),
    ('messagebox.showinfo("不用改", "当前就是这个显示大小。")',
     'messagebox.showinfo(t("不用改"), t("当前就是这个显示大小。"))'),
    ('messagebox.showwarning("打不开文件夹", str(e))',
     'messagebox.showwarning(t("打不开文件夹"), str(e))'),
    ('messagebox.showerror("删除失败", str(e))',
     'messagebox.showerror(t("删除失败"), str(e))'),
    ('messagebox.showwarning("无法完整还原",', 'messagebox.showwarning(t("无法完整还原"),'),
    ('top.title("显示大小 / 分辨率自适应")', 'top.title(t("显示大小 / 分辨率自适应"))'),
    ('top.title("显示诊断")', 'top.title(t("显示诊断"))'),
]


def compile_ok(path):
    try:
        with tempfile.TemporaryDirectory() as td:
            py_compile.compile(path, cfile=os.path.join(td, "x.pyc"), doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)


def main():
    src = io.open(PATH, encoding="utf-8", newline=None).read()
    backup = src

    applied = 0
    skipped = []
    for old, new in REPLACEMENTS:
        if new in src:
            skipped.append((old, "已经是包好的"))
            continue
        if old not in src:
            skipped.append((old, "找不到该写法"))
            continue
        src = src.replace(old, new)
        applied += 1

    if src == backup:
        print("没有需要改的地方")
        return 0

    io.open(PATH, "w", encoding="utf-8", newline="\r\n").write(src)

    ok, err = compile_ok(PATH)
    if not ok:
        io.open(PATH, "w", encoding="utf-8", newline="\r\n").write(backup)
        print("✘ 改完语法错误，已回滚：")
        print("   " + (err or "").split("\n")[0])
        return 1

    print("已包 t() 共 %d 处，语法检查通过" % applied)
    if skipped:
        print("\n跳过 %d 处：" % len(skipped))
        for old, why in skipped:
            print("  [%s] %s" % (why, old[:76]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
