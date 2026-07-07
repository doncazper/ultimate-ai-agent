#!/usr/bin/env python3
"""Validate FCC-INBOX-001 Action Inbox approval-envelope UX truth."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "FCC-INBOX-001"
DOC = ROOT / "docs/control_center/FCC_INBOX_001_APPROVAL_ENVELOPE_UX.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
GAP_MAP = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
OPERATIONAL_MATURITY_MANIFEST = (
    ROOT / "docs/control_center/operational_maturity_manifest.json"
)
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
API_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FOUNDER_LOOP_PANELS = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"
STORAGE_ACTIONS_TEST = ROOT / "tests/test_founder_loop_storage_actions.py"
STORAGE_CRUD_TEST = ROOT / "tests/test_founder_loop_storage_crud.py"
CONTROL_CENTER_ROUTE_TEST = ROOT / "tests/test_control_center_api_routes.py"

DOC_REF = "docs/control_center/FCC_INBOX_001_APPROVAL_ENVELOPE_UX.md"
VERIFIER_REF = "scripts/verify_fcc_inbox_001_approval_envelope_ux.py"
ACTION_INBOX_ROUTE = "GET /control-center/actions/inbox"
LOCAL_TASK_COMMIT_ROUTE = "POST /control-center/actions/{action_id}/local-task/commit"
LOCAL_TASK_AUTHORITY_CAPABILITY_ID = (
    "authority-capability:action-inbox:local-task-create"
)
LOCAL_TASK_AUTHORITY_DOMAIN_REF = "authority-domain-ref:workspace"
LOCAL_TASK_AUTHORITY_CAPABILITY_REF = "authority-capability-ref:write"
LOCAL_TASK_AUTHORITY_MODE_REF = "authority-mode-ref:ask-before-changes"
READ_MODEL_SOURCE = "python_core_action_inbox_read_model"


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read_text(root: Path, path: Path, failures: list[str]) -> str:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return ""
    return target.read_text(encoding="utf-8")


def _read_json(root: Path, path: Path, failures: list[str]) -> dict[str, Any]:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return {}
    try:
        loaded = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON in {rel_path.as_posix()}: {exc.msg}")
        return {}
    if not isinstance(loaded, dict):
        failures.append(f"{rel_path.as_posix()} must contain a JSON object")
        return {}
    return loaded


def _require_fragments(
    rel_path: str,
    text: str,
    fragments: list[str],
    failures: list[str],
) -> None:
    compact = " ".join(text.lower().split())
    lowered = text.lower()
    for fragment in fragments:
        needle = fragment.lower()
        if needle not in lowered and needle not in compact:
            failures.append(f"{rel_path} missing FCC-INBOX-001 fragment: {fragment}")


def _validate_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(DOC),
        text,
        [
            "Status: Implemented",
            "Primary surface: `/actions` Action Inbox",
            "Related surface: `/inbox` source-readiness",
            "_action_approval_envelope_read_model",
            "_action_receipt_visibility_read_model",
            ACTION_INBOX_ROUTE,
            LOCAL_TASK_COMMIT_ROUTE,
            "FounderLoopActionApprovalEnvelope",
            "FounderLoopActionReceiptVisibility",
            "ApprovalEnvelopeCard",
            "ReceiptVisibilityCard",
            READ_MODEL_SOURCE,
            "mock_fallback_non_authoritative",
            "Action Inbox remains rank 3 overall",
            "local_task_create",
            "does not add generic action execution",
            VERIFIER_REF,
        ],
        failures,
    )


def _validate_backend_and_frontend(root: Path, failures: list[str]) -> None:
    requirements = {
        STORAGE: [
            "def _action_approval_envelope_read_model",
            '"schema_version": "founder_loop_action_approval_envelope.v1"',
            f'"source": "{READ_MODEL_SOURCE}"',
            '"backend_owned": True',
            "exact_scope",
            "risk_class",
            "side_effect_class",
            "approval_requirement",
            "idempotency_ref",
            "expected_receipt_refs",
            "rollback_safe_disable_posture",
            "blocked_authority_refs",
            "def _action_receipt_visibility_read_model",
            '"schema_version": "founder_loop_action_receipt_visibility.v1"',
            "decision_receipt_ref",
            "local_task_commit_receipt_ref",
            "evidence_timeline_event_ref",
            "replay_posture",
            "conflict_posture",
            "review_filter_facets",
        ],
        API_TYPES: [
            "FounderLoopActionApprovalEnvelope",
            "FounderLoopActionReceiptVisibility",
            READ_MODEL_SOURCE,
            "mock_fallback_non_authoritative",
            "approval_envelope?: FounderLoopActionApprovalEnvelope",
            "receipt_visibility?: FounderLoopActionReceiptVisibility",
        ],
        FOUNDER_LOOP_PANELS: [
            "ApprovalEnvelopeCard",
            "ReceiptVisibilityCard",
            "missingActionEnvelope",
            "missingReceiptVisibility",
            "hasAuthoritativeActionReadModel",
            "mock_fallback_non_authoritative",
            "Decision controls unavailable until the local backend supplies an",
            "React does not mint authority",
            "React does not create receipts",
            "Commit local task",
            "actionReadModelAuthoritative",
        ],
        APP_TEST: [
            "filters Action Inbox lanes as presentation-only drilldowns over backend groups",
            "keeps missing Action Inbox envelope fields non-authoritative",
            "records approval through backend refresh before committing the local task lane",
            "shows replay posture from the refreshed Action Inbox read model",
            "keeps conflicting local task commits out of committed UI state",
            "Backend read model refreshed; receipt visibility now comes from the Action Inbox API.",
        ],
        STORAGE_ACTIONS_TEST: [
            "founder_loop_action_approval_envelope.v1",
            "founder_loop_action_receipt_visibility.v1",
            READ_MODEL_SOURCE,
            "local_task_commit_receipt_ref",
            "idempotency_replay_available",
            "conflicting_idempotency_payload_rejected",
        ],
        STORAGE_CRUD_TEST: [
            "approval_envelope",
            "receipt_visibility",
            "decision_receipt_ref",
            "local_task_commit_receipt_ref",
            "evidence_timeline_event_ref",
        ],
        CONTROL_CENTER_ROUTE_TEST: [
            "/control-center/actions/inbox",
            "local-task/commit",
            "test_control_center_action_local_task_commit_requires_exact_approval_and_receipts",
            "test_control_center_action_local_task_commit_denies_safe_disabled_lane",
        ],
    }
    for path, fragments in requirements.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def _validate_operational_maturity(root: Path, failures: list[str]) -> None:
    manifest = _read_json(root, OPERATIONAL_MATURITY_MANIFEST, failures)
    modules = manifest.get("modules")
    if not isinstance(modules, list):
        failures.append("operational maturity manifest must contain modules list")
        return
    action_inbox = next(
        (
            item
            for item in modules
            if isinstance(item, dict) and item.get("module_id") == "action_inbox"
        ),
        None,
    )
    if not isinstance(action_inbox, dict):
        failures.append("operational maturity manifest missing action_inbox module")
        return

    expected_values: dict[str, object] = {
        "current_rank": 3,
        "current_rank_label": "decision_receipts",
        "next_target_rank": 5,
        "real_local_mutation": False,
        "backend_owned_receipts": True,
    }
    for key, expected in expected_values.items():
        if action_inbox.get(key) != expected:
            failures.append(
                f"action_inbox maturity {key} must be {expected!r}, "
                f"got {action_inbox.get(key)!r}"
            )

    for field, expected in {
        "backend_routes": ACTION_INBOX_ROUTE,
        "evidence_refs": DOC_REF,
        "test_refs": "apps/control-center/src/App.test.tsx",
        "verifier_refs": VERIFIER_REF,
        "blocked_authorities": "connector_write",
        "missing_contracts": "generic_action_execution",
    }.items():
        values = action_inbox.get(field)
        if not isinstance(values, list) or expected not in values:
            failures.append(f"action_inbox maturity {field} missing {expected}")

    capabilities = action_inbox.get("authority_capabilities")
    if not isinstance(capabilities, list):
        failures.append("action_inbox maturity missing authority_capabilities")
        return
    local_task_capability = next(
        (
            item
            for item in capabilities
            if isinstance(item, dict)
            and item.get("capability_id") == LOCAL_TASK_AUTHORITY_CAPABILITY_ID
        ),
        None,
    )
    if not isinstance(local_task_capability, dict):
        failures.append("action_inbox local_task_create authority capability missing")
        return
    if local_task_capability.get("rank") != 5:
        failures.append("local_task_create authority capability must remain rank 5")
    expected_fields = {
        "authority_domain_ref": LOCAL_TASK_AUTHORITY_DOMAIN_REF,
        "authority_capability_ref": LOCAL_TASK_AUTHORITY_CAPABILITY_REF,
        "required_mode_ref": LOCAL_TASK_AUTHORITY_MODE_REF,
        "active_lease_required": True,
        "exact_approval_required": True,
        "idempotency_required": True,
        "receipts_required": True,
        "audit_required": True,
        "redaction_required": True,
    }
    for field, expected in expected_fields.items():
        if local_task_capability.get(field) != expected:
            failures.append(
                "local_task_create authority capability "
                f"{field} drifted from {expected!r}"
            )
    if LOCAL_TASK_COMMIT_ROUTE not in set(
        local_task_capability.get("backend_routes", [])
    ):
        failures.append("local_task_create authority capability missing commit route")


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "FCC-INBOX-001 Action Inbox And Approval Envelope UX",
            DOC_REF,
            "FCC-BRIEFING-001 Morning Briefing And Today Plan V1",
        ],
        FCC_BOARD: [
            "FCC-INBOX-001",
            "Approval Envelope and Receipt Visibility cards/read models",
            DOC_REF,
        ],
        PRODUCT_TRUTH: [
            "FCC-INBOX-001",
            DOC_REF,
            "backend-owned Approval Envelope and Receipt Visibility",
        ],
        GAP_MAP: [
            "FCC-INBOX-001 adds backend-owned `approval_envelope` and `receipt_visibility`",
            "FCC-INBOX-001 and FCC-ACTION-002 claim no broader maturity rank promotion",
        ],
        DOCS_README: [DOC_REF],
        DOCS_INDEX: [DOC_REF],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def validate_fcc_inbox_001_approval_envelope_ux(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    _validate_doc(root, failures)
    _validate_backend_and_frontend(root, failures)
    _validate_operational_maturity(root, failures)
    _validate_active_docs(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate FCC-INBOX-001 Action Inbox approval-envelope UX."
    )
    parser.add_argument("--root", default=str(ROOT), help="Repository root to inspect.")
    args = parser.parse_args(argv)

    failures = validate_fcc_inbox_001_approval_envelope_ux(Path(args.root).resolve())
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print(f"{TASK_REF} approval-envelope UX verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
