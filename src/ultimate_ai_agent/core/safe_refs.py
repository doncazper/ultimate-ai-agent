from __future__ import annotations

import hashlib


def hash_bytes(value: bytes) -> str:
    """Return a deterministic full SHA-256 digest for bytes."""

    return hashlib.sha256(value).hexdigest()


def hash_text(value: str) -> str:
    """Return a deterministic full SHA-256 digest for safe reference building."""

    return hash_bytes(value.encode("utf-8"))
