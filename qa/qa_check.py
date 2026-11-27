#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qa_check.py — CSCV 推广物料（纯文本 CN-EN）v2 最终交付物自动检查

用法：
    python3 qa/qa_check.py deliverables/CSCV_推广物料_纯文本_CN-EN_v2.md

约定（与 WORKBRIEF.md / 共享任务 task-4 一致）：
  - 中文字符数 = 去掉空白字符后的字符总数
  - 英文字符数 = 含空格的字符总数（LinkedIn 口径；换行处理见下方容差说明）
  - 输出逐项 PASS / FAIL / WARN（WARN=建议项，不影响退出码）
  - 全部检查无 FAIL 时退出码 0，否则 1；参数/文件错误退出码 2

纯标准库，无第三方依赖。
"""

import re
import sys
import difflib
from pathlib import Path

# ---------------------------------------------------------------------------
# 事实表（冻结口径，来自 WORKBRIEF.md §1 与 source/svc.txt）
# ---------------------------------------------------------------------------
CANON = {
    "brand": "JAZZFRONT Consulting™",
    "entity_cn": "广州玄墨商业咨询有限公司",
    "entity_en": "Guangzhou Xuanmo Business Consulting Co., Ltd.",
    "credit_code": "91440115MAKKFBK005",
    "addr_cn": "广州市南沙区凯翔路 1 号 408 房（自编南塔 401）",
    "addr_en": "Room 408, No. 1 Kaixiang Road, Nansha District, Guangzhou",
    "phone": "+86 189 2872 4769",
    "phone_digits": "8618928724769",
    "email": "JFC.Consulting@outlook.com",
}

# 价格白名单（数值；范围另做组合校验）
RMB_SINGLE_ALLOWED = {1800, 3000, 3200, 4500, 7200, 1500, 1440, 6000, 15000}
RMB_RANGE_ALLOWED = {(1800, 3000), (3200, 4500), (6000, 15000)}
USD_SINGLE_ALLOWED = {20000, 2, 20}  # USD 20,000 / 2 万美元
WORKDAY_SINGLE_ALLOWED = {5}
WORKDAY_RANGE_ALLOWED = {(7, 10)}
PAGE_RANGE_ALLOWED = {(8, 12)}
PCT_SINGLE_ALLOWED = {30, 40, 60, 70, 100, 10}  # 10% 仅允许用于“抽查”
PCT_RANGE_ALLOWED = {(60, 100), (60, 70), (40, 70)}

# 物料规格：字符数上限/建议区间
MATERIAL_RULES = {
    "A1": {"cn_limit": (None, 1100), "en_limit": (None, 2600),
           "cn_suggest": (480, 620), "en_suggest": (1600, 2000),
           "cn_required": True, "en_required": True},
    "A2": {"cn_limit": (450, 700), "en_limit": None,
           "cn_suggest": (450, 700), "en_suggest": (900, 1200),
           "cn_required": True, "en_required": True},
    "A3": {"cn_limit": (None, 140), "en_limit": (None, 280),
           "cn_required": True, "en_required": True},
    "A4": {"cn_limit": (450, 650), "en_limit": (1150, 1450),
           "cn_required": True, "en_required": True},
    "B1": {"headline_limit": 220},
    "B2": {"headline_limit": 220},
    "B3": {"headline_limit": 220},
    "B4": {"headline_limit": 220},
}

# 英式拼写（硬：明确应改美式；软：可接受但建议统一）
UK_HARD = {
    "standardise": "standardize", "standardised": "standardized",
    "standardisation": "standardization",
    "organise": "organize", "organised": "organized",
    "organises": "organizes", "organisation": "organization",
    "organisations": "organizations", "organising": "organizing",
    "centre": "center", "centres": "centers", "centred": "centered",
    "labour": "labor", "labours": "labors",
    "colour": "color", "colours": "colors", "coloured": "colored",
    "favour": "favor", "favours": "favors", "favourable": "favorable",
    "favourite": "favorite",
    "behaviour": "behavior", "behaviours": "behaviors",
    "analyse": "analyze", "analysed": "analyzed", "analysing": "analyzing",
    "programme": "program", "programmes": "programs",
    "licence": "license", "licences": "licenses",
    "defence": "defense", "offence": "offense",
    "travelling": "traveling", "travelled": "traveled",
    "catalogue": "catalog", "catalogues": "catalogs",
    "utilise": "utilize", "utilised": "utilized",
    "utilisation": "utilization",
    "optimise": "optimize", "optimised": "optimized",
    "optimisation": "optimization",
    "minimise": "minimize", "minimised": "minimized",
    "maximise": "maximize", "maximised": "maximized",
    "recognise": "recognize", "recognised": "recognized",
    "summarise": "summarize", "summarised": "summarized",
    "emphasise": "emphasize", "emphasised": "emphasized",
    "prioritise": "prioritize", "prioritised": "prioritized",
    "realise": "realize", "realised": "realized",
    "specialise": "specialize", "specialised": "specialized",
    "personalise": "personalize", "personalised": "personalized",
    "localise": "localize", "localised": "localized",
    "globalisation": "globalization",
    "metre": "meter", "metres": "meters",
    "litre": "liter", "litres": "liters",
    "fibre": "fiber", "cheque": "check", "mould": "mold",
    "ageing": "aging", "judgement": "judgment", "fulfil": "fulfill",
    "enrolment": "enrollment", "skilful": "skillful",
}
UK_SOFT = {
    "dialogue": "dialog", "towards": "toward", "amongst": "among",
    "whilst": "while", "grey": "gray", "cancelled": "canceled",
    "cancelling": "canceling", "practise": "practice",
    "focussed": "focused", "programmes": "programs",
}

# 绝对化 / 夸张禁用词
ABSOLUTE_PATTERNS = [
    (r"领先", "领先"),
    (r"第一(?!次|步|天|单|批|个|时间|年|季|阶段|轮|层|人称|段|页|屏|条|句|节|手|项|版)",
     "第一"),
    (r"唯一", "唯一"),
    (r"最佳", "最佳"), (r"最好", "最好"), (r"最优", "最优"),
    (r"最大", "最大"), (r"最强", "最强"), (r"最高", "最高"),
    (r"最低", "最低"), (r"最专业", "最专业"), (r"最可靠", "最可靠"),
    (r"独家", "独家"), (r"首选", "首选"), (r"顶级", "顶级"),
    (r"世界级", "世界级"), (r"行业标杆", "行业标杆"),
    (r"no\.?\s*1(?![0-9])(?!\s*(?:Kaixiang|Road|Street|Ave|Floor|Room))", "No.1"),
    (r"#\s*1(?![0-9])", "#1"),
    (r"number\s+one", "number one"),
    (r"world[\s-]?class", "world-class"),
    (r"world[\s-]?leader", "world leader"),
    (r"best[\s-]in[\s-]class", "best-in-class"),
    (r"industry[\s-]leading", "industry-leading"),
    (r"\bleading\b(?!\s+to)", "leading"),
    (r"top[\s-]tier", "top-tier"), (r"unmatched", "unmatched"),
    (r"unrivall?ed", "unrivalled"), (r"risk[\s-]free", "risk-free"),
    (r"100%\s*(?:safe|risk)", "100% safe"),
    (r"zero\s+risk", "zero risk"),
    (r"cutting[\s-]edge", "cutting-edge"),
    (r"state[\s-]of[\s-]the[\s-]art", "state-of-the-art"),
    (r"revolutionary", "revolutionary"),
    (r"game[\s-]chang", "game-changing"),
    (r"trusted\s+by", "trusted by"),
    (r"\bwe\s+ensure\b", "we ensure"),
]

# 仿造/未授权客户名（实体白名单）
CN_COMPANY_RE = re.compile(
    r"[\u4e00-\u9fa5A-Za-z0-9]{4,16}(?:股份有限公司|有限公司|实业公司|集团)")
EN_COMPANY_RE = re.compile(
    r"\b[A-Z][A-Za-z&.\-]+(?:\s+[A-Z][A-Za-z&.\-]+){0,4}\s+"
    r"(?:Inc|Ltd|LLC|GmbH|Corp|Corporation|Co)\b")

# 占位/未完成标记（B4 方括号占位单独放行）
TODO_RE = re.compile(
    r"\bTODO\b|\bTBD\b|\bXXX\b|待补|待填|Lorem ipsum|"
    r"【待|（待", re.IGNORECASE)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?86[\s\-]?)?1[3-9]\d[\s\-]?\d{4}[\s\-]?\d{4}")
URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z]")


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def cjk_count(s):
    return len(CJK_RE.findall(s))


def nonws_count(s):
    return len(re.sub(r"\s", "", s))


def norm_ws(s):
    return re.sub(r"\s+", " ", s).strip()


def parse_int(tok):
    try:
        return int(tok.replace(",", ""))
    except ValueError:
        return None


def snippet(s, n=68):
    s = norm_ws(s)
    return s if len(s) <= n else s[: n - 1] + "…"


class Result:
    def __init__(self, rid, title):
        self.rid = rid
        self.title = title
        self.fails = []
        self.warns = []

    @property
    def status(self):
        if self.fails:
            return "FAIL"
        if self.warns:
            return "WARN"
        return "PASS"

    def fail(self, msg):
        self.fails.append(msg)

    def warn(self, msg):
        self.warns.append(msg)


RESULTS = []


def new_result(rid, title):
    r = Result(rid, title)
    RESULTS.append(r)
    return r


# ---------------------------------------------------------------------------
# 文档解析
# ---------------------------------------------------------------------------
class Doc:
    def __init__(self, path, text):
        self.path = path
        self.text = text
        self.lines = text.split("\n")
        self.fences = []          # {start,end,closed,lines:[(lineno,text)]}
        self.headings = []        # {idx,level,text}
        self.sections = []        # level-2: {idx,title,numeral,start,end,subs}
        self._parse_fences()
        self._parse_headings()
        self._build_sections()

    # ---- fences ----
    def _parse_fences(self):
        in_fence = False
        cur = None
        for i, ln in enumerate(self.lines):
            if re.match(r"^\s*```", ln):
                if not in_fence:
                    in_fence = True
                    cur = {"start": i, "end": None, "closed": False, "lines": []}
                else:
                    cur["end"] = i
                    cur["closed"] = True
                    self.fences.append(cur)
                    in_fence = False
                    cur = None
            elif in_fence:
                cur["lines"].append((i, ln))
        if in_fence and cur is not None:  # 未闭合
            cur["end"] = len(self.lines) - 1
            cur["closed"] = False
            self.fences.append(cur)

    def inside_fence_idx(self):
        s = set()
        for f in self.fences:
            s.update(range(f["start"], f["end"] + 1))
        return s

    # ---- headings ----
    def _parse_headings(self):
        inside = self.inside_fence_idx()
        for i, ln in enumerate(self.lines):
            if i in inside:
                continue
            m = re.match(r"^(#{1,6})\s+(.*)$", ln)
            if m:
                self.headings.append(
                    {"idx": i, "level": len(m.group(1)), "text": m.group(2).strip()})

    # ---- sections ----
    def _build_sections(self):
        for h in self.headings:
            if h["level"] != 2:
                continue
            numeral = None
            m = re.match(
                r"^([〇零一二三四五六七八九十]+)\s*[、.．,:：]?\s*(.*)$", h["text"])
            if m:
                numeral = m.group(1).replace("零", "〇")
                title = m.group(2)
            else:
                title = h["text"]
            self.sections.append({
                "idx": h["idx"], "title": h["text"], "numeral": numeral,
                "start": h["idx"] + 1, "end": len(self.lines), "subs": []})
        for i, s in enumerate(self.sections):
            if i + 1 < len(self.sections):
                s["end"] = self.sections[i + 1]["idx"]
        for s in self.sections:
            subs = [h for h in self.headings
                    if h["level"] == 3 and s["start"] <= h["idx"] < s["end"]]
            for j, h in enumerate(subs):
                sub = {"idx": h["idx"], "title": h["text"],
                       "start": h["idx"] + 1,
                       "end": subs[j + 1]["idx"] if j + 1 < len(subs) else s["end"],
                       "parent": s}
                s["subs"].append(sub)

    # ---- helpers ----
    def section(self, numeral):
        for s in self.sections:
            if s["numeral"] == numeral:
                return s
        return None

    def fences_in(self, lo, hi):
        return [f for f in self.fences if lo <= f["start"] < hi]

    def outside_lines(self, lo, hi):
        inside = self.inside_fence_idx()
        return [(i, self.lines[i]) for i in range(lo, min(hi, len(self.lines)))
                if i not in inside]

    def sub_by_pattern(self, section, pattern, flags=0):
        out = []
        if section is None:
            return out
        for sub in section["subs"]:
            if re.search(pattern, sub["title"], flags):
                out.append(sub)
        return out


def fence_text(f):
    return "\n".join(t for _, t in f["lines"])


def fence_clean_text(f):
    return "\n".join(t.strip() for _, t in f["lines"]).strip()


def line_kind(t):
    """行语言类型：C=中文行，E=英文行，M=中英混排行，N=中性（空行/邮箱/电话等）。"""
    s = t.strip()
    if not s:
        return "N"
    # 只有「联系方式型」行才算中性；正文里夹带邮箱（如 A3 单行贴文）仍按正文判断
    s2 = PHONE_RE.sub(" ", EMAIL_RE.sub(" ", s))
    if not s2.strip() or (cjk_count(s2) == 0 and
                          len(re.sub(r"\s", "", s2)) < 12):
        return "N"
    c = cjk_count(s2)
    l = len(LATIN_RE.findall(s2))
    if c == 0:
        return "E" if l >= 5 else "N"
    if l == 0:
        return "C"
    ratio = c / (c + l)
    if ratio >= 0.60:
        return "C"
    if ratio <= 0.25:
        return "E"
    return "M"


def line_has_cn(t):
    return cjk_count(t) >= 1


def line_is_cn(t):
    return line_kind(t) == "C"


def line_is_en(t):
    return line_kind(t) == "E"


def fence_kinds(f):
    return [line_kind(t) for _, t in f["lines"]]


def fence_langs(f):
    """围栏是否含中文行 / 英文行（混排行 M 视为两者都含）。"""
    kinds = fence_kinds(f)
    has_cn = any(k in ("C", "M") for k in kinds)
    has_en = any(k in ("E", "M") for k in kinds)
    return has_cn, has_en


def fence_profile(f):
    txt = fence_text(f)
    c = cjk_count(txt)
    l = len(LATIN_RE.findall(txt))
    return c, l, (c / (c + l) if (c + l) else 0.0)


def pick_fence(fs, want_cn, after=None):
    """挑选正文 CN/EN 围栏。

    只接受「单语主导」围栏（严格：CN 框不含英文行 / EN 框不含中文行），
    从而跳过 Headline、Experience、Skills 这类双语混排框（B 组结构）。
    """
    cand = [f for f in fs if after is None or f["start"] > after]
    oriented = [f for f in cand
                if (fence_langs(f)[0] if want_cn else fence_langs(f)[1])]
    strict = [f for f in oriented
              if not (fence_langs(f)[1] if want_cn else fence_langs(f)[0])]
    pool = strict or oriented
    if not pool:
        return None
    if want_cn:
        return max(pool, key=lambda f: fence_profile(f)[2])
    return pool[0]


def fence_span(f):
    return "L{}-L{}".format(f["start"] + 1, f["end"] + 1)


# ---------------------------------------------------------------------------
# ① 结构
# ---------------------------------------------------------------------------
NUMERALS = ["〇", "一", "二", "三", "四", "五", "六", "七"]


def check_structure(doc):
    # --- 1. 七大章节齐全、顺序正确 ---
    r = new_result("结构-1", "〇一二三四五六七 章节齐全且顺序正确（## 二级标题）")
    found = [s for s in doc.sections if s["numeral"]]
    order = [s["numeral"] for s in found]
    if not found:
        r.fail("未找到任何带编号的 ## 二级章节（〇/一/二/…/七）")
    else:
        for want in NUMERALS:
            if want not in order:
                r.fail("缺少章节：## {}、…".format(want))
        for i in range(len(order) - 1):
            try:
                a = NUMERALS.index(order[i])
                b = NUMERALS.index(order[i + 1])
                if b < a:
                    r.fail("章节顺序错误：{} 出现在 {} 之后".format(
                        order[i + 1], order[i]))
            except ValueError:
                r.fail("出现非预期章节编号：{}".format(order[i + 1]))
        if doc.sections and doc.sections[0]["numeral"] != "〇":
            r.warn("首个 ## 章节不是「〇、事实表」，实际为：{}".format(
                doc.sections[0]["title"]))
    extras = [s["title"] for s in doc.sections if not s["numeral"]]
    if extras:
        r.warn("存在非编号 ## 章节（确认是否为引导段，不应是正文物料）：{}"
               .format("；".join(extras[:4])))

    # --- 2. 二、四版资料卡 A1–A4 ---
    r = new_result("结构-2", "二、资料卡 A1–A4 齐全且顺序正确")
    sec2 = doc.section("二")
    if sec2 is None:
        r.fail("未找到「## 二、四版资料卡（A1–A4）」章节")
    else:
        mats = []
        for sub in sec2["subs"]:
            m = re.match(r"^A([1-4])(?![0-9])", sub["title"])
            if m:
                mats.append(("A" + m.group(1), sub))
        got = [k for k, _ in mats]
        for k in ["A1", "A2", "A3", "A4"]:
            if k not in got:
                r.fail("{} 小节缺失（应为 ### {} …）".format(k, k))
        if got and got != sorted(got):
            r.fail("A1–A4 顺序不对：{}".format(got))

    # --- 3. 三、员工资料包 ---
    r = new_result("结构-3", "三、员工资料包 B1–B4 + 员工发布规范 + 一句话介绍")
    sec3 = doc.section("三")
    if sec3 is None:
        r.fail("未找到「## 三、员工资料包（B1–B4）」章节")
    else:
        bmats = []
        for sub in sec3["subs"]:
            m = re.match(r"^B([1-4])(?![0-9])", sub["title"])
            if m:
                bmats.append("B" + m.group(1))
        for k in ["B1", "B2", "B3", "B4"]:
            if k not in bmats:
                r.fail("{} 小节缺失".format(k))
        if bmats and bmats != ["B1", "B2", "B3", "B4"]:
            r.fail("B1–B4 顺序不对：{}".format(bmats))
        rules = doc.sub_by_pattern(sec3, r"员工发布规范|Staff Posting Rules", re.I)
        intro = doc.sub_by_pattern(sec3, r"一句话自我介绍|One-Line Introduction", re.I)
        if not rules:
            r.fail("缺少「### 员工发布规范 / Staff Posting Rules」小节")
        if not intro:
            r.fail("缺少「### 一句话自我介绍 / One-Line Introduction」小节")
        if rules and bmats:
            last_b = max([s["idx"] for s in sec3["subs"]
                          if re.match(r"^B[1-4](?![0-9])", s["title"])] or [-1])
            if rules[0]["idx"] < last_b:
                r.fail("「员工发布规范」应位于 B4 之后（当前在 B 系列小节之间）")
        if rules and intro and rules[0]["idx"] > intro[0]["idx"]:
            r.warn("「一句话自我介绍」在「员工发布规范」之前，建议规范在后")

    # --- 4. 四、八项新增建议 ---
    r = new_result("结构-4", "四、八项新增建议 01–08 齐全、顺序与固定字段")
    sec4 = doc.section("四")
    if sec4 is None:
        r.fail("未找到「## 四、八项新增建议」章节")
    else:
        items = []
        for sub in sec4["subs"]:
            m = re.match(r"^0([1-8])(?![0-9])", sub["title"])
            if m:
                items.append((int(m.group(1)), sub))
        nums = [n for n, _ in items]
        for n in range(1, 9):
            if n not in nums:
                r.fail("第 0{} 项缺失".format(n))
        if nums and nums != sorted(nums):
            r.fail("八项顺序不对：{}".format(nums))
        labels = {
            "用途": r"用途", "Use": r"\bUse\b",
            "形式": r"形式", "Form": r"\bForm\b",
            "要点": r"要点", "What to write": r"What to write",
            "负责": r"负责", "Owner": r"\bOwner\b",
            "优先级": r"优先级", "Priority": r"\bPriority\b",
        }
        for n, sub in items:
            body = "\n".join(doc.lines[sub["start"]:sub["end"]])
            miss = [lab for lab, pat in labels.items()
                    if not re.search(pat, body, re.IGNORECASE)]
            if miss:
                r.fail("第 0{} 项缺少固定字段：{}".format(n, "、".join(miss)))

    # --- 5. 〇 事实表关键要素 ---
    r = new_result("结构-5", "〇、事实表含关键要素")
    sec0 = doc.section("〇")
    if sec0 is None:
        r.fail("未找到「## 〇、事实表」章节")
    else:
        body = "\n".join(doc.lines[sec0["start"]:sec0["end"]])
        need = [("电话", CANON["phone"]), ("邮箱", CANON["email"]),
                ("中文地址", CANON["addr_cn"]), ("英文地址", CANON["addr_en"]),
                ("A-Report 价", "1,800"), ("B-Report 价", "3,200"),
                ("信用代码", CANON["credit_code"]),
                ("品牌", CANON["brand"]), ("公司主体", CANON["entity_cn"])]
        for name, token in need:
            if token not in body:
                r.fail("事实表缺少 {}{}".format(name, "（{}）".format(snippet(token, 40))))
        if not re.search(r"^\s*\|.*项目.*\|", body, re.MULTILINE):
            r.warn("事实表未检测到 Markdown 表格表头（项目 / 中文 / English）")

    # --- 6. 一、物料总览三层 ---
    r = new_result("结构-6", "一、物料总览按三层分级")
    sec1 = doc.section("一")
    if sec1 is None:
        r.fail("未找到「## 一、物料总览」章节")
    else:
        body = "\n".join(doc.lines[sec1["start"]:sec1["end"]])
        if not re.search(r"三层|三个层级|three\s+(?:tiers|layers)", body, re.I):
            r.fail("未检测到「三层/three tiers」分级表述")
        markers = re.findall(
            r"第一层|第二层|第三层|第 ?1 ?层|第 ?2 ?层|第 ?3 ?层|"
            r"Layer\s*[123]|Tier\s*[123]|\bL[123]\b", body, re.I)
        if len(markers) < 3:
            r.warn("三层标记不足 3 处（实际 {}），请人工确认分级结构".format(
                len(markers)))
        for token in ["A1", "B1", "建议", "清单"]:
            if token not in body:
                r.warn("总览中未见「{}」，确认是否完整覆盖物料".format(token))

    # --- 7. 七、清单 19 行 ---
    r = new_result("结构-7", "七、清单表 19 行")
    sec7 = doc.section("七")
    if sec7 is None:
        r.fail("未找到「## 七、清单」章节")
    else:
        tbl = [ln.strip() for ln in doc.lines[sec7["start"]:sec7["end"]]
               if ln.strip().startswith("|")]
        if not tbl:
            r.fail("清单章节未检测到 Markdown 表格")
        else:
            sep_ids = [i for i, ln in enumerate(tbl)
                       if re.match(r"^\|[\s:|\-]+\|?$", ln)]
            header = 1
            body_rows = 0
            for i, ln in enumerate(tbl):
                if i == 0 or i == (sep_ids[0] if sep_ids else -1):
                    continue
                body_rows += 1
            total_lines = len(tbl)
            ok = (body_rows == 19) or (total_lines == 19)
            if not ok:
                r.fail("清单行数不符：数据行 {} 行 / 表格总行数 {} 行（期望 19 行）"
                       .format(body_rows, total_lines))
            else:
                r.warn("清单计数：数据行 {} / 总行数 {}（规范暂按 19 行核对，请人工确认口径）"
                       .format(body_rows, total_lines)) if not (body_rows == 19) else None
            header_cells = [c for c in tbl[0].split("|") if c.strip()]
            if len(header_cells) < 3:
                r.warn("清单表列数偏少（{} 列）".format(len(header_cells)))

    # --- 8. 一级标题：仅允许整份文档标题（首行）---
    r = new_result("结构-8", "一级标题仅用于整份文档标题（首行），内文无多余 #")
    h1 = [h for h in doc.headings if h["level"] == 1]
    if len(h1) > 1:
        r.fail("存在多个一级标题：{}（L{} 等），内文应使用 ## / ###".format(
            snippet(h1[0]["text"], 40), h1[0]["idx"] + 1))
    elif h1 and h1[0]["idx"] > 3:
        r.fail("一级标题不在文档开头（L{}）：{}".format(
            h1[0]["idx"] + 1, snippet(h1[0]["text"], 40)))
    # 首行标题（# …）视为允许项，不再报错。
    # 编号章节必须是 ## 二级
    for h in doc.headings:
        if h["level"] != 2 and re.match(r"^[〇零一二三四五六七八九十]\s*[、.．]", h["text"]):
            r.fail("编号章节「{}」不是 ## 二级标题（L{}）".format(
                snippet(h["text"], 30), h["idx"] + 1))


# ---------------------------------------------------------------------------
# ② 围栏：配对、CN/EN 位置、元信息在框外
# ---------------------------------------------------------------------------
def _materials(doc):
    mats = {}
    sec2 = doc.section("二")
    if sec2:
        for sub in sec2["subs"]:
            m = re.match(r"^A([1-4])(?![0-9])", sub["title"])
            if m:
                mats["A" + m.group(1)] = sub
    sec3 = doc.section("三")
    if sec3:
        for sub in sec3["subs"]:
            m = re.match(r"^B([1-4])(?![0-9])", sub["title"])
            if m:
                mats["B" + m.group(1)] = sub
    return mats


def check_fences(doc):
    # --- 1. 配对与闭合 ---
    r = new_result("围栏-1", "围栏成对、全部闭合")
    bad = [f for f in doc.fences if not f["closed"]]
    if bad:
        for f in bad:
            r.fail("围栏未闭合，起始于 L{}".format(f["start"] + 1))
    markers = [i for i, ln in enumerate(doc.lines)
               if re.match(r"^\s*```", ln)]
    if len(markers) % 2 != 0:
        r.fail("围栏标记总数为奇数（{} 个），存在未闭合围栏".format(len(markers)))
    if not doc.fences:
        r.fail("全文未检测到 ``` 围栏（发布文案必须放在围栏内）")

    mats = _materials(doc)
    # --- 2/3. 每个物料 CN 前 EN 后 ---
    for key in ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]:
        rid = "围栏-{}".format(key)
        title = "{} 中文块在前、英文块在后且均在围栏内".format(key)
        r = new_result(rid, title)
        sub = mats.get(key)
        if sub is None:
            r.fail("未找到 {} 小节".format(key))
            continue
        fs = doc.fences_in(sub["start"], sub["end"])
        if not fs:
            r.fail("{} 小节内没有 ``` 围栏".format(key))
            continue
        langs = [fence_langs(f) for f in fs]
        has_cn_any = any(c for c, _ in langs)
        has_en_any = any(e for _, e in langs)
        if not has_cn_any:
            r.fail("未检测到中文发布块（围栏内无中文段落）")
        if not has_en_any:
            r.fail("未检测到英文发布块（围栏内无英文段落）")
        # CN 前 EN 后：只比较「中文正文框」与「英文正文框」。
        # B 组的 Headline / Experience / Skills 是 CN+EN 同框（或双语逐条），
        # 用 pick_fence 自动跳过，只对 About 等单语正文框判先后。
        cn_f = pick_fence(fs, want_cn=True)
        en_f = pick_fence(fs, want_cn=False)
        if cn_f is not None and en_f is not None and en_f["start"] < cn_f["start"]:
            r.fail("英文正文块（{}）出现在中文正文块（{}）之前，应为 CN 前 EN 后"
                   .format(fence_span(en_f), fence_span(cn_f)))
        # 双语混排框内部：中文行应在英文行之前
        for f in fs:
            kinds = fence_kinds(f)
            idx_cn = next((i for i, k in enumerate(kinds) if k == "C"), None)
            idx_en = next((i for i, k in enumerate(kinds) if k == "E"), None)
            if idx_cn is not None and idx_en is not None and idx_en < idx_cn:
                r.fail("围栏 {} 内英文行先于中文行（CN 应在 EN 前）"
                       .format(fence_span(f)))
                break
        if key.startswith("A"):
            if len(fs) < 2:
                r.fail("{} 应有中文、英文两个围栏，实际只有 {} 个".format(key, len(fs)))

    # --- 4. 元信息在围栏外（A1–A4） ---
    r = new_result("围栏-4", "A1–A4 平台/读者/上限/字符数元信息在围栏外")
    for key in ["A1", "A2", "A3", "A4"]:
        sub = mats.get(key)
        if sub is None:
            r.fail("{} 缺失，无法检查元信息".format(key))
            continue
        outside = "\n".join(t for _, t in doc.outside_lines(sub["start"], sub["end"]))
        # A4 是「一页式邮件/PDF 留资」，元信息用「用途 / Use」而非「平台」
        first = ("用途 / Use", r"用途|Use|平台|Platform") if key == "A4" \
            else ("平台 / Platform", r"平台|Platform")
        need = [first,
                ("读者 / Audience", r"读者|Audience"),
                ("上限 / Limit", r"上限|Limit|建议"),
                ("字符数 Characters", r"字符数\s*Characters?")]
        for name, pat in need:
            if not re.search(pat, outside, re.I):
                r.fail("{} 围栏外缺少元信息：{}".format(key, name))
        fenced = "\n".join(fence_text(f) for f in doc.fences_in(sub["start"], sub["end"]))
        if re.search(r"字符数\s*Characters?", fenced):
            r.fail("{} 的「字符数 Characters」行出现在围栏内（元信息必须在框外）"
                   .format(key))

    # --- 5. 正文不应大量出现在围栏外 ---
    r = new_result("围栏-5", "发布文案未散落在围栏外")
    for key, sub in mats.items():
        for i, ln in doc.outside_lines(sub["start"], sub["end"]):
            s = ln.strip()
            if not s or s.startswith("#") or s.startswith("|"):
                continue
            if any(t in s for t in ["平台", "Platform", "读者", "Audience",
                                    "上限", "Limit", "字符数", "Characters",
                                    "用途", "Use:", "字符"]):
                continue
            if cjk_count(s) >= 20 and not re.search(r"[。；：！]$", s):
                pass
            if cjk_count(s) >= 30:
                r.warn("{} 围栏外出现较长中文段落，疑似正文未入框（L{}）：{}"
                       .format(key, i + 1, snippet(s)))
                break

    # --- 6. 围栏内无 Markdown 强调与元信息 ---
    r = new_result("围栏-6", "围栏内为纯文本（无 Markdown 强调号）")
    for f in doc.fences:
        txt = fence_text(f)
        if "**" in txt:
            r.fail("围栏 {} 内出现 Markdown 加粗 **".format(fence_span(f)))
        if "字符数" in txt or re.search(r"^\s*平台\s*[:：]", txt, re.MULTILINE):
            r.fail("围栏 {} 内混入元信息（字符数/平台）".format(fence_span(f)))


# ---------------------------------------------------------------------------
# ③ 字符数声明一致性与上限
# ---------------------------------------------------------------------------
DECL_RE = re.compile(r"字符数\s*Characters?\s*[:：]\s*(.*)$", re.IGNORECASE)


def parse_decl_line(rest):
    """从 '字符数 Characters: ...' 冒号后文本解析中英数字。返回 (cn, en) 或 None。"""
    cn_word = re.search(r"中文|中文字符|CN", rest)
    en_word = re.search(r"English|英文|EN", rest)
    nums = re.findall(r"[\d,]+", rest)
    # 去掉年份等明显非计数（字符数字不会超过 6 位）
    nums = [n for n in nums if 0 < (parse_int(n) or 0) <= 999999]
    cn = en = None
    if cn_word and en_word:
        tail_cn = rest[cn_word.end():]
        tail_en = rest[en_word.end():]
        m = re.search(r"([\d,]+)", tail_cn)
        if m:
            cn = parse_int(m.group(1))
        m = re.search(r"([\d,]+)", tail_en)
        if m:
            en = parse_int(m.group(1))
        if cn is None or en is None:
            if len(nums) >= 2:
                cn, en = parse_int(nums[0]), parse_int(nums[1])
    elif len(nums) == 2:
        cn, en = parse_int(nums[0]), parse_int(nums[1])
    elif len(nums) == 1:
        cn = parse_int(nums[0])
    if cn is None and en is None:
        return None
    return cn, en


def decls_in_section(doc, sub):
    inside = doc.inside_fence_idx()
    out = []
    for i in range(sub["start"], min(sub["end"], len(doc.lines))):
        if i in inside:
            continue
        ln = doc.lines[i]
        m = DECL_RE.search(ln)
        if not m:
            continue
        prefix = ln[:m.start()]
        # 上下文标签：本行冒号前文字 + 前 3 行非空行
        label = prefix
        for j in range(i - 1, max(sub["start"], i - 4) - 1, -1):
            if j in inside:
                continue
            s = doc.lines[j].strip()
            if s:
                label += " " + s
                break
        parsed = parse_decl_line(m.group(1))
        out.append({"idx": i, "label": label, "parsed": parsed})
    return out


def _fence_after(fs, line_idx):
    return [f for f in fs if f["start"] > line_idx]


def actual_counts(fence):
    """返回 (cn_actual, {en 变体名: 数值})"""
    raw_lines = [t.rstrip() for _, t in fence["lines"]]
    txt_nl = "\n".join(raw_lines).strip()
    txt_join = "".join(t.strip() for t in raw_lines).strip()
    txt_space = " ".join(t.strip() for t in raw_lines if t.strip()).strip()
    cn = nonws_count(txt_nl)
    return cn, {
        "换行保留": len(txt_nl),
        "无换行": len(txt_join),
        "以空格连接": len(txt_space),
    }


def check_char_decls(doc):
    mats = _materials(doc)
    for key in ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]:
        sub = mats.get(key)
        rule = MATERIAL_RULES[key]
        rid = "字符数-{}".format(key)
        title = "{} 字符数声明与实际统计一致".format(key)
        r = new_result(rid, title)
        if sub is None:
            r.fail("未找到 {} 小节".format(key))
            continue
        decls = decls_in_section(doc, sub)
        if not decls:
            if key.startswith("A"):
                r.fail("未找到「字符数 Characters: 中文 X / English Y」声明行")
            else:
                r.warn("未找到 About 的「字符数 Characters」声明行（建议补填）")
            continue
        if len(decls) > 1:
            r.warn("检测到 {} 处字符数声明，仅校验第一处（L{}）".format(
                len(decls), decls[0]["idx"] + 1))
        d = decls[0]
        if d["parsed"] is None:
            r.fail("字符数声明无法解析（L{}）：{}".format(
                d["idx"] + 1, snippet(doc.lines[d["idx"]])))
            continue
        decl_cn, decl_en = d["parsed"]
        fs = _fence_after(doc.fences_in(sub["start"], sub["end"]), d["idx"])
        if not fs:
            r.fail("字符数声明（L{}）之后没有对应围栏".format(d["idx"] + 1))
            continue
        # 找 CN / EN 正文围栏：跳过 Headline / Experience / Skills 等双语混排框
        cn_f = pick_fence(fs, want_cn=True)
        en_f = pick_fence(fs, want_cn=False,
                          after=cn_f["start"] if cn_f is not None else None)
        if cn_f is None:
            cn_f = pick_fence(fs, want_cn=True)
        if cn_f is None:
            r.fail("字符数声明（L{}）之后未找到中文围栏".format(d["idx"] + 1))
            continue
        if rule.get("cn_required") and decl_cn is None:
            r.fail("中文声明缺失数字（L{}）".format(d["idx"] + 1))
        if rule.get("en_required") and decl_en is None:
            r.fail("英文声明缺失数字（L{}）".format(d["idx"] + 1))
        # 实际统计
        if decl_cn is not None:
            cn_actual, _ = actual_counts(cn_f)
            if decl_cn != cn_actual:
                r.fail("中文声明 {} 与实际 {} 不一致（{}；声明 L{}）".format(
                    decl_cn, cn_actual, fence_span(cn_f), d["idx"] + 1))
            if decl_cn == 0:
                r.fail("中文声明为 0，疑似未填真实字符数（L{}）".format(
                    d["idx"] + 1))
        if decl_en is not None and en_f is not None:
            _, variants = actual_counts(en_f)
            if decl_en not in variants.values():
                r.fail("英文声明 {} 与实际不一致（{}；实际变体：{}；声明 L{}）"
                       .format(decl_en, fence_span(en_f),
                               "、".join("{}={}".format(k, v)
                                        for k, v in variants.items()),
                               d["idx"] + 1))
        elif decl_en is not None and en_f is None:
            r.fail("英文声明存在但未找到英文围栏（L{}）".format(d["idx"] + 1))

        # 上限
        r = new_result("字符数-上限-{}".format(key),
                       "{} 字符数符合规格上限".format(key))
        lim_cn = rule.get("cn_limit")
        lim_en = rule.get("en_limit")
        if lim_cn and decl_cn is not None:
            lo, hi = lim_cn
            if (lo is not None and decl_cn < lo) or (hi is not None and decl_cn > hi):
                r.fail("中文 {} 字，超出规格 {}（L{}）".format(
                    decl_cn, _range_text(lo, hi), d["idx"] + 1))
        if lim_en and decl_en is not None:
            lo, hi = lim_en
            if (lo is not None and decl_en < lo) or (hi is not None and decl_en > hi):
                r.fail("英文 {} 字符，超出规格 {}（L{}）".format(
                    decl_en, _range_text(lo, hi), d["idx"] + 1))
        # 建议区间
        sug_cn = rule.get("cn_suggest")
        sug_en = rule.get("en_suggest")
        if sug_cn and decl_cn is not None and not (sug_cn[0] <= decl_cn <= sug_cn[1]):
            r.warn("中文 {} 字，建议区间 {}-{}（视上限内即可，供参考）".format(
                decl_cn, sug_cn[0], sug_cn[1]))
        if sug_en and decl_en is not None and not (sug_en[0] <= decl_en <= sug_en[1]):
            r.warn("英文 {} 字符，建议区间 {}-{}（视上限内即可，供参考）".format(
                decl_en, sug_en[0], sug_en[1]))

    # --- Headline ≤220 ---
    for key in ["B1", "B2", "B3", "B4"]:
        r = new_result("字符数-Headline-{}".format(key),
                       "{} Headline 每行 ≤220 字符且 CN 在前".format(key))
        sub = mats.get(key)
        if sub is None:
            r.fail("未找到 {} 小节".format(key))
            continue
        inside = doc.inside_fence_idx()
        label_idx = None
        for i in range(sub["start"], sub["end"]):
            if i in inside:
                continue
            if re.search(r"Headline", doc.lines[i], re.I):
                label_idx = i
                if "220" not in doc.lines[i]:
                    r.warn("Headline 标注行未写明 220 字符上限（L{}）".format(i + 1))
                break
        if label_idx is None:
            r.fail("未找到 Headline 标注行（Headline（上限 220 字符…））")
            continue
        fs = _fence_after(doc.fences_in(sub["start"], sub["end"]), label_idx)
        if not fs:
            r.fail("Headline 标注行（L{}）之后没有围栏".format(label_idx + 1))
            continue
        hf = fs[0]
        lines = [t for _, t in hf["lines"] if t.strip()]
        if not lines:
            r.fail("Headline 围栏为空（{}）".format(fence_span(hf)))
            continue
        if len(lines) < 2:
            r.warn("Headline 围栏仅 {} 行，确认是否含 CN+EN 两行".format(len(lines)))
        for j, t in enumerate(lines):
            n = nonws_count(t) if line_is_cn(t) else len(t.strip())
            if n > 220:
                r.fail("Headline 第 {} 行 {} 字符，超过 220（{}）：{}".format(
                    j + 1, n, fence_span(hf), snippet(t, 50)))
        if lines and not line_is_cn(lines[0]):
            r.fail("Headline 围栏第一行不是中文，应 CN 在前（{}）".format(
                fence_span(hf)))
        if len(lines) >= 2 and line_is_cn(lines[1]):
            r.warn("Headline 第二行仍为中文，确认 CN/EN 分行是否正确")
        # 校核「Headline 字符数 / Headline characters: 中文 X / English Y」声明
        hs = None
        for i in range(sub["start"], sub["end"]):
            if i in inside:
                continue
            if re.search(r"Headline\s*(?:字符数|characters)", doc.lines[i], re.I):
                hs = i
                break
        if hs is not None:
            m = re.search(r"[:：]\s*(.+)$", doc.lines[hs])
            parsed = parse_decl_line(m.group(1)) if m else None
            if parsed is None:
                r.warn("Headline 字符数声明无法解析（L{}）".format(hs + 1))
            else:
                dcn, den = parsed
                act_cn = nonws_count(lines[0])
                act_en = len(lines[1].strip()) if len(lines) > 1 else None
                if dcn is not None and dcn != act_cn:
                    r.fail("Headline 中文声明 {} 与实际 {} 不一致（声明 L{}）"
                           .format(dcn, act_cn, hs + 1))
                if den is not None and act_en is not None and den != act_en:
                    r.fail("Headline 英文声明 {} 与实际 {} 不一致（声明 L{}）"
                           .format(den, act_en, hs + 1))


def _range_text(lo, hi):
    if lo is not None and hi is not None:
        return "{}-{}".format(lo, hi)
    if hi is not None:
        return "≤{}".format(hi)
    return "≥{}".format(lo)


# ---------------------------------------------------------------------------
# ④ 事实一致性
# ---------------------------------------------------------------------------
HR = r"[–—−~-]"
TOK = r"\d{1,3}(?:,\d{3})+|\d+"
RANGE = r"({0})(?:\s*{1}\s*({0}))?".format(TOK, HR)


def _iter_lines(doc):
    for i, ln in enumerate(doc.lines):
        yield i + 1, ln


def check_facts(doc):
    whole = "\n".join(doc.lines)
    whole_norm = norm_ws(whole)

    # --- 1. 地址 / 建塔建滔 ---
    r = new_result("事实-1", "地址逐字一致，无「建塔/建滔」")
    inside_fence = doc.inside_fence_idx()
    for lineno, ln in _iter_lines(doc):
        if not re.search(r"建塔|建滔", ln):
            continue
        if (lineno - 1) in inside_fence:
            r.fail("发布文案围栏内出现禁用地址写法「建塔/建滔」（L{}）：{}"
                   .format(lineno, snippet(ln)))
        elif re.search(r"不写|不要|不得|禁用|禁止|避免|never write|do not write",
                       ln, re.I):
            continue  # 合规/口径说明中的禁止性引用
        elif re.search(r"凯翔路|地址|Address|408", ln):
            r.fail("地址相关行出现「建塔/建滔」（L{}）：{}".format(
                lineno, snippet(ln)))
        else:
            r.warn("L{} 出现「建塔/建滔」字样，请人工确认是否为否定说明：{}"
                   .format(lineno, snippet(ln)))
    if "凯翔路" in whole:
        addr_variants = [whole_norm, whole.replace("\n", "")]
        if not any(CANON["addr_cn"] in v for v in addr_variants):
            r.fail("中文地址不是事实表逐字口径：「{}」".format(CANON["addr_cn"]))
    if re.search(r"Kaixiang", whole, re.I):
        addr_variants = [whole_norm, whole.replace("\n", "")]
        if "Kaixiang" in whole and not any(
                CANON["addr_en"] in v for v in addr_variants):
            r.fail("英文地址不是事实表逐字口径：「{}」".format(CANON["addr_en"]))
    # 地址若出现 408 房 / Room 408，必须完整
    for lineno, ln in _iter_lines(doc):
        if re.search(r"408\s*房|Room\s*408", ln):
            if "408 房" in ln and "凯翔路" in whole and CANON["addr_cn"] not in norm_ws(whole):
                r.fail("L{} 含 408 房但全文无完整中文地址".format(lineno))

    # --- 2. 价格白名单 ---
    r = new_result("事实-2", "价格只用事实表白名单（RMB 1,800–3,000 / 3,200–4,500 / 套餐价 / 顾问费）")
    for lineno, ln in _iter_lines(doc):
        # RMB 前缀
        for m in re.finditer(r"(?:RMB|Rmb)\s*" + RANGE, ln):
            _validate_price(r, "RMB", m, lineno, ln, "CNY")
        # “元”后缀
        for m in re.finditer(RANGE + r"\s*元", ln):
            _validate_price(r, "元", m, lineno, ln, "CNY")
        # 每站点/月 单价
        for m in re.finditer(r"(" + TOK + r")\s*/\s*(?:站点|site|月|month)", ln, re.I):
            val = parse_int(m.group(1))
            if val not in RMB_SINGLE_ALLOWED:
                r.fail("L{} 非白名单单价 {}：{}".format(
                    lineno, m.group(0), snippet(ln)))
        # 人民币符号
        if re.search(r"[¥￥]", ln):
            r.fail("L{} 使用了人民币符号（应写 RMB 或「元」）：{}".format(
                lineno, snippet(ln)))
        # USD
        for m in re.finditer(r"(?:USD|US\$)\s*" + RANGE, ln):
            _validate_usd(r, m, lineno, ln)
        for m in re.finditer(RANGE + r"\s*万\s*美元", ln):
            _validate_usd(r, m, lineno, ln)
        if re.search(r"\$\s*\d", ln):
            r.fail("L{} 使用了 $ 价格写法（应写 USD）：{}".format(
                lineno, snippet(ln)))

    # --- 3. 电话 ---
    r = new_result("事实-3", "电话与事实表逐字一致（+86 189 2872 4769）")
    for lineno, ln in _iter_lines(doc):
        for m in PHONE_RE.finditer(ln):
            digits = re.sub(r"\D", "", m.group(0))
            if not digits.endswith("18928724769"):
                r.fail("L{} 电话与事实表不一致：{}".format(lineno, snippet(ln)))
    if "189" in whole and CANON["phone"] not in whole:
        r.warn("出现电话片段但未见完整「+86 189 2872 4769」")

    # --- 4. 邮箱 ---
    r = new_result("事实-4", "邮箱与事实表逐字一致（JFC.Consulting@outlook.com）")
    for lineno, ln in _iter_lines(doc):
        for m in EMAIL_RE.finditer(ln):
            if m.group(0) != CANON["email"]:
                r.fail("L{} 邮箱不一致：{}".format(lineno, snippet(ln)))
    if CANON["email"] not in whole:
        r.fail("全文未出现事实表邮箱 {}".format(CANON["email"]))

    # --- 5. 公司主体 / 信用代码 ---
    r = new_result("事实-5", "公司主体与信用代码逐字一致")
    for lineno, ln in _iter_lines(doc):
        for m in re.finditer(r"9144[0-9A-Za-z]{10,}", ln):
            if m.group(0) != CANON["credit_code"]:
                r.fail("L{} 信用代码错误：{}".format(lineno, snippet(ln)))
        for m in re.finditer(r"[\u4e00-\u9fa5]{0,8}玄墨[\u4e00-\u9fa5]{0,10}", ln):
            if CANON["entity_cn"] not in m.group(0):
                r.fail("L{} 公司主体名称与事实表不一致：{}".format(
                    lineno, snippet(ln)))

    # --- 6. 时限 ---
    r = new_result("事实-6", "工时口径只用 5 / 7–10 个工作日")
    for lineno, ln in _iter_lines(doc):
        for m in re.finditer(
                r"(\d+)(?:\s*" + HR + r"\s*(\d+))?\s*个工作日", ln):
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else None
            if b is None and a not in WORKDAY_SINGLE_ALLOWED:
                r.fail("L{} 非白名单工时：{}".format(lineno, snippet(ln)))
            elif b is not None and (a, b) not in WORKDAY_RANGE_ALLOWED:
                r.fail("L{} 非白名单工时：{}".format(lineno, snippet(ln)))
        for m in re.finditer(r"(\d+)(?:\s*(?:–|-|to)\s*(\d+))?\s*business\s+days?",
                             ln, re.I):
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else None
            if b is None and a not in WORKDAY_SINGLE_ALLOWED:
                r.fail("L{} 非白名单工时（EN）：{}".format(lineno, snippet(ln)))
            elif b is not None and (a, b) not in WORKDAY_RANGE_ALLOWED:
                r.fail("L{} 非白名单工时（EN）：{}".format(lineno, snippet(ln)))
        if re.search(r"seven\s+to\s+ten\s+business\s+days", ln, re.I):
            pass
        elif re.search(r"(?<![\d–-])\d+\s+working\s+days?", ln, re.I):
            m = re.search(r"(\d+)\s+working\s+days?", ln, re.I)
            if int(m.group(1)) not in WORKDAY_SINGLE_ALLOWED:
                r.warn("L{} 使用 working days，建议统一 business days：{}".format(
                    lineno, snippet(ln)))

    # --- 7. 百分比 ---
    r = new_result("事实-7", "百分比只用事实表口径（30/40/60–70/60–100/100，10% 仅抽查）")
    for lineno, ln in _iter_lines(doc):
        if INSTRUCTION_RE.search(ln):
            continue  # 合规说明中对禁用数字的引用，不算对外数据
        for m in re.finditer(r"(\d+)\s*" + HR + r"\s*(\d+)\s*[%％]", ln):
            a, b = int(m.group(1)), int(m.group(2))
            if (a, b) not in PCT_RANGE_ALLOWED:
                r.fail("L{} 非白名单百分比区间：{}".format(lineno, snippet(ln)))
        for m in re.finditer(r"(\d+)\s*[%％]", ln):
            # 跳过区间表达式的后半段
            start = m.start()
            if re.search(r"\d\s*" + HR + r"\s*$", ln[:start]):
                continue
            val = int(m.group(1))
            if val not in PCT_SINGLE_ALLOWED:
                r.fail("L{} 非白名单百分比：{}".format(lineno, snippet(ln)))
            elif val == 10 and not re.search(r"抽查|spot", ln, re.I):
                r.fail("L{} 10% 仅允许用于「抽查」语境：{}".format(
                    lineno, snippet(ln)))

    # --- 8. 禁用统计与区间 ---
    r = new_result("事实-8", "无 73% / 20–100 倍 / 非白名单页数区间")
    for lineno, ln in _iter_lines(doc):
        if INSTRUCTION_RE.search(ln):
            continue  # 合规说明中的“不写 73%”“never cite 20–100×”等引用
        if re.search(r"73\s*[%％]", ln):
            r.fail("L{} 出现禁用数据 73%：{}".format(lineno, snippet(ln)))
        if re.search(r"20\s*" + HR + r"\s*100\s*(?:倍|x|X|times)", ln):
            r.fail("L{} 出现禁用规划数字 20–100 倍：{}".format(lineno, snippet(ln)))
        for m in re.finditer(r"(\d+)\s*" + HR + r"\s*(\d+)\s*页", ln):
            a, b = int(m.group(1)), int(m.group(2))
            if (a, b) not in PAGE_RANGE_ALLOWED:
                r.fail("L{} 非白名单页数区间：{}".format(lineno, snippet(ln)))
        for m in re.finditer(r"(\d+)\s*(?:–|-|to)\s*(\d+)[\s-]*pages?", ln, re.I):
            a, b = int(m.group(1)), int(m.group(2))
            if (a, b) not in PAGE_RANGE_ALLOWED:
                r.fail("L{} 非白名单页数区间（EN）：{}".format(lineno, snippet(ln)))

    # --- 9. 虚构客户名 ---
    r = new_result("事实-9", "无虚构客户/案例名称")
    for lineno, ln in _iter_lines(doc):
        for m in CN_COMPANY_RE.finditer(ln):
            txt = m.group(0)
            if CANON["entity_cn"] in txt or txt in CANON["entity_cn"]:
                continue
            if "玄墨" in txt:
                continue
            r.fail("L{} 疑似虚构客户/公司名：{}".format(lineno, snippet(ln)))
        for m in EN_COMPANY_RE.finditer(ln):
            around = ln[max(0, m.start() - 60):m.end() + 60]
            if "Guangzhou Xuanmo Business Consulting" in around:
                continue
            r.fail("L{} 疑似虚构客户/公司名（EN）：{}".format(lineno, snippet(ln)))

    # --- 10. 网址 / 其他货币 ---
    r = new_result("事实-10", "无事实表之外的网址与其他货币符号")
    for lineno, ln in _iter_lines(doc):
        if URL_RE.search(ln):
            r.fail("L{} 出现网址（事实表无网址，不得自行发明）：{}".format(
                lineno, snippet(ln)))
        if re.search(r"€|£", ln):
            r.fail("L{} 出现其他货币符号：{}".format(lineno, snippet(ln)))


def _validate_price(r, source, m, lineno, ln, kind):
    nums = [parse_int(g) for g in m.groups() if g]
    if not nums:
        return
    if len(nums) == 1:
        if nums[0] not in RMB_SINGLE_ALLOWED:
            r.fail("L{} 非白名单价格（{} {}）：{}".format(
                lineno, source, nums[0], snippet(ln)))
    else:
        pair = (nums[0], nums[1])
        if pair not in RMB_RANGE_ALLOWED:
            r.fail("L{} 非白名单价格区间（{} {:,}–{:,}）：{}".format(
                lineno, source, nums[0], nums[1], snippet(ln)))


def _validate_usd(r, m, lineno, ln):
    nums = [parse_int(g) for g in m.groups() if g]
    for v in nums:
        if v not in USD_SINGLE_ALLOWED:
            msg = ("L{} 美元金额 {} 不在事实表白名单（事实表仅 USD 20,000），"
                   "若为模板示例请人工确认：{}".format(lineno, v, snippet(ln)))
            if msg not in r.warns:
                r.warn(msg)


# ---------------------------------------------------------------------------
# ⑤ 合规
# ---------------------------------------------------------------------------
def _line_has_negation(text, pos, window=16):
    left = text[max(0, pos - window):pos]
    return bool(re.search(r"不|非|无|未|没有|no\b|not\b|never\b|without\b|"
                          r"isn't|don't|doesn't", left, re.I))


def _negated_around(text, start, end, left=24, right=14):
    """检查词左右是否处于否定/禁止语境（不写、不称、no、not、never…）。"""
    l = text[max(0, start - left):start]
    r = text[end:end + right]
    return bool(re.search(
        r"不|非|无|未|没有|no\b|not\b|never\b|without\b|isn't|don't|doesn't|"
        r"cannot|none\b", l, re.I)) or bool(re.search(
        r"\b(?:not|no|never)\b|不做|不发|不出|不构成|不承诺|不担保", r, re.I))


# 「禁止性规则 / 术语表释义」上下文：命中的是禁用词本身，不是宣称
INSTRUCTION_RE = re.compile(
    r"不写|不称|不使用|不引用|不对外|不得|禁用|禁止|避免|不要|不承诺|不担保|"
    r"\bNever\b|\bDo not\b|\bDon't\b|☐|"
    r"术语表|Glossary|这类|此类", re.IGNORECASE)


def _in_section(doc, sub_patterns):
    """返回满足标题匹配的 section/sub 行号集合。"""
    ids = set()
    for s in doc.sections:
        if any(re.search(p, s["title"], re.I) for p in sub_patterns):
            ids.update(range(s["start"], s["end"]))
    for s in doc.sections:
        for sub in s["subs"]:
            if any(re.search(p, sub["title"], re.I) for p in sub_patterns):
                ids.update(range(sub["start"], sub["end"]))
    return ids


def check_compliance(doc):
    # --- 1. 感叹号 ---
    r = new_result("合规-1", "全文无感叹号（! / ！）")
    for lineno, ln in _iter_lines(doc):
        if "!" in ln or "！" in ln:
            r.fail("L{} 出现感叹号：{}".format(lineno, snippet(ln)))

    # --- 2. 认证 / certification 宣称 ---
    r = new_result("合规-2",
                   "无「认证/certification」宣称（禁止性规则与术语表释义除外）")
    inside = doc.inside_fence_idx()
    gloss_or_compliance = _in_section(
        doc, [r"术语表|Glossary", r"合规|Compliance", r"发布规范|Posting Rules"])
    noted = set()
    for lineno, ln in _iter_lines(doc):
        in_fence = (lineno - 1) in inside
        in_gloss = (lineno - 1) in gloss_or_compliance
        for m in re.finditer(r"认证|certif[a-z]*", ln, re.I):
            if in_gloss:
                # 术语表/合规节：禁用词是被解释或禁止的对象，只记 NOTE
                if lineno not in noted:
                    noted.add(lineno)
                    r.warn("L{} 术语表/合规节释义（NOTE，不计 FAIL）：{}"
                           .format(lineno, snippet(ln)))
                continue
            if not in_fence and INSTRUCTION_RE.search(ln):
                continue
            if _negated_around(ln, m.start(), m.end()):
                continue
            ctx = ln[max(0, m.start() - 30):m.end() + 30]
            strong = re.search(
                r"(获得|通过|取得|颁发|授予|出具|提供)\s*(?:相关)?认证|"
                r"认证(?:机构|证书|报告)|"
                r"\bcertified\b|\bwe certify\b|"
                r"certification\s+(?:body|process|report|program)",
                ctx, re.I)
            if strong:
                if in_fence:
                    r.fail("L{} 发布文案出现认证宣称：{}".format(
                        lineno, snippet(ln)))
                else:
                    r.warn("L{} 出现认证宣称字样，请人工确认：{}".format(
                        lineno, snippet(ln)))
            else:
                r.warn("L{} 出现「{}」字样，请人工确认是否否定/术语解释：{}"
                       .format(lineno, m.group(0), snippet(ln)))

    # --- 3. 保证 / 担保 / guarantee ---
    r = new_result("合规-3", "无「保证/担保/guarantee」承诺（否定/禁止语境除外）")
    for lineno, ln in _iter_lines(doc):
        in_fence = (lineno - 1) in inside
        if not in_fence and INSTRUCTION_RE.search(ln):
            continue
        for m in re.finditer(r"保证|担保", ln):
            if _negated_around(ln, m.start(), m.end()):
                continue
            if in_fence:
                r.fail("L{} 发布文案出现保证/担保表述：{}".format(
                    lineno, snippet(ln)))
            else:
                r.warn("L{} 出现保证/担保字样，请人工确认：{}".format(
                    lineno, snippet(ln)))
        for m in re.finditer(r"guarantee|guaranteed|guarantees", ln, re.I):
            if _negated_around(ln, m.start(), m.end()):
                continue
            if in_fence:
                r.fail("L{} 发布文案出现 guarantee 表述：{}".format(
                    lineno, snippet(ln)))
            else:
                r.warn("L{} 出现 guarantee 字样，请人工确认：{}".format(
                    lineno, snippet(ln)))

    # --- 4. 绝对化用语 ---
    r = new_result("合规-4", "无绝对化用语（最/第一/唯一/领先/最佳…）")
    for lineno, ln in _iter_lines(doc):
        in_fence = (lineno - 1) in inside
        if not in_fence and INSTRUCTION_RE.search(ln):
            continue
        for pat, label in ABSOLUTE_PATTERNS:
            for m in re.finditer(pat, ln, re.IGNORECASE):
                if label in ("唯一", "第一") and _negated_around(
                        ln, m.start(), m.end()):
                    continue
                if in_fence:
                    r.fail("L{} 发布文案出现绝对化用语「{}」：{}".format(
                        lineno, label, snippet(ln)))
                else:
                    r.warn("L{} 出现绝对化用语「{}」，请人工确认语境：{}".format(
                        lineno, label, snippet(ln)))

    # --- 5. 营销黑名单 ---
    r = new_result("合规-5", "无夸大用语（100% risk-free / we ensure 等）")
    for lineno, ln in _iter_lines(doc):
        in_fence = (lineno - 1) in inside
        if not in_fence and INSTRUCTION_RE.search(ln):
            continue
        for m in re.finditer(r"100%\s*risk[\s-]?free|zero\s+risk|we\s+ensure|"
                             r"we\s+guarantee|no\s+risk", ln, re.I):
            if _negated_around(ln, m.start(), m.end()):
                continue
            if in_fence:
                r.fail("L{} 发布文案出现夸大/担保用语：{}".format(
                    lineno, snippet(ln)))
            else:
                r.warn("L{} 出现夸大/担保字样，请人工确认：{}".format(
                    lineno, snippet(ln)))

    # --- 6. 建议：克制性表述（“最X”修辞，task-4 要求避免“最”）---
    r = new_result("合规-6", "建议：发布文案避免“最贵/最难”等“最X”修辞")
    for lineno, ln in _iter_lines(doc):
        if (lineno - 1) not in inside:
            continue
        if re.search(r"最(?:贵|难|坏|痛|麻烦)", ln):
            r.warn("L{} 发布文案含“最X”修辞，建议改写得更克制：{}".format(
                lineno, snippet(ln)))


# ---------------------------------------------------------------------------
# ⑥ 英式拼写
# ---------------------------------------------------------------------------
def check_spelling(doc):
    r = new_result("拼写-1", "英文无英式拼写（standardise/organisation/centre/labour…）")
    hits = []
    for lineno, ln in _iter_lines(doc):
        for uk, us in UK_HARD.items():
            for m in re.finditer(r"\b" + re.escape(uk) + r"\b", ln, re.I):
                hits.append((lineno, m.group(0), us, snippet(ln)))
    for lineno, got, us, sn in hits:
        r.fail("L{} 英式拼写「{}」→ 应为「{}」：{}".format(lineno, got, us, sn))

    r = new_result("拼写-2", "疑似英式拼写（建议项）")
    for lineno, ln in _iter_lines(doc):
        for uk, us in UK_SOFT.items():
            for m in re.finditer(r"\b" + re.escape(uk) + r"\b", ln, re.I):
                r.warn("L{} 疑似英式拼写「{}」（美式建议「{}」）：{}".format(
                    lineno, m.group(0), us, snippet(ln)))


# ---------------------------------------------------------------------------
# ⑦ 编辑审读（可自动化的部分）
# ---------------------------------------------------------------------------
def check_editorial(doc):
    mats = _materials(doc)

    # --- 1. B4 方括号占位保留 ---
    r = new_result("编辑-1", "B4 通用模板保留方括号占位")
    b4 = mats.get("B4")
    if b4 is None:
        r.fail("未找到 B4 小节")
    else:
        body = "\n".join(doc.lines[b4["start"]:b4["end"]])
        ph = re.findall(r"\[[^\[\]\n]{1,40}\]", body)
        if len(ph) < 3:
            r.fail("B4 方括号占位不足（实际 {} 个），应保留 [姓名]/[职位]/[具体职责] 等"
                   .format(len(ph)))
        for token in ["姓名", "职位", "职责", "一句话", "专业背景"]:
            if not re.search(r"\[[^\]]*" + token, body):
                r.warn("B4 未见含「{}」的方括号占位".format(token))
        if "不得原样发布" not in body:
            r.fail("B4 缺少「方括号内容不得原样发布」提示")

    # --- 2. 员工发布规范 5 条 ---
    r = new_result("编辑-2", "员工发布规范 5 条且覆盖关键要求")
    sec3 = doc.section("三")
    rules = doc.sub_by_pattern(sec3, r"员工发布规范|Staff Posting Rules", re.I) \
        if sec3 else []
    if not rules:
        r.fail("未找到员工发布规范小节")
    else:
        sub = rules[0]
        body_lines = doc.lines[sub["start"]:sub["end"]]
        items = [ln for ln in body_lines
                 if re.match(r"^\s*(?:[-*]|\d+[.、)）])\s+\S", ln)]
        if len(items) < 5:
            r.fail("员工发布规范条目不足 5 条（检测到 {} 条）".format(len(items)))
        body = "\n".join(body_lines)
        for name in ["事实表", "认证", "客户名称"]:
            if name not in body:
                r.warn("发布规范未提及「{}」，请人工确认覆盖度".format(name))

    # --- 3. 一句话自我介绍 ---
    r = new_result("编辑-3", "一句话自我介绍含 CN/EN 与邮件签名行")
    intro = doc.sub_by_pattern(sec3, r"一句话自我介绍|One-Line Introduction", re.I) \
        if sec3 else []
    if not intro:
        r.fail("未找到一句话自我介绍小节")
    else:
        sub = intro[0]
        fs = doc.fences_in(sub["start"], sub["end"])
        body = fence_text({"lines": [(0, t) for _, t in
                                     doc.outside_lines(sub["start"], sub["end"])]
                           }) if False else "\n".join(
            t for _, t in doc.outside_lines(sub["start"], sub["end"]))
        fenced = "\n".join(fence_text(f) for f in fs)
        all_txt = body + "\n" + fenced
        if CANON["email"] not in all_txt:
            r.fail("一句话自我介绍/邮件签名中未见固定邮箱")
        if not fs:
            r.fail("一句话自我介绍小节内无围栏（示例应放在围栏内）")
        if not re.search(r"[\u4e00-\u9fa5]{10,}", fenced):
            r.warn("围栏内未见中文示例句")
        if CANON["phone"] not in all_txt:
            r.warn("未见电话 +86 189 2872 4769（邮件签名建议包含）")

    # --- 4. A4 六小节 ---
    r = new_result("编辑-4", "A4 含 01–06 六个编号小节（CN+EN）")
    a4 = mats.get("A4")
    if a4 is None:
        r.fail("未找到 A4 小节")
    else:
        fs = doc.fences_in(a4["start"], a4["end"])
        txt = "\n".join(fence_text(f) for f in fs)
        for n in ["01", "02", "03", "04", "05", "06"]:
            if n not in txt:
                r.fail("A4 文案缺少编号小节 {}".format(n))
        if re.search(r"谁|WHO", txt) and re.search(r"下一步|NEXT", txt):
            pass
        else:
            r.fail("A4 文案缺少「我们是谁 / 下一步」对应小节标题")

    # --- 5. A1 五条独立性承诺要点 ---
    r = new_result("编辑-5", "A1 写出单边收费/不收被核验方费用/方法不披露")
    a1 = mats.get("A1")
    if a1 is None:
        r.fail("未找到 A1 小节")
    else:
        fs = doc.fences_in(a1["start"], a1["end"])
        txt = "\n".join(fence_text(f) for f in fs)
        checks = [
            ("单边收费", r"单边收费|只向买方收费|只向委托方收费|只向买方|只为买方|"
                         r"only\s+the\s+buyer|paid\s+only\s+by\s+the\s+"
                         r"(?:buyer|commissioning)"),
            ("不向被核验方收费", r"不向被核验|不向工厂|不收.*(?:工厂|被核验)|no\s+fee.*(?:from\s+the\s+(?:subject|factory))"),
            ("方法不披露", r"方法不(?:对外)?披露|methodology\s+is\s+not\s+disclosed|not\s+disclosed"),
        ]
        for name, pat in checks:
            if not re.search(pat, txt, re.I):
                r.warn("A1 未明确写出「{}」，请人工确认（§4.1 要求）".format(name))

    # --- 6. A3 hashtag 数量 ---
    r = new_result("编辑-6", "A3 无 hashtag 堆砌（≤1）")
    a3 = mats.get("A3")
    if a3 is None:
        r.fail("未找到 A3 小节")
    else:
        fs = doc.fences_in(a3["start"], a3["end"])
        txt = "\n".join(fence_text(f) for f in fs)
        tags = re.findall(r"#[A-Za-z0-9_]+", txt)
        if len(tags) > 1:
            r.warn("A3 检测到 {} 个 hashtag：{}".format(len(tags), " ".join(tags[:5])))

    # --- 7. 重复段落 ---
    r = new_result("编辑-7", "无跨物料重复段落/啰嗦")
    seen = {}
    for f in doc.fences:
        for _, t in f["lines"]:
            s = norm_ws(t)
            if len(s) < 45:
                continue
            if EMAIL_RE.search(s) or PHONE_RE.search(s):
                continue  # 固定邮箱/电话签名跨物料重复属正常
            key = re.sub(r"[^\w\u4e00-\u9fa5]", "", s)
            if key in seen:
                r.warn("疑似重复段落（{} 与 {}）：{}".format(
                    seen[key], fence_span(f), snippet(s, 50)))
                break
            seen[key] = fence_span(f)

    # --- 8. 中英事实对应（关键数字） ---
    r = new_result("编辑-8", "A1–A4 中英块关键事实对应")
    for key in ["A1", "A2", "A3", "A4"]:
        sub = mats.get(key)
        if sub is None:
            continue
        fs = doc.fences_in(sub["start"], sub["end"])
        cn_txt, en_txt = "", ""
        for f in fs:
            c, e = fence_langs(f)
            if c and not e:
                cn_txt += "\n" + fence_text(f)
            elif e and not c:
                en_txt += "\n" + fence_text(f)
            else:
                cn_txt += "\n" + fence_text(f)
                en_txt += "\n" + fence_text(f)
        if not cn_txt or not en_txt:
            continue
        for token_cn, token_en, name in [
                ("1,800", "1,800", "A-Report 价格"),
                ("3,200", "3,200", "B-Report 价格"),
                ("8–12", "8–12", "报告页数"),
                ("24 小时", "24 hours", "24 小时回复")]:
            if key == "A3" and name == "24 小时回复":
                continue
            if token_cn in cn_txt and token_en not in en_txt:
                r.warn("{} 中文块有「{}」但英文块未见对应「{}」，请人工核对"
                       .format(key, token_cn, token_en))
            if token_en in en_txt and token_cn not in cn_txt:
                r.warn("{} 英文块有「{}」但中文块未见对应「{}」，请人工核对"
                       .format(key, token_en, token_cn))

    # --- 9. 占位残留在非模板区 ---
    r = new_result("编辑-9", "无 TODO/待补 等未完成占位")
    b4_idx = mats.get("B4")
    for lineno, ln in _iter_lines(doc):
        m = TODO_RE.search(ln)
        if not m:
            continue
        if b4_idx and b4_idx["start"] <= lineno - 1 < b4_idx["end"]:
            continue  # B4 方括号占位另行检查
        if "[" in ln and "]" in ln:
            continue  # 方括号占位属授权内容
        r.fail("L{} 出现未完成占位「{}」：{}".format(
            lineno, m.group(0), snippet(ln)))

    # --- 10. 中文标点/半角引号 ---
    r = new_result("编辑-10", "中文块使用全角标点（建议项）")
    for f in doc.fences:
        c, e = fence_langs(f)
        if not c:
            continue
        for _, t in f["lines"]:
            if not line_is_cn(t):
                continue
            if re.search(r'[\u4e00-\u9fa5]"[\u4e00-\u9fa5]', t):
                r.warn("{} 中文块使用半角引号：{}".format(
                    fence_span(f), snippet(t)))
                break
            if re.search(r"[\u4e00-\u9fa5],[\u4e00-\u9fa5]|"
                         r"[\u4e00-\u9fa5]\.[\u4e00-\u9fa5]", t):
                r.warn("{} 中文块使用半角逗号/句号：{}".format(
                    fence_span(f), snippet(t)))
                break

    # --- 11. 物料必备事实要素 ---
    r = new_result("编辑-11", "各物料关键要素抽查（事实/行动号召/邮箱）")
    for key in ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]:
        sub = mats.get(key)
        if sub is None:
            continue
        fs = doc.fences_in(sub["start"], sub["end"])
        txt = "\n".join(fence_text(f) for f in fs)
        if CANON["email"] not in txt:
            r.fail("{} 围栏内未见固定邮箱".format(key))
        if key.startswith("A") and key != "A3":
            if not re.search(r"24\s*(?:小时|hours)", txt, re.I) and key in ("A1", "A4"):
                r.warn("{} 未写 24 小时/24 hours 回复（§4.1 行动号召）".format(key))
        if key in ("A1", "A2", "A4"):
            if not re.search(r"1,800", txt):
                r.warn("{} 未写 A-Report 价格 1,800".format(key))
    # 四、八项：03 邮件签名必须含电话与邮箱；07 术语表四词
    sec4 = doc.section("四")
    if sec4:
        for sub in sec4["subs"]:
            m = re.match(r"^0([1-8])(?![0-9])", sub["title"])
            if not m:
                continue
            n = int(m.group(1))
            body = "\n".join(doc.lines[sub["start"]:sub["end"]])
            if n == 3:
                if CANON["phone"] not in body:
                    r.fail("四-03 邮件签名示例缺少电话 {}".format(CANON["phone"]))
                if CANON["email"] not in body:
                    r.fail("四-03 邮件签名示例缺少邮箱 {}".format(CANON["email"]))
            if n == 7:
                for term in ["verification", "inspection", "audit", "certification"]:
                    if not re.search(term, body, re.I):
                        r.fail("四-07 术语表缺少「{}」释义".format(term))
            if n in (2, 6):
                if not re.search(r"[\u4e00-\u9fa5]", body) or \
                   not re.search(r"\b[A-Za-z]{3,}", body):
                    r.warn("四-0{} 未检测到中英双语示例".format(n))

    # --- 12. 非围栏正文的近似重复句（多文件拼接残留）---
    r = new_result("编辑-12", "非围栏正文无近似重复/拼接残留（中英各一句）")
    prev = None
    for lineno, ln in _iter_lines(doc):
        if (lineno - 1) in doc.inside_fence_idx():
            continue
        s = ln.strip()
        if (not s or s.startswith("#") or s.startswith("|")
                or s.startswith("- ") or s.startswith("* ")):
            prev = None
            continue
        if cjk_count(s) < 10 or nonws_count(s) < 20:
            prev = None
            continue
        if prev is not None:
            ratio = difflib.SequenceMatcher(None, prev[1], s).ratio()
            if ratio >= 0.60:
                r.fail("L{} 与 L{} 中文段落近似重复（相似度 {:.2f}），疑似拼接残留：\n"
                       "      A: {}\n      B: {}".format(
                           prev[0], lineno, ratio, snippet(prev[1], 60),
                           snippet(s, 60)))
        prev = (lineno, s)


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------
def main(argv):
    if len(argv) != 2:
        print("用法: python3 qa/qa_check.py <交付物 markdown 路径>")
        return 2
    path = Path(argv[1])
    if not path.is_file():
        print("错误：文件不存在：{}".format(path))
        return 2
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print("错误：文件不是 UTF-8 编码：{}".format(path))
        return 2
    if not text.strip():
        print("错误：文件为空：{}".format(path))
        return 1

    doc = Doc(path, text)
    check_structure(doc)
    check_fences(doc)
    check_char_decls(doc)
    check_facts(doc)
    check_compliance(doc)
    check_spelling(doc)
    check_editorial(doc)

    n_pass = sum(1 for r in RESULTS if r.status == "PASS")
    n_fail = sum(1 for r in RESULTS if r.status == "FAIL")
    n_warn = sum(1 for r in RESULTS if r.status == "WARN")

    print("=" * 78)
    print("CSCV 推广物料 v2 · QA 自动检查")
    print("文件: {}".format(path))
    print("行数: {}  围栏: {} 对（{} 个标记）  章节: {} 个 ## "
          .format(len(doc.lines), len(doc.fences) // 2, len(doc.fences),
                  len(doc.sections)))
    print("=" * 78)
    for r in RESULTS:
        head = "[{}] {} {}".format(r.status, r.rid, r.title)
        print(head)
        for msg in r.fails:
            print("   ✗ {}".format(msg))
        for msg in r.warns:
            print("   ! {}".format(msg))
    print("-" * 78)
    print("汇总：PASS {} / FAIL {} / WARN {}".format(n_pass, n_fail, n_warn))
    if n_fail:
        print("结论：FAIL —— {} 项必须修复（清单见上 ✗ 行）".format(n_fail))
        return 1
    print("结论：PASS —— 全部自动检查通过（WARN 为建议项，需人工复核）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
