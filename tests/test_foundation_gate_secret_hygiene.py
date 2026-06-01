import json

from ultimate_ai_agent.core.gate import (
    FoundationGateEvaluator,
    FoundationGateStatus,
    scan_public_gate_payload_for_secrets,
)


def test_gate_evaluator_report_contains_no_raw_secret_like_values():
    report = FoundationGateEvaluator().evaluate()
    payload = report.model_dump(mode="json")

    assert scan_public_gate_payload_for_secrets(payload) == []
    assert report.overall_status in {FoundationGateStatus.passed, FoundationGateStatus.warning}


def test_sample_gate_report_is_secret_clean():
    with open("reports/foundation_gate/sample_foundation_gate_report.json", encoding="utf-8") as handle:
        payload = json.load(handle)

    assert scan_public_gate_payload_for_secrets(payload) == []
