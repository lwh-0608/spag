# CSCV — social banner set · design notes

Brand system: **CSCV “FIELD DOSSIER”** (Nov 2026). Warm paper `#F1EDE3`, ink `#0A0D10`,
signal orange `#FF4D00`, registration crosshairs, faint construction grid, tick rules,
rotated evidence stamp, barcode, mono metadata; Archivo 800/900 display + Inter text +
JetBrains Mono labels + PingFang SC; Chinese first, English paired below/beside.
Copy only from `banners/kit/copydeck.py` → `CSCV_COPY` (no prices, clients, cases,
certifications, guarantees, “leading/best”, no 73 % figure, no emoji).

Reference flagship: `linkedin-personal` (1584×396) was built by the Lead and is **not
modified** here. This file records the four additional formats built by the CSCV designer.

Render command (from the ticket root, for every format):

```bash
PY=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
$PY banners/kit/tools/render.py banners/cscv/src/<format>.html \
    --format <format> --out banners/cscv/png/<format>.png
$PY banners/kit/tools/render.py banners/cscv/src/<format>.html \
    --format <format> --out /tmp/<format>-safe.png --overlay   # safe-zone proof
```

The renderer writes the 1× PNG at the exact canvas size and the `@2x` retina file next to it.

---

## Family decisions (apply to all four)

- **One dossier cover, five crops.** Every banner is a cover sheet: official colour logo
  top-left on paper, orange mono kicker, the official headline pair as the single focal
  point, a measurement/tick rule, and an evidence cluster on the right (rotated
  `ON-SITE VERIFIED · 现场核验` stamp, `CSCV / FIELD DOSSIER · NOV 2026` serial, barcode,
  `只向买方收费 · PAID ONLY BY THE BUYER`, contact meta). No new copy was written.
- **Alignment logic borrowed from the flagship**: logo and headline share an optical left
  edge (headline set 2 px left of the logo to compensate for the CJK left bearing);
  evidence items right-align to one column; mono labels stay 10.5 px only in the meta line.
- **Layout is re-composed per aspect ratio**, not pasted. Trust elements are consistent,
  proportions are not.
- **Blocked UI zones**: the profile-photo rect of each platform is left free of all text
  (not only `data-critical`); only registration marks / rules may fall under it.
- **Orange discipline**: kicker + stamp + `<b>` in the proof line + four registration
  crosshairs, i.e. the flagship’s accent set. On the paper-light formats this stays a
  quiet 1–2 % signal; deliberately not pushed to the nominal 5–15 % band, which would
  break the “dossier, not advertisement” read (see *Possible deviations*).
- **Type sizes** are chosen for the platform display size, not for the export: LinkedIn
  ribbon 37/22 px, X 50/30 px, Facebook 38/22 px, YouTube 80/40 px in the guaranteed band.

---

## linkedin-company · 1512×256

Files: `banners/cscv/src/linkedin-company.html` →
`banners/cscv/png/linkedin-company.png` / `linkedin-company@2x.png`.

**Copy used** — `kicker_cn`+`kicker_en` (set as the flagship’s single mono label
“CSCV · 中国供应链核验 · CHINA SUPPLY CHAIN VERIFICATION”), `headline_cn`,
`headline_en`, `stamp`, `serial`, `proof_cn`+`proof_en`, `meta` (full CSCV_COPY variant).
**Copy dropped** — `three_cn`/`three_en` (the brief explicitly allows compressing or
dropping the positioning line in a 256 px ribbon; the service line is kept) and
`scope_cn`/`scope_en`.

**Layout** — a horizontal ribbon: logo (44 px) → measurement tick rule closing the logo
row → kicker → one-line 37 px Chinese headline → 22 px English headline on the left;
evidence column right-aligned to x 1456 (stamp, serial, barcode, proof, meta). Nothing on
the left sits below y 206 because the page logo covers x 30–150 / y 206–256. The proof
line and the English headline share a baseline (y 190) so the two halves tie together.

**Checks** — 1× = 1512×256, @2x = 3024×512; overlay proof: all `data-critical` inside
safe (24,24,1464,208) and outside the blocked rect; probe: 1 artboard, scroll =
1512×256, no text collisions, fonts loaded, `data-lang` zh+en present, min font 10.5 px
(meta only), logo sharp (rendered from the 1460 px colour lockup at 2×).

## x-header · 1500×500

Files: `banners/cscv/src/x-header.html` → `banners/cscv/png/x-header.png` /
`x-header@2x.png`.

**Copy used** — kicker (single mono label, as flagship), `headline_cn`, `headline_en`,
`three_cn`/`three_en`, `scope_cn`/`scope_en` (“每份报告逐条列出未核验项 /
EVERY REPORT LISTS WHAT COULD NOT BE VERIFIED”), `stamp`, `serial`, `proof_cn`+`proof_en`,
`meta` (short flagship variant `JAZZFRONT Consulting™ · JFC.Consulting@outlook.com` —
the full “· CSCV ·” line does not fit the right-aligned column width).
**Copy dropped** — nothing else.

**Layout** — the most spacious format, two parts. Left: logo (52 px), kicker, 50 px
Chinese headline, 30 px English headline, a 924 px tick rule and the three-question
line. Right: a pasted **evidence label** — a 396×350 plate in `paper_2` `#E7E1D3` with a
2 px signal-orange top rule — containing the rotated stamp, serial, barcode, a hairline,
the scope statement, a second hairline and the paid-only-by-buyer line; the contact meta
sits as a caption under the plate. The plate gives the right side the mass the headline
has on the left and keeps the dossier “label pasted on the file” metaphor. Everything on
the left stays above y 360 so the profile photo (x 0–220 / y 360–500) covers only paper.

**Checks** — 1× = 1500×500, @2x = 3000×1000; overlay proof: all critical inside safe
(24,40,1452,420), outside the avatar rect; no collisions; plate border, stamp and rules
all clear of the plate edges; fonts loaded; min font 10.5 px.

## facebook-cover · 820×360

Files: `banners/cscv/src/facebook-cover.html` → `banners/cscv/png/facebook-cover.png` /
`facebook-cover@2x.png`.

**Copy used** — kicker (single mono label), `headline_cn` (two lines),
`headline_en` (two lines), `three_cn`/`three_en`, `stamp`, `serial`, `proof_cn`+`proof_en`.
**Copy dropped** — `meta` and `scope_cn`/`scope_en`: this is the smallest canvas and the
brief asks for fewer elements; two footer rows already carry the evidence.

**Layout** — the hardest crop. All meaning sits in x 120–700 / y 30–330 inside the
640×312 safe area; the outer 90 px each side is grid/registration decoration only.
Logo 38 px top-left with the stamp (11 px, reduced for the small canvas) and barcode at
top-right; the 38 px headline is set on two lines so both languages stay large; a
580 px tick rule then a two-row document footer: `主体 · 产能 · 风险` + paid-only line on
row one, `ENTITY · CAPACITY · RISK` + serial on row two. Nothing enters the avatar
rect (x 0–100 / y 270–360).

**Checks** — 1× = 820×360, @2x = 1640×720; overlay proof: critical content inside safe
(90,24,640,312), outside the avatar rect; simulated the mobile crop (x 90–730) and the
desktop crop (y 24–336) from the PNG and both read as complete covers; no collisions;
fonts loaded; min font 10.5 px.

## youtube-channel · 2560×1440

Files: `banners/cscv/src/youtube-channel.html` → `banners/cscv/png/youtube-channel.png` /
`youtube-channel@2x.png`.

**Copy used** — kicker (single mono label, 16 px), `headline_cn` (two lines, 80 px),
`headline_en` (40 px, one line), `three_cn`/`three_en` (26/16 px), `stamp` (18 px),
`serial` (16 px), `proof_cn`+`proof_en` (15 px), barcode.
**Copy dropped** — `meta` (the e-mail lives on the channel About section; keeping it would
have forced the band to a fourth mono size and crowded the lower-right evidence column)
and `scope_cn`/`scope_en`.

**Layout** — the guaranteed band (507, 508, 1546, 423) is composed as a **complete
banner**: title block left (logo 62 px, kicker, two-line 80 px Chinese headline, 40 px
English headline) and an evidence column right-aligned to x 2005 (stamp, serial, barcode,
paid-only-by-buyer line, three-question pair). The English headline and
`ENTITY · CAPACITY · RISK` share one baseline (y 876) to lock the band. TV-only
decoration above and below is quiet and non-critical: a giant outlined `CSCV` watermark
(Archivo 900, 560 px, 3 px ink stroke at 11 %), two measurement tick rules that frame the
band (y 474 / y 958), a low-opacity barcode strip and an outlined mono `FIELD DOSSIER`
watermark. All data text stays inside the safe band; the TV-only marks are decorative and
are allowed to sit outside it per the brief.

**Checks** — 1× = 2560×1440, @2x = 5120×2880; overlay proof: all critical inside the
green band; simulated the desktop crop (2560×423, y 508–931) and the mobile crop
(1546×423, x 507–2053) from the rendered PNG — each reads as a complete banner, no
clipping; TV-only watermarks contained inside the canvas; no collisions; fonts loaded;
min font 15 px inside the band.

---

## Possible deviations / open points for the Lead

1. **Orange share.** The set follows the Lead’s `linkedin-personal` flagship (orange as
   kicker + stamp + one orange word + registration marks) rather than the brief’s nominal
   “orange is 5–15 % of the surface”. At 5 % of a 2560×1440 canvas the orange element
   would be a large block and would fight the quiet paper dossier look; flagging in case
   QA prefers a stronger signal on the YouTube TV canvas.
2. **Kicker line.** All formats use the flagship’s single mono label
   “CSCV · 中国供应链核验 · CHINA SUPPLY CHAIN VERIFICATION”. It does contain both
   languages inside one mono label; kept for family consistency with the Lead’s flagship
   (mono metadata labels are treated as labels, not prose).
3. **Meta.** Full `CSCV_COPY["meta"]` in linkedin-company; the short flagship variant in
   x-header (width); omitted in facebook-cover and youtube-channel (documented above).
4. **YouTube watermark text** (`CSCV`, `FIELD DOSSIER`) sits outside the guaranteed safe
   band by design (decorative watermark lettering, allowed to bleed). No data-critical
   content is outside the band.
5. The `linkedin-personal` flagship was not touched; the five exports form one family.
