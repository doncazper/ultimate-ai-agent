"""Standard-library-only transport for explicit synthetic Finance configuration.

This module does not validate, provision, or authorize a Finance workspace. Its
content-free identity only guards reuse of an already running local backend.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json


FINANCE_WORKSPACE_REPOSITORY_ENV = "UAA_FINANCE_SYNTHETIC_REPOSITORY_DIR"
FINANCE_WORKSPACE_HELPER_ENV = "UAA_FINANCE_NATIVE_HELPER_PATH"
FINANCE_WORKSPACE_HELPER_DIGEST_ENV = "UAA_FINANCE_NATIVE_HELPER_SHA256"
FINANCE_WORKSPACE_DISABLE_ENV = "UAA_FINANCE_SAFE_DISABLE"
FINANCE_STARTUP_ENV_NAMES = (
    FINANCE_WORKSPACE_REPOSITORY_ENV,
    FINANCE_WORKSPACE_HELPER_ENV,
    FINANCE_WORKSPACE_HELPER_DIGEST_ENV,
    FINANCE_WORKSPACE_DISABLE_ENV,
)
FINANCE_STARTUP_METADATA_KEY = "finance_startup_configuration_ref"
_IDENTITY_DOMAIN = b"uaa:finance-startup-configuration:v1\x00"


def finance_startup_environment(environ: Mapping[str, str]) -> dict[str, str]:
    """Copy only admitted names, preserving absent, empty, and invalid values."""

    return {name: environ[name] for name in FINANCE_STARTUP_ENV_NAMES if name in environ}


def finance_startup_configuration_ref(environ: Mapping[str, str]) -> str:
    """Bind exact transported values without retaining paths or other content."""

    encoded = json.dumps(
        finance_startup_environment(environ),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    digest = hashlib.sha256(_IDENTITY_DOMAIN + encoded).hexdigest()
    return f"configuration-ref:finance-startup:sha256:{digest}"


def finance_startup_configuration_matches(
    recorded_ref: object, environ: Mapping[str, str]
) -> bool:
    """Missing, malformed, or different launch metadata cannot prove reuse."""

    return isinstance(recorded_ref, str) and recorded_ref == finance_startup_configuration_ref(environ)
