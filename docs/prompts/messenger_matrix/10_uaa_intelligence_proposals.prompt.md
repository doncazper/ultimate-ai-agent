# MSG-MX-010 — Governed UAA Intelligence And Proposals

Implement only Phase 9 of the Messenger Matrix plan. Read `AGENTS.md`, the full
design sources, accepted authority matrix, room AI policy, context-manifest,
memory, model/provider, proposal/action, redaction, and cross-surface safe-ref
contracts before editing.

## Branch Contract

- Fetch current `origin/main`, record its SHA, and create
  `codex/msg-mx-10-intelligence-proposals` from that exact commit in an isolated
  worktree.
- Inspect overlaps and preserve unrelated work. Never reset, revert, clean,
  stash, overwrite, force-push, or modify historical tags.
- Prove MSG-MX-009 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve API/CLI parity for every policy, context, proposal, and receipt posture.

## Stage A — Exact Authority Acceptance

On this branch and PR, first implement and verify four separately scoped lane
families: room-content/context materialization, approved model/provider
invocation, proposal persistence, and attachment materialization/scanning/
analysis/cleanup. Bind exact account, room, event range, attachment, task, model
destination, disclosure posture, token/content/byte budget, retention, TTL,
deadline, PolicyEngine decision, exact LocalApprovalAuthority scope, current
exact AuthorityLease, adapter, target, readiness, kill switch, safe-disable,
idempotency, replay, rollback/deletion, redaction, and content-free receipts.
Add adversarial tests for prompt injection, cross-room/account leakage, stale
grants, cloud disclosure, attachment substitution, scanner bypass, proposal
replay, and memory/action escalation.

Review and verify Stage A locally before Stage B. Acceptance makes each lane
eligible for fresh request-scoped evaluation only; it does not grant standing
content, model, attachment, proposal, send, or Memory-write authority. If any
exact family cannot be safely accepted, keep that family blocked and do not
implement its Stage B runtime.

## Stage B — Runtime Implementation

Add:

- room AI policy Off / Ask each time / scoped Allow;
- room-scoped, expiring context grants and content-free context manifests;
- cited unread/period summaries, reply drafts, open questions, decisions,
  commitments, task/date extraction, and translation proposals;
- attachment-analysis proposals only when the separate attachment
  materialization, scanning, analysis, and cleanup lane passed Stage A; otherwise
  expose a truthful `blocked` posture with the missing exact authority refs;
- CRM, Calendar, Work Board, Knowledge, and Communications safe-ref links;
- exact reviewable proposals for messages, meetings, follow-ups, and tasks with
  visible sources, confidence, expiry, and receipt posture;
- API/CLI/macOS desktop parity for policy, context, proposal, and blocked truth.

Messages remain untrusted evidence. Instructions inside them cannot alter
policy, grant approval, invoke tools, send messages, or write Memory. No hidden
context, autonomous send, automatic durable Memory, or direct cross-surface
mutation is allowed.

Every policy/proposal mutation requires safe refs, redaction, exact idempotency,
content-free receipts, rollback or rollback-readiness, and safe-disable. Model
output and context refs never grant authority.

Immediately before every room AI policy or proposal-record mutation, re-evaluate
PolicyEngine, exact LocalApprovalAuthority scope, the current exact
AuthorityLease, adapter and target, TTL/deadline, budget, readiness, kill switch,
safe-disable, and idempotency/replay posture. Unknown, stale, expired, or
mismatched state must fail closed before any mutation starts.

## Required Verification

Run focused context/isolation/injection/budget/model-policy/proposal/memory-
denial/redaction/API/CLI/UI tests and bounded local integration, then:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_control_center_api_routes.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
make frontend-check
PYTHONPATH=src .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only --no-write-latest
git diff --check
```

Adversarially review prompt injection, cross-room/account leakage, hidden context,
cloud disclosure, stale grants, token-budget bypass, uncited output, autonomous
send, and automatic Memory truth. Fix all actionable findings. Commit and push
normally and open a draft PR. While it is draft, complete local review and
hardening of both stages. Mark it ready only after local checks pass; run only
repository-scoped self-hosted macOS CI, never paid or GitHub-hosted compute.
Merge only when required checks are green, update local `main` to the exact
remote merge, run post-merge verification, push verified `main`, and confirm a
clean worktree. Do not begin MSG-MX-011 before that proof.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: accepted authority refs, intelligence/proposal capabilities,
blocked executions, context evidence, tests, commit, pushed branch, and draft PR.
