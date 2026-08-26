#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = ROOT / "docs/product/social_read_only_foundation_promotion_v1.json"
SCHEMA_PATH = ROOT / "docs/schemas/social_read_only_foundation_promotion_v1.schema.json"
EXTERNAL_HUMAN_IDENTITY_AUTHORITY_CONFIGURED = False

NORMATIVE_SUBJECT_PATHS = (
    "apps/control-center/src/App.test.tsx",
    "apps/control-center/src/api/client.summaryEndpoints.test.ts",
    "apps/control-center/src/api/client.ts",
    "apps/control-center/src/api/types.ts",
    "apps/control-center/src/mocks/controlCenterData.ts",
    "apps/control-center/src/northstar/PrimarySurfaces.tsx",
    "apps/control-center/src/northstar/WiredSurfaces.test.tsx",
    "apps/control-center/tests/visual/foundation-surfaces.real.spec.ts",
    "apps/control-center/tests/visual/__snapshots__/desktop/crm.png",
    "apps/control-center/tests/visual/__snapshots__/mobile/crm.png",
    "docs/control_center/visual_regression_manifest.json",
    "docs/product/UAA_PRIVATE_DOGFOOD_DIRECTION_ACCEPTANCE.md",
    "docs/product/UAA_SOCIAL_READ_ONLY_FOUNDATION_PROFILE.md",
    "docs/schemas/social_read_only_foundation_promotion_v1.schema.json",
    "scripts/dev/uaa_crm.py",
    "scripts/verify_social_read_only_foundation_profile.py",
    "src/ultimate_ai_agent/api/control_center.py",
    "src/ultimate_ai_agent/core/authority/contracts.py",
    "src/ultimate_ai_agent/core/communications/contracts.py",
    "src/ultimate_ai_agent/core/communications/local_projection.py",
    "src/ultimate_ai_agent/core/control_center/work_board.py",
    "src/ultimate_ai_agent/core/crm/__init__.py",
    "src/ultimate_ai_agent/core/crm/local_command_center.py",
    "src/ultimate_ai_agent/core/crm/social_projection.py",
    "tests/test_communications_reviewed_projection.py",
    "tests/test_control_center_work_board.py",
    "tests/test_crm_local_command_center.py",
    "tests/test_crm_local_command_center_api_routes.py",
    "tests/test_social_read_only_foundation_profile.py",
)

EXPECTED_FOUNDATIONS = {
    "foundation-ref:social-profile:work-board": (
        "owner-ref:work-board",
        "contract-ref:work-board-social-content-saved-projection:v1",
    ),
    "foundation-ref:social-profile:communications": (
        "owner-ref:communications",
        "contract-ref:communications-reviewed-projection:v1",
    ),
    "foundation-ref:social-profile:crm": (
        "owner-ref:crm",
        "contract-ref:crm-social-relationship-projection:v1",
    ),
    "foundation-ref:social-profile:promotion-contract": (
        "owner-ref:governance",
        "contract-ref:social-read-only-foundation-profile:v1",
    ),
}
EXPECTED_FOUNDATION_INVENTORIES = {
    "foundation-ref:social-profile:work-board": {
        "path_refs": (
            "repo-path-ref:src/ultimate_ai_agent/core/control_center/work_board.py",
            "repo-path-ref:tests/test_control_center_work_board.py",
        ),
        "api_refs": ("GET /control-center/work-board",),
        "cli_refs": ("repo-local-command:uaa-work-board:inspect-board",),
        "ui_refs": ("control-center-surface-ref:work-board-social-content",),
        "verifier_refs": ("verifier-ref:social-foundation:work-board",),
        "evidence_refs": (
            "evidence-ref:social-foundation:work-board-owner-projection",
        ),
    },
    "foundation-ref:social-profile:communications": {
        "path_refs": (
            "repo-path-ref:src/ultimate_ai_agent/core/communications/contracts.py",
            "repo-path-ref:src/ultimate_ai_agent/core/communications/local_projection.py",
            "repo-path-ref:tests/test_communications_reviewed_projection.py",
        ),
        "api_refs": (
            "GET /control-center/communications/conversations",
            "GET /control-center/communications/conversations/{conversation_ref}",
        ),
        "cli_refs": ("repo-local-command:uaa-communications:conversations",),
        "ui_refs": ("control-center-surface-ref:communications-social-media",),
        "verifier_refs": ("verifier-ref:social-foundation:communications",),
        "evidence_refs": (
            "evidence-ref:social-foundation:communications-owner-projection",
        ),
    },
    "foundation-ref:social-profile:crm": {
        "path_refs": (
            "repo-path-ref:apps/control-center/src/App.test.tsx",
            "repo-path-ref:apps/control-center/src/api/client.summaryEndpoints.test.ts",
            "repo-path-ref:apps/control-center/src/api/client.ts",
            "repo-path-ref:apps/control-center/src/api/types.ts",
            "repo-path-ref:apps/control-center/src/mocks/controlCenterData.ts",
            "repo-path-ref:apps/control-center/src/northstar/PrimarySurfaces.tsx",
            "repo-path-ref:apps/control-center/src/northstar/WiredSurfaces.test.tsx",
            "repo-path-ref:apps/control-center/tests/visual/foundation-surfaces.real.spec.ts",
            "repo-path-ref:apps/control-center/tests/visual/__snapshots__/desktop/crm.png",
            "repo-path-ref:apps/control-center/tests/visual/__snapshots__/mobile/crm.png",
            "repo-path-ref:docs/control_center/visual_regression_manifest.json",
            "repo-path-ref:scripts/dev/uaa_crm.py",
            "repo-path-ref:src/ultimate_ai_agent/api/control_center.py",
            "repo-path-ref:src/ultimate_ai_agent/core/authority/contracts.py",
            "repo-path-ref:src/ultimate_ai_agent/core/crm/__init__.py",
            "repo-path-ref:src/ultimate_ai_agent/core/crm/local_command_center.py",
            "repo-path-ref:src/ultimate_ai_agent/core/crm/social_projection.py",
            "repo-path-ref:tests/test_crm_local_command_center.py",
            "repo-path-ref:tests/test_crm_local_command_center_api_routes.py",
            "repo-path-ref:tests/test_social_read_only_foundation_profile.py",
        ),
        "api_refs": ("GET /control-center/crm/relationships",),
        "cli_refs": (
            "repo-local-command:uaa-crm:inspect-social-relationships",
            "repo-local-command:uaa-crm:mutate-local",
        ),
        "ui_refs": ("control-center-surface-ref:crm-social-relationship-context",),
        "verifier_refs": ("verifier-ref:social-foundation:crm",),
        "evidence_refs": ("evidence-ref:social-foundation:crm-owner-projection",),
    },
    "foundation-ref:social-profile:promotion-contract": {
        "path_refs": (
            "repo-path-ref:docs/product/UAA_PRIVATE_DOGFOOD_DIRECTION_ACCEPTANCE.md",
            "repo-path-ref:docs/product/UAA_SOCIAL_READ_ONLY_FOUNDATION_PROFILE.md",
            "repo-path-ref:docs/schemas/social_read_only_foundation_promotion_v1.schema.json",
            "repo-path-ref:scripts/verify_social_read_only_foundation_profile.py",
        ),
        "api_refs": (),
        "cli_refs": ("repo-local-command:verify-social-read-only-foundation-profile",),
        "ui_refs": (),
        "verifier_refs": ("verifier-ref:social-foundation:promotion-v1",),
        "evidence_refs": ("evidence-ref:social-foundation:acceptance-subject-bound",),
    },
}
EXPECTED_REVIEW_ROLES = {
    "reviewer-role-ref:social-foundation:product-design",
    "reviewer-role-ref:social-foundation:crm-owner",
    "reviewer-role-ref:social-foundation:privacy-security",
    "reviewer-role-ref:social-foundation:accessibility",
    "reviewer-role-ref:social-foundation:implementation",
}
SAFE_REF = re.compile(r"^[a-z][a-z0-9-]*(?::[a-z0-9][a-z0-9._/-]*)+$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
SECRET_LIKE_REF = re.compile(
    r"(?i)(?:^|[:/_-])(?:sk_live|sk_test|ghp|github_pat|xox[baprs]|AIza|tokenvalue)"
    r"(?:[_-]?[A-Za-z0-9]+)?"
)
FORBIDDEN_MARKERS = (
    "raw prompt",
    "raw response",
    "raw provider payload",
    "raw log",
    "api key",
    "password",
    "private key",
    "bearer ",
    "cookie",
    "/users/",
    "/home/",
    "username",
    "hostname",
    "environment dump",
)


def _load(path: Path = LEDGER_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("promotion ledger must be a JSON object")
    return payload


def _is_safe_ref(value: Any) -> bool:
    if not isinstance(value, str) or not SAFE_REF.fullmatch(value):
        return False
    try:
        validate_execution_ref(value, "social_foundation_ref")
    except ValueError:
        return False
    return not contains_obvious_secret(value) and not SECRET_LIKE_REF.search(value)


def actual_subject() -> tuple[list[dict[str, str]], str]:
    files: list[dict[str, str]] = []
    for relative in NORMATIVE_SUBJECT_PATHS:
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"normative subject file is missing or unsafe: {relative}")
        files.append(
            {
                "path_ref": f"repo-path-ref:{relative}",
                "sha256": f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}",
            }
        )
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return files, f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _iter_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_strings(nested)


def _verify_foundation_implementations() -> list[str]:
    failures: list[str] = []
    try:
        from ultimate_ai_agent.core.control_center.work_board import (
            WORK_BOARD_SOCIAL_CONTENT_PROJECTION_CONTRACT_REF,
            WORK_BOARD_SOCIAL_CONTENT_PROJECTION_REF,
            build_work_board_read_model,
        )

        board = build_work_board_read_model()
        social = [
            projection
            for projection in board.saved_projections
            if projection.projection_ref == WORK_BOARD_SOCIAL_CONTENT_PROJECTION_REF
        ]
        if (
            len(social) != 1
            or social[0].contract_ref
            != WORK_BOARD_SOCIAL_CONTENT_PROJECTION_CONTRACT_REF
            or not social[0].backend_owned
            or not social[0].read_only
            or social[0].publishing_enabled
            or social[0].connector_write_enabled
        ):
            failures.append("WORK_BOARD_FOUNDATION_CHECK_FAILED")
    except Exception:
        failures.append("WORK_BOARD_FOUNDATION_CHECK_FAILED")

    try:
        from ultimate_ai_agent.core.communications.local_projection import (
            COMMUNICATIONS_PROJECTION_FILENAME,
            ReviewedCommunicationsProjectionStore,
        )

        communications_payload = {
            "schema_version": "uaa-communications-reviewed-projection.v1",
            "snapshot_ref": "snapshot-ref:communications:social-foundation-check",
            "source": {
                "source_ref": "source-ref:communications:reviewed-manual-import",
                "source_kind": "reviewed_manual_import",
                "schema_version": "uaa-communications-reviewed-projection.v1",
                "observed_at": "2026-08-25T00:00:00Z",
                "freshness": "current",
                "coverage_ref": "coverage-ref:communications:bounded-check",
                "retention_ref": "retention-ref:communications:operator-managed",
                "privacy_ref": "privacy-ref:communications:redacted-summary-only",
                "evidence_refs": [
                    "evidence-ref:communications:social-foundation-check"
                ],
                "connector_configured": False,
                "live_sync_enabled": False,
                "external_actions_enabled": False,
                "raw_content_persisted": False,
            },
            "threads": [
                {
                    "conversation_ref": "conversation-ref:communications:social-check",
                    "channel_ref": "channel-ref:communications:social-review",
                    "participant_refs": [
                        "participant-ref:communications:social-reviewer"
                    ],
                    "item_refs": ["item-ref:communications:social-check-1"],
                    "latest_activity_at": "2026-08-25T00:00:00Z",
                    "needs_attention": True,
                    "safe_label": "Reviewed Social signal",
                    "safe_summary": "A reviewed redacted signal needs attention.",
                    "evidence_refs": [
                        "evidence-ref:communications:social-thread-check"
                    ],
                }
            ],
            "items": [
                {
                    "item_ref": "item-ref:communications:social-check-1",
                    "conversation_ref": "conversation-ref:communications:social-check",
                    "sender_ref": "sender-ref:communications:reviewed-source",
                    "item_kind": "message",
                    "occurred_at": "2026-08-25T00:00:00Z",
                    "safe_summary": "Reviewed redacted signal summary.",
                    "content_fingerprint_ref": (
                        "fingerprint-ref:communications:social-check-1"
                    ),
                    "relation_ref": None,
                    "evidence_refs": ["evidence-ref:communications:social-item-check"],
                    "content_untrusted": True,
                    "not_instruction_authority": True,
                    "reviewed_redacted_summary_only": True,
                    "raw_content_omitted": True,
                }
            ],
            "raw_content_persisted": False,
        }
        with tempfile.TemporaryDirectory(
            prefix="uaa-social-foundation-communications-"
        ) as temp_dir:
            state_dir = Path(temp_dir) / "projection"
            state_dir.mkdir()
            (state_dir / COMMUNICATIONS_PROJECTION_FILENAME).write_text(
                json.dumps(communications_payload, sort_keys=True),
                encoding="utf-8",
            )
            store = ReviewedCommunicationsProjectionStore(state_dir)
            page = store.list_threads(limit=1, needs_attention=True)
            detail = store.get_thread("conversation-ref:communications:social-check")
        if (
            page.status.value != "ready"
            or page.pagination.returned_count != 1
            or len(page.items) != 1
            or not page.read_only
            or page.send_enabled
            or page.reply_enabled
            or page.delete_enabled
            or page.moderate_enabled
            or not page.raw_content_omitted
            or detail.status.value != "ready"
            or len(detail.items) != 1
            or not detail.items[0].content_untrusted
            or not detail.items[0].not_instruction_authority
            or not detail.items[0].reviewed_redacted_summary_only
            or not detail.items[0].raw_content_omitted
            or detail.source.connector_configured
            or detail.source.live_sync_enabled
            or detail.source.external_actions_enabled
            or detail.source.raw_content_persisted
        ):
            failures.append("COMMUNICATIONS_FOUNDATION_CHECK_FAILED")
    except Exception:
        failures.append("COMMUNICATIONS_FOUNDATION_CHECK_FAILED")

    try:
        from ultimate_ai_agent.core.crm.local_command_center import CrmLocalStore

        with tempfile.TemporaryDirectory(prefix="uaa-social-foundation-") as temp_dir:
            crm = CrmLocalStore(Path(temp_dir) / "crm").read_model()
        projection = crm.social_relationship_projection
        if (
            not projection.backend_owned
            or not projection.read_only
            or projection.live_source_access_enabled
            or projection.publishing_enabled
            or projection.external_write_enabled
            or not projection.items
        ):
            failures.append("CRM_FOUNDATION_CHECK_FAILED")
    except Exception:
        failures.append("CRM_FOUNDATION_CHECK_FAILED")
    return failures


def verify(payload: dict[str, Any] | None = None) -> tuple[list[str], str]:
    ledger = payload if payload is not None else _load()
    failures: list[str] = []

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        schema_errors = sorted(
            Draft202012Validator(schema).iter_errors(ledger),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        failures.extend(
            f"SCHEMA_VALIDATION_FAILED:{error.validator}" for error in schema_errors
        )
    except (OSError, ValueError, json.JSONDecodeError):
        failures.append("PROMOTION_SCHEMA_COULD_NOT_BE_VALIDATED")

    expected_constants = {
        "schema_version": "uaa-social-foundation-promotion.v1",
        "ledger_ref": "ledger-ref:social-read-only-foundation-promotion:v1",
        "profile_ref": "contract-ref:social-read-only-foundation-profile:v1",
        "promotion_status": "pending_independent_review",
    }
    for field_name, expected in expected_constants.items():
        if ledger.get(field_name) != expected:
            failures.append(f"{field_name} must equal {expected}")
    if not _is_safe_ref(ledger.get("candidate_author_ref")):
        failures.append("candidate_author_ref must be a safe ref")

    try:
        subject_files, subject_digest = actual_subject()
    except (OSError, ValueError):
        failures.append("ACCEPTANCE_SUBJECT_COULD_NOT_BE_RESOLVED")
        subject_files, subject_digest = [], ""
    if ledger.get("subject_files") != subject_files:
        failures.append("subject file manifest does not match the exact current files")
    if ledger.get("acceptance_subject_digest") != subject_digest:
        failures.append("acceptance subject digest does not match the current files")

    foundations = ledger.get("foundations")
    if not isinstance(foundations, list):
        failures.append("foundations must be a list")
        foundations = []
    seen_foundations: set[str] = set()
    assigned_paths: set[str] = set()
    subject_path_refs = {entry["path_ref"] for entry in subject_files}
    for foundation in foundations:
        if not isinstance(foundation, dict):
            failures.append("foundation entry must be an object")
            continue
        foundation_ref = foundation.get("foundation_ref")
        if not isinstance(foundation_ref, str):
            failures.append("foundation_ref must be a safe string ref")
            continue
        if foundation_ref in seen_foundations:
            failures.append("duplicate foundation_ref")
        seen_foundations.add(str(foundation_ref))
        expected = EXPECTED_FOUNDATIONS.get(str(foundation_ref))
        if expected is None:
            failures.append("unknown foundation_ref")
            continue
        if (foundation.get("owner_ref"), foundation.get("contract_ref")) != expected:
            failures.append("foundation owner or contract drifted")
        if foundation.get("implementation_state") != "implemented":
            failures.append("foundation is not implemented")
        expected_inventory = EXPECTED_FOUNDATION_INVENTORIES[str(foundation_ref)]
        for field_name, expected_values in expected_inventory.items():
            if foundation.get(field_name) != list(expected_values):
                failures.append(f"foundation exact {field_name} drifted")
        path_refs = foundation.get("path_refs")
        if not isinstance(path_refs, list) or not path_refs:
            failures.append("foundation path refs missing")
            continue
        for path_ref in path_refs:
            if not isinstance(path_ref, str):
                failures.append("foundation contains non-string path ref")
                continue
            if path_ref not in subject_path_refs:
                failures.append("foundation has unbound path ref")
            if path_ref in assigned_paths:
                failures.append("subject path assigned more than once")
            assigned_paths.add(str(path_ref))
        for ref_field in ("cli_refs", "ui_refs", "verifier_refs", "evidence_refs"):
            values = foundation.get(ref_field)
            if not isinstance(values, list) or (
                ref_field in {"verifier_refs", "evidence_refs"} and not values
            ):
                failures.append(f"foundation {ref_field} invalid")
                continue
            for value in values:
                if not _is_safe_ref(value):
                    failures.append(f"foundation contains unsafe {ref_field}")
        api_refs = foundation.get("api_refs")
        if not isinstance(api_refs, list):
            failures.append("foundation api_refs invalid")
    if seen_foundations != set(EXPECTED_FOUNDATIONS):
        failures.append("exact foundation inventory is incomplete")
    if assigned_paths != subject_path_refs:
        failures.append("every acceptance subject file must have exactly one owner")

    reviewers = ledger.get("reviewers")
    if not isinstance(reviewers, list):
        failures.append("reviewers must be a list")
        reviewers = []
    roles: set[str] = set()
    for reviewer in reviewers:
        if not isinstance(reviewer, dict):
            failures.append("reviewer entry must be an object")
            continue
        role_ref = reviewer.get("role_ref")
        if not isinstance(role_ref, str):
            failures.append("reviewer role_ref must be a safe string ref")
            continue
        roles.add(str(role_ref))
        if role_ref not in EXPECTED_REVIEW_ROLES:
            failures.append("unknown reviewer role_ref")
        if reviewer.get("decision") != "pending":
            failures.append("independent decisions cannot be self-asserted in v1")
        if any(
            reviewer.get(field_name) is not None
            for field_name in (
                "reviewer_ref",
                "acceptance_subject_digest",
                "receipt_ref",
            )
        ):
            failures.append("pending reviewer identity and receipt fields must be null")
        if reviewer.get("finding_refs") != []:
            failures.append("pending reviewer finding_refs must be empty")
    if roles != EXPECTED_REVIEW_ROLES:
        failures.append("exact independent reviewer role inventory is incomplete")

    failures.extend(_verify_foundation_implementations())

    if ledger.get("external_human_identity_authority_configured") is not False:
        failures.append("external identity authority cannot be asserted by this ledger")
    if EXTERNAL_HUMAN_IDENTITY_AUTHORITY_CONFIGURED:
        failures.append(
            "v1 verifier must remain fail-closed without an external adapter"
        )
    for field_name in (
        "live_source_access_enabled",
        "connector_runtime_enabled",
        "provider_model_call_enabled",
        "publishing_enabled",
        "external_write_enabled",
        "production_authority_enabled",
        "raw_content_included",
    ):
        if ledger.get(field_name) is not False:
            failures.append(f"{field_name} must remain false")

    for value in _iter_strings(ledger):
        lowered = value.lower()
        if (
            contains_obvious_secret(value)
            or SECRET_LIKE_REF.search(value)
            or any(marker in lowered for marker in FORBIDDEN_MARKERS)
        ):
            failures.append("promotion ledger contains forbidden durable content")
            break
    try:
        validate_safe_execution_text(
            str(ledger.get("next_safe_action", "")),
            "next_safe_action",
        )
    except ValueError:
        failures.append("next_safe_action must be safe bounded text")

    state = (
        "IMPLEMENTATION_EVIDENCE_VERIFIED_PROMOTION_PENDING"
        if not failures
        else "INVALID"
    )
    return failures, state


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the fail-closed Social read-only foundation profile."
    )
    parser.add_argument("--require-promoted", action="store_true")
    parser.add_argument("--print-subject", action="store_true")
    args = parser.parse_args()
    if args.print_subject:
        files, digest = actual_subject()
        print(
            json.dumps(
                {"acceptance_subject_digest": digest, "subject_files": files},
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    failures, state = verify()
    payload = {
        "schema_version": "uaa-social-foundation-verification.v1",
        "status": state,
        "failure_count": len(failures),
        "failures": failures,
        "implementation_evidence_verified": not failures,
        "independent_promotion_verified": False,
        "external_human_identity_authority_configured": False,
        "live_source_access_enabled": False,
        "publishing_enabled": False,
        "external_write_enabled": False,
        "production_authority_enabled": False,
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    if failures:
        return 1
    if args.require_promoted:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
