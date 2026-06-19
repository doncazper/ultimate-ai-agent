# Release Latency Baseline Harness

Status: active UAA-P0-006 performance baseline harness

Scope: production-readiness latency evidence for local release-critical paths

This harness makes p50 and p95 latency visible for release review without
granting runtime authority. It measures the existing Foundation Gate evaluator
and the release-critical local FastAPI paths through `TestClient`, then writes
redacted timing summaries under `reports/performance`.

## Commands

```bash
.venv/bin/python scripts/benchmark_foundation_gate.py
.venv/bin/python scripts/check_foundation_gate_latency.py
```

`scripts/benchmark_foundation_gate.py` writes:

- `reports/performance/latest_release_latency_baseline.json`
- `reports/performance/latest_release_latency_baseline.md`

`scripts/check_foundation_gate_latency.py` fails when the typed Foundation Gate
status fails, the Foundation Gate evaluator exceeds its budget, or any required
release latency path misses its p95 budget.

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
`skipped-ref:p0-006:control-center-render-runner-not-scoped` until a reviewed
frontend render timing runner is added. The backend release paths are required.

## Safety

Authority decisions must never be cached, skipped, shortened, or bypassed for
speed. The harness calls the real local route handlers with their existing
policy, approval, bearer, side-effect classification, OpenAPI, and Foundation
Gate checks intact.

Reports contain timing summaries, status, budgets, reason codes, and safe refs
only. They do not record request bodies, response bodies, provider payload
content, local path material, log material, machine identity, environment dumps,
or credential material.

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
`reports/performance/latest_release_latency_baseline.md`.

To roll back the harness, revert the P0-006 changes to
`scripts/benchmark_foundation_gate.py`,
`scripts/check_foundation_gate_latency.py`, this document, and the associated
docs/Kanban/verifier links.
