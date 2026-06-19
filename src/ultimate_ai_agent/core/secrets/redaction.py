import re
from typing import Any

from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets

SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(?P<key>api[_-]?key|client[_-]?secret|auth[_-]?token|secret|token|password|"
    r"private[_-]?key|access[_-]?key|secret[_-]?access[_-]?key)\b"
    r"(?P<separator>\s*[:=]\s*)"
    r"(?P<quote>['\"]?)"
    r"(?P<value>[A-Za-z0-9_./:+\-]{12,})"
    r"(?P=quote)"
)
BEARER_TOKEN_PATTERN = re.compile(
    r"(?i)\b(?P<prefix>authorization\s*:\s*bearer\s+)(?P<value>[A-Za-z0-9._~+/=\-]{12,})"
)
KEY_BOUNDARY_BEGIN = "-" * 5 + "BEGIN"
KEY_BOUNDARY_END = "-" * 5 + "END"
KEY_TYPE_PRIVATE = "PRIVATE" + " KEY"
KEY_BOUNDARY_SUFFIX = KEY_TYPE_PRIVATE + "-" * 5
PRIVATE_KEY_BLOCK_PATTERN = re.compile(
    rf"(?is){re.escape(KEY_BOUNDARY_BEGIN)} [A-Z0-9 ]*{re.escape(KEY_BOUNDARY_SUFFIX)}"
    rf".*?{re.escape(KEY_BOUNDARY_END)} [A-Z0-9 ]*{re.escape(KEY_BOUNDARY_SUFFIX)}"
)
PRIVATE_KEY_HEADER_PATTERN = re.compile(
    rf"(?i){re.escape(KEY_BOUNDARY_BEGIN)} [A-Z0-9 ]*{re.escape(KEY_BOUNDARY_SUFFIX)}"
)
STANDALONE_SECRET_PATTERN = re.compile(
    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|\bgh[pousr]_[A-Za-z0-9_]{20,}\b"
)
SAFE_PLACEHOLDER_MARKERS = (
    "placeholder",
    "example",
    "dummy",
    "mock",
    "redacted",
    "safe",
    "sample",
    "changeme",
    "replace_me",
)


def _is_safe_placeholder(value: str) -> bool:
    normalized = value.strip().strip("'\"`<>[]{}()").lower()
    if not normalized:
        return True
    return any(marker in normalized for marker in SAFE_PLACEHOLDER_MARKERS)


def _redact_assignment(match: re.Match[str]) -> str:
    value = match.group("value")
    if _is_safe_placeholder(value):
        return match.group(0)
    return f"{match.group('key')}{match.group('separator')}[REDACTED_SECRET]"


def _redact_bearer(match: re.Match[str]) -> str:
    value = match.group("value")
    if _is_safe_placeholder(value):
        return match.group(0)
    return f"{match.group('prefix')}[REDACTED_SECRET]"


def redact_secret_value(value: str) -> str:
    redacted = PRIVATE_KEY_BLOCK_PATTERN.sub("[REDACTED_SECRET]", value)
    redacted = PRIVATE_KEY_HEADER_PATTERN.sub("[REDACTED_SECRET]", redacted)
    redacted = SECRET_ASSIGNMENT_PATTERN.sub(_redact_assignment, redacted)
    redacted = BEARER_TOKEN_PATTERN.sub(_redact_bearer, redacted)
    return STANDALONE_SECRET_PATTERN.sub("[REDACTED_SECRET]", redacted)


def _contains_extended_secret(val: Any) -> bool:
    if isinstance(val, str):
        return redact_secret_value(val) != val
    if isinstance(val, dict):
        return any(_contains_extended_secret(k) or _contains_extended_secret(v) for k, v in val.items())
    if isinstance(val, list):
        return any(_contains_extended_secret(item) for item in val)
    return False


def contains_obvious_secret(payload: Any) -> bool:
    return scan_payload_for_secrets(payload) or _contains_extended_secret(payload)
