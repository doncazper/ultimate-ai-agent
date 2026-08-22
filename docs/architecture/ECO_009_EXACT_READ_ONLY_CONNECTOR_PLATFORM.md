# ECO-009 Exact Read-Only Connector Platform

Status: implemented inactive exact calendar metadata snapshot lane. No live
account, authentication, network, provider, background sync, raw content,
connector write, or production authority is granted.

## Accepted first lane

ECO-009 begins with one deliberately bounded adapter over an already-redacted,
caller-supplied or synthetic calendar metadata snapshot. It is useful for
proving the shared connector contract without choosing a provider, storing
credentials, or claiming a live integration.

The Python Core owns:

- exact workspace and source binding;
- an allowlist of event ref, start, end, availability ref, and source revision
  ref fields;
- a 31-day maximum time window and 100-item maximum page;
- source-bound, request-bound, expiring in-memory cursors;
- provenance and retention refs on every projected item;
- idempotent request refs with conflicting reuse denied inside a bounded
  in-memory replay cache;
- per-source rate limiting;
- source revocation and irreversible in-instance global safe-disable;
- content-free outcomes and truthful fail-closed status; and
- an inspection posture consumed by Source Readiness in the Control Center.

No raw title, location, participant identifier, body, attachment, credential,
provider payload, local path, or secret-like value is admitted. The adapter
does not perform external reads: it projects only the snapshot the caller has
already supplied.

## Product truth

The exact adapter posture is available through the repo-local inspection CLI;
it reports `implemented_inactive_no_snapshot_source` when no snapshot has been
registered. The existing backend Source Readiness route remains the authority
for calendar source and metadata-contract failure state. The UI combines that
backend-owned failure truth with the static ECO-009 contract label; it does not
register a snapshot or invent a second backend state. The broad
connector-runtime flag remains false, and the UI says that live account,
network, authentication, background sync, raw content, and connector writes
are blocked.

## Deferred lanes

Every provider-backed calendar, email, message, CRM, meeting, form, finance,
or compliance source needs its own adapter milestone and proof. A future live
adapter must add provider/license review, credential ownership, exact read
scope, sandbox or test-account evidence, durable cursor storage, transport
failure handling, audit evidence, revocation, and safe-disable without
broadening this snapshot lane. Finance and compliance remain separately named
`FIN-CONN-001` and `COMP-CONN-001` milestones.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_eco_009_read_only_connectors.py \
  tests/test_eco_009_verifier.py
PYTHONPATH=src .venv/bin/python scripts/verify_eco_009_read_only_connectors.py
PYTHONPATH=src .venv/bin/python scripts/inspect_eco_009_read_only_connectors.py
PYTHONPATH=src .venv/bin/python scripts/inspect_eco_009_read_only_connectors.py \
  --demo-safe-snapshot
```
