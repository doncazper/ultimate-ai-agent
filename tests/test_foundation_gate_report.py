from ultimate_ai_agent.core.gate import (
    FoundationGateCommandReceipt,
    FoundationGateResult,
    FoundationGateStatus,
    build_foundation_gate_report,
    validate_foundation_gate_report,
)


def result(criterion_id: str, status: FoundationGateStatus) -> FoundationGateResult:
    return FoundationGateResult(
        criterion_id=criterion_id,
        status=status,
        safe_message=f"{criterion_id} {status.value}",
        evidence_refs=[f"evidence:{criterion_id}"],
    )


def test_required_failure_makes_foundation_gate_report_fail():
    report = build_foundation_gate_report(
        version="0.10.0",
        results=[
            result("versioning_consistent", FoundationGateStatus.passed),
            result("secret_hygiene_clean", FoundationGateStatus.failed),
        ],
    )

    assert report.overall_status == FoundationGateStatus.failed
    assert report.passed_count == 1
    assert report.failed_count == 1
    assert report.warning_count == 0
    assert validate_foundation_gate_report(report).success is True


def test_warning_report_stays_warning_not_passed():
    report = build_foundation_gate_report(
        version="0.10.0",
        results=[result("documentation_current", FoundationGateStatus.warning)],
    )

    assert report.overall_status == FoundationGateStatus.warning
    assert report.next_recommended_action == "Review warnings before expansion."


def test_foundation_gate_report_orders_results_deterministically():
    report = build_foundation_gate_report(
        version="0.10.0",
        results=[
            result("secret_hygiene_clean", FoundationGateStatus.passed),
            result("versioning_consistent", FoundationGateStatus.passed),
            result("blocked_modules_absent", FoundationGateStatus.passed),
        ],
    )

    assert [item.criterion_id for item in report.results] == [
        "blocked_modules_absent",
        "secret_hygiene_clean",
        "versioning_consistent",
    ]


def test_foundation_gate_report_includes_command_receipts():
    receipt = FoundationGateCommandReceipt(
        command_ref="command:scripts.verify_all",
        command_mode="ci-after-verify-all",
        status="satisfied_external",
        satisfied_by="ci-master-verification",
        safe_summary="Master verification was satisfied externally.",
    )
    report = build_foundation_gate_report(
        version="0.10.0",
        results=[result("versioning_consistent", FoundationGateStatus.passed)],
        command_mode="ci-after-verify-all",
        command_receipts=[receipt],
    )

    assert report.command_mode == "ci-after-verify-all"
    assert report.command_receipts == [receipt]
    assert validate_foundation_gate_report(report).success is True


def test_report_validation_blocks_raw_secret_like_payloads():
    report = build_foundation_gate_report(
        version="0.10.0",
        results=[
            FoundationGateResult(
                criterion_id="secret_hygiene_clean",
                status=FoundationGateStatus.failed,
                safe_message="raw token was found",
                evidence_refs=[],
                failures=["api_key=superlongrawvalue123"],
            )
        ],
    )

    envelope = validate_foundation_gate_report(report)

    assert envelope.success is False
    assert envelope.error is not None
    assert envelope.error.code == "FOUNDATION_GATE_REPORT_SECRET_EXPOSURE"
