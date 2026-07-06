#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROMPT="$ROOT/docs/prompts/coding_pair_agent_relay_runner/00_execute_coding_pair_agent_relay_runner_end_to_end.prompt.md"
VERIFY="$ROOT/scripts/verify_coding_pair_agent_relay_runner_prompt_pack.py"
OUTPUT="${CODING_PAIR_AGENT_RELAY_OUTPUT:-/tmp/coding-pair-agent-relay-runner-prompt-pack.md}"
CODEX_BIN="${CODEX_BIN:-codex}"
SANDBOX="${CODING_PAIR_AGENT_RELAY_SANDBOX:-workspace-write}"
DRY_RUN=0
LIST_ONLY=0
MODEL_ARG=()

if [[ -n "${CODING_PAIR_AGENT_RELAY_MODEL:-}" ]]; then
  MODEL_ARG=(--model "$CODING_PAIR_AGENT_RELAY_MODEL")
fi

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
else
  PYTHON="${PYTHON:-python3}"
fi

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/dev/run_coding_pair_agent_relay_runner_prompt_pack.sh [options]

Options:
  --dry-run       Verify the pack and emit a combined prompt without Codex.
  --list          List ordered prompt files and exit.
  --output PATH   Combined prompt output path for review/dry-run.
  --help          Show this help.

Environment:
  CODEX_BIN                         Codex CLI binary. Default: codex
  CODING_PAIR_AGENT_RELAY_MODEL     Optional Codex model argument.
  CODING_PAIR_AGENT_RELAY_SANDBOX   Codex sandbox. Default: workspace-write
  CODING_PAIR_AGENT_RELAY_OUTPUT    Combined prompt output path.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --list)
      LIST_ONLY=1
      shift
      ;;
    --output)
      if [[ $# -lt 2 ]]; then
        echo "--output requires a path" >&2
        exit 2
      fi
      OUTPUT="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$PROMPT" ]]; then
  echo "Missing prompt: $PROMPT" >&2
  exit 1
fi

if [[ "$LIST_ONLY" -eq 1 ]]; then
  "$PYTHON" "$VERIFY" --list
  exit 0
fi

"$PYTHON" "$VERIFY" --emit-combined "$OUTPUT"

echo "Coding Pair Agent Relay Runner prompt pack:"
echo "  repo: $ROOT"
echo "  prompt: $PROMPT"
echo "  combined prompt: $OUTPUT"
echo "  sandbox: $SANDBOX"
echo

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run complete. The prompt pack was validated and emitted without invoking Codex."
  exit 0
fi

if ! command -v "$CODEX_BIN" >/dev/null 2>&1; then
  echo "Codex CLI not found. Install Codex or set CODEX_BIN=/path/to/codex." >&2
  echo "Validated prompt to run manually: $PROMPT" >&2
  echo "Combined prompt for review: $OUTPUT" >&2
  exit 127
fi

echo "Running the end-to-end Coding Pair Agent Relay Runner wrapper prompt with Codex."
echo "Stop now if you do not want Codex to implement, verify, and harden changes."
echo

"$CODEX_BIN" exec -C "$ROOT" --sandbox "$SANDBOX" "${MODEL_ARG[@]}" - < "$PROMPT"

