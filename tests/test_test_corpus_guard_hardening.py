from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.verification import test_corpus_guard as guard


def _record(
    retired_ref: str,
    replacement_ref: str,
) -> dict[str, object]:
    replacement_refs = [replacement_ref]
    assertion_artifact = {
        "schema_version": guard.ASSERTION_EVIDENCE_SCHEMA,
        "replacement_ref": replacement_ref,
        "safe_summary": "The replacement preserves the exact guarded assertion.",
    }
    result_artifact = {
        "schema_version": guard.TEST_RESULT_EVIDENCE_SCHEMA,
        "status": "passed",
        "verified_refs": replacement_refs,
        "safe_summary": "Focused verification passed for the replacement behavior.",
    }
    equivalence_artifact = {
        "schema_version": guard.ASSERTION_EQUIVALENCE_SCHEMA,
        "retired_ref": retired_ref,
        "replacement_refs": replacement_refs,
        "preserved_assertion_evidence": [
            {
                "artifact": assertion_artifact,
                "ref": guard.retirement_artifact_ref(
                    "assertion-ref", assertion_artifact
                ),
            }
        ],
    }
    evidence_artifact = {
        "schema_version": guard.RETIREMENT_EVIDENCE_SCHEMA,
        "retired_ref": retired_ref,
        "replacement_refs": replacement_refs,
        "verification_evidence": [
            {
                "artifact": result_artifact,
                "ref": guard.retirement_artifact_ref(
                    "test-result-ref", result_artifact
                ),
            }
        ],
    }
    return {
        "retired_ref": retired_ref,
        "replacement_refs": replacement_refs,
        "reason": "The replacement preserves the same exact defect class.",
        "assertion_equivalence_artifact": equivalence_artifact,
        "assertion_equivalence_ref": guard.retirement_artifact_ref(
            "assertion-equivalence-ref",
            equivalence_artifact,
        ),
        "evidence_artifact": evidence_artifact,
        "evidence_ref": guard.retirement_artifact_ref(
            "test-corpus-evidence-ref",
            evidence_artifact,
        ),
    }


@pytest.mark.parametrize(
    ("artifact_field", "list_field", "message"),
    (
        (
            "assertion_equivalence_artifact",
            "preserved_assertion_evidence",
            "equivalence ref is invalid",
        ),
        (
            "evidence_artifact",
            "verification_evidence",
            "evidence ref is invalid",
        ),
    ),
)
def test_retirement_artifact_hashes_are_recomputed(
    artifact_field: str,
    list_field: str,
    message: str,
) -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    record = _record(retired, replacement)
    artifact = record[artifact_field]
    assert isinstance(artifact, dict)
    evidence = artifact[list_field]
    assert isinstance(evidence, list)
    nested = evidence[0]
    assert isinstance(nested, dict)
    nested_artifact = nested["artifact"]
    assert isinstance(nested_artifact, dict)
    nested_artifact["safe_summary"] = (
        "This changed nested artifact no longer matches its content-bound ref."
    )
    nested["ref"] = guard.retirement_artifact_ref(
        (
            "assertion-ref"
            if list_field == "preserved_assertion_evidence"
            else "test-result-ref"
        ),
        nested_artifact,
    )

    with pytest.raises(guard.TestCorpusGuardError, match=message):
        guard.validate_retirements(
            {replacement},
            {retired},
            {"retirements": [record]},
        )


def test_assertion_evidence_covers_every_replacement() -> None:
    retired = "tests/test_sample.py::test_removed"
    first = "tests/test_sample.py::test_first_replacement"
    second = "tests/test_sample.py::test_second_replacement"
    record = _record(retired, first)
    replacement_refs = record["replacement_refs"]
    assert isinstance(replacement_refs, list)
    replacement_refs.append(second)
    equivalence = record["assertion_equivalence_artifact"]
    evidence = record["evidence_artifact"]
    assert isinstance(equivalence, dict)
    assert isinstance(evidence, dict)
    verification = evidence["verification_evidence"]
    assert isinstance(verification, list)
    result = verification[0]
    assert isinstance(result, dict)
    result_artifact = result["artifact"]
    assert isinstance(result_artifact, dict)
    result["ref"] = guard.retirement_artifact_ref("test-result-ref", result_artifact)
    record["assertion_equivalence_ref"] = guard.retirement_artifact_ref(
        "assertion-equivalence-ref", equivalence
    )
    record["evidence_ref"] = guard.retirement_artifact_ref(
        "test-corpus-evidence-ref", evidence
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="preserved assertion evidence is invalid",
    ):
        guard.validate_retirements(
            {first, second},
            {retired},
            {"retirements": [record]},
        )


def test_historical_retirement_records_are_immutable() -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    historical = _record(retired, replacement)
    changed = _record(retired, replacement)
    changed["reason"] = "This later reason tries to rewrite accepted evidence."

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="historical retirement record changed",
    ):
        guard.validate_retirements(
            {replacement},
            set(),
            {"retirements": [changed]},
            base_ledger={"retirements": [historical]},
        )


def test_historical_replacement_retirement_preserves_an_active_chain() -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    successor = "tests/test_sample.py::test_successor"
    historical = _record(retired, replacement)
    replacement_retirement = _record(replacement, successor)

    count = guard.validate_retirements(
        {successor},
        {replacement},
        {"retirements": [historical, replacement_retirement]},
        base_ledger={"retirements": [historical]},
    )

    assert count == 2


def test_replacement_chain_reaches_active_test_without_base_ledger() -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    successor = "tests/test_sample.py::test_successor"

    count = guard.validate_retirements(
        {successor},
        set(),
        {
            "retirements": [
                _record(retired, replacement),
                _record(replacement, successor),
            ]
        },
    )

    assert count == 2


def test_new_retirement_record_must_match_a_removed_test() -> None:
    retired = "tests/test_sample.py::test_typo"
    replacement = "tests/test_sample.py::test_replacement"

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="retirement records do not match removed tests",
    ):
        guard.validate_retirements(
            {replacement},
            set(),
            {"retirements": [_record(retired, replacement)]},
            base_ledger={"retirements": []},
        )


def test_worktree_inventory_reader_rejects_symlinked_parent(
    tmp_path: Path,
) -> None:
    external = tmp_path / "external"
    external.mkdir()
    (external / "test_external.py").write_text(
        "def test_external(): pass\n",
        encoding="utf-8",
    )
    tests_link = tmp_path / "tests"
    tests_link.symlink_to(external, target_is_directory=True)

    with pytest.raises(guard.TestCorpusGuardError, match="file is unsafe"):
        guard._read_worktree_text(tmp_path, "tests/test_external.py")


def test_worktree_reader_closes_parent_descriptors_on_missing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    opened = iter((101, 102))
    closed: list[int] = []

    def fake_open(*_args: object, **_kwargs: object) -> int:
        try:
            return next(opened)
        except StopIteration:
            raise FileNotFoundError from None

    monkeypatch.setattr(guard.os, "open", fake_open)
    monkeypatch.setattr(
        guard.os,
        "fstat",
        lambda _descriptor: os.stat_result((0o040000, 0, 0, 1, 0, 0, 0, 0, 0, 0)),
    )
    monkeypatch.setattr(guard.os, "close", closed.append)

    with pytest.raises(guard.TestCorpusGuardError, match="cannot read test inventory"):
        guard._read_worktree_text(tmp_path, "tests/test_missing.py")

    assert closed == [101, 102]


def test_worktree_reader_closes_new_descriptor_when_fstat_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    opened = iter((101, 102))
    closed: list[int] = []

    monkeypatch.setattr(guard.os, "open", lambda *_args, **_kwargs: next(opened))

    def fake_fstat(descriptor: int) -> os.stat_result:
        if descriptor == 102:
            raise OSError("inspection failed")
        return os.stat_result((0o040000, 0, 0, 1, 0, 0, 0, 0, 0, 0))

    monkeypatch.setattr(guard.os, "fstat", fake_fstat)
    monkeypatch.setattr(guard.os, "close", closed.append)

    with pytest.raises(guard.TestCorpusGuardError, match="file is unsafe"):
        guard._read_worktree_text(tmp_path, "tests/test_example.py")

    assert closed == [102, 101]


def test_run_git_translates_spawn_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def unavailable(*_args: object, **_kwargs: object) -> subprocess.Popen[bytes]:
        raise FileNotFoundError("git unavailable")

    monkeypatch.setattr(guard.subprocess, "Popen", unavailable)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="git inspection is unavailable",
    ) as caught:
        guard._run_git(tmp_path, ["status"])

    assert isinstance(caught.value.__cause__, FileNotFoundError)


def test_changed_test_paths_union_index_worktree_and_untracked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = iter(
        (
            b"tests/test_head.py\0",
            b"tests/test_index.py\0",
            b"tests/test_worktree.py\0",
            b"tests/test_untracked.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=next(outputs),
            stderr=b"",
        ),
    )

    assert guard._changed_test_paths(Path("."), "a" * 40) == (
        "tests/test_head.py",
        "tests/test_index.py",
        "tests/test_untracked.py",
        "tests/test_worktree.py",
    )


def test_changed_test_paths_enforce_aggregate_byte_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"x" * (guard.MAX_CHANGED_PATH_BYTES + 1),
            stderr=b"",
        ),
    )

    with pytest.raises(guard.TestCorpusGuardError, match="exceed byte budget"):
        guard._changed_test_paths(Path("."), "a" * 40)


def test_existing_base_blob_read_failure_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    results = iter(
        (
            subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=b"100\n",
                stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout=b"",
                stderr=b"",
            ),
        )
    )
    monkeypatch.setattr(guard, "_run_git", lambda _repo, _args: next(results))

    with pytest.raises(guard.TestCorpusGuardError, match="cannot read base test file"):
        guard._base_text(Path("."), "a" * 40, "tests/test_example.py")


def test_existing_base_ledger_inspection_failure_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = guard.RETIREMENT_LEDGER.as_posix()
    results = iter(
        (
            subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=path.encode("utf-8") + b"\0",
                stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout=b"",
                stderr=b"",
            ),
        )
    )
    monkeypatch.setattr(guard, "_run_git", lambda _repo, _args: next(results))

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="cannot inspect base test-corpus retirement ledger",
    ):
        guard._load_base_ledger(Path("."), "a" * 40)


def test_case_only_rename_retires_the_exact_old_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_path = "apps/control-center/src/example.test.ts"
    new_path = "apps/control-center/src/Example.test.ts"
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base: (old_path, new_path),
    )
    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (new_path,))
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            'test("case-bound declaration", () => {});' if path == old_path else None
        ),
    )
    monkeypatch.setattr(
        guard,
        "_read_worktree_text",
        lambda _repo, path: (
            'test("case-bound declaration", () => {});' if path == new_path else ""
        ),
    )

    assert guard.removed_declarations(Path("."), "a" * 40) == (
        f"{old_path}::case-bound declaration",
    )
