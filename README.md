# Claude Code Dev Pipeline Config — Seed

A shareable seed of a Claude Code configuration: behavioral rules, a plan→review→implement→verify pipeline command with its 6 supporting agents, two shell hooks, a statusline script, and a curated settings.json. Clone this repo, run `bash seed/install.sh`, and get a battle-tested Claude Code setup without manually assembling config files.

---

## What's included

### Claude Code config (`seed/claude/`)

| Path | Purpose |
|------|---------|
| `seed/claude/CLAUDE.md` | Global behavioral rules loaded every session (CodeGraph integration, 8 core rules) |
| `seed/claude/rules/arch-common.md` | Architecture rules: think-before-coding, simplicity, surgical changes, goal-driven execution |
| `seed/claude/rules/common-sense.md` | Common-sense coding rules: plan first, smallest diff, explain root cause, build+test before done |
| `seed/claude/agents/planner.md` | Agent: produces a structured, reviewable implementation plan |
| `seed/claude/agents/plan-reviewer.md` | Agent: reviews a plan for correctness and completeness before implementation |
| `seed/claude/agents/implementer.md` | Agent: executes an approved plan with minimal, surgical changes |
| `seed/claude/agents/impl-reviewer.md` | Agent: reviews an implementation diff against the approved plan |
| `seed/claude/agents/dead-code.md` | Agent: identifies dead/unreachable code introduced or uncovered by changes |
| `seed/claude/agents/pr-summarizer.md` | Agent: writes a concise, human-readable PR summary from a diff |
| `seed/claude/commands/pipeline.md` | `/pipeline` slash command — orchestrates the full plan→review→implement→verify loop |
| `seed/claude/commands/cleanup-branches.md` | `/cleanup-branches` — delete local branches whose remote is gone; lists + confirms, never force-deletes |
| `seed/claude/commands/test-green.md` | `/test-green` — run tests+coverage and loop fixing failures/gaps until thresholds pass |
| `seed/claude/commands/options.md` | `/options` — generate three distinct approaches (ship-fast / maintainable / robust) before committing |
| `seed/claude/hooks/permission-screen.mjs` | PreToolUse Bash hook: silently auto-approves a strict read-only allowlist, blocks dangerous patterns |
| `seed/claude/hooks/context-mode-cache-heal.mjs` | SessionStart hook: heals the context-mode plugin cache; no-ops if plugin is absent |
| `seed/claude/statusline-command.sh` | Shell script powering the Claude Code statusline (requires `jq`) |
| `seed/claude/settings.json` | Curated settings: permissions, hooks wiring, statusline, plugins, marketplaces |

### Dotfiles (`seed/dotfiles/`) — optional

| Path | Installs to | Notes |
|------|-------------|-------|
| `seed/dotfiles/home/.zshrc` | `~/.zshrc` | Generic portable baseline; no secrets, no org-specific config |
| `seed/dotfiles/config/starship.toml` | `~/.config/starship.toml` | Gruvbox Material prompt theme |
| `seed/dotfiles/config/nvim/` | `~/.config/nvim/` | NvChad-based Neovim config |
| `seed/dotfiles/config/kitty/` | `~/.config/kitty/` | Curated kitty config (kitty.conf, themes, tab_bar.py, kittens) |

---

## Prerequisites

- **Claude Code** — the CLI this config targets
- **`jq`** — the statusline hard-depends on it; the status line will be broken without it (`brew install jq` or `apt install jq`)
- **Node.js** — hooks are `.mjs` ES modules and require a Node.js runtime
- **bash** — `install.sh` and `statusline-command.sh` are bash scripts

Model IDs are intentionally NOT pinned in this seed. You use whichever model you have configured or prefer.

---

## Install

### Claude Code config only (default)

```bash
git clone https://github.com/your-username/ClaudeCode-dev-pipeline-config.git
cd ClaudeCode-dev-pipeline-config
bash seed/install.sh
```

The installer honors a `CLAUDE_DIR` environment override. To do a dry test without touching your real config:

```bash
CLAUDE_DIR=/tmp/test-claude bash seed/install.sh
```

### Dotfiles bootstrap (optional)

Set `INSTALL_DOTFILES=1` to also install the dotfiles payload (`seed/dotfiles/`). This is opt-in — the default run is claude-only and the dotfiles are never touched without it.

```bash
INSTALL_DOTFILES=1 bash seed/install.sh
```

**What gets installed:**

- `~/.zshrc` — generic portable zsh baseline (oh-my-zsh + starship + common tools). No secrets, no org-specific config. Customize for your machine after installing.
- `~/.config/starship.toml` — Gruvbox Material prompt theme.
- `~/.config/nvim/` — NvChad-based Neovim config (full tree).
- `~/.config/kitty/` — Curated kitty config: `kitty.conf`, theme files, `tab_bar.py`, kittens, `kitty_search`.

**Notes:**

- The `.zshrc` is a sanitized generic baseline. It contains no secrets and no org-specific configuration. Add your own machine-specific overrides (private tokens, project paths) after installing — do **not** commit those to this repo.
- `.zprofile` is intentionally omitted. If you use Amazon Q or another tool that manages `.zprofile`, this seed will not conflict with it.
- The kitty `background_image` path in `kitty.conf` is tokenized as `__HOME__/Pictures/pics/wallpappers/thumb-1920-696469.png`. The installer substitutes `__HOME__` with your real home directory at install time. The wallpaper image itself is **not** shipped — supply the file at that path or remove/change the `background_image` line in `~/.config/kitty/kitty.conf` after installing.
- Directory targets (`nvim`, `kitty`) are **replaced**, not merged. Existing directories are moved aside into the backup root before the fresh tree is written.
- Backup root for dotfiles: `~/.dotfiles-backup-<timestamp>/`. One directory per run; clean up manually when no longer needed.

**Dry-run into a temp directory:**

```bash
TMP=$(mktemp -d)
HOME_DIR="$TMP" CLAUDE_DIR="$TMP/.claude" INSTALL_DOTFILES=1 bash seed/install.sh
```

### Core toolchain bootstrap (optional)

Set `INSTALL_DEPS=1` to also run `seed/dotfiles/bootstrap-deps.sh`, which installs the Core toolchain on macOS. The script is idempotent — safe to re-run — and bootstraps Homebrew (and Xcode Command Line Tools) if they are missing.

**Fresh-machine one-liner** (Claude config + dotfiles + Core toolchain in one shot):

```bash
INSTALL_DEPS=1 INSTALL_DOTFILES=1 bash seed/install.sh
```

**What the Core toolchain installs:**

- **Terminal / shell:** kitty, oh-my-zsh, zsh plugins (zsh-autosuggestions, zsh-syntax-highlighting, zsh-history-substring-search, zsh-completions), powerlevel10k (installed; starship stays the active prompt), starship
- **Editor:** neovim
- **CLI tools:** fzf, bat, ripgrep, fd, lazygit, jq, atuin, broot, git, tmux, direnv, node, colorls (Ruby gem; powers the `la`/`lc` aliases)
- **Fonts:** font-blex-mono-nerd-font (Nerd Font)
- **Apps / auth:** 1Password CLI, Claude Code
- **System:** Xcode Command Line Tools

**Intentionally NOT included (out of Core scope):**

Language runtimes and version managers — Go, Java, PHP, chruby, pyenv, nvm, pnpm, bun — and Amazon Q are not installed by this script. Add them separately for your machine. (Ruby is installed only as the `colorls` dependency, not as a managed runtime.) The shipped `.zshrc` is a generic portable baseline with no secrets and no org-specific configuration.

---

## Backup-then-replace (NOT a merge)

If `~/.claude` already exists, the installer copies it to `~/.claude.backup.<timestamp>` before writing anything. It then overwrites matching files. Your existing `settings.json` is **replaced**, not merged — it is recoverable from the backup directory. Backups accumulate one directory per run; clean them up manually when you no longer need them.

---

## Security — review before installing

The install wires up two hooks that execute on your machine. Read `seed/claude/hooks/` before installing:

- **`permission-screen.mjs`** (PreToolUse Bash): silently auto-approves a strict read-only Bash allowlist without prompting. It never denies requests — it fails safe — and blocks redirection operators, `$()` subshells, backticks, `sed -i`, and `find -exec`. Wiring this hook changes your security posture: commands on the allowlist will not trigger a permission prompt.
- **`context-mode-cache-heal.mjs`** (SessionStart): repairs the context-mode plugin's local cache at the start of each session. It no-ops gracefully if the context-mode plugin is not installed.

---

## Plugins & marketplaces

`settings.json` enables the following plugins and registers two third-party marketplaces:

| Plugin key | Purpose |
|------------|---------|
| `claude-code-setup@claude-plugins-official` | Official Claude Code setup helpers |
| `context-mode@context-mode` | Context management (registered from `mksglu/context-mode` on GitHub) |
| `feature-dev@claude-plugins-official` | Feature development workflow |
| `superpowers@claude-plugins-official` | Extended Claude Code capabilities |
| `claude-mem@thedotmack` | Persistent memory (registered from `thedotmack/claude-mem` on GitHub) |

Remove any `enabledPlugins` entries and corresponding `extraKnownMarketplaces` entries you don't want before installing, or edit `~/.claude/settings.json` after installing.

---

## Intentionally omitted

Personal model pins (`ANTHROPIC_*_MODEL`, top-level `model`, `availableModels`) and machine-specific `additionalDirectories` are dropped from the seed. To pin a model, add it back:

```json
{
  "env": {
    "ANTHROPIC_MODEL": "claude-opus-4-8[1m]"
  }
}
```

---

## Notes

- `permissions.defaultMode: "plan"` is a deliberate default that requires you to approve tool calls in a first pass. It is easily removed by changing the value to `"default"` or deleting the key.
- The CodeGraph section in `CLAUDE.md` assumes the CodeGraph tool and a `.codegraph/` index exist in your project. Remove that section if you don't use CodeGraph.

---

## Excluded

Local skills are not shipped in this seed: `grill-me`, `handoff`, `vibe-check`, `vibe-explain`, `vibe-guard`, `vibe-secure`.

---

## Manual install fallback

If you prefer not to run the install script:

1. Copy `seed/claude/*` into `~/.claude/` (preserving subdirectory structure).
2. In `~/.claude/settings.json`, replace all 3 occurrences of `__CLAUDE_DIR__` with your real `~/.claude` path.
3. Make hooks and statusline executable:
   ```bash
   chmod +x ~/.claude/hooks/*.mjs ~/.claude/statusline-command.sh
   ```
