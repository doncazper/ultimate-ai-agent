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
    PrivateOperatorTrialAcceptanceLedger,
    build_private_operator_trial_acceptance_ledger,
)


CONTRACT_DOC = (
    "docs/macos/UAA_P1_087_2B_PRIVATE_TRIAL_ACCEPTANCE_LEDGER.md"
)
LEDGER_JSON = "docs/macos/private_operator_trial_acceptance_ledger_v1.json"
SEQUENCE_DOC = "docs/macos/UAA_P1_087_PRIVATE_OPERATOR_BOOT_AND_UI_TRIAL_SEQUENCE.md"
FRONTEND_PANEL = "apps/control-center/src/components/PrivateOperatorTrialPanel.tsx"
FRONTEND_PACKET = "apps/control-center/src/mocks/privateOperatorTrialPacket.ts"
APP_TEST = "apps/control-center/src/App.test.tsx"
FOCUSED_TEST = "tests/test_uaa_p1_087_2b_private_trial_acceptance_ledger.py"
SUCCESS_MESSAGE = "UAA-P1-087.2b private trial acceptance ledger verification passed."

REQUIRED_DOC_SNIPPETS = {
    CONTRACT_DOC: [
        "Status: implemented as an incremental acceptance ledger",
        "UAA-P1-087.2b does not complete full UAA-P1-087.2",
        "docs/macos/private_operator_trial_acceptance_ledger_v1.json",
        "manual smoke step refs",
        "pending_operator_review",
        "adds no backend endpoint",
    ],
    SEQUENCE_DOC: [
        "`UAA-P1-087.2b` Private Trial Findings Capture And Acceptance Ledger",
        "Full `UAA-P1-087.2` still requires accepted or revised private-trial findings",
    ],
    FRONTEND_PANEL: [
        "UAA-P1-087.2b adds the acceptance ledger",
        "Acceptance ledger",
        "manualSmokeStepRefs",
        "surfaceReviews",
        "pending_operator_review",
    ],
    FRONTEND_PACKET: [
        "milestone:uaa-p1-087.2b",
        "ledger-ref:private-operator-trial-acceptance:v1",
        "manual-smoke-step:private-trial:boot-control-center",
        "acceptance-question:private-trial:memory-confidence",
        "tuning-decision:private-trial:pending-memory-review-emphasis",
        "finding-ref:private-trial:pending:crm-lite-follow-ups",
    ],
    APP_TEST: [
        "milestone:uaa-p1-087.2b",
        "ledger-ref:private-operator-trial-acceptance:v1",
        "manual-smoke-step:private-trial:boot-control-center",
        "acceptance-question:private-trial:memory-confidence",
        "Full UAA-P1-087.2 still needs accepted or revised local\\/private findings",
    ],
    FOCUSED_TEST: [
        "test_private_operator_trial_acceptance_ledger_defines_pending_reviews",
        "test_private_operator_trial_acceptance_ledger_rejects_authority_creep",
        "test_p1_087_2b_verifier_flags_full_087_2_completion_claim",
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
    ledger_text: str | None = None,
    active_doc_text: dict[str, str] | None = None,
    check_files: bool = True,
) -> list[str]:
    failures: list[str] = []
    _append_ledger_failures(failures, ledger_text)
    if check_files:
        _append_static_file_failures(failures)
    _append_completion_claim_failures(failures, active_doc_text)
    return failures


def _append_ledger_failures(failures: list[str], ledger_text: str | None) -> None:
    try:
        raw = ledger_text if ledger_text is not None else read_text(LEDGER_JSON)
        ledger = PrivateOperatorTrialAcceptanceLedger.model_validate_json(raw)
    except Exception as exc:  # noqa: BLE001
        failures.append(f"private trial acceptance ledger failed validation: {exc}")
        return

    built = build_private_operator_trial_acceptance_ledger()
    if ledger.contract_ref != PRIVATE_OPERATOR_TRIAL_CONTRACT_REF:
        failures.append("private trial acceptance ledger contract ref drifted")
    if ledger.milestone_ref != "milestone:uaa-p1-087.2b":
        failures.append("private trial acceptance ledger must be incremental UAA-P1-087.2b")
    if ledger.status != built.status:
        failures.append("private trial acceptance ledger status drifted from builder")
    if ledger.trial_run_state != "operator_review_ready":
        failures.append("private trial acceptance ledger must be operator-review ready")
    if {review.surface for review in ledger.surface_reviews} != set(
        PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES
    ):
        failures.append("private trial acceptance ledger missing required surfaces")
    if {review.review_state for review in ledger.surface_reviews} != {
        "pending_operator_review"
    }:
        failures.append("private trial acceptance ledger must not claim accepted findings")
    if set(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS) - set(
        ledger.blocked_state_refs
    ):
        failures.append("private trial acceptance ledger missing required blocked refs")
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
        if getattr(ledger, field_name) is not False:
            failures.append(
                f"private trial acceptance ledger enables denied flag {field_name}"
            )

    serialized = json.dumps(ledger.model_dump(mode="json"), sort_keys=True).lower()
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
                f"private trial acceptance ledger contains unsafe marker {forbidden!r}"
            )


def _append_static_file_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(failures, REQUIRED_DOC_SNIPPETS)
    append_forbidden_claims(
        failures,
        [CONTRACT_DOC, LEDGER_JSON, FRONTEND_PANEL, FRONTEND_PACKET],
        FORBIDDEN_CLAIMS,
    )
    for path in [FRONTEND_PANEL, FRONTEND_PACKET]:
        text = read_text(path)
        for forbidden in FORBIDDEN_RUNTIME_SNIPPETS:
            if forbidden in text:
                failures.append(f"{path} contains forbidden runtime snippet {forbidden!r}")
    api_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src/ultimate_ai_agent/api").rglob("*.py")
    )
    if "private-trial" in api_source or "private_operator_trial" in api_source:
        failures.append("P1-087.2b must not add a backend private-trial route")


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
                    f"{path} claims full UAA-P1-087.2 completion; only incremental UAA-P1-087.2a/2b is allowed"
                )
                break


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
