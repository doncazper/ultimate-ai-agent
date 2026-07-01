from __future__ import annotations

import pytest

from ultimate_ai_agent.core.crm import (
    CRM_M1_FIXTURE_CONTRACT_REF,
    CRM_M1_REQUIRED_BLOCKED_REFS,
    CRM_M1_REQUIRED_STATE_LABELS,
    CRM_M1_VERTICAL_ORDER,
    CrmImplementationState,
    CrmWorkspaceKind,
    build_crm_m1_fixture_map,
    validate_crm_m1_fixture_map,
)


def test_crm_m1_fixture_map_builds_prompt_ordered_verticals() -> None:
    fixture_map = validate_crm_m1_fixture_map(build_crm_m1_fixture_map())

    assert fixture_map.contract_ref == CRM_M1_FIXTURE_CONTRACT_REF
    assert [vertical.workspace_kind for vertical in fixture_map.verticals] == (
        CRM_M1_VERTICAL_ORDER
    )
    assert set(fixture_map.state_labels) == set(CRM_M1_REQUIRED_STATE_LABELS)
    assert fixture_map.fixture_only is True
    assert fixture_map.backend_read_model_added is False
    assert fixture_map.backend_route_added is False
    assert fixture_map.control_center_route_added is False
    assert fixture_map.connector_runtime_enabled is False
    assert fixture_map.send_enabled is False
    assert fixture_map.calendar_write_enabled is False
    assert fixture_map.provider_model_call_enabled is False
    assert fixture_map.live_web_enabled is False
    assert fixture_map.browser_runtime_enabled is False
    assert fixture_map.production_authority_enabled is False
    assert set(CRM_M1_REQUIRED_BLOCKED_REFS).issubset(
        fixture_map.blocked_authority_refs
    )
    assert fixture_map.prompts_executed_refs == [
        f"prompt-ref:crm-product-sequence:{index:02d}" for index in range(1, 13)
    ]


def test_crm_m1_verticals_are_screen_ready_but_fixture_only() -> None:
    fixture_map = build_crm_m1_fixture_map()

    for vertical in fixture_map.verticals:
        assert vertical.fixture_only is True
        assert vertical.state == CrmImplementationState.fixture_only
        assert set(vertical.state_labels) == set(CRM_M1_REQUIRED_STATE_LABELS)
        assert vertical.nav_refs
        assert vertical.object_kind_refs
        assert vertical.work_queue_refs
        assert vertical.pipeline_refs
        assert vertical.inspector_section_refs
        assert vertical.pipeline_lanes
        assert vertical.screen_sections
        assert vertical.communications_metadata_refs
        assert vertical.evidence_refs
        assert vertical.memory_provenance_refs
        assert vertical.next_safe_action_refs
        assert set(CRM_M1_REQUIRED_BLOCKED_REFS).issubset(
            vertical.blocked_authority_refs
        )
        assert any(
            section.state == CrmImplementationState.blocked
            for section in vertical.screen_sections
        )
        assert any(
            section.state == CrmImplementationState.proposal_only
            for section in vertical.screen_sections
        )
        assert vertical.backend_route_added is False
        assert vertical.control_center_route_added is False
        assert vertical.contact_import_enabled is False
        assert vertical.silent_identity_merge_enabled is False


def test_crm_m1_vertical_fixture_terms_are_distinct() -> None:
    by_kind = {
        vertical.workspace_kind: " ".join(vertical.object_kind_refs)
        for vertical in build_crm_m1_fixture_map().verticals
    }

    assert "listing" in by_kind[CrmWorkspaceKind.real_estate]
    assert "referral" in by_kind[CrmWorkspaceKind.healthcare]
    assert "renewal" in by_kind[CrmWorkspaceKind.finance_insurance]
    assert "customer-cohort" in by_kind[CrmWorkspaceKind.retail_ecommerce]
    assert "commitment" in by_kind[CrmWorkspaceKind.professional_services]


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("backend_read_model_added", "CRM_M1_BACKEND_READ_MODEL_DENIED"),
        ("backend_route_added", "CRM_M1_BACKEND_ROUTE_DENIED"),
        ("control_center_route_added", "CRM_M1_CONTROL_CENTER_ROUTE_DENIED"),
        ("connector_runtime_enabled", "CRM_M1_CONNECTOR_RUNTIME_DENIED"),
        ("connector_write_enabled", "CRM_M1_CONNECTOR_WRITE_DENIED"),
        ("account_sync_enabled", "CRM_M1_ACCOUNT_SYNC_DENIED"),
        ("send_enabled", "CRM_M1_SEND_DENIED"),
        ("calendar_write_enabled", "CRM_M1_CALENDAR_WRITE_DENIED"),
        ("provider_model_call_enabled", "CRM_M1_PROVIDER_MODEL_DENIED"),
        ("live_web_enabled", "CRM_M1_LIVE_WEB_DENIED"),
        ("browser_runtime_enabled", "CRM_M1_BROWSER_RUNTIME_DENIED"),
        ("hidden_context_injection_enabled", "CRM_M1_CONTEXT_INJECTION_DENIED"),
        ("production_authority_enabled", "CRM_M1_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_crm_m1_fixture_map_rejects_authority_creep(
    field_name: str,
    reason: str,
) -> None:
    payload = build_crm_m1_fixture_map().model_dump(mode="python")
    payload[field_name] = True

    with pytest.raises(ValueError, match=reason):
        validate_crm_m1_fixture_map(payload)


def test_crm_m1_vertical_rejects_authority_creep() -> None:
    payload = build_crm_m1_fixture_map().model_dump(mode="python")
    payload["verticals"][0]["control_center_route_added"] = True

    with pytest.raises(ValueError, match="CRM_M1_CONTROL_CENTER_ROUTE_DENIED"):
        validate_crm_m1_fixture_map(payload)
