# Q29 Governed Self-Improvement

Status: implemented proposal-only local contract

Q29 connects accepted, content-free evaluation gaps, Q28 correction decisions,
operator feedback, and verified outcome receipts into deterministic improvement
proposals. It does not create or apply a patch, mutate a target, train a model,
grant approval, promote a proposal, publish Git state, or merge work.

## Contract

`ultimate_ai_agent.core.ecosystem.improvements` owns the Python contract. Each
source binds a receipt ref, exact source revision ref, provenance ref,
source-specific rights posture, rights-evidence ref when permitted, and bounded
evidence refs. Unknown or denied rights fail closed as `blocked_rights`.

A proposal binds its target revision, bounded delta refs, regression refs,
exceptions, rollback plan, review packet, and a separate future change-review
scope. TCB proposals remain inert and explicitly require a dedicated ADR.

Human review can accept a proposal only when a distinct independent reviewer
identity, independent-review evidence ref, and verified-review posture are all
bound for a separately governed change review. Synthetic CLI reviews remain
unverified and blocked. Acceptance is not LocalApprovalAuthority approval and
does not create a ChangeSet or patch. Rejection and supersession remain
immutable review outcomes.

Outcome receipts bind an accepted review receipt, verified implementation
evidence, the exact accepted change scope, target and base revision, implemented
revision, independent review, and one typed result for every planned regression
expectation. A regressed outcome requires both a failed regression result,
revert confirmation, and rollback evidence. Successful or neutral outcomes
become eligible only when every planned regression result passed, and then only
as evidence for a future proposal after fresh rights review; no automatic learning occurs.

## Durability and authority

The reference `ImprovementSession` is process-local, bounded to 256 review and
outcome receipts, idempotent for exact replay, conflict-detecting for changed
payloads, and fail-closed at capacity without eviction. Durable storage, API
routes, Control Center controls, source ingestion, model calls, training,
automatic code changes, background work, Git publication, merge, and external
writes remain outside Q29.

CLI inspection uses only built-in synthetic safe refs:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_governed_improvement.py status
PYTHONPATH=src .venv/bin/python scripts/inspect_governed_improvement.py proposal --rights-unresolved
PYTHONPATH=src .venv/bin/python scripts/inspect_governed_improvement.py review --json
```

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_q29_governed_improvement.py
.venv/bin/python scripts/verify_q29_governed_improvement.py
```
