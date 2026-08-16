"""Bounded, content-free frontend failure references for hosted CI summaries."""

from __future__ import annotations

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
MAX_SUITE_DEPTH = 32
SUMMARY_ENV = "GITHUB_STEP_SUMMARY"

_SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_SAFE_REF_RE = re.compile(
    r"^frontend-test-ref:(?:vitest|playwright):"
    r"[a-z0-9_.-]{1,72}:[a-f0-9]{12}$"
)


class FrontendFailureDiagnosticsError(ValueError):
    """A raw reporter result could not produce bounded diagnostic refs."""


def _load_result(path: Path) -> dict[str, Any]:
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_RESULT_BYTES:
            raise FrontendFailureDiagnosticsError("frontend diagnostic result is unsafe")
        payload = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
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
    component = (component[:72] or "frontend-test").lower()
    digest = hashlib.sha256(
        "\0".join((runner, relative_path, *identity)).encode("utf-8")
    ).hexdigest()[:12]
    ref = f"frontend-test-ref:{runner}:{component}:{digest}"
    if _SAFE_REF_RE.fullmatch(ref) is None:
        raise FrontendFailureDiagnosticsError("frontend diagnostic ref is unsafe")
    return ref


def _bounded_refs(refs: list[str]) -> tuple[str, ...]:
    return tuple(sorted(set(refs))[:MAX_FAILED_TEST_REFS])


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
                        refs.append(
                            _safe_ref(
                                "playwright",
                                relative_path,
                                spec_id,
                                project_id,
                            )
                        )
            walk(child_suites, depth=depth + 1)

    walk(suites, depth=1)
    return _bounded_refs(refs)


def publish_failed_test_refs(
    refs: tuple[str, ...],
    *,
    failed_test_count: int,
) -> None:
    """Append refs to the GitHub summary and stdout without raw reporter content."""

    if failed_test_count <= 0:
        return
    if not refs or len(refs) > min(failed_test_count, MAX_FAILED_TEST_REFS):
        raise FrontendFailureDiagnosticsError(
            "frontend diagnostic refs disagree with the failed count"
        )
    lines = [
        f"Frontend diagnostic refs: {len(refs)} of {failed_test_count} failed tests",
        *(f"Diagnostic frontend test ref: {ref}" for ref in refs),
    ]
    for line in lines:
        print(line)

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
