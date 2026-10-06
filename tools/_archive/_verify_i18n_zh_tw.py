# -*- coding: utf-8 -*-
"""驗證 src/i18n_zh_tw.py：語法、編碼、鍵一致性、佔位符、繁體用字。"""
import ast
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
PACK = os.path.join(SRC, "i18n_zh_tw.py")

raw = io.open(PACK, "rb").read()
print("1) 檔案大小: %d bytes" % len(raw))
print("   無 BOM: %s" % (not raw.startswith(b"\xef\xbb\xbf")))
print("   UTF-8 可解碼: %s" % bool(raw.decode("utf-8")))

text = raw.decode("utf-8")
tree = ast.parse(text)
print("2) ast.parse 語法通過: True")

ns = {}
exec(compile(tree, PACK, "exec"), ns)
CAT = ns["CATALOG"]
print("3) CATALOG 載入成功，%d 條" % len(CAT))
print("   全部鍵值皆為 str: %s" % all(isinstance(k, str) and isinstance(v, str)
                                      for k, v in CAT.items()))
print("   無重複鍵（dict 長度 == 鍵數）: %s" % (len(CAT) == len(set(CAT))))

# 鍵必須是 app.py 裡的原文
sys.path.insert(0, SRC)
import app  # noqa: E402

strings = set()
src = io.open(os.path.join(SRC, "app.py"), encoding="utf-8").read()
t = ast.parse(src)
docs = set()
for node in ast.walk(t):
    if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        b = getattr(node, "body", None)
        if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                and isinstance(b[0].value.value, str):
            docs.add(id(b[0].value))
for node in ast.walk(t):
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
        strings.add(node.value)

bad = [k for k in CAT if k not in strings and not any(k in s for s in strings)]
print("4) 鍵在 app.py 中逐字存在: %s （不符 %d 條）" % (not bad, len(bad)))
for k in bad:
    print("   BAD: %r" % k)

# 佔位符一致（%s/%d/%.2f/%% 與 {n}）
ph = re.compile(r"%[-#0-9.]*[sdrf]|%%|\{[a-zA-Z_][a-zA-Z0-9_]*\}")
ph_bad = []
for k, v in CAT.items():
    if sorted(ph.findall(k)) != sorted(ph.findall(v)):
        ph_bad.append((k, v, ph.findall(k), ph.findall(v)))
print("5) 格式化佔位符一致: %s （不符 %d 條）" % (not ph_bad, len(ph_bad)))
for k, v, a, b in ph_bad:
    print("   PH: %r\n       key=%s val=%s" % (k, a, b))

# 換行結構一致
nl_bad = [(k, v) for k, v in CAT.items() if k.count("\n") != v.count("\n")]
print("6) 換行數一致: %s （不符 %d 條）" % (not nl_bad, len(nl_bad)))
for k, v in nl_bad:
    print("   NL: %r -> %r" % (k[:40], v[:40]))

# 簡體殘留檢查（常見簡體字／詞）
SIMP_CHARS = "软件信息文件夹视程序默认录保存粘贴复制打印屏幕网络数据支持通过质这么点线长门开车东"
SIMP_WORDS = ["软件", "信息", "文件", "文件夹", "视频", "程序", "默认", "登录", "保存",
              "粘贴", "复制", "打印", "屏幕", "网络", "数据", "支持", "通过", "质量",
              "简体", "语言", "设置", "文档", "图标", "统计", "计算", "标题", "内容",
              "预览", "删除", "确认", "载入", "存档", "刷新", "关闭", "选择", "这个",
              "什么", "为什", "怎么", "这样", "地址", "推荐", "档位", "字号", "窗口",
              "字体", "主题", "诊断", "重开", "开始"]
susp = []
for k, v in CAT.items():
    hits = [w for w in SIMP_WORDS if w in v]
    if hits:
        susp.append((hits, v))
print("7) 譯文疑似簡體詞殘留: %d 條" % len(susp))
for hits, v in susp[:40]:
    print("   %s :: %s" % (hits, v[:70]))

# 全形標點/emoji 保留
EMO = ["✅", "❌", "⭐", "⚠️", "⚠", "✔", "📋", "💾", "🧹", "🔄", "📂", "🗑", "↩",
       "🔍", "🩺", "🌐", "✕", "◐", "◈", "→", "·", "「", "」", "（", "）", "；", "："]
emo_bad = []
for k, v in CAT.items():
    for e in EMO:
        if k.count(e) != v.count(e):
            emo_bad.append((e, k[:40], v[:40]))
print("8) 標點/emoji 數量一致: %s （不符 %d 條）" % (not emo_bad, len(emo_bad)))
for e, k, v in emo_bad[:20]:
    print("   %r :: %r -> %r" % (e, k, v))

# 執行期：t() 真的能取到譯文
import i18n  # noqa: E402
i18n.set_lang("zh-TW")
i18n.reload_packs()
ok = i18n.t("复制需求")
print("9) i18n.t('📋 复制需求') -> %r" % i18n.t("📋 复制需求"))
i18n.set_lang("zh-CN")
print("   zh-CN t('📋 复制需求') -> %r" % i18n.t("📋 复制需求"))
i18n.set_lang("zh-TW")
print("   格式化 t('已填 {n}/{m} 格'): %r" % i18n.t("已填 {n}/{m} 格", n=1, m=2)
      if "已填 {n}/{m} 格" in CAT else "   （無此鍵，略：app.py 是 f-string，由片段拼出）")
_rendered = i18n.t("🌐  界面语言（%s）") % "繁體中文"
print("   格式化 t('🌐  界面语言（%s）') 套用 '繁體中文': " + repr(_rendered))

# 覆蓋率（QUESTIONS / 關鍵區塊）
missing = [s for s in strings
           if re.search(r"[\u4e00-\u9fff]", s) and s not in CAT
           and not any(s in k for k in CAT)
           and s not in {"需求存档", "使用说明.txt", "提示词模板.txt", "显示诊断.txt",
                         "===== 原始答案（给程序自己看，不用管） =====",
                         "===== 原始答案结束 =====", "小白造软件助手"}]
print("10) app.py 使用者可見中文未覆蓋: %d 條" % len(missing))
for m in missing:
    print("    MISSING: %r" % m)

# 每個 QUESTION 的 title/hint/help/example/options 是否都有譯文
# （system 那題是動態拼出來的，見下方 12 的執行期檢查）
DYN_PREFIX = ("跟我电脑一样：", "例如：", "为什么要问？", "请把它做成")
qbad = []
for q in app.QUESTIONS:
    for field in ("title", "hint", "help", "example"):
        v = q.get(field)
        if not isinstance(v, str) or not re.search(r"[\u4e00-\u9fff]", v):
            continue
        if q["key"] == "system" and (v.startswith(DYN_PREFIX) or v in CAT
                                     or any(v.startswith(p) for p in DYN_PREFIX)):
            continue
        if v not in CAT:
            qbad.append((q["key"], field, v[:40]))
    for o in (q.get("options") or []):
        if q["key"] == "system":
            continue
        if o not in CAT:
            qbad.append((q["key"], "option", o[:40]))
print("11) QUESTIONS 非動態欄位全覆蓋: %s （缺 %d）" % (not qbad, len(qbad)))
for x in qbad[:20]:
    print("    ", x)

print()
q_texts = []
for q in app.QUESTIONS:
    for f in ("title", "hint", "help", "example"):
        if isinstance(q.get(f), str):
            q_texts.append(q[f])
    q_texts.extend(q.get("options") or [])
trans = i18n.translate_catalog(q_texts, "zh-TW")
han = re.compile(r"[\u4e00-\u9fff]")
print("QUESTIONS 相關字串 %d 條，繁體譯文中文字數 %d"
      % (len(set(q_texts)), sum(len(han.findall(v)) for v in trans.values())))
print("QUESTIONS 譯文與原文不同的比例：%d / %d"
      % (sum(1 for k, v in trans.items() if k != v), len(trans)))
