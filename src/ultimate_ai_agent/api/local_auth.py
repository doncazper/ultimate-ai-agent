from __future__ import annotations

import hmac
import os
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ultimate_ai_agent.api.contracts import ApiRouteClassification
from ultimate_ai_agent.api.manifest import (
    PUBLIC_METADATA_PATHS,
    route_classification_for_path,
    route_side_effect_class,
)
from ultimate_ai_agent.core.local_model_management import llama_cpp_gateway_authorized
from ultimate_ai_agent.core.mattermost import mattermost_bridge_authority_error
from ultimate_ai_agent.core.openwebui_bridge import openwebui_test_gateway_authorized
from ultimate_ai_agent.core.task_decomposition.api_safety import task_decomposition_authority_error


LOCAL_API_AUTH_ENABLED_ENV = "UAA_API_LOCAL_AUTH_ENABLED"
LOCAL_API_BEARER_ENV = "UAA_API_LOCAL_BEARER"
LOCAL_API_BEARER_FILE_ENV = "UAA_LOCAL_RUNTIME_SECRET_FILE"
LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV = "UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY"
LOCAL_API_AUTH_POLICY_REF = "auth:p1-083:local-protected-routes:v1"
MIN_LOCAL_API_BEARER_LENGTH = 12
MAX_LOCAL_API_BEARER_FILE_BYTES = 4096

LOCAL_AUTH_PUBLIC_METADATA_PATHS = frozenset({*PUBLIC_METADATA_PATHS, "/openapi.json"})
LOCAL_AUTH_PROTECTED_CLASSIFICATIONS = frozenset(
    {
        ApiRouteClassification.local_readonly,
        ApiRouteClassification.local_sensitive,
        ApiRouteClassification.mutating_requires_authority,
    }
)


@dataclass(frozen=True)
class LocalApiAuthFailure:
    status_code: int
    code: str
    safe_message: str


def _env_values(env: Mapping[str, str] | None = None) -> Mapping[str, str]:
    return os.environ if env is None else env


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def local_api_bearer_value(env: Mapping[str, str] | None = None) -> str | None:
    values = _env_values(env)
    value = values.get(LOCAL_API_BEARER_ENV, "").strip()
    if value:
        return value
    path_value = values.get(LOCAL_API_BEARER_FILE_ENV, "").strip()
    if not path_value:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        return None
    try:
        metadata = path.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size <= 0
            or metadata.st_size > MAX_LOCAL_API_BEARER_FILE_BYTES
        ):
            return None
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        )
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if (
                opened.st_dev != metadata.st_dev
                or opened.st_ino != metadata.st_ino
                or not stat.S_ISREG(opened.st_mode)
                or opened.st_size <= 0
                or opened.st_size > MAX_LOCAL_API_BEARER_FILE_BYTES
            ):
                return None
            raw_value = stream.read(MAX_LOCAL_API_BEARER_FILE_BYTES + 1)
        if len(raw_value) > MAX_LOCAL_API_BEARER_FILE_BYTES:
            return None
        file_value = raw_value.decode("utf-8").strip()
    except (OSError, UnicodeError):
        return None
    return file_value or None


def local_api_auth_configured(env: Mapping[str, str] | None = None) -> bool:
    values = _env_values(env)
    return _truthy(values.get(LOCAL_API_AUTH_ENABLED_ENV)) or bool(local_api_bearer_value(values))


def local_api_auth_dev_bypass_enabled(env: Mapping[str, str] | None = None) -> bool:
    return _truthy(_env_values(env).get(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV))


def route_requires_local_api_auth(method: str, path: str) -> bool:
    if method.upper() in {"OPTIONS", "HEAD"}:
        return False
    if path in LOCAL_AUTH_PUBLIC_METADATA_PATHS:
        return False
    side_effect_class = route_side_effect_class(path)
    route_classification, _reason = route_classification_for_path(method, path, side_effect_class)
    return route_classification in LOCAL_AUTH_PROTECTED_CLASSIFICATIONS


def local_api_authorized(
    authorization_header: str | None,
    *,
    env: Mapping[str, str] | None = None,
) -> bool:
    expected = local_api_bearer_value(env)
    if not expected or len(expected) < MIN_LOCAL_API_BEARER_LENGTH:
        return False
    if not authorization_header:
        return False
    scheme, _, value = authorization_header.strip().partition(" ")
    return scheme.lower() == "bearer" and hmac.compare_digest(value, expected)


def endpoint_specific_local_authorized(
    authorization_header: str | None,
    *,
    path: str,
    env: Mapping[str, str] | None = None,
) -> bool:
    values = _env_values(env)
    if path.startswith("/v1/"):
        return openwebui_test_gateway_authorized(
            authorization_header,
            values,
        ) or llama_cpp_gateway_authorized(authorization_header, values)
    if path.startswith("/task-decomposition"):
        return task_decomposition_authority_error(authorization_header, values) is None
    if path.startswith("/integrations/mattermost"):
        return mattermost_bridge_authority_error(authorization_header, values) is None
    return False


def local_api_auth_failure(
    authorization_header: str | None,
    *,
    method: str,
    path: str,
    env: Mapping[str, str] | None = None,
) -> LocalApiAuthFailure | None:
    if not route_requires_local_api_auth(method, path):
        return None
    if local_api_auth_dev_bypass_enabled(env):
        return None
    if endpoint_specific_local_authorized(authorization_header, path=path, env=env):
        return None
    expected = local_api_bearer_value(env)
    if not expected or len(expected) < MIN_LOCAL_API_BEARER_LENGTH:
        return LocalApiAuthFailure(
            status_code=503,
            code="LOCAL_API_AUTH_NOT_CONFIGURED",
            safe_message="Local protected-route auth is enabled but no valid local bearer is configured.",
        )
    if local_api_authorized(authorization_header, env=env):
        return None
    return LocalApiAuthFailure(
        status_code=401,
        code="LOCAL_API_AUTH_REQUIRED",
        safe_message="Local protected routes require the configured local bearer value.",
    )


def local_api_auth_policy_payload() -> dict[str, object]:
    return {
        "policy_ref": LOCAL_API_AUTH_POLICY_REF,
        "fail_closed_by_default": True,
        "enabled_env": LOCAL_API_AUTH_ENABLED_ENV,
        "bearer_env": LOCAL_API_BEARER_ENV,
        "bearer_file_env": LOCAL_API_BEARER_FILE_ENV,
        "maximum_bearer_file_bytes": MAX_LOCAL_API_BEARER_FILE_BYTES,
        "dev_only_bypass_env": LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
        "dev_only_bypass_enabled": local_api_auth_dev_bypass_enabled(),
        "public_metadata_paths": sorted(LOCAL_AUTH_PUBLIC_METADATA_PATHS),
        "protected_route_classifications": sorted(
            classification.value for classification in LOCAL_AUTH_PROTECTED_CLASSIFICATIONS
        ),
        "minimum_bearer_length": MIN_LOCAL_API_BEARER_LENGTH,
        "authorization_header_scheme": "Bearer",
        "session_cookie_auth_enabled": False,
        "enterprise_auth_enabled": False,
        "multi_user_auth_enabled": False,
        "oauth_enabled": False,
        "password_flow_enabled": False,
        "dev_only_bypass_production_authority": False,
        "production_authority_enabled": False,
    }
