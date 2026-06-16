import pytest

from ultimate_ai_agent.core.autonomy import (
    M136_MAX_DEPENDENCY_STEP_REFS,
    M136_MAX_TOOL_REFS,
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    CrossToolDependencyEdge,
    CrossToolDependencyExecutionPolicy,
    CrossToolDependencyExecutionRequest,
    CrossToolDependencyExecutionStatus,
    build_cross_tool_dependency_execution_decision,
    validate_cross_tool_dependency_execution_decision,
    validate_cross_tool_dependency_execution_policy,
    validate_cross_tool_dependency_execution_request,
)


def _edge(edge_ref, upstream, downstream):
    return CrossToolDependencyEdge(
        edge_ref=edge_ref,
        upstream_step_ref=upstream,
        downstream_step_ref=downstream,
        dependency_kind_ref="dependency-kind:m136:safe-output-ref",
        safe_dependency_summary="A safe dependency ref is reviewed before any execution.",
    )


def _request(**overrides):
    steps = [
        "dependency-step:m136:collect-safe-ref",
        "dependency-step:m136:review-safe-ref",
        "dependency-step:m136:final-safe-summary",
    ]
    data = {
        "request_ref": "cross-tool-dependency-execution-request:m136:review",
        "dependency_execution_plan_ref": "cross-tool-dependency-execution-plan:m136:review",
        "mode_ref": "autonomy-mode:m136:mode5",
        "actor_ref": "actor:m136:reviewer",
        "user_ref": "user:m136:owner",
        "workspace_ref": "workspace:m136:local",
        "scope_ref": "scope:m136:single-workspace",
        "resource_refs": ["resource:m136:dependency-summary"],
        "capability_refs": ["capability:m136:dependency-graph-review"],
        "allowlist_refs": ["allowlist:m136:safe-tool-refs-only"],
        "m135_recovery_planner_decision_ref": (
            "autonomous-recovery-planner-decision:m135:review"
        ),
        "m134_human_checkpoint_decision_ref": (
            "human-checkpoint-scheduling-decision:m134:review"
        ),
        "m133_supervisor_decision_ref": (
            "long-running-task-supervisor-decision:m133:review"
        ),
        "m132_trusted_workflow_decision_ref": (
            "trusted-recurring-workflow-decision:m132:review"
        ),
        "dependency_graph_ref": "dependency-graph:m136:declared",
        "dependency_step_refs": steps,
        "dependency_edges": [
            _edge("dependency-edge:m136:first", steps[0], steps[1]),
            _edge("dependency-edge:m136:second", steps[1], steps[2]),
        ],
        "safe_tool_refs": [
            "tool:m136:first-safe-tool-ref",
            "tool:m136:second-safe-tool-ref",
        ],
        "dry_run_plan_ref": "dry-run-plan:m136:no-execution",
        "execution_order_ref": "execution-order:m136:review-only",
        "dependency_resolution_ref": "dependency-resolution:m136:safe-refs-only",
        "conflict_policy_ref": "conflict-policy:m136:human-review",
        "failure_policy_ref": "failure-policy:m136:stop-and-review",
        "recovery_plan_ref": "recovery-plan:m136:no-execution",
        "checkpoint_ref": "checkpoint:m136:human-review",
        "human_checkpoint_ref": "human-checkpoint:m136:owner-review",
        "policy_decision_ref": "policy-decision:m136:mode5-dependency-review",
        "risk_decision_ref": "risk-decision:m136:low-only",
        "audit_ref": "audit:m136:dependency-review",
        "replay_ref": "replay:m136:dependency-review",
        "revocation_ref": "revocation:m136:dependency-review",
        "kill_switch_ref": "kill-switch:m136:dependency-review",
        "no_effect_receipt_plan_ref": "receipt-plan:m136:dependency:no-effect",
        "max_dependency_steps": M136_MAX_DEPENDENCY_STEP_REFS,
        "max_risk_class": AutonomyRiskClass.low,
        "safe_dependency_summary": (
            "Review a cross-tool dependency execution contract without running tools."
        ),
    }
    data.update(overrides)
    return CrossToolDependencyExecutionRequest(**data)


def test_m136_cross_tool_dependency_execution_is_review_only_and_route_free():
    decision = build_cross_tool_dependency_execution_decision(_request())

    assert decision.status == CrossToolDependencyExecutionStatus.ready_for_review
    assert decision.selected_mode == AutonomyAuthorityMode.trusted_recurring_automation
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.cross_tool_dependency_execution_only is True
    assert decision.deterministic is True
    assert decision.local_only is True
    assert decision.safe_refs_only is True
    assert decision.exact_scope_bound is True
    assert decision.mode5_bound is True
    assert decision.m135_recovery_planner_bound is True
    assert decision.m134_human_checkpoint_bound is True
    assert decision.m133_supervisor_bound is True
    assert decision.m132_trusted_workflow_bound is True
    assert decision.dependency_graph_bound is True
    assert decision.acyclic_graph_validated is True
    assert decision.dependency_order_bound is True
    assert decision.cross_tool_scope_bound is True
    assert decision.dry_run_plan_bound is True
    assert decision.human_checkpoint_bound is True
    assert decision.audit_replay_bound is True
    assert decision.revocation_bound is True
    assert decision.kill_switch_bound is True
    assert decision.no_effect_receipt_required is True
    assert decision.dependency_order_refs == [
        "dependency-step:m136:collect-safe-ref",
        "dependency-step:m136:review-safe-ref",
        "dependency-step:m136:final-safe-summary",
    ]
    assert decision.mode5_runtime_authorized is False
    assert decision.cross_tool_dependency_runtime_authorized is False
    assert decision.dependency_execution_authorized is False
    assert decision.dependency_execution_performed is False
    assert decision.dependency_resolver_runtime_started is False
    assert decision.cross_tool_runtime_started is False
    assert decision.parallel_tool_execution_performed is False
    assert decision.tool_state_handoff_performed is False
    assert decision.tool_output_routing_performed is False
    assert decision.recovery_execution_performed is False
    assert decision.supervisor_runtime_started is False
    assert decision.autonomous_actions_authorized is False
    assert decision.execution_authorized is False
    assert decision.tool_execution_authorized is False
    assert decision.tool_execution_performed is False
    assert decision.shell_execution_performed is False
    assert decision.network_access_performed is False
    assert decision.browser_automation_performed is False
    assert decision.plugin_execution_performed is False
    assert decision.connector_runtime_performed is False
    assert decision.model_call_performed is False
    assert decision.memory_write_performed is False
    assert decision.context_injection_performed is False
    assert decision.backend_route_added is False
    assert decision.dependency_added is False
    assert decision.production_authority_granted is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_dependency_order_refs_only is True
    assert decision.receipt_plan.store_raw_tool_payload is False
    assert decision.receipt_plan.dependency_execution_performed is False
    assert decision.receipt_plan.dependency_order_refs == decision.dependency_order_refs
    assert decision.reason_codes == [
        "M136_CROSS_TOOL_DEPENDENCY_EXECUTION_CONTRACT_ONLY",
        "M136_ACYCLIC_DEPENDENCY_GRAPH_REQUIRED",
        "M136_EXACT_TOOL_SCOPE_REQUIRED",
        "M136_NO_DEPENDENCY_EXECUTION",
        "M137_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("mode5_runtime_enabled", "M136_MODE5_RUNTIME_DENIED"),
        ("cross_tool_dependency_runtime_enabled", "M136_CROSS_TOOL_RUNTIME_DENIED"),
        ("dependency_execution_enabled", "M136_DEPENDENCY_EXECUTION_DENIED"),
        ("dependency_resolver_runtime_enabled", "M136_DEPENDENCY_RESOLVER_DENIED"),
        ("cross_tool_runtime_enabled", "M136_CROSS_TOOL_RUNTIME_DENIED"),
        ("parallel_tool_execution_enabled", "M136_PARALLEL_TOOL_EXECUTION_DENIED"),
        ("tool_state_handoff_enabled", "M136_TOOL_STATE_HANDOFF_DENIED"),
        ("tool_output_routing_enabled", "M136_TOOL_OUTPUT_ROUTING_DENIED"),
        ("recovery_execution_enabled", "M136_RECOVERY_EXECUTION_DENIED"),
        ("supervisor_runtime_enabled", "M136_SUPERVISOR_RUNTIME_DENIED"),
        ("checkpoint_scheduler_enabled", "M136_CHECKPOINT_SCHEDULER_DENIED"),
        ("scheduler_enabled", "M136_SCHEDULER_DENIED"),
        ("background_worker_enabled", "M136_BACKGROUND_WORKER_DENIED"),
        ("autonomous_actions_enabled", "M136_AUTONOMOUS_ACTIONS_DENIED"),
        ("execution_enabled", "M136_EXECUTION_DENIED"),
        ("tool_execution_enabled", "M136_TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "M136_SHELL_EXECUTION_DENIED"),
        ("network_access_enabled", "M136_NETWORK_ACCESS_DENIED"),
        ("browser_automation_enabled", "M136_BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "M136_PLUGIN_EXECUTION_DENIED"),
        ("connector_runtime_enabled", "M136_CONNECTOR_RUNTIME_DENIED"),
        ("model_call_enabled", "M136_MODEL_CALL_DENIED"),
        ("memory_write_enabled", "M136_MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "M136_CONTEXT_INJECTION_DENIED"),
        ("backend_route_enabled", "M136_BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "M136_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M136_DEPENDENCY_DENIED"),
        ("beta_release_enabled", "M136_BETA_RELEASE_DENIED"),
        ("production_authority_granted", "M136_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m136_policy_denies_dependency_runtime_and_future_authority(field, reason):
    with pytest.raises(ValueError, match=reason):
        validate_cross_tool_dependency_execution_policy(
            CrossToolDependencyExecutionPolicy(**{field: True})
        )


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"requested_mode": AutonomyAuthorityMode.scoped_autonomy_window}, "M136_MODE5_REQUIRED"),
        ({"max_risk_class": AutonomyRiskClass.medium}, "M136_RISK_CEILING_DENIED"),
        ({"resource_refs": []}, "M136_RESOURCE_REF_REQUIRED"),
        ({"resource_refs": ["resource:m136:a", "resource:m136:a"]}, "M136_REF_DUPLICATE"),
        ({"capability_refs": []}, "M136_CAPABILITY_REF_REQUIRED"),
        ({"allowlist_refs": []}, "M136_ALLOWLIST_REF_REQUIRED"),
        ({"dependency_step_refs": []}, "M136_DEPENDENCY_STEP_REF_REQUIRED"),
        (
            {
                "dependency_step_refs": [
                    f"dependency-step:m136:{index}"
                    for index in range(M136_MAX_DEPENDENCY_STEP_REFS + 1)
                ]
            },
            "M136_REF_LIST_TOO_LONG",
        ),
        ({"safe_tool_refs": ["tool:m136:only-one"]}, "M136_CROSS_TOOL_SCOPE_REQUIRED"),
        (
            {"safe_tool_refs": [f"tool:m136:{index}" for index in range(M136_MAX_TOOL_REFS + 1)]},
            "M136_REF_LIST_TOO_LONG",
        ),
        ({"mode5_runtime_requested": True}, "M136_MODE5_RUNTIME_DENIED"),
        (
            {"cross_tool_dependency_runtime_requested": True},
            "M136_CROSS_TOOL_RUNTIME_DENIED",
        ),
        ({"dependency_execution_requested": True}, "M136_DEPENDENCY_EXECUTION_DENIED"),
        (
            {"dependency_resolver_runtime_requested": True},
            "M136_DEPENDENCY_RESOLVER_DENIED",
        ),
        ({"cross_tool_runtime_requested": True}, "M136_CROSS_TOOL_RUNTIME_DENIED"),
        (
            {"parallel_tool_execution_requested": True},
            "M136_PARALLEL_TOOL_EXECUTION_DENIED",
        ),
        ({"tool_state_handoff_requested": True}, "M136_TOOL_STATE_HANDOFF_DENIED"),
        ({"tool_output_routing_requested": True}, "M136_TOOL_OUTPUT_ROUTING_DENIED"),
        ({"recovery_execution_requested": True}, "M136_RECOVERY_EXECUTION_DENIED"),
        ({"supervisor_runtime_requested": True}, "M136_SUPERVISOR_RUNTIME_DENIED"),
        ({"checkpoint_scheduler_requested": True}, "M136_CHECKPOINT_SCHEDULER_DENIED"),
        ({"scheduler_requested": True}, "M136_SCHEDULER_DENIED"),
        ({"background_worker_requested": True}, "M136_BACKGROUND_WORKER_DENIED"),
        ({"autonomous_actions_requested": True}, "M136_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_requested": True}, "M136_EXECUTION_DENIED"),
        ({"tool_execution_requested": True}, "M136_TOOL_EXECUTION_DENIED"),
        ({"shell_execution_requested": True}, "M136_SHELL_EXECUTION_DENIED"),
        ({"network_access_requested": True}, "M136_NETWORK_ACCESS_DENIED"),
        ({"browser_automation_requested": True}, "M136_BROWSER_AUTOMATION_DENIED"),
        ({"plugin_execution_requested": True}, "M136_PLUGIN_EXECUTION_DENIED"),
        ({"connector_runtime_requested": True}, "M136_CONNECTOR_RUNTIME_DENIED"),
        ({"model_call_requested": True}, "M136_MODEL_CALL_DENIED"),
        ({"memory_write_requested": True}, "M136_MEMORY_WRITE_DENIED"),
        ({"context_injection_requested": True}, "M136_CONTEXT_INJECTION_DENIED"),
        ({"backend_route_requested": True}, "M136_BACKEND_ROUTE_DENIED"),
        ({"dependency_requested": True}, "M136_DEPENDENCY_DENIED"),
        ({"beta_release_requested": True}, "M136_BETA_RELEASE_DENIED"),
        ({"production_authority_requested": True}, "M136_PRODUCTION_AUTHORITY_DENIED"),
        ({"contains_raw_tool_payload": True}, "M136_RAW_TOOL_PAYLOAD_DENIED"),
        ({"contains_raw_prompt": True}, "M136_RAW_PROMPT_DENIED"),
        (
            {"contains_raw_provider_payload": True},
            "M136_RAW_PROVIDER_PAYLOAD_DENIED",
        ),
        ({"contains_secret": True}, "M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED"),
        ({"side_effects_performed": ["tool-run"]}, "M136_SIDE_EFFECTS_DENIED"),
    ],
)
def test_m136_request_rejects_unbounded_or_executing_dependency_work(
    overrides, reason
):
    with pytest.raises(ValueError, match=reason):
        validate_cross_tool_dependency_execution_request(_request(**overrides))


def test_m136_dependency_graph_requires_known_acyclic_edges():
    steps = [
        "dependency-step:m136:a",
        "dependency-step:m136:b",
        "dependency-step:m136:c",
    ]

    with pytest.raises(ValueError, match="M136_DEPENDENCY_EDGE_REF_REQUIRED"):
        _request(dependency_edges=[])

    with pytest.raises(ValueError, match="M136_DEPENDENCY_EDGE_UNKNOWN_STEP"):
        _request(
            dependency_step_refs=steps,
            dependency_edges=[
                _edge("dependency-edge:m136:unknown", steps[0], "dependency-step:m136:missing")
            ],
        )

    with pytest.raises(ValueError, match="M136_DEPENDENCY_CYCLE_DENIED"):
        _request(
            dependency_step_refs=steps,
            dependency_edges=[
                _edge("dependency-edge:m136:ab", steps[0], steps[1]),
                _edge("dependency-edge:m136:bc", steps[1], steps[2]),
                _edge("dependency-edge:m136:ca", steps[2], steps[0]),
            ],
        )

    with pytest.raises(ValueError, match="M136_SELF_DEPENDENCY_DENIED"):
        _request(
            dependency_step_refs=steps,
            dependency_edges=[_edge("dependency-edge:m136:self", steps[0], steps[0])],
        )


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"selected_mode": AutonomyAuthorityMode.scoped_autonomy_window}, "M136_MODE5_REQUIRED"),
        ({"dependency_order_refs": ["dependency-step:m136:review-safe-ref"]}, "M136_DEPENDENCY_ORDER_MISMATCH"),
        ({"mode5_runtime_authorized": True}, "M136_MODE5_RUNTIME_DENIED"),
        (
            {"cross_tool_dependency_runtime_authorized": True},
            "M136_CROSS_TOOL_RUNTIME_DENIED",
        ),
        ({"dependency_execution_authorized": True}, "M136_DEPENDENCY_EXECUTION_DENIED"),
        ({"dependency_execution_performed": True}, "M136_DEPENDENCY_EXECUTION_DENIED"),
        (
            {"dependency_resolver_runtime_started": True},
            "M136_DEPENDENCY_RESOLVER_DENIED",
        ),
        ({"cross_tool_runtime_started": True}, "M136_CROSS_TOOL_RUNTIME_DENIED"),
        (
            {"parallel_tool_execution_performed": True},
            "M136_PARALLEL_TOOL_EXECUTION_DENIED",
        ),
        ({"tool_state_handoff_performed": True}, "M136_TOOL_STATE_HANDOFF_DENIED"),
        ({"tool_output_routing_performed": True}, "M136_TOOL_OUTPUT_ROUTING_DENIED"),
        ({"recovery_execution_performed": True}, "M136_RECOVERY_EXECUTION_DENIED"),
        ({"supervisor_runtime_started": True}, "M136_SUPERVISOR_RUNTIME_DENIED"),
        ({"checkpoint_scheduler_started": True}, "M136_CHECKPOINT_SCHEDULER_DENIED"),
        ({"scheduler_started": True}, "M136_SCHEDULER_DENIED"),
        ({"background_worker_started": True}, "M136_BACKGROUND_WORKER_DENIED"),
        ({"autonomous_actions_authorized": True}, "M136_AUTONOMOUS_ACTIONS_DENIED"),
        ({"execution_authorized": True}, "M136_EXECUTION_DENIED"),
        ({"tool_execution_authorized": True}, "M136_TOOL_EXECUTION_DENIED"),
        ({"tool_execution_performed": True}, "M136_TOOL_EXECUTION_DENIED"),
        ({"shell_execution_performed": True}, "M136_SHELL_EXECUTION_DENIED"),
        ({"network_access_performed": True}, "M136_NETWORK_ACCESS_DENIED"),
        ({"browser_automation_performed": True}, "M136_BROWSER_AUTOMATION_DENIED"),
        ({"plugin_execution_performed": True}, "M136_PLUGIN_EXECUTION_DENIED"),
        ({"connector_runtime_performed": True}, "M136_CONNECTOR_RUNTIME_DENIED"),
        ({"model_call_performed": True}, "M136_MODEL_CALL_DENIED"),
        ({"memory_write_performed": True}, "M136_MEMORY_WRITE_DENIED"),
        ({"context_injection_performed": True}, "M136_CONTEXT_INJECTION_DENIED"),
        ({"backend_route_added": True}, "M136_BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "M136_CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_added": True}, "M136_DEPENDENCY_DENIED"),
        ({"beta_release_enabled": True}, "M136_BETA_RELEASE_DENIED"),
        ({"production_authority_granted": True}, "M136_PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["dependency-run"]}, "M136_SIDE_EFFECTS_DENIED"),
        ({"reason_codes": []}, "M136_REASON_CODE_REQUIRED"),
        ({"max_risk_class": AutonomyRiskClass.high}, "M136_RISK_CEILING_DENIED"),
    ],
)
def test_m136_decision_rejects_runtime_or_unsafe_mutations(update, reason):
    decision = build_cross_tool_dependency_execution_decision(_request())

    with pytest.raises(ValueError, match=reason):
        validate_cross_tool_dependency_execution_decision(decision.model_copy(update=update))


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("store_raw_tool_payload", "M136_RAW_TOOL_PAYLOAD_DENIED"),
        ("store_raw_prompt", "M136_RAW_PROMPT_DENIED"),
        ("store_raw_provider_payload", "M136_RAW_PROVIDER_PAYLOAD_DENIED"),
        ("store_secret", "M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED"),
        ("dependency_execution_performed", "M136_DEPENDENCY_EXECUTION_DENIED"),
        ("dependency_resolver_started", "M136_DEPENDENCY_RESOLVER_DENIED"),
        ("cross_tool_runtime_started", "M136_CROSS_TOOL_RUNTIME_DENIED"),
        ("parallel_tool_execution_performed", "M136_PARALLEL_TOOL_EXECUTION_DENIED"),
        ("tool_state_handoff_performed", "M136_TOOL_STATE_HANDOFF_DENIED"),
        ("tool_output_routing_performed", "M136_TOOL_OUTPUT_ROUTING_DENIED"),
        ("tool_execution_performed", "M136_TOOL_EXECUTION_DENIED"),
        ("execution_performed", "M136_EXECUTION_DENIED"),
    ],
)
def test_m136_receipt_plan_rejects_raw_storage_and_effects(field, reason):
    decision = build_cross_tool_dependency_execution_decision(_request())
    receipt = decision.receipt_plan.model_copy(update={field: True})

    with pytest.raises(ValueError, match=reason):
        validate_cross_tool_dependency_execution_decision(
            decision.model_copy(update={"receipt_plan": receipt})
        )


def test_m136_receipt_plan_must_match_decision_scope():
    decision = build_cross_tool_dependency_execution_decision(_request())

    with pytest.raises(ValueError, match="M136_RECEIPT_BINDING_MISMATCH"):
        validate_cross_tool_dependency_execution_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"dependency_graph_ref": "dependency-graph:m136:other"}
                    )
                }
            )
        )


def test_m136_rejects_secret_like_safe_summary_and_metadata():
    with pytest.raises(ValueError, match="M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED"):
        _request(safe_dependency_summary="token=secret")

    with pytest.raises(ValueError, match="M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED"):
        CrossToolDependencyExecutionPolicy(metadata={"api_key": "secret"})
