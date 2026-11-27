# -*- coding: utf-8 -*-
"""Build and QA every banner in the kit.

Renders banners/<brand>/src/<format>.html -> banners/<brand>/png/<format>.png
(+ @2x), writes safe-zone diagrams to preview/safe-zones/, and runs the QA probe
(DOM bounds vs safe areas, blocked UI rects, fonts, bilingual pairing, overflow,
minimum type size, element collisions).

Usage:
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
        banners/kit/tools/build.py              # build + QA + report
    ... build.py --only jfc                  # one brand
    ... build.py --qa-only                   # QA existing PNGs
    ... build.py --skip-overlay              # no safe-zone diagrams
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[3]
KIT = ROOT / "banners" / "kit"
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(KIT / "tools"))

from PIL import Image  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from platform_specs import ORDER, PLATFORMS  # noqa: E402
import render as R  # noqa: E402

BRANDS = ["jfc", "cscv"]
BRAND_LABEL = {"jfc": "JFC", "cscv": "CSCV"}
REQUIRED_FONTS = {
    "jfc": ["avenir", "pingfang"],
    "cscv": ["archivo", "inter", "mono", "pingfang"],
}
MIN_FS_FAIL = 9.5
MIN_FS_WARN = 10.5


def _cjk_count(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def _latin_count(text: str) -> int:
    return sum(1 for ch in text if ch.isascii() and ch.isalpha())


def _intersect(a, b) -> tuple[float, float]:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    return ix, iy


def _inside(rect, safe, tol=1.5) -> bool:
    x, y, w, h = rect
    sx, sy, sw, sh = safe
    return (
        x >= sx - tol
        and y >= sy - tol
        and x + w <= sx + sw + tol
        and y + h <= sy + sh + tol
    )


def check_banner(brand: str, fmt: str, html: pathlib.Path, png: pathlib.Path, probe: dict):
    spec = PLATFORMS[fmt]
    w, h = spec["canvas"]
    safe = spec["safe"]
    blocked = [b for b in spec["blocked"] if b[2] > 0 and b[3] > 0]
    checks = []

    def add(name, ok, detail="", level="fail"):
        checks.append({"name": name, "ok": ok, "detail": detail, "level": level if not ok else "pass"})

    # 1. exported PNG size
    im = Image.open(png)
    add("png_size", im.size == (w, h), f"{im.size} vs {(w, h)}")
    im2p = png.with_name(png.stem + "@2x.png")
    if im2p.exists():
        add("png_2x_size", Image.open(im2p).size == (w * 2, h * 2), f"{Image.open(im2p).size} vs {(w*2, h*2)}")

    # 2. single artboard, no page overflow
    add("artboard", probe["artCount"] == 1, f"artboards={probe['artCount']}")
    add("no_overflow", probe["scrollW"] <= w + 1 and probe["scrollH"] <= h + 1,
        f"scroll={probe['scrollW']}x{probe['scrollH']}")

    # 3. critical content inside safe area / outside platform UI
    crit = [c for c in probe["crit"] if c["w"] > 0 and c["h"] > 0]
    add("critical_present", len(crit) >= 3, f"{len(crit)} critical elements")
    out = [c for c in crit if not _inside((c["x"], c["y"], c["w"], c["h"]), safe)]
    add("inside_safe", not out, "; ".join(
        f"{c['text'][:24]!r}@({c['x']:.0f},{c['y']:.0f},{c['w']:.0f},{c['h']:.0f})" for c in out[:5]))
    hits = []
    for c in crit:
        for b in blocked:
            ix, iy = _intersect((c["x"], c["y"], c["w"], c["h"]), b)
            if ix > 1 and iy > 1:
                hits.append(f"{c['text'][:20]!r} x blocked {b}")
    add("outside_blocked", not hits, "; ".join(hits[:5]))

    # 4. collisions between critical elements
    coll = []
    for i in range(len(crit)):
        for j in range(i + 1, len(crit)):
            a, b = crit[i], crit[j]
            ix, iy = _intersect((a["x"], a["y"], a["w"], a["h"]), (b["x"], b["y"], b["w"], b["h"]))
            if ix > 2 and iy > 2:
                coll.append(f"{a['text'][:18]!r} x {b['text'][:18]!r} ({ix:.0f}x{iy:.0f})")
    add("no_text_collision", not coll, "; ".join(coll[:5]))

    # 5. fonts
    fonts = probe["fonts"]
    missing = [f for f in REQUIRED_FONTS[brand] if not fonts.get(f)]
    add("fonts_loaded", not missing, f"missing={missing}; {fonts}")

    # 6. bilingual
    body = probe["bodyText"]
    add("bilingual", _cjk_count(body) > 5 and _latin_count(body) > 20,
        f"cjk={_cjk_count(body)} latin={_latin_count(body)}")
    langs = {c["lang"] for c in crit if c["lang"]}
    add("lang_pairs", {"zh", "en"} <= langs, f"langs={sorted(langs)}")

    # 7. minimum type size
    small = [t for t in probe["texts"] if 0 < t["fs"] < MIN_FS_FAIL]
    add("min_font", not small, "; ".join(f"{t['text'][:24]!r} {t['fs']:.1f}px" for t in small[:6]))
    warn = [t for t in probe["texts"] if MIN_FS_FAIL <= t["fs"] < MIN_FS_WARN]
    if warn:
        add("small_font_warn", True,
            "; ".join(f"{t['text'][:24]!r} {t['fs']:.1f}px" for t in warn[:6]), level="warn")

    return checks


def run_build(brands, qa_only=False, overlay=True):
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for brand in brands:
                results[brand] = {}
                for fmt in ORDER:
                    html = ROOT / "banners" / brand / "src" / f"{fmt}.html"
                    png = ROOT / "banners" / brand / "png" / f"{fmt}.png"
                    if not html.exists():
                        results[brand][fmt] = {"status": "missing", "checks": []}
                        continue
                    if qa_only:
                        if not png.exists():
                            results[brand][fmt] = {"status": "missing_png", "checks": []}
                            continue
                        probe = _probe_existing(browser, html, fmt)
                    else:
                        r = R.render_one(browser, html, png, fmt)
                        probe = r["probe"]
                    checks = check_banner(brand, fmt, html, png, probe)
                    fails = [c for c in checks if not c["ok"] and c["level"] == "fail"]
                    warns = [c for c in checks if not c["ok"] and c["level"] == "warn"]
                    results[brand][fmt] = {
                        "status": "fail" if fails else ("warn" if warns else "pass"),
                        "checks": checks,
                    }
                    if overlay and not qa_only:
                        out = ROOT / "preview" / "safe-zones" / f"{brand}-{fmt}-safe.png"
                        R.render_one(browser, html, out, fmt, overlay=True)
        finally:
            browser.close()
    return results


def _probe_existing(browser, html, fmt):
    spec = PLATFORMS[fmt]
    w, h = spec["canvas"]
    page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    R._prepare_page(page, html)
    probe = page.evaluate(R.PROBE_JS)
    page.close()
    return probe


def write_report(results):
    qa = ROOT / "qa"
    qa.mkdir(exist_ok=True)
    (qa / "report.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    lines = ["# Banner QA report", "", "Brands: JFC (`jfc`) and CSCV (`cscv`). Each banner is checked for exact export size, single artboard, no page overflow, critical content inside the platform safe area and outside platform-UI blocked rects, no text collisions, required fonts loaded, bilingual pairing, and minimum type size.", ""]
    total = fails = warns = 0
    for brand, fmts in results.items():
        lines.append(f"## {BRAND_LABEL[brand]} — {brand}")
        lines.append("")
        lines.append("| format | status | detail |")
        lines.append("|---|---|---|")
        for fmt in ORDER:
            r = fmts.get(fmt)
            if not r:
                continue
            total += 1
            bad = [c for c in r["checks"] if not c["ok"] and c["level"] == "fail"]
            wrn = [c for c in r["checks"] if not c["ok"] and c["level"] == "warn"]
            fails += 1 if bad else 0
            warns += 1 if wrn and not bad else 0
            if r["status"] == "missing":
                detail = "HTML not built yet"
            elif bad:
                detail = "; ".join(f"**{c['name']}**: {c['detail']}" for c in bad[:4])
            elif wrn:
                detail = "; ".join(f"warn {c['name']}: {c['detail']}" for c in wrn[:3])
            else:
                detail = "all checks pass"
            lines.append(f"| `{fmt}` | {r['status']} | {detail} |")
        lines.append("")
    lines.append(f"**{total} banners checked, {fails} with failures, {warns} with warnings.**")
    (qa / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=BRANDS + ["all"], default="all")
    ap.add_argument("--qa-only", action="store_true")
    ap.add_argument("--skip-overlay", action="store_true")
    args = ap.parse_args()
    brands = BRANDS if args.only == "all" else [args.only]
    results = run_build(brands, qa_only=args.qa_only, overlay=not args.skip_overlay)
    fails = write_report(results)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
