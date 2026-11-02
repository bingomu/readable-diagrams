#!/usr/bin/env python3
"""readable-diagrams · export

Turn a rendered page into a standalone .svg or a .png.

    python3 scripts/export.py out.html --svg out.svg
    python3 scripts/export.py out.html --png out.png [--scale 2]

SVG export keeps only the diagram's <svg> node (page furniture is dropped by
design). PNG export renders that SVG through headless Chrome/Chromium, so no
third-party Python package is needed.

Exit codes: 0 ok, 2 unreadable input, 3 no browser found, 4 browser failed.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME_CANDIDATES = [
    os.environ.get("CHROME_PATH", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def find_browser() -> str:
    for cand in CHROME_CANDIDATES:
        if cand and Path(cand).exists():
            return cand
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return ""


def extract_svg(html: str) -> str:
    m = re.search(r"<svg\b.*?</svg>", html, re.DOTALL)
    if not m:
        raise SystemExit("no <svg> element found; is this a readable-diagrams page?")
    svg = m.group(0)
    if "xmlns=" not in svg.split(">", 1)[0]:
        svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    return svg


def rasterize(svg: str, out: Path, scale: float = 2) -> None:
    browser = find_browser()
    if not browser:
        raise SystemExit("no Chrome/Chromium found; set CHROME_PATH or export SVG instead")
    vb = re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"', svg)
    w, h = (float(vb.group(1)), float(vb.group(2))) if vb else (960, 600)
    width, height = int(round(w * scale)), int(round(h * scale))
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{{margin:0;padding:0;background:transparent}}
svg{{display:block;width:{width}px;height:{height}px}}</style></head>
<body>{svg}</body></html>"""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "frame.html"
        src.write_text(page, encoding="utf-8")
        shot = Path(tmp) / "shot.png"
        cmd = [browser, "--headless=old", "--no-sandbox", "--disable-gpu",
               "--disable-crash-reporter", "--disable-breakpad", "--hide-scrollbars",
               "--no-first-run", f"--user-data-dir={tmp}/profile",
               f"--window-size={width},{height}",
               f"--screenshot={shot}", src.as_uri()]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if not shot.exists():
            raise SystemExit(f"browser did not produce a screenshot:\n{res.stderr[-800:]}")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(shot.read_bytes())


def main(argv=None):
    ap = argparse.ArgumentParser(description="Export a readable-diagrams page")
    ap.add_argument("html")
    ap.add_argument("--svg", help="write a standalone .svg")
    ap.add_argument("--png", help="write a .png")
    ap.add_argument("--scale", type=float, default=2.0, help="PNG scale (default 2)")
    args = ap.parse_args(argv)
    src = Path(args.html)
    if not src.exists():
        raise SystemExit(f"missing input: {src}")
    html = src.read_text(encoding="utf-8")
    svg = extract_svg(html)
    if not args.svg and not args.png:
        raise SystemExit("nothing to do: pass --svg and/or --png")
    if args.svg:
        dst = Path(args.svg)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(svg, encoding="utf-8")
        print(f"svg  {dst}")
    if args.png:
        dst = Path(args.png)
        rasterize(svg, dst, args.scale)
        print(f"png  {dst}  ({dst.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
