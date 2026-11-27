#!/usr/bin/env python3
"""Lead self-check for the assembled CSCV kit (independent of the QA teammate)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "deliverables" / "CSCV_推广物料_纯文本_CN-EN_v2.md"
text = MD.read_text(encoding="utf-8")
lines = text.split("\n")

problems: list[str] = []
notes: list[str] = []


def check(cond, msg):
    if not cond:
        problems.append(msg)


def boxes(sec: str):
    return re.findall(r"```\n(.*?)```", sec, re.S)


def cn_len(s):
    return len(re.sub(r"\s", "", s))


# ---------- 1. structure ----------
required = [
    "## 〇、事实表（先冻结）",
    "## 一、物料总览",
    "## 二、四版资料卡",
    "## 三、员工资料包",
    "## 四、八项新增建议",
    "## 五、执行建议",
    "## 六、使用与合规提醒",
    "## 七、团队清单",
]
for r in required:
    check(r in text, f"missing section: {r}")
for tag in ("A1", "A2", "A3", "A4"):
    check(f"### {tag}" in text, f"missing card {tag}")
for tag in ("B1", "B2", "B3", "B4"):
    check(f"### {tag}" in text, f"missing staff profile {tag}")
for i in range(1, 9):
    check(f"### 0{i} " in text, f"missing suggestion 0{i}")
fences = text.count("```")
check(fences % 2 == 0, f"unbalanced code fences: {fences}")
check(text.count("\n| F0 |") == 1, "checklist F0 row missing")
check(len(re.findall(r"^\| [A-Z]\d+ \|", text, re.M)) >= 18, "checklist rows missing")

# ---------- 2. character counts ----------
def split_sections(pattern):
    parts = re.split(rf"\n(?=### {pattern})", text)
    return parts[1:]

card_limits = {"A1": (1100, 2600), "A2": (700, 1200), "A3": (140, 280), "A4": (650, 1450)}
for sec in split_sections(r"A\d"):
    tag = sec.split()[1]
    m = re.search(r"字符数 Characters: 中文 (\d+) / English (\d+)", sec)
    b = boxes(sec)
    if not m or len(b) < 2:
        problems.append(f"{tag}: char-count line or boxes missing")
        continue
    cn, en = cn_len(b[0]), len(b[1].strip())
    if abs(cn - int(m.group(1))) > 0:
        problems.append(f"{tag}: CN declared {m.group(1)} actual {cn}")
    if abs(en - int(m.group(2))) > 0:
        problems.append(f"{tag}: EN declared {m.group(2)} actual {en}")
    if tag in card_limits:
        cn_max, en_max = card_limits[tag]
        check(cn <= cn_max, f"{tag}: CN {cn} > {cn_max}")
        check(en <= en_max, f"{tag}: EN {en} > {en_max}")

for sec in split_sections(r"B\d"):
    tag = sec.split()[1]
    b = boxes(sec)
    if len(b) < 6:
        problems.append(f"{tag}: expected 6 boxes, got {len(b)}")
        continue
    m = re.search(r"字符数 Characters: 中文 (\d+) / English (\d+)", sec)
    hm = re.search(r"Headline 字符数 / Headline characters: 中文 (\d+) / English (\d+)", sec)
    about_cn, about_en = cn_len(b[1]), len(b[2].strip())
    hl = [x for x in b[0].split("\n") if x.strip()]
    hcn, hen = cn_len(hl[0]), len(" ".join(hl[1:]))
    if m:
        if (about_cn, about_en) != (int(m.group(1)), int(m.group(2))):
            problems.append(f"{tag}: About declared {m.group(1)}/{m.group(2)} actual {about_cn}/{about_en}")
    else:
        problems.append(f"{tag}: no About char count line")
    if hm:
        if (hcn, hen) != (int(hm.group(1)), int(hm.group(2))):
            problems.append(f"{tag}: Headline declared {hm.group(1)}/{hm.group(2)} actual {hcn}/{hen}")
    else:
        problems.append(f"{tag}: no headline char count line")
    check(hcn <= 220 and hen <= 220, f"{tag}: headline over 220 ({hcn}/{hen})")
    check(420 <= about_cn <= 560, f"{tag}: About CN {about_cn} outside 420-560")
    check(650 <= about_en <= 900, f"{tag}: About EN {about_en} outside 650-900")

# ---------- 3. facts ----------
allowed_money = {
    "1,800–3,000", "3,200–4,500", "4,500", "7,200", "1,500", "1,440",
    "6,000–15,000", "20,000",
}
for m in re.finditer(r"RMB ([0-9][0-9,–\-]*)", text):
    val = m.group(1)
    if val not in allowed_money:
        problems.append(f"unexpected RMB amount: RMB {val}")
for m in re.finditer(r"([0-9][0-9,]*(?:–[0-9][0-9,]*)?)\s*元", text):
    val = m.group(1)
    if val not in allowed_money:
        problems.append(f"unexpected CNY amount: {val} 元")

check("+86 189 2872 4769" in text, "phone missing")
check(text.count("JFC.Consulting@outlook.com") >= 20, "email appears too rarely")
check("广州市南沙区凯翔路 1 号 408 房（自编南塔 401）" in text, "address missing")
prohibition_markers = ("不写", "不使用", "不称", "Never write", "Never call", "Never use",
                        "Do not publish", "☐ 无", "stay in internal", "不对外", "不引用", "Do not cite")
for bad in ("建塔", "建滔", "73%", "20–100", "100% 安全", "零风险"):
    for i, line in enumerate(lines, 1):
        if bad in line and not any(mk in line for mk in prohibition_markers):
            problems.append(f"forbidden text: {bad} (line {i}: {line[:60]})")

# ---------- 4. compliance terms ----------
for bad in ("！", "!"):
    for i, line in enumerate(lines, 1):
        if bad in line:
            problems.append(f"exclamation at line {i}: {line[:60]}")
for term in ("保证", "guarantee", "Guarantee", "最佳", "领先", "第一", "唯一"):
    hits = [i for i, line in enumerate(lines, 1) if term in line]
    if hits:
        notes.append(f"review term {term} at lines {hits}")
if "认证" in text or "certification" in text.lower():
    notes.append("review: 认证/certification occurrences (independence/glossary context expected)")

# ---------- 5. British spellings ----------
british = {
    "standardise": "standardize", "standardised": "standardized", "organisation": "organization",
    "organise": "organize", "centre": "center", "colour": "color", "favour": "favor",
    "labour": "labor", "analyse": "analyze", "programme": "program", "behaviour": "behavior",
    "licence": "license", "towards": "toward", "defence": "defense", "utilise": "utilize",
    "recognise": "recognize", "summarise": "summarize", "prioritise": "prioritize",
    "optimise": "optimize", "authorise": "authorize", "minimise": "minimize",
    "maximise": "maximize", "apologise": "apologize", "practise": "practice",
}
low = text.lower()
for b in british:
    if re.search(r"\b" + b, low):
        problems.append(f"British spelling: {b} -> {british[b]}")

# ---------- 6. placeholder sanity ----------
check("[姓名]" in text and "[Name]" in text, "B4 name placeholder missing")
check("[职位]" in text and "[Role]" in text, "B4 role placeholder missing")

print("=" * 70)
print(f"CHECKS: {len(problems)} problem(s), {len(notes)} note(s)")
for p in problems:
    print("FAIL:", p)
for n in notes:
    print("NOTE:", n)
if not problems:
    print("ALL AUTOMATED CHECKS PASS")
sys.exit(1 if problems else 0)
