# Phase 01: Work Board Read Model And CLI

Goal: Ensure the Kanban Work Board is backed by Python Agent Core read-model
truth with safe refs, honest blocked authority posture, API exposure, and CLI
inspection.

Required scope:
- A backend-owned `WorkBoardReadModel` that includes board, column, card,
  blocked-lane, drag/drop posture, proof, evidence, redaction, CLI, frontend,
  backend route, full-strength goal, repo-safe scope, and promotion-path refs.
- A read-only API route for the Work Board.
- A CLI inspection command that prints the safe read model.
- Validators or tests that reject raw paths/content, durable mutation flags,
  shell/browser/provider/connector/background/production authority, and card
  mutation flags.
- Route manifest/OpenAPI/release-surface behavior aligned with the read-only
  local-sensitive route posture.

Non-goals:
- No durable board mutation.
- No issue tracker or connector writes.
- No provider/model calls.
- No shell/subprocess execution.
- No browser automation as UAA product behavior.
- No background workers or autonomous agent dispatch.
- No public beta/release/production claims.

Acceptance:
- `GET /control-center/work-board` returns safe backend-owned Work Board data.
- `scripts/dev/uaa_work_board.py inspect-board` returns the same safe refs.
- Tests prove route, CLI, validators, redaction posture, and blocked authority.
