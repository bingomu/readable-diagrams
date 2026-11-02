#!/usr/bin/env python3
"""readable-diagrams · comprehension check (the reading gate)

Verifies that a generated page carries everything a reader needs to understand
the figure without the author in the room: a conclusion-shaped title, a one-line
takeaway, a caption, a legend, a numbered reading path, accessible SVG metadata,
a bounded focal accent count, legible type sizes and token contrast.

This gate is the fused skill's addition: Archify validates the diagram's
structure, diagram-design validates its SVG hygiene. This one validates that a
human can read it.

Usage:
    python3 scripts/comprehension_check.py out.html [more.html ...] [--json] [--strict]

Exit code 0 = pass (warnings allowed), 1 = at least one failure.
No third-party dependencies. Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

STRUCTURAL = {"architecture", "flow", "state", "sequence", "tree"}
CHARTY = {"bar", "quadrant", "timeline", "layers"}
MAX_NODES = {"architecture": 9, "flow": 9, "state": 9, "sequence": 7,
             "tree": 14, "timeline": 12, "bar": 12, "quadrant": 10, "layers": 6}

TOKEN_KEYS = ("paper", "ink", "muted", "soft", "accent", "link")


class Checker:
    def __init__(self, path, strict=False):
        self.path = path
        self.strict = strict
        self.items = []   # (level, code, message)

    def add(self, level, code, msg):
        self.items.append((level, code, msg))

    def fail(self, code, msg):
        self.add("FAIL", code, msg)

    def warn(self, code, msg):
        self.add("WARN", code, msg)

    def ok(self, code, msg):
        self.add("PASS", code, msg)

    # -- WCAG ----------------------------------------------------------- #
    @staticmethod
    def _lum(hexcolor):
        h = hexcolor.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        rgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

    @classmethod
    def contrast(cls, fg, bg):
        l1, l2 = cls._lum(fg), cls._lum(bg)
        hi, lo = max(l1, l2), min(l1, l2)
        return (hi + 0.05) / (lo + 0.05)

    # -- parsing -------------------------------------------------------- #
    def parse(self):
        src = Path(self.path).read_text(encoding="utf-8")
        if "\ufffd" in src:
            self.fail("encoding", "file contains U+FFFD replacement characters (mojibake)")
        if "</html>" not in src:
            self.fail("complete", "document does not end with </html> (truncated?)")
        self.src = src
        self.doc = SimpleDoc()
        self.doc.feed(src)
        self.doc.close()

    def run(self):
        self.parse()
        d = self.doc
        typ = getattr(d, "doc_type", "diagram")

        # 1. conclusion-shaped title
        title = "".join(d.h1).strip()
        if not title:
            self.fail("title", "missing <h1 class=rd-title>")
        elif len(title) > 60:
            self.warn("title-length", "title is %d chars; keep ≤60 so it reads at a glance" % len(title))
        elif len(title) < 6:
            self.fail("title-length", "title is too short to state a conclusion: %r" % title)
        else:
            self.ok("title", "title: %s" % title)

        # 2. takeaway line
        take = "".join(d.takeaway).strip()
        if not take:
            self.fail("takeaway", "missing one-line takeaway (.rd-takeaway)")
        elif not (8 <= len(take) <= 100):
            self.warn("takeaway-length", "takeaway is %d chars; 8–100 reads best" % len(take))
        else:
            self.ok("takeaway", "takeaway present (%d chars)" % len(take))

        # 3. caption / reading guide
        cap = "".join(d.caption).strip()
        if not cap:
            self.fail("caption", "missing figure caption (.rd-caption) — say how to read it")
        elif len(cap) < 12:
            self.warn("caption-length", "caption is very short: %r" % cap)
        else:
            self.ok("caption", "caption present (%d chars)" % len(cap))

        # 4. accessible SVG
        attrs = d.svg_attrs or {}
        if not attrs:
            self.fail("svg", "no <svg> found")
        else:
            if attrs.get("role") != "img":
                self.fail("a11y-role", "<svg> needs role=img")
            labelled = (attrs.get("aria-labelledby") or "").split()
            ids = set(re.findall(r'id="([^"]+)"', self.src))
            if len(labelled) < 2:
                self.fail("a11y-labelled", "<svg> aria-labelledby must name <title> and <desc>")
            elif not all(x in ids for x in labelled):
                self.fail("a11y-labelled", "aria-labelledby points at missing ids: %s" % labelled)
            if not d.title_text.strip():
                self.fail("a11y-title", "<title> text is empty")
            elif len(d.title_text.strip()) > 70:
                self.warn("a11y-title-length", "<title> is longer than 70 chars")
            if not d.desc_text.strip():
                self.fail("a11y-desc", "<desc> is empty — add one sentence about the content")
            elif d.desc_text.strip() == d.title_text.strip():
                self.fail("a11y-desc", "<desc> must say more than the title")
            else:
                self.ok("a11y", "accessible title + desc present")

        # 5. viewBox + responsive wrapper
        vb = attrs.get("viewBox") or attrs.get("viewbox") or ""
        m = re.match(r"\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*$", vb)
        if not m:
            self.fail("viewbox", "viewBox must be '0 0 W H', got %r" % vb)
        else:
            vbw = float(m.group(1))
            if not d.found_canvas:
                self.fail("wrapper", "SVG is not inside .rd-canvas (overflow-x:auto wrapper)")
            if not d.min_widths:
                csm = re.search(r"min-width:\s*([0-9.]+)px", d.css or "")
                if csm:
                    d.min_widths.append(float(csm.group(1)))
            if not d.min_widths:
                self.warn("min-width", "SVG has no min-width; it can shrink below its type ramp on phones")
            elif abs(d.min_widths[0] - vbw) > 1:
                self.warn("min-width", "SVG min-width %g != viewBox width %g" % (d.min_widths[0], vbw))
            else:
                self.ok("viewbox", "viewBox %gx%g with matching min-width wrapper" % (vbw, float(m.group(2))))

        # 6. legend when more than one visual language is in play
        kinds = set(re.findall(r'data-rd-kind="([^"]+)"', self.src))
        variants = set()
        if "url(#arrow-accent)" in self.src:
            variants.add("accent")
        if "url(#arrow-link)" in self.src:
            variants.add("link")
        need_legend = len(kinds - {"backend", "decision"}) >= 1 or len(variants) >= 1
        if need_legend and d.legend_items == 0:
            self.fail("legend", "diagram uses colour/kind distinctions but has no legend strip")
        elif d.legend_items:
            self.ok("legend", "legend lists %d items" % d.legend_items)

        # 7. reading path
        if d.steps:
            if d.steps < 2:
                self.warn("steps", "only one reading step; either order two steps or drop the list")
            else:
                self.ok("steps", "%d numbered reading steps" % d.steps)
        elif typ in STRUCTURAL:
            self.fail("steps", "structural diagram has no numbered reading path (.rd-steps)")
        else:
            self.warn("steps", "no numbered reading path; charts read fine without one")

        # 8. focal accent budget
        if d.focal > 2:
            self.fail("accent", "%d focal nodes; the accent budget is 2 per diagram" % d.focal)
        elif d.focal:
            self.ok("accent", "%d focal node(s) within budget" % d.focal)

        # 9. node budget
        cap_nodes = MAX_NODES.get(typ, 10)
        if d.nodes and d.nodes > cap_nodes:
            self.fail("nodes", "%d nodes exceeds the %s budget of %d; split overview + detail"
                      % (d.nodes, typ, cap_nodes))
        elif d.nodes:
            self.ok("nodes", "%d nodes within the %s budget" % (d.nodes, typ))

        # 10. edge labels: explain every non-obvious connector
        if typ in ("architecture", "flow", "state", "sequence") and d.edges:
            ratio = d.arrow_labels / max(d.edges, 1)
            if ratio < 0.6:
                self.warn("edge-labels", "only %d/%d edges carry a label; name the rest or merge them"
                          % (d.arrow_labels, d.edges))
            else:
                self.ok("edge-labels", "%d/%d edges labelled" % (d.arrow_labels, d.edges))

        # 11. type ramp floors
        floors = {"name": 11, "sublabel": 8, "arrow": 8, "eyebrow": 7}
        small = []
        for role, size in d.font_sizes:
            floor = floors.get(role, 8)
            if size and size < floor:
                small.append((role, size))
        if small:
            self.warn("type-size", "text below the ramp floor: %s" % small[:6])
        else:
            self.ok("type", "all text at or above the role ramp floors")

        # 12. token contrast
        css = d.css or ""
        toks = dict(re.findall(r"--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8})", css))
        if toks:
            bg = toks.get("paper")
            bad = []
            for key in ("ink", "muted", "soft", "accent", "link"):
                fg = toks.get(key)
                if fg and bg:
                    ratio = self.contrast(fg, bg)
                    if ratio < 4.5:
                        bad.append("%s %.2f:1" % (key, ratio))
            if bad:
                self.fail("contrast", "tokens below 4.5:1 on paper: %s" % ", ".join(bad))
            else:
                self.ok("contrast", "all text tokens clear 4.5:1 on paper")

        # 13. connectors are orthogonal (no diagonal straight segments)
        diag = []
        for dd in d.paths:
            cur = None
            for cmd, rest in re.findall(r"([MLHVQCZ])([^MLHVQCZ]*)", dd):
                nums = [float(n) for n in re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)", rest)]
                if cmd == "M" and len(nums) >= 2:
                    cur = (nums[0], nums[1])
                elif cmd == "L" and cur and len(nums) >= 2:
                    nx, ny = nums[0], nums[1]
                    if abs(nx - cur[0]) > 0.6 and abs(ny - cur[1]) > 0.6:
                        diag.append(dd[:48])
                    cur = (nx, ny)
                elif cmd == "H" and cur and nums:
                    cur = (nums[0], cur[1])
                elif cmd == "V" and cur and nums:
                    cur = (cur[0], nums[0])
                elif cmd in ("Q", "C", "Z") and cur:
                    if len(nums) >= 2:
                        cur = (nums[-2], nums[-1])
        if diag:
            self.warn("connectors", "%d diagonal connector segment(s); use right-angle elbows" % len(diag))
        elif d.paths:
            self.ok("connectors", "connectors are right-angled")

        # 14. repeated node names make the figure harder to scan
        names = re.findall(r'<text[^>]*data-role="name"[^>]*>([^<]+)</text>', self.src)
        dupes = {n for n in names if names.count(n) > 1 and len(n) > 1}
        if dupes:
            self.warn("duplicates", "repeated node labels: %s" % ", ".join(sorted(dupes)[:4]))
        else:
            self.ok("labels", "node labels are distinct")

        # 15. reading furniture must not be empty
        if not d.found_rd_doc:
            self.warn("doc", "no .rd-doc container; page furniture may not be styled")

        return self


class SimpleDoc(HTMLParser):
    """A small, explicit DOM-ish collector (kept separate for clarity)."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr", "circle",
            "rect", "line", "path", "polygon", "marker", "stop", "text"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.h1 = []
        self.takeaway = []
        self.caption = []
        self.steps = 0
        self.legend_items = 0
        self.svg_attrs = None
        self.title_text = ""
        self.desc_text = ""
        self.nodes = 0
        self.focal = 0
        self.edges = 0
        self.arrow_labels = 0
        self.font_sizes = []
        self.paths = []
        self.css = ""
        self.found_canvas = False
        self.found_rd_doc = False
        self.min_widths = []
        self.doc_type = "diagram"
        self.in_style = False
        self.in_title = False
        self.in_desc = False
        self.capture = None
        self.capture_tag = None

    def _cls(self, a):
        return (a.get("class") or "")

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = self._cls(a)
        if tag not in self.VOID:
            self.stack.append((tag, cls))
        if "rd-doc" in cls:
            self.found_rd_doc = True
        if "rd-canvas" in cls or "diagram-container" in cls:
            self.found_canvas = True
        if tag == "h1" and "rd-title" in cls:
            self.capture, self.capture_tag = "h1", tag
        elif "rd-takeaway" in cls:
            self.capture, self.capture_tag = "takeaway", tag
        elif "rd-caption" in cls or tag == "figcaption":
            self.capture, self.capture_tag = "caption", tag
        elif tag == "ol" and "rd-steps" in cls:
            self.capture, self.capture_tag = "steps", tag
        elif tag == "style":
            self.in_style = True
        elif tag == "svg" and self.svg_attrs is None:
            self.svg_attrs = a
            self.doc_type = a.get("data-rd-type", "diagram")
            sm = re.search(r"min-width:\s*([0-9.]+)px", a.get("style") or "")
            if sm:
                self.min_widths.append(float(sm.group(1)))
        elif tag == "title" and self.svg_attrs is not None and not self.title_text:
            self.in_title = True
        elif tag == "desc" and self.svg_attrs is not None and not self.desc_text:
            self.in_desc = True
        elif tag == "g" and a.get("data-rd-node") == "1":
            self.nodes += 1
            self.focal += (a.get("data-rd-kind") == "focal")
        elif a.get("data-rd-edge") == "1":
            self.edges += 1
        elif tag == "li":
            ctx = " ".join(c for _, c in self.stack)
            if "rd-steps" in ctx:
                self.steps += 1
            elif "rd-legend" in ctx:
                self.legend_items += 1
        if tag == "text":
            role = a.get("data-role")
            if role:
                try:
                    size = float(a.get("font-size") or 0)
                except ValueError:
                    size = 0.0
                self.font_sizes.append((role, size))
                if role == "arrow":
                    self.arrow_labels += 1
        if tag == "path":
            self.paths.append(a.get("d") or "")
        # min-width may live on a child <svg> with inline style
        if tag == "svg":
            sm = re.search(r"min-width:\s*([0-9.]+)px", a.get("style") or "")
            if sm and not self.min_widths:
                self.min_widths.append(float(sm.group(1)))
        # inline style attribute carrying min-width is handled above only for svg

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == self.capture_tag:
            self.capture, self.capture_tag = None, None
        if tag == "style":
            self.in_style = False
        if tag == "title":
            self.in_title = False
        if tag == "desc":
            self.in_desc = False
        if tag == "svg" and self.svg_attrs is not None:
            pass
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.in_style:
            self.css += data
            return
        if self.in_title:
            self.title_text += data
            return
        if self.in_desc:
            self.desc_text += data
            return
        if self.capture == "h1":
            self.h1.append(data)
        elif self.capture == "takeaway":
            self.takeaway.append(data)
        elif self.capture == "caption":
            self.caption.append(data)


def check_file(path, strict=False):
    c = Checker(path, strict).run()
    fails = [i for i in c.items if i[0] == "FAIL"]
    warns = [i for i in c.items if i[0] == "WARN"]
    passes = [i for i in c.items if i[0] == "PASS"]
    return c, fails, warns, passes


def main(argv=None):
    ap = argparse.ArgumentParser(description="Comprehension gate for readable-diagrams output")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args(argv)
    results = []
    failed = False
    for f in args.files:
        c, fails, warns, passes = check_file(f, args.strict)
        if fails or (args.strict and warns):
            failed = True
        results.append({"file": f, "fails": fails, "warns": warns, "passes": passes})
        if not args.json:
            print("readable-diagrams · comprehension gate")
            print(f"file: {f}")
            for level, code, msg in c.items:
                print(f"  [{level:4s}] {code:14s} {msg}")
            print(f"  RESULT: {len(passes)} pass · {len(warns)} warn · {len(fails)} fail")
            print()
    if args.json:
        print(json.dumps([{"file": r["file"],
                           "fail": [m for _, _, m in r["fails"]],
                           "warn": [m for _, _, m in r["warns"]]} for r in results],
                         ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
