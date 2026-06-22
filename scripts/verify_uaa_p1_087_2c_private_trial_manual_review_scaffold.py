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
    PrivateOperatorTrialManualReviewScaffold,
    build_private_operator_trial_manual_review_scaffold,
)


CONTRACT_DOC = (
    "docs/macos/UAA_P1_087_2C_PRIVATE_TRIAL_MANUAL_REVIEW_SCAFFOLD.md"
)
SCAFFOLD_JSON = "docs/macos/private_operator_trial_manual_review_scaffold_v1.json"
SEQUENCE_DOC = "docs/macos/UAA_P1_087_PRIVATE_OPERATOR_BOOT_AND_UI_TRIAL_SEQUENCE.md"
FRONTEND_ROUTES = "apps/control-center/src/routes.tsx"
FRONTEND_PANEL = "apps/control-center/src/components/PrivateOperatorTrialPanel.tsx"
FRONTEND_PACKET = "apps/control-center/src/mocks/privateOperatorTrialPacket.ts"
APP_TEST = "apps/control-center/src/App.test.tsx"
FOCUSED_TEST = (
    "tests/test_uaa_p1_087_2c_private_trial_manual_review_scaffold.py"
)
SUCCESS_MESSAGE = (
    "UAA-P1-087.2c private trial manual review scaffold verification passed."
)

REQUIRED_DOC_SNIPPETS = {
    CONTRACT_DOC: [
        "Status: implemented as an unanswered manual review intake scaffold",
        "UAA-P1-087.2c does not complete full UAA-P1-087.2",
        "docs/macos/private_operator_trial_manual_review_scaffold_v1.json",
        "unanswered_pending_manual_review",
        "manual_review_deferred_pending_implementation",
        "adds no backend endpoint",
    ],
    SEQUENCE_DOC: [
        "`UAA-P1-087.2c` Private Trial Manual Review Intake Scaffold",
        "Full `UAA-P1-087.2` is deferred until more Founder Loop implementation exists",
        "`FCC-V1-000`",
    ],
    FRONTEND_ROUTES: [
        'path: "/private-trial"',
        'label: "Trial Packet"',
        'status: "087.2a-2c packet"',
        "<PrivateOperatorTrialPanel />",
    ],
    FRONTEND_PANEL: [
        "UAA-P1-087.2c adds unanswered manual",
        "Manual review scaffold",
        "scaffold.reviewState",
        "unanswered_pending_manual_review",
        "missingImplementationRefs",
    ],
    FRONTEND_PACKET: [
        "milestone:uaa-p1-087.2c",
        "scaffold-ref:private-operator-trial-manual-review:v1",
        "manual_review_deferred_pending_implementation",
        "pending-answer:private-trial:crm-lite-follow-ups",
        "missing-implementation:founder-loop:action-decision-receipts",
        "deferred-decision:private-trial:full-087-2-acceptance",
    ],
    APP_TEST: [
        "milestone:uaa-p1-087.2c",
        "scaffold-ref:private-operator-trial-manual-review:v1",
        "manual_review_deferred_pending_implementation",
        "unanswered_pending_manual_review",
        "pending-answer:private-trial:crm-lite-follow-ups",
    ],
    FOCUSED_TEST: [
        "test_private_operator_trial_manual_review_scaffold_stays_unanswered",
        "test_private_operator_trial_manual_review_scaffold_rejects_answers",
        "test_p1_087_2c_verifier_flags_answer_claim",
    ],
}

FORBIDDEN_CLAIMS = [
    "public beta is ready",
    "private beta is ready",
    "private beta ready",
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
    "onClick",
    "fetch(",
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
    scaffold_text: str | None = None,
    active_doc_text: dict[str, str] | None = None,
    check_files: bool = True,
) -> list[str]:
    failures: list[str] = []
    _append_scaffold_failures(failures, scaffold_text)
    if check_files:
        _append_static_file_failures(failures)
    _append_completion_claim_failures(failures, active_doc_text)
    return failures


def _append_scaffold_failures(
    failures: list[str],
    scaffold_text: str | None,
) -> None:
    try:
        raw = scaffold_text if scaffold_text is not None else read_text(SCAFFOLD_JSON)
        scaffold = PrivateOperatorTrialManualReviewScaffold.model_validate_json(raw)
    except Exception as exc:  # noqa: BLE001
        failures.append(f"private trial manual review scaffold failed validation: {exc}")
        return

    built = build_private_operator_trial_manual_review_scaffold()
    if scaffold.contract_ref != PRIVATE_OPERATOR_TRIAL_CONTRACT_REF:
        failures.append("private trial manual review scaffold contract ref drifted")
    if scaffold.milestone_ref != "milestone:uaa-p1-087.2c":
        failures.append("private trial manual review scaffold must be UAA-P1-087.2c")
    if scaffold.status != built.status:
        failures.append("private trial manual review scaffold status drifted from builder")
    if scaffold.review_state != "manual_review_deferred_pending_implementation":
        failures.append("private trial manual review scaffold must stay deferred")
    if {item.surface for item in scaffold.review_items} != set(
        PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES
    ):
        failures.append("private trial manual review scaffold missing required surfaces")
    if {item.answer_state for item in scaffold.review_items} != {
        "unanswered_pending_manual_review"
    }:
        failures.append("private trial manual review scaffold must not contain answers")
    if not all(item.pending_answer_ref for item in scaffold.review_items):
        failures.append("private trial manual review scaffold missing pending answer refs")
    if set(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS) - set(
        scaffold.blocked_state_refs
    ):
        failures.append("private trial manual review scaffold missing required blocked refs")
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
        if getattr(scaffold, field_name) is not False:
            failures.append(
                f"private trial manual review scaffold enables denied flag {field_name}"
            )

    serialized = json.dumps(scaffold.model_dump(mode="json"), sort_keys=True).lower()
    for forbidden in [
        "raw prompt",
        "raw response",
        "provider payload",
        "raw screenshot",
        "raw ocr",
        "raw log",
        "api key",
        "authorization",
        "password",
        "/users/",
        "/home/",
        "/var/",
        "/etc/",
    ]:
        if forbidden in serialized:
            failures.append(
                f"private trial manual review scaffold contains unsafe marker {forbidden!r}"
            )


def _append_static_file_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(failures, REQUIRED_DOC_SNIPPETS)
    append_forbidden_claims(
        failures,
        [CONTRACT_DOC, SCAFFOLD_JSON, FRONTEND_PANEL, FRONTEND_PACKET],
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
        failures.append("P1-087.2c must not add a backend private-trial route")


def _append_completion_claim_failures(
    failures: list[str],
    active_doc_text: dict[str, str] | None,
) -> None:
    full_completion_patterns = [
        re.compile(
            r"uaa-p1-087\.2(?![a-z0-9])(?:(?!uaa-p1-)[^\n]){0,80}\b(done|complete|implemented)\b"
        ),
        re.compile(
            r"\b(done|completed|implemented)\s+(?:full\s+)?uaa-p1-087\.2(?![a-z0-9])\b"
        ),
    ]
    manual_answer_patterns = [
        re.compile(
            r"uaa-p1-087\.2c[^\n]{0,120}\b(accepted|revised|answered|passed)\b"
        ),
        re.compile(r"\bmanual review answers recorded\b"),
        re.compile(r"\bmanual review complete\b"),
        re.compile(r"\bfounder findings accepted\b"),
    ]
    docs = active_doc_text or {
        path: read_text(path)
        for path in ACTIVE_TRUTH_DOCS
        if (ROOT / path).exists()
    }
    for path, text in docs.items():
        lowered = text.lower()
        for pattern in full_completion_patterns:
            match = pattern.search(lowered)
            if match and not _is_deferred_full_087_2_reference(match.group(0)):
                failures.append(
                    f"{path} claims full UAA-P1-087.2 completion; only incremental UAA-P1-087.2a/2b/2c is allowed"
                )
                break
        for pattern in manual_answer_patterns:
            if pattern.search(lowered):
                failures.append(
                    f"{path} claims manual review answers for UAA-P1-087.2c; answers must stay pending"
                )
                break


def _is_deferred_full_087_2_reference(match_text: str) -> bool:
    return any(
        marker in match_text
        for marker in [
            "deferred",
            "planned",
            "blocked",
            "not complete",
            "does not complete",
            "missing",
        ]
    )


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
