#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_073_PLANS_ACTION_ENVELOPES.md"
SCHEMA = ROOT / "docs/schemas/plans_action_envelopes.schema.json"
ACTION_ENVELOPES = ROOT / "src/ultimate_ai_agent/core/planning/action_envelopes.py"
PLANNING_INIT = ROOT / "src/ultimate_ai_agent/core/planning/__init__.py"
STORAGE_INIT = ROOT / "src/ultimate_ai_agent/core/storage/__init__.py"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
FOCUSED_TEST = ROOT / "tests/test_uaa_p1_073_plans_action_envelopes.py"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"

REVIEW_ACTIONS = ["approve", "edit", "reject", "defer"]
REQUIRED_REF_FIELDS = [
    "action_envelope_ref",
    "source_plan_ref",
    "scope_ref",
    "side_effect_class",
    "risk_class",
    "approval_requirement_ref",
    "review_posture_refs",
    "evidence_refs",
    "expected_receipt_refs",
    "idempotency_key_ref",
    "expires_at",
    "rollback_ref",
    "safe_disable_ref",
    "blocked_state_refs",
]
REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-action-execution",
    "blocked-state:no-tool-execution",
    "blocked-state:no-workflow-execution",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:approval-refs-identifiers-only",
    "blocked-state:no-connector-runtime",
    "blocked-state:no-connector-write",
    "blocked-state:no-browser-automation",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-model-provider-authority",
    "blocked-state:no-public-beta-or-distribution",
    "blocked-state:no-production-authority",
]
DENIED_POSTURE_FLAGS = [
    "approval_ref_authority",
    "approval_grant_capture_enabled",
    "action_execution_enabled",
    "state_change_enabled",
    "tool_execution_enabled",
    "workflow_execution_enabled",
    "browser_execution_enabled",
    "connector_runtime_enabled",
    "connector_write_enabled",
    "shell_subprocess_execution_enabled",
    "model_provider_authority_allowed",
    "memory_write_authorized",
    "context_injection_authorized",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]
FORBIDDEN_SNIPPETS = [
    "raw_prompt",
    "raw_response",
    "provider_payload",
    "api_key",
    "authorization",
    "cookie",
    "password",
    "private_key",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
]
FORBIDDEN_RUNTIME_CALLS = [
    "subprocess.run",
    "subprocess.Popen",
    "requests.",
    "httpx.",
    "openai.",
    "connector.write",
    "approval_authority.grant",
    "execute_action",
]
OLD_MISSING_MARKERS = [
    "contract-ref:plans-action-envelope-missing",
    "blocked_until_uaa_p1_073",
    "partial_action_envelope_contract_missing",
    "partial_until_action_envelopes",
    "no_plan_execution_from_evidence_timeline",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _require_absent(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet in text:
            failures.append(f"{path.relative_to(ROOT)} contains forbidden {snippet!r}")


def _extract(today: dict, inbox: dict) -> dict:
    return {
        "plans_action_envelope_contract_ref": today[
            "plans_action_envelope_contract_ref"
        ],
        "plans_action_envelope_review_postures": today[
            "plans_action_envelope_review_postures"
        ],
        "plans_action_envelope_required_ref_fields": today[
            "plans_action_envelope_required_ref_fields"
        ],
        "plans_action_envelope_required_blocked_refs": today[
            "plans_action_envelope_required_blocked_refs"
        ],
        "plans_action_envelope_surface_bindings": today[
            "plans_action_envelope_surface_bindings"
        ],
        "plans_action_envelope_authority_posture": today[
            "plans_action_envelope_authority_posture"
        ],
        "plans_action_envelope_status": today["plans_action_envelope_status"],
        "plan_action_state": today["plan_action_state"],
        "plans": [
            {
                "action_envelope_contract_ref": plan[
                    "action_envelope_contract_ref"
                ],
                "action_envelope_ref": plan["action_envelope_ref"],
                "scope_ref": plan["scope_ref"],
                "approval_requirement_ref": plan["approval_requirement_ref"],
                "review_actions": plan["review_actions"],
                "expected_receipt_refs": plan["expected_receipt_refs"],
                "idempotency_key_ref": plan["idempotency_key_ref"],
                "rollback_ref": plan["rollback_ref"],
                "safe_disable_ref": plan["safe_disable_ref"],
                "blocked_state_refs": plan["blocked_state_refs"],
                "action_execution_enabled": plan["action_execution_enabled"],
                "approval_grant_capture_enabled": plan[
                    "approval_grant_capture_enabled"
                ],
                "raw_content_included": plan["raw_content_included"],
            }
            for plan in today["plans"]
        ],
        "actions": [
            {
                "action_envelope_contract_ref": action[
                    "action_envelope_contract_ref"
                ],
                "action_envelope_ref": action["action_envelope_ref"],
                "action_scope_ref": action["action_scope_ref"],
                "action_approval_requirement_ref": action[
                    "action_approval_requirement_ref"
                ],
                "action_review_actions": action["action_review_actions"],
                "action_expected_receipt_refs": action["action_expected_receipt_refs"],
                "action_rollback_ref": action["action_rollback_ref"],
                "action_safe_disable_ref": action["action_safe_disable_ref"],
                "action_blocked_state_refs": action["action_blocked_state_refs"],
                "action_envelope_execution_enabled": action[
                    "action_envelope_execution_enabled"
                ],
                "action_envelope_grant_capture_enabled": action[
                    "action_envelope_grant_capture_enabled"
                ],
                "action_envelope_raw_content_included": action[
                    "action_envelope_raw_content_included"
                ],
            }
            for action in inbox["items"]
        ],
    }


def _validate_live_contract(schema: dict, failures: list[str]) -> None:
    from pydantic import ValidationError

    from ultimate_ai_agent.core.planning.action_envelopes import (
        PLANS_ACTION_ENVELOPE_CONTRACT_REF,
        PLANS_ACTION_ENVELOPE_REQUIRED_BLOCKED_REFS,
        PLANS_ACTION_ENVELOPE_REQUIRED_REF_FIELDS,
        PlanActionEnvelope,
        build_plan_action_envelope,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="uaa-p1-073-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()
        inbox = repo.actions_inbox()

    contract = _extract(today, inbox)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda error: error.path)
    for error in errors:
        failures.append(f"live Plans Action envelope schema error: {error.message}")

    if contract["plans_action_envelope_contract_ref"] != (
        PLANS_ACTION_ENVELOPE_CONTRACT_REF
    ):
        failures.append("live Plans Action envelope contract ref drifted")
    if contract["plans_action_envelope_required_ref_fields"] != (
        PLANS_ACTION_ENVELOPE_REQUIRED_REF_FIELDS
    ):
        failures.append("live Plans Action envelope required fields drifted")
    if contract["plans_action_envelope_required_blocked_refs"] != (
        PLANS_ACTION_ENVELOPE_REQUIRED_BLOCKED_REFS
    ):
        failures.append("live Plans Action envelope blockers drifted")
    if [
        row["review_action"]
        for row in contract["plans_action_envelope_review_postures"]
    ] != REVIEW_ACTIONS:
        failures.append("live Plans Action envelope review actions drifted")

    posture = contract["plans_action_envelope_authority_posture"]
    if posture.get("safe_refs_only") is not True:
        failures.append("Plans Action envelope posture is not safe-ref-only")
    if posture.get("exact_scope_required") is not True:
        failures.append("Plans Action envelope posture does not require exact scope")
    if posture.get("approval_required_before_mutation") is not True:
        failures.append("Plans Action envelope posture does not require approval")
    for flag in DENIED_POSTURE_FLAGS:
        if posture.get(flag) is not False:
            failures.append(f"Plans Action envelope posture has unsafe {flag}")

    serialized = json.dumps(contract, sort_keys=True).lower()
    for forbidden in FORBIDDEN_SNIPPETS:
        if forbidden in serialized:
            failures.append(f"live Plans Action envelope contract contains {forbidden}")

    for plan in contract["plans"]:
        if set(REQUIRED_BLOCKED_REFS) - set(plan["blocked_state_refs"]):
            failures.append(f"{plan['action_envelope_ref']} missing blocked refs")
        if not plan["expected_receipt_refs"]:
            failures.append(f"{plan['action_envelope_ref']} missing receipt refs")
        if not plan["rollback_ref"]:
            failures.append(f"{plan['action_envelope_ref']} missing rollback ref")
        if not plan["safe_disable_ref"]:
            failures.append(f"{plan['action_envelope_ref']} missing safe-disable ref")
        if plan["action_execution_enabled"] is not False:
            failures.append(f"{plan['action_envelope_ref']} enables execution")
        if plan["approval_grant_capture_enabled"] is not False:
            failures.append(f"{plan['action_envelope_ref']} enables grant capture")
        if plan["raw_content_included"] is not False:
            failures.append(f"{plan['action_envelope_ref']} includes raw content")

    for action in contract["actions"]:
        if set(REQUIRED_BLOCKED_REFS) - set(action["action_blocked_state_refs"]):
            failures.append(f"{action['action_envelope_ref']} missing blocked refs")
        if not action["action_expected_receipt_refs"]:
            failures.append(f"{action['action_envelope_ref']} missing receipt refs")
        if not action["action_rollback_ref"]:
            failures.append(f"{action['action_envelope_ref']} missing rollback ref")
        if not action["action_safe_disable_ref"]:
            failures.append(f"{action['action_envelope_ref']} missing safe-disable ref")
        if action["action_envelope_execution_enabled"] is not False:
            failures.append(f"{action['action_envelope_ref']} enables execution")
        if action["action_envelope_grant_capture_enabled"] is not False:
            failures.append(f"{action['action_envelope_ref']} enables grant capture")
        if action["action_envelope_raw_content_included"] is not False:
            failures.append(f"{action['action_envelope_ref']} includes raw content")

    envelope = build_plan_action_envelope(
        source_plan_ref="plan-summary:verifier",
        title="Verifier envelope",
        safe_summary="Safe verifier envelope.",
        evidence_refs=["evidence-ref:plans-action-envelope:verifier"],
    )
    for flag in [
        "approval_ref_authority",
        "approval_grant_capture_enabled",
        "action_execution_enabled",
        "tool_execution_enabled",
        "workflow_execution_enabled",
        "browser_execution_enabled",
        "connector_runtime_enabled",
        "connector_write_enabled",
        "shell_subprocess_execution_enabled",
        "model_provider_authority_allowed",
        "raw_content_included",
    ]:
        payload = envelope.model_dump(mode="json")
        payload[flag] = True
        try:
            PlanActionEnvelope(**payload)
        except ValidationError:
            continue
        failures.append(f"PlanActionEnvelope accepted unsafe {flag}=true")

    for unsafe_summary in [
        "raw prompt material",
        "raw response material",
        "provider payload material",
        "account identifier material",
    ]:
        try:
            build_plan_action_envelope(
                source_plan_ref="plan-summary:unsafe",
                title="Unsafe envelope",
                safe_summary=unsafe_summary,
                evidence_refs=["evidence-ref:plans-action-envelope:unsafe"],
            )
        except ValidationError:
            continue
        failures.append(f"PlanActionEnvelope accepted unsafe summary {unsafe_summary}")

    timeline_kinds = {item["item_kind"] for item in today["evidence_timeline"]}
    if "plan_action_envelope_ref" not in timeline_kinds:
        failures.append("Evidence Timeline missing plan_action_envelope_ref item")


def main() -> int:
    failures: list[str] = []
    schema = json.loads(_read(SCHEMA))

    required_snippets = [
        "contract-ref:plans-action-envelope:v1",
        "approve",
        "edit",
        "reject",
        "defer",
        "blocked-state:no-action-execution",
        "blocked-state:no-tool-execution",
        "blocked-state:no-workflow-execution",
        "blocked-state:no-approval-grant-capture",
        "blocked-state:no-connector-runtime",
        "blocked-state:no-browser-automation",
        "expected_receipt_refs",
        "rollback_ref",
        "safe_disable_ref",
        "approval_grant_capture_enabled",
        "action_execution_enabled",
    ]
    _require(
        ACTION_ENVELOPES,
        [
            "PLANS_ACTION_ENVELOPE_CONTRACT_REF",
            "PlanActionEnvelope",
            "build_plan_action_envelope",
            "UNSAFE_ACTION_ENVELOPE_TEXT_FRAGMENTS",
        ],
        failures,
    )
    _require(
        FOUNDER_LOOP,
        ["PLANS_ACTION_ENVELOPE_CONTRACT_REF", "plans_action_envelope_status"],
        failures,
    )
    _require(
        FRONTEND_TYPES,
        ["plans_action_envelope_contract_ref", "action_envelope_contract_ref"],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        ["Action envelope contract", "action_envelope_contract_ref"],
        failures,
    )
    _require(FRONTEND_MOCK, required_snippets[:2], failures)
    _require(
        FOCUSED_TEST,
        ["PLANS_ACTION_ENVELOPE_CONTRACT_REF", "approve"],
        failures,
    )
    _require(
        STORAGE_TEST,
        ["PLANS_ACTION_ENVELOPE_CONTRACT_REF", "approve"],
        failures,
    )
    _require(
        API_TEST,
        ["PLANS_ACTION_ENVELOPE_CONTRACT_REF", "approve"],
        failures,
    )
    _require(APP_TEST, required_snippets[:2], failures)
    _require(
        PLANNING_INIT,
        ["PLANS_ACTION_ENVELOPE_CONTRACT_REF", "PlanActionEnvelope"],
        failures,
    )
    _require(STORAGE_INIT, ["PLANS_ACTION_ENVELOPE_CONTRACT_REF"], failures)
    _require(SCHEMA, ["plans_action_envelope_contract_ref"], failures)
    _require(CONTRACT_DOC, required_snippets, failures)

    for path in [
        CONTRACT_DOC,
        FOUNDER_LOOP,
        FRONTEND_TYPES,
        FRONTEND_PANEL,
        FRONTEND_MOCK,
        FOCUSED_TEST,
        STORAGE_TEST,
        API_TEST,
        APP_TEST,
    ]:
        _require_absent(path, OLD_MISSING_MARKERS, failures)

    _require_absent(ACTION_ENVELOPES, FORBIDDEN_RUNTIME_CALLS, failures)
    _validate_live_contract(schema, failures)

    if failures:
        for failure in failures:
            print(f"[UAA-P1-073 verifier] {failure}")
        return 1

    print("[UAA-P1-073 verifier] Plans Action envelope contract checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
