"""Bounded, content-free frontend failure references for hosted CI summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any


MAX_RESULT_BYTES = 16 * 1024 * 1024
MAX_TESTS = 100_000
MAX_FAILED_TEST_REFS = 8
MAX_FAILED_ATTEMPT_REFS = 32
MAX_SUITE_DEPTH = 32
SUMMARY_ENV = "GITHUB_STEP_SUMMARY"
DIAGNOSTIC_NAME = "failure-diagnostics.json"
DIAGNOSTIC_SCHEMA = "uaa.frontend_failure_diagnostics.v1"
DIAGNOSTIC_ATTEMPT_SCHEMA = "uaa.frontend_failure_diagnostics.v2"

_SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_SAFE_REF_RE = re.compile(
    r"^frontend-test-ref:(?:vitest|playwright):"
    r"[A-Za-z0-9_.-]{1,72}:[a-f0-9]{12}$"
)
_SAFE_ATTEMPT_REF_RE = re.compile(
    r"^frontend-attempt-ref:playwright:([a-f0-9]{12}):[0-7]:"
    r"(?:failed|timed-out|interrupted|other):(?:0|[1-9][0-9]{0,5})$"
)


class FrontendFailureDiagnosticsError(ValueError):
    """A raw reporter result could not produce bounded diagnostic refs."""


def _load_result(path: Path) -> dict[str, Any]:
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_RESULT_BYTES:
            raise FrontendFailureDiagnosticsError("frontend diagnostic result is unsafe")
        payload = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise FrontendFailureDiagnosticsError(
            "frontend diagnostic result is unavailable"
        ) from exc
    if not isinstance(payload, dict):
        raise FrontendFailureDiagnosticsError("frontend diagnostic result is invalid")
    return payload


def _relative_report_path(
    rendered: object,
    *,
    repository_root: Path,
    relative_base: Path,
) -> str:
    if not isinstance(rendered, str) or not rendered or "\0" in rendered:
        raise FrontendFailureDiagnosticsError("frontend diagnostic path is invalid")
    candidate = Path(rendered)
    if not candidate.is_absolute():
        candidate = relative_base / candidate
    try:
        relative = candidate.resolve(strict=False).relative_to(
            repository_root.resolve(strict=True)
        )
    except (OSError, ValueError) as exc:
        raise FrontendFailureDiagnosticsError(
            "frontend diagnostic path is outside the repository"
        ) from exc
    return relative.as_posix()


def _safe_ref(runner: str, relative_path: str, *identity: str) -> str:
    component = _SAFE_COMPONENT_RE.sub(
        "-", PurePosixPath(relative_path).name
    ).strip(".-")
    component = component[:72] or "frontend-test"
    digest = hashlib.sha256(
        "\0".join((runner, relative_path, *identity)).encode("utf-8")
    ).hexdigest()[:12]
    ref = f"frontend-test-ref:{runner}:{component}:{digest}"
    if _SAFE_REF_RE.fullmatch(ref) is None:
        raise FrontendFailureDiagnosticsError("frontend diagnostic ref is unsafe")
    return ref


def _bounded_refs(refs: list[str]) -> tuple[str, ...]:
    return tuple(sorted(set(refs))[:MAX_FAILED_TEST_REFS])


def _validate_failed_refs(
    refs: tuple[str, ...],
    *,
    failed_test_count: int,
) -> None:
    if (
        failed_test_count <= 0
        or not refs
        or len(refs) > min(failed_test_count, MAX_FAILED_TEST_REFS)
        or len(refs) != len(set(refs))
        or tuple(sorted(refs)) != refs
        or any(_SAFE_REF_RE.fullmatch(ref) is None for ref in refs)
    ):
        raise FrontendFailureDiagnosticsError(
            "frontend diagnostic refs disagree with the failed count"
        )


def select_failed_attempt_refs(
    candidates: set[str], refs: tuple[str, ...],
) -> tuple[str, ...]:
    """Bind bounded code-location hints to the selected failing test identities."""
    identities = {
        ref.rsplit(":", 1)[1] for ref in refs
        if ref.startswith("frontend-test-ref:playwright:")
    }
    selected = []
    for candidate in sorted(candidates):
        match = _SAFE_ATTEMPT_REF_RE.fullmatch(candidate)
        if match is None:
            raise FrontendFailureDiagnosticsError("frontend attempt ref is invalid")
        if match.group(1) in identities:
            selected.append(candidate)
    return tuple(selected[:MAX_FAILED_ATTEMPT_REFS])


def _validate_attempt_refs(attempt_refs: tuple[str, ...], refs: tuple[str, ...]) -> None:
    if (
        len(attempt_refs) > MAX_FAILED_ATTEMPT_REFS
        or any(not isinstance(ref, str) for ref in attempt_refs)
        or select_failed_attempt_refs(set(attempt_refs), refs) != attempt_refs
    ):
        raise FrontendFailureDiagnosticsError("frontend attempt refs are invalid")


def _playwright_attempt_refs(
    test: dict[str, Any], ref: str, *, relative_path: str,
    repository_root: Path, playwright_root: Path,
) -> set[str]:
    results = test.get("results", [])
    if not isinstance(results, list):
        raise FrontendFailureDiagnosticsError("playwright attempt results are invalid")
    identity = ref.rsplit(":", 1)[1]
    refs: set[str] = set()
    for index, result in enumerate(results[:8]):
        if not isinstance(result, dict):
            raise FrontendFailureDiagnosticsError("playwright attempt result is invalid")
        status = result.get("status")
        if status in ("passed", "skipped"):
            continue
        reason = {
            "failed": "failed", "timedOut": "timed-out", "interrupted": "interrupted",
        }.get(status, "other") if isinstance(status, str) else "other"
        line = 0
        errors = result.get("errors", [])
        for error in errors[:8] if isinstance(errors, list) else []:
            location = error.get("location") if isinstance(error, dict) else None
            if not isinstance(location, dict):
                continue
            candidate_line = location.get("line")
            if type(candidate_line) is not int or not 1 <= candidate_line <= 999_999:
                continue
            try:
                location_path = _relative_report_path(
                    location.get("file"), repository_root=repository_root,
                    relative_base=playwright_root,
                )
            except FrontendFailureDiagnosticsError:
                continue
            if location_path == relative_path:
                line = candidate_line
                break
        # No messages, stacks, titles, paths, expected values or attachments.
        # Zero means the reporter did not provide a valid same-test source line.
        refs.add(f"frontend-attempt-ref:playwright:{identity}:{index}:{reason}:{line}")
    return refs


def vitest_failed_test_refs(
    path: Path,
    *,
    repository_root: Path,
) -> tuple[str, ...]:
    """Extract bounded refs from a Vitest JSON report without retaining titles."""

    payload = _load_result(path)
    suites = payload.get("testResults")
    if not isinstance(suites, list):
        raise FrontendFailureDiagnosticsError("vitest diagnostic suites are invalid")
    refs: list[str] = []
    observed = 0
    occurrences: dict[tuple[str, str], int] = {}
    for suite in suites:
        if not isinstance(suite, dict):
            raise FrontendFailureDiagnosticsError("vitest diagnostic suite is invalid")
        relative_path = _relative_report_path(
            suite.get("name"),
            repository_root=repository_root,
            relative_base=repository_root,
        )
        assertions = suite.get("assertionResults")
        if not isinstance(assertions, list):
            raise FrontendFailureDiagnosticsError(
                "vitest diagnostic assertions are invalid"
            )
        for assertion in assertions:
            observed += 1
            if observed > MAX_TESTS or not isinstance(assertion, dict):
                raise FrontendFailureDiagnosticsError(
                    "vitest diagnostic tests exceed the safe boundary"
                )
            full_name = assertion.get("fullName")
            status = assertion.get("status")
            if not isinstance(full_name, str) or not isinstance(status, str):
                raise FrontendFailureDiagnosticsError(
                    "vitest diagnostic identity is invalid"
                )
            occurrence_key = (relative_path, full_name)
            occurrence = occurrences.get(occurrence_key, 0)
            occurrences[occurrence_key] = occurrence + 1
            if status == "failed":
                refs.append(
                    _safe_ref(
                        "vitest",
                        relative_path,
                        full_name,
                        str(occurrence),
                    )
                )
    return _bounded_refs(refs)


def playwright_failed_test_refs(
    path: Path,
    *,
    repository_root: Path,
    attempt_refs: set[str] | None = None,
) -> tuple[str, ...]:
    """Extract bounded refs from a Playwright JSON report without retaining titles."""

    payload = _load_result(path)
    config = payload.get("config")
    suites = payload.get("suites")
    if not isinstance(config, dict) or not isinstance(suites, list):
        raise FrontendFailureDiagnosticsError(
            "playwright diagnostic result is invalid"
        )
    root_rendered = config.get("rootDir")
    if not isinstance(root_rendered, str):
        raise FrontendFailureDiagnosticsError("playwright diagnostic root is invalid")
    playwright_root = Path(root_rendered)
    if not playwright_root.is_absolute():
        raise FrontendFailureDiagnosticsError("playwright diagnostic root is invalid")
    _relative_report_path(
        root_rendered,
        repository_root=repository_root,
        relative_base=repository_root,
    )

    refs: list[str] = []
    attempts_by_test: dict[str, set[str]] = {}
    observed = 0

    def walk(raw_suites: list[object], *, depth: int) -> None:
        nonlocal observed
        if depth > MAX_SUITE_DEPTH:
            raise FrontendFailureDiagnosticsError(
                "playwright diagnostic suites exceed the safe depth"
            )
        for suite in raw_suites:
            if not isinstance(suite, dict):
                raise FrontendFailureDiagnosticsError(
                    "playwright diagnostic suite is invalid"
                )
            child_suites = suite.get("suites", [])
            specs = suite.get("specs", [])
            if not isinstance(child_suites, list) or not isinstance(specs, list):
                raise FrontendFailureDiagnosticsError(
                    "playwright diagnostic suite is invalid"
                )
            for spec in specs:
                if not isinstance(spec, dict):
                    raise FrontendFailureDiagnosticsError(
                        "playwright diagnostic spec is invalid"
                    )
                relative_path = _relative_report_path(
                    spec.get("file"),
                    repository_root=repository_root,
                    relative_base=playwright_root,
                )
                spec_id = spec.get("id")
                tests = spec.get("tests")
                if not isinstance(spec_id, str) or not isinstance(tests, list):
                    raise FrontendFailureDiagnosticsError(
                        "playwright diagnostic spec is invalid"
                    )
                for test in tests:
                    observed += 1
                    if observed > MAX_TESTS or not isinstance(test, dict):
                        raise FrontendFailureDiagnosticsError(
                            "playwright diagnostic tests exceed the safe boundary"
                        )
                    outcome = test.get("status")
                    project_id = test.get("projectId")
                    if not isinstance(outcome, str) or not isinstance(project_id, str):
                        raise FrontendFailureDiagnosticsError(
                            "playwright diagnostic identity is invalid"
                        )
                    if outcome == "unexpected":
                        ref = _safe_ref(
                            "playwright", relative_path, spec_id, project_id,
                        )
                        refs.append(ref)
                        if attempt_refs is not None:
                            attempts_by_test[ref] = _playwright_attempt_refs(
                                test, ref, relative_path=relative_path,
                                repository_root=repository_root,
                                playwright_root=playwright_root,
                            )
                            if len(attempts_by_test) > MAX_FAILED_TEST_REFS:
                                del attempts_by_test[max(attempts_by_test)]
            walk(child_suites, depth=depth + 1)

    walk(suites, depth=1)
    selected = _bounded_refs(refs)
    if attempt_refs is not None:
        attempt_refs.update(select_failed_attempt_refs(
            set().union(*attempts_by_test.values()), selected,
        ))
    return selected


def publish_failed_test_refs(
    refs: tuple[str, ...],
    *,
    failed_test_count: int,
    summary_path: Path | None = None,
    attempt_refs: tuple[str, ...] = (),
) -> None:
    """Append refs to the GitHub summary and stdout without raw reporter content."""

    _validate_failed_refs(refs, failed_test_count=failed_test_count)
    _validate_attempt_refs(attempt_refs, refs)
    lines = [
        f"Frontend diagnostic refs: {len(refs)} of {failed_test_count} failed tests",
        *(f"Diagnostic frontend test ref: {ref}" for ref in refs),
        *(f"Diagnostic frontend attempt ref: {ref}" for ref in attempt_refs),
    ]
    for line in lines:
        print(line)

    if summary_path is None:
        rendered = os.environ.get(SUMMARY_ENV)
        if rendered is None:
            return
        summary_path = Path(rendered)
    if not summary_path.is_absolute() or summary_path.name in {"", ".", ".."}:
        raise FrontendFailureDiagnosticsError(
            "frontend diagnostic summary target is invalid"
        )
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(summary_path, flags, 0o600)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise FrontendFailureDiagnosticsError(
                    "frontend diagnostic summary target is unsafe"
                )
            os.write(descriptor, ("\n".join(lines) + "\n").encode("ascii"))
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise FrontendFailureDiagnosticsError(
            "frontend diagnostic summary target is unavailable"
        ) from exc


def retain_failed_test_refs(
    path: Path,
    refs: tuple[str, ...],
    *,
    failed_test_count: int,
    attempt_refs: tuple[str, ...] = (),
) -> None:
    """Retain only validated refs for the workflow summary follow-up step."""

    _validate_failed_refs(refs, failed_test_count=failed_test_count)
    _validate_attempt_refs(attempt_refs, refs)
    if not path.is_absolute() or path.name != DIAGNOSTIC_NAME:
        raise FrontendFailureDiagnosticsError(
            "frontend diagnostic retention target is invalid"
        )
    try:
        parent = path.parent.resolve(strict=True)
    except OSError as exc:
        raise FrontendFailureDiagnosticsError(
            "frontend diagnostic retention parent is unavailable"
        ) from exc
    if parent != path.parent or path.parent.is_symlink() or not parent.is_dir():
        raise FrontendFailureDiagnosticsError(
            "frontend diagnostic retention parent is unsafe"
        )
    payload = {
        "schema_version": DIAGNOSTIC_SCHEMA,
        "failed_test_count": failed_test_count,
        "failed_test_refs": list(refs),
        "redaction_status": "content_free",
    }
    if attempt_refs:
        payload["schema_version"] = DIAGNOSTIC_ATTEMPT_SCHEMA
        payload["failed_attempt_refs"] = list(attempt_refs)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "ascii"
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise FrontendFailureDiagnosticsError(
                    "frontend diagnostic retention target is unsafe"
                )
            os.write(descriptor, encoded)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise FrontendFailureDiagnosticsError(
            "frontend diagnostic retention target is unavailable"
        ) from exc


def publish_retained_failed_test_refs(
    path: Path,
    *,
    summary_path: Path,
) -> bool:
    """Validate, publish, and consume a retained content-free diagnostic."""

    if not path.exists():
        return False
    payload = _load_result(path)
    expected_keys = {
        "schema_version",
        "failed_test_count",
        "failed_test_refs",
        "redaction_status",
    }
    has_attempts = payload.get("schema_version") == DIAGNOSTIC_ATTEMPT_SCHEMA
    if has_attempts:
        expected_keys.add("failed_attempt_refs")
    if set(payload) != expected_keys:
        raise FrontendFailureDiagnosticsError(
            "retained frontend diagnostic schema is invalid"
        )
    failed_test_count = payload["failed_test_count"]
    raw_refs = payload["failed_test_refs"]
    if (
        payload["schema_version"] not in (DIAGNOSTIC_SCHEMA, DIAGNOSTIC_ATTEMPT_SCHEMA)
        or payload["redaction_status"] != "content_free"
        or isinstance(failed_test_count, bool)
        or not isinstance(failed_test_count, int)
        or not isinstance(raw_refs, list)
        or any(not isinstance(ref, str) for ref in raw_refs)
    ):
        raise FrontendFailureDiagnosticsError(
            "retained frontend diagnostic is invalid"
        )
    refs = tuple(raw_refs)
    raw_attempts = payload.get("failed_attempt_refs", [])
    if not isinstance(raw_attempts, list) or (has_attempts and not raw_attempts):
        raise FrontendFailureDiagnosticsError("retained frontend attempts are invalid")
    publish_failed_test_refs(
        refs,
        failed_test_count=failed_test_count,
        summary_path=summary_path,
        attempt_refs=tuple(raw_attempts),
    )
    try:
        path.unlink()
    except OSError as exc:
        raise FrontendFailureDiagnosticsError(
            "retained frontend diagnostic could not be consumed"
        ) from exc
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Publish retained content-free frontend failure refs."
    )
    parser.add_argument("--diagnostic-file", type=Path, required=True)
    parser.add_argument("--summary-file", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        published = publish_retained_failed_test_refs(
            args.diagnostic_file,
            summary_path=args.summary_file,
        )
    except (FrontendFailureDiagnosticsError, KeyboardInterrupt, OSError):
        print(
            "Frontend diagnostics: blocked "
            "(reason-ref:frontend-diagnostics:unsafe-evidence)"
        )
        return 1
    if not published:
        print(
            "Frontend diagnostics: unavailable "
            "(reason-ref:frontend-diagnostics:not-produced)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
