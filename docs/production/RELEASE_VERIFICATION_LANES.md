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
separately. Product/readiness language maps through
`docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md`; a lane `pass` is check
evidence only and does not by itself make a capability shipped, production
ready, or publicly released.

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
| security-redaction | `command:secret-broker.redaction`, `command:file-secret.blocking`, `command:foundation-gate.secret-hygiene`, `command:security.artifact-redaction` | Not skippable for a release candidate; blocked by raw prompt, raw response, raw provider payload, raw path, raw log, username, hostname, serial, environment dump, credential-like output, or unsafe release claim. |
| local-model-e2e | `command:local-model.release-gate`, `command:local-model.hardening`, `command:openwebui.local-gateway` | Live hardware or model prerequisites may be skipped only when the harness reports skipped with reason code; blocked by missing reviewed safe refs, approved model refs, or local-only auth prerequisites. |
| durability | `command:durable.state-machine`, `command:event-ledger.append-only`, `command:file.atomic-writes`, `command:backup-restore.verify` | Not skippable for local durable-state release candidates; blocked by corruption, duplicate mutation, missing idempotency, unreceipted mutation, missing minimum backup set, or failed offline restore verification. |
| frontend | `command:frontend.check`, `command:frontend.safety`, `command:frontend.browser-smoke` | Can be skipped only in split CI when an equivalent required frontend job is referenced; blocked by hidden authority, raw JSON primary UI, inaccessible failure state, or failed frontend checks. |
| visual-regression | `command:frontend.visual-regression` (`make frontend-visual-check`), `command:frontend.visual-regression-contract` | Visual compare is skippable only when Playwright browser prerequisites are unavailable and no release claim depends on screenshot evidence; blocked by screenshot drift, missing required surfaces, unsafe screenshot refs, raw/private screenshots, missing redacted baseline policy, or hash mismatch. |
| desktop-packaging | `command:desktop-packaging.proof`, `command:desktop-packaging.contract` | Launch smoke is skippable only when local Docker or Playwright prerequisites are unavailable and the proof remains non-distribution evidence; blocked by launch smoke failure, API health failure, Control Center load failure, manifest mismatch, screenshot failure, shutdown failure, raw logs, raw paths, unsafe evidence refs, or distribution claims. |
| performance | `command:performance.benchmark`, `command:performance.latency-gate`, `command:foundation-gate.report-only` | Optional frontend timing prerequisites may be skipped only when visible with reason code; blocked by required latency failures, missing reports, or authority bypass/caching. |

The static verifier stack also runs the Control Center capability-surface
governance check adjacent to the release-surface scan:

```bash
PYTHONPATH=src .venv/bin/python scripts/generate_control_center_capability_surface.py --check
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_capability_surface.py
```

This is a product-truth and coverage check only. It does not add backend
routes, Control Center controls, shell/subprocess authority, provider/model
calls, connector writes, browser automation, public release claims, production
readiness, or production authority.

## Release-Candidate Usage

For a local release candidate, run:

```bash
.venv/bin/python scripts/verify_all.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

For faster local pre-review feedback, run:

```bash
make verify-dev-fast
make verify-dev-sharded
```

`verify-dev-fast` runs `ruff`, the complete timing-balanced pytest inventory,
`verify-static`, and `verify-gate-architecture` concurrently, then generates a
serialized report-only Foundation Gate summary with `--no-write-latest`.
`VERIFY_DEV_FAST_JOBS` bounds top-level phases and `PYTEST_SHARD_WORKERS`
separately bounds pytest subprocesses. It is useful local evidence, but it does
not create populated release evidence packets or claim release readiness.
CI proves pytest equivalence with eight logical timing-balanced shards in one
installed self-hosted suite job and a stable aggregate `pytest` check; `make
verify` runs the same complete pytest posture plus the release-grade local gate
sequence.

The current private-repository workflow schedules those named jobs only on the
repo-scoped self-hosted Apple Silicon runner pool described in
`docs/developer/SELF_HOSTED_MACOS_CI.md`. This preserves the named lane and
eight-shard evidence contract without consuming GitHub-hosted runner minutes.
Fork pull requests cannot schedule local jobs, the workflow token is read-only,
checkout credentials are not persisted, and GitHub Actions caches and uploaded
artifacts are intentionally absent. Self-hosting changes only CI compute; it
does not grant runtime authority or imply release readiness.
Python 3.12 and Node 22 are provisioned as shared read-only Homebrew toolchains;
the workflow intentionally avoids setup actions whose macOS installation path
would require host-level privileges unavailable to the non-admin runner.

`verify-dev-sharded` and `verify-local` expose the readable local/dev runner. It uses
`scripts/verification/run_dev_fast_gate.py` to run `ruff`, sharded pytest,
static verification, and gate-architecture checks in bounded local fanout, then
runs Foundation Gate serialized in report-only mode with `--no-write-latest`.
The sharded pytest phase runs `scripts/verification/run_pytest_shards.py` across
deterministic test-file membership with timing-aware assignment. The runners record inspectable per-phase and
per-shard logs under ignored `/tmp` paths, write timing summaries, and print
concise phase summaries on success while preserving detailed log tails on
failure. The tracked advisory seed is overlaid by a newer local profile; new or
missing files receive a conservative p90 estimate. Normal runs do not rewrite
timing data; `make test-sharded-profile` is the explicit green refresh lane.
This adds no pytest-xdist dependency. The required self-hosted pytest lane uses
eight bounded logical shards with four workers in one installed environment,
rejects partial coverage through a stable aggregate check, and keeps optional
live/model-heavy execution disabled.

The sharded lane is not a live/model-heavy lane. Shard subprocesses strip known
opt-in environment variables for live GGUF search/acquisition, local model root
enumeration, llama.cpp gateway/startup paths, OpenWebUI test gateway startup,
provider and Web Hybrid live-network smoke tests, Firecrawl credential refs,
model loading, benchmarking, and
model-router sweep posture. Existing optional/live tests remain env-gated and
skipped by default, so `verify-dev-sharded` stays local/dev contract
verification rather than model discovery or runtime activation.

`verify-fast` and `verify-affected` provide deterministic changed-path selection
for advisory local feedback. They cache no pass result, and unknown, CI,
dependency, shared-test, gate, or verifier-topology changes fail closed to the
complete local/dev gate. They do not replace any release lane or populate a
release evidence packet.

For lane-focused review, use the command refs from
`scripts/verify_release_lanes.py --json`. Split CI may satisfy a lane with an
equivalent required job only when the release evidence packet records the job
ref and the lane status is `pass`, `skipped`, `blocked`, or `accepted_failure`
according to the semantics above.

## Security And Artifact Redaction Lane

UAA-P1-055 hardens the `security-redaction` lane with
`scripts/verify_security_redaction_artifacts.py`. The verifier is internal
repo automation only, not an external security audit, signed-release check,
public beta gate, public distribution review, or production-readiness claim.

The artifact scan covers active release/security docs, the current Kanban and
product truth packet, Control Center product-language rules, Foundation Gate and
performance reports, release evidence templates, and optional Control Center
frontend build output under `apps/control-center/dist`. It intentionally does
not scan historical archive folders, dependency folders, or external systems.

The verifier fails when scoped artifacts contain raw prompt markers, raw
response markers, raw provider payload markers, raw local path material, raw log
material, usernames, hostnames, serials, environment dumps, credential-like
assignments, bearer/private-key/token patterns, or unsafe public distribution,
public release, public beta, signed-release, external-audit, production
authority, or production-readiness claims.

Failure output is safe-summary-only. It reports file refs, line refs, category
labels, and short SHA-256 evidence hashes; it must not echo the offending raw
content. The safe report ref for release packets is
`report:security-redaction:artifact-scan`.

The lane is pass/fail for release candidates. It is not skippable when release
artifacts exist. Missing optional frontend build output is allowed because the
frontend lane owns building that output; when present, `dist` is scanned.

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

To roll back UAA-P1-055, remove
`scripts/verify_security_redaction_artifacts.py`, remove
`command:security.artifact-redaction` from the security/redaction lane, CI job,
release evidence packet template, `verify_all` guard, focused tests, and this
section. Do not remove the existing secret broker, file secret blocking, or
Foundation Gate secret-hygiene checks.
