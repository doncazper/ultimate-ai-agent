#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message=r"Using `httpx` with `starlette\.testclient` is deprecated.*",
    category=Warning,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.gate import (  # noqa: E402
    FoundationGateCommandReceipt,
    FoundationGateEvaluator,
    FoundationGateLatencySummary,
    FoundationGateReport,
    FoundationGateReleaseLaneSummary,
    FoundationGateStatus,
)
from ultimate_ai_agent.core.gate.reports import (  # noqa: E402
    foundation_gate_evaluation_provenance_digest,
)
from scripts.verification.verification_github_prerequisites import (  # noqa: E402
    FoundationPrerequisiteManifest,
    load_foundation_prerequisite_manifest,
)


def exact_repository_revision(
    repository_root: Path,
    *,
    git_executable: str | Path = "git",
) -> str:
    git_command = str(git_executable)
    repository_probe = subprocess.run(
        [git_command, "rev-parse", "--show-toplevel"],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if repository_probe.returncode != 0:
        raise RuntimeError(
            "Foundation Gate exact revision provenance requires the repository root"
        )
    resolved_root = Path(repository_probe.stdout.strip()).resolve()
    if resolved_root != repository_root.resolve():
        raise RuntimeError(
            "Foundation Gate exact revision provenance requires the repository root"
        )
    worktree_status = subprocess.run(
        [git_command, "status", "--porcelain", "--untracked-files=all"],
        cwd=resolved_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if worktree_status:
        raise RuntimeError(
            "Foundation Gate revision provenance requires a clean worktree"
        )
    revision = subprocess.run(
        [git_command, "rev-parse", "HEAD"],
        cwd=resolved_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return f"git-sha:{revision}"


def evaluate_foundation_gate_at_exact_repository_revision(
    repository_root: Path,
    *,
    git_executable: str | Path = "git",
) -> tuple[str, FoundationGateReport]:
    """Run the canonical evaluator and inseparably bind its clean revision."""

    evaluated_revision_ref = exact_repository_revision(
        repository_root,
        git_executable=git_executable,
    )
    report = FoundationGateEvaluator(repository_root).evaluate()
    if (
        exact_repository_revision(
            repository_root,
            git_executable=git_executable,
        )
        != evaluated_revision_ref
    ):
        raise RuntimeError("Foundation Gate revision changed during evaluation")
    bound = report.model_copy(
        update={"evaluated_revision_ref": evaluated_revision_ref}
    )
    bound = bound.model_copy(
        update={
            "evaluation_provenance_digest_ref": (
                foundation_gate_evaluation_provenance_digest(bound)
            )
        }
    )
    return evaluated_revision_ref, bound


def evaluate_foundation_gate_for_repository_state(
    repository_root: Path,
    *,
    require_clean_revision: bool,
) -> tuple[str | None, FoundationGateReport]:
    """Preserve dirty-tree development checks without issuing provenance."""

    try:
        return evaluate_foundation_gate_at_exact_repository_revision(repository_root)
    except RuntimeError as exc:
        if (
            require_clean_revision
            or str(exc)
            != "Foundation Gate revision provenance requires a clean worktree"
        ):
            raise
    return None, FoundationGateEvaluator(repository_root).evaluate()


GATE_TESTS = [
    "tests/test_foundation_gate_criteria.py",
    "tests/test_foundation_gate_report.py",
    "tests/test_shadow_replay_m5.py",
    "tests/test_contract_compatibility.py",
    "tests/test_foundation_gate_blocked_modules.py",
    "tests/test_foundation_gate_secret_hygiene.py",
    "tests/test_foundation_gate_receipts.py",
    "tests/test_foundation_gate_rollback.py",
    "tests/test_foundation_gate_truth_evidence.py",
    "tests/test_foundation_gate_api_routes.py",
    "tests/test_model_profiles.py",
    "tests/test_model_routing_policy.py",
    "tests/test_model_router_decisions.py",
    "tests/test_model_router_privacy.py",
    "tests/test_model_router_context_budget.py",
    "tests/test_model_router_no_execution.py",
    "tests/test_cost_budgets.py",
    "tests/test_cost_governor.py",
    "tests/test_resource_governor.py",
    "tests/test_m7_api_routes.py",
    "tests/test_m7_gate_integration.py",
    "tests/test_api_manifest.py",
    "tests/test_openapi_contract.py",
    "tests/test_agents_md_guidance.py",
    "tests/test_m75_gate_integration.py",
    "tests/test_model_runtime_manifests.py",
    "tests/test_model_runtime_requests.py",
    "tests/test_model_runtime_simulator.py",
    "tests/test_model_runtime_no_real_calls.py",
    "tests/test_model_runtime_redaction.py",
    "tests/test_model_runtime_event_metadata.py",
    "tests/test_model_runtime_api_routes.py",
    "tests/test_m8_gate_integration.py",
    "tests/test_approval_requests.py",
    "tests/test_approval_authority.py",
    "tests/test_approval_validation.py",
    "tests/test_approval_expiration.py",
    "tests/test_approval_scope.py",
    "tests/test_approval_receipts.py",
    "tests/test_approval_integration_model_router.py",
    "tests/test_approval_integration_model_runtime.py",
    "tests/test_approval_integration_tool_broker.py",
    "tests/test_approval_integration_kernel.py",
    "tests/test_m85_api_routes.py",
    "tests/test_m85_gate_integration.py",
    "tests/test_local_loopback_endpoint_policy.py",
    "tests/test_local_loopback_transport.py",
    "tests/test_local_loopback_adapter.py",
    "tests/test_local_loopback_approval.py",
    "tests/test_local_loopback_no_remote.py",
    "tests/test_local_loopback_api_routes.py",
    "tests/test_m9_gate_integration.py",
    "tests/test_manual_loopback_smoke_policy.py",
    "tests/test_manual_loopback_smoke_transport.py",
    "tests/test_manual_loopback_smoke_script.py",
    "tests/test_manual_loopback_smoke_api_routes.py",
    "tests/test_m10_gate_integration.py",
    "tests/test_remote_worker_models.py",
    "tests/test_remote_worker_registry.py",
    "tests/test_remote_worker_policy.py",
    "tests/test_remote_worker_transports.py",
    "tests/test_remote_worker_dry_run.py",
    "tests/test_remote_worker_api_routes.py",
    "tests/test_remote_worker_no_network.py",
    "tests/test_remote_worker_gate_integration.py",
]


COMMAND_MODES = {
    "full",
    "legacy-full",
    "targeted-tests",
    "verify-all",
    "report-only",
    "ci-after-verify-all",
    "ci-parallel",
}


def run_command(command_ref: str, command_mode: str, args: list[str], safe_summary: str) -> FoundationGateCommandReceipt:
    print(f"\nRunning: {' '.join(args)}")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    started = time.perf_counter()
    result = subprocess.run(args, cwd=ROOT, env=env, text=True)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    status = "PASS" if result.returncode == 0 else f"FAIL ({result.returncode})"
    print(f"Command status: {status}")
    return FoundationGateCommandReceipt(
        command_ref=command_ref,
        command_mode=command_mode,
        status="passed" if result.returncode == 0 else "failed",
        satisfied_by="direct",
        safe_summary=safe_summary,
        return_code=result.returncode,
        elapsed_ms=elapsed_ms,
    )


def external_verify_all_receipt(command_mode: str) -> FoundationGateCommandReceipt:
    return FoundationGateCommandReceipt(
        command_ref="command:scripts.verify_all",
        command_mode=command_mode,
        status="satisfied_external",
        satisfied_by="ci-master-verification",
        safe_summary=(
            "Master verification was satisfied by the preceding CI step; "
            "Foundation Gate generated the typed report only."
        ),
    )


def parallel_ci_receipt(
    command_mode: str,
    *,
    prerequisite_path: Path,
    repository_sha: str,
    base_sha: str,
) -> FoundationGateCommandReceipt:
    prerequisite: FoundationPrerequisiteManifest = (
        load_foundation_prerequisite_manifest(
            prerequisite_path,
            ROOT,
            repository_sha,
            base_sha,
        )
    )
    return FoundationGateCommandReceipt(
        command_ref="command:ci.parallel_verification",
        command_mode=command_mode,
        status="satisfied_by_exact_receipts",
        satisfied_by=prerequisite.content_ref,
        safe_summary=(
            "Lint, complete pytest, and static verification were revalidated "
            "from exact-SHA, exact-plan GitHub job receipts; Foundation Gate "
            "generated the typed report without repeating those commands."
        ),
    )


def report_only_receipt(command_mode: str) -> FoundationGateCommandReceipt:
    return FoundationGateCommandReceipt(
        command_ref="command:foundation_gate.typed_report",
        command_mode=command_mode,
        status="report_only",
        satisfied_by="typed-foundation-gate-evaluator",
        safe_summary=(
            "No external verifier commands were run. The typed Foundation Gate "
            "evaluator and latency summary still run local read/probe code; use "
            "--no-write-latest when the latest report files must not be updated."
        ),
    )


def commands_for_mode(command_mode: str) -> list[tuple[str, list[str], str]]:
    if command_mode == "full":
        return [
            (
                "command:scripts.verify_all",
                [sys.executable, "scripts/verify_all.py"],
                "Run the master verifier once; it includes Ruff, pytest, static scans, baseline, skill, and OpenAPI checks.",
            )
        ]
    if command_mode == "legacy-full":
        return [
            (
                "command:foundation_gate.targeted_tests",
                [sys.executable, "-m", "pytest", *GATE_TESTS],
                "Run targeted Foundation Gate tests.",
            ),
            (
                "command:scripts.verify_current_baseline",
                [sys.executable, "scripts/verify_current_baseline.py"],
                "Run current baseline verification.",
            ),
            (
                "command:scripts.verify_skill_package_security_rule",
                [sys.executable, "scripts/verify_skill_package_security_rule.py"],
                "Run skill package security rule verification.",
            ),
            (
                "command:scripts.verify_all",
                [sys.executable, "scripts/verify_all.py"],
                "Run the master verification suite.",
            ),
        ]
    if command_mode == "targeted-tests":
        return [
            (
                "command:foundation_gate.targeted_tests",
                [sys.executable, "-m", "pytest", *GATE_TESTS],
                "Run targeted Foundation Gate tests only.",
            )
        ]
    if command_mode == "verify-all":
        return [
            (
                "command:scripts.verify_all",
                [sys.executable, "scripts/verify_all.py"],
                "Run the master verification suite only.",
            )
        ]
    return []


def build_latency_gate_summary(
    *,
    foundation_gate_report_json: str | None,
    foundation_gate_report_md: str | None,
    write_report: bool = True,
    precomputed_foundation_gate_ms: float | None = None,
    precomputed_foundation_gate_status: str | None = None,
    precomputed_foundation_gate_result_count: int | None = None,
) -> FoundationGateLatencySummary:
    from scripts.check_foundation_gate_latency import run_latency_gate_summary

    summary = run_latency_gate_summary(
        foundation_gate_report_json=foundation_gate_report_json,
        foundation_gate_report_md=foundation_gate_report_md,
        write_report=write_report,
        precomputed_foundation_gate_ms=precomputed_foundation_gate_ms,
        precomputed_foundation_gate_status=precomputed_foundation_gate_status,
        precomputed_foundation_gate_result_count=precomputed_foundation_gate_result_count,
    )
    return FoundationGateLatencySummary.model_validate(summary)


def build_release_lane_summary() -> FoundationGateReleaseLaneSummary:
    from scripts.verify_release_lanes import build_release_lane_manifest

    manifest = build_release_lane_manifest()
    summary = {
        "schema_version": manifest["schema_version"],
        "task_ref": manifest["task_ref"],
        "overall_status": manifest["overall_status"],
        "definition_status": manifest["definition_status"],
        "command_execution_status": manifest["command_execution_status"],
        "lane_count": manifest["lane_count"],
        "lane_ids": [lane["lane_id"] for lane in manifest["lanes"]],
        "status_semantics": manifest["status_semantics"],
        "accepted_failures": manifest["accepted_failures"],
        "validation_failures": manifest["validation_failures"],
        "report_safety": manifest["report_safety"],
        "safe_summary": manifest["safe_summary"],
    }
    return FoundationGateReleaseLaneSummary.model_validate(summary)


def write_markdown_payload(payload: dict, markdown_path: Path) -> None:
    lines = [
        "# Foundation Gate Report",
        "",
        f"- Report: `{payload['report_id']}`",
        f"- Version: `{payload['version']}`",
        f"- Overall status: `{payload['overall_status']}`",
        f"- Summary: {payload['summary']}",
        f"- Next action: {payload['next_recommended_action']}",
        f"- Command mode: `{payload.get('command_mode') or 'none'}`",
        "",
        "## Command Receipts",
        "",
    ]
    if payload.get("command_receipts"):
        for receipt in payload["command_receipts"]:
            lines.append(
                f"- `{receipt['command_ref']}`: `{receipt['status']}` "
                f"via `{receipt['satisfied_by']}` - {receipt['safe_summary']}"
            )
    else:
        lines.append("- No command receipts recorded.")
    latency_gate = payload.get("latency_gate")
    if latency_gate:
        lines.extend([
            "",
            "## Latency Gate",
            "",
            f"- Status: `{latency_gate['status']}`",
            f"- p50/p95 status: `{latency_gate['p50_p95_status']}`",
            f"- Release latency: `{latency_gate['release_latency_status']}`",
            f"- Hot-path profile: `{latency_gate['hot_path_profile_status']}`",
            (
                "- Foundation Gate latency: "
                f"best `{latency_gate['foundation_gate_best_ms']}` ms "
                f"(budget `{latency_gate['foundation_gate_best_budget_ms']}` ms), "
                f"mean `{latency_gate['foundation_gate_mean_ms']}` ms "
                f"(budget `{latency_gate['foundation_gate_mean_budget_ms']}` ms)"
            ),
        ])
        if latency_gate.get("foundation_gate_report_json"):
            lines.append(
                f"- Report path: `{latency_gate['foundation_gate_report_json']}`"
            )
        accepted_failures = latency_gate.get("accepted_failures", [])
        lines.append(f"- Accepted failures: `{len(accepted_failures)}`")
        optional_prerequisites = latency_gate.get("optional_prerequisites", [])
        if optional_prerequisites:
            lines.extend(["", "### Optional Prerequisites", ""])
            for result in optional_prerequisites:
                reason_codes = ", ".join(result.get("reason_codes", [])) or "none"
                lines.append(
                    f"- `{result['safe_label']}`: `{result['status']}` "
                    f"({reason_codes})"
                )
        lines.extend(["", "### Latency Path Results", ""])
        for result in latency_gate.get("path_results", []):
            p95 = result["p95_ms"] if result["p95_ms"] is not None else "not measured"
            p50 = result["p50_ms"] if result["p50_ms"] is not None else "not measured"
            lines.append(
                f"- `{result['safe_label']}`: `{result['status']}` "
                f"p50 `{p50}` ms, p95 `{p95}` ms, budget "
                f"`{result['budget_ms']}` ms, `{result['budget_status']}`"
            )
        if latency_gate.get("failures"):
            lines.extend(["", "### Latency Failures", ""])
            for failure in latency_gate["failures"]:
                lines.append(f"- {failure}")
    release_lanes = payload.get("release_verification_lanes")
    if release_lanes:
        lines.extend([
            "",
            "## Release Verification Lanes",
            "",
            f"- Manifest status: `{release_lanes['overall_status']}`",
            f"- Definition status: `{release_lanes['definition_status']}`",
            f"- Command execution status: `{release_lanes['command_execution_status']}`",
            f"- Lane count: `{release_lanes['lane_count']}`",
            f"- Accepted failures: `{len(release_lanes.get('accepted_failures', []))}`",
            f"- Validation failures: `{len(release_lanes.get('validation_failures', []))}`",
            "- Lanes: "
            + ", ".join(f"`{lane_id}`" for lane_id in release_lanes.get("lane_ids", [])),
        ])
        lines.extend(["", "### Lane Status Semantics", ""])
        for status, meaning in release_lanes.get("status_semantics", {}).items():
            lines.append(f"- `{status}`: {meaning}")
    lines.extend([
        "",
        "## Criteria",
        "",
    ])
    for result in payload["results"]:
        lines.append(f"- `{result['criterion_id']}`: `{result['status']}` - {result['safe_message']}")
    write_text_atomic(markdown_path, "\n".join(lines) + "\n")


def write_text_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def write_json_atomic(path: Path, payload: str) -> None:
    if not payload.strip():
        raise ValueError("Foundation Gate JSON report payload must not be empty.")
    json.loads(payload)
    write_text_atomic(path, payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M6 Foundation Gate checks.")
    parser.add_argument(
        "--command-mode",
        choices=sorted(COMMAND_MODES),
        default="full",
        help=(
            "Command mode. full runs the master verifier once; legacy-full preserves the old targeted+baseline+skill+verify_all sequence; "
            "report-only skips external verifier commands but still runs local typed evaluator/probe summaries; ci-after-verify-all records an external CI verification receipt; "
            "ci-parallel records verification satisfied by required parallel CI jobs."
        ),
    )
    parser.add_argument("--skip-commands", action="store_true", help="Legacy alias for --command-mode report-only.")
    parser.add_argument("--no-write-latest", action="store_true", help="Do not update reports/foundation_gate/latest_* files.")
    parser.add_argument("--output", help="Optional path for an additional JSON report copy.")
    parser.add_argument("--ci-prerequisite-manifest")
    parser.add_argument("--ci-prerequisite-sha")
    parser.add_argument("--ci-prerequisite-base-sha")
    parser.add_argument(
        "--require-clean-revision",
        action="store_true",
        help=(
            "Fail unless the report can bind one clean exact Git revision. "
            "TAW-08 receipt issuance always enforces this independently."
        ),
    )
    args = parser.parse_args(argv)

    command_mode = "report-only" if args.skip_commands else args.command_mode
    prerequisite_values = (
        args.ci_prerequisite_manifest,
        args.ci_prerequisite_sha,
        args.ci_prerequisite_base_sha,
    )
    if command_mode == "ci-parallel" and not all(prerequisite_values):
        parser.error(
            "ci-parallel requires an exact prerequisite manifest and repository SHA"
        )
    if command_mode != "ci-parallel" and any(prerequisite_values):
        parser.error("CI prerequisite evidence is limited to ci-parallel mode")
    command_failures = []
    command_receipts: list[FoundationGateCommandReceipt] = []
    if command_mode == "ci-after-verify-all":
        command_receipts.append(external_verify_all_receipt(command_mode))
    elif command_mode == "ci-parallel":
        command_receipts.append(
            parallel_ci_receipt(
                command_mode,
                prerequisite_path=Path(args.ci_prerequisite_manifest),
                repository_sha=args.ci_prerequisite_sha,
                base_sha=args.ci_prerequisite_base_sha,
            )
        )
    elif command_mode == "report-only":
        command_receipts.append(report_only_receipt(command_mode))
    for command_ref, command, safe_summary in commands_for_mode(command_mode):
        receipt = run_command(command_ref, command_mode, command, safe_summary)
        command_receipts.append(receipt)
        if receipt.return_code != 0:
            command_failures.append(command_ref)

    foundation_gate_started = time.perf_counter()
    _evaluated_revision_ref, report = (
        evaluate_foundation_gate_for_repository_state(
            ROOT,
            require_clean_revision=args.require_clean_revision,
        )
    )
    foundation_gate_elapsed_ms = round(
        (time.perf_counter() - foundation_gate_started) * 1000,
        2,
    )
    report = report.model_copy(
        update={
            "command_mode": command_mode,
            "command_receipts": command_receipts,
        }
    )
    output_dir = ROOT / "reports" / "foundation_gate"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "latest_foundation_gate_report.json"
    markdown_path = output_dir / "latest_foundation_gate_report.md"
    latency_gate = build_latency_gate_summary(
        foundation_gate_report_json=None
        if args.no_write_latest
        else str(report_path.relative_to(ROOT)),
        foundation_gate_report_md=None
        if args.no_write_latest
        else str(markdown_path.relative_to(ROOT)),
        precomputed_foundation_gate_ms=foundation_gate_elapsed_ms,
        precomputed_foundation_gate_status=str(report.overall_status),
        precomputed_foundation_gate_result_count=len(report.results),
        write_report=not args.no_write_latest,
    )
    report = report.model_copy(
        update={
            "latency_gate": latency_gate,
            "release_verification_lanes": build_release_lane_summary(),
        }
    )
    report_payload = report.model_dump_json(indent=2)
    report_payload_dict = json.loads(report_payload)
    if not args.no_write_latest:
        write_json_atomic(report_path, report_payload)
        write_markdown_payload(report_payload_dict, markdown_path)
    requested_output_path = None
    if args.output:
        requested_output_path = Path(args.output)
        if not requested_output_path.is_absolute():
            requested_output_path = ROOT / requested_output_path
        requested_output_path.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(requested_output_path, report_payload)

    print("\n=== Foundation Gate Summary ===")
    print(f"Command mode: {command_mode}")
    if args.no_write_latest:
        print("Report: latest report update skipped")
        print("Markdown: latest markdown update skipped")
    else:
        print(f"Report: {report_path.relative_to(ROOT)}")
        print(f"Markdown: {markdown_path.relative_to(ROOT)}")
    if requested_output_path:
        print("Requested output: custom report copy written")
    print(f"Overall status: {report.overall_status}")
    print(report.summary)
    if report.latency_gate is not None:
        print(f"Latency gate: {report.latency_gate.status}")
        print(f"Latency p50/p95 status: {report.latency_gate.p50_p95_status}")
    if report.release_verification_lanes is not None:
        print(f"Release lane definitions: {report.release_verification_lanes.definition_status}")
        print(
            "Release lane command execution: "
            f"{report.release_verification_lanes.command_execution_status}"
        )
        print(f"Release lane count: {report.release_verification_lanes.lane_count}")

    if command_failures:
        print("\nCommand failures:")
        for failure in command_failures:
            print(f"- {failure}")
        return 1

    if report.overall_status != FoundationGateStatus.passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
