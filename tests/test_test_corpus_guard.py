import subprocess
from pathlib import Path

import pytest

from scripts.verification import test_corpus_guard as guard


def _record(
    retired_ref: str,
    replacement_ref: str,
) -> dict[str, object]:
    return {
        "retired_ref": retired_ref,
        "replacement_refs": [replacement_ref],
        "reason": "The replacement preserves the same exact defect class.",
        "assertion_equivalence_ref": "assertion-equivalence-ref:sha256:" + ("a" * 64),
        "evidence_ref": "test-corpus-evidence-ref:sha256:" + ("b" * 64),
    }


def test_python_inventory_includes_module_async_and_class_tests() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        """
def test_sync():
    assert True

async def test_async():
    assert True

class TestGroup:
    def test_method(self):
        assert True

def helper():
    pass
""",
    )

    assert [item.ref for item in declarations] == [
        "tests/test_sample.py::test_sync",
        "tests/test_sample.py::test_async",
        "tests/test_sample.py::TestGroup::test_method",
    ]


def test_frontend_inventory_normalizes_titles_and_disambiguates_duplicates() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
test("renders   a panel", () => {});
it.only('renders a panel', () => {});
test.skip(`blocks mutation`, () => {});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.tsx::renders a panel",
        "apps/control-center/src/example.test.tsx::renders a panel#2",
        "apps/control-center/src/example.test.tsx::blocks mutation",
    ]


def test_frontend_inventory_includes_parameterized_test_titles() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
it.each([
  ["one", { nested: call("value)") }],
  ["two", { nested: true }],
])("renders %s safely", () => {});
test.concurrent.each(cases)("rejects %s", () => {});
test.each`
  name | allowed
  ${"x"} | ${false}
`("blocks $name", () => {});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.tsx::renders %s safely",
        "apps/control-center/src/example.test.tsx::rejects %s",
        "apps/control-center/src/example.test.tsx::blocks $name",
    ]


def test_parameterized_frontend_inventory_rejects_missing_title() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="parameterized test title is missing",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            "it.each(cases);",
        )


def test_frontend_inventory_ignores_test_syntax_in_comments_and_strings() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
// it("commented out", () => {});
/* test.each(cases)("also commented out", () => {}); */
const sample = 'it("string payload", () => {})';
it("real declaration", () => {});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.tsx::real declaration",
    ]


def test_frontend_inventory_handles_escaped_title_quotes() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        r"""
it("renders \"quoted\" text", () => {});
test('rejects \'quoted\' input', () => {});
""",
    )

    assert [item.ref for item in declarations] == [
        r"apps/control-center/src/example.test.tsx::renders \"quoted\" text",
        r"apps/control-center/src/example.test.tsx::rejects \'quoted\' input",
    ]


def test_frontend_inventory_rejects_dynamic_direct_test_titles() -> None:
    with pytest.raises(guard.TestCorpusGuardError, match="test title is invalid"):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            "it(dynamicTitle, () => {});",
        )


def test_frontend_inventory_ignores_playwright_conditional_skip_annotations() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/tests/example.spec.ts",
        """
test("declared test", async ({ page }) => {
  test.skip(testInfo.project.name !== "desktop", "desktop only");
});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/tests/example.spec.ts::declared test",
    ]


def test_removed_test_without_evidence_fails_closed() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="lack retirement/replacement evidence",
    ):
        guard.validate_retirements(
            {"tests/test_sample.py::test_replacement"},
            {"tests/test_sample.py::test_removed"},
            {"retirements": []},
        )


def test_retirement_requires_present_replacement_and_evidence() -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    count = guard.validate_retirements(
        {replacement},
        {retired},
        {"retirements": [_record(retired, replacement)]},
    )

    assert count == 1


def test_retirement_with_missing_replacement_fails_closed() -> None:
    retired = "tests/test_sample.py::test_removed"
    with pytest.raises(guard.TestCorpusGuardError, match="missing replacements"):
        guard.validate_retirements(
            set(),
            {retired},
            {"retirements": [_record(retired, "tests/test_sample.py::test_missing")]},
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        (
            "assertion_equivalence_ref",
            "assertion-equivalence-ref:not-content-bound",
            "equivalence ref is invalid",
        ),
        (
            "evidence_ref",
            "test-corpus-evidence-ref:not-content-bound",
            "evidence ref is invalid",
        ),
        (
            "reason",
            "A substantive reason that includes\nunbounded lines.",
            "reason is too weak",
        ),
    ),
)
def test_retirement_metadata_must_be_bounded_and_content_bound(
    field: str,
    value: str,
    message: str,
) -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    record = _record(retired, replacement)
    record[field] = value

    with pytest.raises(guard.TestCorpusGuardError, match=message):
        guard.validate_retirements(
            {replacement},
            {retired},
            {"retirements": [record]},
        )


def test_retirement_records_reject_unknown_durable_fields() -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    record = _record(retired, replacement)
    record["raw_output"] = "not allowed"

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="record fields are invalid",
    ):
        guard.validate_retirements(
            {replacement},
            {retired},
            {"retirements": [record]},
        )


def test_retired_ref_must_use_a_supported_safe_test_path() -> None:
    replacement = "tests/test_sample.py::test_replacement"
    retired = "docs/not_a_test.py::test_removed"

    with pytest.raises(guard.TestCorpusGuardError, match="retired test ref is invalid"):
        guard.validate_retirements(
            {replacement},
            {retired},
            {"retirements": [_record(retired, replacement)]},
        )


def test_retired_ref_requires_a_nonempty_declaration() -> None:
    replacement = "tests/test_sample.py::test_replacement"
    retired = "tests/test_sample.py::"

    with pytest.raises(guard.TestCorpusGuardError, match="retired test ref is invalid"):
        guard.validate_retirements(
            {replacement},
            {retired},
            {"retirements": [_record(retired, replacement)]},
        )


def test_retirement_ledger_rejects_symlinks_and_oversized_files(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / guard.RETIREMENT_LEDGER
    ledger.parent.mkdir(parents=True)
    external = tmp_path / "external.json"
    external.write_text(
        '{"schema_version":"uaa.test_corpus_retirements.v1","retirements":[]}',
        encoding="utf-8",
    )
    ledger.symlink_to(external)

    with pytest.raises(guard.TestCorpusGuardError, match="ledger is unsafe"):
        guard._load_ledger(tmp_path)

    ledger.unlink()
    ledger.write_bytes(b" " * (guard.MAX_RETIREMENT_LEDGER_BYTES + 1))
    with pytest.raises(guard.TestCorpusGuardError, match="ledger is unsafe"):
        guard._load_ledger(tmp_path)


def test_worktree_inventory_reader_rejects_symlinks_and_hardlinks(
    tmp_path: Path,
) -> None:
    external = tmp_path / "external.py"
    external.write_text("def test_external(): pass\n", encoding="utf-8")
    symlink = tmp_path / "test_symlink.py"
    symlink.symlink_to(external)

    with pytest.raises(guard.TestCorpusGuardError, match="file is unsafe"):
        guard._read_worktree_text(tmp_path, symlink.name)

    hardlink = tmp_path / "test_hardlink.py"
    hardlink.hardlink_to(external)
    with pytest.raises(guard.TestCorpusGuardError, match="file is unsafe"):
        guard._read_worktree_text(tmp_path, hardlink.name)


def test_active_test_cannot_be_marked_retired() -> None:
    retired = "tests/test_sample.py::test_still_active"
    with pytest.raises(guard.TestCorpusGuardError, match="still active"):
        guard.validate_retirements(
            {retired},
            set(),
            {"retirements": [_record(retired, retired)]},
        )


def test_inventory_fingerprint_is_order_sensitive_and_content_free() -> None:
    first = (
        guard.TestDeclaration("tests/test_a.py::test_a", "python_test"),
        guard.TestDeclaration("tests/test_b.py::test_b", "python_test"),
    )
    second = tuple(reversed(first))

    assert guard.inventory_fingerprint(first) != guard.inventory_fingerprint(second)
    assert guard.inventory_fingerprint(first).startswith(
        "test-corpus-inventory-ref:sha256:"
    )


def test_repository_inventory_is_nonempty_and_deterministic() -> None:
    root = Path(__file__).resolve().parents[1]
    first = guard.inventory_worktree(root)
    second = guard.inventory_worktree(root)

    assert first == second
    assert len(first) > 1000
    assert {item.kind for item in first} == {"python_test", "frontend_test"}


def test_malformed_requested_base_fails_closed() -> None:
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(guard.TestCorpusGuardError, match="base SHA is malformed"):
        guard.verify_test_corpus_guard(root, base_sha="not-a-sha")


def test_ci_without_canonical_base_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=b"",
            stderr=b"",
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="canonical CI comparison base is missing",
    ):
        guard._resolve_base_sha(Path("."), None)


def test_malformed_canonical_ci_base_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"not-a-sha\n",
            stderr=b"",
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="canonical CI comparison base is malformed",
    ):
        guard._resolve_base_sha(Path("."), None)


@pytest.mark.parametrize(
    "path",
    (
        "tests/example_test.py",
        "tests/test_example.py",
        "apps/control-center/src/example.test.ts",
        "apps/control-center/src/example.test.tsx",
        "apps/control-center/tests/example.spec.ts",
        "apps/control-center/tests/example.spec.tsx",
    ),
)
def test_supported_test_paths_cover_collector_suffixes(path: str) -> None:
    assert guard._is_test_path(path)


@pytest.mark.parametrize(
    "path",
    (
        "/tests/test_escape.py",
        "tests/../test_escape.py",
        "tests\\test_escape.py",
        "tests/test:escape.py",
        "tests/test_escape.py\nother",
    ),
)
def test_unsafe_changed_test_paths_fail_closed(path: str) -> None:
    with pytest.raises(guard.TestCorpusGuardError, match="path is unsafe"):
        guard._validate_test_path(path)


def test_changed_test_paths_reject_non_utf8_git_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"tests/test_bad_" + bytes([0xFF]) + b".py\0",
            stderr=b"",
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="paths are malformed",
    ):
        guard._changed_test_paths(Path("."), "a" * 40)


def test_changed_test_paths_disable_rename_collapsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_args: list[list[str]] = []

    def completed(
        _repo: Path,
        args: list[str],
    ) -> subprocess.CompletedProcess[bytes]:
        captured_args.append(args)
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"tests/test_old.py\0tests/test_new.py\0",
            stderr=b"",
        )

    monkeypatch.setattr(guard, "_run_git", completed)

    assert guard._changed_test_paths(Path("."), "a" * 40) == (
        "tests/test_new.py",
        "tests/test_old.py",
    )
    assert captured_args == [
        [
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            "a" * 40 + "...HEAD",
            "--",
            "tests",
            "apps",
        ]
    ]
