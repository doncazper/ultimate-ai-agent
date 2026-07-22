#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERIFY="$ROOT/scripts/verify_uaa_parity_gap_closure_prompt_pack.py"
OUTPUT="${UAA_PARITY_GAP_CLOSURE_OUTPUT:-/tmp/uaa-parity-gap-closure-prompt-pack.md}"
CODEX_BIN="${CODEX_BIN:-codex}"
SANDBOX="${UAA_PARITY_GAP_CLOSURE_SANDBOX:-workspace-write}"
DRY_RUN=0
LIST_ONLY=0
CODEX_ARGS=(exec -C "$ROOT" --sandbox "$SANDBOX")

if [[ -n "${UAA_PARITY_GAP_CLOSURE_MODEL:-}" ]]; then
  CODEX_ARGS+=(--model "$UAA_PARITY_GAP_CLOSURE_MODEL")
fi

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
else
  PYTHON="${PYTHON:-python3}"
fi

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/dev/run_uaa_parity_gap_closure_prompt_pack.sh [options]

Options:
  --dry-run          Verify and emit the combined pack without invoking Codex.
  --list             List ordered prompt files and exit.
  --output PATH      Set the combined prompt output path.
  --help             Show this help.

Environment:
  CODEX_BIN                         Codex CLI binary. Default: codex
  UAA_PARITY_GAP_CLOSURE_MODEL      Optional Codex model argument.
  UAA_PARITY_GAP_CLOSURE_SANDBOX    Codex sandbox. Default: workspace-write
  UAA_PARITY_GAP_CLOSURE_OUTPUT     Combined prompt output path.
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

if [[ "$LIST_ONLY" -eq 1 ]]; then
  "$PYTHON" "$VERIFY" --list
  exit 0
fi

echo "UAA Hermes/OpenClaw parity gap closure prompt pack:"
echo "  repo: repository-root-ref"
echo "  wrapper: docs/prompts/uaa_parity_gap_closure/00_execute_parity_gap_closure_end_to_end.prompt.md"
echo "  combined prompt: configured-output-ref"
echo "  sandbox: $SANDBOX"
echo

if [[ "$DRY_RUN" -eq 1 ]]; then
  "$PYTHON" "$VERIFY" --emit-combined "$OUTPUT"
  echo "Dry run complete. The validated pack was emitted without invoking Codex."
  exit 0
fi

if ! command -v "$CODEX_BIN" >/dev/null 2>&1; then
  echo "Codex CLI not found. Install Codex or set CODEX_BIN=/path/to/codex." >&2
  echo "Wrapper ref: docs/prompts/uaa_parity_gap_closure/00_execute_parity_gap_closure_end_to_end.prompt.md" >&2
  echo "Combined pack: not-emitted" >&2
  exit 127
fi

echo "Running the overlap-aware end-to-end wrapper with Codex."
echo "The wrapper may create, push, review, and merge scoped phase PRs."
echo

"$PYTHON" "$VERIFY" --emit-combined "$OUTPUT" --stream-combined \
  | "$CODEX_BIN" "${CODEX_ARGS[@]}" -
