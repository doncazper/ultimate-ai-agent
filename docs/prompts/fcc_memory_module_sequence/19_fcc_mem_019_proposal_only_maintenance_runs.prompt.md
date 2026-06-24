# FCC-MEM-019 Proposal-Only Maintenance Runs

Repository: this repository.

Goal: add governed memory quality scans that propose maintenance actions into
reviewable surfaces without applying them. The system may recommend merge,
supersede, forget-request, stale review, missing-evidence repair, or citation
repair, but it must never auto-merge, auto-supersede, auto-forget, auto-write,
delete, inject context, execute actions, or grant production authority.

## Required First Audit

Before editing, inspect:

- `docs/control_center/FCC_HEALTH_001_SELF_HEALING_RECOMMENDATIONS_TO_INBOX.md`
- `docs/control_center/FCC_MEM_001_MEMORY_WORKBENCH.md`
- `docs/control_center/FCC_MEM_015_MEMORY_IMPACT_GRAPH_AND_FOLLOW_UP_QUEUE.md`
- `src/ultimate_ai_agent/core/control_center/health_recommendations.py`
- `src/ultimate_ai_agent/core/memory/workbench.py`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `tests/test_fcc_health_001_self_healing_recommendations_to_inbox.py`

## Implementation Scope

Create a backend-owned proposal-only maintenance scan read model. Prefer:

- `GET /control-center/memory/maintenance-runs`
- CLI: `memory-maintenance-runs`
- contract ref: `contract-ref:fcc-mem-019-proposal-only-maintenance-runs:v1`

The read model must include run ref, scan ref, proposal count, ranked proposals,
source quality issue refs, source citation integrity refs, recommended action
kind, target refs, reason refs, affected surface refs, and blocked-state refs.

Recommended action kinds should include:

- merge
- supersede
- forget_request
- stale_review
- missing_evidence
- citation_repair

## Safety Requirements

The route must be read-only/projection-only and explicitly report:

- `proposal_only=true`
- `auto_merge_authorized=false`
- `auto_supersede_authorized=false`
- `auto_forget_authorized=false`
- `automatic_memory_write_authorized=false`
- `delete_execution_authorized=false`
- `context_injection_authorized=false`
- `production_authority_enabled=false`

## Verification

Add focused tests and a verifier proving proposals are derived from quality and
citation signals, no maintenance action is applied, route/CLI/docs are aligned,
and the Action Inbox/self-healing docs still distinguish proposal from
authority.
