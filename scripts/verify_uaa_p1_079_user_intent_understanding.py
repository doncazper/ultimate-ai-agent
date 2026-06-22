#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_079_USER_INTENT_UNDERSTANDING.md"
SCHEMA = ROOT / "docs/schemas/user_intent_understanding.schema.json"
INTENT_MODULE = ROOT / "src/ultimate_ai_agent/core/intent/user_intent.py"
INTENT_INIT = ROOT / "src/ultimate_ai_agent/core/intent/__init__.py"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
FOCUSED_TEST = ROOT / "tests/test_uaa_p1_079_user_intent_understanding.py"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"

REQUIRED_SURFACES = [
    "Today",
    "Memory Review",
    "Evidence Timeline",
    "Plans",
    "Actions",
    "Chat",
    "Governed Code",
]
ROUTING_DECISIONS = ["ask", "act", "defer"]
REQUIRED_REF_FIELDS = [
    "proposal_ref",
    "source_surface",
    "intent_label",
    "confidence_score",
    "confidence_band",
    "ambiguity_posture",
    "routing_decision",
    "source_refs",
    "evidence_refs",
    "dependency_refs",
    "required_contract_refs",
    "conflict_refs",
    "ask_user_question_ref",
    "next_safe_action",
]
REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-hidden-intent-authority",
    "blocked-state:low-confidence-must-ask-user",
    "blocked-state:conflicting-intent-must-ask-user",
    "blocked-state:no-action-execution",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-memory-write",
    "blocked-state:no-automatic-memory-write",
    "blocked-state:no-context-injection",
    "blocked-state:no-tool-execution",
    "blocked-state:no-provider-model-authority",
    "blocked-state:no-connector-write",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-code-apply-execution",
    "blocked-state:no-broad-autonomy",
    "blocked-state:no-public-beta",
    "blocked-state:no-production-authority",
]
DENIED_FLAGS = [
    "hidden_authority_enabled",
    "acts_without_review",
    "action_execution_enabled",
    "approval_grant_capture_enabled",
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "tool_execution_enabled",
    "provider_model_authority_allowed",
    "connector_write_enabled",
    "shell_subprocess_execution_enabled",
    "code_apply_execution_enabled",
    "broad_autonomy_enabled",
    "public_beta_claim_enabled",
    "production_authority_enabled",
]
FORBIDDEN_SNIPPETS = [
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
    "intent executes actions",
    "automatic action execution",
    "hidden authority enabled",
    "memory writes enabled",
    "context injection enabled",
    "provider authority enabled",
    "connector writes enabled",
    "code apply enabled",
    "production ready",
    "public beta is ready",
]
FORBIDDEN_RUNTIME_CALLS = [
    "subprocess.run",
    "subprocess.Popen",
    "requests.",
    "httpx.",
    "openai.",
    "execute_action",
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
        "user_intent_understanding_contract_ref": today[
            "user_intent_understanding_contract_ref"
        ],
        "user_intent_understanding_status": today[
            "user_intent_understanding_status"
        ],
        "user_intent_required_surfaces": today["user_intent_required_surfaces"],
        "user_intent_routing_decisions": today["user_intent_routing_decisions"],
        "user_intent_required_dependency_refs": today[
            "user_intent_required_dependency_refs"
        ],
        "user_intent_required_ref_fields": today[
            "user_intent_required_ref_fields"
        ],
        "user_intent_required_blocked_refs": today[
            "user_intent_required_blocked_refs"
        ],
        "user_intent_proposal_count": today["user_intent_proposal_count"],
        "user_intent_proposals": today["user_intent_proposals"],
        "user_intent_surface_bindings": today["user_intent_surface_bindings"],
        "user_intent_authority_posture": today["user_intent_authority_posture"],
        "user_intent_blocked_state_refs": today["user_intent_blocked_state_refs"],
        "user_intent_low_confidence_policy_ref": today[
            "user_intent_low_confidence_policy_ref"
        ],
        "user_intent_conflict_policy_ref": today["user_intent_conflict_policy_ref"],
        "user_intent_next_safe_action": today["user_intent_next_safe_action"],
        "user_intent_review_required": today["user_intent_review_required"],
        "user_intent_safe_refs_only": today["user_intent_safe_refs_only"],
        "user_intent_evidence_required": today["user_intent_evidence_required"],
        "user_intent_low_confidence_asks_user": today[
            "user_intent_low_confidence_asks_user"
        ],
        "user_intent_conflicting_intent_asks_user": today[
            "user_intent_conflicting_intent_asks_user"
        ],
        "user_intent_hidden_authority_enabled": today[
            "user_intent_hidden_authority_enabled"
        ],
        "user_intent_action_execution_enabled": today[
            "user_intent_action_execution_enabled"
        ],
    }


def _validate_live_contract(schema: dict, failures: list[str]) -> None:
    from ultimate_ai_agent.core.intent import USER_INTENT_UNDERSTANDING_CONTRACT_REF
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="uaa-p1-079-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()
        inbox = repo.actions_inbox()

    contract = _extract(today)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda error: error.path)
    for error in errors:
        failures.append(f"live user intent schema error: {error.message}")

    if (
        contract["user_intent_understanding_contract_ref"]
        != USER_INTENT_UNDERSTANDING_CONTRACT_REF
    ):
        failures.append("live user intent contract ref drifted")
    if contract["user_intent_required_surfaces"] != REQUIRED_SURFACES:
        failures.append("live user intent surfaces drifted")
    if contract["user_intent_routing_decisions"] != ROUTING_DECISIONS:
        failures.append("live user intent routing decisions drifted")
    if contract["user_intent_required_ref_fields"] != REQUIRED_REF_FIELDS:
        failures.append("live user intent ref fields drifted")
    if set(REQUIRED_BLOCKED_REFS) - set(contract["user_intent_blocked_state_refs"]):
        failures.append("live user intent blocked refs drifted")
    for flag in DENIED_FLAGS:
        if contract["user_intent_authority_posture"].get(flag) is not False:
            failures.append(f"live user intent authority posture enabled {flag}")
    for proposal in contract["user_intent_proposals"]:
        if proposal["confidence_band"] in {"low", "conflicting"}:
            if proposal["routing_decision"] != "ask":
                failures.append(f"{proposal['proposal_ref']} low/conflict did not ask")
            if not proposal.get("ask_user_question_ref"):
                failures.append(f"{proposal['proposal_ref']} missing user question ref")
        for flag in DENIED_FLAGS:
            if proposal.get(flag) is not False:
                failures.append(f"{proposal['proposal_ref']} enabled {flag}")
    if inbox.get("user_intent_understanding_contract_ref") != (
        USER_INTENT_UNDERSTANDING_CONTRACT_REF
    ):
        failures.append("Actions Inbox missing user intent contract ref")
    timeline_items = [
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "user_intent_understanding_proposal_ref"
    ]
    if len(timeline_items) != 1:
        failures.append("Evidence Timeline missing user intent item")
    else:
        item = timeline_items[0]
        if item["history_answers"]["approved"]["status"] != "blocked":
            failures.append("user intent Evidence approved answer must be blocked")
        if item["approval_ref_authority"] is not False:
            failures.append("user intent Evidence must not grant approval authority")

    serialized = json.dumps(contract, sort_keys=True).lower()
    for forbidden in FORBIDDEN_SNIPPETS:
        if forbidden in serialized:
            failures.append(f"live user intent contains unsafe snippet: {forbidden}")


def main() -> int:
    failures: list[str] = []
    for path in [
        CONTRACT_DOC,
        SCHEMA,
        INTENT_MODULE,
        INTENT_INIT,
        FOUNDER_LOOP,
        FRONTEND_TYPES,
        FRONTEND_PANEL,
        FRONTEND_MOCK,
        FOCUSED_TEST,
        STORAGE_TEST,
        API_TEST,
        APP_TEST,
    ]:
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)} is missing")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    schema = json.loads(_read(SCHEMA))
    _validate_live_contract(schema, failures)

    _require(
        CONTRACT_DOC,
        [
            "contract-ref:user-intent-understanding:v1",
            "confidence",
            "source refs",
            "evidence refs",
            "ambiguity posture",
            "ask/act/defer",
            "Low-confidence or conflicting intent asks the user",
            "not hidden authority",
            "No action execution",
            "No memory write",
            "No context injection",
            "No provider/model authority",
            "UAA-P1-080",
        ],
        failures,
    )
    _require(
        INTENT_MODULE,
        [
            "USER_INTENT_UNDERSTANDING_CONTRACT_REF",
            "USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS",
            "ReviewableUserIntentProposal",
            "UserIntentUnderstandingContract",
            "build_user_intent_understanding_contract",
            "low or conflicting user intent must ask the user",
        ],
        failures,
    )
    _require_absent(INTENT_MODULE, FORBIDDEN_RUNTIME_CALLS, failures)
    _require(
        FOUNDER_LOOP,
        [
            "user_intent_understanding_contract",
            "user_intent_understanding_proposal_ref",
            "USER_INTENT_UNDERSTANDING_CONTRACT_REF",
        ],
        failures,
    )
    _require(
        FRONTEND_TYPES,
        [
            "FounderLoopUserIntentProposal",
            "user_intent_understanding_contract_ref",
            "user_intent_routing_decisions",
            "user_intent_authority_posture",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "User intent understanding",
            "Low confidence",
            "Hidden authority",
            "Intent action gate",
        ],
        failures,
    )
    _require(
        FRONTEND_MOCK,
        [
            "userIntentUnderstandingContractRef",
            "userIntentProposals",
            "user_intent_understanding_contract_ref",
            "user_intent_understanding_proposal_ref",
        ],
        failures,
    )
    _require_absent(FRONTEND_MOCK, FORBIDDEN_CLAIMS, failures)
    _require(
        FOCUSED_TEST,
        [
            "test_user_intent_contract_defines_reviewable_taxonomy",
            "test_user_intent_low_confidence_or_conflict_asks_user",
            "test_user_intent_rejects_authority_creep_and_missing_dependencies",
        ],
        failures,
    )
    _require(
        APP_TEST,
        [
            "User intent understanding",
            "contract-ref:user-intent-understanding:v1",
            "asks user",
            "blocked-state:no-hidden-intent-authority",
        ],
        failures,
    )

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("UAA-P1-079 user intent understanding verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
