#!/usr/bin/env python3
"""Release verification lane manifest and validator.

This script is inspection-only. It defines release-candidate verification lanes
and their commands, but it does not execute those commands.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LANE_SCHEMA_VERSION = "uaa_release_verification_lanes.v1"
LANE_TASK_REF = "UAA-P1-013"
REQUIRED_LANE_IDS = {
    "docs",
    "openapi",
    "api-safety",
    "security-redaction",
    "local-model-e2e",
    "durability",
    "frontend",
    "performance",
}
STATUS_SEMANTICS = {
    "pass": "All required commands in the lane completed successfully and produced only safe summaries or safe refs.",
    "fail": "One or more required commands failed; release promotion or scope expansion is blocked until fixed.",
    "skipped": "A prerequisite was unavailable and the lane explicitly defines a safe skipped state with reason code.",
    "blocked": "The lane cannot run or cannot pass because a required gate, approval, or prerequisite is missing.",
    "accepted_failure": "A known failure is allowed only with reviewer, expiry, evidence ref, and release-packet acceptance.",
}
REPORT_SAFETY = {
    "raw_prompt_included": False,
    "raw_response_included": False,
    "raw_provider_payload_included": False,
    "raw_path_included": False,
    "raw_log_included": False,
    "username_included": False,
    "hostname_included": False,
    "serial_included": False,
    "environment_dump_included": False,
    "credential_material_included": False,
}


@dataclass(frozen=True)
class LaneCommand:
    command_ref: str
    argv: tuple[str, ...]
    purpose: str
    required: bool = True
    env: dict[str, str] = field(default_factory=dict)
    report_ref: str | None = None

    def display(self) -> str:
        env_prefix = " ".join(f"{key}={value}" for key, value in sorted(self.env.items()))
        command = " ".join(self.argv)
        return f"{env_prefix} {command}".strip()


@dataclass(frozen=True)
class ReleaseLane:
    lane_id: str
    name: str
    owner: str
    purpose: str
    commands: tuple[LaneCommand, ...]
    required_for_release_candidate: bool
    skipped_policy: str
    blocked_policy: str
    accepted_failure_policy: str
    evidence_refs: tuple[str, ...]


def release_lanes() -> tuple[ReleaseLane, ...]:
    py = ".venv/bin/python"
    return (
        ReleaseLane(
            lane_id="docs",
            name="Documentation Integrity",
            owner="release-review",
            purpose="Prove active docs, roadmap, Kanban, baseline, and release-facing claims stay consistent.",
            commands=(
                LaneCommand(
                    command_ref="command:docs.integrity",
                    argv=(py, "scripts/verify_documentation_integrity.py"),
                    purpose="Validate documentation currentness, safety language, and canonical links.",
                    report_ref="report:docs-integrity:console-summary",
                ),
            ),
            required_for_release_candidate=True,
            skipped_policy="Not skippable for a release candidate.",
            blocked_policy="Blocked when canonical docs, roadmap, or Kanban currentness cannot be verified.",
            accepted_failure_policy="No accepted failures without a release evidence packet ref and owner sign-off.",
            evidence_refs=("docs/DOCUMENTATION_INDEX.md", "docs/canonical/CANONICAL_DOC_MAP.md"),
        ),
        ReleaseLane(
            lane_id="openapi",
            name="OpenAPI Contract",
            owner="api-review",
            purpose="Prove route count, operation ids, side-effect classes, and public route contract remain stable.",
            commands=(
                LaneCommand(
                    command_ref="command:openapi.contract",
                    argv=(py, "scripts/verify_openapi_contract.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Validate the generated OpenAPI contract.",
                    report_ref="report:openapi:console-summary",
                ),
                LaneCommand(
                    command_ref="command:api.manifest.tests",
                    argv=(py, "-m", "pytest", "tests/test_api_manifest.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Validate API manifest route metadata and safe static cache behavior.",
                ),
            ),
            required_for_release_candidate=True,
            skipped_policy="Not skippable for a release candidate.",
            blocked_policy="Blocked by route-count drift, missing operation ids, or unsafe route metadata.",
            accepted_failure_policy="No accepted failures for route-contract drift.",
            evidence_refs=("docs/api/openapi_contract.md", "docs/api/route_inventory.md"),
        ),
        ReleaseLane(
            lane_id="api-safety",
            name="API Safety",
            owner="api-review",
            purpose="Prove API errors and visible Control Center routes remain safe, bounded, and non-authoritative.",
            commands=(
                LaneCommand(
                    command_ref="command:api.safe-errors",
                    argv=(py, "-m", "pytest", "tests/test_api_safe_exception_messages.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify safe exception and error-message behavior.",
                ),
                LaneCommand(
                    command_ref="command:control-center.api-routes",
                    argv=(py, "-m", "pytest", "tests/test_control_center_api_routes.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify Control Center route contracts remain read-only or validation-only.",
                ),
            ),
            required_for_release_candidate=True,
            skipped_policy="Not skippable for a release candidate.",
            blocked_policy="Blocked by unsafe error output, missing route metadata, or side-effect classification drift.",
            accepted_failure_policy="No accepted failures for unsafe API output.",
            evidence_refs=("docs/control_center/OPERATOR_SHELL_GAP_MAP.md",),
        ),
        ReleaseLane(
            lane_id="security-redaction",
            name="Security and Redaction",
            owner="security-review",
            purpose="Prove secret-like content, raw evidence, unsafe logs, and redaction regressions stay blocked.",
            commands=(
                LaneCommand(
                    command_ref="command:secret-broker.redaction",
                    argv=(py, "-m", "pytest", "tests/test_secret_broker_redaction.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify secret broker redaction behavior.",
                ),
                LaneCommand(
                    command_ref="command:file-secret.blocking",
                    argv=(py, "-m", "pytest", "tests/test_file_secret_blocking.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify workspace diff and preview secret-like blocking.",
                ),
                LaneCommand(
                    command_ref="command:foundation-gate.secret-hygiene",
                    argv=(py, "-m", "pytest", "tests/test_foundation_gate_secret_hygiene.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify Foundation Gate evidence remains secret-clean.",
                ),
            ),
            required_for_release_candidate=True,
            skipped_policy="Not skippable for a release candidate.",
            blocked_policy="Blocked by raw prompt, raw response, raw path, raw log, or credential-like output.",
            accepted_failure_policy="No accepted failures for credential or private-data exposure.",
            evidence_refs=("SECURITY.md", "docs/security/SECURITY_TRIAGE_RUNBOOK.md"),
        ),
        ReleaseLane(
            lane_id="local-model-e2e",
            name="Local Model E2E",
            owner="local-model-review",
            purpose="Prove the local GGUF, llama.cpp, UAA /v1, and OpenWebUI shell lane reports real or honest skipped/blocked state.",
            commands=(
                LaneCommand(
                    command_ref="command:local-model.release-gate",
                    argv=(py, "-m", "pytest", "tests/test_m166_production_release_gate.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify M166 local model release gate behavior.",
                ),
                LaneCommand(
                    command_ref="command:local-model.hardening",
                    argv=(py, "-m", "pytest", "tests/test_m167_live_model_hardening.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify M167 local model hardening and tuning evidence behavior.",
                ),
                LaneCommand(
                    command_ref="command:openwebui.local-gateway",
                    argv=(py, "-m", "pytest", "tests/test_m151_openwebui_local_gateway_api.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify local OpenWebUI shell compatibility with UAA /v1 gateway.",
                ),
            ),
            required_for_release_candidate=True,
            skipped_policy="Live hardware or model prerequisites may be skipped only when the harness reports skipped with reason code.",
            blocked_policy="Blocked when reviewed safe refs, approved model refs, or local-only auth prerequisites are missing.",
            accepted_failure_policy="Accepted failures require reviewer ref, hardware profile, expiry, and release evidence packet entry.",
            evidence_refs=("docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md",),
        ),
        ReleaseLane(
            lane_id="durability",
            name="Durability",
            owner="runtime-state-review",
            purpose="Prove run state, event ledger, receipts, idempotency, and atomic file behavior remain restart-safe.",
            commands=(
                LaneCommand(
                    command_ref="command:durable.state-machine",
                    argv=(py, "-m", "pytest", "tests/test_execution_state_machine_safety.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify durable run transition and replay safety contracts.",
                ),
                LaneCommand(
                    command_ref="command:event-ledger.append-only",
                    argv=(py, "-m", "pytest", "tests/test_event_ledger_append_only.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify append-only ledger and receipt behavior.",
                ),
                LaneCommand(
                    command_ref="command:file.atomic-writes",
                    argv=(py, "-m", "pytest", "tests/test_file_atomic_writes.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify atomic local write behavior.",
                ),
                LaneCommand(
                    command_ref="command:backup-restore.verify",
                    argv=(py, "scripts/verify_backup_restore.py"),
                    purpose="Verify backup minimum set integrity and offline restore behavior with safe refs only.",
                    report_ref="report:backup-restore:console-summary",
                ),
            ),
            required_for_release_candidate=True,
            skipped_policy="Not skippable for local durable-state release candidates.",
            blocked_policy="Blocked by corruption, duplicate mutation, missing idempotency, unreceipted mutation, missing minimum backup set, or failed offline restore verification.",
            accepted_failure_policy="No accepted failures for corruption or duplicate mutation protection.",
            evidence_refs=(
                "docs/execution/EXECUTION_STATE_MACHINE.md",
                "docs/production/BACKUP_RESTORE_VERIFICATION.md",
            ),
        ),
        ReleaseLane(
            lane_id="frontend",
            name="Control Center Frontend",
            owner="operator-shell-review",
            purpose="Prove Control Center UI safety, browser smoke readiness, and frontend checks remain truthful.",
            commands=(
                LaneCommand(
                    command_ref="command:frontend.check",
                    argv=("make", "frontend-check"),
                    purpose="Run Control Center typecheck, lint, tests, and build through the existing Make target.",
                ),
                LaneCommand(
                    command_ref="command:frontend.safety",
                    argv=(py, "scripts/verify_control_center_frontend.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify frontend safety and no hidden authority.",
                ),
                LaneCommand(
                    command_ref="command:frontend.browser-smoke",
                    argv=(py, "scripts/verify_control_center_browser_smoke_readiness.py"),
                    env={"PYTHONPATH": "src"},
                    purpose="Verify browser smoke readiness fixtures and accessible states.",
                ),
            ),
            required_for_release_candidate=True,
            skipped_policy="Can be skipped only in split CI when an equivalent required frontend job is referenced.",
            blocked_policy="Blocked by hidden authority, raw JSON primary UI, inaccessible failure state, or failed frontend checks.",
            accepted_failure_policy="Accepted frontend failures require issue ref, owner, expiry, and release evidence packet entry.",
            evidence_refs=("docs/control_center/OPERATOR_SHELL_GAP_MAP.md",),
        ),
        ReleaseLane(
            lane_id="performance",
            name="Performance",
            owner="release-review",
            purpose="Prove p50/p95 latency budgets and Foundation Gate latency evidence remain visible and safe.",
            commands=(
                LaneCommand(
                    command_ref="command:performance.benchmark",
                    argv=(py, "scripts/benchmark_foundation_gate.py"),
                    purpose="Generate release latency baseline, regression, and hot-path profile reports.",
                    report_ref="reports/performance/latest_release_latency_baseline.json",
                ),
                LaneCommand(
                    command_ref="command:performance.latency-gate",
                    argv=(py, "scripts/check_foundation_gate_latency.py"),
                    purpose="Fail required path budget regressions and unsafe authority caching/bypass flags.",
                    report_ref="reports/performance/latest_performance_regression_report.json",
                ),
                LaneCommand(
                    command_ref="command:foundation-gate.report-only",
                    argv=(py, "scripts/run_foundation_gate.py", "--command-mode", "report-only"),
                    purpose="Generate Foundation Gate report with latency gate summary.",
                    report_ref="reports/foundation_gate/latest_foundation_gate_report.json",
                ),
            ),
            required_for_release_candidate=True,
            skipped_policy="Optional frontend timing prerequisites may be skipped only when visible with reason code.",
            blocked_policy="Blocked by required latency failures, missing reports, or authority bypass/caching.",
            accepted_failure_policy="Accepted latency failures require release evidence packet entry with expiry and owner.",
            evidence_refs=("docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md",),
        ),
    )


def _lane_to_dict(lane: ReleaseLane) -> dict[str, Any]:
    data = asdict(lane)
    data["commands"] = [
        {
            **asdict(command),
            "argv": list(command.argv),
            "display": command.display(),
        }
        for command in lane.commands
    ]
    data["evidence_refs"] = list(lane.evidence_refs)
    return data


def build_release_lane_manifest() -> dict[str, Any]:
    lanes = release_lanes()
    failures = validate_release_lane_definitions(lanes)
    definition_status = "pass" if not failures else "fail"
    return {
        "schema_version": LANE_SCHEMA_VERSION,
        "task_ref": LANE_TASK_REF,
        "overall_status": f"definition_{definition_status}",
        "definition_status": definition_status,
        "command_execution_status": "not_executed",
        "status_semantics": STATUS_SEMANTICS,
        "accepted_failures": [],
        "validation_failures": failures,
        "lane_count": len(lanes),
        "lanes": [_lane_to_dict(lane) for lane in lanes],
        "report_safety": REPORT_SAFETY,
        "non_goals": [
            "does not execute commands",
            "does not grant production authority",
            "does not claim public distribution readiness",
            "does not record raw prompts, responses, provider payloads, paths, logs, environment dumps, or credentials",
        ],
        "safe_summary": (
            "Release lane definitions are validated by this manifest; lane commands are not executed here."
        ),
    }


def validate_release_lane_definitions(
    lanes: tuple[ReleaseLane, ...] | list[ReleaseLane] | None = None,
) -> list[str]:
    lanes = tuple(release_lanes() if lanes is None else lanes)
    failures: list[str] = []
    lane_ids = {lane.lane_id for lane in lanes}
    missing = sorted(REQUIRED_LANE_IDS - lane_ids)
    extra = sorted(lane_ids - REQUIRED_LANE_IDS)
    for lane_id in missing:
        failures.append(f"missing release verification lane: {lane_id}")
    for lane_id in extra:
        failures.append(f"unknown release verification lane: {lane_id}")
    if len(lane_ids) != len(lanes):
        failures.append("release verification lane ids must be unique")
    for status in ("pass", "fail", "skipped", "blocked", "accepted_failure"):
        if status not in STATUS_SEMANTICS or not STATUS_SEMANTICS[status]:
            failures.append(f"missing release lane status semantics: {status}")
    for lane in lanes:
        if not lane.commands:
            failures.append(f"{lane.lane_id} lane must define at least one command")
        for command in lane.commands:
            if not command.command_ref.startswith("command:"):
                failures.append(f"{lane.lane_id} command ref must start with command:")
            if not command.argv:
                failures.append(f"{lane.lane_id} command must define argv")
            if any(str(token).startswith("/") for token in command.argv):
                failures.append(f"{lane.lane_id} command must not record absolute paths")
            if any("/Users/" in str(token) or "\\Users\\" in str(token) for token in command.argv):
                failures.append(f"{lane.lane_id} command must not record user paths")
            if any(key != "PYTHONPATH" or value != "src" for key, value in command.env.items()):
                failures.append(f"{lane.lane_id} command env must be safe and repo-relative")
        for field_name in (
            "skipped_policy",
            "blocked_policy",
            "accepted_failure_policy",
        ):
            if not getattr(lane, field_name):
                failures.append(f"{lane.lane_id} lane missing {field_name}")
        if not lane.evidence_refs:
            failures.append(f"{lane.lane_id} lane must define evidence refs")
    return failures


def print_human_manifest(manifest: dict[str, Any]) -> None:
    print("Ultimate AI Agent release verification lanes")
    print(f"Schema: {manifest['schema_version']}")
    print(f"Task: {manifest['task_ref']}")
    print(f"Overall status: {manifest['overall_status']}")
    print("Status semantics:")
    for status, meaning in manifest["status_semantics"].items():
        print(f"- {status}: {meaning}")
    print("Lanes:")
    for lane in manifest["lanes"]:
        print(f"- {lane['lane_id']}: {lane['name']}")
        print(f"  Owner: {lane['owner']}")
        print(f"  Purpose: {lane['purpose']}")
        print(f"  Skipped: {lane['skipped_policy']}")
        print(f"  Blocked: {lane['blocked_policy']}")
        print(f"  Accepted failure: {lane['accepted_failure_policy']}")
        for command in lane["commands"]:
            print(f"  - {command['command_ref']}: {command['display']}")
    if manifest["validation_failures"]:
        print("Validation failures:")
        for failure in manifest["validation_failures"]:
            print(f"- {failure}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate release verification lane definitions.")
    parser.add_argument("--json", action="store_true", help="Print the lane manifest as JSON.")
    args = parser.parse_args(argv)
    manifest = build_release_lane_manifest()
    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print_human_manifest(manifest)
    return 0 if manifest["definition_status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
