# FCC-V1-004 Chat Durable Receipt And Handoff

Status: implemented for durable Chat receipts and reviewable handoffs.
Baseline: v0.102.3 / 0.102.3.

FCC-V1-004 makes the Chat Local Operator surface produce backend-owned safe
receipt refs after a redacted local readiness turn and record reviewable
Actions or Plans handoff refs. Model output remains non-authoritative. Handoffs
create proposals only; they do not execute actions, execute plans, write
memory, inject context, call providers, write connectors, run shell/subprocess
work, or grant production/public beta authority.

## Contract

The durable receipt contract is
`contract-ref:founder-loop-chat-durable-receipt:v1`.

Implemented routes:

- `POST /control-center/chat/turns`
- `GET /control-center/chat/turns/{turn_ref}/receipt`
- `POST /control-center/chat/turns/{turn_ref}/handoff`

The receipt path stores safe refs only:

- `turn_ref`
- `route_ref`
- `model_ref`
- `runtime_truth`
- `auth_truth`
- `tool_denial_truth`
- `safe_summary_ref`
- `handoff_refs`
- `receipt_ref`
- `evidence_ref`
- `idempotency_key_ref`
- `payload_fingerprint_ref`
- `blocked_state_refs`

Raw prompt content, raw response content, raw provider payloads, raw
transcripts, raw tool output, credential material, local paths, usernames,
hostnames, and provider payload content are not receipt fields.

## Handoff

`handoff_target=actions` records a reviewable Action proposal ref.
`handoff_target=plans` records a reviewable Plan proposal ref.

Both handoff modes are idempotent and receipt-backed. They preserve the blocked
posture for action execution, plan execution, connector writes, memory writes,
model-output authority, context injection, and production authority.

## Evidence

Today summary and Evidence Timeline can show:

- Chat turn receipt refs.
- Chat handoff receipt refs.
- Created proposal refs.
- Audit refs and blocked-state refs.
- The route/runtime/auth/tool-denial posture behind the Chat turn.

Evidence reads as history: what was proposed, what happened, what changed, what
can be inspected, and what remains blocked. It is not a raw transcript or model
answer display.

## Proof

Primary proof lanes:

- `scripts/verify_fcc_v1_004_chat_durable_receipt_handoff.py`
- `tests/test_fcc_v1_004_chat_durable_receipt_handoff.py`
- `apps/control-center/src/components/OperatorFlowPanels.tsx`
- `docs/control_center/release_surface_manifest.json`
- `docs/control_center/route_status_manifest.json`

The verifier checks route metadata, release-surface truth, milestone truth,
idempotency replay/conflict behavior, missing-receipt handoff rejection, no
unsafe raw content fields, and no denied authority flags.
