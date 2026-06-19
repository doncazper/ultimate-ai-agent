# Backup/Restore Verification

Status: active UAA-P1-045 backup/offline restore verification

Scope: release-readiness verification for the local backup minimum set and
offline restore behavior. This document and verifier do not inspect real local
state, perform live restore, grant runtime authority, publish release artifacts,
or claim public distribution readiness.

Canonical files:

```text
scripts/verify_backup_restore.py
tests/test_backup_restore_verification.py
docs/production/BACKUP_RESTORE_VERIFICATION.md
docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md
```

## Backup Minimum Set

UAA-P1-045 uses the UAA-P1-028 minimum local state set from the durable local
runtime spine plan. A release-candidate backup is incomplete unless it accounts
for every category below using safe refs and redacted summaries only.

| Category | Safe evidence required | Restore expectation |
|---|---|---|
| runs | `run:*`, idempotency refs, audit refs, receipt refs, replay refs, and run state summary | Restored offline with the same safe run truth. |
| receipts | `receipt:*` refs and replay-safe receipt hashes | Restored offline with stable hash evidence. |
| approvals | `approval:*` refs, exact scope refs, status, and revocation posture | Restored offline without widening approval scope. |
| settings | `settings:*` refs and local mode summary | Restored offline without raw paths, hostnames, usernames, or secrets. |
| registry | `registry:*` and capability refs | Restored offline as inspectable metadata, not runtime authority. |
| audit_summaries | `audit:*` refs and redacted event counts or summaries | Restored offline as summaries only, not raw logs. |
| local_model_cache_refs | `model-cache:*` and approved model refs | Restored offline as references only, not raw cache locations or model payloads. |

## Verification Behavior

Run:

```bash
.venv/bin/python scripts/verify_backup_restore.py
.venv/bin/python scripts/verify_backup_restore.py --json
```

The verifier creates a deterministic synthetic fixture in a temporary workspace,
builds a backup manifest for the minimum set, verifies SHA-256 integrity,
restores the backup into a separate offline temporary workspace, and confirms
that corruption detection catches a changed record. Output is safe-ref-only and
contains:

- `schema_version`
- `task_ref`
- `backup_ref`
- `restore_ref`
- minimum state categories
- per-category backup item refs and SHA-256 values
- `backup_integrity_status`
- `offline_restore_status`
- `corruption_detection_status`
- `live_restore_supported: false`
- `live_restore_status: not_scoped`
- report-safety flags
- failure guidance

The verifier does not print raw paths, raw logs, raw prompts, raw responses,
raw provider payloads, usernames, hostnames, serial numbers, environment dumps,
credential material, or private content.

## Release Lane Binding

The durability release verification lane includes
`command:backup-restore.verify`, which points to
`scripts/verify_backup_restore.py`. `scripts/verify_all.py` also runs the
backup/restore guard directly. Release evidence packets may cite the verifier
as `report:backup-restore:*` safe refs only.

Local rollback planning and safe-disable decisions are governed by
`docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md`. Backup verification evidence
does not by itself prove rollback success, live restore safety, or populated
real-state restore safety.

## Failure Guidance

If the verifier fails, treat the release candidate as blocked for backup/restore
evidence. Re-run the verifier, inspect the failing category safe ref, repair the
minimum-set manifest or restore procedure, and keep live restore disabled.

## Non-Goals

This task does not add:

- live restore safety
- hot restore, online restore, or automatic restore
- production authority
- public release, public distribution, signed installer readiness, or hosted
  production support
- shell execution, command execution, subprocess execution, or process spawn
- connector writes
- plugin runtime import or arbitrary plugin execution
- mobile control or mobile sensor runtime
- raw prompt, raw response, raw provider payload, raw path, raw log, username,
  hostname, serial, environment dump, credential material, or private content
  in evidence

Live restore remains not scoped until a later reviewed milestone separately
defines and verifies it.

## Rollback

To roll back UAA-P1-045, remove `scripts/verify_backup_restore.py`,
`tests/test_backup_restore_verification.py`, this document, the durability lane
command ref, the `verify_all` backup/restore guard, documentation-integrity
checks, release evidence packet references, and the docs index, canonical map,
roadmap, product-truth, local state rollback runbook cross-link, and Kanban
links added for this task.
