Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.29.2

Status: Active master plan for v0.29.2 / M25 hardening.

v0.29.2 hardens local-dev API authority and raw preview safety before M26. It
keeps M25 Truth Source Router + Evidence Claim Checker as the current
implemented capability layer while closing local review-surface risks.

## Hardening Scope

- Test-prefixed `approval_test_*` refs are no longer fallback authority in Tool
  Broker/kernel mutation paths.
- Public `/kernel/tasks/run` local-dev mutation requests are forced to dry-run
  behavior and must not write files.
- Public file read preview responses are metadata-only by default: size, hash,
  status, and redaction markers are allowed; raw text content is omitted.
- API exception handlers must not echo raw exception strings or hostile invalid
  input values in `safe_message` or `detail`.
- Direct truth validation helpers for memory/model authority boundaries fail
  closed when unsafe refs are passed directly.
- Foundation Gate and `scripts/verify_all.py` include deterministic probes for
  these hardening boundaries.

## Non-Goals

v0.29.2 adds no web search, external verification, autonomous fact checking,
model/provider calls, retrieval/RAG/vector/embedding functionality, source
crawling, memory writes, evidence mutation, Event Ledger mutation, backend
truth verification routes, backend route expansion, dependencies, M26 Grounded
Recall Router, M26 Context Pack Builder, or production authority.

OpenAPI path count remains `74`. M26 remains future as Grounded Recall Router
+ Evidence-Linked Context Pack Builder.
