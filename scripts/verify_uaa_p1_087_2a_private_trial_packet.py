#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    append_missing_doc_snippets,
    print_failures_or_success,
    read_text,
)
from ultimate_ai_agent.core.readiness import (  # noqa: E402
    PRIVATE_OPERATOR_TRIAL_CONTRACT_REF,
    PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS,
    PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES,
    PrivateOperatorTrialPacket,
    build_private_operator_trial_packet,
)


CONTRACT_DOC = (
    "docs/macos/UAA_P1_087_2A_PRIVATE_TRIAL_PACKET_AND_UI_TUNING_SURFACE.md"
)
PACKET_JSON = "docs/macos/private_operator_trial_packet_v1.json"
SEQUENCE_DOC = "docs/macos/UAA_P1_087_PRIVATE_OPERATOR_BOOT_AND_UI_TRIAL_SEQUENCE.md"
FRONTEND_ROUTES = "apps/control-center/src/routes.tsx"
FRONTEND_PANEL = "apps/control-center/src/components/PrivateOperatorTrialPanel.tsx"
FRONTEND_PACKET = "apps/control-center/src/mocks/privateOperatorTrialPacket.ts"
APP_TEST = "apps/control-center/src/App.test.tsx"
FOCUSED_TEST = "tests/test_uaa_p1_087_2a_private_trial_packet.py"
SUCCESS_MESSAGE = "UAA-P1-087.2a private trial packet verification passed."

REQUIRED_DOC_SNIPPETS = {
    CONTRACT_DOC: [
        "Status: implemented as an incremental local/private trial packet",
        "UAA-P1-087.2a prepares the full UAA-P1-087.2",
        "docs/macos/private_operator_trial_packet_v1.json",
        "The Control Center exposes the packet at `/private-trial`",
        "Full UAA-P1-087.2 Gate",
        "UAA-P1-087.2 should remain planned",
        "adds no backend endpoint",
    ],
    SEQUENCE_DOC: [
        "`UAA-P1-087.2` In-Person Private Operator UI Functional Tuning",
        "Do not jump to `UAA-P1-087.3`",
    ],
    FRONTEND_ROUTES: [
        'path: "/private-trial"',
        'label: "Trial Packet"',
        'status: "087.2a packet"',
        "<PrivateOperatorTrialPanel />",
    ],
    FRONTEND_PANEL: [
        "UAA-P1-087.2a prepares",
        "Full UAA-P1-087.2 still needs local/private acceptance findings.",
        "adds no backend route",
        "connector write",
        "blockedStateRefs",
    ],
    FRONTEND_PACKET: [
        PRIVATE_OPERATOR_TRIAL_CONTRACT_REF,
        "milestone:uaa-p1-087.2a",
        "private-trial-check:local-boot",
        "private-trial-check:crm-lite-follow-ups",
        "blocked-state:openwebui-secondary-only",
    ],
    APP_TEST: [
        '"/private-trial"',
        "Private Operator Trial",
        "milestone:uaa-p1-087.2a",
        "Full UAA-P1-087.2 still needs local\\/private acceptance findings",
    ],
    FOCUSED_TEST: [
        "test_private_operator_trial_packet_defines_safe_checklist",
        "test_private_operator_trial_rejects_authority_creep_and_unsafe_text",
        "test_p1_087_2a_verifier_flags_full_087_2_completion_claim",
    ],
}

FORBIDDEN_CLAIMS = [
    "public beta is ready",
    "private beta is ready",
    "public release ready",
    "production authority is granted",
    "production ready",
    "signed installer is ready",
    "notarized app is ready",
    "launchagent is installed",
    "daemon is installed",
    "openwebui plugin is installed",
    "action inbox decisions are shipped",
    "chat durable receipts are shipped",
    "memory accept/correct/reject is shipped",
    "evidence timeline productization is shipped",
]

FORBIDDEN_RUNTIME_SNIPPETS = [
    "subprocess.run",
    "subprocess.Popen",
    "requests.",
    "httpx.",
    "openai.",
    "playwright",
    "computer_use(",
    "connector.write",
    "memory_write(",
    "execute_action",
]

ACTIVE_TRUTH_DOCS = [
    "README.md",
    "docs/README.md",
    "docs/DOCUMENTATION_INDEX.md",
    "docs/canonical/09_roadmap.md",
    "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    "docs/kanban/current_board.md",
    "docs/kanban/founder_command_center_board.md",
    "docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md",
    "docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md",
    "docs/codex/CODEX_EXECUTION_PROMPTS.md",
]


def verify(
    *,
    packet_text: str | None = None,
    active_doc_text: dict[str, str] | None = None,
    check_files: bool = True,
) -> list[str]:
    failures: list[str] = []
    _append_packet_failures(failures, packet_text)
    if check_files:
        _append_static_file_failures(failures)
    _append_completion_claim_failures(failures, active_doc_text)
    return failures


def _append_packet_failures(failures: list[str], packet_text: str | None) -> None:
    try:
        raw = packet_text if packet_text is not None else read_text(PACKET_JSON)
        packet = PrivateOperatorTrialPacket.model_validate_json(raw)
    except Exception as exc:  # noqa: BLE001
        failures.append(f"private trial packet failed validation: {exc}")
        return

    built = build_private_operator_trial_packet()
    if packet.contract_ref != PRIVATE_OPERATOR_TRIAL_CONTRACT_REF:
        failures.append("private trial packet contract ref drifted")
    if packet.milestone_ref != "milestone:uaa-p1-087.2a":
        failures.append("private trial packet must be incremental UAA-P1-087.2a")
    if packet.status != built.status:
        failures.append("private trial packet status drifted from builder")
    if {item.surface for item in packet.checklist_items} != set(
        PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES
    ):
        failures.append("private trial packet missing required checklist surfaces")
    if set(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS) - set(
        packet.blocked_state_refs
    ):
        failures.append("private trial packet missing required blocked refs")
    for field_name in [
        "public_beta_claim_enabled",
        "public_distribution_claim_enabled",
        "production_readiness_claim_enabled",
        "production_authority_enabled",
        "connector_write_enabled",
        "memory_write_authorized",
        "action_execution_enabled",
        "code_apply_execution_enabled",
        "runtime_authority_added",
        "backend_route_added",
    ]:
        if getattr(packet, field_name) is not False:
            failures.append(f"private trial packet enables denied flag {field_name}")

    serialized = json.dumps(packet.model_dump(mode="json"), sort_keys=True).lower()
    for forbidden in [
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
    ]:
        if forbidden in serialized:
            failures.append(f"private trial packet contains unsafe marker {forbidden!r}")


def _append_static_file_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(failures, REQUIRED_DOC_SNIPPETS)
    append_forbidden_claims(
        failures,
        [CONTRACT_DOC, PACKET_JSON, FRONTEND_PANEL, FRONTEND_PACKET],
        FORBIDDEN_CLAIMS,
    )
    for path in [FRONTEND_PANEL, FRONTEND_PACKET, FRONTEND_ROUTES]:
        text = read_text(path)
        for forbidden in FORBIDDEN_RUNTIME_SNIPPETS:
            if forbidden in text:
                failures.append(f"{path} contains forbidden runtime snippet {forbidden!r}")
    api_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src/ultimate_ai_agent/api").rglob("*.py")
    )
    if "private-trial" in api_source or "private_operator_trial" in api_source:
        failures.append("P1-087.2a must not add a backend private-trial route")


def _append_completion_claim_failures(
    failures: list[str],
    active_doc_text: dict[str, str] | None,
) -> None:
    full_completion_patterns = [
        re.compile(
            r"uaa-p1-087\.2(?!a)(?:(?!uaa-p1-)[^\n]){0,80}\b(done|complete|implemented)\b"
        ),
        re.compile(r"\b(done|completed|implemented)\s+(?:full\s+)?uaa-p1-087\.2(?!a)\b"),
    ]
    docs = active_doc_text or {
        path: read_text(path)
        for path in ACTIVE_TRUTH_DOCS
        if (ROOT / path).exists()
    }
    for path, text in docs.items():
        lowered = text.lower()
        for pattern in full_completion_patterns:
            if pattern.search(lowered):
                failures.append(
                    f"{path} claims full UAA-P1-087.2 completion; only UAA-P1-087.2a is allowed"
                )
                break


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
