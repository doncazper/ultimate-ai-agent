from ultimate_ai_agent.core.runtime_readiness.matrix import build_matrix
from ultimate_ai_agent.core.runtime_readiness.reports import build_readiness_report
from ultimate_ai_agent.core.runtime_readiness.smoke_reports import validate_manual_smoke_report


def m11_gate_safe_smoke_report_payload() -> dict:
    return {
        "report_id": "m11_gate_safe_smoke_report",
        "run_id": "m11_gate",
        "smoke_request_id": "smoke_req_m11_gate",
        "endpoint_summary": "loopback host localhost; no query; no credentials",
        "model_id_summary": "local-smoke-model",
        "response_origin": "fake_manual_loopback_smoke",
        "fixed_prompt_hash": "sha256:0123456789abcdef",
        "response_marker_found": True,
        "response_preview": "UAA_LOCAL_SMOKE_OK",
        "response_body_sha256": "sha256:abcdef0123456789",
        "model_output_authoritative": False,
        "metadata": {"manual_only": True, "no_provider_call": True},
    }


def assert_m11_runtime_readiness_gate() -> bool:
    matrix = build_matrix()
    report = build_readiness_report()
    validation = validate_manual_smoke_report(m11_gate_safe_smoke_report_payload())
    return (
        matrix.assert_no_runtime_expansion()
        and matrix.assert_foundation_gate_coverage()
        and report.production_ready is False
        and report.real_model_runtime_ready is False
        and validation.allowed is True
    )
