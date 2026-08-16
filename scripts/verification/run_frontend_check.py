#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "apps/control-center"
EVIDENCE_ENV = "UAA_FRONTEND_COLLECTION_EVIDENCE_PATH"
TYPECHECK_TIMEOUT_SECONDS = 300
TEST_TIMEOUT_SECONDS = 600
BUILD_TIMEOUT_SECONDS = 300

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.frontend_collection_evidence import (  # noqa: E402
    FrontendCollectionEvidenceError,
    consume_vitest_json_result,
    publish_frontend_collection_evidence,
    validate_frontend_collection_target,
)
from scripts.verification.frontend_command_process import (  # noqa: E402
    FrontendCommandProcessError,
    resolve_installed_frontend_tool,
    run_frontend_command,
)
from scripts.verification.frontend_failure_diagnostics import (  # noqa: E402
    DIAGNOSTIC_NAME,
    FrontendFailureDiagnosticsError,
    publish_failed_test_refs,
    retain_failed_test_refs,
    vitest_failed_test_refs,
)


class FrontendCheckError(RuntimeError):
    """The bounded frontend check could not produce exact safe evidence."""


def _load_scripts() -> dict[str, str]:
    try:
        payload = json.loads((APP / "package.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FrontendCheckError("frontend package declaration is unavailable") from exc
    scripts = payload.get("scripts")
    if not isinstance(scripts, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in scripts.items()
    ):
        raise FrontendCheckError("frontend package scripts are invalid")
    expected = {
        "typecheck": "tsc -b --pretty false",
        "lint": "tsc -b --pretty false",
        "test": "vitest",
        "build": "tsc -b && vite build",
    }
    if any(scripts.get(key) != value for key, value in expected.items()):
        raise FrontendCheckError("frontend duplicate-proof declaration changed")
    return scripts


@contextmanager
def _private_umask() -> Iterator[None]:
    previous = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(previous)


def _run(
    argv: tuple[str, ...],
    *,
    timeout: int,
    env: dict[str, str],
    cwd: Path = ROOT,
) -> int:
    try:
        return run_frontend_command(
            argv,
            cwd=cwd,
            env=env,
            timeout_seconds=timeout,
        )
    except FrontendCommandProcessError as exc:
        raise FrontendCheckError("frontend command did not settle safely") from exc


def _evidence_target() -> Path | None:
    rendered = os.environ.get(EVIDENCE_ENV)
    if rendered is None:
        return None
    path = Path(rendered)
    if not path.is_absolute() or path.name in {"", ".", ".."}:
        raise FrontendCheckError("frontend evidence target is invalid")
    validate_frontend_collection_target(path)
    return path


def run() -> int:
    _load_scripts()
    external_target = _evidence_target()
    parent = Path(tempfile.gettempdir()).resolve(strict=True)
    with tempfile.TemporaryDirectory(
        prefix="uaa-frontend-check-",
        dir=parent,
    ) as temporary:
        temporary_root = Path(temporary)
        temporary_root.chmod(0o700)
        raw_result = temporary_root / "vitest-result.json"
        build_output = temporary_root / "vite-dist"
        env = dict(os.environ)

        if _run(
            ("npm", "--prefix", "apps/control-center", "run", "typecheck", "--if-present"),
            timeout=TYPECHECK_TIMEOUT_SECONDS,
            env=env,
        ) != 0:
            print("Frontend typecheck: failed (reason-ref:frontend:typecheck-failed)")
            return 1
        print("Frontend typecheck: passed (exactly one TypeScript execution)")
        print("Frontend lint alias: satisfied by the exact matching typecheck declaration")

        with _private_umask():
            test_returncode = _run(
                (
                    "npm",
                    "--prefix",
                    "apps/control-center",
                    "run",
                    "test",
                    "--if-present",
                    "--",
                    "--run",
                    "--no-cache",
                    "--reporter=json",
                    f"--outputFile={raw_result}",
                ),
                timeout=TEST_TIMEOUT_SECONDS,
                env=env,
            )
        failed_test_refs = vitest_failed_test_refs(
            raw_result,
            repository_root=ROOT,
        )
        observation = consume_vitest_json_result(raw_result, repository_root=ROOT)
        if (test_returncode == 0) != (observation["result_status"] == "passed"):
            raise FrontendCheckError("frontend test status and evidence disagree")
        if external_target is not None:
            publish_frontend_collection_evidence(
                external_target,
                (observation,),
            )
        print(
            "Frontend unit tests: "
            f"{observation['result_status']} "
            f"({observation['collected_test_count']} observed)"
        )
        if test_returncode != 0:
            if external_target is not None:
                retain_failed_test_refs(
                    external_target.with_name(DIAGNOSTIC_NAME),
                    failed_test_refs,
                    failed_test_count=int(observation["failed_test_count"]),
                )
            publish_failed_test_refs(
                failed_test_refs,
                failed_test_count=int(observation["failed_test_count"]),
            )
            print("Frontend unit tests: failed (reason-ref:frontend:tests-failed)")
            return 1

        build_returncode = _run(
            (
                str(resolve_installed_frontend_tool(APP, "vite")),
                "build",
                "--outDir",
                str(build_output),
                "--emptyOutDir",
            ),
            timeout=BUILD_TIMEOUT_SECONDS,
            env=env,
            cwd=APP,
        )
        if build_returncode != 0:
            print("Frontend build: failed (reason-ref:frontend:build-failed)")
            return 1
        print("Frontend Vite production build: passed")
    return 0


def main() -> int:
    try:
        return run()
    except (
        FrontendCheckError,
        FrontendCollectionEvidenceError,
        FrontendFailureDiagnosticsError,
        KeyboardInterrupt,
        OSError,
    ):
        print("Frontend check: blocked (reason-ref:frontend-check:unsafe-evidence)")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
