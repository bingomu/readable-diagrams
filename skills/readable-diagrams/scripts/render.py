#!/usr/bin/env python3
"""readable-diagrams · spec renderer

JSON spec -> one self-contained editorial HTML page that a reader can understand
on first look. Fuses Archify's validated-IR pipeline with diagram-design's
editorial design system, and adds the comprehension layer: conclusion-first
title, takeaway line, numbered reading path, legend strip, caption.

Usage:
    python3 scripts/render.py spec.json -o out.html [--json]

Types: architecture, flow, sequence, timeline, tree, layers, bar, quadrant.

No third-party dependencies. Python 3.9+.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import re
import sys
from pathlib import Path

__version__ = "1.1.0"

# --------------------------------------------------------------------------- #
# Theme tokens (diagram-design's editorial skin, light + dark)
# --------------------------------------------------------------------------- #

THEMES = {
    "light": {
        "paper": "#f5f5f5",
        "paper-2": "#ececec",
        "ink": "#2d3142",
        "ink-strong": "#111111",
        "muted": "#4f5d75",
        "soft": "#5a6580",
        "rule": "rgba(45,49,66,0.12)",
        "rule-solid": "#bfc0c0",
        "accent": "#bf4520",
        "accent-tint": "rgba(191,69,32,0.08)",
        "link": "#2e5aa8",
        "white": "#ffffff",
        "page": "#f5f5f5",
    },
    "dark": {
        "paper": "#2d3142",
        "paper-2": "#393e53",
        "ink": "#f5f5f5",
        "ink-strong": "#ffffff",
        "muted": "#bfc0c0",
        "soft": "#949eb2",
        "rule": "rgba(245,245,245,0.12)",
        "rule-solid": "rgba(191,192,192,0.25)",
        "accent": "#f08a59",
        "accent-tint": "rgba(240,138,89,0.10)",
        "link": "#739fdf",
        "white": "#ffffff",
        "page": "#2d3142",
    },
}

FONT_TITLE = "'Instrument Serif', 'Noto Serif SC', 'Songti SC', 'SimSun', Georgia, serif"
FONT_SANS = ("'Geist', 'PingFang SC', 'Hiragino Sans GB', 'Noto Sans SC', "
             "'Microsoft YaHei', system-ui, -apple-system, sans-serif")
FONT_MONO = ("'Geist Mono', ui-monospace, 'SFMono-Regular', Menlo, "
             "'PingFang SC', monospace")

KIND_LABELS = {
    "zh": {
        "focal": "焦点节点",
        "backend": "服务 / 组件",
        "store": "存储 / 状态",
        "external": "外部系统",
        "input": "用户 / 入口",
        "optional": "可选 / 异步",
        "security": "边界 / 安全",
        "decision": "判断",
    },
    "en": {
        "focal": "focal node",
        "backend": "service",
        "store": "store",
        "external": "external",
        "input": "actor / entry",
        "optional": "optional / async",
        "security": "boundary",
        "decision": "decision",
    },
}
VARIANT_LABELS = {
    "zh": {"default": "调用", "accent": "主路径", "link": "外部调用",
           "dashed": "异步 / 返回", "return": "返回"},
    "en": {"default": "call", "accent": "primary path", "link": "external call",
           "dashed": "async / return", "return": "return"},
}

RAMP = {
    "standard": dict(title=28, name=12, sub=9, arrow=8, eyebrow=8, box_min_h=48, gap=32),
    "presentation": dict(title=40, name=16, sub=12, arrow=12, eyebrow=8, box_min_h=64, gap=40),
    "print": dict(title=32, name=12, sub=9, arrow=8, eyebrow=8, box_min_h=48, gap=24),
}
PRESETS = {
    "doc-inline": dict(w=960, h=600, ramp="standard", margin=40),
    "doc-wide": dict(w=1280, h=720, ramp="standard", margin=40),
    "slide-16x9": dict(w=1280, h=720, ramp="presentation", margin=48),
    "slide-4x3": dict(w=1024, h=768, ramp="presentation", margin=48),
    "social-og": dict(w=1200, h=632, ramp="presentation", margin=64),
    "social-square": dict(w=1080, h=1080, ramp="presentation", margin=56),
    "print-a4-landscape": dict(w=1120, h=792, ramp="print", margin=40),
    "print-a3-landscape": dict(w=1584, h=1120, ramp="print", margin=56),
    "fit": dict(w=None, h=None, ramp="standard", margin=40),
}


# --------------------------------------------------------------------------- #
# small utilities
# --------------------------------------------------------------------------- #

def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def hex_rgb(h: str):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgba(color: str, alpha: float) -> str:
    r, g, b = hex_rgb(color)
    return "rgba(%d,%d,%d,%s)" % (r, g, b, ("%.3f" % alpha).rstrip("0").rstrip("."))


def is_wide(ch: str) -> bool:
    o = ord(ch)
    return (0x1100 <= o <= 0x115F or 0x2E80 <= o <= 0xA4CF or
            0xAC00 <= o <= 0xD7A3 or 0xF900 <= o <= 0xFAFF or
            0xFE30 <= o <= 0xFE6F or 0xFF00 <= o <= 0xFF60 or
            0xFFE0 <= o <= 0xFFE6 or 0x1F300 <= o <= 0x1FAFF)


def has_cjk(s: str) -> bool:
    return any(is_wide(c) and not (0x1F300 <= ord(c) <= 0x1FAFF) for c in s)


def text_w(s: str, size: float, mono: bool = False) -> float:
    """Width budget: wide/full-width char = 1em, latin = .60em sans / .62em mono."""
    unit = 0.62 if mono else 0.60
    total = 0.0
    for ch in str(s):
        if is_wide(ch):
            total += 1.0
        elif ch in "\u200b\u200c\u200d\ufeff":
            continue
        else:
            total += unit
    return total * size


def wrap_text(s: str, max_px: float, size: float, mono: bool = False):
    """Greedy wrap; CJK breaks anywhere, latin breaks on spaces."""
    s = str(s)
    if text_w(s, size, mono) <= max_px:
        return [s]
    lines, cur, cur_w = [], "", 0.0
    tokens = []
    buf = ""
    for ch in s:
        if ch == " " or is_wide(ch):
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(ch)
        else:
            buf += ch
    if buf:
        tokens.append(buf)
    for tok in tokens:
        w = text_w(tok, size, mono)
        space_w = text_w(" ", size, mono)
        need = w + (space_w if (cur and not is_wide(tok[0]) and tok != " ") else 0)
        if cur and cur_w + need > max_px:
            lines.append(cur.rstrip())
            cur = "" if tok == " " else tok
            cur_w = 0.0 if tok == " " else w
        else:
            if cur and not is_wide(tok[0]) and tok != " ":
                cur += " "
                cur_w += space_w
            cur += tok
            cur_w += w
    if cur.strip():
        lines.append(cur.rstrip())
    return lines or [""]


def rounded_path(points, r: float = 8.0) -> str:
    """Orthogonal polyline through points, with quarter-arc corners."""
    pts = [tuple(map(float, p)) for p in points]
    if len(pts) < 2:
        return ""
    out = ["M %.1f,%.1f" % pts[0]]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        d1 = (p1[0] - p0[0], p1[1] - p0[1])
        d2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1 = math.hypot(*d1) or 1.0
        l2 = math.hypot(*d2) or 1.0
        rr = min(r, l1 / 2.0, l2 / 2.0)
        a = (p1[0] - d1[0] / l1 * rr, p1[1] - d1[1] / l1 * rr)
        b = (p1[0] + d2[0] / l2 * rr, p1[1] + d2[1] / l2 * rr)
        out.append("L %.1f,%.1f" % a)
        out.append("Q %.1f,%.1f %.1f,%.1f" % (p1[0], p1[1], b[0], b[1]))
    out.append("L %.1f,%.1f" % pts[-1])
    return " ".join(out)


# --------------------------------------------------------------------------- #
# Scene: collects svg nodes + tracks the painted bounding box
# --------------------------------------------------------------------------- #

class Scene:
    def __init__(self):
        self.parts = []
        self.x0 = self.y0 = float("inf")
        self.x1 = self.y1 = float("-inf")

    def add(self, markup, x0, y0, x1, y1):
        self.parts.append(markup)
        self.x0 = min(self.x0, x0)
        self.y0 = min(self.y0, y0)
        self.x1 = max(self.x1, x1)
        self.y1 = max(self.y1, y1)

    @property
    def empty(self):
        return self.x0 == float("inf")

    def box(self):
        if self.empty:
            return 0, 0, 0, 0
        return self.x0, self.y0, self.x1, self.y1

    def markup(self):
        return "".join(self.parts)


class Canvas:
    """Emits diagram primitives against a theme, tracking bounds in a Scene."""

    def __init__(self, theme, ramp, lang="zh"):
        self.t = theme
        self.ramp = ramp
        self.lang = lang
        self.scene = Scene()
        self.accent_count = 0
        self.node_count = 0
        self.node_ids = []
        self.edge_count = 0
        self.labeled_edges = 0

    # -- paint helpers ------------------------------------------------------ #
    def role_fill(self, kind):
        t = self.t
        if kind == "focal":
            return t["accent-tint"]
        if kind == "backend":
            return t["white"] if t["paper"] == "#f5f5f5" else rgba(t["ink"], 0.10)
        if kind == "store":
            return rgba(t["ink"], 0.05)
        if kind == "external":
            return rgba(t["ink"], 0.03)
        if kind == "input":
            return rgba(t["muted"], 0.10)
        if kind == "optional":
            return rgba(t["ink"], 0.02)
        if kind == "security":
            return rgba(t["accent"], 0.05)
        if kind == "decision":
            return t["white"] if t["paper"] == "#f5f5f5" else rgba(t["ink"], 0.12)
        return t["white"] if t["paper"] == "#f5f5f5" else rgba(t["ink"], 0.10)

    def role_stroke(self, kind):
        t = self.t
        if kind == "focal":
            return t["accent"]
        if kind == "backend":
            return t["ink"]
        if kind == "store":
            return t["muted"]
        if kind == "external":
            return rgba(t["ink"], 0.30)
        if kind == "input":
            return t["soft"]
        if kind == "optional":
            return rgba(t["ink"], 0.20)
        if kind == "security":
            return rgba(t["accent"], 0.50)
        if kind == "decision":
            return t["ink"]
        return t["ink"]

    def dash(self, kind):
        return ' stroke-dasharray="4,3"' if kind in ("optional", "security") else ""

    def rect(self, x, y, w, h, fill, stroke=None, sw=1, rx=6, dash="", extra=""):
        m = ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" fill="%s"'
             % (x, y, w, h, rx, fill))
        if stroke:
            m += ' stroke="%s" stroke-width="%s"' % (stroke, sw)
        m += dash + extra + "/>"
        self.scene.add(m, x, y, x + w, y + h)
        return m

    def line(self, x1, y1, x2, y2, stroke, sw=1, dash="", marker="", extra=""):
        m = ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"'
             % (x1, y1, x2, y2, stroke, sw))
        if dash:
            m += ' stroke-dasharray="%s"' % dash
        if marker:
            m += ' marker-end="url(#%s)"' % marker
        m += extra + "/>"
        self.scene.add(m, min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        return m

    def path(self, d, stroke, sw=1.2, dash="", marker="", extra=""):
        m = ('<path d="%s" fill="none" stroke="%s" stroke-width="%s"'
             % (d, stroke, sw))
        if dash:
            m += ' stroke-dasharray="%s"' % dash
        if marker:
            m += ' marker-end="url(#%s)"' % marker
        m += extra + "/>"
        self.scene.add(m, *path_bbox(d))
        return m

    def _text(self, x, y, s, size, role, fill, anchor="middle", weight=None,
              family=None, spacing=None, extra=""):
        """Return (markup, bbox) without touching the scene."""
        fam = family or (FONT_MONO if role in ("sublabel", "eyebrow", "arrow") else FONT_SANS)
        w = text_w(s, size, mono=(fam == FONT_MONO))
        if anchor == "middle":
            x0, x1 = x - w / 2, x + w / 2
        elif anchor == "end":
            x0, x1 = x - w, x
        else:
            x0, x1 = x, x + w
        y0, y1 = y - size * 0.82, y + size * 0.28
        attrs = ' fill="%s" font-size="%s" font-family="%s" text-anchor="%s" data-role="%s"'
        attrs = attrs % (fill, fmt(size), fam, anchor, role)
        if weight:
            attrs += ' font-weight="%s"' % weight
        if spacing:
            attrs += ' letter-spacing="%s"' % spacing
        m = '<text x="%.1f" y="%.1f"%s%s>%s</text>' % (x, y, attrs, extra, esc(s))
        return m, (x0, y0, x1, y1)

    def text(self, x, y, s, size, role, fill, anchor="middle", weight=None,
             family=None, spacing=None, extra=""):
        m, bb = self._text(x, y, s, size, role, fill, anchor, weight, family, spacing, extra)
        self.scene.add(m, *bb)
        return m

    def _circle(self, cx, cy, r, fill, stroke=None, sw=1, extra=""):
        m = '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"' % (cx, cy, r, fill)
        if stroke:
            m += ' stroke="%s" stroke-width="%s"' % (stroke, sw)
        m += extra + "/>"
        return m, (cx - r, cy - r, cx + r, cy + r)

    def circle(self, cx, cy, r, fill, stroke=None, sw=1, extra=""):
        m, bb = self._circle(cx, cy, r, fill, stroke, sw, extra)
        self.scene.add(m, *bb)
        return m

    def wrap(self, start, open_tag, close_tag="</g>"):
        """Wrap scene parts emitted after `start` in a group (for hover targets)."""
        parts = self.scene.parts[start:]
        self.scene.parts[start:] = [open_tag] + parts + [close_tag]

    # -- composite: node box ------------------------------------------------- #
    def node(self, x, y, w, h, label, kind="backend", sublabel=None, step=None,
             node_id=None, font_name=None, font_sub=None, index=0):
        """Draw an editorial node box; returns markup."""
        if node_id and node_id not in self.node_ids:
            self.node_ids.append(node_id)
        fill, stroke = self.role_fill(kind), self.role_stroke(kind)
        dash = self.dash(kind)
        parts = []
        nid_attr = (' data-node-id="%s"' % node_id) if node_id else ""
        if kind == "decision":
            cut = min(16.0, h / 3.0)
            pts = "%.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f" % (
                x + cut, y, x + w - cut, y, x + w, y + h / 2, x + w - cut, y + h,
                x + cut, y + h, x, y + h / 2)
            parts.append('<polygon class="rd-mask" points="%s" fill="%s"/>' % (pts, self.t["paper"]))
            parts.append('<g class="rd-node" data-rd-node="1" data-rd-kind="%s"%s style="--i:%d">'
                         % (kind, nid_attr, index))
            parts.append('<title>%s</title>' % esc(label))
            parts.append('<polygon class="rd-shape" points="%s" fill="%s" stroke="%s" stroke-width="1"/>'
                         % (pts, fill, stroke))
        else:
            # opaque paper mask so connectors never bleed through
            parts.append('<rect class="rd-mask" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="6" fill="%s"/>'
                         % (x, y, w, h, self.t["paper"]))
            parts.append('<g class="rd-node" data-rd-node="1" data-rd-kind="%s"%s style="--i:%d">'
                         % (kind, nid_attr, index))
            parts.append('<title>%s</title>' % esc(label))
            parts.append('<rect class="rd-shape" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="6" fill="%s" '
                         'stroke="%s" stroke-width="1"%s/>'
                         % (x, y, w, h, fill, stroke, dash))
        if kind == "focal":
            self.accent_count += 1
        cx = x + w / 2
        name_size = self.ramp["name"]
        sub_size = self.ramp["sub"]
        lines = wrap_text(label, w - 20, name_size)
        line_h = name_size * 1.35
        block_h = line_h * len(lines) + (sub_size * 1.5 if sublabel else 0)
        ty = y + (h - block_h) / 2 + name_size * 0.95
        for i, ln in enumerate(lines):
            m, _ = self._text(cx, ty + i * line_h, ln, name_size, "name",
                              self.t["ink"], weight="600",
                              family=font_name or FONT_SANS)
            parts.append(m)
        if sublabel:
            m, _ = self._text(cx, ty + line_h * (len(lines) - 1) + sub_size * 1.6,
                              sublabel, sub_size, "sublabel", self.t["muted"],
                              family=font_sub or FONT_MONO)
            parts.append(m)
        # reading-order badge
        if step:
            bx, by = x + w - 2, y + 2
            cm, _ = self._circle(bx, by, 9, self.t["accent"])
            tm, _ = self._text(bx, by + 3.4, str(step), 10, "eyebrow",
                               self.t["white"], weight="600", family=FONT_SANS)
            parts.append(cm)
            parts.append(tm)
        parts.append("</g>")
        markup = "".join(parts)
        self.node_count += 1
        self.scene.add(markup, x - 10, y - 10, x + w + 10, y + h + 10)
        return markup


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def path_bbox(d: str):
    nums = [float(n) for n in re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)", d or "")]
    xs, ys = nums[0::2], nums[1::2]
    if not xs:
        return 0, 0, 0, 0
    return min(xs), min(ys), max(xs), max(ys)


# --------------------------------------------------------------------------- #
# Layout engines — each returns (markup, width, height, extras)
# --------------------------------------------------------------------------- #

def _node_size(canvas, node, max_w=190):
    size = canvas.ramp["name"]
    sub_size = canvas.ramp["sub"]
    label = str(node.get("label", node["id"]))
    sub = node.get("sublabel")
    w_name = min(text_w(label, size) + 40, max_w)
    w_sub = text_w(sub, sub_size) + 32 if sub else 0
    w = max(112, w_name, w_sub)
    w = math.ceil(w / 4.0) * 4
    lines = wrap_text(label, w - 20, size)
    h = max(canvas.ramp["box_min_h"], 20 + len(lines) * size * 1.35 + (14 if sub else 0))
    h = math.ceil(h / 4.0) * 4
    return w, h


def _topo_layers(ids, edges):
    indeg = {n: 0 for n in ids}
    adj = {n: [] for n in ids}
    for e in edges:
        a, b = e["from"], e["to"]
        if a in indeg and b in indeg:
            adj[a].append(b)
            indeg[b] += 1
    layer = {n: 0 for n in ids}
    queue = [n for n in ids if indeg[n] == 0]
    seen = set()
    while queue:
        n = queue.pop(0)
        seen.add(n)
        for m in adj[n]:
            layer[m] = max(layer[m], layer[n] + 1)
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    for n in ids:  # cycle leftovers keep their best estimate
        if n not in seen and not adj.get(n):
            layer[n] = max(layer.values(), default=0) + 1
    return layer



def _wrap_label(canvas, start, from_id, to_id):
    attrs = ""
    if from_id:
        attrs += ' data-edge-from="%s"' % from_id
    if to_id:
        attrs += ' data-edge-to="%s"' % to_id
    canvas.wrap(start, '<g class="rd-edge-label"%s>' % attrs)


def edge_label(canvas, pts, label, index=0, from_id=None, to_id=None):
    """Place an edge label on the best segment: above a long horizontal run,
    beside a long vertical run, otherwise above the source."""
    start = len(canvas.scene.parts)
    lab_size = canvas.ramp["arrow"] if not has_cjk(label) else 11
    mono = not has_cjk(label)
    lw = text_w(label, lab_size, mono=mono) + 10
    hs = []   # horizontal segments that can hold the label
    vs = []   # vertical segments long enough
    for p, q in zip(pts, pts[1:]):
        dx, dy = abs(q[0] - p[0]), abs(q[1] - p[1])
        if dx >= lw + 12:
            hs.append((dx, p, q))
        if dy >= 30:
            vs.append((dy, p, q))
    best = None
    if hs:
        # the closest-to-target run is the easiest to read; fall back to the longest
        best = ("h",) + hs[-1][1:]
    elif vs:
        best = ("v",) + max(vs)[1:]
    if best is None:
        # source-anchored: sit just after the source edge, above the line,
        # inside the column gap so no node can cover it
        sx, sy = pts[0]
        nx, ny = pts[1]
        if abs(ny - sy) < 1:  # first run is horizontal
            avail = max(30.0, abs(nx - sx) - 14)
            lines = wrap_text(label, avail, lab_size)
            y = sy - 21 - (index % 2) * 15
            for i, ln in enumerate(lines):
                yy = y - i * 13
                wln = text_w(ln, lab_size, mono=mono) + 10
                canvas.rect(sx + 8, yy - 1, wln, 14, canvas.t["paper"], rx=2)
                canvas.text(sx + 8 + wln / 2, yy + 10.5, ln, lab_size, "arrow",
                            canvas.t["soft"], spacing="0.04em")
        else:  # first run is vertical — label to the right of the line
            canvas.rect(sx + 6, sy - lw / 2 if False else sy - 7, lw, 14,
                        canvas.t["paper"], rx=2)
            canvas.text(sx + 6 + lw / 2, sy + 3, label, lab_size, "arrow",
                        canvas.t["soft"])
        _wrap_label(canvas, start, from_id, to_id)
        return
    kind, p, q = best
    if kind == "h":
        mx, my = (p[0] + q[0]) / 2, p[1]
        my -= (index % 2) * 15
        canvas.rect(mx - lw / 2, my - 24, lw, 14, canvas.t["paper"], rx=2)
        canvas.text(mx, my - 12, label, lab_size, "arrow", canvas.t["soft"],
                    spacing="0.04em")
        _wrap_label(canvas, start, from_id, to_id)
    else:
        mx, my = p[0], (p[1] + q[1]) / 2
        canvas.rect(mx + 8, my - 7, lw, 13, canvas.t["paper"], rx=2)
        canvas.text(mx + 8 + lw / 2, my + 3, label, lab_size, "arrow",
                    canvas.t["soft"])


def render_graph(canvas, spec, kind="architecture"):
    """architecture / flow / state: layered left-to-right graph."""
    nodes = spec.get("nodes", [])
    edges = spec.get("edges", [])
    zones = spec.get("zones", [])
    ids = [n["id"] for n in nodes]
    by_id = {n["id"]: n for n in nodes}

    sizes = {n["id"]: _node_size(canvas, n) for n in nodes}
    explicit_col = any("col" in n for n in nodes)
    if explicit_col:
        layer = {n["id"]: int(n.get("col", 0)) for n in nodes}
    else:
        layer = _topo_layers(ids, edges)
    layers = {}
    for nid in ids:
        layers.setdefault(layer.get(nid, 0), []).append(nid)
    for k in layers:
        layers[k].sort(key=lambda i: (int(by_id[i].get("row", 0)), ids.index(i)))

    # one barycenter pass to cut connector crossings
    preds = {n: [] for n in ids}
    for e in edges:
        if e["from"] in preds and e["to"] in preds:
            preds[e["to"]].append(e["from"])
    for lk in sorted(layers)[1:]:
        idx_in_prev = {}
        for pk in sorted(layers):
            if pk >= lk:
                break
            for j, nid in enumerate(layers[pk]):
                idx_in_prev.setdefault(nid, j)
        def bary(nid):
            ps = [idx_in_prev[p] for p in preds[nid] if p in idx_in_prev]
            return sum(ps) / len(ps) if ps else 1e9
        layers[lk].sort(key=bary)

    gap_x, gap_y = 132, canvas.ramp["gap"]
    x_of, y_of, pos = {}, {}, {}
    x = 0.0
    max_layer_h = 0.0
    for lk in sorted(layers):
        col = layers[lk]
        col_w = max(sizes[n][0] for n in col)
        total_h = sum(sizes[n][1] for n in col) + gap_y * (len(col) - 1)
        max_layer_h = max(max_layer_h, total_h)
        y = -total_h / 2
        for nid in col:
            w, h = sizes[nid]
            pos[nid] = (x + (col_w - w) / 2, y, w, h)
            y += h + gap_y
        x_of[lk] = x
        x += col_w + gap_x

    # zones painted first
    for z in zones:
        members = [n["id"] for n in nodes if n.get("zone") == z["id"]]
        if not members:
            continue
        xs0 = min(pos[m][0] for m in members) - 20
        ys0 = min(pos[m][1] for m in members) - 36
        xs1 = max(pos[m][0] + pos[m][2] for m in members) + 20
        ys1 = max(pos[m][1] + pos[m][3] for m in members) + 20
        canvas.rect(xs0, ys0, xs1 - xs0, ys1 - ys0, rgba(canvas.t["ink"], 0.02),
                    rgba(canvas.t["ink"], 0.10), sw=0.8, rx=8)
        canvas.text(xs0 + 14, ys0 + 16, str(z.get("label", z["id"])).upper(),
                    canvas.ramp["eyebrow"], "eyebrow", canvas.t["soft"],
                    anchor="start", spacing="0.14em")

    # edges painted before nodes; labels collected and painted after all strokes
    pending_labels = []
    for i, e in enumerate(edges):
        a, b = e["from"], e["to"]
        if a not in pos or b not in pos:
            continue
        ax, ay, aw, ah = pos[a]
        bx, by, bw, bh = pos[b]
        variant = e.get("variant", "default")
        stroke = {"accent": canvas.t["accent"], "link": canvas.t["link"]}.get(
            variant, canvas.t["muted"])
        marker = {"accent": "arrow-accent", "link": "arrow-link"}.get(variant, "arrow")
        dash = "5,4" if variant in ("dashed", "return") else ""
        sw = 1.4 if variant == "accent" else 1.1
        la, lb = layer[a], layer[b]
        pts = []
        if abs(lb - la) == 1 and bx > ax:
            sy, ey = ay + ah / 2, by + bh / 2
            sx, ex = ax + aw, bx
            if abs(ey - sy) < 1:
                pts = [(sx, sy), (ex, ey)]
            else:
                mid = sx + 24 + (i % 8) * 10
                mid = min(mid, ex - 24)
                pts = [(sx, sy), (mid, sy), (mid, ey), (ex, ey)]
        elif abs(lb - la) == 1 and bx < ax:  # right-to-left layer (return edge)
            sy, ey = ay + ah / 2, by + bh / 2
            sx, ex = ax, bx + bw
            mid = sx - 40 - (i % 4) * 16
            mid = max(mid, ex + 24)
            pts = [(sx, sy), (mid, sy), (mid, ey), (ex, ey)]
        elif bx <= ax and lb == la:
            cy = max(ay + ah, by + bh) / 2 + 26 + (i % 3) * 14
            pts = [(ax + aw / 2, ay + ah), (ax + aw / 2, cy),
                   (bx + bw / 2, cy), (bx + bw / 2, by + bh)]
        else:  # skip edge — corridor above or below
            corr = min(ay, by) - 30 - (i % 2) * 16
            sx, sy = ax + aw, ay + ah / 2
            ex, ey = bx, by + bh / 2
            pts = [(sx, sy), (sx + 18, sy), (sx + 18, corr),
                   (ex - 18, corr), (ex - 18, ey), (ex, ey)]
        d = rounded_path(pts, 8)
        canvas.path(d, stroke, sw=sw, dash=dash, marker=marker,
                    extra=' class="rd-edge" data-rd-edge="1" data-edge-from="%s" data-edge-to="%s"'
                    % (a, b))
        canvas.edge_count += 1
        label = e.get("label")
        if label:
            canvas.labeled_edges += 1
            pending_labels.append((pts, str(label), i, a, b))

    for pts, label, li, ea, eb in pending_labels:
        edge_label(canvas, pts, label, li, ea, eb)

    # nodes painted last
    steps = spec.get("meta", {}).get("reading_path") or []
    step_index = {nid: i + 1 for i, nid in enumerate(steps)}
    for seq_i, nid in enumerate(ids):
        x, y, w, h = pos[nid]
        n = by_id[nid]
        canvas.node(x, y, w, h, n.get("label", nid), n.get("kind", "backend"),
                    n.get("sublabel"), step=step_index.get(nid), node_id=nid,
                    index=seq_i)

    w = x - gap_x
    return canvas.scene.markup(), w, max_layer_h, {}


def render_sequence(canvas, spec):
    actors = spec.get("actors", [])
    messages = spec.get("messages", [])
    events = []
    if not actors:
        return "", 0, 0, {}
    sizes = []
    for a in actors:
        w = max(112, text_w(a.get("label", a["id"]), canvas.ramp["name"]) + 40)
        sizes.append(math.ceil(w / 4) * 4)
    gap = 56
    xs, x = [], 0.0
    for w in sizes:
        xs.append(x + w / 2)
        x += w + gap
    total_w = x - gap
    box_h = canvas.ramp["box_min_h"]
    top = 0.0
    row = 44
    bottom = top + box_h + 40 + max(0, len(messages) - 1) * row + 40

    for i, a in enumerate(actors):
        canvas.node(xs[i] - sizes[i] / 2, top, sizes[i], box_h,
                    a.get("label", a["id"]), a.get("kind", "backend"),
                    node_id=a.get("id"), index=i)
        canvas.line(xs[i], top + box_h, xs[i], bottom, rgba(canvas.t["ink"], 0.18), sw=1)
    if messages:
        canvas.line(xs[0] - sizes[0] / 2, top + box_h + 20,
                    xs[0] - sizes[0] / 2, top + box_h + 20,
                    rgba(canvas.t["ink"], 0.18), sw=1)
    for i, m in enumerate(messages):
        y = top + box_h + 36 + i * row
        a, b = m["from"], m["to"]
        if a not in [x["id"] for x in actors] or b not in [x["id"] for x in actors]:
            continue
        ia = [x["id"] for x in actors].index(a)
        ib = [x["id"] for x in actors].index(b)
        x1, x2 = xs[ia], xs[ib]
        variant = m.get("variant", "default")
        stroke = {"accent": canvas.t["accent"], "link": canvas.t["link"]}.get(
            variant, canvas.t["muted"])
        marker = {"accent": "arrow-accent", "link": "arrow-link"}.get(variant, "arrow")
        dash = "5,4" if variant in ("dashed", "return") else ""
        if abs(x1 - x2) < 2:
            # self message — small loop
            d = rounded_path([(x1, y), (x1 + 34, y), (x1 + 34, y + 20),
                              (x1 + 4, y + 20)], 6)
            canvas.path(d, stroke, dash=dash, marker=marker, extra=' data-rd-edge="1"')
            canvas.text(x1 + 40, y + 4, str(m.get("label", "")), 10, "arrow",
                        canvas.t["soft"], anchor="start")
            canvas.labeled_edges += 1
        else:
            canvas.line(x1, y, x2, y, stroke, sw=1.2, dash=dash, marker=marker,
                        extra=' class="rd-edge" data-rd-edge="1" data-edge-from="%s" data-edge-to="%s"'
                        % (a, b))
            canvas.edge_count += 1
            label = str(m.get("label", ""))
            if label:
                canvas.labeled_edges += 1
                lab_size = 9 if not has_cjk(label) else 11
                lw = text_w(label, lab_size, mono=not has_cjk(label)) + 8
                mx, my = (x1 + x2) / 2, y
                st = len(canvas.scene.parts)
                canvas.rect(mx - lw / 2, my - 21, lw, 14, canvas.t["paper"], rx=2)
                canvas.text(mx, my - 9, label, lab_size, "arrow",
                            canvas.t["soft"], spacing="0.04em")
                canvas.wrap(st, '<g class="rd-edge-label" data-edge-from="%s" data-edge-to="%s">'
                            % (a, b))
    h = bottom - top
    return canvas.scene.markup(), total_w, h, {}


def _parse_time(s):
    if not s:
        return None
    s = str(s).strip().replace("Z", "+00:00")
    try:
        return _dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def render_timeline(canvas, spec):
    events = spec.get("events", [])
    lanes = spec.get("lanes", [])
    times = [_parse_time(e.get("time")) for e in events]
    use_time = all(t is not None for t in times) and len(times) > 0
    x0, x1 = 120.0, 720.0
    lane_of = {}
    for i, e in enumerate(events):
        lane_of.setdefault(e.get("lane", "main"), []).append(i)
    lane_ids = [l["id"] for l in lanes] or list(lane_of.keys())
    lane_label = {l["id"]: l.get("label", l["id"]) for l in lanes}
    row_h = 86
    canvas.line(x0, 34, x0, 34, canvas.t["rule"], sw=1)
    for li, lid in enumerate(lane_ids):
        y = 60 + li * row_h
        canvas.text(0, y + 4, lane_label.get(lid, lid), 9, "eyebrow",
                    canvas.t["soft"], anchor="start", spacing="0.12em")
        canvas.line(x0, y, x1, y, rgba(canvas.t["ink"], 0.16), sw=0.8,
                    marker="arrow")
    if use_time:
        tmin, tmax = min(times), max(times)
        span = (tmax - tmin).total_seconds() or 1
    for i, e in enumerate(events):
        lid = e.get("lane", "main")
        li = lane_ids.index(lid) if lid in lane_ids else 0
        y = 60 + li * row_h
        if use_time:
            frac = ((times[i] - tmin).total_seconds()) / span if span else 0.5
            px = x0 + 40 + frac * (x1 - x0 - 80)
        else:
            idxs = lane_of.get(lid, [i])
            k = idxs.index(i) if i in idxs else 0
            px = x0 + 40 + (k + 0.5) * ((x1 - x0 - 80) / max(1, len(idxs)))
        kind = e.get("kind", "default")
        fill = {"alert": canvas.t["accent"], "recovery": canvas.t["link"]}.get(
            kind, canvas.t["ink"])
        if kind in ("alert", "change", "action", "recovery") and kind != "recovery":
            if kind == "alert":
                canvas.accent_count += 1
        canvas.circle(px, y, 5, fill, stroke=canvas.t["paper"], sw=2)
        canvas.line(px, y - 5, px, y - 20, rgba(canvas.t["ink"], 0.25), sw=0.8)
        label = str(e.get("label", ""))
        above = li % 2 == 0
        ly = y - 26 if above else y + 32
        canvas.text(px, ly, label, 11 if has_cjk(label) else 9, "name",
                    canvas.t["ink"], weight="600", family=FONT_SANS)
        if e.get("desc"):
            canvas.text(px, ly + 14, str(e.get("desc")), 9,
                        "sublabel", canvas.t["soft"], family=FONT_SANS)
        if use_time:
            canvas.text(px, y + 14, times[i].strftime("%m-%d %H:%M"), 8, "eyebrow",
                        canvas.t["soft"], spacing="0.04em")
    return canvas.scene.markup(), x1 - 0, 60 + len(lane_ids) * row_h, {}


def render_tree(canvas, spec):
    nodes = spec.get("nodes", [])
    children = {}
    roots = []
    for n in nodes:
        p = n.get("parent")
        if p:
            children.setdefault(p, []).append(n["id"])
        else:
            roots.append(n["id"])
    by_id = {n["id"]: n for n in nodes}
    sizes = {n["id"]: _node_size(canvas, n, max_w=180) for n in nodes}
    gap_x = 24
    gap_y = 64
    x_cursor = [0.0]
    pos = {}
    order = []

    def place(nid, depth):
        kids = children.get(nid, [])
        if not kids:
            w = sizes[nid][0]
            cx = x_cursor[0] + w / 2
            x_cursor[0] += w + gap_x
        else:
            for k in kids:
                place(k, depth + 1)
            first = pos[kids[0]][0] + sizes[kids[0]][0] / 2
            last = pos[kids[-1]][0] + sizes[kids[-1]][0] / 2
            cx = (first + last) / 2
            w = sizes[nid][0]
            if cx - w / 2 < 0:
                dx = -(cx - w / 2)
                for k in kids:
                    pos[k] = (pos[k][0] + dx,) + pos[k][1:]
                cx += dx
        w, h = sizes[nid]
        pos[nid] = (cx - w / 2, depth * (max(s[1] for s in sizes.values()) + gap_y), w, h)
        order.append(nid)

    for r in roots:
        place(r, 0)

    for nid in order:
        n = by_id[nid]
        p = n.get("parent")
        if p and p in pos:
            px, py, pw, ph = pos[p]
            cx, cy, cw, ch = pos[nid]
            pts = [(px + pw / 2, py + ph), (px + pw / 2, py + ph + gap_y / 2),
                   (cx + cw / 2, py + ph + gap_y / 2), (cx + cw / 2, cy)]
            canvas.path(rounded_path(pts, 8), rgba(canvas.t["muted"], 0.8), sw=1.1,
                        extra=' class="rd-edge" data-rd-edge="1" data-edge-from="%s" data-edge-to="%s"'
                        % (p, nid))
            canvas.edge_count += 1
    steps = spec.get("meta", {}).get("reading_path") or []
    step_index = {nid: i + 1 for i, nid in enumerate(steps)}
    for seq_i, nid in enumerate(order):
        x, y, w, h = pos[nid]
        n = by_id[nid]
        canvas.node(x, y, w, h, n.get("label", nid), n.get("kind", "backend"),
                    n.get("sublabel"), step=step_index.get(nid), node_id=nid,
                    index=seq_i)
    return canvas.scene.markup(), x_cursor[0], (max(p[1] + p[3] for p in pos.values())
        if pos else 0), {}


def render_layers(canvas, spec):
    items = spec.get("items", [])
    if not items:
        return "", 0, 0, {}
    width = max(460, max(text_w(i.get("label", ""), canvas.ramp["name"]) +
                         text_w(i.get("detail", ""), canvas.ramp["sub"]) + 140
                         for i in items))
    width = math.ceil(width / 4) * 4
    band_h = 76
    for i, it in enumerate(items):
        st = len(canvas.scene.parts)
        y = i * (band_h + 12)
        focal = it.get("focus")
        fill = canvas.t["accent-tint"] if focal else (
            canvas.t["white"] if canvas.t["paper"] == "#f5f5f5" else rgba(canvas.t["ink"], 0.10))
        stroke = canvas.t["accent"] if focal else canvas.t["ink"]
        if focal:
            canvas.accent_count += 1
        canvas.rect(0, y, width, band_h, fill, stroke, sw=1, rx=8)
        canvas.text(24, y + band_h / 2 + 4, str(it.get("label", "")),
                    canvas.ramp["name"], "name", canvas.t["ink"], anchor="start",
                    weight="600", family=FONT_SANS)
        if it.get("detail"):
            canvas.text(width - 24, y + band_h / 2 + 4, str(it.get("detail")),
                        canvas.ramp["sub"], "sublabel", canvas.t["muted"], anchor="end",
                        family=FONT_SANS)
        canvas.wrap(st, '<g class="rd-node" data-node-id="layer-%d" style="--i:%d">' % (i, i))
    return canvas.scene.markup(), width, len(items) * (band_h + 12), {}


def render_bar(canvas, spec):
    data = spec.get("data", [])
    if not data:
        return "", 0, 0, {}
    unit = spec.get("meta", {}).get("unit", "")
    label_w = max(text_w(d.get("label", ""), canvas.ramp["name"]) for d in data) + 32
    bar_max = 420.0
    max_v = max(abs(float(d.get("value", 0))) for d in data) or 1
    row_h = 44
    height = len(data) * row_h + 20
    val_w = 80
    canvas.line(label_w, 0, label_w, height, rgba(canvas.t["ink"], 0.20), sw=0.8)
    for i, d in enumerate(data):
        st = len(canvas.scene.parts)
        y = i * row_h + 16
        v = float(d.get("value", 0))
        w = abs(v) / max_v * bar_max
        focal = bool(d.get("focus"))
        if focal:
            canvas.accent_count += 1
        fill = canvas.t["accent"] if focal else rgba(canvas.t["ink"], 0.72)
        canvas.text(label_w - 12, y + 14, str(d.get("label", "")),
                    canvas.ramp["name"], "name", canvas.t["ink"], anchor="end",
                    weight="600", family=FONT_SANS)
        canvas.rect(label_w + 12, y, w, 18, fill, rx=2)
        canvas.text(label_w + 20 + w, y + 13,
                    ("%s%s" % (fmt(v), (" " + unit) if unit else "")),
                    10, "sublabel", canvas.t["ink"], anchor="start", family=FONT_SANS)
        canvas.wrap(st, '<g class="rd-node" data-node-id="bar-%d" style="--i:%d">' % (i, i))
    canvas.edge_count = 0
    return canvas.scene.markup(), label_w + bar_max + val_w + 20, height, {}


def render_quadrant(canvas, spec):
    axes = spec.get("axes", {})
    points = spec.get("points", [])
    size = 440.0
    pad = 60
    x0, y0 = pad, 0.0
    canvas.rect(x0, y0, size, size, rgba(canvas.t["ink"], 0.02),
                rgba(canvas.t["ink"], 0.12), sw=0.8, rx=8)
    canvas.line(x0 + size / 2, y0, x0 + size / 2, y0 + size,
                rgba(canvas.t["ink"], 0.22), sw=1, dash="4,4")
    canvas.line(x0, y0 + size / 2, x0 + size, y0 + size / 2,
                rgba(canvas.t["ink"], 0.22), sw=1, dash="4,4")
    canvas.text(x0 + size / 2, y0 + size + 26, str(axes.get("x", {}).get("label", "x")),
                canvas.ramp["sub"], "eyebrow", canvas.t["muted"], spacing="0.1em")
    canvas.text(x0 - 40, y0 + size / 2 + 4, str(axes.get("y", {}).get("label", "y")),
                canvas.ramp["sub"], "eyebrow", canvas.t["muted"], spacing="0.1em")
    for p in spec.get("quadrants", []) or []:
        m = p.get("at", "tl")
        left, top = "l" in m, "t" in m
        px = x0 + (22 if left else size - 22)
        py = y0 + (30 if top else size - 20)
        canvas.text(px, py, str(p.get("label", "")), 10, "eyebrow",
                    rgba(canvas.t["soft"], 0.9),
                    anchor="start" if left else "end", spacing="0.12em")
    for pi, pt in enumerate(points):
        st = len(canvas.scene.parts)
        px = x0 + float(pt.get("x", 0.5)) * size
        py = y0 + (1 - float(pt.get("y", 0.5))) * size
        focal = bool(pt.get("focus"))
        if focal:
            canvas.accent_count += 1
        canvas.circle(px, py, 5.5, canvas.t["accent"] if focal else canvas.t["ink"],
                      stroke=canvas.t["paper"], sw=2)
        label = str(pt.get("label", ""))
        canvas.text(px + 12, py + 4, label, 11 if has_cjk(label) else 9, "name",
                    canvas.t["ink"], anchor="start", weight="600", family=FONT_SANS)
        canvas.wrap(st, '<g class="rd-node" data-node-id="pt-%d" style="--i:%d">' % (pi, pi))
    return canvas.scene.markup(), size + pad + 260, size + 46, {}


RENDERERS = {
    "architecture": lambda c, s: render_graph(c, s),
    "flow": lambda c, s: render_graph(c, s, "flow"),
    "state": lambda c, s: render_graph(c, s, "state"),
    "sequence": render_sequence,
    "timeline": render_timeline,
    "tree": render_tree,
    "layers": render_layers,
    "bar": render_bar,
    "quadrant": render_quadrant,
}


# --------------------------------------------------------------------------- #
# Page chrome
# --------------------------------------------------------------------------- #

CSS = """
:root{
  --paper:%(paper)s; --paper-2:%(paper2)s; --ink:%(ink)s; --muted:%(muted)s;
  --soft:%(soft)s; --rule:%(rule)s; --accent:%(accent)s; --accent-tint:%(accent_tint)s;
  --link:%(link)s; --doc-w:%(docw)dpx;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%%}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:%(sans)s;font-size:16px;line-height:1.6;
  -webkit-font-smoothing:antialiased}
.rd-doc{max-width:var(--doc-w,1080px);margin:0 auto;padding:64px 40px 80px}
.rd-eyebrow{font-family:%(mono)s;font-size:11px;font-weight:500;letter-spacing:.18em;
  text-transform:uppercase;color:var(--muted)}
.rd-title{font-family:%(serif)s;font-weight:400;font-size:clamp(26px,3.4vw,42px);
  line-height:1.16;letter-spacing:-.005em;margin:12px 0 0;max-width:20em;
  text-wrap:balance}
.rd-takeaway{margin:16px 0 0;max-width:66ch;font-size:17px;line-height:1.65;color:var(--muted)}
.rd-takeaway strong{color:var(--ink);font-weight:600}
.rd-figure{margin:36px 0 0}
.rd-canvas{width:100%%;overflow-x:auto;padding-bottom:4px}
.rd-canvas svg{width:100%%;min-width:%(vbw)dpx;height:auto;display:block}
.rd-caption{margin:14px 0 0;font-size:13px;line-height:1.6;color:var(--soft);max-width:70ch}
.rd-steps{list-style:none;margin:28px 0 0;padding:0;display:grid;gap:10px;
  border-top:1px solid var(--rule);padding-top:20px}
.rd-steps li{display:grid;grid-template-columns:26px 1fr;gap:12px;align-items:start}
.rd-steps .n{display:flex;align-items:center;justify-content:center;
  width:22px;height:22px;border-radius:50%%;background:var(--accent);color:#fff;
  font-size:11px;font-weight:600;margin-top:2px}
.rd-steps .t{font-weight:600;font-size:14px}
.rd-steps .d{display:block;color:var(--muted);font-size:13px;font-weight:400;margin-top:1px}
.rd-legend{display:flex;flex-wrap:wrap;gap:10px 22px;margin:26px 0 0;
  padding-top:16px;border-top:1px solid var(--rule);font-size:12px;color:var(--muted)}
.rd-legend li{display:inline-flex;align-items:center;gap:7px;list-style:none}
.rd-legend ul{display:contents}
.rd-swatch{width:14px;height:10px;border-radius:2px;display:inline-block}
.rd-footer{margin:34px 0 0;padding-top:14px;border-top:1px solid var(--rule);
  display:flex;flex-wrap:wrap;gap:8px 18px;font-family:%(mono)s;font-size:11px;
  color:var(--soft);letter-spacing:.04em}
.rd-footer .dot{opacity:.5}
@media print{
  body{background:#fff}
  .rd-doc{padding:24px 0}
  .rd-canvas{overflow-x:visible}
  .rd-canvas svg{min-width:0}
}
@media (max-width:640px){
  .rd-doc{padding:40px 20px 56px}
  .rd-title{font-size:26px}
}
"""


def interaction_css(theme, node_ids, steps):
    """Hover + entrance motion, pure CSS (no script, self_check-safe)."""
    a = theme["accent"]
    out = ['''
.rd-canvas svg .rd-node,.rd-canvas svg .rd-edge,.rd-canvas svg .rd-edge-label{
  transition:opacity .18s ease,stroke .18s ease,stroke-width .18s ease}
.rd-canvas svg .rd-edge-label{stroke:none}
.rd-canvas svg .rd-node{cursor:default;
  animation:rd-rise .52s cubic-bezier(.2,.7,.3,1) backwards;
  animation-delay:calc(var(--i,0)*55ms)}
.rd-canvas svg .rd-edge,.rd-canvas svg .rd-edge-label{
  animation:rd-fade .6s ease backwards;animation-delay:.25s}
@keyframes rd-rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@keyframes rd-fade{from{opacity:0}to{opacity:1}}
.rd-canvas svg .rd-node:hover>.rd-shape{stroke:%s;stroke-width:1.9}
.rd-canvas svg:has(.rd-node:hover) .rd-node:not(:hover){opacity:.32}
.rd-canvas svg:has(.rd-node:hover) .rd-edge{opacity:.14}
.rd-canvas svg:has(.rd-node:hover) .rd-edge-label{opacity:.16}
.rd-canvas svg:has(.rd-edge:hover) .rd-node{opacity:.55}
.rd-canvas svg:has(.rd-edge:hover) .rd-edge:not(:hover){opacity:.28}
.rd-canvas svg:has(.rd-edge:hover) .rd-edge-label:not(:hover){opacity:.3}
.rd-canvas svg .rd-edge:hover{stroke-width:2.1}
.rd-steps li{transition:background .15s ease;border-radius:6px}
.rd-steps li:hover{background:var(--accent-tint)}
.rd-steps .n{transition:transform .15s ease}
.rd-steps li:hover .n{transform:scale(1.12)}
@media (prefers-reduced-motion:reduce){
  .rd-canvas svg *,.rd-steps *{animation:none!important;transition:none!important}}
@media print{
  .rd-canvas svg .rd-node,.rd-canvas svg .rd-edge,.rd-canvas svg .rd-edge-label{
    animation:none!important;opacity:1!important}}
''' % a]
    for nid in node_ids:
        out.append('''
.rd-canvas svg:has([data-node-id="%(n)s"]:hover) .rd-edge[data-edge-from="%(n)s"],
.rd-canvas svg:has([data-node-id="%(n)s"]:hover) .rd-edge[data-edge-to="%(n)s"]{
  opacity:1!important;stroke:%(a)s!important;stroke-width:1.8!important}
.rd-canvas svg:has([data-node-id="%(n)s"]:hover) .rd-edge-label[data-edge-from="%(n)s"],
.rd-canvas svg:has([data-node-id="%(n)s"]:hover) .rd-edge-label[data-edge-to="%(n)s"]{
  opacity:1!important}
''' % {"n": nid, "a": a})
    for st in steps:
        nid = st.get("node")
        if not nid:
            continue
        out.append('''
body:has(.rd-steps li[data-step-for="%(n)s"]:hover) [data-node-id="%(n)s"]>.rd-shape{
  stroke:%(a)s!important;stroke-width:2!important}
body:has(.rd-steps li[data-step-for="%(n)s"]:hover) [data-node-id="%(n)s"]{opacity:1!important}
''' % {"n": nid, "a": a})
    return "".join(out)


def build_html(spec, canvas, markup, vbw, vbh):
    meta = spec.get("meta", {})
    theme_name = meta.get("theme", "light")
    ramp_name = PRESETS.get(meta.get("size", "doc-inline"), PRESETS["doc-inline"])["ramp"]
    lang_code = "zh" if has_cjk(str(meta.get("title", ""))) else "en"
    html_lang = "zh-CN" if lang_code == "zh" else "en"
    theme = THEMES[theme_name]
    legend = meta.get("legend") or auto_legend(spec, lang_code, theme)
    steps = reading_steps(spec)
    slug = meta.get("slug") or "diagram"
    title = str(meta.get("title", ""))
    takeaway = str(meta.get("takeaway", ""))
    caption = str(meta.get("caption", ""))
    source = meta.get("source")
    eyebrow = str(meta.get("eyebrow", spec.get("type", "diagram")))
    css = CSS % dict(
        paper=theme["paper"], paper2=theme["paper-2"], ink=theme["ink"],
        muted=theme["muted"], soft=theme["soft"], rule=theme["rule"],
        accent=theme["accent"], accent_tint=theme["accent-tint"], link=theme["link"],
        sans=FONT_SANS, mono=FONT_MONO, serif=FONT_TITLE, vbw=int(math.ceil(vbw)),
        docw=int(math.ceil(max(1080, vbw + 120))),
    ) + interaction_css(theme, canvas.node_ids, steps)
    font_link = (
        '<link href="https://fonts.googleapis.com/css2?'
        'family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600&'
        'family=Geist+Mono:wght@400;500&family=Noto+Serif+SC:wght@400&'
        'family=Noto+Sans+SC:wght@400;500;600&display=swap" rel="stylesheet">')
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
        'role="img" aria-labelledby="%s-title %s-desc" data-rd-type="%s">'
        '<title id="%s-title">%s</title>'
        '<desc id="%s-desc">%s</desc>'
        '<defs>'
        '<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
        '<polygon points="0 0, 8 3, 0 6" fill="%s"/></marker>'
        '<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
        '<polygon points="0 0, 8 3, 0 6" fill="%s"/></marker>'
        '<marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
        '<polygon points="0 0, 8 3, 0 6" fill="%s"/></marker>'
        '</defs>'
        '<rect width="%d" height="%d" fill="%s"/>'
        '%s</svg>'
    ) % (vbw, vbh, slug, slug, spec.get("type", "diagram"), slug, esc(title),
         slug, esc(meta.get("alt") or desc_sentence(spec, lang_code)),
         theme["muted"], theme["accent"], theme["link"], vbw, vbh, theme["paper"], markup)

    steps_html = ""
    if steps:
        items = "".join(
            '<li%s><span class="n">%d</span><span><span class="t">%s</span>'
            '<span class="d">%s</span></span></li>'
            % (' data-step-for="%s"' % s["node"] if s.get("node") else "",
               i + 1, esc(s["title"]), esc(s.get("detail", "")))
            for i, s in enumerate(steps))
        steps_html = ('<ol class="rd-steps" data-rd-steps="%d">%s</ol>'
                      % (len(steps), items))
    legend_html = ""
    if legend:
        lis = "".join(
            '<li><span class="rd-swatch" style="background:%s"></span>%s</li>'
            % (lg["fill"], esc(lg["label"])) for lg in legend)
        legend_html = '<ul class="rd-legend" data-rd-legend="1">%s</ul>' % lis
    footer_bits = ['<span>%s</span>' % esc(spec.get("type", "")).upper(),
                   '<span class="dot">·</span>',
                   '<span>%s</span>' % esc(meta.get("size", "doc-inline")),
                   '<span class="dot">·</span>',
                   '<span>%s</span>' % esc(meta.get("audience", "mixed"))]
    if source:
        footer_bits += ['<span class="dot">·</span>', '<span>%s</span>' % esc(source)]
    footer = '<footer class="rd-footer">%s</footer>' % "".join(footer_bits)

    return """<!DOCTYPE html>
<html lang="%s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
%s
<style>%s</style>
</head>
<body class="rd-%s">
<main class="rd-doc" data-rd-doc="1">
  <div class="rd-eyebrow">%s</div>
  <h1 class="rd-title">%s</h1>
  <p class="rd-takeaway">%s</p>
  <figure class="rd-figure">
    <div class="rd-canvas">%s</div>
    <figcaption class="rd-caption">%s</figcaption>
  </figure>
  %s
  %s
  %s
</main>
</body>
</html>
""" % (html_lang, esc(title), font_link, css, theme_name, esc(eyebrow), esc(title),
       takeaway, svg, esc(caption), steps_html, legend_html, footer)


def desc_sentence(spec, lang_code):
    meta = spec.get("meta", {})
    take = str(meta.get("takeaway", "")).strip()
    if take:
        return take
    return "%s diagram: %s" % (spec.get("type", "diagram"), meta.get("title", ""))


def auto_legend(spec, lang, theme=None):
    kinds = []
    for n in spec.get("nodes", []) + spec.get("actors", []):
        k = n.get("kind", "backend")
        if k not in kinds and k != "backend":
            kinds.append(k)
    (kinds.insert(0, "backend") if "backend" in
     [n.get("kind", "backend") for n in spec.get("nodes", []) + spec.get("actors", [])]
     else None)
    labels = KIND_LABELS.get(lang, KIND_LABELS["en"])
    t = theme or THEMES["light"]
    out = []
    for k in kinds[:5]:
        fill = {"focal": t["accent"], "store": rgba(t["ink"], 0.55),
                "external": rgba(t["ink"], 0.35), "input": rgba(t["ink"], 0.25),
                "optional": rgba(t["ink"], 0.15), "security": rgba(t["accent"], 0.5),
                "decision": t["ink"], "backend": t["ink"]}.get(k, t["ink"])
        out.append({"label": labels.get(k, k), "fill": fill})
    variants = []
    for e in spec.get("edges", []) + spec.get("messages", []):
        v = e.get("variant", "default")
        if v not in ("default",) and v not in variants:
            variants.append(v)
    vlabels = VARIANT_LABELS.get(lang, VARIANT_LABELS["en"])
    for v in variants[:3]:
        out.append({"label": vlabels.get(v, v),
                    "fill": {"accent": t["accent"], "link": t["link"]}.get(v, t["muted"])})
    return out


def reading_steps(spec):
    meta = spec.get("meta", {})
    explicit = meta.get("steps")
    if explicit:
        path = meta.get("reading_path") or []
        out = []
        for i, st in enumerate(explicit):
            item = dict(st)
            if "node" not in item and i < len(path):
                item["node"] = path[i]
            out.append(item)
        return out
    path = meta.get("reading_path") or []
    by_id = {n["id"]: n for n in spec.get("nodes", []) + spec.get("actors", [])}
    out = []
    for i, nid in enumerate(path):
        n = by_id.get(nid, {"label": nid})
        out.append({"title": str(n.get("label", nid)),
                    "detail": str(n.get("note", "")),
                    "node": nid})
    return out


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #

REQUIRED_DATA = {
    "architecture": "nodes", "flow": "nodes", "state": "nodes",
    "sequence": "actors", "timeline": "events", "tree": "nodes",
    "layers": "items", "bar": "data", "quadrant": "points",
}


def validate_spec(spec):
    """Fail with a readable message instead of a traceback."""
    if not isinstance(spec, dict):
        raise SystemExit("spec must be a JSON object")
    meta = spec.get("meta")
    if not isinstance(meta, dict):
        raise SystemExit("spec.meta is missing: title/takeaway/caption belong there")
    for key in ("title", "takeaway", "caption"):
        if not str(meta.get(key, "")).strip():
            raise SystemExit("spec.meta.%s is required — it is part of the reading contract" % key)
    rtype = spec.get("type")
    if rtype not in RENDERERS:
        raise SystemExit("unknown type %r; choose from %s" % (rtype, ", ".join(RENDERERS)))
    key = REQUIRED_DATA[rtype]
    rows = spec.get(key)
    if not isinstance(rows, list) or not rows:
        raise SystemExit("spec.%s must be a non-empty list for type %r" % (key, rtype))
    if rtype in ("architecture", "flow", "state", "tree"):
        ids = [n.get("id") for n in rows]
        if any(not i for i in ids):
            raise SystemExit("every node needs an id")
        if len(set(ids)) != len(ids):
            raise SystemExit("node ids must be unique")
        for e in spec.get("edges", []):
            for end in ("from", "to"):
                if e.get(end) not in ids:
                    raise SystemExit("edge %s=%r is not a node id" % (end, e.get(end)))


def render_spec(spec, out_path=None):
    validate_spec(spec)
    meta = spec.get("meta", {})
    theme_name = meta.get("theme", "light")
    preset = PRESETS.get(meta.get("size", "doc-inline"), PRESETS["doc-inline"])
    ramp = RAMP[preset["ramp"]]
    lang = "zh" if has_cjk(str(meta.get("title", ""))) else "en"
    rtype = spec.get("type", "architecture")
    if rtype not in RENDERERS:
        raise SystemExit("unknown type %r; choose from %s" % (rtype, ", ".join(RENDERERS)))
    canvas = Canvas(THEMES[theme_name], ramp, lang)
    markup, cw, ch, _ = RENDERERS[rtype](canvas, spec)

    # the painted bounding box is the source of truth for framing
    if canvas.scene.empty:
        bx0 = by0 = 0.0
        inner_w = inner_h = 1.0
    else:
        bx0, by0, bx1, by1 = canvas.scene.box()
        inner_w, inner_h = max(bx1 - bx0, 1.0), max(by1 - by0, 1.0)
    margin = preset["margin"] if preset["w"] else 40
    if preset["w"] is None:  # "fit": the page follows the content
        vbw = int(math.ceil((inner_w + margin * 2) / 4.0) * 4)
        vbh = int(math.ceil((inner_h + margin * 2) / 4.0) * 4)
        vbw = max(vbw, 720)
    else:
        vbw = max(preset["w"], int(math.ceil((inner_w + margin * 2) / 4.0) * 4))
        vbh = max(int(preset["h"] * 0.7), int(math.ceil((inner_h + margin * 2) / 4.0) * 4))
    tx = (vbw - inner_w) / 2 - bx0
    ty = (vbh - inner_h) / 2 - by0
    wrapped = '<g transform="translate(%.1f,%.1f)">%s</g>' % (tx, ty, markup)
    html = build_html(spec, canvas, wrapped, vbw, vbh)
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(html, encoding="utf-8")
    return {
        "html": html,
        "viewBox": [vbw, vbh],
        "nodes": canvas.node_count,
        "edges": canvas.edge_count,
        "labeled_edges": canvas.labeled_edges,
        "accent": canvas.accent_count,
        "type": rtype,
        "size": meta.get("size", "doc-inline"),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="render.py",
        description="Render a readable-diagrams JSON spec to a single HTML page.")
    ap.add_argument("spec", nargs="?", help="path to spec .json")
    ap.add_argument("-o", "--out", help="output .html (default: spec.html)")
    ap.add_argument("--theme", choices=["light", "dark"], help="override meta.theme")
    ap.add_argument("--size", choices=list(PRESETS), help="override meta.size")
    ap.add_argument("--json", action="store_true", help="print a machine summary")
    ap.add_argument("--list-types", action="store_true", help="print the engine types and exit")
    ap.add_argument("--version", action="version", version="readable-diagrams %s" % __version__)
    args = ap.parse_args(argv)
    if args.list_types:
        for t in RENDERERS:
            print(t)
        return 0
    if not args.spec:
        ap.error("a spec file is required")
    try:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit("%s: invalid JSON at line %d column %d: %s"
                         % (args.spec, exc.lineno, exc.colno, exc.msg))
    except OSError as exc:
        raise SystemExit("cannot read %s: %s" % (args.spec, exc))
    meta = spec.setdefault("meta", {})
    if args.theme:
        meta["theme"] = args.theme
    if args.size:
        meta["size"] = args.size
    out = args.out or str(Path(args.spec).with_suffix(".html"))
    info = render_spec(spec, out)
    info.pop("html", None)
    info["output"] = out
    print(json.dumps(info, ensure_ascii=False) if args.json else
          "wrote %s (%d nodes, %d edges, %d accent)" %
          (out, info["nodes"], info["edges"], info["accent"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
