# Release Evidence Packet

Status: active UAA-P1-044 release evidence packet format

Scope: production-release evidence formatting for local release candidates. This
document defines what a release packet must contain; it does not publish a
release, distribute artifacts, sign installers, grant runtime authority, or
accept any failure by itself.

Canonical packet files:

```text
docs/schemas/release_evidence_packet.schema.json
docs/production/RELEASE_EVIDENCE_PACKET_TEMPLATE.json
scripts/verify_release_evidence_packet.py
tests/test_release_evidence_packet.py
```

## Packet Purpose

A release evidence packet is the repo-owned record for one local release
candidate. It must prove exactly:

- which commit/ref and baseline were reviewed
- which verification lanes were checked
- which reports were cited by safe ref
- which checks passed, failed, were skipped, were blocked, or were accepted as
  time-bound reviewed failures
- which artifact hashes were reviewed
- which release blockers remain open
- which capabilities remain not scoped
- which rollback notes apply

The packet stores safe refs and redacted summaries only. It must not contain raw
prompts, raw responses, raw provider payloads, raw paths, raw logs, usernames,
hostnames, serial numbers, environment dumps, credential material, or private
content.

Backup/offline restore evidence is governed by
`docs/production/BACKUP_RESTORE_VERIFICATION.md` and may appear in packets only
as safe report refs and redacted status summaries.

Local rollback guidance is governed by
`docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md`. Packet rollback notes may
cite rollback plan refs, safe-disable refs, category state refs, blocker refs,
and reviewer refs only; they must not imply live restore or unverified
real-state rollback success.

## Required Sections

| Section | Required content |
|---|---|
| `commit_ref` | Safe commit identifier for the reviewed release candidate. |
| `baseline_ref` | Safe baseline identifier such as `baseline:v0.102.0`. |
| `verification_lanes` | Lane ids, status, command refs, report refs, and safe summaries from the release verification lanes. |
| `report_refs` | Safe refs to Foundation Gate, documentation, OpenAPI, security, frontend, visual regression, desktop/local packaging, durability, backup/restore, local model, and performance evidence where applicable. |
| `accepted_failures` | Empty when none exist; otherwise owner ref, reviewer ref, expiry, reason code, safe impact summary, and evidence refs. |
| `artifact_hashes` | Artifact safe refs plus SHA-256 values for reviewed release-candidate artifacts. |
| `release_blockers` | Open, closed, and not-scoped blocker refs with blocking gate and safe summary. |
| `not_scoped` | Capabilities intentionally excluded from the candidate. |
| `rollback_notes` | Rollback safe refs, safe-disable refs, category state refs, blocker refs, and redacted operator summary. |
| `non_goals` | Explicit limits preventing production/public/autonomy/runtime overclaims. |
| `packet_safety` | Boolean safety flags, all false for forbidden raw or private material. |

## Status Semantics

| Status | Meaning |
|---|---|
| pass | The lane completed and produced safe summaries or safe refs. |
| fail | The lane failed and blocks promotion until fixed. |
| skipped | A scoped optional prerequisite was unavailable and a safe reason code is recorded. |
| blocked | A required gate, approval, or prerequisite is missing. |
| accepted_failure | A reviewed failure is time-bound, owner-bound, evidence-bound, and recorded in the packet. |

Accepted failures are never implicit. A lane manifest may describe the policy,
but the release evidence packet is the required place to bind any accepted
failure to owner, reviewer, expiry, reason code, impact, and safe evidence refs.
Failures involving credential exposure, raw private data exposure, route
contract drift, unsafe API output, corruption, duplicate mutation protection, or
unreviewed authority escalation are not acceptable release failures.

## Artifact Hashes

Artifact hashes use SHA-256 and this value form:

```text
sha256:<64 lowercase hex characters>
```

The artifact itself is cited by safe ref, such as
`artifact:source-archive:release-candidate`. The packet must not include raw
artifact locations, local filesystem paths, usernames, hostnames, environment
dumps, or logs.

## Non-Goals

This format does not add:

- production authority
- public release, public distribution, public beta, signed installer readiness,
  or hosted production support
- broad autonomy or autonomous background sessions
- shell execution, command execution, subprocess execution, or process spawn
- unrestricted network access or unrestricted browser automation
- connector writes
- plugin runtime import or arbitrary plugin execution
- mobile control or mobile sensor runtime
- model/provider output as production authority
- raw prompt, raw response, raw provider payload, raw path, raw log, username,
  hostname, serial, environment dump, credential material, or private content
  in evidence

No production authority is granted by this packet format.

## Verification

Run:

```bash
.venv/bin/python scripts/verify_release_evidence_packet.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_all.py
```

The packet verifier is inspection-only. It checks the schema, template, required
status semantics, lane coverage, safety flags, placeholder blocker state,
artifact hash format, and forbidden raw-data language. It does not execute
verification lane commands and does not create release artifacts.

## Rollback

To roll back UAA-P1-044, remove this document,
`docs/schemas/release_evidence_packet.schema.json`,
`docs/production/RELEASE_EVIDENCE_PACKET_TEMPLATE.json`,
`scripts/verify_release_evidence_packet.py`,
`tests/test_release_evidence_packet.py`, the `verify_all` and documentation
integrity hooks, local state rollback runbook cross-link, and the docs index,
canonical map, roadmap, product-truth, and Kanban links added for this packet.
