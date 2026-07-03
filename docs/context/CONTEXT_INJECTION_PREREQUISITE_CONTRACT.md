# Context Injection Prerequisite Contract

Status: planned-only prerequisite contract; contract-ready for review; runtime
injection blocked.
Status ref: `prerequisite_contract_ready_runtime_blocked`.
Contract ref: `contract-ref:fcc-mem-020-context-manifest:v1`.
Scope ref: `exact-scope-ref:context-injection:context-pack-preview-materialization`.

This document defines prerequisite refs for a future `context_injection`
authority lane. It grants no runtime prompt/context injection, hidden context,
prompt writing, model/provider call, OpenWebUI handoff execution, memory write,
connector write, action execution, backend mutation route, Control Center
control, public beta, public release, production readiness, or production
authority.

## Exact Scope

The only future scope this contract prepares is:

`exact-scope-ref:context-injection:context-pack-preview-materialization`

That scope means backend-owned, safe-ref-only context-pack preview or
materialization artifacts for operator review. It does not mean context is sent
to a prompt, provider request, connector payload, browser session, shell
command, OpenWebUI request, or any runtime consumer.

## Allowed Source Refs

A later preview/materialization lane may use only reviewed or inspection-only
source refs:

- `memory-record-ref:*`
- `reviewed-recall-ref:*`
- `l1-preview-ref:*`
- `l2-projection-ref:*`
- `l3-representation-ref:*`
- `context-pack-ref:*`
- `context-manifest-ref:*`
- `citation-integrity-ref:*`
- `quality-issue-ref:*`
- `evidence-ref:*`
- `receipt:*`

Raw prompts, raw responses, raw provider payloads, raw source bodies, raw local
paths, raw logs, account identifiers, contacts, credentials, tokens, and file
contents are not allowed source material.

## Allowed Destination Refs

Allowed destination or consumer refs are review artifacts only:

- `context-pack-preview-ref:*`
- `context-materialization-preview-ref:*`
- `proof-ref:*`
- `evidence-ref:*`
- `receipt:context-pack-preview:*`
- `audit:context-pack-preview:*`
- `repo-local-command:founder-loop-memory-context-manifest`

Runtime destinations are explicitly blocked. A later lane may not target
provider/model prompts, OpenWebUI context, connector drafts, browser sessions,
shell/subprocess commands, files, memory writes, or external systems unless a
separate exact milestone grants that authority.

## Approval Binding

Any later preview/materialization micro-lane must validate exact
`LocalApprovalAuthority` scope before materialization. Approval refs are
identifiers only and must not grant broad context, memory, connector, provider,
shell, browser, action, or production authority.

The approval request must bind:

- exact scope ref
- context-pack ref
- context-manifest ref
- source refs
- destination/consumer ref
- reviewer ref
- idempotency ref
- payload fingerprint ref
- redaction posture ref
- blocked runtime authority refs

## Idempotency And Receipts

Any later lane must use append-first durable receipts with replay/conflict
posture. The idempotency key must bind source refs, destination refs, redaction
posture, approval ref, and payload fingerprint ref.

Receipts must include:

- `receipt:context-pack-preview:*`
- context-pack and context-manifest refs
- source refs
- destination/consumer refs
- approval refs
- evidence refs
- audit refs
- proof refs where available
- redaction state
- blocked runtime refs
- rollback ref
- safe-disable ref
- next safe action

## Rollback And Safe Disable

The prerequisite rollback and safe-disable refs are:

- `rollback-ref:context-injection:suppress-context-preview-materialization`
- `safe-disable-ref:context-injection:context-pack-preview-materialization`

Rollback means suppressing or invalidating a preview/materialization artifact.
It does not delete Memory audit history, raw source systems, connector data,
provider data, local files, or external state.

## CLI And Verifier Parity

The repo-local inspection path is:

`scripts/dev/uaa_founder_loop.py memory-context-manifest`

Verifier coverage must include:

- `scripts/verify_fcc_mem_016_020_memory_diagnostics.py`
- `scripts/verify_operational_maturity.py`
- `tests/test_fcc_mem_016_020_memory_diagnostics.py::test_founder_loop_cli_memory_context_manifest_omits_raw_paths`
- `tests/test_governed_memory_context_pack_proposals.py::test_context_pack_api_route_is_backend_backed_and_read_only`

## Still Blocked

The following remain blocked until a separate exact micro-lane is proposed,
implemented, reviewed, and verified:

- runtime prompt/context injection
- live model or provider context injection
- OpenWebUI context handoff execution
- automatic memory inclusion
- provider prompt context injection
- connector-derived context injection
- browser or web-derived context injection
- shell, subprocess, file, or path-derived context injection
- hidden prompt context
- raw payload persistence
- connector writes
- action execution
- public beta, public release, production readiness, or production authority
