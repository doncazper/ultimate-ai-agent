# Local State Rollback Runbook

Status: active UAA-P1-046 local state rollback runbook

Scope: production-readiness rollback guidance for local state categories. This
runbook documents operator-controlled safe-disable, rollback, backup restore,
and unsupported recovery handling. It does not perform rollback, inspect real
local state, execute commands, grant runtime authority, publish release
artifacts, or claim live restore safety.

Canonical related files:

```text
docs/production/BACKUP_RESTORE_VERIFICATION.md
docs/production/RELEASE_EVIDENCE_PACKET.md
docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md
docs/production/LOCAL_RUNTIME_PACKAGING.md
```

## Terms

| Term | Meaning |
|---|---|
| Rollback | Return one local state category to a previous reviewed safe ref after backup, verification, approval, and rollback planning. |
| Safe-disable | Disable or mark unavailable a local capability when rollback cannot be proven safely. Safe-disable is the default conservative action for unknown or unsafe state. |
| Backup restore | Offline/operator-run restoration from a verified backup set. Backup restore is not live restore, hot restore, or automatic recovery. |
| Unsupported recovery | Any recovery path needing unscoped authority, raw private evidence, live restore, broad filesystem mutation, shell/subprocess execution, connector writes, plugin runtime import, network/browser automation, mobile control, public distribution, or production runtime claims. |

## Backup Before Rollback

Before any rollback is reviewed, an operator must record backup-before-rollback
evidence with safe refs and redacted summaries only:

- `backup-ref:local-state:<candidate>` for the reviewed backup set.
- `verification-ref:backup-restore:<candidate>` for backup integrity and
  offline restore verification status.
- `rollback-plan-ref:local-state:<category>` for the proposed category action.
- `reviewer-ref:local-state:<review>` for the maintainer or release reviewer.
- `blocker-ref:local-state:<reason>` when backup, approval, or evidence is
  incomplete.

Backup evidence must account for the UAA-P1-028 minimum set when applicable:
runs, receipts, approvals, settings, registry, audit summaries, and local model
cache refs. It must not contain raw prompts, raw responses, raw provider
payloads, raw paths, raw logs, usernames, hostnames, serial numbers,
environment dumps, credential material, or private content.

## Safety Checks

Every rollback decision must answer these checks before any operator action is
described as ready:

| Check | Required answer |
|---|---|
| Backup exists | A safe backup ref and verification ref exist before rollback. |
| Scope is exact | The category, state ref, approval ref, rollback ref, and expected outcome are exact. |
| Evidence is safe | Only safe refs and redacted summaries are stored. |
| Approval is bound | Mutating rollback requires exact approval; approval refs alone are not authority. |
| Rollback is idempotent | Repeating the same request does not create duplicate mutation or duplicate receipt state. |
| Audit is preserved | Audit summaries remain inspectable; raw logs are not copied into evidence. |
| Live restore is absent | Live, hot, automatic, or background restore is not claimed. |
| Unsupported authority is denied | Shell/subprocess, broad filesystem mutation, connector writes, plugin runtime import, network/browser automation, mobile control, or public distribution paths are blocked. |

## Category Runbook

| State category | Rollback steps | Safe-disable path | Backup restore handling | Unsupported recovery handling |
|---|---|---|---|---|
| Local model cache | Preserve the current `model-cache:*` ref, identify the previous approved `model:*` and integrity refs, verify rollback does not delete audit or provenance refs, then record `rollback-ref:local-state:model-cache` and a redacted result summary. | Mark the local model cache unavailable with `safe-disable-ref:local-state:model-cache` when provenance, checksum/signature review, approved model ref, or rollback ref is missing. | Restore only approved cache refs and model refs from the verified offline backup set; do not restore raw cache locations or model payloads into evidence. | Unsupported if recovery needs unreviewed downloads, unknown binary trust, raw cache paths, broad cleanup, non-loopback runtime exposure, or live restore. |
| Settings | Capture the current `settings:*` ref, compare it to the previous reviewed local-loopback settings ref, confirm no secret values are in evidence, then roll back by exact settings ref with `rollback-ref:local-state:settings`. | Apply `safe-disable-ref:local-state:settings` when loopback posture, credential state, or approval binding is uncertain. | Restore settings only from a verified backup summary and revalidate local-only posture by safe result ref. | Unsupported if recovery requires storing secret values, hostnames, usernames, raw paths, environment dumps, or public/network-facing configuration. |
| Registry | Preserve the current `registry:*` and capability refs, select the previous inspectable registry snapshot, verify no callable/runtime catalog is enabled by rollback, then record `rollback-ref:local-state:registry`. | Use `safe-disable-ref:local-state:registry` when capability provenance, risk class, activation status, or revocation posture is unknown. | Restore registry metadata as inspectable records only; do not treat restored registry refs as runtime authority. | Unsupported if recovery would activate plugins, import runtime code, widen capability grants, or create callable authority from metadata. |
| Approvals | Preserve current `approval:*`, scope, revocation, expiry, and audit refs, restore only exact-scope approval records that remain valid, and record `rollback-ref:local-state:approvals`. | Use `safe-disable-ref:local-state:approvals` when approval scope, reviewer, expiry, revocation status, or audit binding is missing. | Restore approval records offline as evidence and require policy revalidation before any approval is treated as active. | Unsupported if recovery relies on approval refs alone, broad standing approvals, missing revocation state, or unreviewed authority expansion. |
| Audit state | Preserve `audit:*` summary refs, event counts, receipt refs, and corruption status, then restore only redacted audit summaries with `rollback-ref:local-state:audit`. | Use `safe-disable-ref:local-state:audit` when audit continuity, event ordering, receipt hash, or corruption status cannot be proven. | Restore summaries and safe refs only; raw logs and raw event payloads stay out of release evidence. | Unsupported if recovery requires raw logs, raw prompts, raw responses, raw provider payloads, raw paths, identity material, or environment dumps. |
| Run/receipt state | Preserve `run:*`, `receipt:*`, idempotency, replay, audit, and state-transition refs, verify the desired previous state is valid, and record `rollback-ref:local-state:runs-receipts`. | Use `safe-disable-ref:local-state:runs-receipts` when transition truth, receipt hash, replay ref, idempotency key, or corruption status is uncertain. | Restore runs and receipts from the verified offline backup minimum set; revalidate state truth before retry, resume, or cancel decisions. | Unsupported if recovery hides dead-letter state, silently deduplicates unknown mutations, fabricates receipts, or claims live replay/restore safety. |

## Redacted Examples

Safe release evidence examples:

```text
rollback-ref:local-state:settings:reviewed
safe-disable-ref:local-state:registry:unknown-provenance
backup-ref:local-state:release-candidate
verification-ref:backup-restore:synthetic-minimum-set
result-ref:local-state:rollback-blocked
```

Safe redacted summary example:

```text
Settings rollback blocked because the previous reviewed settings ref is
missing. Local runtime remains safe-disabled until backup verification and
approval binding are reviewed.
```

Do not record raw local paths, raw logs, raw prompts, raw responses, raw
provider payloads, usernames, hostnames, serials, environment dumps,
credential values, private content, or secret-like material in rollback
evidence.

## Release Evidence Binding

Release evidence packets may cite this runbook only through safe refs and
redacted summaries. A packet can record:

- rollback plan ref
- backup verification ref
- safe-disable ref
- category state ref
- blocker ref
- reviewer ref
- result ref

A packet must not claim a rollback succeeded unless the category-specific
backup, approval, idempotency, audit, and evidence-safety checks are satisfied.
Skipped, blocked, unsupported, and safe-disabled states must remain visible.

## Non-Goals

This runbook does not add:

- live restore, hot restore, automatic restore, or background restore
- production authority
- public release, public distribution, public beta, hosted production support,
  signed installer readiness, or enterprise support
- shell execution, command execution, subprocess execution, or process spawn
- unrestricted network access or unrestricted browser automation
- broad filesystem mutation or cleanup authority
- connector writes
- plugin runtime import or arbitrary plugin execution
- mobile control or mobile sensor runtime
- model/provider output as production authority
- raw prompt, raw response, raw provider payload, raw path, raw log, username,
  hostname, serial, environment dump, credential material, or private content
  in evidence

## Known Gaps

- This runbook is operator guidance and documentation integrity coverage only.
- Populated real local-state backup packets remain separate release-candidate
  evidence.
- Live restore safety remains not scoped.
- Category rollback execution remains dependent on later exact-scope
  implementation and approval gates where mutation is required.

## Rollback

To roll back UAA-P1-046, remove this document, release evidence packet and
backup/restore links to it, documentation-integrity checks, docs index and
canonical-map entries, roadmap/product-truth/Kanban updates, and any release
packet references added for this task. Until a replacement runbook is accepted,
local state rollback evidence should remain blocked or safe-disabled for
production-readiness review.
