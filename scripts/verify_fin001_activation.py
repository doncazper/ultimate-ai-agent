#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = ROOT / "docs/product/finance_fin001_activation_v1.json"
SCHEMA_PATH = ROOT / "docs/schemas/finance_fin001_activation_v1.schema.json"
DIRECTION_LEDGER_RELATIVE_PATH = Path(
    "docs/product/private_dogfood_direction_acceptance_v1.json"
)

EXPECTED_DEPENDENCIES = {
    (
        "dev-task:queue-v2-q00-pr379-action-inbox-finish",
        "commit-ref:71e0fa4a98b59a153aa651be4387a5541ce2eea7",
    ),
    (
        "dev-task:queue-v2-q08-today-render-fidelity",
        "commit-ref:cdc5c5cfb96d8974d00b01db70dfff3e6342b1b1",
    ),
    (
        "dev-task:queue-v2-q11-eco001-shared-local-data",
        "merge-commit-ref:e8088e7abaa56ecc884222a15e464cf2ef2de92f",
    ),
    (
        "dev-task:queue-v2-q13-eco003-boards",
        "commit-ref:c9d5448ab482c8df2dc8caa7e1750a796700e6a6",
    ),
    (
        "dev-task:queue-v2-q14-eco004-local-calendar",
        "commit-ref:38959c58863dabe7324edcfe2cc30a0cf12a874a",
    ),
    (
        "dev-task:queue-v2-q19-eco008-entitylink-changeset",
        "commit-ref:9fc8f37a4533e19436e9608da7078f9c179b8778",
    ),
    (
        "dev-task:queue-v2-q21-weekly-ceo-review-private-trial",
        "commit-ref:c22a2d3ced004da774a60f6522913d171e735a08",
    ),
}
EXPECTED_IMPLEMENTATION_PLAN = {
    "protected_data_plan_ref": "plan-ref:finance/FIN-001/encrypted-sqlite-boundary",
    "key_plan_ref": "plan-ref:finance/FIN-001/opaque-keychain-handle",
    "migration_plan_ref": "plan-ref:finance/FIN-001/versioned-synthetic-schema",
    "backup_restore_plan_ref": "plan-ref:finance/FIN-001/encrypted-synthetic-round-trip-proof",
    "deletion_plan_ref": "plan-ref:finance/FIN-001/cryptographic-and-explicit-delete",
    "redaction_plan_ref": "plan-ref:finance/FIN-001/safe-refs-no-raw-ledger-evidence",
    "cli_parity_plan_ref": "plan-ref:finance/FIN-001/core-cli-parity",
    "api_ui_parity_plan_ref": "plan-ref:finance/FIN-001/no-route-until-separate-review",
    "focused_verifier_plan_ref": "plan-ref:finance/FIN-001/balance-reversal-backup-restore-tests",
    "rollback_plan_ref": "plan-ref:finance/FIN-001/default-off-safe-disable",
    "synthetic_evidence_plan_ref": "plan-ref:finance/FIN-001/deterministic-fixtures",
    "local_approval_authority_plan_ref": "plan-ref:finance/FIN-001/exact-cli-approval-binding",
    "idempotency_plan_ref": "plan-ref:finance/FIN-001/request-ref-replay-conflict",
    "audit_receipt_plan_ref": "plan-ref:finance/FIN-001/append-first-mutation-receipts",
    "mutation_scope_plan_ref": "plan-ref:finance/FIN-001/exact-operation-and-revision-scope",
    "mutation_governance_verifier_plan_ref": "plan-ref:finance/FIN-001/approval-idempotency-receipt-tests",
    "synthetic_input_policy_plan_ref": "plan-ref:finance/FIN-001/fixture-ref-allowlist-only",
    "fixture_manifest_plan_ref": "plan-ref:finance/FIN-001/versioned-deterministic-fixture-manifest",
    "real_data_rejection_verifier_plan_ref": "plan-ref:finance/FIN-001/arbitrary-value-rejection-tests",
    "policy_engine_plan_ref": "plan-ref:finance/FIN-001/current-policy-decision-binding",
    "policy_governance_verifier_plan_ref": "plan-ref:finance/FIN-001/denied-and-stale-policy-tests",
    "authority_lease_plan_ref": "plan-ref:finance/FIN-001/exact-binding-registration-and-pre-persist-revalidation",
    "authority_lease_verifier_plan_ref": "plan-ref:finance/FIN-001/coarse-expired-and-revoked-lease-denial-tests",
}
EXPECTED_TOP_LEVEL_BINDINGS = {
    "schema_version": "uaa.finance-fin001-activation.v1",
    "activation_ref": "activation-ref:finance/FIN-001/synthetic-kernel:v1",
    "decision_receipt_ref": "receipt-ref:founder-private-dogfood:2026-08-25",
    "queue_task_receipt_ref": "developer-work-receipt-ref:sha256:9352c6acbdff3bcd1e5493f3",
    "queue_block_receipt_ref": "developer-work-receipt-ref:sha256:44573429fe043729321aee47",
    "source_revision_ref": "git-sha:6ac977ba9b98c2fbc323606f5be377b9949690df",
    "task_ref": "dev-task:finance-fin001-synthetic-kernel",
    "parent_program_task_ref": "dev-task:queue-v2-q26-finance-compliance-local-product",
    "milestone_ref": "milestone-ref:finance/FIN-001",
    "status": "blocked_pending_activation_merge_and_explicit_unblock",
    "safe_summary": "FIN-001 has an exact synthetic-only task and a vacant product-surface lane reservation. Implementation remains blocked until this activation record merges and the coordinator removes the sole exact merge-pending blocker using the actual merge commit before claim.",
    "next_safe_action": "After this record merges, verify the exact merge-pending blocker is the only blocker and the product-surface lane is vacant, unblock it with the actual PR 426 merge-commit ref, claim only dev-task:finance-fin001-synthetic-kernel, persist its claim receipt, and then implement the encrypted synthetic kernel under the exact mutation-governance plans.",
}
EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "activation_ref",
    "decision_receipt_ref",
    "queue_task_receipt_ref",
    "queue_block_receipt_ref",
    "source_revision_ref",
    "task_ref",
    "parent_program_task_ref",
    "milestone_ref",
    "status",
    "safe_summary",
    "dependency_evidence",
    "normative_path_refs",
    "first_slice",
    "implementation_plan",
    "board_claim_plan",
    "authority_posture",
    "next_safe_action",
}
EXPECTED_BOARD_CLAIM_PLAN = {
    "queue_snapshot_revision": 162,
    "lane_vacant_at_recording": True,
    "task_state_at_recording": "blocked",
    "blocker_ref": "blocker-ref:finance/FIN-001/pr426-activation-merge-pending",
    "queue_block_receipt_ref": "developer-work-receipt-ref:sha256:44573429fe043729321aee47",
    "claim_required_after_merge": True,
    "unblock_required_after_merge": True,
    "unblock_requires_merge_commit_ref": True,
    "claim_receipt_ref": None,
    "wip_lane": "product_surface",
    "reserved_task_ref": "dev-task:finance-fin001-synthetic-kernel",
}
EXPECTED_FIRST_SLICE = {
    "scope_refs": [
        "scope-ref:finance/FIN-001/balanced-posting-validation",
        "scope-ref:finance/FIN-001/core-contracts",
        "scope-ref:finance/FIN-001/synthetic-backup-restore-proof",
        "scope-ref:finance/FIN-001/synthetic-local-repository",
    ],
    "non_goal_refs": [
        "non-goal-ref:finance/FIN-001/accountant-access",
        "non-goal-ref:finance/FIN-001/advice-or-filing",
        "non-goal-ref:finance/FIN-001/api-or-ui-route",
        "non-goal-ref:finance/FIN-001/import-or-ocr",
        "non-goal-ref:finance/FIN-001/live-connector",
        "non-goal-ref:finance/FIN-001/payment-or-transfer",
        "non-goal-ref:finance/FIN-001/real-financial-data",
    ],
    "synthetic_only": True,
    "persistent_real_financial_data_allowed": False,
    "input_mode": "allowlisted_deterministic_fixture_refs_only",
    "arbitrary_operator_values_allowed": False,
    "mutation_capability_ref": "capability-ref:finance/FIN-001/synthetic-book-mutation",
}
EXPECTED_AUTHORITY_POSTURE = {
    "real_financial_data_allowed": False,
    "connector_allowed": False,
    "accountant_access_allowed": False,
    "payment_allowed": False,
    "filing_allowed": False,
    "advice_allowed": False,
    "provider_or_model_calls_allowed": False,
    "browser_runtime_allowed": False,
    "background_sync_allowed": False,
    "public_release_allowed": False,
    "production_authority_granted": False,
}
EXPECTED_NORMATIVE_PATH_REFS = {
    "repo-path-ref:docs/decisions/ADR-0063-finance-protected-local-data-boundary.md",
    "repo-path-ref:docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md",
    "repo-path-ref:docs/product/UAA_FINANCE_COMPLIANCE_PRODUCT_CONTRACT.md",
    "repo-path-ref:docs/product/UAA_PRIVATE_DOGFOOD_DIRECTION_ACCEPTANCE.md",
    "repo-path-ref:docs/roadmap/UAA_FINANCE_COMPLIANCE_QUEUE_INSERTION.md",
    "repo-path-ref:docs/security/UAA_FINANCE_COMPLIANCE_THREAT_MODEL.md",
}
SECRET_LIKE_REF = re.compile(
    r"(?i)(?:sk_(?:live|test)|gh[pousr]_|akia|asia|api[_-]?key|tokenvalue)"
)
CREDENTIAL_KEY = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret|private[_-]?key|credential)"
)
RAW_LOCAL_PATH = re.compile(
    r"(?i)(?:/(?:users|home|private|var/folders)/|[a-z]:\\\\users\\\\)"
)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise ValueError("governance JSON contains a duplicate object key")
        payload[key] = value
    return payload


def _load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except json.JSONDecodeError:
        raise ValueError("governance JSON is malformed") from None
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def _walk_strings(value: Any, key: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for child_key, child in value.items():
            found.extend(_walk_strings(child, str(child_key)))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_strings(child, key))
    elif isinstance(value, str):
        found.append((key, value))
    return found


def _has_secret_like_durable_content(value: Any) -> bool:
    if contains_obvious_secret(value) or any(
        SECRET_LIKE_REF.search(text) for _, text in _walk_strings(value)
    ):
        return True
    if isinstance(value, dict):
        for key, child in value.items():
            if CREDENTIAL_KEY.search(str(key)):
                if isinstance(child, dict):
                    annotations = (
                        child.get("default"),
                        child.get("const"),
                        child.get("enum"),
                        child.get("examples"),
                    )
                    if any(item not in (None, False, "", []) for item in annotations):
                        return True
                elif child not in (None, False, "", []):
                    return True
            if _has_secret_like_durable_content(child):
                return True
    elif isinstance(value, list):
        return any(_has_secret_like_durable_content(item) for item in value)
    return False


def _schema_has_nonlocal_ref(schema: Any) -> bool:
    return any(
        key in {"$ref", "$dynamicRef"} and not value.startswith("#/")
        for key, value in _walk_strings(schema)
    )


def _has_raw_local_path(value: Any) -> bool:
    return any(RAW_LOCAL_PATH.search(text) for _, text in _walk_strings(value))


def verify(payload: dict[str, Any] | None = None, *, root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    try:
        payload = _load(LEDGER_PATH) if payload is None else payload
        schema = _load(SCHEMA_PATH)
    except (OSError, ValueError):
        return ["activation governance JSON is invalid or ambiguous"]

    if _has_secret_like_durable_content(payload):
        failures.append("activation record contains secret-like durable content")
    if _has_secret_like_durable_content(schema):
        failures.append("activation schema contains secret-like durable content")
    if _has_raw_local_path(payload) or _has_raw_local_path(schema):
        failures.append("activation governance contains a raw local path")
    if any(
        payload.get(key) != value for key, value in EXPECTED_TOP_LEVEL_BINDINGS.items()
    ):
        failures.append("FIN-001 top-level activation binding drifted")
    if set(payload) != EXPECTED_TOP_LEVEL_KEYS:
        failures.append("FIN-001 top-level activation shape drifted")
    if payload.get("first_slice") != EXPECTED_FIRST_SLICE:
        failures.append("FIN-001 complete first-slice boundary drifted")
    if payload.get("authority_posture") != EXPECTED_AUTHORITY_POSTURE:
        failures.append("FIN-001 complete authority posture drifted")
    if _schema_has_nonlocal_ref(schema):
        failures.append("activation schema contains a nonlocal reference")
    if failures:
        return failures
    try:
        direction = _load(root / DIRECTION_LEDGER_RELATIVE_PATH)
    except (OSError, ValueError):
        failures.append("founder direction acceptance artifact is invalid or missing")
    else:
        if direction.get("decision_receipt_ref") != payload["decision_receipt_ref"]:
            failures.append("founder direction decision receipt drifted")
        if direction.get("acceptance_level") != (
            "founder_accepted_for_private_dogfood"
        ):
            failures.append("founder direction acceptance level drifted")
        q26_direction = direction.get("programs", {}).get("q26", {})
        if q26_direction.get("status") != (
            "direction_accepted_synthetic_kernel_dependency_and_board_gated"
        ):
            failures.append("founder Q26 direction status drifted")
    if failures:
        return failures
    try:
        Draft202012Validator.check_schema(schema)
        schema_errors = list(Draft202012Validator(schema).iter_errors(payload))
    except Exception:
        failures.append("activation schema is invalid or unresolvable")
        return failures
    for error in sorted(
        schema_errors,
        key=lambda item: tuple(str(part) for part in item.absolute_schema_path),
    ):
        failures.append(f"schema:validation_failed:{error.validator}")
    if failures:
        return failures

    for key, value in _walk_strings(payload):
        try:
            if key.endswith("_ref") or key.endswith("_refs"):
                if SECRET_LIKE_REF.search(value):
                    failures.append(
                        f"activation record contains secret-like durable content in {key}"
                    )
                    continue
                validate_execution_ref(value, key)
            elif key in {"safe_summary", "next_safe_action"}:
                validate_safe_execution_text(value, key)
        except ValueError as exc:
            failures.append(f"unsafe durable value for {key}: {exc}")

    dependencies = {
        (item["task_ref"], item["evidence_ref"])
        for item in payload["dependency_evidence"]
    }
    if dependencies != EXPECTED_DEPENDENCIES:
        failures.append("FIN-001 dependency evidence drifted")
    for task_ref, evidence_ref in dependencies:
        if not evidence_ref.startswith(("commit-ref:", "merge-commit-ref:")):
            continue
        revision = evidence_ref.split(":", 1)[1]
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, "HEAD"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode != 0:
            failures.append(
                f"dependency commit evidence is not in current history: {task_ref}"
            )
    if set(payload["normative_path_refs"]) != EXPECTED_NORMATIVE_PATH_REFS:
        failures.append("FIN-001 normative path inventory drifted")
    for path_ref in payload["normative_path_refs"]:
        path = root / path_ref.removeprefix("repo-path-ref:")
        if path.is_symlink() or not path.is_file():
            failures.append(
                f"normative path is missing or not a regular file: {path_ref}"
            )

    if payload["implementation_plan"] != EXPECTED_IMPLEMENTATION_PLAN:
        failures.append("FIN-001 implementation plan drifted")
    if payload["board_claim_plan"] != EXPECTED_BOARD_CLAIM_PLAN:
        failures.append("FIN-001 blocked queue handoff drifted")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the FIN-001 synthetic-only activation record."
    )
    parser.parse_args()
    failures = verify()
    if failures:
        print(json.dumps({"status": "FAILED", "failures": failures}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "status": "BLOCKED_PENDING_ACTIVATION_MERGE_AND_EXPLICIT_UNBLOCK",
                "activation_ref": "activation-ref:finance/FIN-001/synthetic-kernel:v1",
                "claim_ready": False,
                "task_claimed": False,
                "product_runtime_authority_granted": False,
                "real_financial_data_allowed": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
