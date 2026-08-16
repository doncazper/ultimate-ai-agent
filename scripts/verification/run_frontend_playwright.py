#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "apps/control-center"
EVIDENCE_ENV = "UAA_FRONTEND_COLLECTION_EVIDENCE_PATH"
TIMEOUT_SECONDS = 900

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.frontend_collection_evidence import (  # noqa: E402
    FrontendCollectionEvidenceError,
    consume_playwright_json_result,
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
    playwright_failed_test_refs,
    publish_failed_test_refs,
    retain_failed_test_refs,
)


class FrontendPlaywrightError(RuntimeError):
    """A bounded Playwright check could not produce exact safe evidence."""


@contextmanager
def _private_umask() -> Iterator[None]:
    previous = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(previous)


def _evidence_target() -> Path | None:
    rendered = os.environ.get(EVIDENCE_ENV)
    if rendered is None:
        return None
    path = Path(rendered)
    if not path.is_absolute() or path.name in {"", ".", ".."}:
        raise FrontendPlaywrightError("frontend evidence target is invalid")
    validate_frontend_collection_target(path)
    return path


def run(suite: str) -> int:
    config = {
        "visual": "playwright.visual.config.ts",
        "smoke": "playwright.smoke.config.ts",
    }[suite]
    external_target = _evidence_target()
    parent = Path(tempfile.gettempdir()).resolve(strict=True)
    with tempfile.TemporaryDirectory(
        prefix=f"uaa-frontend-{suite}-",
        dir=parent,
    ) as temporary:
        temporary_root = Path(temporary)
        temporary_root.chmod(0o700)
        raw_result = temporary_root / "playwright-result.json"
        artifact_output = temporary_root / "playwright-artifacts"
        artifact_output.mkdir(mode=0o700)
        env = dict(os.environ)
        env["PLAYWRIGHT_JSON_OUTPUT_FILE"] = str(raw_result)
        project_args = ("--project=desktop",) if suite == "visual" else ()
        try:
            with _private_umask():
                returncode = run_frontend_command(
                    (
                        str(resolve_installed_frontend_tool(APP, "playwright")),
                        "test",
                        f"--config={config}",
                        *project_args,
                        "--reporter=json",
                        f"--output={artifact_output}",
                    ),
                    cwd=APP,
                    env=env,
                    timeout_seconds=TIMEOUT_SECONDS,
                )
        except FrontendCommandProcessError as exc:
            raise FrontendPlaywrightError(
                "frontend Playwright command did not settle safely"
            ) from exc
        failed_test_refs = playwright_failed_test_refs(
            raw_result,
            repository_root=ROOT,
        )
        observation = consume_playwright_json_result(
            raw_result,
            repository_root=ROOT,
        )
        if (returncode == 0) != (observation["result_status"] == "passed"):
            raise FrontendPlaywrightError(
                "frontend Playwright status and evidence disagree"
            )
        if external_target is not None:
            publish_frontend_collection_evidence(
                external_target,
                (observation,),
            )
        print(
            "Frontend Playwright "
            f"{suite}: {observation['result_status']} "
            f"({observation['collected_test_count']} observed)"
        )
        if returncode != 0:
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
            print(
                "Frontend Playwright: failed "
                "(reason-ref:frontend:playwright-failed)"
            )
        return 0 if returncode == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one bounded Control Center Playwright suite."
    )
    parser.add_argument("--suite", choices=("visual", "smoke"), required=True)
    args = parser.parse_args(argv)
    try:
        return run(args.suite)
    except (
        FrontendPlaywrightError,
        FrontendCollectionEvidenceError,
        FrontendFailureDiagnosticsError,
        KeyboardInterrupt,
        OSError,
    ):
        print("Frontend Playwright: blocked (reason-ref:frontend-check:unsafe-evidence)")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
