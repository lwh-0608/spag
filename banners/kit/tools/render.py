# -*- coding: utf-8 -*-
"""Render banner HTML artboards to exact-size PNGs with headless Chromium.

Usage (from the ticket root):
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
        banners/kit/tools/render.py banners/jfc/src/linkedin-personal.html \
        --format linkedin-personal --out /tmp/test.png

The artboard is rendered at 2x device pixel ratio and downsampled to the exact
deliverable size, so text edges are clean. A @2x file is also written next to
the 1x file (suffix @2x) for platforms that accept retina uploads.
"""
from __future__ import annotations

import argparse
import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]  # ticket root
KIT = ROOT / "banners" / "kit"
sys.path.insert(0, str(KIT))

from PIL import Image  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from platform_specs import PLATFORMS  # noqa: E402

PROBE_JS = r"""
() => {
  const crit = [...document.querySelectorAll('[data-critical]')].map(el => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {
      tag: el.tagName.toLowerCase(),
      text: ((el.innerText || el.alt || '') + '').trim().slice(0, 90),
      lang: el.dataset.lang || null,
      x: r.x, y: r.y, w: r.width, h: r.height,
      fs: parseFloat(cs.fontSize) || 0,
      color: cs.color,
    };
  });
  const texts = [...document.querySelectorAll('body *')].filter(el => {
    if (el.children.length) return false;
    const t = (el.innerText || '').trim();
    return t.length > 0 && t.length < 200;
  }).map(el => ({
    text: (el.innerText || '').trim().slice(0, 60),
    fs: parseFloat(getComputedStyle(el).fontSize) || 0,
  }));
  const fonts = {
    status: document.fonts.status,
    avenir: document.fonts.check('600 16px "Avenir Next"'),
    pingfang: document.fonts.check('600 16px "PingFang SC"'),
    archivo: document.fonts.check('800 16px "Archivo"'),
    inter: document.fonts.check('400 16px "Inter"'),
    mono: document.fonts.check('400 16px "JetBrains Mono"'),
  };
  return {
    artCount: document.querySelectorAll('.art').length,
    crit, texts, fonts,
    scrollW: document.documentElement.scrollWidth,
    scrollH: document.documentElement.scrollHeight,
    bodyText: document.body.innerText || '',
  };
}
"""


def _prepare_page(page, html_path: pathlib.Path):
    page.goto(html_path.resolve().as_uri(), wait_until="load")
    page.wait_for_function("document.fonts.status === 'loaded'", timeout=20000)
    page.evaluate(
        "() => Promise.all([...document.images].map(i => i.decode().catch(() => {})))"
    )
    page.wait_for_timeout(120)


def render_page(
    browser,
    html_path: pathlib.Path,
    out_png: pathlib.Path,
    w: int,
    h: int,
    *,
    overlay: bool = False,
    dsf: int = 2,
) -> dict:
    page = browser.new_page(
        viewport={"width": w, "height": h},
        device_scale_factor=dsf,
    )
    _prepare_page(page, html_path)
    shot = page.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h})
    probe = page.evaluate(PROBE_JS)
    page.close()
    img = Image.open(io.BytesIO(shot)).convert("RGB")
    if img.size != (w, h):
        img = img.resize((w, h), Image.LANCZOS)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png, optimize=True)
    return {"png": img, "probe": probe}


def render_one(
    browser,
    html_path: pathlib.Path,
    out_png: pathlib.Path,
    fmt: str,
    *,
    overlay: bool = False,
    dsf: int = 2,
) -> dict:
    spec = PLATFORMS[fmt]
    w, h = spec["canvas"]
    page = browser.new_page(
        viewport={"width": w, "height": h},
        device_scale_factor=dsf,
    )
    _prepare_page(page, html_path)
    if overlay:
        _inject_safe_overlay(page, fmt)
    shot = page.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h})
    probe = page.evaluate(PROBE_JS)
    page.close()

    img = Image.open(io.BytesIO(shot)).convert("RGB")
    if img.size != (w, h):
        img = img.resize((w, h), Image.LANCZOS)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png, optimize=True)
    if not overlay:
        # keep the 2x render as an optional retina upload
        two = Image.open(io.BytesIO(shot)).convert("RGB")
        two.save(out_png.with_name(out_png.stem + "@2x.png"), optimize=True)
    return {"png": img, "probe": probe, "spec": spec}


def _inject_safe_overlay(page, fmt: str):
    spec = PLATFORMS[fmt]
    x, y, w, h = spec["safe"]
    blocked = spec["blocked"]
    page.evaluate(
        """([x, y, w, h, blocked]) => {
        const add = (rect, style) => {
            const d = document.createElement('div');
            d.style.cssText = 'position:fixed;z-index:9999;pointer-events:none;' + style;
            d.style.left = rect[0] + 'px'; d.style.top = rect[1] + 'px';
            d.style.width = rect[2] + 'px'; d.style.height = rect[3] + 'px';
            document.body.appendChild(d);
        };
        add([x, y, w, h], 'outline:2px dashed rgba(0,200,120,.95);outline-offset:-2px;');
        for (const b of blocked) {
            add(b, 'background:repeating-linear-gradient(45deg,rgba(255,60,60,.35) 0 6px,rgba(255,60,60,.12) 6px 12px);border:1px solid rgba(255,60,60,.8);');
        }
    }""",
        [x, y, w, h, blocked],
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--format", required=True, choices=list(PLATFORMS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--overlay", action="store_true")
    args = ap.parse_args()
    html_path = pathlib.Path(args.html)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            render_one(
                browser,
                html_path,
                pathlib.Path(args.out),
                args.format,
                overlay=args.overlay,
            )
        finally:
            browser.close()
    print(f"rendered {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
