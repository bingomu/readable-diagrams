#!/usr/bin/env bash
# Install the readable-diagrams skill into the shared agent-skills directory
# (~/.agents/skills by default; override with SKILLS_DIR).
#
#   bash install.sh
#
# This is the generic path — Claude Code, Codex, Cursor and DSH all read
# SKILL.md folders from a skills directory. For DeepSeek Harness you can also
# install the repo as a plugin (see README).
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST_ROOT="${SKILLS_DIR:-$HOME/.agents/skills}"
DEST="$DEST_ROOT/readable-diagrams"

mkdir -p "$DEST_ROOT"
if [ -e "$DEST" ]; then
  echo "already installed at $DEST"
  echo "replacing (old copy kept at $DEST.bak)"
  rm -rf "$DEST.bak"
  mv "$DEST" "$DEST.bak"
fi
cp -R "$SRC/skills/readable-diagrams" "$DEST"
rm -rf "$DEST/scripts/__pycache__" "$DEST/examples/__pycache__"

echo "installed -> $DEST"
echo
echo "verify:"
python3 "$DEST/scripts/self_check.py" "$DEST/examples/architecture.html"
python3 "$DEST/scripts/comprehension_check.py" "$DEST/examples/architecture.html"
