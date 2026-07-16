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
) -> dict[str, object]:
    items = assertions or [_vitest_assertion()]
    status_counts = {
        "passed": sum(item["status"] == "passed" for item in items),
        "failed": sum(item["status"] == "failed" for item in items),
        "pending": sum(item["status"] in {"pending", "skipped"} for item in items),
        "todo": sum(item["status"] == "todo" for item in items),
    }
    suite_status = (
        "failed"
        if status_counts["failed"]
        else "pending"
        if status_counts["pending"] + status_counts["todo"] == len(items)
        else "passed"
    )
    return {
        "numFailedTestSuites": int(suite_status == "failed"),
        "numFailedTests": status_counts["failed"],
        "numPassedTestSuites": int(suite_status == "passed"),
        "numPassedTests": status_counts["passed"],
        "numPendingTestSuites": int(suite_status == "pending"),
        "numPendingTests": status_counts["pending"],
        "numTodoTests": status_counts["todo"],
        "numTotalTestSuites": 1,
        "numTotalTests": len(items),
        "snapshot": {},
        "startTime": 1_700_000_000_000,
        "success": status_counts["failed"] == 0,
        "testResults": [
            {
                "assertionResults": items,
                "endTime": 1_700_000_000_001,
                "message": "raw suite output must disappear",
                "name": suite_name or str(VITEST_FILE),
                "startTime": 1_700_000_000_000,
                "status": suite_status,
            }
        ],
    }


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


def test_vitest_failed_run_remains_valid_collection_evidence(tmp_path: Path) -> None:
    directory = _private_directory(tmp_path)
    raw = _write_raw(
        directory,
        _vitest_payload([_vitest_assertion(status="failed")]),
    )

    result = evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert result["result_status"] == "failed"
    assert result["failed_test_count"] == 1
    assert not raw.exists()


def test_vitest_file_suite_count_does_not_count_describe_ancestors(
    tmp_path: Path,
) -> None:
    directory = _private_directory(tmp_path)
    assertion = _vitest_assertion(name="uses one file-level suite")
    assertion["ancestorTitles"] = ["outer describe", "nested describe"]
    assertion["fullName"] = "outer describe nested describe uses one file-level suite"
    raw = _write_raw(directory, _vitest_payload([assertion]))

    result = evidence.consume_vitest_json_result(raw, repository_root=ROOT)

    assert result["collected_test_count"] == 1
    assert result["passed_test_count"] == 1
    assert result["result_status"] == "passed"
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
