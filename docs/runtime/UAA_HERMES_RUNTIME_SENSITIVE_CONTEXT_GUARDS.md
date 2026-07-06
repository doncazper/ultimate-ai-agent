# UAA Hermes Runtime Sensitive Context Guards

Status: Hermes Runtime Adoption Phase 17 repo-safe hardening

## Full-Strength Version

UAA blocks credential-bearing and private context across file, folder, diff,
search, runtime, memory, CRM, issue, and delegated-runtime adapters before any
context can become a preview, context pack, runtime turn input, or action input.

## Repo-Safe Version

Phase 17 adds shared Python Core sensitive-context classification for runtime
context references and session-search attachable context refs. It emits only
hash-backed safe candidate refs, reason refs, blocked authority refs, and
redaction refs. The candidate itself is not persisted by the classifier.

Current guarded surfaces:

- `RuntimeContextReferencePostureReadModel`
- `RuntimeSessionSearchReadModel`
- `GET /api/runtime/context-references`
- `GET /api/runtime/session-search`
- `scripts/dev/uaa_runtime.py inspect-context-references`
- `scripts/dev/uaa_runtime.py inspect-session-search`

The guard blocks protected config markers, hidden local path segments, absolute
local path markers, home-relative path markers, traversal markers, encoded
unsafe path markers, protected file suffixes, and credential-bearing markers.

This is guard metadata only. It does not add file reads, raw path persistence,
raw file-content persistence, context retrieval, context-pack materialization,
automatic context injection, provider/model calls, connector writes,
shell/subprocess execution, browser automation, bypass execution, or production
authority.

## Blocked / Needs Authority

- bypass exceptions without exact operator approval and proof
- raw or protected context preview persistence
- context retrieval from local files or live URLs
- context injection into model/runtime turns
- source-specific allowlists without redaction and receipts
- broad runtime adapter context reads
- production authority

## Exact Promotion Path

Future promotion requires a narrow source allowlist, redacted preview contract,
approval reason, time-bound grant, receipt, verifier, safe-disable posture,
route classification review, CLI/API/Core parity, and proof refs. Approval refs
must validate the exact context source and cannot grant broad bypass authority.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_sensitive_context_guards.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_17.py
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_16.py
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_12.py
```
