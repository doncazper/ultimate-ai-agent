from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

import pytest

from scripts.verification import test_corpus_guard as guard


VERIFICATION_ENVELOPE = "github-verification-envelope:test-fixture"


def _visual_timeout_manifest_source() -> str:
    return (
        "def _command_from_release(command):\n"
        '    timeout = 600 if category == "frontend" else 300\n'
        '    if command.command_ref == "command:foundation-gate.report-only":\n'
        "        timeout = 900\n"
        "\n"
        "def command_registry():\n"
        "    return {\n"
        '            "command:foundation-gate.ci-parallel": CommandSpec(\n'
        '                "command:foundation-gate.ci-parallel",\n'
        "                (\n"
        '                    ".venv/bin/python",\n'
        '                    "-I",\n'
        '                    "-B",\n'
        '                    "-S",\n'
        '                    "scripts/run_foundation_gate.py",\n'
        '                    "--command-mode",\n'
        '                    "ci-parallel",\n'
        '                    "--ci-prerequisite-manifest",\n'
        '                    "{temp_root}/uaa_foundation_prerequisite_manifest.json",\n'
        '                    "--ci-prerequisite-sha",\n'
        '                    "{repository_sha}",\n'
        '                    "--ci-prerequisite-base-sha",\n'
        '                    "{base_sha}",\n'
        '                    "--no-write-latest",\n'
        "                ),\n"
        "                (),\n"
        '                "gate",\n'
        "                300,\n"
        "            ),\n"
        "    }\n"
    )


def test_exact_visual_timeout_alignment_is_admitted() -> None:
    path = "scripts/verification/ci_command_manifest.py"
    prior = _visual_timeout_manifest_source()
    current = prior.replace(
        '    if command.command_ref == "command:foundation-gate.report-only":\n',
        '    if command.command_ref == "command:frontend.visual-regression":\n'
        "        timeout = 930\n"
        '    if command.command_ref == "command:foundation-gate.report-only":\n',
    )

    assert guard._safe_visual_regression_timeout_alignment_paths(
        current_by_path={path: current},
        prior_by_path={path: prior},
    ) == {path}


def test_exact_terminal_foundation_timeout_alignment_is_admitted() -> None:
    path = "scripts/verification/ci_command_manifest.py"
    prior = _visual_timeout_manifest_source()
    current = prior.replace(
        '    if command.command_ref == "command:foundation-gate.report-only":\n',
        '    if command.command_ref == "command:frontend.visual-regression":\n'
        "        timeout = 930\n"
        '    if command.command_ref == "command:foundation-gate.report-only":\n',
    ).replace(
        '                "gate",\n                300,\n',
        '                "gate",\n                900,\n',
    )

    assert guard._safe_visual_regression_timeout_alignment_paths(
        current_by_path={path: current},
        prior_by_path={path: prior},
    ) == {path}


@pytest.mark.parametrize(
    "mutation",
    (
        "\n# unrelated runner change\n",
        '\nPYTEST_ARGS = ("--ignore", "tests/security")\n',
    ),
)
def test_visual_timeout_alignment_rejects_extra_runner_changes(
    mutation: str,
) -> None:
    path = "scripts/verification/ci_command_manifest.py"
    prior = _visual_timeout_manifest_source()
    current = prior.replace(
        '    if command.command_ref == "command:foundation-gate.report-only":\n',
        '    if command.command_ref == "command:frontend.visual-regression":\n'
        "        timeout = 930\n"
        '    if command.command_ref == "command:foundation-gate.report-only":\n',
    )

    assert guard._safe_visual_regression_timeout_alignment_paths(
        current_by_path={path: current + mutation},
        prior_by_path={path: prior},
    ) == set()


def test_visual_scope_expansion_preserves_all_runner_configuration() -> None:
    path = "scripts/verification/ci_command_manifest.py"
    prior = 'VISUAL_SCOPE_PATHS = ("apps/control-center",)\nPYTEST_ARGS = ("tests",)\n'
    current = prior.replace(
        '("apps/control-center",)',
        '("apps/control-center", "scripts/verification/run_frontend_playwright.py")',
    )
    assert guard._safe_visual_scope_expansion_paths(
        current_by_path={path: current}, prior_by_path={path: prior},
    ) == {path}
    assert not guard._safe_visual_scope_expansion_paths(
        current_by_path={path: current, "scripts/verification/run_pytest_shards.py": "changed"},
        prior_by_path={path: prior},
    )


@pytest.mark.parametrize("scope", (
    '()',
    '("docs/control_center",)',
    '("apps/control-center", "apps/control-center", "docs/control_center")',
    'tuple(("apps/control-center", "docs/control_center"))',
    '("apps/control-center", *EXTRA_PATHS)',
    '("apps/control-center", False)',
    '("apps/control-center", "../tests")',
    '("apps/control-center", "/tests")',
))
def test_visual_scope_expansion_rejects_removals_and_dynamic_paths(scope: str) -> None:
    path = "scripts/verification/ci_command_manifest.py"
    prior = 'VISUAL_SCOPE_PATHS = ("apps/control-center",)\nPYTEST_ARGS = ("tests",)\n'
    current = f'VISUAL_SCOPE_PATHS = {scope}\nPYTEST_ARGS = ("tests",)\n'
    assert not guard._safe_visual_scope_expansion_paths(
        current_by_path={path: current}, prior_by_path={path: prior},
    )


@pytest.mark.parametrize("extra", (
    'PYTEST_ARGS = ("--ignore", "tests/security")\n',
    'TIMEOUT_SECONDS = 99999\n',
    'VISUAL_SCOPE_PATHS = ()\n',
))
def test_visual_scope_expansion_rejects_any_other_executable_change(extra: str) -> None:
    path = "scripts/verification/ci_command_manifest.py"
    prior = 'VISUAL_SCOPE_PATHS = ("apps/control-center",)\nPYTEST_ARGS = ("tests",)\n'
    current = prior.replace(
        '("apps/control-center",)', '("apps/control-center", "docs/control_center")',
    ) + extra
    assert not guard._safe_visual_scope_expansion_paths(
        current_by_path={path: current}, prior_by_path={path: prior},
    )


@pytest.mark.parametrize("mutation", ("expand", "reorder", "remove", "command", "syntax"))
def test_changed_visual_scope_configuration_requires_additive_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    path = "scripts/verification/ci_command_manifest.py"
    prior = (
        'VISUAL_SCOPE_PATHS = ("apps/control-center", "docs/control_center")\n'
        'PYTEST_ARGS = ("tests",)\n'
    )
    current = prior.replace(
        '"docs/control_center")',
        '"docs/control_center", "scripts/verification/run_frontend_playwright.py")',
    )
    if mutation == "reorder":
        current = current.replace(
            '"apps/control-center", "docs/control_center"',
            '"docs/control_center", "apps/control-center"',
        )
    elif mutation == "remove":
        current = current.replace('"apps/control-center", ', "")
    elif mutation == "command":
        current = current.replace('("tests",)', '("--ignore", "tests/security")')
    elif mutation == "syntax":
        current += "broken = (\n"
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text(current)
    outputs = iter((f"{path}\0".encode(), b"", b"", b"",
                    str(len(prior.encode())).encode(), prior.encode()))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b"",
        ),
    )
    if mutation == "expand":
        assert guard._changed_test_paths(tmp_path, "a" * 40) == ()
    else:
        with pytest.raises(guard.TestCorpusGuardError, match="pytest runner configuration"):
            guard._changed_test_paths(tmp_path, "a" * 40)


def test_exact_httpx2_security_dependency_alignment_is_pair_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_path = "pyproject.toml"
    lock_path = "uv.lock"
    prior = {
        project_path: 'dev = ["httpx2>=2.5.0,<3.0.0"]\n',
        lock_path: 'name = "httpx2"\nversion = "2.5.0"\n',
    }
    current = {
        project_path: 'dev = ["httpx2>=2.12.0,<3.0.0"]\n',
        lock_path: 'name = "httpx2"\nversion = "2.12.0"\n',
    }
    monkeypatch.setattr(
        guard,
        "HTTPX2_SECURITY_DEPENDENCY_APPROVED_SHA256_BY_PATH",
        {
            path: (
                hashlib.sha256(prior[path].encode()).hexdigest(),
                hashlib.sha256(current[path].encode()).hexdigest(),
            )
            for path in prior
        },
    )

    assert guard._safe_httpx2_security_dependency_alignment_paths(
        current_by_path=current,
        prior_by_path=prior,
    ) == {project_path, lock_path}
    assert not guard._safe_httpx2_security_dependency_alignment_paths(
        current_by_path={
            **current,
            lock_path: current[lock_path] + "pytest-exclusion = true\n",
        },
        prior_by_path=prior,
    )
    assert not guard._safe_httpx2_security_dependency_alignment_paths(
        current_by_path=current,
        prior_by_path={
            **prior,
            project_path: prior[project_path] + "# different base\n",
        },
    )
    assert not guard._safe_httpx2_security_dependency_alignment_paths(
        current_by_path={project_path: current[project_path]},
        prior_by_path={project_path: prior[project_path]},
    )


def test_httpx2_security_dependency_current_fingerprints_are_exact() -> None:
    root = Path(__file__).parents[1]
    assert set(guard.HTTPX2_SECURITY_DEPENDENCY_APPROVED_SHA256_BY_PATH) == set(
        guard.ANYIO_SECURITY_DEPENDENCY_APPROVED_SHA256_BY_PATH
    )
    for path, (_, historical_current_digest) in (
        guard.HTTPX2_SECURITY_DEPENDENCY_APPROVED_SHA256_BY_PATH.items()
    ):
        prior_digest, current_digest = (
            guard.ANYIO_SECURITY_DEPENDENCY_APPROVED_SHA256_BY_PATH[path]
        )
        assert historical_current_digest == prior_digest
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == current_digest


def _source_ref(test_ref: str) -> str:
    return guard.build_test_source_ref(test_ref, f"verified-source:{test_ref}")


def _validate_envelope(value: str, _replacement_refs: list[str]) -> None:
    if value != VERIFICATION_ENVELOPE:
        raise ValueError("verification envelope is invalid")


def _validate_retirements(*args: object, **kwargs: object) -> int:
    return guard.validate_retirements(
        *args,
        resolve_assertion_source_ref=_source_ref,
        validate_verification_envelope=_validate_envelope,
        **kwargs,
    )


def _record(
    retired_ref: str,
    replacement_ref: str,
) -> dict[str, object]:
    replacement_refs = [replacement_ref]
    assertion_artifact = {
        "schema_version": guard.ASSERTION_EVIDENCE_SCHEMA,
        "replacement_ref": replacement_ref,
        "source_ref": _source_ref(replacement_ref),
    }
    result_artifact = {
        "schema_version": guard.TEST_RESULT_EVIDENCE_SCHEMA,
        "verified_refs": replacement_refs,
        "verification_envelope": VERIFICATION_ENVELOPE,
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
            "preserved assertion evidence is invalid",
        ),
        (
            "evidence_artifact",
            "verification_evidence",
            "verification evidence is invalid",
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
    if list_field == "preserved_assertion_evidence":
        nested_artifact["source_ref"] = f"test-source-ref:sha256:{'0' * 64}"
    else:
        nested_artifact["verification_envelope"] = "fabricated-envelope"

    with pytest.raises(guard.TestCorpusGuardError, match=message):
        _validate_retirements(
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
        _validate_retirements(
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
        _validate_retirements(
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

    count = _validate_retirements(
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

    count = _validate_retirements(
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
        _validate_retirements(
            {replacement},
            set(),
            {"retirements": [_record(retired, replacement)]},
            base_ledger={"retirements": []},
        )


def test_fabricated_verification_envelope_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(
        guard.TestCorpusEvidenceError,
        match="verification receipt is invalid",
    ):
        guard._validate_verification_envelope(
            tmp_path,
            "fabricated-envelope",
            ["tests/test_sample.py::test_replacement"],
            _source_ref,
        )


def test_repository_constructed_passed_envelope_is_not_authoritative(
    tmp_path: Path,
) -> None:
    from scripts.verification.verification_github_transport import (
        encode_github_job_output,
    )
    from tests.test_verification_github_transport import _envelope

    encoded = encode_github_job_output(_envelope(include_run=True))

    with pytest.raises(
        guard.TestCorpusEvidenceError,
        match="lacks independent GitHub attestation",
    ):
        guard._validate_verification_envelope(
            tmp_path,
            encoded,
            ["tests/test_sample.py::test_replacement"],
            _source_ref,
        )


def test_historical_source_ref_fallback_allows_missing_worktree_declaration(
    tmp_path: Path,
) -> None:
    test_ref = "tests/test_sample.py::test_replacement"
    historical = {test_ref: _source_ref(test_ref)}

    assert (
        guard._resolve_assertion_source_ref(tmp_path, test_ref, historical)
        == (historical[test_ref])
    )

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    external = tmp_path / "external.py"
    external.write_text("def test_replacement(): pass\n", encoding="utf-8")
    (tests_dir / "test_sample.py").symlink_to(external)

    with pytest.raises(guard.TestCorpusGuardError, match="file is unsafe"):
        guard._resolve_assertion_source_ref(tmp_path, test_ref, historical)

    (tests_dir / "test_sample.py").unlink()
    (tests_dir / "test_sample.py").write_text(
        "def test_neighbor(): pass\n",
        encoding="utf-8",
    )
    assert (
        guard._resolve_assertion_source_ref(tmp_path, test_ref, historical)
        == historical[test_ref]
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
            b"",
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
    monkeypatch.setattr(guard, "_base_text", lambda _repo, _base, _path: None)

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
    monkeypatch.setattr(guard, "_base_file_paths", lambda _repo, _base: frozenset())
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


def _python_test_ref(source: str) -> str:
    declarations = guard.parse_python_declarations("tests/test_sample.py", source)
    assert len(declarations) == 1
    return declarations[0].ref


def _frontend_test_ref(source: str) -> str:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/sample.test.ts",
        source,
    )
    assert len(declarations) == 1
    return declarations[0].ref


def test_successful_pytest_exit_binds_runtime_posture() -> None:
    aborting = _python_test_ref(
        "import pytest\n"
        "def test_sample():\n"
        "    pytest.exit('complete', returncode=0)\n"
    )
    running = _python_test_ref(
        "import pytest\n"
        "def test_sample():\n"
        "    return None\n"
    )

    assert aborting != running


def test_successful_pytest_exit_expanded_returncode_binds_runtime_posture() -> None:
    aborting = _python_test_ref(
        "import pytest\n"
        "def test_sample():\n"
        "    pytest.exit('complete', **{'returncode': 0})\n"
    )
    running = _python_test_ref(
        "import pytest\n"
        "def test_sample():\n"
        "    return None\n"
    )

    assert aborting != running


def test_named_pytest_exit_returncode_binds_runtime_posture() -> None:
    zero = _python_test_ref(
        "import pytest\n"
        "RETURN_CODE = 0\n"
        "def test_sample():\n"
        "    pytest.exit('complete', returncode=RETURN_CODE)\n"
    )
    nonzero = _python_test_ref(
        "import pytest\n"
        "RETURN_CODE = 1\n"
        "def test_sample():\n"
        "    pytest.exit('complete', returncode=RETURN_CODE)\n"
    )

    assert zero != nonzero


def test_successful_pytest_exit_starred_arguments_bind_runtime_posture() -> None:
    aborting = _python_test_ref(
        "import pytest\n"
        "def test_sample():\n"
        "    pytest.exit(*('complete', 0))\n"
    )
    running = _python_test_ref(
        "import pytest\n"
        "def test_sample():\n"
        "    return None\n"
    )

    assert aborting != running


def test_successful_pytest_exit_starred_arguments_bind_collection_posture() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module-level pytest collection abort",
    ):
        _python_test_ref(
            "import pytest\n"
            "pytest.exit(*('complete', 0))\n"
            "def test_sample():\n"
            "    return None\n"
        )


@pytest.mark.parametrize(
    "body",
    (
        "raise unittest.SkipTest('disabled')",
        "self.skipTest('disabled')",
    ),
)
def test_unittest_body_skip_binds_runtime_posture(body: str) -> None:
    if body.startswith("self"):
        aborting_source = (
            "import unittest\n"
            "class TestSample(unittest.TestCase):\n"
            "    def test_sample(self):\n"
            f"        {body}\n"
        )
        running_source = (
            "import unittest\n"
            "class TestSample(unittest.TestCase):\n"
            "    def test_sample(self):\n"
            "        return None\n"
        )
    else:
        aborting_source = (
            "import unittest\n"
            "def test_sample():\n"
            f"    {body}\n"
        )
        running_source = (
            "import unittest\n"
            "def test_sample():\n"
            "    return None\n"
        )

    assert _python_test_ref(aborting_source) != _python_test_ref(running_source)


def test_unittest_bound_skip_method_binds_runtime_posture() -> None:
    aborting = _python_test_ref(
        "import unittest\n"
        "class TestSample(unittest.TestCase):\n"
        "    def test_sample(self):\n"
        "        skip = self.skipTest\n"
        "        skip('disabled')\n"
    )
    running = _python_test_ref(
        "import unittest\n"
        "class TestSample(unittest.TestCase):\n"
        "    def test_sample(self):\n"
        "        return None\n"
    )

    assert aborting != running


def test_unittest_getattr_bound_skip_method_binds_runtime_posture() -> None:
    aborting = _python_test_ref(
        "import unittest\n"
        "class TestSample(unittest.TestCase):\n"
        "    def test_sample(self):\n"
        "        skip = getattr(self, 'skipTest')\n"
        "        skip('disabled')\n"
    )
    running = _python_test_ref(
        "import unittest\n"
        "class TestSample(unittest.TestCase):\n"
        "    def test_sample(self):\n"
        "        return None\n"
    )

    assert aborting != running


def test_unittest_bound_skip_method_rebinding_clears_runtime_posture() -> None:
    rebound = _python_test_ref(
        "import unittest\n"
        "class TestSample(unittest.TestCase):\n"
        "    def test_sample(self):\n"
        "        skip = self.skipTest\n"
        "        skip = lambda message: None\n"
        "        skip('active')\n"
    )
    running = _python_test_ref(
        "import unittest\n"
        "class TestSample(unittest.TestCase):\n"
        "    def test_sample(self):\n"
        "        return None\n"
    )

    assert rebound == running


def test_conditional_skip_method_rebinding_remains_fail_closed() -> None:
    possibly_aborting = _python_test_ref(
        "import unittest\n"
        "class TestSample(unittest.TestCase):\n"
        "    def test_sample(self, replace):\n"
        "        skip = self.skipTest\n"
        "        if replace:\n"
        "            skip = lambda message: None\n"
        "        skip('maybe disabled')\n"
    )
    running = _python_test_ref(
        "import unittest\n"
        "class TestSample(unittest.TestCase):\n"
        "    def test_sample(self, replace):\n"
        "        return None\n"
    )

    assert possibly_aborting != running


def test_module_lambda_skip_helper_binds_runtime_posture() -> None:
    aborting = _python_test_ref(
        "import pytest\n"
        "abort = lambda: pytest.skip('disabled')\n"
        "def test_sample():\n"
        "    abort()\n"
    )
    running = _python_test_ref(
        "import pytest\n"
        "abort = lambda: None\n"
        "def test_sample():\n"
        "    abort()\n"
    )

    assert aborting != running


def test_runtime_abort_binds_referenced_module_global() -> None:
    disabled = _python_test_ref(
        "import pytest\n"
        "DISABLED = True\n"
        "def test_sample():\n"
        "    if DISABLED:\n"
        "        pytest.skip('disabled')\n"
    )
    enabled = _python_test_ref(
        "import pytest\n"
        "DISABLED = False\n"
        "def test_sample():\n"
        "    if DISABLED:\n"
        "        pytest.skip('disabled')\n"
    )

    assert disabled != enabled


@pytest.mark.parametrize(
    "runtime_skip",
    (
        "import pytest\ndef test_sample():\n"
        "    raise pytest.skip.Exception('disabled')\n",
        "import pytest\ndef test_sample():\n"
        "    Abort = pytest.skip.Exception\n    raise Abort('disabled')\n",
        "import pytest\ndef test_sample():\n"
        "    Abort = getattr(pytest.skip, 'Exception')\n"
        "    raise Abort('disabled')\n",
    ),
)
def test_runtime_abort_binds_pytest_skip_exception(runtime_skip: str) -> None:
    running = _python_test_ref("def test_sample():\n    return None\n")
    skipped = _python_test_ref(runtime_skip)

    assert skipped != running


@pytest.mark.parametrize(
    "runtime_skip",
    (
        "import pytest\ndef test_sample():\n"
        "    vars(pytest)['skip']('disabled')\n",
        "import pytest\ndef test_sample():\n"
        "    namespace = vars(pytest)\n"
        "    namespace['skip']('disabled')\n",
        "import pytest\nfrom builtins import vars as namespace\n"
        "def test_sample():\n"
        "    namespace(pytest).get('skip')('disabled')\n",
    ),
)
def test_runtime_abort_binds_indexed_pytest_callable(runtime_skip: str) -> None:
    running = _python_test_ref("def test_sample():\n    return None\n")
    skipped = _python_test_ref(runtime_skip)

    assert skipped != running


def test_dynamic_indexed_pytest_callable_fails_closed() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic pytest namespace lookup",
    ):
        _python_test_ref(
            "import pytest\ndef test_sample(name):\n"
            "    vars(pytest)[name]('disabled')\n"
        )


def test_collect_ignore_glob_binds_collection_posture() -> None:
    first = _python_test_ref(
        "collect_ignore_glob = ['legacy_*.py']\n"
        "def test_sample():\n"
        "    return None\n"
    )
    second = _python_test_ref(
        "collect_ignore_glob = ['retired_*.py']\n"
        "def test_sample():\n"
        "    return None\n"
    )

    assert first != second


def test_local_vitest_setup_hook_binds_test_posture() -> None:
    skipping = _frontend_test_ref(
        'import { beforeEach, test } from "vitest";\n'
        "beforeEach(context => context.skip());\n"
        'test("sample", () => {});\n'
    )
    running = _frontend_test_ref(
        'import { beforeEach, test } from "vitest";\n'
        "beforeEach(() => {});\n"
        'test("sample", () => {});\n'
    )

    assert skipping != running


def test_vitest_around_each_hook_binds_test_posture() -> None:
    skipping = _frontend_test_ref(
        'import { aroundEach, test } from "vitest";\n'
        "aroundEach(async (_runTest, context) => { context.skip(); });\n"
        'test("sample", () => {});\n'
    )
    running = _frontend_test_ref(
        'import { aroundEach, test } from "vitest";\n'
        "aroundEach(async (runTest) => { await runTest(); });\n"
        'test("sample", () => {});\n'
    )

    assert skipping != running


def test_vitest_extended_api_binds_auto_fixture_posture() -> None:
    skipping = _frontend_test_ref(
        'import { test } from "vitest";\n'
        "const extended = test.extend({\n"
        "  fixture: [async ({ skip }, use) => { skip(); await use('x'); }, "
        "{ auto: true }],\n"
        "});\n"
        'extended("sample", () => {});\n'
    )
    running = _frontend_test_ref(
        'import { test } from "vitest";\n'
        "const extended = test.extend({\n"
        "  fixture: [async ({}, use) => { await use('x'); }, { auto: true }],\n"
        "});\n"
        'extended("sample", () => {});\n'
    )

    assert skipping != running

    disabled = _frontend_test_ref(
        'import { test } from "vitest";\n'
        "const disabled = true;\n"
        "const extended = test.extend({\n"
        "  fixture: [async ({ skip }, use) => { if (disabled) skip(); "
        "await use('x'); }, { auto: true }],\n"
        "});\n"
        'extended("sample", () => {});\n'
    )
    enabled = _frontend_test_ref(
        'import { test } from "vitest";\n'
        "const disabled = false;\n"
        "const extended = test.extend({\n"
        "  fixture: [async ({ skip }, use) => { if (disabled) skip(); "
        "await use('x'); }, { auto: true }],\n"
        "});\n"
        'extended("sample", () => {});\n'
    )

    assert disabled != enabled


def test_aliased_local_vitest_setup_hook_binds_test_posture() -> None:
    skipping = _frontend_test_ref(
        'import { beforeEach, test } from "vitest";\n'
        "const hook = beforeEach;\n"
        "hook(context => context.skip());\n"
        'test("sample", () => {});\n'
    )
    running = _frontend_test_ref(
        'import { beforeEach, test } from "vitest";\n'
        "const hook = beforeEach;\n"
        "hook(() => {});\n"
        'test("sample", () => {});\n'
    )

    assert skipping != running


def test_semicolonless_aliased_vitest_setup_hook_binds_test_posture() -> None:
    skipping = _frontend_test_ref(
        'import { beforeEach, test } from "vitest"\n'
        "const hook = beforeEach\n"
        "hook(context => context.skip())\n"
        'test("sample", () => {})\n'
    )
    running = _frontend_test_ref(
        'import { beforeEach, test } from "vitest"\n'
        "const hook = beforeEach\n"
        "hook(() => {})\n"
        'test("sample", () => {})\n'
    )

    assert skipping != running


def test_dormant_vitest_setup_hook_does_not_bind_test_posture() -> None:
    skipping = _frontend_test_ref(
        'import { beforeEach, test } from "vitest";\n'
        "function dormant() { beforeEach(context => context.skip()); }\n"
        'test("sample", () => {});\n'
    )
    running = _frontend_test_ref(
        'import { beforeEach, test } from "vitest";\n'
        "function dormant() { beforeEach(() => {}); }\n"
        'test("sample", () => {});\n'
    )

    assert skipping == running


def test_vitest_setup_hook_binds_callback_dependencies() -> None:
    skipping = _frontend_test_ref(
        'import { beforeEach, test } from "vitest";\n'
        "const disabled = true;\n"
        "beforeEach(context => { if (disabled) context.skip(); });\n"
        'test("sample", () => {});\n'
    )
    running = _frontend_test_ref(
        'import { beforeEach, test } from "vitest";\n'
        "const disabled = false;\n"
        "beforeEach(context => { if (disabled) context.skip(); });\n"
        'test("sample", () => {});\n'
    )

    assert skipping != running


def test_vitest_setup_hook_is_scoped_to_its_enclosing_suite() -> None:
    skipping_source = (
        'import { beforeEach, describe, test } from "vitest";\n'
        'describe("nested", () => {\n'
        "  beforeEach(context => context.skip());\n"
        '  test("inside", () => {});\n'
        "});\n"
        'test("outside", () => {});\n'
    )
    running_source = skipping_source.replace(
        "beforeEach(context => context.skip())",
        "beforeEach(() => {})",
    )
    skipping = guard.parse_frontend_declarations(
        "apps/control-center/src/sample.test.ts",
        skipping_source,
    )
    running = guard.parse_frontend_declarations(
        "apps/control-center/src/sample.test.ts",
        running_source,
    )

    assert len(skipping) == len(running) == 2
    assert skipping[0].ref != running[0].ref
    assert skipping[1].ref == running[1].ref


def test_shadowed_local_vitest_setup_hook_alias_fails_closed() -> None:
    source = (
        'import { beforeEach, test } from "vitest";\n'
        "const hook = beforeEach;\n"
        "function helper() { const hook = value => value; hook('active'); }\n"
        "helper();\n"
        'test("sample", () => {});\n'
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="setup hook alias shadowing",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/sample.test.ts",
            source,
        )


def _anyio_security_dependency_pair() -> tuple[dict[str, str], dict[str, str]]:
    prior = {
        "pyproject.toml": (
            '[project]\ndependencies = ["starlette>=1.3.1,<2.0.0"]\n'
            '[project.optional-dependencies]\ndev = ["pytest>=7,<10"]\n'
        ),
        "uv.lock": '[[package]]\nname = "anyio"\nversion = "4.13.0"\n',
    }
    current = {
        "pyproject.toml": prior["pyproject.toml"].replace(
            'dependencies = [', 'dependencies = ["anyio>=4.14.2,<5.0.0", '
        ),
        "uv.lock": prior["uv.lock"].replace("4.13.0", "4.14.2"),
    }
    return prior, current


def _bind_anyio_security_dependency_pair(
    monkeypatch: pytest.MonkeyPatch,
    prior: dict[str, str],
    current: dict[str, str],
) -> None:
    monkeypatch.setattr(
        guard,
        "ANYIO_SECURITY_DEPENDENCY_APPROVED_SHA256_BY_PATH",
        {
            path: (
                hashlib.sha256(prior[path].encode()).hexdigest(),
                hashlib.sha256(current[path].encode()).hexdigest(),
            )
            for path in prior
        },
    )


@pytest.mark.parametrize("side", ("prior", "current"))
@pytest.mark.parametrize(
    "mutation",
    (
        "project_byte",
        "lock_byte",
        "missing_project",
        "missing_lock",
        "extra_path",
        "reversed_project",
    ),
)
def test_anyio_security_dependency_alignment_rejects_pair_substitution(
    monkeypatch: pytest.MonkeyPatch, side: str, mutation: str
) -> None:
    prior, current = _anyio_security_dependency_pair()
    _bind_anyio_security_dependency_pair(monkeypatch, prior, current)
    assert guard._safe_anyio_security_dependency_alignment_paths(
        prior_by_path=prior, current_by_path=current
    ) == {"pyproject.toml", "uv.lock"}

    target = prior if side == "prior" else current
    if mutation == "project_byte":
        target["pyproject.toml"] += " "
    elif mutation == "lock_byte":
        target["uv.lock"] += " "
    elif mutation == "missing_project":
        del target["pyproject.toml"]
    elif mutation == "missing_lock":
        del target["uv.lock"]
    elif mutation == "extra_path":
        target["pytest.ini"] = "[pytest]\n"
    else:
        target["pyproject.toml"] = (current if side == "prior" else prior)[
            "pyproject.toml"
        ]
    assert not guard._safe_anyio_security_dependency_alignment_paths(
        prior_by_path=prior, current_by_path=current
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "none",
        "project_byte",
        "lock_byte",
        "wrong_base",
        "different_patch",
        "unrelated_lock_record",
        "lock_only",
        "missing_project",
        "missing_lock",
        "pytest_config",
        "pytest_plugin",
        "dev_dependency",
    ),
)
def test_anyio_security_dependency_alignment_keeps_collection_boundary_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    prior, current = _anyio_security_dependency_pair()
    _bind_anyio_security_dependency_pair(monkeypatch, prior, current)
    changed_paths = set(current)
    if mutation == "project_byte":
        current["pyproject.toml"] += " "
    elif mutation == "lock_byte":
        current["uv.lock"] += " "
    elif mutation == "wrong_base":
        prior["uv.lock"] = prior["uv.lock"].replace("4.13.0", "4.12.1")
    elif mutation == "different_patch":
        current["uv.lock"] = current["uv.lock"].replace("4.14.2", "4.15.0")
    elif mutation == "unrelated_lock_record":
        current["uv.lock"] += '[[package]]\nname = "other"\nversion = "1.0"\n'
    elif mutation == "lock_only":
        changed_paths.remove("pyproject.toml")
        current["pyproject.toml"] = prior["pyproject.toml"]
    elif mutation == "missing_project":
        del current["pyproject.toml"]
    elif mutation == "missing_lock":
        del current["uv.lock"]
    elif mutation == "pytest_config":
        changed_paths.add("pytest.ini")
        current["pytest.ini"] = "[pytest]\naddopts = --ignore=tests/security\n"
    elif mutation == "pytest_plugin":
        current["pyproject.toml"] += (
            '[project.entry-points.pytest11]\nother = "other.plugin"\n'
        )
    elif mutation == "dev_dependency":
        current["pyproject.toml"] = current["pyproject.toml"].replace(
            '"pytest>=7,<10"', '"pytest>=8,<10"'
        )
    for path, value in current.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)
    outputs = iter(
        (("\0".join(sorted(changed_paths)) + "\0").encode(), b"", b"", b"")
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(guard, "_base_text", lambda _repo, _base, path: prior.get(path))
    if mutation == "none":
        assert guard._changed_test_paths(tmp_path, "a" * 40) == ()
    else:
        with pytest.raises(
            guard.TestCorpusGuardError,
            match="changed pytest (dependency lock|collection configuration)",
        ):
            guard._changed_test_paths(tmp_path, "a" * 40)
