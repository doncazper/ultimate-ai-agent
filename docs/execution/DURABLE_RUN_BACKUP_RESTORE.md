# Durable Run Backup, Verify, And Offline Restore

Status: active UAA-P1-028 recovery plan

UAA-P1-028 defines the minimum local-state backup set, verification process,
and offline operator-run restore plan for durable local state. It is a recovery
contract only. It does not add live restore, automatic restore, backup rotation,
new runtime authority, shell or subprocess behavior, browser or network
automation, connector writes, plugin runtime import, mobile control,
model/provider authority, autonomous background work, public distribution, or
production authority.

## Scope

This plan covers local durable state that already exists in the Operator
Runtime Excellence P1 lane:

- durable run records and run snapshots
- durable receipt summaries with receipt hash refs and replay validation refs
- approval state needed to validate exact scoped approvals
- local operator settings required to interpret state safely
- task decomposition registry and registered safe handler metadata
- task decomposition audit summaries
- local model cache references used by reviewed local model evidence

Backup content is safe-reference and redacted-summary only. It must not include
task request text, model/provider content, literal local locations, host-specific
identity material, process configuration exports, secrets, or private content.

## Backup Minimum Set

| Component | Required backup item | Verification requirement | Restore behavior |
|---|---|---|---|
| Runs | `state-ref:durable-runs` append-first durable run storage entries. | JSONL entries parse, schema versions match, per-entry hashes match, previous-entry hash chain matches, duplicate per-run idempotency keys are denied, latest snapshots restore. | Restore as append-first run truth only after verification. |
| Receipts | `state-ref:durable-receipts` receipt-summary entries linked to run ids. | Receipt summaries parse, receipt refs are structured safe refs, summaries are redacted, receipt hash refs validate, replay validation refs bind the receipt to its run, and each receipt points to a known run ref. | Restore as review evidence only; receipts do not authorize execution. |
| Approvals | `state-ref:approval-state` approval requests and grants. | Approval schema validates, grants remain exact-scope, expired or revoked grants remain truthful, and approval refs are evidence only. | Restore for validation history and exact scoped approval checks; no approval ref becomes standalone authority. |
| Settings | `state-ref:operator-settings` local operator settings required to interpret backed-up state. | Settings schema validates, defaults remain least-authority, feature gates remain disabled unless backed by reviewed state, and no secret-like value is present. | Restore only after operator review confirms settings do not broaden authority. |
| Registry | `state-ref:capability-registry` task decomposition capability registry document. | Registry schema validates, signatures or digests match, handler refs are allowlisted, and side-effecting capabilities remain approval-gated. | Restore registry before replay or run inspection so capability ids resolve safely. |
| Audit summaries | `state-ref:audit-summaries` redacted task decomposition audit document. | Audit schema validates, events carry safe summaries, and durable, receipt, replay, and rollback refs are structured safe refs. | Restore as inspectable history only; audit summaries do not restart work. |
| Local model cache references | `state-ref:local-model-cache-refs` reviewed model/cache reference manifest. | Model refs, GGUF refs, checksum refs, hardware-profile refs, blocker refs, and reviewer refs are structured safe refs. No model blob or cache content is included. | Restore references only; binaries and model files require separate provenance review before use. |

The minimum set is all-or-blocked for release evidence. If any required item is
missing or unverifiable, the backup is not production-ready and offline restore
must remain blocked.

## Backup Manifest

Each backup set must include one manifest record with:

- `schema_version`: `uaa-local-backup.v1`
- `backup_ref`: structured safe ref for the backup set
- `created_at_ref`: safe timestamp or release-evidence ref
- `source_baseline_ref`: product/package baseline or checkpoint safe ref
- `component_refs`: the seven minimum-set component refs
- `component_hash_refs`: checksum refs for each component payload
- `verification_ref`: safe ref for the verification result
- `rollback_ref`: safe ref for the pre-restore rollback plan
- `operator_review_ref`: safe ref for the approving reviewer or review packet
- `offline_restore_only`: `true`
- `live_restore_claimed`: `false`
- `safe_ref_only`: `true`

The manifest must not include literal storage locations, machine identity,
secret values, process configuration values, request text, provider content,
transcript content, or unredacted local evidence.

Example shape:

```json
{
  "schema_version": "uaa-local-backup.v1",
  "backup_ref": "backup:local-state-p1-028",
  "source_baseline_ref": "baseline:v0.102.0",
  "component_refs": [
    "state-ref:durable-runs",
    "state-ref:durable-receipts",
    "state-ref:approval-state",
    "state-ref:operator-settings",
    "state-ref:capability-registry",
    "state-ref:audit-summaries",
    "state-ref:local-model-cache-refs"
  ],
  "verification_ref": "verification:backup-p1-028",
  "rollback_ref": "rollback:offline-restore-p1-028",
  "operator_review_ref": "review:offline-restore-p1-028",
  "offline_restore_only": true,
  "live_restore_claimed": false,
  "safe_ref_only": true
}
```

## Verification Checks

Verification is required before a backup is accepted and again before any
offline restore:

1. Confirm all seven minimum-set component refs are present.
2. Confirm the backup manifest schema version is supported.
3. Validate every component payload against its current schema.
4. Recompute component checksum refs and compare to the manifest.
5. Verify durable run storage hash-chain continuity and snapshot checksum
   restore.
6. Verify durable receipt summaries are redacted, receipt hash refs validate,
   replay validation refs match, and receipts are linked to known run refs.
7. Verify approval requests and grants are exact-scope, truthful, and do not
   convert approval refs into runtime authority.
8. Verify registry signatures or digests and allowlisted handler refs.
9. Verify audit summaries contain only safe summaries and structured refs.
10. Verify local model cache refs name provenance, checksum, reviewer, hardware,
    blocker, and rollback refs without storing model/cache content.
11. Verify settings keep authority disabled by default unless a reviewed
    milestone explicitly allows the narrower capability.
12. Verify no component contains private content, secret values, provider
    content, task request text, transcript content, literal local locations, or
    machine identity material.

Any failed check blocks backup acceptance and restore. Failure output must be a
safe summary with reason codes and safe refs only.

## Offline Restore Plan

Offline restore is operator-run and review-gated:

1. Put the local operator surface into a safe-disabled state.
2. Preserve the current local state as a rollback candidate using safe refs.
3. Verify the selected backup manifest and all minimum-set components.
4. Restore into an isolated local state area that is not serving live requests.
5. Re-run the verification checks against the restored state.
6. Inspect durable run truth, approval state, registry, and audit summaries.
7. Confirm local model cache refs are references only and still require
   provenance review before local model use.
8. Record an offline restore review packet with verification, rollback, and
   operator review refs.
9. Promote the restored state only after review confirms least-authority
   settings and exact-scope approvals.
10. Keep the previous local state rollback candidate until the restored state is
    accepted.

The offline restore plan does not resume runs, retry runs, restart model
processes, launch OpenWebUI, invoke handlers, apply settings automatically, or
perform external actions. Those behaviors require separate scoped milestones.

## Rollback

Rollback is required before restore is accepted:

- record a rollback ref for the pre-restore state
- keep the pre-restore state immutable until the restored state is accepted
- if verification fails, abandon the restored candidate and keep the prior
  accepted state
- if operator review fails, keep the prior accepted state and record a blocked
  restore summary
- if the restored state is later rejected, use the rollback ref to select the
  prior accepted local state for offline verification

Rollback evidence is safe-summary and safe-ref only.

## Non-Goals

UAA-P1-028 does not add:

- live restore safety
- backup rotation
- automatic retry, automatic resume, scheduler, or background worker behavior
- task, tool, action, file, memory, network, browser, mobile, remote, plugin,
  shell, subprocess, or model/provider execution authority
- connector writes or external mutations
- storage migrations
- new backend routes or Control Center controls
- public release, public beta, signed installer, or distribution claims

## Verification

Required verifier lane:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
```
