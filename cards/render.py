#!/usr/bin/env python3
"""Render the JFC · CSCV Field Cards (9 A6 cards, front CN / back EN).

Pipeline
--------
cards/data.json + cards/templates/{style.css,layouts.py}
    -> HTML (Chromium via Playwright) -> per-side PDF at 111×154mm (A6 + 3mm bleed)
    -> 150dpi preview PNGs
    -> CSCV_FieldCards_v1_print.pdf (18 pages)
    -> A4_office_proof.pdf (4-up, 96%, for in-house proofing)
    -> preview/all_fronts.png, all_backs.png, all_cards_preview.png

Run with the framework Python 3.13:
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 cards/render.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "cards" / "templates"))
import layouts  # noqa: E402

DATA = ROOT / "cards" / "data.json"
if len(sys.argv) > 1:
    DATA = Path(sys.argv[1]).resolve()
OUT_PRINT = ROOT / "deliverables" / "cards" / "print"
OUT_PREVIEW = ROOT / "deliverables" / "cards" / "preview"
TMP = ROOT / "cards" / "render" / "tmp"
TRIMMED_PNG = ROOT / "cards" / "render" / "trimmed"

PAGE_W_MM, PAGE_H_MM = 111, 154
OVERFLOW = []
TRIM_W_MM, TRIM_H_MM = 105, 148
BLEED_MM = 3


def load_data() -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = data["cards"]
    for c in cards:
        c.setdefault("total", f"{len(cards):02d}")
    return data


def render_side(page, card: dict, lang: str, edition: str, out_pdf: Path) -> None:
    html = layouts.build_html(card, lang, edition)
    tmp_html = TMP / f"{card['code']}_{lang}.html"
    tmp_html.write_text(html, encoding="utf-8")
    page.goto(tmp_html.as_uri(), wait_until="load")
    page.evaluate(
        """async () => {
            await document.fonts.ready;
            await Promise.all(Array.from(document.images).map(img =>
                img.complete ? Promise.resolve() : new Promise(r => {
                    img.onload = r; img.onerror = r;
                })
            ));
        }"""
    )
    info = page.evaluate(
        """() => {
            const inner = document.querySelector('.inner');
            const ir = inner.getBoundingClientRect();
            const skip = new Set(['photo', 'ruleband', 'grad-band', 'bigmark', 'spine', 'ghost-code']);
            const bad = [];
            inner.querySelectorAll('*').forEach(el => {
                if ([...el.classList].some(c => skip.has(c))) return;
                if (el.closest('.photo')) return;
                const r = el.getBoundingClientRect();
                if (r.height === 0 && r.width === 0) return;
                if (r.bottom > ir.bottom + 1 || r.right > ir.right + 1 ||
                    r.left < ir.left - 1 || r.top < ir.top - 1) {
                    bad.push({
                        tag: (el.className || el.tagName).toString().slice(0, 24),
                        text: (el.textContent || '').trim().slice(0, 28),
                        dBottom: Math.round(r.bottom - ir.bottom),
                        dRight: Math.round(r.right - ir.right),
                    });
                }
            });
            return {
                innerH: Math.round(ir.height),
                innerScroll: inner.scrollHeight,
                bad: bad.slice(0, 6),
                missing: document.documentElement.innerHTML.includes('MISSING IMAGE'),
            };
        }"""
    )
    OVERFLOW.append((card["code"], lang, info))
    page.pdf(
        path=str(out_pdf),
        width=f"{PAGE_W_MM}mm",
        height=f"{PAGE_H_MM}mm",
        margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        print_background=True,
        prefer_css_page_size=True,
    )


def pdf_to_png(pdf_path: Path, png_path: Path, dpi: int = 150) -> Image.Image:
    doc = fitz.open(pdf_path)
    pix = doc[0].get_pixmap(dpi=dpi, colorspace=fitz.csRGB)
    pix.save(str(png_path))
    doc.close()
    return Image.open(png_path)


def crop_bleed(img: Image.Image, dpi: int) -> Image.Image:
    px = round(BLEED_MM / 25.4 * dpi)
    return img.crop((px, px, img.width - px, img.height - px))


def contact_sheet(images: list[Image.Image], cols: int, out: Path, label: str = "") -> None:
    if not images:
        return
    w, h = images[0].size
    pad = 24
    head = 52 if label else 0
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w + (cols + 1) * pad, rows * h + (rows + 1) * pad + head), "white")
    draw = ImageDraw.Draw(sheet)
    if label:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 30)
        except Exception:
            font = ImageFont.load_default()
        draw.text((pad, 12), label, fill="#111", font=font)
    for i, im in enumerate(images):
        r, c = divmod(i, cols)
        x = pad + c * (w + pad)
        y = head + pad + r * (h + pad)
        sheet.paste(im, (x, y))
        draw.rectangle([x, y, x + w, y + h], outline="#cccccc", width=2)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def build_a4_proof(sides: dict[str, dict[str, Image.Image]], cards: list[dict]) -> None:
    """4 cards per A4 page at 96% scale, fronts then backs; for office proofing only."""
    MM = 72 / 25.4
    scale = 0.96
    card_w = TRIM_W_MM * scale * MM
    card_h = TRIM_H_MM * scale * MM
    gutter = 2.0 * MM
    margin_x = 2.0 * MM
    top = 9.0 * MM
    page_w, page_h = 210 * MM, 297 * MM

    doc = fitz.open()

    def add_sheet(items, label):
        page = doc.new_page(width=page_w, height=page_h)
        page.insert_text((margin_x, 6.0 * MM), label, fontsize=7, fontname="helv", color=(0.42, 0.42, 0.42))
        for i, (code, side, img) in enumerate(items):
            r, c = divmod(i, 2)
            x = margin_x + c * (card_w + gutter)
            y = top + r * (card_h + gutter)
            rect = fitz.Rect(x, y, x + card_w, y + card_h)
            buf = io.BytesIO()
            img.resize((round(card_w * 300 / 72), round(card_h * 300 / 72)), Image.LANCZOS).save(
                buf, format="PNG", dpi=(300, 300)
            )
            page.insert_image(rect, stream=buf.getvalue())
            page.draw_rect(rect, color=(0.75, 0.75, 0.75), width=0.4)

    cards4 = [cards[i:i + 4] for i in range(0, len(cards), 4)]
    for chunk in cards4:
        add_sheet([(c["code"], "front", sides[c["code"]]["front"]) for c in chunk],
                  "FRONT  " + "  ".join(c["code"] for c in chunk))
    for chunk in cards4:
        add_sheet([(c["code"], "back", sides[c["code"]]["back"]) for c in chunk],
                  "BACK  " + "  ".join(c["code"] for c in chunk))

    out = ROOT / "deliverables" / "cards" / "A4_office_proof.pdf"
    doc.save(str(out), garbage=3, deflate=True)
    doc.close()
    print("wrote", out.relative_to(ROOT), f"({len(cards4) * 2} pages)")


def main() -> None:
    for d in (OUT_PRINT, OUT_PREVIEW, TMP, TRIMMED_PNG):
        d.mkdir(parents=True, exist_ok=True)
    data = load_data()
    cards = data["cards"]
    edition = data.get("series", {}).get("edition", "NOV 2026")
    print(f"cards: {len(cards)} -> {[c['code'] for c in cards]}")

    sides_png: dict[str, dict[str, Image.Image]] = {}
    combined = fitz.open()
    missing_photos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-color-profile=srgb"])
        page = browser.new_page(viewport={"width": 800, "height": 1000})

        for card in cards:
            code = card["code"]
            if card.get("photo") and not (layouts.ASSETS / "images" / card["photo"]).exists():
                missing_photos.append(f"{code}:{card['photo']}")
            sides_png[code] = {}
            for side, lang in (("front", "cn"), ("back", "en")):
                pdf_path = OUT_PRINT / f"{code}_{side}.pdf"
                render_side(page, card, lang, edition, pdf_path)
                combined.insert_pdf(fitz.open(pdf_path))
                png_full = TRIMMED_PNG / f"{code}_{side}_full.png"
                img = pdf_to_png(pdf_path, png_full, dpi=150)
                sides_png[code][side] = crop_bleed(img, dpi=150)
                sides_png[code][side].save(OUT_PREVIEW / f"{code}_{side}.png", dpi=(150, 150))
                print(f"  {code} {side:5s} -> pdf+preview")

        browser.close()

    combined.set_metadata({
        "title": "JFC · CSCV Field Cards v1 — print (9 cards, front CN / back EN)",
        "author": "JAZZFRONT Consulting™",
        "subject": "A6 105×148mm + 3mm bleed, 18 pages, front/back pairs",
    })
    combined_out = OUT_PRINT / "CSCV_FieldCards_v1_print.pdf"
    combined.save(str(combined_out), garbage=3, deflate=True)
    combined.close()
    print("wrote", combined_out.relative_to(ROOT))

    fronts = [sides_png[c["code"]]["front"] for c in cards]
    backs = [sides_png[c["code"]]["back"] for c in cards]
    contact_sheet(fronts, 3, OUT_PREVIEW / "all_fronts.png", "FRONTS · 正面（中）")
    contact_sheet(backs, 3, OUT_PREVIEW / "all_backs.png", "BACKS · 背面（EN）")

    # all-cards preview: each row = 3 cards, each block is front | back
    block_w = sides_png[cards[0]["code"]]["front"].width
    block_h = sides_png[cards[0]["code"]]["front"].height
    gap = 16
    rows = (len(cards) + 2) // 3
    sheet = Image.new("RGB", (3 * (2 * block_w + gap) + 4 * gap, rows * block_h + (rows + 1) * gap), "white")
    for i, card in enumerate(cards):
        r, c = divmod(i, 3)
        x = gap + c * (2 * block_w + gap * 2)
        y = gap + r * (block_h + gap)
        sheet.paste(sides_png[card["code"]]["front"], (x, y))
        sheet.paste(sides_png[card["code"]]["back"], (x + block_w + gap, y))
    sheet.save(OUT_PREVIEW / "all_cards_preview.png")
    print("wrote preview sheets")

    build_a4_proof(sides_png, cards)

    issues = []
    for code, lang, info in OVERFLOW:
        if info["bad"]:
            issues.append(f"{code}/{lang}: overflow {info['bad']}")
        if info["missing"]:
            issues.append(f"{code}/{lang}: MISSING IMAGE placeholder visible")
    report = ROOT / "cards" / "render" / "overflow-report.txt"
    report.write_text("\n".join(issues) if issues else "OK — no overflow, no missing images\n", encoding="utf-8")
    if issues:
        print("WARNING layout issues:", file=sys.stderr)
        for line in issues:
            print("  " + line, file=sys.stderr)
    if missing_photos:
        print("WARNING missing photos:", ", ".join(missing_photos), file=sys.stderr)
    print("done")


if __name__ == "__main__":
    main()
