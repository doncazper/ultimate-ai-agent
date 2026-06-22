# UAA-P1-078 Private Beta-Readiness Gate

Status: Done for a read-only local/private beta-test readiness evidence gate.
This is not public beta, public distribution, production readiness, broad
autonomy, connector write authority, provider/model authority, action execution,
Code apply authority, memory write authority, account sync, CRM write, or
context injection authority.

## Purpose

UAA-P1-078 turns the Founder Command Center beta-readiness question into a
typed, reviewable evidence contract. The gate answers whether the current
single-user founder loop has local/private beta-test evidence for:

- Today
- Morning Briefing
- Action Inbox
- Memory Review
- Evidence Timeline
- Chat/Plans Handoff
- Governed Code
- CRM-Lite Follow-Ups

The gate distinguishes pass, fail, skipped, blocked, partial, mock-only, and
accepted-failure states.

Canonical state vocabulary: pass, fail, skipped, blocked, partial, mock-only, and accepted-failure.

The current checked-in seed state is intentionally partial, mock-only, and
blocked where evidence is missing. Public beta remains blocked.

## Implemented Contract

Core contract:

- `src/ultimate_ai_agent/core/readiness/private_beta.py`
- `contract-ref:private-beta-readiness-gate:v1`
- `PRIVATE_BETA_READINESS_REQUIRED_SURFACES`
- `PRIVATE_BETA_READINESS_ACCEPTANCE_STATES`
- `PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS`
- `PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS`
- `PrivateBetaReadinessCriterion`
- `PrivateBetaReadinessGate`
- `build_private_beta_readiness_gate`
- `private_beta_readiness_authority_posture`
- `private_beta_readiness_surface_bindings`

Schema and verifier:

- `docs/schemas/private_beta_readiness_gate.schema.json`
- `scripts/verify_uaa_p1_078_private_beta_readiness_gate.py`
- `tests/test_uaa_p1_078_private_beta_readiness_gate.py`

Control Center binding:

- `GET /control-center/today/summary` includes
  `private_beta_readiness_*` fields.
- `GET /control-center/actions/inbox` includes read-only readiness metadata for
  the Action Inbox criterion.
- Evidence Timeline includes `private_beta_readiness_gate_ref` with the history
  grammar: what was proposed, approved, happened, changed, undoable, stale, and
  blocked.
- The React Today surface shows the gate state, evidence packet ref, acceptance
  states, missing evidence refs, and blocked authority refs.

## Gate States

| State | Meaning |
| --- | --- |
| `pass` | Acceptance evidence is present and no blocker remains. |
| `fail` | Evidence contradicts the acceptance criterion. |
| `skipped` | Criterion was intentionally skipped with a safe reason. |
| `blocked` | Required evidence or authority boundary is missing. |
| `partial` | Some evidence exists, but beta-test proof is incomplete. |
| `mock_only` | Only mock or skeleton evidence exists. |
| `accepted_failure` | Known failure is accepted only with documented risk refs. |

## Current Criteria

| Surface | Current state | Required evidence posture |
| --- | --- | --- |
| Today | `partial` | Product spine, blockers, follow-ups, memory refs, and readiness refs are visible; local rehearsal receipts remain missing. |
| Morning Briefing | `mock_only` | Storage-backed skeleton exists; source reads and delivery remain blocked until read-only source contracts land. |
| Action Inbox | `partial` | Reviewable Action envelopes and memory-derived proposals are visible; execution and approval grant capture remain blocked. |
| Memory Review | `partial` | Source, provenance, quality, decision, intake, and loop refs are visible; writes and context injection remain blocked. |
| Evidence Timeline | `partial` | History grammar exists and includes readiness evidence; durable beta-test run receipts remain missing. |
| Chat/Plans Handoff | `partial` | Local operator turn truth and handoff refs exist; model output is not truth, authority, memory, approval, or execution. |
| Governed Code | `partial` | Repo-local proposal, validation, expected apply receipt, and rollback posture refs exist; apply remains blocked. |
| CRM-Lite Follow-Ups | `blocked` | Follow-ups can be represented as memory/action refs only; CRM writes and account sync remain blocked. |

## Authority Boundary

The gate requires these posture flags to remain true:

- `local_private_only`
- `safe_refs_only`
- `review_required`
- `evidence_required`
- `redaction_required`

The gate requires these posture flags to remain false:

- `private_beta_execution_authorized`
- `public_beta_claim_enabled`
- `public_distribution_claim_enabled`
- `production_readiness_claim_enabled`
- `production_authority_enabled`
- `broad_autonomy_enabled`
- `connector_write_enabled`
- `provider_model_authority_allowed`
- `unrestricted_shell_enabled`
- `shell_subprocess_execution_enabled`
- `remote_execution_enabled`
- `account_sync_enabled`
- `crm_write_enabled`
- `memory_write_authorized`
- `automatic_memory_write_authorized`
- `context_injection_authorized`
- `approval_grant_capture_enabled`
- `action_execution_enabled`
- `code_apply_execution_enabled`

## Evidence As History

The Evidence Timeline entry must read like history:

- Proposed: a private local beta-test acceptance gate for the Founder Loop
  surfaces.
- Approved: the evidence gate only, with no public beta, distribution,
  production readiness, write, execution, or autonomy authority.
- Happened: readiness criteria, acceptance states, missing evidence refs, and
  blocked authority refs were produced.
- Changed: no connector, account, CRM, memory, action, Code apply, provider,
  shell, remote, or production state changed.
- Undoable: no rollback execution exists because the gate is read-only metadata.
- Stale: readiness refs must be rechecked after local rehearsals and API
  perimeter hardening.
- Blocked: all blocked authority refs remain visible.

## Tests And Verifiers

Focused checks:

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_078_private_beta_readiness_gate.py`
- `.venv/bin/python scripts/verify_uaa_p1_078_private_beta_readiness_gate.py`

Regression checks:

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_founder_loop_storage.py tests/test_control_center_founder_loop_api.py`
- `make frontend-check`
- `.venv/bin/python scripts/verify_documentation_integrity.py`

## Next Conveyor State

UAA-P1-079 User Intent Understanding V1 is complete in the bounded Today-spine
conveyor. The next documented product lane is UAA-P1-080 API Route
Classification And Public/Protected Inventory, but it remains planned/queued API
boundary-hardening work until a separate scoped prompt starts it. It must not
be treated as route authority, broad autonomy, action execution, memory write
authority, provider authority, connector write authority, public beta,
distribution, or production authority.
