# -*- coding: utf-8 -*-
"""守住「工具自己可靠」这条线。

起因：check_i18n.py 曾在**任何覆盖率下**都跑不完 ——
它 print 的 [OK]/[X] 在 Windows 的 GBK 控制台上编码不了，直接崩 exit 1。
验证工具自己不可靠最要命：看起来像"检查失败"，实际是工具挂了。

这个测试盯两件事：
  1. check_i18n.py 在**默认编码**下也能跑完（不靠 PYTHONUTF8 之类的外挂）
  2. 它的检查口径要含「运行时才查表的键」（页名、问卷字段），
     否则会给出虚假的 100% —— 导航页名就是这么漏掉的

用法: python tools/selftest_tooling.py
"""
import os
import subprocess
import sys

def _force_utf8_output():
    """让中文输出在 Windows 默认（GBK）控制台上也不乱码、不崩。

    不加这个的话，print 中文会变成乱码甚至 UnicodeEncodeError，
    而这类检查工具的用途就是给人看结论 —— 结论读不了等于没做。
    重定向到文件时同样是 UTF-8，输出一致。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001  老 Python 没有 reconfigure
            pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

pass_n = fail_n = 0


def check(name, fn):
    global pass_n, fail_n
    try:
        fn()
        pass_n += 1
        print("  OK   %s" % name)
    except AssertionError as e:
        fail_n += 1
        print("  FAIL %s\n       %s" % (name, e))
    except Exception as e:  # noqa: BLE001
        fail_n += 1
        print("  FAIL %s\n       %r" % (name, e))


print("=" * 62)
print("工具自身可靠性")
print("=" * 62)


def t_runs_on_default_encoding():
    """★ 关键：清掉所有 UTF-8 外挂，用系统默认编码跑"""
    env = dict(os.environ)
    for k in ("PYTHONIOENCODING", "PYTHONUTF8"):
        env.pop(k, None)
    r = subprocess.run(
        [sys.executable, os.path.join(HERE, "check_i18n.py")],
        cwd=ROOT, env=env, capture_output=True)
    out = (r.stdout or b"").decode("utf-8", "replace") + \
          (r.stderr or b"").decode("utf-8", "replace")
    assert r.returncode == 0, \
        "check_i18n.py 在默认编码下退出码 %d\n%s" % (r.returncode, out[-600:])
    assert "UnicodeEncodeError" not in out, "出现编码错误:\n" + out[-400:]
    assert "无回退项" in out, "没跑到结论行:\n" + out[-400:]


check("check_i18n.py 在默认控制台编码下能跑完", t_runs_on_default_encoding)


def t_checks_runtime_keys():
    """★ 口径必须含运行时键，否则会漏掉导航页名这类"""
    import check_i18n as c

    statics, _ = c.t_call_args(os.path.join(ROOT, "src", "app.py"))
    rt, _ = c.runtime_keys(os.path.join(ROOT, "src"))
    assert rt, "应该能取到运行时键（页名/问卷字段等）"
    # 页名必须在里面
    assert "先查查" in rt, "页名没被纳入检查口径: %s" % rt[:8]
    assert "填写需求" in rt, "页名没被纳入检查口径"


check("检查口径包含运行时才查表的键（页名等）", t_checks_runtime_keys)


def t_exempts_platform_labels():
    """平台标签由 platform_info 自己本地化，不该算成漏翻（否则天天假警报）"""
    import check_i18n as c

    rt, _ = c.runtime_keys(os.path.join(ROOT, "src"))
    for label in ("Windows 32 位", "Linux ARM64", "macOS Intel（x64）"):
        assert label not in rt, "平台标签 %r 不该进检查清单" % label


check("平台标签被正确豁免（不产生假警报）", t_exempts_platform_labels)


def t_other_tools_run():
    """其余检查工具也要能在默认编码下跑完"""
    env = dict(os.environ)
    for k in ("PYTHONIOENCODING", "PYTHONUTF8"):
        env.pop(k, None)
    for tool, want in (("check_encoding.py", "检查"),
                       ("check_option_uniqueness.py", "唯一性")):
        r = subprocess.run([sys.executable, os.path.join(HERE, tool)],
                           cwd=ROOT, env=env, capture_output=True)
        out = (r.stdout or b"").decode("utf-8", "replace")
        assert want in out, "%s 没正常输出: %s" % (tool, out[-300:])
        assert "UnicodeEncodeError" not in out, "%s 有编码错误" % tool


check("其它检查工具在默认编码下也能跑", t_other_tools_run)

print()
print("=" * 62)
print("通过 %d 项，失败 %d 项" % (pass_n, fail_n))
print("=== 全部通过 ===" if fail_n == 0 else "=== 有失败项 ===")
sys.exit(0 if fail_n == 0 else 1)
