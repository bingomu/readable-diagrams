# Changelog

## 1.1.0 — 2026-11-02

- **Hover interaction layer** (pure CSS, no script): node hover dims the rest and
  lights connected edges; edge hover thickens the edge; reading steps
  cross-highlight their node; staggered entrance animation; reduced-motion and
  print fall back to the static frame.
- `render.py`: spec validation with readable errors, `--theme` / `--size`
  overrides, `--list-types`, `--version`.
- Repo packaging for three distribution channels: DSH plugin
  (`dsh.bundle` + `cordis.patch.yml` + `lib/index.js`), Claude Code plugin
  (`.claude-plugin/`), Codex plugin (`.codex-plugin/`), plus the generic
  `skills/readable-diagrams/` layout.
- `scripts/check.py` gate suite; GitHub Actions CI on Python 3.9 and 3.12.
- English + Chinese README, CONTRIBUTING, SECURITY, AGENTS.md.

## 1.0.0 — 2026-11-01

- First fused release: JSON-spec renderer for nine structural types, editorial
  design system (light/dark, CJK-aware), `self_check.py` (MIT, from
  diagram-design), `comprehension_check.py` (original), Mermaid / draw.io /
  Excalidraw extractors, SVG / PNG export, eight example pages passing both
  gates.
