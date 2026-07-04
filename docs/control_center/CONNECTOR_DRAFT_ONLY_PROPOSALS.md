# Connector Draft-Only Proposals

Status: implemented as backend-owned local draft proposal refs; connector
send/write/runtime remains blocked

## Purpose

Connector draft-only proposals make communication work reviewable before UAA
has connector runtime authority. The lane exposes safe email-response and
calendar-hold proposal refs through Source Readiness, Inbox, Proof, Trust, and
CLI inspection so the operator can see what would be drafted without sending,
writing, syncing, authenticating, polling, or ingesting raw source data.

## Full-strength version

The full connector product should let the operator review, revise, approve,
send, write, sync, and audit connector-backed drafts across email, calendar,
messages, CRM, and future accounts. Full-strength connector work needs exact
target allowlists, account authorization, idempotency, receipts, rollback or
safe-disable posture, delivery proof, revocation, redaction, and operator
controls before any external effect.

## Repo-safe beta-10 version

Beta 10 keeps Connector Draft-Only proposals as embedded, backend-owned,
safe-ref artifacts only. The current lane is available for local draft review
through Source Readiness, `/inbox`, `/proof`, `/trust`, and
`python scripts/inspect_connector_draft_proposals.py`. It adds no standalone
connector draft API route, connector runtime, account connection flow, OAuth
flow, credential collection, source sync, send/write button, provider/model
call, memory write, context injection, background worker, public release, or
production authority.

No connector send, write, account sync, OAuth, auth-material collection,
background sync, scheduler, or delivery worker is enabled. Approval refs shown
by the read model are future posture refs only; they do not execute or grant
send/write authority.

## Implemented Scope

- Backend read model:
  `src/ultimate_ai_agent/core/connectors/connector_draft_proposals.py`.
- Embedded API surface:
  `GET /control-center/sources/readiness#connector_draft_proposals`.
- CLI inspection:
  `python scripts/inspect_connector_draft_proposals.py`.
- Control Center surface: `/inbox` Source Readiness cards.
- Trust map lane: `trust-lane:connector-draft-only`.
- Universal Proof ref: `proof-ref:connector-draft-only-proposals:v1`, rendered
  by `GET /control-center/proof/index` and
  `GET /control-center/proof/{proof_ref}`.
- Contract ref: `contract-ref:connector-draft-only-proposals:v1`.
- Proof ref: `proof-ref:connector-draft-only-proposals:v1`.

The read model contains safe refs only: proposal refs, run refs, connector and
channel refs, target-session refs, redacted subject/body-summary refs,
approval posture refs, idempotency refs, rollback/safe-disable refs, audit
refs, evidence refs, proof refs, and blocked-authority refs.

## Blocked / needs authority

- Live connector runtime.
- Email send, archive, delete, label, move, or write behavior.
- Calendar write, invite send, update, or delete behavior.
- Account sync, polling, OAuth flow, or auth-material collection.
- Raw message, contact, file, path, account, auth, or provider payload
  persistence.
- Connector-derived memory write or context injection.
- Provider/model calls, browser execution, shell/subprocess execution,
  background scheduler work, public beta, public release, production readiness,
  or production authority.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_connector_draft_proposals.py tests/test_control_center_api_routes.py tests/test_fcc_sources_001_source_readiness_draft_only_inputs.py -q
.venv/bin/python scripts/inspect_connector_draft_proposals.py
.venv/bin/python scripts/verify_beta_10_connector_draft_only.py
.venv/bin/python scripts/verify_fcc_sources_001_source_readiness_draft_only_inputs.py
```

This lane does not add send, write, sync, provider, browser, shell, background,
or production authority. Future send/write work must graduate separately with
exact approval, idempotency, receipt, rollback, safe-disable, redaction, and
test-target proof.

## Exact promotion path

Promoting beyond beta-10 requires a separate accepted lane with exact connector
scope, test account or target allowlist, OAuth/account authorization proof where
needed, LocalApprovalAuthority binding, idempotency key, send/write receipt,
delivery evidence, redacted output summary, rollback or safe-disable posture,
revocation, CLI parity, OpenAPI/route truth, frontend truth labels, and focused
tests proving no raw account/contact/body/credential data is persisted.
