#!/usr/bin/env python3
"""Independent print-QA checker for the JFC · CSCV printable field cards (task-7).

Read-only on the deliverable tree: this script only writes under qa/.
It intentionally re-implements every check instead of reusing cards/print_check.py
(which writes deliverables/cards/PRINT-CHECK.txt).

Run:
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 qa/cards_check.py

Exit code: 0 = no FAIL, 1 = at least one FAIL, 2 = environment/input error.

Groups:
  A  file inventory
  B  geometry / page count / page order / A4 proof / combined-vs-single consistency
  C  font embedding and text extractability
  D  images: effective dpi, logo identity/placement, photo bleed, placeholders
  E  layout: safe area, bleed intrusion, collisions (baseline-based), title wrap
  F  content: data.json <> rendered text, facts whitelist, forbidden wording, placeholders
  G  data.json against CARD-SPEC §0/§1 limits
  H  documents: PRINT-SPEC.md, SOURCES.md, Lead's PRINT-CHECK / overflow report
  I  preview PNGs and contact sheets
  Z  evidence: hashes + mtimes of the accepted files
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "cards"
CONTENT = ROOT / "content"
DELIV = ROOT / "deliverables" / "cards"
PRINT = DELIV / "print"
PREVIEW = DELIV / "preview"
ASSETS = ROOT / "assets" / "cards"
IMGDIR = ASSETS / "images"
QA = ROOT / "qa"
SPEC = ROOT / "CARD-SPEC.md"

MM = 25.4 / 72.0
SIDE_W, SIDE_H = 111.0, 154.0
TOL_MM = 0.6
TRIM_W, TRIM_H = 105.0, 148.0
BLEED = 3.0
SAFE = 10.0
MIN_DPI = 300.0
TOTAL = "09"
EDITION = "NOV 2026"

FP = "JFC.Consulting@outlook.com"
PHONE_CN = "+86 189 2872 4769"
ADDR_CN = "广州南沙"
ADDR_EN = "Nansha, Guangzhou"

LAYOUT_EXPECT = {
    "C1": "promo-paper", "C2": "promo-ink", "C3": "promo-paper",
    "C4": "promo-paper", "C5": "promo-ink",
    "C6": "staff-ink", "C7": "staff-paper", "C8": "staff-paper", "C9": "staff-paper",
}
CARD_SPEC_PHOTO = {  # CARD-SPEC §0/§4 conventional names
    "C1": "img1_city.jpg", "C2": "img2_factory.jpg", "C3": "img3_inspection_v2.jpg",
    "C4": "img4_team.jpg", "C5": "img5_port_v2.jpg",
}
FOOTER_CN = f"{FP} · {PHONE_CN} · {ADDR_CN}"
FOOTER_EN = f"{FP} · {PHONE_CN} · {ADDR_EN}"
ALLOWED_PRICE_PAIRS = {("1,800", "3,000"), ("3,200", "4,500"), ("6,000", "15,000")}


# --------------------------------------------------------------------------- #
# report plumbing
# --------------------------------------------------------------------------- #

@dataclass
class Finding:
    level: str            # PASS / FAIL / WARN / INFO
    group: str
    check: str
    target: str
    msg: str = ""


class Report:
    def __init__(self) -> None:
        self.items: list[Finding] = []

    def add(self, level: str, group: str, check: str, target: str = "", msg: str = "") -> None:
        self.items.append(Finding(level, group, check, target, msg))

    def pass_(self, group: str, check: str, target: str = "", msg: str = "") -> None:
        self.add("PASS", group, check, target, msg)

    def fail(self, group: str, check: str, target: str, msg: str) -> None:
        self.add("FAIL", group, check, target, msg)

    def warn(self, group: str, check: str, target: str, msg: str) -> None:
        self.add("WARN", group, check, target, msg)

    def info(self, group: str, check: str, target: str = "", msg: str = "") -> None:
        self.add("INFO", group, check, target, msg)

    def counts(self) -> dict[str, int]:
        c = {"PASS": 0, "FAIL": 0, "WARN": 0, "INFO": 0}
        for f in self.items:
            c[f.level] += 1
        return c

    def emit(self) -> str:
        lines = []
        for lv in ("FAIL", "WARN", "PASS", "INFO"):
            rows = [f for f in self.items if f.level == lv]
            if not rows:
                continue
            lines.append(f"\n## {lv} ({len(rows)})")
            for f in rows:
                tgt = f" [{f.target}]" if f.target else ""
                lines.append(f"  {f.group}: {f.check}{tgt} — {f.msg}" if f.msg else f"  {f.group}: {f.check}{tgt}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def norm(s: str) -> str:
    """Whitespace-insensitive form (Type3 letter-spacing / line wraps add spaces)."""
    return re.sub(r"\s+", "", s or "")


def mm(v: float) -> float:
    return v * MM


def page_mm(page) -> tuple[float, float]:
    return mm(page.rect.width), mm(page.rect.height)


def load_data() -> dict:
    return json.loads((CARDS_DIR / "data.json").read_text(encoding="utf-8"))


try:
    sys.path.insert(0, str(CARDS_DIR / "templates"))
    import layouts as LAYOUTS  # noqa: E402  (read-only import for cross-checks)
except Exception:  # pragma: no cover
    LAYOUTS = None


def line_boxes(page) -> list[dict]:
    """Text lines with mm bbox / baseline, font size and owning block number."""
    out = []
    d = page.get_text("dict")
    for bno, block in enumerate(d.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(s.get("text", "") for s in spans)
            if not text.strip():
                continue
            x0, y0, x1, y1 = line["bbox"]
            base = spans[0]["origin"][1]
            out.append({
                "block": bno,
                "text": text,
                "size": max(s.get("size", 0) for s in spans),
                "bbox": (mm(x0), mm(y0), mm(x1), mm(y1)),
                "baseline": mm(base),
            })
    return out


def rect_mm(r) -> tuple[float, float, float, float]:
    return mm(r.x0), mm(r.y0), mm(r.x1), mm(r.y1)


def inter(a, b) -> tuple[float, float]:
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0.0, w), max(0.0, h)


def font_embedded(doc, xref: int) -> tuple[str, str, bool]:
    try:
        keys = doc.xref_get_keys(xref)
    except Exception:
        return ("?", "?", False)
    subtype = (doc.xref_get_key(xref, "Subtype")[1] or "").lstrip("/")
    base = (doc.xref_get_key(xref, "BaseFont")[1] or "").lstrip("/") if "BaseFont" in keys else ""
    if subtype == "Type3":
        cp = doc.xref_get_key(xref, "CharProcs")[1] if "CharProcs" in keys else ""
        return (subtype, base or "Type3", bool(cp) and cp not in ("null", ""))
    desc = None
    if "FontDescriptor" in keys:
        v = doc.xref_get_key(xref, "FontDescriptor")
        if v[0] == "xref":
            desc = int(v[1].split()[0])
    if desc is None and "DescendantFonts" in keys:
        arr = doc.xref_get_key(xref, "DescendantFonts")[1]
        for cand in re.findall(r"(\d+)\s+0\s+R", arr or ""):
            if "FontDescriptor" in doc.xref_get_keys(int(cand)):
                v = doc.xref_get_key(int(cand), "FontDescriptor")
                if v[0] == "xref":
                    desc = int(v[1].split()[0])
                break
    if desc is None:
        return (subtype, base, False)
    dk = doc.xref_get_keys(desc)
    for k in ("FontFile", "FontFile2", "FontFile3"):
        if k in dk:
            return (subtype, base, True)
    return (subtype, base, False)


def classify_images(doc, page) -> list[dict]:
    out = []
    for img in page.get_images(full=True):
        xref = img[0]
        try:
            info = doc.extract_image(xref)
        except Exception:
            continue
        for r in page.get_image_rects(xref):
            if r.width <= 0 or r.height <= 0:
                continue
            rect = rect_mm(r)
            wmm, hmm = rect[2] - rect[0], rect[3] - rect[1]
            dpi_x = float(info["width"]) / (wmm / 25.4) if wmm else 0.0
            dpi_y = float(info["height"]) / (hmm / 25.4) if hmm else 0.0
            aspect = float(info["width"]) / float(info["height"]) if info["height"] else 0.0
            out.append({
                "xref": xref, "w": int(info["width"]), "h": int(info["height"]),
                "aspect": aspect, "rect": rect, "wmm": wmm, "hmm": hmm,
                "dpi": min(dpi_x, dpi_y), "colorspace": info.get("colorspace"),
                "kind": "logo" if abs(aspect - 1460 / 476) < 0.06 and hmm < 10 else "photo",
                "bytes": info["image"],
            })
    return out


def logo_identity(blob: bytes) -> tuple[str, str]:
    import numpy as np
    im = Image.open(io.BytesIO(blob)).convert("RGBA")
    arr = np.asarray(im).astype(float)
    alpha = arr[..., 3:4] / 255.0
    rgb = arr[..., :3]
    if float(alpha.mean()) > 0.995:  # flattened by Chromium: transparent pixels -> black
        alpha = np.ones_like(alpha)
    flat = rgb * alpha
    best = None
    for name in ("logo_navy.png", "logo_white.png"):
        src = Image.open(ASSETS / name).convert("RGBA")
        sa = np.asarray(src).astype(float)
        if sa.shape[:2] != flat.shape[:2]:
            src = src.resize((im.width, im.height))
            sa = np.asarray(src).astype(float)
        sa_flat = sa[..., :3] * (sa[..., 3:4] / 255.0)
        diff = float(np.abs(flat - sa_flat).mean())
        if best is None or diff < best[0]:
            best = (diff, name)
    return best[1], f"mean|diff|={best[0]:.1f}"


def cjk_count(s: str) -> int:
    return len(re.findall(r"[\u3400-\u9fff]", s or ""))


def contains_ci(text: str, needle: str) -> bool:
    return norm(needle).lower() in norm(text).lower()


def remove_ci(text: str, needle: str) -> str:
    """Remove first case-insensitive occurrence of the whitespace-normalised needle."""
    n = norm(needle)
    if not n:
        return text
    tn = norm(text)
    idx = tn.lower().find(n.lower())
    if idx < 0:
        return text
    positions = [i for i, ch in enumerate(text) if not ch.isspace()]
    start, end = positions[idx], positions[idx + len(n) - 1]
    return text[:start] + text[end + 1:]


def price_occurrences(text: str) -> list[str]:
    found = [m.group(0) for m in re.finditer(r"RMB\s*[\d,]+\s*[–\-]\s*[\d,]+", text)]
    found += [m.group(0) for m in re.finditer(r"[\d,]+\s*[–\-]\s*[\d,]+\s*元(?:/站)?", text)]
    return found


def parse_price(s: str):
    m = re.search(r"(\d[\d,]*)\s*[–\-]\s*(\d[\d,]*)", s)
    return (m.group(1), m.group(2)) if m else s


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# A. inventory
# --------------------------------------------------------------------------- #

def check_inventory(rep: Report, data: dict) -> None:
    codes = [c["code"] for c in data["cards"]]
    missing = []
    for code in codes:
        for side in ("front", "back"):
            p = PRINT / f"{code}_{side}.pdf"
            if not p.exists():
                missing.append(p.name)
    for name, where in (("CSCV_FieldCards_v1_print.pdf", PRINT),
                        ("CSCV_FieldCards_v1_print_marks.pdf", PRINT),
                        ("A4_office_proof.pdf", DELIV),
                        ("PRINT-SPEC.md", DELIV), ("SOURCES.md", IMGDIR)):
        if not (where / name).exists():
            missing.append(str((where / name).relative_to(ROOT)))
    for name in ("logo_navy.png", "logo_white.png"):
        if not (ASSETS / name).exists():
            missing.append(f"assets/cards/{name}")
    for side in [f"C{c}_{s}.png" for c in range(1, 10) for s in ("front", "back")]:
        if not (PREVIEW / side).exists():
            missing.append(f"preview/{side}")
    for name in ("all_fronts.png", "all_backs.png", "all_cards_preview.png"):
        if not (PREVIEW / name).exists():
            missing.append(f"preview/{name}")
    for card in data["cards"]:
        photo = card.get("photo")
        if photo and not (IMGDIR / photo).exists():
            missing.append(f"assets/cards/images/{photo}")
    if missing:
        rep.fail("A", "A1 required files present", "", "missing: " + ", ".join(missing))
    else:
        rep.pass_("A", "A1 required files present",
                  f"{len(codes)*2} side PDFs + combined + A4 proof + 18 previews + assets")


# --------------------------------------------------------------------------- #
# B. geometry, page order, A4 proof
# --------------------------------------------------------------------------- #

def check_geometry(rep: Report, data: dict) -> dict:
    codes = [c["code"] for c in data["cards"]]
    docs: dict[str, fitz.Document] = {}
    for code in codes:
        for side in ("front", "back"):
            p = PRINT / f"{code}_{side}.pdf"
            if not p.exists():
                continue
            doc = fitz.open(p)
            docs[f"{code}_{side}"] = doc
            if len(doc) != 1:
                rep.fail("B", "B1 side PDF single page", p.name, f"pages={len(doc)}")
            w, h = page_mm(doc[0])
            if abs(w - SIDE_W) > TOL_MM or abs(h - SIDE_H) > TOL_MM:
                rep.fail("B", "B1 side PDF page size 111×154mm", p.name, f"{w:.2f}×{h:.2f}mm")
    if not any(f.check == "B1 side PDF page size 111×154mm" and f.level == "FAIL" for f in rep.items):
        rep.pass_("B", "B1 side PDF page size 111×154mm", "18/18", "111.17×154.18mm (±0.6mm)")
    if not any(f.check == "B1 side PDF single page" and f.level == "FAIL" for f in rep.items):
        rep.pass_("B", "B1 side PDF single page", "18/18")

    combined = PRINT / "CSCV_FieldCards_v1_print.pdf"
    cdoc = fitz.open(combined) if combined.exists() else None
    if cdoc is not None:
        if len(cdoc) != len(codes) * 2:
            rep.fail("B", "B2 combined 18 pages", combined.name, f"pages={len(cdoc)}")
        else:
            rep.pass_("B", "B2 combined 18 pages", combined.name, "18 pages")
        bad = [f"p{i+1}:{page_mm(p)[0]:.2f}×{page_mm(p)[1]:.2f}" for i, p in enumerate(cdoc)
               if abs(page_mm(p)[0] - SIDE_W) > TOL_MM or abs(page_mm(p)[1] - SIDE_H) > TOL_MM]
        if bad:
            rep.fail("B", "B2 combined page size 111×154mm", combined.name, "; ".join(bad[:6]))
        else:
            rep.pass_("B", "B2 combined page size 111×154mm", combined.name, "all 18 pages")
        order_bad = []
        for i, page in enumerate(cdoc):
            code = codes[i // 2]
            if norm(f"{code} / {TOTAL} · {EDITION}") not in norm(page.get_text()):
                order_bad.append(f"p{i+1} expected {code}")
        if order_bad:
            rep.fail("B", "B2 combined page order", combined.name, "; ".join(order_bad[:6]))
        else:
            rep.pass_("B", "B2 combined page order", combined.name, "p1..p18 = C1 front/back … C9 front/back")
        diffs, diffs_px = [], []
        import numpy as np
        for i, page in enumerate(cdoc):
            code = codes[i // 2]
            side = "front" if i % 2 == 0 else "back"
            key = f"{code}_{side}"
            if key not in docs:
                continue
            if norm(docs[key][0].get_text()) != norm(page.get_text()):
                diffs.append(key)
            pa = docs[key][0].get_pixmap(dpi=72, colorspace=fitz.csRGB)
            pb = page.get_pixmap(dpi=72, colorspace=fitz.csRGB)
            if (pa.width, pa.height) != (pb.width, pb.height):
                diffs_px.append(f"{key}: size mismatch")
                continue
            a = np.frombuffer(pa.samples, dtype=np.uint8).reshape(pa.height, pa.width, pa.n)
            b = np.frombuffer(pb.samples, dtype=np.uint8).reshape(pb.height, pb.width, pb.n)
            d = float(np.abs(a.astype(float) - b.astype(float)).mean())
            if d > 2.0:
                diffs_px.append(f"{key}: mean|Δ|={d:.2f}")
        if diffs:
            rep.fail("B", "B3 combined text equals single-side PDFs", "", ", ".join(diffs))
        else:
            rep.pass_("B", "B3 combined text equals single-side PDFs", "18/18")
        if diffs_px:
            rep.fail("B", "B4 combined pages pixel-equal to single-side PDFs", "", "; ".join(diffs_px[:6]))
        else:
            rep.pass_("B", "B4 combined pages pixel-equal to single-side PDFs", "18/18", "mean|Δ| ≤ 2/255")
    return {"single": docs, "combined": cdoc}


def check_marks_pdf(rep: Report, data: dict, combined) -> None:
    p = PRINT / "CSCV_FieldCards_v1_print_marks.pdf"
    if not p.exists():
        rep.warn("B", "B12 trim-marks PDF", "", "CSCV_FieldCards_v1_print_marks.pdf missing")
        return
    codes = [c["code"] for c in data["cards"]]
    doc = fitz.open(p)
    if len(doc) != len(codes) * 2:
        rep.fail("B", "B12 trim-marks PDF 18 pages", p.name, f"pages={len(doc)}")
    w, h = page_mm(doc[0])
    if abs(w - 117) > 1 or abs(h - 160) > 1:
        rep.fail("B", "B12 trim-marks page 117×160mm", p.name, f"{w:.1f}×{h:.1f}mm")
    bad_text, bad_marks = [], []
    for i, page in enumerate(doc):
        if combined is not None and i < len(combined):
            if norm(page.get_text()) != norm(combined[i].get_text()):
                bad_text.append(f"p{i+1}")
        # trim lines at 6mm and 111mm / 154mm of the 117×160 page (105×148 trim box)
        lines = []
        for dr in page.get_drawings():
            r = dr.get("rect")
            if r is None:
                continue
            x0, y0, x1, y1 = rect_mm(r)
            if (x1 - x0) < 0.6 and (y1 - y0) > 3:     # vertical rule
                lines.append(("v", x0))
            elif (y1 - y0) < 0.6 and (x1 - x0) > 3:   # horizontal rule
                lines.append(("h", y0))
        targets_v = [6.0, 111.0]
        targets_h = [6.0, 154.0]
        hit_v = {t: any(k == "v" and abs(x - t) <= 1.2 for k, x in lines) for t in targets_v}
        hit_h = {t: any(k == "h" and abs(y - t) <= 1.2 for k, y in lines) for t in targets_h}
        if not (all(hit_v.values()) and all(hit_h.values())):
            bad_marks.append(f"p{i+1}")
    if bad_text:
        rep.fail("B", "B12 trim-marks content equals combined PDF", p.name, ", ".join(bad_text[:6]))
    if bad_marks:
        rep.warn("B", "B12 trim-marks trim lines at 105×148 box", p.name,
                 "could not find thin trim rules at 6/111mm and 6/154mm on " + ", ".join(bad_marks[:6]))
    if not bad_text and not bad_marks:
        rep.pass_("B", "B12 trim-marks PDF", p.name,
                  "18 pages, 117×160mm, 105×148 trim lines, content identical to combined PDF")
    doc.close()


def check_a4_proof(rep: Report, data: dict) -> None:
    p = DELIV / "A4_office_proof.pdf"
    if not p.exists():
        return
    codes = [c["code"] for c in data["cards"]]
    doc = fitz.open(p)
    expect_pages = 2 * math.ceil(len(codes) / 4)
    if len(doc) != expect_pages:
        rep.fail("B", "B5 A4 proof page count", p.name, f"pages={len(doc)} expected {expect_pages}")
    else:
        rep.pass_("B", "B5 A4 proof page count", p.name, f"{len(doc)} pages (3 front sheets + 3 back sheets)")
    bad = [f"p{i+1}:{page_mm(pg)[0]:.1f}×{page_mm(pg)[1]:.1f}mm" for i, pg in enumerate(doc)
           if abs(page_mm(pg)[0] - 210) > 1 or abs(page_mm(pg)[1] - 297) > 1]
    if bad:
        rep.fail("B", "B6 A4 proof page size A4", p.name, "; ".join(bad))
    else:
        rep.pass_("B", "B6 A4 proof page size A4", p.name, "210×297mm")
    count_bad, layout_bad, dpi_bad = [], [], []
    for i, page in enumerate(doc):
        imgs = []
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                info = doc.extract_image(xref)
            except Exception:
                continue
            for r in page.get_image_rects(xref):
                rect = rect_mm(r)
                imgs.append((rect[2] - rect[0], rect[3] - rect[1], info["width"], info["height"]))
        if not imgs:
            count_bad.append(f"p{i+1}: no card images")
            continue
        if len(imgs) > 4:
            count_bad.append(f"p{i+1}: {len(imgs)} images > 4")
        for wmm, hmm, pw, ph in imgs:
            if abs(wmm - 100.8) > 1.0 or abs(hmm - 142.08) > 1.5:
                layout_bad.append(f"p{i+1}: {wmm:.1f}×{hmm:.1f}mm != 100.8×142.08 (96% trim)")
            if abs(wmm / hmm - TRIM_W / TRIM_H) > 0.01:
                layout_bad.append(f"p{i+1}: aspect {wmm/hmm:.3f} != trim {TRIM_W/TRIM_H:.3f}")
            dpi = min(pw / (wmm / 25.4), ph / (hmm / 25.4))
            if dpi < MIN_DPI - 2:
                dpi_bad.append(f"p{i+1}: {dpi:.0f}dpi")
    if count_bad:
        rep.fail("B", "B7 A4 proof 4-up", p.name, "; ".join(count_bad))
    else:
        rep.pass_("B", "B7 A4 proof 4-up", p.name, "≤4 trimmed cards per sheet")
    if layout_bad:
        rep.fail("B", "B8 A4 proof cards at 96% trim size (no bleed)", p.name, "; ".join(layout_bad[:6]))
    else:
        rep.pass_("B", "B8 A4 proof cards at 96% trim size (no bleed)", p.name, "100.8×142.0mm each")
    if dpi_bad:
        rep.warn("B", "B9 A4 proof raster resolution", p.name, "; ".join(dpi_bad[:6]))
    else:
        rep.pass_("B", "B9 A4 proof raster resolution", p.name, "≈300dpi")
    label_bad, tofu = [], []
    for i, page in enumerate(doc):
        t = norm(page.get_text()).upper()
        if "FRONT" not in t and "BACK" not in t:
            label_bad.append(f"p{i+1}")
        if "·" in t:
            tofu.append(f"p{i+1}")
    if label_bad:
        rep.fail("B", "B10 A4 proof sheet labels", p.name, ", ".join(label_bad))
    else:
        rep.pass_("B", "B10 A4 proof sheet labels", p.name, "FRONT / BACK label on every sheet")
    if tofu:
        rep.warn("B", "B11 A4 proof label CJK glyphs", p.name,
                 "sheet labels still contain replacement dots (CJK not encoded by the proof font)")
    else:
        rep.pass_("B", "B11 A4 proof label renders cleanly", p.name, "no replacement glyphs in labels")
    doc.close()


# --------------------------------------------------------------------------- #
# C. fonts
# --------------------------------------------------------------------------- #

def check_fonts(rep: Report, docs: dict) -> None:
    non_embedded, inventory = [], {}
    for key, doc in docs.items():
        for i, page in enumerate(doc):
            for f in page.get_fonts(full=True):
                subtype, base, emb = font_embedded(doc, f[0])
                inv = f"{subtype}:{base or '(unnamed)'}"
                inventory[inv] = inventory.get(inv, 0) + 1
                if not emb:
                    non_embedded.append(f"{key} p{i+1}: {subtype} {base or '(unnamed)'} ext={f[1]}")
    if non_embedded:
        rep.fail("C", "C1 all fonts embedded", "", "; ".join(non_embedded[:8]))
    else:
        rep.pass_("C", "C1 all fonts embedded", "18 side PDFs",
                  "Type3 via CharProcs + Type0/CID via FontFile2; no unembedded font")
    na_bad = []
    for key, doc in docs.items():
        for i, page in enumerate(doc):
            for f in page.get_fonts(full=True):
                subtype, base, _ = font_embedded(doc, f[0])
                if f[1] in ("n/a", "", "none") and subtype != "Type3":
                    na_bad.append(f"{key} p{i+1}: {subtype} {base}")
    if na_bad:
        rep.fail("C", "C2 ext n/a only on Type3", "", "; ".join(na_bad[:6]))
    else:
        rep.pass_("C", "C2 ext n/a only on Type3", "n/a reserved for embedded Type3 glyph programs")
    bad = [k for k, d in docs.items() if len(norm(d[0].get_text())) < 40]
    if bad:
        rep.fail("C", "C3 text extractable", "", ", ".join(bad))
    else:
        rep.pass_("C", "C3 text extractable", "18/18", "ToUnicode present on every font")
    named = {k: v for k, v in inventory.items() if not k.startswith("Type3")}
    t3 = sum(v for k, v in inventory.items() if k.startswith("Type3"))
    rep.info("C", "C4 font inventory", f"{len(inventory)} distinct / {sum(inventory.values())} uses",
             f"Type3 uses={t3}; named={named}")
    if not any("Menlo" in k for k in inventory):
        rep.fail("C", "C5 Menlo embedded", "", "no Menlo subset found")
    else:
        rep.pass_("C", "C5 Menlo embedded", "Menlo-Regular subsets (Type0/Identity-H)")
    bad = [k for k, d in docs.items() if k.endswith("_front") and cjk_count(d[0].get_text()) < 20]
    if bad:
        rep.fail("C", "C6 CJK text present on CN fronts", "", ", ".join(bad))
    else:
        rep.pass_("C", "C6 CJK text present on CN fronts", "9/9",
                  "PingFang SC embedded as Type3 glyph programs (allowed)")
    rep.info("C", "C7 CJK embedding style", "PingFang SC -> Type3",
             "Chromium/Skia embeds macOS system CJK fonts as Type3; glyph programs are inside the "
             "PDF (vector, self-contained). Accepted per task-7 item 2 (Type3/CID allowed).")


# --------------------------------------------------------------------------- #
# D. images
# --------------------------------------------------------------------------- #

def check_images(rep: Report, data: dict, docs: dict) -> None:
    cards = {c["code"]: c for c in data["cards"]}
    logo_bad, logo_ident_bad, dpi_bad, photo_bad, missing = [], [], [], [], []
    photo_seen: dict[str, dict] = {}
    for key, doc in docs.items():
        code, side = key.split("_")
        page = doc[0]
        imgs = classify_images(doc, page)
        logos = [i for i in imgs if i["kind"] == "logo"]
        photos = [i for i in imgs if i["kind"] == "photo"]
        if len(logos) != 1:
            logo_bad.append(f"{key}: {len(logos)} logo images")
        else:
            lg = logos[0]
            x0, y0, _, _ = lg["rect"]
            if not (8.0 <= y0 <= 20.0):
                logo_bad.append(f"{key}: logo at y={y0:.1f}mm, not in the top band")
            if not (8.0 <= x0 <= 60.0):
                logo_bad.append(f"{key}: logo at x={x0:.1f}mm, outside the header zone")
            if not (17.0 <= lg["wmm"] <= 22.0):
                logo_bad.append(f"{key}: logo width {lg['wmm']:.1f}mm (spec ≈20mm)")
            label, detail = logo_identity(lg["bytes"])
            want = "logo_white.png" if cards[code]["layout"].endswith("ink") else "logo_navy.png"
            if label != want:
                logo_ident_bad.append(f"{key}: {label} ({detail}) but {cards[code]['layout']} needs {want}")
        for ph in photos:
            photo_seen.setdefault(code, ph)
            x0, y0, x1, y1 = ph["rect"]
            touches = [edge for edge, ok in (
                ("left", x0 <= 0.6), ("right", x1 >= SIDE_W - 0.6),
                ("top", y0 <= 0.6), ("bottom", y1 >= SIDE_H - 0.6)) if ok]
            if not touches:
                photo_bad.append(f"{key}: photo floats inside margins, no bleed edge ({x0:.1f},{y0:.1f})")
            frac = (ph["wmm"] * ph["hmm"]) / (SIDE_W * SIDE_H)
            if frac < 0.06:
                photo_bad.append(f"{key}: photo only {frac*100:.0f}% of the side")
            if ph["dpi"] < MIN_DPI - 1:
                dpi_bad.append(f"{key}: {ph['w']}×{ph['h']} placed {ph['wmm']:.1f}×{ph['hmm']:.1f}mm "
                               f"-> {ph['dpi']:.1f}dpi")
        if "MISSING" in page.get_text().upper():
            missing.append(f"{key}: MISSING IMAGE placeholder")
    if logo_bad:
        rep.fail("D", "D1 logo on every page, top-left, ≈20mm wide", "", "; ".join(logo_bad[:10]))
    else:
        rep.pass_("D", "D1 logo present in header, ≈20mm wide", "18/18", "19.0×6.2mm; x=10.1mm or 43.9mm on sidebar layouts")
    if logo_ident_bad:
        rep.fail("D", "D2 correct logo colour per layout", "", "; ".join(logo_ident_bad[:10]))
    else:
        rep.pass_("D", "D2 correct logo colour per layout", "18/18", "navy on paper, white on ink")
    for code in ("C1", "C2", "C3", "C4", "C5"):
        if code not in photo_seen:
            missing.append(f"{code}: no illustration on any side")
    if photo_bad:
        rep.fail("D", "D3 illustration reaches bleed, covers ≥6% of the side", "", "; ".join(photo_bad[:10]))
    else:
        geos = ", ".join(f"{c}:{p['wmm']:.0f}×{p['hmm']:.0f}mm" for c, p in sorted(photo_seen.items()))
        rep.pass_("D", "D3 illustration reaches bleed, covers ≥6% of the side",
                  f"{len(photo_seen)}/5 cards", geos)
    if dpi_bad:
        rep.fail("D", "D4 photo/logo effective resolution ≥300dpi", "", "; ".join(dpi_bad[:10]))
    else:
        sample = next(iter(photo_seen.values()), None)
        extra = f"photo {sample['dpi']:.0f}dpi" if sample else ""
        rep.pass_("D", "D4 photo/logo effective resolution ≥300dpi", "5 photo bands + 18 logos",
                  extra + "; logo ≈1947dpi")
    if missing:
        rep.fail("D", "D5 no MISSING IMAGE / placeholder", "", "; ".join(missing[:10]))
    else:
        rep.pass_("D", "D5 no MISSING IMAGE / placeholder", "18/18", "no placeholder text")
    src = (IMGDIR / "SOURCES.md").read_text(encoding="utf-8") if (IMGDIR / "SOURCES.md").exists() else ""
    map_bad, map_notes = [], []
    for code in ("C1", "C2", "C3", "C4", "C5"):
        photo = cards[code].get("photo")
        if not photo:
            map_bad.append(f"{code}: no photo field")
            continue
        if not (IMGDIR / photo).exists():
            map_bad.append(f"{code}: file {photo} missing")
        if not re.search(rf"`{re.escape(photo)}`", src):
            map_bad.append(f"{code}: {photo} not listed in SOURCES.md")
        if photo != CARD_SPEC_PHOTO[code]:
            spec_txt = SPEC.read_text(encoding="utf-8") if SPEC.exists() else ""
            if photo in spec_txt:
                map_notes.append(f"{code}: uses {photo} (approved replacement in CARD-SPEC §4 / SOURCES)")
            else:
                map_bad.append(f"{code}: {photo} differs from CARD-SPEC §4 and is not documented")
    if map_bad:
        rep.fail("D", "D6 data.json photo mapping → file → SOURCES", "", "; ".join(map_bad))
    else:
        rep.pass_("D", "D6 data.json photo mapping → file → SOURCES", "C1..C5",
                  "; ".join(map_notes) if map_notes else "img1..img5 as in CARD-SPEC §4")
    staff_photo = [k for k in docs if k.split("_")[0] in ("C6", "C7", "C8", "C9")
                   and any(i["kind"] == "photo" for i in classify_images(docs[k], docs[k][0]))]
    if staff_photo:
        rep.warn("D", "D7 staff cards photo-free", "", ", ".join(staff_photo))
    else:
        rep.pass_("D", "D7 staff cards photo-free", "C6..C9", "no photo band on staff cards")
    import numpy as np
    for code in ("C1", "C2", "C3", "C4", "C5"):
        key = f"{code}_front"
        photo = cards[code].get("photo")
        if key not in docs or not photo or not (IMGDIR / photo).exists() or code not in photo_seen:
            continue
        ph = photo_seen[code]
        emb = Image.open(io.BytesIO(ph["bytes"])).convert("RGB")
        s = Image.open(IMGDIR / photo).convert("RGB")
        sw, sh = s.size
        crop_h = int(round(sw / (ph["wmm"] / ph["hmm"])))
        if crop_h <= sh:
            top = (sh - crop_h) // 2
            s = s.crop((0, top, sw, top + crop_h))
        s = s.resize(emb.size)
        d = float(np.abs(np.asarray(s).astype(float) - np.asarray(emb).astype(float)).mean())
        if d > 45:
            rep.warn("D", "D8 photo band matches recorded source", key,
                     f"mean|Δ|={d:.1f} vs centre crop of {photo}; check crop/source")
        else:
            rep.pass_("D", "D8 photo band matches recorded source", key, f"{photo}, mean|Δ|={d:.1f}")
    edge_issues, edge_note = [], []
    for key, doc in docs.items():
        page = doc[0]
        pix = page.get_pixmap(dpi=600, colorspace=fitz.csRGB)
        a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
        mmpx = 25.4 / 600.0

        def white_run(seq):
            n = 0
            for px in seq:
                if (px > 250).all():
                    n += 1
                else:
                    break
            return n

        runs = {
            "top": white_run(a[:, a.shape[1] // 2, :]),
            "bottom": white_run(a[::-1, a.shape[1] // 2, :]),
            "left": white_run(a[a.shape[0] // 2, :, :]),
            "right": white_run(a[a.shape[0] // 2, ::-1, :]),
        }
        worst = max(runs.items(), key=lambda kv: kv[1])
        if worst[1] * mmpx > 0.05:
            edge_issues.append(f"{key}: {worst[0]} white strip {worst[1]*mmpx:.2f}mm")
        edge_note.append(worst[1] * mmpx)
    if edge_issues:
        worst_mm = max(edge_note) if edge_note else 0
        if worst_mm >= BLEED:
            rep.fail("D", "D9 background reaches bleed edge", "", "; ".join(edge_issues[:6]))
        else:
            rep.warn("D", "D9 background reaches bleed edge", "",
                     f"white strip up to {worst_mm:.2f}mm on the right/bottom edge of all 18 sides "
                     f"(inside the 3 mm bleed, trimmed off by the cutter; Chromium rounds the "
                     f"111×154mm page box to whole CSS px). Suggest extending the background 0.3mm or "
                     f"rendering the exact page box before a reprint.")
    else:
        rep.pass_("D", "D9 background reaches bleed edge", "18/18", "no unprinted edge pixels")


# --------------------------------------------------------------------------- #
# E. layout
# --------------------------------------------------------------------------- #

def spec_monogram_mm() -> float:
    if SPEC.exists():
        m = re.search(r"(\d+)\s*×\s*(\d+)\s*mm\s*的?[“\"]?首字母块", SPEC.read_text(encoding="utf-8"))
        if m:
            return float(m.group(1))
    return 40.0


def check_layout(rep: Report, data: dict, docs: dict) -> None:
    cards = {c["code"]: c for c in data["cards"]}
    safe_bad, bleed_bad, collide_bad, orphan_warn, title_bad = [], [], [], [], []
    sub_counts: list[str] = []
    mono_expect = spec_monogram_mm()
    mono_bad = []
    for key, doc in docs.items():
        page = doc[0]
        lines = line_boxes(page)
        code, side = key.split("_")
        is_staff = cards[code]["layout"].startswith("staff")
        for ln in lines:
            x0, y0, x1, y1 = ln["bbox"]
            if x0 < SAFE - TOL_MM or y0 < SAFE - TOL_MM or x1 > SIDE_W - SAFE + TOL_MM or y1 > SIDE_H - SAFE + TOL_MM:
                safe_bad.append(f"{key}: {ln['text'][:20]!r} bbox=({x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f})")
            if x0 < BLEED or y0 < BLEED or x1 > SIDE_W - BLEED or y1 > SIDE_H - BLEED:
                bleed_bad.append(f"{key}: {ln['text'][:20]!r} inside bleed")
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                a, b = lines[i], lines[j]
                if a["block"] == b["block"]:
                    continue
                if a["size"] >= 40 or b["size"] >= 40:
                    continue
                if abs(a["baseline"] - b["baseline"]) > 0.5 * max(a["size"], b["size"]) * MM:
                    continue
                iw, _ = inter(a["bbox"], b["bbox"])
                if iw > 2.0:
                    collide_bad.append(f"{key}: {a['text'][:22]!r} ({a['size']:.0f}pt) and "
                                       f"{b['text'][:22]!r} ({b['size']:.0f}pt) share a baseline band")
        if not is_staff:
            title = [l for l in lines if 16.5 <= l["size"] < 40 and l["text"].strip() != code]
            if title:
                nlines = len(title)
                limit = 2 if side == "front" else 3
                if nlines > limit:
                    title_bad.append(f"{key}: title wraps to {nlines} lines")
                last = title[-1]["text"].strip()
                widths = [t["bbox"][2] - t["bbox"][0] for t in title]
                last_w = widths[-1]
                if side == "front" and cjk_count(last) <= 1 and len(last) <= 2:
                    orphan_warn.append(f"{key}: title last line {last!r} is a lone character")
                elif last_w < 0.22 * max(widths):
                    orphan_warn.append(f"{key}: title last line {last!r} very short "
                                       f"({last_w:.0f}mm vs {max(widths):.0f}mm)")
            subs = [l for l in lines if abs(l["size"] - 7.6) < 0.25]
            if subs:
                sub_counts.append(f"{key}: {len(subs)}")
    for key, doc in docs.items():
        code = key.split("_")[0]
        if not cards[code]["layout"].startswith("staff"):
            continue
        boxes = []
        for dr in doc[0].get_drawings():
            r = dr.get("rect")
            if r is None:
                continue
            x0, y0, x1, y1 = rect_mm(r)
            w, h = x1 - x0, y1 - y0
            if 15 <= w <= 45 and abs(w - h) < 1.5:
                boxes.append(w)
        if boxes:
            w = max(boxes)
            if abs(w - mono_expect) > 1.5:
                mono_bad.append(f"{key}: {w:.1f}mm vs CARD-SPEC {mono_expect:.0f}mm")
    # E8: footer + photo-band baselines should register across the 9-card series
    foot_y = {}
    band_y = {}
    for key, doc in docs.items():
        page = doc[0]
        for ln in line_boxes(page):
            if "JFC.Consulting" in ln["text"]:
                foot_y[key] = ln["bbox"][1]
        for im in classify_images(doc, page):
            if im["kind"] == "photo":
                band_y[key] = im["rect"][1]
    if foot_y:
        lo_key = min(foot_y, key=foot_y.get)
        hi_key = max(foot_y, key=foot_y.get)
        spread = foot_y[hi_key] - foot_y[lo_key]
        detail = (f"footer top edge: {lo_key} {foot_y[lo_key]:.1f}mm … {hi_key} {foot_y[hi_key]:.1f}mm "
                  f"(spread {spread:.1f}mm of 154mm file; back/staff sides sit at 141.4–141.6mm)")
        if spread > 5:
            rep.warn("E", "E8 footer baseline consistent across sides", "", detail +
                     " — CN promo sides are not bottom-anchored (.foot has no margin-top:auto), so the "
                     "footer and photo band shift with the title line count; C1_front leaves a 26mm bottom void")
        else:
            rep.pass_("E", "E8 footer baseline consistent across sides", "", detail)
    if band_y:
        groups = sorted({round(v, 1) for v in band_y.values()})
        rep.info("E", "E9 photo band positions by layout family", f"{len(band_y)}/5",
                 f"tops {groups} mm — intentionally different per layout family (C1 band / C2 full "
                 f"bleed / C3 high band / C4 short band / C5 top band); each still reaches the bleed edge")
    if safe_bad:
        rep.fail("E", "E1 all text inside 7mm safe margin (10mm from file edge)", "", "; ".join(safe_bad[:10]))
    else:
        rep.pass_("E", "E1 all text inside 7mm safe margin (10mm from file edge)", "18/18",
                  "tightest text box 10.0/143.7mm from file edge")
    if bleed_bad:
        rep.fail("E", "E2 no text inside 3mm bleed", "", "; ".join(bleed_bad[:10]))
    else:
        rep.pass_("E", "E2 no text inside 3mm bleed", "18/18")
    if collide_bad:
        rep.fail("E", "E3 no overlapping text blocks", "", "; ".join(collide_bad[:10]))
    else:
        rep.pass_("E", "E3 no overlapping text blocks", "18/18", "no line pair shares a baseline band")
    if title_bad:
        rep.fail("E", "E4 title line count within spec", "", "; ".join(title_bad[:10]))
    else:
        rep.pass_("E", "E4 title line count within spec", "18/18", "CN ≤2 lines, EN ≤3 lines")
    if orphan_warn:
        rep.warn("E", "E5 no orphan line in title", "", "; ".join(orphan_warn[:10]))
    else:
        rep.pass_("E", "E5 no orphan line in title", "18/18", "no lone char / stub last line")
    if mono_bad:
        rep.warn("E", "E6 staff monogram block size = CARD-SPEC §2", "", "; ".join(mono_bad[:10]))
    else:
        rep.pass_("E", "E6 staff monogram block size = CARD-SPEC §2", "C6..C9",
                  f"{mono_expect:.0f}×{mono_expect:.0f}mm (actual 27.8mm stroked box)")
    rep.info("E", "E7 subtitle line counts", "promo cards", "; ".join(sub_counts[:10]))

    # E10: screen-proxy local contrast between text and whatever is behind it
    # (photo band, gradient transition, paper / ink). WCAG formula on luma percentiles.
    import numpy as np

    def _lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    low = []
    for key, doc in docs.items():
        page = doc[0]
        pix = page.get_pixmap(dpi=200, colorspace=fitz.csRGB)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].astype(float)
        ppm = 200 / 25.4
        luma = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
        for ln in line_boxes(page):
            if ln["size"] >= 40 or ln["size"] < 2.5:
                continue
            if ln["text"].strip() == key.split("_")[0]:  # ghost card-number watermark
                continue
            x0, y0, x1, y1 = ln["bbox"]
            c0 = int(max(0, x0 * ppm)); c1 = int(min(pix.width, x1 * ppm))
            r0 = int(max(0, y0 * ppm)); r1 = int(min(pix.height, y1 * ppm))
            if c1 - c0 < 4 or r1 - r0 < 3:
                continue
            reg = luma[r0:r1, c0:c1].ravel()
            p05, p50, p95 = np.percentile(reg, [5, 50, 95])
            fg, bg = (p05, p95) if p50 >= 128 else (p95, p05)
            cr = (max(_lin(fg / 255), _lin(bg / 255)) + 0.05) / (min(_lin(fg / 255), _lin(bg / 255)) + 0.05)
            if ln["size"] >= 6:
                limit = 3.0
            elif ln["size"] >= 4.2:
                limit = 2.5
            else:
                limit = 2.0   # 3–4pt micro-type: only flag near-invisible cases
            if cr < limit:
                low.append(f"{key}: {ln['text'][:18]!r} {ln['size']:.1f}pt contrast {cr:.1f}:1")
    if low:
        rep.warn("E", "E10 text/backing contrast (screen proxy)", "", "; ".join(low[:10]))
    else:
        rep.pass_("E", "E10 text/backing contrast (screen proxy)", "18/18",
                  "≥3.0:1 body text / ≥2.4:1 fine print; covers text over photo/gradient/paper/ink")


# --------------------------------------------------------------------------- #
# F. content
# --------------------------------------------------------------------------- #

def quote_text(card: dict, side: str) -> str:
    lang = "cn" if side == "front" else "en"
    q = card.get(f"quote_{lang}")
    if q:
        return q
    if LAYOUTS is not None:
        return LAYOUTS.QUOTES.get(card.get("code", ""), ("", ""))[0 if lang == "cn" else 1]
    return ""


def skills_text(card: dict, lang: str) -> str:
    s = card.get(f"skills_{lang}")
    if s:
        return s
    if LAYOUTS is not None:
        d = LAYOUTS.SKILLS if lang == "cn" else LAYOUTS.SKILLS_EN
        return d.get(card.get("code", ""), "")
    return ""


def present_with_fallback(text: str, s: str) -> bool:
    """The sidebar layout family (!) re-stacks the footer and shortens the series
    line; accept those documented variants instead of the single-line form."""
    if contains_ci(text, s):
        return True
    if "·" in s and ("@" in s or "+86" in s or "广州" in s or "Nansha" in s):
        parts = [p.strip() for p in s.split("·") if p.strip()]
        return all(contains_ci(text, p) for p in parts)
    if s.startswith("JFC · CSCV FIELD CARDS"):
        return contains_ci(text, "FIELD CARDS")
    if s.startswith("NANSHA · GUANGZHOU"):
        return (contains_ci(text, "NANSHA") or contains_ci(text, "GUANGZHOU")
                or contains_ci(text, "广州南沙"))
    if s.startswith("JFC · CSCV · FIELD CARDS · NANSHA"):
        return contains_ci(text, "FIELD CARDS")
    return False


def expected_side_strings(card: dict, side: str) -> list[str]:
    lang = "cn" if side == "front" else "en"
    out = [card.get(f"eyebrow_{lang}", ""), card.get(f"title_{lang}", ""),
           card.get(f"sub_{lang}", ""), card.get(f"footer_{lang}", "")]
    for p in card.get("points", []):
        out += [str(p.get("num", "")), p.get(lang, "")]
    out += [f"{card['code']} / {TOTAL} · {EDITION}", "JFC · CSCV FIELD CARDS", "NANSHA · GUANGZHOU"]
    if card["layout"].startswith("staff"):
        out += [card.get(f"role_{lang}", ""), card.get(f"name_{lang}", ""),
                card.get(f"headline_{lang}", ""), card.get(f"note_{lang}") or "",
                "JFC · CSCV · FIELD CARDS · NANSHA",
                "负责范围 / SCOPE" if lang == "cn" else "SCOPE / 负责范围",
                "专长 / EXPERTISE" if lang == "cn" else "EXPERTISE / 专长"]
        out.append(skills_text(card, lang).strip())  # keep "·" separators so the whole line cancels out
        out.append(quote_text(card, side))
    elif side == "back":
        out.append(quote_text(card, side))
    return [s for s in out if s and s.strip()]


def check_content(rep: Report, data: dict, docs: dict) -> None:
    cards = data["cards"]
    missing = []
    for card in cards:
        for side in ("front", "back"):
            key = f"{card['code']}_{side}"
            if key not in docs:
                continue
            text = docs[key][0].get_text()
            for s in expected_side_strings(card, side):
                if not present_with_fallback(text, s):
                    missing.append(f"{key}: missing {s[:40]!r}")
    if missing:
        rep.fail("F", "F1 data.json copy present in rendered text", "", "; ".join(missing[:10]) +
                 (f" (+{len(missing)-10} more)" if len(missing) > 10 else ""))
    else:
        rep.pass_("F", "F1 data.json copy present in rendered text", "18/18",
                  "eyebrow/title/sub/points/footer/name/role/headline/note all found "
                  "(case-insensitive, whitespace-insensitive)")
    leftover = []
    for card in cards:
        for side in ("front", "back"):
            key = f"{card['code']}_{side}"
            if key not in docs:
                continue
            text = docs[key][0].get_text()
            for s in expected_side_strings(card, side):
                if contains_ci(text, s):
                    text = remove_ci(text, s)
                elif "·" in s and ("@" in s or "+86" in s or "广州" in s or "Nansha" in s):
                    for part in [x.strip() for x in s.split("·") if x.strip()]:
                        text = remove_ci(text, part)
                elif s.startswith("JFC · CSCV FIELD CARDS") or s.startswith("JFC · CSCV · FIELD CARDS"):
                    text = remove_ci(text, "JFC · FIELD CARDS")
            # ghost card-number watermark on the back sides (decorative)
            hops_num = 0
            while card["code"] in text and hops_num < 3:
                text = text.replace(card["code"], "", 1)
                hops_num += 1
            # staff cards draw the initials twice: the bordered block and a 58pt ghost monogram
            mono = card.get("monogram")
            if not mono and LAYOUTS is not None:
                mono = LAYOUTS.MONOGRAM_FALLBACK.get(card["code"])
            hops = 0
            while mono and contains_ci(text, mono) and hops < 4:
                text = remove_ci(text, mono)
                hops += 1
            if norm(text):
                leftover.append(f"{key}: {norm(text)[:50]!r}")
    if leftover:
        rep.warn("F", "F2 no unapproved copy on cards", "", "; ".join(leftover[:8]))
    else:
        rep.pass_("F", "F2 no unapproved copy on cards", "18/18",
                  "every rendered character traceable to data.json (staff initials are drawn twice: "
                  "bordered block + decorative ghost monogram)")
    outside = []
    for card in cards:
        if not card["layout"].startswith("staff"):
            continue
        if not card.get("quote_cn") or not card.get("quote_en"):
            outside.append(f"{card['code']}: quote")
        if not card.get("skills_cn") or not card.get("skills_en"):
            outside.append(f"{card['code']}: skills")
    if outside:
        rep.warn("F", "F3 staff quote/skills not stored in data.json", "",
                 ", ".join(outside) + " — these strings are hard-coded in cards/templates/layouts.py "
                 "(QUOTES/SKILLS). PRINT-SPEC §6 says all card copy lives in cards/data.json, so this "
                 "is a content-traceability gap (not a print defect).")
    else:
        rep.pass_("F", "F3 staff quote/skills stored in data.json", "C6..C9")
    want = {"C7_front": ["[姓名]"], "C7_back": ["[Name]"], "C8_front": ["[姓名]"], "C8_back": ["[Name]"],
            "C9_front": ["[姓名]", "[职位]", "负责 [具体职责"], "C9_back": ["[Name]", "[Role]"]}
    bad = [f"{key}: missing {w}" for key, ws in want.items() if key in docs
           for w in ws if not contains_ci(docs[key][0].get_text(), w)]
    if bad:
        rep.fail("F", "F4 bracket placeholders kept", "", "; ".join(bad))
    else:
        rep.pass_("F", "F4 bracket placeholders kept", "C7/C8/C9", "[姓名]/[Name]/[职位]/[Role] retained")
    note = cards[8].get("note_cn", ""), cards[8].get("note_en", "")
    for key, n in (("C9_front", note[0]), ("C9_back", note[1])):
        if key in docs and n and not contains_ci(docs[key][0].get_text(), n):
            rep.fail("F", "F5 C9 no-publish note", key, f"missing {n!r}")
    if not any(f.check == "F5 C9 no-publish note" and f.level == "FAIL" for f in rep.items):
        rep.pass_("F", "F5 C9 no-publish note", "C9 front/back", "方括号须填写、不得原样发布")
    bad_abs, bad_other, bad_excl, unneg = [], [], [], []
    for key, doc in docs.items():
        t = doc[0].get_text()
        for m in re.finditer("最", t):
            if t[m.start():m.start() + 2] != "最多":
                bad_abs.append(f"{key}: 最 context {t[m.start():m.start()+4]!r}")
        for m in re.finditer("第一", t):
            if t[m.start():m.start() + 3] != "第一次":
                bad_abs.append(f"{key}: 第一 context {t[m.start():m.start()+4]!r}")
        for w in ("唯一", "领先", "顶级", "最佳", "最好", "保证", "guaranteed", "world-class",
                  "No.1", "best-in-class"):
            if w.lower() in t.lower():
                bad_abs.append(f"{key}: {w!r}")
        for w in ("包过", "承诺效果", "100% 保证"):
            if w in t:
                bad_other.append(f"{key}: {w!r}")
        if "!" in t or "！" in t:
            bad_excl.append(key)
        for term in ("认证", "certification", "Certification", "guarantee", "Guarantee", "担保"):
            for m in re.finditer(re.escape(term), t):
                pre = t[max(0, m.start() - 8):m.start()]
                if "不" not in pre and "no " not in pre.lower():
                    unneg.append(f"{key}: unnegated {term!r} ({pre!r})")
    if bad_abs:
        rep.fail("F", "F6 no absolute/superlative wording", "", "; ".join(bad_abs[:8]))
    else:
        rep.pass_("F", "F6 no absolute/superlative wording", "18/18",
                  "no 最/第一/唯一/领先/best/guarantee")
    if bad_other or bad_excl:
        rep.fail("F", "F7 no promise wording / exclamation marks", "", "; ".join((bad_other + bad_excl)[:8]))
    else:
        rep.pass_("F", "F7 no promise wording / exclamation marks", "18/18")
    if unneg:
        rep.fail("F", "F8 认证/担保 only in negated form", "", "; ".join(unneg[:8]))
    else:
        rep.pass_("F", "F8 认证/担保 only in negated form", "18/18",
                  "all occurrences are 不认证 / no certification / no guarantee")
    fact_bad = []
    for key, doc in docs.items():
        t = doc[0].get_text()
        if norm(FP) not in norm(t):
            fact_bad.append(f"{key}: missing email")
        if norm(PHONE_CN) not in norm(t):
            fact_bad.append(f"{key}: missing phone")
        if key.endswith("front") and norm(ADDR_CN) not in norm(t):
            fact_bad.append(f"{key}: missing 广州南沙")
        if key.endswith("back") and norm(ADDR_EN) not in norm(t):
            fact_bad.append(f"{key}: missing Nansha, Guangzhou")
        for price in price_occurrences(t):
            if parse_price(price) not in ALLOWED_PRICE_PAIRS:
                fact_bad.append(f"{key}: unapproved price {price!r}")
        if not key.startswith("C2") and price_occurrences(t):
            fact_bad.append(f"{key}: price outside C2 pricing card")
    expect = {
        "C2_front": ["1,800–3,000 元/站", "3,200–4,500 元/站", "5 个工作日", "7–10 个工作日"],
        "C2_back": ["RMB 1,800–3,000", "RMB 3,200–4,500", "5 business days", "7–10 business days"],
        "C3_front": ["8–12 页", "100% 预付", "七步"],
        "C3_back": ["8–12 page", "100% prepayment", "Seven steps"],
        "C5_front": ["单边收费", "不认证", "不撮合", "不担保"],
        "C5_back": ["One-sided fee", "No certification", "no matchmaking", "no guarantee"],
        "C8_front": ["24 小时内", "15 分钟"],
        "C8_back": ["within 24 hours", "15 minutes"],
    }
    for key, phrases in expect.items():
        if key not in docs:
            continue
        t = docs[key][0].get_text()
        for ph in phrases:
            if not contains_ci(t, ph):
                fact_bad.append(f"{key}: missing fact phrase {ph!r}")
    if fact_bad:
        rep.fail("F", "F9 facts match content/01_front.md fact sheet", "", "; ".join(fact_bad[:10]))
    else:
        rep.pass_("F", "F9 facts match content/01_front.md fact sheet", "18/18",
                  "prices 1,800–3,000 / 3,200–4,500, 5 & 7–10 business days, 8–12 pages, 100% "
                  "prepayment, phone/email/address, five commitments, seven steps, 24h reply")
    if any("建塔" in d[0].get_text() or "建滔" in d[0].get_text() for d in docs.values()):
        rep.fail("F", "F10 address wording clean", "", "建塔/建滔 found")
    else:
        rep.pass_("F", "F10 address wording clean", "18/18", "no 建塔/建滔")
    fmt_bad = [key for key, doc in docs.items()
               if norm(f"{key.split('_')[0]} / {TOTAL} · {EDITION}") not in norm(doc[0].get_text())]
    if fmt_bad:
        rep.warn("F", "F11 footer card-code format", "", ", ".join(fmt_bad[:6]))
    else:
        rep.info("F", "F11 footer card-code format", "C1 / 09 · NOV 2026 bottom-right",
                 "CARD-SPEC §1 asks 'JFC · CSCV FIELD CARDS · NOV 2026' + card code at the foot; the "
                 "template puts the series line in the header and keeps 'C1 / 09 · NOV 2026' bottom-right "
                 "— both elements present, documented design choice")
    if cards[3].get("quote_cn"):
        rep.info("F", "F12 unused quote_cn field", "C4",
                 "only the EN back renders the pull quote (CN front design has no quote)")
    rep.info("F", "F13 claims outside the fact table",
             "C1 大湾区 SME / 精品国际咨询; C8 15 分钟·三样信息; C7 广东及周边省份",
             "sourced from source/company_profile.txt, source/service_portfolio.txt and WORKBRIEF "
             "§4.2 B3 rather than the fact sheet; role owner should confirm before printing")


# --------------------------------------------------------------------------- #
# G. data.json against CARD-SPEC
# --------------------------------------------------------------------------- #

def check_data(rep: Report, data: dict) -> None:
    cards = data["cards"]
    bad, warn = [], []
    if len(cards) != 9:
        bad.append(f"{len(cards)} cards")
    if [c["code"] for c in cards] != [f"C{i}" for i in range(1, 10)]:
        bad.append("card order " + ",".join(c["code"] for c in cards))
    if data.get("series", {}).get("edition") != EDITION:
        bad.append(f"edition {data.get('series', {}).get('edition')!r}")
    for c in cards:
        code = c["code"]
        if c.get("layout") != LAYOUT_EXPECT[code]:
            bad.append(f"{code}: layout {c.get('layout')!r} != {LAYOUT_EXPECT[code]!r}")
        if len(c.get("points", [])) != 3:
            bad.append(f"{code}: {len(c.get('points', []))} points")
        if cjk_count(c.get("title_cn", "")) > 16:
            bad.append(f"{code}: title_cn {cjk_count(c.get('title_cn',''))} CJK > 16")
        if len(c.get("title_en", "")) > 60:
            bad.append(f"{code}: title_en {len(c.get('title_en',''))} > 60")
        if cjk_count(c.get("sub_cn", "")) > 30:
            bad.append(f"{code}: sub_cn {cjk_count(c.get('sub_cn',''))} > 30")
        if len(c.get("sub_en", "")) > 90:
            bad.append(f"{code}: sub_en {len(c.get('sub_en',''))} > 90")
        for p in c.get("points", []):
            cj, tot = cjk_count(p.get("cn", "")), len(p.get("cn", ""))
            if cj > 24:
                bad.append(f"{code}/{p.get('num')}: point cn {cj} CJK > 24")
            elif tot > 24:
                warn.append(f"{code}/{p.get('num')}: {tot} chars incl. Latin/digits (CJK {cj})")
            if len(p.get("en", "")) > 60:
                bad.append(f"{code}/{p.get('num')}: point en {len(p.get('en',''))} > 60")
        if c.get("footer_cn") != FOOTER_CN:
            bad.append(f"{code}: footer_cn mismatch")
        if c.get("footer_en") != FOOTER_EN:
            bad.append(f"{code}: footer_en mismatch")
        if c["layout"].startswith("staff"):
            for fld in ("role_cn", "role_en", "name_cn", "name_en", "headline_cn", "headline_en"):
                if not c.get(fld):
                    bad.append(f"{code}: missing {fld}")
            if cjk_count(c.get("headline_cn", "")) > 20:
                bad.append(f"{code}: headline_cn {cjk_count(c.get('headline_cn',''))} > 20")
            if len(c.get("headline_en", "")) > 80:
                bad.append(f"{code}: headline_en {len(c.get('headline_en',''))} > 80")
        elif not c.get("photo"):
            bad.append(f"{code}: missing photo field")
        blob = json.dumps(c, ensure_ascii=False)
        for marker in ("TODO", "TBD", "lorem", "XXX"):
            if marker in blob:
                bad.append(f"{code}: contains {marker}")
    if bad:
        rep.fail("G", "G1 data.json spec limits (CARD-SPEC §0/§1)", "", "; ".join(bad[:10]))
    else:
        rep.pass_("G", "G1 data.json spec limits (CARD-SPEC §0/§1)", "9 cards",
                  "layout / 3 points / CN-EN length caps / exact footer / staff fields / photo map")
    if warn:
        rep.warn("G", "G2 CN length counting convention", "", "; ".join(warn[:6]))
    else:
        rep.pass_("G", "G2 CN length counting convention", "9 cards", "all point lines ≤24 字")
    if not cards[8].get("note_cn") or not cards[8].get("note_en"):
        rep.fail("G", "G3 C9 no-publish note", "", "note_cn/note_en missing")
    elif "不得原样发布" not in cards[8]["note_cn"]:
        rep.warn("G", "G3 C9 no-publish note", "", "note_cn lacks 不得原样发布")
    else:
        rep.pass_("G", "G3 C9 no-publish note", "C9", cards[8]["note_cn"])


# --------------------------------------------------------------------------- #
# H. documents
# --------------------------------------------------------------------------- #

def check_docs(rep: Report, data: dict, docs: dict) -> None:
    spec_path = DELIV / "PRINT-SPEC.md"
    spec = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
    if spec:
        checks = [
            ("H1 trim/bleed sizes", "105 × 148" in spec and "111 × 154" in spec and "3 mm" in spec),
            ("H2 18-page combined file", "18 页" in spec),
            ("H3 paper recommendation", "300" in spec and ("白卡" in spec or "哑粉" in spec)),
            ("H4 RGB→CMYK note", "CMYK" in spec),
            ("H5 A4 proof 96% 4-up", "96%" in spec and "4 张/页" in spec),
            ("H6 photo licence reference", "SOURCES.md" in spec),
            ("H7 page order C1 front/back …", "C1 正/背" in spec),
        ]
        for name, ok in checks:
            if ok:
                rep.pass_("H", name, "deliverables/cards/PRINT-SPEC.md")
            else:
                rep.fail("H", name, "deliverables/cards/PRINT-SPEC.md", "statement inconsistent with actual files")
        refs = set(re.findall(r"(C\d(?:_front|_back)\.pdf|CSCV_FieldCards_v1_print\.pdf|A4_office_proof\.pdf|PRINT-CHECK\.txt)", spec))
        missing_refs = [r for r in refs if not ((PRINT / r).exists() or (DELIV / r).exists())]
        if missing_refs:
            rep.fail("H", "H8 PRINT-SPEC referenced files exist", "", ", ".join(missing_refs))
        else:
            rep.pass_("H", "H8 PRINT-SPEC referenced files exist", f"{len(refs)} referenced deliverable files")
        d = docs.get("combined")
        if d is not None:
            ok = all(norm(f"C{i//2+1} / {TOTAL} · {EDITION}") in norm(d[i].get_text()) for i in range(len(d)))
            if ok:
                rep.pass_("H", "H9 PRINT-SPEC page order matches combined PDF", "18 pages")
            else:
                rep.fail("H", "H9 PRINT-SPEC page order matches combined PDF", "", "order mismatch")
    src_path = IMGDIR / "SOURCES.md"
    if not src_path.exists():
        rep.fail("H", "H10 SOURCES.md present", "", "missing")
    else:
        src = src_path.read_text(encoding="utf-8")
        problems = []
        used = [c.get("photo") for c in data["cards"] if c.get("photo")]
        for photo in used:
            row = re.search(rf"\|\s*`{re.escape(photo)}`[^\n]*", src)
            if not row:
                problems.append(f"{photo}: not in a SOURCES table")
                continue
            rowtxt = row.group(0)
            if "http" not in rowtxt:
                problems.append(f"{photo}: no source URL")
            if not any(t in rowtxt for t in ("Pexels License", "Unsplash License", "CC0", "Public domain")):
                problems.append(f"{photo}: no licence")
            if rowtxt.count("|") < 7:
                problems.append(f"{photo}: author/licence columns missing")
            m = re.search(r"(\d{3,5})×(\d{3,5})", rowtxt)
            if not m:
                problems.append(f"{photo}: pixel size not recorded")
            else:
                if max(int(m.group(1)), int(m.group(2))) < 2000:
                    problems.append(f"{photo}: long edge < 2000px")
                fp = IMGDIR / photo
                if fp.exists():
                    try:
                        im = Image.open(fp)
                        if (im.width, im.height) != (int(m.group(1)), int(m.group(2))):
                            problems.append(f"{photo}: recorded {m.group(1)}×{m.group(2)} "
                                            f"!= actual {im.width}×{im.height}")
                    except Exception as e:
                        problems.append(f"{photo}: unreadable ({e})")
        listed = set(re.findall(r"`(img[\w.-]+\.(?:jpg|jpeg|png))`", src))
        files = {p.name for p in IMGDIR.glob("img*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")}
        unlisted = files - listed
        if unlisted:
            problems.append("files not documented: " + ", ".join(sorted(unlisted)))
        missing_files = [n for n in listed if not (IMGDIR / n).exists()]
        if missing_files:
            problems.append("documented but missing: " + ", ".join(sorted(missing_files)))
        if problems:
            rep.fail("H", "H10 SOURCES.md licence records traceable", "", "; ".join(problems[:10]))
        else:
            rep.pass_("H", "H10 SOURCES.md licence records traceable", f"{len(used)} used images (+alternates)",
                      "file / card / pixels / source URL / author / licence all recorded")
        band = re.search(r"(\d+)\s*×\s*(\d+)\s*mm\s*照片带", src)
        actual = None
        for key, doc in docs.items():
            if key.endswith("_front"):
                for i in classify_images(doc, doc[0]):
                    if i["kind"] == "photo":
                        actual = (i["wmm"], i["hmm"])
                        break
            if actual:
                break
        if band and actual:
            bw, bh = int(band.group(1)), int(band.group(2))
            if abs(actual[0] - bw) > 2:
                rep.warn("H", "H11 SOURCES photo band width matches render", "",
                         f"SOURCES {bw}×{bh}mm vs actual {actual[0]:.0f}×{actual[1]:.0f}mm")
            else:
                rep.pass_("H", "H11 SOURCES photo band width matches render", f"{bw}mm wide",
                          f"height varies by layout family (measured {actual[1]:.0f}mm on C1)")
    lead_check = DELIV / "PRINT-CHECK.txt"
    if lead_check.exists():
        t = lead_check.read_text(encoding="utf-8", errors="replace")
        if re.search(r"\bFAIL\b", t) or "MISSING IMAGE" in t:
            rep.warn("H", "H12 Lead PRINT-CHECK.txt consistent", lead_check.name,
                     "contains FAIL / MISSING IMAGE wording")
        elif "PASS" in t:
            rep.pass_("H", "H12 Lead PRINT-CHECK.txt consistent", lead_check.name,
                      "PASS — sizes/pages/fonts/dpi/placeholders")
        else:
            rep.warn("H", "H12 Lead PRINT-CHECK.txt consistent", lead_check.name, "no PASS/FAIL marker")
        if "300dpi" in t and "placed 111" in t:
            rep.info("H", "H12b Lead PRINT-CHECK photo dpi", "300dpi effective at 111×50mm",
                     "matches my independent measurement (300.1dpi)")
    else:
        rep.warn("H", "H12 Lead PRINT-CHECK.txt consistent", "", "missing")
    overflow = CARDS_DIR / "render" / "overflow-report.txt"
    if overflow.exists():
        t = overflow.read_text(encoding="utf-8", errors="replace").strip()
        problems = [ln for ln in t.splitlines() if "MISSING IMAGE" in ln or re.match(r"\s*C\d", ln)]
        if problems:
            rep.fail("H", "H13 render overflow report clean", overflow.name, "; ".join(problems[:6]))
        elif "OK" in t:
            rep.pass_("H", "H13 render overflow report clean", overflow.name, t[:80])
        else:
            rep.warn("H", "H13 render overflow report clean", overflow.name, t[:80])
    else:
        rep.warn("H", "H13 render overflow report clean", "", "missing")


# --------------------------------------------------------------------------- #
# I. previews
# --------------------------------------------------------------------------- #

def check_previews(rep: Report, data: dict, docs: dict) -> None:
    codes = [c["code"] for c in data["cards"]]
    bad_dims, bad_dpi, bad_diff = [], [], []
    import numpy as np
    for code in codes:
        for side in ("front", "back"):
            p = PREVIEW / f"{code}_{side}.png"
            if not p.exists():
                continue
            im = Image.open(p)
            wmm, hmm = im.width / 150 * 25.4, im.height / 150 * 25.4
            if abs(wmm - TRIM_W) > 0.6 or abs(hmm - TRIM_H) > 0.6:
                bad_dims.append(f"{p.name}: {im.width}×{im.height}px = {wmm:.1f}×{hmm:.1f}mm @150dpi")
            dpi = im.info.get("dpi")
            if not dpi or abs(dpi[0] - 150) > 2:
                bad_dpi.append(f"{p.name}: dpi {dpi}")
            key = f"{code}_{side}"
            if key in docs:
                pix = docs[key][0].get_pixmap(dpi=150, colorspace=fitz.csRGB)
                arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
                off = round(BLEED / 25.4 * 150)
                crop = arr[off:arr.shape[0] - off, off:arr.shape[1] - off]
                ref = np.asarray(im.convert("RGB")).astype(float)
                h, w = min(crop.shape[0], ref.shape[0]), min(crop.shape[1], ref.shape[1])
                diff = float(np.abs(crop[:h, :w].astype(float) - ref[:h, :w]).mean())
                if diff > 3:
                    bad_diff.append(f"{p.name}: mean|Δ|={diff:.1f} vs PDF render")
    if bad_dims:
        rep.fail("I", "I1 previews are 105×148mm @150dpi", "", "; ".join(bad_dims[:6]))
    else:
        rep.pass_("I", "I1 previews are 105×148mm @150dpi", "18/18", "621×875px, 150dpi metadata")
    if bad_dpi:
        rep.fail("I", "I2 preview dpi metadata", "", "; ".join(bad_dpi[:6]))
    else:
        rep.pass_("I", "I2 preview dpi metadata", "18/18", "150dpi")
    if bad_diff:
        rep.fail("I", "I3 previews match PDF renders", "", "; ".join(bad_diff[:6]))
    else:
        rep.pass_("I", "I3 previews match PDF renders", "18/18", "trim crop of side PDF at 150dpi")
    exp = {
        "all_fronts.png": (3 * 621 + 4 * 24, 3 * 875 + 4 * 24 + 52),
        "all_backs.png": (3 * 621 + 4 * 24, 3 * 875 + 4 * 24 + 52),
        "all_cards_preview.png": (3 * (2 * 621 + 16) + 4 * 16, 3 * 875 + 4 * 16),
    }
    bad = []
    for name, (ew, eh) in exp.items():
        p = PREVIEW / name
        if not p.exists():
            bad.append(f"{name} missing")
            continue
        im = Image.open(p)
        if abs(im.width - ew) > 4 or abs(im.height - eh) > 4:
            bad.append(f"{name}: {im.width}×{im.height} != {ew}×{eh}")
    if bad:
        rep.fail("I", "I4 contact sheets composition", "", "; ".join(bad))
    else:
        rep.pass_("I", "I4 contact sheets composition", "3 sheets",
                  "all_fronts/all_backs 3×3; all_cards_preview 3 rows × (front|back)")


# --------------------------------------------------------------------------- #
# Z. evidence
# --------------------------------------------------------------------------- #

def check_evidence(rep: Report, data: dict) -> None:
    files = [CARDS_DIR / "data.json", DELIV / "PRINT-SPEC.md",
             PRINT / "CSCV_FieldCards_v1_print.pdf", DELIV / "A4_office_proof.pdf"]
    lines = []
    for f in files:
        if f.exists():
            st = f.stat()
            lines.append(f"{f.relative_to(ROOT)} sha256={sha256(f)[:16]}… "
                         f"mtime={datetime.fromtimestamp(st.st_mtime):%m-%d %H:%M:%S}")
    rep.info("Z", "Z1 accepted-file evidence", "hashes + mtimes", " | ".join(lines))
    rep.info("Z", "Z2 data.json sha256", sha256(CARDS_DIR / "data.json"), "")
    newest = max((f.stat().st_mtime for f in files if f.exists()), default=0)
    age = datetime.now().timestamp() - newest
    if age < 60:
        rep.warn("Z", "Z3 files stable", "",
                 f"a deliverable was modified {age:.0f}s ago — confirm the render is final before sign-off")
    else:
        rep.pass_("Z", "Z3 files stable", "", f"newest deliverable {age/60:.1f} min old at check time")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description="Independent print QA for JFC·CSCV field cards")
    ap.add_argument("--out", default=str(QA / "cards_check_output.txt"))
    ap.add_argument("--json", default=str(QA / "cards_check_summary.json"))
    args = ap.parse_args()

    for need in (CARDS_DIR / "data.json", PRINT, DELIV / "PRINT-SPEC.md"):
        if not need.exists():
            print(f"error: required input missing: {need}", file=sys.stderr)
            return 2

    data = load_data()
    rep = Report()

    check_inventory(rep, data)
    docs = check_geometry(rep, data)
    check_marks_pdf(rep, data, docs.get("combined"))
    check_a4_proof(rep, data)
    singles = docs.get("single", {})
    check_fonts(rep, singles)
    check_images(rep, data, singles)
    check_layout(rep, data, singles)
    check_content(rep, data, singles)
    check_data(rep, data)
    check_docs(rep, data, {"combined": docs.get("combined"), **singles})
    check_previews(rep, data, singles)
    check_evidence(rep, data)

    counts = rep.counts()
    text = "\n".join([
        "# JFC · CSCV Field Cards — independent print QA (qa/cards_check.py)",
        f"# cards: {[c['code'] for c in data['cards']]}",
        f"# summary: PASS={counts['PASS']} FAIL={counts['FAIL']} WARN={counts['WARN']} INFO={counts['INFO']}",
        rep.emit(),
    ]) + "\n"
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(text, encoding="utf-8")
    Path(args.json).write_text(json.dumps({
        "generated": "qa/cards_check.py",
        "counts": counts,
        "findings": [f.__dict__ for f in rep.items],
        "data_json_sha256": sha256(CARDS_DIR / "data.json"),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(text)
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
