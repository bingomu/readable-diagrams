#!/usr/bin/env python3
"""Repo gate suite — the same checks CI runs.

    python3 scripts/check.py

1. renders every `skills/readable-diagrams/examples/*.spec.json` into a temp dir
2. runs the structural gate and the comprehension gate on each rendered page
3. runs both gates on the committed example pages
4. parses `lib/index.js` as an ES module

Exit code 0 = everything passed. No third-party dependencies.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "readable-diagrams"
PY = sys.executable


def run(cmd, label):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    ok = proc.returncode == 0
    print(("  PASS  " if ok else "  FAIL  ") + label)
    if not ok:
        for line in (proc.stdout + proc.stderr).strip().splitlines()[-14:]:
            print("        " + line)
    return ok, proc


def main() -> int:
    failures = 0
    examples = sorted(SKILL.glob("examples/*.spec.json"))
    if not examples:
        print("no example specs found under", SKILL / "examples")
        return 1

    print("readable-diagrams · repo gates")
    print("skill:", SKILL)
    print("examples:", len(examples))
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for spec in examples:
            out = tmp / (spec.stem + ".html")
            ok, proc = run([PY, str(SKILL / "scripts" / "render.py"), str(spec),
                            "-o", str(out), "--json"], "render       " + spec.stem)
            if not ok:
                failures += 1
                continue
            info = json.loads(proc.stdout or "{}")
            if not info.get("nodes") and info.get("type") not in ("timeline", "bar", "quadrant", "layers"):
                print("  FAIL  empty diagram for", spec.stem)
                failures += 1
            for gate, label in ((("self_check.py"), "structure    "),
                                (("comprehension_check.py"), "comprehension ")):
                ok, _ = run([PY, str(SKILL / "scripts" / gate), str(out)], label + spec.stem)
                failures += 0 if ok else 1

    committed = sorted(SKILL.glob("examples/*.html"))
    if committed:
        ok, _ = run([PY, str(SKILL / "scripts" / "self_check.py"), *map(str, committed)],
                    "structure    committed examples (%d)" % len(committed))
        failures += 0 if ok else 1
        ok, _ = run([PY, str(SKILL / "scripts" / "comprehension_check.py"), *map(str, committed)],
                    "comprehension committed examples (%d)" % len(committed))
        failures += 0 if ok else 1

    node = shutil.which("node")
    if node:
        ok, _ = run([node, "--check", str(ROOT / "lib" / "index.js")],
                    "syntax       lib/index.js")
        failures += 0 if ok else 1

    print()
    if failures:
        print("FAILED: %d check(s)" % failures)
        return 1
    print("OK: all gates passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
