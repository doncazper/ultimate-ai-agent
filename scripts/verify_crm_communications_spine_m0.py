#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.crm import (  # noqa: E402
    CRM_COMMUNICATIONS_CANONICAL_NOUNS,
    CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS,
    CRM_COMMUNICATIONS_REQUIRED_STATE_WORDS,
    CRM_COMMUNICATIONS_SPINE_CONTRACT_REF,
    CrmWorkspaceKind,
    build_crm_communications_spine_contract,
    validate_crm_communications_spine_contract,
)


CONTRACT = ROOT / "src/ultimate_ai_agent/core/crm/contracts.py"
INIT = ROOT / "src/ultimate_ai_agent/core/crm/__init__.py"
DOC = ROOT / "docs/strategy/CRM_COMMUNICATIONS_SPINE_M0.md"
PRODUCT_LANGUAGE = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
CANONICAL_MAP = ROOT / "docs/canonical/CANONICAL_DOC_MAP.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
TEST = ROOT / "tests/test_crm_communications_spine_contracts.py"

BANNED_RUNTIME_MARKERS = [
    "requests",
    "httpx",
    "urllib.request",
    "urllib3",
    "http.client",
    "subprocess",
    "openai",
    "anthropic",
    "playwright",
    "selenium",
    "firecrawl",
    "browserbase",
]

DENIED_FLAG_NAMES = [
    "backend_routes_added",
    "control_center_route_added",
    "connector_runtime_enabled",
    "connector_write_enabled",
    "account_sync_enabled",
    "send_enabled",
    "calendar_write_enabled",
    "silent_merge_enabled",
    "silent_contact_creation_enabled",
    "provider_model_call_enabled",
    "live_web_enabled",
    "browser_runtime_enabled",
    "production_authority_enabled",
]

ACTIVE_SUMMARY_REQUIRED = [
    "CRM + Communications Spine M0",
    "CRM_COMMUNICATIONS_SPINE_M0.md",
    "no /crm",
    "no backend endpoints",
    "no connector runtime",
    "no connector writes",
    "no sends",
    "no calendar writes",
    "no silent merges",
    "no silent contact creation",
    "no provider/model calls",
    "no live web",
    "no browser runtime",
    "no public beta",
    "no production authority",
]

DOC_REQUIRED = [
    "CRM + Communications Spine M0",
    "Global Identity -> Workspace Context -> Pipeline Object -> Communications Spine -> Work Queue / Proposal -> Action Inbox / Evidence / Memory",
    "contract-only",
    "Person",
    "Organization",
    "Workspace",
    "WorkspaceContext",
    "PipelineObject",
    "CommunicationItem",
    "WorkQueue",
    "GovernedPlaybook",
    "EngagementSignal",
    "IdentityMatchCandidate",
    "CrmProposal",
    "PresetPack",
    "mock_only",
    "fixture_only",
    "read_only",
    "proposal_only",
    "blocked",
    "implemented",
    "no /crm UI",
    "no backend endpoints",
    "no connector runtime",
    "no connector writes",
    "no sends",
    "no calendar writes",
    "no silent merges",
    "no silent contact creation",
    "no provider/model calls",
    "no live web",
    "no production authority",
]


def _fail(message: str) -> None:
    raise SystemExit(f"CRM Communications Spine M0 verifier failed: {message}")


def _read(path: Path) -> str:
    if not path.exists():
        _fail(f"missing required file {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _require(path: Path, fragments: list[str]) -> None:
    text = _read(path)
    compact = " ".join(text.split())
    lowered = compact.lower()
    for fragment in fragments:
        if fragment.lower() not in lowered:
            _fail(f"{path.relative_to(ROOT)} missing fragment: {fragment}")


def _assert_contract() -> None:
    contract = validate_crm_communications_spine_contract(
        build_crm_communications_spine_contract()
    )
    if contract.contract_ref != CRM_COMMUNICATIONS_SPINE_CONTRACT_REF:
        _fail("contract ref drifted")
    if contract.canonical_nouns != CRM_COMMUNICATIONS_CANONICAL_NOUNS:
        _fail("canonical nouns drifted")
    if contract.state_words != CRM_COMMUNICATIONS_REQUIRED_STATE_WORDS:
        _fail("state words drifted")
    if {preset.workspace_kind for preset in contract.preset_packs} != set(CrmWorkspaceKind):
        _fail("missing one or more first-class preset packs")
    missing_blockers = set(CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS) - set(
        contract.blocked_authority_refs
    )
    if missing_blockers:
        _fail(f"missing blocked authority refs: {sorted(missing_blockers)}")
    payload = contract.model_dump(mode="json")
    for field_name in DENIED_FLAG_NAMES:
        if payload.get(field_name) is not False:
            _fail(f"contract does not deny {field_name}")
    if payload["authority"]["route_or_ui_visibility_grants_authority"] is not False:
        _fail("visibility is being treated as authority")


def _assert_contract_source() -> None:
    for path in [CONTRACT, INIT]:
        text = _read(path).lower()
        for marker in BANNED_RUNTIME_MARKERS:
            if marker in text:
                _fail(f"{path.relative_to(ROOT)} contains banned runtime marker {marker}")
    _require(
        CONTRACT,
        [
            "CRM_COMMUNICATIONS_CANONICAL_NOUNS",
            "CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS",
            "CrmCommunicationsSpineContract",
            "CrmCommunicationItem",
            "CrmProposal",
            "validate_crm_communications_spine_contract",
            "CRM_PRIVATE_FIELD_DENIED",
            "CRM_PRIVATE_CONTENT_DENIED",
        ],
    )
    _require(
        INIT,
        [
            "CrmCommunicationsSpineContract",
            "CrmCommunicationItem",
            "CrmProposal",
            "build_crm_communications_spine_contract",
        ],
    )


def _assert_docs() -> None:
    _require(DOC, DOC_REQUIRED)
    _require(
        PRODUCT_LANGUAGE,
        [
            "CRM and Communications copy",
            "fixture_only",
            "read_only",
            "proposal_only",
            "Drafts are not sends",
            "Calendar proposals are not calendar writes",
            "silent merges",
            "silent contact creation",
            "browser runtime",
        ],
    )
    for path in [DOCS_README, DOCS_INDEX, CANONICAL_MAP, TRUTH_PACKET, CURRENT_BOARD, FCC_BOARD]:
        _require(path, ACTIVE_SUMMARY_REQUIRED)


def _assert_no_m0_routes() -> None:
    route_markers = ["/control-center/crm", "control-center/crm", '"/crm"', "path: \"/crm\""]
    for root in [ROOT / "src", ROOT / "apps"]:
        for path in root.rglob("*"):
            if path.is_dir() or path.suffix not in {".py", ".ts", ".tsx"}:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for marker in route_markers:
                if marker.lower() in text:
                    _fail(f"M0 must not add CRM route marker {marker} in {path.relative_to(ROOT)}")


def _assert_tests() -> None:
    _require(
        TEST,
        [
            "test_crm_m0_builds_contract_with_canonical_nouns_and_locked_architecture",
            "test_crm_m0_includes_all_five_first_class_preset_packs",
            "test_crm_m0_contract_requires_all_blocked_authority_refs",
            "test_crm_m0_contract_rejects_authority_creep_flags",
            "test_crm_m0_proposals_remain_proposal_only",
            "test_crm_m0_communication_items_are_metadata_only_not_sends",
            "test_crm_m0_contract_rejects_raw_extra_fields_without_echoing_private_content",
            "test_crm_m0_contract_rejects_raw_private_values_without_echoing_content",
            "test_crm_m0_direct_evidence_models_reject_private_marked_text",
            "test_crm_m0_direct_signal_models_reject_private_marked_text",
            "test_crm_m0_package_has_no_runtime_network_provider_browser_or_subprocess_imports",
        ],
    )


def main() -> int:
    _assert_contract()
    _assert_contract_source()
    _assert_docs()
    _assert_no_m0_routes()
    _assert_tests()
    print("CRM Communications Spine M0 verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
