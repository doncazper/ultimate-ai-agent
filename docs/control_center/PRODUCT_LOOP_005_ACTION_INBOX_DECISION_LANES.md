# Product Loop 005 Action Inbox Decision-Lane Polish

Status: implemented as a backend-owned local read model.

Product Loop 005 adds `action_inbox_decision_lane_read_model` to the existing
Action Inbox read route:

```text
contract-ref:product-loop-005-action-inbox-decision-lanes:v1
```

The read model groups Action Inbox items by operator decision posture:

- needs approval
- blocked
- draft-only
- Cost blocked
- No provider authority
- approved / no execution
- rejected
- deferred
- receipt recorded

It is safe-ref-only review metadata. The rule "approval alone does not execute"
remains explicit, and
approval refs remain identifiers until exact backend scope is validated by the
existing authority path. Missing approval envelope, exact scope, idempotency,
expected receipt, rollback, safe-disable, evidence, provider/model, or cost
telemetry fields fail closed into blocked or cost/authority lanes.
Cost labels are accounting readiness only; `Cost approved` and
`Provider/model refs present` do not authorize provider calls, model calls,
frontier routing, connector runtime, action execution, or any mutation.

The companion CLI inspection path is:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_action_inbox_decision_lanes.py
```

Inspection is read-only, safe-ref-only, and redacted. The lane adds no action
execution, connector writes, shell/subprocess execution, browser execution,
provider/model calls, memory writes, hidden context injection, public beta,
distribution, or production authority.

## Required Operator Signals

Every item exposes, when available:

- approval envelope ref and approval scope ref
- expected receipt refs
- evidence refs
- blocked authority refs
- estimated USD and max approved USD
- provider/model safe refs
- metered-unit estimate
- cost estimate, usage capture, budget decision, and cost receipt refs
- Unknown paid cost requiring explicit approval
- rollback and safe-disable refs

Frontier/provider usage claims must remain cost-telemetry bound. If frontier
usage appears without cost estimate, budget decision, captured usage, provider
and model refs, and cost receipt refs, the typed contract rejects the record.
