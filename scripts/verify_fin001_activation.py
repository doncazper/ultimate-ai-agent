#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
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

EXPECTED_DEPENDENCIES = {
    (
        "dev-task:queue-v2-q00-pr379-action-inbox-finish",
        "commit-ref:71e0fa4a98b59a153aa651be4387a5541ce2eea7",
    ),
    (
        "dev-task:queue-v2-q08-today-render-fidelity",
        "evidence-ref:pr-395-merge-cdc5c5cf",
    ),
    (
        "dev-task:queue-v2-q11-eco001-shared-local-data",
        "merge-commit-ref:e8088e7abaa56ecc884222a15e464cf2ef2de92f",
    ),
    (
        "dev-task:queue-v2-q13-eco003-boards",
        "evidence-ref:queue-v2/Q13/pr-401-merge-c9d5448a",
    ),
    (
        "dev-task:queue-v2-q14-eco004-local-calendar",
        "evidence-ref:queue-v2/Q14/pr-404-merge-38959c58",
    ),
    (
        "dev-task:queue-v2-q19-eco008-entitylink-changeset",
        "commit-ref:bfad7dabb2a08dbcf1fabc469c5ca80267e4eedd",
    ),
    (
        "dev-task:queue-v2-q21-weekly-ceo-review-private-trial",
        "report-ref:queue-v2:q21:weekly-review-private-trial:v1",
    ),
}
EXPECTED_NORMATIVE_PATH_REFS = {
    "repo-path-ref:docs/decisions/ADR-0063-finance-protected-local-data-boundary.md",
    "repo-path-ref:docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md",
    "repo-path-ref:docs/product/UAA_FINANCE_COMPLIANCE_PRODUCT_CONTRACT.md",
    "repo-path-ref:docs/product/UAA_PRIVATE_DOGFOOD_DIRECTION_ACCEPTANCE.md",
    "repo-path-ref:docs/roadmap/UAA_FINANCE_COMPLIANCE_QUEUE_INSERTION.md",
    "repo-path-ref:docs/security/UAA_FINANCE_COMPLIANCE_THREAT_MODEL.md",
}
EXPECTED_SCOPE_REFS = {
    "scope-ref:finance/FIN-001/balanced-posting-validation",
    "scope-ref:finance/FIN-001/core-contracts",
    "scope-ref:finance/FIN-001/synthetic-backup-restore-proof",
    "scope-ref:finance/FIN-001/synthetic-local-repository",
}
EXPECTED_NON_GOAL_REFS = {
    "non-goal-ref:finance/FIN-001/accountant-access",
    "non-goal-ref:finance/FIN-001/advice-or-filing",
    "non-goal-ref:finance/FIN-001/api-or-ui-route",
    "non-goal-ref:finance/FIN-001/import-or-ocr",
    "non-goal-ref:finance/FIN-001/live-connector",
    "non-goal-ref:finance/FIN-001/payment-or-transfer",
    "non-goal-ref:finance/FIN-001/real-financial-data",
}
SECRET_LIKE_REF = re.compile(
    r"(?i)(?:sk_(?:live|test)|gh[pousr]_|akia|asia|api[_-]?key|tokenvalue)"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
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


def verify(payload: dict[str, Any] | None = None, *, root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    payload = _load(LEDGER_PATH) if payload is None else payload
    schema = _load(SCHEMA_PATH)

    for error in sorted(Draft202012Validator(schema).iter_errors(payload), key=str):
        location = ".".join(str(part) for part in error.absolute_path) or "root"
        failures.append(f"schema:{location}:{error.message}")
    if failures:
        return failures

    if contains_obvious_secret(payload):
        failures.append("activation record contains secret-like durable content")
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
    if set(payload["normative_path_refs"]) != EXPECTED_NORMATIVE_PATH_REFS:
        failures.append("FIN-001 normative path inventory drifted")
    for path_ref in payload["normative_path_refs"]:
        path = root / path_ref.removeprefix("repo-path-ref:")
        if path.is_symlink() or not path.is_file():
            failures.append(
                f"normative path is missing or not a regular file: {path_ref}"
            )

    first_slice = payload["first_slice"]
    if set(first_slice["scope_refs"]) != EXPECTED_SCOPE_REFS:
        failures.append("FIN-001 first-slice scope drifted")
    if set(first_slice["non_goal_refs"]) != EXPECTED_NON_GOAL_REFS:
        failures.append("FIN-001 non-goal boundary drifted")

    if any(payload["authority_posture"].values()):
        failures.append(
            "FIN-001 activation cannot grant external or production authority"
        )
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
                "status": "ACTIVATED_SYNTHETIC_ONLY",
                "activation_ref": "activation-ref:finance/FIN-001/synthetic-kernel:v1",
                "product_runtime_authority_granted": False,
                "real_financial_data_allowed": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
