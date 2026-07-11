from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verification/run_pytest_shards.py"
MAKEFILE = ROOT / "Makefile"
TIMING_SEED = ROOT / "scripts/verification/pytest_file_timing_seed.json"


def load_runner() -> Any:
    spec = importlib.util.spec_from_file_location("run_pytest_shards", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_deterministic_file_count_shards_are_stable() -> None:
    runner = load_runner()

    plans, method = runner.assign_shards(
        ["tests/test_c.py", "tests/test_a.py", "tests/test_b.py", "tests/test_d.py"],
        2,
        None,
    )

    assert method == "deterministic-file-count"
    assert [plan.files for plan in plans] == [
        ("tests/test_a.py", "tests/test_c.py"),
        ("tests/test_b.py", "tests/test_d.py"),
    ]


def test_test_discovery_is_recursive_and_sorted(tmp_path: Path) -> None:
    runner = load_runner()
    (tmp_path / "tests/nested").mkdir(parents=True)
    (tmp_path / "tests/test_z.py").write_text("", encoding="utf-8")
    (tmp_path / "tests/nested/test_a.py").write_text("", encoding="utf-8")
    (tmp_path / "tests/nested/helper.py").write_text("", encoding="utf-8")

    assert runner.discover_test_files(tmp_path) == [
        "tests/nested/test_a.py",
        "tests/test_z.py",
    ]


def test_shard_selection_is_exact_and_validated() -> None:
    runner = load_runner()
    plans = runner.deterministic_file_count_shards(
        [f"tests/test_{index}.py" for index in range(8)],
        4,
    )

    assert runner.select_shard(plans, None) == plans
    assert runner.select_shard(plans, 2) == [plans[2]]
    with pytest.raises(ValueError, match="one configured shard"):
        runner.select_shard(plans, -1)
    with pytest.raises(ValueError, match="one configured shard"):
        runner.select_shard(plans, 4)


def test_eight_way_partition_covers_every_file_once() -> None:
    runner = load_runner()
    files = [f"tests/test_{index}.py" for index in range(810)]

    plans, method = runner.assign_shards(files, 8, None)
    assigned = [file_path for plan in plans for file_path in plan.files]

    assert method == "deterministic-file-count"
    assert sorted(assigned) == sorted(files)
    assert len(assigned) == len(set(assigned))
    assert sorted(len(plan.files) for plan in plans) == [101] * 6 + [102] * 2


def test_timing_aware_shards_balance_by_prior_duration() -> None:
    runner = load_runner()
    files = [
        "tests/test_a.py",
        "tests/test_b.py",
        "tests/test_c.py",
        "tests/test_d.py",
    ]
    timings = {
        "tests/test_a.py": 100.0,
        "tests/test_b.py": 90.0,
        "tests/test_c.py": 10.0,
        "tests/test_d.py": 1.0,
    }

    plans, method = runner.assign_shards(files, 2, timings)

    assert method == "timing-aware"
    assert "tests/test_a.py" in plans[0].files
    assert "tests/test_b.py" in plans[1].files
    assert [plan.expected_seconds for plan in plans] == [101.0, 100.0]


def test_partial_timings_use_conservative_fallback_without_dropping_profile(
    tmp_path: Path,
) -> None:
    runner = load_runner()
    files = ["tests/test_a.py", "tests/test_b.py"]
    timings_json = tmp_path / "timings.json"
    timings_json.write_text(
        json.dumps(
            {
                "schema_version": runner.TIMING_SCHEMA_VERSION,
                "timings": [
                    {"path": "tests/test_a.py", "seconds": 2.0},
                ],
            }
        ),
        encoding="utf-8",
    )

    timings, timing_source = runner.load_complete_timings(timings_json, files)
    plans, method = runner.assign_shards(files, 2, timings)

    assert timings == {"tests/test_a.py": 2.0, "tests/test_b.py": 2.0}
    assert timing_source == "partial:1:fallback=2.000s"
    assert method == "timing-aware"
    assert [plan.files for plan in plans] == [
        ("tests/test_a.py",),
        ("tests/test_b.py",),
    ]


def test_multiple_profiles_merge_with_fresh_overlay_and_reject_invalid_values(
    tmp_path: Path,
) -> None:
    runner = load_runner()
    files = [
        "tests/test_a.py",
        "tests/test_b.py",
        "tests/test_c.py",
        "tests/test_d.py",
    ]
    seed = tmp_path / "seed.json"
    overlay = tmp_path / "overlay.json"
    seed.write_text(
        json.dumps(
            {
                "timings": {
                    "tests/test_a.py": 2.0,
                    "tests/test_b.py": 3.0,
                    "tests/test_c.py": float("inf"),
                    "tests/test_d.py": True,
                }
            }
        ),
        encoding="utf-8",
    )
    overlay.write_text(
        json.dumps({"timings": {"tests/test_a.py": 5.0}}),
        encoding="utf-8",
    )

    timings, source = runner.load_timing_profiles([seed, overlay], files)

    assert timings == {
        "tests/test_a.py": 5.0,
        "tests/test_b.py": 3.0,
        "tests/test_c.py": 5.0,
        "tests/test_d.py": 5.0,
    }
    assert source == "profiles=2:partial:2:fallback=5.000s"


def test_non_object_timing_profile_fails_soft_and_keeps_valid_seed(
    tmp_path: Path,
) -> None:
    runner = load_runner()
    seed = tmp_path / "seed.json"
    overlay = tmp_path / "overlay.json"
    seed.write_text(
        json.dumps({"timings": {"tests/test_a.py": 2.0}}), encoding="utf-8"
    )
    overlay.write_text("[]\n", encoding="utf-8")

    timings, source = runner.load_timing_profiles(
        [seed, overlay], ["tests/test_a.py"]
    )

    assert timings == {"tests/test_a.py": 2.0}
    assert source == "profiles=1:complete"


def test_incompatible_timing_schema_fails_soft(tmp_path: Path) -> None:
    runner = load_runner()
    profile = tmp_path / "profile.json"
    profile.write_text(
        json.dumps(
            {
                "schema_version": "uaa_pytest_file_timings.v999",
                "timings": {"tests/test_a.py": 99.0},
            }
        ),
        encoding="utf-8",
    )

    assert runner.load_timing_profiles([profile], ["tests/test_a.py"]) == (
        None,
        "unsupported-schema",
    )


def test_fixture_affinity_co_locates_consumers_without_omitting_files(
    tmp_path: Path,
) -> None:
    runner = load_runner()
    root = tmp_path / "repo"
    (root / "tests").mkdir(parents=True)
    files = [f"tests/test_{name}.py" for name in ["gate_a", "gate_b", "x", "y"]]
    (root / files[0]).write_text(
        "def test_one(foundation_gate_results): pass\n", encoding="utf-8"
    )
    (root / files[1]).write_text(
        "def test_two(foundation_gate_report): pass\n", encoding="utf-8"
    )
    for file_path in files[2:]:
        (root / file_path).write_text("def test_plain(): pass\n", encoding="utf-8")

    groups = runner.discover_affinity_groups(files, root)
    plans, method = runner.assign_shards(
        files,
        2,
        {file_path: 1.0 for file_path in files},
        groups,
    )
    assigned = [file_path for plan in plans for file_path in plan.files]
    gate_shards = {
        plan.index
        for plan in plans
        if any(file_path in plan.files for file_path in files[:2])
    }

    assert method == "timing-aware+fixture-affinity"
    assert gate_shards == {0}
    assert sorted(assigned) == sorted(files)
    assert len(assigned) == len(set(assigned))


def test_complete_timings_can_load_list_or_mapping_schema(tmp_path: Path) -> None:
    runner = load_runner()
    files = ["tests/test_a.py", "tests/test_b.py"]
    list_json = tmp_path / "list.json"
    mapping_json = tmp_path / "mapping.json"
    list_json.write_text(
        json.dumps(
            {
                "schema_version": runner.TIMING_SCHEMA_VERSION,
                "timings": [
                    {"path": "tests/test_a.py", "seconds": 2.0},
                    {"path": "tests/test_b.py", "seconds": 3.5},
                ],
            }
        ),
        encoding="utf-8",
    )
    mapping_json.write_text(
        json.dumps({"timings": {"tests/test_a.py": 2.0, "tests/test_b.py": 3.5}}),
        encoding="utf-8",
    )

    assert runner.load_complete_timings(list_json, files) == (
        {"tests/test_a.py": 2.0, "tests/test_b.py": 3.5},
        "complete",
    )
    assert runner.load_complete_timings(mapping_json, files) == (
        {"tests/test_a.py": 2.0, "tests/test_b.py": 3.5},
        "complete",
    )


def test_tracked_timing_seed_is_safe_advisory_and_covers_most_current_files() -> None:
    runner = load_runner()
    payload = json.loads(TIMING_SEED.read_text(encoding="utf-8"))
    files = runner.discover_test_files(ROOT)

    timings, source = runner.load_timing_profiles([TIMING_SEED], files)

    assert payload["schema_version"] == runner.TIMING_SCHEMA_VERSION
    assert payload["advisory_only"] is True
    assert payload["verification_evidence"] is False
    assert payload["source_run_status_attestation"] == "operator_supplied_advisory"
    seed_paths = {entry["path"] for entry in payload["timings"]}
    current_paths = set(files)
    pytest_candidates = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "tests").rglob("*.py")
        if path.name.startswith("test") or path.name.endswith("_test.py")
    }
    assert current_paths == pytest_candidates
    assert payload["timed_file_count"] == len(seed_paths)
    assert len(seed_paths & current_paths) / len(current_paths) >= 0.95
    assert timings is not None
    assert source == "profiles=1:complete" or source.startswith("profiles=1:partial:")
    rendered = json.dumps(payload)
    assert "/Users/" not in rendered
    assert "/home/" not in rendered
    assert all(path.startswith("tests/test_") for path in timings)


def test_parse_pytest_durations_aggregates_by_file() -> None:
    runner = load_runner()
    log_text = """
    0.25s call     tests/test_a.py::test_one
    0.10s setup    tests/test_a.py::test_one
    2.50s call     tests/test_b.py::test_two[param with spaces]
    9.99s call     tests/not_allowed.py::test_ignored
    """

    durations = runner.parse_pytest_durations(
        log_text,
        {"tests/test_a.py", "tests/test_b.py"},
    )

    assert durations == {"tests/test_a.py": 0.35, "tests/test_b.py": 2.5}


def test_build_pytest_command_is_isolated_and_duration_aware(tmp_path: Path) -> None:
    runner = load_runner()
    plan = runner.ShardPlan(
        index=3,
        files=("tests/test_a.py",),
        expected_seconds=1.0,
    )

    command = runner.build_pytest_command(
        plan,
        tmp_path / "basetemp",
        write_timings=True,
        junit_dir=tmp_path / "junit",
    )

    assert command[:6] == [
        runner.sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
    ]
    assert "--basetemp" in command
    assert "--durations=0" in command
    assert "--durations-min=0" in command
    assert f"--junitxml={tmp_path / 'junit' / 'pytest-shard-3.xml'}" in command
    assert command[-1] == "tests/test_a.py"


def test_shard_env_strips_live_model_opt_in_flags(tmp_path: Path) -> None:
    runner = load_runner()
    inherited = {
        "PYTHONPATH": "existing",
        "UAA_M160_LIVE_HF_GGUF_SEARCH": "1",
        "UAA_M160_LIVE_HF_QUERY": "qwen gguf",
        "UAA_M162_LIVE_HF_ACQUISITION": "1",
        "UAA_M162_LIVE_HF_REPO": "org/model",
        "UAA_LLAMA_CPP_GATEWAY_ENABLED": "1",
        "UAA_LLAMA_CPP_MODEL_PATH": "model-path-ref:test",
        "UAA_MODEL_ROUTER_SWEEP_ENABLED": "1",
        "UAA_OPENWEBUI_TEST_GATEWAY_ENABLED": "1",
        "UAA_TINY_LIVE_PROVIDER_REAL_NETWORK": "1",
        "UAA_TINY_LIVE_PROVIDER_TRANSIENT_CREDENTIAL": "credential-ref:test",
        "UAA_LOCAL_MODEL_ROOTS": "model-root-ref:test",
        "UAA_LOCAL_MODEL_REF": "local-model-ref:test",
        "UAA_WEB_HYBRID_LIVE_SEARXNG": "1",
        "UAA_WEB_HYBRID_LIVE_FIRECRAWL_LOCAL": "1",
        "UAA_WEB_HYBRID_LIVE_FIRECRAWL_CLOUD": "1",
        "UAA_FIRECRAWL_CLOUD_SECRET_FILE": "secret-file-ref:test",
        "SAFE_UNRELATED_ENV": "kept",
    }

    env = runner.build_shard_env(tmp_path, inherited)

    assert env["PYTHONPATH"] == f"{tmp_path / 'src'}:existing"
    assert env["SAFE_UNRELATED_ENV"] == "kept"
    assert "UAA_M160_LIVE_HF_GGUF_SEARCH" not in env
    assert "UAA_M160_LIVE_HF_QUERY" not in env
    assert "UAA_M162_LIVE_HF_ACQUISITION" not in env
    assert "UAA_M162_LIVE_HF_REPO" not in env
    assert "UAA_LLAMA_CPP_GATEWAY_ENABLED" not in env
    assert "UAA_LLAMA_CPP_MODEL_PATH" not in env
    assert "UAA_MODEL_ROUTER_SWEEP_ENABLED" not in env
    assert "UAA_OPENWEBUI_TEST_GATEWAY_ENABLED" not in env
    assert "UAA_TINY_LIVE_PROVIDER_REAL_NETWORK" not in env
    assert "UAA_TINY_LIVE_PROVIDER_TRANSIENT_CREDENTIAL" not in env
    assert "UAA_LOCAL_MODEL_ROOTS" not in env
    assert "UAA_LOCAL_MODEL_REF" not in env
    assert "UAA_WEB_HYBRID_LIVE_SEARXNG" not in env
    assert "UAA_WEB_HYBRID_LIVE_FIRECRAWL_LOCAL" not in env
    assert "UAA_WEB_HYBRID_LIVE_FIRECRAWL_CLOUD" not in env
    assert "UAA_FIRECRAWL_CLOUD_SECRET_FILE" not in env


def test_live_model_opt_in_env_guard_covers_known_live_lanes() -> None:
    runner = load_runner()

    guarded = {
        "UAA_M160_LIVE_HF_GGUF_SEARCH",
        "UAA_M160_LIVE_HF_QUERY",
        "UAA_M162_LIVE_HF_ACQUISITION",
        "UAA_M162_LIVE_HF_FILENAME",
        "UAA_LLAMA_CPP_GATEWAY_ENABLED",
        "UAA_LLAMA_CPP_API_KEY",
        "UAA_LLAMA_CPP_BASE_URL",
        "UAA_LLAMA_CPP_MODEL_CACHE_ROOT",
        "UAA_LLAMA_CPP_MODEL_PATH",
        "UAA_MODEL_ROUTER_SWEEP_ENABLED",
        "UAA_OPENWEBUI_TEST_GATEWAY_ENABLED",
        "UAA_OPENWEBUI_TEST_MODEL_ID",
        "UAA_TINY_LIVE_PROVIDER_REAL_NETWORK",
        "UAA_TINY_LIVE_PROVIDER_TRANSIENT_CREDENTIAL",
        "UAA_LOCAL_MODEL_ROOTS",
        "UAA_LOCAL_MODEL_REF",
        "UAA_WEB_HYBRID_LIVE_SEARXNG",
        "UAA_WEB_HYBRID_LIVE_FIRECRAWL_LOCAL",
        "UAA_WEB_HYBRID_LIVE_FIRECRAWL_CLOUD",
        "UAA_FIRECRAWL_CLOUD_SECRET_FILE",
    }

    assert all(runner.is_live_model_opt_in_env_var(name) for name in guarded)
    assert not runner.is_live_model_opt_in_env_var("UAA_ENV")
    assert not runner.is_live_model_opt_in_env_var("PYTHONPATH")


def test_sharded_command_does_not_select_live_or_model_heavy_markers(
    tmp_path: Path,
) -> None:
    runner = load_runner()
    plan = runner.ShardPlan(
        index=0,
        files=(
            "tests/test_m160_hf_gguf_search.py",
            "tests/test_m162_model_acquisition.py",
        ),
        expected_seconds=1.0,
    )

    command = runner.build_pytest_command(
        plan,
        tmp_path / "basetemp",
        write_timings=False,
        junit_dir=None,
    )

    assert command[1:3] == ["-m", "pytest"]
    assert "-m" not in command[3:]
    assert "--runxfail" not in command
    assert "--durations=0" not in command
    assert "UAA_M160_LIVE_HF_GGUF_SEARCH=1" not in " ".join(command)
    assert "UAA_M162_LIVE_HF_ACQUISITION=1" not in " ".join(command)


def test_shard_subprocess_preserves_default_skips_for_live_model_tests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_runner()
    root = tmp_path / "repo"
    tests_dir = root / "tests"
    (root / "src").mkdir(parents=True)
    tests_dir.mkdir()
    (tests_dir / "test_live_model_guard.py").write_text(
        "\n".join(
            [
                "import os",
                "import pytest",
                "",
                "@pytest.mark.skipif(",
                "    os.getenv('UAA_M160_LIVE_HF_GGUF_SEARCH') != '1',",
                "    reason='explicit live smoke only',",
                ")",
                "def test_live_smoke_would_fail_if_env_leaked():",
                "    raise AssertionError('live smoke env leaked into shard')",
                "",
                "def test_live_model_env_is_not_visible():",
                "    assert os.getenv('UAA_M160_LIVE_HF_GGUF_SEARCH') is None",
                "    assert os.getenv('UAA_M162_LIVE_HF_ACQUISITION') is None",
                "    assert os.getenv('UAA_LLAMA_CPP_GATEWAY_ENABLED') is None",
                "    assert os.getenv('UAA_OPENWEBUI_TEST_GATEWAY_ENABLED') is None",
                "    assert os.getenv('UAA_WEB_HYBRID_LIVE_SEARXNG') is None",
                "    assert os.getenv('UAA_WEB_HYBRID_LIVE_FIRECRAWL_LOCAL') is None",
                "    assert os.getenv('UAA_WEB_HYBRID_LIVE_FIRECRAWL_CLOUD') is None",
                "    assert os.getenv('UAA_FIRECRAWL_CLOUD_SECRET_FILE') is None",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UAA_M160_LIVE_HF_GGUF_SEARCH", "1")
    monkeypatch.setenv("UAA_WEB_HYBRID_LIVE_SEARXNG", "1")
    monkeypatch.setenv("UAA_WEB_HYBRID_LIVE_FIRECRAWL_LOCAL", "1")
    monkeypatch.setenv("UAA_WEB_HYBRID_LIVE_FIRECRAWL_CLOUD", "1")
    monkeypatch.setenv("UAA_FIRECRAWL_CLOUD_SECRET_FILE", "secret-file-ref:test")
    monkeypatch.setenv("UAA_M162_LIVE_HF_ACQUISITION", "1")
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", "1")
    monkeypatch.setenv("UAA_OPENWEBUI_TEST_GATEWAY_ENABLED", "1")

    results = runner.run_shards(
        [runner.ShardPlan(0, ("tests/test_live_model_guard.py",), 0.0)],
        root=root,
        basetemp=tmp_path / "shards",
        junit_dir=None,
        write_timings=False,
        quiet=True,
    )

    assert runner.overall_return_code(results) == 0
    log_text = results[0].log_path.read_text(encoding="utf-8")
    assert "1 passed, 1 skipped" in log_text


def test_run_shards_respects_explicit_worker_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = load_runner()
    active = 0
    max_active = 0

    class ImmediateProcess:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            self._settled = False

        def poll(self) -> int:
            nonlocal active
            if not self._settled:
                active -= 1
                self._settled = True
            return 0

    monkeypatch.setattr(runner.subprocess, "Popen", ImmediateProcess)
    plans = [
        runner.ShardPlan(index, (f"tests/test_{index}.py",), 1.0)
        for index in range(5)
    ]

    results = runner.run_shards(
        plans,
        root=tmp_path,
        basetemp=tmp_path / "shards",
        junit_dir=None,
        write_timings=False,
        quiet=True,
        max_workers=2,
    )

    assert max_active == 2
    assert [result.index for result in results] == list(range(5))
    assert runner.overall_return_code(results) == 0


def test_overall_return_code_fails_if_any_shard_failed(tmp_path: Path) -> None:
    runner = load_runner()
    passed = runner.ShardResult(0, 1, 0, 1.0, tmp_path / "a.log")
    failed = runner.ShardResult(1, 1, 2, 1.0, tmp_path / "b.log")

    assert runner.overall_return_code([passed]) == 0
    assert runner.overall_return_code([passed, failed]) == 1


def test_timing_output_uses_atomic_process_scoped_temporary_file(
    tmp_path: Path,
) -> None:
    runner = load_runner()
    output = tmp_path / "timings.json"

    runner.write_timings_json(
        output,
        [
            {
                "path": "tests/test_a.py",
                "seconds": 1.25,
                "source": "pytest-duration-summary",
            }
        ],
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == runner.TIMING_SCHEMA_VERSION
    assert payload["timings"][0]["path"] == "tests/test_a.py"
    assert list(tmp_path.glob("timings.json.*.tmp")) == []


def test_single_shard_rejects_partial_timing_output(capsys) -> None:
    runner = load_runner()

    assert (
        runner.main(
            [
                "--shards",
                "8",
                "--shard-index",
                "2",
                "--write-timings-json",
                "timings.json",
            ]
        )
        == 2
    )
    assert "complete shard set" in capsys.readouterr().err


def test_safe_summary_omits_local_log_paths(tmp_path: Path, capsys) -> None:
    runner = load_runner()
    result = runner.ShardResult(
        index=2,
        file_count=101,
        returncode=0,
        elapsed_seconds=12.5,
        log_path=tmp_path / "private" / "pytest.log",
    )

    runner.print_summary(
        [result],
        assignment_method="deterministic-file-count",
        timing_source="not-requested",
        timing_output=None,
        safe_summary=True,
    )

    output = capsys.readouterr().out
    assert "pytest-shard-log:2" in output
    assert str(tmp_path) not in output


def test_makefile_makes_sharded_pytest_canonical_and_preserves_serial_diagnostics() -> (
    None
):
    makefile = MAKEFILE.read_text(encoding="utf-8")

    assert "\ntest-sharded:\n" in makefile
    assert "\ntest-sharded-profile:\n" in makefile
    assert "\ntest-serial:\n" in makefile
    assert "\nverify-dev-sharded:\n" in makefile
    assert "scripts/verification/run_pytest_shards.py" in makefile
    test_block = makefile.split("\ntest:\n", 1)[1].split("\ntest-serial:", 1)[0]
    assert "test-sharded" in test_block
    verify_block = makefile.split("\nverify:\n", 1)[1].split("\nverify-static:", 1)[0]
    assert "test-sharded" in verify_block
    assert "verify-static" in verify_block
