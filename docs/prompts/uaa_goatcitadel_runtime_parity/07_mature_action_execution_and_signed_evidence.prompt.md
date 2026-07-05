# Phase 07: Mature Action Execution And Signed Evidence

Goal: raise UAA's execution readiness by making exact approved action lanes
reviewable, idempotent, receipt-backed, rollback-aware, and portable-evidence
ready without granting broad execution authority.

Reference pattern: GoatCitadel connects runtime plans, approvals, tools, and
evidence into an operator-visible execution spine. Borrow the product loop, not
the authority assumptions.

## Required Work

1. Inspect UAA's Action Inbox, LocalApprovalAuthority, execution lanes, tool
   runtime, receipts, evidence, artifact hashes, redaction, CLI, API, and UI.
2. Choose the smallest existing exact action lane that can safely demonstrate
   mature execution. If no lane is already accepted, implement the blocked
   proposal/readiness surface and exact future graduation prompt instead.
3. Ensure every executable lane requires:
   - exact approval ref;
   - exact action kind;
   - exact resource refs;
   - idempotency key;
   - replay conflict detection;
   - rollback or rollback-readiness posture;
   - safe-disable behavior;
   - receipt/proof refs;
   - route-decision binding;
   - policy decision ref.
4. Implement or harden portable evidence receipts:
   - canonical JSON serialization;
   - stable digest;
   - signature or verifier ref using existing UAA signing/receipt utilities or
     a new local-only testable signer;
   - redacted summary;
   - artifact hashes where relevant;
   - no raw prompt, response, payload, local path, raw log, or secret material.
5. Add CLI/API/Control Center views that show what happened, what was approved,
   what evidence exists, and what remains blocked.
6. Add tests for pass path, missing approval, scope drift, replay conflict,
   safe-disable, rollback posture, redaction, and receipt verification.

## Explicit Non-Goals

- Do not create a broad execution switch.
- Do not execute unapproved actions.
- Do not add unrestricted shell/subprocess execution.
- Do not add connector writes, browser actions, remote execution, or plugin
  runtime execution.

## Acceptance Criteria

- The selected lane is exact-scoped and approval-bound.
- Receipts are portable, verifiable, redacted, and linked to evidence.
- Replays and scope drift fail closed.
- Operator-facing surfaces avoid raw JSON for critical decisions.
- Blocked lanes are labeled honestly instead of hidden.

## Verification

Run focused action/execution/evidence tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_turn_contract_router_executor_fence.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_runtime_replay_protection.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_runtime_authority_boundaries.py -q
```
