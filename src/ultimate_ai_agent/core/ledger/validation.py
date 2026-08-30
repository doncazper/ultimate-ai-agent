import re
from typing import Any

# W3C Trace Context traceparent regex
TRACEPARENT_PATTERN = re.compile(r"^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")

# Broad secret key assignment regex scanner.
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|client[_-]?secret|auth[_-]?token|secret|token|password)\s*=\s*"
    r"(?:['\"][A-Za-z0-9_\-\.\:/]{12,}['\"]|[A-Za-z0-9_\-\.\:/]{16,})"
)
STANDALONE_SECRET_PATTERN = re.compile(
    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|\bgh[pousr]_[A-Za-z0-9_]{20,}\b"
)

def validate_traceparent(traceparent: str) -> bool:
    """Verify traceparent string matches W3C standard format."""
    if not traceparent:
        return False
    return bool(TRACEPARENT_PATTERN.match(traceparent))

def scan_payload_for_secrets(val: Any) -> bool:
    """Recursively scan dynamic payloads for raw credential assignments."""
    if isinstance(val, str):
        if SECRET_PATTERN.search(val) or STANDALONE_SECRET_PATTERN.search(val):
            return True
    elif isinstance(val, dict):
        for k, v in val.items():
            if scan_payload_for_secrets(k) or scan_payload_for_secrets(v):
                return True
    elif isinstance(val, list):
        for item in val:
            if scan_payload_for_secrets(item):
                return True
    return False
