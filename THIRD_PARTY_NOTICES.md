# Third-party notices

This project is MIT-licensed (see `LICENSE`). It vendors the files below and
builds on two upstream skills.

## Vendored code — MIT

Source: https://github.com/cathrynlavery/diagram-design (MIT)
Copyright (c) Cathryn Lavery and contributors.

| File | Origin | Changes |
| --- | --- | --- |
| `scripts/self_check.py` | `scripts/self_check.py` | unchanged |
| `scripts/mermaid_extract.py` | `scripts/mermaid_extract.py` | unchanged |
| `scripts/drawio_extract.py` | `scripts/drawio_extract.py` | unchanged |
| `scripts/excalidraw_extract.py` | `scripts/excalidraw_extract.py` | unchanged |

The design tokens, type ramp, node treatments and connector rules in
`references/design-system.md` and `references/hand-authoring.md` are adapted from
the same project's `references/style-guide.md`, `references/primitives-core.md`
and `references/output-spec.md` (MIT, with attribution).

## Referenced work — Apache-2.0, no code copied

Source: https://github.com/tt-a1i/archify (Apache-2.0)

The JSON-intermediate pipeline, the "validate → render → finalize" delivery
discipline, the conclusion-first explainer narrative and the output contract in
this skill are inspired by Archify. No Archify source file is copied; the
renderer here is an independent implementation in Python.

## Our own code

`scripts/render.py`, `scripts/comprehension_check.py`, `scripts/export.py`,
`assets/template.html`, `SKILL.md`, `README.md` and `references/*` are original
to this project (MIT).
