#!/bin/bash

# Read JSON input
input=$(cat)

# Extract data from JSON
cwd=$(echo "$input" | jq -r '.workspace.current_dir')
session_name=$(echo "$input" | jq -r '.session_name // empty')
model_name=$(echo "$input" | jq -r '.model.display_name')
context_remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')

# Gruvbox colors (dimmed for status line)
color_orange="\033[38;2;214;93;14m"
color_yellow="\033[38;2;215;153;33m"
color_aqua="\033[38;2;104;157;106m"
color_blue="\033[38;2;69;133;136m"
color_bg1="\033[48;2;60;56;54m"
color_fg0="\033[38;2;251;241;199m"
color_green="\033[38;2;152;151;26m"
color_reset="\033[0m"

# Build status line
printf "${color_orange}"

# OS icon
printf "󰀵 "

# Username
printf "$(whoami) "

# Directory - truncate to 3 levels
dir_truncated=$(echo "$cwd" | awk -F/ '{
    n=NF;
    if (n<=3) print $0;
    else printf "…/%s/%s/%s", $(n-2), $(n-1), $n
}')
printf "${color_yellow} $dir_truncated ${color_reset}"

# Git branch (if in git repo)
if git rev-parse --git-dir > /dev/null 2>&1; then
    branch=$(git -c core.fileMode=false -c core.fsmonitor=false rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ -n "$branch" ]; then
        printf "${color_aqua}  $branch${color_reset}"
        
        # Git status indicators
        if [ -n "$(git -c core.fileMode=false -c core.fsmonitor=false status --porcelain 2>/dev/null)" ]; then
            printf "${color_aqua} *${color_reset}"
        fi
    fi
fi

# Model and context info
printf "${color_blue}  $model_name${color_reset}"
if [ -n "$context_remaining" ]; then
    printf "${color_blue} ($(printf '%.0f' "$context_remaining")%%)${color_reset}"
fi

# Session name if set
if [ -n "$session_name" ]; then
    printf "${color_bg1}${color_fg0}  $session_name ${color_reset}"
fi

printf "\n"
