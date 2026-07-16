from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.verification import pytest_collection_evidence as evidence
from scripts.verification import run_pytest_shards as runner


ROOT = Path(__file__).resolve().parents[1]
PLAN_REF = "pytest-shard-plan-ref:sha256:" + "a" * 64


def _private_directory(path: Path) -> Path:
    path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path


def _write_sidecar(
    directory: Path,
    *,
    index: int,
    count: int,
    nodeids: tuple[str, ...],
    plan_ref: str = PLAN_REF,
    errors: int = 0,
) -> Path:
    sidecar = directory / f"shard-{index}.json"
    item = evidence.build_shard_evidence(
        nodeids,
        shard_index=index,
        shard_count=count,
        plan_fingerprint_ref=plan_ref,
        collection_error_count=errors,
    )
    evidence.write_new_evidence(sidecar, item.to_payload())
    return sidecar


def test_shard_evidence_hashes_nodeids_and_is_order_independent() -> None:
    nodeids = (
        "tests/test_private.py::test_secret[operator-value]",
        "tests/test_private.py::test_other",
    )

    first = evidence.build_shard_evidence(
        nodeids,
        shard_index=0,
        shard_count=1,
        plan_fingerprint_ref=PLAN_REF,
    )
    second = evidence.build_shard_evidence(
        reversed(nodeids),
        shard_index=0,
        shard_count=1,
        plan_fingerprint_ref=PLAN_REF,
    )

    assert first == second
    assert first.collected_test_count == 2
    assert first.unique_test_count == 2
    rendered = json.dumps(first.to_payload())
    assert "operator-value" not in rendered
    assert "test_private" not in rendered


def test_duplicate_nodeids_are_content_free_and_fail_aggregation(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path / "evidence")
    sidecar = _write_sidecar(
        directory,
        index=0,
        count=1,
        nodeids=("tests/test_a.py::test_one", "tests/test_a.py::test_one"),
    )

    assert "test_one" not in sidecar.read_text(encoding="utf-8")
    with pytest.raises(evidence.CollectionEvidenceError, match="duplicate node IDs"):
        evidence.aggregate_shard_evidence(
            [sidecar],
            expected_shard_count=1,
            expected_plan_fingerprint_ref=PLAN_REF,
        )


def test_aggregate_is_exact_contiguous_and_arrival_order_independent(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path / "evidence")
    first = _write_sidecar(
        directory,
        index=0,
        count=2,
        nodeids=("tests/test_a.py::test_one",),
    )
    second = _write_sidecar(
        directory,
        index=1,
        count=2,
        nodeids=("tests/test_b.py::test_two", "tests/test_b.py::test_three"),
    )

    forward = evidence.aggregate_shard_evidence(
        [first, second],
        expected_shard_count=2,
        expected_plan_fingerprint_ref=PLAN_REF,
    )
    reverse = evidence.aggregate_shard_evidence(
        [second, first],
        expected_shard_count=2,
        expected_plan_fingerprint_ref=PLAN_REF,
    )

    assert forward == reverse
    assert forward["collected_test_count"] == 3
    assert "unique_test_count" not in forward
    assert forward["redaction_status"] == "content_free"


def test_aggregate_loader_requires_exact_schema_and_bindings(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path / "evidence")
    sidecar = _write_sidecar(
        directory,
        index=0,
        count=1,
        nodeids=("tests/test_a.py::test_one",),
    )
    output = directory / "aggregate.json"
    evidence.publish_aggregate_evidence(
        [sidecar],
        output_path=output,
        expected_shard_count=1,
        expected_plan_fingerprint_ref=PLAN_REF,
    )

    loaded = evidence.load_aggregate_evidence(
        output,
        expected_shard_count=1,
        expected_plan_fingerprint_ref=PLAN_REF,
    )

    assert loaded["collected_test_count"] == 1
    assert loaded["collection_digest_ref"].startswith("sha256:")
    with pytest.raises(evidence.CollectionEvidenceError, match="binding"):
        evidence.load_aggregate_evidence(
            output,
            expected_shard_count=2,
            expected_plan_fingerprint_ref=PLAN_REF,
        )
    with pytest.raises(evidence.CollectionEvidenceError, match="binding"):
        evidence.load_aggregate_evidence(
            output,
            expected_shard_count=1,
            expected_plan_fingerprint_ref=(
                "pytest-shard-plan-ref:sha256:" + "b" * 64
            ),
        )


def test_aggregate_loader_rejects_extra_fields_and_boolean_counts(
    tmp_path: Path,
) -> None:
    for name, mutation, message in (
        ("extra", {"unexpected": "field"}, "fields"),
        ("bool-count", {"collected_test_count": True}, "counts"),
        ("bool-shards", {"shard_count": True}, "types"),
    ):
        directory = _private_directory(tmp_path / name)
        path = directory / "aggregate.json"
        payload = {
            "collected_test_count": 1,
            "collection_digest_ref": "sha256:" + "c" * 64,
            "collection_error_count": 0,
            "plan_fingerprint_ref": PLAN_REF,
            "redaction_status": "content_free",
            "schema_version": evidence.AGGREGATE_SCHEMA_VERSION,
            "shard_count": 1,
            **mutation,
        }
        evidence.write_new_evidence(path, payload)

        with pytest.raises(evidence.CollectionEvidenceError, match=message):
            evidence.load_aggregate_evidence(
                path,
                expected_shard_count=1,
                expected_plan_fingerprint_ref=PLAN_REF,
            )


@pytest.mark.parametrize("posture", ["missing", "duplicate", "wrong-plan", "error"])
def test_aggregate_fails_closed_for_incomplete_or_invalid_sets(
    tmp_path: Path, posture: str
) -> None:
    directory = _private_directory(tmp_path / "evidence")
    first = _write_sidecar(
        directory,
        index=0,
        count=2,
        nodeids=("tests/test_a.py::test_one",),
        errors=1 if posture == "error" else 0,
    )
    second = _write_sidecar(
        directory,
        index=1,
        count=2,
        nodeids=("tests/test_b.py::test_two",),
        plan_ref=(
            "pytest-shard-plan-ref:sha256:" + "b" * 64
            if posture == "wrong-plan"
            else PLAN_REF
        ),
    )
    paths = {
        "missing": [first],
        "duplicate": [first, first],
        "wrong-plan": [first, second],
        "error": [first, second],
    }[posture]

    with pytest.raises(evidence.CollectionEvidenceError):
        evidence.aggregate_shard_evidence(
            paths,
            expected_shard_count=2,
            expected_plan_fingerprint_ref=PLAN_REF,
        )


def test_safe_evidence_io_rejects_symlink_fifo_hardlink_and_unsafe_mode(
    tmp_path: Path,
) -> None:
    if os.name != "posix":
        pytest.skip("strict POSIX artifact proof")
    directory = _private_directory(tmp_path / "evidence")
    regular = _write_sidecar(
        directory,
        index=0,
        count=1,
        nodeids=("tests/test_a.py::test_one",),
    )
    symlink = directory / "symlink.json"
    symlink.symlink_to(regular)
    fifo = directory / "fifo.json"
    os.mkfifo(fifo, mode=0o600)

    with pytest.raises(evidence.CollectionEvidenceError):
        evidence.read_evidence(symlink)
    with pytest.raises(evidence.CollectionEvidenceError):
        evidence.read_evidence(fifo)

    hardlink = directory / "hardlink.json"
    os.link(regular, hardlink)
    with pytest.raises(evidence.CollectionEvidenceError):
        evidence.read_evidence(regular)
    hardlink.unlink()

    regular.chmod(0o644)
    with pytest.raises(evidence.CollectionEvidenceError):
        evidence.read_evidence(regular)


def test_evidence_reader_rejects_duplicate_json_fields(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path / "evidence")
    path = directory / "duplicate-fields.json"
    path.write_text('{"schema_version":"one","schema_version":"two"}\n')
    path.chmod(0o600)

    with pytest.raises(evidence.CollectionEvidenceError, match="duplicate fields"):
        evidence.read_evidence(path)


def test_safe_evidence_publish_is_exclusive_owner_only_and_bounded(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path / "evidence")
    output = directory / "aggregate.json"
    payload = {"schema_version": "safe"}

    evidence.write_new_evidence(output, payload)

    metadata = output.lstat()
    assert stat.S_ISREG(metadata.st_mode)
    assert metadata.st_nlink == 1
    assert stat.S_IMODE(metadata.st_mode) == 0o600
    assert metadata.st_size <= evidence.MAX_EVIDENCE_BYTES
    with pytest.raises(evidence.CollectionEvidenceError, match="already exists"):
        evidence.write_new_evidence(output, payload)
    with pytest.raises(evidence.CollectionEvidenceError, match="size bound"):
        evidence.write_new_evidence(
            directory / "too-large.json",
            {"value": "x" * evidence.MAX_EVIDENCE_BYTES},
        )


def test_collection_bounds_reject_oversized_test_and_shard_sets() -> None:
    oversized = (f"tests/test_a.py::test_{index}" for index in range(100_001))
    item = evidence.build_shard_evidence(
        oversized,
        shard_index=0,
        shard_count=1,
        plan_fingerprint_ref=PLAN_REF,
    )
    assert item.collected_test_count == evidence.MAX_TESTS
    assert item.collection_error_count == 1

    with pytest.raises(evidence.CollectionEvidenceError, match="shard bounds"):
        evidence.build_shard_evidence(
            (),
            shard_index=0,
            shard_count=evidence.MAX_SHARDS + 1,
            plan_fingerprint_ref=PLAN_REF,
        )


def test_real_pytest_invocation_writes_only_content_free_collection_evidence(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path / "evidence")
    sidecar = directory / "shard-0.json"
    test_file = tmp_path / "test_observed_collection.py"
    test_file.write_text(
        "import pytest\n"
        "@pytest.mark.parametrize('value', [1], ids=['private-parameter'])\n"
        "def test_observed(value):\n"
        "    assert value == 1\n",
        encoding="utf-8",
    )
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "scripts.verification.pytest_collection_evidence",
        "--uaa-collection-evidence-sidecar",
        str(sidecar),
        "--uaa-collection-shard-index",
        "0",
        "--uaa-collection-shard-count",
        "1",
        "--uaa-collection-plan-fingerprint",
        PLAN_REF,
        str(test_file),
    ]

    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    item = evidence.load_shard_evidence(sidecar)
    assert item.collected_test_count == 1
    rendered = sidecar.read_text(encoding="utf-8")
    assert "private-parameter" not in rendered
    assert "test_observed" not in rendered
    assert str(tmp_path) not in rendered


def test_real_collection_error_is_recorded_and_cannot_aggregate(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path / "evidence")
    sidecar = directory / "shard-0.json"
    test_file = tmp_path / "test_collection_error.py"
    test_file.write_text("def broken(:\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "scripts.verification.pytest_collection_evidence",
            "--uaa-collection-evidence-sidecar",
            str(sidecar),
            "--uaa-collection-shard-index",
            "0",
            "--uaa-collection-shard-count",
            "1",
            "--uaa-collection-plan-fingerprint",
            PLAN_REF,
            str(test_file),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    item = evidence.load_shard_evidence(sidecar)
    assert item.collection_error_count >= 1
    with pytest.raises(evidence.CollectionEvidenceError, match="collection reported"):
        evidence.aggregate_shard_evidence(
            [sidecar],
            expected_shard_count=1,
            expected_plan_fingerprint_ref=PLAN_REF,
        )


def test_runner_option_uses_real_shard_process_and_publishes_aggregate(
    tmp_path: Path,
) -> None:
    output_dir = _private_directory(tmp_path / "output")
    output = output_dir / "collection.json"
    test_file = tmp_path / "test_runner_collection.py"
    test_file.write_text("def test_runner_collection(): pass\n", encoding="utf-8")
    plan = runner.ShardPlan(0, (str(test_file),), 0.0)
    plan_ref = runner.shard_plan_fingerprint([plan])

    results = runner.run_shards(
        [plan],
        root=ROOT,
        basetemp=tmp_path / "shards",
        failure_ref_dir=None,
        write_timings=False,
        quiet=True,
        collection_evidence_output=output,
        collection_plan_fingerprint_ref=plan_ref,
    )

    assert runner.overall_return_code(results) == 0
    payload = evidence.read_evidence(output)
    assert payload["schema_version"] == evidence.AGGREGATE_SCHEMA_VERSION
    assert payload["collected_test_count"] == 1
    assert payload["plan_fingerprint_ref"] == plan_ref
    assert "test_runner_collection" not in json.dumps(payload)


def test_build_command_and_cli_leave_default_behavior_unchanged(tmp_path: Path) -> None:
    plan = runner.ShardPlan(0, ("tests/test_a.py",), 0.0)
    default_command = runner.build_pytest_command(
        plan,
        tmp_path / "base",
        write_timings=False,
        failure_ref_dir=None,
    )
    evidence_command = runner.build_pytest_command(
        plan,
        tmp_path / "base",
        write_timings=False,
        failure_ref_dir=None,
        collection_evidence_dir=tmp_path,
        collection_shard_count=1,
        collection_plan_fingerprint_ref=PLAN_REF,
    )

    assert "scripts.verification.pytest_collection_evidence" not in default_command
    assert "--uaa-collection-evidence-sidecar" not in default_command
    assert "scripts.verification.pytest_collection_evidence" in evidence_command
    assert runner.main(
        [
            "--shards",
            "8",
            "--shard-index",
            "2",
            "--collection-evidence",
            str(tmp_path / "collection.json"),
        ]
    ) == 2


def test_missing_sidecars_fail_the_runner_instead_of_minting_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class ImmediateProcess:
        returncode = 0

    monkeypatch.setattr(
        runner.shard_processes,
        "spawn_owned_process_group",
        lambda *_args, **_kwargs: ImmediateProcess(),
    )
    monkeypatch.setattr(
        runner.shard_processes,
        "process_group_leader_is_terminal_without_reaping",
        lambda _process: True,
    )
    monkeypatch.setattr(
        runner.shard_processes,
        "stop_processes",
        lambda _processes, _grace: None,
    )
    output_dir = _private_directory(tmp_path / "output")

    with pytest.raises(evidence.CollectionEvidenceError, match="unavailable"):
        runner.run_shards(
            [runner.ShardPlan(0, ("tests/test_a.py",), 0.0)],
            root=tmp_path,
            basetemp=tmp_path / "shards",
            failure_ref_dir=None,
            write_timings=False,
            quiet=True,
            collection_evidence_output=output_dir / "collection.json",
            collection_plan_fingerprint_ref=PLAN_REF,
        )


def test_collection_evidence_rejects_overlapping_shard_file_ownership(
    tmp_path: Path,
) -> None:
    output_dir = _private_directory(tmp_path / "output")

    with pytest.raises(evidence.CollectionEvidenceError, match="unique shard file"):
        runner.run_shards(
            [
                runner.ShardPlan(0, ("tests/test_a.py",), 0.0),
                runner.ShardPlan(1, ("tests/test_a.py",), 0.0),
            ],
            root=tmp_path,
            basetemp=tmp_path / "shards",
            failure_ref_dir=None,
            write_timings=False,
            quiet=True,
            collection_evidence_output=output_dir / "collection.json",
            collection_plan_fingerprint_ref=PLAN_REF,
        )


def test_runner_rejects_existing_aggregate_before_launching_tests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launched = False

    class UnexpectedProcess:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            nonlocal launched
            launched = True

    monkeypatch.setattr(runner.subprocess, "Popen", UnexpectedProcess)
    output_dir = _private_directory(tmp_path / "output")
    output = output_dir / "collection.json"
    output.write_text("reserved\n", encoding="utf-8")
    output.chmod(0o600)

    with pytest.raises(evidence.CollectionEvidenceError, match="already exists"):
        runner.run_shards(
            [runner.ShardPlan(0, ("tests/test_a.py",), 0.0)],
            root=tmp_path,
            basetemp=tmp_path / "shards",
            failure_ref_dir=None,
            write_timings=False,
            quiet=True,
            collection_evidence_output=output,
            collection_plan_fingerprint_ref=PLAN_REF,
        )
    assert launched is False
