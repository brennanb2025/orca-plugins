#!/bin/sh
# Prints the 16 terminal colors as swatches, for terminal theme screenshots.
names='black red green yellow blue magenta cyan white'
printf '\n  normal  '
i=0
for name in $names; do printf '\033[4%dm      \033[0m ' "$i"; i=$((i + 1)); done
printf '\n  bright  '
i=0
for name in $names; do printf '\033[10%dm      \033[0m ' "$i"; i=$((i + 1)); done
printf '\n          '
for name in $names; do printf '%-7s' "$name"; done
printf '\n\n'
