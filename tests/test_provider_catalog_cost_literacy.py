from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.providers import (
    ProviderAuthorityPosture,
    ProviderCatalog,
    ProviderCostProfile,
    ProviderKeyInstruction,
    ProviderSetupCard,
    ProviderSourceRef,
    build_provider_setup_guide_catalog,
)


client = TestClient(app)


def test_provider_setup_guide_catalog_is_complete_static_and_guidance_only() -> None:
    catalog = build_provider_setup_guide_catalog()

    assert isinstance(catalog, ProviderCatalog)
    assert catalog.route_ref == "GET /control-center/providers/setup-guide"
    assert catalog.status == "read_only_guidance"
    assert catalog.source_posture == "reviewed_static_timestamped_metadata"
    assert len(catalog.provider_cards) >= 30
    assert catalog.no_credential_input is True
    assert catalog.no_raw_key_storage is True
    assert catalog.no_provider_validation is True
    assert catalog.no_provider_sdk_calls is True
    assert catalog.no_model_invocation is True
    assert catalog.no_runtime_web_fetching is True
    assert catalog.no_automatic_pricing_fetch is True
    assert catalog.no_provider_output_authority is True
    assert catalog.catalog_visibility_grants_authority is False

    for card in catalog.provider_cards:
        assert isinstance(card, ProviderSetupCard)
        assert card.authority_state == "guidance_only"
        assert card.pricing_may_change is True
        assert card.not_billing_authority is True
        assert card.guidance_only is True
        assert card.credential_input_enabled is False
        assert card.raw_key_storage_enabled is False
        assert card.credential_validation_enabled is False
        assert card.provider_sdk_call_enabled is False
        assert card.model_invocation_enabled is False
        assert card.automatic_pricing_refresh_enabled is False
        assert card.provider_output_authority_enabled is False
        assert card.setup_link.startswith("https://")
        assert card.api_docs_link.startswith("https://")
        assert card.pricing_link.startswith("https://")
        assert card.key_instruction.env_var_styles == card.env_var_styles
        assert card.cost_profile.token_cost_notes == card.token_cost_notes
        assert {source.source_kind for source in card.source_refs} >= {
            "setup",
            "api_docs",
            "pricing",
        }
        assert all(source.runtime_fetch_performed is False for source in card.source_refs)
        assert all(source.provider_call_performed is False for source in card.source_refs)


def test_provider_setup_guide_budget_posture_binds_unknown_paid_cost_to_approval() -> None:
    budget = build_provider_setup_guide_catalog().budget_posture

    assert budget.unknown_paid_cost_requires_explicit_approval is True
    assert budget.estimated_cost_above_budget_blocks_use is True
    assert budget.provider_model_refs_required is True
    assert budget.cost_estimate_ref_required is True
    assert budget.budget_decision_ref_required is True
    assert budget.receipt_ref_required is True
    assert budget.max_approved_usd_required is True
    assert budget.cost_governor_binding_required is True
    assert budget.provider_use_authority_granted is False


@pytest.mark.parametrize(
    ("factory", "kwargs", "reason"),
    [
        (
            ProviderSourceRef,
            {
                "source_ref": "provider-source:test:setup",
                "source_kind": "setup",
                "label": "Provider setup",
                "url": "http://example.com/setup",
            },
            "HTTPS_URL_REQUIRED",
        ),
        (
            ProviderKeyInstruction,
            {
                "instruction_ref": "provider-key-instruction:test",
                "provider_ref": "provider-catalog:test",
                "env_var_styles": ["TEST_PROVIDER_API_KEY"],
                "setup_source_ref": "provider-source:test:setup",
                "api_docs_source_ref": "provider-source:test:api-docs",
                "safe_summary": "Use provider documentation to understand setup.",
                "credential_input_enabled": True,
            },
            "PROVIDER_KEY_INSTRUCTION_AUTHORITY_DENIED",
        ),
        (
            ProviderCostProfile,
            {
                "cost_profile_ref": "provider-cost-profile:test",
                "provider_ref": "provider-catalog:test",
                "pricing_source_ref": "provider-source:test:pricing",
                "billing_prerequisite": "provider_billing_required",
                "cost_units": ["input_tokens"],
                "token_cost_notes": ["Costs can vary by token direction and model."],
                "automatic_pricing_fetch_enabled": True,
            },
            "PROVIDER_COST_AUTHORITY_DENIED",
        ),
        (
            ProviderAuthorityPosture,
            {
                "authority_ref": "provider-authority:test",
                "provider_sdk_call_enabled": True,
            },
            "PROVIDER_CATALOG_AUTHORITY_DENIED",
        ),
    ],
)
def test_provider_catalog_contracts_reject_authority_claims(
    factory,
    kwargs: dict[str, object],
    reason: str,
) -> None:
    with pytest.raises(ValidationError, match=reason):
        factory(**kwargs)


def test_provider_catalog_rejects_unsafe_copy_or_local_paths() -> None:
    with pytest.raises(ValidationError, match="FORBIDDEN_TOKEN_COST_NOTE_TEXT"):
        ProviderCostProfile(
            cost_profile_ref="provider-cost-profile:unsafe-copy",
            provider_ref="provider-catalog:unsafe-copy",
            pricing_source_ref="provider-source:unsafe-copy:pricing",
            billing_prerequisite="provider_billing_required",
            cost_units=["input_tokens"],
            token_cost_notes=["Paste your key into the provider setup form."],
        )


def test_control_center_provider_setup_guide_route_is_read_only_and_safe() -> None:
    response = client.get("/control-center/providers/setup-guide")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_providers_setup_guide"
    assert body["redactions_applied"] == [
        "safe_refs_only",
        "credential_values_omitted",
        "provider_payloads_omitted",
        "live_prices_omitted",
    ]
    data = body["data"]
    assert data["route_ref"] == "GET /control-center/providers/setup-guide"
    assert data["no_credential_input"] is True
    assert data["no_provider_sdk_calls"] is True
    assert data["no_model_invocation"] is True
    assert data["no_runtime_web_fetching"] is True
    assert data["catalog_visibility_grants_authority"] is False
    assert data["provider_cards"]
    serialized = json.dumps(data).lower()
    for forbidden in [
        "paste your key",
        "save key",
        "test provider",
        "connect provider",
        "invoke provider",
        "raw prompt",
        "raw response",
        "raw provider payload",
    ]:
        assert forbidden not in serialized


def test_provider_setup_guide_route_manifest_posture_is_metadata_only() -> None:
    manifest = build_api_manifest(app)
    route = next(
        route
        for route in manifest.routes
        if route.path == "/control-center/providers/setup-guide"
        and route.method == "GET"
    )

    assert route.operation_id == "get_control_center_providers_setup_guide"
    assert route.side_effect_class == "validation_only"
    assert route.route_classification == "local_readonly"
    assert route.approval_posture == "not_required_for_route_classification"
    assert route.idempotency_required is False
    assert route.rate_limit_targeted is False
    assert "control_center_provider_setup_guide_read_only" in manifest.capabilities_declared
    assert "control_center_provider_setup_guide_as_credential_enrollment" in (
        manifest.capabilities_blocked
    )
    assert "control_center_provider_setup_guide_provider_invocation" in (
        manifest.capabilities_blocked
    )


def test_inspect_provider_setup_guide_cli_uses_same_safe_schema() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/inspect_provider_setup_guide.py"],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)

    assert payload["schema_version"] == "uaa-provider-catalog-cost-literacy.v1"
    assert payload["route_ref"] == "GET /control-center/providers/setup-guide"
    assert payload["no_credential_input"] is True
    assert payload["no_provider_sdk_calls"] is True
    assert payload["provider_cards"]
