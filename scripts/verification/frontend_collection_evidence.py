from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Callable


SCHEMA_VERSION = "uaa_frontend_collection_evidence.v1"
AGGREGATE_SCHEMA_VERSION = "uaa_frontend_collection_aggregate.v1"
MAX_RESULT_BYTES = 16 * 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 500_000
MAX_JSON_STRING_CHARS = 256 * 1024
MAX_TESTS = 100_000
MAX_SUITES = 25_000
MAX_ATTEMPTS_PER_TEST = 10
MAX_PATH_CHARS = 4_096
MAX_IDENTITY_CHARS = 16_384

_VITEST_RUNNER_REF = "runner-ref:frontend:vitest"
_PLAYWRIGHT_RUNNER_REF = "runner-ref:frontend:playwright"
_VITEST_TOP_LEVEL_FIELDS = {
    "numFailedTestSuites",
    "numFailedTests",
    "numPassedTestSuites",
    "numPassedTests",
    "numPendingTestSuites",
    "numPendingTests",
    "numTodoTests",
    "numTotalTestSuites",
    "numTotalTests",
    "snapshot",
    "startTime",
    "success",
    "testResults",
}
_VITEST_OPTIONAL_TOP_LEVEL_FIELDS = {"coverageMap"}
_VITEST_SUITE_FIELDS = {
    "assertionResults",
    "endTime",
    "message",
    "name",
    "startTime",
    "status",
}
_VITEST_ASSERTION_REQUIRED_FIELDS = {
    "ancestorTitles",
    "failureMessages",
    "fullName",
    "meta",
    "status",
    "tags",
    "title",
}
_VITEST_ASSERTION_OPTIONAL_FIELDS = {"duration", "location"}
_PLAYWRIGHT_TOP_LEVEL_FIELDS = {"config", "errors", "stats", "suites"}
_PLAYWRIGHT_OUTCOMES = {"expected", "flaky", "skipped", "unexpected"}
_PLAYWRIGHT_RESULT_STATUSES = {
    "failed",
    "interrupted",
    "passed",
    "skipped",
    "timedOut",
}
_SAFE_OBSERVATION_FIELDS = {
    "collected_test_count",
    "collection_digest_ref",
    "collection_error_count",
    "failed_test_count",
    "flaky_test_count",
    "passed_test_count",
    "redaction_status",
    "result_status",
    "retry_attempt_count",
    "runner_ref",
    "schema_version",
    "skipped_test_count",
    "todo_test_count",
}
_AGGREGATE_FIELDS = {
    "schema_version",
    "collection_digest_ref",
    "collected_test_count",
    "failed_test_count",
    "observations",
    "redaction_status",
    "result_status",
}


class FrontendCollectionEvidenceError(ValueError):
    """A raw frontend result could not produce safe collection evidence."""


def _fail(reason: str) -> None:
    raise FrontendCollectionEvidenceError(
        f"frontend collection evidence is invalid ({reason})"
    )


def _require_dict(value: object, reason: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(reason)
    return value


def _require_list(value: object, reason: str) -> list[Any]:
    if not isinstance(value, list):
        _fail(reason)
    return value


def _require_int(
    value: object,
    reason: str,
    *,
    minimum: int = 0,
    maximum: int = MAX_TESTS,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(reason)
    if not minimum <= value <= maximum:
        _fail(reason)
    return value


def _require_finite_number(
    value: object,
    reason: str,
    *,
    minimum: float = 0,
) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        _fail(reason)
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < minimum:
        _fail(reason)
    return parsed


def _require_string(
    value: object,
    reason: str,
    *,
    allow_empty: bool = False,
    maximum: int = MAX_IDENTITY_CHARS,
) -> str:
    if not isinstance(value, str):
        _fail(reason)
    if (not allow_empty and not value) or len(value) > maximum or "\x00" in value:
        _fail(reason)
    return value


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    decoded: dict[str, Any] = {}
    for key, value in pairs:
        if key in decoded:
            _fail("duplicate-json-field")
        decoded[key] = value
    return decoded


def _reject_nonfinite_constant(_value: str) -> None:
    _fail("nonfinite-json-number")


def _parse_finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        _fail("nonfinite-json-number")
    return parsed


def _validate_json_bounds(payload: object) -> None:
    nodes = 0
    stack: list[tuple[object, int]] = [(payload, 0)]
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            _fail("json-bounds")
        if isinstance(value, str):
            if len(value) > MAX_JSON_STRING_CHARS or "\x00" in value:
                _fail("json-string-bounds")
        elif isinstance(value, bool) or value is None:
            continue
        elif isinstance(value, int):
            if value.bit_length() > 63:
                _fail("json-integer-bounds")
        elif isinstance(value, float):
            if not math.isfinite(value):
                _fail("nonfinite-json-number")
        elif isinstance(value, list):
            stack.extend((item, depth + 1) for item in value)
        elif isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str) or len(key) > MAX_PATH_CHARS:
                    _fail("json-field-bounds")
                stack.append((item, depth + 1))
        else:
            _fail("json-value-type")


def _open_private_parent(path: Path) -> int:
    absolute = Path(os.path.abspath(path))
    components = absolute.parts[1:]
    if (
        not components
        or len(components) > 128
        or any(
            component in {"", ".", ".."}
            or "\x00" in component
            or len(os.fsencode(component)) > 255
            for component in components
        )
    ):
        _fail("unsafe-parent")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= (
        getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor: int | None = None
    try:
        descriptor = os.open(absolute.anchor, flags)
        for component in components:
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
    except OSError:
        if descriptor is not None:
            os.close(descriptor)
        raise FrontendCollectionEvidenceError(
            "frontend collection evidence parent is unsafe"
        ) from None
    assert descriptor is not None
    metadata = os.fstat(descriptor)
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        os.close(descriptor)
        _fail("unsafe-parent")
    return descriptor


def _read_and_unlink_raw_result(path: Path) -> bytes:
    """Read one private result exactly once and always remove its directory entry."""

    path = Path(path)
    if path.name in {"", ".", ".."} or path.parent == path:
        _fail("unsafe-result-name")
    parent_descriptor = _open_private_parent(path.parent)
    descriptor: int | None = None
    cleanup_error: OSError | None = None
    try:
        flags = os.O_RDONLY
        flags |= (
            getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        try:
            descriptor = os.open(path.name, flags, dir_fd=parent_descriptor)
            before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_uid != os.getuid()
                or before.st_nlink != 1
                or stat.S_IMODE(before.st_mode) != 0o600
                or not 0 < before.st_size <= MAX_RESULT_BYTES
            ):
                _fail("unsafe-result-file")
            remaining = before.st_size
            chunks: list[bytes] = []
            while remaining:
                chunk = os.read(descriptor, min(remaining, 65_536))
                if not chunk:
                    _fail("truncated-result-file")
                chunks.append(chunk)
                remaining -= len(chunk)
            if os.read(descriptor, 1):
                _fail("growing-result-file")
            after = os.fstat(descriptor)
            directory_entry = os.stat(
                path.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            identity_before = (
                before.st_dev,
                before.st_ino,
                before.st_mode,
                before.st_nlink,
                before.st_uid,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            )
            identity_after = (
                after.st_dev,
                after.st_ino,
                after.st_mode,
                after.st_nlink,
                after.st_uid,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            )
            if identity_before != identity_after:
                _fail("changing-result-file")
            if (
                directory_entry.st_dev != before.st_dev
                or directory_entry.st_ino != before.st_ino
                or directory_entry.st_mode != before.st_mode
                or directory_entry.st_nlink != before.st_nlink
                or directory_entry.st_uid != before.st_uid
                or directory_entry.st_size != before.st_size
            ):
                _fail("changing-result-file")
            return b"".join(chunks)
        except OSError:
            raise FrontendCollectionEvidenceError(
                "frontend collection evidence input is unsafe"
            ) from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            os.unlink(path.name, dir_fd=parent_descriptor)
            os.fsync(parent_descriptor)
        except OSError as exc:
            cleanup_error = exc
        finally:
            os.close(parent_descriptor)
        if cleanup_error is not None:
            raise FrontendCollectionEvidenceError(
                "frontend collection evidence input cleanup failed"
            ) from None


def _consume_json(path: Path) -> dict[str, Any]:
    encoded = _read_and_unlink_raw_result(path)
    try:
        payload = json.loads(
            encoded,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite_constant,
            parse_float=_parse_finite_float,
        )
    except FrontendCollectionEvidenceError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        raise FrontendCollectionEvidenceError(
            "frontend collection evidence input is malformed"
        ) from None
    _validate_json_bounds(payload)
    return _require_dict(payload, "top-level-object")


def _inside_root(candidate: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((candidate, root)) == os.fspath(root)
    except ValueError:
        return False


def _validated_report_path(
    value: object,
    *,
    repository_root: Path,
    relative_base: Path,
) -> str:
    rendered = _require_string(value, "test-path", maximum=MAX_PATH_CHARS)
    if "\\" in rendered:
        _fail("test-path")
    posix_path = PurePosixPath(rendered)
    if ".." in posix_path.parts:
        _fail("test-path")

    try:
        repository = Path(os.path.abspath(repository_root)).resolve(strict=True)
        base = Path(os.path.abspath(relative_base)).resolve(strict=True)
    except OSError:
        _fail("repository-root")
    if not repository.is_dir() or not _inside_root(base, repository):
        _fail("repository-root")
    raw_path = Path(rendered)
    candidate = raw_path if raw_path.is_absolute() else base / raw_path
    try:
        normalized = Path(os.path.abspath(candidate)).resolve(strict=False)
    except OSError:
        _fail("test-path")
    if not _inside_root(normalized, repository):
        _fail("test-path-outside-repository")
    relative = normalized.relative_to(repository).as_posix()
    if not relative or relative == "." or len(relative) > MAX_PATH_CHARS:
        _fail("test-path")
    return relative


def _identity_hash(*parts: str) -> str:
    encoded = json.dumps(parts, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _safe_payload(
    *,
    runner_ref: str,
    identities: list[tuple[str, str]],
    passed: int,
    failed: int,
    skipped: int,
    todo: int,
    flaky: int,
    retries: int,
    result_status: str | None = None,
    digest_bindings: dict[str, int | str | bool] | None = None,
) -> dict[str, Any]:
    effective_result_status = (
        result_status if result_status is not None else "failed" if failed else "passed"
    )
    if effective_result_status not in {"passed", "failed"}:
        _fail("result-status")
    collected = len(identities)
    canonical_projection: dict[str, object] = {
        "collected_test_count": collected,
        "failed_test_count": failed,
        "flaky_test_count": flaky,
        "identities": sorted(identities),
        "passed_test_count": passed,
        "result_status": effective_result_status,
        "retry_attempt_count": retries,
        "runner_ref": runner_ref,
        "skipped_test_count": skipped,
        "todo_test_count": todo,
    }
    if digest_bindings is not None:
        canonical_projection["runner_bindings"] = digest_bindings
    encoded = json.dumps(
        canonical_projection,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return {
        "collected_test_count": collected,
        "collection_digest_ref": f"sha256:{hashlib.sha256(encoded).hexdigest()}",
        "collection_error_count": 0,
        "failed_test_count": failed,
        "flaky_test_count": flaky,
        "passed_test_count": passed,
        "redaction_status": "content_free",
        "result_status": effective_result_status,
        "retry_attempt_count": retries,
        "runner_ref": runner_ref,
        "schema_version": SCHEMA_VERSION,
        "skipped_test_count": skipped,
        "todo_test_count": todo,
    }


def consume_vitest_json_result(
    path: Path,
    *,
    repository_root: Path,
) -> dict[str, Any]:
    """Consume a pinned Vitest JSON reporter result into content-free evidence."""

    payload = _consume_json(path)
    payload_fields = set(payload)
    if (
        not _VITEST_TOP_LEVEL_FIELDS <= payload_fields
        or not payload_fields
        <= _VITEST_TOP_LEVEL_FIELDS | _VITEST_OPTIONAL_TOP_LEVEL_FIELDS
    ):
        _fail("vitest-schema")
    if "coverageMap" in payload and payload["coverageMap"] is not None:
        _require_dict(payload["coverageMap"], "vitest-coverage-map")
    counts = {
        key: _require_int(payload[key], f"vitest-{key}")
        for key in (
            "numFailedTestSuites",
            "numFailedTests",
            "numPassedTestSuites",
            "numPassedTests",
            "numPendingTestSuites",
            "numPendingTests",
            "numTodoTests",
            "numTotalTestSuites",
            "numTotalTests",
        )
    }
    if not isinstance(payload["success"], bool):
        _fail("vitest-success")
    _require_int(
        payload["startTime"],
        "vitest-start-time",
        maximum=(1 << 63) - 1,
    )
    _require_dict(payload["snapshot"], "vitest-snapshot")
    suites = _require_list(payload["testResults"], "vitest-test-results")
    if not suites or len(suites) > MAX_SUITES:
        _fail("vitest-suite-count")

    identity_material: list[tuple[str, str, str]] = []
    observed = {"passed": 0, "failed": 0, "skipped": 0, "todo": 0}
    observed_file_statuses: dict[str, str] = {}
    for raw_suite in suites:
        suite = _require_dict(raw_suite, "vitest-suite")
        if set(suite) != _VITEST_SUITE_FIELDS:
            _fail("vitest-suite-schema")
        suite_status = _require_string(suite["status"], "vitest-suite-status")
        if suite_status not in {"passed", "failed"}:
            _fail("vitest-suite-status")
        suite_start = _require_finite_number(
            suite["startTime"], "vitest-suite-start-time"
        )
        suite_end = _require_finite_number(suite["endTime"], "vitest-suite-end-time")
        if suite_end < suite_start:
            _fail("vitest-suite-time")
        _require_string(
            suite["message"],
            "vitest-suite-message",
            allow_empty=True,
            maximum=MAX_JSON_STRING_CHARS,
        )
        relative_path = _validated_report_path(
            suite["name"],
            repository_root=repository_root,
            relative_base=repository_root,
        )
        assertions = _require_list(
            suite["assertionResults"], "vitest-assertion-results"
        )
        if not assertions:
            _fail("vitest-empty-suite")
        file_has_failed_test = False
        for raw_assertion in assertions:
            if len(identity_material) >= MAX_TESTS:
                _fail("vitest-test-count")
            assertion = _require_dict(raw_assertion, "vitest-assertion")
            assertion_fields = set(assertion)
            if (
                not _VITEST_ASSERTION_REQUIRED_FIELDS <= assertion_fields
                or not assertion_fields
                <= _VITEST_ASSERTION_REQUIRED_FIELDS | _VITEST_ASSERTION_OPTIONAL_FIELDS
            ):
                _fail("vitest-assertion-schema")
            if "duration" in assertion and assertion["duration"] is not None:
                _require_finite_number(assertion["duration"], "vitest-test-duration")
            if "location" in assertion and assertion["location"] is not None:
                location = _require_dict(assertion["location"], "vitest-test-location")
                if set(location) != {"line", "column"}:
                    _fail("vitest-test-location")
                _require_int(
                    location["line"],
                    "vitest-test-location",
                    minimum=1,
                    maximum=(1 << 31) - 1,
                )
                _require_int(
                    location["column"],
                    "vitest-test-location",
                    minimum=1,
                    maximum=(1 << 31) - 1,
                )
            failures = assertion["failureMessages"]
            if failures is not None:
                for failure in _require_list(failures, "vitest-failure-messages"):
                    _require_string(
                        failure,
                        "vitest-failure-message",
                        allow_empty=True,
                        maximum=MAX_JSON_STRING_CHARS,
                    )
            _require_dict(assertion["meta"], "vitest-test-meta")
            for tag in _require_list(assertion["tags"], "vitest-test-tags"):
                _require_string(tag, "vitest-test-tag")
            full_name = _require_string(assertion["fullName"], "vitest-test-identity")
            _require_string(assertion["title"], "vitest-test-title")
            ancestors = _require_list(
                assertion["ancestorTitles"], "vitest-ancestor-titles"
            )
            if len(ancestors) > MAX_JSON_DEPTH:
                _fail("vitest-ancestor-depth")
            for ancestor in ancestors:
                _require_string(ancestor, "vitest-ancestor-title")
            status_value = _require_string(assertion["status"], "vitest-test-status")
            if status_value == "pending":
                _fail("vitest-test-incomplete")
            status = status_value
            if status not in observed:
                _fail("vitest-test-status")
            observed[status] += 1
            file_has_failed_test = file_has_failed_test or status == "failed"
            identity_material.append((relative_path, full_name, status))
        if file_has_failed_test and suite_status != "failed":
            _fail("vitest-suite-status-mismatch")
        if relative_path in observed_file_statuses:
            _fail("vitest-duplicate-file-suite")
        observed_file_statuses[relative_path] = suite_status

    suite_total = counts["numTotalTestSuites"]
    suite_failed = counts["numFailedTestSuites"]
    suite_passed = counts["numPassedTestSuites"]
    suite_pending = counts["numPendingTestSuites"]
    if suite_total != suite_passed + suite_failed + suite_pending:
        _fail("vitest-suite-count-mismatch")
    file_count = len(observed_file_statuses)
    failed_file_count = sum(
        status == "failed" for status in observed_file_statuses.values()
    )
    passed_file_count = file_count - failed_file_count
    if (
        not file_count <= suite_total <= MAX_SUITES
        or suite_failed < failed_file_count
        or suite_passed < passed_file_count
        or suite_pending > suite_total - file_count
        or bool(suite_failed) != bool(failed_file_count)
    ):
        _fail("vitest-suite-count-mismatch")
    if counts["numTotalTests"] != len(identity_material) or counts[
        "numTotalTests"
    ] != sum(observed.values()):
        _fail("vitest-test-count-mismatch")
    if (
        counts["numPassedTests"] != observed["passed"]
        or counts["numFailedTests"] != observed["failed"]
        or counts["numPendingTests"] != observed["skipped"]
        or counts["numTodoTests"] != observed["todo"]
    ):
        _fail("vitest-test-count-mismatch")
    expected_success = suite_failed == 0 and observed["failed"] == 0
    if payload["success"] != expected_success:
        _fail("vitest-success-mismatch")
    occurrence_by_name: dict[tuple[str, str], int] = {}
    identities: list[tuple[str, str]] = []
    for relative_path, full_name, status in sorted(identity_material):
        occurrence_key = (relative_path, full_name)
        occurrence = occurrence_by_name.get(occurrence_key, 0)
        occurrence_by_name[occurrence_key] = occurrence + 1
        identity = _identity_hash(relative_path, full_name, str(occurrence))
        identities.append((identity, status))
    return _safe_payload(
        runner_ref=_VITEST_RUNNER_REF,
        identities=identities,
        passed=observed["passed"],
        failed=observed["failed"],
        skipped=observed["skipped"],
        todo=observed["todo"],
        flaky=0,
        retries=0,
        result_status="passed" if expected_success else "failed",
        digest_bindings={
            "failed_file_count": failed_file_count,
            "num_failed_test_suites": suite_failed,
            "num_passed_test_suites": suite_passed,
            "num_pending_test_suites": suite_pending,
            "num_total_test_suites": suite_total,
            "success": expected_success,
        },
    )


def _walk_playwright_suites(
    suites: list[Any],
    *,
    repository_root: Path,
    playwright_root: Path,
    on_test: Callable[[str, dict[str, Any], dict[str, Any]], None],
    depth: int = 0,
) -> int:
    if depth > MAX_JSON_DEPTH:
        _fail("playwright-suite-depth")
    observed_suites = 0
    for raw_suite in suites:
        observed_suites += 1
        if observed_suites > MAX_SUITES:
            _fail("playwright-suite-count")
        suite = _require_dict(raw_suite, "playwright-suite")
        allowed_fields = {"column", "file", "line", "specs", "suites", "title"}
        if not set(suite) <= allowed_fields or not {
            "column",
            "file",
            "line",
            "specs",
            "title",
        } <= set(suite):
            _fail("playwright-suite-schema")
        _require_string(suite["title"], "playwright-suite-title", allow_empty=True)
        _require_int(suite["line"], "playwright-suite-line", maximum=10_000_000)
        _require_int(
            suite["column"], "playwright-suite-column", maximum=10_000_000
        )
        suite_file = _validated_report_path(
            suite["file"],
            repository_root=repository_root,
            relative_base=playwright_root,
        )
        specs = _require_list(suite["specs"], "playwright-specs")
        for raw_spec in specs:
            spec = _require_dict(raw_spec, "playwright-spec")
            required_fields = {"column", "file", "id", "line", "ok", "tests", "title"}
            allowed_spec_fields = required_fields | {"tags"}
            if not required_fields <= set(spec) or not set(spec) <= allowed_spec_fields:
                _fail("playwright-spec-schema")
            if not isinstance(spec["ok"], bool):
                _fail("playwright-spec-ok")
            _require_string(spec["title"], "playwright-spec-title")
            _require_int(spec["line"], "playwright-spec-line", maximum=10_000_000)
            _require_int(
                spec["column"], "playwright-spec-column", maximum=10_000_000
            )
            spec_file = _validated_report_path(
                spec["file"],
                repository_root=repository_root,
                relative_base=playwright_root,
            )
            if spec_file != suite_file:
                _fail("playwright-spec-path-mismatch")
            for raw_test in _require_list(spec["tests"], "playwright-tests"):
                on_test(spec_file, spec, _require_dict(raw_test, "playwright-test"))
        child_suites = suite.get("suites", [])
        observed_suites += _walk_playwright_suites(
            _require_list(child_suites, "playwright-child-suites"),
            repository_root=repository_root,
            playwright_root=playwright_root,
            on_test=on_test,
            depth=depth + 1,
        )
        if observed_suites > MAX_SUITES:
            _fail("playwright-suite-count")
    return observed_suites


def consume_playwright_json_result(
    path: Path,
    *,
    repository_root: Path,
) -> dict[str, Any]:
    """Consume a pinned Playwright JSON reporter result into safe evidence."""

    payload = _consume_json(path)
    if set(payload) != _PLAYWRIGHT_TOP_LEVEL_FIELDS:
        _fail("playwright-schema")
    config = _require_dict(payload["config"], "playwright-config")
    playwright_root_rendered = _require_string(
        config.get("rootDir"), "playwright-root", maximum=MAX_PATH_CHARS
    )
    playwright_root = Path(playwright_root_rendered)
    if not playwright_root.is_absolute():
        _fail("playwright-root")
    _validated_report_path(
        playwright_root_rendered,
        repository_root=repository_root,
        relative_base=repository_root,
    )
    if _require_list(payload["errors"], "playwright-errors"):
        _fail("playwright-global-errors")
    stats = _require_dict(payload["stats"], "playwright-stats")
    required_stats = {"duration", "expected", "flaky", "skipped", "startTime", "unexpected"}
    if set(stats) != required_stats:
        _fail("playwright-stats-schema")
    _require_string(stats["startTime"], "playwright-start-time")
    duration = stats["duration"]
    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(duration)
        or not 0 <= duration <= 86_400_000
    ):
        _fail("playwright-duration")
    expected_counts = {
        key: _require_int(stats[key], f"playwright-{key}")
        for key in ("expected", "flaky", "skipped", "unexpected")
    }

    identities: list[tuple[str, str]] = []
    observed = {"expected": 0, "flaky": 0, "skipped": 0, "unexpected": 0}
    retries = 0
    spec_outcomes: dict[tuple[str, str], tuple[bool, list[str]]] = {}

    def observe_test(
        relative_path: str,
        spec: dict[str, Any],
        test: dict[str, Any],
    ) -> None:
        nonlocal retries
        if len(identities) >= MAX_TESTS:
            _fail("playwright-test-count")
        required_test_fields = {
            "annotations",
            "expectedStatus",
            "projectId",
            "projectName",
            "results",
            "status",
            "timeout",
        }
        if set(test) != required_test_fields:
            _fail("playwright-test-schema")
        outcome = _require_string(test["status"], "playwright-test-outcome")
        if outcome not in _PLAYWRIGHT_OUTCOMES:
            _fail("playwright-test-outcome")
        expected_status = _require_string(
            test["expectedStatus"], "playwright-expected-status"
        )
        if expected_status not in _PLAYWRIGHT_RESULT_STATUSES:
            _fail("playwright-expected-status")
        project_id = _require_string(test["projectId"], "playwright-project-id")
        _require_string(test["projectName"], "playwright-project-name", allow_empty=True)
        _require_int(test["timeout"], "playwright-timeout", maximum=86_400_000)
        _require_list(test["annotations"], "playwright-annotations")
        spec_id = _require_string(spec["id"], "playwright-spec-id")
        attempts = _require_list(test["results"], "playwright-results")
        if not 1 <= len(attempts) <= MAX_ATTEMPTS_PER_TEST:
            _fail("playwright-attempt-count")
        attempt_statuses: list[str] = []
        for attempt_index, raw_attempt in enumerate(attempts):
            attempt = _require_dict(raw_attempt, "playwright-result")
            retry = _require_int(
                attempt.get("retry"),
                "playwright-retry-index",
                maximum=MAX_ATTEMPTS_PER_TEST - 1,
            )
            if retry != attempt_index:
                _fail("playwright-retry-sequence")
            status_value = _require_string(
                attempt.get("status"), "playwright-result-status"
            )
            if status_value not in _PLAYWRIGHT_RESULT_STATUSES:
                _fail("playwright-result-status")
            attempt_statuses.append(status_value)
        final_status = attempt_statuses[-1]
        if outcome == "expected" and final_status != expected_status:
            _fail("playwright-outcome-mismatch")
        if outcome == "unexpected" and (
            final_status == expected_status or final_status == "skipped"
        ):
            _fail("playwright-outcome-mismatch")
        if outcome == "skipped" and any(
            status_value != "skipped" for status_value in attempt_statuses
        ):
            _fail("playwright-outcome-mismatch")
        if outcome == "flaky" and (
            len(attempts) < 2
            or final_status != expected_status
            or all(status_value == expected_status for status_value in attempt_statuses)
        ):
            _fail("playwright-outcome-mismatch")
        retries += len(attempts) - 1
        observed[outcome] += 1
        identity = _identity_hash(relative_path, spec_id, project_id)
        identities.append((identity, outcome))
        spec_key = (relative_path, spec_id)
        spec_ok = spec["ok"]
        assert isinstance(spec_ok, bool)
        existing = spec_outcomes.get(spec_key)
        if existing is None:
            spec_outcomes[spec_key] = (spec_ok, [outcome])
        else:
            existing_ok, outcomes = existing
            if existing_ok != spec_ok:
                _fail("playwright-spec-ok-mismatch")
            outcomes.append(outcome)

    suites = _require_list(payload["suites"], "playwright-suites")
    if not suites:
        _fail("playwright-suite-count")
    suite_count = _walk_playwright_suites(
        suites,
        repository_root=repository_root,
        playwright_root=playwright_root,
        on_test=observe_test,
    )
    if not 1 <= suite_count <= MAX_SUITES or not identities:
        _fail("playwright-collection-count")
    if len({identity for identity, _outcome in identities}) != len(identities):
        _fail("playwright-duplicate-test")
    if sum(expected_counts.values()) != len(identities):
        _fail("playwright-test-count-mismatch")
    if any(expected_counts[key] != observed[key] for key in expected_counts):
        _fail("playwright-test-count-mismatch")
    if any(
        spec_ok != all(outcome != "unexpected" for outcome in outcomes)
        for spec_ok, outcomes in spec_outcomes.values()
    ):
        _fail("playwright-spec-ok-mismatch")
    return _safe_payload(
        runner_ref=_PLAYWRIGHT_RUNNER_REF,
        identities=identities,
        passed=observed["expected"],
        failed=observed["unexpected"],
        skipped=observed["skipped"],
        todo=0,
        flaky=observed["flaky"],
        retries=retries,
    )


def _validated_safe_observation(payload: object) -> dict[str, Any]:
    observation = _require_dict(payload, "safe-observation")
    if set(observation) != _SAFE_OBSERVATION_FIELDS:
        _fail("safe-observation-schema")
    if observation["schema_version"] != SCHEMA_VERSION:
        _fail("safe-observation-schema-version")
    runner_ref = _require_string(observation["runner_ref"], "safe-observation-runner")
    if runner_ref not in {_VITEST_RUNNER_REF, _PLAYWRIGHT_RUNNER_REF}:
        _fail("safe-observation-runner")
    digest_ref = _require_string(
        observation["collection_digest_ref"],
        "safe-observation-digest",
    )
    if (
        not digest_ref.startswith("sha256:")
        or len(digest_ref) != len("sha256:") + 64
        or any(character not in "0123456789abcdef" for character in digest_ref[7:])
    ):
        _fail("safe-observation-digest")
    if observation["redaction_status"] != "content_free":
        _fail("safe-observation-redaction")
    if observation["result_status"] not in {"passed", "failed"}:
        _fail("safe-observation-status")
    counts = {
        field: _require_int(observation[field], f"safe-observation-{field}")
        for field in (
            "collected_test_count",
            "collection_error_count",
            "failed_test_count",
            "flaky_test_count",
            "passed_test_count",
            "retry_attempt_count",
            "skipped_test_count",
            "todo_test_count",
        )
    }
    if counts["collection_error_count"] != 0:
        _fail("safe-observation-collection-error")
    if counts["collected_test_count"] != sum(
        counts[field]
        for field in (
            "failed_test_count",
            "flaky_test_count",
            "passed_test_count",
            "skipped_test_count",
            "todo_test_count",
        )
    ):
        _fail("safe-observation-count")
    if (counts["failed_test_count"] == 0) != (
        observation["result_status"] == "passed"
    ):
        _fail("safe-observation-status")
    return dict(observation)


def _aggregate_payload(observations: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    if not observations or len(observations) > 2:
        _fail("aggregate-observation-count")
    normalized = tuple(
        sorted(
            (_validated_safe_observation(observation) for observation in observations),
            key=lambda observation: str(observation["runner_ref"]),
        )
    )
    runner_refs = tuple(str(observation["runner_ref"]) for observation in normalized)
    if len(runner_refs) != len(set(runner_refs)):
        _fail("aggregate-observation-duplicate")
    digest_material = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    aggregate_digest = hashlib.sha256(
        b"uaa-frontend-aggregate-v1\0" + digest_material
    ).hexdigest()
    failed = sum(int(observation["failed_test_count"]) for observation in normalized)
    payload = {
        "schema_version": AGGREGATE_SCHEMA_VERSION,
        "collection_digest_ref": f"sha256:{aggregate_digest}",
        "collected_test_count": sum(
            int(observation["collected_test_count"]) for observation in normalized
        ),
        "failed_test_count": failed,
        "observations": list(normalized),
        "redaction_status": "content_free",
        "result_status": "failed" if failed else "passed",
    }
    return payload


def _write_private_json(path: Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    if path.name in {"", ".", ".."} or path.parent == path:
        _fail("aggregate-output-name")
    parent_descriptor = _open_private_parent(path.parent)
    descriptor: int | None = None
    try:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        if not 0 < len(encoded) <= MAX_RESULT_BYTES:
            _fail("aggregate-output-size")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= (
            getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        try:
            descriptor = os.open(
                path.name,
                flags,
                0o600,
                dir_fd=parent_descriptor,
            )
        except OSError:
            _fail("aggregate-output-unsafe")
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            _fail("aggregate-output-unsafe")
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                _fail("aggregate-output-write")
            view = view[written:]
        os.fsync(descriptor)
        os.fsync(parent_descriptor)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_descriptor)


def validate_frontend_collection_target(path: Path) -> None:
    """Fail before execution unless one new owner-only evidence target is safe."""

    path = Path(path)
    if path.name in {"", ".", ".."} or path.parent == path:
        _fail("aggregate-output-name")
    parent_descriptor = _open_private_parent(path.parent)
    try:
        try:
            os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            return
        except OSError:
            _fail("aggregate-output-unsafe")
        _fail("aggregate-output-exists")
    finally:
        os.close(parent_descriptor)


def publish_frontend_collection_evidence(
    path: Path,
    observations: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    """Publish one bounded content-free frontend collection aggregate."""

    validate_frontend_collection_target(path)
    payload = _aggregate_payload(observations)
    _write_private_json(path, payload)
    return payload


def consume_frontend_collection_evidence(path: Path) -> dict[str, Any]:
    """Consume and delete one bounded content-free frontend collection aggregate."""

    payload = _consume_json(path)
    if set(payload) != _AGGREGATE_FIELDS:
        _fail("aggregate-schema")
    observations = _require_list(payload["observations"], "aggregate-observations")
    expected = _aggregate_payload(
        tuple(_validated_safe_observation(observation) for observation in observations)
    )
    if payload != expected:
        _fail("aggregate-binding")
    return payload
