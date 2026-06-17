# Latency Review Report - Foundation Gate and Verification Pipeline

Date: 2026-06-17
Baseline reviewed: v1.7.3, commit `df7218a`
Scope: local code review, local timing runs, and latest GitHub Actions metadata. This report proposes latency reductions only. It does not propose removing safety checks, adding runtime authority, adding dependencies, or changing the contract-first product boundary.

## Executive Summary

The largest latency issue is duplicated verification. The current CI `verify` job runs `scripts/verify_all.py`, then runs `scripts/run_foundation_gate.py`, and Foundation Gate invokes `scripts/verify_all.py` again. The latest successful CI run spent 7m21s in master verification and then another 10m33s in Foundation Gate. A CI mode that runs the typed Foundation Gate report after master verification would preserve the same evidence while likely reducing the `verify` job from about 18m12s to about 7m40s before deeper code optimization.

The second largest issue is repeated repository scanning inside the Foundation Gate evaluator and verifier scripts. A gate-only run with commands skipped took 18.97s locally. Under profiler overhead it made 38,332,395 function calls, including 56,007 `pathlib.rglob` calls and 205,451 `posix.scandir` calls. The evaluator and verifier should use a per-process repository snapshot for tracked file lists, file text, lowercase text, and OpenAPI schema.

The third issue is test duplication. The Foundation Gate targeted test command covers 65 files, 223 tests, and took 155.70s locally. The slowest tests each instantiate the full Foundation Gate evaluator and cost about 16.8s to 17.8s. Many tests can safely share a session-scoped read-only gate report fixture while retaining separate tests for temp-root and selected-criteria behavior.

## Evidence

- Latest successful CI run: `27660190922` on `df7218a`, completed successfully.
- CI `verify` job duration: 18m12s.
- CI master verification step: 7m21s.
- CI Foundation Gate step: 10m33s.
- CI install step: 11s.
- Local full pytest observed previously: 5595 passed in 408.96s.
- Local `scripts/run_foundation_gate.py --skip-commands`: 18.97s real time.
- Profiled `scripts/run_foundation_gate.py --skip-commands`: 25.877s under profiler overhead, 38,332,395 calls.
- Profiled gate-only path: 56,007 `pathlib.rglob` calls, 205,451 `posix.scandir` calls.
- Local `scripts/verify_current_baseline.py`: 17.97s real time.
- Local `scripts/verify_skill_package_security_rule.py`: 0.04s real time.
- Local `scripts/verify_openapi_contract.py`: 0.87s real time.
- Local targeted Foundation Gate pytest command: 65 files, 223 passed, 155.70s.

## Finding 1: CI Re-runs the Master Verifier Inside Foundation Gate

Evidence:

- `.github/workflows/ci.yml` runs master verification at lines 30-31, Foundation Gate at lines 33-34, OpenAPI at lines 36-37, and Ruff at lines 39-40.
- `scripts/run_foundation_gate.py` lines 151-155 invoke targeted pytest, baseline verification, skill package verification, and `scripts/verify_all.py`.
- `scripts/verify_all.py` lines 28631-28653 already runs Ruff, full pytest, static scans, current baseline verification, documentation integrity verification, skill package verification, and OpenAPI verification.

Impact:

- The current CI path runs one full master verification, then runs another full master verification from inside Foundation Gate.
- The latest CI run spent 7m21s in the first master verification and 10m33s in Foundation Gate.
- This is the highest-confidence speedup because it does not require weakening any check.

Resolution:

- Keep the current Foundation Gate default as the full local/release command.
- Add an explicit CI mode, for example `scripts/run_foundation_gate.py --skip-commands` or a clearer `--command-mode report-only`.
- Update CI so the sequence is:
  - run `scripts/verify_all.py`
  - run `scripts/run_foundation_gate.py --skip-commands`
- Include command receipt metadata in the Foundation Gate report so the report states that prerequisite commands were satisfied externally by CI.
- Remove or demote the standalone OpenAPI and Ruff CI steps after `verify_all.py`, or keep them only as cheap explicit smoke checks. They are already covered by `verify_all.py`.

Expected effect:

- Immediate CI `verify` wall time should drop by roughly 10 minutes on the current workflow.
- The release/local full-gate path remains available and unchanged.

## Finding 2: Targeted Foundation Gate Tests Duplicate Full Pytest Work

Evidence:

- `scripts/run_foundation_gate.py` line 152 runs `pytest` over `GATE_TESTS`.
- The same Foundation Gate command later runs `scripts/verify_all.py`, which runs the full pytest suite.
- The targeted Foundation Gate set took 155.70s locally before the full pytest suite would run again.
- The slowest targeted tests were repeated full evaluator invocations:
  - `test_foundation_gate_evaluator_confirms_blocked_modules_are_absent`: 17.82s.
  - `test_foundation_gate_evaluator_passes_m8_runtime_checks`: 16.96s.
  - `test_gate_evaluator_report_contains_no_raw_secret_like_values`: 16.96s.
  - Several more full evaluator tests cluster around 16.8s.

Impact:

- The targeted set is useful as a fast failure path only if it avoids the full suite or runs before a different phase.
- In the current full gate command, it adds about 2m36s locally while `verify_all.py` later reruns full pytest.

Resolution:

- Add a Foundation Gate command mode that chooses one of:
  - targeted tests only
  - full `verify_all.py`
  - typed report only
- In the release/full mode, either run full pytest once through `verify_all.py`, or run targeted tests as a preflight and skip the later full pytest only when a separate full-suite receipt already exists.
- Add a session-scoped `foundation_gate_report` fixture for tests that only inspect the current repository's full report. Keep direct evaluator calls for temp-root, selected-criteria, and mutation tests.

Expected effect:

- Save about 2m36s from the full Foundation Gate command locally.
- Reduce test-suite tail latency from repeated 17s evaluator calls.

## Finding 3: Foundation Gate Repeatedly Walks and Reads the Repository

Evidence:

- `src/ultimate_ai_agent/core/gate/evaluators.py` is 52,616 lines.
- `scripts/verify_all.py` is 28,658 lines.
- `src/ultimate_ai_agent/core/gate/evaluators.py` has 176 `rglob` call sites and 120 `read_text` call sites.
- `scripts/verify_all.py` has 146 `rglob` call sites and 253 `read_text` call sites.
- Profiled gate-only execution made 56,007 `pathlib.rglob` calls and 205,451 `posix.scandir` calls.
- `FoundationGateEvaluator._tracked_runtime_files()` rebuilds the source file list with `self.src_root.rglob("*.py")`.
- `FoundationGateEvaluator._read()` reads file content directly every time without caching.

Impact:

- The typed Foundation Gate report costs about 19s even when all command execution is skipped.
- The same files and directories are scanned repeatedly for milestone-specific static safety checks.
- This cost grows with every milestone and every new checker.

Resolution:

- Introduce a per-evaluation `GateRepositorySnapshot` or `GateScanCache`.
- Build these once per evaluator instance:
  - tracked git files
  - source Python files
  - test Python files
  - docs Markdown files
  - Control Center source files
  - iOS skeleton files
  - file text by path
  - lowercase file text by path
  - OpenAPI schema
- Replace direct checker calls to `Path.rglob`, `Path.read_text`, `subprocess git ls-files`, and `app.openapi()` with snapshot helpers.
- Keep the cache process-local only. Do not persist it across commits or invocations.

Expected effect:

- Reduce `scripts/run_foundation_gate.py --skip-commands` from about 19s toward low single-digit seconds.
- Reduce static scan time inside `verify_all.py` once the same snapshot pattern is applied there.

## Finding 4: OpenAPI Schema Generation Is Repeated Across Verifiers, Gate Checks, and Tests

Evidence:

- `scripts/verify_all.py` has 129 `app.openapi()` call sites.
- `src/ultimate_ai_agent/core/gate/evaluators.py` has 137 `app.openapi()` call sites.
- Many gate integration tests also call OpenAPI-related checks.
- Standalone `scripts/verify_openapi_contract.py` is fast at 0.87s locally, but repeated schema generation inside larger scripts adds avoidable overhead.

Impact:

- The absolute standalone cost is small, but repeated schema creation across hundreds of checks compounds.
- It also makes the code harder to reason about because each checker owns its own route snapshot.

Resolution:

- Add a process-local OpenAPI schema helper to the gate/verifier context.
- Call `app.openapi()` once per process or once per explicit root/app context.
- Pass the cached `paths` mapping into milestone route-boundary helpers.
- Keep `scripts/verify_openapi_contract.py` as the authoritative standalone CLI, but avoid rerunning it in CI after `verify_all.py` unless desired as a cheap explicit smoke check.

Expected effect:

- Small to moderate direct speedup.
- Cleaner code and fewer chances of inconsistent route-boundary checks.

## Finding 5: `verify_current_baseline.py` Is Slow Enough To Deserve Its Own Cache Path

Evidence:

- Local `scripts/verify_current_baseline.py` took 17.97s.
- It prints many static guard checks that overlap with `scripts/verify_all.py` and Foundation Gate checks.
- It reads repo files and scans runtime source as a separate process.

Impact:

- Running it separately before or after master verification adds a visible 18s locally.
- Foundation Gate currently runs it before running `verify_all.py`, which runs baseline consistency again.

Resolution:

- Convert baseline checks into importable functions that accept the same repository snapshot/context used by `verify_all.py`.
- Preserve the CLI wrapper for direct local use.
- In CI and Foundation Gate, avoid running the standalone baseline script when `verify_all.py` has already emitted a baseline receipt.

Expected effect:

- Save about 18s on local gate paths before larger dedupe work.
- Make baseline verification more maintainable.

## Finding 6: `verify_all.py` Has No Per-Scan Timing Output

Evidence:

- `scripts/verify_all.py` prints scan names and then runs the entire `SCAN_SEQUENCE`.
- It does not emit per-scan durations or a machine-readable timing artifact.

Impact:

- The project cannot see which static scans regress over time.
- Performance work has to rely on external shell timing and profiling.

Resolution:

- Add optional timing output, for example `scripts/verify_all.py --timings-json reports/verification_timings/latest.json`.
- Wrap each static scan and subprocess verifier with `time.perf_counter()`.
- Record status, duration, and scan name.
- Keep text output unchanged by default except for concise elapsed summaries.

Expected effect:

- No direct speedup, but it makes future latency regressions visible and cheap to debug.

## Finding 7: Full Pytest Dominates Master Verification Wall Time

Evidence:

- Previous local full pytest in `verify_all.py`: 5595 passed in 408.96s.
- Latest CI master verification step: 7m21s.
- Many milestone tests are deterministic contract tests with no external services.

Impact:

- Even after Foundation Gate dedupe, full pytest remains the largest single verification cost.

Resolution:

- Add CI matrix sharding by stable test groups, for example core contracts, API, gate integration, mobile/checkpoints, and safety scanners.
- Prefer matrix sharding before adding `pytest-xdist`, because sharding avoids new dependencies and keeps side effects easier to audit.
- Add a changed-file-aware presubmit mode for local developer use, while keeping the full suite for main/release gates.
- Run `pytest --durations=50` on scheduled or release verification and publish the slow-test list as an artifact.

Expected effect:

- CI wall time can drop substantially if test shards run in parallel.
- Full coverage remains intact for protected branches and release gates.

## Finding 8: Report-Only Gate Runs Still Rewrite Latest Reports

Evidence:

- `scripts/run_foundation_gate.py --skip-commands` still writes `reports/foundation_gate/latest_foundation_gate_report.json` and `.md`.
- `write_markdown()` reads JSON back from disk immediately after `report.model_dump_json()` was already available in memory.

Impact:

- Minor latency impact, but it creates unnecessary file churn during profiling and local inspection.

Resolution:

- Add `--no-write-latest` or `--output-only` for profiling/report-only runs.
- Generate Markdown from the in-memory report object instead of re-reading JSON from disk.

Expected effect:

- Small speedup and cleaner working trees during local review.

## Recommended Implementation Order

1. Add Foundation Gate command modes and update CI to avoid running `verify_all.py` twice.
2. Add Foundation Gate report command-receipt metadata so CI can prove prerequisite checks were satisfied externally.
3. Add a session-scoped full gate report fixture for read-only gate integration tests.
4. Add a `GateRepositorySnapshot` to cache file lists, file text, lowercase text, git tracked files, and OpenAPI schema.
5. Port the highest-volume evaluator checks to the snapshot helpers.
6. Add `VerifyContext` and timing output to `scripts/verify_all.py`.
7. Split CI pytest into stable matrix shards after timing data identifies clean boundaries.

## Suggested Acceptance Criteria

- `scripts/verify_all.py` still passes.
- `scripts/run_foundation_gate.py` full mode still passes and remains the local release gate.
- CI splits lint, pytest, static verification, and typed Foundation Gate report jobs so coverage remains complete while the slow legs run in parallel.
- Foundation Gate report includes enough receipt metadata to show whether commands were run directly or satisfied by CI.
- `scripts/run_foundation_gate.py --command-mode ci-parallel --no-write-latest` stays bounded to typed report generation plus an external verification receipt.
- The core Python CI path is bounded by the slowest parallel job without removing checks.
- No recommendation grants runtime authority, shell execution, browser execution, network authority, mobile sensor runtime, backend routes, Control Center controls, dependencies, memory writes, context injection, model/provider calls, beta release, or production authority.

## Implementation Pass Results

Implemented on 2026-06-17:

- Added Foundation Gate command modes:
  - `full`: runs `scripts/verify_all.py` once before the typed report.
  - `legacy-full`: preserves the previous targeted-test plus baseline plus skill plus `verify_all.py` sequence.
  - `targeted-tests`: runs the targeted Foundation Gate pytest set only.
  - `verify-all`: runs the master verifier only.
  - `report-only`: generates the typed report only.
  - `ci-after-verify-all`: records that master verification was satisfied by a preceding CI step.
  - `ci-parallel`: records that lint, pytest, and static verification are satisfied by required parallel CI jobs.
- Added Foundation Gate command receipts to the typed report.
- Updated CI so lint, pytest, static verification, and Foundation Gate report generation run as separate jobs.
- Changed the static verification job to run `scripts/verify_all.py --skip-ruff --skip-pytest`, leaving Ruff and pytest to their dedicated jobs.
- Added skip flags to `scripts/verify_all.py` and `scripts/verify_current_baseline.py` so CI can avoid duplicated static scans while preserving standalone full verification defaults.
- Enabled pip caching in the Python CI setup.
- Added `--no-write-latest` to Foundation Gate for profiling/report-only runs that should not dirty tracked reports.
- Changed Foundation Gate Markdown generation to use the in-memory report payload instead of re-reading JSON from disk.
- Added a session-scoped Foundation Gate report fixture for read-only current-repo gate tests.
- Added a repository-scoped filesystem cache around Foundation Gate evaluation for repeated `Path.rglob()` and `Path.read_text()` calls under the repo root. Temporary-file safety probes remain uncached.
- Added `scripts/verify_all.py --timings-json` for per-phase and per-static-scan timing records.

Measured after implementation:

- Targeted Foundation Gate pytest set:
  - Before: 223 passed in 155.70s, 156.14s wall-clock wrapper time.
  - After first pass: 224 passed in 21.95s, 22.59s wall-clock wrapper time.
  - After second pass: 224 passed in 15.86s, 16.50s wall-clock wrapper time.
- Typed Foundation Gate report-only path:
  - Before: 18.97s real time.
  - After filesystem cache: 13.23s real time.
- Full pytest inside `verify_all.py`:
  - Before observed baseline: 5595 passed in 408.96s.
  - After implementation: 5602 passed in 219.30s.
- Full `scripts/verify_all.py --timings-json /tmp/uaa_verify_all_timings_after_latency.json` passed.
  - Timed phases total: 258,368ms.
  - Pytest: 220,268ms.
  - Current baseline verifier: 18,403ms.
  - OpenAPI verifier: 839ms.
- Final local CI-parallel measurements after the pytest-focused cleanup:
  - `scripts/run_foundation_gate.py --command-mode ci-parallel --no-write-latest`: 12.67s real time.
  - `scripts/verify_all.py --skip-ruff --skip-pytest --timings-json /tmp/uaa_static_verification_timings_after_ci_parallel.json`: 18.29s real time.
  - `python -m pytest -q --durations=50 --durations-min=0.05`: 5607 passed in 52.71s, 53.70s real time.
  - `python -m ruff check .`: passed.
  - Comparable core Python CI wall time is now bounded by pytest at about 54s locally, before GitHub runner setup/install overhead.

Remaining latency opportunities:

- `scripts/verify_current_baseline.py` still costs about 18s and overlaps with static checks in `verify_all.py`.
- Typed Foundation Gate report generation is now dominated by contract validation and import/model-construction costs rather than filesystem traversal.
- Further reductions should focus on import flattening, reusable validator fixtures for generated milestone chains, and sharing baseline-verifier context with `verify_all.py`.

## Hermes Router Follow-Up Pass

Reviewed `/Users/sambehdjou/Documents/GitHub/hermes-router` for transferable latency work.

Borrowed patterns:

- Hermes keeps latency checks as small standalone benchmark and guard scripts with JSON output and environment-overridable budgets.
- Hermes precomputes config-derived routing data on initialized router objects instead of rebuilding it during every candidate decision.
- Hermes avoids extra full-list ranking work on hot paths when only the top decision is required.

Implemented in UAA:

- Added `scripts/benchmark_foundation_gate.py` for side-effect-free typed Foundation Gate evaluator timing.
- Added `scripts/check_foundation_gate_latency.py` with `FOUNDATION_GATE_MAX_BEST_MS` and `FOUNDATION_GATE_MAX_MEAN_MS` budget overrides.
- Added tests for the benchmark and latency guard script behavior.
- Updated the UAA model router to prepare policy-derived provider/capability sets once per route request.
- Replaced full eligible-candidate sorting with `min(...)` when selecting the single best model-route candidate.

Not borrowed:

- Hermes's prompt-scoring regex and `route_fast(...)` internals are router-domain-specific and do not safely map onto UAA's contract-first Foundation Gate.
- The new Foundation Gate latency guard is not wired into `verify_all.py` by default, because mandatory benchmarking would add latency to the normal verification path.
