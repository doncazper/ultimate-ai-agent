from ultimate_ai_agent.core.gate import (
    FoundationGateCategory,
    FoundationGateStatus,
    default_foundation_gate_criteria,
)


def test_default_foundation_gate_criteria_cover_m6_acceptance_surface():
    criteria = default_foundation_gate_criteria()
    by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert {
        "versioning_consistent",
        "release_docs_present",
        "foundation_modules_present",
        "blocked_modules_absent",
        "forbidden_runtime_integrations_absent",
        "shell_execution_absent",
        "broad_filesystem_scanning_absent",
        "secret_hygiene_clean",
        "tool_broker_blocks_advanced_adapters",
        "truth_evidence_contracts_valid",
        "memory_file_contracts_valid",
        "m5_shadow_replay_passes",
        "m7_modules_present",
        "model_router_decision_only",
        "cost_governor_blocks_over_budget",
        "m7_arbitrary_approval_ref_rejected",
        "m7_context_budget_exhaustion_blocks_route",
        "m7_soft_budget_warning_allows_route",
        "m7_hard_budget_denies_route",
        "m7_cost_warnings_visible_in_route_decision",
        "open_design_governance_docs_present",
        "openwebui_ccc_strategy_docs_present",
        "roadmap_milestone_charters_current",
        "documentation_integrity_current",
        "codex_plugin_governance_docs_present",
    }.issubset(by_id)
    assert all(criterion.required for criterion in criteria)
    assert FoundationGateCategory.blocked_modules in {criterion.category for criterion in criteria}
    assert FoundationGateCategory.rollback in {criterion.category for criterion in criteria}
    assert all(criterion.pass_condition for criterion in criteria)


def test_foundation_gate_criterion_rejects_unknown_fields():
    criterion = default_foundation_gate_criteria()[0]
    payload = criterion.model_dump()
    payload["unexpected"] = "not allowed"

    try:
        type(criterion)(**payload)
    except Exception as exc:
        assert "extra" in str(exc).lower()
    else:
        raise AssertionError("FoundationGateCriterion accepted an unknown field")


def test_foundation_gate_status_values_are_public_contracts():
    assert {status.value for status in FoundationGateStatus} == {
        "passed",
        "failed",
        "warning",
        "skipped",
        "blocked",
    }
