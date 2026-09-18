"""Standard-library-only capture and transport of synthetic Finance configuration.

This module does not validate, provision, or authorize a Finance workspace. Its
content-free identity only guards reuse of an already running local backend.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
import hashlib
import json

from ultimate_ai_agent.core.finance_managed_profile import (
    FINANCE_CONFIGURATION_ENV_NAMES,
    FINANCE_EXPLICIT_ENV_NAMES,
    FINANCE_WORKSPACE_DISABLE_ENV as FINANCE_WORKSPACE_DISABLE_ENV,
    FINANCE_WORKSPACE_HELPER_DIGEST_ENV as FINANCE_WORKSPACE_HELPER_DIGEST_ENV,
    FINANCE_WORKSPACE_HELPER_ENV as FINANCE_WORKSPACE_HELPER_ENV,
    FINANCE_WORKSPACE_REPOSITORY_ENV as FINANCE_WORKSPACE_REPOSITORY_ENV,
    FinanceConfigurationResolution,
    FinanceManagedLayout,
    resolve_finance_configuration,
)

FINANCE_STARTUP_MODE_ENV = "UAA_FINANCE_STARTUP_MODE"
FINANCE_STARTUP_ENV_NAMES = (
    *FINANCE_CONFIGURATION_ENV_NAMES,
    FINANCE_STARTUP_MODE_ENV,
)
FINANCE_STARTUP_METADATA_KEY = "finance_startup_configuration_ref"
_IDENTITY_DOMAIN = b"uaa:finance-startup-configuration:v2\x00"


def finance_startup_environment(environ: Mapping[str, str]) -> dict[str, str]:
    """Copy only admitted names, preserving absent, empty, and invalid values."""

    return {name: environ[name] for name in FINANCE_STARTUP_ENV_NAMES if name in environ}


def capture_finance_startup_environment(
    environ: Mapping[str, str], layout: FinanceManagedLayout | None = None,
) -> dict[str, str]:
    """Discover once and freeze the resulting mode; caller markers are ignored."""

    resolution = resolve_finance_configuration(environ, layout)
    snapshot = dict(resolution.effective_environment)
    snapshot[FINANCE_STARTUP_MODE_ENV] = resolution.mode
    return snapshot


def consume_finance_startup_environment(
    environ: Mapping[str, str], layout: FinanceManagedLayout | None = None,
) -> FinanceConfigurationResolution:
    """A captured backend never discovers a later on-disk profile implicitly."""

    if FINANCE_STARTUP_MODE_ENV not in environ:
        return resolve_finance_configuration(environ, layout)
    mode = environ[FINANCE_STARTUP_MODE_ENV]
    effective = tuple(
        (name, environ[name]) for name in FINANCE_CONFIGURATION_ENV_NAMES
        if name in environ
    )
    if mode == "absent" and not any(name in environ for name in FINANCE_EXPLICIT_ENV_NAMES):
        return FinanceConfigurationResolution(
            mode="absent", effective_environment=effective, repository_dir=None,
            helper_path=None, helper_sha256=None, profile_ref=None,
            state_ref=None, error_code=None,
        )
    if mode in {"explicit", "managed"} and all(name in environ for name in FINANCE_EXPLICIT_ENV_NAMES):
        # Presence selects A's explicit branch before any layout discovery.
        # The same structural grammar validates both captured source modes.
        resolution = resolve_finance_configuration(dict(effective), layout)
        if resolution.mode == "explicit":
            return replace(resolution, mode=mode)
        return resolution
    return FinanceConfigurationResolution(
        mode="invalid", effective_environment=effective, repository_dir=None,
        helper_path=None, helper_sha256=None, profile_ref=None,
        state_ref=None, error_code="FIN003_MANAGED_STARTUP_MODE_INVALID",
    )


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
