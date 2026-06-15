"""Custom Kitty tab bar.

Layout per tab:    <wedge|sep> <bell?> <activity?> <icon> <title> <wedge>

Far-left global cell (drawn once with the first tab):
    <layout-glyph> <layout-name> [· <num-windows>w]

Right-aligned status (drawn once after the last tab):
    <user>  <host>  <cwd>

Design notes:
  * Stays compatible with the configured `active_tab_font_style` /
    `inactive_tab_font_style` by snapshotting cursor.bold / cursor.italic
    around our own drawing.
  * Caches per-tab icon resolution to avoid repeated TabAccessor system
    calls (active_oldest_exe traverses the process tree).
  * Pre-compiles a single regex over icon keywords for the title-scan
    fallback so the per-redraw cost is O(title length), not O(N keywords).
  * Pure-ASCII source for all glyphs (\\uXXXX / \\UXXXXXXXX) so the file
    survives copy/paste through chat surfaces and editors that strip
    Private-Use-Area characters.
"""

import os
import re
import socket

from kitty.boss import get_boss
from kitty.fast_data_types import Screen, wcswidth
from kitty.tab_bar import (
    DrawData,
    ExtraData,
    Formatter,
    TabBarData,
    TabAccessor,
    as_rgb,
    draw_attributed_string,
    draw_tab_with_separator,
)


# ---------------------------------------------------------------------------
# Palette (Gruvbox Material).
# ---------------------------------------------------------------------------
GRUV_AQUA   = 0x8EC07C
GRUV_BLUE   = 0x83A598
GRUV_PURPLE = 0xD3869B
GRUV_FG     = 0xEBDBB2
GRUV_SEP    = 0x665C54
GRUV_RED    = 0xFB4934
GRUV_YELLOW = 0xFABD2F
GRUV_GREEN  = 0xB8BB26
GRUV_ORANGE = 0xFE8019


# ---------------------------------------------------------------------------
# Glyph tables. Use \uXXXX / \UXXXXXXXX so source stays pure-ASCII.
# Requires a Nerd Font (e.g. SauceCodePro Nerd Font).
# ---------------------------------------------------------------------------

# Set to True to use Unicode emoji instead of Nerd Font glyphs.
# Emoji are wider/uneven and may misalign tabs; glyphs are recommended.
USE_EMOJI = False

NF_ICONS: dict[str, tuple[str, int]] = {
    # Shells -- nf-fa-terminal
    "zsh":         ("\uf120", GRUV_AQUA),
    "bash":        ("\uf120", GRUV_AQUA),
    "fish":        ("\uf120", GRUV_AQUA),
    "sh":          ("\uf120", GRUV_AQUA),
    "pwsh":        ("\uf120", GRUV_BLUE),

    # Editors
    "nvim":        ("\ue62b", GRUV_GREEN),    # nf-custom-vim
    "vim":         ("\ue62b", GRUV_GREEN),
    "vi":          ("\ue62b", GRUV_GREEN),
    "nano":        ("\uf040", GRUV_YELLOW),   # nf-fa-pencil
    "emacs":       ("\ue632", GRUV_PURPLE),   # nf-custom-emacs
    "code":        ("\ue70c", GRUV_BLUE),     # nf-dev-visualstudio
    "cursor":      ("\uf121", GRUV_BLUE),     # nf-fa-code
    "hx":          ("\ue62b", GRUV_PURPLE),

    # Pagers / viewers -- nf-fa-book
    "less":        ("\uf02d", GRUV_FG),
    "more":        ("\uf02d", GRUV_FG),
    "bat":         ("\uf02d", GRUV_ORANGE),
    "man":         ("\uf02d", GRUV_FG),

    # File managers / nav -- nf-fa-folder
    "ranger":      ("\uf07b", GRUV_YELLOW),
    "lf":          ("\uf07b", GRUV_YELLOW),
    "yazi":        ("\uf07b", GRUV_YELLOW),
    "nnn":         ("\uf07b", GRUV_YELLOW),

    # Multiplexers / monitors
    "tmux":        ("\uf108", GRUV_GREEN),    # nf-fa-desktop
    "screen":      ("\uf108", GRUV_GREEN),
    "htop":        ("\uf0ae", GRUV_RED),      # nf-fa-tasks
    "btop":        ("\uf0ae", GRUV_RED),
    "top":         ("\uf0ae", GRUV_RED),

    # VCS / forge
    "git":         ("\uf1d3", GRUV_ORANGE),   # nf-fa-git
    "lazygit":     ("\uf1d3", GRUV_ORANGE),
    "tig":         ("\uf1d3", GRUV_ORANGE),
    "gh":          ("\uf09b", GRUV_FG),       # nf-fa-github

    # Containers / orchestration
    "docker":      ("\uf308", GRUV_BLUE),     # nf-linux-docker
    "podman":      ("\uf308", GRUV_BLUE),
    "kubectl":     ("\u2638", GRUV_BLUE),     # wheel of dharma
    "k9s":         ("\u2638", GRUV_BLUE),
    "helm":        ("\u2638", GRUV_BLUE),

    # Cloud / infra
    "aws":         ("\uf375", GRUV_ORANGE),
    "terraform":   ("\uf1b2", GRUV_PURPLE),   # nf-fa-cube
    "tofu":        ("\uf1b2", GRUV_PURPLE),
    "ansible":     ("\uf1b3", GRUV_RED),      # nf-fa-cubes

    # SSH / network
    "ssh":         ("\uf084", GRUV_AQUA),     # nf-fa-key
    "mosh":        ("\uf084", GRUV_AQUA),
    "scp":         ("\uf084", GRUV_AQUA),
    "rsync":       ("\uf021", GRUV_AQUA),     # nf-fa-refresh
    "curl":        ("\uf0ac", GRUV_AQUA),     # nf-fa-globe
    "wget":        ("\uf0ac", GRUV_AQUA),
    "ping":        ("\uf0ac", GRUV_AQUA),

    # Languages / runtimes / REPLs
    "python":      ("\ue73c", GRUV_YELLOW),
    "python3":     ("\ue73c", GRUV_YELLOW),
    "ipython":     ("\ue73c", GRUV_YELLOW),
    "node":        ("\ue718", GRUV_GREEN),
    "deno":        ("\ue628", GRUV_FG),
    "bun":         ("\ue718", GRUV_YELLOW),
    "ruby":        ("\ue739", GRUV_RED),
    "irb":         ("\ue739", GRUV_RED),
    "go":          ("\ue724", GRUV_BLUE),
    "rustc":       ("\ue7a8", GRUV_ORANGE),
    "cargo":       ("\ue7a8", GRUV_ORANGE),
    "java":        ("\ue738", GRUV_RED),
    "lua":         ("\ue620", GRUV_BLUE),
    "perl":        ("\ue7ab", GRUV_BLUE),
    "php":         ("\ue73d", GRUV_PURPLE),

    # Package / build tools
    "npm":         ("\ue71e", GRUV_RED),
    "pnpm":        ("\ue71e", GRUV_ORANGE),
    "yarn":        ("\ue6a7", GRUV_BLUE),
    "make":        ("\uf013", GRUV_FG),
    "cmake":       ("\uf013", GRUV_FG),
    "pip":         ("\ue73c", GRUV_YELLOW),
    "uv":          ("\ue73c", GRUV_YELLOW),
    "poetry":      ("\ue73c", GRUV_YELLOW),
    "brew":        ("\uf0fc", GRUV_YELLOW),   # nf-fa-beer
    "apt":         ("\uf1b2", GRUV_ORANGE),

    # Databases
    "psql":        ("\ue76e", GRUV_BLUE),
    "mysql":       ("\ue704", GRUV_ORANGE),
    "sqlite3":     ("\ue706", GRUV_BLUE),
    "redis-cli":   ("\ue706", GRUV_RED),
    "mongo":       ("\ue7a4", GRUV_GREEN),

    # Misc
    "ssh-agent":   ("\uf084", GRUV_FG),
    "gpg":         ("\uf023", GRUV_YELLOW),   # nf-fa-lock
    "fzf":         ("\uf002", GRUV_PURPLE),   # nf-fa-search
    "rg":          ("\uf002", GRUV_PURPLE),
    "ag":          ("\uf002", GRUV_PURPLE),
    "find":        ("\uf002", GRUV_PURPLE),
    "watch":       ("\uf06e", GRUV_YELLOW),   # nf-fa-eye
    "sudo":        ("\uf023", GRUV_RED),
}

EMOJI_ICONS: dict[str, tuple[str, int]] = {
    "zsh":       ("\U0001f41a", GRUV_AQUA),
    "bash":      ("\U0001f41a", GRUV_AQUA),
    "fish":      ("\U0001f41f", GRUV_AQUA),
    "nvim":      ("\U0001f4dd", GRUV_GREEN),
    "vim":       ("\U0001f4dd", GRUV_GREEN),
    "nano":      ("\U0001f4dd", GRUV_YELLOW),
    "emacs":     ("\U0001f4dd", GRUV_PURPLE),
    "less":      ("\U0001f4d6", GRUV_FG),
    "man":       ("\U0001f4d6", GRUV_FG),
    "ranger":    ("\U0001f4c1", GRUV_YELLOW),
    "lf":        ("\U0001f4c1", GRUV_YELLOW),
    "yazi":      ("\U0001f4c1", GRUV_YELLOW),
    "tmux":      ("\U0001fa9f", GRUV_GREEN),
    "htop":      ("\U0001f4ca", GRUV_RED),
    "btop":      ("\U0001f4ca", GRUV_RED),
    "top":       ("\U0001f4ca", GRUV_RED),
    "git":       ("\U0001f33f", GRUV_ORANGE),
    "lazygit":   ("\U0001f33f", GRUV_ORANGE),
    "docker":    ("\U0001f433", GRUV_BLUE),
    "podman":    ("\U0001f433", GRUV_BLUE),
    "kubectl":   ("\u2638",     GRUV_BLUE),
    "k9s":       ("\u2638",     GRUV_BLUE),
    "ssh":       ("\U0001f510", GRUV_AQUA),
    "mosh":      ("\U0001f510", GRUV_AQUA),
    "curl":      ("\U0001f310", GRUV_AQUA),
    "wget":      ("\U0001f310", GRUV_AQUA),
    "python":    ("\U0001f40d", GRUV_YELLOW),
    "python3":   ("\U0001f40d", GRUV_YELLOW),
    "ipython":   ("\U0001f40d", GRUV_YELLOW),
    "node":      ("\U0001f7e2", GRUV_GREEN),
    "ruby":      ("\U0001f48e", GRUV_RED),
    "go":        ("\U0001f439", GRUV_BLUE),
    "rustc":     ("\U0001f980", GRUV_ORANGE),
    "cargo":     ("\U0001f980", GRUV_ORANGE),
    "java":      ("\u2615",     GRUV_RED),
    "psql":      ("\U0001f418", GRUV_BLUE),
    "mysql":     ("\U0001f42c", GRUV_ORANGE),
    "redis-cli": ("\U0001f4d5", GRUV_RED),
    "mongo":     ("\U0001f343", GRUV_GREEN),
    "make":      ("\U0001f528", GRUV_FG),
    "fzf":       ("\U0001f50d", GRUV_PURPLE),
    "rg":        ("\U0001f50d", GRUV_PURPLE),
    "watch":     ("\U0001f441", GRUV_YELLOW),
    "sudo":      ("\U0001f512", GRUV_RED),
}

DEFAULT_ICON_NF    = ("\uf013", GRUV_FG)        # nf-fa-cog
DEFAULT_ICON_EMOJI = ("\u2699\ufe0f", GRUV_FG)  # gear

# Layout indicators (per kitty layout name).
LAYOUT_ICONS: dict[str, str] = {
    "tall":       "\uf0db",   # nf-fa-columns
    "fat":        "\uf0db",
    "horizontal": "\uf0c9",   # nf-fa-bars
    "vertical":   "\uf0db",
    "stack":      "\uf2d2",   # nf-fa-window-maximize
    "grid":       "\uf009",   # nf-fa-th-large
    "splits":     "\uf009",
}
LAYOUT_DEFAULT_ICON = "\uf2d0"  # nf-fa-window

# Per-tab status indicators.
BELL_ICON     = "\uf0a2"  # nf-fa-bell
ACTIVITY_ICON = "\u25cf"  # ●

# Strip "user@host:" prompt prefix from each tab title before display.
# What follows the colon is preserved (it's typically the cwd or a command).
_PROMPT_PREFIX_RE = re.compile(r"^[\w.-]+@[\w.-]+:\s*")

# A title that, after prefix-stripping, looks like a bare path (no spaces,
# starts with "/" or "~"). For these we display only the basename — the
# full cwd is already shown in the right-status.
_BARE_PATH_RE = re.compile(r"^[~/][^\s]*$")


# ---------------------------------------------------------------------------
# Caches.
# ---------------------------------------------------------------------------

# tab_id -> (title_at_resolve, icon_glyph, icon_color)
# We use the tab's title as the cache key because shell_integration mirrors
# the foreground command into the title; when the user runs `nvim`, the
# title changes, so the icon is recomputed.
_ICON_CACHE: dict[int, tuple[str, str, int]] = {}
_ICON_CACHE_MAX = 128

# Single regex over all known keywords, longer keys first so "python3"
# matches before "python".
_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(
        re.escape(k) for k in sorted(NF_ICONS.keys(), key=len, reverse=True)
    ) + r")\b"
)


# ---------------------------------------------------------------------------
# Icon resolution.
# ---------------------------------------------------------------------------

def _resolve_icon(exe: str | None, title: str) -> tuple[str, int]:
    table = EMOJI_ICONS if USE_EMOJI else NF_ICONS
    default = DEFAULT_ICON_EMOJI if USE_EMOJI else DEFAULT_ICON_NF

    if exe:
        name = os.path.basename(exe).lower()
        if name in table:
            return table[name]
        stripped = re.sub(r"[\d.]+$", "", name)
        if stripped and stripped in table:
            return table[stripped]

    if title:
        lt = title.lower()
        first = lt.split()[0] if lt.split() else ""
        first = os.path.basename(first)
        if first in table:
            return table[first]
        m = _KEYWORD_RE.search(lt)
        if m:
            return table[m.group(1)]

    return default


def _clean_title(title: str) -> str:
    """Strip noisy prompt prefixes (user@host:) from a tab title.

    If what's left is a bare path (e.g. "~/work/project"), reduce it to
    just the folder name. Command-style titles ("nvim README.md") are
    left as-is.
    """
    if not title:
        return title

    cleaned = _PROMPT_PREFIX_RE.sub("", title, count=1).strip()

    if cleaned and _BARE_PATH_RE.match(cleaned):
        base = os.path.basename(cleaned.rstrip("/"))
        if base:
            cleaned = base

    return cleaned or " "  # never return empty (kitty truncates badly)


def _icon_for_tab(tab: TabBarData) -> tuple[str, int]:
    """Return (glyph, color) for a tab. Cached by (tab_id, title)."""
    title_key = tab.title or ""
    cached = _ICON_CACHE.get(tab.tab_id)
    if cached is not None and cached[0] == title_key:
        return cached[1], cached[2]

    # Cache miss: do the expensive lookup.
    try:
        exe = TabAccessor(tab.tab_id).active_oldest_exe
    except Exception:
        exe = None

    icon, color = _resolve_icon(exe, title_key)
    _ICON_CACHE[tab.tab_id] = (title_key, icon, color)

    if len(_ICON_CACHE) > _ICON_CACHE_MAX:
        # Evict oldest entry (dicts preserve insertion order).
        try:
            _ICON_CACHE.pop(next(iter(_ICON_CACHE)))
        except StopIteration:
            pass

    return icon, color


# ---------------------------------------------------------------------------
# Drawing.
# ---------------------------------------------------------------------------

def _draw_global_left(draw_data: DrawData, screen: Screen) -> None:
    """Far-left cell: layout glyph + name + window count."""
    boss = get_boss()
    active = getattr(boss, "active_tab", None)
    if active is None:
        return

    layout_obj = getattr(active, "current_layout", None)
    layout_name = getattr(layout_obj, "name", "") or ""
    if not layout_name:
        return

    n_windows = getattr(active, "num_window_groups", 1) or 1
    glyph = LAYOUT_ICONS.get(layout_name, LAYOUT_DEFAULT_ICON)

    text = f"  {glyph} {layout_name}"
    if n_windows > 1:
        text += f" \u00b7 {n_windows}w"  # ·
    text += " "

    screen.cursor.italic = False
    screen.cursor.bold = False
    screen.cursor.fg = as_rgb(GRUV_AQUA)
    screen.cursor.bg = as_rgb(int(draw_data.default_bg))
    screen.draw(text)


def draw_tab(
    draw_data: DrawData,
    screen: Screen,
    tab: TabBarData,
    before: int,
    max_title_length: int,
    index: int,
    is_last: bool,
    extra_data: ExtraData,
) -> int:
    old_fg, old_bg = screen.cursor.fg, screen.cursor.bg
    old_bold, old_italic = screen.cursor.bold, screen.cursor.italic

    if index == 1:
        _draw_global_left(draw_data, screen)

    # Powerline-style wedge or inter-tab separator.
    if tab.is_active:
        screen.cursor.fg = as_rgb(int(draw_data.active_bg))
        screen.cursor.bg = as_rgb(int(draw_data.default_bg))
        screen.draw("\u2590\u2588")  # ▐█
    elif extra_data.prev_tab is not None and not extra_data.prev_tab.is_active:
        screen.cursor.bg = as_rgb(int(draw_data.default_bg))
        screen.cursor.fg = as_rgb(GRUV_SEP)
        screen.draw(" \u2502 ")  # │

    # Build prefix: optional bell, optional activity dot, then exe icon.
    parts: list[tuple[str, int]] = []
    if getattr(tab, "needs_attention", False):
        parts.append((BELL_ICON, GRUV_RED))
    if getattr(tab, "has_activity_since_last_focus", False) and not tab.is_active:
        parts.append((ACTIVITY_ICON, GRUV_YELLOW))
    icon, icon_color = _icon_for_tab(tab)
    parts.append((icon, icon_color))

    tab_bg = int(draw_data.active_bg if tab.is_active else draw_data.inactive_bg)
    screen.cursor.bg = as_rgb(tab_bg)
    screen.cursor.bold = False
    screen.cursor.italic = False

    # Layout: " <glyph> <glyph> ... <glyph>  " (single space between, two at end).
    prefix_cells = 1  # opening space
    screen.draw(" ")
    for i, (sym, color) in enumerate(parts):
        screen.cursor.fg = as_rgb(color)
        screen.draw(sym)
        prefix_cells += wcswidth(sym)
        if i < len(parts) - 1:
            screen.draw(" ")
            prefix_cells += 1
    screen.draw(" ")
    prefix_cells += 1

    # Restore so kitty's renderer applies configured tab font styles.
    screen.cursor.fg, screen.cursor.bg = old_fg, old_bg
    screen.cursor.bold, screen.cursor.italic = old_bold, old_italic

    adjusted_max = max(1, max_title_length - prefix_cells)
    # Strip noisy prompt prefix from the title for display only;
    # the original title is still used as the icon-cache key above.
    display_tab = tab._replace(title=_clean_title(tab.title or ""))
    draw_tab_with_separator(
        draw_data,
        screen,
        display_tab,
        before + prefix_cells,
        adjusted_max,
        index,
        is_last,
        extra_data,
    )

    if tab.is_active:
        screen.cursor.fg = as_rgb(int(draw_data.active_bg))
        screen.cursor.bg = as_rgb(int(draw_data.default_bg))
        screen.draw("\u2588\u258c")  # █▌

    if is_last:
        _draw_right_status(draw_data, screen)

    return screen.cursor.x


# ---------------------------------------------------------------------------
# Right-aligned status.
# ---------------------------------------------------------------------------

def _draw_right_status(draw_data: DrawData, screen: Screen) -> None:
    draw_attributed_string(Formatter.reset, screen)
    cells = _create_cells()

    while cells:
        used = sum(_cell_width(c) for c in cells) + max(len(cells) - 1, 0)
        padding = screen.columns - screen.cursor.x - used
        if padding >= 0:
            break
        cells = cells[1:]
    else:
        return

    if padding:
        screen.draw(" " * padding)

    screen.cursor.bg = as_rgb(int(draw_data.default_bg))
    sep_fg = as_rgb(GRUV_SEP)

    for i, (title, symbol, color) in enumerate(cells):
        if i > 0:
            screen.cursor.fg = sep_fg
            screen.draw("\u2502")  # │
        screen.cursor.fg = as_rgb(color)
        screen.draw(f" {title}")
        screen.cursor.fg = sep_fg
        screen.draw(f" \u27f5 {symbol} ")  # ⟵


def _cell_width(cell: tuple[str, str, int]) -> int:
    title, symbol, _ = cell
    return wcswidth(f" {title} \u27f5 {symbol} ")


def _create_cells() -> list[tuple[str, str, int]]:
    boss = get_boss()
    active = getattr(boss, "active_tab", None)

    username = os.environ.get("USER") or "?"
    hostname = socket.gethostname() or "?"

    cwd = "?"
    if active is not None:
        try:
            cwd = TabAccessor(active.id).active_oldest_wd or "?"
        except Exception:
            cwd = "?"

    if isinstance(cwd, str):
        home = os.path.expanduser("~")
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
        cwd = _shorten_path(cwd, max_len=40)

    return [
        (username, "\uf007", GRUV_PURPLE),  # nf-fa-user
        (hostname, "\uf108", GRUV_BLUE),    # nf-fa-desktop
        (cwd,      "\uf07b", GRUV_AQUA),    # nf-fa-folder
    ]


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------

def _shorten_path(path: str, max_len: int = 40) -> str:
    """Abbreviate intermediate components when path is too long.

    /a/bb/ccc/dddd  ->  /a/b/c/dddd
    ~/foo/bar/baz/qux -> ~/f/b/b/qux  (when it overflows max_len)
    """
    if len(path) <= max_len:
        return path

    # Remember whether path is absolute.
    absolute = path.startswith("/")
    parts = [p for p in path.split("/") if p]
    if not parts:
        return path

    last = parts[-1]
    head = parts[:-1]
    abbreviated = [p[0] for p in head]
    candidate = "/".join(abbreviated + [last])
    if absolute:
        candidate = "/" + candidate
    if len(candidate) <= max_len:
        return candidate

    # Fall back: just the basename, ellipsised if still too long.
    if len(last) > max_len:
        return last[: max_len - 1] + "\u2026"  # …
    return last
