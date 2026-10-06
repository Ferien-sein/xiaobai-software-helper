# -*- coding: utf-8 -*-
"""小白造软件助手 —— 安装程序。

## 为什么自己做，而不是用 Inno Setup

这台机器上没有 Inno Setup / NSIS，也不该为了打包去装一个新工具。
tkinter 是 Python 自带的，PyInstaller 又能把它打进一个 exe ——
于是「安装器」本身就是一个单文件 exe，用户双击即可，不需要额外依赖。

## 一个必须讲清楚的坑

装到 C:\\Program Files 会**要求管理员权限**，而且装完之后程序目录只读。
本程序把存档和配置写在数据目录里，所以：
  · 默认装到 %LOCALAPPDATA%\\Programs\\小白造软件助手（用户可写、无需管理员）
  · 用户要是选了 Program Files，安装器会明确提示；装完后应用自己会退到
    %APPDATA%\\小白造软件助手 存数据（app.py 里的 _pick_app_dir 负责）。

## 用法

  python installer.py            # 直接运行（开发时用）
  python installer.py --list     # 只列出会安装哪些文件，不装

打包成安装器 exe：
  python build_installer.py      # 见同目录脚本
"""
import json
import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

HERE = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "小白造软件助手"


def _force_utf8_output():
    """命令行输出的中文在 Windows GBK 控制台上会乱码。

    本项目的 check_i18n.py 就因为这个崩过一次（print 中文 → UnicodeEncodeError
    → exit 1，看起来像「检查失败」，其实是工具挂了）。
    安装器的 --list / --uninstall 也会打印中文，所以同样要处理。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001  老 Python 没有 reconfigure
            pass


_force_utf8_output()

APP_ID = "xiaobai-software-helper"
APP_VERSION = "1.13.0"

def _payload_dir():
    """安装内容放在哪。

    ★ 两种运行方式位置不同：
      源码运行  → installer/payload/
      打包运行  → PyInstaller 解压出来的临时目录（sys._MEIPASS）/payload
    不区分的话，打包出来的安装器会找不到内容。
    """
    if getattr(sys, "frozen", False):
        return os.path.join(getattr(sys, "_MEIPASS", HERE), "payload")
    return os.path.join(HERE, "payload")


PAYLOAD = _payload_dir()

# 卸载时不要动的用户数据（在用户目录，不在安装目录）
KEEP_HINT = "你的存档不会被删除（它们在你的用户目录里）"


def default_dir():
    """默认安装位置：用户可写、不需要管理员。

    ★ 故意不默认 Program Files：那会弹 UAC，而且装完程序目录只读，
      应用得把数据挪到用户目录 —— 对不懂技术的用户是额外的困惑。
    """
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") \
            or os.path.expanduser("~")
        return os.path.join(base, "Programs", APP_NAME)
    return os.path.join(os.path.expanduser("~"), ".local", "share", APP_ID)


def is_program_files(path):
    """这个路径是不是在 Program Files 底下（会要管理员权限）。"""
    p = os.path.normcase(os.path.abspath(path))
    roots = []
    for env in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        v = os.environ.get(env)
        if v:
            roots.append(os.path.normcase(os.path.abspath(v)))
    return any(p == r or p.startswith(r + os.sep) for r in roots)


def desktop_link_path():
    if os.name != "nt":
        return None
    d = os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(d, APP_NAME + ".lnk")


def start_menu_dir():
    if os.name != "nt":
        return None
    base = os.environ.get("APPDATA")
    if not base:
        return None
    return os.path.join(base, "Microsoft", "Windows", "Start Menu", "Programs", APP_NAME)


def make_shortcut(link_path, target, workdir, icon=None):
    """用 WScript.Shell 建 .lnk。

    为什么不用 pywin32：那是个额外依赖，而 WScript.Shell 是 Windows 自带的，
    通过 PowerShell 调一次就行。
    """
    ps = (
        "$w = New-Object -ComObject WScript.Shell; "
        "$s = $w.CreateShortcut('%s'); "
        "$s.TargetPath = '%s'; "
        "$s.WorkingDirectory = '%s'; "
        "%s"
        "$s.Save()"
    ) % (
        link_path.replace("'", "''"),
        target.replace("'", "''"),
        workdir.replace("'", "''"),
        ("$s.IconLocation = '%s'; " % icon.replace("'", "''")) if icon else "",
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, text=True, timeout=30)


def long_path(path):
    """把 8.3 短路径还原成完整路径。

    为什么需要：命令行传进来的可能是 C:\\Users\\汐仔小~1\\...（短名），
    卸载时按短名判断目录会对不上。os.path.abspath 不解析短名，
    要用 Windows 的 GetLongPathNameW。
    """
    p = os.path.abspath(path)
    if os.name != "nt":
        return p
    try:
        import ctypes
        GetLong = ctypes.windll.kernel32.GetLongPathNameW
        n = GetLong(p, None, 0)
        if n:
            buf = ctypes.create_unicode_buffer(n)
            if GetLong(p, buf, n):
                return buf.value
    except Exception:  # noqa: BLE001  拿不到就用原路径，不影响安装
        pass
    return p


def collect_payload():
    """安装包里有哪些文件。"""
    if not os.path.isdir(PAYLOAD):
        return None
    items = []
    for root, _dirs, files in os.walk(PAYLOAD):
        for f in files:
            src = os.path.join(root, f)
            rel = os.path.relpath(src, PAYLOAD)
            items.append((src, rel, os.path.getsize(src)))
    return items


def total_size(items):
    return sum(s for _s, _r, s in items)


# ---------------------------------------------------------------------------
# 安装逻辑（和界面分开，便于测试）
# ---------------------------------------------------------------------------

def install_to(target, items, progress=None, log=print, desktop_shortcut=True):
    """把 payload 里的文件复制到 target。

    ★ 先写临时目录再改名，避免「装到一半失败留下半个程序」。
    """
    tmp = target + ".installing"
    if os.path.exists(tmp):
        shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)

    done = 0
    total = total_size(items) or 1
    for src, rel, size in items:
        dst = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        done += size
        if progress:
            progress(done, total, rel)
    log("  文件已复制到临时目录，准备就位")

    # 移除旧版本（保留用户数据是不可能的 —— 数据本来就不在这）
    if os.path.exists(target):
        log("  发现旧版本，先移除")
        shutil.rmtree(target, ignore_errors=True)
    os.rename(tmp, target)
    target = os.path.abspath(target)
    log("  已就位：%s" % target)

    exe = os.path.join(target, APP_ID + ".exe")
    if desktop_shortcut:
        link = desktop_link_path()
        if link and os.path.isdir(os.path.dirname(link)):
            try:
                make_shortcut(link, exe, target, exe)
                log("  已创建桌面快捷方式")
            except Exception as e:  # noqa: BLE001
                log("  [!] 桌面快捷方式没建成：%r" % (e,))
    sm = start_menu_dir()
    if sm:
        try:
            os.makedirs(sm, exist_ok=True)
            make_shortcut(os.path.join(sm, APP_NAME + ".lnk"), exe, target, exe)
            log("  已创建开始菜单项")
        except Exception as e:  # noqa: BLE001
            log("  [!] 开始菜单项没建成：%r" % (e,))

    write_uninstaller(target, items)
    return exe


def write_uninstaller(target, items):
    """在安装目录放一个卸载脚本 + 一个能双击的 .bat。"""
    # ★ 必须存**长路径**：命令行传进来的可能是 8.3 短名
    #   （C:\Users\汐仔小~1\...），卸载时按短名判断目录会对不上。
    #   注意 long_path 只对**已存在**的路径有效，所以要在文件就位之后调用。
    long_target = long_path(target)
    try:
        linfo = {
            "app": APP_NAME,
            "id": APP_ID,
            "version": APP_VERSION,
            "install_dir": long_target,
            "desktop_link": desktop_link_path(),
            "start_menu": start_menu_dir(),
        }
        with open(os.path.join(target, "uninstall-info.json"), "w",
                  encoding="utf-8") as f:
            json.dump(linfo, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

    # .bat 必须是纯 ASCII（cmd 按 ANSI 读，中文路径会乱码）
    bat = os.path.join(target, "Uninstall.bat")
    try:
        with open(bat, "w", encoding="ascii", newline="\r\n") as f:
            f.write("@echo off\r\n")
            f.write('powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"\r\n')
        ps1 = os.path.join(target, "uninstall.ps1")
        with open(ps1, "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write(uninstall_ps1())
        return bat
    except OSError:
        return None


def uninstall_ps1():
    """卸载脚本：删快捷方式、删自己所在的目录。"""
    return """# 小白造软件助手 卸载脚本
$ErrorActionPreference = 'SilentlyContinue'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$info = Get-Content (Join-Path $dir 'uninstall-info.json') -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Host ''
Write-Host '  正在卸载 小白造软件助手 ...' -ForegroundColor Cyan
if ($info.desktop_link -and (Test-Path $info.desktop_link)) {
  Remove-Item $info.desktop_link -Force
  Write-Host '    已删除桌面快捷方式'
}
if ($info.start_menu -and (Test-Path $info.start_menu)) {
  Remove-Item $info.start_menu -Recurse -Force
  Write-Host '    已删除开始菜单项'
}
# 程序目录整块删掉；用户数据在 %APPDATA% 里，这里不动
Start-Process -WindowStyle Hidden -FilePath 'cmd.exe' `
  -ArgumentList '/c','ping 127.0.0.1 -n 2 >nul & rmdir /s /q "' + $dir + '"'
Write-Host '    正在删除程序文件 ...'
Write-Host ''
Write-Host '  卸载完成。' -ForegroundColor Green
Write-Host '  你的存档没有被删除，还在：%APPDATA%\\小白造软件助手' -ForegroundColor Yellow
Write-Host ''
Write-Host '  按任意键关闭。'
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
"""


# ---------------------------------------------------------------------------
# 界面
# ---------------------------------------------------------------------------

class Installer:
    def __init__(self, root, items):
        self.root = root
        self.items = items
        self.done = False
        root.title("%s 安装程序" % APP_NAME)
        root.geometry("640x440")
        root.resizable(False, False)

        pad = {"padx": 18, "pady": 6}

        ttk.Label(root, text="安装 %s" % APP_NAME,
                  font=("Microsoft YaHei UI", 16)).pack(anchor="w", **pad)
        ttk.Label(root, text="版本 %s　·　一共 %d 个文件，约 %.1f MB"
                  % (APP_VERSION, len(items), total_size(items) / 1024 / 1024),
                  foreground="#666").pack(anchor="w", padx=18)

        box = ttk.LabelFrame(root, text=" 装到哪里 ")
        box.pack(fill="x", **pad)

        self.var_dir = tk.StringVar(value=default_dir())
        row = ttk.Frame(box)
        row.pack(fill="x", padx=10, pady=8)
        entry = ttk.Entry(row, textvariable=self.var_dir)
        entry.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="浏览…", command=self.browse).pack(side="left", padx=(8, 0))

        self.warn = ttk.Label(box, text="", foreground="#b06000", wraplength=560,
                              justify="left")
        self.warn.pack(anchor="w", padx=10, pady=(0, 8))
        self.var_dir.trace_add("write", lambda *_: self.check_dir())
        self.check_dir()

        opt = ttk.LabelFrame(root, text=" 选项 ")
        opt.pack(fill="x", **pad)
        self.var_desktop = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt, text="在桌面放一个快捷方式",
                        variable=self.var_desktop).pack(anchor="w", padx=10, pady=4)
        self.var_run = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt, text="装完马上打开",
                        variable=self.var_run).pack(anchor="w", padx=10, pady=(0, 8))

        self.bar = ttk.Progressbar(root, mode="determinate")
        self.bar.pack(fill="x", padx=18, pady=(8, 2))
        self.status = ttk.Label(root, text="点「开始安装」即可。", foreground="#666")
        self.status.pack(anchor="w", padx=18)

        self.log = tk.Text(root, height=6, wrap="word", relief="solid", borderwidth=1)
        self.log.pack(fill="both", expand=True, padx=18, pady=(6, 0))
        self.log.configure(state="disabled")

        btns = ttk.Frame(root)
        btns.pack(fill="x", padx=18, pady=12)
        self.btn_install = ttk.Button(btns, text="开始安装", command=self.go)
        self.btn_install.pack(side="right")
        ttk.Button(btns, text="取消", command=root.destroy).pack(side="right", padx=(0, 8))

    def say(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.root.update_idletasks()

    def check_dir(self):
        d = self.var_dir.get().strip()
        if not d:
            self.warn.configure(text="")
            return
        if is_program_files(d):
            self.warn.configure(
                text="⚠️ 你选的是 Program Files，安装需要管理员权限，而且这个目录是只读的。\n"
                     "   程序能装进去，但你的存档会被放到  %APPDATA%\\小白造软件助手。\n"
                     "   不想这么麻烦就点「浏览」换一个自己文件夹里的位置（推荐）。")
        else:
            self.warn.configure(text="")

    def browse(self):
        d = filedialog.askdirectory(title="选择安装位置",
                                    initialdir=os.path.dirname(self.var_dir.get()))
        if d:
            self.var_dir.set(os.path.join(d, APP_NAME))

    def go(self):
        target = self.var_dir.get().strip()
        if not target:
            messagebox.showwarning("还没选位置", "请先选择要装到哪个文件夹。")
            return
        try:
            os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        except OSError as e:
            messagebox.showerror("这个位置不能用", str(e))
            return

        self.btn_install.configure(state="disabled")
        self.status.configure(text="正在安装…")
        try:
            exe = install_to(
                target, self.items,
                progress=self._progress,
                log=self.say,
                desktop_shortcut=self.var_desktop.get(),
            )
        except PermissionError:
            self.btn_install.configure(state="normal")
            self.status.configure(text="安装失败：没有写入权限。")
            messagebox.showerror(
                "没有写入权限",
                "装到这个文件夹需要管理员权限。\n\n"
                "两个办法：\n"
                "  1. 换一个自己文件夹里的位置（推荐，最省事）\n"
                "  2. 右键这个安装程序 → 以管理员身份运行")
            return
        except Exception as e:  # noqa: BLE001
            self.btn_install.configure(state="normal")
            self.status.configure(text="安装失败。")
            messagebox.showerror("安装失败", repr(e))
            return

        self.bar["value"] = 100
        self.status.configure(text="安装完成。")
        self.say("")
        self.say("安装完成！程序在：%s" % target)
        self.say("要卸载的话，双击安装目录里的 Uninstall.bat。")
        self.say(KEEP_HINT + "。")
        self.done = True

        if self.var_run.get():
            try:
                os.startfile(exe) if os.name == "nt" else subprocess.Popen([exe])
            except OSError:
                pass
        if messagebox.askyesno("装好了", "安装完成！\n\n要现在打开文件夹看看吗？"):
            try:
                os.startfile(target) if os.name == "nt" else None
            except OSError:
                pass
        self.root.destroy()

    def _progress(self, done, total, rel):
        self.bar["value"] = 100.0 * done / max(1, total)
        if done == total:
            return
        self.root.update_idletasks()


def do_uninstall(quiet=False):
    """从安装目录卸载（命令行用，也便于自动化测试）。

    刻意**不删**用户目录里的存档 —— 那是用户的资料。
    """
    target = None
    info = os.path.join(HERE, "uninstall-info.json")
    if os.path.exists(info):
        try:
            with open(info, encoding="utf-8") as f:
                target = json.load(f).get("install_dir")
        except (OSError, ValueError):
            target = None
    if not target:
        # 打包运行时间：假定自己在安装目录里
        target = HERE

    msgs = []
    link = desktop_link_path()
    if link and os.path.exists(link):
        try:
            os.remove(link)
            msgs.append("已删除桌面快捷方式")
        except OSError:
            pass
    sm = start_menu_dir()
    if sm and os.path.isdir(sm):
        shutil.rmtree(sm, ignore_errors=True)
        msgs.append("已删除开始菜单项")

    # 删程序文件（自己可能就在里面，交给系统稍后删）
    if os.path.normcase(os.path.abspath(target)) != os.path.normcase(HERE):
        shutil.rmtree(target, ignore_errors=True)
        msgs.append("已删除程序文件：%s" % target)
    else:
        msgs.append("程序文件在：%s（请手动删除该文件夹）" % target)

    msgs.append("你的存档没有被删除，还在：%s" % os.path.join(
        os.environ.get("APPDATA", "~"), APP_NAME))
    if not quiet:
        for m in msgs:
            print("  " + m)
    return 0


def main():
    if "--uninstall" in sys.argv:
        return do_uninstall(quiet="--quiet" in sys.argv)

    items = collect_payload()
    if items is None:
        print("找不到 payload 目录：%s" % PAYLOAD)
        print("先跑 build_installer.py 准备安装内容。")
        return 1

    # 命令行安装（便于自动化验证整个 exe，也方便给高级用户脚本化部署）
    if "--install-to" in sys.argv:
        i = sys.argv.index("--install-to")
        if i + 1 >= len(sys.argv):
            print("用法: --install-to <目录> [--no-shortcut] [--quiet]")
            return 1
        target = sys.argv[i + 1]
        no_sc = "--no-shortcut" in sys.argv
        quiet = "--quiet" in sys.argv
        if not quiet:
            print("安装到: %s" % target)
            print("  共 %d 个文件，%.1f MB" % (len(items), total_size(items) / 1024 / 1024))
            if is_program_files(target):
                print("  ⚠️ 这是 Program Files，需要管理员权限；")
                print("     装完后你的存档会放到 %s" % os.path.join(
                    os.environ.get("APPDATA", "~"), APP_NAME))
        try:
            exe = install_to(target, items,
                             log=(lambda m: None) if quiet else (lambda m: print("  " + m)),
                             desktop_shortcut=not no_sc)
        except PermissionError:
            print("✘ 没有写入权限。换一个自己文件夹里的位置，或以管理员身份运行。")
            return 1
        if not quiet:
            print("完成。程序：%s" % exe)
        return 0

    if "--list" in sys.argv:
        print("会安装 %d 个文件，共 %.1f MB：" % (len(items), total_size(items) / 1024 / 1024))
        for _s, rel, size in sorted(items, key=lambda x: x[1])[:40]:
            print("  %8.1f KB  %s" % (size / 1024, rel))
        if len(items) > 40:
            print("  ... 还有 %d 个" % (len(items) - 40))
        return 0

    root = tk.Tk()
    Installer(root, items)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
