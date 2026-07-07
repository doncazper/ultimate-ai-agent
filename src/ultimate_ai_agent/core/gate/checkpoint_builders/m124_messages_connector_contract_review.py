from __future__ import annotations
from typing import Any
from importlib import import_module
from ultimate_ai_agent.core.mobile_companion import (
    build_mobile_approval_renewal_ux_report,
    build_mobile_kill_switch_revocation_record,
    build_mobile_sensor_audit_ledger_record,
    build_mobile_sensor_hardening_freeze_record,
)
from ultimate_ai_agent.core.production_readiness import (
    build_account_connector_contract_review_record,
    build_deployment_mode_matrix_record,
    build_production_audit_retention_policy_record,
    build_production_authority_readiness_review_record,
    build_production_red_team_harness_record,
    build_production_threat_model_record,
    build_remote_agent_coordination_contract_record,
    build_role_based_authority_model_record,
    build_secrets_boundary_record,
    build_user_workspace_identity_record,
)


def _connectors() -> Any:
    try:
        return import_module("ultimate_ai_agent.core.connectors")
    except ModuleNotFoundError as exc:
        pytest.fail(f"M124 connectors package missing: {exc}")


def _m120_source_record() -> Any:
    return build_production_authority_readiness_review_record(
        source_record=build_production_red_team_harness_record(
            source_record=build_deployment_mode_matrix_record(
                source_record=build_remote_agent_coordination_contract_record(
                    source_record=build_role_based_authority_model_record(
                        source_record=build_production_audit_retention_policy_record(
                            source_record=build_account_connector_contract_review_record(
                                source_record=build_secrets_boundary_record(
                                    source_record=build_user_workspace_identity_record(
                                        source_record=build_production_threat_model_record(
                                            source_record=build_mobile_sensor_hardening_freeze_record(
                                                source_record=build_mobile_sensor_audit_ledger_record(
                                                    source_record=build_mobile_kill_switch_revocation_record(
                                                        source_report=build_mobile_approval_renewal_ux_report()
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )


def _source_record() -> Any:
    connectors = _connectors()
    return connectors.build_contacts_connector_contract_refresh_record(
        source_record=connectors.build_calendar_connector_contract_refresh_record(
            source_record=connectors.build_email_connector_contract_refresh_record(
                source_record=_m120_source_record()
            )
        )
    )
