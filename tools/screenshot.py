# -*- coding: utf-8 -*-
"""启动程序并把它自己的窗口截图存成 PNG —— 用来核对配色和布局。

之前改 UI 全靠"应该对"，看不到结果。这个脚本让改样式变成可验证的事。

用法: python _截图.py dark 截图_暗色.png
"""
import ctypes
import ctypes.wintypes      # 必须显式导入：ctypes.wintypes 不会随 ctypes 自动可用
import os
import subprocess
import sys
import time

from PIL import ImageGrab

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
ROOT = os.path.dirname(SRC)
APP = os.path.join(SRC, "app.py")
PY = sys.executable
u = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32      # PrintWindow 方案要用来建位图
u.SetProcessDPIAware()

theme = sys.argv[1] if len(sys.argv) > 1 else "dark"
out = sys.argv[2] if len(sys.argv) > 2 else "assets/screenshot-%s.png" % theme
# 输出路径按【仓库根目录】解析，这样 `assets/xxx.png` 写在哪儿都对
out = out if os.path.isabs(out) else os.path.join(ROOT, out)
os.makedirs(os.path.dirname(out), exist_ok=True)

env = dict(os.environ)
env["XBSH_THEME"] = theme
# 用独立的配置文件：不动用户真实 config.json，
# 也避免多个语言并行截图时互相覆盖语言设置（实测踩到过）。
env["XBSH_CONFIG"] = os.path.join(ROOT, ".screenshot-config.json")

# 语言可以用环境变量指定：python screenshot.py dark out.png zh-TW
if len(sys.argv) > 3:
    env["XBSH_LANG"] = sys.argv[3]
# 打开哪一页（0=填写需求 1=先查查 2=历史记录 3=使用说明）
# 用环境变量传，app.py 启动后自行切换 —— 截图脚本不必去点界面。
if len(sys.argv) > 4:
    env["XBSH_PAGE"] = str(sys.argv[4])
env["PYTHONIOENCODING"] = "utf-8"
cfg = os.path.join(SRC, "config.json")
if os.path.exists(cfg):
    os.remove(cfg)

proc = subprocess.Popen([PY, "-X", "utf8", APP], env=env)

# 等窗口出现。
#
# ⚠️ 不能用「标题包含某个固定的中文串」来找窗口 —— 界面语言切换后标题也变了
#    （英文是 "Little White's Software Helper"、繁体是「小白造軟體助手」），
#    匹配不上就会退化成 "found[0]"，抓到**别的程序的窗口**（实测抓到过
#    一个游戏修改器），截出来的图完全不对。
#    这里改成两条判据都用：标题多语言匹配 + 属于我们启动的那个进程。
TITLE_HINTS = ("小白造", "Little White", "Software Helper")


def is_ours(h):
    # 必须属于我们刚启动的那个进程，避免抓到同名/邻近的其它窗口
    pid = ctypes.wintypes.DWORD()
    u.GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value != proc.pid:
        return False
    n = u.GetWindowTextLengthW(h)
    if not n:
        return False
    buf = ctypes.create_unicode_buffer(n + 1)
    u.GetWindowTextW(h, buf, n + 1)
    return any(hint in buf.value for hint in TITLE_HINTS)


hwnd = 0
for _ in range(80):
    time.sleep(0.5)
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(h, _l):
        if u.IsWindowVisible(h) and is_ours(h):
            found.append(h)
        return True

    u.EnumWindows(cb, None)
    if found:
        hwnd = found[0]
        break

if not hwnd:
    proc.terminate()
    print("没找到窗口（进程 %s，语言 %s）" % (proc.pid, env.get("XBSH_LANG", "(默认)")))
    print("提示：标题应含 %s，请检查界面语言是否导致标题变化" % (TITLE_HINTS,))
    sys.exit(1)

def grab_window_direct(hwnd):
    """用 PrintWindow 把指定窗口的内容画到位图上。

    为什么需要它：前台锁会让 SetForegroundWindow 静默失败，
    窗口被别的程序压住时，截屏区域取到的是别人的画面。
    PrintWindow 直接向窗口要一份绘制，与前后台顺序无关，
    因此是抓指定窗口的正确方式。

    PW_RENDERFULLCONTENT (2) 是新加的标志，没有它某些控件（含部分 Tk 绘制）
    会画出空白，所以要带上；老系统不支持时退回 0。
    """
    import ctypes.wintypes as wt
    from PIL import Image

    r = wt.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    if w <= 0 or h <= 0:
        return None

    hdc_win = u.GetWindowDC(hwnd)
    if not hdc_win:
        return None
    hdc_mem = gdi32.CreateCompatibleDC(hdc_win)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_win, w, h)
    if not (hdc_mem and hbmp):
        u.ReleaseDC(hwnd, hdc_win)
        return None
    old = gdi32.SelectObject(hdc_mem, hbmp)

    ok = False
    for flag in (2, 0):          # PW_RENDERFULLCONTENT, 退回 0
        if u.PrintWindow(hwnd, hdc_mem, flag):
            ok = True
            break
    if not ok:
        gdi32.SelectObject(hdc_mem, old)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        u.ReleaseDC(hwnd, hdc_win)
        return None

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                    ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                    ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                    ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
                    ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h              # 负值 = 自上而下，省得再翻转
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0          # BI_RGB

    buf = ctypes.create_string_buffer(w * h * 4)
    got = gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, ctypes.byref(bmi), 0)

    gdi32.SelectObject(hdc_mem, old)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    u.ReleaseDC(hwnd, hdc_win)

    if not got:
        return None
    # BGRA -> RGB
    return Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")


print("窗口句柄:", hwnd)
u.ShowWindow(hwnd, 5)

# 让它浮到最前。
#
# ⚠️ 只调 SetForegroundWindow 不够：Windows 有"前台锁"，当调用方不是前台进程时
#    这次调用会被**静默拒绝**（不报错、返回 0），于是别的窗口压在我们上面，
#    截出来的图是别人的界面（实测截到过 DSH 自己的窗口）。
#    所以这里组合几种手法，并且**校验是否真的在最前**，不行就如实报错而不是
#    默默存一张错的图。
SWP_NOMOVE, SWP_NOSIZE, SWP_SHOWWINDOW = 0x0002, 0x0001, 0x0040
HWND_TOP, HWND_TOPMOST, HWND_NOTOPMOST = 0, -1, -2


def bring_to_front():
    u.SetForegroundWindow(hwnd)
    u.BringWindowToTop(hwnd)
    u.SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0,
                   SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
    # 短暂置顶再取消置顶，绕开前台锁且不留下"总在最前"的副作用
    u.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                   SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
    time.sleep(0.4)
    u.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                   SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)


def is_obscured():
    """检查窗口中心点是否被别的窗口遮住（遮住就不是我们在最前）。"""
    import ctypes.wintypes as wt

    r = wt.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    cx, cy = (r.left + r.right) // 2, (r.top + r.bottom) // 2
    pt = wt.POINT(cx, cy)
    top = u.WindowFromPoint(pt)
    if not top:
        return True, 0
    # 逐级取父窗口，因为 WindowFromPoint 可能返回子控件
    root = top
    for _ in range(8):
        parent = u.GetAncestor(root, 2)   # GA_ROOT
        if not parent or parent == root:
            break
        root = parent
    return root != hwnd, root


top_ok = False
for attempt in range(5):
    bring_to_front()
    time.sleep(0.8)
    obscured, other = is_obscured()
    if not obscured:
        top_ok = True
        break
    print("第 %d 次尝试仍被遮挡（覆盖窗口句柄 %s）" % (attempt + 1, other))

if not top_ok:
    # 前台锁拒绝置顶时，不要放弃 —— 改用 PrintWindow 直接把窗口内容画到位图上。
    # 这个 API 不需要窗口在最前，也不会被别的窗口盖住，
    # 是"抓某个指定窗口"的正确做法（比截屏区域可靠）。
    print("窗口被遮挡，改用 PrintWindow 直接抓窗口内容")
    img = grab_window_direct(hwnd)
    if img is None:
        proc.terminate()
        print("✘ PrintWindow 也失败，无法截图。")
        sys.exit(2)
    img.save(out)
    print("已保存(PrintWindow):", out, img.size)
    proc.terminate()
    sys.exit(0)

time.sleep(0.6)

rect = ctypes.wintypes.RECT() if hasattr(ctypes, "wintypes") else None
import ctypes.wintypes as wt
rect = wt.RECT()
u.GetWindowRect(hwnd, ctypes.byref(rect))
w, h = rect.right - rect.left, rect.bottom - rect.top
print("窗口矩形: %d,%d %dx%d" % (rect.left, rect.top, w, h))

img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
img.save(out)
print("已保存:", out, img.size)

proc.terminate()
try:
    proc.wait(timeout=5)
except subprocess.TimeoutExpired:
    proc.kill()
