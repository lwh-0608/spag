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
    "service_cn": "中国供应链核验（CSCV）· 只为买方工作",
    "service_en": "China Supply Chain Verification (CSCV) · Paid only by the buyer",
}

CSCV_COPY = {
    "kicker_cn": "CSCV · 中国供应链核验",
    "kicker_en": "CHINA SUPPLY CHAIN VERIFICATION",
    # line used on the official CSCV service card
    "headline_cn": "付款之前，把「能不能生产」变成事实。",
    "headline_en": "Before payment, turn “can they produce?” into a fact.",
    # short line built from the service definition's own three questions
    "short_cn": "付款之前，到现场核实主体、产能、风险。",
    "short_en": "On-site verification before payment: entity, capacity, risk.",
    "three_cn": "主体 · 产能 · 风险",
    "three_en": "ENTITY · CAPACITY · RISK",
    "proof_cn": "只向买方收费",
    "proof_en": "PAID ONLY BY THE BUYER",
    "scope_cn": "每份报告逐条列出未核验项",
    "scope_en": "EVERY REPORT LISTS WHAT COULD NOT BE VERIFIED",
    "stamp": "ON-SITE VERIFIED · 现场核验",
    "serial": "CSCV / FIELD DOSSIER · NOV 2026",
    "meta": "JAZZFRONT Consulting™ · CSCV · JFC.Consulting@outlook.com",
}
