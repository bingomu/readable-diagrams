# Design system

Editorial skin shared by every rendered page. The values live in
`scripts/render.py` (`THEMES`, `RAMP`, `PRESETS`, `FONT_*`, `CSS`); this file is
the contract those constants implement. Change the constants, not individual
pages.

---

## 1. Tokens

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| `paper` | `#f5f5f5` | `#2d3142` | page + SVG background |
| `paper-2` | `#ececec` | `#393e53` | zones, containers |
| `ink` | `#2d3142` | `#f5f5f5` | primary text and stroke |
| `muted` | `#4f5d75` | `#bfc0c0` | secondary text, default arrows |
| `soft` | `#5a6580` | `#949eb2` | sublabels, legend, eyebrow, boundary labels |
| `rule` | `rgba(45,49,66,.12)` | `rgba(245,245,245,.12)` | hairlines |
| `accent` | `#bf4520` | `#f08a59` | focal node / primary path — **max 2** |
| `accent-tint` | `rgba(191,69,32,.08)` | `rgba(240,138,89,.10)` | focal node fill |
| `link` | `#2e5aa8` | `#739fdf` | external / HTTP calls |
| white | `#ffffff` | `rgba(245,245,245,.10)`-ish | service node fill |

Derived washes are built with `rgba(ink, α)` so the two skins invert without
per-page edits:

| Treatment | Fill | Stroke |
| --- | --- | --- |
| `focal` | accent-tint | accent |
| `backend` (service) | white / ink@.10 | ink |
| `store` | ink@.05 | muted |
| `external` | ink@.03 | ink@.30 |
| `input` (actor/entry) | muted@.10 | soft |
| `optional` (async) | ink@.02 | ink@.20, dashed `4,3` |
| `security` (boundary) | accent@.05 | accent@.50, dashed `4,4` |
| `decision` | white / ink@.12 | ink, hexagon |

### Contrast contract

| Use | Minimum | Checked by |
| --- | --- | --- |
| Any text token on its actual background | 4.5:1 | `comprehension_check.py` (`contrast`) |
| Essential non-text marks (arrows, borders, data points) | 3:1 | author |

Light `accent` is deliberately darker than the brand tangerine so it clears
4.5:1 as text. In dark mode the accent brightens. Do not “fix” either value to
match a brand swatch without re-checking contrast.

---

## 2. Typography

| Role | Family | Standard | Presentation | Print |
| --- | --- | --- | --- | --- |
| `title` (HTML H1, not SVG) | Instrument Serif / Noto Serif SC | 28–42 responsive | — | — |
| `name` (node name) | Geist 600 / PingFang SC | 12 | 16 | 12 |
| `sublabel` | Geist Mono / mono CJK fallback | 9 | 12 | 9 |
| `arrow` (edge label) | Geist Mono | 8 (CJK → 11 sans) | 12 | 8 |
| `eyebrow` (zone/axis) | Geist Mono, tracked | 8 | 8 | 8 |

Font link (one request, Google Fonts only):

```
Instrument+Serif:ital@0;1 · Geist:wght@400;500;600 · Geist+Mono:wght@400;500
Noto+Serif+SC:wght@400 · Noto+Sans+SC:wght@400;500;600
```

Only `fonts.googleapis.com` is permitted by `self_check.py`. For offline pages,
strip the `<link>`: every stack already ends in a generic family.

### Non-Latin labels

Geist carries no CJK. The renderer handles this automatically:

- Node names switch to the sans stack and keep a **12px floor** — never shrink a
  Chinese name below 12; cut the name instead.
- Edge labels, eyebrows and legend items switch from 8px mono uppercase to
  **11–12px sans, no tracking, no uppercase** when the string contains CJK.
- Sublabels stay Latin (ports, types, versions); a prose sublabel is not a
  sublabel — move it into the caption.
- Width budget is per character: wide/full-width char = 1em, Latin = 0.60em sans
  / 0.62em mono. Punctuation `（），。：` counts as full width.

Japanese/Korean pages: keep the same rules, add the platform CJK face
(`Hiragino Sans`, `Noto Sans JP` / `Noto Sans KR`, `Apple SD Gothic Neo`) after
Geist in `FONT_SANS` in `render.py`.

---

## 3. Geometry

| Token | Value |
| --- | --- |
| grid | 4px — origins, widths, heights, gaps are multiples of 4 |
| stroke | 0.8 hairline · 1 default · 1.4 accent path |
| radius | 2 tag · 6 node · 8 zone |
| inner padding | ≥20px inside a node |
| node gap | 32px standard / 40px presentation (vertical), 132px column gap with labels |
| page margin | 40px (presets) / 64px (social-og) |
| SVG outer margin | 32–40px, content never touches the viewBox edge |

Connector grammar (also enforced in hand-authored pages):

1. Orthogonal only — right-angle elbows at `r=8`; straight lines only when both
   ends share an x or y.
2. Every edge label sits on an opaque `paper` mask with a 6–10px gap from its
   stroke.
3. No overlapping or stacked strokes; offset parallel routes ≥12px.
4. Fan attach points on a shared edge: `L·k/(N+1)`, ≥12px apart.
5. A connector never transits behind a non-endpoint node.
6. A label mask never overlaps a node painted after it.

Arrows: `muted` default · `accent` primary path · `link` external/HTTP ·
dashed `5,4` for async/return/optional. Draw paths before nodes.

---

## 4. Page furniture (what makes it readable)

```
eyebrow      TYPE · 类型        small, tracked, muted
H1           the conclusion      serif, clamp(26–42px), ≤60 chars
takeaway     one sentence       16–17px, muted, ≤100 chars
figure       .rd-canvas          overflow-x:auto + svg{min-width:viewBox width}
caption      how to read it     13px, soft, direction/units/omission
steps        numbered path      2–5 items, accent badge + title + detail
legend       decode strip       hairline separated, only when needed
footer       type · size · audience · source
```

Responsive behaviour is built in: the SVG keeps its `min-width` so phones scroll
the figure rather than shrinking 12px type into 8px; `@media print` releases the
scroll and `min-width` so paper scales the figure to fit.

---

## 5. Dark theme

Set `meta.theme: "dark"`. Tokens invert; opacities stay the same. Rules:

- Never hand-invert a hex in a page — regenerate from the spec.
- Check contrast in both themes when you customize tokens.
- Export/print from the light theme unless the destination is dark.

---

## 6. Customising the skin

1. Edit `THEMES` in `scripts/render.py` (both light and dark columns).
2. Keep the contrast contract: re-run `comprehension_check.py` on one example;
   it fails if a text token drops below 4.5:1.
3. Keep one accent hue. If a brand ships eight colours, pick paper, ink and one
   accent; the rest become `muted`/washes.
4. Keep three families (serif title, sans names, mono technical). The serif/sans
   contrast is load-bearing, not taste.
