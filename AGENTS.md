# Notes for coding agents

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing anything. This file is
the short version of what agents keep getting wrong.

## Where things live

- The skill is `skills/readable-diagrams/` — that folder is the installable unit.
  `SKILL.md`, `references/`, `scripts/`, `assets/` and `examples/` all move
  together; a path in `SKILL.md` is relative to that folder.
- `lib/index.js` only registers the skill with DeepSeek Harness. It never
  contains diagram logic; keep it that way.
- Repo-level checks live in `scripts/check.py`; run it before every push.

## Rules for a change

1. Run `python3 scripts/check.py` — it renders every example and runs both gates.
   A red gate is never "fixed" by editing a generated HTML file; fix the spec or
   the renderer and regenerate.
2. Any renderer change must re-render `skills/readable-diagrams/examples/*.html`
   in the same commit (`for f in examples/*.spec.json; do python3 scripts/render.py "$f" -o "${f%.spec.json}.html"; done`
   from the skill folder). Committed pages are what CI gates.
3. Version lives in four places: `package.json`, `.claude-plugin/plugin.json`,
   `.codex-plugin/plugin.json`, and the `version` line in `SKILL.md` metadata.
   Bump them together; `CHANGELOG.md` gets a section.
4. New diagram type: add the renderer, a type row in `SKILL.md`,
   `references/type-router.md` and `references/spec-schema.md`, an example spec
   under `examples/`, and raise the type list in `render.py`'s CLI text if any.
5. New visual language (colour, line style): it must have a legend entry and pass
   `comprehension_check.py`'s accent budget. Two accents is the ceiling.

## Things that are load-bearing — do not "simplify" them

- The page furniture (title / takeaway / caption / steps / legend). It is the
  product, not decoration.
- `self_check.py` is vendored MIT code from diagram-design; keep the attribution
  in `THIRD_PARTY_NOTICES.md`.
- Hover CSS is generated per node id. Removing the `data-node-id` /
  `data-edge-from` / `data-edge-to` / `data-step-for` attributes silently kills
  the interaction layer while every gate still passes.
