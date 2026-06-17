#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.gate import (  # noqa: E402
    FoundationGateCommandReceipt,
    FoundationGateEvaluator,
    FoundationGateStatus,
)


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


def parallel_ci_receipt(command_mode: str) -> FoundationGateCommandReceipt:
    return FoundationGateCommandReceipt(
        command_ref="command:ci.parallel_verification",
        command_mode=command_mode,
        status="satisfied_external",
        satisfied_by="ci-parallel-required-jobs",
        safe_summary=(
            "Lint, pytest, and static verification are satisfied by required "
            "parallel CI jobs in this workflow; Foundation Gate generated the "
            "typed report only."
        ),
    )


def report_only_receipt(command_mode: str) -> FoundationGateCommandReceipt:
    return FoundationGateCommandReceipt(
        command_ref="command:foundation_gate.typed_report",
        command_mode=command_mode,
        status="report_only",
        satisfied_by="typed-foundation-gate-evaluator",
        safe_summary="No external commands were run; only the typed Foundation Gate report was generated.",
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
    json.loads(payload)
    if not payload.strip():
        raise ValueError("Foundation Gate JSON report payload must not be empty.")
    write_text_atomic(path, payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M6 Foundation Gate checks.")
    parser.add_argument(
        "--command-mode",
        choices=sorted(COMMAND_MODES),
        default="full",
        help=(
            "Command mode. full runs the master verifier once; legacy-full preserves the old targeted+baseline+skill+verify_all sequence; "
            "report-only only generates the typed report; ci-after-verify-all records an external CI verification receipt; "
            "ci-parallel records verification satisfied by required parallel CI jobs."
        ),
    )
    parser.add_argument("--skip-commands", action="store_true", help="Legacy alias for --command-mode report-only.")
    parser.add_argument("--no-write-latest", action="store_true", help="Do not update reports/foundation_gate/latest_* files.")
    parser.add_argument("--output", help="Optional path for an additional JSON report copy.")
    args = parser.parse_args(argv)

    command_mode = "report-only" if args.skip_commands else args.command_mode
    command_failures = []
    command_receipts: list[FoundationGateCommandReceipt] = []
    if command_mode == "ci-after-verify-all":
        command_receipts.append(external_verify_all_receipt(command_mode))
    elif command_mode == "ci-parallel":
        command_receipts.append(parallel_ci_receipt(command_mode))
    elif command_mode == "report-only":
        command_receipts.append(report_only_receipt(command_mode))
    for command_ref, command, safe_summary in commands_for_mode(command_mode):
        receipt = run_command(command_ref, command_mode, command, safe_summary)
        command_receipts.append(receipt)
        if receipt.return_code != 0:
            command_failures.append(command_ref)

    report = FoundationGateEvaluator(ROOT).evaluate()
    report.command_mode = command_mode
    report.command_receipts = command_receipts
    output_dir = ROOT / "reports" / "foundation_gate"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "latest_foundation_gate_report.json"
    markdown_path = output_dir / "latest_foundation_gate_report.md"
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
        print(f"Requested output: {requested_output_path}")
    print(f"Overall status: {report.overall_status}")
    print(report.summary)

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
