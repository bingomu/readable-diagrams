# Contributing

## Layout

- `skills/readable-diagrams/` is the installable skill. Every path in `SKILL.md`
  is relative to that folder. It must stay runnable on its own (copy the folder
  somewhere and the gates still work).
- `lib/index.js` is the DSH plugin wrapper; it registers the skill and adds a
  runtime section with the absolute folder. No diagram logic there.
- `scripts/check.py` is the repo gate suite; CI runs exactly it.

## Before you push

```bash
python3 scripts/check.py
```

It renders every `examples/*.spec.json` into a temp directory, runs both gates on
the rendered page *and* on the committed `examples/*.html`, and parses
`lib/index.js`. A red gate is never fixed by editing generated HTML — fix the
spec or the renderer and regenerate.

## Changing the renderer

Re-render the committed examples in the same commit:

```bash
cd skills/readable-diagrams
for f in examples/*.spec.json; do
  python3 scripts/render.py "$f" -o "${f%.spec.json}.html"
done
```

The committed pages are what CI gates, so a stale page fails review.

## Adding a type

1. Add the renderer in `scripts/render.py` and register it in `RENDERERS`.
2. Add a row to `SKILL.md` §2 and to `references/type-router.md`, plus a full
   section in `references/spec-schema.md`.
3. Add `examples/<type>.spec.json`, render it, and make both gates pass with
   zero warnings.
4. Mention it in `README.md` / `README.zh.md` if it changes the headline list.

## New visual language

A new colour, fill or line style needs a legend entry and must survive
`comprehension_check.py`'s accent budget (≤2 focal elements). If a figure needs
more visual languages, it is probably two figures.

## Version bumps

The version lives in `package.json`, `.claude-plugin/plugin.json`,
`.codex-plugin/plugin.json` and the `metadata.version` line of `SKILL.md`.
Bump all four together and add a `CHANGELOG.md` section.

## Style

- Python: standard library only, 3.9-compatible. No formatter required; keep it
  readable.
- Copy: terse, specific, no marketing adjectives in code comments or docs.
- Tests: prefer a new example spec over a new unit-test harness — the gate suite
  is the test.
