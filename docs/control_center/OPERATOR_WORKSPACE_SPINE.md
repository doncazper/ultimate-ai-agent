# Operator Workspace Spine

Beta 11 adds a backend-owned read model for the operator workspace cockpit:
workspace status, Git posture, preview status, run logs, and coworker handoff.
It is inspired by coding workbench products, but the current lane is not a
coding IDE, file editor, terminal, Git client, browser controller, or coworker
dispatcher.

## Full-strength version

UAA should eventually give the operator one coherent workspace spine for repo
work: workspace status, Git posture, live preview posture, run logs, proof,
evidence, and coworker handoff state. A future full-strength version may show
changed-file refs, patch proposal refs, command receipts, test receipts,
dev-server manifests, screenshot proof, reviewer handoffs, and branch/PR
posture when each lane has exact authority, redaction, rollback, and receipts.

## Repo-safe beta-11 version

The current implementation exposes `operator_workspace_spine_read_model` from
`GET /control-center/today/summary#operator_workspace_spine`, Proof Detail, and
Trust. It is local read-model data only:

- Workspace status is a safe workspace/ref posture.
- Git posture is a read-only placeholder ref, not live branch or dirty state.
- Preview status is manifest-only posture, not dev-server control.
- Run-log posture is receipt/summary refs only, not raw output.
- Coworker handoff is metadata only, not worker dispatch.

CLI inspection is available through:

```bash
python scripts/inspect_operator_workspace_spine.py
```

Verification is covered by:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_beta_11_operator_workspace_spine.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_beta_11_operator_workspace_spine_verifier.py
.venv/bin/python scripts/verify_beta_11_operator_workspace_spine.py
```

## Blocked / needs authority

The lane does not add file writes, patch apply, Git mutation, shell/subprocess
execution, browser automation, dev-server start/stop, provider/model calls,
connector writes, coworker dispatch, background autonomy, raw path persistence,
raw log persistence, public release, or production authority.

No route is added for `/control-center/git/commit`,
`/control-center/git/push`, `/control-center/workspace/apply`,
`/control-center/workspace/run`, or `/control-center/coworker/dispatch`.

## Exact promotion path

Promote one authority lane at a time. Each promotion needs Python Core
ownership, route classification if a route is added, OpenAPI/API manifest
truth, CLI inspection, exact `LocalApprovalAuthority` scope for mutations,
idempotency, redacted receipt/evidence/proof refs, rollback/safe-disable,
product-language updates, focused backend/frontend tests, Foundation Gate, and
release-surface verification.

Recommended next promotions are:

- Exact Git status read contract with redacted branch/status summary refs.
- Dev-server manifest read contract without start/stop authority.
- Allowlisted command/test receipt lane with bounded redacted output.
- Coworker handoff receipt lane without autonomous dispatch.
