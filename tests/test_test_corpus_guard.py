import subprocess
from pathlib import Path

import pytest

from scripts.verification import test_corpus_guard as guard


VERIFICATION_ENVELOPE = "github-verification-envelope:test-fixture"


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


def test_python_inventory_matches_inherited_pytest_class_collection() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        """
class Base:
    def test_inherited(self):
        assert True

class TestChild(Base):
    pass
""",
    )

    assert [item.ref for item in declarations] == [
        "tests/test_sample.py::TestChild::test_inherited",
    ]


def test_python_inventory_binds_parameterized_decorator_changes() -> None:
    path = "tests/test_sample.py"
    before = guard.parse_python_declarations(
        path,
        """
import pytest

@pytest.mark.parametrize("value", ["one", "two"])
def test_case(value):
    assert value
""",
    )
    after = guard.parse_python_declarations(
        path,
        """
import pytest

@pytest.mark.parametrize("value", ["one"])
def test_case(value):
    assert value
""",
    )

    assert len(before) == len(after) == 1
    assert before[0].ref.startswith(f"{path}::test_case::parametrize-sha256:")
    assert after[0].ref.startswith(f"{path}::test_case::parametrize-sha256:")
    assert before[0].ref != after[0].ref


def test_python_inventory_binds_module_parameter_data_changes() -> None:
    path = "tests/test_sample.py"
    template = """
import pytest

CASES = {cases}

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
"""
    before = guard.parse_python_declarations(
        path,
        template.format(cases='["one", "two"]'),
    )
    after = guard.parse_python_declarations(
        path,
        template.format(cases='["one"]'),
    )

    assert before[0].ref != after[0].ref


def test_python_source_ref_hashes_only_the_replacement_declaration() -> None:
    test_ref = "tests/test_sample.py::test_replacement"
    before = """
import first_dependency

def test_replacement():
    assert True

def test_neighbor():
    assert True
"""
    unrelated_change = """
import second_dependency

def test_replacement():
    assert True

def test_neighbor():
    assert False
"""
    replacement_change = unrelated_change.replace("assert True", "assert 1 == 1", 1)

    source_ref = guard._source_ref_from_text(test_ref, before)
    assert guard._source_ref_from_text(test_ref, unrelated_change) == source_ref
    assert guard._source_ref_from_text(test_ref, replacement_change) != source_ref


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


@pytest.mark.parametrize(
    "shadowing_source",
    [
        'const test = helper; test("not collected", () => {});',
        'function it() {} it("not collected", () => {});',
        'const { test } = helper; test("not collected", () => {});',
        'const helper = (test) => test("not collected", () => {});',
        'import { test } from "local-helper"; test("not collected", () => {});',
    ],
)
def test_frontend_inventory_rejects_shadowed_runner_names(
    shadowing_source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="frontend test API name is shadowed",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            shadowing_source,
        )


def test_frontend_inventory_allows_nonshadowing_property_destructure() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.ts",
        """
import { it } from "vitest";
const { test: helperTest } = helper;
it("collected", () => helperTest());
""",
    )

    assert [declaration.ref for declaration in declarations] == [
        "apps/control-center/src/example.test.ts::collected"
    ]


def test_frontend_source_ref_hashes_only_the_replacement_declaration() -> None:
    path = "apps/control-center/src/example.test.ts"
    test_ref = f"{path}::replacement"
    before = """
import { it } from "vitest";
const unrelated = "first";
it("replacement", () => { expect(true).toBe(true); });
it("neighbor", () => { expect(true).toBe(true); });
"""
    unrelated_change = """
import { it } from "vitest";
const unrelated = "second";
it("replacement", () => { expect(true).toBe(true); });
it("neighbor", () => { expect(false).toBe(true); });
"""
    replacement_change = unrelated_change.replace(
        "expect(true).toBe(true)",
        "expect(1).toBe(1)",
        1,
    )

    source_ref = guard._source_ref_from_text(test_ref, before)
    assert guard._source_ref_from_text(test_ref, unrelated_change) == source_ref
    assert guard._source_ref_from_text(test_ref, replacement_change) != source_ref


def test_frontend_inventory_includes_parameterized_test_titles() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
it.each([
  ["one", { nested: call("value)") }],
  ["two", { nested: true }],
])("renders %s safely", () => {});
test.concurrent.each(cases)("rejects %s", () => {});
test.for(cases)("binds one case object", () => {});
test.each`
  name | allowed
  ${"x"} | ${false}
`("blocks $name", () => {});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.tsx::renders %s safely",
        "apps/control-center/src/example.test.tsx::rejects %s",
        "apps/control-center/src/example.test.tsx::binds one case object",
        "apps/control-center/src/example.test.tsx::blocks $name",
    ]


def test_frontend_inventory_includes_supported_modifiers() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
it.skipIf(process.platform === "win32")("skips on Windows", () => {});
test.runIf(featureEnabled)("runs when enabled", () => {});
it.sequential("runs in sequence", () => {});
test.fail("records an expected failure", () => {});
test.fixme("records an unavailable case", () => {});
test("declared test", async () => {
  test.fail(runtimeCondition, "runtime annotation");
  test.fixme(runtimeCondition, "runtime annotation");
});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.tsx::runs in sequence",
        "apps/control-center/src/example.test.tsx::records an expected failure",
        "apps/control-center/src/example.test.tsx::records an unavailable case",
        "apps/control-center/src/example.test.tsx::declared test",
        "apps/control-center/src/example.test.tsx::skips on Windows",
        "apps/control-center/src/example.test.tsx::runs when enabled",
    ]


def test_frontend_inventory_masks_nested_template_interpolations() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
const label = `prefix ${fn(`inner ${value("nested")}`)} suffix`;
const decoy = `test("not a declaration", () => {})`;
it("real test", () => {});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.tsx::real test",
    ]


def test_frontend_inventory_handles_comments_and_regex_literals() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.spec.ts",
        r"""
const patterns = [/path\//]; it /* lexical trivia */ ("after comment", () => {});
it.each([/path\//])("matches escaped slash", () => {});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.spec.ts::after comment",
        "apps/control-center/src/example.spec.ts::matches escaped slash",
    ]


def test_frontend_inventory_handles_regex_after_division_operator() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.spec.ts",
        r"""
const matched = value / /path\//.test(input);
const ratio = /path/ / divisor;
test("covered after division", () => matched);
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.spec.ts::covered after division",
    ]


@pytest.mark.parametrize(
    "path",
    [
        "apps/control-center/src/example.test.js",
        "apps/control-center/src/example.spec.jsx",
        "apps/control-center/src/example.test.ts",
        "apps/control-center/src/example.spec.tsx",
        "apps/control-center/src/example.test.cjs",
        "apps/control-center/src/example.spec.cjsx",
        "apps/control-center/src/example.test.mjs",
        "apps/control-center/src/example.spec.mjsx",
        "apps/control-center/src/example.test.cts",
        "apps/control-center/src/example.spec.ctsx",
        "apps/control-center/src/example.test.mts",
        "apps/control-center/src/example.spec.mtsx",
    ],
)
def test_vitest_default_extensions_are_guarded(path: str) -> None:
    assert guard._is_test_path(path)


def test_discovery_covers_every_vitest_default_extension(tmp_path: Path) -> None:
    source_root = tmp_path / "apps/control-center/src"
    source_root.mkdir(parents=True)
    expected: set[str] = set()
    for index, extension in enumerate(guard.FRONTEND_TEST_EXTENSIONS):
        kind = "test" if index % 2 == 0 else "spec"
        relative = f"apps/control-center/src/example-{index}.{kind}.{extension}"
        (tmp_path / relative).write_text('test("covered", () => {});\n')
        expected.add(relative)

    assert set(guard.discover_test_files(tmp_path)) == expected


def test_frontend_inventory_tracks_import_aliases_and_extended_apis() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.spec.ts",
        """
import { test as pw } from "@playwright/test";
const fixtureTest = pw.extend({ account: async ({}, use) => use("safe") });
pw("aliased test", () => {});
fixtureTest("extended test", () => {});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.spec.ts::aliased test",
        "apps/control-center/src/example.spec.ts::extended test",
    ]


def test_frontend_inventory_fails_closed_for_untracked_extended_api() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="extended test API cannot be inventoried safely",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.spec.ts",
            "const fixtureTest = test.extend<Fixtures>({});",
        )


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
        _validate_retirements(
            {"tests/test_sample.py::test_replacement"},
            {"tests/test_sample.py::test_removed"},
            {"retirements": []},
        )


def test_retirement_requires_present_replacement_and_evidence() -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    count = _validate_retirements(
        {replacement},
        {retired},
        {"retirements": [_record(retired, replacement)]},
    )

    assert count == 1


def test_retirement_with_missing_replacement_fails_closed() -> None:
    retired = "tests/test_sample.py::test_removed"
    with pytest.raises(guard.TestCorpusGuardError, match="missing replacements"):
        _validate_retirements(
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
        _validate_retirements(
            {replacement},
            {retired},
            {"retirements": [record]},
        )


@pytest.mark.parametrize(
    "unsafe_reason",
    (
        "Retirement evidence contains "
        + "/Us"
        + "ers/example/private/source material.",
        "Retirement evidence includes username from a local operator record.",
        "Retirement evidence includes api_"
        + "key="
        + "abcdefghijklmnop credential data.",
        "Retirement evidence includes a raw prompt from a prior run.",
    ),
)
def test_retirement_reason_rejects_sensitive_durable_content(
    unsafe_reason: str,
) -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    record = _record(retired, replacement)
    record["reason"] = unsafe_reason

    with pytest.raises(guard.TestCorpusGuardError, match="reason is too weak"):
        _validate_retirements(
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
        _validate_retirements(
            {replacement},
            {retired},
            {"retirements": [record]},
        )


def test_nested_retirement_evidence_is_content_bound() -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    record = _record(retired, replacement)
    equivalence = record["assertion_equivalence_artifact"]
    assert isinstance(equivalence, dict)
    nested_records = equivalence["preserved_assertion_evidence"]
    assert isinstance(nested_records, list)
    nested = nested_records[0]
    assert isinstance(nested, dict)
    artifact = nested["artifact"]
    assert isinstance(artifact, dict)
    artifact["source_ref"] = f"test-source-ref:sha256:{'0' * 64}"
    record["assertion_equivalence_ref"] = guard.retirement_artifact_ref(
        "assertion-equivalence-ref", equivalence
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="preserved assertion evidence is invalid",
    ):
        _validate_retirements(
            {replacement},
            {retired},
            {"retirements": [record]},
        )


def test_retired_ref_must_use_a_supported_safe_test_path() -> None:
    replacement = "tests/test_sample.py::test_replacement"
    retired = "docs/not_a_test.py::test_removed"

    with pytest.raises(guard.TestCorpusGuardError, match="retired test ref is invalid"):
        _validate_retirements(
            {replacement},
            {retired},
            {"retirements": [_record(retired, replacement)]},
        )


def test_retired_ref_requires_a_nonempty_declaration() -> None:
    replacement = "tests/test_sample.py::test_replacement"
    retired = "tests/test_sample.py::"

    with pytest.raises(guard.TestCorpusGuardError, match="retired test ref is invalid"):
        _validate_retirements(
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
        _validate_retirements(
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
        "apps/control-center/src/example.spec.ts",
        "apps/control-center/src/example.spec.tsx",
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
            "a" * 40,
            "HEAD",
            "--",
            "tests",
            "apps",
        ],
        [
            "diff",
            "--cached",
            "--name-only",
            "--no-renames",
            "-z",
            "--",
            "tests",
            "apps",
        ],
        [
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            "--",
            "tests",
            "apps",
        ],
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "tests",
            "apps",
        ],
    ]
