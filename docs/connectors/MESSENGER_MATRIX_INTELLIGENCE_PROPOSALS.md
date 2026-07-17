# Messenger Matrix Intelligence And Review-Only Proposals

Status: `partial_exact_local_lanes`

Milestone: `MSG-MX-010`

This document is the canonical runtime truth for the first governed Matrix
intelligence boundary. Six separately evaluated operations are accepted for
fresh request-scoped local execution: room AI policy read/write, transient
context materialization, and redacted proposal read/persist/delete.
Provider invocation remains blocked, and attachment analysis remains blocked. No
accepted operation calls a model, analyzes an attachment, sends a message,
executes an action, injects context, or writes Memory.

## Stage A acceptance

Stage A evaluated four independent lane families. Acceptance means eligibility
for one fresh exact evaluation; it never grants standing authority.

| Family | Stage A result | Stage B runtime | Exact authority or blocker refs |
| --- | --- | --- | --- |
| room-content/context materialization | `accepted_request_scoped` | policy read/write and transient content-free context manifests | `authority-lane-ref:matrix-intelligence-room-ai-policy-read`, `authority-lane-ref:matrix-intelligence-room-ai-policy-write`, `authority-lane-ref:matrix-intelligence-context-materialize` |
| approved model/provider invocation | `blocked_missing_exact_authority` | absent | `blocked-reason-ref:msg-mx:model-provider-runtime-prohibited`, `blocked-reason-ref:msg-mx:model-context-authority-not-accepted` |
| proposal persistence | `accepted_request_scoped` | redacted review-metadata read/persist/delete | `authority-lane-ref:matrix-intelligence-proposal-read`, `authority-lane-ref:matrix-intelligence-proposal-persist`, `authority-lane-ref:matrix-intelligence-proposal-delete` |
| attachment materialization/scanning/analysis/cleanup | `blocked_missing_exact_authority` | absent | `blocked-reason-ref:msg-mx:attachment-scanner-adapter-missing`, `blocked-reason-ref:msg-mx:attachment-composite-binding-not-proven` |

The blocked families have no enum operation, tool binding, API execution route,
CLI execution command, adapter, or runtime callback. A scanner bypass therefore
cannot be represented as an accepted intelligence operation.

## Exact pre-start evaluation

Every one of the six accepted operations binds one account, room, event range,
event set where applicable, policy, context grant, proposal and proposal
fingerprint where applicable, task, mission, run, dispatch, idempotency key,
local model-destination-blocked posture, local-only disclosure posture,
content/event/byte limits, retention, deadline, readiness, kill switch,
safe-disable, rollback or deletion posture, and complete request fingerprint.

Immediately before the local owner starts, the shared authority dispatcher
re-evaluates:

- `PolicyEngine` and a fresh exact `LocalApprovalAuthority` grant;
- the current exact session `AuthorityLease` and complete resource-ref set;
- capability, tool, adapter, target, provider, runtime, task, mission, and run;
- deadline, bounded zero-cost budget, readiness freshness, kill switch, and
  safe-disable;
- exact idempotency and replay posture.

Approval refs alone grant nothing. Unknown, stale, expired, revoked, or
mismatched state fails closed before the local owner starts. The store rejects
same-idempotency substitution and proposal-ref reuse with a changed
fingerprint.

## Room AI policy

The backend-owned policy modes are:

- `off`: default; context materialization is ineligible.
- `ask_each_time`: a fresh exact context request, approval, and lease are
  required for each attempt.
- `scoped_allow`: the exact room/context grant and its expiry must match in
  addition to the fresh request-level gates.

Policy state is stored only as safe refs, mode, bounded expiry, and content-free
receipt metadata. A stale scoped grant projects back to effective `off`.

## Transient context manifest

Context input exists only in the sealed in-memory runtime input for the duration
of one accepted operation. Event refs must match the command exactly and in
order. The runtime enforces at most 64 events, 262,144 UTF-8 bytes, a 4,096
content-unit estimate, and a context TTL no longer than 900 seconds. The
content-unit estimate is a conservative local token-equivalent budget without a
tokenizer or model call.

The result contains event refs, keyed safe fingerprint refs, counts, policy and
grant refs, expiry, and a content-free receipt. It never contains message
bodies. All message content is untrusted data: text that requests a policy
change, approval, tool call, send, action, context injection, or Memory write is
fingerprinted as data and has no control effect. The context manifest itself is
evidence metadata, not authority or durable Memory.

## Review-only proposal store

The proposal contract can represent cited unread or period summaries, reply
drafts, open questions, decisions, commitments, task/date extraction,
translation, and exact message, meeting, follow-up, or task proposals. In this
milestone the proposal input is already-redacted review metadata supplied to the
local owner; no generator or model runtime exists.

Each record binds exact account, room, context-manifest ref, source refs,
confidence ref, expiry, and an exact destination and time when the proposal kind
requires them. Cross-surface links are safe refs only for CRM, Calendar, Work
Board, Knowledge, and Communications. A link does not create or mutate the
linked object. Records are explicitly `proposal_only`, `review_required`, and
`execution_path_present=false`; model output, even if introduced later, will
never grant action authority. Proposal deletion has an exact content-free
receipt and no false restore claim.

The local JSON store uses an app-owned root, a single-writer lock, atomic
replacement, and mode `0600`. It persists safe refs and bounded redacted
summaries only. Raw prompts, responses, provider payloads, message bodies,
attachments, paths, identity values, logs, and credentials are prohibited.

## API, CLI, and desktop truth

Protected no-store API inspection is available at:

- `GET /control-center/communications/matrix-intelligence/posture`
- `POST /control-center/communications/matrix-intelligence/proposal`

Six protected, rate-limited, idempotency-required operation routes sit under
`/control-center/communications/matrix-intelligence/`. The CLI exposes the same
posture, command proposal, and dispatch boundary through
`scripts/dev/uaa_communications.py matrix-intelligence-status` and
`matrix-intelligence propose|dispatch`. Runtime input files use bounded,
no-follow local reads; their contents are never printed.

The macOS Control Center Intelligence inspector consumes the typed backend
posture. It shows policy modes, the accepted context/proposal families, safe
cross-surface links, and the two blocked families. The shell does not mint
approval, lease, provider, attachment, send, action, or Memory authority. Room
and message content elsewhere in the current Messenger shell remains synthetic.

## Verification and remaining blocks

`scripts/verify_msg_mx_010_intelligence_proposals.py` closes the operation set,
generic AuthorityLease allowlist, blocked-family absence, default posture,
route contract, and canonical-document markers. Focused tests additionally
cover prompt injection, cross-room/account leakage, stale grants, cloud
disclosure, token-equivalent and byte budgets, revoked leases, uncited/source
scope drift, proposal replay, safe-summary redaction, autonomous-send denial,
and automatic Memory/action escalation.

Still blocked after MSG-MX-010:

- all provider/model invocation and any disclosure beyond the exact local-only
  boundary;
- attachment materialization, scanning, analysis, and cleanup as an intelligence
  composite family;
- automatic proposal generation, direct cross-surface mutation, autonomous
  send, action execution, context injection, and automatic durable Memory;
- enrolled live Matrix account configuration, remote homeservers, mobile
  surfaces, public distribution, and production authority.
