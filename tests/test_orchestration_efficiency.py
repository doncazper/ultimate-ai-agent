import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tests.m7_helpers import classification, cloud_profile, local_profile, policy, route_request
from ultimate_ai_agent.core.context_budget import ContextBudget
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue
from ultimate_ai_agent.core.model_router import (
    ModelRouteCostMode,
)
from ultimate_ai_agent.core.orchestration_efficiency import (
    CacheabilityPlan,
    OrchestrationEfficiencyPlanner,
    OrchestrationEfficiencyPolicy,
    OrchestrationPreviewStatus,
    RouteOptimizationWeights,
)


def cache_plan(**overrides) -> CacheabilityPlan:
    data = {
        "plan_ref": "cache-plan:route_req_1:stable",
        "run_id": "run_m7",
        "model_profile_id": None,
        "runtime_optimization_profile_ref": "runtime-optimization:local",
        "prompt_bundle_hash": "sha256:prompt",
        "tool_schema_bundle_hash": "sha256:tools",
        "tool_order_hash": "sha256:tool-order",
        "context_pack_hash": "sha256:context",
        "data_classification": "project_private",
        "cache_eligible": True,
        "predicted_prefix_reuse_tokens": 800,
        "predicted_cache_write_tokens": 1000,
        "predicted_cache_hit_tokens": 700,
    }
    data.update(overrides)
    return CacheabilityPlan(**data)


def efficiency_policy(**overrides) -> OrchestrationEfficiencyPolicy:
    data = {
        "policy_id": "orch-efficiency-policy:test",
        "cost_mode": ModelRouteCostMode.balanced,
    }
    data.update(overrides)
    return OrchestrationEfficiencyPolicy(**data)


def test_efficiency_planner_prefers_lower_weighted_cost_and_latency() -> None:
    slow_expensive = local_profile(
        profile_id="slow_expensive",
        cost_per_1k_input_tokens=0.04,
        cost_per_1k_output_tokens=0.04,
    ).model_copy(update={"time_to_first_token_ms": 900})
    fast_cheap = local_profile(
        profile_id="fast_cheap",
        cost_per_1k_input_tokens=0.001,
        cost_per_1k_output_tokens=0.001,
    ).model_copy(update={"time_to_first_token_ms": 80})
    request = route_request(
        profiles=[slow_expensive, fast_cheap],
        routing_policy=policy(allow_paid=True, fallback_allowed=True),
    )

    decision = OrchestrationEfficiencyPlanner().preview(
        request,
        efficiency_policy(fallback_allowed=True),
        cache_plan(),
    )

    assert decision.status == OrchestrationPreviewStatus.selected
    assert decision.selected_profile_id == "fast_cheap"
    assert "CHEAPER_ROUTE_SELECTED" in decision.reason_codes
    assert "LATENCY_WEIGHT_APPLIED" in decision.reason_codes
    assert "FALLBACK_PLANNED" in decision.reason_codes
    assert decision.fallback_plan.fallback_profile_ids == ["slow_expensive"]
    assert decision.no_effect is True


def test_hard_privacy_filter_beats_efficiency_scoring() -> None:
    request = route_request(
        profiles=[cloud_profile(profile_id="cheap_cloud")],
        data_classification=classification(ClassificationValue.credential_secret),
        routing_policy=policy(allow_cloud=True, allow_paid=True),
    )

    decision = OrchestrationEfficiencyPlanner().preview(
        request,
        efficiency_policy(weights=RouteOptimizationWeights(cost_weight=100, latency_weight=100)),
        cache_plan(cache_eligible=False, invalidation_reason_codes=["CACHE_DISABLED_FOR_SECRET"]),
    )

    assert decision.status == OrchestrationPreviewStatus.privacy_blocked
    assert decision.selected_profile_id is None
    assert "CREDENTIAL_SECRET_NEVER_TO_MODEL" in decision.reason_codes


def test_context_overflow_fails_closed_before_scoring() -> None:
    request = route_request(
        profiles=[local_profile()],
        context_budget=ContextBudget(
            model_context_limit=4096,
            system_prompt_tokens=3000,
            completion_reserve_tokens=900,
            safety_margin_tokens=196,
        ),
        routing_policy=policy(),
    )

    decision = OrchestrationEfficiencyPlanner().preview(
        request,
        efficiency_policy(),
        cache_plan(cache_eligible=False, invalidation_reason_codes=["TRIM_CONTEXT_REQUIRED"]),
    )

    assert decision.status == OrchestrationPreviewStatus.context_too_small
    assert "CONTEXT_BUDGET_EXHAUSTED" in decision.reason_codes
    assert decision.metric_summary.available_history_tokens == 0


def test_unknown_paid_cloud_cost_requires_approval() -> None:
    request = route_request(
        profiles=[
            cloud_profile(
                profile_id="unknown_cost_cloud",
                cost_per_1k_input_tokens=None,
                cost_per_1k_output_tokens=0.02,
            )
        ],
        routing_policy=policy(allow_cloud=True, allow_paid=True),
    )

    decision = OrchestrationEfficiencyPlanner().preview(
        request,
        efficiency_policy(),
        cache_plan(cache_eligible=False),
    )

    assert decision.status == OrchestrationPreviewStatus.approval_required
    assert "UNKNOWN_PAID_COST_REQUIRES_APPROVAL" in decision.reason_codes
    assert decision.metric_summary.unknown_paid_cost_count == 1


def test_cheap_mode_rejects_premium_profiles() -> None:
    premium = local_profile(profile_id="premium_local")
    request = route_request(profiles=[premium], routing_policy=policy())

    decision = OrchestrationEfficiencyPlanner().preview(
        request,
        efficiency_policy(
            cost_mode=ModelRouteCostMode.cheap,
            premium_profile_refs=["premium_local"],
        ),
        cache_plan(cache_eligible=False),
    )

    assert decision.status == OrchestrationPreviewStatus.denied
    assert "PREMIUM_PROFILE_DISALLOWED_IN_CHEAP_MODE" in decision.reason_codes


def test_premium_mode_logs_premium_route_justification() -> None:
    premium = local_profile(profile_id="premium_local")
    request = route_request(profiles=[premium], routing_policy=policy())

    decision = OrchestrationEfficiencyPlanner().preview(
        request,
        efficiency_policy(
            cost_mode=ModelRouteCostMode.premium,
            premium_profile_refs=["premium_local"],
        ),
        cache_plan(),
    )

    assert decision.status == OrchestrationPreviewStatus.selected
    assert "PREMIUM_ROUTE_JUSTIFIED" in decision.reason_codes


def test_critical_mode_requires_approval_and_plans_verifier() -> None:
    request = route_request(profiles=[local_profile()], routing_policy=policy())

    denied = OrchestrationEfficiencyPlanner().preview(
        request,
        efficiency_policy(cost_mode=ModelRouteCostMode.critical),
        cache_plan(cache_eligible=False),
    )

    assert denied.status == OrchestrationPreviewStatus.approval_required
    assert "CRITICAL_APPROVAL_REQUIRED" in denied.reason_codes
    assert denied.verification_required is True

    approved_request = route_request(
        profiles=[local_profile()],
        routing_policy=policy(),
        approval_ref="approval:critical:local-review",
    )
    selected = OrchestrationEfficiencyPlanner().preview(
        approved_request,
        efficiency_policy(cost_mode=ModelRouteCostMode.critical),
        cache_plan(cache_eligible=False),
    )

    assert selected.status == OrchestrationPreviewStatus.selected
    assert selected.verification_required is True
    assert selected.verifier_plan_ref == "verifier-plan:route_req_1:critical"
    assert "CRITICAL_VERIFIER_REQUIRED" in selected.reason_codes


def test_cache_plan_invalidation_and_ledger_metadata_are_redacted() -> None:
    request = route_request(profiles=[local_profile()], routing_policy=policy())
    decision = OrchestrationEfficiencyPlanner().preview(
        request,
        efficiency_policy(),
        cache_plan(invalidation_reason_codes=["PROMPT_BUNDLE_CHANGED"]),
    )

    metadata = decision.to_redacted_ledger_metadata()

    assert metadata["cache_plan_ref"] == "cache-plan:route_req_1:stable"
    assert "PROMPT_BUNDLE_CHANGED" in decision.reason_codes
    assert "Summarize the task" not in json.dumps(metadata)
    assert "provider payload" not in json.dumps(metadata).lower()
    assert metadata["no_effect"] is True


def test_orchestration_efficiency_contracts_reject_unknown_fields_and_secrets() -> None:
    with pytest.raises(ValidationError):
        OrchestrationEfficiencyPolicy(policy_id="policy", cost_mode="balanced", surprise=True)

    with pytest.raises(ValueError, match="secret-like"):
        CacheabilityPlan(
            plan_ref="cache-plan:bad",
            run_id="run_bad",
            data_classification="public",
            cache_eligible=False,
            metadata={"note": "api_key='abcdefabcdefabcdef'"},
        )


def test_orchestration_efficiency_schemas_are_closed_contracts() -> None:
    for schema_name in [
        "orchestration_efficiency_policy.schema.json",
        "cacheability_plan.schema.json",
        "orchestration_preview_decision.schema.json",
    ]:
        schema = json.loads((Path("docs/schemas") / schema_name).read_text(encoding="utf-8"))
        assert schema["additionalProperties"] is False


def test_orchestration_efficiency_source_has_no_runtime_imports() -> None:
    forbidden_modules = {
        "openai",
        "anthropic",
        "google.generativeai",
        "ollama",
        "requests",
        "httpx",
        "urllib.request",
        "subprocess",
        "socket",
    }

    for path in (Path("src") / "ultimate_ai_agent" / "core" / "orchestration_efficiency").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_modules
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module not in forbidden_modules
