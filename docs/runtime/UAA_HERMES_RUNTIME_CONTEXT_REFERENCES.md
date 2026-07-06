# UAA Hermes Runtime Context References

Status: Hermes Runtime Adoption Phase 16 repo-safe read model

## Full-Strength Version

UAA can let an operator compose task context from file, folder, diff, URL
evidence, run, proof, task, memory, CRM object, and issue refs. A future lane
can retrieve, redact, preview, approve, attach, receipt, and prove context-pack
materialization without turning context into hidden prompt injection or runtime
authority.

## Repo-Safe Version

Phase 16 adds a Python Agent Core read model for governed context references:

- `GET /api/runtime/context-references`
- `scripts/dev/uaa_runtime.py inspect-context-references`
- `RuntimeContextReferencePostureReadModel`
- safe-ref grammar for file, folder, diff, URL evidence, run, proof, task,
  memory, CRM object, and issue refs
- per-ref safe summaries and why-included refs
- preview availability and blocked ref posture
- token budget limit, estimate, remaining budget, and budget-state ref
- blocked live URL fetch, raw path persistence, raw file content persistence,
  secret/config reads, and automatic context injection

This is inspection metadata only. It does not fetch URLs, persist raw paths or
raw file contents, read secret/config material, inject context into runtime
turns, call providers/models, write connectors, run shell commands, perform
browser automation, or claim production authority.

## Blocked / Needs Authority

- live URL fetch
- raw path persistence
- raw file-content persistence
- automatic or hidden context injection
- secret/config reads
- provider/model context expansion
- connector-derived context writes
- shell/subprocess file reads
- browser/web-derived context collection
- production authority

## Exact Promotion Path

Future promotion requires source-specific policy, source-specific redaction,
bounded previews, explicit operator approval, retrieval logs, context-pack
receipts, proof refs, safe-disable posture, rollback or rollback-readiness
posture, CLI/API/Core parity, route classification updates, and focused tests
that prove context can only be attached through the exact approved lane.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_context_references.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_16.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```
