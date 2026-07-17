# Messenger Matrix Reliability And Security Hardening

Status: `partial_hardening_evidence`

Milestone: `MSG-MX-011`

Baseline: `d38b91124163f0a716906074187189af13c31c28`

MSG-MX-011 grants no new runtime authority. It hardens the exact local,
request-scoped lanes accepted by MSG-MX-004 through MSG-MX-010 and adds one
content-free read-only posture surface. Calls, agent room participants, hosted
infrastructure, public federation, and production deployment remain blocked.

## Findings And Repairs

Two cumulative resource-escape gaps were found and repaired:

- protected sync-cache history could grow across individually bounded batches;
  retained history is now pruned deterministically to 5,000 events, with at
  most 2,000 retained event refs per room and 128 rooms;
- encrypted outbox records were individually bounded but their directory count
  was not; the outbox now rejects creation beyond 256 records and bounds its
  directory scan.

Low-disk failures now fail before cache staging when free capacity is below the
8 MiB reserve, and cache/outbox `ENOSPC` or quota failures return content-free
typed errors. Unsupported cache schema and hostile queue entries fail closed.
Event normalization also bounds rooms, events, typing users, receipts, Space
parents, and relation depth before durable state changes.

## Measured Budgets

| Budget | Limit |
|---|---:|
| sync response | 1 MiB |
| events per sync batch | 500 |
| rooms per sync batch | 128 |
| protected cache ciphertext | 16 MiB |
| retained cache events | 5,000 |
| retained event refs per room | 2,000 |
| relation depth | 16 |
| encrypted outbox records | 256 |

These are fail-closed local limits, not throughput or production-readiness
claims.

## Hardening Truth

The content-free posture reports twelve categories. Nine have bounded local
evidence: large-room/backpressure, cache/queue bounds, rate-limit and malicious
event defenses, retention/deletion/low-disk behavior, restart/offline recovery,
desktop accessibility, telemetry redaction, dependency/SBOM gates, and
rollback/safe-disable. Localization readiness is `partial` because no production
catalog is selected. Cache migration and persistent multi-device ownership are
`blocked` because their executors are uncomposed. Independent Element Desktop
interoperability is `external_facility_required`; unavailable external evidence
is not simulated.

## Operator Surfaces

- API: protected, no-store
  `GET /control-center/communications/matrix-hardening/posture`
- CLI: `python scripts/dev/uaa_communications.py matrix-hardening-status`
- desktop: Messenger recovery inspector, showing passed checks, gaps, budgets,
  and the external-facility state

All surfaces are projections of the same Python Core posture. The API route has
side-effect class `none`; the UI does not mint authority or store product truth
in React state.

## Deny Floor And Evidence

Every accepted runtime operation must still re-evaluate exact policy, approval
scope where required, AuthorityLease, capability, adapter, provider, target,
mission/run, TTL/deadline, budget, readiness, kill switch, safe-disable, and
idempotency/replay immediately before a call. Unknown, stale, expired, or
mismatched state fails closed. Approval refs alone authorize nothing.

Focused proof lives in `tests/test_msg_mx_011_messenger_hardening.py` and
`scripts/verify_msg_mx_011_messenger_hardening.py`. Evidence is safe-ref and
content-free; raw message content, credentials, local paths, and provider
payloads are excluded.
