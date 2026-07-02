# Provider And Tool Runtime Safety Contracts

Status: contract-only foundation
Scope: backend-owned Python Agent Core contracts for future provider/tool runtime binding to durable runs

This document defines how future provider and tool runtime work must attach to
the durable run lifecycle before any live calls or tool execution can be
promoted. It adds typed invocation envelopes, result contracts, redacted stream
event shapes, replay sanitization, and fail-closed validation posture only.

It does not add provider/model calls, provider SDK calls, tool execution
expansion, runtime activation, background workers, scheduler behavior,
connector writes, browser automation, live web fetching, shell execution,
billing authority, public beta, public release, or production authority.

## Boundary

The contract layer lives in:

- `src/ultimate_ai_agent/core/execution/provider_tool_runtime_safety.py`
- `tests/test_provider_tool_runtime_safety_contracts.py`

Durable runs remain the inspection spine. Provider/tool runtime contracts may
reference run refs, invocation refs, approval refs, cost refs, receipt refs,
evidence refs, rollback refs, and redaction posture refs. Those refs are
identifiers only and do not authorize execution.

Existing exact-scoped provider and tool lanes remain separate governed lanes.
This contract layer does not enable, invoke, import, or generalize those
adapters. It describes the safety envelope future runtime promotion must satisfy
before any callable runtime can be considered.

## Invocation Envelope

Every future provider/tool invocation candidate must be represented by a
run-bound envelope with safe refs only:

- run ref
- invocation ref
- provider or tool ref
- exact approval scope ref
- approval ref
- idempotency ref
- redacted input ref
- expected result schema ref
- cost estimate ref
- max approved USD ref
- privacy posture ref
- replay posture ref
- rollback posture ref
- safe-disable posture ref
- redaction posture ref
- authority boundary refs
- optional evidence refs

The envelope is metadata only. A valid envelope still reports
`valid_contract_only`, with execution not permitted and runtime activation
disabled.

## Result Contract

Provider/tool results are also metadata-only contracts. Allowed statuses are:

- `blocked`
- `validation_failed`
- `approval_required`
- `cost_blocked`
- `redacted_result_ready`
- `failed`
- `canceled`

Result contracts can include:

- redacted output refs
- usage receipt refs
- cost receipt refs
- evidence refs
- safe error summary refs

They cannot include raw prompts, raw responses, raw provider payloads, raw tool
payloads, raw local paths, environment dumps, credentials, usernames, hostnames,
tokens, cookies, or secret-like values. They cannot claim execution was
performed.

## Stream Event Shape

Future streaming/progress work must use ordered durable-run event metadata
before live streaming is promoted. The current contract recognizes:

- `stream_started`
- `stream_delta_redacted`
- `stream_heartbeat`
- `stream_completed`
- `stream_failed`
- `stream_canceled`
- `stream_redaction_applied`

Stream event contracts require a durable run event ref and monotonic sequence
ordering. Delta events require redacted delta refs. Heartbeats require heartbeat
refs. Redaction events require redaction posture refs. Live provider streaming,
tool streaming, SSE, WebSocket behavior, reconnect behavior, and runtime stream
activation remain blocked for later scoped work.

## Blocking Rules

The validator fails closed. It blocks or fails validation when:

- run ref is missing
- exact approval scope or approval ref is missing
- LocalApprovalAuthority validation has not been represented
- approval scope mismatches
- provider/tool ref is unknown
- cost estimate ref is missing
- paid cost is unknown
- actual cost is incomplete
- idempotency ref is missing
- redaction posture ref is missing
- raw payload-like fields or values appear
- runtime activation, provider SDK calls, model calls, tool execution, connector
  writes, background worker behavior, billing authority, or production
  authority are claimed

Unknown provider/tool refs are blocked by default. They are not read-only, not
noop, and not delegation-ready.

## Replay Posture

Replay sanitization returns safe refs only:

- run ref
- invocation ref
- target ref
- result status
- stream sequence refs
- receipt refs
- evidence refs
- redacted refs

Replay records omit raw content and do not execute anything. Replay refs are
inspection evidence, not authority.

## Future Promotion Gates

Any future provider/tool runtime promotion must separately prove:

- exact scoped LocalApprovalAuthority validation
- CostGovernor hard blocking
- complete usage/cost receipts
- incomplete-cost blocking before further use
- idempotent replay behavior
- redacted input/output refs only
- durable run event ordering
- audit/replay inspection
- revocation and safe-disable posture
- UI/CLI inspection parity if surfaced
- no raw payload persistence
- explicit rollback or no-rollback posture

This contract does not satisfy those gates by itself. It only defines the shape
future work must satisfy.
