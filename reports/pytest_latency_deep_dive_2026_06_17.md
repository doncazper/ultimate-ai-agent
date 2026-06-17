# Pytest Latency Deep Dive - 2026-06-17

Scope: local pytest profiling for the Ultimate AI Agent repo. This report assesses why the test suite is slow and lists safe speedup options. It does not remove safety checks, weaken Foundation Gate coverage, add runtime authority, or change product behavior.

## Measurements

Commands run:

- `/usr/bin/time -p .venv/bin/python -m pytest --collect-only -q > /tmp/uaa_pytest_collect_20260617.txt`
- `/usr/bin/time -p .venv/bin/python -m pytest -q --durations=250 --durations-min=0.05 > /tmp/uaa_pytest_durations_20260617.txt`
- `/usr/bin/time -p .venv/bin/python -m pytest -q tests/test_m*_gate_integration.py tests/test_m75_browser_action_gate_integration.py tests/test_m76_openwebui_runtime_bridge_gate_integration.py tests/test_m79_plugin_install_review_gate_integration.py --durations=120 --durations-min=0.05 > /tmp/uaa_pytest_gate_integrations_20260617.txt`
- `/usr/bin/time -p .venv/bin/python -m pytest -q tests/test_m125*.py tests/test_m126*.py tests/test_m127*.py tests/test_m128*.py tests/test_m129*.py tests/test_m130*.py --durations=120 --durations-min=0.05 > /tmp/uaa_pytest_connector_block_20260617.txt`

Observed results:

| Run | Result | Wall time |
| --- | ---: | ---: |
| Collection only | 5,614 collected node lines | 2.23s |
| Full pytest | 5,606 passed, 1 warning | 220.50s real / 219.53s pytest |
| Gate integration slice | 519 passed, 1 warning | 128.18s real / 127.50s pytest |
| M125-M130 connector slice | 210 passed | 58.11s real / 57.53s pytest |

Interpretation:

- Collection/import is not the main problem; collection is only about 1% of full runtime.
- Gate integration tests are the largest structural bucket, at about 58% of full suite wall time.
- M125-M130 connector tests are the second major bucket, at about 26% of full suite wall time. This overlaps slightly with the gate slice because it includes M125-M130 gate integration tests.
- The remaining time is mostly many small contract tests in the 0.05s-0.25s range.

## Slowest Hotspots

Full suite slowest records:

- `tests/test_m43_gate_integration.py::test_m43_gate_criteria_are_registered_and_pass` - 11.73s
- `tests/test_m40_gate_integration.py::test_m40_gate_criteria_are_registered_and_pass` - 11.73s
- `tests/test_run_foundation_gate_script.py::test_run_foundation_gate_ci_mode_records_external_verify_receipt` - 11.69s
- `tests/test_foundation_gate_blocked_modules.py::test_foundation_gate_evaluator_confirms_blocked_modules_are_absent` setup - 11.68s
- `tests/test_m39_gate_integration.py::test_m39_gate_criteria_are_registered_and_pass` - 11.67s
- `tests/test_m41_gate_integration.py::test_m41_gate_criteria_are_registered_and_pass` - 11.66s
- `tests/test_m37_gate_integration.py::test_m37_gate_criteria_are_registered_and_pass` - 11.65s
- `tests/test_m44_gate_integration.py::test_m44_gate_criteria_are_registered_and_pass` - 11.65s
- `tests/test_m42_gate_integration.py::test_m42_gate_criteria_are_registered_and_pass` - 11.65s
- `tests/test_m38_gate_integration.py::test_m38_gate_criteria_are_registered_and_pass` - 11.64s
- `tests/test_run_foundation_gate_script.py::test_run_foundation_gate_writes_requested_output` - 11.62s

Gate integration slice slowest records:

- One shared `foundation_gate_results` session fixture setup: 12.05s.
- M37-M44 current-repo positive tests: about 11.56s-11.71s each.
- Modern milestone current-repo positive tests are much cheaper, generally about 0.09s-0.80s each, because they evaluate selected criteria instead of the whole gate.

Connector slice slowest records:

- M128/M129 exact binding tests: 2.63s-2.66s.
- M129 runtime/revocation policy denial test: 1.75s.
- M128/M129 model-copy revalidation tests: about 0.90s.
- Many M125-M130 parametrized Pydantic validation tests: about 0.29s-0.32s each.

## Root Causes

### 1. Repeated Full Foundation Gate Evaluations

The repo now has a session-scoped `foundation_gate_report` / `foundation_gate_results` fixture, and that one full gate setup costs about 12s. That is acceptable if reused.

The slow tail comes from additional full gate evaluations, especially:

- `tests/test_m37_gate_integration.py`
- `tests/test_m38_gate_integration.py`
- `tests/test_m39_gate_integration.py`
- `tests/test_m40_gate_integration.py`
- `tests/test_m41_gate_integration.py`
- `tests/test_m42_gate_integration.py`
- `tests/test_m43_gate_integration.py`
- `tests/test_m44_gate_integration.py`
- `tests/test_run_foundation_gate_script.py`

The older M37-M44 tests call `FoundationGateEvaluator().evaluate(criteria)` where `criteria` is the full default list. They only need to prove their own milestone criteria are registered and passing, so each test is effectively paying for a full typed gate run.

### 2. Script Tests Exercise Full Gate Logic When They Mostly Test CLI Plumbing

`tests/test_run_foundation_gate_script.py` invokes `run_foundation_gate.main(...)` twice. Each call generates a full Foundation Gate report. The assertions are mostly about command mode, command receipts, output writing, and atomic JSON behavior, not deep gate evaluation correctness.

### 3. Connector Tests Rebuild Deep Source-Record Chains Per Test

M125-M130 tests repeatedly build nested source records:

- mobile approval renewal
- mobile kill switch/revocation
- mobile sensor audit/hardening
- production threat model through readiness review
- email/calendar/contacts/messages connector contracts
- read-only runtime records
- approval and dry-run/write execution records

Those objects are Pydantic models with `model_validator` hooks. The tests intentionally revalidate mutated copies, but many tests rebuild the same valid ancestor chain from scratch before mutating one field.

### 4. Large Parametrized Safety Matrices Are Correct But Expensive

The M125-M130 safety matrices are valuable because they protect authority boundaries. The cost is cumulative: many individual tests take only about 0.29s, but there are many of them.

### 5. Collection Is Fine

Collection took 2.23s, so import discovery and pytest collection are not the main problem. Avoid spending engineering time here until the gate and connector buckets are fixed.

## Speedup Options

### Option A - Reuse Session Gate Results For Current-Repo Positive Gate Tests

Change older current-repo positive tests to use `foundation_gate_results` for positive pass assertions, while keeping targeted failure probes on `tmp_path` as direct evaluator calls.

Targets:

- M37-M44 current-repo positive tests first.
- Any remaining current-repo tests that call the full criteria list.

Expected impact:

- Save roughly 80s-95s from full pytest.
- Gate integration slice could drop from about 128s to about 30s-45s.

Risk:

- Low if each test still asserts its milestone criterion IDs exist and the shared result status is passed.
- Keep direct evaluator tests for custom `tmp_path` negative cases.

### Option B - Make `run_foundation_gate` Script Tests Use A Fake Report For CLI Plumbing

Monkeypatch `scripts.run_foundation_gate.FoundationGateEvaluator` in command-mode and output-writing tests so they verify CLI/report-writing behavior without rebuilding the full gate twice.

Keep one real integration path covered by:

- the session fixture,
- `scripts/check_foundation_gate_latency.py`,
- or one explicit slow script integration test if desired.

Expected impact:

- Save about 23s from full pytest.

Risk:

- Low to medium. The test will cover script plumbing, not full gate correctness. That is acceptable if full gate correctness remains covered elsewhere.

### Option C - Add Module-Scoped Connector Source Fixtures

For M125-M130 tests, build the valid source record chain once per module and reuse it. For mutation tests, call `model_copy(update=...)` or construct only the final request layer from a cached valid source.

Targets:

- `_m120_source_record()`
- `_m124_source_record()`
- `_runtime_record()`
- `_approval_decision(...)`
- M128/M129 source decision/report builders

Expected impact:

- Save roughly 25s-40s in the connector block.
- Full suite could drop another 20s-35s after accounting for overlap.

Risk:

- Medium. Shared Pydantic objects must not be mutated in-place. Prefer immutable use plus per-test copies.

### Option D - Split Positive Chain Construction From Negative Matrix Validation

For repeated denial matrices, create one known-good request payload dict once, then update one field per case. Avoid rebuilding every upstream record chain for every parametrized case.

Expected impact:

- Similar to Option C, possibly stronger for M126-M129.

Risk:

- Medium. The tests must still prove builder functions create safe records at least once per milestone.

### Option E - Add Explicit Test Markers And Fast Local Profiles

Add pytest markers such as:

- `gate`
- `slow_gate`
- `connector_chain`
- `contract_matrix`

Then provide documented commands:

- fast local unit loop excluding slow gates,
- full local safety suite,
- CI full suite.

Expected impact:

- No reduction for full CI by itself.
- Better developer feedback loop immediately.

Risk:

- Low if CI still runs all tests.

### Option F - Evaluate `pytest-xdist` After Reducing Duplicate Full Gate Runs

Adding `pytest-xdist` could reduce wall time by running independent files in parallel.

Important sequencing:

- Do not add parallelism before removing duplicate full Foundation Gate evaluations, or each worker may repeat expensive session fixtures.
- Use `--dist loadfile` or similar grouping to avoid fixture churn.

Expected impact:

- After Options A-D, full suite could plausibly fall below 60s-90s on a multi-core local machine.

Risk:

- Medium. This adds a dev dependency and can expose hidden test order/global-state coupling.

### Option G - Keep Pytest Duration Reporting In CI

Run pytest with `--durations=50 --durations-min=0.05` in CI or as an optional timing job. This catches future regressions like a reintroduced full gate call.

Expected impact:

- No direct speedup, but good regression prevention.

Risk:

- Low.

## Recommended Implementation Order

1. Convert M37-M44 current-repo positive tests to `foundation_gate_results`.
2. Monkeypatch `run_foundation_gate` script plumbing tests to avoid full gate evaluation.
3. Add a helper for current-repo gate result assertions to make future tests use the fast path by default.
4. Add module-scoped connector source fixtures for M125-M130.
5. Re-run full pytest with `--durations=250`.
6. If full suite remains above 90s, evaluate `pytest-xdist` with `--dist loadfile`.

## Expected Outcome

Conservative expected full-suite improvement:

- Current: about 220s.
- After Options A-B: about 105s-125s.
- After Options C-D: about 75s-100s.
- With safe parallelism after cleanup: potentially below 60s-90s depending on core count and disk contention.

## Implementation Results

Implemented on 2026-06-17:

- Converted M37-M44 current-repo positive gate tests to reuse the session `foundation_gate_results` report instead of re-running the full Foundation Gate in each file.
- Kept M37-M44 criterion registration checks and route/surface negative probes intact.
- Changed `tests/test_run_foundation_gate_script.py` command-mode and output-writing tests to use a one-criterion fake evaluator that still produces a real `FoundationGateReport` payload.
- Added in-module cached source-record builders for M125-M130 connector tests where the source records are reused read-only.
- Fixed eager expensive defaults in M128 and M129 request helpers so overridden source decisions/results no longer build unused default chains.

Validation after implementation:

| Run | Before | After |
| --- | ---: | ---: |
| Focused changed tests | not measured as a group | 212 passed in 17.09s |
| Gate integration slice | 128.18s real / 127.50s pytest | 33.57s real / 32.86s pytest |
| M125-M130 connector slice | 58.11s real / 57.53s pytest | 7.62s real / 7.07s pytest |
| Full pytest | 220.50s real / 219.53s pytest | 52.58s real / 51.60s pytest |
| Final full pytest confirmation | 220.50s real / 219.53s pytest | 53.70s real / 52.71s pytest, 5607 passed |

CI-parallel follow-up implemented after the test cleanup:

- `scripts/verify_all.py` now has skip flags for CI sharding, while default standalone verification remains complete.
- `scripts/verify_current_baseline.py --skip-static-scans` allows a caller that already ran static scans to avoid repeating them.
- `scripts/run_foundation_gate.py --command-mode ci-parallel --no-write-latest` records an external parallel-CI receipt and generates the typed report without rerunning lint, pytest, or static verification.
- `.github/workflows/ci.yml` now runs `lint`, `pytest`, `static-verification`, and `foundation-gate-report` as separate jobs.

Final local measurements for those parallel legs:

| CI leg | Local result |
| --- | ---: |
| Ruff lint | passed |
| Pytest | 5607 passed in 52.71s / 53.70s real |
| Static verification without Ruff/Pytest | passed in 18.29s real |
| Foundation Gate `ci-parallel` report | passed in 12.67s real |

Comparable core Python CI wall time is now bounded by pytest at about 54s locally, before GitHub runner setup/install overhead.

Remaining slowest records after implementation:

- One shared full Foundation Gate fixture setup: about 11.0s.
- `tests/test_openapi_contract.py::test_export_openapi_script_writes_valid_json_to_stdout`: about 0.85s.
- M121-M127 gate/current-repo positive tests and connector source-binding checks: generally 0.2s-0.8s.
- Documentation integrity tests: about 0.39s each.

Additional safe next opportunities:

- Cache or fixture common M121-M124 connector source records, similar to M125-M130.
- Reduce remaining per-milestone current-repo gate checks by grouping consecutive milestone criteria where a single shared report already covers them.
- Add CI pytest duration reporting so future duplicate full-gate calls are visible immediately.
- Evaluate `pytest-xdist` only after confirming all tests are order-independent; after this cleanup, parallelism should be much less wasteful.

## Non-Goals

Do not speed this up by:

- removing Foundation Gate criteria,
- deleting safety matrix cases,
- weakening authority-boundary assertions,
- skipping current-repo verification in CI,
- hiding failures behind broad mocks,
- adding runtime authority, network calls, model calls, shell execution, or production behavior.
