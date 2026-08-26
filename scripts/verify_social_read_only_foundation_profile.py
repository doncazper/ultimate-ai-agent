#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
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
    "apps/control-center/src/api/types.ts",
    "apps/control-center/src/mocks/controlCenterData.ts",
    "apps/control-center/src/northstar/PrimarySurfaces.tsx",
    "apps/control-center/src/northstar/WiredSurfaces.test.tsx",
    "docs/product/UAA_PRIVATE_DOGFOOD_DIRECTION_ACCEPTANCE.md",
    "docs/product/UAA_SOCIAL_READ_ONLY_FOUNDATION_PROFILE.md",
    "docs/schemas/social_read_only_foundation_promotion_v1.schema.json",
    "scripts/dev/uaa_crm.py",
    "scripts/verify_social_read_only_foundation_profile.py",
    "src/ultimate_ai_agent/api/control_center.py",
    "src/ultimate_ai_agent/core/communications/contracts.py",
    "src/ultimate_ai_agent/core/communications/local_projection.py",
    "src/ultimate_ai_agent/core/control_center/work_board.py",
    "src/ultimate_ai_agent/core/crm/local_command_center.py",
    "src/ultimate_ai_agent/core/crm/social_projection.py",
    "tests/test_communications_reviewed_projection.py",
    "tests/test_control_center_work_board.py",
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


def verify(payload: dict[str, Any] | None = None) -> tuple[list[str], str]:
    ledger = payload if payload is not None else _load()
    failures: list[str] = []

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        failures.extend(
            f"schema validation: {error.message}"
            for error in sorted(
                Draft202012Validator(schema).iter_errors(ledger),
                key=lambda error: list(error.absolute_path),
            )
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"promotion schema could not be validated: {exc}")

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
    except (OSError, ValueError) as exc:
        failures.append(str(exc))
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
        if foundation_ref in seen_foundations:
            failures.append(f"duplicate foundation: {foundation_ref}")
        seen_foundations.add(str(foundation_ref))
        expected = EXPECTED_FOUNDATIONS.get(str(foundation_ref))
        if expected is None:
            failures.append(f"unknown foundation: {foundation_ref}")
            continue
        if (foundation.get("owner_ref"), foundation.get("contract_ref")) != expected:
            failures.append(f"foundation owner or contract drifted: {foundation_ref}")
        if foundation.get("implementation_state") != "implemented":
            failures.append(f"foundation is not implemented: {foundation_ref}")
        path_refs = foundation.get("path_refs")
        if not isinstance(path_refs, list) or not path_refs:
            failures.append(f"foundation path refs missing: {foundation_ref}")
            continue
        for path_ref in path_refs:
            if path_ref not in subject_path_refs:
                failures.append(f"foundation has unbound path ref: {path_ref}")
            if path_ref in assigned_paths:
                failures.append(f"subject path assigned more than once: {path_ref}")
            assigned_paths.add(str(path_ref))
        for ref_field in ("cli_refs", "ui_refs", "verifier_refs", "evidence_refs"):
            values = foundation.get(ref_field)
            if not isinstance(values, list) or (
                ref_field in {"verifier_refs", "evidence_refs"} and not values
            ):
                failures.append(f"foundation {ref_field} invalid: {foundation_ref}")
                continue
            for value in values:
                if not _is_safe_ref(value):
                    failures.append(f"foundation contains unsafe {ref_field}: {value}")
        api_refs = foundation.get("api_refs")
        if not isinstance(api_refs, list):
            failures.append(f"foundation api_refs invalid: {foundation_ref}")
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
        roles.add(str(role_ref))
        if role_ref not in EXPECTED_REVIEW_ROLES:
            failures.append(f"unknown reviewer role: {role_ref}")
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
