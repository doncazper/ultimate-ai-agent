# Release Latency Baseline Harness

Status: active UAA-P1-043 Foundation Gate latency integration over UAA-P1-042
safe static manifest caching, UAA-P1-041 hot-path profiling, UAA-P1-040
performance regression reports, UAA-P1-039 latency budget gate, and UAA-P0-006
performance baseline harness

Scope: production-readiness latency evidence for local release-critical paths

This harness makes p50 and p95 latency visible for release review without
granting runtime authority. UAA-P0-006 introduced the baseline measurement
loop; UAA-P1-039 makes the required local path budgets an explicit release gate;
UAA-P1-040 adds machine-readable and human-readable regression reports; UAA-P1-041
adds safe hot-path profiling for task decomposition and OpenAPI build; UAA-P1-043
adds a typed `latency_gate` summary to the Foundation Gate report. The
scripts measure the existing Foundation Gate evaluator and the release-critical
local FastAPI paths through `TestClient`, then write redacted timing summaries
under `reports/performance`.

## Commands

```bash
.venv/bin/python scripts/benchmark_foundation_gate.py
.venv/bin/python scripts/check_foundation_gate_latency.py
PYTHONPATH=src .venv/bin/python scripts/profile_hot_paths.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

`scripts/benchmark_foundation_gate.py` writes:

- `reports/performance/latest_release_latency_baseline.json`
- `reports/performance/latest_release_latency_baseline.md`
- `reports/performance/latest_performance_regression_report.json`
- `reports/performance/latest_performance_regression_report.md`
- `reports/performance/latest_hot_path_profile.json`
- `reports/performance/latest_hot_path_profile.md`

`scripts/check_foundation_gate_latency.py` fails when the typed Foundation Gate
status fails, the Foundation Gate evaluator exceeds its budget, required budget
definitions or path results are missing, any required release latency path fails
or misses its p95 budget, or a measured path reports authority caching or bypass
for speed.

`scripts/run_foundation_gate.py --command-mode report-only` includes the same
release latency evidence in `reports/foundation_gate/latest_foundation_gate_report.json`
under `latency_gate`, and in
`reports/foundation_gate/latest_foundation_gate_report.md` under the Latency Gate
section. The Foundation Gate integration reports p50/p95 status, pass/fail/
skipped path state, accepted failures, report refs, optional prerequisite state,
and an environment-safe summary. It does not include raw paths, raw logs,
hostname, username, serial number, environment dumps, prompts, responses,
provider payloads, or credential material.

## Budgets

| Path | p95 budget |
|---|---:|
| `/health` | 50 ms |
| `/api/manifest` | 150 ms |
| `/models/route/preview` | 150 ms |
| `/task-decomposition/classify` | 100 ms |
| `/task-decomposition/decompose` | 250 ms |
| `/files/read/preview` bounded text | 150 ms |
| `/v1/models` local gateway | 100 ms |
| `/v1/chat/completions` local path | 250 ms |
| Control Center first useful local render | 1500 ms |

The Control Center first useful local render row is currently optional and
reports `skipped` with
`skipped-ref:p1-039:control-center-render-runner-not-scoped` until a reviewed
frontend render timing runner is added. The backend release paths are required.
Optional rows must report `passed`, `skipped`, or `blocked` with reason codes;
they must not disappear from the report.

## Regression Report Fields

The UAA-P1-040 regression report contains:

- p50 and p95 timing for each measured row
- sample count
- pass, fail, skipped, or blocked status
- budget comparison, budget ratio, and remaining budget margin
- reason codes and operator action labels
- environment-safe summary that records measurement mode and runner class only
- retention guidance for release evidence packets

Regression reports compare the current measurement to the release budget. They
do not claim historical trend storage; retained history belongs in reviewed
release evidence packets as safe report refs and summarized timing rows only.

## Hot-Path Profiling

UAA-P1-041 profiles:

- task decomposition classify route handler
- task decomposition decompose route handler
- OpenAPI schema build

Profiling output contains p50, p95, mean timing, sample count, warmup count,
pass/fail status, reason codes, and authority-boundary labels. It is
timing-summary only: it does not record request bodies, response bodies, raw
OpenAPI schema bodies, raw paths, logs, hostnames, usernames, environment
dumps, prompts, provider payloads, or credential material.

Task decomposition profiling uses the same bearer-gated local route path as the
latency gate. OpenAPI build profiling clears and restores the in-process schema
cache for each sample so build cost is visible without changing route authority
or OpenAPI verification behavior.

## Foundation Gate Integration

UAA-P1-043 adds a typed `latency_gate` block to the Foundation Gate report. The
block contains:

- overall latency gate status
- p50/p95 status for release-critical local paths
- Foundation Gate best and mean timing with budget comparison
- pass, fail, skipped, or blocked state for each measured path
- accepted failures, currently an empty list unless a later reviewed release
  packet records one
- report refs for the latency baseline, regression report, and hot-path profile
- optional prerequisite rows such as Control Center render timing when safely
  skipped or blocked
- environment-safe summary, authority invariants, and report-safety flags

The integration is reporting-only inside `scripts/run_foundation_gate.py`.
`scripts/check_foundation_gate_latency.py` remains the dedicated latency gate
command. Optional local-model or frontend prerequisites may be `skipped` or
`blocked` only when the row remains visible and includes reason codes; unavailable
optional prerequisites must not block local developer report generation.

## Safety

Authority decisions must never be cached, skipped, shortened, or bypassed for
speed. The harness calls the real local route handlers with their existing
policy, approval, bearer, side-effect classification, OpenAPI, and Foundation
Gate checks intact. Budget changes must be made by changing
`RELEASE_LATENCY_BUDGETS_MS` and the verifier-backed table in this document, not
by weakening route authority.

Reports contain timing summaries, status, budgets, reason codes, and safe refs
only. They do not record request bodies, response bodies, provider payload
content, local path material, log material, machine identity, environment dumps,
or credential material. The environment-safe summary must not include hostname,
username, serial number, raw local paths, environment variable dumps, logs,
prompts, responses, provider payloads, or secrets.

## Local Setup

The benchmark enables only local/dev test authority inside its process for
routes that already require it:

- task decomposition local API bearer checks remain active
- M151 OpenWebUI local test gateway bearer checks remain active
- file preview uses a temporary safe root and records no local path material
- live llama.cpp prerequisites are not required for this baseline

Missing optional frontend timing support produces a safe skipped result instead
of a fabricated measurement.

## Rollback

To roll back generated evidence, delete
`reports/performance/latest_release_latency_baseline.json` and
`reports/performance/latest_release_latency_baseline.md`, plus
`reports/performance/latest_performance_regression_report.json` and
`reports/performance/latest_performance_regression_report.md`, plus
`reports/performance/latest_hot_path_profile.json` and
`reports/performance/latest_hot_path_profile.md`.

To roll back the baseline harness, revert the P0-006 changes to
`scripts/benchmark_foundation_gate.py`,
`scripts/check_foundation_gate_latency.py`, this document, and the associated
docs/Kanban/verifier links.

To roll back the P1-039 gate, revert the gate metadata, required-path coverage
checks, optional skipped/blocked status checks, and verifier/Kanban updates
added for UAA-P1-039.

To roll back the P1-040 reports, revert the regression report writer, Markdown
template, report retention guidance, tests, verifier rules, and Kanban updates
added for UAA-P1-040.

To roll back the P1-041 profiler, revert the hot-path profiling writer,
`scripts/profile_hot_paths.py`, Markdown template, docs, tests, verifier rules,
and Kanban updates added for UAA-P1-041.

To roll back the P1-043 Foundation Gate integration, revert the optional
`latency_gate` Foundation Gate report field, the `run_latency_gate_summary`
reuse path, the Foundation Gate Markdown Latency Gate section, and the associated
tests, docs, verifier rules, and Kanban updates.
