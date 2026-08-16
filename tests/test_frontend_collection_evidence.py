from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.verification import frontend_collection_evidence as evidence


ROOT = Path(__file__).resolve().parents[1]
VITEST_FILE = ROOT / "apps/control-center/src/icons/iconRegistry.test.ts"
PLAYWRIGHT_ROOT = ROOT / "apps/control-center"
PLAYWRIGHT_FILE = "tests/visual/control-center.visual.spec.ts"


def _private_directory(tmp_path: Path) -> Path:
    directory = tmp_path / "raw"
    directory.mkdir(mode=0o700, parents=True)
    directory.chmod(0o700)
    return directory


def _write_raw(directory: Path, payload: object, name: str = "result.json") -> Path:
    path = directory / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(0o600)
    return path


def _vitest_assertion(
    *,
    name: str = "renders safe status",
    status: str = "passed",
) -> dict[str, object]:
    return {
        "ancestorTitles": ["safe suite"],
        "duration": 1,
        "failureMessages": ["raw failure must disappear"] if status == "failed" else [],
        "fullName": f"safe suite {name}",
        "meta": {},
        "status": status,
        "tags": [],
        "title": name,
    }


def _vitest_payload(
    assertions: list[dict[str, object]] | None = None,
    *,
    suite_name: str | None = None,
    suite_counts: tuple[int, int, int] | None = None,
    file_status: str | None = None,
    coverage_map: object = ...,
) -> dict[str, object]:
    items = assertions if assertions is not None else [_vitest_assertion()]
    status_counts = {
        "passed": sum(item["status"] == "passed" for item in items),
        "failed": sum(item["status"] == "failed" for item in items),
        "pending": sum(item["status"] in {"pending", "skipped"} for item in items),
        "todo": sum(item["status"] == "todo" for item in items),
    }
    if suite_counts is None:
        suite_counts = (
            0 if status_counts["failed"] else 2,
            2 if status_counts["failed"] else 0,
            0,
        )
    passed_suites, failed_suites, pending_suites = suite_counts
    resolved_file_status = file_status or (
        "failed" if failed_suites or status_counts["failed"] else "passed"
    )
    payload: dict[str, object] = {
        "numFailedTestSuites": failed_suites,
        "numFailedTests": status_counts["failed"],
        "numPassedTestSuites": passed_suites,
        "numPassedTests": status_counts["passed"],
        "numPendingTestSuites": pending_suites,
        "numPendingTests": status_counts["pending"],
        "numTodoTests": status_counts["todo"],
        "numTotalTestSuites": sum(suite_counts),
        "numTotalTests": len(items),
        "snapshot": {},
        "startTime": 1_700_000_000_000,
        "success": failed_suites == 0 and status_counts["failed"] == 0,
        "testResults": [
            {
                "assertionResults": items,
                "endTime": 1_700_000_000_001,
                "message": "raw suite output must disappear",
                "name": suite_name or str(VITEST_FILE),
                "startTime": 1_700_000_000_000,
                "status": resolved_file_status,
            }
        ],
    }
    if coverage_map is not ...:
        payload["coverageMap"] = coverage_map
    return payload


def _playwright_attempt(status: str, retry: int) -> dict[str, object]:
    return {
        "annotations": [],
        "attachments": [],
        "duration": 10,
        "error": {"message": "raw error must disappear"} if status == "failed" else None,
        "errors": [],
        "parallelIndex": 0,
        "retry": retry,
        "startTime": "2026-01-01T00:00:00.000Z",
        "status": status,
        "stderr": [{"text": "raw stderr must disappear"}],
        "stdout": [{"text": "raw stdout must disappear"}],
        "workerIndex": 0,
    }


def _playwright_test(
    *,
    outcome: str = "expected",
    attempts: list[dict[str, object]] | None = None,
    project_id: str = "desktop",
) -> dict[str, object]:
    return {
        "annotations": [],
        "expectedStatus": "passed",
        "projectId": project_id,
        "projectName": "desktop",
        "results": attempts or [_playwright_attempt("passed", 0)],
        "status": outcome,
        "timeout": 30_000,
    }


def _playwright_payload(
    tests: list[dict[str, object]] | None = None,
    *,
    file_name: str = PLAYWRIGHT_FILE,
) -> dict[str, object]:
    items = tests or [_playwright_test()]
    outcomes = {
        name: sum(item["status"] == name for item in items)
        for name in ("expected", "flaky", "skipped", "unexpected")
    }
    return {
        "config": {
            "rootDir": str(PLAYWRIGHT_ROOT),
            "projects": [],
        },
        "errors": [],
        "stats": {
            "duration": 12,
            "expected": outcomes["expected"],
            "flaky": outcomes["flaky"],
            "skipped": outcomes["skipped"],
            "startTime": "2026-01-01T00:00:00.000Z",
            "unexpected": outcomes["unexpected"],
        },
        "suites": [
            {
                "column": 0,
                "file": file_name,
                "line": 0,
                "specs": [
                    {
                        "column": 1,
                        "file": file_name,
                        "id": "safe-spec-id",
                        "line": 1,
                        "ok": all(item["status"] != "unexpected" for item in items),
                        "tags": [],
                        "tests": items,
                        "title": "raw title must disappear",
                    }
                ],
                "title": "raw suite title must disappear",
            }
        ],
    }


def test_vitest_result_is_content_free_counted_and_consumed(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    raw = _write_raw(
        directory,
        _vitest_payload(
            [
                _vitest_assertion(name="passes", status="passed"),
                _vitest_assertion(name="is skipped", status="skipped"),
                _vitest_assertion(name="is todo", status="todo"),
            ]
        ),
    )

    result = evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert not raw.exists()
    assert result == {
        **result,
        "collected_test_count": 3,
        "failed_test_count": 0,
        "passed_test_count": 1,
        "result_status": "passed",
        "runner_ref": "runner-ref:frontend:vitest",
        "skipped_test_count": 1,
        "todo_test_count": 1,
    }
    rendered = json.dumps(result)
    assert result["collection_digest_ref"].startswith("sha256:")
    assert str(ROOT) not in rendered
    assert "passes" not in rendered
    assert "raw" not in rendered


def test_safe_frontend_aggregate_is_content_bound_and_consumed(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path)
    target = directory / "aggregate.json"
    observation = evidence.consume_vitest_json_result(
        _write_raw(directory, _vitest_payload(), name="vitest.json"),
        repository_root=ROOT,
    )

    published = evidence.publish_frontend_collection_evidence(
        target,
        (observation,),
    )
    consumed = evidence.consume_frontend_collection_evidence(target)

    assert consumed == published
    assert consumed["schema_version"] == evidence.AGGREGATE_SCHEMA_VERSION
    assert consumed["collected_test_count"] == 1
    assert consumed["failed_test_refs"] == []
    assert consumed["result_status"] == "passed"
    assert consumed["collection_digest_ref"].startswith("sha256:")
    assert not target.exists()
    rendered = json.dumps(consumed)
    assert str(ROOT) not in rendered
    assert "safe suite" not in rendered


def test_safe_frontend_aggregate_rejects_duplicate_runner_and_tampering(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path)
    observation = evidence.consume_vitest_json_result(
        _write_raw(directory, _vitest_payload(), name="vitest.json"),
        repository_root=ROOT,
    )

    with pytest.raises(
        evidence.FrontendCollectionEvidenceError,
        match="aggregate-observation-duplicate",
    ):
        evidence.publish_frontend_collection_evidence(
            directory / "duplicate.json",
            (observation, observation),
        )

    target = directory / "aggregate.json"
    payload = evidence.publish_frontend_collection_evidence(target, (observation,))
    payload["collected_test_count"] = 2
    target.unlink()
    target.write_text(json.dumps(payload), encoding="utf-8")
    target.chmod(0o600)
    with pytest.raises(
        evidence.FrontendCollectionEvidenceError,
        match="aggregate-binding",
    ):
        evidence.consume_frontend_collection_evidence(target)
    assert not target.exists()


def test_safe_frontend_aggregate_rejects_unsafe_output_target(
    tmp_path: Path,
) -> None:
    private = _private_directory(tmp_path / "private")
    outside = tmp_path / "outside"
    outside.mkdir()
    observation = evidence.consume_vitest_json_result(
        _write_raw(private, _vitest_payload(), name="vitest.json"),
        repository_root=ROOT,
    )
    linked = private / "linked"
    linked.symlink_to(outside, target_is_directory=True)

    with pytest.raises(evidence.FrontendCollectionEvidenceError):
        evidence.publish_frontend_collection_evidence(
            linked / "aggregate.json",
            (observation,),
        )


def test_safe_frontend_aggregate_rejects_symlinked_ancestor(
    tmp_path: Path,
) -> None:
    private = _private_directory(tmp_path / "private")
    observation = evidence.consume_vitest_json_result(
        _write_raw(private, _vitest_payload(), name="vitest.json"),
        repository_root=ROOT,
    )
    real_root = tmp_path / "real-root"
    real_root.mkdir(mode=0o700)
    child = real_root / "child"
    child.mkdir(mode=0o700)
    linked_root = tmp_path / "linked-root"
    linked_root.symlink_to(real_root, target_is_directory=True)

    with pytest.raises(evidence.FrontendCollectionEvidenceError, match="unsafe"):
        evidence.publish_frontend_collection_evidence(
            linked_root / "child" / "aggregate.json",
            (observation,),
        )
    assert not (child / "aggregate.json").exists()


def test_vitest_failed_run_remains_valid_collection_evidence(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    raw = _write_raw(
        directory,
        _vitest_payload([_vitest_assertion(status="failed")]),
    )

    result = evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert result["result_status"] == "failed"
    assert result["failed_test_count"] == 1
    assert len(result["failed_test_refs"]) == 1
    assert evidence.is_safe_frontend_test_ref(result["failed_test_refs"][0])
    assert not raw.exists()


def test_playwright_failed_run_retains_only_bounded_safe_test_refs(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path)
    failed = _playwright_test(
        outcome="unexpected",
        attempts=[_playwright_attempt("failed", 0)],
    )
    raw = _write_raw(directory, _playwright_payload([failed]))

    result = evidence.consume_playwright_json_result(raw, repository_root=ROOT)

    assert result["result_status"] == "failed"
    assert result["failed_test_count"] == 1
    assert len(result["failed_test_refs"]) == 1
    assert evidence.is_safe_frontend_test_ref(result["failed_test_refs"][0])
    rendered = json.dumps(result)
    for forbidden in ("raw", "title", str(ROOT), "stdout", "stderr"):
        assert forbidden not in rendered
    assert not raw.exists()

    target = directory / "aggregate.json"
    published = evidence.publish_frontend_collection_evidence(target, (result,))
    consumed = evidence.consume_frontend_collection_evidence(target)
    assert consumed["failed_test_refs"] == result["failed_test_refs"]
    assert consumed == published


def test_vitest_4_1_8_real_shape_counts_file_root_and_describe_suite(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path)
    payload = _vitest_payload(
        [
            _vitest_assertion(name="first assertion"),
            _vitest_assertion(name="second assertion"),
            _vitest_assertion(name="third assertion"),
        ]
    )
    assert payload["numTotalTestSuites"] == 2
    assert len(payload["testResults"]) == 1  # type: ignore[arg-type]
    raw = _write_raw(directory, payload)

    result = evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert result["collected_test_count"] == 3
    assert result["passed_test_count"] == 3
    assert result["result_status"] == "passed"
    assert not raw.exists()


def test_vitest_nested_and_sibling_describes_have_distinct_suite_prefixes(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path)
    nested_a = _vitest_assertion(name="nested a")
    nested_a["ancestorTitles"] = ["outer", "inner a"]
    nested_a["fullName"] = "outer inner a nested a"
    nested_b = _vitest_assertion(name="nested b")
    nested_b["ancestorTitles"] = ["outer", "inner b"]
    nested_b["fullName"] = "outer inner b nested b"
    sibling = _vitest_assertion(name="sibling")
    sibling["ancestorTitles"] = ["sibling describe"]
    sibling["fullName"] = "sibling describe sibling"
    payload = _vitest_payload(
        [nested_a, nested_b, sibling],
        suite_counts=(5, 0, 0),
    )
    assert payload["numTotalTestSuites"] == 5
    raw = _write_raw(directory, payload)

    result = evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert result["collected_test_count"] == 3
    assert result["result_status"] == "passed"
    assert not raw.exists()


def test_vitest_duplicate_sibling_describe_titles_use_reported_suite_counts(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path)
    first = _vitest_assertion(name="first")
    first["ancestorTitles"] = ["duplicate"]
    first["fullName"] = "duplicate first"
    second = _vitest_assertion(name="second")
    second["ancestorTitles"] = ["duplicate"]
    second["fullName"] = "duplicate second"
    raw = _write_raw(
        directory,
        _vitest_payload([first, second], suite_counts=(3, 0, 0)),
    )

    result = evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert result["collected_test_count"] == 2
    assert result["passed_test_count"] == 2
    assert result["result_status"] == "passed"
    assert not raw.exists()


def test_vitest_duplicate_full_names_receive_bounded_occurrence_identities(
    tmp_path: Path,
) -> None:
    single_directory = _private_directory(tmp_path / "single")
    duplicate_directory = _private_directory(tmp_path / "duplicate")
    assertion = _vitest_assertion(name="same")
    single_raw = _write_raw(single_directory, _vitest_payload([assertion]))
    duplicate_raw = _write_raw(
        duplicate_directory,
        _vitest_payload([assertion, dict(assertion)]),
    )

    single = evidence.consume_vitest_json_result(single_raw, repository_root=ROOT)
    duplicate = evidence.consume_vitest_json_result(duplicate_raw, repository_root=ROOT)

    assert single["collected_test_count"] == 1
    assert duplicate["collected_test_count"] == 2
    assert single["collection_digest_ref"] != duplicate["collection_digest_ref"]


def test_vitest_ordinary_skipped_and_todo_suites_remain_reported_as_passed(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path)
    skipped = _vitest_assertion(name="skipped child", status="skipped")
    skipped["ancestorTitles"] = ["ordinary skipped"]
    skipped["fullName"] = "ordinary skipped skipped child"
    skipped.pop("duration")
    todo = _vitest_assertion(name="todo child", status="todo")
    todo["ancestorTitles"] = ["ordinary todo"]
    todo["fullName"] = "ordinary todo todo child"
    todo.pop("duration")
    raw = _write_raw(
        directory,
        _vitest_payload([skipped, todo], suite_counts=(3, 0, 0)),
    )

    result = evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert result["result_status"] == "passed"
    assert result["skipped_test_count"] == 1
    assert result["todo_test_count"] == 1


def test_vitest_describe_todo_uses_reported_pending_suite_count(
    tmp_path: Path,
) -> None:
    pending_directory = _private_directory(tmp_path / "pending")
    ordinary_directory = _private_directory(tmp_path / "ordinary")
    todo = _vitest_assertion(name="child", status="todo")
    todo["ancestorTitles"] = ["todo suite"]
    todo["fullName"] = "todo suite child"
    todo.pop("duration")
    root_pass = _vitest_assertion(name="root passes")
    root_pass["ancestorTitles"] = []
    root_pass["fullName"] = "root passes"
    pending_raw = _write_raw(
        pending_directory,
        _vitest_payload(
            [todo, root_pass],
            suite_counts=(1, 0, 1),
        ),
    )
    ordinary_raw = _write_raw(
        ordinary_directory,
        _vitest_payload(
            [todo, root_pass],
            suite_counts=(2, 0, 0),
        ),
    )

    result = evidence.consume_vitest_json_result(pending_raw, repository_root=ROOT)
    ordinary_result = evidence.consume_vitest_json_result(
        ordinary_raw, repository_root=ROOT
    )

    assert result["result_status"] == "passed"
    assert result["passed_test_count"] == 1
    assert result["todo_test_count"] == 1
    assert result["collection_digest_ref"] != ordinary_result["collection_digest_ref"]


def test_vitest_hook_failure_is_failed_even_without_failed_test(
    tmp_path: Path,
) -> None:
    failed_directory = _private_directory(tmp_path / "failed")
    skipped_directory = _private_directory(tmp_path / "skipped")
    skipped = _vitest_assertion(name="never ran", status="skipped")
    skipped["ancestorTitles"] = []
    skipped["fullName"] = "never ran"
    skipped.pop("duration")
    failed_raw = _write_raw(
        failed_directory,
        _vitest_payload(
            [skipped],
            suite_counts=(0, 1, 0),
            file_status="failed",
        ),
    )
    skipped_raw = _write_raw(
        skipped_directory,
        _vitest_payload(
            [skipped],
            suite_counts=(1, 0, 0),
            file_status="passed",
        ),
    )

    result = evidence.consume_vitest_json_result(failed_raw, repository_root=ROOT)
    skipped_result = evidence.consume_vitest_json_result(
        skipped_raw, repository_root=ROOT
    )

    assert result["result_status"] == "failed"
    assert result["failed_test_count"] == 0
    assert result["skipped_test_count"] == 1
    assert result["collection_digest_ref"] != skipped_result["collection_digest_ref"]


def test_vitest_pending_assertion_is_rejected_as_incomplete(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path)
    pending = _vitest_assertion(name="unfinished", status="pending")
    pending.pop("duration")
    raw = _write_raw(directory, _vitest_payload([pending]))

    with pytest.raises(
        evidence.FrontendCollectionEvidenceError,
        match="vitest-test-incomplete",
    ):
        evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert not raw.exists()


def test_vitest_optional_location_coverage_and_absent_duration_are_accepted(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path)
    assertion = _vitest_assertion()
    assertion.pop("duration")
    assertion["location"] = {"line": 3, "column": 5}
    raw = _write_raw(
        directory,
        _vitest_payload([assertion], coverage_map={}),
    )

    result = evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert result["collected_test_count"] == 1
    assert result["result_status"] == "passed"


def test_vitest_suite_counter_algebra_is_fail_closed(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    payload = _vitest_payload()
    payload["numTotalTestSuites"] = 3
    raw = _write_raw(directory, payload)

    with pytest.raises(
        evidence.FrontendCollectionEvidenceError,
        match="vitest-suite-count-mismatch",
    ):
        evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert not raw.exists()


def test_playwright_retries_are_exact_and_content_free(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    raw = _write_raw(
        directory,
        _playwright_payload(
            [
                _playwright_test(
                    outcome="flaky",
                    attempts=[
                        _playwright_attempt("failed", 0),
                        _playwright_attempt("passed", 1),
                    ],
                )
            ]
        ),
    )

    result = evidence.consume_playwright_json_result(raw, repository_root=ROOT)

    assert result["collected_test_count"] == 1
    assert result["flaky_test_count"] == 1
    assert result["retry_attempt_count"] == 1
    assert result["result_status"] == "passed"
    assert result["runner_ref"] == "runner-ref:frontend:playwright"
    assert not raw.exists()
    rendered = json.dumps(result)
    for forbidden in ("raw", "visual", "desktop", str(ROOT), "stdout", "stderr"):
        assert forbidden not in rendered


@pytest.mark.parametrize("framework", ["vitest", "playwright"])
def test_internal_count_mismatch_is_rejected_and_consumed(
    tmp_path: Path,
    framework: str,
) -> None:
    directory = _private_directory(tmp_path)
    payload = _vitest_payload() if framework == "vitest" else _playwright_payload()
    if framework == "vitest":
        payload["numTotalTests"] = 2
        parser = evidence.consume_vitest_json_result
    else:
        stats = payload["stats"]
        assert isinstance(stats, dict)
        stats["expected"] = 2
        parser = evidence.consume_playwright_json_result
    raw = _write_raw(directory, payload)

    with pytest.raises(
        evidence.FrontendCollectionEvidenceError,
        match="count-mismatch",
    ):
        parser(raw, repository_root=ROOT)
    assert not raw.exists()


@pytest.mark.parametrize(
    "payload, parser",
    [
        (_vitest_payload(suite_name="/private/outside.test.ts"), evidence.consume_vitest_json_result),
        (_playwright_payload(file_name="../outside.spec.ts"), evidence.consume_playwright_json_result),
    ],
)
def test_paths_outside_repository_are_rejected_and_consumed(
    tmp_path: Path,
    payload: dict[str, object],
    parser: object,
) -> None:
    directory = _private_directory(tmp_path)
    raw = _write_raw(directory, payload)

    with pytest.raises(evidence.FrontendCollectionEvidenceError, match="test-path"):
        parser(raw, repository_root=ROOT)  # type: ignore[operator]
    assert not raw.exists()


def test_symlink_is_rejected_and_unlinked(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    target = tmp_path / "target.json"
    target.write_text(json.dumps(_vitest_payload()), encoding="utf-8")
    target.chmod(0o600)
    raw = directory / "result.json"
    raw.symlink_to(target)

    with pytest.raises(evidence.FrontendCollectionEvidenceError, match="unsafe"):
        evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert not raw.exists()
    assert target.exists()


def test_fifo_is_rejected_without_blocking_and_unlinked(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    raw = directory / "result.json"
    os.mkfifo(raw, mode=0o600)

    with pytest.raises(evidence.FrontendCollectionEvidenceError, match="unsafe"):
        evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert not raw.exists()


def test_hardlink_is_rejected_and_only_raw_link_is_removed(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    target = tmp_path / "target.json"
    target.write_text(json.dumps(_vitest_payload()), encoding="utf-8")
    target.chmod(0o600)
    raw = directory / "result.json"
    os.link(target, raw)

    with pytest.raises(evidence.FrontendCollectionEvidenceError, match="unsafe"):
        evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert not raw.exists()
    assert target.exists()


def test_oversized_file_is_rejected_and_unlinked(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    raw = directory / "result.json"
    with raw.open("wb") as handle:
        handle.truncate(evidence.MAX_RESULT_BYTES + 1)
    raw.chmod(0o600)

    with pytest.raises(evidence.FrontendCollectionEvidenceError, match="unsafe"):
        evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert not raw.exists()


def test_group_readable_file_is_rejected_and_unlinked(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    raw = _write_raw(directory, _vitest_payload())
    raw.chmod(0o640)

    with pytest.raises(evidence.FrontendCollectionEvidenceError, match="unsafe"):
        evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert not raw.exists()


@pytest.mark.parametrize(
    "encoded, reason",
    [
        (b'{"success":true,"success":false}', "duplicate-json-field"),
        (b'{"duration":NaN}', "nonfinite-json-number"),
        (b'{"duration":Infinity}', "nonfinite-json-number"),
        (b'{"duration":1e9999}', "nonfinite-json-number"),
    ],
)
def test_duplicate_and_nonfinite_json_are_rejected_and_unlinked(
    tmp_path: Path,
    encoded: bytes,
    reason: str,
) -> None:
    directory = _private_directory(tmp_path)
    raw = directory / "result.json"
    raw.write_bytes(encoded)
    raw.chmod(0o600)

    with pytest.raises(evidence.FrontendCollectionEvidenceError, match=reason):
        evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert not raw.exists()


def test_invalid_retry_sequence_is_rejected_and_unlinked(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    raw = _write_raw(
        directory,
        _playwright_payload(
            [
                _playwright_test(
                    outcome="flaky",
                    attempts=[
                        _playwright_attempt("failed", 0),
                        _playwright_attempt("passed", 2),
                    ],
                )
            ]
        ),
    )

    with pytest.raises(
        evidence.FrontendCollectionEvidenceError,
        match="retry-sequence",
    ):
        evidence.consume_playwright_json_result(raw, repository_root=ROOT)

    assert not raw.exists()


def test_digest_is_order_independent_but_status_bound(tmp_path: Path) -> None:
    first_directory = _private_directory(tmp_path / "first")
    second_directory = _private_directory(tmp_path / "second")
    first_items = [
        _vitest_assertion(name="one"),
        _vitest_assertion(name="two"),
    ]
    first_raw = _write_raw(first_directory, _vitest_payload(first_items))
    second_raw = _write_raw(second_directory, _vitest_payload(list(reversed(first_items))))

    first = evidence.consume_vitest_json_result(first_raw, repository_root=ROOT)
    second = evidence.consume_vitest_json_result(second_raw, repository_root=ROOT)

    assert first["collection_digest_ref"] == second["collection_digest_ref"]


def test_deep_json_is_rejected_after_raw_file_is_removed(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    value = "leaf"
    for _ in range(evidence.MAX_JSON_DEPTH + 3):
        value = [value]  # type: ignore[assignment]
    raw = _write_raw(directory, value)

    with pytest.raises(evidence.FrontendCollectionEvidenceError, match="json-bounds"):
        evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert not raw.exists()
