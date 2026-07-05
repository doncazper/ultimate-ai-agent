# CRM Local Command Center M2

Status: partial backend-owned local command center
Contract ref: `contract-ref:crm-local-command-center:m2:v1`
Verifier: `scripts/verify_crm_local_command_center.py`

## What Changed

CRM M2 promotes the historical CRM M1 fixture-only `/crm` shell into a
backend-owned local CRM command center. The current `/crm` surface reads from
Python core and exposes local relationship, timeline, follow-up, pipeline,
smart-list, proposal, report, import/export posture, storage, authority, and
CLI refs.

The M1 fixture contract remains historical evidence and fixture coverage. It
does not grant current authority by itself.

## API Routes

| Route | Posture |
|---|---|
| `GET /control-center/crm/summary` | Read-only summary over the complete CRM read model. |
| `GET /control-center/crm/relationships` | Read-only people, organizations, relationships, drafts, and proposals. |
| `GET /control-center/crm/timeline` | Read-only timeline and reports. |
| `GET /control-center/crm/follow-ups` | Read-only follow-up queue. |
| `GET /control-center/crm/pipelines` | Read-only pipelines and opportunities. |
| `GET /control-center/crm/smart-lists` | Read-only smart lists plus connector/sends posture. |
| `POST /control-center/crm/local-mutations` | Exact local mutation receipt lane requiring idempotency and exact approval. |

## Storage And Redaction

Local CRM state uses repo-local/user-local JSON snapshot and JSONL event
posture. Public API, CLI, docs, tests, and durable reports expose safe refs,
bounded summaries, state labels, counts, and blocked authority refs only.

The read model and receipts deny raw contact details, raw message bodies, raw
paths, raw provider payloads, account material, and secret-like values.

## CLI Parity

`scripts/dev/uaa_crm.py` exposes inspection and local-state helpers:

- `inspect-summary`
- `inspect-relationships`
- `inspect-timeline`
- `inspect-follow-ups`
- `inspect-pipelines`
- `inspect-smart-lists`
- `inspect-storage`
- `seed-demo`
- `clear-demo --confirm-local-only`
- `export-redacted`
- `import-preview --csv`
- `expected-approval`
- `mutate-local`

## Release Truth

Current status is partial. UAA CRM has backend-owned local read routes and one
exact local mutation lane. It does not have connector runtime, external CRM
writeback, account sync, contact import commit, sends, calendar writes,
provider/model calls, live web, no live web fetching, browser automation,
background autonomy, public beta, public release, production readiness, or
production authority.
