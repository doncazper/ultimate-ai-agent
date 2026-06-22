#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md"
SCHEMA = ROOT / "docs/schemas/governed_code_workbench.schema.json"
CODE_WORKBENCH = ROOT / "src/ultimate_ai_agent/core/code/workbench.py"
CODE_INIT = ROOT / "src/ultimate_ai_agent/core/code/__init__.py"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
FOCUSED_TEST = ROOT / "tests/test_uaa_p1_075_governed_code_workbench.py"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"

REQUIRED_REF_FIELDS = [
    "proposal_ref",
    "repo_scope_ref",
    "safe_diff_summary_ref",
    "validation_plan_ref",
    "validation_result_refs",
    "approval_requirement_ref",
    "expected_apply_receipt_ref",
    "expected_rollback_receipt_ref",
    "evidence_refs",
    "idempotency_key_ref",
    "blocked_state_refs",
]
REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-unapproved-mutation",
    "blocked-state:no-apply-execution",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-unrestricted-shell",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-remote-execution",
    "blocked-state:no-broad-coding-agent-autonomy",
    "blocked-state:no-provider-sdk-call",
    "blocked-state:no-web-fetch",
    "blocked-state:no-connector-write",
    "blocked-state:no-diff-body-storage",
    "blocked-state:no-production-authority",
]
DENIED_POSTURE_FLAGS = [
    "apply_execution_enabled",
    "approval_grant_capture_enabled",
    "direct_file_write_enabled",
    "unrestricted_shell_enabled",
    "shell_subprocess_execution_enabled",
    "remote_execution_enabled",
    "broad_coding_agent_autonomy_enabled",
    "provider_sdk_call_enabled",
    "web_fetch_enabled",
    "connector_write_enabled",
    "diff_body_storage_enabled",
    "production_authority_enabled",
]
REQUIRED_TRUE_FLAGS = [
    "safe_refs_only",
    "repo_local_scope_required",
    "safe_diff_summary_only",
    "validation_required_before_apply",
    "approval_required_before_apply",
    "atomic_apply_required",
    "rollback_receipt_required",
    "audit_required",
    "redaction_required",
]
FORBIDDEN_SNIPPETS = [
    "raw diff",
    "full diff",
    "unredacted diff",
    "raw patch",
    "provider payload",
    "api key",
    "authorization",
    "cookie",
    "password",
    "private_key",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
]
FORBIDDEN_PYTHON_RUNTIME_CALLS = [
    "subprocess.run",
    "subprocess.Popen",
    "requests.",
    "httpx.",
    "openai.",
    "connector.write",
    "approval_authority.grant",
    "execute_action",
    "apply_patch(",
]
OLD_MISSING_MARKERS = [
    "contract-ref:governed-code-workbench-missing",
    "planned_blocked_until_uaa_p1_075",
    "governed-code-workbench-missing",
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
        "governed_code_workbench_contract_ref": today[
            "governed_code_workbench_contract_ref"
        ],
        "governed_code_workbench_status": today["governed_code_workbench_status"],
        "governed_code_workbench_proposal_ref": today[
            "governed_code_workbench_proposal_ref"
        ],
        "governed_code_workbench_repo_scope_ref": today[
            "governed_code_workbench_repo_scope_ref"
        ],
        "governed_code_workbench_safe_diff_summary_ref": today[
            "governed_code_workbench_safe_diff_summary_ref"
        ],
        "governed_code_workbench_validation_plan_ref": today[
            "governed_code_workbench_validation_plan_ref"
        ],
        "governed_code_workbench_validation_result_refs": today[
            "governed_code_workbench_validation_result_refs"
        ],
        "governed_code_workbench_approval_requirement_ref": today[
            "governed_code_workbench_approval_requirement_ref"
        ],
        "governed_code_workbench_expected_apply_receipt_ref": today[
            "governed_code_workbench_expected_apply_receipt_ref"
        ],
        "governed_code_workbench_expected_rollback_receipt_ref": today[
            "governed_code_workbench_expected_rollback_receipt_ref"
        ],
        "governed_code_workbench_evidence_refs": today[
            "governed_code_workbench_evidence_refs"
        ],
        "governed_code_workbench_idempotency_key_ref": today[
            "governed_code_workbench_idempotency_key_ref"
        ],
        "governed_code_workbench_safe_summary": today[
            "governed_code_workbench_safe_summary"
        ],
        "governed_code_workbench_validation_plan_summary": today[
            "governed_code_workbench_validation_plan_summary"
        ],
        "governed_code_workbench_required_ref_fields": today[
            "governed_code_workbench_required_ref_fields"
        ],
        "governed_code_workbench_required_blocked_refs": today[
            "governed_code_workbench_required_blocked_refs"
        ],
        "governed_code_workbench_surface_bindings": today[
            "governed_code_workbench_surface_bindings"
        ],
        "governed_code_workbench_authority_posture": today[
            "governed_code_workbench_authority_posture"
        ],
        "governed_code_workbench_blocked_state_refs": today[
            "governed_code_workbench_blocked_state_refs"
        ],
    }


def _validate_live_contract(schema: dict, failures: list[str]) -> None:
    from pydantic import ValidationError

    from ultimate_ai_agent.core.code import (
        GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
        GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS,
        GOVERNED_CODE_WORKBENCH_REQUIRED_REF_FIELDS,
        GovernedCodeWorkbenchProposal,
        build_governed_code_workbench_proposal,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="uaa-p1-075-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()

    contract = _extract(today)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda error: error.path)
    for error in errors:
        failures.append(f"live governed Code workbench schema error: {error.message}")

    if contract["governed_code_workbench_contract_ref"] != (
        GOVERNED_CODE_WORKBENCH_CONTRACT_REF
    ):
        failures.append("live governed Code workbench contract ref drifted")
    if contract["governed_code_workbench_required_ref_fields"] != (
        GOVERNED_CODE_WORKBENCH_REQUIRED_REF_FIELDS
    ):
        failures.append("live governed Code workbench ref fields drifted")
    if contract["governed_code_workbench_required_blocked_refs"] != (
        GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS
    ):
        failures.append("live governed Code workbench blockers drifted")

    posture = contract["governed_code_workbench_authority_posture"]
    for flag in REQUIRED_TRUE_FLAGS:
        if posture.get(flag) is not True:
            failures.append(f"governed Code posture is missing true {flag}")
    for flag in DENIED_POSTURE_FLAGS:
        if posture.get(flag) is not False:
            failures.append(f"governed Code posture has unsafe {flag}")

    serialized = json.dumps(contract, sort_keys=True).lower()
    for forbidden in FORBIDDEN_SNIPPETS:
        if forbidden in serialized:
            failures.append(f"live governed Code workbench contains {forbidden}")

    bindings = {
        binding["surface"]: binding
        for binding in contract["governed_code_workbench_surface_bindings"]
    }
    if set(bindings) != {"Today", "Code", "Actions", "Evidence", "Memory"}:
        failures.append("governed Code surface bindings drifted")
    if bindings["Memory"]["feed_status"] != "blocked_until_cross_surface_memory_intake":
        failures.append("governed Code memory binding is not blocked")

    module_feeds = {item["module"]: item for item in today["module_feed_contract"]}
    code_feed = module_feeds.get("Code", {})
    if code_feed.get("status") != (
        "implemented_governed_code_workbench_contract_apply_blocked"
    ):
        failures.append("Today module feed does not mark Code implemented")
    if GOVERNED_CODE_WORKBENCH_CONTRACT_REF not in (
        code_feed.get("current_feed_refs") or []
    ):
        failures.append("Today module feed missing governed Code contract ref")

    timeline_kinds = {item["item_kind"] for item in today["evidence_timeline"]}
    if "governed_code_workbench_proposal_ref" not in timeline_kinds:
        failures.append("Evidence Timeline missing governed Code proposal ref")
    code_item = next(
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "governed_code_workbench_proposal_ref"
    )
    if code_item["approval_ref_authority"] is not False:
        failures.append("governed Code evidence item grants approval authority")
    if code_item["rollback_execution_enabled"] is not False:
        failures.append("governed Code evidence item enables rollback execution")
    if code_item["raw_evidence_included"] is not False:
        failures.append("governed Code evidence item includes raw evidence")
    if "no files were changed" not in code_item["history_answers"]["happened"]["answer"]:
        failures.append("governed Code evidence item does not record no-op happened")
    if set(REQUIRED_BLOCKED_REFS) - set(code_item["blocked_states"]):
        failures.append("governed Code evidence item missing blocked-state refs")

    proposal = build_governed_code_workbench_proposal()
    for flag in DENIED_POSTURE_FLAGS:
        payload = proposal.model_dump(mode="json")
        payload[flag] = True
        try:
            GovernedCodeWorkbenchProposal(**payload)
        except ValidationError:
            continue
        failures.append(f"GovernedCodeWorkbenchProposal accepted unsafe {flag}=true")

    for unsafe_summary in [
        "raw patch material",
        "raw diff material",
        "provider payload material",
        "api key material",
    ]:
        payload = proposal.model_dump(mode="json")
        payload["safe_summary"] = unsafe_summary
        try:
            GovernedCodeWorkbenchProposal(**payload)
        except ValidationError:
            continue
        failures.append(f"GovernedCodeWorkbenchProposal accepted {unsafe_summary}")


def main() -> int:
    failures: list[str] = []
    schema = json.loads(_read(SCHEMA))

    required_snippets = [
        "contract-ref:governed-code-workbench:v1",
        "proposal_ref",
        "repo_scope_ref",
        "safe_diff_summary_ref",
        "validation_plan_ref",
        "expected_apply_receipt_ref",
        "expected_rollback_receipt_ref",
        "blocked-state:no-apply-execution",
        "blocked-state:no-approval-grant-capture",
        "blocked-state:no-unrestricted-shell",
        "blocked-state:no-diff-body-storage",
        "apply_execution_enabled",
        "approval_grant_capture_enabled",
        "diff_body_storage_enabled",
    ]
    _require(
        CODE_WORKBENCH,
        [
            "GOVERNED_CODE_WORKBENCH_CONTRACT_REF",
            "GovernedCodeWorkbenchProposal",
            "build_governed_code_workbench_proposal",
            "UNSAFE_CODE_WORKBENCH_TEXT_FRAGMENTS",
        ],
        failures,
    )
    _require(
        FOUNDER_LOOP,
        [
            "GOVERNED_CODE_WORKBENCH_CONTRACT_REF",
            "governed_code_workbench_status",
            "governed_code_workbench_proposal_ref",
        ],
        failures,
    )
    _require(CODE_INIT, ["GovernedCodeWorkbenchProposal"], failures)
    _require(FRONTEND_TYPES, ["governed_code_workbench_contract_ref"], failures)
    _require(FRONTEND_MOCK, ["governedCodeWorkbenchContractRef"], failures)
    _require(FOCUSED_TEST, ["GOVERNED_CODE_WORKBENCH_CONTRACT_REF"], failures)
    _require(STORAGE_TEST, ["GOVERNED_CODE_WORKBENCH_CONTRACT_REF"], failures)
    _require(API_TEST, ["GOVERNED_CODE_WORKBENCH_CONTRACT_REF"], failures)
    _require(
        APP_TEST,
        ["implemented_governed_code_workbench_contract_apply_blocked"],
        failures,
    )
    _require(SCHEMA, ["governed_code_workbench_contract_ref"], failures)
    _require(CONTRACT_DOC, required_snippets, failures)

    for path in [
        FOUNDER_LOOP,
        FRONTEND_TYPES,
        FRONTEND_MOCK,
        FOCUSED_TEST,
        STORAGE_TEST,
        API_TEST,
        APP_TEST,
    ]:
        _require_absent(path, OLD_MISSING_MARKERS, failures)

    _require_absent(CODE_WORKBENCH, FORBIDDEN_PYTHON_RUNTIME_CALLS, failures)
    _validate_live_contract(schema, failures)

    if failures:
        for failure in failures:
            print(f"[UAA-P1-075 verifier] {failure}")
        return 1

    print("[UAA-P1-075 verifier] Governed Code workbench checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
