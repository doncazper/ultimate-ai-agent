from __future__ import annotations

from typing import Any

from ultimate_ai_agent.core.task_decomposition.contracts import (
    CapabilityCallContext,
    CapabilityContract,
    CapabilityRoutingCard,
)
from ultimate_ai_agent.core.task_decomposition.enums import (
    CapabilityKind,
    CostHint,
    DataSensitivity,
    ExecutionMode,
    RiskLevel,
)
from ultimate_ai_agent.core.task_decomposition.registry import CapabilityRegistry


REQUEST_INPUT_SCHEMA = {
    "type": "object",
    "required": ["request"],
    "properties": {
        "request": {"type": "string"},
    },
    "additionalProperties": True,
}

SUCCESS_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {"type": "boolean"},
        "summary": {"type": "string"},
        "status": {"type": "string"},
    },
    "additionalProperties": True,
}


def echo_summary_handler(args: dict[str, Any], context: CapabilityCallContext) -> dict[str, Any]:
    request = str(args.get("request", ""))
    return {
        "success": True,
        "status": "succeeded",
        "summary": f"Processed request with {len(request.split())} words.",
        "run_id": context.run_id,
    }


def validation_workflow_handler(args: dict[str, Any], context: CapabilityCallContext) -> dict[str, Any]:
    request = str(args.get("request", ""))
    return {
        "success": bool(request.strip()),
        "status": "succeeded" if request.strip() else "failed",
        "summary": "Validated request shape through local workflow capability.",
        "run_id": context.run_id,
    }


def build_echo_tool_capability() -> CapabilityContract:
    return CapabilityContract(
        card=CapabilityRoutingCard(
            id="capability:example-echo-summary",
            name="Example Echo Summary",
            version="1.0.0",
            kind=CapabilityKind.tool,
            summary="Summarize a request locally without side effects.",
            use_when=["Need a simple local summary or direct task placeholder."],
            do_not_use_when=["A capability requires shell, network, private data, or mutation."],
            domains=["planning", "summary"],
            tags=["example", "local", "summary", "direct"],
            input_hints=["request"],
            output_hints=["success", "summary", "status"],
            risk_level=RiskLevel.low,
            requires_approval=False,
            typical_latency_ms=25,
            cost_hint=CostHint.free,
            reliability_score=0.95,
        ),
        input_schema=REQUEST_INPUT_SCHEMA,
        output_schema=SUCCESS_OUTPUT_SCHEMA,
        examples=[{"input": {"request": "Summarize this task."}, "output": {"success": True}}],
        limitations=["Example capability for local deterministic tests."],
        side_effects=["none"],
        required_permissions=["compute"],
        data_sensitivity=DataSensitivity.public,
        execution_mode=ExecutionMode.python_callable,
        handler_ref="example.echo_summary_handler",
        timeout_s=5,
        retry_policy={"max_attempts": 1, "backoff_s": 0.0},
        cache_policy={"cacheable": True},
        concurrency_limit=4,
        preconditions=["Input request is a safe summary string."],
        postconditions=["Output contains a concise safe summary."],
    )


def build_validation_workflow_capability() -> CapabilityContract:
    return CapabilityContract(
        card=CapabilityRoutingCard(
            id="capability:example-validation-workflow",
            name="Example Validation Workflow",
            version="1.0.0",
            kind=CapabilityKind.workflow,
            summary="Run a local validation workflow for known request shapes.",
            use_when=["Need a reusable workflow for validating and summarizing simple requests."],
            do_not_use_when=["The request needs external systems or unregistered tools."],
            domains=["workflow", "validation", "planning"],
            tags=["example", "workflow", "skill_reuse", "validation"],
            input_hints=["request"],
            output_hints=["success", "summary", "status"],
            risk_level=RiskLevel.low,
            requires_approval=False,
            typical_latency_ms=40,
            cost_hint=CostHint.free,
            reliability_score=0.9,
        ),
        input_schema=REQUEST_INPUT_SCHEMA,
        output_schema=SUCCESS_OUTPUT_SCHEMA,
        examples=[{"input": {"request": "Validate this plan."}, "output": {"success": True}}],
        limitations=["Workflow example is local and deterministic."],
        side_effects=["none"],
        required_permissions=["workflow"],
        data_sensitivity=DataSensitivity.public,
        execution_mode=ExecutionMode.workflow,
        handler_ref="example.validation_workflow_handler",
        timeout_s=5,
        retry_policy={"max_attempts": 1, "backoff_s": 0.0},
        cache_policy={"cacheable": True},
        concurrency_limit=2,
        preconditions=["Input request is available."],
        postconditions=["Validation status is returned."],
    )


def build_example_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register(build_echo_tool_capability(), echo_summary_handler)
    registry.register(build_validation_workflow_capability(), validation_workflow_handler)
    return registry
