from typing import Any
import asyncio
import time

from ultimate_ai_agent.core.task_decomposition import (
    CapabilityCallContext,
    CapabilityCallStatus,
    CapabilityContract,
    CapabilityKind,
    CapabilityRegistry,
    CapabilityRoutingCard,
    DAGExecutionStatus,
    DAGExecutor,
    DataSensitivity,
    ExecutionMode,
    NodeExecutionStatus,
    PlanStrategy,
    PlanValidationStatus,
    PlanValidator,
    ReflectionStore,
    RiskLevel,
    TaskDecomposer,
    TaskNode,
    TaskNodeStrategy,
    TaskPlan,
    build_example_registry,
)


REQUEST_SCHEMA = {
    "type": "object",
    "required": ["request"],
    "properties": {"request": {"type": "string"}},
    "additionalProperties": True,
}

OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {"type": "boolean"},
        "summary": {"type": "string"},
        "status": {"type": "string"},
    },
    "additionalProperties": True,
}


def _contract(
    capability_id: str,
    *,
    summary: str = "Run a safe local capability.",
    risk: RiskLevel = RiskLevel.low,
    requires_approval: bool = False,
    permissions: list[str] | None = None,
    execution_mode: ExecutionMode = ExecutionMode.python_callable,
    concurrency_limit: int = 1,
    retry_policy: dict | None = None,
    kind: CapabilityKind = CapabilityKind.tool,
) -> CapabilityContract:
    return CapabilityContract(
        card=CapabilityRoutingCard(
            id=capability_id,
            name=capability_id.replace("capability:", "").replace("-", " ").title(),
            version="1.0.0",
            kind=kind,
            summary=summary,
            use_when=[summary],
            domains=["testing", "planning"],
            tags=["test", "summary", "workflow"],
            input_hints=["request"],
            output_hints=["success", "summary", "status"],
            risk_level=risk,
            requires_approval=requires_approval,
            typical_latency_ms=10,
            reliability_score=0.9,
        ),
        input_schema=REQUEST_SCHEMA,
        output_schema=OUTPUT_SCHEMA,
        side_effects=["none"],
        required_permissions=permissions or ["compute"],
        data_sensitivity=DataSensitivity.public,
        execution_mode=execution_mode,
        handler_ref=f"tests.{capability_id}",
        timeout_s=5,
        retry_policy=retry_policy or {"max_attempts": 1, "backoff_s": 0.0},
        concurrency_limit=concurrency_limit,
    )


def _success_handler(args: Any, context: Any) -> dict[str, Any]:
    return {"success": True, "status": "succeeded", "summary": str(args.get("request", "done"))}


def _plan(nodes: list[TaskNode]) -> TaskPlan:
    return TaskPlan(
        plan_id="task-decomposition-plan:test",
        goal="Run test plan.",
        strategy=PlanStrategy.dag_plan,
        nodes=nodes,
        final_success_criteria=["Produces validated output."],
    )


def test_registry_registers_searches_ranks_and_exports_json() -> None:
    registry = build_example_registry()
    cards = registry.search("summary request", top_k=2)

    assert cards
    assert cards[0].id == "capability:example-echo-summary"

    intent = TaskDecomposer(registry).classify_intent("Summarize this request.")
    ranked = registry.rank_for_task(intent, cards)
    assert ranked[0].id == "capability:example-echo-summary"

    imported = CapabilityRegistry.from_json(registry.export_json())
    assert imported.get("capability:example-echo-summary") is not None
    assert imported.get("capability:example-validation-workflow") is not None


def test_registry_validates_schema_and_rejects_unregistered_capability() -> None:
    registry = build_example_registry()

    missing = registry.validate_call("capability:missing", {"request": "x"})
    assert missing.status == CapabilityCallStatus.unavailable
    assert "CAPABILITY_NOT_REGISTERED" in missing.reason_codes

    invalid = registry.validate_call("capability:example-echo-summary", {})
    assert invalid.valid is False
    assert any(code.startswith("SCHEMA_REQUIRED_MISSING") for code in invalid.reason_codes)


def test_validator_detects_cycle_and_missing_capability() -> None:
    registry = build_example_registry()
    plan = _plan(
        [
            TaskNode(
                id="node:a",
                title="A",
                objective="A",
                depends_on=["node:b"],
                candidate_capabilities=["capability:example-echo-summary"],
                selected_capability="capability:example-echo-summary",
                input_bindings={"request": "a"},
                success_criteria=["A succeeds."],
            ),
            TaskNode(
                id="node:b",
                title="B",
                objective="B",
                depends_on=["node:a"],
                candidate_capabilities=["capability:missing"],
                selected_capability=None,
                input_bindings={"request": "b"},
                success_criteria=["B succeeds."],
            ),
        ]
    )

    result = PlanValidator().validate(plan, registry)

    assert result.valid is False
    assert "TASK_PLAN_DEPENDENCY_CYCLE" in result.reason_codes
    assert "TASK_PLAN_CANDIDATE_CAPABILITY_MISSING" in result.reason_codes


def test_validator_schema_issue_uses_redacted_safe_message() -> None:
    registry = build_example_registry()
    plan = _plan(
        [
            TaskNode(
                id="node:redacted",
                title="Redacted",
                objective="Redacted",
                candidate_capabilities=["capability:example-echo-summary"],
                selected_capability="capability:example-echo-summary",
                input_bindings={"request": "token=should-not-appear"},
                success_criteria=["Redacted succeeds."],
            )
        ]
    )
    invalid_node = plan.nodes[0].model_copy(update={"title": ""})
    invalid_plan = plan.model_copy(update={"nodes": [invalid_node]})

    result = PlanValidator().validate(invalid_plan, registry)

    assert "TASK_PLAN_SCHEMA_INVALID" in result.reason_codes
    schema_issue = next(issue for issue in result.issues if issue.reason_code == "TASK_PLAN_SCHEMA_INVALID")
    assert schema_issue.safe_message == "Task plan schema validation failed safely; details are redacted."
    assert "should-not-appear" not in schema_issue.safe_message


def test_risky_capability_requires_plan_gate_and_runtime_approval() -> None:
    registry = CapabilityRegistry()
    registry.register(
        _contract(
            "capability:write-preview",
            risk=RiskLevel.medium,
            requires_approval=True,
            permissions=["write:file"],
        ),
        _success_handler,
    )
    unsafe_plan = _plan(
        [
            TaskNode(
                id="node:write",
                title="Write",
                objective="Write",
                candidate_capabilities=["capability:write-preview"],
                selected_capability="capability:write-preview",
                input_bindings={"request": "write a file"},
                success_criteria=["Write preview succeeds."],
            )
        ]
    )

    validation = PlanValidator().validate(unsafe_plan, registry)
    assert validation.valid is False
    assert "TASK_PLAN_RISK_APPROVAL_GATE_MISSING" in validation.reason_codes

    gated_plan = unsafe_plan.model_copy(
        update={"nodes": [unsafe_plan.nodes[0].model_copy(update={"requires_approval": True})]}
    )
    gated_validation = PlanValidator().validate(gated_plan, registry)
    assert gated_validation.valid is True
    assert gated_validation.status == PlanValidationStatus.approval_required

    result = asyncio.run(DAGExecutor(registry).execute(gated_plan))
    assert result.status == DAGExecutionStatus.awaiting_approval
    assert result.node_records[0].status == NodeExecutionStatus.awaiting_approval

    approved = CapabilityCallContext(approved_capability_ids=["capability:write-preview"])
    approved_result = asyncio.run(DAGExecutor(registry).execute(gated_plan, approved))
    assert approved_result.status == DAGExecutionStatus.succeeded


def test_executor_runs_dag_in_dependency_order() -> None:
    events: list[str] = []
    registry = CapabilityRegistry()

    def first(args: Any, context: Any) -> dict[str, Any]:
        events.append("first")
        return {"success": True, "status": "succeeded", "summary": "first"}

    def second(args: Any, context: Any) -> dict[str, Any]:
        events.append(f"second:{args['request']}")
        return {"success": True, "status": "succeeded", "summary": "second"}

    registry.register(_contract("capability:first"), first)
    registry.register(_contract("capability:second"), second)
    plan = _plan(
        [
            TaskNode(
                id="node:first",
                title="First",
                objective="First",
                candidate_capabilities=["capability:first"],
                selected_capability="capability:first",
                input_bindings={"request": "start"},
                success_criteria=["First succeeds."],
            ),
            TaskNode(
                id="node:second",
                title="Second",
                objective="Second",
                depends_on=["node:first"],
                candidate_capabilities=["capability:second"],
                selected_capability="capability:second",
                input_bindings={"request": "$node:first.summary"},
                success_criteria=["Second succeeds."],
            ),
        ]
    )

    result = asyncio.run(DAGExecutor(registry).execute(plan))

    assert result.status == DAGExecutionStatus.succeeded
    assert events == ["first", "second:first"]


def test_executor_runs_independent_nodes_in_parallel() -> None:
    registry = CapabilityRegistry()

    async def sleeper(args: Any, context: Any) -> dict[str, Any]:
        await asyncio.sleep(0.05)
        return {"success": True, "status": "succeeded", "summary": args["request"]}

    registry.register(_contract("capability:sleep-a", concurrency_limit=2), sleeper)
    registry.register(_contract("capability:sleep-b", concurrency_limit=2), sleeper)
    plan = _plan(
        [
            TaskNode(
                id="node:a",
                title="A",
                objective="A",
                candidate_capabilities=["capability:sleep-a"],
                selected_capability="capability:sleep-a",
                input_bindings={"request": "a"},
                success_criteria=["A succeeds."],
            ),
            TaskNode(
                id="node:b",
                title="B",
                objective="B",
                candidate_capabilities=["capability:sleep-b"],
                selected_capability="capability:sleep-b",
                input_bindings={"request": "b"},
                success_criteria=["B succeeds."],
            ),
        ]
    )

    started = time.perf_counter()
    result = asyncio.run(DAGExecutor(registry, parallel=True).execute(plan))
    elapsed = time.perf_counter() - started

    assert result.status == DAGExecutionStatus.succeeded
    assert elapsed < 0.09


def test_executor_retries_failed_node_until_success() -> None:
    registry = CapabilityRegistry()
    calls = {"count": 0}

    def flaky(args: Any, context: Any) -> dict[str, Any]:
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("boom")
        return {"success": True, "status": "succeeded", "summary": "recovered"}

    registry.register(
        _contract("capability:flaky", retry_policy={"max_attempts": 2, "backoff_s": 0.0}),
        flaky,
    )
    plan = _plan(
        [
            TaskNode(
                id="node:flaky",
                title="Flaky",
                objective="Flaky",
                candidate_capabilities=["capability:flaky"],
                selected_capability="capability:flaky",
                input_bindings={"request": "retry"},
                success_criteria=["Retry succeeds."],
            )
        ]
    )

    result = asyncio.run(DAGExecutor(registry).execute(plan))

    assert result.status == DAGExecutionStatus.succeeded
    assert result.node_records[0].attempts == 2
    assert calls["count"] == 2


def test_executor_triggers_repair_hook_when_fallback_exists() -> None:
    registry = CapabilityRegistry()

    def failing(args: Any, context: Any) -> dict[str, Any]:
        return {"success": False, "status": "failed", "summary": "failed"}

    registry.register(_contract("capability:failing"), failing)
    plan = _plan(
        [
            TaskNode(
                id="node:primary",
                title="Primary",
                objective="Primary",
                candidate_capabilities=["capability:failing"],
                selected_capability="capability:failing",
                input_bindings={"request": "fail"},
                success_criteria=["Primary succeeds."],
                fallback_node_ids=["node:repair"],
            ),
            TaskNode(
                id="node:repair",
                title="Repair",
                objective="Repair",
                depends_on=["node:primary"],
                decomposition_strategy=TaskNodeStrategy.repair,
                input_bindings={"request": "repair"},
                success_criteria=["Repair is requested."],
            ),
        ]
    )

    result = asyncio.run(DAGExecutor(registry).execute(plan))

    assert result.repair_requested is True
    assert result.repair_node_ids == ["node:repair"]
    assert result.status == DAGExecutionStatus.failed
    assert any(record.node_id == "node:repair" and record.status == NodeExecutionStatus.succeeded for record in result.node_records)


def test_reflection_store_records_failures_and_promotes_repeated_successes() -> None:
    promoted = []
    store = ReflectionStore(promotion_hook=promoted.append, promotion_threshold=2)
    registry = build_example_registry()
    plan = TaskDecomposer(registry).decompose("Summarize this request directly")
    result = asyncio.run(DAGExecutor(registry).execute(plan))

    store.record_execution(plan, result)
    store.record_execution(plan, result)

    assert store.reflections() == []
    assert promoted
    assert store.promotion_candidates()[0].promoted is True


def test_end_to_end_decompose_validate_and_execute() -> None:
    registry = build_example_registry()
    decomposer = TaskDecomposer(registry)

    plan = decomposer.decompose("Summarize this request directly.")
    validation = decomposer.validate_plan(plan)
    result = asyncio.run(DAGExecutor(registry).execute(plan))

    assert validation.valid is True
    assert plan.strategy == PlanStrategy.direct
    assert result.status == DAGExecutionStatus.succeeded
    assert result.outputs["node:direct"]["success"] is True
