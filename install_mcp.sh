#!/usr/bin/env bash
# shellcheck disable=SC2034
help='
Download, install, and register VModal MCP with Claude Code or Codex.
Requires Python 3.10+ with pip, git, curl, and the selected client CLI.
Uses the active Python environment; no virtual environment is created.

## Usage:
  bash install_mcp.sh claude [API_KEY]
  bash install_mcp.sh codex [API_KEY]

## Examples:
  curl -fsSL https://raw.githubusercontent.com/v-modal/vmodal_mcp/refs/heads/main/install_mcp.sh | bash -s -- claude
  curl -fsSL https://raw.githubusercontent.com/v-modal/vmodal_mcp/refs/heads/main/install_mcp.sh | bash -s -- codex
  export api_key=PUT_API_KEY_HERE
  bash install_mcp.sh codex

Provide API_KEY, export api_key, or enter your key at the terminal prompt.
Set PYTHON_BIN to select an existing Python installation.
'
set -euo pipefail

mcp_bootstrap() {
  local help='
  ## Usage:
    bash install_mcp.sh claude
    bash install_mcp.sh codex API_KEY
  '
  local client="$1" cmd key dep
  case "$client" in
    claude) cmd=claude_code ;;
    codex) cmd=codex ;;
  esac
  for dep in curl git "$client"; do
    if ! command -v "$dep" >/dev/null 2>&1; then
      echo "Error: $dep was not found. Install it and re-run." >&2
      return 1
    fi
  done
  key="${2:-${api_key:-}}"
  if [ -z "$key" ]; then
    if ! { IFS= read -r -s -p 'VModal API key: ' key </dev/tty; }; then
      echo "Error: provide API_KEY or export api_key before running the installer." >&2
      return 1
    fi
    printf '\n' >&2
  fi
  if [ -z "$key" ] || [ "$key" = PUT_API_KEY_HERE ]; then
    echo "Error: provide a valid VModal API key." >&2
    return 1
  fi

  # Keep the downloaded helper outside any checkout so it installs the public
  # Git package instead of selecting the editable development installation.
  mcp_tmp="$(mktemp -d "${TMPDIR:-/tmp}/vmodal-mcp.XXXXXX")"
  trap 'rm -rf -- "$mcp_tmp"' EXIT
  curl -fsSL https://raw.githubusercontent.com/v-modal/vmodal_mcp/refs/heads/main/install.sh \
    -o "$mcp_tmp/install.sh"
  api_key="$key" bash "$mcp_tmp/install.sh" "$cmd"
  echo "VModal MCP installed for $client. Restart your assistant to use it."
}

case "${1:-help}" in
  claude|codex)
    if [ "$#" -gt 2 ]; then
      echo "$help" >&2
      exit 1
    fi
    mcp_bootstrap "$@"
    ;;
  help|-h|--help) echo "$help" ;;
  *) echo "$help" >&2; exit 1 ;;
esac
