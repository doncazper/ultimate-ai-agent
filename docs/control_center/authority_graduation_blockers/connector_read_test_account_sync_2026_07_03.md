# Connector Read Test-Account Sync Blocker

Status: blocked, no connector read runtime promoted
Lane: Connector Read
Attempted promotion: Level 1 read-only/dry-run test-account sync
Date: 2026-07-03

## Existing Verified Posture

UAA already has two safe connector-read-adjacent foundations.

The M125 connector read-only runtime contract is deterministic, local, and
safe-ref-only:

- core: `src/ultimate_ai_agent/core/connectors/connector_read_only_runtime.py`
- doc: `docs/connectors/CONNECTOR_READ_ONLY_RUNTIME.md`
- tests: `tests/test_m125_connector_read_only_runtime.py`
- foundation_id: `read_only_connector_metadata`

M125 permits reviewed safe metadata preview refs for email, calendar, contacts,
and messages. It explicitly does not perform live connector runtime calls,
connect accounts, authenticate, access the network, handle credentials, read raw
connector content, add backend routes, or add Control Center controls.

UAA also exposes backend-owned source readiness and draft-only connector
proposal posture through:

- route_ref: `GET /control-center/sources/readiness`
- embedded route_refs: `GET /control-center/today/summary`,
  `GET /control-center/morning-briefing/summary`, and
  `GET /control-center/actions/inbox`
- doc: `docs/control_center/FCC_SOURCES_001_SOURCE_READINESS_DRAFT_ONLY_INPUTS.md`
- verifier:
  `scripts/verify_fcc_sources_001_source_readiness_draft_only_inputs.py`
- test:
  `tests/test_fcc_sources_001_source_readiness_draft_only_inputs.py`

The current source readiness model is useful operator truth, but it is still a
readiness/proposal surface. Together, M125 and FCC-SOURCES-001 prove safe
metadata/readiness posture only. They do not authenticate accounts, sync live
connector data, ingest raw source bodies, or create test-account connector sync
receipts.

Safe posture inspection on 2026-07-03 confirmed:

- `connector_runtime_enabled`: `false`
- `source_refresh_enabled`: `false`
- `notification_delivery_enabled`: `false`
- `account_auth_enabled`: `false`
- `raw_source_ingestion_enabled`: `false`
- `write_authority_enabled`: `false`
- source proposal candidates remain
  `proposal_only_no_execution_path`

## Why This Was Not Unblocked

The next requested promotion requires one test-account, read-only connector sync
with least-scope authorization, redacted metadata refs, no raw body/contact/path
or credential persistence, explicit account revocation posture, audit/evidence
receipts, and CLI parity over the same backend-owned read model.

That promotion was not safe in this run because:

- no approved test connector account or OAuth grant ref exists;
- no least-scope live connector read contract is implemented for one named
  adapter;
- no connector read receipt store exists for redacted metadata-only sync
  evidence;
- no cache purge/revocation proof exists for test-account read data;
- no CLI inspection path exists for actual connector sync receipts;
- current UI/routes intentionally show proposal/readiness posture only.

## Missing Contract / Test / Evidence

- exact connector adapter contract for one named read-only test connector;
- least-scope OAuth or credential boundary with revocation proof;
- test-account allowlist and production-account rejection tests;
- metadata-only receipt schema with safe refs for account, source, item, and
  evidence refs;
- proof that raw message body, contact, account, token, cookie, attachment,
  calendar description, path, or credential values are not persisted or
  rendered;
- idempotency and replay posture for repeated read-only sync inspection;
- cache purge/safe-disable path for the test account;
- CLI inspection over the same backend-owned connector read receipts.

## Smallest Next Safe Action

Run a dedicated connector-read unblock PR that implements exactly one
test-account, read-only metadata sync contract for one connector adapter, or
records a no-go if OAuth/test-account prerequisites are not available.

## Authority Still Blocked

- connector account auth
- connector runtime sync
- raw source ingestion
- broad account sync
- production account access
- message body/contact/attachment/calendar-description persistence
- sends, writes, archive/delete/label/move, CRM writes, or calendar writes
- background polling or scheduler-driven connector reads
- connector-derived memory write or context injection
- public beta, public release, or production authority
