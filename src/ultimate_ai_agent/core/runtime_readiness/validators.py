from ultimate_ai_agent.core.runtime_readiness.matrix import RuntimeCapabilityMatrix, build_matrix
from ultimate_ai_agent.core.runtime_readiness.reports import RuntimeReadinessReport, build_readiness_report
from ultimate_ai_agent.core.runtime_readiness.smoke_reports import (
    ManualSmokeReport,
    ManualSmokeReportValidation,
    validate_manual_smoke_report,
)


def assert_no_runtime_expansion(matrix: RuntimeCapabilityMatrix | None = None) -> bool:
    return (matrix or build_matrix()).assert_no_runtime_expansion()


def assert_foundation_gate_coverage(matrix: RuntimeCapabilityMatrix | None = None) -> bool:
    return (matrix or build_matrix()).assert_foundation_gate_coverage()


__all__ = [
    "ManualSmokeReport",
    "ManualSmokeReportValidation",
    "RuntimeCapabilityMatrix",
    "RuntimeReadinessReport",
    "assert_foundation_gate_coverage",
    "assert_no_runtime_expansion",
    "build_matrix",
    "build_readiness_report",
    "validate_manual_smoke_report",
]
