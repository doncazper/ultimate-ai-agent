# UAA-P1-070 Memory Source And Provenance Model

Status: Done

Contract ref: `contract-ref:memory-source-provenance:v1`

## Purpose

UAA-P1-070 defines the source/provenance envelope every Founder Loop memory
candidate must carry before later review decisions can become credible. The
contract keeps memory useful across manual notes, external assistant review
summaries, local chat summaries, local coding summaries, task plans, action
proposals, evidence timeline refs, read-only calendar/email metadata refs, and
CRM-lite business records without treating any source as truth or write
authority.

## Required Source Kinds

- `manual_note`
- `external_assistant_review_summary`
- `local_chat_summary`
- `local_coding_summary`
- `task_plan`
- `action_proposal`
- `evidence_timeline_ref`
- `read_only_calendar_metadata_ref`
- `read_only_email_metadata_ref`
- `crm_lite_business_record`

Each source kind is an origin kind, not a recall rank, truth rank, provider
rank, or connector authority grant.

## Required Posture

Every memory source/provenance ref requires:

- `contract-ref:memory-source-provenance:v1`
- A structured source ref and provenance ref
- A safe label or redacted summary ref
- Evidence refs and source-readiness refs when available
- `review_required=true`
- `trust_posture=untrusted_until_reviewed`
- `redaction_status=redacted_summary_only`
- Stale-state and blocked-state posture
- Reason codes that explain why the candidate is safe to inspect but not
  authority

The Today summary exposes the contract through
`GET /control-center/today/summary` so Memory Review, Evidence Timeline, and
the Founder Loop surface share the same source/provenance truth.

## Denied Content Refs

The durable contract uses denied-content refs instead of storing private source
bodies:

- `denied-content-ref:prompt-body`
- `denied-content-ref:response-body`
- `denied-content-ref:provider-body`
- `denied-content-ref:local-path`
- `denied-content-ref:log-body`
- `denied-content-ref:account-identifier`
- `denied-content-ref:username`
- `denied-content-ref:hostname`
- `denied-content-ref:credential`
- `denied-content-ref:token`
- `denied-content-ref:private-content`

Legacy `MemorySourceRef` validation now rejects unsafe provenance markers when
the validation path is used, while the stricter beta contract lives in
`core.memory.source_provenance`.

## Denied Authority

All source/provenance candidates must keep these authorities false:

- Source truth authority
- Memory write authority
- Automatic memory write authority
- Context injection authority
- Connector runtime authority
- Account auth authority
- Provider/model authority
- Public beta claim authority
- Public distribution claim authority
- Production authority

Source refs help the user review a candidate. They do not write memory, inject
context, fetch accounts, sync connectors, call models, authorize actions, or
publish release claims.

## Out Of Scope

No review decision capture, accept/correct/reject/defer, merge, supersede,
forget, memory writes, memory deletes, exports, retention execution, context
injection, connector runtime/fetch/auth, browser import, external assistant
import, model/provider calls, cross-surface intake, CRM sync, quality scoring,
dedupe controls, conflict resolution, or recall/truth ranking changes are
included in UAA-P1-070.

UAA-P1-071 owns Memory Review Decision Capture.

## Verification

- `tests/test_uaa_p1_070_memory_source_provenance_model.py`
- `tests/test_founder_loop_storage.py`
- `tests/test_control_center_founder_loop_api.py`
- `scripts/verify_uaa_p1_070_memory_source_provenance_model.py`
- `docs/schemas/memory_source_provenance.schema.json`
