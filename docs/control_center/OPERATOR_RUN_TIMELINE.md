# Operator Run Timeline

Status: implemented as a read-only nested read model on
`GET /control-center/evidence/timeline`.

Contract ref: `contract-ref:operator-run-timeline:v1`

Cost telemetry contract ref:
`contract-ref:frontier-ai-cost-usage-telemetry:v1`

## Purpose

The Operator Run Timeline gives the Founder Command Center one shared run spine
for Today, Plans, Action Inbox, Memory, Evidence, and Settings without adding a
new route or granting new runtime authority. It is derived from the Python core
Evidence Timeline read model and remains safe-ref and redacted-summary only.

## Borrowed Patterns

The implementation keeps the five borrowed OpenHands-style patterns visible as
explicit contract data:

- `typed_event_ledger`
- `run_control_states`
- `evidence_based_completion`
- `approval_preview_and_rejection_feedback`
- `evidence_condensing_with_safe_refs`

These patterns are represented as read-only posture and evidence fields. They do
not authorize execution, connector writes, provider SDK calls, model calls,
rollback, browser activity, or production authority.

## Frontier AI Cost Slots

Frontier AI usage is tracked as accounting slots, not provider execution. The
current contract records:

- provider and model refs as `not-invoked` until scoped authority exists
- estimated and captured USD totals
- input, output, and total metered units
- cost governor and budget status refs
- cost estimate, captured usage, budget decision, and safe provider/model refs
- cost receipt refs and cost blocked-state refs
- unknown paid cost requiring approval before routing

Prompt content, response content, and provider exchange content are not stored in
the timeline.

Unknown paid cost, estimated cost above the approved max, missing provider/model
refs, and claimed frontier usage without cost receipt refs are blocked states.
Approval envelopes carry estimated USD, max approved USD, provider/model refs,
metered-unit estimates, and explicit unknown-paid-cost approval posture so cost
is part of approval scope rather than side metadata.

## UI Surfaces

The Control Center renders a compact Operator Run Timeline summary in the shared
Founder loop spine and a fuller panel on Evidence. The UI shows state counts,
borrowed pattern refs, cost telemetry, and blocked authority refs as inspection
data only.

Action Inbox and plan/action-envelope cards show `Cost blocked`, `Cost approved`,
`Unknown paid cost`, and `No provider authority` states before approval. The
Action Inbox approval and local-task commit controls are disabled when the
backend read model reports a blocked or missing cost posture.

## CLI And Verifier

The repo-local CLI inspection path is:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_operator_run_timeline.py
```

The dedicated enforcement verifier is:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_operator_run_timeline_enforcement.py
```

The verifier fails if frontier usage appears without cost telemetry, unknown
paid cost is not approval-bound, provider/model authority is implied without
scope, or prompt/response/provider exchange content is stored in the timeline.

## Non-Goals

- No new OpenAPI route.
- No runtime model calls.
- No provider SDK calls.
- No connector writes.
- No browser automation.
- No action execution or rollback execution.
- No production authority.
