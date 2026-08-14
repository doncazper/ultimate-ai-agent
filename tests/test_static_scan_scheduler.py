from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.verification import static_scan_worker
from scripts.verification.cpu_budget import (
    CPU_BUDGET_ENV,
    capped_worker_count,
    resolve_cpu_budget,
)
from scripts.verification import run_static_scan_shards
from scripts.verification import run_static_verification_lane
from scripts.verification.run_static_scan_shards import (
    _ActiveWorker,
    StaticScanOutcome,
    _complete_outcomes,
    _parse_outcomes,
    _run_batch,
    _safe_run_root,
)
from scripts.verification.static_scan_context import (
    StaticVerificationContext,
    resolve_repository_sha,
)
from scripts.verification.static_scan_plan import (
    APPROVED_PARALLEL_REGISTRY_FINGERPRINT,
    STATIC_PLAN_SCHEMA,
    StaticScanSpec,
    assign_static_shards,
    build_scan_specs,
    exclusive_plans,
    plan_fingerprint,
    scan_registry_fingerprint,
)


def _approved_specs(
    sequence: tuple[tuple[str, str], ...],
) -> tuple[StaticScanSpec, ...]:
    return build_scan_specs(
        sequence,
        approved_parallel_registry_fingerprint=scan_registry_fingerprint(sequence),
    )


def test_cpu_budget_defaults_caps_and_rejects_invalid_values() -> None:
    assert resolve_cpu_budget(environ={}, cpu_count=12) == 8
    assert resolve_cpu_budget(6, environ={}, cpu_count=12) == 6
    assert resolve_cpu_budget(20, environ={}, cpu_count=4) == 4
    assert resolve_cpu_budget(environ={CPU_BUDGET_ENV: "3"}, cpu_count=12) == 3
    with pytest.raises(ValueError, match="positive integer"):
        resolve_cpu_budget(environ={CPU_BUDGET_ENV: "many"}, cpu_count=8)
    with pytest.raises(ValueError, match="between 1"):
        resolve_cpu_budget(0, environ={}, cpu_count=8)


def test_worker_count_never_exceeds_cpu_budget() -> None:
    assert capped_worker_count(8, 4) == 4
    with pytest.raises(ValueError, match="greater than zero"):
        capped_worker_count(0, 4)


def test_scan_registry_rejects_duplicate_names_and_functions() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        build_scan_specs(())
    with pytest.raises(ValueError, match="duplicate static scan name"):
        build_scan_specs((("same", "one"), ("same", "two")))
    with pytest.raises(ValueError, match="duplicate static scan function"):
        build_scan_specs((("one", "same"), ("two", "same")))


def test_timing_aware_plans_are_complete_balanced_and_stable() -> None:
    sequence = (
        ("slow", "slow_scan"),
        ("medium", "medium_scan"),
        ("quick-a", "quick_a_scan"),
        ("quick-b", "quick_b_scan"),
    )
    specs = _approved_specs(sequence)
    timings = {
        "slow_scan": 1000.0,
        "medium_scan": 600.0,
        "quick_a_scan": 200.0,
        "quick_b_scan": 200.0,
    }

    plans = assign_static_shards(specs, 2, timings)

    assigned = [spec.index for plan in plans for spec in plan.scans]
    assert sorted(assigned) == [0, 1, 2, 3]
    assert len(assigned) == len(set(assigned))
    assert [plan.expected_milliseconds for plan in plans] == [1000.0, 1000.0]
    assert plan_fingerprint(plans) == plan_fingerprint(
        assign_static_shards(specs, 2, timings)
    )


def test_scan_plans_keep_api_affinity_and_exclusive_lanes() -> None:
    sequence = (
        ("generated", "verify_no_generated_artifacts"),
        ("maturity", "verify_operational_maturity"),
        ("api-80", "verify_uaa_p1_080_api_route_classification"),
        ("api-81", "verify_uaa_p1_081_fastapi_security_headers"),
        ("other", "other_scan"),
    )
    specs = _approved_specs(sequence)

    plans = assign_static_shards(specs, 3, {})
    worker_by_function = {
        spec.function_name: plan.index for plan in plans for spec in plan.scans
    }

    assert "verify_no_generated_artifacts" not in worker_by_function
    assert (
        worker_by_function["verify_uaa_p1_080_api_route_classification"]
        == (worker_by_function["verify_uaa_p1_081_fastapi_security_headers"])
    )
    serial_lane = exclusive_plans(specs)
    assert len(serial_lane) == 1
    assert [spec.function_name for spec in serial_lane[0].scans] == [
        "verify_no_generated_artifacts",
        "verify_operational_maturity",
    ]


def test_current_registry_is_exact_and_unknown_scans_fail_closed_serial() -> None:
    current = tuple(static_scan_worker.legacy.SCAN_SEQUENCE)

    assert scan_registry_fingerprint(current) == (
        APPROVED_PARALLEL_REGISTRY_FINGERPRINT
    )
    drifted = (*current, ("unreviewed", "unreviewed_scan"))
    specs = build_scan_specs(drifted)

    assert assign_static_shards(specs, 4) == ()
    serial = exclusive_plans(specs)
    assert len(serial) == 1
    assert len(serial[0].scans) == len(drifted)


def test_complete_outcomes_fails_closed_for_missing_or_duplicate_results() -> None:
    specs = build_scan_specs((("one", "one_scan"), ("two", "two_scan")))
    duplicate = StaticScanOutcome(
        0,
        specs[0].scan_ref,
        specs[0].name,
        specs[0].function_name,
        "passed",
        1,
    )

    outcomes = _complete_outcomes(specs, (duplicate, duplicate))

    assert outcomes[0].failure_ref == "coverage-ref:duplicate-result"
    assert outcomes[1].status == "not_run"
    assert outcomes[1].failure_ref == "coverage-ref:missing-result"

    unexpected = StaticScanOutcome(
        99,
        "static-scan-ref:099",
        "unexpected",
        "unexpected_scan",
        "passed",
        1,
    )
    unexpected_outcomes = _complete_outcomes(
        specs, (duplicate, outcomes[1], unexpected)
    )
    assert unexpected_outcomes[0].status == "failed"
    assert unexpected_outcomes[0].failure_ref == "coverage-ref:unexpected-result"


def test_static_context_caches_reads_and_restores_path_methods(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sample.txt"
    source.write_text("first", encoding="utf-8")
    original_read_text = Path.read_text
    context = StaticVerificationContext.capture(
        tmp_path,
        ("scan-ref:test",),
        "a" * 40,
        "static-registry-ref:sha256:" + "b" * 64,
    )

    with context.cached_repository_view():
        assert source.read_text(encoding="utf-8") == "first"
        source.write_text("second", encoding="utf-8")
        assert source.read_text(encoding="utf-8") == "first"

    assert Path.read_text is original_read_text
    assert source.read_text(encoding="utf-8") == "second"


def test_run_root_does_not_change_caller_owned_base_permissions(tmp_path: Path) -> None:
    base = tmp_path / "caller-owned"
    base.mkdir(mode=0o755)

    run_root = _safe_run_root(base)

    assert base.stat().st_mode & 0o777 == 0o755
    assert run_root.parent == base
    assert run_root.stat().st_mode & 0o777 == 0o700
    shutil.rmtree(run_root)


def test_worker_stops_after_first_failure_and_emits_safe_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def passing() -> None:
        calls.append("passed")

    def failing() -> None:
        calls.append("failed")
        raise SystemExit(1)

    def unreachable() -> None:
        calls.append("unreachable")

    monkeypatch.setattr(
        static_scan_worker.legacy,
        "SCAN_SEQUENCE",
        [("pass", "test_pass"), ("fail", "test_fail"), ("later", "test_later")],
    )
    monkeypatch.setattr(static_scan_worker.legacy, "test_pass", passing, raising=False)
    monkeypatch.setattr(static_scan_worker.legacy, "test_fail", failing, raising=False)
    monkeypatch.setattr(
        static_scan_worker.legacy, "test_later", unreachable, raising=False
    )
    repository_sha = resolve_repository_sha(Path(__file__).resolve().parents[1])
    registry_fingerprint = scan_registry_fingerprint(
        static_scan_worker.legacy.SCAN_SEQUENCE
    )
    specs = build_scan_specs(static_scan_worker.legacy.SCAN_SEQUENCE)
    context = StaticVerificationContext.capture(
        static_scan_worker.ROOT,
        tuple(spec.scan_ref for spec in specs),
        repository_sha,
        registry_fingerprint,
    )
    plan = tmp_path / "plan.json"
    result = tmp_path / "result.json"
    progress = tmp_path / "progress.json"
    plan.write_text(
        json.dumps(
            {
                "schema_version": STATIC_PLAN_SCHEMA,
                "context_ref": context.snapshot_ref,
                "registry_fingerprint": registry_fingerprint,
                "repository_sha": repository_sha,
                "scan_indices": [0, 1, 2],
            }
        ),
        encoding="utf-8",
    )

    assert static_scan_worker.run_worker(plan, result, progress) == 1

    payload = json.loads(result.read_text(encoding="utf-8"))
    assert calls == ["passed", "failed"]
    assert [item["status"] for item in payload["outcomes"]] == ["passed", "failed"]
    assert payload["outcomes"][1]["failure_ref"] == "exception-ref:SystemExit"
    assert str(tmp_path) not in json.dumps(payload)


def test_scan_timeout_stops_worker_and_emits_identity_bound_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = _approved_specs((("slow", "slow_scan"),))[0]
    plan = assign_static_shards((spec,), 1)[0]

    class HangingProcess:
        returncode: int | None = None
        pid = None

        def poll(self) -> int | None:
            return self.returncode

    process = HangingProcess()
    worker = _ActiveWorker(
        plan=plan,
        process=process,  # type: ignore[arg-type]
        result_path=tmp_path / "result.json",
        progress_path=tmp_path / "progress.json",
        context_ref="static-context-ref:sha256:" + "c" * 64,
        registry_fingerprint="static-registry-ref:sha256:" + "b" * 64,
        repository_sha="a" * 40,
        launched_at=time.perf_counter(),
    )

    monkeypatch.setattr(
        run_static_scan_shards,
        "_launch_worker",
        lambda *args, **kwargs: worker,
    )
    monkeypatch.setattr(
        run_static_scan_shards,
        "_progress_scan_index",
        lambda active: spec.index,
    )

    def stop_processes(processes: object, grace_seconds: float) -> None:
        assert grace_seconds >= 0
        process.returncode = -15

    monkeypatch.setattr(
        run_static_scan_shards.shard_processes,
        "stop_processes",
        stop_processes,
    )

    outcomes, timed_out = _run_batch(
        (plan,),
        root=tmp_path,
        run_root=tmp_path,
        base_env={},
        scan_timeout_seconds=0.001,
        deadline=time.perf_counter() + 1,
        safe_summary=True,
        batch_ref="timeout-test",
        repository_sha="a" * 40,
        registry_fingerprint="static-registry-ref:sha256:" + "b" * 64,
    )

    assert timed_out is True
    assert len(outcomes) == 1
    assert outcomes[0].scan_ref == spec.scan_ref
    assert outcomes[0].status == "timed_out"
    assert outcomes[0].failure_ref == "timeout-ref:static-scan"


def test_partial_worker_launch_failure_stops_started_processes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = _approved_specs((("one", "one_scan"), ("two", "two_scan")))
    plans = assign_static_shards(specs, 2)

    class RunningProcess:
        returncode = None

    process = RunningProcess()
    first_worker = _ActiveWorker(
        plan=plans[0],
        process=process,  # type: ignore[arg-type]
        result_path=tmp_path / "result.json",
        progress_path=tmp_path / "progress.json",
        context_ref="static-context-ref:sha256:" + "c" * 64,
        registry_fingerprint="static-registry-ref:sha256:" + "b" * 64,
        repository_sha="a" * 40,
        launched_at=time.perf_counter(),
    )
    launches = 0

    def launch(*args: object, **kwargs: object) -> _ActiveWorker:
        nonlocal launches
        launches += 1
        if launches == 1:
            return first_worker
        raise RuntimeError("synthetic launch failure")

    stopped: list[object] = []
    monkeypatch.setattr(run_static_scan_shards, "_launch_worker", launch)
    monkeypatch.setattr(
        run_static_scan_shards.shard_processes,
        "stop_processes",
        lambda processes, grace: stopped.extend(processes),
    )

    with pytest.raises(RuntimeError, match="synthetic launch failure"):
        _run_batch(
            plans,
            root=tmp_path,
            run_root=tmp_path,
            base_env={},
            scan_timeout_seconds=1,
            deadline=time.perf_counter() + 10,
            safe_summary=True,
            batch_ref="launch-test",
            repository_sha="a" * 40,
            registry_fingerprint="static-registry-ref:sha256:" + "b" * 64,
        )

    assert stopped == [process]


def test_worker_result_identity_substitution_fails_closed(tmp_path: Path) -> None:
    spec = _approved_specs((("one", "one_scan"),))[0]
    plan = assign_static_shards((spec,), 1)[0]

    class SettledProcess:
        returncode = 0

    worker = _ActiveWorker(
        plan=plan,
        process=SettledProcess(),  # type: ignore[arg-type]
        result_path=tmp_path / "result.json",
        progress_path=tmp_path / "progress.json",
        context_ref="static-context-ref:sha256:" + "c" * 64,
        registry_fingerprint="static-registry-ref:sha256:" + "b" * 64,
        repository_sha="a" * 40,
        launched_at=time.perf_counter(),
    )
    worker.result_path.write_text(
        json.dumps(
            {
                "schema_version": static_scan_worker.RESULT_SCHEMA,
                "context_ref": "static-context-ref:sha256:" + "d" * 64,
                "registry_fingerprint": worker.registry_fingerprint,
                "repository_sha": worker.repository_sha,
                "outcomes": [],
            }
        ),
        encoding="utf-8",
    )

    outcomes = _parse_outcomes(worker)

    assert len(outcomes) == 1
    assert outcomes[0].status == "failed"
    assert outcomes[0].failure_ref == "identity-ref:worker-result-mismatch"


def test_ci_v4_static_command_keeps_exact_head_fenced_entrypoint() -> None:
    from scripts.verification.ci_command_manifest import (
        SCHEMA_VERSION,
        command_registry,
    )

    command = command_registry()["command:static.verify-all"]

    assert SCHEMA_VERSION == "uaa_ci_command_manifest.v4"
    assert command.argv == (
        ".venv/bin/python",
        "scripts/verify_all.py",
        "--skip-ruff",
        "--skip-pytest",
        "--timings-json",
        "{temp_root}/uaa_static_verification_timings.json",
    )


def test_local_static_lane_replaces_only_static_stage_and_restores_legacy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = run_static_verification_lane.legacy.run_static_scans
    observed: dict[str, object] = {}

    def fake_execute(sequence: object, **kwargs: object) -> SimpleNamespace:
        observed["sequence"] = sequence
        observed.update(kwargs)
        return SimpleNamespace(
            passed=True,
            timing_entries=[{"name": "static_scan:one", "elapsed_ms": 1}],
        )

    def fake_legacy_main(argv: object) -> None:
        observed["legacy_argv"] = argv
        timings: list[dict[str, object]] = []
        run_static_verification_lane.legacy.run_static_scans(timings)
        observed["timings"] = timings

    monkeypatch.setattr(
        run_static_verification_lane, "execute_static_scans", fake_execute
    )
    monkeypatch.setattr(run_static_verification_lane.legacy, "main", fake_legacy_main)

    run_static_verification_lane.main(
        [
            "--skip-ruff",
            "--static-workers",
            "3",
            "--cpu-budget",
            "2",
            "--static-scan-timeout-seconds",
            "9",
        ]
    )

    assert observed["sequence"] is run_static_verification_lane.legacy.SCAN_SEQUENCE
    assert observed["max_workers"] == 3
    assert observed["cpu_budget"] == "2"
    assert observed["scan_timeout_seconds"] == 9
    assert observed["legacy_argv"] == ["--skip-ruff"]
    assert observed["timings"] == [{"name": "static_scan:one", "elapsed_ms": 1}]
    assert run_static_verification_lane.legacy.run_static_scans is original


def test_local_static_lane_keeps_serial_diagnostic_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def serial_runner(timings: object) -> None:
        calls.append("serial")

    monkeypatch.setattr(
        run_static_verification_lane.legacy,
        "main",
        lambda argv: run_static_verification_lane.legacy.run_static_scans(calls),
    )
    monkeypatch.setattr(
        run_static_verification_lane,
        "execute_static_scans",
        lambda *args, **kwargs: pytest.fail("parallel scheduler should not run"),
    )
    monkeypatch.setattr(
        run_static_verification_lane.legacy,
        "run_static_scans",
        serial_runner,
    )

    run_static_verification_lane.main(["--static-workers", "1"])

    assert calls == ["serial"]
    assert run_static_verification_lane.legacy.run_static_scans is serial_runner
