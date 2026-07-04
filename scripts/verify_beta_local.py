#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PYTHON = os.environ.get("UAA_BETA_GATE_PYTHON", ".venv/bin/python")


@dataclass(frozen=True)
class BetaGateCommand:
    lane_id: str
    command_ref: str
    argv: tuple[str, ...]
    purpose: str
    required_for_beta: bool = True
    timeout_seconds: int = 900


REQUIRED_LANES = {
    "workspace_hygiene",
    "docs_integrity",
    "security_redaction",
    "product_truth",
    "operational_maturity",
    "openapi_contract",
    "api_perimeter",
    "gate_architecture",
    "release_lanes",
    "release_evidence_packet",
    "release_surface",
    "dogfood_live_loop",
    "dogfood_private_harness",
    "private_beta_readiness",
    "private_product_loop_trial",
    "private_trial_packet",
    "private_trial_ledger",
    "private_trial_manual_review",
    "web_runtime_authority",
    "authority_frontend_guard",
    "visual_proof",
    "setup_assistant",
    "evidence_memory",
    "trust_authority",
    "web_evidence",
    "provider_draft",
    "connector_draft",
    "workspace_spine",
    "backend_api",
    "frontend_states",
    "foundation_gate",
    "frontend",
}

LIVE_VISUAL_LANE = "frontend_live_visual"

FORBIDDEN_ARG_FRAGMENTS = {
    "curl",
    "wget",
    "openai",
    "anthropic",
    "npm install",
    "pip install",
    "gh pr merge",
    "git push",
    "git reset",
    "rm -rf",
}
MAX_FAILURE_OUTPUT_LINES = 80


def python_cmd(script: str, *args: str) -> tuple[str, ...]:
    return (PYTHON, script, *args)


def build_beta_local_gate_commands() -> list[BetaGateCommand]:
    return [
        BetaGateCommand(
            lane_id="workspace_hygiene",
            command_ref="command:git.diff-check",
            argv=("git", "diff", "--check"),
            purpose="Reject whitespace errors before beta QA claims.",
        ),
        BetaGateCommand(
            lane_id="frontend",
            command_ref="command:frontend.check",
            argv=("make", "frontend-check"),
            purpose="Run Control Center typecheck, lint, tests, and build before product-truth scanning.",
        ),
        BetaGateCommand(
            lane_id="docs_integrity",
            command_ref="command:docs.integrity",
            argv=python_cmd("scripts/verify_documentation_integrity.py"),
            purpose="Verify documentation links and indexes remain coherent.",
        ),
        BetaGateCommand(
            lane_id="security_redaction",
            command_ref="command:security.redaction-artifacts",
            argv=python_cmd("scripts/verify_security_redaction_artifacts.py"),
            purpose="Verify release-facing artifacts do not carry raw sensitive data.",
        ),
        BetaGateCommand(
            lane_id="product_truth",
            command_ref="command:product.truth",
            argv=python_cmd("scripts/verify_product_truth.py"),
            purpose="Reject public beta, production, or authority overclaims.",
        ),
        BetaGateCommand(
            lane_id="operational_maturity",
            command_ref="command:operational.maturity",
            argv=python_cmd("scripts/verify_operational_maturity.py"),
            purpose="Verify authority taxonomy and maturity posture.",
        ),
        BetaGateCommand(
            lane_id="openapi_contract",
            command_ref="command:openapi.contract",
            argv=python_cmd("scripts/verify_openapi_contract.py"),
            purpose="Verify the API contract and operation ids.",
        ),
        BetaGateCommand(
            lane_id="api_perimeter",
            command_ref="command:api.perimeter-lane",
            argv=python_cmd("scripts/verification/api_lane.py"),
            purpose="Verify UAA-P1-080 through UAA-P1-086 API perimeter guards.",
        ),
        BetaGateCommand(
            lane_id="gate_architecture",
            command_ref="command:gate.architecture",
            argv=python_cmd("scripts/verify_gate_architecture.py"),
            purpose="Verify Foundation Gate architecture and evaluator wiring.",
        ),
        BetaGateCommand(
            lane_id="release_lanes",
            command_ref="command:release.lanes",
            argv=python_cmd("scripts/verify_release_lanes.py", "--json"),
            purpose="Verify release verification lane definitions without executing release commands.",
        ),
        BetaGateCommand(
            lane_id="release_evidence_packet",
            command_ref="command:release.evidence-packet",
            argv=python_cmd("scripts/verify_release_evidence_packet.py"),
            purpose="Verify release evidence packet schema, template, and safe status semantics.",
        ),
        BetaGateCommand(
            lane_id="release_surface",
            command_ref="command:control-center.release-surface",
            argv=python_cmd("scripts/verify_control_center_release_surface.py"),
            purpose="Verify visible routes, release labels, and visual proof refs.",
        ),
        BetaGateCommand(
            lane_id="dogfood_live_loop",
            command_ref="command:dogfood.live-loop",
            argv=python_cmd("scripts/verify_dogfood_live_loop_acceptance.py"),
            purpose="Prove the Start Here to Trust local dogfood loop.",
        ),
        BetaGateCommand(
            lane_id="dogfood_private_harness",
            command_ref="command:dogfood.private-harness",
            argv=python_cmd("scripts/verify_fcc_dogfood_001_fourteen_day_private_harness.py"),
            purpose="Verify the private 14-day dogfood harness remains local/private and safe-ref only.",
        ),
        BetaGateCommand(
            lane_id="private_beta_readiness",
            command_ref="command:private-beta.readiness-gate",
            argv=python_cmd("scripts/verify_uaa_p1_078_private_beta_readiness_gate.py"),
            purpose="Verify private beta readiness remains local/private and blocked-authority explicit.",
        ),
        BetaGateCommand(
            lane_id="private_product_loop_trial",
            command_ref="command:private-product-loop.trial-script",
            argv=python_cmd("scripts/verify_product_loop_012_private_trial_script.py"),
            purpose="Verify the local/private product loop trial script and acceptance ledger posture.",
        ),
        BetaGateCommand(
            lane_id="private_trial_packet",
            command_ref="command:private-trial.packet",
            argv=python_cmd("scripts/verify_uaa_p1_087_2a_private_trial_packet.py"),
            purpose="Verify the UAA-P1-087.2a private trial packet remains local/private.",
        ),
        BetaGateCommand(
            lane_id="private_trial_ledger",
            command_ref="command:private-trial.acceptance-ledger",
            argv=python_cmd("scripts/verify_uaa_p1_087_2b_private_trial_acceptance_ledger.py"),
            purpose="Verify the UAA-P1-087.2b private trial acceptance ledger remains review-only.",
        ),
        BetaGateCommand(
            lane_id="private_trial_manual_review",
            command_ref="command:private-trial.manual-review",
            argv=python_cmd("scripts/verify_uaa_p1_087_2c_private_trial_manual_review_scaffold.py"),
            purpose="Verify the UAA-P1-087.2c manual review scaffold remains unanswered and safe.",
        ),
        BetaGateCommand(
            lane_id="web_runtime_authority",
            command_ref="command:web-runtime.authority",
            argv=python_cmd("scripts/verify_web_runtime_authority.py"),
            purpose="Verify WebAccessGateway, browser, provider, and subprocess authority boundaries.",
        ),
        BetaGateCommand(
            lane_id="authority_frontend_guard",
            command_ref="command:control-center.frontend-safety",
            argv=python_cmd("scripts/verify_control_center_frontend.py"),
            purpose="Verify Control Center has no fake mutation controls or unsafe frontend authority.",
        ),
        BetaGateCommand(
            lane_id="visual_proof",
            command_ref="command:control-center.visual-regression",
            argv=python_cmd("scripts/verify_control_center_visual_regression.py"),
            purpose="Verify checked-in redacted route and state visual baselines.",
        ),
        BetaGateCommand(
            lane_id="setup_assistant",
            command_ref="command:beta.setup-assistant",
            argv=python_cmd("scripts/verify_beta_02_setup_assistant_local_package.py"),
            purpose="Verify Setup Assistant and local package beta posture.",
        ),
        BetaGateCommand(
            lane_id="evidence_memory",
            command_ref="command:beta.evidence-memory",
            argv=python_cmd("scripts/verify_beta_06_evidence_memory_binding.py"),
            purpose="Verify Evidence and Memory bind to the same run, action, proof, and safe refs.",
        ),
        BetaGateCommand(
            lane_id="trust_authority",
            command_ref="command:beta.trust-authority",
            argv=python_cmd("scripts/verify_beta_07_trust_authority_map.py"),
            purpose="Verify Trust remains an authority map without granting broad authority.",
        ),
        BetaGateCommand(
            lane_id="web_evidence",
            command_ref="command:beta.web-evidence",
            argv=python_cmd("scripts/verify_beta_08_web_evidence_product_slice.py"),
            purpose="Verify Web Evidence remains WebAccessGateway-only and bounded.",
        ),
        BetaGateCommand(
            lane_id="provider_draft",
            command_ref="command:beta.provider-draft",
            argv=python_cmd("scripts/verify_beta_09_provider_draft_preview.py"),
            purpose="Verify provider draft preview remains exact-scoped and disabled by default.",
        ),
        BetaGateCommand(
            lane_id="connector_draft",
            command_ref="command:beta.connector-draft",
            argv=python_cmd("scripts/verify_beta_10_connector_draft_only.py"),
            purpose="Verify connector outputs remain draft-only safe refs.",
        ),
        BetaGateCommand(
            lane_id="workspace_spine",
            command_ref="command:beta.operator-workspace",
            argv=python_cmd("scripts/verify_beta_11_operator_workspace_spine.py"),
            purpose="Verify operator workspace posture remains read-only.",
        ),
        BetaGateCommand(
            lane_id="backend_api",
            command_ref="command:beta.backend-api",
            argv=python_cmd("scripts/verify_beta_12_backend_modularization_api.py"),
            purpose="Verify backend API modularization and route truth.",
        ),
        BetaGateCommand(
            lane_id="frontend_states",
            command_ref="command:beta.frontend-states",
            argv=python_cmd("scripts/verify_beta_13_frontend_loading_visual_proof.py"),
            purpose="Verify route-state grammar and visual proof.",
        ),
        BetaGateCommand(
            lane_id="foundation_gate",
            command_ref="command:foundation-gate.report-only",
            argv=python_cmd(
                "scripts/run_foundation_gate.py",
                "--command-mode",
                "report-only",
                "--no-write-latest",
            ),
            purpose="Run Foundation Gate report-only without writing latest artifacts.",
        ),
    ]


def build_live_visual_gate_commands() -> list[BetaGateCommand]:
    return [
        BetaGateCommand(
            lane_id=LIVE_VISUAL_LANE,
            command_ref="command:frontend.visual-check",
            argv=("make", "frontend-visual-check"),
            purpose="Run the explicit live Playwright visual comparison lane.",
            timeout_seconds=1200,
        ),
    ]


def validate_gate_commands(commands: list[BetaGateCommand]) -> list[str]:
    return _validate_commands(commands, allow_live_visual=False)


def validate_live_visual_gate_commands(commands: list[BetaGateCommand]) -> list[str]:
    failures = _validate_commands(commands, allow_live_visual=True)
    lane_ids = {command.lane_id for command in commands}
    if lane_ids != {LIVE_VISUAL_LANE}:
        failures.append("live visual QA gate must contain only the live visual lane")
    return failures


def _validate_commands(
    commands: list[BetaGateCommand],
    *,
    allow_live_visual: bool,
) -> list[str]:
    failures: list[str] = []
    lane_ids = [command.lane_id for command in commands]
    command_refs = [command.command_ref for command in commands]
    if not allow_live_visual:
        missing = sorted(REQUIRED_LANES.difference(lane_ids))
        if missing:
            failures.append(f"beta local QA gate missing lanes: {missing}")
    if len(lane_ids) != len(set(lane_ids)):
        failures.append("beta local QA gate lane ids must be unique")
    if len(command_refs) != len(set(command_refs)):
        failures.append("beta local QA gate command refs must be unique")
    for command in commands:
        if not command.argv:
            failures.append(f"{command.lane_id} has empty argv")
            continue
        joined = " ".join(command.argv).lower()
        for fragment in FORBIDDEN_ARG_FRAGMENTS:
            if fragment in joined:
                failures.append(
                    f"{command.lane_id} uses forbidden command fragment: {fragment}"
                )
        if command.argv[0] in {"sh", "bash", "zsh"}:
            failures.append(f"{command.lane_id} must not run through a shell")
        if command.required_for_beta is not True:
            failures.append(f"{command.lane_id} must be required for beta QA")
        if command.lane_id == LIVE_VISUAL_LANE and not allow_live_visual:
            failures.append("live Playwright visual checks must use --include-live-visual")
        for arg in command.argv:
            if str(ROOT) in arg:
                failures.append(f"{command.lane_id} must not list absolute local paths")
            if arg.startswith("/"):
                failures.append(f"{command.lane_id} must not list absolute paths")
    return failures


def redact_output(text: str) -> str:
    redacted = text.replace(str(ROOT), "<repo-root>")
    home = str(Path.home())
    if home and home != str(ROOT):
        redacted = redacted.replace(home, "<home>")
    return redacted


def bounded_failure_output(stdout: str, stderr: str) -> str:
    combined = "\n".join(part for part in [stdout, stderr] if part)
    redacted = redact_output(combined)
    lines = redacted.splitlines()
    if len(lines) > MAX_FAILURE_OUTPUT_LINES:
        omitted = len(lines) - MAX_FAILURE_OUTPUT_LINES
        lines = [
            f"... {omitted} earlier output lines omitted by beta QA gate ...",
            *lines[-MAX_FAILURE_OUTPUT_LINES:],
        ]
    return "\n".join(lines)


def run_commands(commands: list[BetaGateCommand]) -> list[str]:
    failures: list[str] = []
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    total = len(commands)
    for index, command in enumerate(commands, start=1):
        print(f"[{index}/{total}] {command.command_ref}: {command.purpose}", flush=True)
        started = time.perf_counter()
        try:
            result = subprocess.run(
                list(command.argv),
                cwd=ROOT,
                env=env,
                check=False,
                timeout=command.timeout_seconds,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - started
            failures.append(
                f"{command.command_ref} timed out after {command.timeout_seconds}s"
            )
            print(f"TIMEOUT {command.command_ref} ({elapsed:.1f}s)", flush=True)
            break
        elapsed = time.perf_counter() - started
        if result.returncode != 0:
            failures.append(
                f"{command.command_ref} failed with exit code {result.returncode}"
            )
            output = bounded_failure_output(result.stdout, result.stderr)
            if output:
                print(output, flush=True)
            print(f"FAIL {command.command_ref} ({elapsed:.1f}s)", flush=True)
            break
        print(f"OK {command.command_ref} ({elapsed:.1f}s)", flush=True)
    return failures


def format_command(command: BetaGateCommand) -> str:
    return f"{command.command_ref}\t{command.lane_id}\t{' '.join(command.argv)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local beta QA gate.")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the beta QA commands without running them.",
    )
    parser.add_argument(
        "--include-live-visual",
        action="store_true",
        help="Also run the explicit live Playwright visual comparison lane.",
    )
    args = parser.parse_args(argv)

    commands = build_beta_local_gate_commands()
    failures = validate_gate_commands(commands)
    live_visual_commands: list[BetaGateCommand] = []
    if args.include_live_visual:
        live_visual_commands = build_live_visual_gate_commands()
        failures.extend(validate_live_visual_gate_commands(live_visual_commands))
    run_commands_list = [*commands, *live_visual_commands]
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    if args.list:
        for command in run_commands_list:
            print(format_command(command))
        return 0
    failures = run_commands(run_commands_list)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("OK: local beta QA gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
