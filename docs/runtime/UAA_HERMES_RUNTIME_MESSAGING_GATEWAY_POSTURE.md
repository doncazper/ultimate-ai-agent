# UAA Hermes Runtime Messaging Gateway Posture

Status: Phase 42 repo-safe Python Core read model.
Route: `GET /api/runtime/messaging-gateway-posture`
CLI: `scripts/dev/uaa_runtime.py inspect-messaging-gateway-posture`  
Core: `src/ultimate_ai_agent/core/runtime_gateway/messaging_gateway_posture.py`

## Full-Strength

UAA should eventually coordinate operator sessions across messaging platforms
while preserving identity, approval, redaction, proof, receipts, revocation, and
safe-disable posture. Mature gateway lanes may include email, Slack, Telegram,
SMS, Discord, webhooks, and future messaging surfaces, but only after exact
connector authority is proven.

## Repo-Safe

The current implementation is a Python Core read model, API route, CLI
inspection path, and Control Center display only. The read model is now bound to
AuthorityState as `lane-ref:runtime-messaging-gateway-posture-read-model`, which
evaluates as Workspace/read under the active read-only lease. That allowed
decision applies only to inspecting safe messaging gateway labels and refs.

- email readiness label
- Slack readiness label
- Telegram readiness label
- SMS readiness label
- Discord readiness label
- generic webhook readiness label

Each platform exposes connector labels, inbound readiness refs, outbound write
labels, OAuth labels, webhook labels, account-sync labels, redaction policy
refs, proof refs, blocked authority refs, and promotion path refs. It does not
run any connector, fetch accounts, expose a webhook, send messages, or write to
external services.

## AuthorityState

The safe inspection capability is governed by:

- route: `GET /api/runtime/messaging-gateway-posture`
- CLI: `repo-local-command:uaa-runtime-inspect-messaging-gateway-posture`
- AuthorityState route: `GET /api/runtime/authority-state`
- AuthorityState CLI: `repo-local-command:uaa-runtime-inspect-authority-state`
- mapping ref: `lane-ref:runtime-messaging-gateway-posture-read-model`
- domain/capability: `workspace/read`
- required mode: `read_only`

Known authority inside the active lease allows only posture inspection. Email,
Slack, Telegram, SMS, Discord, and webhook adapters remain unsupported and do
not become executable from this read model.

## Blocked / Needs Authority

The following remain blocked:

- connector runtime
- connector reads
- sends
- OAuth
- webhook exposure
- account sync
- external writes
- raw message persistence
- Control Center authority minting

## Exact Authority Path

Execution authority requires later, exact AuthorityLease-governed adapter lanes
for each messaging action. Those later lanes must prove:

1. exact connector read/write authority
2. account refs with no raw account material persistence
3. delivery receipt and proof binding
4. revoke and safe-disable posture
5. redaction verifier for messages, account material, and connector payloads
6. idempotency for any send/write action
7. CLI/API/Core parity before Control Center initiation
8. route side-effect classification for any future API route

Planning text and readiness labels do not grant messaging connector authority.
