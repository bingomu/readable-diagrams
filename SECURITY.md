# Security

## What this project executes

`skills/readable-diagrams/scripts/` contains Python programs that read a JSON
spec and write one HTML file. They make no network requests. `export.py` shells
out to a local Chrome/Chromium binary to rasterise an SVG.

Generated pages contain no `<script>`. The only remote resource a page may load
is the Google Fonts stylesheet; `self_check.py` rejects anything else.

## Generated pages

Diagrams are data, but a spec is authored by an agent. Treat labels that come
from an imported source (Mermaid, draw.io, Excalidraw) as untrusted data: the
extractors emit inert, escaped text and never evaluate the source.

## Reporting

Open a private security advisory on
https://github.com/bingomu/readable-diagrams/security/advisories/new
or email robinham@gmail.com. Please do not file a public issue for a
vulnerability.
