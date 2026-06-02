# Foundation Gate Implementation Plan v0.21.0

Status: Historical Foundation Gate implementation plan for v0.21.0.

v0.21.0 adds Foundation Gate coverage for M17 Evidence/File/Memory Viewer safety.

## Skill Package Security Rule

v0.21.0 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

Criterion:

- `m17_evidence_file_memory_viewer_safe`

Evaluator:

- `FoundationGateEvaluator.check_m17_evidence_file_memory_viewer_safe`

The evaluator checks:

- M17 evidence, file ref, and memory viewer component files exist.
- `/evidence`, `/files`, and `/memory` frontend routes are present.
- viewer headings and M17 knowledge surface copy are present.
- evidence, file ref, and memory views are read-only and summary-only.
- memory is recall, not authority, and canonical files plus governed source systems outrank memory.
- safe mock evidence, file, memory, event, receipt, and relation refs exist.
- raw prompt, file, memory, evidence, provider, secret, and credential-like knowledge fields are rejected.
- private path fragments are rejected in M17 mock knowledge fixtures.
- file mutation, memory mutation, filesystem browsing, execution, browser storage, credential field, and dangerous control fragments are absent from app implementation files.
- OpenAPI path count remains `74`.
- backend evidence/raw, file write/delete/content, filesystem browse, and memory raw/write/delete/learn/forget routes are absent.
- `scripts/verify_control_center_frontend.py` passes.
- docs for Evidence Viewer, File Reference Viewer, Memory Viewer, and M17 safety exist.

This gate does not add runtime execution, backend routes, model/provider calls, remote dispatch, mobile sensor access, plugin enablement, native build workflows, raw payload display, or production Control Center authority.
