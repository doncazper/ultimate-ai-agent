from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verification/run_pytest_shards.py"
MAKEFILE = ROOT / "Makefile"


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


def test_missing_or_partial_timings_fall_back_to_deterministic(tmp_path: Path) -> None:
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

    assert timings is None
    assert timing_source == "incomplete:1"
    assert method == "deterministic-file-count"
    assert [plan.files for plan in plans] == [
        ("tests/test_a.py",),
        ("tests/test_b.py",),
    ]


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


def test_overall_return_code_fails_if_any_shard_failed(tmp_path: Path) -> None:
    runner = load_runner()
    passed = runner.ShardResult(0, 1, 0, 1.0, tmp_path / "a.log")
    failed = runner.ShardResult(1, 1, 2, 1.0, tmp_path / "b.log")

    assert runner.overall_return_code([passed]) == 0
    assert runner.overall_return_code([passed, failed]) == 1


def test_makefile_exposes_opt_in_sharded_targets_without_changing_verify() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")

    assert "\ntest-sharded:\n" in makefile
    assert "\nverify-dev-sharded:\n" in makefile
    assert "scripts/verification/run_pytest_shards.py" in makefile
    verify_block = makefile.split("\nverify:\n", 1)[1].split("\nverify-static:", 1)[0]
    assert "scripts/verify_all.py" in verify_block
    assert "run_pytest_shards.py" not in verify_block
