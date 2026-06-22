from __future__ import annotations

import hmac
import os
from collections.abc import Mapping
from dataclasses import dataclass

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
LOCAL_API_AUTH_POLICY_REF = "auth:p1-083:local-protected-routes:v1"
MIN_LOCAL_API_BEARER_LENGTH = 12

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
    value = _env_values(env).get(LOCAL_API_BEARER_ENV, "").strip()
    return value or None


def local_api_auth_configured(env: Mapping[str, str] | None = None) -> bool:
    values = _env_values(env)
    return _truthy(values.get(LOCAL_API_AUTH_ENABLED_ENV)) or bool(local_api_bearer_value(values))


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
    if not local_api_auth_configured(env):
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
        "enabled_env": LOCAL_API_AUTH_ENABLED_ENV,
        "bearer_env": LOCAL_API_BEARER_ENV,
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
        "production_authority_enabled": False,
    }
