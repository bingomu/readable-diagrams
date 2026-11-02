// dsh-readable-diagrams — registers the readable-diagrams skill with DeepSeek Harness.
//
// The skill itself is plain files under skills/readable-diagrams (SKILL.md,
// references, Python scripts, examples), so the same folder works for Claude
// Code, Codex and any agent that reads SKILL.md. This module only mounts it in
// DSH's skill registry and tells the agent where the folder is on disk.
import { statSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { join, sep } from "node:path";
import { fileURLToPath } from "node:url";

const SKILL_NAME = "readable-diagrams";
const PROVIDER = "dsh-readable-diagrams";
const BUNDLED_SKILL_RANK = 600;
const packageRoot = fileURLToPath(new URL("../", import.meta.url));

const DESCRIPTION =
  "Create one self-contained HTML page whose diagram a reader understands on " +
  "first look: architecture, flow, sequence, timeline, tree, layer stack, bar " +
  "comparison and quadrant, plus hand-authored chart families. Fuses a validated " +
  "JSON-spec renderer with an editorial design system and a machine-checked " +
  "comprehension contract (conclusion title, takeaway line, numbered reading " +
  "path, legend, caption, accessible SVG, contrast and type-size floors).";

function isFile(path) {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}

function stripFrontmatter(raw, path) {
  const match = /^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)/u.exec(raw);
  if (match === null) throw new Error(`${PROVIDER}: ${path} has no YAML frontmatter`);
  return raw.slice(match[0].length).trim();
}

/** Appended to the skill body so the agent knows the absolute folder on this machine. */
export function runtimeSection(skillDir) {
  const script = (name) => join(skillDir, "scripts", name);
  return [
    "",
    "",
    "## Running in DeepSeek Harness",
    "",
    "This skill's folder is:",
    "",
    "```",
    skillDir,
    "```",
    "",
    "Resolve every `scripts/...` path in this file against that folder, and quote it",
    "(the path can contain spaces):",
    "",
    "```sh",
    `python3 "${script("render.py")}" spec.json -o page.html --json`,
    `python3 "${script("self_check.py")}" page.html`,
    `python3 "${script("comprehension_check.py")}" page.html`,
    "```",
    "",
    "Both gates must pass before you hand the page over. Export only when asked:",
    "",
    "```sh",
    `python3 "${script("export.py")}" page.html --png figure.png --scale 2`,
    "```",
  ].join("\n");
}

export const name = SKILL_NAME;
export const inject = ["skills"];

export function apply(ctx) {
  const skillDir = join(packageRoot, "skills", SKILL_NAME);
  const skillPath = join(skillDir, "SKILL.md");
  if (!isFile(skillPath)) throw new Error(`${PROVIDER}: ${skillPath} is missing`);

  const candidate = {
    name: SKILL_NAME,
    description: DESCRIPTION,
    invocation: { modelInvocable: true, userInvocable: true },
    provider: PROVIDER,
    source: "bundled",
    rank: BUNDLED_SKILL_RANK,
    path: skillPath,
    resourceBase: { kind: "directory", path: skillDir.split(sep).join("/") },
  };

  const provider = {
    name: PROVIDER,
    list: () => Promise.resolve([candidate]),
    async get(item, options) {
      const { rank: _rank, ...summary } = item;
      const raw = await readFile(item.path, { encoding: "utf8", signal: options?.signal });
      return {
        ...summary,
        content: stripFrontmatter(raw, item.path) + runtimeSection(skillDir),
      };
    },
  };

  ctx.skills.registerProvider(() => provider);
}

export default { name: SKILL_NAME, inject, apply };
