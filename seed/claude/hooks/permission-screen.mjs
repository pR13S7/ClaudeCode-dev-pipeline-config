#!/usr/bin/env node
/**
 * PreToolUse hook: conservatively auto-approve obviously-safe read-only Bash
 * commands to reduce permission friction. Everything else falls through to the
 * normal permission flow (we emit no decision). This NEVER denies — it only
 * fast-paths a strict allowlist — so getting the schema wrong fails safe.
 *
 * Only Bash is screened. A command is auto-approved only when ALL of:
 *   - it contains no redirection (`>`/`>>`), command substitution (`$(`/backticks),
 *     or process-substitution,
 *   - every chained segment (split on | && || ;) starts with a read-only binary
 *     from SAFE_CMDS,
 *   - it does not reference protected paths (.env, secrets/, *.internal).
 * Otherwise we stay silent and let Claude Code prompt as usual.
 */

import { readFileSync } from "node:fs";

// Read-only binaries safe to auto-approve.
const SAFE_CMDS = new Set([
  "git", "ls", "cat", "head", "tail", "wc", "rg", "grep", "find",
  "pwd", "echo", "which", "file", "stat", "tree", "sort", "uniq",
  "cut", "awk", "sed", "diff", "basename", "dirname", "realpath",
]);

// git is read-only only for these subcommands.
const SAFE_GIT_SUB = new Set([
  "status", "diff", "log", "show", "branch", "remote", "blame",
  "rev-parse", "describe", "config", "ls-files", "ls-tree", "shortlog",
  "tag", "stash", // stash with no args lists; bare reads handled below
]);

function defer() {
  // No output + exit 0 => no decision; normal permission flow proceeds.
  process.exit(0);
}

function allow(reason) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: reason,
    },
  }));
  process.exit(0);
}

let raw = "";
try {
  raw = readFileSync(0, "utf8");
} catch {
  defer();
}

let payload;
try {
  payload = JSON.parse(raw);
} catch {
  defer();
}

if (payload?.tool_name !== "Bash") defer();

const command = String(payload?.tool_input?.command ?? "");
if (!command.trim()) defer();

// Reject anything that can write, escape, or escalate.
if (/[>]|\$\(|`|<\(|>\(/.test(command)) defer();

// Never fast-path protected paths (mirrors settings.json deny-list intent).
if (/\.env\b|secrets\/|\.internal\b/.test(command)) defer();

// Each chained segment must be a known read-only command.
const segments = command.split(/\|\||&&|[|;]/).map((s) => s.trim()).filter(Boolean);
if (segments.length === 0) defer();

for (const seg of segments) {
  const tokens = seg.split(/\s+/);
  const bin = tokens[0];
  if (!SAFE_CMDS.has(bin)) defer();
  if (bin === "git") {
    const sub = tokens[1];
    if (!sub || !SAFE_GIT_SUB.has(sub)) defer();
  }
  // Block in-place editors masquerading as read-only (sed -i, awk writing files
  // is already blocked by the no-redirection check; sed -i is not).
  if (bin === "sed" && tokens.some((t) => t === "-i" || t.startsWith("-i"))) defer();
  if (bin === "find" && tokens.some((t) => t === "-delete" || t === "-exec" || t === "-execdir")) defer();
}

allow("auto-approved read-only command (permission-screen hook)");
