#!/usr/bin/env bash
set -euo pipefail

# Load shell env if available so the MiniMax key can be sourced from the user's shell setup.
if [ -f "$HOME/.bashrc" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.bashrc" >/dev/null 2>&1 || true
fi

: "${OPENCODE_GO_API_KEY:?OPENCODE_GO_API_KEY is not set}"

export CLAUDE_CODE_SIMPLE="${CLAUDE_CODE_SIMPLE:-1}"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="${CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC:-1}"

exec /home/newadmin/.vscode/extensions/anthropic.claude-code-2.1.112-linux-x64/resources/native-binary/claude "$@"
