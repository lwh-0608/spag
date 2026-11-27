# -*- coding: utf-8 -*-
"""Build the review previews: platform mockups (before / after) and the contact sheet.

    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
        banners/kit/tools/preview.py

Outputs:
    preview/mockups/<brand>-<format>-before-after.png
    preview/contact-sheet.png
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
KIT = ROOT / "banners" / "kit"
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(KIT / "tools"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from platform_specs import ORDER, PLATFORMS  # noqa: E402
import render as R  # noqa: E402

BRANDS = ["jfc", "cscv"]
CARD_W = 1000
SHEET_W = 2160

IDENTITY = {
    "jfc": {
        "name": "JAZZFRONT Consulting™",
        "sub_cn": "中国供应链核验 · 专为无法亲临现场的买家设计",
        "sub_en": "China Supply Chain Verification · For buyers who cannot be on site.",
        "meta": "Nansha, Guangzhou, China · 广州南沙",
        "tag": "Boutique international consulting",
        "logo": "banners/kit/assets/logo-color.png",
        "avatar_round": True,
    },
    "cscv": {
        "name": "CSCV · 中国供应链核验",
        "sub_cn": "专为无法亲临现场的买家设计。",
        "sub_en": "For buyers who cannot be on site.",
        "meta": "JAZZFRONT Consulting™ · CSCV · Nansha, Guangzhou",
        "tag": "Field dossier / 现场档案",
        "logo": "banners/kit/assets/logo-color.png",
        "avatar_round": True,
    },
}

SUBTITLE = {
    "linkedin-personal": ("个人主页 / Personal profile", "领英 LinkedIn"),
    "linkedin-company": ("公司主页 / Company page", "领英 LinkedIn"),
    "x-header": ("个人资料页 / Profile", "X (Twitter)"),
    "facebook-cover": ("主页 / Page", "Facebook"),
    "youtube-channel": ("频道首页 / Channel", "YouTube"),
}


def _banner_rel(brand: str, fmt: str) -> str:
    return f"../../../banners/{brand}/png/{fmt}.png"


def mockup_html(brand: str, fmt: str) -> str:
    spec = PLATFORMS[fmt]
    w, h = spec["canvas"]
    banner_h = round(CARD_W * h / w)
    idn = IDENTITY[brand]
    state_label, platform = SUBTITLE[fmt]
    avatar_cls = "" if idn["avatar_round"] else " avatar--square"
    src_before = f"<div class='banner banner--empty' style='height:{banner_h}px'><span>未设置横幅 · No banner set</span></div>"
    src_after = (
        f"<div class='banner' style='height:{banner_h}px'>"
        f"<img src='{_banner_rel(brand, fmt)}' alt='{brand} {fmt}'></div>"
    )

    def column(state: str, banner: str) -> str:
        return f"""
      <div class="col">
        <p class="state state--{state}">{'BEFORE' if state == 'before' else 'AFTER'} · {'平台默认（无横幅）' if state == 'before' else '套用模板'}</p>
        <div class="card">
          {banner}
          <div class="identity">
            <div class="avatar{avatar_cls}"><img src="../../../{idn['logo']}" alt="logo"></div>
            <h1>{idn['name']}</h1>
            <p class="sub">{idn['sub_cn']}</p>
            <p class="sub">{idn['sub_en']}</p>
            <p class="meta">{idn['meta']}</p>
            <span class="tag">{idn['tag']}</span>
          </div>
        </div>
      </div>"""

    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="mockup.css">
</head><body>
<div class="sheet">
  <div class="sheet-head">
    <div class="sheet-title">{platform} · {state_label} — {BRANDS.index(brand) and 'CSCV' or 'JFC'}</div>
    <div class="sheet-note">界面示意图 · illustrative UI mockup, not an actual platform screenshot</div>
  </div>
  <div class="pair">
    {column('before', src_before)}
    {column('after', src_after)}
  </div>
  <p class="caption">左：平台默认状态，未上传横幅。<b>Before:</b> platform default, no banner uploaded.
  右：套用本套模板后的效果。<b>After:</b> with the kit template applied. 平台界面为示意，非真实截图。</p>
</div>
</body></html>"""


def build_mockups(browser):
    out = ROOT / "preview" / "mockups"
    src = out / "src"
    src.mkdir(parents=True, exist_ok=True)
    html_path = src / "mockup.css"
    if not html_path.exists():
        raise SystemExit("mockup.css missing")
    made = []
    for brand in BRANDS:
        for fmt in ORDER:
            png = ROOT / "banners" / brand / "png" / f"{fmt}.png"
            if not png.exists():
                continue
            spec = PLATFORMS[fmt]
            w, h = spec["canvas"]
            banner_h = round(CARD_W * h / w)
            sheet_h = 36 + 60 + banner_h + 300 + 60
            html = src / f"{brand}-{fmt}.html"
            html.write_text(mockup_html(brand, fmt), encoding="utf-8")
            dest = out / f"{brand}-{fmt}-before-after.png"
            R.render_page(browser, html, dest, SHEET_W, sheet_h, dsf=2)
            made.append(dest)
    return made


def _font(size: int, cn: bool = False, bold: bool = False):
    """macOS system fonts that PIL can actually load (Hiragino Sans GB carries CJK)."""
    if cn:
        p = "/System/Library/Fonts/Hiragino Sans GB.ttc"
        idx = 2 if bold else 0
    else:
        p = "/System/Library/Fonts/Avenir Next.ttc"
        idx = 0
    try:
        return ImageFont.truetype(p, size, index=idx)
    except Exception:
        try:
            return ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", size)
        except Exception:
            return ImageFont.load_default()


def contact_sheet():
    cells = []
    for brand in BRANDS:
        for fmt in ORDER:
            png = ROOT / "banners" / brand / "png" / f"{fmt}.png"
            if png.exists():
                cells.append((brand, fmt, png))
    if not cells:
        raise SystemExit("no banners rendered yet")
    pad = 40
    cell_w = (2400 - 2 * pad) // 5
    img_box_w, img_box_h = cell_w - 24, 190
    row_h = 300
    header_h = 250
    rows = len(BRANDS)
    H = header_h + rows * (row_h + 46) + 60
    sheet = Image.new("RGB", (2400, H), "#14171c")
    d = ImageDraw.Draw(sheet)

    f_title = _font(54, bold=True)
    f_title_cn = _font(42, cn=True, bold=True)
    f_sub = _font(21)
    f_sub_cn = _font(19, cn=True)
    f_brand = _font(28, bold=True)
    f_brand_cn = _font(26, cn=True, bold=True)
    f_cell = _font(15)
    f_cell_cn = _font(15, cn=True)

    d.text((pad, 54), "JFC / CSCV", font=f_title, fill="#e7f0fd")
    d.text((pad, 122), "官方社媒背景横幅模板 · Social Banner Template Kit", font=f_title_cn, fill="#ffffff")
    d.text((pad, 182), "5 formats × 2 brands · LinkedIn / X / Facebook / YouTube · November 2026 · v1.2",
           font=f_sub, fill="#9db4d8")

    brand_names = {"jfc": ("JFC 公司品牌 · 机构蓝", "JFC company brand · Institutional Blue"),
                   "cscv": ("CSCV 视觉品牌 · 现场档案", "CSCV visual brand · Field Dossier")}
    for row, brand in enumerate(BRANDS):
        y = header_h + row * (row_h + 46)
        d.text((pad, y), brand_names[brand][0], font=f_brand_cn, fill={"jfc": "#7ea6ff", "cscv": "#ff7a45"}[brand])
        d.text((pad + 470, y + 8), brand_names[brand][1], font=f_cell, fill="#8a94a3")
        row_cells = [c for c in cells if c[0] == brand]
        for col, (_, fmt, png) in enumerate(row_cells):
            x = pad + col * cell_w
            im = Image.open(png).convert("RGB")
            im.thumbnail((img_box_w, img_box_h), Image.LANCZOS)
            bx = x + (cell_w - 24 - im.width) // 2
            by = y + 48 + (img_box_h - im.height) // 2
            sheet.paste(im, (bx, by))
            spec = PLATFORMS[fmt]
            d.rectangle([x + 2, y + 44, x + cell_w - 22, y + 48 + img_box_h + 4],
                        outline="#2b3038", width=1)
            d.text((x + 2, y + 48 + img_box_h + 16),
                   f"{spec['name_cn']}", font=f_cell_cn, fill="#c9d2de")
            d.text((x + 2, y + 48 + img_box_h + 40),
                   f"{spec['canvas'][0]}×{spec['canvas'][1]} px · PNG", font=f_cell, fill="#7e8794")
    d.text((pad, H - 48),
           "所有尺寸已按平台安全区校验；文件与重新生成方式见 GUIDE。All sizes checked against platform safe areas — see the guide.",
           font=_font(19, cn=True), fill="#7e8794")
    out = ROOT / "preview" / "contact-sheet.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, optimize=True)
    return out


def main() -> int:
    preview = ROOT / "preview"
    (preview / "mockups").mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            made = build_mockups(browser)
        finally:
            browser.close()
    print(f"mockups: {len(made)}")
    print("contact sheet:", contact_sheet())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
