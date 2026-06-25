# FCC-MEMORY-CRM-001 Professional Memory And CRM-lite Binding

Status: Implemented
Baseline: v0.104.0 / 0.104.0
Primary surfaces: `/today`, `/briefing`, `/actions`, and `/memory`

## Purpose

FCC-MEMORY-CRM-001 binds reviewed professional memory to the daily founder
loop as recall, not truth or authority. Reviewed memory can explain why a
person, relationship, opportunity, commitment, stale follow-up, or draft
opportunity appears, but it cannot silently become hidden context, CRM state,
account sync, or external write authority.

This is a local readability/proposal lane. It is not automatic memory truth,
hidden context injection, external CRM writes, account sync, connector writes,
provider/model calls, background sync, memory delete/export execution, or
production authority.

## Implementation Evidence

- Read surfaces: `GET /control-center/today/summary`,
  `GET /control-center/morning-briefing/summary`, and
  `GET /control-center/actions/inbox`.
- Memory surface: `GET /control-center/memory/review` and the existing
  reviewed-memory/index/context-pack read routes.
- Storage/source: `src/ultimate_ai_agent/core/storage/founder_loop.py`.
- Frontend binding:
  `apps/control-center/src/components/FounderLoopPanels.tsx::CrmLiteFollowUpCards`
  and `MemoryWhyShownCards`.
- Frontend types:
  `apps/control-center/src/api/types.ts::FounderLoopCrmLiteFollowUp` and
  `FounderLoopMemoryWhyShownItem`.
- Verification:
  `scripts/verify_fcc_memory_crm_001_professional_memory_crm_lite_binding.py`,
  `tests/test_fcc_memory_crm_001_professional_memory_crm_lite_binding.py`,
  `tests/test_control_center_api_routes.py`,
  `tests/test_founder_loop_storage.py`,
  `tests/test_founder_loop_storage_safety.py`, and
  `apps/control-center/src/App.test.tsx`.

## Current Truth

Professional memory and CRM-lite bindings expose:

- `CrmLiteRelationshipFollowUp` typed contract rows with
  `contract-ref:relationship-crm-lite-memory:v1`, relationship/person/org/
  project/opportunity/promise refs, reviewed-recall-only posture, redacted
  summary status, and explicit blocked authority flags.
- `crm_lite_followups` with relationship refs, opportunity refs,
  follow-up refs, review envelope refs, memory/source/evidence refs, stale
  review posture, and blocked CRM/account/write authority.
- `memory_why_shown_items` with memory refs, loop item refs, surface, display
  reason, review state, stale state, conflict state, source refs, evidence
  refs, missing evidence refs, and next safe action.
- Review queue groups for memory candidates and draft opportunities.
- Weekly Review carry-forward refs that include stale, blocked, and
  missing-source memory context.

Every memory-derived item remains backend-owned and must carry provenance and
an explicit "why shown" explanation. Candidate, conflict, stale, blocked,
missing-evidence, and draft-only states remain visible instead of being
collapsed into truth.

## Authority Boundary

FCC-MEMORY-CRM-001 does not add automatic memory truth, hidden context
injection, model-output authority, external CRM writes, account sync,
connector writes, background sync, memory delete/export execution, action
execution, public beta, public distribution, production readiness, or
production authority.

CRM-lite bindings are local/read-only/proposal-only until a later accepted
milestone grants a specific mutation lane with exact scope, tests, receipts,
and rollback/safe-disable posture.

## CLI Inspection

Repo-local CRM-lite inspection is available without React:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_relationship_crm_lite_memory.py
```

The command opens existing Founder Loop state in read-only inspection mode,
reports `state_not_found_no_write` when no state exists, and reports
`existing_state_unreadable_redacted` with a safe error ref when local state
cannot be read. It must not seed memory, create storage, write logs, print
tracebacks, or emit raw relationship content, usernames, hostnames, local
paths, raw logs, prompts, responses, provider payloads, credentials, connector
payloads, account IDs, or external CRM records.

## Verification Commands

```bash
.venv/bin/python scripts/verify_fcc_memory_crm_001_professional_memory_crm_lite_binding.py
PYTHONPATH=src .venv/bin/python scripts/inspect_relationship_crm_lite_memory.py >/tmp/uaa_crm_lite_memory.json
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_memory_crm_001_professional_memory_crm_lite_binding.py tests/test_control_center_api_routes.py tests/test_founder_loop_storage_safety.py -q
.venv/bin/python scripts/verify_operational_maturity.py
.venv/bin/python scripts/verify_documentation_integrity.py
make frontend-check
git diff --check
```
