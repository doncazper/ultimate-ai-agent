# FCC Fusion Routing And Delegation

Status: implemented backend-owned readability metadata; no execution authority
Baseline: v0.104.0 / 0.104.0
Contract ref: `contract-ref:fcc-fusion-routing-delegation:v1`

This decision note records the safe Founder Command Center slice for work
classification, route/delegation visibility, cache/context economics refs, and
private dogfood evidence. The lane is subordinate to the Founder Loop V1 proof
path, Action Inbox approval envelopes, Plans-to-Actions bridge, Chat handoff,
Governed Code Workbench, Evidence Timeline, ModelRouter, and CostGovernor.

The implemented slice is review metadata only. It adds no runtime model calls,
no provider SDK calls, no sidekick or worker runtime, no action execution, no
tool execution, no browser or shell execution, no connector runtime or writes,
no memory writes, no context injection, no approval shortcut, no background
dispatch, no public beta claim, no public release claim, and no production
authority.

## Safe Sequence

1. Classify work with bounded values: `judgment_required`, `mechanical`,
   `validation`, `bookkeeping`, `ambiguous`, and `blocked`.
2. Surface ModelRouter-style route decisions as preview/readability metadata:
   selected profile refs, rejected profile refs, reason codes, privacy posture,
   cost posture, context posture, approval posture, and no-execution proof.
3. Propose future-only delegation envelopes for mechanical, validation, or
   bookkeeping work while keeping the main planner responsible for ambiguity,
   significant judgment, plan ownership, and final review.
4. Attach cache/context economics refs that explain context budget, compaction
   boundary, expected cache posture, reroute reason, and cost posture without
   switching models or measuring provider events.
5. Capture private dogfood usefulness evidence as local safe refs and redacted
   summary refs only.
6. Render the backend-owned truth in Control Center surfaces without adding UI
   controls that imply worker start, model invocation, runtime switching,
   approval shortcut, or standing grants.
7. Verify product language and contract invariants with focused tests and
   `scripts/verify_fcc_fusion_routing_delegation.py`.

## Product Truth

Implemented:

- Python Agent Core contracts in
  `src/ultimate_ai_agent/core/control_center/fusion_routing.py`.
- Founder Loop storage projection fields for Today, Plans, Actions, Code, and
  Evidence Timeline readability.
- Control Center rendering for routing/delegation readability where backend
  data exists.
- Focused backend tests and a repo-local verifier.

Proposal-only:

- Delegation envelopes describe possible future roles and receipts. They do not
  create approval refs, execution refs, queues, dispatches, retries, workers, or
  schedules.
- Work classifications help operators review routing and delegation posture.
  They do not authorize work.

Planned:

- Any future runtime delegation lane would need a separate accepted milestone
  with exact scopes, approval boundaries, receipts, rollback/safe-disable
  posture, UI/CLI parity, red-team coverage, and replay/audit proof.

Blocked:

- Provider/model invocation, runtime model switching, sidekick or worker
  execution, action execution, tool execution, shell/browser execution,
  connector writes, memory writes, context injection, background dispatch,
  public distribution, and production authority.

Partial:

- Route visibility is preview/readability metadata only. It can explain known
  ModelRouter and CostGovernor reason codes, but it does not invoke a route,
  validate credentials, fetch pricing, or create spend authority.

Mock-only:

- No mock-only metadata may become product truth. Fallback UI data must fail
  closed if backend-owned fusion routing/delegation fields are missing or unsafe.

## Integration Points

- Action Inbox receives `work_classification`, `delegation_proposal`, and
  `cache_context_economics` fields on backend-owned items.
- Plans-to-Actions bridge items expose the same metadata for reviewable Action
  envelope proposals.
- Governed Code Workbench proposals label validation posture and keep apply
  authority blocked.
- Today summary exposes a fusion routing/delegation read model, surface
  bindings, blocked-state refs, and authority posture.
- Evidence Timeline can show a safe-ref readability item that proves metadata
  exists without claiming delegation, routing, model calls, or action execution
  happened.
- Control Center renders human-readable summaries before refs; raw JSON is not
  the primary operator view.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_fusion_routing_delegation.py -q
.venv/bin/python scripts/verify_fcc_fusion_routing_delegation.py
```

The verifier checks that the read model is backend-owned, safe-ref-only,
blocked for every unscoped authority, bound into Founder Loop storage, and free
of forbidden release/UI claims in the scoped product docs and UI component.

## Rollback

Rollback is to remove the fusion routing/delegation contract fields, Control
Center rendering, this decision note, the focused verifier, and focused tests.
No runtime authority, persistent model/provider state, connector state, memory
state, browser/shell state, or external data is created by this lane.
