from ultimate_ai_agent.core.gate import (
    FoundationGateCommandReceipt,
    FoundationGateLatencySummary,
    FoundationGateReleaseLaneSummary,
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


def test_foundation_gate_report_accepts_safe_latency_summary():
    report = build_foundation_gate_report(
        version="0.10.0",
        results=[result("versioning_consistent", FoundationGateStatus.passed)],
    )
    report.latency_gate = FoundationGateLatencySummary(
        schema_version="uaa_foundation_gate_latency_summary.v1",
        task_ref="UAA-P1-043",
        status="passed",
        p50_p95_status="passed",
        foundation_gate_status="passed",
        foundation_gate_best_ms=10.0,
        foundation_gate_mean_ms=12.0,
        foundation_gate_best_budget_ms=20_000.0,
        foundation_gate_mean_budget_ms=25_000.0,
        release_latency_status="passed",
        hot_path_profile_status="passed",
        accepted_failures=[],
        failures=[],
        report_refs={
            "release_latency_report_json": (
                "reports/performance/latest_release_latency_baseline.json"
            )
        },
        foundation_gate_report_json=(
            "reports/foundation_gate/latest_foundation_gate_report.json"
        ),
        foundation_gate_report_md=(
            "reports/foundation_gate/latest_foundation_gate_report.md"
        ),
        environment_safe_summary={
            "machine_identity_recorded": False,
            "environment_variables_recorded": False,
            "raw_paths_recorded": False,
        },
        authority_invariants={
            "authority_decisions_cached_for_speed": False,
            "foundation_gate_checks_preserved": True,
        },
        report_safety={
            "path_material_included": False,
            "credential_material_included": False,
        },
        path_results=[
            {
                "path_id": "api_manifest",
                "safe_label": "GET /api/manifest",
                "required": True,
                "status": "passed",
                "samples": 5,
                "p50_ms": 5.0,
                "p95_ms": 7.0,
                "budget_ms": 150.0,
                "budget_status": "within_budget",
                "reason_codes": [],
                "authority_path_bypassed_for_speed": False,
                "authority_decision_cached_for_speed": False,
                "request_body_recorded": False,
                "response_body_recorded": False,
            }
        ],
        optional_prerequisites=[],
    )

    payload = report.model_dump(mode="json")

    assert payload["latency_gate"]["task_ref"] == "UAA-P1-043"
    assert payload["latency_gate"]["path_results"][0]["p95_ms"] == 7.0
    assert validate_foundation_gate_report(report).success is True


def test_foundation_gate_report_accepts_safe_release_lane_summary():
    report = build_foundation_gate_report(
        version="0.10.0",
        results=[result("versioning_consistent", FoundationGateStatus.passed)],
    )
    report.release_verification_lanes = FoundationGateReleaseLaneSummary(
        schema_version="uaa_release_verification_lanes.v1",
        task_ref="UAA-P1-013",
        overall_status="definition_pass",
        definition_status="pass",
        command_execution_status="not_executed",
        lane_count=8,
        lane_ids=[
            "docs",
            "openapi",
            "api-safety",
            "security-redaction",
            "local-model-e2e",
            "durability",
            "frontend",
            "performance",
        ],
        status_semantics={
            "pass": "All required commands passed.",
            "fail": "A required command failed.",
            "skipped": "A prerequisite was unavailable with a reason code.",
            "blocked": "A required gate or prerequisite is missing.",
            "accepted_failure": "A reviewed release packet accepted the failure.",
        },
        accepted_failures=[],
        validation_failures=[],
        report_safety={
            "raw_path_included": False,
            "raw_log_included": False,
            "credential_material_included": False,
        },
        safe_summary="Release lane definitions validated; commands not executed.",
    )

    payload = report.model_dump(mode="json")

    assert payload["release_verification_lanes"]["task_ref"] == "UAA-P1-013"
    assert payload["release_verification_lanes"]["definition_status"] == "pass"
    assert payload["release_verification_lanes"]["command_execution_status"] == "not_executed"
    assert "performance" in payload["release_verification_lanes"]["lane_ids"]
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
