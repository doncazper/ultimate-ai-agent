from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.verification import test_corpus_guard as guard


def _record(
    retired_ref: str,
    replacement_ref: str,
) -> dict[str, object]:
    replacement_refs = [replacement_ref]
    equivalence_artifact = {
        "schema_version": guard.ASSERTION_EQUIVALENCE_SCHEMA,
        "retired_ref": retired_ref,
        "replacement_refs": replacement_refs,
        "preserved_assertion_refs": ["assertion-ref:sha256:" + ("a" * 64)],
    }
    evidence_artifact = {
        "schema_version": guard.RETIREMENT_EVIDENCE_SCHEMA,
        "retired_ref": retired_ref,
        "replacement_refs": replacement_refs,
        "verification_refs": ["test-result-ref:sha256:" + ("b" * 64)],
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
            "preserved_assertion_refs",
            "equivalence ref is invalid",
        ),
        (
            "evidence_artifact",
            "verification_refs",
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
    artifact[list_field] = (
        ["assertion-ref:sha256:" + ("c" * 64)]
        if list_field == "preserved_assertion_refs"
        else ["test-result-ref:sha256:" + ("c" * 64)]
    )

    with pytest.raises(guard.TestCorpusGuardError, match=message):
        guard.validate_retirements(
            {replacement},
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
