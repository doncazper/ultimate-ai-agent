# Connector Draft-Only Proposals

Status: implemented as backend-owned local draft proposal refs; connector
send/write/runtime remains blocked

## Purpose

Connector draft-only proposals make communication work reviewable before UAA
has connector runtime authority. The lane exposes safe email-response and
calendar-hold proposal refs through Source Readiness, Inbox, Trust, and CLI
inspection so the operator can see what would be drafted without sending,
writing, syncing, authenticating, polling, or ingesting raw source data.

## Implemented Scope

- Backend read model:
  `src/ultimate_ai_agent/core/connectors/connector_draft_proposals.py`.
- Embedded API surface:
  `GET /control-center/sources/readiness#connector_draft_proposals`.
- CLI inspection:
  `python scripts/inspect_connector_draft_proposals.py`.
- Control Center surface: `/inbox` Source Readiness cards.
- Trust map lane: `trust-lane:connector-draft-only`.
- Contract ref: `contract-ref:connector-draft-only-proposals:v1`.
- Proof ref: `proof-ref:connector-draft-only-proposals:v1`.

The read model contains safe refs only: proposal refs, run refs, connector and
channel refs, target-session refs, redacted subject/body-summary refs,
approval posture refs, idempotency refs, rollback/safe-disable refs, audit
refs, evidence refs, proof refs, and blocked-authority refs.

## Still Blocked

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
.venv/bin/python scripts/verify_fcc_sources_001_source_readiness_draft_only_inputs.py
```

This lane does not add send, write, sync, provider, browser, shell, background,
or production authority. Future send/write work must graduate separately with
exact approval, idempotency, receipt, rollback, safe-disable, redaction, and
test-target proof.
