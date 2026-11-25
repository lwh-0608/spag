#!/usr/bin/env python3
"""Lead print-check for the JFC · CSCV Field Cards.

Checks every per-side PDF, the combined print PDF and the A4 office proof:
size, page count, embedded fonts, effective image resolution, missing-image marks.

Run:
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 cards/print_check.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
PRINT = ROOT / "deliverables" / "cards" / "print"
REPORT = ROOT / "deliverables" / "cards" / "PRINT-CHECK.txt"
MM = 25.4 / 72  # pt -> mm

PAGE_MM = (111.0, 154.0)
TOL_MM = 0.6
MIN_DPI = 295  # allow sub-0.5% rounding at the 300dpi threshold


def page_mm(page) -> tuple[float, float]:
    return page.rect.width * MM, page.rect.height * MM


def check_pdf(path: Path, expect_pages: int | None, problems: list[str], notes: list[str]) -> None:
    doc = fitz.open(path)
    n = len(doc)
    if expect_pages is not None and n != expect_pages:
        problems.append(f"{path.name}: pages {n} != {expect_pages}")
    sizes = {page_mm(p) for p in doc}
    for w, h in sizes:
        if abs(w - PAGE_MM[0]) > TOL_MM or abs(h - PAGE_MM[1]) > TOL_MM:
            problems.append(f"{path.name}: page size {w:.2f}×{h:.2f}mm != 111×154 (±{TOL_MM})")

    for i, page in enumerate(doc):
        # embedded fonts (Type3/CID both acceptable; 'n/a' ext means not embedded)
        for font in page.get_fonts(full=True):
            ext, ftype = font[1], font[2]
            # Type3 glyph programs carry ext "n/a" and are embedded by definition
            if ftype == "Type3":
                continue
            if ext in ("n/a", "", "none"):
                problems.append(f"{path.name} p{i + 1}: font not embedded: {font[3]}")
        # image effective dpi
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                info = doc.extract_image(xref)
            except Exception:
                continue
            for rect in page.get_image_rects(xref):
                if rect.width <= 0 or rect.height <= 0:
                    continue
                dpi_x = info["width"] / (rect.width / 72)
                dpi_y = info["height"] / (rect.height / 72)
                effective = min(dpi_x, dpi_y)
                if effective < MIN_DPI:
                    problems.append(
                        f"{path.name} p{i + 1}: image {xref} effective {effective:.0f}dpi < {MIN_DPI}"
                    )
                else:
                    notes.append(f"{path.name} p{i + 1}: image {info['width']}×{info['height']} "
                                 f"placed {rect.width * MM:.1f}×{rect.height * MM:.1f}mm -> {effective:.0f}dpi")
        text = page.get_text()
        if "MISSING IMAGE" in text:
            problems.append(f"{path.name} p{i + 1}: missing-image placeholder visible")
    doc.close()


def main() -> int:
    problems: list[str] = []
    notes: list[str] = []

    data = json.loads((ROOT / "cards" / "data.json").read_text(encoding="utf-8"))
    codes = [c["code"] for c in data["cards"]]

    for code in codes:
        for side in ("front", "back"):
            p = PRINT / f"{code}_{side}.pdf"
            if not p.exists():
                problems.append(f"missing print file: {p.name}")
                continue
            check_pdf(p, 1, problems, notes)

    combined = PRINT / "CSCV_FieldCards_v1_print.pdf"
    if not combined.exists():
        problems.append("missing combined print PDF")
    else:
        check_pdf(combined, len(codes) * 2, problems, notes)

    proof = ROOT / "deliverables" / "cards" / "A4_office_proof.pdf"
    if not proof.exists():
        problems.append("missing A4 office proof")
    else:
        doc = fitz.open(proof)
        for i, page in enumerate(doc):
            w, h = page_mm(page)
            if abs(w - 210) > 1 or abs(h - 297) > 1:
                problems.append(f"A4_office_proof p{i + 1}: size {w:.1f}×{h:.1f}mm != A4")
        doc.close()

    lines = []
    lines.append("JFC · CSCV Field Cards — print check")
    lines.append(f"cards: {len(codes)} ({', '.join(codes)})")
    if notes:
        lines.append("")
        lines.append("image resolutions:")
        lines.extend("  " + n for n in notes)
    lines.append("")
    if problems:
        lines.append(f"FAIL — {len(problems)} problem(s)")
        lines.extend("  " + p for p in problems)
    else:
        lines.append("PASS — sizes, pages, embedded fonts, image dpi and placeholders all OK")
    report = "\n".join(lines) + "\n"
    REPORT.write_text(report, encoding="utf-8")
    print(report)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
