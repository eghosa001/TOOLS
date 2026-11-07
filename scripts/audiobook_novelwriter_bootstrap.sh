#!/usr/bin/env bash
# Audiobook Studio: idempotent novelWriter setup on persistent Linux desktops.
set -euo pipefail

if command -v novelwriter >/dev/null 2>&1; then
  echo "novelWriter is already available: $(command -v novelwriter)"
  novelwriter --version || true
  exit 0
fi

if ! command -v pipx >/dev/null 2>&1; then
  echo 'pipx is missing. Install it with: sudo apt update && sudo apt install pipx' >&2
  exit 2
fi

if ! getent ahosts pypi.org >/dev/null 2>&1; then
  echo 'Cannot resolve pypi.org; no installation attempted. Retry when this machine has package network access.' >&2
  exit 3
fi

pipx install novelwriter
if ! command -v novelwriter >/dev/null 2>&1 && [[ -x "$HOME/.local/bin/novelwriter" ]]; then
  export PATH="$HOME/.local/bin:$PATH"
fi
if ! command -v novelwriter >/dev/null 2>&1; then
  echo 'Installation may have succeeded, but novelwriter is not on PATH; run pipx ensurepath and reopen the shell.' >&2
  exit 4
fi
novelwriter --version
printf '\nReady. Launch novelWriter on your desktop using: novelwriter\n'
