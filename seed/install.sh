#!/usr/bin/env bash
set -euo pipefail

SEED_DIR="$(cd "$(dirname "$0")/claude" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"

if [ ! -d "$SEED_DIR" ]; then
  echo "error: seed payload not found at $SEED_DIR" >&2
  exit 1
fi

backup_dir=""
if [ -d "$CLAUDE_DIR" ]; then
  backup_dir="$CLAUDE_DIR.backup.$(date +%Y%m%d-%H%M%S)"
  cp -pR "$CLAUDE_DIR" "$backup_dir"
fi

mkdir -p "$CLAUDE_DIR"

count=0
while IFS= read -r -d '' f; do
  rel="${f#"$SEED_DIR"/}"
  dest="$CLAUDE_DIR/$rel"
  mkdir -p "$(dirname "$dest")"
  cp -p "$f" "$dest"
  count=$((count + 1))
done < <(find "$SEED_DIR" -type f -print0)

# Substitute the placeholder token in the installed settings.json
if [ -f "$CLAUDE_DIR/settings.json" ]; then
  tmp="$(mktemp)"
  sed "s|__CLAUDE_DIR__|$CLAUDE_DIR|g" "$CLAUDE_DIR/settings.json" > "$tmp"
  mv "$tmp" "$CLAUDE_DIR/settings.json"
fi

# Ensure executables (belt-and-suspenders; cp -p already preserves mode)
chmod +x "$CLAUDE_DIR"/hooks/*.mjs 2>/dev/null || true
chmod +x "$CLAUDE_DIR/statusline-command.sh" 2>/dev/null || true

echo "Seed installed into: $CLAUDE_DIR"
echo "Files installed:      $count"
if [ -n "$backup_dir" ]; then
  echo "Previous config backed up to: $backup_dir"
fi
echo "Review hooks in $CLAUDE_DIR/hooks/ before your next session."
