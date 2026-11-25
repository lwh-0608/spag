#!/usr/bin/env python3
"""Assemble the CSCV promotion kit.

Reads content/*.md in order, writes:
  deliverables/CSCV_推广物料_纯文本_CN-EN_v2.md   (canonical plain text)
  deliverables/CSCV_推广物料_纯文本_CN-EN_v2.docx (readable copy, boxes = shaded panels)
and converts the docx to PDF with LibreOffice.

Run with the framework Python 3.13:
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 build/assemble.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
OUT = ROOT / "deliverables"

ORDER = [
    "01_front.md",
    "02_inventory.md",
    "03_cards.md",
    "04_staff.md",
    "05_suggestions.md",
    "06_execution.md",
    "07_compliance.md",
    "08_checklist.md",
]

NAVY = RGBColor(0x1B, 0x2A, 0x4A)
INK = RGBColor(0x1F, 0x1F, 0x1F)
GRAY = RGBColor(0x59, 0x59, 0x59)
BOX_FILL = "F4F1EA"
HEAD_FILL = "E6E2D8"

CN_FONT = "PingFang SC"
EN_FONT = "Avenir Next"
MONO_FONT = "Menlo"


def assemble_md() -> str:
    parts = []
    missing = []
    for name in ORDER:
        p = CONTENT / name
        if not p.exists():
            missing.append(name)
            continue
        parts.append(p.read_text(encoding="utf-8").strip())
    if missing:
        print(f"WARNING: missing content files: {missing}", file=sys.stderr)
    md = "\n\n".join(parts) + "\n"
    (OUT / "CSCV_推广物料_纯文本_CN-EN_v2.md").write_text(md, encoding="utf-8")
    fences = md.count("```")
    print(f"markdown written: {len(md)} chars, {fences} fence markers "
          f"({'balanced' if fences % 2 == 0 else 'UNBALANCED'})")
    return md


# --------------------------------------------------------------------------- #
# docx helpers
# --------------------------------------------------------------------------- #

def set_run_font(run, size=None, bold=None, italic=None, color=None,
                 ea=CN_FONT, latin=EN_FONT):
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    run.font.name = latin
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), latin)
    rfonts.set(qn("w:hAnsi"), latin)
    rfonts.set(qn("w:eastAsia"), ea)


def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(table, top=80, start=120, bottom=80, end=120):
    tbl_pr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for tag, val in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = OxmlElement(f"w:{tag}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    tbl_pr.append(mar)


def set_table_borders(table, color="D0CCC1", size=4):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tbl_pr.append(borders)


def add_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("JAZZFRONT Consulting™ · CSCV 推广物料 v2 · 纯文本 / plain text · ")
    set_run_font(run, size=8, color=GRAY)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run2 = p.add_run()
    run2._r.append(fld_begin)
    run2._r.append(instr)
    run2._r.append(fld_end)
    set_run_font(run2, size=8, color=GRAY)


def add_body_paragraph(doc, text, style=None, indent_cm=0.0):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.35
    if indent_cm:
        p.paragraph_format.left_indent = Cm(indent_cm)
    add_inline_runs(p, text)
    return p


def add_inline_runs(paragraph, text):
    """Handle **bold** and `code` inline spans."""
    tokens = re.split(r"(\*\*.+?\*\*|`[^`]+`)", text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            run = paragraph.add_run(tok[2:-2])
            set_run_font(run, bold=True, color=INK)
        elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2:
            run = paragraph.add_run(tok[1:-1])
            set_run_font(run, size=9.5, color=NAVY, latin=MONO_FONT, ea=CN_FONT)
        else:
            run = paragraph.add_run(tok)
            set_run_font(run, color=INK)


def is_meta_line(line: str) -> bool:
    heads = ("平台：", "Platform:", "读者：", "Audience:", "上限：", "Limit:",
             "字符数", "Characters:", "用途：", "Use:", "Headline（", "Headline (",
             "形式：", "Form:", "负责", "Owner", "优先级", "Priority",
             "建议：", "Target:", "字数", "覆盖", "投放")
    return line.startswith(heads)


def add_box(doc, lines):
    """A single-cell shaded table = the copy box."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Cm(16.0)
    cell = table.cell(0, 0)
    cell.width = Cm(16.0)
    shade_cell(cell, BOX_FILL)
    set_table_borders(table, color="CFC9B8", size=6)
    set_cell_margins(table, top=120, start=160, bottom=120, end=160)
    # clear default empty paragraph
    first = cell.paragraphs[0]
    first.text = ""
    first.paragraph_format.space_after = Pt(0)
    for i, line in enumerate(lines):
        p = first if i == 0 else cell.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.35
        if line == "":
            p.paragraph_format.space_after = Pt(2)
            continue
        run = p.add_run(line)
        set_run_font(run, size=10.5, color=INK)
    return table


def parse_table_rows(lines):
    rows = []
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if i == 1 and all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    return rows


def add_table(doc, lines):
    rows = parse_table_rows(lines)
    if not rows:
        return
    ncols = len(rows[0])
    table = doc.add_table(rows=len(rows), cols=ncols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.autofit = False
    set_table_borders(table)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    table._tbl.tblPr.append(layout)
    weigh = {
        2: [3.0, 13.0],
        3: [2.6, 6.5, 6.9],
        4: [2.2, 4.6, 4.6, 4.6],
        5: [2.0, 3.6, 3.6, 3.6, 3.6],
        7: [0.8, 2.0, 2.9, 2.2, 3.3, 2.6, 1.4],
        8: [0.9, 3.4, 1.0, 2.6, 0.9, 0.9, 1.2, 1.4],
    }.get(ncols)
    if weigh is None:
        weigh = [16.4 / ncols] * ncols
    scale = 16.2 / sum(weigh)
    # header row repeats on every page; rows do not split across pages
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        tr_pr.append(cant)
    header_tr = table.rows[0]._tr
    header_pr = header_tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    header_pr.append(tbl_header)

    for c_i in range(ncols):
        table.columns[c_i].width = Cm(weigh[c_i] * scale)
    for r_i, row in enumerate(rows):
        for c_i in range(ncols):
            cell = table.cell(r_i, c_i)
            cell.width = Cm(weigh[c_i] * scale)
            text = row[c_i] if c_i < len(row) else ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.15
            run = p.add_run(text)
            size = 8.5 if ncols >= 7 else 9.0
            set_run_font(run, size=size, bold=(r_i == 0),
                         color=NAVY if r_i == 0 else INK)
            if r_i == 0:
                shade_cell(cell, HEAD_FILL)
    return table


def build_docx(md: str):
    doc = Document()
    # page setup
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

    style = doc.styles["Normal"]
    style.font.name = EN_FONT
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)

    add_footer(section)

    lines = md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # fenced code block -> box
        if stripped.startswith("```"):
            i += 1
            block = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1  # closing fence
            add_box(doc, block)
            continue

        if not stripped:
            i += 1
            continue

        # headings
        if stripped.startswith("# "):
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(stripped[2:].strip())
            set_run_font(run, size=20, bold=True, color=NAVY)
            i += 1
            continue
        if stripped.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[3:].strip())
            set_run_font(run, size=15, bold=True, color=NAVY)
            i += 1
            continue
        if stripped.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[4:].strip())
            set_run_font(run, size=12, bold=True, color=NAVY)
            i += 1
            continue

        # tables
        if stripped.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            add_table(doc, block)
            doc.add_paragraph().paragraph_format.space_after = Pt(0)
            continue

        # bullets
        if stripped.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(5)
            p.paragraph_format.line_spacing = 1.35
            add_inline_runs(p, stripped[2:].strip())
            i += 1
            continue

        # blockquote
        if stripped.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            p.paragraph_format.space_after = Pt(5)
            run = p.add_run(stripped[2:].strip())
            set_run_font(run, italic=True, color=GRAY)
            i += 1
            continue

        # prefix "开头写：" style labels are plain paragraphs
        if is_meta_line(stripped):
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.left_indent = Cm(0.3)
            add_inline_runs(p, stripped)
            for r in p.runs:
                r.font.size = Pt(9.5)
                r.font.italic = True
                r.font.color.rgb = GRAY
            i += 1
            continue

        add_body_paragraph(doc, stripped)
        i += 1

    docx_path = OUT / "CSCV_推广物料_纯文本_CN-EN_v2.docx"
    doc.save(docx_path)
    print(f"docx written: {docx_path}")
    return docx_path


def to_pdf(docx_path: Path) -> None:
    try:
        subprocess.run(
            ["/opt/homebrew/bin/soffice", "--headless", "--convert-to", "pdf",
             "--outdir", str(OUT), str(docx_path)],
            check=True, capture_output=True, timeout=180,
        )
        print("pdf written")
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: pdf conversion failed: {exc}", file=sys.stderr)


def main():
    OUT.mkdir(exist_ok=True)
    md = assemble_md()
    docx_path = build_docx(md)
    to_pdf(docx_path)


if __name__ == "__main__":
    main()
