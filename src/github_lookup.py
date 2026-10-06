# -*- coding: utf-8 -*-
"""先查查：在动手做之前，先看 GitHub 上有没有现成的软件/插件。

**设计原则（重要）**

1. **只在你主动点击时才联网**。程序启动、填问卷、生成需求说明的过程
   一律不碰网络。这样「填需求的内容不会自动上传」这一点仍然成立。
2. **只读搜索，不登录、不上传你的内容**。
   查询词只用你选的那几个关键词（你可以在页面上改），
   不把你写的需求正文发出去。
3. **离线也能用**：连不上网时不是报错了事，而是给出一段可以直接
   粘给 AI 的「查重指令」，让 AI 帮你查。

为什么值得做：很多需求 GitHub 上已经有成熟方案（尤其是通用工具类），
先看一眼能省掉大量重复劳动；而且如果已有项目能用，
「拿来改」通常比自己从零做更可靠。
"""
import json
import urllib.error
import urllib.parse
import urllib.request

GITHUB_SEARCH = "https://api.github.com/search/repositories"


# ---------------------------------------------------------------------------
# 界面文案的翻译钩子
# ---------------------------------------------------------------------------
# 为什么用「可注入的翻译器」而不是直接 import i18n：
#   这个模块是**纯逻辑模块**，要能在没有界面的情况下单独 import 和测试
#   （selftest_lookup.py 就是这么用的）。硬 import i18n 会让它带上一串依赖。
#   app.py 启动时调 set_translator(i18n.t) 接上真实翻译；
#   没接上时原样返回原文 —— 漏翻只会显示中文，不会崩。
_TRANSLATOR = None


def set_translator(fn):
    """由宿主接上翻译函数（签名 t(text) -> str）。传 None 恢复原样。"""
    global _TRANSLATOR
    _TRANSLATOR = fn


def _(text, **fmt):
    """取译文。没接翻译器时返回原文。"""
    out = text
    if _TRANSLATOR is not None:
        try:
            out = _TRANSLATOR(text)
        except Exception:  # noqa: BLE001  翻译出问题不能影响功能
            out = text
    if fmt:
        try:
            out = out.format(**fmt)
        except (KeyError, IndexError, ValueError):
            pass
    return out

# 判定「现成方案足够好」的门槛。这些数字是经验值，不是硬标准，
# 页面上会显示理由，让用户自己判断。
GOOD_STARS = 200
OK_STARS = 30
RECENT_DAYS = 540          # 约 1.5 年内有更新，视为还在维护


def _clean(text):
    """把一段用户描述压成关键词。

    ⚠️ 中文没有空格，**不能简单按空格切分** —— 那样会把
    「一个把每天三份销售 Excel 自动合并汇总的小工具」整句当成一个词，
    拿去搜什么也搜不到（实测就是这个结果）。
    这里改成：先剥掉句子里的虚词/量词，再按这些虚词的位置切出名词块。
    """
    if not text:
        return []
    s = str(text)
    for ch in "，。、；：！？（）【】「」《》,.;:!?()[]<>\"'`~!@#$%^&*+=|\\/—…\n\t":
        s = s.replace(ch, " ")

    # 这些词在句子里只是连接/语气，本身没有检索价值
    STOP = [
        "帮我", "我想", "我要", "想要", "我需要", "可以做", "能不能", "有没有",
        "一个", "一份", "一张", "一套", "把", "的", "和", "与", "跟",
        "用来", "用了", "然后", "就是", "这个", "那个", "什么", "怎么", "可以",
        "简单", "方便", "自动", "小工具", "软件", "程序", "工具", "东西",
    ]
    for w in STOP:
        s = s.replace(w, " ")

    out = []
    seen = set()
    for w in s.split():
        w = w.strip("-—_·")
        if len(w) < 2:
            continue
        # 纯中文的长块通常是句子的一部分，按 6 字切开更利于检索
        if len(w) > 8 and all("\u4e00" <= c <= "\u9fff" for c in w):
            for i in range(0, len(w), 6):
                piece = w[i:i + 6]
                if len(piece) >= 2 and piece not in seen:
                    seen.add(piece)
                    out.append(piece)
            continue
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def _relevance_score(repo, terms):
    """判断一个仓库跟关键词有多相关（0~1）。

    用途：GitHub 按星数排序时，**高星的无关项目会排在最前**
    ——实测搜 "excel merge tool" 的第一名是个政治话题仓库（3250 星），
    只看星数就会给出「建议用现成的」这种完全错误的结论。
    所以必须先把不相关的排掉。
    """
    if not terms:
        return 0.0
    hay = ((repo.get("full_name") or "") + " " +
           (repo.get("description") or "")).lower()
    used = [str(t).strip().lower() for t in terms if len(str(t).strip()) >= 2]
    if not used:
        return 0.0
    hits = sum(1 for t in used if t in hay)
    return hits / len(used)


def rank_repos(repos, terms, min_score=0.34):
    """按「相关性优先、其次星数」排序，并丢掉完全不相关的。

    返回 (保留的列表, 被丢掉的个数)。
    """
    # 没给关键词就没有判断依据，原样返回。
    # 否则 _relevance_score 一律返回 0，会被当成「全都不相关」而全部丢掉。
    if not terms:
        return list(repos), 0

    scored = []
    dropped = 0
    for r in repos:
        sc = _relevance_score(r, terms)
        if sc < min_score:
            dropped += 1
            continue
        scored.append((sc, r))
    scored.sort(key=lambda x: (-x[0], -int(x[1].get("stars") or 0)))
    return [r for _, r in scored], dropped


def build_queries(answers):
    """按问卷答案生成查询词（返回列表，不重复）。

    取的是「做什么」+「输入输出」+「痛点」里最有信息量的词。
    每一条都会在页面上显示出来，用户可编辑后再查 —— 不偷偷用别的内容。

    ⚠️ 不要把这些词直接拿去搜 GitHub —— 中文关键词在 GitHub 上命中率很低。
    真正查询时用 to_search_query() 转成英文词再搜。
    """
    keys = ("what", "input", "output", "pain")
    seen = set()
    out = []
    for k in keys:
        v = (answers.get(k) or "").strip()
        if not v:
            continue
        # 只取第一行、前 60 字，避免把整段需求当查询词
        head = v.splitlines()[0][:60]
        for w in _clean(head):
            if w not in seen:
                seen.add(w)
                out.append(w)
    # 组合一条更具体的（多条词一起搜，命中更准）
    if len(out) >= 2:
        out.insert(0, " ".join(out[:3]))
    return out[:6]


# 中文 → 英文检索词的小词典。
# 为什么需要：GitHub 上绝大多数项目用英文描述，直接拿中文词去搜
# 命中率很低（实测「一个把每天三份销售 Excel 自动合并汇总的小工具」
# 查回来 0 个）。这里把常见需求词映射成英文说法，多条备选一起搜。
_EN_HINTS = [
    (("excel", "表格", "报表", "汇总", "合并"), ["excel merge", "spreadsheet merge"]),
    (("对账", "核对", "比对"), ["reconcile", "reconciliation", "compare spreadsheet"]),
    (("记账", "花销", "开销", "支出"), ["expense tracker", "personal finance"]),
    (("库存", "出入库", "进销存"), ["inventory management", "stock control"]),
    (("排班", "值班", "轮班"), ["shift scheduler", "roster", "scheduling"]),
    (("工资", "薪资", "加班", "考勤"), ["payroll", "attendance", "overtime"]),
    (("报价", "成本", "预算", "装修"), ["cost estimator", "quotation", "budget"]),
    (("文件", "批量改名", "整理", "归档"), ["file organizer", "batch rename"]),
    (("pdf", "word", "文档", "转换", "生成文档"), ["pdf convert", "docx generate", "document automation"]),
    (("提醒", "定时", "待办", "任务"), ["reminder", "todo", "scheduler"]),
    (("客户", "crm", "联系人"), ["crm", "contact management"]),
    (("图表", "统计", "可视化", "报表图"), ["chart", "visualization", "report"]),
    (("爬虫", "抓取", "采集"), ["scraper", "crawler"]),
    (("聊天", "机器人", "bot"), ["chatbot", "bot"]),
]


def to_search_query(text):
    """把人话需求转成**适合在 GitHub 上搜的英文查询串**。

    找不到映射时退回原词（至少不会更差），并如实告诉调用方命中了哪条。
    返回 (query, 命中的中文词列表)。
    """
    low = str(text or "").lower()
    hits = []
    en_terms = []
    for needles, equivalents in _EN_HINTS:
        if any(n in low for n in needles):
            hits.extend([n for n in needles if n in low])
            en_terms.extend(equivalents)
    if not en_terms:
        return str(text or "").strip(), []
    # 只取前 2 组，避免 OR 太散导致结果不相关；
    # 并且按「词」去重 —— 否则会出现 "excel merge spreadsheet merge"
    # 这种同词重复的查询串（实测踩到过），浪费额度也让结果更散。
    seen_words = set()
    picked = []
    for term in en_terms:
        parts = [w for w in term.split() if w not in seen_words]
        if not parts:
            continue
        for w in parts:
            seen_words.add(w)
        picked.append(" ".join(parts))
        if len(picked) >= 3:
            break
    return " ".join(picked), hits


def search_repos(query, per_page=8, timeout=12, opener=None):
    """调 GitHub 搜索接口。

    返回 (repos, error)：
      repos  列表，每项是精简后的 dict；出错时为空列表
      error  None 或一句人话说明
    """
    if not query or not str(query).strip():
        return [], _("查询词是空的")

    params = urllib.parse.urlencode({
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max(1, min(30, int(per_page))),
    })
    url = GITHUB_SEARCH + "?" + params
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "xiaobai-software-helper",
    })
    op = opener or urllib.request.urlopen
    try:
        with op(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return [], _("GitHub 限制了查询频率（每小时 10 次左右），请过一会儿再试")
        if e.code == 422:
            return [], _("查询词 GitHub 不接受，换个更简单的说法再试")
        return [], _("GitHub 返回错误 %s") % e.code
    except urllib.error.URLError as e:
        return [], _("连不上 GitHub（%s）。可以先用下面的「让 AI 帮你查」") % (e.reason,)
    except Exception as e:  # noqa: BLE001  任何异常都不该让界面崩
        return [], _("查询失败：%r") % (e,)

    items = data.get("items") or []
    repos = []
    for it in items:
        repos.append({
            "full_name": it.get("full_name", ""),
            "url": it.get("html_url", ""),
            "description": (it.get("description") or "").strip(),
            "stars": int(it.get("stargazers_count") or 0),
            "language": it.get("language") or "",
            "license": ((it.get("license") or {}) or {}).get("spdx_id") or "",
            "updated": (it.get("pushed_at") or it.get("updated_at") or "")[:10],
            "archived": bool(it.get("archived")),
            "issues": int(it.get("open_issues_count") or 0),
        })
    return repos, None


def _days_since(date_str):
    """'2026-01-02' → 距今天数；解析不了返回 None"""
    if not date_str:
        return None
    try:
        import datetime

        d = datetime.date(*[int(x) for x in date_str.split("-")[:3]])
        return (datetime.date.today() - d).days
    except Exception:  # noqa: BLE001
        return None


def judge(repos, terms=None):
    """给出一句「该自己做还是用现成的」的判断，并附理由。

    判断只看客观信号（相关性、星数、是否归档、最近是否更新、有没有许可证），
    不猜项目质量 —— 那需要有人的判断。

    terms：查询用的关键词。传了就**先按相关性过滤**，
    否则高星的无关项目会让结论完全跑偏（实测踩到过）。
    """
    dropped = 0
    if terms:
        repos, dropped = rank_repos(repos, terms)

    reasons = []
    if dropped:
        reasons.append(_("（有 %d 个搜索结果与你的需求明显无关，已排除 —— "
                         "GitHub 按星数排时经常把无关的高星项目排在最前）") % dropped)

    if not repos:
        return {
            "verdict": "none",
            "headline": _("没找到现成的，可以自己做"),
            "reasons": reasons + ["GitHub 上没有搜到明显相关的项目。"],
            "dropped": dropped,
        }

    top = repos[0]
    # 用 .get 且兼容两种输入格式：
    #   · search_repos() 输出的精简格式：license 是字符串 "MIT"
    #   · GitHub 原始格式：license 是 {"spdx_id": "MIT"}
    # 早先直接写 top["license"].strip()，遇到原始格式就 AttributeError 崩掉 ——
    # 判重函数不该要求调用方一定先规整格式。
    stars = int(top.get("stars") or top.get("stargazers_count") or 0)
    updated = str(top.get("updated") or top.get("pushed_at") or top.get("updated_at") or "")
    archived = bool(top.get("archived"))
    raw_license = top.get("license")
    if isinstance(raw_license, dict):
        raw_license = raw_license.get("spdx_id") or ""
    license_ = str(raw_license or "").strip()
    days = _days_since(updated[:10])
    strong = 0

    top = {**top, "stars": stars, "updated": updated,
           "archived": archived, "license": license_}

    if stars >= GOOD_STARS:
        strong += 1
        reasons.append(_("最相关的项目有 %d 颗星，说明用的人不少") % stars)
    elif stars >= OK_STARS:
        reasons.append(_("最相关的项目有 %d 颗星，有一定使用量") % stars)
    else:
        reasons.append(_("星数都不高（最高 %d），可能没有成熟方案") % stars)

    if archived:
        reasons.append(_("⚠️ 但该项目已归档，作者不再维护"))
        strong -= 1
    elif days is not None and days > RECENT_DAYS:
        reasons.append(_("⚠️ 而且已 %d 个月没更新，要留意是否还适用") % (days // 30))
        strong -= 1
    elif days is not None:
        reasons.append(_("最近还有更新（%s），看来仍在维护") % updated)
        strong += 1

    if license_ in ("", "NOASSERTION", "NONE"):
        reasons.append(_("❓ 没写清楚开源许可证，商用前要确认"))
    else:
        reasons.append(_("许可证是 %s") % license_)

    if strong >= 2:
        verdict = "reuse"
        head = _("建议先用现成的，别从零做")
    elif strong >= 1:
        verdict = "compare"
        head = _("有可参考的项目，值得先看一眼再决定")
    else:
        verdict = "build"
        head = _("现成的都不太合适，自己做更省事")

    return {"verdict": verdict, "headline": head, "reasons": reasons, "top": top}


def build_ai_instruction(questions, answers=None):
    """离线回退：给一段可以直接粘给 AI 的「查重指令」。

    连不上网、或者想换个更强的搜索时用这段。
    """
    q = [x for x in (questions or []) if x.strip()]
    if not q:
        q = [_("（把你的需求填进上面几格，这里会自动生成查询词）")]
    lines = [
        _("在动手做之前，请先帮我查一下 GitHub 上有没有现成的软件或插件。"),
        "",
        _("请搜索这些关键词（可以自己扩展同义词、英文词）："),
    ]
    for i, item in enumerate(q, 1):
        lines.append("%d. %s" % (i, item))
    lines += [
        "",
        _("查完请按下面的格式回答，不要只丢链接："),
        _("1. 有没有现成的？如果有，列出最相关的 3~5 个，每个给出："),
        _("   项目名 / 链接 / 星数 / 最近更新时间 / 许可证 / 一句话说明它能不能满足我的需求"),
        _("2. 这些项目**能不能直接满足我的需求**？缺哪些部分？"),
        _("3. 给我一个明确建议：直接用现成的、拿现成的改、还是自己做？并说明理由。"),
        _("4. 如果用现成的，告诉我怎么装、怎么用（我不懂技术，请一步步说）。"),
        "",
        _("如果确实没有合适的，再动手做；不要因为搜索麻烦就跳过这一步。"),
    ]
    return "\n".join(lines)


def format_report(repos, verdict=None):
    """把结果渲染成可读文本（也便于存进存档）。"""
    if not repos:
        return _("没有找到相关项目。")
    lines = []
    if verdict:
        lines.append(_("【判断】") + verdict["headline"])
        for r in verdict.get("reasons", []):
            lines.append("  · " + r)
        lines.append("")
    lines.append(_("找到 %d 个相关项目（按星数排序）：") % len(repos))
    for i, r in enumerate(repos, 1):
        flags = []
        if r.get("archived"):
            flags.append("已归档")
        if (r.get("license") or "") in ("", "NOASSERTION", "NONE"):
            flags.append("许可证不明")
        tail = "（" + "、".join(flags) + "）" if flags else ""
        lines.append("")
        lines.append("%d. %s  ⭐%d  %s%s" % (i, r.get("full_name", ""), int(r.get("stars") or 0),
                                            r.get("language") or "", tail))
        lines.append("   %s" % r.get("url", ""))
        if r.get("description"):
            lines.append("   %s" % r["description"][:200])
        lines.append("   最近更新：%s   许可证：%s" % (r.get("updated") or "未知",
                                                     r.get("license") or "未标注"))
    return "\n".join(lines)
