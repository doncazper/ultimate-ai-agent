# Founder Command Center Authority Ramp Conveyor

Status: active planning and verifier gate
Baseline: v0.104.0 / 0.104.0
Scorecard: `docs/control_center/authority_candidate_scorecard.json`
Verifier: `scripts/verify_operational_maturity.py`

`FCC-AUTH-RAMP-001` is the repo-owned conveyor for moving future Founder
Command Center authority candidates from visible proposal state to a possible
exact micro-lane. It does not grant authority by itself.

## Conveyor

```text
read-only status
-> proposal-only UX
-> authority candidate ranking
-> one approved micro-lane candidate
-> exact-scoped authority implementation later
```

Every step must preserve the core boundary: Python Agent Core owns behavior;
Control Center and OpenWebUI are shells; approval refs are identifiers until
LocalApprovalAuthority validates exact scope.

## Foundation Lanes

The near-term foundation stays read-only or proposal-only:

| Lane | Current posture | Authority boundary |
|---|---|---|
| Read-only connector metadata | Partial source-readiness posture appears in Today, Morning Briefing, and Action Inbox. | No account auth, polling, raw source reads, send/archive/delete/label/move, calendar write, connector runtime, or connector write. |
| Memory-to-loop proposals | Implemented as reviewed recall refs, memory-derived Action proposal refs, and Weekly Review carry-forward refs. | Memory is recall, not truth or authority. No automatic memory write, context injection, action execution, CRM sync, connector write, or provider/model authority. |
| Context-pack proposal display | Implemented as read-only `/control-center/memory/context-packs` inspection plus Control Center Memory display. | Context packs are proposal refs only. No hidden prompt writing, context injection, provider/model call, connector sync, memory write, or production authority. |

## Authority Candidates

The scorecard ranks these future authority classes:

- connector writes
- memory writes
- shell/subprocess local maintenance
- browser automation
- provider/model authority
- context injection

The scorecard may mark a class as `not_ready`, `proposal_only_ready`,
`contract_ready`, `micro_lane_candidate`, or `blocked_by_policy`.

## Micro-Lane Gate

A candidate may become `micro_lane_candidate` only when all of the following
refs exist and resolve:

- backend/core owner ref
- route side-effect ref
- exact scope ref
- approval plan ref
- idempotency plan ref
- receipt/evidence plan ref
- rollback/safe-disable plan ref
- redaction plan ref
- CLI/API/core parity refs
- focused test refs
- verifier refs

At most one candidate may be selected for the first micro-lane at a time. If no
candidate satisfies the gate, the first micro-lane decision must be `no_go`
with a blocker and smallest next safe action.

## Current Decision

No new authority candidate is selected. The existing Action Inbox
`local_task_create` lane remains the only rank 5 local execution lane. Future
connector writes, memory writes, shell/subprocess work, browser automation,
provider/model authority, and context injection remain blocked until the
scorecard and operational maturity verifier agree that one exact lane is ready.

## Non-Goals

This conveyor does not add generic execution, connector writes,
shell/subprocess execution, provider/model authority, memory writes, context
injection, browser automation, remote execution, plugin runtime import, public
beta, public release, production-readiness claims, or production authority.
