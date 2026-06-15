#!/usr/bin/env bash
set -euo pipefail

# bootstrap-deps.sh — Core toolchain installer for a fresh macOS machine.
# Idempotent: safe to re-run. Installs Homebrew, formulae, casks, oh-my-zsh,
# zsh plugins, powerlevel10k, and Claude Code.
# Run standalone:  bash seed/dotfiles/bootstrap-deps.sh
# Or via install.sh with INSTALL_DEPS=1.

ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"

# ---------------------------------------------------------------------------
# Non-interactive guard
# ---------------------------------------------------------------------------
if [ ! -t 0 ]; then
  if ! xcode-select -p >/dev/null 2>&1; then
    echo "ERROR: Xcode Command Line Tools are required but missing." >&2
    echo "       Run this script in an interactive terminal so the installer can prompt." >&2
    exit 1
  fi
  if ! command -v brew >/dev/null 2>&1; then
    echo "ERROR: Homebrew is required but missing." >&2
    echo "       Run this script in an interactive terminal so the installer can prompt." >&2
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# 1. Xcode Command Line Tools
# ---------------------------------------------------------------------------
echo "==> [1/8] Checking Xcode Command Line Tools..."
if ! xcode-select -p >/dev/null 2>&1; then
  xcode-select --install
  echo "    Waiting for Xcode CLT installation to complete..."
  until xcode-select -p >/dev/null 2>&1; do sleep 5; done
fi
echo "    Xcode CLT: OK"

# ---------------------------------------------------------------------------
# 2. Homebrew
# ---------------------------------------------------------------------------
echo "==> [2/8] Checking Homebrew..."
if ! command -v brew >/dev/null 2>&1; then
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
# Resolve brew prefix robustly (Apple Silicon: /opt/homebrew; Intel: /usr/local)
eval "$($(command -v brew || echo /opt/homebrew/bin/brew) shellenv)"
echo "    Homebrew: OK ($(brew --version | head -1))"

# ---------------------------------------------------------------------------
# 3. Brew formulae
# ---------------------------------------------------------------------------
echo "==> [3/8] Installing brew formulae..."
for formula in starship neovim bat fzf ripgrep fd lazygit jq atuin broot git tmux direnv node ruby; do
  if brew list "$formula" >/dev/null 2>&1; then
    echo "    $formula: already installed"
  else
    echo "    Installing $formula..."
    brew install "$formula"
  fi
done

# colorls (Ruby gem) — powers the `la`/`lc` aliases in .zshrc.
# `ruby` is installed via brew above; expose its gem executables on PATH.
_brew_prefix="$(brew --prefix)"
export PATH="$_brew_prefix/opt/ruby/bin:$PATH"
for _gembin in "$_brew_prefix"/lib/ruby/gems/*/bin; do
  [ -d "$_gembin" ] && export PATH="$_gembin:$PATH"
done
unset _gembin _brew_prefix
if command -v colorls >/dev/null 2>&1; then
  echo "    colorls: already installed"
else
  echo "    Installing colorls (gem)..."
  gem install colorls
fi

# ---------------------------------------------------------------------------
# 4. Brew casks
# ---------------------------------------------------------------------------
echo "==> [4/8] Installing brew casks..."
for cask in kitty 1password-cli font-blex-mono-nerd-font; do
  if brew list --cask "$cask" >/dev/null 2>&1; then
    echo "    $cask: already installed"
  else
    echo "    Installing $cask..."
    brew install --cask "$cask"
  fi
done

# ---------------------------------------------------------------------------
# 5. broot launcher
# ---------------------------------------------------------------------------
echo "==> [5/8] Installing broot launcher..."
[ -f "$HOME/.config/broot/launcher/bash/br" ] || broot --install
echo "    broot launcher: OK"

# ---------------------------------------------------------------------------
# 6. oh-my-zsh
# ---------------------------------------------------------------------------
echo "==> [6/8] Checking oh-my-zsh..."
if [ ! -d "$HOME/.oh-my-zsh" ]; then
  echo "    Installing oh-my-zsh (no shell change, no .zshrc clobber)..."
  RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended --keep-zshrc
fi
echo "    oh-my-zsh: OK"

# ---------------------------------------------------------------------------
# 7. zsh plugins + powerlevel10k
# ---------------------------------------------------------------------------
echo "==> [7/8] Installing zsh plugins and powerlevel10k..."

_clone_if_missing() {
  local repo="$1"
  local dest="$2"
  if [ -d "$dest" ]; then
    echo "    $(basename "$dest"): already installed"
  else
    echo "    Cloning $(basename "$dest")..."
    git clone --depth=1 "$repo" "$dest"
  fi
}

_clone_if_missing "https://github.com/zsh-users/zsh-autosuggestions" \
  "$ZSH_CUSTOM/plugins/zsh-autosuggestions"

_clone_if_missing "https://github.com/zsh-users/zsh-syntax-highlighting" \
  "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"

_clone_if_missing "https://github.com/zsh-users/zsh-history-substring-search" \
  "$ZSH_CUSTOM/plugins/zsh-history-substring-search"

_clone_if_missing "https://github.com/zsh-users/zsh-completions" \
  "$ZSH_CUSTOM/plugins/zsh-completions"

_clone_if_missing "https://github.com/romkatv/powerlevel10k" \
  "$ZSH_CUSTOM/themes/powerlevel10k"

# ---------------------------------------------------------------------------
# 8. Claude Code
# ---------------------------------------------------------------------------
echo "==> [8/8] Checking Claude Code..."
if command -v claude >/dev/null 2>&1; then
  echo "    claude: already installed ($(claude --version 2>/dev/null || echo 'version unknown'))"
else
  echo "    Installing Claude Code..."
  npm install -g @anthropic-ai/claude-code
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "=================================================================="
echo "  Core toolchain installed successfully."
echo ""
echo "  Installed: starship neovim bat fzf ripgrep fd lazygit jq atuin"
echo "             broot git tmux direnv node ruby colorls kitty"
echo "             1password-cli font-blex-mono-nerd-font oh-my-zsh"
echo "             zsh-plugins powerlevel10k claude-code"
echo ""
echo "  NOTE: Language runtimes (go, java, python, nvm, pnpm, bun)"
echo "        and Amazon Q are NOT installed — add them separately."
echo "        (ruby is installed only as the colorls dependency.)"
echo "  NOTE: Restart your terminal (or run: exec zsh) to apply changes."
echo "=================================================================="
