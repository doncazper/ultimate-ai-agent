import re
from typing import Any

from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets

SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret|token|password)\s*=\s*['\"][^'\"]{8,}['\"]"
)


def redact_secret_value(value: str) -> str:
    return SECRET_VALUE_PATTERN.sub("[REDACTED_SECRET]", value)


def contains_obvious_secret(payload: Any) -> bool:
    return scan_payload_for_secrets(payload)
