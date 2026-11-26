# DESIGN BRIEF · JFC / CSCV social banner templates

Internal brief for the two banner designers. Read the whole file before you write any layout.

Ticket: `social-banner-templates-272491b334d6` — “设计 JFC 公司品牌与 CSCV 视觉品牌的官方图版模板，用作领英和其他主流社交平台的背景横幅图”.
Lead owns the shared kit, the guide, previews, QA and delivery. You own one brand’s banner set.

---

## 1. What we deliver

A reusable **social banner template kit** for two brands:

| Brand | Visual system | Formats |
|---|---|---|
| **JFC company brand** | **INSTITUTIONAL BLUE** — official logo, navy `#0A295B`, ice `#E7F0FD`, logo blue `#2C63E0`, green signal `#2E9D74`; Avenir Next + PingFang SC | 5 |
| **CSCV visual brand** | **FIELD DOSSIER** — warm paper `#F1EDE3`, ink `#0A0D10`, signal orange `#FF4D00`, verify green / acid, registration marks, stamps, Archivo / Inter / JetBrains Mono + PingFang SC | 5 |

Formats (exact export sizes; the PNG size is the upload size):

| slug | format | canvas px | safe area (x,y,w,h) | blocked by platform UI (x,y,w,h) |
|---|---|---|---|---|
| `linkedin-personal` | 领英 · 个人主页背景 / LinkedIn personal profile background | **1584×396** | 24, 24, 1536, 348 | 40, 324, 152, 72 (avatar) |
| `linkedin-company` | 领英 · 公司主页封面 / LinkedIn company page cover | **1512×256** | 24, 24, 1464, 208 | 30, 206, 120, 50 (page logo) |
| `x-header` | X（Twitter）· 页头横幅 / X header | **1500×500** | 24, 40, 1452, 420 | 0, 360, 220, 140 (avatar) |
| `facebook-cover` | Facebook · 主页封面 / Facebook page cover | **820×360** | 90, 24, 640, 312 | 0, 270, 100, 90 (avatar) |
| `youtube-channel` | YouTube · 频道封面 / YouTube channel art | **2560×1440** | 507, 508, 1546, 423 | — |

`safe area` = the region that must stay visible on every device / crop. `blocked` = covered by platform UI.
**All text and the logo must sit inside the safe area and outside the blocked rects.** Decorative marks
(grid, registration crosshairs, oversized watermark lettering, barcode) may bleed outside the safe area,
but nothing that carries meaning may.

Both brands are also used for the *other* brand’s formats? No. Keep each brand’s five formats as one family.

Reference flagship already built by the Lead (copy it, keep the system, adapt the layout):
- `banners/jfc/src/linkedin-personal.html` → `banners/jfc/png/linkedin-personal.png`
- `banners/cscv/src/linkedin-personal.html` → `banners/cscv/png/linkedin-personal.png`

Read those two HTML files first. They show the exact CSS classes, the safe margins and the tone.

---

## 2. Brand rules (hard)

### JFC — INSTITUTIONAL BLUE
- Ground: `linear-gradient(104deg, #061A3B 0%, #0A295B 58%, #0B2C61 100%)`. No photos, no orange, no rounded corners, no shadows.
- Type: Avenir Next for latin, PingFang SC for Chinese. Chinese headline is semibold.
- Accents: one thin green rule or bar (`#2E9D74`), the official logo blue only inside the logo, an ice hairline inset frame, a faint construction grid fading to the right, the white leaf silhouette at 8–12 % opacity bled from a corner.
- Official logo: **white lockup** (`banners/kit/assets/logo-white.png`) on navy. Never recolour, never distort, never put it on a busy area.
- Copy: from `banners/kit/copydeck.py` → `JFC_COPY`. Do not invent slogans.
- Hierarchy: logo → kicker (uppercase, letterspaced, ice-muted) → Chinese headline (largest) → English headline (paired below) → positioning / service line → meta (mono, muted).
- Keep it quiet and institutional; generous negative space is correct.

### CSCV — FIELD DOSSIER
- Ground: warm paper `#F1EDE3` (light format) or ink `#0A0D10` (dark variant, only if you keep the whole
  layout consistent with the rest of the set — the default set is paper). No pure white, no blue, no soft shadows.
- Type: Archivo 800/900 for English display, Inter for English body, JetBrains Mono for labels/meta/uppercase,
  PingFang SC for Chinese. Chinese and English always paired, Chinese first.
- Components (all defined in `banners/kit/css/cscv.css`): registration crosshairs at the corners
  (`.cscv-reg`), faint construction grid, orange kicker, tick rule (`.cscv-ticks`), rotated evidence stamp
  (`.cscv-stamp`), barcode (`.cscv-barcode`), mono meta, hairline rules.
- Official logo: **colour lockup** (`banners/kit/assets/logo-color.png`) on paper; white lockup on ink.
- Copy: from `banners/kit/copydeck.py` → `CSCV_COPY`. No prices, no client names, no certifications,
  no guarantees, no “leading/best”. The 73 % figure never appears on a banner.
- Signal discipline: orange is a signal kept under 15 % (kicker / stamp / one emphasis); paper covers stay restrained. At most one
  acid or verify accent. Text on orange is ink only.
- The system is evidence-led: the banner looks like the cover of an on-site dossier, not an ad.

### Both
- Bilingual: every banner carries both Chinese and English, paired; never set a Chinese and English
  fragment inside the same line. English uses American spelling.
- No prices, no invented facts, no clients, no cases, no “100 %”, no emoji.
- Minimum type size: **11 px** at 1× (mono labels may be 10.5 px only in the meta line; nothing smaller).
- All text elements that must be legible get `data-critical`, and `data-lang="zh"` / `data-lang="en"` on the
  bilingual pairs so the QA probe can check them.
- Do not touch: `banners/kit/**` (except reading), the other brand’s folder, `guide/`, `preview/`, `qa/`,
  `README.md`, `DELIVERY.md`, `DESIGN-BRIEF.md`. Do not run git. Do not send Feishu messages.

---

## 3. Layout guidance per format

Adapt the flagship; do not paste a 1584×396 layout into another aspect ratio. These are starting points.

- **linkedin-company 1512×256** — a horizontal ribbon. Logo top-left, one-line Chinese headline, English
  headline below (or to the right), meta/stamp on the right. Keep left content above y = 206 (page logo
  overlap). Compress the positioning line to one short line or drop it; keep the service line.
- **x-header 1500×500** — the most spacious. Consider a two-part composition: left = logo + kicker +
  headline + English + one proof line; right = a dossier/evidence block (stamp, serial, barcode, tick rule)
  or the JFC leaf/inset frame. Bottom-left 220×140 must stay empty (avatar).
- **facebook-cover 820×360** — the hardest crop (mobile shows the middle 640×312). Build the design inside
  x 90–730 / y 24–336; the outer 90 px on each side is decoration only. Fewer elements, bigger type.
- **youtube-channel 2560×1440** — the canvas is huge but only the centre 1546×423 is guaranteed. Compose a
  “safe band” inside it (roughly y 508–931) and use the TV-only top/bottom for quiet decoration: oversized
  grid, registration marks, a giant ghost wordmark, the leaf motif. Type here is 2–3× the LinkedIn size.
  Do not put essential content outside the safe band.

Sizes are relative: choose type sizes that read at the platform’s on-screen size (a 1584 px-wide banner is
displayed at ~800–1100 CSS px on a laptop; a 2560 px channel art is displayed small). Keep one clear
focal point per banner.

---

## 4. File conventions

For each brand, create the four missing format files:

```
banners/<brand>/src/<format>.html      # the layout: standalone HTML, exact artboard size
banners/<brand>/png/<format>.png       # 1x export (exact canvas size)
banners/<brand>/png/<format>@2x.png    # retina export (written automatically)
banners/<brand>/NOTES.md               # design decisions, copy used, checks (append)
```

The existing `linkedin-personal` flagship counts as one of the five; do not rebuild it.

HTML skeleton:

```html
<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>JFC · X header · 1500×500</title>
<link rel="stylesheet" href="../../kit/css/base.css">
<link rel="stylesheet" href="../../kit/css/jfc.css">   <!-- or cscv.css -->
<style>
  .art { width: 1500px; height: 500px; }
  /* absolute positions in px for this format */
</style></head>
<body><div class="art jfc"> ... </div></body></html>
```

Render + self-review (run from the ticket root):

```bash
PY=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
$PY banners/kit/tools/render.py banners/jfc/src/x-header.html --format x-header --out banners/jfc/png/x-header.png
# safe-zone proof (green = must-keep, red hatch = platform UI):
$PY banners/kit/tools/render.py banners/jfc/src/x-header.html --format x-header --out /tmp/x-safe.png --overlay
```

Inspect the rendered PNG and the overlay with `read_image`. Look for: clipped glyphs, text colliding,
Chinese/English touching, text too small, logo too small or blurred, content inside the red hatch,
empty unbalanced areas, accidental “underline” effects, JPEG-ish banding (PNG only).

---

## 5. Acceptance criteria

1. PNG dimensions exactly match the canvas; no extra margin.
2. All `data-critical` elements inside the safe area and outside the blocked rects (the QA probe checks this;
   run it if you can — Lead runs it for the final set).
3. Both languages present on every banner, paired; American English.
4. Brand system unmistakable: JFC = navy/ice/official logo; CSCV = paper/ink/orange/dossier marks.
5. Readable at display size; one focal point; balanced negative space; no clipping.
6. Copy only from `copydeck.py`; no new facts, prices, clients, guarantees.
7. `NOTES.md` records: what you built, which copy lines you used/dropped, what you checked.
8. No edited files outside `banners/<your brand>/`.

When the four banners are rendered and self-reviewed, message the Lead (`send_message`, target `lead`) with:
status, file list, anything you deliberately dropped, and any remaining concern. Do not commit or push.

---

## 6. Useful paths

- Kit tokens: `banners/kit/tokens.py`
- Copy deck: `banners/kit/copydeck.py`
- Platform specs / safe areas: `banners/kit/platform_specs.py`
- Shared CSS: `banners/kit/css/base.css`, `banners/jfc` styles in `banners/kit/css/jfc.css`, `banners/kit/css/cscv.css`
- Assets: `banners/kit/assets/` (official logo colour/white, leaf silhouettes, OFL fonts)
- Renderer: `banners/kit/tools/render.py`
- Brand references: `banners/jfc/src/linkedin-personal.html`, `banners/cscv/src/linkedin-personal.html`
- Official JFC brand source (read-only): `~/Desktop/待办事件/JFC_公司简介_重建/`, `~/Desktop/待办事件/JFC 服务组合_重建版.pdf`
- CSCV field-dossier system (read-only): `/Users/a1-6/src/spag/bizmodel-redesign-8d2bab8a14d8/design/README.md`
