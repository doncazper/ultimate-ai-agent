# North Star Metrics

Status: planning and measurement artifact

These metrics define what the Founder Command Center should optimize after the
first product loop exists. This document does not add analytics SDKs, external
telemetry, tracking, backend routes, Control Center controls, or production
claims. Any measurement implementation must use redacted summaries, safe refs,
local-first storage, and existing evidence boundaries unless separately scoped.

## North Star

Useful actions completed per day.

A useful action is an operator-reviewed outcome that advanced the user's day
and has safe evidence. It may be a completed local scoped action, accepted
draft, resolved follow-up, corrected memory record, reviewed plan, or closed
decision. It is not a raw model response, mock fallback, preview-only route,
or unreviewed automation.

Inferred estimates may use only reviewed outcome metadata, safe summaries, and
safe refs. They must not require raw private content, external telemetry, hidden
tracking, raw calendars, raw messages, raw logs, raw paths, or credential
material.

## Product Metrics

| Metric | Definition | Why it matters | Safety requirement |
|---|---|---|---|
| Useful actions completed per day | Count of reviewed useful outcomes with safe evidence refs. | Measures real work, not surface area. | Count only redacted summaries and refs. |
| Founder Loop V1 receipt carry-through | Count of Today items that become Action envelopes, receive approve/edit/reject/defer decisions, produce durable receipts, and update Evidence Timeline. | Measures whether the first real loop exists end to end before broader expansion. | Use only backend-owned state, receipt refs, idempotency refs, and redacted evidence refs. |
| Primary loop quality before new surfaces | Reviewed quality of Today, Inbox, Plans, Actions, Memory, Evidence, and Settings before adding net-new surfaces. | Prevents breadth from masquerading as product progress. | Safe summaries and refs only. |
| User-approved action rate | Approved exact-scoped action proposals divided by total eligible proposals. | Shows whether proposals are useful and trusted. | Approval refs are identifiers only; no raw content. |
| Time saved per day | User-entered or inferred safe estimate attached to reviewed outcomes. | Captures perceived leverage. | No private calendars/messages required for MVP. |
| Setup clarity score | User-reviewed or checklist-backed signal that setup state, prerequisites, blocked states, and next safe actions are understandable. | Measures low setup pain and coherent first-run experience. | No shell output, raw paths, credentials, or logs required. |
| Action review confidence | Reviewed action proposals marked clear enough to approve, edit, reject, or defer. | Measures beautiful action review before authority expands. | Count only safe summaries and refs. |
| History and reversibility inspection | Evidence timeline or rollback/safe-disable refs inspected for completed scoped outcomes. | Measures whether history and reversibility are understandable. | Safe refs and redacted summaries only. |
| Morning briefing adoption | Days with a reviewed Morning Briefing divided by active days. | Shows whether Today is habit-forming. | Local summary only. |
| Follow-up capture rate | Follow-ups captured from reviewed plans, memory, inbox metadata, or manual entries divided by identified follow-up opportunities. | Measures business memory usefulness. | Safe refs and reviewed memory only. |
| Draft acceptance/edit rate | Accepted or edited draft-only proposals divided by draft proposals. | Shows if draft-only help is useful before send authority exists. | No send/write tracking. |
| Memory correction rate | Corrected/rejected memory candidates divided by reviewed memory candidates. | Measures memory quality and user trust. | Memory remains recall, not authority. |
| Task completion carry-through | Planned tasks that reach reviewed outcome or explicit defer state. | Shows planning quality and follow-through. | Durable run/evidence refs only. |
| Rollback success rate | Scoped local rollbacks that produce reviewed rollback receipt divided by rollback attempts. | Measures recoverability. | Only for scoped local mutation lanes. |
| Zero unsafe authority incidents | Count of authority bypass, raw evidence leak, or unscoped mutation incidents must remain zero. | Safety is a product requirement. | Any incident blocks readiness claims until triaged. |

## Workflow Metrics

### Morning Briefing

- Briefings opened.
- Briefings marked reviewed.
- Priorities accepted, edited, or rejected.
- Blocked states with next safe action.
- Evidence gaps carried forward.

### Inbox And Drafts

- Metadata items reviewed.
- Draft-only proposals created.
- Drafts accepted, edited, rejected, or deferred.
- Connector-write attempts blocked.

### Plans And Actions

- Plans created.
- Plans validated.
- Action proposals generated.
- Action proposals approved, edited, rejected, or expired.
- Safe capability actions with receipts.

### Memory

- Memory candidates created.
- Memory candidates reviewed.
- Corrections applied.
- Rejections and deletion/retention decisions.
- Follow-ups created from reviewed memory.

### Evidence

- Receipts inspected.
- Evidence timeline opened.
- Rollback refs inspected.
- Foundation Gate summaries reviewed.

## Engineering Metrics

| Metric | Definition | Target direction | Safety requirement |
|---|---|---|---|
| First-run setup time | Time from fresh checkout to local Control Center showing safe status. | Down. | Local-only, no credential collection. |
| API p95 latency | p95 for release-critical local API paths. | Within documented budgets. | Do not cache authority decisions. |
| Control Center route success rate | Percent of primary local route reads that render online or correctly degraded state. | Up. | Mock fallback must stay non-authoritative. |
| Mock/degraded state frequency | Frequency of mock fallback, degraded, skipped, or blocked prerequisites. | Down for intended local loop. | Must stay visible. |
| Product-language consistency | Primary surfaces using shared labels for implemented, planned, partial, blocked, skipped, mock-only, missing, approval, evidence, and rollback states. | Up. | Product copy cannot imply unscoped authority. |
| Percent workflows with receipts | Workflow outcomes with receipt/evidence refs divided by completed scoped outcomes. | Up. | Safe refs only. |
| Percent proposed actions with evidence | Action proposals with evidence refs divided by all proposals. | Up. | Evidence must be redacted. |
| Approval bypass test pass rate | Bypass/denial regression tests passing divided by total. | 100 percent. | Required before readiness claims. |
| Redaction test pass rate | Redaction/no-secret-output tests passing divided by total. | 100 percent. | Required before readiness claims. |
| OpenAPI contract drift | Unexpected route count, operation ID, or side-effect class changes. | Zero unexpected drift. | Any drift needs scoped API update. |
| Foundation Gate status | Report-only gate status for scoped changes. | Pass or explicit accepted failure. | No hidden failures. |

## Guardrail Metrics

These must remain zero unless a private security triage record says otherwise:

These zero-incident rules apply to durable evidence, docs, reports, tests,
fixtures, logs, release packets, and product-facing summaries.

- PolicyEngine bypass.
- LocalApprovalAuthority bypass.
- Route side-effect misclassification.
- Raw prompt or raw response in durable evidence.
- Raw provider payload in durable evidence.
- Raw local path in durable evidence.
- Raw log or environment dump in durable evidence.
- Credential or secret-like value in durable evidence, docs, tests, or logs.
- Connector write without exact scoped approval.
- Plugin runtime import without scoped milestone.
- Shell/subprocess authority outside scoped lane.
- Unrestricted browsing or browser automation.
- Mobile sensor/runtime access.

## MVP Measurement Rules

- Prefer local counters and safe summaries over external telemetry.
- Measurements must be reviewable in Evidence.
- Metrics cannot become hidden product authority.
- Metrics must distinguish implemented, planned, partial, blocked, skipped,
  mock-only, and missing states.
- User-entered estimates are allowed only as safe summaries.
- Do not store raw private content to compute metrics.

## Release Evidence Use

For future release candidates, cite these metrics only when they are backed by
tests, safe report refs, evidence packets, or reviewed local summaries. A metric
row by itself is not a readiness claim.
