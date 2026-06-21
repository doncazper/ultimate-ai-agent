from typing import Any
import pytest

from ultimate_ai_agent.core.production_readiness import (
    REQUIRED_M166_EVIDENCE_KINDS,
    ProductionReadinessEvidenceKind,
    ProductionReadinessEvidenceStatus,
    ProductionReleaseGateStatus,
    build_m166_green_production_readiness_evidence,
    build_m166_production_release_gate_record,
    validate_m166_production_readiness_evidence_record,
    validate_m166_production_release_gate_policy,
    validate_m166_production_release_gate_record,
)


def _reviewed(evidence: Any) -> Any:
    return [
        item.model_copy(
            update={
                "reviewed_live_evidence": True,
                "reviewed_by_ref": f"review-ref:m166:{item.kind.value}",
            }
        )
        for item in evidence
    ]


def test_m166_fixture_evidence_covers_required_production_readiness_lane() -> None:
    evidence = build_m166_green_production_readiness_evidence()

    assert [item.kind.value for item in evidence] == list(REQUIRED_M166_EVIDENCE_KINDS)
    for item in evidence:
        assert item.source_checkpoint_ref == "checkpoint:m165"
        assert item.status == ProductionReadinessEvidenceStatus.passed
        assert item.redacted is True
        assert item.safe_refs_only is True
        assert item.loopback_only is True
        assert item.openwebui_shell_only is True
        assert item.openwebui_is_agent_brain is False
        assert item.raw_prompt_included is False
        assert item.raw_response_included is False
        assert item.secret_included is False
        assert item.blocker_refs == []
        assert item.reviewed_live_evidence is False
        assert item.reviewed_by_ref is None
        assert validate_m166_production_readiness_evidence_record(item) == item


def test_m166_fixture_evidence_cannot_grant_production_authority() -> None:
    evidence = build_m166_green_production_readiness_evidence()

    with pytest.raises(ValueError, match="M166_REVIEWED_LIVE_EVIDENCE_REQUIRED"):
        build_m166_production_release_gate_record(evidence_records=evidence)


def test_m166_release_gate_grants_production_authority_when_all_evidence_is_reviewed() -> None:
    evidence = _reviewed(build_m166_green_production_readiness_evidence())
    gate = build_m166_production_release_gate_record(evidence_records=evidence)

    assert gate.status == ProductionReleaseGateStatus.production_authority_granted
    assert gate.source_checkpoint_ref == "checkpoint:m165"
    assert gate.evidence_refs == [item.evidence_ref for item in evidence]
    assert gate.required_evidence_kinds == [
        ProductionReadinessEvidenceKind(kind)
        for kind in REQUIRED_M166_EVIDENCE_KINDS
    ]
    assert gate.exact_scope_bound is True
    assert gate.all_evidence_passed is True
    assert gate.redacted_evidence_only is True
    assert gate.blockers_cleared is True
    assert gate.rollback_ready is True
    assert gate.audit_required is True
    assert gate.replay_safe is True
    assert gate.production_authority_granted is True
    assert gate.production_runtime_authorized is True
    assert gate.go_live_authorized is True
    assert gate.production_deployment_authorized is True
    assert gate.traffic_routing_authorized is True
    assert gate.side_effects_performed == []
    assert "M166_PRODUCTION_AUTHORITY_GRANTED" in gate.reason_codes
    assert validate_m166_production_release_gate_record(gate) == gate


def test_m166_release_gate_requires_all_six_evidence_categories() -> None:
    evidence = [
        item
        for item in _reviewed(build_m166_green_production_readiness_evidence())
        if item.kind != ProductionReadinessEvidenceKind.load_test
    ]

    with pytest.raises(ValueError, match="M166_ALL_REQUIRED_EVIDENCE_REQUIRED"):
        build_m166_production_release_gate_record(evidence_records=evidence)


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"status": ProductionReadinessEvidenceStatus.failed}, "M166_EVIDENCE_MUST_PASS"),
        ({"blocker_refs": ["blocker-ref:m166:critical"]}, "M166_BLOCKERS_MUST_BE_EMPTY"),
        ({"redacted": False}, "M166_REDACTED_EVIDENCE_REQUIRED"),
        ({"raw_prompt_included": True}, "M166_RAW_PROMPT_DENIED"),
        ({"raw_response_included": True}, "M166_RAW_RESPONSE_DENIED"),
        ({"raw_path_included": True}, "M166_RAW_PATH_DENIED"),
        ({"secret_included": True}, "M166_SECRET_DENIED"),
        ({"openwebui_is_agent_brain": True}, "M166_OPENWEBUI_AUTHORITY_DENIED"),
        ({"unsupported_network_used": True}, "M166_UNSUPPORTED_NETWORK_DENIED"),
        ({"reviewed_live_evidence": True}, "M166_REVIEWED_BY_REF_REQUIRED"),
        (
            {"source_checkpoint_ref": "checkpoint:m164"},
            "M166_SOURCE_CHECKPOINT_M165_REQUIRED",
        ),
    ],
)
def test_m166_evidence_rejects_unsafe_mutations(update: Any, reason: str) -> None:
    evidence = build_m166_green_production_readiness_evidence()[0]

    with pytest.raises(ValueError, match=reason):
        validate_m166_production_readiness_evidence_record(
            evidence.model_copy(update=update)
        )


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"production_authority_granted": False}, "M166_PRODUCTION_AUTHORITY_GRANT_REQUIRED"),
        ({"production_runtime_authorized": False}, "M166_PRODUCTION_RUNTIME_AUTH_REQUIRED"),
        ({"go_live_authorized": False}, "M166_GO_LIVE_AUTH_REQUIRED"),
        ({"rollback_ready": False}, "M166_ROLLBACK_REQUIRED"),
        ({"raw_prompt_exported": True}, "M166_RAW_PROMPT_DENIED"),
        ({"raw_response_exported": True}, "M166_RAW_RESPONSE_DENIED"),
        ({"credential_material_exported": True}, "M166_CREDENTIAL_MATERIAL_DENIED"),
        ({"backend_route_added": True}, "M166_BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "M166_CONTROL_CENTER_CONTROL_DENIED"),
        ({"side_effects_performed": ["deploy"]}, "M166_RELEASE_GATE_SIDE_EFFECTS_DENIED"),
    ],
)
def test_m166_release_gate_rejects_unsafe_mutations(update: Any, reason: str) -> None:
    gate = build_m166_production_release_gate_record(
        evidence_records=_reviewed(build_m166_green_production_readiness_evidence())
    )

    with pytest.raises(ValueError, match=reason):
        validate_m166_production_release_gate_record(gate.model_copy(update=update))


def test_m166_policy_requires_exact_evidence_and_grant_authority() -> None:
    policy = validate_m166_production_release_gate_policy(
        {
            "production_authority_grant_allowed": True,
            "production_runtime_authorization_allowed": True,
            "go_live_authorization_allowed": True,
        }
    )

    assert policy.source_checkpoint_ref == "checkpoint:m165"
    assert [kind.value for kind in policy.required_evidence_kinds] == list(
        REQUIRED_M166_EVIDENCE_KINDS
    )
