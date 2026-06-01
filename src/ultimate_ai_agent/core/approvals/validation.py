from typing import Any

from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets


RISK_ORDER = {
    "safe": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def assert_approval_secret_clean(value: Any, field_name: str) -> None:
    if scan_payload_for_secrets(value):
        raise ValueError(f"{field_name} contains secret-like content.")


def risk_value(value: object) -> int:
    return RISK_ORDER.get(str(value), -1)


def refs_subset(requested: list[str], approved: list[str]) -> bool:
    approved_set = set(approved)
    return set(requested).issubset(approved_set)
