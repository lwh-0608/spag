# -*- coding: utf-8 -*-
"""Brand tokens for the JFC / CSCV social banner kit.

Two brand systems live in this kit. They intentionally look different — the
request asked for JFC *company* brand and CSCV *visual* brand banners:

A. JFC — "INSTITUTIONAL BLUE"
   The official company look already used in JFC's company profile and service
   portfolio: deep navy field, ice-blue type, the official logo blue, and the
   thin green signal rule. Typography is Avenir Next + PingFang SC.

B. CSCV — "FIELD DOSSIER"
   The CSCV visual brand designed in November 2026 for the CSCV service
   definition and deck: warm paper, ink, signal orange, verification green,
   registration marks, stamps and Archivo / Inter / JetBrains Mono type.
   (See bizmodel-redesign-8d2bab8a14d8/design/README.md for the parent system.)

The official logo is never recoloured. Use the colour lockup on light grounds
and the white lockup on ink / navy grounds.
"""

JFC = {
    "key": "jfc",
    "name_cn": "JFC 公司品牌",
    "name_en": "JFC company brand",
    "style_name_cn": "机构蓝",
    "style_name_en": "Institutional Blue",
    # grounds
    "ground": "#0A295B",       # navy — primary banner ground
    "ground_deep": "#061A3B",  # navy gradient end
    "ice": "#E7F0FD",          # pale ice-blue (portfolio cover background)
    # signals
    "blue": "#2C63E0",         # official logo blue
    "green": "#2E9D74",        # thin signal rule on official materials
    # type
    "ink": "#0A0D10",          # on light grounds only
    "muted": "#9DB4D8",        # secondary type on navy
    "muted_deep": "#7C93B8",
    "hairline": "rgba(231, 240, 253, 0.20)",
    "white": "#FFFFFF",
    # typefaces
    "font_display": '"Avenir Next", "Helvetica Neue", Arial, sans-serif',
    "font_text": '"Avenir Next", "Helvetica Neue", Arial, sans-serif',
    "font_mono": '"SF Mono", "JetBrains Mono", Menlo, monospace',
    "font_cn": '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
}

CSCV = {
    "key": "cscv",
    "name_cn": "CSCV 视觉品牌",
    "name_en": "CSCV visual brand",
    "style_name_cn": "现场档案",
    "style_name_en": "Field Dossier",
    # grounds
    "ink": "#0A0D10",
    "ink_2": "#12161B",
    "paper": "#F1EDE3",
    "paper_2": "#E7E1D3",
    # signals
    "orange": "#FF4D00",
    "acid": "#C8F26B",
    "verify": "#37E08A",
    "muted": "#7E838B",
    "line": "rgba(10, 13, 16, 0.16)",
    "line_strong": "rgba(10, 13, 16, 0.32)",
    "line_inv": "rgba(241, 237, 227, 0.20)",
    "line_inv_strong": "rgba(241, 237, 227, 0.40)",
    # typefaces (woff2 vendored, OFL — see assets/fonts/OFL.txt)
    "font_display": '"Archivo", "Helvetica Neue", Arial, sans-serif',
    "font_text": '"Inter", "Helvetica Neue", Arial, sans-serif',
    "font_mono": '"JetBrains Mono", "SF Mono", Menlo, monospace',
    "font_cn": '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
}

BRANDS = {"jfc": JFC, "cscv": CSCV}
