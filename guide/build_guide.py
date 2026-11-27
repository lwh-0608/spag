# -*- coding: utf-8 -*-
"""Render the A4 brand guide HTML to PDF and review PNGs.

    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 guide/build_guide.py

Outputs:
    guide/JFC_CSCV_Social_Banner_Kit_CN-EN.pdf
    guide/preview/page-01.png … (for visual review)

Fails loudly on broken images, page overflow or an unexpected page count.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
GUIDE = ROOT / "guide"
SRC = GUIDE / "src" / "guide.html"
PDF = GUIDE / "JFC_CSCV_Social_Banner_Kit_CN-EN.pdf"
EXPECTED_PAGES = 7

from playwright.sync_api import sync_playwright  # noqa: E402


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 794, "height": 1123})
            page.goto(SRC.as_uri(), wait_until="load")
            page.wait_for_function("document.fonts.status === 'loaded'", timeout=20000)
            page.evaluate(
                "() => Promise.all([...document.images].map(i => i.decode().catch(() => {})))"
            )
            page.wait_for_timeout(200)
            broken = page.evaluate(
                "() => [...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.src)"
            )
            boxes = page.evaluate(
                """() => [...document.querySelectorAll('.page')].map((el, i) => ({
                    i, h: el.scrollHeight, ch: el.clientHeight, w: el.scrollWidth, cw: el.clientWidth }))"""
            )
            pages = page.evaluate("() => document.querySelectorAll('.page').length")
            page.pdf(
                path=str(PDF),
                format="A4",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                prefer_css_page_size=True,
            )
        finally:
            browser.close()

    problems = []
    if broken:
        problems.append(f"broken images: {broken}")
    if pages != EXPECTED_PAGES:
        problems.append(f"expected {EXPECTED_PAGES} sections, found {pages}")
    for b in boxes:
        if b["h"] > b["ch"] + 2 or b["w"] > b["cw"] + 2:
            problems.append(f"page {b['i']+1} overflows: {b['w']}x{b['h']} > {b['cw']}x{b['ch']}")

    # PDF page count + metadata + review PNGs
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(PDF)
        if doc.page_count != EXPECTED_PAGES:
            problems.append(f"PDF has {doc.page_count} pages, expected {EXPECTED_PAGES}")
        doc.set_metadata({
            "title": "JFC / CSCV 官方社媒背景横幅模板 · Official Social Banner Template Kit",
            "author": "JAZZFRONT Consulting (JFC)",
            "subject": "Social banner template kit — brand guide, v1.0, November 2026",
            "keywords": "JFC, CSCV, LinkedIn, X, Facebook, YouTube, brand templates",
        })
        prev = GUIDE / "preview"
        prev.mkdir(parents=True, exist_ok=True)
        for i in range(doc.page_count):
            pix = doc[i].get_pixmap(dpi=110)
            pix.save(prev / f"page-{i+1:02d}.png")
        doc.saveIncr()
        doc.close()
    except ImportError:
        problems.append("PyMuPDF not available: page review PNGs skipped")

    if problems:
        print("GUIDE FAIL")
        for x in problems:
            print(" -", x)
        return 1
    print(f"GUIDE OK · {EXPECTED_PAGES} pages · {PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
