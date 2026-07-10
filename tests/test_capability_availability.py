from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from scripts.dev import uaa_runtime
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.capabilities.approval import (
    CapabilityApprovalGrant,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityCostClass,
    CapabilityKind,
    CoordinationMode,
    PolicyDecisionStatus,
    RiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityManifest,
    PolicyDecision,
    SafetyPolicy,
    TaskEnvelope,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.capability_availability import (
    AuthorityPosture,
    CapabilityAvailabilitySnapshot,
    CapabilityInvocationRequest,
    CatalogStatus,
    CompatibilityStatus,
    ConfigurationStatus,
    CostPosture,
    DerivedRuntimeReadinessStatus,
    FreshnessStatus,
    HealthStatus,
    IdempotencyPosture,
    InvocationDecisionOutcome,
    ResourceBudgetStatus,
    SafeDisableStatus,
    build_capability_availability_read_model,
    build_capability_availability_snapshot,
    derive_runtime_readiness,
    evaluate_capability_invocation,
    snapshot_from_capability_manifest,
    snapshot_from_extension_catalog_entry,
    snapshot_from_provider_manifest,
)
from ultimate_ai_agent.core.costs import BudgetStatus, CostDecision
from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
)
from ultimate_ai_agent.core.providers import (
    GovernedProviderInvocationReadiness,
    ProviderAuthRequirement,
    ProviderCapability,
    ProviderCostClass,
    ProviderDomain,
    ProviderManifest,
    ProviderStatus,
)


FIXED_TIME = datetime(2026, 7, 10, 16, 0, tzinfo=timezone.utc)
client = TestClient(app)


def _snapshot(**overrides: Any) -> CapabilityAvailabilitySnapshot:
    values: dict[str, Any] = {
        "snapshot_ref": "capability-availability-ref:test-capability",
        "capability_ref": "capability-ref:test-capability",
        "catalog_status": CatalogStatus.supported,
        "compatibility_status": CompatibilityStatus.supported,
        "configuration_status": ConfigurationStatus.configured,
        "health_status": HealthStatus.healthy,
        "authority_posture": AuthorityPosture.eligible_for_policy_evaluation,
        "resource_status": ResourceBudgetStatus.available,
        "cost_posture": CostPosture.not_metered,
        "safe_disable_status": SafeDisableStatus.inactive,
        "checked_at": FIXED_TIME,
        "freshness_status": FreshnessStatus.current,
        "source_ref": "source-ref:test-capability",
        "safe_summary": "Deterministic test capability readiness metadata.",
    }
    values.update(overrides)
    return build_capability_availability_snapshot(**values)


def _request(**overrides: Any) -> CapabilityInvocationRequest:
    values: dict[str, Any] = {
        "request_ref": "capability-invocation-request-ref:test-capability",
        "snapshot_ref": "capability-availability-ref:test-capability",
        "capability_ref": "capability-ref:test-capability",
        "idempotency_posture": IdempotencyPosture.not_required,
        "expected_execution_receipt_ref": "receipt-ref:test-capability:future",
    }
    values.update(overrides)
    return CapabilityInvocationRequest(**values)


def _policy_decision(
    *,
    status: PolicyDecisionStatus = PolicyDecisionStatus.allowed,
    allowed: bool = True,
    requires_approval: bool = False,
) -> PolicyDecision:
    return PolicyDecision(
        status=status,
        allowed=allowed,
        requires_approval=requires_approval,
        reason_codes=["CAPABILITY_EXECUTION_ALLOWED"],
        safe_message="Exact capability policy decision for test.",
        capability_id="capability-ref:test-capability",
    )


def _manifest(
    capability_id: str = "capability-ref:test-capability",
    *,
    approval_required: bool = False,
) -> CapabilityManifest:
    return CapabilityManifest(
        id=capability_id,
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name="Test Capability",
        description="Deterministic capability contract for availability tests.",
        examples=["Inspect safe metadata."],
        anti_examples=["Do not infer execution authority."],
        input_schema={"type": "object", "additionalProperties": False},
        output_schema={"type": "object", "additionalProperties": False},
        input_modes=["safe_refs"],
        output_modes=["safe_summary"],
        side_effects=SideEffectLevel.none,
        risk_level=RiskLevel.high if approval_required else RiskLevel.low,
        approval_required=approval_required or None,
        deterministic=True,
        estimated_cost_class=CapabilityCostClass.none,
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        safety=SafetyPolicy(approval_required=approval_required),
    )


def test_unknown_compatibility_fails_closed() -> None:
    snapshot = _snapshot(compatibility_status=CompatibilityStatus.unknown)

    assert snapshot.runtime_readiness_status == DerivedRuntimeReadinessStatus.unknown
    assert "COMPATIBILITY_STATUS_UNKNOWN" in snapshot.blocker_codes


def test_unsupported_version_fails_closed() -> None:
    snapshot = _snapshot(compatibility_status=CompatibilityStatus.unsupported)

    assert snapshot.runtime_readiness_status == DerivedRuntimeReadinessStatus.unavailable
    assert "COMPATIBILITY_UNSUPPORTED" in snapshot.blocker_codes


def test_not_configured_fails_closed() -> None:
    snapshot = _snapshot(configuration_status=ConfigurationStatus.not_configured)

    assert snapshot.runtime_readiness_status == DerivedRuntimeReadinessStatus.unavailable
    assert "NOT_CONFIGURED" in snapshot.blocker_codes


@pytest.mark.parametrize("health_status", [HealthStatus.stale, HealthStatus.unhealthy])
def test_stale_and_unhealthy_health_fail_closed(
    health_status: HealthStatus,
) -> None:
    snapshot = _snapshot(health_status=health_status)

    assert snapshot.runtime_readiness_status == DerivedRuntimeReadinessStatus.unavailable
    assert any(code.startswith("HEALTH_") for code in snapshot.blocker_codes)


def test_degraded_health_requires_exact_future_policy() -> None:
    snapshot = _snapshot(health_status=HealthStatus.degraded)

    assert snapshot.runtime_readiness_status == DerivedRuntimeReadinessStatus.unavailable
    assert "HEALTH_DEGRADED_NOT_PERMITTED" in snapshot.blocker_codes


def test_unknown_cost_posture_fails_closed() -> None:
    snapshot = _snapshot(cost_posture=CostPosture.unknown)

    assert snapshot.runtime_readiness_status == DerivedRuntimeReadinessStatus.unknown
    assert "COST_POSTURE_UNKNOWN" in snapshot.blocker_codes


def test_safe_disable_overrides_positive_readiness() -> None:
    snapshot = _snapshot(safe_disable_status=SafeDisableStatus.active)

    assert snapshot.runtime_readiness_status == DerivedRuntimeReadinessStatus.blocked
    assert snapshot.blocker_codes[0] == "SAFE_DISABLE_ACTIVE"


def test_healthy_does_not_grant_authority() -> None:
    snapshot = _snapshot(authority_posture=AuthorityPosture.blocked)
    environmental = derive_runtime_readiness(
        catalog_status=snapshot.catalog_status,
        compatibility_status=snapshot.compatibility_status,
        configuration_status=snapshot.configuration_status,
        health_status=snapshot.health_status,
        resource_status=snapshot.resource_status,
        cost_posture=snapshot.cost_posture,
        safe_disable_status=snapshot.safe_disable_status,
        freshness_status=snapshot.freshness_status,
        checked_at=snapshot.checked_at,
        expires_at=snapshot.expires_at,
    )

    assert environmental.status == DerivedRuntimeReadinessStatus.ready
    decision = evaluate_capability_invocation(
        request=_request(),
        snapshot=snapshot,
        policy_decision=_policy_decision(),
        evaluated_at=FIXED_TIME,
    )
    assert decision.outcome == InvocationDecisionOutcome.blocked
    assert "AVAILABILITY_AUTHORITY_POSTURE_BLOCKED" in decision.blocker_codes


def test_approval_identifier_alone_does_not_grant_authority() -> None:
    snapshot = _snapshot(authority_posture=AuthorityPosture.approval_required)
    request = _request(approval_ref="approval-ref:test-capability")

    decision = evaluate_capability_invocation(
        request=request,
        snapshot=snapshot,
        policy_decision=_policy_decision(),
        evaluated_at=FIXED_TIME,
    )

    assert decision.outcome == InvocationDecisionOutcome.approval_required
    assert "EXACT_LOCAL_APPROVAL_VALIDATION_REQUIRED" in decision.reason_codes


def test_exact_local_approval_validation_can_satisfy_request_gate() -> None:
    manifest = _manifest(approval_required=True)
    task = TaskEnvelope(
        task_id="task-ref:test-capability",
        user_request="Inspect safe capability metadata.",
        objective="Validate one exact request gate.",
        context={"approval_ref": "approval-ref:test-capability"},
    )
    approval_authority = LocalApprovalAuthority(
        [
            CapabilityApprovalGrant(
                approval_ref="approval-ref:test-capability",
                capability_id=manifest.id,
                task_id=task.task_id,
                granted_by="operator-ref:test",
            )
        ]
    )
    context = {"approval_ref": "approval-ref:test-capability"}
    approval_decision = approval_authority.validate_approval(manifest, task, context)
    policy_decision = PolicyEngine(
        approval_authority=approval_authority
    ).can_execute(manifest, task, context)

    decision = evaluate_capability_invocation(
        request=_request(
            task_ref=task.task_id,
            approval_ref="approval-ref:test-capability",
        ),
        snapshot=_snapshot(authority_posture=AuthorityPosture.approval_required),
        policy_decision=policy_decision,
        local_approval_decision=approval_decision,
        evaluated_at=FIXED_TIME,
    )

    assert approval_decision.reason_codes == ["APPROVAL_GRANT_VALID"]
    assert decision.outcome == InvocationDecisionOutcome.allow
    assert decision.cache_posture == "not_cacheable"


def test_exact_authority_lease_scope_is_required_when_declared() -> None:
    snapshot = _snapshot(authority_posture=AuthorityPosture.lease_required)
    missing = evaluate_capability_invocation(
        request=_request(),
        snapshot=snapshot,
        policy_decision=_policy_decision(),
        evaluated_at=FIXED_TIME,
    )
    lease = AuthorityLease(
        lease_ref="authority-lease-ref:test-capability",
        mode=TrustMode.read_only,
        domains={AuthorityDomain.workspace: [AuthorityCapability.read]},
        issued_at=FIXED_TIME,
        expires_at=FIXED_TIME + timedelta(hours=1),
        safe_summary="Allow one exact read capability for test.",
    )
    authority_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:test-capability",
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.read,
            capability_ref="capability-ref:test-capability",
            safe_summary="Evaluate one exact read capability for test.",
        ),
        [lease],
        now=FIXED_TIME,
    )
    matched = evaluate_capability_invocation(
        request=_request(),
        snapshot=snapshot,
        policy_decision=_policy_decision(),
        authority_decision=authority_decision,
        evaluated_at=FIXED_TIME,
    )

    assert missing.outcome == InvocationDecisionOutcome.lease_required
    assert authority_decision.outcome == "allow"
    assert matched.outcome == InvocationDecisionOutcome.allow


def test_missing_budget_blocks_metered_request() -> None:
    snapshot = _snapshot(cost_posture=CostPosture.metered)
    request = _request(idempotency_posture=IdempotencyPosture.validated)
    allowed_request = request.model_copy(
        update={
            "budget_decision_ref": "budget-decision-ref:cost-decision-test-capability"
        }
    )

    missing = evaluate_capability_invocation(
        request=request,
        snapshot=snapshot,
        policy_decision=_policy_decision(),
        evaluated_at=FIXED_TIME,
    )
    allowed = evaluate_capability_invocation(
        request=allowed_request,
        snapshot=snapshot,
        policy_decision=_policy_decision(),
        budget_decision=CostDecision(
            decision_id="cost-decision-test-capability",
            allowed=True,
            status=BudgetStatus.allowed,
            reason_codes=["WITHIN_BUDGET"],
            safe_message="Exact request is within its budget.",
        ),
        evaluated_at=FIXED_TIME,
    )

    assert missing.outcome == InvocationDecisionOutcome.blocked
    assert "REQUEST_BUDGET_DECISION_REQUIRED" in missing.blocker_codes
    assert allowed.outcome == InvocationDecisionOutcome.allow


def test_budget_decision_ref_must_match_exact_request() -> None:
    decision = evaluate_capability_invocation(
        request=_request(
            budget_decision_ref="budget-decision-ref:different-request",
        ),
        snapshot=_snapshot(cost_posture=CostPosture.metered),
        policy_decision=_policy_decision(),
        budget_decision=CostDecision(
            decision_id="cost-decision-test-capability",
            allowed=True,
            status=BudgetStatus.allowed,
            reason_codes=["WITHIN_BUDGET"],
            safe_message="Exact request is within its budget.",
        ),
        evaluated_at=FIXED_TIME,
    )

    assert decision.outcome == InvocationDecisionOutcome.blocked
    assert "REQUEST_BUDGET_DECISION_REF_MISMATCH" in decision.blocker_codes


def test_policy_and_approval_task_scope_must_match_exact_request() -> None:
    unscoped = _policy_decision()
    decision = evaluate_capability_invocation(
        request=_request(
            task_ref="task-ref:test-capability",
            approval_ref="approval-ref:test-capability",
        ),
        snapshot=_snapshot(authority_posture=AuthorityPosture.approval_required),
        policy_decision=unscoped,
        local_approval_decision=unscoped.model_copy(
            update={"reason_codes": ["APPROVAL_GRANT_VALID"]}
        ),
        evaluated_at=FIXED_TIME,
    )

    assert decision.outcome == InvocationDecisionOutcome.blocked
    assert "POLICY_TASK_SCOPE_MISMATCH" in decision.blocker_codes
    assert "EXACT_LOCAL_APPROVAL_VALIDATION_REQUIRED" in decision.reason_codes


def test_inspectable_extension_catalog_entry_is_not_callable() -> None:
    entry = build_default_inspectable_extension_catalog().entries[0]
    snapshot = snapshot_from_extension_catalog_entry(
        entry,
        checked_at=FIXED_TIME,
        safe_disable_status=SafeDisableStatus.inactive,
    )

    assert snapshot.catalog_status == CatalogStatus.supported
    assert snapshot.configuration_status == ConfigurationStatus.not_configured
    assert snapshot.authority_posture == AuthorityPosture.blocked
    assert "EXTENSION_CATALOG_ENTRY_NOT_CALLABLE" in snapshot.blocker_codes


def test_runtime_ready_snapshot_still_requires_separate_request_decision() -> None:
    snapshot = _snapshot()
    payload = snapshot.model_dump(mode="json")

    assert snapshot.runtime_readiness_status == DerivedRuntimeReadinessStatus.ready
    assert "outcome" not in payload
    assert not any(key in payload for key in ("authorized", "callable"))

    decision = evaluate_capability_invocation(
        request=_request(),
        snapshot=snapshot,
        policy_decision=_policy_decision(),
        evaluated_at=FIXED_TIME,
    )
    assert decision.outcome == InvocationDecisionOutcome.allow
    assert decision.expected_execution_receipt_ref == "receipt-ref:test-capability:future"


def test_capability_and_provider_adapters_preserve_unknown_and_blocked_states() -> None:
    capability_snapshot = snapshot_from_capability_manifest(
        _manifest(), checked_at=FIXED_TIME
    )
    provider_snapshot = snapshot_from_provider_manifest(
        ProviderManifest(
            provider_id="provider-contract-test",
            display_name="Provider Contract Test",
            domain=ProviderDomain.generic,
            status=ProviderStatus.blocked,
            auth_requirement=ProviderAuthRequirement.none,
            cost_class=ProviderCostClass.paid,
            capabilities=[ProviderCapability.generic_query],
            owner="core",
            source="tests",
            version="1.0.0",
        ),
        readiness=GovernedProviderInvocationReadiness(),
        checked_at=FIXED_TIME,
    )

    assert capability_snapshot.compatibility_status == CompatibilityStatus.unknown
    assert capability_snapshot.configuration_status == ConfigurationStatus.unknown
    assert capability_snapshot.health_status == HealthStatus.unknown
    assert capability_snapshot.runtime_readiness_status == DerivedRuntimeReadinessStatus.unknown
    assert provider_snapshot.authority_posture == AuthorityPosture.blocked
    assert provider_snapshot.resource_status == ResourceBudgetStatus.unknown
    assert "PROVIDER_INVOCATION_NOT_SCOPED" in provider_snapshot.blocker_codes


@pytest.mark.parametrize(
    "unsafe_summary",
    [
        "api_key" + "=abcdefghijklmnop",
        "Unsafe local path /" + "Users/example/private.",
        "Raw username " + "@" + "example-user is not allowed.",
        "Raw host node" + ".internal is not allowed.",
        "OPENAI_VALUE" + "=raw-environment-value",
    ],
)
def test_snapshot_rejects_unsafe_summary_payloads(unsafe_summary: str) -> None:
    with pytest.raises((ValidationError, ValueError)):
        _snapshot(safe_summary=unsafe_summary)


def test_snapshot_rejects_unknown_raw_payload_fields() -> None:
    payload = _snapshot().model_dump(mode="python")
    payload["raw_provider_payload"] = {"response": "unsafe"}

    with pytest.raises(ValidationError, match="extra_forbidden"):
        CapabilityAvailabilitySnapshot.model_validate(payload)


def test_backend_read_model_contains_representative_safe_states() -> None:
    read_model = build_capability_availability_read_model(checked_at=FIXED_TIME)
    payload = read_model.model_dump(mode="json")
    by_ref = {item["capability_ref"]: item for item in payload["snapshots"]}

    assert payload["truth_owner"] == "python_core"
    assert payload["request_scoped_evaluation_required"] is True
    assert payload["availability_does_not_grant_execution"] is True
    assert payload["execution_evidence_posture"] == "separate_receipt_contract"
    assert payload["snapshot_count"] == len(payload["snapshots"]) >= 6
    assert by_ref["capability-ref:manual-local-loopback-smoke-validation"][
        "runtime_readiness_status"
    ] == "unavailable"
    assert by_ref["capability-ref:simulated-model-runtime"][
        "authority_posture"
    ] == "blocked"
    assert by_ref["capability-ref:governed-runtime-command"][
        "safe_disable_status"
    ] == "active"
    assert by_ref["capability-ref:api-contract-metadata"][
        "runtime_readiness_status"
    ] == "ready"
    assert all(item["reason_codes"] for item in payload["snapshots"])
    assert all(item["source_ref"] for item in payload["snapshots"])
    serialized = json.dumps(payload)
    assert "/" + "Users/" not in serialized
    assert "api_key" + "=" not in serialized.lower()


def test_cli_and_api_expose_same_backend_owned_truth(
    capsys: pytest.CaptureFixture[str],
) -> None:
    response = client.get("/control-center/capabilities/availability")
    assert response.status_code == 200
    api_payload = response.json()
    assert api_payload["operation"] == "control_center_capabilities_availability"

    assert uaa_runtime.main(["capability-availability", "--json"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    api_model = api_payload["data"]
    cli_model = cli_payload["capability_availability"]

    def states(model: dict[str, Any]) -> dict[str, tuple[str, str]]:
        return {
            item["capability_ref"]: (
                item["runtime_readiness_status"],
                item["authority_posture"],
            )
            for item in model["snapshots"]
        }

    assert api_model["schema_version"] == cli_model["schema_version"]
    assert api_model["source_ref"] == cli_model["source_ref"]
    assert states(api_model) == states(cli_model)


def test_cli_primary_output_is_readable(capsys: pytest.CaptureFixture[str]) -> None:
    assert uaa_runtime.main(["capability-availability"]) == 0
    output = capsys.readouterr().out

    assert "Capability availability truth model" in output
    assert "States:" in output
    assert "Availability never grants execution" in output
    assert not output.lstrip().startswith("{")


def test_api_manifest_keeps_availability_route_read_only_and_static() -> None:
    manifest = build_api_manifest(app).model_dump(mode="json")
    route = next(
        item
        for item in manifest["routes"]
        if item["path"] == "/control-center/capabilities/availability"
    )

    assert route["method"] == "GET"
    assert route["operation_id"] == "get_control_center_capabilities_availability"
    assert route["route_classification"] == "local_readonly"
    assert route["side_effect_class"] == "validation_only"
    assert "control_center_capability_availability_read_model" in manifest[
        "capabilities_declared"
    ]
    assert "capability_availability_global_authorization" in manifest[
        "capabilities_blocked"
    ]
