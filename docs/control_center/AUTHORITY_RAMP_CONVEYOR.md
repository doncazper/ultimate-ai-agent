# Founder Command Center Authority Graduation Program

Status: active planning and verifier gate
Baseline: v0.104.0 / 0.104.0
Scorecard: `docs/control_center/authority_candidate_scorecard.json`
Verifier: `scripts/verify_operational_maturity.py`

`FCC-AUTH-RAMP-001` is the repo-owned Authority Graduation Program for moving
one exact Founder Command Center authority lane at a time from visible proposal
state to a possible exact micro-lane. It does not grant authority by itself.
The file path is retained for compatibility with existing verifier and manifest
refs.

## Program Sequence

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

## Fixed First Implementation Lane

The first implementation lane is fixed and may not be substituted:

```text
read_only_real_world_web_fetch through WebAccessGateway
```

This lane is narrower than the follow-on authority candidate set. It may only
scope HTTPS GET through `WebAccessGateway`, explicit public allowlist, bounded
redacted preview, gateway audit/request refs, and blocked labels for every
disallowed capability. It must not add browser observe, browser action dry-run,
provider SDK calls, connector reads or writes, authenticated sessions,
downloads/uploads, POST/PUT/PATCH/DELETE, memory writes, context injection,
action execution, generic browsing, or production authority.

If this lane cannot safely graduate, the program must record a blocked/no-go
posture and harden docs, tests, and verifiers instead of selecting another lane.

## Foundation Lanes

The near-term foundation stays read-only or proposal-only:

| Lane | Current posture | Authority boundary |
|---|---|---|
| Read-only real-world web fetch through `WebAccessGateway` | Implemented only as an explicit M72 tool-runtime transport and CLI inspector; no backend route or Control Center control. | HTTPS GET only, explicit public allowlist, bounded redacted preview, safe refs, gateway audit/request refs. No raw body/header persistence, browser automation, provider SDK call, connector read/write, credentials/cookies, downloads/uploads, POST/PUT/PATCH/DELETE, memory write, context injection, action execution, generic browsing, or production authority. |
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

The deterministic follow-on ranking is:

1. `memory_write`
2. `context_injection`
3. `shell_subprocess_local_maintenance`
4. `connector_write`
5. `browser_automation`
6. `provider_model_authority`

`memory_write` is implemented only as the narrow reviewed recall-write lane for
Memory Review accept/correct decisions. The lane is local-first, Founder Loop
valuable, and bound to exact scope, `LocalApprovalAuthority` validation,
idempotency, receipts, safe-disable posture, CLI parity, and verifier refs.
Broader automatic memory writes, delete/export execution, context injection,
connector writes, and source-truth authority remain blocked.

The scorecard may mark a class as `not_ready`, `proposal_only_ready`,
`contract_ready`, `micro_lane_candidate`, `implemented`, or
`blocked_by_policy`.

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

The first follow-on authority candidate is selected: `memory_write`, only for
reviewed recall-write accept/correct decisions. The existing Action Inbox
`local_task_create` lane remains rank 5, and Memory now has a separate rank 5
`reviewed_memory_recall_write` lane inside an otherwise limited module. Future
connector writes, automatic/broad memory writes, shell/subprocess work, browser
automation, provider/model authority, and context injection remain blocked
until the scorecard and operational maturity verifier agree that one exact lane
is ready.
The fixed first implementation lane, `read_only_real_world_web_fetch` through
`WebAccessGateway`, is implemented only for the exact allowlisted HTTPS GET
tool-runtime/CLI path. It is not a follow-on authority candidate and cannot be
used to justify broader browser, provider, connector, memory, action, or
production authority.

Prompt 04 originally produced a no-go hardening result. The follow-on memory
write hardening pass implemented the missing exact reviewed recall-write scope,
LocalApprovalAuthority binding, rollback/safe-disable posture, CLI parity, and
focused verifier refs for the narrow accept/correct lane only.

## Non-Goals

This program does not add generic execution, connector writes,
shell/subprocess execution, provider/model authority, automatic or broad memory
writes, context injection, browser automation, remote execution, plugin runtime
import, public beta, public release, production-readiness claims, or production
authority.
