from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.verify_operational_maturity import (
    AUTHORITY_SCORECARD_PATH,
    EXPECTED_AUTHORITY_CANDIDATES,
    EXPECTED_AUTHORITY_FOUNDATIONS,
    LADDER_LABELS,
    LOCAL_MODEL_CLI_REF,
    LOCAL_TASK_REPEATABILITY_GATE_REF,
    LOCAL_TASK_REPEATABILITY_REQUIRED_FOCUSED_TEST_REFS,
    LOCAL_TASK_REPEATABILITY_REQUIRED_FRONTEND_TEST_REFS,
    LOCAL_TASK_REPEATABILITY_REQUIRED_VERIFIER_REFS,
    LOCAL_TASK_ROLLBACK_REF,
    LOCAL_TASK_SAFE_DISABLE_REF,
    MANIFEST_PATH,
    MEMORY_CONTEXT_PACK_ROUTE,
    MEMORY_CONTEXT_PACK_TEST_REFS,
    MEMORY_CONTEXT_PACK_VERIFIER_REFS,
    PATCH_WORKBENCH_APPLY_ROUTE,
    PATCH_WORKBENCH_MODULE_ID,
    PATCH_WORKBENCH_REQUIRED_MISSING_CONTRACTS,
    SCHEMA_PATH,
    _append_local_model_manifest_failures,
    _append_memory_context_pack_manifest_failures,
    _append_patch_workbench_manifest_failures,
    _append_module_failures,
    _append_mock_fallback_fixture_failures,
    _append_read_only_status_probe_failures,
    _append_stale_language_scan_failures,
    verify,
)
from scripts.verification.repo import load_json


def test_operational_maturity_manifest_passes_verifier() -> None:
    assert verify() == []


def test_operational_maturity_manifest_declares_canonical_ladder() -> None:
    manifest = load_json(MANIFEST_PATH)
    schema = load_json(SCHEMA_PATH)
    modules = {module["module_id"]: module for module in manifest["modules"]}

    assert manifest["schema_version"] == "uaa-control-center-operational-maturity.v1"
    assert schema["$defs"]["rank"]["minimum"] == 0
    assert schema["$defs"]["rank"]["maximum"] == 7
    assert set(LADDER_LABELS.values()) == {
        "docs_only",
        "read_only_status",
        "proposal_review",
        "decision_receipts",
        "execution_ready_contract",
        "local_execution_receipt_evidence",
        "rollback_safe_disable_verified",
        "routine_operational_loop",
    }
    assert modules["action_inbox"]["current_rank"] == 3
    local_task_lane = modules["action_inbox"]["graduated_lanes"][0]
    assert local_task_lane["lane_id"] == "local_task_create"
    assert local_task_lane["rank"] == 5
    assert (
        "POST /control-center/actions/{action_id}/local-task/commit"
        in local_task_lane["backend_routes"]
    )
    assert local_task_lane["rollback_or_safe_disable_required"] is True
    assert set(local_task_lane["rollback_or_safe_disable_refs"]) == {
        LOCAL_TASK_ROLLBACK_REF,
        LOCAL_TASK_SAFE_DISABLE_REF,
    }
    assert "rollback_execution" in local_task_lane["blocked_authorities"]
    assert local_task_lane["repeatability_gate_ref"] == LOCAL_TASK_REPEATABILITY_GATE_REF
    assert LOCAL_TASK_REPEATABILITY_REQUIRED_FOCUSED_TEST_REFS.issubset(
        set(local_task_lane["focused_test_refs"])
    )
    assert LOCAL_TASK_REPEATABILITY_REQUIRED_FRONTEND_TEST_REFS.issubset(
        set(local_task_lane["frontend_repeatability_test_refs"])
    )
    assert LOCAL_TASK_REPEATABILITY_REQUIRED_VERIFIER_REFS.issubset(
        set(local_task_lane["verifier_repeatability_refs"])
    )
    assert MEMORY_CONTEXT_PACK_ROUTE in modules["memory"]["backend_routes"]
    assert MEMORY_CONTEXT_PACK_TEST_REFS.issubset(set(modules["memory"]["test_refs"]))
    assert MEMORY_CONTEXT_PACK_VERIFIER_REFS.issubset(
        set(modules["memory"]["verifier_refs"])
    )
    assert LOCAL_MODEL_CLI_REF in modules["local_models"]["cli_or_script_refs"]


def test_operational_maturity_gate_docs_exist() -> None:
    for path in [MANIFEST_PATH, SCHEMA_PATH, AUTHORITY_SCORECARD_PATH]:
        assert Path(path).exists()


def test_operational_maturity_verifier_requires_local_task_posture_refs() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    lane = modules["action_inbox"]["graduated_lanes"][0]
    lane["rollback_or_safe_disable_refs"] = []

    failures = verify(manifest_override=manifest)

    assert any(
        "action_inbox:local_task_create rank 5 lane requires posture refs" in failure
        for failure in failures
    )
    assert any(
        f"local_task_create lane missing {LOCAL_TASK_ROLLBACK_REF}" in failure
        for failure in failures
    )
    assert any(
        f"local_task_create lane missing {LOCAL_TASK_SAFE_DISABLE_REF}" in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_local_task_repeatability_gate() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    lane = modules["action_inbox"]["graduated_lanes"][0]
    lane["repeatability_gate_ref"] = None
    lane["focused_test_refs"] = []
    lane["frontend_repeatability_test_refs"] = []
    lane["verifier_repeatability_refs"] = []

    failures = verify(manifest_override=manifest)

    assert any(
        "local_task_create lane must declare FCC-ACTION-002" in failure
        for failure in failures
    )
    assert any(
        "local_task_create repeatability gate missing tests/test_fcc_v1_003_founder_loop_vertical_slice.py::test_founder_loop_cli_commits_local_task_with_safe_refs"
        in failure
        for failure in failures
    )
    assert any(
        "local_task_create repeatability gate missing frontend test apps/control-center/src/App.test.tsx::commits only the eligible Action Inbox local task lane through the typed route"
        in failure
        for failure in failures
    )
    assert any(
        "local_task_create repeatability gate missing verifier ref scripts/verify_operational_maturity.py::_append_local_task_repeatability_gate_failures"
        in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_local_task_safe_disable_flag() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    modules["action_inbox"]["graduated_lanes"][0][
        "rollback_or_safe_disable_required"
    ] = False

    failures = verify(manifest_override=manifest)

    assert any(
        "action_inbox:local_task_create rank 5 lane requires rollback_or_safe_disable_required"
        in failure
        for failure in failures
    )
    assert any(
        "local_task_create lane must require rollback or safe-disable" in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_rollback_execution_blocked() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    lane = modules["action_inbox"]["graduated_lanes"][0]
    lane["blocked_authorities"] = [
        authority
        for authority in lane["blocked_authorities"]
        if authority != "rollback_execution"
    ]

    failures = verify(manifest_override=manifest)

    assert any(
        "action_inbox:local_task_create rank 5 lane must block rollback_execution"
        in failure
        for failure in failures
    )
    assert any(
        "local_task_create lane must keep rollback_execution blocked" in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_memory_context_pack_refs() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    memory = modules["memory"]
    memory["backend_routes"] = [
        route
        for route in memory["backend_routes"]
        if route != MEMORY_CONTEXT_PACK_ROUTE
    ]
    memory["test_refs"] = [
        ref
        for ref in memory["test_refs"]
        if ref not in MEMORY_CONTEXT_PACK_TEST_REFS
    ]
    memory["verifier_refs"] = [
        ref
        for ref in memory["verifier_refs"]
        if ref not in MEMORY_CONTEXT_PACK_VERIFIER_REFS
    ]
    failures: list[str] = []

    _append_memory_context_pack_manifest_failures(failures, memory)

    assert any(
        f"memory context-pack readiness missing route {MEMORY_CONTEXT_PACK_ROUTE}"
        in failure
        for failure in failures
    )
    assert any(
        "memory context-pack readiness missing test" in failure
        for failure in failures
    )
    assert any(
        "memory context-pack readiness missing verifier" in failure
        for failure in failures
    )


def test_operational_maturity_verifier_rejects_patch_apply_claim_without_gates() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    patch = modules[PATCH_WORKBENCH_MODULE_ID]
    patch["current_rank"] = 4
    patch["current_rank_label"] = "execution_ready_contract"
    patch["honest_status"] = "execution_ready_contract"
    patch["missing_contracts"] = []
    patch["backend_routes"] = [
        route for route in patch["backend_routes"] if route != PATCH_WORKBENCH_APPLY_ROUTE
    ]
    patch["cli_or_script_refs"] = []
    patch["receipt_refs"] = []
    patch["backend_owned_receipts"] = False

    failures: list[str] = []
    _append_patch_workbench_manifest_failures(failures, patch)

    assert any(PATCH_WORKBENCH_APPLY_ROUTE in failure for failure in failures)
    assert any("requires backend_owned_receipts" in failure for failure in failures)
    assert any("requires receipt_refs" in failure for failure in failures)
    assert any("requires CLI parity" in failure for failure in failures)


def test_operational_maturity_verifier_requires_patch_rank2_apply_blockers() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    patch = modules[PATCH_WORKBENCH_MODULE_ID]
    patch["honest_status"] = "proposal_review"
    patch["missing_contracts"] = []
    patch["blocked_authorities"] = []
    patch["durable_receipt"] = True

    failures: list[str] = []
    _append_patch_workbench_manifest_failures(failures, patch)

    assert any("must keep apply_blocked honest_status" in failure for failure in failures)
    for contract_ref in PATCH_WORKBENCH_REQUIRED_MISSING_CONTRACTS:
        assert any(contract_ref in failure for failure in failures)
    assert any("must block code_apply_execution" in failure for failure in failures)
    assert any("must not claim durable_receipt" in failure for failure in failures)


def test_operational_maturity_verifier_requires_path_backed_local_model_cli_ref() -> (
    None
):
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    local_models = modules["local_models"]
    local_models["cli_or_script_refs"] = ["uaa local-model status"]
    failures: list[str] = []

    _append_local_model_manifest_failures(failures, local_models)

    assert any(LOCAL_MODEL_CLI_REF in failure for failure in failures)


def test_operational_maturity_read_only_status_probe_passes() -> None:
    failures: list[str] = []

    _append_read_only_status_probe_failures(failures)

    assert failures == []


def test_authority_candidate_scorecard_declares_no_go_conveyor() -> None:
    scorecard = load_json(AUTHORITY_SCORECARD_PATH)

    assert (
        scorecard["schema_version"]
        == "uaa-control-center-authority-candidate-scorecard.v1"
    )
    assert scorecard["status"] == "active authority candidate scorecard"
    assert {
        lane["foundation_id"] for lane in scorecard["proposal_foundation"]
    } == EXPECTED_AUTHORITY_FOUNDATIONS
    assert {
        candidate["candidate_id"] for candidate in scorecard["authority_candidates"]
    } == EXPECTED_AUTHORITY_CANDIDATES
    assert all(
        candidate["selected_for_micro_lane"] is False
        for candidate in scorecard["authority_candidates"]
    )
    assert scorecard["first_micro_lane_decision"]["status"] == "no_go"
    assert scorecard["first_micro_lane_decision"]["selected_candidate_id"] is None
    assert "local_task_create" not in {
        candidate["candidate_id"] for candidate in scorecard["authority_candidates"]
    }


def test_authority_scorecard_rejects_selected_candidate_without_micro_lane_status() -> (
    None
):
    scorecard = _scorecard_copy()
    candidate = scorecard["authority_candidates"][0]
    candidate["selected_for_micro_lane"] = True
    candidate["status"] = "contract_ready"
    scorecard["first_micro_lane_decision"]["status"] = "selected"
    scorecard["first_micro_lane_decision"]["selected_candidate_id"] = candidate[
        "candidate_id"
    ]
    scorecard["first_micro_lane_decision"]["no_go_reason"] = None

    failures = verify(scorecard_override=scorecard)

    assert any(
        f"{candidate['candidate_id']} selected micro-lane must be micro_lane_candidate"
        in failure
        for failure in failures
    )


def test_authority_scorecard_rejects_micro_lane_candidate_missing_required_refs() -> (
    None
):
    scorecard = _scorecard_copy()
    candidate = scorecard["authority_candidates"][1]
    candidate["status"] = "micro_lane_candidate"
    candidate["selected_for_micro_lane"] = True
    scorecard["first_micro_lane_decision"]["status"] = "selected"
    scorecard["first_micro_lane_decision"]["selected_candidate_id"] = candidate[
        "candidate_id"
    ]
    scorecard["first_micro_lane_decision"]["no_go_reason"] = None

    failures = verify(scorecard_override=scorecard)

    assert any(
        f"{candidate['candidate_id']} micro-lane candidate requires exact_scope_ref"
        in failure
        for failure in failures
    )
    assert any(
        f"{candidate['candidate_id']} micro-lane candidate requires rollback_safe_disable_plan_ref"
        in failure
        for failure in failures
    )
    assert any(
        f"{candidate['candidate_id']} micro-lane candidate requires cli_api_core_parity_refs"
        in failure
        for failure in failures
    )


def test_authority_scorecard_rejects_multiple_selected_candidates() -> None:
    scorecard = _scorecard_copy()
    for candidate in scorecard["authority_candidates"][:2]:
        candidate["status"] = "micro_lane_candidate"
        candidate["selected_for_micro_lane"] = True
    scorecard["first_micro_lane_decision"]["status"] = "selected"
    scorecard["first_micro_lane_decision"]["selected_candidate_id"] = scorecard[
        "authority_candidates"
    ][0]["candidate_id"]
    scorecard["first_micro_lane_decision"]["no_go_reason"] = None

    failures = verify(scorecard_override=scorecard)

    assert any(
        "authority scorecard must select at most one micro-lane candidate" in failure
        for failure in failures
    )


def test_authority_scorecard_requires_documented_no_go_when_none_selected() -> None:
    scorecard = _scorecard_copy()
    scorecard["first_micro_lane_decision"]["status"] = "selected"
    scorecard["first_micro_lane_decision"]["selected_candidate_id"] = None
    scorecard["first_micro_lane_decision"]["no_go_reason"] = None
    scorecard["first_micro_lane_decision"]["smallest_next_safe_action"] = ""

    failures = verify(scorecard_override=scorecard)

    assert any(
        "authority scorecard with no selected candidate requires no_go decision"
        in failure
        for failure in failures
    )
    assert any(
        "no_go authority decision requires no_go_reason" in failure
        for failure in failures
    )
    assert any(
        "no_go authority decision requires smallest_next_safe_action" in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_ui_status_binding_for_rank2_status_route() -> (
    None
):
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    modules["settings"].pop("ui_status_binding")

    failures = verify(manifest_override=manifest)

    assert any(
        "settings rank 2+ backend status route requires ui_status_binding" in failure
        for failure in failures
    )


def test_operational_maturity_verifier_rejects_undocumented_backend_only_status() -> (
    None
):
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    binding = modules["local_models"]["ui_status_binding"]
    binding["backend_only_status"] = True
    binding["backend_only_reason"] = None
    binding["backend_only_doc_ref"] = None
    binding["backend_only_blocker_ref"] = None

    failures = verify(manifest_override=manifest)

    assert any(
        "local_models backend-only status binding requires backend_only_reason"
        in failure
        for failure in failures
    )
    assert any(
        "local_models backend-only status binding requires backend_only_doc_ref"
        in failure
        for failure in failures
    )
    assert any(
        "local_models backend-only status binding requires backend_only_blocker_ref"
        in failure
        for failure in failures
    )


def test_operational_maturity_verifier_accepts_documented_backend_only_status() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    binding = modules["local_models"]["ui_status_binding"]
    binding["backend_only_status"] = True
    binding["backend_only_reason"] = (
        "Backend status is intentionally hidden until the product surface is scoped."
    )
    binding["backend_only_doc_ref"] = "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
    binding["backend_only_blocker_ref"] = "docs/kanban/founder_command_center_board.md"
    binding["frontend_endpoint_ref"] = None
    binding["frontend_client_ref"] = None
    binding["frontend_type_ref"] = None
    binding["frontend_component_refs"] = []
    binding["frontend_test_refs"] = []
    binding["stale_language_scan_refs"] = []

    assert verify(manifest_override=manifest) == []


def test_operational_maturity_stale_language_scan_is_module_scoped() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "surface.tsx"
        source.write_text(
            """
const SURFACE_CONFIGS = {
  Models: {
    summary: "Backend-owned status is surfaced.",
  },
  Settings: {
    summary: "Blocked: settings routes not implemented",
  },
};
""",
            encoding="utf-8",
        )
        failures: list[str] = []

        _append_stale_language_scan_failures(
            failures,
            root,
            "local_models",
            ["surface.tsx::Models:"],
        )
        assert failures == []

        _append_stale_language_scan_failures(
            failures,
            root,
            "settings",
            ["surface.tsx::Settings:"],
        )
        assert any(
            "settings stale UI/backend status language" in failure
            for failure in failures
        )


def test_operational_maturity_module_scan_uses_supplied_root() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "surface.tsx"
        source.write_text(
            """
const SURFACE_CONFIGS = {
  Settings: {
    summary: "Blocked: settings routes not implemented",
  },
};
""",
            encoding="utf-8",
        )
        manifest = {
            "modules": [
                {
                    "module_id": "settings",
                    "role": "support",
                    "primary_surface": "Settings",
                    "current_rank": 2,
                    "current_rank_label": "proposal_review",
                    "next_target_rank": 2,
                    "honest_status": "Backend status exists.",
                    "smallest_next_operational_action": "Keep status surfaced.",
                    "backend_routes": ["GET /control-center/settings/status"],
                    "ui_status_binding": {
                        "surface": "Settings",
                        "status_route_ref": "GET /control-center/settings/status",
                        "frontend_endpoint_ref": "surface.tsx::Settings",
                        "frontend_client_ref": "surface.tsx::Settings",
                        "frontend_type_ref": "surface.tsx::Settings",
                        "frontend_component_refs": ["surface.tsx::Settings:"],
                        "frontend_test_refs": ["surface.tsx::Settings:"],
                        "backend_only_status": False,
                        "backend_only_reason": None,
                        "backend_only_doc_ref": None,
                        "backend_only_blocker_ref": None,
                        "stale_language_scan_refs": ["surface.tsx::Settings:"],
                    },
                }
            ]
        }
        routes_by_ref = {
            "GET /control-center/settings/status": {
                "method": "GET",
                "path": "/control-center/settings/status",
                "route_classification": "local_readonly",
                "side_effect_class": "validation_only",
                "protected_route": True,
                "idempotency_required": False,
            }
        }
        failures: list[str] = []

        _append_module_failures(failures, manifest, routes_by_ref, root)

        assert any(
            "settings stale UI/backend status language" in failure
            for failure in failures
        )
        assert not any("missing path surface.tsx" in failure for failure in failures)


def test_operational_maturity_verifier_rejects_authoritative_action_mock_fixture() -> (
    None
):
    with TemporaryDirectory() as directory:
        root = Path(directory)
        fixture = root / "apps/control-center/src/mocks/controlCenterData.ts"
        fixture.parent.mkdir(parents=True)
        fixture.write_text(
            """
export const mockControlCenterData = {
  founderActionsInbox: {
    items: [{
      status: "receipt_recorded",
      action_group_id: "receipt_recorded",
      local_task_commit_eligible: true,
      local_task_commit_receipt_ref: "receipt:founder-loop-local-task:mock",
      approval_envelope: {
        source: "python_core_action_inbox_read_model" as const,
        backend_owned: true,
      },
      receipt_visibility: {
        source: "mock_fallback_non_authoritative" as const,
        backend_owned: false,
        local_task_commit_receipt_ref: "receipt:founder-loop-local-task:mock",
        replay_posture: "idempotency_replay_available",
        conflict_posture: "conflicting_idempotency_payload_rejected",
        evidence_timeline_event_ref:
          "evidence-timeline-event:local-task:mock",
      },
    }],
  },
};
""",
            encoding="utf-8",
        )
        failures: list[str] = []

        _append_mock_fallback_fixture_failures(failures, root)

        assert any(
            "mock fallback must not claim python_core_action_inbox_read_model"
            in failure
            for failure in failures
        )
        assert any(
            "mock fallback must not claim local_task_commit_eligible true" in failure
            for failure in failures
        )
        assert any(
            "mock fallback must not claim committed local task receipt refs" in failure
            for failure in failures
        )
        assert any(
            "mock fallback must not claim receipt_recorded local task state" in failure
            for failure in failures
        )
        assert any(
            "mock fallback must not claim backend local task replay posture" in failure
            for failure in failures
        )
        assert any(
            "mock fallback must not claim backend local task conflict posture" in failure
            for failure in failures
        )


def test_operational_maturity_verifier_rejects_authoritative_source_readiness_mock_fixture() -> (
    None
):
    with TemporaryDirectory() as directory:
        root = Path(directory)
        fixture = root / "apps/control-center/src/mocks/controlCenterData.ts"
        fixture.parent.mkdir(parents=True)
        fixture.write_text(
            """
const sourceReadinessPosture = {
  source: "python_core_source_readiness_read_model" as const,
  backend_owned: true,
};

const sourceReadinessProposalCandidates = [
  {
    source: "mock_fallback_non_authoritative" as const,
    backend_owned: true,
  },
];

export const mockControlCenterData = {
  founderSourceReadiness: {
    source: "python_core_source_readiness_read_model" as const,
    backend_owned: true,
    source_readiness_proposal_candidates: sourceReadinessProposalCandidates,
  },
  founderToday: {
    source_readiness_posture: sourceReadinessPosture,
  },
};
""",
            encoding="utf-8",
        )
        failures: list[str] = []

        _append_mock_fallback_fixture_failures(failures, root)

        assert any(
            "mock fallback must not claim backend-owned source readiness read models"
            in failure
            for failure in failures
        )
        assert any(
            "mock fallback source readiness posture must not claim backend_owned true"
            in failure
            for failure in failures
        )
        assert any(
            "mock fallback source readiness proposals must not be backend-owned"
            in failure
            for failure in failures
        )


def _manifest_copy() -> dict:
    return deepcopy(load_json(MANIFEST_PATH))


def _scorecard_copy() -> dict:
    return deepcopy(load_json(AUTHORITY_SCORECARD_PATH))
