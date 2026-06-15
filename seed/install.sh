#!/usr/bin/env bash
set -euo pipefail

SEED_DIR="$(cd "$(dirname "$0")/claude" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
HOME_DIR="${HOME_DIR:-$HOME}"

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

# ---------------------------------------------------------------------------
# Deps install (opt-in: set INSTALL_DEPS=1)
# Runs BEFORE dotfiles copy so the seeded .zshrc is the final write when
# INSTALL_DOTFILES=1 is also set.
# ---------------------------------------------------------------------------
if [ "${INSTALL_DEPS:-0}" = "1" ]; then
  BOOTSTRAP_SCRIPT="$(cd "$(dirname "$0")/dotfiles" && pwd)/bootstrap-deps.sh"
  if [ ! -f "$BOOTSTRAP_SCRIPT" ]; then
    echo "error: bootstrap-deps.sh not found at $BOOTSTRAP_SCRIPT" >&2
    exit 1
  fi
  bash "$BOOTSTRAP_SCRIPT"
fi

# ---------------------------------------------------------------------------
# Dotfiles install (opt-in: set INSTALL_DOTFILES=1)
# ---------------------------------------------------------------------------
dotfiles_backup=""
if [ "${INSTALL_DOTFILES:-0}" = "1" ]; then
  DOTFILES_SEED="$(cd "$(dirname "$0")/dotfiles" && pwd)"

  if [ ! -d "$DOTFILES_SEED" ]; then
    echo "error: dotfiles payload not found at $DOTFILES_SEED" >&2
    exit 1
  fi

  dotfiles_backup="$HOME_DIR/.dotfiles-backup-$(date +%Y%m%d%H%M%S)"
  mkdir -p "$dotfiles_backup"

  # Helper: install_tree <src_root> <dest_root>
  # Walks src with find-prune (skip .git, __pycache__, *.bak), cp -p preserving
  # structure into dest_root, creating parent dirs as needed.
  install_tree() {
    local src_root="$1"
    local dest_root="$2"
    find "$src_root" -type d \( -name .git -o -name __pycache__ \) -prune \
      -o -type f ! -name '*.bak' -print | while IFS= read -r f; do
      local rel="${f#"$src_root"/}"
      local dest="$dest_root/$rel"
      mkdir -p "$(dirname "$dest")"
      cp -p "$f" "$dest"
    done
  }

  # --- .zshrc (file target) ---
  if [ -f "$HOME_DIR/.zshrc" ]; then
    cp -p "$HOME_DIR/.zshrc" "$dotfiles_backup/.zshrc"
  fi
  mkdir -p "$HOME_DIR"
  cp -p "$DOTFILES_SEED/home/.zshrc" "$HOME_DIR/.zshrc"

  # --- starship.toml (file target) ---
  if [ -f "$HOME_DIR/.config/starship.toml" ]; then
    mkdir -p "$dotfiles_backup/.config"
    cp -p "$HOME_DIR/.config/starship.toml" "$dotfiles_backup/.config/starship.toml"
  fi
  mkdir -p "$HOME_DIR/.config"
  cp -p "$DOTFILES_SEED/config/starship.toml" "$HOME_DIR/.config/starship.toml"

  # --- nvim (directory target: move aside, then copy fresh) ---
  if [ -d "$HOME_DIR/.config/nvim" ]; then
    mv "$HOME_DIR/.config/nvim" "$dotfiles_backup/nvim"
  fi
  install_tree "$DOTFILES_SEED/config/nvim" "$HOME_DIR/.config/nvim"

  # --- kitty (directory target: move aside, then copy fresh) ---
  if [ -d "$HOME_DIR/.config/kitty" ]; then
    mv "$HOME_DIR/.config/kitty" "$dotfiles_backup/kitty"
  fi
  install_tree "$DOTFILES_SEED/config/kitty" "$HOME_DIR/.config/kitty"

  # Substitute __HOME__ token in kitty.conf
  if [ -f "$HOME_DIR/.config/kitty/kitty.conf" ]; then
    tmp="$(mktemp)"
    sed "s|__HOME__|$HOME_DIR|g" "$HOME_DIR/.config/kitty/kitty.conf" > "$tmp"
    mv "$tmp" "$HOME_DIR/.config/kitty/kitty.conf"
  fi

  # Ensure onepassword_kitten.py is executable
  chmod +x "$HOME_DIR/.config/kitty/onepassword_kitten.py" 2>/dev/null || true
fi

echo "Seed installed into: $CLAUDE_DIR"
echo "Files installed:      $count"
if [ -n "$backup_dir" ]; then
  echo "Previous config backed up to: $backup_dir"
fi
if [ "${INSTALL_DEPS:-0}" = "1" ]; then
  echo "Core toolchain:          installed (see bootstrap-deps.sh output above)"
fi
if [ "${INSTALL_DOTFILES:-0}" = "1" ]; then
  echo "Dotfiles installed into: $HOME_DIR"
  echo "Dotfiles backup:         $dotfiles_backup"
fi
echo "Review hooks in $CLAUDE_DIR/hooks/ before your next session."
