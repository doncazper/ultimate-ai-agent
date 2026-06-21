from ultimate_ai_agent.core.production_readiness import (
    build_m166_green_production_readiness_evidence,
    build_m166_production_release_gate_record,
)


def test_m166_release_gate_remains_exact_bound_for_m167_matrix_scaffold() -> None:
    reviewed_evidence = [
        item.model_copy(
            update={
                "reviewed_live_evidence": True,
                "reviewed_by_ref": f"review-ref:m166:{item.kind.value}",
            }
        )
        for item in build_m166_green_production_readiness_evidence()
    ]

    gate = build_m166_production_release_gate_record(evidence_records=reviewed_evidence)

    assert gate.source_checkpoint_ref == "checkpoint:m165"
    assert gate.exact_scope_bound is True
    assert gate.production_authority_granted is True
    assert gate.production_runtime_authorized is True
    assert gate.production_deployment_authorized is True
    assert gate.redacted_evidence_only is True
    assert gate.rollback_ready is True
    assert gate.backend_route_added is False
    assert gate.control_center_control_added is False
    assert gate.unreviewed_dependency_added is False
    assert gate.raw_prompt_exported is False
    assert gate.raw_response_exported is False
    assert gate.credential_material_exported is False
    assert gate.side_effects_performed == []
