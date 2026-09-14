"""Shared transport-compatible idempotency shape; not replay authority."""

MIN_IDEMPOTENCY_VALUE_LENGTH = 8
MAX_IDEMPOTENCY_VALUE_LENGTH = 200
IDEMPOTENCY_VALUE_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,199}$"
