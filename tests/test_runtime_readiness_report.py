from ultimate_ai_agent.core.runtime_readiness import (
    RuntimeReadinessStatus,
    build_readiness_report,
)


def test_runtime_readiness_report_is_not_production_or_execution_ready():
    report = build_readiness_report(baseline_version="0.15.0")
    dumped = report.model_dump(mode="json")

    assert report.status == RuntimeReadinessStatus.ready_for_manual_smoke
    assert report.production_ready is False
    assert report.real_model_runtime_ready is False
    assert report.remote_execution_ready is False
    assert report.mobile_sensor_ready is False
    assert report.plugin_or_native_build_ready is False
    assert report.model_output_authoritative is False
    assert dumped["capability_matrix"]["summary"]["real_model_runtime_ready"] is False
    assert "no runtime execution" in " ".join(report.guardrail_summary).lower()
