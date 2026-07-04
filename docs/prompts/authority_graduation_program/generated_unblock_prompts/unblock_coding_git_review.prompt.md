# Unblock Coding Git Review

Goal:
Implement exactly one read-only Coding Cockpit Git review lane with status,
diff, changed-file refs, redaction, receipts, CLI parity, and Proof Detail
binding. Keep Git mutation as a separate later exact-approval lane.

Branch:
`codex/unblock-coding-git-review`

Read first:

- `AGENTS.md`
- `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`
- `docs/control_center/authority_graduation_blockers/coding_git_review_2026_07_04.md`
- `src/ultimate_ai_agent/core/code/coding_cockpit.py`
- `src/ultimate_ai_agent/core/execution/durable_runs.py`
- `src/ultimate_ai_agent/core/execution/run_storage.py`

Hard rules:

- Do not broaden authority beyond exact read-only Coding Git review.
- Do not add stage, commit, push, PR open, merge, tag, release, arbitrary shell,
  installs, network commands, destructive commands, background processes,
  provider/model calls, browser automation, connector writes, public release, or
  production authority.
- Do not persist raw prompt, response, provider payload, raw local path, raw Git
  output, raw diff, credential material, account data, environment dumps, or
  private data.
- Python Agent Core owns durable truth.
- Control Center only renders backend-owned state and initiates exact approved
  requests.

Implementation scope:

1. Add exact read-only Git status contract with bounded output and safe refs.
2. Add exact read-only Git diff contract with redaction and safe file/hunk refs.
3. Add changed-file refs without raw local paths.
4. Add commit proposal and pull-request description proposal artifacts over safe
   summaries only.
5. Add Git read receipts with evidence and proof refs.
6. Add safe-disable posture and idempotency refs.
7. Add CLI inspection for readiness, Git read receipts, and blocked mutation
   posture.
8. Add frontend display only when backend read models prove exact read authority.
9. Keep stage, commit, push, PR open, merge, tag, and release blocked unless a
   separate later mutation lane is explicitly scoped.
10. Update route status, release surface, OpenAPI/API manifest tests, docs, and
    verifiers.

Acceptance:

- Only exact read-only Git status and diff operations can run.
- Raw Git output, raw diff, and raw local paths are redacted or omitted from
  durable artifacts.
- Git mutation remains blocked.
- Receipts prove status using safe refs and bounded summaries only.
- Mock fallback and missing backend state cannot expose Git controls.
- All broad runtime authority remains blocked.
- Focused tests and required verifiers are green.
