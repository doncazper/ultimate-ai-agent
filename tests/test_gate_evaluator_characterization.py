import json
from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import (
    FoundationGateEvaluator as PackageFoundationGateEvaluator,
)
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluator_modules.route_contracts import (
    evaluate_route_contract,
    route_contract_registry,
)
from ultimate_ai_agent.core.gate.evaluator_modules.route_boundaries import (
    EXPECTED_M36_OPENAPI_PATH_COUNT,
    EXPECTED_M167_OPENAPI_PATH_COUNT,
    FOUNDER_LOOP_ACTION_DECISION_ROUTES,
    FOUNDER_LOOP_ACTION_ENVELOPE_ROUTES,
    FOUNDER_LOOP_CHAT_DURABLE_RECEIPT_ROUTES,
    CONTROL_CENTER_OPERATIONAL_STATUS_ROUTES,
    CONTROL_CENTER_CODING_COCKPIT_ROUTES,
    CONTROL_CENTER_PROVIDER_CREDENTIAL_VALIDATION_ROUTES,
    CONTROL_CENTER_PROVIDER_ROUTER_DRY_RUN_ROUTES,
    CONTROL_CENTER_CRM_COMMAND_CENTER_ROUTES,
    CONTROL_CENTER_RUNTIME_COCKPIT_ROUTES,
    CONTROL_CENTER_WORK_BOARD_COMMAND_ROUTES,
    CONTROL_CENTER_WORK_BOARD_ROUTES,
    FOUNDER_LOOP_CONTROL_CENTER_ROUTES,
    FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTES,
    FOUNDER_LOOP_MEMORY_CONTEXT_ACTION_PROPOSAL_ROUTES,
    FOUNDER_LOOP_MEMORY_CONTEXT_ROUTES,
    FOUNDER_LOOP_MEMORY_FEATURE_MINE_ROUTES,
    FOUNDER_LOOP_MEMORY_REVIEW_DECISION_ROUTES,
    GOVERNED_RUNTIME_PILOT_CONTRACT_ROUTES,
    POST_MILESTONE_SAFE_ROUTE_FAMILIES,
    RUN_ATTACHED_APPROVAL_QUEUE_ROUTES,
    UAA_RUNTIME_CONTROL_PLANE_ROUTES,
    UAA_RUNTIME_EXTENSION_ROUTES,
    _historical_openapi_path_set,
    _post_m151_route_boundary_path_set,
)
from ultimate_ai_agent.core.gate.evaluator_modules.route_side_effects import (
    forbidden_route_fragment_failures,
    operation_id_failures,
    unsafe_side_effect_class_failures,
)
from ultimate_ai_agent.core.gate.evaluator_registry import evaluator_registry
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    GOVERNED_RUNTIME_COMMAND_ADAPTER_STATIC_SCAN_ALLOWED_FILES,
    STATIC_SAFETY_EVALUATOR_DATA_FILES,
    STATIC_SAFETY_EVALUATOR_DATA_PREFIXES,
    _is_static_safety_scan_allowed_file,
    m21_forbidden_openwebui_runtime_fragment_failures,
    m36_openapi_route_failures,
    m167_openapi_route_failures,
)
from scripts.classify_foundation_gate_failures import classify_failures


ROOT = Path(__file__).resolve().parents[1]


def test_foundation_gate_legacy_imports_remain_compatible() -> None:
    assert PackageFoundationGateEvaluator is FoundationGateEvaluator
    assert callable(m36_openapi_route_failures)
    assert callable(m167_openapi_route_failures)


def test_foundation_gate_criterion_ids_match_check_method_convention() -> None:
    evaluator = FoundationGateEvaluator(ROOT)
    missing = [
        criterion.criterion_id
        for criterion in default_foundation_gate_criteria()
        if not callable(getattr(evaluator, f"check_{criterion.criterion_id}", None))
    ]

    assert missing == []


def test_route_contract_module_delegates_to_legacy_facade_without_output_drift() -> (
    None
):
    paths = app.openapi()["paths"].keys()

    assert evaluate_route_contract(36, paths) == m36_openapi_route_failures(paths)
    assert evaluate_route_contract(167, paths) == m167_openapi_route_failures(paths)
    assert evaluate_route_contract(36, paths) == []
    assert evaluate_route_contract(167, paths) == []


def test_post_milestone_safe_route_families_are_explicitly_normalized() -> None:
    paths = set(app.openapi()["paths"].keys())

    assert FOUNDER_LOOP_CONTROL_CENTER_ROUTES == {
        "/control-center/actions/inbox",
        "/control-center/actions/{action_id}/approve",
        "/control-center/actions/{action_id}/defer",
        "/control-center/actions/{action_id}/edit",
        "/control-center/actions/{action_id}/receipt",
        "/control-center/actions/{action_id}/reject",
        "/control-center/chat/turns",
        "/control-center/chat/turns/{turn_ref}/handoff",
        "/control-center/chat/turns/{turn_ref}/receipt",
        "/control-center/evidence/timeline",
        "/control-center/memory/citation-integrity",
        "/control-center/memory/context-manifest",
        "/control-center/memory/review",
        "/control-center/memory/context-packs",
        "/control-center/memory/context-packs/{context_pack_ref}/action-proposal",
        "/control-center/memory/context-packs/{context_pack_ref}/preview",
        "/control-center/memory/contradictions",
        "/control-center/memory/feedback",
        "/control-center/memory/follow-ups",
        "/control-center/memory/impact-graph",
        "/control-center/memory/l1-index",
        "/control-center/memory/l2-index",
        "/control-center/memory/l3-index",
        "/control-center/memory/maintenance-runs",
        "/control-center/memory/observation-candidates",
        "/control-center/memory/probe",
        "/control-center/memory/quality-issues",
        "/control-center/memory/recall-health",
        "/control-center/memory/retrieval-diagnostics",
        "/control-center/memory/search",
        "/control-center/memory/workbench",
        "/control-center/memory/review/{candidate_ref}/accept",
        "/control-center/memory/review/{candidate_ref}/correct",
        "/control-center/memory/review/{candidate_ref}/defer",
        "/control-center/memory/review/{candidate_ref}/expire",
        "/control-center/memory/review/{candidate_ref}/forget-request",
        "/control-center/memory/review/{candidate_ref}/merge",
        "/control-center/memory/review/{candidate_ref}/reject",
        "/control-center/memory/review/{candidate_ref}/receipt",
        "/control-center/memory/review/{candidate_ref}/supersede",
        "/control-center/memory/review/manual-candidate",
        "/control-center/actions/{action_id}/local-task/commit",
        "/control-center/today/action-envelope",
        "/control-center/morning-briefing/summary",
        "/control-center/sources/readiness",
        "/control-center/storage/status",
        "/control-center/today/exact-action/approve",
        "/control-center/today/exact-action/execute",
        "/control-center/today/exact-action/prepare",
        "/control-center/today/exact-action/source-review",
        "/control-center/today/exact-action/{today_item_ref}/status",
        "/control-center/today/summary",
    }
    assert FOUNDER_LOOP_ACTION_DECISION_ROUTES == {
        "/control-center/actions/{action_id}/approve",
        "/control-center/actions/{action_id}/defer",
        "/control-center/actions/{action_id}/edit",
        "/control-center/actions/{action_id}/reject",
    }
    assert FOUNDER_LOOP_ACTION_ENVELOPE_ROUTES == {
        "/control-center/today/action-envelope",
    }
    assert FOUNDER_LOOP_CHAT_DURABLE_RECEIPT_ROUTES == {
        "/control-center/chat/turns",
        "/control-center/chat/turns/{turn_ref}/handoff",
    }
    assert FOUNDER_LOOP_MEMORY_REVIEW_DECISION_ROUTES == {
        "/control-center/memory/review/{candidate_ref}/accept",
        "/control-center/memory/review/{candidate_ref}/correct",
        "/control-center/memory/review/{candidate_ref}/defer",
        "/control-center/memory/review/{candidate_ref}/expire",
        "/control-center/memory/review/{candidate_ref}/forget-request",
        "/control-center/memory/review/{candidate_ref}/merge",
        "/control-center/memory/review/{candidate_ref}/reject",
        "/control-center/memory/review/{candidate_ref}/receipt",
        "/control-center/memory/review/{candidate_ref}/supersede",
        "/control-center/memory/review/manual-candidate",
    }
    assert FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTES == {
        "/control-center/actions/{action_id}/local-task/commit",
    }
    assert FOUNDER_LOOP_MEMORY_CONTEXT_ROUTES == {
        "/control-center/memory/context-packs",
        "/control-center/memory/context-packs/{context_pack_ref}/preview",
        "/control-center/memory/l1-index",
        "/control-center/memory/l2-index",
        "/control-center/memory/l3-index",
        "/control-center/memory/search",
        "/control-center/memory/workbench",
    }
    assert FOUNDER_LOOP_MEMORY_CONTEXT_ACTION_PROPOSAL_ROUTES == {
        "/control-center/memory/context-packs/{context_pack_ref}/action-proposal",
    }
    assert FOUNDER_LOOP_MEMORY_FEATURE_MINE_ROUTES == {
        "/control-center/memory/contradictions",
        "/control-center/memory/feedback",
        "/control-center/memory/observation-candidates",
        "/control-center/memory/probe",
    }
    assert CONTROL_CENTER_OPERATIONAL_STATUS_ROUTES == {
        "/control-center/local-models/status",
        "/control-center/settings/status",
    }
    assert CONTROL_CENTER_PROVIDER_CREDENTIAL_VALIDATION_ROUTES == {
        "/control-center/providers/credentials/validate",
    }
    assert CONTROL_CENTER_PROVIDER_ROUTER_DRY_RUN_ROUTES == {
        "/control-center/providers/router/dry-run",
    }
    assert CONTROL_CENTER_CODING_COCKPIT_ROUTES == {
        "/control-center/coding/context",
        "/control-center/coding/git-review",
        "/control-center/coding/live-preview",
        "/control-center/coding/multi-agent-review",
        "/control-center/coding/patch-apply-readiness",
        "/control-center/coding/patch-proposal",
        "/control-center/coding/session",
        "/control-center/coding/test-command-readiness",
    }
    assert CONTROL_CENTER_WORK_BOARD_ROUTES == {
        "/control-center/work-board",
    }
    assert CONTROL_CENTER_WORK_BOARD_COMMAND_ROUTES == {
        "/control-center/work-board/cards",
        "/control-center/work-board/reorder",
        "/control-center/work-board/tasks",
    }
    assert CONTROL_CENTER_CRM_COMMAND_CENTER_ROUTES == {
        "/control-center/crm/follow-ups",
        "/control-center/crm/local-mutations",
        "/control-center/crm/pipelines",
        "/control-center/crm/relationships",
        "/control-center/crm/smart-lists",
        "/control-center/crm/summary",
        "/control-center/crm/timeline",
    }
    assert CONTROL_CENTER_RUNTIME_COCKPIT_ROUTES == {
        "/control-center/agent-loop/thread",
        "/control-center/providers/runtime-control-plane",
        "/control-center/runtime-readiness/summary",
    }
    assert GOVERNED_RUNTIME_PILOT_CONTRACT_ROUTES == {
        "/api/runtime/capabilities",
        "/api/runtime/command/run",
        "/api/runtime/invocations",
        "/api/runtime/invocations/{id}",
        "/api/runtime/invocations/{id}/approve",
        "/api/runtime/invocations/{id}/execute",
        "/api/runtime/invocations/{id}/receipt",
        "/api/runtime/local-model/call",
        "/api/runtime/safe-disable",
    }
    assert UAA_RUNTIME_EXTENSION_ROUTES == {
        "/api/runtime/background-jobs",
        "/api/runtime/doctor-diagnostics",
        "/api/runtime/logging-profile",
        "/api/runtime/lsp-diagnostics",
        "/api/runtime/managed-scope-policy",
        "/api/runtime/mcp-catalog-filtering",
        "/api/runtime/messaging-gateway-posture",
        "/api/runtime/plugin-metadata-posture",
        "/api/runtime/preview-rail",
        "/api/runtime/remote-execution-posture",
        "/api/runtime/result-classification",
        "/api/runtime/session-continuity",
        "/api/runtime/skill-marketplace-posture",
        "/api/runtime/slash-command-registry",
        "/api/runtime/subagent-isolation",
        "/api/runtime/voice-media-posture",
        "/api/runtime/worktree-per-agent",
    }
    assert len(paths & UAA_RUNTIME_CONTROL_PLANE_ROUTES) == 61
    assert RUN_ATTACHED_APPROVAL_QUEUE_ROUTES == {
        "/control-center/approvals/queue",
    }
    assert set(POST_MILESTONE_SAFE_ROUTE_FAMILIES) == {
        "control_center_matrix_harness",
        "control_center_matrix_session",
        "control_center_communications_readonly",
        "control_center_operational_status",
        "control_center_proof_start_trust",
        "control_center_provider_catalog",
        "control_center_provider_credential_validation",
        "control_center_provider_router_dry_run",
        "control_center_coding_cockpit",
        "control_center_capability_surface",
        "control_center_crm_command_center",
        "control_center_runtime_cockpit",
        "control_center_work_board",
        "control_center_work_board_commands",
        "control_center_setup_assistant",
        "control_center_tiny_provider_lane",
        "extension_disabled_install_record",
        "founder_loop",
        "governed_runtime_pilot_contracts",
        "mattermost",
        "packaging_proof",
        "redacted_observability",
        "run_attached_approval_queue",
        "task_decomposition",
        "turn_contract_router_diagnostic",
        "uaa_runtime_control_plane",
        "visual_proof",
        "web_evidence_product_slice",
        "v1_local_model_gateway",
    }
    assert (
        len(_post_m151_route_boundary_path_set(paths))
        == EXPECTED_M167_OPENAPI_PATH_COUNT
    )
    assert len(_historical_openapi_path_set(paths)) == EXPECTED_M36_OPENAPI_PATH_COUNT


def test_route_side_effect_helpers_match_current_manifest_contract() -> None:
    from ultimate_ai_agent.api.manifest import iter_api_route_items
    from ultimate_ai_agent.api.openapi import (
        FORBIDDEN_ROUTE_FRAGMENT_EXEMPTIONS,
        FORBIDDEN_ROUTE_FRAGMENTS,
    )

    routes = iter_api_route_items(app)

    assert operation_id_failures(routes) == []
    assert (
        forbidden_route_fragment_failures(
            routes,
            FORBIDDEN_ROUTE_FRAGMENTS,
            exact_path_exemptions=FORBIDDEN_ROUTE_FRAGMENT_EXEMPTIONS,
        )
        == []
    )
    assert unsafe_side_effect_class_failures(routes) == []


def test_foundation_gate_failure_classification_fixture_is_safe_and_bounded() -> None:
    fixture_path = ROOT / "tests/fixtures/foundation_gate_failure_classification.json"
    summary = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert summary["schema_version"] == "uaa-foundation-gate-failure-classification.v1"
    assert summary["source"]["report_ref"] == "foundation-gate-report:latest"
    assert summary["source"]["failed_count"] == len(summary["items"])
    assert set(summary["classification_counts"]).issubset(
        {
            "expected_safe_route_family_needs_normalization",
            "real_unsafe_route_drift",
            "stale_historical_expectation",
            "unknown_needs_review",
        }
    )
    assert "raw_paths_omitted" in summary["redactions_applied"]
    assert "/Users/" not in json.dumps(summary)


def test_static_safety_evaluator_data_exemption_is_scoped() -> None:
    criteria_file = "src/ultimate_ai_agent/core/gate/criteria.py"
    evaluator_facade_file = "src/ultimate_ai_agent/core/gate/evaluators.py"
    legacy_checks_file = "src/ultimate_ai_agent/core/gate/legacy_checks.py"
    route_boundary_data_file = (
        "src/ultimate_ai_agent/core/gate/evaluator_modules/route_boundaries.py"
    )
    legacy_support_file = "src/ultimate_ai_agent/core/gate/legacy_support.py"
    web_hybrid_policy_file = (
        "src/ultimate_ai_agent/core/gate/web_hybrid_static_policy.py"
    )
    legacy_check_family_files = {
        f"src/ultimate_ai_agent/core/gate/legacy_check_families/part_{part_number:03d}.py"
        for part_number in range(1, 45)
    }
    criteria_family_files = {
        "src/ultimate_ai_agent/core/gate/criteria_families/foundation_core.py",
        "src/ultimate_ai_agent/core/gate/criteria_families/runtime_authority_bootstrap.py",
        "src/ultimate_ai_agent/core/gate/criteria_families/control_center_shell.py",
        "src/ultimate_ai_agent/core/gate/criteria_families/product_spine_m21_m66.py",
        "src/ultimate_ai_agent/core/gate/criteria_families/safety_expansion_m67_m98.py",
        "src/ultimate_ai_agent/core/gate/criteria_families/post_m100_m99_m130.py",
        "src/ultimate_ai_agent/core/gate/criteria_families/autonomy_alpha_m131_m150.py",
        "src/ultimate_ai_agent/core/gate/criteria_families/local_model_m151_m167.py",
        "src/ultimate_ai_agent/core/gate/criteria_families/cross_release_docs.py",
    }
    command_adapter_file = "src/ultimate_ai_agent/core/runtime_gateway/command.py"

    assert STATIC_SAFETY_EVALUATOR_DATA_FILES == frozenset(
        {
            criteria_file,
            evaluator_facade_file,
            legacy_checks_file,
            route_boundary_data_file,
            legacy_support_file,
            web_hybrid_policy_file,
        }
        | legacy_check_family_files
        | criteria_family_files
    )
    assert STATIC_SAFETY_EVALUATOR_DATA_PREFIXES == (
        "src/ultimate_ai_agent/core/gate/checkpoint_builders/",
    )
    assert GOVERNED_RUNTIME_COMMAND_ADAPTER_STATIC_SCAN_ALLOWED_FILES == frozenset(
        {command_adapter_file}
    )
    assert _is_static_safety_scan_allowed_file(criteria_file, frozenset())
    assert _is_static_safety_scan_allowed_file(evaluator_facade_file, frozenset())
    assert _is_static_safety_scan_allowed_file(legacy_checks_file, frozenset())
    assert _is_static_safety_scan_allowed_file(route_boundary_data_file, frozenset())
    assert _is_static_safety_scan_allowed_file(legacy_support_file, frozenset())
    assert _is_static_safety_scan_allowed_file(
        "src/ultimate_ai_agent/core/gate/legacy_check_families/part_001.py",
        frozenset(),
    )
    assert _is_static_safety_scan_allowed_file(
        "src/ultimate_ai_agent/core/gate/criteria_families/product_spine_m21_m66.py",
        frozenset(),
    )
    assert _is_static_safety_scan_allowed_file(
        "src/ultimate_ai_agent/core/gate/checkpoint_builders/m150_ultimate_ai_agent_alpha.py",
        frozenset(),
    )
    assert _is_static_safety_scan_allowed_file(command_adapter_file, frozenset())
    assert not _is_static_safety_scan_allowed_file(
        "src/ultimate_ai_agent/core/evidence_signing/macos_keychain.py",
        frozenset(),
    )
    assert _is_static_safety_scan_allowed_file("src/allowed.py", {"src/allowed.py"})
    assert not _is_static_safety_scan_allowed_file(
        "src/ultimate_ai_agent/core/gate/evaluator_modules/route_contracts.py",
        frozenset(),
    )
    assert not _is_static_safety_scan_allowed_file(
        "src/ultimate_ai_agent/core/gate/checkpoint_builder_notes.py",
        frozenset(),
    )


def test_sealed_backend_is_not_a_global_static_scan_exception() -> None:
    backend_rel = "src/ultimate_ai_agent/core/sandbox_calculation/backend.py"
    assert not _is_static_safety_scan_allowed_file(backend_rel, frozenset())


def test_route_boundary_data_only_static_scan_failures_classify_as_stale() -> None:
    summary = classify_failures(
        {
            "overall_status": "failed",
            "results": [
                {
                    "criterion_id": "m100_mobile_permission_model_v1_static_safety",
                    "status": "failed",
                    "failures": [
                        "M100 forbidden mobile permission fragment in "
                        "src/ultimate_ai_agent/core/gate/evaluator_modules/route_boundaries.py: "
                        "backend_route_added=True",
                    ],
                }
            ],
        }
    )

    assert summary["classification_counts"] == {"stale_historical_expectation": 1}
    assert summary["items"][0]["reason_code"] == (
        "EXTRACTED_EVALUATOR_DATA_STATIC_SCAN_FALSE_POSITIVE"
    )


def test_route_contract_registry_maps_existing_openapi_milestones() -> None:
    registry = route_contract_registry()
    milestones = {entry.milestone for entry in registry}

    assert {16, 36, 80, 108, 167}.issubset(milestones)
    assert all(entry.status == "extracted_route_boundary" for entry in registry)
    assert all(
        entry.module == "ultimate_ai_agent.core.gate.evaluator_modules.route_boundaries"
        for entry in registry
    )


def test_evaluator_registry_marks_route_contracts_as_extracted() -> None:
    entries = {entry.name: entry for entry in evaluator_registry()}

    route_entry = entries["route_contract_evaluators"]
    assert route_entry.status == "extracted_route_boundary"
    assert (
        route_entry.module
        == "ultimate_ai_agent.core.gate.evaluator_modules.route_contracts"
    )


def test_foundation_gate_openapi_characterization_report_shape() -> None:
    criteria_by_id = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }
    selected = [
        criteria_by_id["api_manifest_endpoint_present"],
        criteria_by_id["openapi_contract_valid"],
        criteria_by_id["api_operation_ids_unique"],
    ]

    report = FoundationGateEvaluator(ROOT).evaluate(selected)
    result_ids = {result.criterion_id for result in report.results}

    assert result_ids == {
        "api_manifest_endpoint_present",
        "openapi_contract_valid",
        "api_operation_ids_unique",
    }
    assert report.overall_status == "passed"
    assert report.failed_count == 0
    assert report.passed_count == 3
    assert report.summary == "3 passed, 0 failed, 0 warnings, 0 blocked."


def test_m12_accepts_exact_founder_loop_local_dev_summary_routes() -> None:
    criteria_by_id = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    report = FoundationGateEvaluator(ROOT).evaluate(
        [criteria_by_id["m12_control_center_api_read_only"]]
    )

    assert report.overall_status == "passed"
    assert report.failed_count == 0


def test_proof_lane_normalizations_do_not_create_legacy_gate_false_positives() -> None:
    criteria_by_id = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }
    selected = [
        criteria_by_id["m13_web_shell_read_only_preview_only"],
        criteria_by_id["m13_frontend_ci_covers_local_checks"],
        criteria_by_id["m21_openwebui_bridge_contract_safe"],
        criteria_by_id["m167_live_model_production_hardening_static_safety"],
    ]

    report = FoundationGateEvaluator(ROOT).evaluate(selected)

    assert report.overall_status == "passed"
    assert report.failed_count == 0


def test_m13_playwright_ci_exception_rejects_chained_execution(tmp_path: Path) -> None:
    workflow = tmp_path / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "\n".join(
            [
                "jobs:",
                "  release-lane-visual-regression:",
                "    steps:",
                "      - run: cd apps/control-center",
                "      - run: npm ci",
                "      - run: npm run typecheck --if-present",
                "      - run: npm run lint --if-present",
                "      - run: npm run test --if-present -- --run",
                "      - run: npm run build --if-present",
                "      - run: npm run visual:check",
                "      - run: PYTHONPATH=src .venv/bin/python "
                "scripts/verify_control_center_visual_regression.py",
                "      - name: Install Playwright Chromium",
                "        run: npx playwright install --with-deps chromium "
                "&& npx playwright test https://example.invalid",
                "  release-lane-desktop-packaging:",
                "    steps:",
                "      - run: PYTHONPATH=src .venv/bin/python "
                "scripts/run_local_runtime_packaging_proof.py",
            ]
        ),
        encoding="utf-8",
    )
    verifier = tmp_path / "scripts/verify_control_center_browser_smoke_readiness.py"
    verifier.parent.mkdir(parents=True)
    verifier.write_text(
        (ROOT / "scripts/verify_control_center_browser_smoke_readiness.py").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    (tmp_path / "Makefile").write_text(
        (ROOT / "Makefile").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    criteria_by_id = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    report = FoundationGateEvaluator(tmp_path).evaluate(
        [criteria_by_id["m13_frontend_ci_covers_local_checks"]]
    )

    assert report.overall_status == "failed"
    assert report.failed_count == 1
    assert "forbidden CI browser automation fragment: playwright" in (
        report.results[0].failures
    )


def test_m21_packaging_proof_exception_only_allows_compose_fragment(
    tmp_path: Path,
) -> None:
    script = tmp_path / "scripts/run_local_runtime_packaging_proof.py"
    script.parent.mkdir(parents=True)
    script.write_text('PROOF_SCOPE = "local docker-compose only"\n', encoding="utf-8")

    assert m21_forbidden_openwebui_runtime_fragment_failures(tmp_path) == []

    script.write_text(
        "\n".join(
            [
                'PROOF_SCOPE = "local docker-compose only"',
                'UNSAFE = "openwebui_base_url /openwebui/execute"',
            ]
        ),
        encoding="utf-8",
    )

    failures = m21_forbidden_openwebui_runtime_fragment_failures(tmp_path)
    assert any("openwebui_base_url" in failure for failure in failures)
    assert any("/openwebui/execute" in failure for failure in failures)


def test_representative_static_safety_criteria_ignore_extracted_route_boundary_data() -> (
    None
):
    criteria_by_id = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }
    selected_ids = [
        "m19_mobile_companion_contract_planning_safe",
        "m20_device_capability_broker_contract_safe",
        "m49_mobile_approval_static_safety",
        "m80_network_browser_openwebui_hardening_freeze_static_safety",
        "m100_mobile_permission_model_v1_static_safety",
        "m125_connector_read_only_runtime_static_safety",
        "m131_autonomy_mode4_scoped_work_session_static_safety",
        "m150_ultimate_ai_agent_alpha_static_safety",
        "m166_local_model_production_readiness_static_safety",
    ]

    report = FoundationGateEvaluator(ROOT).evaluate(
        [criteria_by_id[criterion_id] for criterion_id in selected_ids]
    )

    assert report.overall_status == "passed", {
        result.criterion_id: result.failures
        for result in report.results
        if result.status == "failed"
    }


def test_static_safety_scans_still_fail_non_exempt_source_files(tmp_path: Path) -> None:
    source_file = tmp_path / "src/ultimate_ai_agent/core/not_allowed.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("backend_route_added=True\n", encoding="utf-8")
    criteria_by_id = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    report = FoundationGateEvaluator(tmp_path).evaluate(
        [criteria_by_id["m100_mobile_permission_model_v1_static_safety"]]
    )

    assert report.overall_status == "failed"
    assert any(
        "backend_route_added=True" in failure for failure in report.results[0].failures
    )
