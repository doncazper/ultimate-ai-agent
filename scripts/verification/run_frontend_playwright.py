#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
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
    MAX_FAILED_TEST_REFS,
    FrontendFailureDiagnosticsError,
    playwright_failed_test_refs,
    publish_failed_test_refs,
    retain_failed_test_refs,
)


class FrontendPlaywrightError(RuntimeError):
    """A bounded Playwright check could not produce exact safe evidence."""


VISUAL_BACKEND_TRUTH_TEST = "tests/visual/backend-truth.real.spec.ts"
VISUAL_BACKEND_TRUTH_INVERT = "[desktop] > backend-truth.real.spec.ts\n"


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


def _combined_playwright_observation(
    observations: tuple[dict[str, object], ...],
) -> dict[str, object]:
    if len(observations) == 1:
        return observations[0]
    digest_material = json.dumps(
        [observation["collection_digest_ref"] for observation in observations],
        separators=(",", ":"),
    ).encode("ascii")
    failed = sum(int(observation["failed_test_count"]) for observation in observations)
    return {
        "schema_version": "uaa_frontend_collection_evidence.v1",
        "runner_ref": "runner-ref:frontend:playwright",
        "collected_test_count": sum(
            int(observation["collected_test_count"])
            for observation in observations
        ),
        "collection_digest_ref": "sha256:"
        + hashlib.sha256(
            b"uaa-playwright-phase-aggregate-v1\0" + digest_material
        ).hexdigest(),
        "collection_error_count": sum(
            int(observation["collection_error_count"])
            for observation in observations
        ),
        "failed_test_count": failed,
        "flaky_test_count": sum(
            int(observation["flaky_test_count"]) for observation in observations
        ),
        "passed_test_count": sum(
            int(observation["passed_test_count"]) for observation in observations
        ),
        "redaction_status": "content_free",
        "result_status": "failed" if failed else "passed",
        "retry_attempt_count": sum(
            int(observation["retry_attempt_count"])
            for observation in observations
        ),
        "skipped_test_count": sum(
            int(observation["skipped_test_count"]) for observation in observations
        ),
        "todo_test_count": sum(
            int(observation["todo_test_count"]) for observation in observations
        ),
    }


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
        suite_args = (
            ("--project=desktop", "--workers=1") if suite == "visual" else ()
        )
        phases: tuple[tuple[str, ...], ...] = ((),)
        if suite == "visual":
            fixture_list = temporary_root / "visual-fixtures-only.list"
            with _private_umask():
                fixture_list.write_text(
                    VISUAL_BACKEND_TRUTH_INVERT,
                    encoding="ascii",
                )
            fixture_list.chmod(0o600)
            phases = (
                (VISUAL_BACKEND_TRUTH_TEST,),
                (f"--test-list-invert={fixture_list}",),
            )
        try:
            playwright = str(resolve_installed_frontend_tool(APP, "playwright"))
        except FrontendCommandProcessError as exc:
            raise FrontendPlaywrightError(
                "frontend installed Playwright tool is unavailable"
            ) from exc
        deadline = (
            time.monotonic() + TIMEOUT_SECONDS if suite == "visual" else None
        )
        observations: list[dict[str, object]] = []
        all_failed_test_refs: set[str] = set()
        returncodes: list[int] = []
        for phase_index, phase_args in enumerate(phases):
            phase_raw_result = raw_result.with_stem(
                f"{raw_result.stem}-{phase_index}"
            )
            phase_artifact_output = artifact_output / str(phase_index)
            phase_artifact_output.mkdir(mode=0o700)
            env = dict(os.environ)
            env["PLAYWRIGHT_JSON_OUTPUT_FILE"] = str(phase_raw_result)
            if suite == "visual":
                env.pop("CONTROL_CENTER_VISUAL_REUSE_EXISTING_SERVER", None)
            timeout_seconds = (
                TIMEOUT_SECONDS
                if deadline is None
                else int(deadline - time.monotonic())
            )
            if timeout_seconds <= 0:
                raise FrontendPlaywrightError(
                    "frontend Playwright command exceeded its bounded timeout"
                )
            try:
                with _private_umask():
                    returncode = run_frontend_command(
                        (
                            playwright,
                            "test",
                            f"--config={config}",
                            *suite_args,
                            *phase_args,
                            "--reporter=json",
                            f"--output={phase_artifact_output}",
                        ),
                        cwd=APP,
                        env=env,
                        timeout_seconds=timeout_seconds,
                    )
            except FrontendCommandProcessError as exc:
                raise FrontendPlaywrightError(
                    "frontend Playwright command did not settle safely"
                ) from exc
            if deadline is not None and time.monotonic() > deadline:
                raise FrontendPlaywrightError(
                    "frontend Playwright command exceeded its bounded timeout"
                )
            phase_failed_test_refs = playwright_failed_test_refs(
                phase_raw_result,
                repository_root=ROOT,
            )
            phase_observation = consume_playwright_json_result(
                phase_raw_result,
                repository_root=ROOT,
            )
            if (returncode == 0) != (
                phase_observation["result_status"] == "passed"
            ):
                raise FrontendPlaywrightError(
                    "frontend Playwright status and evidence disagree"
                )
            returncodes.append(returncode)
            observations.append(phase_observation)
            all_failed_test_refs.update(phase_failed_test_refs)
        observation = _combined_playwright_observation(tuple(observations))
        returncode = 1 if any(returncodes) else 0
        failed_test_refs = tuple(sorted(all_failed_test_refs))[
            :MAX_FAILED_TEST_REFS
        ]
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
