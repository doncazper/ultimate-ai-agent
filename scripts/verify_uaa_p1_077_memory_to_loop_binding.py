#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_077_MEMORY_TO_LOOP_BINDING.md"
SCHEMA = ROOT / "docs/schemas/memory_to_loop_binding.schema.json"
LOOP_BINDING = ROOT / "src/ultimate_ai_agent/core/memory/loop_binding.py"
MEMORY_INIT = ROOT / "src/ultimate_ai_agent/core/memory/__init__.py"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
FOCUSED_TEST = ROOT / "tests/test_uaa_p1_077_memory_to_loop_binding.py"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"

REQUIRED_SURFACES = [
    "Today",
    "Action Inbox",
    "Evidence Timeline",
    "Weekly CEO Review",
]
REQUIRED_REF_FIELDS = [
    "loop_item_ref",
    "surface",
    "loop_binding_state",
    "memory_candidate_ref",
    "source_refs",
    "evidence_refs",
    "accepted_recall_refs",
    "correction_refs",
    "rejected_item_refs",
    "follow_up_commitment_refs",
    "stale_state",
    "missing_evidence_refs",
    "blocked_state_refs",
    "next_safe_action",
]
REQUIRED_ACTION_REF_FIELDS = [
    "proposal_ref",
    "source_memory_ref",
    "source_loop_item_ref",
    "source_review_ref",
    "source_refs",
    "provenance_refs",
    "evidence_refs",
    "side_effect_class",
    "risk_class",
    "approval_required",
    "approval_posture",
    "approval_requirement_ref",
    "action_envelope_ref",
    "scope_ref",
    "review_posture_refs",
    "expected_receipt_refs",
    "next_safe_action",
    "blocked_state_refs",
]
REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-memory-write",
    "blocked-state:no-automatic-recall",
    "blocked-state:no-context-injection",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-action-execution",
    "blocked-state:no-connector-write",
    "blocked-state:no-account-sync",
    "blocked-state:no-source-truth-authority",
    "blocked-state:no-public-beta-or-distribution",
    "blocked-state:no-production-authority",
]
DENIED_FLAGS = [
    "memory_write_authorized",
    "automatic_recall_enabled",
    "context_injection_authorized",
    "approval_grant_capture_enabled",
    "action_execution_enabled",
    "connector_write_enabled",
    "account_sync_enabled",
    "source_truth_authority",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]
FORBIDDEN_SNIPPETS = [
    "raw prompt",
    "raw response",
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
    "memory_write(",
    "context_injection(",
]
OLD_MISSING_MARKERS = [
    "contract-ref:memory-to-loop-binding-missing",
    "planned_blocked_until_uaa_p1_077",
    "memory-to-loop-binding-missing",
    "blocked_until_memory_to_loop_binding",
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
        "memory_to_loop_binding_contract_ref": today[
            "memory_to_loop_binding_contract_ref"
        ],
        "memory_to_loop_binding_status": today["memory_to_loop_binding_status"],
        "memory_to_loop_required_surfaces": today[
            "memory_to_loop_required_surfaces"
        ],
        "memory_to_loop_required_ref_fields": today[
            "memory_to_loop_required_ref_fields"
        ],
        "memory_derived_action_required_ref_fields": today[
            "memory_derived_action_required_ref_fields"
        ],
        "memory_to_loop_required_blocked_refs": today[
            "memory_to_loop_required_blocked_refs"
        ],
        "memory_to_loop_item_count": today["memory_to_loop_item_count"],
        "memory_to_loop_items": today["memory_to_loop_items"],
        "memory_derived_action_proposal_count": today[
            "memory_derived_action_proposal_count"
        ],
        "memory_derived_action_proposals": today[
            "memory_derived_action_proposals"
        ],
        "memory_candidate_refs": today["memory_candidate_refs"],
        "accepted_recall_refs": today["accepted_recall_refs"],
        "correction_refs": today["correction_refs"],
        "rejected_item_refs": today["rejected_item_refs"],
        "follow_up_commitment_refs": today["follow_up_commitment_refs"],
        "stale_memory_refs": today["stale_memory_refs"],
        "missing_evidence_blocker_refs": today["missing_evidence_blocker_refs"],
        "memory_derived_action_proposal_refs": today[
            "memory_derived_action_proposal_refs"
        ],
        "memory_to_loop_surface_bindings": today[
            "memory_to_loop_surface_bindings"
        ],
        "memory_to_loop_authority_posture": today[
            "memory_to_loop_authority_posture"
        ],
        "memory_to_loop_weekly_review_refs": today[
            "memory_to_loop_weekly_review_refs"
        ],
        "weekly_ceo_review_summary": today["weekly_ceo_review_summary"],
        "memory_to_loop_blocked_state_refs": today[
            "memory_to_loop_blocked_state_refs"
        ],
    }


def _validate_live_contract(schema: dict, failures: list[str]) -> None:
    from pydantic import ValidationError

    from ultimate_ai_agent.core.memory import (
        MEMORY_DERIVED_ACTION_REQUIRED_REF_FIELDS,
        MEMORY_TO_LOOP_BINDING_CONTRACT_REF,
        MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
        MEMORY_TO_LOOP_REQUIRED_REF_FIELDS,
        MEMORY_TO_LOOP_REQUIRED_SURFACES,
        MemoryDerivedActionProposal,
        MemoryToLoopBindingItem,
        build_memory_derived_action_proposal,
        build_memory_to_loop_binding_item,
        memory_to_loop_authority_posture,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="uaa-p1-077-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()
        inbox = repo.actions_inbox()

    contract = _extract(today)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda error: error.path)
    for error in errors:
        failures.append(f"live memory-to-loop schema error: {error.message}")

    if contract["memory_to_loop_binding_contract_ref"] != (
        MEMORY_TO_LOOP_BINDING_CONTRACT_REF
    ):
        failures.append("live memory-to-loop contract ref drifted")
    if contract["memory_to_loop_required_surfaces"] != (
        MEMORY_TO_LOOP_REQUIRED_SURFACES
    ):
        failures.append("live memory-to-loop surfaces drifted")
    if contract["memory_to_loop_required_ref_fields"] != (
        MEMORY_TO_LOOP_REQUIRED_REF_FIELDS
    ):
        failures.append("live memory-to-loop ref fields drifted")
    if contract["memory_derived_action_required_ref_fields"] != (
        MEMORY_DERIVED_ACTION_REQUIRED_REF_FIELDS
    ):
        failures.append("live memory-derived action fields drifted")
    if contract["memory_to_loop_required_blocked_refs"] != (
        MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS
    ):
        failures.append("live memory-to-loop blockers drifted")
    if contract["memory_to_loop_item_count"] != len(REQUIRED_SURFACES):
        failures.append("live memory-to-loop item count drifted")

    loop_items = contract["memory_to_loop_items"]
    if {item["surface"] for item in loop_items} != set(REQUIRED_SURFACES):
        failures.append("memory-to-loop items do not cover all surfaces")
    loop_states = {item["loop_binding_state"] for item in loop_items}
    for required_state in [
        "candidate",
        "follow_up_commitment",
        "missing_evidence_blocker",
        "stale",
    ]:
        if required_state not in loop_states:
            failures.append(f"memory-to-loop missing {required_state} state")
    for item in loop_items:
        if item["contract_ref"] != MEMORY_TO_LOOP_BINDING_CONTRACT_REF:
            failures.append("memory-to-loop item contract ref drifted")
        if not item["source_refs"] or not item["evidence_refs"]:
            failures.append("memory-to-loop item missing source/evidence refs")
        if set(REQUIRED_BLOCKED_REFS) - set(item["blocked_state_refs"]):
            failures.append("memory-to-loop item missing blocked refs")
        for flag in DENIED_FLAGS:
            if item.get(flag) is not False:
                failures.append(f"memory-to-loop item has unsafe {flag}")

    action_proposals = contract["memory_derived_action_proposals"]
    if contract["memory_derived_action_proposal_count"] != len(action_proposals):
        failures.append("memory-derived action proposal count drifted")
    if not action_proposals:
        failures.append("memory-derived action proposals missing")
    for proposal in action_proposals:
        if proposal["contract_ref"] != MEMORY_TO_LOOP_BINDING_CONTRACT_REF:
            failures.append("memory-derived action contract ref drifted")
        if not proposal["source_loop_item_ref"]:
            failures.append("memory-derived action missing source loop item")
        if not proposal["source_review_ref"]:
            failures.append("memory-derived action missing source review ref")
        if not proposal["source_intake_proposal_ref"]:
            failures.append("memory-derived action missing intake proposal ref")
        if not proposal["source_refs"] or not proposal["evidence_refs"]:
            failures.append("memory-derived action missing source/evidence refs")
        if proposal["approval_required"] is not True:
            failures.append("memory-derived action missing approval requirement")
        if proposal["side_effect_class"] != "local_dev_workspace_only":
            failures.append("memory-derived action side-effect class drifted")
        if set(REQUIRED_BLOCKED_REFS) - set(proposal["blocked_state_refs"]):
            failures.append("memory-derived action missing blocked refs")
        for flag in DENIED_FLAGS:
            if proposal.get(flag) is not False:
                failures.append(f"memory-derived action has unsafe {flag}")

    posture = contract["memory_to_loop_authority_posture"]
    if posture != memory_to_loop_authority_posture():
        failures.append("memory-to-loop authority posture drifted")
    if posture.get("safe_refs_only") is not True:
        failures.append("memory-to-loop posture missing safe_refs_only")
    if posture.get("review_required") is not True:
        failures.append("memory-to-loop posture missing review_required")
    for flag in DENIED_FLAGS:
        if posture.get(flag) is not False:
            failures.append(f"memory-to-loop posture has unsafe {flag}")

    weekly = contract["weekly_ceo_review_summary"]
    if weekly["weekly_review_ref"] != "weekly-review-ref:memory-to-loop-binding":
        failures.append("weekly CEO review ref drifted")
    for field_name in [
        "input_refs",
        "decision_refs",
        "commitment_refs",
        "carry_forward_task_refs",
        "unresolved_blocker_refs",
        "memory_correction_refs",
        "rejected_item_refs",
        "stale_memory_refs",
        "missing_evidence_blocker_refs",
        "follow_up_opportunity_refs",
    ]:
        if not weekly.get(field_name):
            failures.append(f"weekly CEO review missing {field_name}")
    if set(REQUIRED_BLOCKED_REFS) - set(weekly["unresolved_blocker_refs"]):
        failures.append("weekly CEO review missing blocked refs")

    module_feeds = {item["module"]: item for item in today["module_feed_contract"]}
    memory_feed = module_feeds.get("Memory", {})
    if memory_feed.get("status") != (
        "implemented_review_queue_quality_intake_and_loop_binding_contract"
    ):
        failures.append("Today module feed does not mark loop binding implemented")
    if MEMORY_TO_LOOP_BINDING_CONTRACT_REF not in (
        memory_feed.get("current_feed_refs") or []
    ):
        failures.append("Today module feed missing memory-to-loop contract ref")

    timeline_kinds = {item["item_kind"] for item in today["evidence_timeline"]}
    if "memory_to_loop_binding_ref" not in timeline_kinds:
        failures.append("Evidence Timeline missing memory-to-loop binding ref")
    loop_timeline = next(
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "memory_to_loop_binding_ref"
    )
    if loop_timeline["history_answers"]["approved"]["status"] != "blocked":
        failures.append("memory-to-loop approved history answer is not blocked")
    for flag in [
        "approval_ref_authority",
        "memory_truth_authority",
        "context_injection_authorized",
        "rollback_execution_enabled",
        "raw_evidence_included",
    ]:
        if loop_timeline[flag] is not False:
            failures.append(f"memory-to-loop evidence has unsafe {flag}")
    if set(REQUIRED_BLOCKED_REFS) - set(loop_timeline["blocked_states"]):
        failures.append("memory-to-loop evidence item missing blocked-state refs")

    if inbox["memory_to_loop_binding_contract_ref"] != (
        MEMORY_TO_LOOP_BINDING_CONTRACT_REF
    ):
        failures.append("Action Inbox missing memory-to-loop contract ref")
    if not inbox["memory_derived_action_proposals"]:
        failures.append("Action Inbox missing memory-derived proposals")

    serialized = json.dumps(contract, sort_keys=True).lower()
    for forbidden in FORBIDDEN_SNIPPETS:
        if forbidden in serialized:
            failures.append(f"live memory-to-loop contains {forbidden}")

    loop_item = build_memory_to_loop_binding_item(
        surface="Action Inbox",
        loop_binding_state="follow_up_commitment",
        memory_candidate_ref="business-memory-candidate:sample",
        review_ref="memory-review:sample",
        safe_summary="Action Inbox shows reviewed memory refs only.",
        source_refs=["source-ref:manual-note:sample"],
        evidence_refs=["evidence-ref:memory-loop:sample"],
        missing_evidence_refs=["missing-evidence-ref:memory-loop:sample"],
        stale_state="recheck_memory_refs_before_loop_use",
        follow_up_commitment_refs=["follow-up-commitment-ref:sample"],
        next_safe_action="Review memory refs before any later action.",
    )
    for flag in DENIED_FLAGS:
        payload = loop_item.model_dump(mode="json")
        payload[flag] = True
        try:
            MemoryToLoopBindingItem(**payload)
        except ValidationError:
            continue
        failures.append(f"MemoryToLoopBindingItem accepted {flag}=true")

    fake_state = loop_item.model_dump(mode="json")
    fake_state["loop_binding_state"] = "accepted_recall"
    fake_state["accepted_recall_refs"] = []
    try:
        MemoryToLoopBindingItem(**fake_state)
    except ValidationError:
        pass
    else:
        failures.append("MemoryToLoopBindingItem accepted fake recall state")

    unsafe = loop_item.model_dump(mode="json")
    unsafe["safe_summary"] = "raw prompt material"
    try:
        MemoryToLoopBindingItem(**unsafe)
    except ValidationError:
        pass
    else:
        failures.append("MemoryToLoopBindingItem accepted unsafe summary")

    action = build_memory_derived_action_proposal(
        proposal_ref="memory-derived-action-proposal:sample",
        source_memory_ref="business-memory-candidate:sample",
        source_loop_item_ref="memory-loop-binding:today:sample",
        source_review_ref="memory-review:sample",
        source_intake_proposal_ref="memory-intake-proposal:today",
        safe_summary="Review only memory-derived action proposal.",
        source_refs=["source-ref:manual-note:sample"],
        provenance_refs=["provenance-ref:manual-note:sample"],
        evidence_refs=["evidence-ref:memory-loop:sample"],
        missing_evidence_refs=["missing-evidence-ref:memory-loop:sample"],
        next_safe_action="Review before any scoped mutation.",
    )
    for flag in DENIED_FLAGS:
        payload = action.model_dump(mode="json")
        payload[flag] = True
        try:
            MemoryDerivedActionProposal(**payload)
        except ValidationError:
            continue
        failures.append(f"MemoryDerivedActionProposal accepted {flag}=true")


def main() -> int:
    failures: list[str] = []
    schema = json.loads(_read(SCHEMA))

    required_snippets = [
        "contract-ref:memory-to-loop-binding:v1",
        "loop_item_ref",
        "loop_binding_state",
        "accepted_recall_refs",
        "follow_up_commitment_refs",
        "memory_derived_action_proposals",
        "weekly_ceo_review_summary",
        "blocked-state:no-automatic-recall",
        "blocked-state:no-context-injection",
        "blocked-state:no-approval-grant-capture",
        "blocked-state:no-action-execution",
        "memory_write_authorized",
        "context_injection_authorized",
        "approval_grant_capture_enabled",
    ]
    _require(
        LOOP_BINDING,
        [
            "MEMORY_TO_LOOP_BINDING_CONTRACT_REF",
            "MemoryToLoopBindingItem",
            "MemoryDerivedActionProposal",
            "memory_to_loop_authority_posture",
        ],
        failures,
    )
    _require(MEMORY_INIT, ["MemoryToLoopBindingItem"], failures)
    _require(
        FOUNDER_LOOP,
        [
            "memory_to_loop_binding_contract_ref",
            "memory_to_loop_items",
            "memory_derived_action_proposals",
            "memory_to_loop_binding_ref",
        ],
        failures,
    )
    _require(FRONTEND_TYPES, ["FounderLoopMemoryToLoopItem"], failures)
    _require(FRONTEND_PANEL, ["Memory-to-loop", "Memory-derived proposals"], failures)
    _require(FRONTEND_MOCK, ["memoryToLoopBindingContractRef"], failures)
    _require(FOCUSED_TEST, ["MEMORY_TO_LOOP_BINDING_CONTRACT_REF"], failures)
    _require(STORAGE_TEST, ["MEMORY_TO_LOOP_BINDING_CONTRACT_REF"], failures)
    _require(API_TEST, ["MEMORY_TO_LOOP_BINDING_CONTRACT_REF"], failures)
    _require(APP_TEST, ["Memory-to-loop"], failures)
    _require(SCHEMA, ["memory_to_loop_binding_contract_ref"], failures)
    _require(CONTRACT_DOC, required_snippets, failures)

    for path in [
        LOOP_BINDING,
        MEMORY_INIT,
        FOUNDER_LOOP,
        FRONTEND_TYPES,
        FRONTEND_PANEL,
        FRONTEND_MOCK,
        FOCUSED_TEST,
        STORAGE_TEST,
        API_TEST,
        APP_TEST,
        CONTRACT_DOC,
        SCHEMA,
    ]:
        _require_absent(path, OLD_MISSING_MARKERS, failures)

    _require_absent(LOOP_BINDING, FORBIDDEN_PYTHON_RUNTIME_CALLS, failures)
    _validate_live_contract(schema, failures)

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    print("UAA-P1-077 memory-to-loop binding verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
