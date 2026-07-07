# CRM Connector Read Capability Blocker

Date: 2026-07-05
Status: blocked pending exact AuthorityLease domain/capability support

Readiness contract:
`posture-ref:crm-connector-read-lanes:v1`

CLI inspection:
`repo-local-command:uaa-crm:inspect-connector-read-lanes`

## Blocked Capability

CRM connector read capabilities remain blocked. CRM M2 implements only local read
models, local storage posture, redacted import preview, and exact local
mutation receipts. It does not read from external CRM providers, email,
calendar, contacts, browser sessions, or authenticated accounts.

The Control Center and CLI now expose connector-read readiness as backend-owned
metadata. This is not connector runtime. It records the intended single-source
metadata-only scope, missing prerequisites, safe-disable posture, proof/evidence
refs, and promotion path while keeping runtime reads disabled by default.

## Required Before Unblock

- Exact connector/source scope and named test account scope.
- PolicyEngine route and source decision coverage.
- LocalApprovalAuthority scope for each connector read attempt.
- Read-only adapter boundary through approved gateway contracts only.
- No raw contact details, message bodies, account material, cookies, auth
  tokens, provider payloads, raw paths, or raw logs in durable output.
- Audit records with adapter, source ref, timestamp, authority mode, risk
  class, policy decision, network lane, and source metadata.
- CLI/API/Control Center parity.
- Safe-disable and rollback-readiness posture.
- Focused tests, OpenAPI/manifest route classification, docs, and verifier
  coverage.

Stable refs in this blocker may still contain `lane` because older core,
frontend, and verifier fixtures consume those identifiers. They are
compatibility refs only; the authority model is mode/domain/capability inside
an active AuthorityLease.

## Current Repo-Safe Readiness State

- `readiness_status`: `blocked_missing_exact_authority`
- `source_scope_ref`:
  `scope-ref:crm-connector-read:single-source-metadata-only:v1`
- `test_account_scope_ref`:
  `scope-ref:crm-connector-read:named-test-account-required:v1`
- `gateway_boundary_ref`:
  `gateway-ref:crm-connector-read:approved-read-gateway-required:v1`
- `policy_decision_ref`:
  `policy-ref:crm-connector-read:deny-until-exact-lane:v1`
- `approval_scope_ref`:
  `approval-scope-ref:crm-connector-read:per-attempt-required:v1`
- `audit_schema_ref`: `audit-schema-ref:crm-connector-read:v1`
- `redaction_policy_ref`:
  `redaction-ref:crm-connector-read:safe-refs-only:v1`
- `safe_disable_ref`: `safe-disable-ref:crm-connector-read:disable-lane:v1`
- `rollback_readiness_ref`:
  `rollback-readiness-ref:crm-connector-read:no-external-mutation:v1`
- `proof_ref`: `proof-ref:crm-connector-read-readiness:v1`
- `evidence_ref`: `evidence-ref:crm-connector-read-readiness:v1`

Denied flags remain false: connector runtime, connector writes, raw body
ingestion, live connector read performed, external account auth, background
polling, provider/model calls, and production authority.

## Exact Promotion Path

1. Define one single-source metadata-only lane and one named test-account/source
   scope.
2. Bind the source to an approved gateway adapter with deny-by-default policy.
3. Add PolicyEngine source decisions and LocalApprovalAuthority per-attempt
   approval scope.
4. Add audit receipt schema, redaction verifier, idempotency posture, and
   safe-disable behavior.
5. Add CLI/API/Control Center parity with OpenAPI and route side-effect
   classification.
6. Run focused tests, product truth, operational maturity, documentation
   integrity, CRM verifier, and OpenAPI verifier before any authority promotion.

## Still Denied

Connector writes, sends, calendar writes, account sync, contact merge, contact
creation, browser automation, downloads/uploads, provider/model calls,
background polling, public beta, public release, production readiness, and
production authority remain denied even if a later read-only lane is accepted.
