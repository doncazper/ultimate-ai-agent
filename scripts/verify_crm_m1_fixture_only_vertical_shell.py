#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.crm import (  # noqa: E402
    CRM_M1_FIXTURE_CONTRACT_REF,
    CRM_M1_REQUIRED_BLOCKED_REFS,
    CRM_M1_REQUIRED_STATE_LABELS,
    CRM_M1_VERTICAL_ORDER,
    CrmWorkspaceKind,
    build_crm_m1_fixture_map,
    validate_crm_m1_fixture_map,
)


FIXTURE_SOURCE = ROOT / "src/ultimate_ai_agent/core/crm/fixtures.py"
DOC = ROOT / "docs/control_center/CRM_M1_FIXTURE_ONLY_VERTICAL_SHELL.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
PRODUCT_LANGUAGE = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"
PROMPTS = ROOT / "docs/prompts/crm_product_sequence.md"
TEST = ROOT / "tests/test_crm_m1_fixture_only_vertical_shell.py"

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

DOC_REQUIRED = [
    "CRM M1 Fixture-Only Vertical Shell",
    "Prompt 01",
    "Prompt 02",
    "Prompt 03",
    "Prompt 04",
    "Prompt 05",
    "Prompt 06",
    "Prompt 07",
    "Prompt 08",
    "Prompt 09",
    "Prompt 10",
    "Prompt 11",
    "Prompt 12",
    "Real Estate/Realtor",
    "Healthcare",
    "Finance/Insurance",
    "Retail/E-commerce",
    "Professional Services",
    "fixture_only",
    "read_only",
    "proposal_only",
    "blocked",
    "no connector runtime",
    "no connector writes",
    "no external CRM writes",
    "no account sync",
    "no sends",
    "no calendar writes",
    "no provider/model calls",
    "no live web",
    "no browser automation",
    "no hidden context injection",
    "no public beta",
    "no production authority",
]

INDEX_REQUIRED = [
    "CRM M1 Fixture-Only Vertical Shell",
    "CRM_M1_FIXTURE_ONLY_VERTICAL_SHELL.md",
    "verify_crm_m1_fixture_only_vertical_shell.py",
    "test_crm_m1_fixture_only_vertical_shell.py",
]


def _fail(message: str) -> None:
    raise SystemExit(f"CRM M1 fixture-only verifier failed: {message}")


def _read(path: Path) -> str:
    if not path.exists():
        _fail(f"missing required file {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _require(path: Path, fragments: list[str]) -> None:
    text = " ".join(_read(path).split()).lower()
    for fragment in fragments:
        if fragment.lower() not in text:
            _fail(f"{path.relative_to(ROOT)} missing fragment: {fragment}")


def _assert_fixture_map() -> None:
    fixture_map = validate_crm_m1_fixture_map(build_crm_m1_fixture_map())
    if fixture_map.contract_ref != CRM_M1_FIXTURE_CONTRACT_REF:
        _fail("contract ref drifted")
    if fixture_map.state_labels != CRM_M1_REQUIRED_STATE_LABELS:
        _fail("state labels drifted")
    if [vertical.workspace_kind for vertical in fixture_map.verticals] != CRM_M1_VERTICAL_ORDER:
        _fail("vertical order drifted")
    if {vertical.workspace_kind for vertical in fixture_map.verticals} != set(CrmWorkspaceKind):
        _fail("missing one or more CRM M1 verticals")
    missing_blockers = set(CRM_M1_REQUIRED_BLOCKED_REFS) - set(
        fixture_map.blocked_authority_refs
    )
    if missing_blockers:
        _fail(f"missing blocked authority refs: {sorted(missing_blockers)}")
    payload = fixture_map.model_dump(mode="json")
    denied_flags = [
        "backend_read_model_added",
        "backend_route_added",
        "control_center_route_added",
        "connector_runtime_enabled",
        "connector_write_enabled",
        "account_sync_enabled",
        "send_enabled",
        "calendar_write_enabled",
        "contact_import_enabled",
        "silent_identity_merge_enabled",
        "provider_model_call_enabled",
        "live_web_enabled",
        "browser_runtime_enabled",
        "hidden_context_injection_enabled",
        "public_beta_claimed",
        "production_authority_enabled",
    ]
    for field_name in denied_flags:
        if payload.get(field_name) is not False:
            _fail(f"fixture map does not deny {field_name}")


def _assert_no_runtime_or_routes() -> None:
    for path in [FIXTURE_SOURCE]:
        text = _read(path).lower()
        for marker in BANNED_RUNTIME_MARKERS:
            if marker in text:
                _fail(f"{path.relative_to(ROOT)} contains banned runtime marker {marker}")
    route_markers = ['"/crm"', "path: \"/crm\"", "/control-center/crm", "control-center/crm"]
    for root in [ROOT / "src", ROOT / "apps"]:
        for path in root.rglob("*"):
            if path.is_dir() or path.suffix not in {".py", ".ts", ".tsx"}:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for marker in route_markers:
                if marker in text:
                    _fail(f"CRM M1 must not add route marker {marker} in {path.relative_to(ROOT)}")


def main() -> int:
    _assert_fixture_map()
    _assert_no_runtime_or_routes()
    _require(DOC, DOC_REQUIRED)
    for path in [DOCS_README, DOCS_INDEX, TRUTH_PACKET, CURRENT_BOARD]:
        _require(path, INDEX_REQUIRED)
    _require(
        PRODUCT_LANGUAGE,
        [
            "CRM and Communications copy",
            "fixture/read/proposal posture",
            "connector runtime",
            "public beta",
            "production authority",
        ],
    )
    _require(PROMPTS, ["Prompt 00", "Prompt 12", "Global CRM Authority Boundary"])
    _require(TEST, ["test_crm_m1_fixture_map_builds_prompt_ordered_verticals"])
    print("CRM M1 fixture-only vertical shell verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
