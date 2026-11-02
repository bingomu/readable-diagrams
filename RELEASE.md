# Release checklist

How this project is published, and what is left for each channel.

## Channels

| Channel | Artifact | Status |
| --- | --- | --- |
| GitHub (source of truth) | repo `bingomu/readable-diagrams`, release `v1.1.0` | ✅ published |
| DSH plugin marketplace | repo entry in `awesome-dsh-plugin` → `data/plugins/bingomu__readable-diagrams.yml` | ⏳ PR [#11412](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin/pull/11412) — repo must be 1 day old (2026-11-03) |
| npm (optional) | `dsh-readable-diagrams@1.1.0` | ⏸ not needed for any other channel — see "Do we need npm?" below |
| Claude Code plugin marketplace | `.claude-plugin/` | ✅ usable now via `/plugin marketplace add bingomu/readable-diagrams` |
| Codex | `.codex-plugin/` + `skills/` | ✅ usable now by copying the skill folder |

## Do we need npm?

No. Every channel above installs from GitHub:

- the DSH marketplace entry points at this repo and requires `dsh.bundle`
  (which is here), so `dsh plugin add <repo or release tarball>` works;
- Claude Code and Codex read the tree directly.

npm would only add the shorter `dsh plugin add dsh-readable-diagrams`. If we
decide to publish later:

```bash
npm login                      # or an Automation token
npm_config_cache=/tmp/npmcache npm publish   # name is free, dry-run already passes
```

## Publish a new version

1. Bump the version in `package.json`, `.claude-plugin/plugin.json`,
   `.codex-plugin/plugin.json` and `SKILL.md` `metadata.version`.
2. Add a `CHANGELOG.md` section.
3. Re-render the examples (`cd skills/readable-diagrams && for f in examples/*.spec.json; do python3 scripts/render.py "$f" -o "${f%.spec.json}.html"; done`).
4. `python3 scripts/check.py` must be green.
5. Commit, tag `vX.Y.Z`, push, `gh release create vX.Y.Z --notes-file …`.
6. npm (when a token is available): `npm_config_cache=/tmp/npmcache npm publish`.
7. DSH marketplace: update the entry's icon/description only if they changed; the
   list reads the repo, so a release is enough for updates.

## What a reviewer checks

- `package.json` declares `dsh.bundle` and `cordis.patch.yml` exists (required).
- The repo has real, working code (it does — eight example pages and a gate suite).
- Repo age ≥ 1 day.

## Local verification of the shipped package

```bash
npm_config_cache=/tmp/npmcache npm pack --dry-run   # 47 files, ~222 kB
node --input-type=module -e "import('./lib/index.js').then(async m => {
  let p; m.apply({ skills: { registerProvider: f => p = f() } });
  const [c] = await p.list(); const g = await p.get(c);
  console.log(c.name, g.content.includes('Running in DeepSeek Harness'));
})"
```
