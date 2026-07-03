#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROMPT="$ROOT/docs/prompts/authority_graduation_program/00_execute_all_review_fix_merge.prompt.md"
CODEX_BIN="${CODEX_BIN:-codex}"
SANDBOX="${CODEX_AUTH_GRAD_SANDBOX:-workspace-write}"
MODEL_ARG=()

if [[ -n "${CODEX_AUTH_GRAD_MODEL:-}" ]]; then
  MODEL_ARG=(--model "$CODEX_AUTH_GRAD_MODEL")
fi

if [[ ! -f "$PROMPT" ]]; then
  echo "Missing prompt: $PROMPT" >&2
  exit 1
fi

if ! command -v "$CODEX_BIN" >/dev/null 2>&1; then
  echo "Codex CLI not found. Install Codex or set CODEX_BIN=/path/to/codex." >&2
  echo "Prompt to run manually: $PROMPT" >&2
  exit 127
fi

echo "Running Authority Graduation Program prompt pack from:"
echo "  $ROOT"
echo
echo "Prompt:"
echo "  $PROMPT"
echo
echo "Sandbox:"
echo "  $SANDBOX"
echo
echo "This run may create branches, PRs, commits, merges, and pushes if the prompt"
echo "gates pass. Stop now if that is not intended."
echo

"$CODEX_BIN" exec -C "$ROOT" --sandbox "$SANDBOX" "${MODEL_ARG[@]}" - < "$PROMPT"
