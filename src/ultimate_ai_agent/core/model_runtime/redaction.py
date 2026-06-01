from typing import Any

from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets


def contains_secret_like(value: Any) -> bool:
    return scan_payload_for_secrets(value)


def assert_secret_clean(value: Any, field_name: str) -> None:
    if contains_secret_like(value):
        raise ValueError(f"{field_name} contains secret-like content.")
