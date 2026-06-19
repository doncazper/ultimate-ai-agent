# Local Model Operational Runbook

Status: active UAA-P0-017 local model operational runbook
Scope: M166/M167 local loopback model operations and recovery guidance
Authority source: M166 exact-scope local llama.cpp/OpenWebUI shell gate

This runbook gives operators safe recovery guidance for local model failures in
the M160-M167 lane. It is production-readiness scaffolding for local loopback
operation only. It does not add production authority, public production support,
public distribution, unrestricted shell/subprocess execution, unrestricted
network/browser automation, connector writes, plugin runtime import, mobile
control, autonomous background execution, model/provider authority, or
OpenWebUI authority.

All recovery evidence must use safe refs and redacted summaries only. Durable
evidence, reports, release docs, tests, and logs must not contain raw prompts,
raw responses, raw provider payloads, raw local paths, raw logs, usernames,
hostnames, serials, environment dumps, credential material, or secret-like
values.

For local state category rollback beyond local model operational incidents, use
`docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md`. That runbook distinguishes
rollback, safe-disable, backup restore, and unsupported recovery for local model
cache, settings, registry, approvals, audit state, and run/receipt state.

## State Semantics

| State | Meaning | Operator posture |
|---|---|---|
| safe | Reviewed local prerequisites are satisfied, evidence refs are redacted, rollback exists, and the local scope remains loopback-only. | Continue within the approved M166/M167 local lane. |
| degraded | The local loop is usable for limited review, but a non-critical capability is missing, slow, or temporarily disabled. | Keep the scope narrow, collect safe evidence, and avoid new authority. |
| blocked | A required prerequisite, safety invariant, approval, provenance, rollback, or evidence ref is missing or failed. | Stop promotion and keep the model state blocked until reviewed evidence clears the blocker. |
| unsupported | The request is outside the local loopback lane or needs authority not granted by M166/M167. | Do not proceed. Record a safe unsupported-state ref and require a later scoped milestone. |

## Evidence Rules

- Use refs such as `evidence-ref:local-model:operation:*`,
  `blocker-ref:local-model:*`, `rollback-ref:local-model:*`, and
  `safe-disable-ref:local-model:*`.
- Summaries may name the scenario, state, reviewed owner, and next safe action.
- Summaries must not include raw local paths, raw logs, raw prompt/response
  content, raw provider payloads, usernames, hostnames, serials, environment
  dumps, tokens, passwords, cookies, API keys, or credential material.
- Unknown model provenance, unknown binary provenance, missing rollback, or
  unsafe evidence collection keeps the state blocked.
- Model output, OpenWebUI output, runtime logs, and tuning advice are never
  authority by themselves.

## Scenario Runbook

| Scenario | Safe recovery steps | Safe evidence refs | Blocked, degraded, or unsupported handling |
|---|---|---|---|
| Cache cleanup | Confirm cleanup is scoped to reviewed local model cache classes, preserve approved model/provenance/integrity/rollback refs, remove only stale or failed artifacts, and re-check offline readiness after cleanup. | `cleanup-ref:local-model:cache`, `evidence-ref:local-model:cache-cleanup`, `rollback-ref:local-model:cache-cleanup` | Block if cleanup would delete rollback state, erase audit evidence, require raw paths, or require broad filesystem authority. |
| Corrupted GGUF | Mark the model candidate blocked, keep the approved previous model ref active, record a safe corruption summary, require fresh provenance and integrity review before reuse, and avoid loading the corrupted artifact. | `blocker-ref:local-model:corrupted-gguf`, `model-ref:local-model:known-good`, `integrity-ref:local-model:replacement-pending` | Block until a reviewed GGUF ref, checksum/signature ref, and rollback ref exist. Unsupported if recovery needs unreviewed download authority. |
| Stuck download | Keep runtime disabled for the pending model, record a safe progress/blocker summary, avoid retry loops without scoped approval, and use already-approved cached artifacts for offline review when available. | `blocker-ref:local-model:stuck-download`, `evidence-ref:local-model:download-state`, `offline-ref:local-model:cached-artifact` | Degraded if an approved cached model can continue local review. Block if the only path forward is an unreviewed network retry or unknown artifact. |
| Port conflict | Do not expose non-loopback endpoints. Record the conflict as a safe blocker, keep the local gateway disabled or bound to the approved loopback configuration, and require reviewed settings before any port change. | `blocker-ref:local-model:port-conflict`, `settings-ref:local-model:loopback-only`, `safe-disable-ref:local-model:gateway` | Block if conflict resolution needs process inspection, raw logs, raw paths, or non-loopback network exposure. Unsupported if a remote/public endpoint is requested. |
| Credential rotation | Rotate only reviewed local gateway credentials through the approved local settings path, never store credential values in evidence, revoke prior refs, and confirm auth failure for old refs by safe result summary only. | `credential-rotation-ref:local-model:gateway`, `revocation-ref:local-model:previous-gateway-key`, `evidence-ref:local-model:auth-rotation` | Block if any token, key, cookie, authorization header, or secret-like value would enter evidence. Unsupported if rotation asks for external credential brokerage not scoped by a milestone. |
| Rollback | Prefer the previous known-good preset/model/runtime ref, keep rollback idempotent, verify the active state by safe summary, and record whether restart was skipped, completed, or blocked. | `rollback-ref:local-model:known-good`, `preset-ref:local-model:previous-known-good`, `result-ref:local-model:rollback-state` | Block if no previous known-good ref exists or if rollback requires destructive cleanup without review. Degraded if rollback succeeds but optional local features remain disabled. |
| Offline mode | Confirm required approved artifacts already exist, deny new network dependency, keep loopback-only settings, and record offline readiness as a safe ref. | `offline-ref:local-model:ready`, `artifact-ref:local-model:approved-local`, `evidence-ref:local-model:offline-check` | Degraded if offline mode can run only a smaller approved model. Block if startup requires unreviewed downloads, telemetry, external auth, or remote calls. |
| Safe evidence collection | Collect only state, status, decision, latency bucket, blocker, rollback, and reviewer refs. Convert operator observations to redacted summaries before evidence is stored. | `evidence-ref:local-model:operation-summary`, `review-ref:local-model:operator`, `blocker-ref:local-model:evidence-safety` | Block if raw prompt, response, provider payload, path, log, identity, environment, credential, or secret-like material is present. |
| Blocked/unknown model state | Treat unknown model, unknown GGUF, unknown binary, unknown checksum, unknown license, unknown provenance, or missing approval as blocked. Keep the previous known-good local state active when available. | `blocker-ref:local-model:unknown-state`, `model-ref:local-model:known-good`, `review-ref:local-model:pending` | Block until provenance, integrity, approval, rollback, and reviewer refs exist. Unsupported if the model source requires authority outside the local lane. |
| Safe-disable path | Disable the local model lane by safe setting state, stop treating `/v1` local gateway results as available, preserve rollback/evidence refs, and keep operator-facing status explicit. | `safe-disable-ref:local-model:gateway`, `status-ref:local-model:disabled`, `rollback-ref:local-model:disable-state` | Use safe-disable for failed prerequisites, uncertain provenance, unsafe evidence, missing approval, or operator-requested stop. Unsupported if disabling would require unscoped process control or external service mutation. |

## Operator Sequence

1. Identify the scenario and assign a safe, degraded, blocked, or unsupported
   state.
2. Preserve the previous known-good model, preset, rollback, and review refs.
3. Collect redacted evidence refs only.
4. Keep local gateway and OpenWebUI shell behavior disabled or degraded when
   provenance, integrity, approval, rollback, or evidence safety is uncertain.
5. Apply no setting, restart, cleanup, credential rotation, download retry, or
   model switch without exact approval and rollback binding.
6. Re-run the scoped verification lane after a recovery action is reviewed.
7. Record remaining blockers as safe refs; do not fabricate pass evidence.

## Safe-Disable Criteria

Use the safe-disable path when any of these are true:

- unknown or unverified model provenance
- unknown or unverified `llama-server` provenance
- missing checksum/signature review for a required artifact
- missing previous known-good rollback ref
- raw or sensitive evidence is present
- loopback-only posture is uncertain
- local gateway auth state is uncertain
- operator requests stop or revocation
- the recovery path requires unsupported authority

Safe-disable is not a failure to hide. It is the expected conservative state
when recovery cannot be proven with safe refs.

## Non-Goals

This runbook does not provide public production support, signed installer
support, public distribution, external service support, unrestricted shell or
process control, broad filesystem cleanup, unreviewed downloads, connector
writes, plugin runtime import, mobile control, autonomous background execution,
model/provider authority, OpenWebUI admin authority, raw evidence export, or
production readiness claims beyond the reviewed local M166/M167 scope.

## Rollback

If this runbook is rolled back, remove links from the active docs index,
canonical map, M167 hardening docs, local smoke harness, product truth packet,
Control Center gap map, and current Kanban board. Until a replacement runbook
is accepted, local model operational controls should remain blocked or pending
for production-readiness review.
