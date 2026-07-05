# CRM Connector Read Lanes Blocker

Date: 2026-07-05
Status: blocked pending exact authority graduation

## Blocked Capability

CRM connector read lanes remain blocked. CRM M2 implements only local read
models, local storage posture, redacted import preview, and exact local
mutation receipts. It does not read from external CRM providers, email,
calendar, contacts, browser sessions, or authenticated accounts.

## Required Before Unblock

- Exact connector/source scope and named test account lane.
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

## Still Denied

Connector writes, sends, calendar writes, account sync, contact merge, contact
creation, browser automation, downloads/uploads, provider/model calls,
background polling, public beta, public release, production readiness, and
production authority remain denied even if a later read-only lane is accepted.
