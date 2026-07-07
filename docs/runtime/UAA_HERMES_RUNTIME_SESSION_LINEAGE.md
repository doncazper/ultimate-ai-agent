# UAA Hermes Runtime Session Lineage

Status: Hermes Runtime Adoption Phase 19 AuthorityState-bound repo-safe read model

## Full-Strength Version

UAA can branch sessions and tasks for alternate approaches, second-opinion
reviews, retries, and comparisons while keeping each branch tied to user
request refs, task refs, run refs, proof refs, reason refs, and rollback or
safe-disable posture.

## Repo-Safe Version

Phase 19 adds Python Core session lineage and fork posture:

- `GET /api/runtime/session-lineage`
- `scripts/dev/uaa_runtime.py inspect-session-lineage`
- `RuntimeSessionLineageReadModel`
- parent/child node refs for user request, coding task, runtime run, proof
  record, review branch, retry branch, and comparison branch posture
- fork refs with explicit operator intent refs, redacted fork-envelope refs,
  retrieval-log refs, compare-view refs, proof refs, verifier refs, and blocked
  authority refs
- AuthorityState route/CLI/mapping/catalog/decision/reason refs and unsupported
  adapter refs for governed lineage inspection

The read model is mapped as `lane-ref:runtime-session-lineage-read-model` under
Read-only `workspace/read` and is evaluated from the active AuthorityLease
decision catalog. This is read-only posture only. It does not clone raw
transcripts, persist raw prompts or responses, inject hidden context into
another runtime, dispatch a runtime, call providers/models, run
shell/subprocess commands, automate browsers, write connectors, or claim
production authority.

## Blocked / Needs Authority

- raw transcript cloning into a new session or runtime
- hidden context transfer
- automatic runtime dispatch for forks
- provider/model calls for reviewer or comparison branches
- shell, browser, connector, or Git mutation from lineage controls
- production authority

## Exact Promotion Path

Future promotion requires a redacted fork envelope, explicit operator intent,
safe refs only, retrieval log refs, proof binding, idempotency, approval scope
validation, safe-disable posture, redaction, CLI/API/Core parity, route
classification updates, and focused verifier coverage. A fork must remain an
inspectable proposal until its exact runtime or provider lane is separately
approved.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_session_lineage.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_19.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```
