#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_078_PRIVATE_BETA_READINESS_GATE.md"
SCHEMA = ROOT / "docs/schemas/private_beta_readiness_gate.schema.json"
READINESS_MODULE = ROOT / "src/ultimate_ai_agent/core/readiness/private_beta.py"
READINESS_INIT = ROOT / "src/ultimate_ai_agent/core/readiness/__init__.py"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
FOCUSED_TEST = ROOT / "tests/test_uaa_p1_078_private_beta_readiness_gate.py"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"

REQUIRED_SURFACES = [
    "Today",
    "Morning Briefing",
    "Action Inbox",
    "Memory Review",
    "Evidence Timeline",
    "Chat/Plans Handoff",
    "Governed Code",
    "CRM-Lite Follow-Ups",
]
ACCEPTANCE_STATES = [
    "pass",
    "fail",
    "skipped",
    "blocked",
    "partial",
    "mock_only",
    "accepted_failure",
]
REQUIRED_REF_FIELDS = [
    "criterion_ref",
    "surface",
    "gate_state",
    "safe_summary",
    "evidence_refs",
    "required_contract_refs",
    "acceptance_refs",
    "missing_evidence_refs",
    "blocked_state_refs",
    "next_safe_action",
]
REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-public-beta",
    "blocked-state:no-public-distribution",
    "blocked-state:no-production-readiness-claim",
    "blocked-state:no-production-authority",
    "blocked-state:no-broad-autonomy",
    "blocked-state:no-connector-write",
    "blocked-state:no-provider-model-authority",
    "blocked-state:no-unrestricted-shell",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-remote-execution",
    "blocked-state:no-account-sync",
    "blocked-state:no-crm-write",
    "blocked-state:no-memory-write",
    "blocked-state:no-automatic-memory-write",
    "blocked-state:no-context-injection",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-action-execution",
    "blocked-state:no-code-apply-execution",
]
DENIED_FLAGS = [
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_readiness_claim_enabled",
    "production_authority_enabled",
    "broad_autonomy_enabled",
    "connector_write_enabled",
    "provider_model_authority_allowed",
    "unrestricted_shell_enabled",
    "shell_subprocess_execution_enabled",
    "remote_execution_enabled",
    "account_sync_enabled",
    "crm_write_enabled",
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "approval_grant_capture_enabled",
    "action_execution_enabled",
    "code_apply_execution_enabled",
]
FORBIDDEN_SNIPPETS = [
    "public beta is ready",
    "private beta is ready",
    "public beta launched",
    "production ready",
    "production-ready",
    "release-ready",
    "public release",
    "public distribution enabled",
    "connector writes enabled",
    "crm writes enabled",
    "account sync enabled",
    "code apply enabled",
    "unrestricted shell enabled",
    "remote execution enabled",
    "raw prompt",
    "raw response",
    "provider payload",
    "api key",
    "authorization",
    "password",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
]
FORBIDDEN_CLAIMS = [
    "public beta is ready",
    "private beta is ready",
    "public beta launched",
    "production ready",
    "production-ready",
    "release-ready",
    "public release",
    "public distribution enabled",
    "connector writes enabled",
    "crm writes enabled",
    "account sync enabled",
    "code apply enabled",
    "unrestricted shell enabled",
    "remote execution enabled",
]
FORBIDDEN_RUNTIME_CALLS = [
    "subprocess.run",
    "subprocess.Popen",
    "requests.",
    "httpx.",
    "openai.",
    "execute_action",
    "apply_execution_enabled=True",
    "memory_write(",
    "context_injection(",
    "connector.write",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _require_absent(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path).lower()
    for snippet in snippets:
        if snippet.lower() in text:
            failures.append(f"{path.relative_to(ROOT)} contains forbidden {snippet!r}")


def _extract(today: dict) -> dict:
    return {
        "private_beta_readiness_contract_ref": today[
            "private_beta_readiness_contract_ref"
        ],
        "private_beta_readiness_status": today["private_beta_readiness_status"],
        "private_beta_readiness_overall_state": today[
            "private_beta_readiness_overall_state"
        ],
        "private_beta_readiness_evidence_packet_ref": today[
            "private_beta_readiness_evidence_packet_ref"
        ],
        "private_beta_readiness_window_ref": today[
            "private_beta_readiness_window_ref"
        ],
        "private_beta_readiness_required_surfaces": today[
            "private_beta_readiness_required_surfaces"
        ],
        "private_beta_readiness_acceptance_states": today[
            "private_beta_readiness_acceptance_states"
        ],
        "private_beta_readiness_acceptance_state_definitions": today[
            "private_beta_readiness_acceptance_state_definitions"
        ],
        "private_beta_readiness_required_ref_fields": today[
            "private_beta_readiness_required_ref_fields"
        ],
        "private_beta_readiness_required_blocked_refs": today[
            "private_beta_readiness_required_blocked_refs"
        ],
        "private_beta_readiness_criterion_count": today[
            "private_beta_readiness_criterion_count"
        ],
        "private_beta_readiness_criteria": today[
            "private_beta_readiness_criteria"
        ],
        "private_beta_readiness_surface_bindings": today[
            "private_beta_readiness_surface_bindings"
        ],
        "private_beta_readiness_authority_posture": today[
            "private_beta_readiness_authority_posture"
        ],
        "private_beta_readiness_blocked_state_refs": today[
            "private_beta_readiness_blocked_state_refs"
        ],
        "private_beta_readiness_missing_evidence_refs": today[
            "private_beta_readiness_missing_evidence_refs"
        ],
        "private_beta_readiness_next_safe_action": today[
            "private_beta_readiness_next_safe_action"
        ],
        "private_beta_readiness_local_private_only": today[
            "private_beta_readiness_local_private_only"
        ],
        "private_beta_readiness_safe_refs_only": today[
            "private_beta_readiness_safe_refs_only"
        ],
        "private_beta_readiness_review_required": today[
            "private_beta_readiness_review_required"
        ],
        "private_beta_readiness_evidence_required": today[
            "private_beta_readiness_evidence_required"
        ],
        "private_beta_readiness_redaction_required": today[
            "private_beta_readiness_redaction_required"
        ],
        "private_beta_readiness_execution_authorized": today[
            "private_beta_readiness_execution_authorized"
        ],
    }


def _validate_live_contract(schema: dict, failures: list[str]) -> None:
    from pydantic import ValidationError

    from ultimate_ai_agent.core.readiness import (
        PRIVATE_BETA_READINESS_ACCEPTANCE_STATES,
        PRIVATE_BETA_READINESS_CONTRACT_REF,
        PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS,
        PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS,
        PRIVATE_BETA_READINESS_REQUIRED_SURFACES,
        PrivateBetaReadinessGate,
        build_private_beta_readiness_gate,
        private_beta_readiness_authority_posture,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="uaa-p1-078-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()
        inbox = repo.actions_inbox()

    contract = _extract(today)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda error: error.path)
    for error in errors:
        failures.append(f"live private beta-readiness schema error: {error.message}")

    if contract["private_beta_readiness_contract_ref"] != (
        PRIVATE_BETA_READINESS_CONTRACT_REF
    ):
        failures.append("live private beta-readiness contract ref drifted")
    if contract["private_beta_readiness_required_surfaces"] != (
        PRIVATE_BETA_READINESS_REQUIRED_SURFACES
    ):
        failures.append("live private beta-readiness surfaces drifted")
    if contract["private_beta_readiness_acceptance_states"] != (
        PRIVATE_BETA_READINESS_ACCEPTANCE_STATES
    ):
        failures.append("live private beta-readiness acceptance states drifted")
    if contract["private_beta_readiness_required_ref_fields"] != (
        PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS
    ):
        failures.append("live private beta-readiness ref fields drifted")
    if set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) - set(
        contract["private_beta_readiness_blocked_state_refs"]
    ):
        failures.append("live private beta-readiness blocked refs missing")
    if contract["private_beta_readiness_criterion_count"] != len(
        PRIVATE_BETA_READINESS_REQUIRED_SURFACES
    ):
        failures.append("live private beta-readiness criterion count drifted")
    if {
        criterion["surface"]
        for criterion in contract["private_beta_readiness_criteria"]
    } != set(PRIVATE_BETA_READINESS_REQUIRED_SURFACES):
        failures.append("live private beta-readiness criteria surfaces drifted")
    if contract["private_beta_readiness_authority_posture"] != (
        private_beta_readiness_authority_posture()
    ):
        failures.append("live private beta-readiness authority posture drifted")
    if contract["private_beta_readiness_execution_authorized"] is not False:
        failures.append("live private beta-readiness execution became authorized")

    gate = build_private_beta_readiness_gate()
    payload = gate.model_dump(mode="json")
    for denied_flag in DENIED_FLAGS:
        if payload[denied_flag] is not False:
            failures.append(f"gate enabled denied flag {denied_flag}")
        unsafe = dict(payload)
        unsafe[denied_flag] = True
        try:
            PrivateBetaReadinessGate(**unsafe)
        except ValidationError:
            pass
        else:
            failures.append(f"gate accepted denied flag {denied_flag}")

    timeline_item = next(
        (
            item
            for item in today["evidence_timeline"]
            if item["item_kind"] == "private_beta_readiness_gate_ref"
        ),
        None,
    )
    if timeline_item is None:
        failures.append("today evidence timeline missing private beta-readiness item")
    else:
        if timeline_item["history_answers"]["approved"]["status"] != "blocked":
            failures.append("private beta-readiness approval history is not blocked")
        if timeline_item["approval_ref_authority"] is not False:
            failures.append("private beta-readiness timeline grants approval authority")
        if timeline_item["rollback_execution_enabled"] is not False:
            failures.append("private beta-readiness timeline enables rollback")
        if set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) - set(
            timeline_item["blocked_states"]
        ):
            failures.append("private beta-readiness timeline missing blocked refs")

    if inbox["private_beta_readiness_contract_ref"] != (
        PRIVATE_BETA_READINESS_CONTRACT_REF
    ):
        failures.append("actions inbox missing private beta-readiness contract")

    serialized = json.dumps(today, sort_keys=True).lower()
    for snippet in FORBIDDEN_SNIPPETS:
        if snippet in serialized:
            failures.append(f"live today payload contains forbidden {snippet!r}")


def main() -> int:
    failures: list[str] = []
    schema = json.loads(_read(SCHEMA))
    Draft202012Validator.check_schema(schema)

    _validate_live_contract(schema, failures)

    _require(
        READINESS_MODULE,
        [
            "PRIVATE_BETA_READINESS_CONTRACT_REF",
            "PRIVATE_BETA_READINESS_ACCEPTANCE_STATES",
            "PrivateBetaReadinessCriterion",
            "PrivateBetaReadinessGate",
            "build_private_beta_readiness_gate",
            "private_beta_readiness_authority_posture",
            "private_beta_readiness_surface_bindings",
            "blocked-state:no-public-beta",
            "blocked-state:no-crm-write",
            "blocked-state:no-code-apply-execution",
        ],
        failures,
    )
    _require(READINESS_INIT, ["PrivateBetaReadinessGate"], failures)
    _require(
        FOUNDER_LOOP,
        [
            "_private_beta_readiness_gate_contract_payload",
            "private_beta_readiness_contract_ref",
            "private_beta_readiness_gate_ref",
            "PRIVATE_BETA_READINESS_CONTRACT_REF",
        ],
        failures,
    )
    _require(
        FRONTEND_TYPES,
        [
            "FounderLoopPrivateBetaReadinessCriterion",
            "private_beta_readiness_contract_ref",
            "private_beta_readiness_authority_posture",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "Private beta-readiness gate",
            "Beta-test criteria",
            "Beta-readiness action gate",
        ],
        failures,
    )
    _require(
        FRONTEND_MOCK,
        [
            "privateBetaReadinessContractRef",
            "privateBetaReadinessAcceptanceStates",
            "private_beta_readiness_gate_ref",
        ],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_private_beta_readiness_gate_defines_local_acceptance_states",
            "test_founder_loop_surfaces_private_beta_readiness_without_authority",
        ],
        failures,
    )
    _require(
        STORAGE_TEST,
        ["PRIVATE_BETA_READINESS_CONTRACT_REF", "private_beta_readiness_gate_ref"],
        failures,
    )
    _require(
        API_TEST,
        ["PRIVATE_BETA_READINESS_CONTRACT_REF", "private_beta_readiness_criteria"],
        failures,
    )
    _require(APP_TEST, ["Private beta-readiness gate", "CRM-Lite Follow-Ups"], failures)
    _require(
        CONTRACT_DOC,
        [
            "UAA-P1-078",
            "pass, fail, skipped, blocked, partial, mock-only, and accepted-failure",
            "Public beta remains blocked",
            "docs/schemas/private_beta_readiness_gate.schema.json",
        ],
        failures,
    )

    for path in [FRONTEND_PANEL, FRONTEND_MOCK, CONTRACT_DOC]:
        _require_absent(path, FORBIDDEN_CLAIMS, failures)
    _require_absent(READINESS_MODULE, FORBIDDEN_RUNTIME_CALLS, failures)

    if failures:
        print("UAA-P1-078 private beta-readiness gate verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("UAA-P1-078 private beta-readiness gate verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
