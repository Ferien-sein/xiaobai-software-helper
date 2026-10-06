# -*- coding: utf-8 -*-
"""把 dist/ 里的程序打包成一个「可指定安装位置」的安装器 exe。

流程：
  1. 检查 dist/ 里的程序是否已构建（没有就先跑 build.bat）
  2. 把 dist 的内容复制到 installer/payload/
  3. 用 PyInstaller 把 installer.py 打成一个 exe，payload 作为数据嵌进去
  4. 产物：installer/dist/小白造软件助手-安装程序.exe

为什么用 --onefile 给安装器：安装器本身只有一个文件才好分发，
解压到临时目录没关系（它只是把 payload 拷到用户选的位置）。

用法: python build_installer.py
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist", "xiaobai-software-helper")
PAYLOAD = os.path.join(HERE, "payload")
OUTNAME = "xiaobai-software-helper-setup"

PY = sys.executable


def human(n):
    return "%.1f MB" % (n / 1024.0 / 1024.0)


def dir_size(p):
    t = 0
    for root, _d, files in os.walk(p):
        for f in files:
            try:
                t += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return t


def main():
    if not os.path.exists(os.path.join(DIST, "xiaobai-software-helper.exe")):
        print("✘ 找不到 %s" % os.path.join(DIST, "xiaobai-software-helper.exe"))
        print("  先构建程序：在仓库根目录跑 build.bat（或用 build_exe 的等效命令）")
        return 1

    print("[1/3] 准备安装内容")
    if os.path.exists(PAYLOAD):
        shutil.rmtree(PAYLOAD)
    shutil.copytree(DIST, PAYLOAD)
    n = sum(len(f) for _r, _d, f in os.walk(PAYLOAD))
    print("      已复制 %d 个文件，%s" % (n, human(dir_size(PAYLOAD))))

    print("[2/3] 打包安装器（单文件）")
    # payload 作为数据嵌入；运行时落进 sys._MEIPASS
    sep = ";" if os.name == "nt" else ":"
    add_data = "%s%s%s" % (PAYLOAD, sep, "payload")
    cmd = [
        PY, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
        "--name", OUTNAME,
        "--distpath", os.path.join(HERE, "dist"),
        "--workpath", os.path.join(HERE, "build"),
        "--specpath", os.path.join(HERE, "build"),
        "--add-data", add_data,
        os.path.join(HERE, "installer.py"),
    ]
    print("      运行:", " ".join(cmd[:6]), "...")
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("✘ PyInstaller 失败")
        tail = (r.stderr or r.stdout or "").strip().splitlines()
        for line in tail[-15:]:
            print("    " + line)
        return 1
    print("      用时 %.1f 秒" % (time.time() - t0))

    exe = os.path.join(HERE, "dist", OUTNAME + ".exe")
    if not os.path.exists(exe):
        print("✘ 没生成 %s" % exe)
        return 1

    print("[3/3] 完成")
    print("      安装器：%s（%s）" % (exe, human(os.path.getsize(exe))))
    print()
    print("  注意：安装器内部要解压 payload，所以它比程序本身大。")
    print("  用户双击它就能自己选安装位置。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
