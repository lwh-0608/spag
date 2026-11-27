#!/usr/bin/env python3
"""Add printer crop marks to the combined card PDF.

Input : deliverables/cards/print/CSCV_FieldCards_v1_print.pdf (18 pages, 111×154mm)
Output: deliverables/cards/print/CSCV_FieldCards_v1_print_marks.pdf
        117×160mm pages: 111×154mm bleed box centred, trim box 105×148mm, crop marks.

Run: /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 cards/add_marks.py
"""
from __future__ import annotations

from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "deliverables" / "cards" / "print" / "CSCV_FieldCards_v1_print.pdf"
OUT = ROOT / "deliverables" / "cards" / "print" / "CSCV_FieldCards_v1_print_marks.pdf"

MM = 72 / 25.4
PAGE_W, PAGE_H = 117 * MM, 160 * MM       # marks sheet
BLEED_OFF = 3 * MM                        # from marks sheet edge to bleed box
TRIM_OFF = BLEED_OFF + 3 * MM             # trim box offset (marks + bleed)
CARD_W, CARD_H = 105 * MM, 148 * MM
MARK_LEN = 4 * MM
GRAY = (0, 0, 0)


def add_marks() -> None:
    src = fitz.open(SRC)
    out = fitz.open()
    for page in src:
        sheet = out.new_page(width=PAGE_W, height=PAGE_H)
        # place the bleed-sized card page inside the marks sheet
        card_rect = fitz.Rect(BLEED_OFF, BLEED_OFF, PAGE_W - BLEED_OFF, PAGE_H - BLEED_OFF)
        sheet.show_pdf_page(card_rect, src, page.number)
        x0, y0 = card_rect.x0 + 3 * MM, card_rect.y0 + 3 * MM       # trim top-left
        x1, y1 = card_rect.x1 - 3 * MM, card_rect.y1 - 3 * MM       # trim bottom-right
        # four corner marks, drawn outside the trim box
        for (x, y, dx, dy) in (
            (x0, y0, -1, -1), (x1, y0, 1, -1), (x0, y1, -1, 1), (x1, y1, 1, 1),
        ):
            hx = x if dx > 0 else x - MARK_LEN
            hy = y - 0.5
            sheet.draw_line(fitz.Point(hx, hy), fitz.Point(hx + MARK_LEN, hy), color=GRAY, width=0.3)
            vx = x - 0.5
            vy = y if dy > 0 else y - MARK_LEN
            sheet.draw_line(fitz.Point(vx, vy), fitz.Point(vx, vy + MARK_LEN), color=GRAY, width=0.3)
    out.set_metadata({
        "title": "JFC · CSCV Field Cards v1 — with crop marks (117×160mm)",
        "author": "JAZZFRONT Consulting™",
    })
    out.save(str(OUT), garbage=3, deflate=True)
    print(f"wrote {OUT} ({len(out)} pages, {PAGE_W / MM:.0f}×{PAGE_H / MM:.0f}mm)")


if __name__ == "__main__":
    add_marks()
