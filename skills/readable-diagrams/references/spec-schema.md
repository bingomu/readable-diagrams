# Spec schema

`render.py` turns one JSON object into one HTML page. Field names are fixed; omit
optional fields rather than inventing new ones.

```bash
python3 scripts/render.py spec.json -o page.html --json
# → {"viewBox":[964,348],"nodes":6,"edges":5,"labeled_edges":5,"accent":1,
#    "type":"architecture","size":"fit","output":"page.html"}
```

A non-zero exit means the spec is wrong; the message names the field.

---

## 1. Top level

| Key | Required | Meaning |
| --- | --- | --- |
| `type` | ✅ | one of `architecture`, `flow`, `state`, `sequence`, `timeline`, `tree`, `layers`, `bar`, `quadrant` |
| `meta` | ✅ | page furniture + reading contract |
| `zones` / `nodes` / `edges` | per type | graph types |
| `actors` / `messages` | per type | `sequence` |
| `lanes` / `events` | per type | `timeline` |
| `items` | per type | `layers` |
| `data` | per type | `bar` |
| `axes` / `quadrants` / `points` | per type | `quadrant` |

---

## 2. `meta`

| Field | Required | Notes |
| --- | --- | --- |
| `title` | ✅ | the conclusion, ≤60 chars; becomes H1, `<title>`, and page title |
| `eyebrow` | recommended | `TYPE · 中文`, uppercase mono strip above the title |
| `takeaway` | ✅ | one sentence the reader leaves with (also the SVG `<desc>` fallback) |
| `caption` | ✅ | how to read it: direction, encoding, provenance, omission |
| `reading_path` | ✅ for structural types | ordered node ids → numbered badges + step list |
| `steps` | alternative | `[{"title": …, "detail": …}]` when custom wording is needed |
| `legend` | when kinds/variants exist | `[{"label": …, "fill": "#hex or rgba()"}]`; auto-derived if omitted |
| `audience` | optional | `executive` / `mixed` / `engineer` (footer only; wording is yours) |
| `size` | optional | `fit` (default), `doc-inline`, `doc-wide`, `slide-16x9`, `slide-4x3`, `social-og`, `social-square`, `print-a4-landscape`, `print-a3-landscape` |
| `theme` | optional | `light` (default) / `dark` |
| `slug` | optional | id prefix for `<title>` / `<desc>`; default `diagram` |
| `source` | optional | provenance line in the footer |
| `unit` | optional | unit appended to `bar` values |
| `alt` | optional | override the generated `<desc>` |

The checker fails the page if `title`, `takeaway`, `caption`, or (for structural
types) the reading path is missing.

---

## 3. Graph types — `architecture` / `flow` / `state`

A layered left-to-right graph. Layers are inferred from the edges (longest-path),
then ordered by one barycenter pass to cut crossings.

```json
{
  "type": "flow",
  "meta": { "...": "..." },
  "zones": [{"id": "core", "label": "CORE"}],
  "nodes": [
    {"id": "alert", "label": "P99 告警", "kind": "input"},
    {"id": "split", "label": "平均耗时也涨了？", "kind": "decision"},
    {"id": "trace", "label": "抓慢请求 trace", "sublabel": "tail only", "kind": "focal"},
    {"id": "fix", "label": "修复并验证", "kind": "backend"}
  ],
  "edges": [
    {"from": "alert", "to": "split"},
    {"from": "split", "to": "trace", "label": "仅尾部", "variant": "accent"},
    {"from": "trace", "to": "fix", "label": "单跳", "variant": "accent"}
  ]
}
```

### Node fields

| Field | Values | Default |
| --- | --- | --- |
| `id` | unique string | — |
| `label` | short noun/verb phrase | id |
| `sublabel` | technical value only | — |
| `kind` | `backend` `focal` `store` `external` `input` `optional` `security` `decision` | `backend` |
| `zone` | id of an entry in `zones` | — |
| `col` | integer — force the layer | inferred |
| `row` | integer — order within the layer | input order |
| `note` | string — used as step detail if this node is in `reading_path` | — |

### Edge fields

| Field | Values | Default |
| --- | --- | --- |
| `from` / `to` | node ids | — |
| `label` | ≤6 CJK / 3 EN words | — |
| `variant` | `default` `accent` `link` `dashed` `return` | `default` |

### Zones

```json
"zones": [{"id": "edge", "label": "EDGE"}, {"id": "core", "label": "CORE"}]
```

Zones draw a wash rectangle behind their member nodes and an uppercase label at
the top-left. Maximum 3 flat zones; nesting should be a `tree` instead.

**Layout controls**

- `col` pins a node to a column when the inference is wrong; use it instead of
  fighting the layout with duplicate ids.
- `row` orders nodes inside a column (top to bottom).
- `fit` size follows the content; fixed presets centre it in a frame.
- Over ~9 nodes: split into an overview (`zones` as nodes) + one detail per zone.

---

## 4. `sequence`

```json
{
  "type": "sequence",
  "actors": [
    {"id": "browser", "label": "浏览器", "kind": "input"},
    {"id": "api", "label": "订单 API", "kind": "focal"},
    {"id": "db", "label": "订单库", "kind": "store"}
  ],
  "messages": [
    {"from": "browser", "to": "api", "label": "GET /orders/42", "variant": "accent"},
    {"from": "api", "to": "db", "label": "SELECT", "variant": "accent"},
    {"from": "db", "to": "api", "label": "row", "variant": "return"}
  ]
}
```

- Actors render as boxes with lifelines; messages are horizontal arrows in order.
- `variant: "return"` / `"dashed"` dashes the arrow; `accent` highlights the path
  the reader waits on.
- Same-actor messages draw as a small self-loop.
- Budget: ≤7 actors; split long call chains into “happy path” + “failure path”.

---

## 5. `timeline`

```json
{
  "type": "timeline",
  "lanes": [{"id": "ops", "label": "运维"}, {"id": "biz", "label": "业务"}],
  "events": [
    {"id": "alert", "time": "2026-10-01T10:12:00+08:00", "label": "错误率告警",
     "desc": "5xx 升到 4%", "lane": "ops", "kind": "alert"},
    {"id": "recover", "time": "2026-10-01T10:42:00+08:00", "label": "指标恢复",
     "lane": "ops", "kind": "recovery"}
  ]
}
```

- If **every** event carries an ISO-8601 `time`, x is proportional to real time;
  otherwise events are evenly spaced.
- `lanes` stack as rows with their own axis; lane labels sit at the left.
- `kind`: `default` `change` `alert` `action` `recovery` — only `alert` uses the
  accent; `recovery` uses link blue.
- Dates render as `MM-DD HH:MM` under each dot.
- Budget: ≤12 events, ≤3 lanes. A long incident belongs in a table with a
  three-event timeline as the headline.

---

## 6. `tree`

```json
{
  "type": "tree",
  "nodes": [
    {"id": "root", "label": "知识库 MVP", "kind": "focal", "parent": null},
    {"id": "ingest", "label": "导入", "parent": "root"},
    {"id": "md", "label": "Markdown", "parent": "ingest"}
  ]
}
```

- Top-down containment; children spread, parents centre over them.
- `parent: null` = root (multiple roots allowed).
- Use `tree` for single-parent containment only. Cross-links and cycles belong in
  `architecture` / `state`.

---

## 7. `layers`

```json
{
  "type": "layers",
  "items": [
    {"label": "表现层 CSS / 组件", "detail": "改这里：样式、间距、主题变量", "focus": true},
    {"label": "技能层 Skill", "detail": "提示词与流程"},
    {"label": "插件层 Cordis", "detail": "注册工具、钩子与生命周期"},
    {"label": "宿主层 DSH", "detail": "会话、文件系统、模型调用"}
  ]
}
```

Stacked bands, top = highest abstraction. One `focus` band gets the accent.
Budget: ≤6 bands.

---

## 8. `bar`

```json
{
  "type": "bar",
  "meta": {"unit": "ms", "...": "..."},
  "data": [
    {"label": "发布前 P50", "value": 75},
    {"label": "发布后 P99", "value": 600, "focus": true}
  ]
}
```

Horizontal bars, values printed at the end. One `focus` bar gets the accent.
Use for magnitude comparison; use `line` (hand-authored) for trends over time.

---

## 9. `quadrant`

```json
{
  "type": "quadrant",
  "axes": {"x": {"label": "实施成本 →"}, "y": {"label": "用户影响 →"}},
  "quadrants": [
    {"at": "tl", "label": "先做"},
    {"at": "tr", "label": "规划"},
    {"at": "bl", "label": "顺手做"},
    {"at": "br", "label": "先不做"}
  ],
  "points": [
    {"label": "缓存预热", "x": 0.28, "y": 0.78, "focus": true},
    {"label": "重写检索", "x": 0.78, "y": 0.82}
  ]
}
```

- `x`/`y` are 0–1, origin bottom-left; `at` is `tl|tr|bl|br`.
- One `focus` point gets the accent — the recommendation.
- Axis labels are short (“成本 →”, “影响 →”); units belong in the caption.

---

## 10. Colour and kinds outside the tokens

Do not put hex values in specs. `kind` and `variant` map to the design tokens in
`references/design-system.md`. If you need a colour that is not a role, the
figure is probably carrying too many visual languages — split it.

For a custom legend swatch, `fill` accepts any CSS colour; keep it to a token
value copied from the design system so light/dark stay coherent.

---

## 11. Common spec errors

| Message | Cause |
| --- | --- |
| `unknown type 'x'` | not one of the nine engine types — hand-author it instead |
| `KeyError: 'from'` on an edge | typo in `from`/`to`, or an edge points at a missing node id |
| duplicate `id` | two nodes share an id; ids are the reading-path keys |
| empty page | `nodes`/`events`/`items`/`data`/`points` is empty |
| content past the viewBox | fixed preset too small for the content — switch to `fit` or split |

After any render, run both gates; they catch what the renderer cannot.
