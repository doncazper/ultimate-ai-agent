from __future__ import annotations

import contextlib
import json
import os
import signal
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.verification import static_scan_context, static_scan_worker
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
    _launch_worker,
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
    STATIC_TIMING_SCHEMA,
    StaticScanSpec,
    StaticShardPlan,
    assign_static_shards,
    build_scan_specs,
    exclusive_plans,
    load_static_timings,
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


def test_make_static_lane_honors_cpu_budget_environment() -> None:
    root = Path(__file__).resolve().parents[1]
    inherited = dict(os.environ)
    inherited.pop(CPU_BUDGET_ENV, None)
    inherited.pop("VERIFY_CPU_BUDGET", None)
    default_plan = subprocess.run(
        ["make", "-n", "verify-static"],
        cwd=root,
        env=inherited,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    constrained_plan = subprocess.run(
        ["make", "-n", "verify-static"],
        cwd=root,
        env={**inherited, CPU_BUDGET_ENV: "1"},
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert "--cpu-budget" not in default_plan
    assert "--cpu-budget 1" in constrained_plan


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


@pytest.mark.parametrize(
    "payload",
    (
        [],
        {"schema_version": STATIC_TIMING_SCHEMA, "timings": {}},
    ),
)
def test_static_timing_history_ignores_structurally_invalid_json(
    tmp_path: Path,
    payload: object,
) -> None:
    path = tmp_path / "timings.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    specs = _approved_specs((("one", "one_scan"),))

    assert load_static_timings(path, specs) == {}


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


def test_static_context_reads_exact_git_tree_and_restores_path_methods(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    source = tmp_path / "sample.txt"
    second = tmp_path / "second.txt"
    source.write_text("first", encoding="utf-8")
    second.write_text("other", encoding="utf-8")
    subprocess.run(["git", "add", "sample.txt", "second.txt"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=UAA Test",
            "-c",
            "user.email=uaa-test@example.invalid",
            "commit",
            "-qm",
            "test immutable snapshot",
        ],
        cwd=tmp_path,
        check=True,
    )
    repository_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    source.write_text("second", encoding="utf-8")
    original_read_text = Path.read_text
    context = StaticVerificationContext.capture(
        tmp_path,
        ("scan-ref:test",),
        repository_sha,
        "static-registry-ref:sha256:" + "b" * 64,
    )

    with context.cached_repository_view():
        assert source.read_text(encoding="utf-8") == "first"
        source.write_text("third", encoding="utf-8")
        assert source.read_text(encoding="utf-8") == "first"
        with ThreadPoolExecutor(max_workers=8) as executor:
            reads = tuple(
                executor.map(
                    lambda path: path.read_text(encoding="utf-8"),
                    (source, second) * 50,
                )
            )
        assert reads == ("first", "other") * 50

    assert Path.read_text is original_read_text
    assert source.read_text(encoding="utf-8") == "third"


def test_repository_identity_rejects_dirty_or_nested_source(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    source = tmp_path / "source.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "source.py"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=UAA Test",
            "-c",
            "user.email=uaa-test@example.invalid",
            "commit",
            "-qm",
            "test source identity",
        ],
        cwd=tmp_path,
        check=True,
    )

    expected = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert resolve_repository_sha(tmp_path) == expected

    nested = tmp_path / "nested"
    nested.mkdir()
    with pytest.raises(ValueError, match="exact clean repository"):
        resolve_repository_sha(nested)

    untracked = tmp_path / "untracked.py"
    untracked.write_text("VALUE = 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exact clean repository"):
        resolve_repository_sha(tmp_path)
    untracked.unlink()

    source.write_text("VALUE = 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exact clean repository"):
        resolve_repository_sha(tmp_path)


def test_repository_identity_empty_git_output_fails_with_bounded_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    results = iter(
        (
            SimpleNamespace(returncode=1, stdout="", stderr="bounded"),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
        )
    )
    monkeypatch.setattr(
        static_scan_context.subprocess,
        "run",
        lambda *args, **kwargs: next(results),
    )

    with pytest.raises(ValueError, match="exact clean repository"):
        resolve_repository_sha(tmp_path)


def test_run_root_does_not_change_caller_owned_base_permissions(tmp_path: Path) -> None:
    base = tmp_path / "caller-owned"
    base.mkdir(mode=0o755)

    run_root = _safe_run_root(base)

    assert base.stat().st_mode & 0o777 == 0o755
    assert run_root.parent == base
    assert run_root.stat().st_mode & 0o777 == 0o700
    shutil.rmtree(run_root)


def test_scheduler_uses_detached_exact_source_tree_and_cleans_it(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    source = repository / "source.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "source.py"], cwd=repository, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=UAA Test",
            "-c",
            "user.email=uaa-test@example.invalid",
            "commit",
            "-qm",
            "test immutable scheduler source",
        ],
        cwd=repository,
        check=True,
    )
    repository_sha = resolve_repository_sha(repository)
    run_root = _safe_run_root(tmp_path)
    source_root = run_root / "source"

    with run_static_scan_shards._immutable_source_tree(
        repository,
        run_root,
        repository_sha,
    ) as immutable_root:
        assert immutable_root == source_root
        source.write_text("VALUE = 2\n", encoding="utf-8")
        assert (immutable_root / "source.py").read_text(
            encoding="utf-8"
        ) == "VALUE = 1\n"
        source.write_text("VALUE = 1\n", encoding="utf-8")

    assert not source_root.exists()
    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert str(source_root) not in worktrees
    shutil.rmtree(run_root)


def test_immutable_source_tree_cleans_up_when_checkout_is_interrupted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[tuple[str, ...]] = []

    def run(command: tuple[str, ...], **_kwargs: object) -> object:
        commands.append(command)
        if command[2:4] == ("add", "--detach"):
            (tmp_path / "run" / "source").mkdir(parents=True)
            raise run_static_scan_shards.StaticRunInterrupted(signal.SIGTERM)
        (tmp_path / "run" / "source").rmdir()
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(run_static_scan_shards.subprocess, "run", run)

    with pytest.raises(run_static_scan_shards.StaticRunInterrupted):
        with run_static_scan_shards._immutable_source_tree(
            tmp_path,
            tmp_path / "run",
            "a" * 40,
        ):
            pytest.fail("interrupted checkout must not yield a source tree")

    assert commands[0][0:4] == ("git", "worktree", "add", "--detach")
    assert commands[1][0:4] == ("git", "worktree", "remove", "--force")
    assert not (tmp_path / "run" / "source").exists()


def test_immutable_source_tree_retries_cleanup_after_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "run" / "source"
    remove_calls = 0

    def run(command: tuple[str, ...], **_kwargs: object) -> object:
        nonlocal remove_calls
        if command[2:4] == ("add", "--detach"):
            source_root.mkdir(parents=True)
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command[1:4] == ("worktree", "remove", "--force"):
            remove_calls += 1
            if remove_calls == 1:
                raise run_static_scan_shards.StaticRunInterrupted(signal.SIGTERM)
            source_root.rmdir()
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {command!r}")

    monkeypatch.setattr(run_static_scan_shards.subprocess, "run", run)
    monkeypatch.setattr(
        run_static_scan_shards,
        "resolve_repository_sha",
        lambda _root: "a" * 40,
    )

    with pytest.raises(run_static_scan_shards.StaticRunInterrupted):
        with run_static_scan_shards._immutable_source_tree(
            tmp_path,
            tmp_path / "run",
            "a" * 40,
        ):
            pass

    assert remove_calls == 2
    assert not source_root.exists()


def test_immutable_source_tree_retries_nonzero_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "run" / "source"
    remove_calls = 0

    def run(command: tuple[str, ...], **_kwargs: object) -> object:
        nonlocal remove_calls
        if command[2:4] == ("add", "--detach"):
            source_root.mkdir(parents=True)
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if command[1:4] == ("worktree", "remove", "--force"):
            remove_calls += 1
            if remove_calls == 1:
                return SimpleNamespace(returncode=1, stdout="", stderr="busy")
            source_root.rmdir()
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {command!r}")

    monkeypatch.setattr(run_static_scan_shards.subprocess, "run", run)
    monkeypatch.setattr(
        run_static_scan_shards,
        "resolve_repository_sha",
        lambda _root: "a" * 40,
    )

    with run_static_scan_shards._immutable_source_tree(
        tmp_path,
        tmp_path / "run",
        "a" * 40,
    ):
        pass

    assert remove_calls == 2
    assert not source_root.exists()


def test_scheduler_retains_run_root_when_worktree_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_sha = "a" * 40

    @contextlib.contextmanager
    def immutable_source(
        root: Path, run_root: Path, *_args: object, **_kwargs: object
    ) -> object:
        yield root
        raise run_static_scan_shards.StaticSourceCleanupError(
            "static scan immutable source cleanup failed"
        )

    monkeypatch.setattr(
        run_static_scan_shards,
        "resolve_repository_sha",
        lambda _root: repository_sha,
    )
    monkeypatch.setattr(
        run_static_scan_shards,
        "_immutable_source_tree",
        immutable_source,
    )
    monkeypatch.setattr(
        run_static_scan_shards,
        "_run_batch",
        lambda *_args, **_kwargs: ([], False),
    )

    with pytest.raises(
        run_static_scan_shards.StaticSourceCleanupError,
        match="immutable source cleanup failed",
    ):
        run_static_scan_shards.execute_static_scans(
            (("one", "one_scan"),),
            root=tmp_path,
            basetemp=tmp_path,
            repository_sha=repository_sha,
        )

    run_roots = list(tmp_path.glob("uaa-static-scan-*"))
    assert len(run_roots) == 1
    shutil.rmtree(run_roots[0])


def test_run_root_cleanup_retries_after_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    remove_calls = 0

    def remove(path: Path) -> None:
        nonlocal remove_calls
        assert path == run_root
        remove_calls += 1
        if remove_calls == 1:
            raise run_static_scan_shards.StaticRunInterrupted(signal.SIGTERM)
        path.rmdir()

    monkeypatch.setattr(run_static_scan_shards.shutil, "rmtree", remove)

    with pytest.raises(run_static_scan_shards.StaticRunInterrupted):
        run_static_scan_shards._remove_run_root(run_root)

    assert remove_calls == 2
    assert not run_root.exists()


def test_immutable_checkout_uses_remaining_hard_deadline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout_timeouts: list[float] = []

    def run(command: tuple[str, ...], **kwargs: object) -> object:
        if command[2:4] == ("add", "--detach"):
            timeout = float(kwargs["timeout"])
            checkout_timeouts.append(timeout)
            raise subprocess.TimeoutExpired(command, timeout=timeout)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(run_static_scan_shards.subprocess, "run", run)

    with pytest.raises(subprocess.TimeoutExpired):
        with run_static_scan_shards._immutable_source_tree(
            tmp_path,
            tmp_path / "run",
            "a" * 40,
            deadline=time.perf_counter() + 1.0,
        ):
            pytest.fail("timed-out checkout must not yield a source tree")

    assert len(checkout_timeouts) == 1
    assert 0 < checkout_timeouts[0] <= 1.0


def test_scheduler_does_not_launch_workers_after_setup_deadline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_sha = "a" * 40
    clock = iter((0.0, 2.0))

    @contextlib.contextmanager
    def immutable_source(root: Path, *_args: object, **_kwargs: object) -> object:
        yield root

    monkeypatch.setattr(
        run_static_scan_shards,
        "resolve_repository_sha",
        lambda _root: repository_sha,
    )
    monkeypatch.setattr(
        run_static_scan_shards,
        "_immutable_source_tree",
        immutable_source,
    )
    monkeypatch.setattr(
        run_static_scan_shards.time,
        "perf_counter",
        lambda: next(clock),
    )
    monkeypatch.setattr(
        run_static_scan_shards,
        "_run_batch",
        lambda *_args, **_kwargs: pytest.fail("workers must not launch after deadline"),
    )

    with pytest.raises(subprocess.TimeoutExpired):
        run_static_scan_shards.execute_static_scans(
            (("one", "one_scan"),),
            root=tmp_path,
            basetemp=tmp_path,
            repository_sha=repository_sha,
            target_seconds=0.5,
            hard_timeout_seconds=1.0,
        )


def test_worker_launch_registers_owned_process_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = _approved_specs((("one", "one_scan"),))[0]
    plan = assign_static_shards((spec,), 1)[0]
    run_root = tmp_path / "runs"
    run_root.mkdir()
    observed: dict[str, object] = {}

    class Process:
        pid = 12345
        returncode = None

    process = Process()

    def spawn(command: list[str], **kwargs: object) -> Process:
        observed["command"] = command
        observed.update(kwargs)
        return process

    monkeypatch.setattr(
        run_static_scan_shards.shard_processes,
        "spawn_owned_process_group",
        spawn,
    )

    worker = _launch_worker(
        plan,
        root=tmp_path,
        run_root=run_root,
        worker_ref="worker-0",
        base_env={},
        repository_sha="a" * 40,
        registry_fingerprint="static-registry-ref:sha256:" + "b" * 64,
    )

    assert worker.process is process
    assert observed["command"][-2:] == ["--progress", str(worker.progress_path)]
    assert observed["cwd"] == tmp_path
    assert "start_new_session" not in observed


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
    repository_sha = "a" * 40
    monkeypatch.setattr(
        static_scan_worker,
        "resolve_repository_sha",
        lambda root: repository_sha,
    )
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


def test_worker_revalidates_repository_after_scans(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_sha = "a" * 40
    sequence = (("pass", "test_pass"),)
    monkeypatch.setattr(static_scan_worker.legacy, "SCAN_SEQUENCE", sequence)
    monkeypatch.setattr(
        static_scan_worker.legacy,
        "test_pass",
        lambda: None,
        raising=False,
    )
    identities = iter((repository_sha, "b" * 40))
    monkeypatch.setattr(
        static_scan_worker,
        "resolve_repository_sha",
        lambda root: next(identities),
    )
    registry_fingerprint = scan_registry_fingerprint(sequence)
    specs = build_scan_specs(sequence)
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
                "scan_indices": [0],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="repository identity changed"):
        static_scan_worker.run_worker(plan, result, progress)


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


def test_timeout_targets_first_unreported_scan_after_completed_progress(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = _approved_specs((("done", "done_scan"), ("next", "next_scan")))
    plan = assign_static_shards(specs, 1)[0]

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
        launched_at=time.perf_counter() - 1,
        active_scan_index=specs[0].index,
        active_scan_observed_at=time.perf_counter() - 1,
    )
    worker.result_path.write_text(
        json.dumps(
            {
                "schema_version": static_scan_worker.RESULT_SCHEMA,
                "context_ref": worker.context_ref,
                "registry_fingerprint": worker.registry_fingerprint,
                "repository_sha": worker.repository_sha,
                "outcomes": [
                    {
                        "scan_index": specs[0].index,
                        "scan_ref": specs[0].scan_ref,
                        "name": specs[0].name,
                        "function_name": specs[0].function_name,
                        "status": "passed",
                        "elapsed_ms": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        run_static_scan_shards,
        "_launch_worker",
        lambda *args, **kwargs: worker,
    )
    monkeypatch.setattr(
        run_static_scan_shards,
        "_progress_scan_index",
        lambda active: specs[0].index,
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
        batch_ref="timeout-progress-test",
        repository_sha=worker.repository_sha,
        registry_fingerprint=worker.registry_fingerprint,
    )

    assert timed_out is True
    assert [(outcome.scan_ref, outcome.status) for outcome in outcomes] == [
        (specs[0].scan_ref, "passed"),
        (specs[1].scan_ref, "timed_out"),
    ]


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


def test_batch_stops_launching_workers_at_deadline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = _approved_specs((("one", "one_scan"), ("two", "two_scan")))
    plans = assign_static_shards(specs, 2)

    class RunningProcess:
        returncode: int | None = None

    process = RunningProcess()
    launches: list[StaticShardPlan] = []
    stopped: list[object] = []

    def launch(plan: StaticShardPlan, **_kwargs: object) -> _ActiveWorker:
        launches.append(plan)
        return _ActiveWorker(
            plan=plan,
            process=process,  # type: ignore[arg-type]
            result_path=tmp_path / "result.json",
            progress_path=tmp_path / "progress.json",
            context_ref="static-context-ref:sha256:" + "c" * 64,
            registry_fingerprint="static-registry-ref:sha256:" + "b" * 64,
            repository_sha="a" * 40,
            launched_at=0.0,
        )

    clock = iter((0.0, 2.0))
    monkeypatch.setattr(
        run_static_scan_shards.time, "perf_counter", lambda: next(clock)
    )
    monkeypatch.setattr(run_static_scan_shards, "_launch_worker", launch)
    monkeypatch.setattr(
        run_static_scan_shards.shard_processes,
        "stop_processes",
        lambda processes, _grace: stopped.extend(processes),
    )

    outcomes, timed_out = _run_batch(
        plans,
        root=tmp_path,
        run_root=tmp_path,
        base_env={},
        scan_timeout_seconds=1,
        deadline=1.0,
        safe_summary=True,
        batch_ref="deadline-test",
        repository_sha="a" * 40,
        registry_fingerprint="static-registry-ref:sha256:" + "b" * 64,
    )

    assert launches == [plans[0]]
    assert stopped == [process]
    assert timed_out is True
    assert [(outcome.scan_ref, outcome.status) for outcome in outcomes] == [
        (specs[0].scan_ref, "timed_out")
    ]


def test_scheduler_signal_cancellation_stops_active_worker_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_sha = "a" * 40
    captured: dict[str, object] = {}
    stopped: list[object] = []
    lifecycle: list[str] = []
    original_rmtree = run_static_scan_shards.shutil.rmtree

    @contextlib.contextmanager
    def installed_handlers(
        signals: object,
        handler: object,
    ) -> object:
        lifecycle.append("handlers-enter")
        captured["signals"] = signals
        captured["handler"] = handler
        try:
            yield
        finally:
            lifecycle.append("handlers-exit")

    class InterruptingProcess:
        returncode: int | None = None
        pid = 12345

        def poll(self) -> int | None:
            handler = captured["handler"]
            assert callable(handler)
            handler(signal.SIGTERM, None)
            return self.returncode

    process = InterruptingProcess()

    def launch(plan: StaticShardPlan, **kwargs: object) -> _ActiveWorker:
        return _ActiveWorker(
            plan=plan,
            process=process,  # type: ignore[arg-type]
            result_path=tmp_path / "result.json",
            progress_path=tmp_path / "progress.json",
            context_ref="static-context-ref:sha256:" + "c" * 64,
            registry_fingerprint="static-registry-ref:sha256:" + "b" * 64,
            repository_sha=repository_sha,
            launched_at=time.perf_counter(),
        )

    def stop_processes(processes: object, grace_seconds: float) -> None:
        assert grace_seconds >= 0
        stopped.extend(processes)  # type: ignore[arg-type]
        process.returncode = -15

    @contextlib.contextmanager
    def immutable_source(root: Path, *_args: object, **_kwargs: object) -> object:
        lifecycle.append("worktree-enter")
        try:
            yield root
        finally:
            lifecycle.append("worktree-exit")

    def remove_run_root(path: Path) -> None:
        lifecycle.append("run-root-remove")
        original_rmtree(path)

    monkeypatch.setattr(
        run_static_scan_shards,
        "resolve_repository_sha",
        lambda root: repository_sha,
    )
    monkeypatch.setattr(run_static_scan_shards, "_launch_worker", launch)
    monkeypatch.setattr(
        run_static_scan_shards,
        "_immutable_source_tree",
        immutable_source,
    )
    monkeypatch.setattr(run_static_scan_shards.shutil, "rmtree", remove_run_root)
    monkeypatch.setattr(
        run_static_scan_shards.shard_processes,
        "installed_signal_handlers",
        installed_handlers,
    )
    monkeypatch.setattr(
        run_static_scan_shards.shard_processes,
        "ignore_signals",
        lambda signals: captured.update(ignored=signals),
    )
    monkeypatch.setattr(
        run_static_scan_shards.shard_processes,
        "stop_processes",
        stop_processes,
    )

    with pytest.raises(run_static_scan_shards.StaticRunInterrupted):
        run_static_scan_shards.execute_static_scans(
            (("one", "one_scan"),),
            root=tmp_path,
            basetemp=tmp_path,
            repository_sha=repository_sha,
        )

    assert signal.SIGTERM in captured["signals"]  # type: ignore[operator]
    assert captured["ignored"] == captured["signals"]
    assert stopped == [process]
    assert lifecycle == [
        "handlers-enter",
        "worktree-enter",
        "worktree-exit",
        "run-root-remove",
        "handlers-exit",
    ]


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


def test_nonzero_worker_cannot_publish_only_passing_outcomes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = _approved_specs((("one", "one_scan"),))[0]
    plan = assign_static_shards((spec,), 1)[0]

    class FailedProcess:
        returncode = 2

        def poll(self) -> int:
            return self.returncode

    worker = _ActiveWorker(
        plan=plan,
        process=FailedProcess(),  # type: ignore[arg-type]
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
                "context_ref": worker.context_ref,
                "registry_fingerprint": worker.registry_fingerprint,
                "repository_sha": worker.repository_sha,
                "outcomes": [
                    {
                        "scan_index": spec.index,
                        "scan_ref": spec.scan_ref,
                        "name": spec.name,
                        "function_name": spec.function_name,
                        "status": "passed",
                        "elapsed_ms": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        run_static_scan_shards,
        "_launch_worker",
        lambda *args, **kwargs: worker,
    )

    outcomes, timed_out = _run_batch(
        (plan,),
        root=tmp_path,
        run_root=tmp_path,
        base_env={},
        scan_timeout_seconds=1,
        deadline=time.perf_counter() + 10,
        safe_summary=True,
        batch_ref="nonzero-test",
        repository_sha=worker.repository_sha,
        registry_fingerprint=worker.registry_fingerprint,
    )

    completed = _complete_outcomes((spec,), outcomes)
    assert timed_out is False
    assert completed[0].status == "failed"
    assert completed[0].failure_ref == "coverage-ref:duplicate-result"


def test_scheduler_revalidates_repository_after_worker_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_sha = "a" * 40
    identity_calls = 0

    def resolve_identity(root: Path) -> str:
        nonlocal identity_calls
        identity_calls += 1
        if identity_calls == 1:
            return repository_sha
        raise ValueError("static verification requires an exact clean revision")

    def run_batch(
        plans: tuple[StaticShardPlan, ...],
        **kwargs: object,
    ) -> tuple[list[StaticScanOutcome], bool]:
        outcomes = [
            StaticScanOutcome(
                spec.index,
                spec.scan_ref,
                spec.name,
                spec.function_name,
                "passed",
                1,
            )
            for plan in plans
            for spec in plan.scans
        ]
        return outcomes, False

    @contextlib.contextmanager
    def immutable_source(root: Path, *_args: object, **_kwargs: object) -> object:
        yield root

    monkeypatch.setattr(
        run_static_scan_shards, "resolve_repository_sha", resolve_identity
    )
    monkeypatch.setattr(
        run_static_scan_shards,
        "_immutable_source_tree",
        immutable_source,
    )
    monkeypatch.setattr(run_static_scan_shards, "_run_batch", run_batch)

    with pytest.raises(ValueError, match="exact clean revision"):
        run_static_scan_shards.execute_static_scans(
            (("one", "one_scan"),),
            root=tmp_path,
            repository_sha=repository_sha,
        )

    assert identity_calls == 2


@pytest.mark.parametrize("value", [float("inf"), float("nan")])
def test_static_scheduler_rejects_non_finite_time_budgets(value: float) -> None:
    with pytest.raises(ValueError, match="finite, positive, and ordered"):
        run_static_scan_shards.execute_static_scans(
            (("one", "one_scan"),),
            scan_timeout_seconds=value,
        )


def test_local_static_lane_redacts_expected_scheduler_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    original = run_static_verification_lane.legacy.run_static_scans

    monkeypatch.setattr(
        run_static_verification_lane.legacy,
        "main",
        lambda argv: run_static_verification_lane.legacy.run_static_scans([]),
    )

    def fail_execute(*args: object, **kwargs: object) -> None:
        raise ValueError("private source path must not escape")

    monkeypatch.setattr(
        run_static_verification_lane,
        "execute_static_scans",
        fail_execute,
    )

    with pytest.raises(SystemExit, match="1"):
        run_static_verification_lane.main([])

    captured = capsys.readouterr()
    assert "failure-ref:ValueError" in captured.err
    assert "private source path" not in captured.err
    assert run_static_verification_lane.legacy.run_static_scans is original


def test_local_static_serial_lane_rejects_mismatched_repository_sha(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    original = run_static_verification_lane.legacy.run_static_scans
    calls: list[object] = []
    monkeypatch.setattr(
        run_static_verification_lane.legacy,
        "main",
        lambda argv: run_static_verification_lane.legacy.run_static_scans([]),
    )

    def reject_mismatch(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise ValueError("private repository identity mismatch")

    monkeypatch.setattr(
        run_static_verification_lane, "execute_static_scans", reject_mismatch
    )

    with pytest.raises(SystemExit, match="1"):
        run_static_verification_lane.main(
            [
                "--static-workers",
                "1",
                "--repository-sha",
                "b" * 40,
            ]
        )

    captured = capsys.readouterr()
    assert "failure-ref:ValueError" in captured.err
    assert "private repository identity mismatch" not in captured.err
    assert len(calls) == 1
    assert calls[0][1]["max_workers"] == 1  # type: ignore[index]
    assert calls[0][1]["repository_sha"] == "b" * 40  # type: ignore[index]
    assert run_static_verification_lane.legacy.run_static_scans is original


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
            "--timings-json",
            "/tmp/static-timings.json",
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
    assert observed["timings_path"] == Path("/tmp/static-timings.json")
    assert observed["scan_timeout_seconds"] == 9
    assert observed["legacy_argv"] == [
        "--skip-ruff",
        "--timings-json",
        "/tmp/static-timings.json",
    ]
    assert observed["timings"] == [{"name": "static_scan:one", "elapsed_ms": 1}]
    assert run_static_verification_lane.legacy.run_static_scans is original


def test_local_static_lane_keeps_bounded_serial_diagnostic_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}
    timings: list[dict[str, object]] = []

    def serial_runner(timings: object) -> None:
        pytest.fail("legacy serial runner should be replaced locally")

    def execute(sequence: object, **kwargs: object) -> SimpleNamespace:
        observed["sequence"] = sequence
        observed.update(kwargs)
        return SimpleNamespace(
            passed=True,
            timing_entries=[{"name": "static_scan:one", "elapsed_ms": 1}],
        )

    monkeypatch.setattr(
        run_static_verification_lane.legacy,
        "main",
        lambda argv: run_static_verification_lane.legacy.run_static_scans(timings),
    )
    monkeypatch.setattr(
        run_static_verification_lane,
        "execute_static_scans",
        execute,
    )
    monkeypatch.setattr(
        run_static_verification_lane.legacy,
        "run_static_scans",
        serial_runner,
    )

    run_static_verification_lane.main(
        ["--static-workers", "1", "--static-scan-timeout-seconds", "7"]
    )

    assert observed["sequence"] is run_static_verification_lane.legacy.SCAN_SEQUENCE
    assert observed["max_workers"] == 1
    assert observed["scan_timeout_seconds"] == 7
    assert timings == [{"name": "static_scan:one", "elapsed_ms": 1}]
    assert run_static_verification_lane.legacy.run_static_scans is serial_runner


def test_standalone_safe_summary_redacts_expected_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_execute(*args: object, **kwargs: object) -> None:
        raise ValueError("private source path must not escape")

    monkeypatch.setattr(run_static_scan_shards, "execute_static_scans", fail_execute)

    assert run_static_scan_shards.main(["--safe-summary"]) == 1
    captured = capsys.readouterr()
    assert "failure-ref:ValueError" in captured.err
    assert "private source path" not in captured.err
