# -*- coding: utf-8 -*-
"""平台与位数探测（Windows 应用用）

对标插件里的 src/platform.js，逻辑保持一致：
  - 探测本机操作系统与 32/64 位
  - 32 位程序能跑在 32/64 位系统上，64 位程序在 32 位系统上跑不起来
  - 不确定时如实标出来，不假装知道

为什么单独成文件：app.py 已经 2300 多行，探测逻辑是可独立测试的纯函数，
放这里能被自检脚本直接 import。
"""
import os
import platform
import struct
import sys

# 操作系统标识
OS_WIN = "win"
OS_MAC = "mac"
OS_LINUX = "linux"

OS_LABELS = {
    OS_WIN: "Windows",
    OS_MAC: "macOS",
    OS_LINUX: "Linux",
}

# 目标平台可选值（与插件 targets 对齐）
TARGETS = [
    "auto",
    "windows-64", "windows-32", "windows-arm64",
    "macos-64", "macos-arm64",
    "linux-64", "linux-arm64",
    "android-arm64", "android-32",
    "ios",
    "harmony",
    "web",
]

TARGET_LABELS = {
    "auto": {
        "zh-CN": "跟随我的电脑（默认）",
        "zh-TW": "跟隨我的電腦（預設）",
        "en": "Follow my own machine (default)",
    },
    "windows-64": {"zh-CN": "Windows 64 位", "zh-TW": "Windows 64 位元", "en": "Windows 64-bit"},
    "windows-32": {"zh-CN": "Windows 32 位", "zh-TW": "Windows 32 位元", "en": "Windows 32-bit"},
    "windows-arm64": {"zh-CN": "Windows ARM64", "zh-TW": "Windows ARM64", "en": "Windows on ARM64"},
    "macos-64": {"zh-CN": "macOS Intel（x64）", "zh-TW": "macOS Intel（x64）", "en": "macOS on Intel (x64)"},
    "macos-arm64": {
        "zh-CN": "macOS Apple 芯片（M 系列）",
        "zh-TW": "macOS Apple 晶片（M 系列）",
        "en": "macOS on Apple silicon (M-series)",
    },
    "linux-64": {"zh-CN": "Linux 64 位（x64）", "zh-TW": "Linux 64 位元（x64）", "en": "Linux 64-bit (x64)"},
    "linux-arm64": {"zh-CN": "Linux ARM64", "zh-TW": "Linux ARM64", "en": "Linux on ARM64"},
    # ---- 手机 App ----
    "android-arm64": {
        "zh-CN": "安卓手机 App（ARM64，现在的手机基本都是）",
        "zh-TW": "安卓手機 App（ARM64，現在的手機幾乎都是）",
        "en": "Android app (ARM64 — almost every current phone)",
    },
    "android-32": {
        "zh-CN": "安卓手机 App（32 位，给老旧手机）",
        "zh-TW": "安卓手機 App（32 位元，給舊手機）",
        "en": "Android app (32-bit, for older phones)",
    },
    "ios": {
        "zh-CN": "iPhone / iPad App（iOS）",
        "zh-TW": "iPhone / iPad App（iOS）",
        "en": "iPhone / iPad app (iOS)",
    },
    "harmony": {
        "zh-CN": "鸿蒙手机 App（HarmonyOS）",
        "zh-TW": "鴻蒙手機 App（HarmonyOS）",
        "en": "HarmonyOS app",
    },
    "web": {
        "zh-CN": "网页（浏览器打开，电脑手机都能用）",
        "zh-TW": "網頁（瀏覽器開啟，電腦手機都能用）",
        "en": "Web page (works on desktop and phone in a browser)",
    },
}

# 哪些目标属于「手机 App」——用于帮助文字里分场景说明
MOBILE_TARGETS = ("android-arm64", "android-32", "ios", "harmony")

# 各平台交付物的常见形式（帮助文字用）
DELIVERABLE_HINT = {
    "windows": {
        "zh-CN": "Windows 上是 .exe（或一个文件夹，双击里面某个文件）",
        "zh-TW": "Windows 上是 .exe（或一個資料夾，雙擊裡面某個檔案）",
        "en": "On Windows it is an .exe (or a folder with a file to double-click)",
    },
    "mac": {
        "zh-CN": "Mac 上是 .app 或 .dmg",
        "zh-TW": "Mac 上是 .app 或 .dmg",
        "en": "On Mac it is an .app or .dmg",
    },
    "linux": {
        "zh-CN": "Linux 上是 .AppImage 或 .deb",
        "zh-TW": "Linux 上是 .AppImage 或 .deb",
        "en": "On Linux it is an .AppImage or .deb",
    },
    "android": {
        "zh-CN": "安卓是 .apk 安装包（拿到手机里点一下就能装；上应用商店要额外花钱和备案）",
        "zh-TW": "安卓是 .apk 安裝檔（拿到手機裡點一下就能裝；上應用程式商店要額外花錢和審核）",
        "en": "Android is an .apk you install by tapping it on the phone "
              "(publishing to an app store costs money and needs review)",
    },
    "ios": {
        "zh-CN": "iPhone 上要装 App 必须有**苹果开发者账号**（一年 99 美元），"
                 "而且只能自己装或上架 App Store；不确定就选网页版",
        "zh-TW": "iPhone 上要裝 App 必須有**蘋果開發者帳號**（一年 99 美元），"
                 "而且只能自己裝或上架 App Store；不確定就選網頁版",
        "en": "Installing an app on an iPhone requires a paid **Apple Developer account** "
              "(99 USD/year), and it can only be side-loaded or published to the App Store; "
              "if unsure, pick the web version",
    },
    "harmony": {
        "zh-CN": "鸿蒙是 .hap 安装包，通常需要在使用者手机上开启开发者模式",
        "zh-TW": "鴻蒙是 .hap 安裝檔，通常需要在使用者手機上開啟開發者模式",
        "en": "HarmonyOS uses .hap packages and usually needs developer mode enabled on the phone",
    },
    "web": {
        "zh-CN": "网页只有一个网址，电脑和手机都能打开，不需要安装",
        "zh-TW": "網頁只有一個網址，電腦和手機都能開啟，不需要安裝",
        "en": "A web page is just a URL — it opens on desktop and phone with nothing to install",
    },
}


def describe_target(target, locale="zh-CN"):
    """目标值 → 人话（按语言）"""
    entry = TARGET_LABELS.get(target)
    if not entry:
        return str(target)
    return entry.get(locale) or entry["zh-CN"]


def detect_platform():
    """探测本机平台。

    返回 dict：
      os         'win' / 'mac' / 'linux'
      os_label   'Windows' / 'macOS' / 'Linux'
      arch       'x64' / 'x86' / 'arm64' / ...
      bits       32 / 64
      certain    是否确定（False 表示可能是模拟层）
      detail     探测依据，便于排错
    """
    system = platform.system().lower()
    machine = (platform.machine() or "").lower()
    bits = struct.calcsize("P") * 8          # 当前 Python 解释器的位数

    if system.startswith("win"):
        os_id = OS_WIN
    elif system == "darwin":
        os_id = OS_MAC
    else:
        os_id = OS_LINUX

    # 归一化架构名
    if machine in ("amd64", "x86_64", "x64"):
        arch = "x64"
    elif machine in ("x86", "i386", "i686", "32bit"):
        arch = "x86"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        arch = machine or "unknown"

    certain = True
    detail = "platform.system()=%s machine=%s struct=%dbit" % (system, machine, bits)

    # ⚠️ struct.calcsize("P") 报的是**当前 Python 解释器**的位数，
    # 不一定是操作系统的位数。64 位系统上装 32 位 Python 会报 32。
    # 所以这里如实标记「不确定」，而不是假装知道。
    if os_id == OS_WIN:
        # Windows：用注册表看真实 OS 位数作为交叉验证（没有 winreg 就跳过）
        try:
            import winreg  # noqa: WPS433 (只在 Windows 上有)

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            )
            try:
                proc_arch = winreg.QueryValueEx(key, "PROCESSOR_ARCHITECTURE")[0]
            finally:
                winreg.CloseKey(key)
            detail += " PROCESSOR_ARCHITECTURE=%s" % proc_arch
            arm_hint = "ARM64" in str(proc_arch).upper()
            if arm_hint and arch != "arm64":
                # x64 模拟层下跑：机器是 ARM64
                certain = False
            elif bits == 32 and str(proc_arch).upper() in ("AMD64", "ARM64"):
                # 64 位系统 + 32 位 Python → 系统是 64 位，但解释器是 32 位
                certain = False
        except Exception:
            certain = False
    elif os_id == OS_MAC:
        # macOS：process arch 可能是 Rosetta 下的 x64，但机器是 arm64
        try:
            import subprocess

            out = subprocess.run(
                ["/usr/sbin/sysctl", "-n", "hw.optional.arm64"],
                capture_output=True, text=True, timeout=2,
            )
            if out.returncode == 0 and out.stdout.strip() == "1" and arch != "arm64":
                arch = "arm64"
                certain = False
                detail += " hw.optional.arm64=1（当前进程在 Rosetta 下）"
        except Exception:
            certain = False

    return {
        "os": os_id,
        "os_label": OS_LABELS[os_id],
        "arch": arch,
        "bits": bits,
        "certain": certain,
        "detail": detail,
    }


def platform_to_target(det):
    """探测结果 → TARGETS 里的取值"""
    if not det:
        return "auto"
    os_id = det.get("os")
    arch = det.get("arch")
    bits = det.get("bits", 64)
    if os_id == OS_WIN:
        if arch == "arm64":
            return "windows-arm64"
        return "windows-32" if bits == 32 else "windows-64"
    if os_id == OS_MAC:
        return "macos-arm64" if arch == "arm64" else "macos-64"
    if os_id == OS_LINUX:
        return "linux-arm64" if arch == "arm64" else "linux-64"
    return "auto"


def bits_word(bits, locale="zh-CN"):
    if locale == "en":
        return "32-bit" if bits == 32 else "64-bit"
    if locale == "zh-TW":
        return "32 位元" if bits == 32 else "64 位元"
    return "32 位" if bits == 32 else "64 位"


def arch_note(arch, locale="zh-CN"):
    if arch != "arm64":
        return ""
    return " (ARM64)" if locale == "en" else "（ARM64）"


def default_target_sentence(det, locale="zh-CN"):
    """给用户看的一句默认值说明，例如：
    「你的电脑是 Windows 64 位 —— 没有特别说明时，就按这个来（Windows 64 位）。」
    """
    det = det or detect_platform()
    target = platform_to_target(det)
    label = describe_target(target, locale)
    os_label = det["os_label"]
    bw = bits_word(det["bits"], locale)
    an = arch_note(det["arch"], locale)

    if locale == "en":
        return (
            "Your machine is %s %s%s — unless stated otherwise, build for this (%s)."
            % (os_label, bw, an, label)
        )
    if locale == "zh-TW":
        return "你的電腦是 %s %s%s —— 沒有特別說明時，就照這個來（%s）。" % (os_label, bw, an, label)
    return "你的电脑是 %s %s%s —— 没有特别说明时，就按这个来（%s）。" % (os_label, bw, an, label)


# 按平台族给兼容性提醒。
#
# ★ 为什么要按目标分：早先写死成「你的电脑是 Windows 64 位 …」，
#   选了安卓之后还在讲 Windows 的 32/64 位 —— 对手机用户完全是错的。
# 键：desktop（桌面，讲位数兼容）/ android / android32 / ios / harmony / web
COMPAT_NOTES = {
    "desktop": {
        "zh-CN": "提醒：32 位程序在 32/64 位系统上都能跑，但 64 位程序在 32 位系统上跑不起来。",
        "zh-TW": "提醒：32 位元的程式在 32／64 位元系統上都能跑，但 64 位元的程式在 32 位元系統上跑不起來。",
        "en": "Note: a 32-bit build runs on both 32- and 64-bit systems, but a 64-bit "
              "build will NOT run on 32-bit systems.",
    },
    "android": {
        "zh-CN": "提醒：安卓 App 给的是 .apk 安装包，装之前手机会提示「允许安装未知来源应用」，"
                 "需要使用者手动同意。",
        "zh-TW": "提醒：安卓 App 給的是 .apk 安裝檔，裝之前手機會提示「允許安裝未知來源應用程式」，"
                 "需要使用者手動同意。",
        "en": "Note: an Android app is delivered as an .apk. The phone warns about installing "
              "from an unknown source, and the user must allow it manually.",
    },
    "android32": {
        "zh-CN": "提醒：安卓 32 位只能装在老手机上；现在的手机也能跑 32 位包，"
                 "但新应用商店多已不收 32 位包。不确定就选 ARM64。",
        "zh-TW": "提醒：安卓 32 位元只能裝在舊手機上；現在的手機也能跑 32 位元包，"
                 "但新的應用程式商店多已不收 32 位元包。不確定就選 ARM64。",
        "en": "Note: 32-bit Android only suits older phones. Current phones can run 32-bit "
              "packages, but most new app stores no longer accept them. When unsure, choose ARM64.",
    },
    "ios": {
        "zh-CN": "提醒：iPhone 装 App 必须有苹果开发者账号（一年 99 美元）；"
                 "否则只能做成网页版加到主屏幕。",
        "zh-TW": "提醒：iPhone 裝 App 必須有蘋果開發者帳號（一年 99 美元）；"
                 "否則只能做成網頁版加到主畫面。",
        "en": "Note: installing an app on an iPhone requires a paid Apple Developer account "
              "(99 USD/year); otherwise the web version added to the home screen is the only option.",
    },
    "harmony": {
        "zh-CN": "提醒：鸿蒙 App 要在使用者手机上开启开发者模式才能装，"
                 "对不熟手机的人可能有点麻烦。",
        "zh-TW": "提醒：鴻蒙 App 要在使用者手機上開啟開發者模式才能裝，"
                 "對不熟手機的人可能有點麻煩。",
        "en": "Note: a HarmonyOS app needs developer mode enabled on the phone before it can be "
              "installed, which can be fiddly for non-technical users.",
    },
    "web": {
        "zh-CN": "提醒：网页版不需要安装，电脑和手机浏览器都能打开；"
                 "但如果要放在网上给别人访问，需要服务器和域名（要花钱）。",
        "zh-TW": "提醒：網頁版不需要安裝，電腦和手機瀏覽器都能開啟；"
                 "但如果要放在網路上給別人存取，需要伺服器和網域（要花錢）。",
        "en": "Note: a web version needs no installation and opens in any desktop or phone "
              "browser; but hosting it for others requires a server and domain (which costs money).",
    },
}


def compat_family(target):
    """目标值 → 用哪一条兼容性提醒"""
    if target is None:
        target = platform_to_target(detect_platform())
    s = str(target)
    if s.startswith("android"):
        return "android32" if s.endswith("-32") else "android"
    if s in ("ios", "harmony", "web"):
        return s
    return "desktop"


def compat_note(locale="zh-CN", target=None):
    """按**所选目标**给兼容性提醒。

    ★ 必须按目标分：早先写死成「你的电脑是 Windows 64 位 …」，
      选了安卓之后还在讲 Windows 的 32/64 位 —— 对手机用户完全是错的。

    只传 locale 时（兼容旧调用）按本机目标判断。
    """
    fam = compat_family(target)
    entry = COMPAT_NOTES.get(fam) or COMPAT_NOTES["desktop"]
    return entry.get(locale) or entry["zh-CN"]


def build_target_block(det=None, locale="zh-CN"):
    """给需求说明用的一整段「目标系统与位数」。"""
    det = det or detect_platform()
    target = platform_to_target(det)
    lines = [default_target_sentence(det, locale)]
    if det["bits"] != 32:
        lines.append(compat_note(locale))
    lines.append("目标平台：" + describe_target(target, locale))
    lines.append("（探测依据：%s）" % det["detail"])
    return "\n".join(lines)


if __name__ == "__main__":
    import json

    d = detect_platform()
    print(json.dumps(d, ensure_ascii=False, indent=2))
    print()
    for loc in ("zh-CN", "zh-TW", "en"):
        print("[%s] %s" % (loc, default_target_sentence(d, loc)))
    print()
    print("默认目标:", platform_to_target(d), "=", describe_target(platform_to_target(d)))
    print()
    print(build_target_block(d))
