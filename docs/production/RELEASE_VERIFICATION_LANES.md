# Release Verification Lanes

Status: active UAA-P1-013 release verification lane contract

Scope: production-release discipline for local release candidates without
granting runtime authority, public distribution readiness, or broader
automation.

UAA-P1-013 defines named verification lanes for release-candidate review.
UAA-P1-053 binds those lane command refs to named GitHub CI jobs with
safe-summary-only step summaries. The lane manifest is repo-owned and
inspection-only:

```bash
.venv/bin/python scripts/verify_release_lanes.py
.venv/bin/python scripts/verify_release_lanes.py --json
```

The manifest names commands and evidence refs; it does not execute those
commands. Its `definition_status` may pass while `command_execution_status`
remains `not_executed`. `scripts/verify_all.py` validates that the lane
definitions remain present, safe, and complete. `scripts/run_foundation_gate.py
--command-mode report-only` includes a compact `release_verification_lanes`
summary in the Foundation Gate report without claiming lane-command execution.
In CI, `scripts/run_foundation_gate.py --command-mode ci-parallel` records that
lane execution evidence is represented by required CI job dependencies, not by
Foundation Gate re-running or storing raw lane output.

Backup/offline restore verification for the durability lane is documented in
`docs/production/BACKUP_RESTORE_VERIFICATION.md`.
Local state rollback and safe-disable guidance is documented in
`docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md`.

## Lane Status Semantics

These statuses apply when a lane command or equivalent required job has
actually run. The inspection-only lane manifest reports definition validation
separately.

| Status | Meaning |
|---|---|
| pass | All required commands in the lane completed successfully and produced only safe summaries or safe refs. |
| fail | One or more required commands failed; release promotion or scope expansion is blocked until fixed. |
| skipped | A prerequisite was unavailable and the lane explicitly defines a safe skipped state with reason code. |
| blocked | The lane cannot run or cannot pass because a required gate, approval, or prerequisite is missing. |
| accepted_failure | A known failure is allowed only with reviewer, expiry, evidence ref, and release-packet acceptance. |

Accepted failures are not granted by the lane manifest itself. They require
the release evidence packet format in
`docs/production/RELEASE_EVIDENCE_PACKET.md` with owner, reviewer, expiry,
reason, impact, and safe evidence refs.

## Lanes

| Lane | Required command refs | Skipped/blocked policy |
|---|---|---|
| docs | `command:docs.integrity` | Not skippable for a release candidate; blocked by canonical docs, roadmap, or Kanban currentness failures. |
| openapi | `command:openapi.contract`, `command:api.manifest.tests`, `command:route-module.ownership` | Not skippable for a release candidate; blocked by route-count drift, missing operation ids, unsafe route metadata, or missing route-module ownership coverage. |
| api-safety | `command:api.safe-errors`, `command:control-center.api-routes` | Not skippable for a release candidate; blocked by unsafe error output or side-effect classification drift. |
| security-redaction | `command:secret-broker.redaction`, `command:file-secret.blocking`, `command:foundation-gate.secret-hygiene` | Not skippable for a release candidate; blocked by raw prompt, raw response, raw path, raw log, or credential-like output. |
| local-model-e2e | `command:local-model.release-gate`, `command:local-model.hardening`, `command:openwebui.local-gateway` | Live hardware or model prerequisites may be skipped only when the harness reports skipped with reason code; blocked by missing reviewed safe refs, approved model refs, or local-only auth prerequisites. |
| durability | `command:durable.state-machine`, `command:event-ledger.append-only`, `command:file.atomic-writes`, `command:backup-restore.verify` | Not skippable for local durable-state release candidates; blocked by corruption, duplicate mutation, missing idempotency, unreceipted mutation, missing minimum backup set, or failed offline restore verification. |
| frontend | `command:frontend.check`, `command:frontend.safety`, `command:frontend.browser-smoke` | Can be skipped only in split CI when an equivalent required frontend job is referenced; blocked by hidden authority, raw JSON primary UI, inaccessible failure state, or failed frontend checks. |
| visual-regression | `command:frontend.visual-regression` (`make frontend-visual-check`), `command:frontend.visual-regression-contract` | Visual compare is skippable only when Playwright browser prerequisites are unavailable and no release claim depends on screenshot evidence; blocked by screenshot drift, missing required surfaces, unsafe screenshot refs, raw/private screenshots, missing redacted baseline policy, or hash mismatch. |
| desktop-packaging | `command:desktop-packaging.proof`, `command:desktop-packaging.contract` | Launch smoke is skippable only when local Docker or Playwright prerequisites are unavailable and the proof remains non-distribution evidence; blocked by launch smoke failure, API health failure, Control Center load failure, manifest mismatch, screenshot failure, shutdown failure, raw logs, raw paths, unsafe evidence refs, or distribution claims. |
| performance | `command:performance.benchmark`, `command:performance.latency-gate`, `command:foundation-gate.report-only` | Optional frontend timing prerequisites may be skipped only when visible with reason code; blocked by required latency failures, missing reports, or authority bypass/caching. |

## Release-Candidate Usage

For a local release candidate, run:

```bash
.venv/bin/python scripts/verify_all.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

For lane-focused review, use the command refs from
`scripts/verify_release_lanes.py --json`. Split CI may satisfy a lane with an
equivalent required job only when the release evidence packet records the job
ref and the lane status is `pass`, `skipped`, `blocked`, or `accepted_failure`
according to the semantics above.

## Safety

Lane reports are redacted release evidence. They must not include raw prompts,
raw responses, raw provider payloads, raw paths, raw logs, usernames, hostnames,
serial numbers, environment dumps, or credential material.

This document does not add shell/subprocess authority, browser or network
automation, connector writes, plugin runtime import, mobile control,
autonomous background execution, production authority, public release, public
distribution, or signed installer readiness.

## Rollback

To roll back UAA-P1-013, remove `scripts/verify_release_lanes.py`, the
`release_verification_lanes` Foundation Gate report summary, the
`verify_release_verification_lanes` static scan in `scripts/verify_all.py`, this
document, and the associated tests, docs index links, Kanban entry, and
documentation-integrity checks.
