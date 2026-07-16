#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import fields, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import (  # noqa: E402
    CI_JOB_GRAPH,
    SCHEMA_VERSION,
    definition_fingerprint,
)
from scripts.verification.ci_fallback_controller import (  # noqa: E402
    AttemptLedger,
    ControllerStatus,
    FallbackController,
    FallbackState,
    GitHubObservation,
    IsolatedPrivateExecutor,
    classify_github,
    status_payload,
)
from scripts.verification.ci_fallback_contracts import (  # noqa: E402
    GITHUB_ACTIVE_STATUSES,
    GITHUB_QUEUE_STATUSES,
    INFRASTRUCTURE_WINDOW,
)
from scripts.verification.pytest_shard_plan import (  # noqa: E402
    CANONICAL_PYTEST_SHARD_COUNT,
)


def _run_json(repo: Path, argv: tuple[str, ...]) -> Any:
    completed = subprocess.run(
        argv,
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError("GitHub read-only observation failed")
    return json.loads(completed.stdout)


def _duration_ms(start: str | None, end: str | None) -> int:
    if not start or not end:
        return 0
    started = datetime.fromisoformat(start.replace("Z", "+00:00"))
    completed = datetime.fromisoformat(end.replace("Z", "+00:00"))
    return max(0, int((completed - started).total_seconds() * 1000))


def observe_github(repo: Path, sha: str) -> GitHubObservation:
    try:
        branch = _git_value(repo, "branch", "--show-current")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        branch = ""
    selector = ("--branch", branch) if branch else ("--commit", sha)
    try:
        runs = _run_json(
            repo,
            (
                "gh",
                "run",
                "list",
                *selector,
                "--workflow",
                "CI",
                "--limit",
                "10",
                "--json",
                "databaseId,headSha,status,conclusion,createdAt,updatedAt,attempt",
            ),
        )
    except (RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired):
        return GitHubObservation(
            repository_sha=sha,
            run_ref="run-ref:github:unavailable",
            status="unavailable",
            conclusion="",
            repository_command_started=False,
            reason_ref="reason-ref:github:api-unavailable",
            observation_source="live_github",
        )
    exact_runs = [run for run in runs if run.get("headSha") == sha]
    if not exact_runs:
        return GitHubObservation(
            repository_sha=sha,
            run_ref="run-ref:github:not-observed",
            status="queued",
            conclusion="",
            repository_command_started=False,
            reason_ref="reason-ref:github:run-not-observed",
            observation_source="live_github",
        )
    run = exact_runs[0]
    run_id = int(run["databaseId"])
    observed_now = datetime.now(UTC)
    created_at = str(run.get("createdAt") or "")
    try:
        run_created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        run_timestamp_available = run_created.tzinfo is not None
    except ValueError:
        run_created = observed_now
        run_timestamp_available = False
    superseded = 0
    if run_timestamp_available:
        window_start = run_created - INFRASTRUCTURE_WINDOW
        for candidate in runs:
            if candidate is run or candidate.get("conclusion") != "cancelled":
                continue
            try:
                candidate_created = datetime.fromisoformat(
                    str(candidate.get("createdAt") or "").replace("Z", "+00:00")
                )
            except ValueError:
                continue
            if window_start <= candidate_created <= run_created:
                superseded += 1
    queue_duration_ms = 0
    if run.get("status") in GITHUB_QUEUE_STATUSES and run_timestamp_available:
        queue_duration_ms = max(
            0, int((datetime.now(UTC) - run_created).total_seconds() * 1000)
        )
    repository_command_started = False
    install_duration_ms = 0
    test_duration_ms = 0
    release_lane_duration_ms = 0
    jobs: list[dict[str, Any]] = []
    job_details_available = True
    job_details_complete = False
    try:
        job_payload = _run_json(
            repo,
            ("gh", "run", "view", str(run_id), "--json", "jobs"),
        )
        jobs = list(job_payload.get("jobs", []))
        job_details_complete = bool(jobs) and all(
            isinstance(job.get("steps"), list) and bool(job["steps"])
            for job in jobs
            if isinstance(job, dict)
        ) and all(isinstance(job, dict) for job in jobs)
    except (RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired):
        job_details_available = False
        jobs = []
    orchestration_steps = {
        "Set up job",
        "Check out repository",
        "Post Check out repository",
        "Complete job",
    }
    for job in jobs:
        job_duration = _duration_ms(job.get("startedAt"), job.get("completedAt"))
        job_name = str(job.get("name", ""))
        if "pytest" in job_name.lower():
            test_duration_ms += job_duration
        if job_name.startswith("Release Lane /") or job_name == "foundation-gate-report":
            release_lane_duration_ms += job_duration
        for step in job.get("steps", []):
            step_name = str(step.get("name", ""))
            if step_name.startswith("Install "):
                install_duration_ms += _duration_ms(
                    step.get("startedAt"), step.get("completedAt")
                )
            if (
                step_name not in orchestration_steps
                and step.get("status") in {"in_progress", "completed"}
            ):
                repository_command_started = True
    run_status = str(run.get("status") or "queued")
    if run_status == "completed" and not job_details_complete:
        repository_command_started = True
    expected_job_names = {job.display_name for job in CI_JOB_GRAPH}
    observed_job_names = {str(job.get("name", "")) for job in jobs}
    required_jobs_green = (
        job_details_complete
        and run_timestamp_available
        and expected_job_names == observed_job_names
        and all(
            job.get("status") == "completed" and job.get("conclusion") == "success"
            for job in jobs
        )
    )
    attestation_job = next(
        (job for job in jobs if job.get("name") == "manifest-attestation"), None
    )
    manifest_attested = bool(
        attestation_job
        and attestation_job.get("conclusion") == "success"
        and any(
            step.get("name") == "Run canonical manifest attestation"
            and step.get("status") == "completed"
            and step.get("conclusion") == "success"
            for step in attestation_job.get("steps", [])
        )
    )
    status = run_status
    conclusion = str(run.get("conclusion") or "")
    if (
        status == "completed"
        and conclusion == "success"
        and job_details_available
        and required_jobs_green
        and manifest_attested
    ):
        reason_ref = "reason-ref:github:exact-sha-green"
    elif status == "completed" and conclusion == "success":
        reason_ref = "reason-ref:github:required-evidence-missing"
        repository_command_started = True
    elif status in GITHUB_ACTIVE_STATUSES:
        reason_ref = (
            "reason-ref:github:runner-capacity"
            if queue_duration_ms > 10 * 60 * 1000
            else "reason-ref:github:run-active"
        )
    elif not job_details_available or not job_details_complete:
        reason_ref = "reason-ref:github:job-evidence-unavailable"
        repository_command_started = True
    elif not repository_command_started and conclusion in {
        "failure",
        "startup_failure",
        "stale",
    }:
        reason_ref = "reason-ref:github:prestart-failure"
    elif conclusion == "cancelled" and superseded >= 2:
        reason_ref = "reason-ref:github:superseded-churn"
    else:
        reason_ref = "reason-ref:github:repository-command-failed"
    return GitHubObservation(
        repository_sha=sha,
        run_ref=f"run-ref:github:{run_id}",
        status=status,
        conclusion=conclusion,
        repository_command_started=repository_command_started,
        reason_ref=reason_ref,
        attempt=int(run.get("attempt") or 1),
        queue_duration_ms=queue_duration_ms,
        install_duration_ms=install_duration_ms,
        test_duration_ms=test_duration_ms,
        release_lane_duration_ms=release_lane_duration_ms,
        superseded_run_count=superseded,
        manifest_version=SCHEMA_VERSION,
        manifest_fingerprint=definition_fingerprint(),
        manifest_attested=manifest_attested,
        observation_source="live_github",
        run_created_at=(
            run_created.astimezone(UTC).isoformat().replace("+00:00", "Z")
        ),
    )


def _observation_from_file(path: Path) -> GitHubObservation:
    if path.is_symlink() or not path.is_file():
        raise ValueError("observation fixture must be a regular file")
    payload = json.loads(path.read_text(encoding="utf-8"))
    allowed = {item.name for item in fields(GitHubObservation)}
    if not isinstance(payload, dict) or set(payload) - allowed:
        raise ValueError("observation fixture contains unknown fields")
    observation = replace(
        GitHubObservation(**payload),
        observation_source="injected_simulation",
        manifest_attested=False,
    )
    observation.validate()
    return observation


def _git_value(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return completed.stdout.strip()


def _require_clean_checkout(repo: Path) -> None:
    if _git_value(repo, "status", "--porcelain"):
        raise ValueError("GitHub-first verification requires a clean exact-SHA checkout")


def _series_ref(repo: Path) -> str:
    branch = _git_value(repo, "branch", "--show-current") or "detached"
    digest = hashlib.sha256(branch.encode()).hexdigest()[:24]
    return f"series-ref:ci:{digest}"


def _ledger_directory(repo: Path) -> Path:
    common = Path(_git_value(repo, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = repo / common
    common = common.resolve()
    if common.is_symlink() or not common.is_dir():
        raise ValueError("Git common directory is unsafe")
    return common / "uaa-ci-private-fallback"


def _print_human(status: ControllerStatus) -> None:
    print("UAA GitHub-first verification controller")
    print(f"Strategy: {status.strategy}")
    print(f"State: {status.state.value}")
    print(f"Exact SHA: {status.repository_sha}")
    print(f"GitHub run: {status.github_run_ref}")
    print(f"Manifest: {status.manifest_version} / {status.manifest_fingerprint}")
    print(f"Private attempts: {status.private_attempt_count}")
    print(f"Commands completed privately: {status.commands_completed}")
    print(f"Remaining gate: {status.remaining_gate}")
    print("Blocker/reason refs:")
    for reason_ref in status.reason_refs:
        print(f"- {reason_ref}")
    for warning_ref in status.timing_warning_refs:
        print(f"- {warning_ref}")
    print(
        "Merge gate satisfied: "
        + ("yes (exact GitHub SHA only)" if status.merge_gate_satisfied else "no")
    )


def inspection_status(observation: GitHubObservation) -> ControllerStatus:
    return ControllerStatus(
        strategy="github-first-bounded-private-fallback",
        state=classify_github(observation),
        repository_sha=observation.repository_sha,
        manifest_version=SCHEMA_VERSION,
        manifest_fingerprint=definition_fingerprint(),
        github_run_ref=observation.run_ref,
        reason_refs=(observation.reason_ref,),
        commands_completed=0,
        remaining_gate=(
            "none"
            if classify_github(observation) == FallbackState.GITHUB_GREEN
            else "green GitHub merge-gate run on the exact final SHA"
        ),
        github_attempt_count=observation.attempt,
        private_attempt_count=0,
        duration_ms=0,
        github_gate_satisfied=(
            classify_github(observation) == FallbackState.GITHUB_GREEN
        ),
        merge_gate_satisfied=(
            classify_github(observation) == FallbackState.GITHUB_GREEN
        ),
    )


def status_exit_code(status: ControllerStatus) -> int:
    if status.state == FallbackState.GITHUB_GREEN:
        return 0
    if status.state in {
        FallbackState.GITHUB_RUNNING,
        FallbackState.PRIVATE_GREEN_PENDING_GITHUB,
        FallbackState.GITHUB_FINAL_RETRY,
    }:
        return 2
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Use GitHub first and bounded private CI only for infrastructure fallback."
    )
    parser.add_argument("--repo", default=".")
    parser.add_argument("--sha", required=True)
    parser.add_argument("--mode", choices=("github-first", "status"), default="github-first")
    parser.add_argument("--observation-file")
    parser.add_argument("--no-private", action="store_true")
    parser.add_argument(
        "--diagnose-pytest-shard",
        action="append",
        type=int,
        choices=range(CANONICAL_PYTEST_SHARD_COUNT),
        default=[],
        metavar=f"0-{CANONICAL_PYTEST_SHARD_COUNT - 1}",
        help="Explicitly reproduce one failed canonical pytest shard privately.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if len(args.diagnose_pytest_shard) != len(set(args.diagnose_pytest_shard)):
        parser.error("--diagnose-pytest-shard values must be unique")
    if args.diagnose_pytest_shard and (
        args.mode == "status" or args.no_private
    ):
        parser.error("pytest shard diagnosis requires active bounded private CI")
    repo = Path(args.repo).resolve()
    if repo.is_symlink() or not repo.is_dir():
        parser.error("repository must be a real directory")
    if _git_value(repo, "rev-parse", "HEAD") != args.sha:
        parser.error("--sha must match the exact checked-out commit")
    if args.mode != "status":
        try:
            _require_clean_checkout(repo)
        except ValueError as exc:
            parser.error(str(exc))
    ledger = AttemptLedger(_ledger_directory(repo))
    if args.mode == "status":
        records = ledger.read()
        last = records[-1] if records else {}
        payload = {
            "schema_version": "uaa_ci_fallback_status.v1",
            "strategy": "github-first-bounded-private-fallback",
            "record_count": len(records),
            "last_state": last.get("status", "github_primary"),
            "repository_sha": last.get("repository_sha", "not-observed"),
            "github_run_ref": last.get("run_ref", "run-ref:github:not-observed"),
            "reason_ref": last.get("reason_ref", "reason-ref:github:not-observed"),
            "duration_ms": last.get("duration_ms", 0),
            "remaining_gate": "green GitHub merge-gate run on the exact final SHA",
            "redaction_status": "content_free_refs_hashes_counts_and_durations_only",
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("UAA CI fallback status")
            print(f"Records: {payload['record_count']}")
            print(f"Last state: {payload['last_state']}")
            print(f"Exact SHA: {payload['repository_sha']}")
            print(f"GitHub run: {payload['github_run_ref']}")
            print(f"Remaining gate: {payload['remaining_gate']}")
        return 0
    observation = (
        _observation_from_file(Path(args.observation_file))
        if args.observation_file
        else observe_github(repo, args.sha)
    )
    if args.no_private:
        status = inspection_status(observation)
    else:
        controller = FallbackController(
            ledger,
            IsolatedPrivateExecutor(repo),
        )
        try:
            status = controller.evaluate(
                observation,
                series_ref=_series_ref(repo),
                diagnostic_unit_refs=tuple(
                    f"diagnostic-pytest-shard-{index}"
                    for index in sorted(args.diagnose_pytest_shard)
                ),
            )
        except (Exception, KeyboardInterrupt):
            print(
                "Private CI stopped: reason-ref:private-ci:controller-failure",
                file=sys.stderr,
            )
            return 1
    if args.json:
        print(json.dumps(status_payload(status), indent=2, sort_keys=True))
    else:
        _print_human(status)
    return status_exit_code(status)


if __name__ == "__main__":
    sys.exit(main())
