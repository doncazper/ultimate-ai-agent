from typing import List, Tuple

from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret, redact_secret_value


def redact_memory_content(content: str) -> Tuple[str, List[str]]:
    if contains_obvious_secret({"content": content}):
        return redact_secret_value(content), ["secret_value"]
    return content, []


def memory_contains_secret(payload: object) -> bool:
    return contains_obvious_secret(payload)
