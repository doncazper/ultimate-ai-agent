from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.verification import run_pytest_shards as runner
from scripts.verification.pytest_safe_failure_plugin import (
    _write_safe_failure_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _failed_result(tmp_path: Path, report_path: Path) -> runner.ShardResult:
    return runner.ShardResult(
        0,
        1,
        1,
        1.0,
        tmp_path / "shard.log",
        failure_ref_path=report_path,
    )


def test_safe_failure_report_is_bounded_and_content_free(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    private_parameter = "private-parameter-value"
    raw_path = "/" + "private/tmp/do-not-retain"
    refs = [
        runner.safe_test_ref(
            f"tests/test_module.py::test_case_{index}[{private_parameter}-{raw_path}]"
        )
        for index in range(12)
    ]
    report_path = tmp_path / "pytest-shard-0.json"
    _write_safe_failure_report(report_path, refs)
    result = _failed_result(tmp_path, report_path)

    collected = runner.collect_failed_test_refs([result])

    assert len(collected[0]) == runner.MAX_FAILED_TEST_REFS_PER_SHARD
    assert all(
        ref.startswith("pytest-test-ref:test_module.py:test_case_")
        for ref in collected[0]
    )
    serialized = report_path.read_text(encoding="utf-8")
    assert private_parameter not in serialized
    assert raw_path not in serialized
    assert report_path.stat().st_size < runner.MAX_SAFE_FAILURE_REPORT_BYTES

    runner.print_summary(
        [result],
        assignment_method="deterministic",
        timing_source="test",
        timing_output=None,
        performance_output=None,
        stretch_goal_seconds=1.0,
        target_seconds=2.0,
        hard_timeout_seconds=3.0,
        total_elapsed_seconds=1.0,
        safe_summary=True,
        failed_test_refs=collected,
    )
    output = capsys.readouterr().out
    assert "pytest-test-ref:test_module.py:test_case_" in output
    assert private_parameter not in output
    assert raw_path not in output


def test_failure_report_writer_refuses_existing_output(tmp_path: Path) -> None:
    report_path = tmp_path / "pytest-shard-0.json"
    report_path.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        _write_safe_failure_report(
            report_path,
            [runner.safe_test_ref("tests/test_module.py::test_case")],
        )


def test_pytest_plugin_writes_only_content_free_failure_refs(tmp_path: Path) -> None:
    test_path = tmp_path / "test_sample.py"
    test_path.write_text(
        "import pytest\n\n"
        "@pytest.mark.parametrize('value', ['private-parameter-value'])\n"
        "def test_sample(value):\n"
        "    assert value == 'expected'\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "failed-refs.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "scripts.verification.pytest_safe_failure_plugin",
            "--uaa-safe-failure-report",
            str(report_path),
            str(test_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    serialized = report_path.read_text(encoding="utf-8")
    assert "private-parameter-value" not in serialized
    assert str(tmp_path) not in serialized
    assert "pytest-test-ref:" in serialized


def test_failure_ref_collection_refuses_symlink(tmp_path: Path) -> None:
    target = tmp_path / "outside.json"
    _write_safe_failure_report(
        target,
        [runner.safe_test_ref("tests/test_module.py::test_case")],
    )
    report_path = tmp_path / "pytest-shard-0.json"
    report_path.symlink_to(target)

    assert runner.collect_failed_test_refs(
        [_failed_result(tmp_path, report_path)]
    ) == {}


def test_failure_ref_collection_refuses_hardlink(tmp_path: Path) -> None:
    target = tmp_path / "outside.json"
    _write_safe_failure_report(
        target,
        [runner.safe_test_ref("tests/test_module.py::test_case")],
    )
    report_path = tmp_path / "pytest-shard-0.json"
    os.link(target, report_path)

    assert runner.collect_failed_test_refs(
        [_failed_result(tmp_path, report_path)]
    ) == {}


@pytest.mark.skipif(os.name != "posix", reason="FIFO proof is POSIX-only")
def test_failure_ref_collection_refuses_fifo_without_blocking(tmp_path: Path) -> None:
    report_path = tmp_path / "pytest-shard-0.json"
    os.mkfifo(report_path)

    started = time.monotonic()
    assert runner.collect_failed_test_refs(
        [_failed_result(tmp_path, report_path)]
    ) == {}
    assert time.monotonic() - started < 1.0


def test_safe_test_ref_ignores_all_parameter_values_in_identity() -> None:
    baseline = runner.safe_test_ref(
        "tests/test_module.py::TestGroup::test_case"
    )
    localish = "/" + "private/location-fragment"
    parameterized = (
        "tests/test_module.py::TestGroup::test_case[first-private-value]",
        "tests/test_module.py::TestGroup::test_case[value::hidden-tail]",
        f"tests/test_module.py::TestGroup::test_case[{localish}::hidden-tail]",
        "tests/test_module.py::TestGroup::test_case[nested[value]::hidden-tail]",
        "tests/test_module.py::TestGroup::test_case[opaque-secret-shaped-value]",
    )

    for nodeid in parameterized:
        test_ref = runner.safe_test_ref(nodeid)
        assert test_ref == baseline
        assert "private-value" not in test_ref
        assert "hidden-tail" not in test_ref
        assert "location-fragment" not in test_ref
        assert "secret-shaped" not in test_ref


def test_removed_junit_option_fails_with_migration_message(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit, match="2"):
        runner.parse_args(["--junit-dir", str(tmp_path)])

    error = capsys.readouterr().err
    assert "--junit-dir was removed" in error
    assert "--failure-ref-dir" in error
    assert str(tmp_path) not in error


def test_failure_ref_reader_rejects_extra_or_unbounded_payload(tmp_path: Path) -> None:
    report_path = tmp_path / "pytest-shard-0.json"
    report_path.write_text(
        json.dumps(
            {
                "schema_version": runner.FAILED_TEST_REFS_SCHEMA_VERSION,
                "failed_test_refs": [],
                "raw_log": "not allowed",
            }
        ),
        encoding="utf-8",
    )

    assert runner.collect_failed_test_refs(
        [_failed_result(tmp_path, report_path)]
    ) == {}


def test_run_shards_refuses_symlinked_failure_ref_root(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    failure_ref_root = tmp_path / "failure-refs"
    failure_ref_root.symlink_to(target, target_is_directory=True)

    with pytest.raises(ValueError, match="failure-ref root"):
        runner.run_shards(
            [runner.ShardPlan(0, ("tests/test_example.py",), 1.0)],
            root=tmp_path,
            basetemp=tmp_path / "shards",
            failure_ref_dir=failure_ref_root,
            write_timings=False,
            quiet=True,
            max_workers=1,
        )


def test_failure_ref_run_directory_is_fresh_and_ignores_stale_base_file(
    tmp_path: Path,
) -> None:
    failure_ref_root = tmp_path / "failure-refs"
    failure_ref_root.mkdir()
    stale_file = failure_ref_root / "pytest-shard-0.json"
    stale_file.write_text("stale", encoding="utf-8")

    run_dir = runner._prepare_failure_ref_run_dir(failure_ref_root, "run-ref")

    assert run_dir == failure_ref_root / "run-ref"
    assert run_dir.is_dir()
    assert not (run_dir / stale_file.name).exists()
    assert stat.S_IMODE(run_dir.stat().st_mode) == 0o700
