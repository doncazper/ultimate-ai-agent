from __future__ import annotations

import re
import unicodedata


_ABSOLUTE_OR_DOT_PATH_RE = re.compile(
    r"(?:^|[\s:=(\"'])((?:/|~/|\./|\.\./|[A-Za-z]:\\)\S+)"
)
_RELATIVE_FILE_PATH_RE = re.compile(
    r"\b[A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)+\.[A-Za-z0-9]{1,12}\b"
)


def validate_safe_contract_text_shape(value: str, field_name: str) -> None:
    """Reject path-shaped or display-control text from durable safe summaries."""

    if any(
        unicodedata.category(character) in {"Cc", "Cf"}
        for character in value
    ):
        raise ValueError(f"{field_name} contains control or formatting characters")
    if _ABSOLUTE_OR_DOT_PATH_RE.search(value) or _RELATIVE_FILE_PATH_RE.search(value):
        raise ValueError(f"{field_name} contains path-shaped content")
