# -*- coding: utf-8 -*-
"""Approved bilingual copy for every banner.

Rules
- Facts and claims only come from JFC's frozen fact sheet (CSCV Service
  Definition v2 / November 2026) and the official company profile. Do not add
  prices, clients, cases, certifications or promises to a banner.
- Chinese first; English is a paired translation below / beside it, never
  mixed inside one line.
- Short and quiet: a banner is a sign, not a paragraph.
"""

JFC_COPY = {
    "kicker": ("JAZZFRONT CONSULTING™ · 广州南沙", "JAZZFRONT CONSULTING™ · GUANGZHOU NANSHA, CHINA"),
    # corporate line used on the official company profile card
    "headline_cn": "让跨境合作，从确认开始。",
    "headline_en": "Cross-border work starts with confirmation.",
    # official service portfolio positioning (four lines)
    "positioning_cn": "精品国际咨询 · 全球准备 · 职业发展 · 中小企业赋能",
    "positioning_en": "Boutique international consulting · Global readiness · Career advancement · SME empowerment",
    "meta_cn": "中国广州南沙 · 22.80°N 113.53°E",
    "meta_en": "Nansha, Guangzhou, China · 22.80°N 113.53°E",
    "contact": "JFC.Consulting@outlook.com",
    "service_cn": "中国供应链核验（CSCV）· 专为无法亲临现场的买家设计",
    "service_en": "China Supply Chain Verification (CSCV) · For buyers who cannot be on site",
}

# ---------------------------------------------------------------- CSCV
# Source: Gordon's revised CSCV Profile Card copy (2026-11-25), shipped as the
# official CSCV card set on 2026-11-26 with prices converted to USD. Banners
# never show prices; the positioning/claims below are the latest approved lines.


CSCV_COPY = {
    "kicker_cn": "CSCV · 中国供应链核验",
    "kicker_en": "CHINA SUPPLY CHAIN VERIFICATION",
    # latest CSCV service-card title (Gordon copy, 2026-11-25), with Levi's
    # banner wording 付款之前 → 采购之前 applied
    "headline_cn": "采购之前您所需的事实，由我们亲临现场核验。",
    "headline_en": "The facts you need before procurement, verified on site by us.",
    # short line built from the service definition's own three questions
    "short_cn": "采购之前，到现场核实主体、产能、风险。",
    "short_en": "On-site verification before procurement: entity, capacity, risk.",
    "three_cn": "主体 · 产能 · 风险",
    "three_en": "ENTITY · CAPACITY · RISK",
    "proof_cn": "只向买家收费",
    "proof_en": "PAID ONLY BY THE BUYER",
    # latest CSCV evidence-card title (Gordon copy, 2026-11-25)
    "scope_cn": "每一项发现均有可审计的证据支撑",
    "scope_en": "EVERY FINDING BACKED BY AUDITABLE EVIDENCE",
    "stamp": "ON-SITE VERIFIED · 现场核验",
    "serial": "CSCV / FIELD DOSSIER · NOV 2026",
    "meta": "JAZZFRONT Consulting™ · CSCV · JFC.Consulting@outlook.com",
}
