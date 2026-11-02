# readable-diagrams — detail

## What it changes about making a diagram

Most diagram skills stop at "the shape is correct". readable-diagrams adds the
step that decides whether the figure is worth looking at: the page must answer
the reader's question before it is allowed to ship.

Every generated page carries:

1. **A conclusion-shaped title** (≤60 chars) — the claim, not the category.
2. **A one-line takeaway** — what the reader leaves with.
3. **A numbered reading path** (2–5 stops) — where the eyes start and go.
4. **A caption** — direction, units, provenance, what was omitted.
5. **A legend** — only when colour or line style encodes a distinction.
6. **Accessible SVG** — role/aria, `<title>` first, a `<desc>` about content.

`comprehension_check.py` fails the page when one of those is missing or when a
budget is broken (≤2 focal accents, node ceilings, type floors, 4.5:1 contrast,
orthogonal connectors). `self_check.py` covers structure and single-file safety.
Neither gate replaces reading the page once — it narrows the failure surface.

## Engine types

| Type | Use |
| --- | --- |
| `architecture` | components, zones, trust boundaries |
| `flow` | steps, branches, decisions (hexagons) |
| `state` | lifecycle and transitions |
| `sequence` | messages over time |
| `timeline` | events on a proportional clock |
| `tree` | containment / decomposition |
| `layers` | abstraction bands |
| `bar` | magnitude comparison |
| `quadrant` | two-axis positioning |

Chart families (line, scatter, sankey, radar, heatmap, Gantt, Venn, funnel,
journey, …) are hand-authored against the same furniture and the same gates.

## Motion

A no-JavaScript layer: nodes rise in with a 55 ms stagger; hovering a node dims
the rest and lights its connected edges; hovering a reading step lights the node
it points at; `prefers-reduced-motion` and print force the static frame.

## Install anywhere

| Host | How |
| --- | --- |
| DeepSeek Harness | install this repo as a plugin (`dsh plugin add` / Plugins page) |
| Claude Code | plugin marketplace `.claude-plugin/`, or copy `skills/readable-diagrams` to `~/.claude/skills/` |
| Codex | `.codex-plugin/` manifest, or copy the skill folder to `~/.codex/skills/` |
| Any agent reading SKILL.md | copy `skills/readable-diagrams` wherever that agent looks for skills |
