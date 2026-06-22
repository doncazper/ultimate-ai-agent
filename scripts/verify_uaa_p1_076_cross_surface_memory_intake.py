#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_076_CROSS_SURFACE_MEMORY_INTAKE.md"
SCHEMA = ROOT / "docs/schemas/cross_surface_memory_intake.schema.json"
MEMORY_INTAKE = ROOT / "src/ultimate_ai_agent/core/memory/intake.py"
MEMORY_INIT = ROOT / "src/ultimate_ai_agent/core/memory/__init__.py"
CHAT_OPERATOR = ROOT / "src/ultimate_ai_agent/core/chat/operator_surface.py"
PLAN_ENVELOPES = ROOT / "src/ultimate_ai_agent/core/planning/action_envelopes.py"
CODE_WORKBENCH = ROOT / "src/ultimate_ai_agent/core/code/workbench.py"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
FOCUSED_TEST = ROOT / "tests/test_uaa_p1_076_cross_surface_memory_intake.py"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"

REQUIRED_SURFACES = [
    "Today",
    "Chat",
    "Plans",
    "Actions",
    "Evidence",
    "Local Coding",
    "External Assistant Review",
]
REQUIRED_REF_FIELDS = [
    "proposal_ref",
    "candidate_ref",
    "review_queue_ref",
    "surface",
    "source_kind",
    "candidate_kind",
    "source_refs",
    "provenance_refs",
    "evidence_refs",
    "quality_state_refs",
    "missing_evidence_refs",
    "stale_state",
    "next_safe_action",
    "blocked_state_refs",
]
REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-automatic-memory-write",
    "blocked-state:no-memory-write",
    "blocked-state:no-context-injection",
    "blocked-state:no-provider-call",
    "blocked-state:no-account-fetch",
    "blocked-state:no-browser-import",
    "blocked-state:no-shell-history-import",
    "blocked-state:no-raw-file-import",
    "blocked-state:no-connector-runtime",
    "blocked-state:no-source-truth-authority",
    "blocked-state:no-public-beta-or-distribution",
    "blocked-state:no-production-authority",
]
DENIED_FLAGS = [
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "provider_call_enabled",
    "account_fetch_enabled",
    "browser_import_enabled",
    "shell_history_import_enabled",
    "raw_file_import_enabled",
    "connector_runtime_enabled",
    "source_truth_authority",
    "accepted_as_recall",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]
REQUIRED_TRUE_FLAGS = [
    "safe_refs_only",
    "review_required",
    "safe_summary_only",
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
]
OLD_MISSING_MARKERS = [
    "contract-ref:cross-surface-memory-intake-missing",
    "planned_blocked_until_uaa_p1_076",
    "cross-surface-memory-intake-missing",
    "blocked_until_cross_surface_memory_intake",
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
        "cross_surface_memory_intake_contract_ref": today[
            "cross_surface_memory_intake_contract_ref"
        ],
        "cross_surface_memory_intake_status": today[
            "cross_surface_memory_intake_status"
        ],
        "cross_surface_memory_intake_required_surfaces": today[
            "cross_surface_memory_intake_required_surfaces"
        ],
        "cross_surface_memory_intake_required_ref_fields": today[
            "cross_surface_memory_intake_required_ref_fields"
        ],
        "cross_surface_memory_intake_required_blocked_refs": today[
            "cross_surface_memory_intake_required_blocked_refs"
        ],
        "cross_surface_memory_intake_proposal_count": today[
            "cross_surface_memory_intake_proposal_count"
        ],
        "cross_surface_memory_intake_proposals": today[
            "cross_surface_memory_intake_proposals"
        ],
        "cross_surface_memory_intake_surface_bindings": today[
            "cross_surface_memory_intake_surface_bindings"
        ],
        "cross_surface_memory_intake_authority_posture": today[
            "cross_surface_memory_intake_authority_posture"
        ],
        "cross_surface_memory_intake_blocked_state_refs": today[
            "cross_surface_memory_intake_blocked_state_refs"
        ],
    }


def _validate_live_contract(schema: dict, failures: list[str]) -> None:
    from pydantic import ValidationError

    from ultimate_ai_agent.core.memory import (
        CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF,
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS,
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_REF_FIELDS,
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES,
        CrossSurfaceMemoryIntakeProposal,
        build_cross_surface_memory_intake_proposal,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="uaa-p1-076-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()

    contract = _extract(today)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda error: error.path)
    for error in errors:
        failures.append(
            f"live cross-surface memory intake schema error: {error.message}"
        )

    if contract["cross_surface_memory_intake_contract_ref"] != (
        CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF
    ):
        failures.append("live memory intake contract ref drifted")
    if contract["cross_surface_memory_intake_required_surfaces"] != (
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES
    ):
        failures.append("live memory intake surfaces drifted")
    if contract["cross_surface_memory_intake_required_ref_fields"] != (
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_REF_FIELDS
    ):
        failures.append("live memory intake ref fields drifted")
    if contract["cross_surface_memory_intake_required_blocked_refs"] != (
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS
    ):
        failures.append("live memory intake blockers drifted")
    if contract["cross_surface_memory_intake_proposal_count"] != len(REQUIRED_SURFACES):
        failures.append("live memory intake proposal count drifted")

    proposals = contract["cross_surface_memory_intake_proposals"]
    if {proposal["surface"] for proposal in proposals} != set(REQUIRED_SURFACES):
        failures.append("live memory intake proposals do not cover all surfaces")
    for proposal in proposals:
        if proposal["contract_ref"] != CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF:
            failures.append("memory intake proposal contract ref drifted")
        if not proposal["source_refs"]:
            failures.append("memory intake proposal missing source refs")
        if not proposal["provenance_refs"]:
            failures.append("memory intake proposal missing provenance refs")
        if not proposal["evidence_refs"]:
            failures.append("memory intake proposal missing evidence refs")
        if not proposal["missing_evidence_refs"]:
            failures.append("memory intake proposal missing missing-evidence refs")
        if set(REQUIRED_BLOCKED_REFS) - set(proposal["blocked_state_refs"]):
            failures.append("memory intake proposal missing blocked refs")
        for flag in DENIED_FLAGS:
            if proposal.get(flag) is not False:
                failures.append(f"memory intake proposal has unsafe {flag}")

    posture = contract["cross_surface_memory_intake_authority_posture"]
    for flag in REQUIRED_TRUE_FLAGS:
        if posture.get(flag) is not True:
            failures.append(f"memory intake posture missing true {flag}")
    for flag in DENIED_FLAGS:
        if posture.get(flag) is not False:
            failures.append(f"memory intake posture has unsafe {flag}")

    bindings = {
        binding["surface"]: binding
        for binding in contract["cross_surface_memory_intake_surface_bindings"]
    }
    if set(bindings) != set(REQUIRED_SURFACES):
        failures.append("memory intake surface bindings drifted")
    if bindings["Local Coding"]["feed_ref"] != "memory-intake-proposal:local-coding":
        failures.append("memory intake local coding binding drifted")

    module_feeds = {item["module"]: item for item in today["module_feed_contract"]}
    memory_feed = module_feeds.get("Memory", {})
    if memory_feed.get("status") != (
        "implemented_review_queue_quality_and_intake_metadata_contract"
    ):
        failures.append("Today module feed does not mark Memory intake implemented")
    if CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF not in (
        memory_feed.get("current_feed_refs") or []
    ):
        failures.append("Today module feed missing memory intake contract ref")

    timeline_kinds = {item["item_kind"] for item in today["evidence_timeline"]}
    if "cross_surface_memory_intake_proposal_ref" not in timeline_kinds:
        failures.append("Evidence Timeline missing memory intake proposal ref")
    intake_item = next(
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "cross_surface_memory_intake_proposal_ref"
    )
    if intake_item["approval_ref_authority"] is not False:
        failures.append("memory intake evidence grants approval authority")
    if intake_item["memory_truth_authority"] is not False:
        failures.append("memory intake evidence grants truth authority")
    if intake_item["context_injection_authorized"] is not False:
        failures.append("memory intake evidence authorizes context injection")
    if intake_item["raw_evidence_included"] is not False:
        failures.append("memory intake evidence includes raw evidence")
    if set(REQUIRED_BLOCKED_REFS) - set(intake_item["blocked_states"]):
        failures.append("memory intake evidence item missing blocked-state refs")

    serialized = json.dumps(contract, sort_keys=True).lower()
    for forbidden in FORBIDDEN_SNIPPETS:
        if forbidden in serialized:
            failures.append(f"live memory intake contains {forbidden}")

    proposal = build_cross_surface_memory_intake_proposal(surface="Chat")
    for flag in DENIED_FLAGS:
        payload = proposal.model_dump(mode="json")
        payload[flag] = True
        try:
            CrossSurfaceMemoryIntakeProposal(**payload)
        except ValidationError:
            continue
        failures.append(f"CrossSurfaceMemoryIntakeProposal accepted {flag}=true")

    unsafe = proposal.model_dump(mode="json")
    unsafe["safe_summary"] = "raw file material"
    try:
        CrossSurfaceMemoryIntakeProposal(**unsafe)
    except ValidationError:
        pass
    else:
        failures.append("CrossSurfaceMemoryIntakeProposal accepted unsafe summary")


def main() -> int:
    failures: list[str] = []
    schema = json.loads(_read(SCHEMA))

    required_snippets = [
        "contract-ref:cross-surface-memory-intake:v1",
        "proposal_ref",
        "candidate_ref",
        "review_queue_ref",
        "missing_evidence_refs",
        "blocked-state:no-automatic-memory-write",
        "blocked-state:no-context-injection",
        "blocked-state:no-provider-call",
        "blocked-state:no-browser-import",
        "blocked-state:no-shell-history-import",
        "blocked-state:no-raw-file-import",
        "memory_write_authorized",
        "context_injection_authorized",
        "provider_call_enabled",
        "account_fetch_enabled",
    ]
    _require(
        MEMORY_INTAKE,
        [
            "CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF",
            "CrossSurfaceMemoryIntakeProposal",
            "cross_surface_memory_intake_proposals",
            "cross_surface_memory_intake_surface_bindings",
        ],
        failures,
    )
    _require(MEMORY_INIT, ["CrossSurfaceMemoryIntakeProposal"], failures)
    _require(CHAT_OPERATOR, ["memory-intake-proposal:chat"], failures)
    _require(PLAN_ENVELOPES, ["memory-intake-proposal:plans"], failures)
    _require(CODE_WORKBENCH, ["memory-intake-proposal:local-coding"], failures)
    _require(
        FOUNDER_LOOP,
        [
            "cross_surface_memory_intake_contract_ref",
            "cross_surface_memory_intake_proposals",
            "cross_surface_memory_intake_proposal_ref",
        ],
        failures,
    )
    _require(FRONTEND_TYPES, ["FounderLoopCrossSurfaceMemoryIntakeProposal"], failures)
    _require(FRONTEND_PANEL, ["Memory intake", "MemoryIntakeProposalCard"], failures)
    _require(FRONTEND_MOCK, ["crossSurfaceMemoryIntakeContractRef"], failures)
    _require(FOCUSED_TEST, ["CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF"], failures)
    _require(STORAGE_TEST, ["CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF"], failures)
    _require(API_TEST, ["CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF"], failures)
    _require(APP_TEST, ["Memory intake"], failures)
    _require(SCHEMA, ["cross_surface_memory_intake_contract_ref"], failures)
    _require(CONTRACT_DOC, required_snippets, failures)

    for path in [
        MEMORY_INTAKE,
        MEMORY_INIT,
        CHAT_OPERATOR,
        PLAN_ENVELOPES,
        CODE_WORKBENCH,
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

    _require_absent(MEMORY_INTAKE, FORBIDDEN_PYTHON_RUNTIME_CALLS, failures)
    _validate_live_contract(schema, failures)

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    print("UAA-P1-076 cross-surface memory intake verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
