# Claude Code Dev Pipeline Config — Seed

A shareable seed of a Claude Code configuration: behavioral rules, a plan→review→implement→verify pipeline command with its 6 supporting agents, two shell hooks, a statusline script, and a curated settings.json. Clone this repo, run `bash seed/install.sh`, and get a battle-tested Claude Code setup without manually assembling config files.

---

## What's included

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
| `seed/claude/hooks/permission-screen.mjs` | PreToolUse Bash hook: silently auto-approves a strict read-only allowlist, blocks dangerous patterns |
| `seed/claude/hooks/context-mode-cache-heal.mjs` | SessionStart hook: heals the context-mode plugin cache; no-ops if plugin is absent |
| `seed/claude/statusline-command.sh` | Shell script powering the Claude Code statusline (requires `jq`) |
| `seed/claude/settings.json` | Curated settings: permissions, hooks wiring, statusline, plugins, marketplaces |

---

## Prerequisites

- **Claude Code** — the CLI this config targets
- **`jq`** — the statusline hard-depends on it; the status line will be broken without it (`brew install jq` or `apt install jq`)
- **Node.js** — hooks are `.mjs` ES modules and require a Node.js runtime
- **bash** — `install.sh` and `statusline-command.sh` are bash scripts

Model IDs are intentionally NOT pinned in this seed. You use whichever model you have configured or prefer.

---

## Install

```bash
git clone https://github.com/your-username/ClaudeCode-dev-pipeline-config.git
cd ClaudeCode-dev-pipeline-config
bash seed/install.sh
```

The installer honors a `CLAUDE_DIR` environment override. To do a dry test without touching your real config:

```bash
CLAUDE_DIR=/tmp/test-claude bash seed/install.sh
```

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
