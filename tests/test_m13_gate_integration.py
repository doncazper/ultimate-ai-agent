from pathlib import Path

import pytest

from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria


ROOT = Path(__file__).resolve().parents[1]


def test_m13_foundation_gate_criteria_exist_and_pass() -> None:
    criteria = default_foundation_gate_criteria()
    m13_ids = {
        "m13_web_control_center_files_present",
        "m13_web_shell_read_only_preview_only",
        "m13_action_preview_ui_posts_only_to_preview",
        "m13_mock_data_safe_non_authoritative",
        "m13_no_tracked_generated_or_native_artifacts",
        "m13_backend_api_contract_unchanged",
        "m13_frontend_no_sensitive_browser_apis",
        "m13_control_center_frontend_safety_verifier_passes",
        "m13_frontend_ci_covers_local_checks",
        "m13_browser_smoke_readiness_manual_local_only",
        "m13_browser_smoke_readiness_verifier_passes",
    }

    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}
    assert m13_ids.issubset(criteria_by_id)

    selected = [criteria_by_id[criterion_id] for criterion_id in sorted(m13_ids)]
    report = FoundationGateEvaluator().evaluate(selected)

    assert report.overall_status == "passed"
    assert report.passed_count == len(m13_ids)
    assert report.failed_count == 0


def test_frontend_source_declares_only_scoped_post_routes() -> None:
    endpoints = (ROOT / "apps/control-center/src/api/endpoints.ts").read_text(encoding="utf-8")
    client = (ROOT / "apps/control-center/src/api/client.ts").read_text(encoding="utf-8")

    assert 'actionPreview: "/control-center/actions/preview"' in endpoints
    assert 'localChatCompletions: "/v1/chat/completions"' in endpoints
    assert "/control-center/actions/execute" not in endpoints
    assert "/control-center/plugins/enable" not in endpoints
    assert "/control-center/remote-workers/dispatch" not in endpoints
    allowed_post_targets = {
        "API_ENDPOINTS.actionPreview",
        "actionDecisionEndpoint(actionId, decision)",
        "actionLocalTaskCommitEndpoint(actionId)",
        "API_ENDPOINTS.controlCenterWorkBoardReorder",
        "API_ENDPOINTS.controlCenterWorkBoardCards",
        "API_ENDPOINTS.controlCenterWorkBoardTasks",
        "API_ENDPOINTS.runtimeAuthorityDecisionPreview",
        "API_ENDPOINTS.runtimeAuthorityMissionPlan",
        "API_ENDPOINTS.runtimeAuthorityLeases",
        "API_ENDPOINTS.runtimeAuthorityLeasesApproveAndIssue",
        "API_ENDPOINTS.runtimeAuthorityLeaseRevoke",
        "API_ENDPOINTS.founderTodayActionEnvelope",
        "API_ENDPOINTS.controlCenterChatTurns",
        "API_ENDPOINTS.founderMemoryManualCandidate",
        "API_ENDPOINTS.founderMemoryFeedback",
        "chatTurnHandoffEndpoint(turnRef)",
        "memoryReviewDecisionEndpoint(candidateRef, decision)",
        "memoryContextPackActionProposalEndpoint(contextPackRef)",
        "API_ENDPOINTS.localChatCompletions",
        "API_ENDPOINTS.turnRouterPreview",
        "API_ENDPOINTS.controlCenterWebEvidenceAttach",
        "postRuntimeGoalMutation",
        "prepareRuntimeGoalMutationApproval",
        "decideRuntimeGoalMutationApproval",
        "revokeRuntimeGoalMutationApproval",
    }
    assert client.count('method: "POST"') == len(allowed_post_targets)
    for target in allowed_post_targets:
        assert target in client
    assert "requestRedactedLocalChatProbe" in client
    assert "responseVisible: false" in client
    assert "stream: false" in client


@pytest.mark.parametrize(
    ("helper_name", "expected_target", "substituted_target"),
    [
        (
            "prepareRuntimeGoalMutationApproval",
            "API_ENDPOINTS.runtimeGoalApprovalPrepareCreate",
            "API_ENDPOINTS.runtimeAuthorityLeasesApproveAndIssue",
        ),
        (
            "decideRuntimeGoalMutationApproval",
            "runtimeGoalApprovalDecisionEndpoint(approvalRequestRef)",
            "API_ENDPOINTS.runtimeAuthorityLeasesApproveAndIssue",
        ),
        (
            "revokeRuntimeGoalMutationApproval",
            "API_ENDPOINTS.runtimeGoalApprovalRevoke",
            "API_ENDPOINTS.runtimeAuthorityLeasesApproveAndIssue",
        ),
    ],
)
def test_m13_rejects_goal_helper_destination_substitution(
    tmp_path: Path,
    helper_name: str,
    expected_target: str,
    substituted_target: str,
) -> None:
    source_root = ROOT / "apps/control-center/src"
    fixture_root = tmp_path / "apps/control-center/src/api"
    fixture_root.mkdir(parents=True)
    (fixture_root / "endpoints.ts").write_text(
        (source_root / "api/endpoints.ts").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    client = (source_root / "api/client.ts").read_text(encoding="utf-8")
    helper_start = client.index(f"function {helper_name}")
    next_export = client.find("\nexport ", helper_start + 1)
    helper_end = len(client) if next_export < 0 else next_export
    helper = client[helper_start:helper_end]
    assert expected_target in helper
    mutated_helper = helper.replace(expected_target, substituted_target, 1)
    assert mutated_helper != helper
    (fixture_root / "client.ts").write_text(
        client[:helper_start] + mutated_helper + client[helper_end:],
        encoding="utf-8",
    )
    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m13_action_preview_ui_posts_only_to_preview"
    )

    result = FoundationGateEvaluator(
        root=tmp_path
    ).check_m13_action_preview_ui_posts_only_to_preview(criterion)

    assert result.status == "failed"
    assert any(
        failure.startswith(
            f"frontend client exact POST binding mismatch: {helper_name}"
        )
        for failure in result.failures
    )


def test_frontend_package_has_only_local_shell_dependencies() -> None:
    package = (ROOT / "apps/control-center/package.json").read_text(encoding="utf-8").lower()
    forbidden = [
        '"next"',
        '"tailwindcss"',
        '"stripe"',
        '"@supabase/supabase-js"',
        '"openai"',
        '"anthropic"',
        '"expo"',
        '"react-native"',
        '"electron"',
        '"puppeteer"',
    ]
    for fragment in forbidden:
        assert fragment not in package
    assert '"lucide-react"' in package
    assert '"@playwright/test"' in package
    assert (
        '"visual:check": "playwright test --config=playwright.visual.config.ts --project=desktop"'
        in package
    )


def test_frontend_mocks_remain_non_authoritative() -> None:
    mock = (ROOT / "apps/control-center/src/mocks/controlCenterData.ts").read_text(encoding="utf-8").lower()
    required = [
        "mock: true",
        "production_control_center: false",
        "production_ready: false",
        "real_model_runtime_ready: false",
        "remote_execution_ready: false",
        "mobile_sensor_ready: false",
        "plugin_or_native_build_ready: false",
        "model_output_authoritative: false",
    ]
    for fragment in required:
        assert fragment in mock
