#!/bin/zsh
line=$(fzf --no-sort --no-mouse --exact -i --tac)
[ -z "$line" ] && exit
clear
printf "%s\n\n\033[2m── select text with mouse to copy · q or Enter to close ──\033[0m\n" "$line"
while IFS= read -rsk1 key; do
  case "$key" in
    q|$'\n'|$'\r') break ;;
  esac
done
