from ultimate_ai_agent.core.gate.reports import (
    scan_public_gate_payload_for_secrets,
    validate_foundation_gate_report,
)
from ultimate_ai_agent.core.gate.shadow_replay import ShadowReplayScenario
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope


def validate_shadow_replay_scenario(scenario: ShadowReplayScenario) -> ResultEnvelope:
    secret_refs = scan_public_gate_payload_for_secrets(scenario.model_dump(mode="json"))
    if secret_refs:
        return ResultEnvelope(
            success=False,
            operation="validate_shadow_replay_scenario",
            service="FoundationGateAPI",
            trace_id=scenario.scenario_id,
            data={"scenario_id": scenario.scenario_id, "status": "rejected"},
        )
    return ResultEnvelope(
        success=True,
        operation="validate_shadow_replay_scenario",
        service="FoundationGateAPI",
        trace_id=scenario.scenario_id,
        data={
            "scenario_id": scenario.scenario_id,
            "status": "validated",
            "executes_replay": False,
        },
    )


__all__ = [
    "scan_public_gate_payload_for_secrets",
    "validate_foundation_gate_report",
    "validate_shadow_replay_scenario",
]
