#!/usr/bin/env python3
"""HTML builders for the JFC · CSCV Field Cards (A6 print cards).

Design system v2 (2026-11-25): photo edges fade into the content field and the
nine cards use several layout families instead of one template.

Layout map (promo cards: CN front = art layout, EN back = text back):
  C1  band      (photo band, left edge fades into paper)
  C2  bleed     (full-bleed photo, dark left gradient carries the copy)
  C3  band      (taller band, no accent rule)
  C4  band      (shorter band, accent rule)
  C5  bleed     (full-bleed photo)
  C6  staff     (ink, centred)
  C7  staff-panel (paper card, ink side panel)
  C8  staff     (paper, centred)
  C9  staff-panel (paper card, orange side panel)
"""
from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS = ROOT / "assets" / "cards"
CSS_PATH = ROOT / "cards" / "templates" / "style.css"

MONOGRAM_FALLBACK = {"C6": "JP", "C7": "HV", "C8": "CD", "C9": "JFC"}

VARIANTS = {
    "C1": ("band", "h-md", True),
    "C2": ("bleed", "", False),
    "C3": ("band", "h-lg", False),
    "C4": ("band", "h-sm", True),
    "C5": ("topband", "h-md", False),
    "C6": ("staff", "", False),
    "C7": ("staff-panel", "", False),
    "C8": ("staff", "", False),
    "C9": ("seal", "", False),
}

QUOTES = {
    "C1": ("买方不缺选项，缺的是确认。", "Buyers are not short of options—they are short of confirmation."),
    "C2": ("一份无法被审计的报告不叫证据。", "A report you cannot audit is not evidence."),
    "C3": ("把“我认识谁”，换成“我去过，这是我看到的”。", "Replace “I know someone” with “I went there, and this is what I saw.”"),
    "C4": ("不增编制，按成果验收。", "No added headcount; acceptance by deliverable."),
    "C5": ("我们不卖“放心”，我们卖可以被审计的事实。", "We do not sell reassurance; we sell facts you can audit."),
    "C6": ("一份听起来不错的意见，不叫证据。", "An opinion is not evidence."),
    "C7": ("空白被写下来，报告才可能被审计。", "Write the gaps down and the report can be audited."),
    "C8": ("首次沟通 15 分钟，三样东西就够。", "The first call takes 15 minutes and three things."),
    "C9": ("只写可以核实的内容。", "Write only what can be verified."),
}

SKILLS = {
    "C6": "供应链尽调 · 供应商核验 · 跨境采购 · 商业调查 · 风险评级 · 报告签发",
    "C7": "现场核验 · 工厂评估 · 证据管理 · 质量控制 · 供应链风险 · 访谈",
    "C8": "客户开发 · 需求界定 · B2B 销售 · 跨境贸易 · 转介绍 · 报价",
    "C9": "按实际岗位填写 · 最多 10 项",
}

SKILLS_EN = {
    "C6": "Supply chain due diligence · Supplier verification · Cross-border sourcing · Business investigation · Risk rating · Report sign-off",
    "C7": "Field verification · Factory assessment · Evidence handling · Quality control · Supply chain risk · Interviewing",
    "C8": "Client development · Scoping · B2B sales · Cross-border trade · Referrals · Quotation",
    "C9": "Fill in from the actual role · maximum 10 skills",
}


def esc(value: str) -> str:
    return html.escape(str(value or ""), quote=False)


def css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def _points(card: dict, lang: str) -> str:
    return "".join(
        f'<li><span class="num">{esc(p.get("num") or f"{i:02d}")}</span>'
        f'<span class="txt">{esc(p.get(lang, ""))}</span></li>'
        for i, p in enumerate(card.get("points", []), 1)
    )


def _quote(card: dict, lang: str, extra: str = "") -> str:
    q = card.get(f"quote_{lang}") or QUOTES.get(card.get("code", ""), ("", ""))[0 if lang == "cn" else 1]
    if not q:
        return ""
    return f'<div class="quote {extra}">{esc(q)}</div>'


def _title(text: str, lang: str) -> str:
    text = str(text or "")
    if lang == "cn" and len(text) > 9:
        for sep in ("：", "，"):
            if sep in text:
                head, tail = text.split(sep, 1)
                return f"{esc(head + sep)}<br>{esc(tail)}"
    return esc(text)




def _headline(text: str, lang: str, narrow: bool = False) -> str:
    text = str(text or "")
    if lang == "cn" and narrow and "，" in text:
        head, tail = text.split("，", 1)
        return f"{esc(head + '，')}<br>{esc(tail)}"
    return esc(text)

def _head(card: dict, ink: bool, compact: bool = False) -> str:
    logo = "logo_white.png" if ink else "logo_navy.png"
    logo_path = ASSETS / logo
    series = "JFC · CSCV FIELD CARDS<br>NANSHA · GUANGZHOU"
    series_html = "" if compact else f'<div class="series">{series}</div>'
    return (
        '<div class="head">'
        f'<img class="logo" src="{logo_path.as_uri()}" alt="JAZZFRONT Consulting">'
        f"{series_html}"
        "</div>"
    )


def _foot(card: dict, lang: str, edition: str, narrow: bool = False) -> str:
    contact = card.get(f"footer_{lang}", "")
    if narrow:
        parts = [p.strip() for p in contact.split("·")]
        contact = "<br>".join(esc(p) for p in parts)
    else:
        contact = esc(contact)
    code = f"{card.get('code', '')} / {card.get('total', '09')} · {edition}"
    return (
        '<div class="foot">'
        f'<div class="contact">{contact}</div>'
        f'<div class="code">{esc(code)}</div>'
        "</div>"
    )


def _photo(card: dict, fade: bool = True, height_cls: str = "") -> str:
    photo = card.get("photo")
    if not photo:
        return ""
    path = ASSETS / "images" / photo
    if path.exists():
        src = path.as_uri()
        img = f'<img src="{src}" alt="">'
    else:
        img = (
            '<div style="position:absolute;inset:0;display:flex;align-items:center;'
            'justify-content:center;color:#bbb;font:5pt Menlo;letter-spacing:.2em">'
            f"MISSING IMAGE: {esc(photo)}</div>"
        )
    edge = '<div class="edge-fade"></div>' if fade else ""
    return (
        f'<div class="photo {height_cls}">{img}'
        '<div class="tint"></div>' + edge + '<div class="shade"></div></div>'
    )


def _shell(card: dict, lang: str, cls: str, body: str, extra: str = "") -> str:
    return f"""<!doctype html>
<html lang="{'zh-CN' if lang == 'cn' else 'en'}">
<head><meta charset="utf-8"><style>{css()}</style></head>
<body>
<div class="{cls}">
{body}
{extra}
</div>
</body></html>"""


# --------------------------------------------------------------------------- #
# promo: CN art layouts
# --------------------------------------------------------------------------- #

def band_html(card: dict, lang: str, height_cls: str, rule: bool) -> str:
    ink = card.get("layout", "").endswith("ink")
    rule_html = '<div class="accent-rule"></div>' if rule else ""
    body = f"""<div class="inner">
{_head(card, ink)}
<div class="eyebrow">{esc(card.get(f'eyebrow_{lang}', ''))}</div>
<h1 class="title">{_title(card.get(f'title_{lang}', ''), lang)}</h1>
<div class="sub">{esc(card.get(f'sub_{lang}', ''))}</div>
{rule_html}
{_photo(card, fade=True, height_cls=height_cls)}
<ol class="points">{_points(card, lang)}</ol>
{_foot(card, lang, card.get("edition", "NOV 2026"))}
</div>"""
    return _shell(card, lang, f"card {'ink' if ink else 'paper'} promo band lang-{lang}", body)




def topband_html(card: dict, lang: str, height_cls: str) -> str:
    ink = card.get("layout", "").endswith("ink")
    body = f"""<div class="inner">
{_head(card, ink)}
{_photo(card, fade=True, height_cls=height_cls)}
<div class="eyebrow">{esc(card.get(f'eyebrow_{lang}', ''))}</div>
<h1 class="title">{_title(card.get(f'title_{lang}', ''), lang)}</h1>
<div class="sub">{esc(card.get(f'sub_{lang}', ''))}</div>
<ol class="points">{_points(card, lang)}</ol>
{_foot(card, lang, card.get("edition", "NOV 2026"))}
</div>"""
    return _shell(card, lang, f"card {'ink' if ink else 'paper'} promo topband lang-{lang}", body)

def bleed_html(card: dict, lang: str) -> str:
    photo = card.get("photo")
    path = ASSETS / "images" / photo if photo else None
    img = f'<img src="{path.as_uri()}" alt="">' if path and path.exists() else ""
    body = f"""<div class="photo-full">{img}<div class="tint"></div><div class="legi"></div></div>
<div class="inner">
{_head(card, True)}
<div class="eyebrow">{esc(card.get(f'eyebrow_{lang}', ''))}</div>
<h1 class="title">{_title(card.get(f'title_{lang}', ''), lang)}</h1>
<div class="sub">{esc(card.get(f'sub_{lang}', ''))}</div>
<ol class="points">{_points(card, lang)}</ol>
{_foot(card, lang, card.get("edition", "NOV 2026"))}
</div>"""
    return _shell(card, lang, f"card ink promo bleed lang-{lang}", body)


# --------------------------------------------------------------------------- #
# promo: EN text back (no photo, gradient rule + ghost code)
# --------------------------------------------------------------------------- #

def back_html(card: dict, lang: str) -> str:
    ink = card.get("layout", "").endswith("ink")
    body = f"""<div class="inner">
{_head(card, ink)}
<div class="eyebrow">{esc(card.get(f'eyebrow_{lang}', ''))}</div>
<h1 class="title">{esc(card.get(f'title_{lang}', ''))}</h1>
<div class="sub">{esc(card.get(f'sub_{lang}', ''))}</div>
<div class="grad-band"></div>
{_quote(card, lang)}
<div class="bottom-block">
<ol class="points">{_points(card, lang)}</ol>
</div>
{_foot(card, lang, card.get("edition", "NOV 2026"))}
</div>
<div class="ghost-code">{esc(card.get('code', ''))}</div>"""
    return _shell(card, lang, f"card {'ink' if ink else 'paper'} promo back lang-{lang}", body)


# --------------------------------------------------------------------------- #
# staff cards
# --------------------------------------------------------------------------- #

def _staff_body(card: dict, lang: str, narrow: bool = False) -> str:
    ink = card.get("layout", "").endswith("ink")
    code = card.get("code", "")
    mono = card.get("monogram") or MONOGRAM_FALLBACK.get(code, "JFC")
    label = "负责范围 / SCOPE" if lang == "cn" else "SCOPE / 负责范围"
    skills = card.get(f"skills_{lang}") or (SKILLS if lang == "cn" else SKILLS_EN).get(code, "")
    note = card.get(f"note_{lang}")
    note_html = f'<div class="note">{esc(note)}</div>' if note else ""
    skills_html = (
        f'<div class="skills-label">{"专长 / EXPERTISE" if lang == "cn" else "EXPERTISE / 专长"}</div>'
        f'<div class="skills-line">{esc(skills)}</div>'
    ) if skills else ""
    return f"""<div class="inner{' panel-right' if narrow else ''}">
{_head(card, ink, compact=narrow)}
<div class="staff-top">
  <div class="who">
    <div class="role-eyebrow">{esc(card.get(f'role_{lang}', ''))}</div>
    <div class="staff-name">{esc(card.get(f'name_{lang}', ''))}</div>
  </div>
  {'' if narrow else f'<div class="monogram">{esc(mono)}</div>'}
</div>
{'' if narrow else f'<div class="bigmark">{esc(mono)}</div>'}
{'' if narrow else '<div class="spine">JFC · CSCV · FIELD CARDS · NANSHA</div>'}
<div class="staff-headline">{_headline(card.get(f'headline_{lang}', ''), lang, narrow)}</div>
{_quote(card, lang, 'staff-quote')}
{skills_html}
<div class="staff-bottom">
<div class="list-label">{label}</div>
<ol class="points staff-points">{_points(card, lang)}</ol>
</div>
{note_html}
{_foot(card, lang, card.get('edition', 'NOV 2026'), narrow=narrow)}
</div>"""


def staff_html(card: dict, lang: str) -> str:
    ink = card.get("layout", "").endswith("ink")
    return _shell(card, lang, f"card {'ink' if ink else 'paper'} staff lang-{lang}",
                  _staff_body(card, lang))


def staff_panel_html(card: dict, lang: str, orange: bool = False) -> str:
    ink = card.get("layout", "").endswith("ink")
    code = card.get("code", "")
    mono = card.get("monogram") or MONOGRAM_FALLBACK.get(code, "JFC")
    panel_cls = "panel orange" if orange else "panel"
    body = f"""<div class="{panel_cls}">
  <div class="mono">{esc(mono)}</div>
  <div class="vlabel">JFC · FIELD CARDS</div>
</div>
{_staff_body(card, lang, narrow=True)}"""
    return _shell(card, lang, f"card {'ink' if ink else 'paper'} staff-panel lang-{lang}", body)


# --------------------------------------------------------------------------- #



def seal_html(card: dict, lang: str) -> str:
    home = "" if lang == "cn" else ""
    label = "负责范围 / SCOPE" if lang == "cn" else "SCOPE / 负责范围"
    skills = card.get(f"skills_{lang}") or (SKILLS if lang == "cn" else SKILLS_EN).get(card.get("code", ""), "")
    note = card.get(f"note_{lang}")
    note_html = f'<div class="note">{esc(note)}</div>' if note else ""
    mono = card.get("monogram") or "JFC"
    return f"""<div class="inner">
{_head(card, False)}
<div class="seal"><div class="mono">{esc(mono)}</div></div>
<div class="role-eyebrow">{esc(card.get(f'role_{lang}', ''))}</div>
<div class="staff-name">{esc(card.get(f'name_{lang}', ''))}</div>
<div class="staff-headline">{_headline(card.get(f'headline_{lang}', ''), lang, False)}</div>
{_quote(card, lang, 'seal-quote')}
<div class="seal-cols">
  <div class="seal-col">
    <div class="list-label">{label}</div>
    <ol class="points">{_points(card, lang)}</ol>
  </div>
  <div class="seal-col">
    <div class="skills-label">{"专长 / EXPERTISE" if lang == "cn" else "EXPERTISE / 专长"}</div>
    <div class="skills-line">{esc(skills)}</div>
  </div>
</div>
{note_html}
{_foot(card, lang, card.get('edition', 'NOV 2026'))}
</div>
<div class="frame"></div>"""

def build_html(card: dict, lang: str, edition: str = "NOV 2026") -> str:
    card = dict(card)
    card["edition"] = edition
    variant, height_cls, rule = VARIANTS.get(card.get("code", ""), ("band", "h-md", True))
    if variant == "staff":
        return staff_html(card, lang)
    if variant == "seal":
        return _shell(card, lang, f"card paper seal lang-{lang}", seal_html(card, lang))
    if variant == "staff-panel":
        return staff_panel_html(card, lang, orange=(card.get("code") == "C9"))
    if lang == "en":
        return back_html(card, lang)
    if variant == "bleed":
        return bleed_html(card, lang)
    if variant == "topband":
        return topband_html(card, lang, height_cls)
    return band_html(card, lang, height_cls, rule)
