from __future__ import annotations

from typing import Any

from ultimate_ai_agent.core.capabilities.models import CapabilityPolicy, CapabilitySpec, RiskLevel


def capability_from_openapi_operation(
    *,
    name: str,
    path: str,
    method: str,
    operation: dict[str, Any],
    version: str = "1.0.0",
) -> CapabilitySpec:
    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {}) if isinstance(request_body, dict) else {}
    json_body = content.get("application/json", {}) if isinstance(content, dict) else {}
    input_schema = json_body.get("schema") or {"type": "object", "additionalProperties": True}
    responses = operation.get("responses", {})
    success = responses.get("200") or responses.get("201") or {}
    success_content = success.get("content", {}) if isinstance(success, dict) else {}
    output_schema = success_content.get("application/json", {}).get("schema") if isinstance(success_content, dict) else None
    return CapabilitySpec(
        id=f"capability:{name}:{version}",
        name=name,
        version=version,
        title=operation.get("summary") or name,
        description=operation.get("description") or operation.get("summary") or f"{method.upper()} {path}",
        tags=set(operation.get("tags", [])),
        input_schema=input_schema,
        output_schema=output_schema,
        policy=CapabilityPolicy(risk=RiskLevel.EXTERNAL_NETWORK, requires_approval=True),
        source="openapi",
        metadata={"path": path, "method": method.upper(), "operation_id": operation.get("operationId")},
    )
