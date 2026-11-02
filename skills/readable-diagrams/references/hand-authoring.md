# Hand-authoring an SVG page

Use this path only for the `✍️` rows in [`type-router.md`](type-router.md). The
spec engine covers the nine structural types; everything else is drawn by hand —
but the page furniture and the two gates are identical.

```bash
cp assets/template.html my-figure.html
# edit the placeholders and the SVG body
python3 scripts/self_check.py my-figure.html
python3 scripts/comprehension_check.py my-figure.html
```

`comprehension_check.py` reads `data-role` / `data-rd-*` attributes, so a
hand-authored page must carry them or it will fail on structure it cannot see.

---

## 1. Page furniture (required)

```html
<main class="rd-doc" data-rd-doc="1">
  <div class="rd-eyebrow">CHART · 对比</div>
  <h1 class="rd-title">结论式标题，≤60 字</h1>
  <p class="rd-takeaway">一句话结论。</p>
  <figure class="rd-figure">
    <div class="rd-canvas"><svg …>…</svg></div>
    <figcaption class="rd-caption">怎么读：方向、编码、口径。</figcaption>
  </figure>
  <ol class="rd-steps" data-rd-steps="3">…</ol>
  <ul class="rd-legend" data-rd-legend="1">…</ul>
  <footer class="rd-footer">…</footer>
</main>
```

The gate looks for: `.rd-doc`, `.rd-title`, `.rd-takeaway`, `.rd-caption`,
`.rd-canvas`, `.rd-steps` (structural types), `.rd-legend` (when colour encodes
a distinction), and the `<svg>` contract below.

---

## 2. The accessible SVG contract

1. `<svg role="img" aria-labelledby="<slug>-title <slug>-desc">`.
2. `<title>` is the **first child** of `<svg>`, before `<defs>`.
3. IDs are prefixed per file/variant: `<slug>-title`, `<slug>-desc` — never bare
   `title` / `desc` (two figures on one page would collide).
4. `<title>` = the subject's short name, ≤60 chars.
5. `<desc>` = one sentence about the content, not the geometry.
6. Decorative-only SVG uses `aria-hidden="true"` and is not a figure.

---

## 3. Required data attributes

| Attribute | Placed on | Meaning |
| --- | --- | --- |
| `data-rd-type="line"` | `<svg>` | the visual type (for the node budget) |
| `data-rd-node="1"` | each node `<g>` | counts toward the node budget |
| `data-rd-kind="focal"` | focal node `<g>` | counts toward the accent budget (≤2) |
| `data-rd-edge="1"` | each connector `<path>`/`<line>` | counts connectors |
| `data-role="name"` | node-name `<text>` | 12px floor (11 with CJK allowed) |
| `data-role="sublabel"` | sublabel `<text>` | 9px floor |
| `data-role="arrow"` | edge-label `<text>` | 8px floor; also counts labelled edges |
| `data-role="eyebrow"` | axis/zone `<text>` | 7px floor |

---

## 4. Tokens

Resolve roles to values once (see [`design-system.md`](design-system.md)), then
use the values consistently. Never invent a hex mid-figure.

| Role | Light | Dark |
| --- | --- | --- |
| paper | `#f5f5f5` | `#2d3142` |
| ink | `#2d3142` | `#f5f5f5` |
| muted | `#4f5d75` | `#bfc0c0` |
| soft | `#5a6580` | `#949eb2` |
| accent | `#bf4520` | `#f08a59` |
| accent-tint | `rgba(191,69,32,.08)` | `rgba(240,138,89,.10)` |
| link | `#2e5aa8` | `#739fdf` |
| white fill | `#ffffff` | `rgba(245,245,245,.10)` |

Fonts: title `Instrument Serif`; names `Geist` 600; technical sublabels /
labels / eyebrows `Geist Mono`. CJK labels append `'PingFang SC', 'Noto Sans SC'`
and keep a 12px floor.

---

## 5. Primitives

### Background and markers — always define all three

```svg
<defs>
  <marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" fill="#4f5d75"/></marker>
  <marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" fill="#bf4520"/></marker>
  <marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" fill="#2e5aa8"/></marker>
</defs>
<rect width="100%" height="100%" fill="#f5f5f5"/>
```

### Node box

```svg
<!-- 1. opaque paper mask so arrows never bleed through -->
<rect x="X" y="Y" width="W" height="H" rx="6" fill="#f5f5f5"/>
<rect x="X" y="Y" width="W" height="H" rx="6" fill="#ffffff"
      stroke="#2d3142" stroke-width="1"/>
<text x="CX" y="CY" fill="#2d3142" font-size="12" font-weight="600"
      font-family="'Geist','PingFang SC',sans-serif" text-anchor="middle"
      data-role="name">Node name</text>
<text x="CX" y="CY+16" fill="#4f5d75" font-size="9"
      font-family="'Geist Mono',monospace" text-anchor="middle"
      data-role="sublabel">:443</text>
```

Minimum box: 112×48, padding ≥20px, origins on the 4px grid.

### Edge label (mask + gap)

```svg
<rect x="MX-20" y="AY-21" width="40" height="14" rx="2" fill="#f5f5f5"/>
<text x="MX" y="AY-9" fill="#5a6580" font-size="8"
      font-family="'Geist Mono',monospace" text-anchor="middle"
      data-role="arrow">WRITE</text>
```

The mask must be `paper`, and the visible gap to the stroke must be 6–10px.
Vertical runs get the label to the side, never `writing-mode`.

### Legend (strip below the figure, in HTML)

```html
<ul class="rd-legend" data-rd-legend="1">
  <li><span class="rd-swatch" style="background:#2d3142"></span>服务</li>
  <li><span class="rd-swatch" style="background:#bf4520"></span>主路径</li>
</ul>
```

Never place the legend inside the plot area.

---

## 6. Connector rules (non-negotiable)

1. **Orthogonal only.** Right-angle elbows (`r=8`, minimum `r=6`); a straight
   line only when both ends share an x or y. Diagonals fail the gate.
2. **Label gap.** Every edge label sits on a `paper` mask with a 6–10px gap from
   the stroke; the connector stays visible.
3. **No overlaps.** Offset parallel routes ≥12px; hop the less important line at
   a crossing (`a 8,8 0 0 1 16,0`).
4. **Fan attach points.** N connectors on one edge attach at `L·k/(N+1)`, ≥12px
   apart, each traceable end to end.
5. **No transit behind a non-endpoint box** — reroute; if geometrically
   unavoidable, dash the stroke and label it at the visible end, with no marker
   on the intervening box.
6. **Mask before node.** A label mask must never overlap a node painted after it
   (z-order is background → zones → connectors → labels → nodes).

Draw connectors before boxes so lines sit behind nodes.

---

## 7. Geometry defaults

- 4px grid for origins, sizes, gaps, padding.
- 40px SVG outer margin; content never touches the viewBox edge.
- Column gap ≥104px when edges carry labels; row gap 32px (40 presentation).
- `viewBox="0 0 W H"` with W/H divisible by 4; `min-width` in CSS equals W.
- Wrap the SVG in `.rd-canvas` (`overflow-x:auto`) so phones scroll instead of
  shrinking the type ramp.

---

## 8. Self-review before delivery

- [ ] Title states a conclusion; takeaway is one sentence; caption teaches.
- [ ] 2–5 numbered steps; the badges on the figure match the list.
- [ ] ≤2 accent elements; everything else ink/muted/soft.
- [ ] Every connector orthogonal; every label masked with a visible gap.
- [ ] Legend covers exactly the kinds that appear.
- [ ] `<title>` first child, `<desc>` says what (not where boxes are).
- [ ] Both gates pass (`self_check.py`, `comprehension_check.py`).
- [ ] I looked at the rendered page once — not just the gate output.
