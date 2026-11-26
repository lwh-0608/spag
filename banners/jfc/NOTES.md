# JFC — INSTITUTIONAL BLUE · social banner set · design notes

Brand: **JFC company brand** (`banners/jfc/`). Visual system: **Institutional Blue** — navy field
`linear-gradient(104deg,#061A3B 0%,#0A295B 58%,#0B2C61 100%)`, ice `#E7F0FD` type, official white logo,
one thin green `#2E9D74` signal rule per banner, ice hairline inset frame, faint construction grid fading
right, white leaf silhouette at 9.5–10 % opacity bled from a corner. Type: Avenir Next (latin) + PingFang SC
(Chinese), via `banners/kit/css/base.css` + `banners/kit/css/jfc.css`. Copy only from `JFC_COPY`.
All formats are standalone HTML artboards with absolute px positions at the exact export canvas size.

Built by the JFC banner designer (task-1). The `linkedin-personal` 1584×396 flagship was built by the Lead
and is **not** rebuilt here; it is the reference for layout rhythm, classes and tone.

## Files

| format | source | exports |
|---|---|---|
| linkedin-company | `banners/jfc/src/linkedin-company.html` | `png/linkedin-company.png` (1512×256), `png/linkedin-company@2x.png` (3024×512) |
| x-header | `banners/jfc/src/x-header.html` | `png/x-header.png` (1500×500), `png/x-header@2x.png` (3000×1000) |
| facebook-cover | `banners/jfc/src/facebook-cover.html` | `png/facebook-cover.png` (820×360), `png/facebook-cover@2x.png` (1640×720) |
| youtube-channel | `banners/jfc/src/youtube-channel.html` | `png/youtube-channel.png` (2560×1440), `png/youtube-channel@2x.png` (5120×2880) |

Render (from the ticket root; `@2x` is written automatically next to the 1x file):

```bash
PY=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
$PY banners/kit/tools/render.py banners/jfc/src/<format>.html --format <format> --out banners/jfc/png/<format>.png
$PY banners/kit/tools/render.py banners/jfc/src/<format>.html --format <format> --out /tmp/safe.png --overlay
```

## Format notes

### linkedin-company — 1512×256 (safe 24,24,1464,208 · blocked 30,206,120,50 page logo)

A horizontal ribbon rather than a paste of the 1584×396 layout. Two groups:

- **Left identity cluster** — logo (h 44) at 56,32; the single green signal bar 40×3 at 58,86; kicker at
  58,96; Chinese headline 38 px at 52,120; English headline 17 px at 58,170. Left content ends at y≈193,
  i.e. 13 px above the blocked page-logo rect (top y 206) — the obstructed bottom-left corner stays empty.
- **Right column** — contact 15 px at top (y 44), coordinates meta (mono 11 px) at y 72, and the
  CSCV "paid only by the buyer" service pair right-aligned at y 168 / 192.
- Decoration: inset frame 14 px, grid, leaf bled from the top-right corner (opacity .095).

**Copy used:** kicker (EN), headline_cn, headline_en, service_cn, service_en, contact, meta_cn.
**Copy dropped:** positioning_cn / positioning_en — the 256 px ribbon cannot carry the four-item
positioning line plus the service line at ≥11 px legibly; the brief explicitly allows compressing or
dropping it, and the service line was kept. meta_en dropped (redundant with meta_cn, as on the flagship).

### x-header — 1500×500 (safe 24,40,1452,420 · blocked 0,360,220,140 avatar)

The most spacious format; built as a two-part composition that keeps the whole bottom-left 220×140 clear:

- **Left** — logo (h 58) at 72,52; kicker at 74,132; Chinese headline 58 px at 68,160; English headline
  21 px at 74,240; green rule 64×3 at 74,288; positioning pair at 74,306 (CN 14 px) / 332 (EN 12 px).
  Left content ends at y≈348, 12 px above the block.
- **Right** — contact 14 px and coordinates meta at the top (y 56 / 82); the service pair right-aligned at
  the bottom (y 392 / 416). The large leaf + frame carry the right-hand field, so the middle stays quiet.
- Decoration: inset frame 16 px, grid, leaf from top-right (opacity .10).

**Copy used:** kicker (EN), headline_cn, headline_en, positioning_cn, positioning_en, service_cn,
service_en, contact, meta_cn (= every JFC_COPY line except the Chinese kicker and meta_en).
**Copy dropped:** meta_en only (meta_cn is the paired place line used on the flagship).

### facebook-cover — 820×360 (safe 90,24,640,312 · blocked 0,270,100,90 avatar)

Built entirely for the mobile 640×360 crop: every content element sits ≥24 px inside the 640 px mobile
frame, so nothing is cut on phones, and the outer 90 px stays decoration only. Fewer elements, larger type:

- Logo (h 40) at 114,46 · kicker 12 px at 116,100 · Chinese headline 34 px at 110,122 · English headline
  17 px at 116,168 · green rule 40×3 at 116,228 · service pair at 116,242 (CN 13 px) / 266 (EN 11 px).
- Contact 14 px and coordinates meta 12 px sit top-right (y 46 / 72) opposite the logo; the bottom-left
  blocked avatar corner stays empty (all text starts at x ≥ 110, i.e. outside the blocked rect).
- Decoration: inset frame 14 px (trimmed by the mobile crop, as intended), grid, leaf from top-right (.10).

**Copy used:** kicker (EN), headline_cn, headline_en, service_cn, service_en, contact, meta_cn.
**Copy dropped:** positioning_cn / positioning_en — the English positioning line would need ~800 px at
≥11 px uppercase, well beyond the 640 px mobile-safe width; the proof line carries the message instead.
meta_en dropped.

### youtube-channel — 2560×1440 (safe 507,508,1546,423)

Everything essential lives inside the 1546×423 band with ~44 px breathing room top and bottom, because
that band is the only part guaranteed to be visible on every device:

- Band content — logo (h 56) at 552,552 · kicker 18 px at 554,622 · Chinese headline 112 px at 548,655
  (≈2× the 58 px flagship size) · English headline 28 px at 554,787 · green rule 72×4 at 556,830 ·
  service pair at 556,842 (CN 18 px) / 872 (EN 13 px). Contact 22 px top-right at y 552; coordinates
  meta 14 px bottom-right at y 872, baseline-aligned with the English service line so the band closes on
  one footer line.
- TV-only decoration (outside the safe band) — inset frame 120 px, the construction grid, and the leaf
  silhouette kept entirely above y 440 so it never washes the band.
- Verified with simulated view crops: desktop slice `y 508–931` (2560×423) and the centred mobile slice
  (1546×423); both read as a designed band with clear margins.

**Copy used:** kicker (EN), headline_cn, headline_en, service_cn, service_en, contact, meta_cn.
**Copy dropped:** positioning_cn / positioning_en — at the required 2–3× flagship type scale the 423 px
band can carry logo + kicker + headline pair + proof line, not a fourth hierarchy level; the CSCV proof
line is the stronger, differentiating line. meta_en dropped.

## Shared decisions

- Hierarchy is identical in all four formats: logo → kicker → Chinese headline → English headline →
  green signal rule → proof/service line → mono meta; contact mirrors it at top-right. Same margin logic:
  logo/headline start ≈ 52–74 px from the artboard edge (the safe rect alone is not used as the margin).
- Exactly one green rule per banner; no other accent colour; official white logo unaltered; the leaf is
  the only image, and only as an 9.5–10 % watermark. No rounded corners, no shadows, no photos.
- Chinese and English are always separate paired lines, never mixed inside one line; English rendered
  uppercase with letterspacing only where the kit's label class does that. Copy is verbatim from
  `JFC_COPY` (the Chinese kicker variant and `meta_en` are the two lines not used).
- Minimum rendered type size is 11 px at 1× everywhere (mono meta 11–14 px), i.e. no QA "small font"
  warning; the flagship's 9.5 px English labels were not copied downward.

## Checks performed

- **Kit QA probe** (read-only reuse of `banners/kit/tools/build.py: check_banner` via a throwaway
  `/tmp/jfc_probe.py`; nothing written to `qa/` or `preview/`): every one of the four formats passes
  `png_size`, `png_2x_size`, `artboard`, `no_overflow`, `critical_present`, `inside_safe`,
  `outside_blocked`, `no_text_collision`, `fonts_loaded` (Avenir Next + PingFang SC both present),
  `bilingual`, `lang_pairs` (`zh`+`en` both tagged on critical elements) and `min_font`.
- **Safe-zone proofs** rendered with `--overlay` to `/tmp` and inspected for all four formats: green
  must-keep rect contains all critical elements; red hatched platform-UI rects contain none. LinkedIn
  blocked page-logo and X/Facebook avatar areas are visibly clear.
- **Visual review**: full renders inspected, plus 100 % crops from the `@2x` exports (headline, kicker,
  footer lines) to confirm no clipped glyphs, no collisions, no accidental underlines, crisp type; PNG only
  (no banding). Contact-sheet comparison of all five JFC formats confirms one family.
- **Platform-view simulations**: YouTube desktop strip (2560×423) and mobile strip (1546×423), Facebook
  mobile crop (640×360) — all content visible and comfortable, none touching a crop edge.
- Iterated three times on the vertical rhythm (kicker→headline and service-line gaps), the Facebook
  content inset (shifted 10 px inward for the mobile crop) and the YouTube band padding (rebalanced after
  the first render showed content nearly touching the 423 px strip edges).

## Remaining concerns / deviations

- The positioning line (four-item service portfolio) appears only on `x-header`; it is deliberately
  dropped on `linkedin-company`, `facebook-cover` and `youtube-channel` for the reasons above — this
  follows the brief's "compress or drop" allowance, but the Lead should confirm the set-wide copy policy.
- The Facebook cover bleeds its leaf from the top-right like the rest of the set, but the leaf is smaller
  than on the wide formats so the small canvas stays quiet; the bottom ~60 px of the desktop 820×360 is
  intentionally empty (mobile crop and avatar area), which may read as generous space rather than a void.
- No pricing, clients, certifications, guarantees or new claims were introduced; nothing outside
  `banners/jfc/` was modified; no git commands run.
