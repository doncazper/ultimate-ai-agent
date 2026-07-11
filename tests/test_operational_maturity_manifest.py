from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.verify_operational_maturity import (
    AUTHORITY_SCORECARD_PATH,
    AUTHORITY_TIER_DOC_REF,
    CONTEXT_INJECTION_CANDIDATE_ID,
    CONTEXT_INJECTION_CLI_REF,
    CONTEXT_INJECTION_CONTRACT_DOC_REF,
    CONTEXT_INJECTION_REQUIRED_BLOCKED_AUTHORITIES,
    CONTEXT_INJECTION_REQUIRED_TEST_REFS,
    CONTEXT_INJECTION_REQUIRED_VERIFIER_REFS,
    CONTEXT_PACK_PREVIEW_CLI_REF,
    EXPECTED_POLICY_DECISIONS,
    EXPECTED_AUTHORITY_CANDIDATES,
    EXPECTED_AUTHORITY_FOUNDATIONS,
    EXPECTED_FOLLOW_ON_CANDIDATE_RANKING,
    FIRST_IMPLEMENTATION_LANE_ID,
    FIRST_IMPLEMENTATION_PROMPT_REF,
    FIRST_IMPLEMENTATION_REQUIRED_ALLOWED_SCOPE,
    FIRST_IMPLEMENTATION_REQUIRED_BLOCKED_AUTHORITIES,
    FIRST_IMPLEMENTATION_REQUIRED_VERIFICATION_REFS,
    EXPECTED_USABLE_AUTHORITY_TIERS,
    LADDER_LABELS,
    LEGACY_LANE_STATUS,
    LOW_FRICTION_TIER_IDS,
    LOCAL_TASK_AUTHORITY_CAPABILITY_ID,
    LOCAL_TASK_AUTHORITY_CAPABILITY_REF,
    LOCAL_TASK_AUTHORITY_DOMAIN_REF,
    LOCAL_TASK_AUTHORITY_LEASE_REQUIREMENT_REF,
    LOCAL_TASK_AUTHORITY_MODE_REF,
    LOCAL_MODEL_CLI_REF,
    LOCAL_TASK_REPEATABILITY_GATE_REF,
    LOCAL_TASK_REPEATABILITY_REQUIRED_FOCUSED_TEST_REFS,
    LOCAL_TASK_REPEATABILITY_REQUIRED_FRONTEND_TEST_REFS,
    LOCAL_TASK_REPEATABILITY_REQUIRED_VERIFIER_REFS,
    LOCAL_TASK_ROLLBACK_REF,
    LOCAL_TASK_SAFE_DISABLE_REF,
    MANIFEST_PATH,
    MEMORY_CONTEXT_PACK_ROUTE,
    MEMORY_CONTEXT_PACK_PREVIEW_ROUTE,
    MEMORY_CONTEXT_MANIFEST_ROUTE,
    MEMORY_CONTEXT_PACK_TEST_REFS,
    MEMORY_CONTEXT_PACK_VERIFIER_REFS,
    MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_CAPABILITY_ID,
    MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_CAPABILITY_REF,
    MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_DOMAIN_REF,
    MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_LEASE_REQUIREMENT_REF,
    MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_MODE_REF,
    PATCH_WORKBENCH_APPLY_ROUTE,
    PATCH_WORKBENCH_MODULE_ID,
    PATCH_WORKBENCH_REQUIRED_MISSING_CONTRACTS,
    SCHEMA_PATH,
    TIER_LOW_FRICTION_FORBIDDEN_CLAIMS,
    TIER_MODEL_REQUIRED_GUARDRAILS,
    _append_authority_tier_model_failures,
    _append_local_model_manifest_failures,
    _append_memory_context_pack_manifest_failures,
    _append_patch_workbench_manifest_failures,
    _append_module_failures,
    _append_read_only_status_probe_failures,
    _append_stale_language_scan_failures,
    verify_contracts,
)
from scripts.verification.repo import load_json


def test_operational_maturity_manifest_declares_canonical_ladder() -> None:
    manifest = load_json(MANIFEST_PATH)
    schema = load_json(SCHEMA_PATH)
    modules = {module["module_id"]: module for module in manifest["modules"]}

    assert manifest["schema_version"] == "uaa-control-center-operational-maturity.v1"
    assert manifest["authority_tier_doc_ref"] == AUTHORITY_TIER_DOC_REF
    authority_contract = manifest["authority_capability_contract"]
    assert authority_contract["canonical_authority_source"] == "authority_capabilities"
    assert authority_contract["legacy_lane_posture"] == LEGACY_LANE_STATUS
    assert authority_contract["default_unknown_authority_decision"] == "deny"
    assert set(authority_contract["policy_decisions"]) == EXPECTED_POLICY_DECISIONS
    assert authority_contract["lease_evaluation_required"] is True
    assert "AuthorityLease" in authority_contract["operator_copy_rule"]
    assert schema["$defs"]["rank"]["minimum"] == 0
    assert schema["$defs"]["rank"]["maximum"] == 7
    assert "authority_tier_model" in schema["$defs"]
    assert "authority_capability_contract" in schema["$defs"]
    assert "authority_capability" in schema["$defs"]
    assert "authority_capability_contract" in schema["required"]
    assert "authority_capabilities" in schema["$defs"]["module"]["required"]
    assert "graduated_lanes" not in schema["$defs"]["module"]["required"]
    assert "graduated_lanes" not in schema["$defs"]["module"]["properties"]
    assert "lane" not in schema["$defs"]
    assert all("graduated_lanes" not in module for module in modules.values())
    assert "policy_decisions" in schema["$defs"]["authority_capability"]["required"]
    assert "blocked_authorities" in schema["$defs"]["authority_capability"]["required"]
    assert (
        "legacy_lane_id"
        not in schema["$defs"]["authority_capability"]["required"]
    )
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
    local_task_capability = modules["action_inbox"]["authority_capabilities"][0]
    assert local_task_capability["capability_id"] == LOCAL_TASK_AUTHORITY_CAPABILITY_ID
    assert local_task_capability["legacy_lane_id"] == "local_task_create"
    assert set(local_task_capability["policy_decisions"]) == EXPECTED_POLICY_DECISIONS
    assert (
        local_task_capability["authority_domain_ref"] == LOCAL_TASK_AUTHORITY_DOMAIN_REF
    )
    assert (
        local_task_capability["authority_capability_ref"]
        == LOCAL_TASK_AUTHORITY_CAPABILITY_REF
    )
    assert local_task_capability["required_mode_ref"] == LOCAL_TASK_AUTHORITY_MODE_REF
    assert (
        local_task_capability["authority_lease_requirement_ref"]
        == LOCAL_TASK_AUTHORITY_LEASE_REQUIREMENT_REF
    )
    assert local_task_capability["active_lease_required"] is True
    assert (
        local_task_capability["repeatability_gate_ref"]
        == LOCAL_TASK_REPEATABILITY_GATE_REF
    )
    assert LOCAL_TASK_REPEATABILITY_REQUIRED_FOCUSED_TEST_REFS.issubset(
        set(local_task_capability["focused_test_refs"])
    )
    assert LOCAL_TASK_REPEATABILITY_REQUIRED_FRONTEND_TEST_REFS.issubset(
        set(local_task_capability["frontend_repeatability_test_refs"])
    )
    assert LOCAL_TASK_REPEATABILITY_REQUIRED_VERIFIER_REFS.issubset(
        set(local_task_capability["verifier_repeatability_refs"])
    )
    assert "rollback_execution" in local_task_capability["blocked_authorities"]
    assert "AuthorityLease" in local_task_capability["operator_copy"]
    assert MEMORY_CONTEXT_PACK_ROUTE in modules["memory"]["backend_routes"]
    assert MEMORY_CONTEXT_PACK_PREVIEW_ROUTE in modules["memory"]["backend_routes"]
    assert MEMORY_CONTEXT_MANIFEST_ROUTE in modules["memory"]["backend_routes"]
    assert CONTEXT_INJECTION_CLI_REF in modules["memory"]["cli_or_script_refs"]
    memory_capability = modules["memory"]["authority_capabilities"][0]
    assert (
        memory_capability["capability_id"]
        == MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_CAPABILITY_ID
    )
    assert memory_capability["legacy_lane_id"] == "reviewed_memory_recall_write"
    assert (
        memory_capability["authority_domain_ref"]
        == MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_DOMAIN_REF
    )
    assert (
        memory_capability["authority_capability_ref"]
        == MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_CAPABILITY_REF
    )
    assert (
        memory_capability["required_mode_ref"]
        == MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_MODE_REF
    )
    assert (
        memory_capability["authority_lease_requirement_ref"]
        == MEMORY_REVIEWED_RECALL_WRITE_AUTHORITY_LEASE_REQUIREMENT_REF
    )
    assert memory_capability["active_lease_required"] is True
    assert set(memory_capability["policy_decisions"]) == EXPECTED_POLICY_DECISIONS
    assert "AuthorityLease" in memory_capability["operator_copy"]
    assert CONTEXT_PACK_PREVIEW_CLI_REF in modules["memory"]["cli_or_script_refs"]
    assert CONTEXT_INJECTION_REQUIRED_BLOCKED_AUTHORITIES.issubset(
        set(modules["memory"]["blocked_authorities"])
    )
    assert MEMORY_CONTEXT_PACK_TEST_REFS.issubset(set(modules["memory"]["test_refs"]))
    assert MEMORY_CONTEXT_PACK_VERIFIER_REFS.issubset(
        set(modules["memory"]["verifier_refs"])
    )
    assert LOCAL_MODEL_CLI_REF in modules["local_models"]["cli_or_script_refs"]


def test_operational_maturity_manifest_declares_usable_authority_tiers() -> None:
    manifest = load_json(MANIFEST_PATH)
    model = manifest["authority_tier_model"]
    tiers = {tier["tier"]: tier for tier in model["tiers"]}

    assert set(tiers) == set(EXPECTED_USABLE_AUTHORITY_TIERS)
    assert {tier["tier_id"] for tier in model["tiers"]} == set(
        EXPECTED_USABLE_AUTHORITY_TIERS.values()
    )
    assert model["guardrails"].keys() >= TIER_MODEL_REQUIRED_GUARDRAILS
    assert all(
        model["guardrails"][key] is True for key in TIER_MODEL_REQUIRED_GUARDRAILS
    )
    for tier in model["tiers"]:
        if tier["tier_id"] in LOW_FRICTION_TIER_IDS:
            assert "No approval" in tier["approval_posture"]
            assert TIER_LOW_FRICTION_FORBIDDEN_CLAIMS.issubset(
                set(tier["blocked_claims"])
            )


def test_operational_maturity_rejects_low_friction_tier_runtime_claims() -> None:
    manifest = _manifest_copy()
    model = manifest["authority_tier_model"]
    for tier in model["tiers"]:
        if tier["tier_id"] in LOW_FRICTION_TIER_IDS:
            tier["approval_posture"] = "Exact approval required for every view."
            tier["blocked_claims"] = [
                claim
                for claim in tier["blocked_claims"]
                if claim != "provider_model_call"
            ]
    model["guardrails"]["draft_available_does_not_mean_send_available"] = False
    failures: list[str] = []

    _append_authority_tier_model_failures(failures, manifest, MANIFEST_PATH.parents[2])

    assert any("must stay low-friction/no-approval" in failure for failure in failures)
    assert any("must block provider_model_call" in failure for failure in failures)
    assert any(
        "authority tier model guardrail missing draft_available_does_not_mean_send_available"
        in failure
        for failure in failures
    )


def test_operational_maturity_gate_docs_exist() -> None:
    for path in [
        MANIFEST_PATH,
        SCHEMA_PATH,
        AUTHORITY_SCORECARD_PATH,
        Path(AUTHORITY_TIER_DOC_REF),
    ]:
        assert Path(path).exists()


def test_operational_maturity_verifier_requires_local_task_posture_refs() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    capability = modules["action_inbox"]["authority_capabilities"][0]
    capability["rollback_or_safe_disable_refs"] = []

    failures = verify_contracts(manifest_override=manifest)

    posture_failure = (
        "action_inbox:authority-capability:action-inbox:local-task-create "
        "authority capability requires posture refs"
    )
    assert any(
        posture_failure in failure for failure in failures
    )
    assert any(
        f"local_task_create authority capability missing {LOCAL_TASK_ROLLBACK_REF}"
        in failure
        for failure in failures
    )
    assert any(
        f"local_task_create authority capability missing {LOCAL_TASK_SAFE_DISABLE_REF}"
        in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_authority_capability_mapping() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    modules["action_inbox"]["authority_capabilities"] = []
    modules["memory"]["authority_capabilities"][0]["authority_domain_ref"] = (
        "authority-domain-ref:workspace"
    )

    failures = verify_contracts(manifest_override=manifest)

    assert any(
        "Action Inbox local_task_create authority capability missing" in failure
        for failure in failures
    )
    assert any(
        "memory reviewed recall-write authority capability authority_domain_ref drifted"
        in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_authority_capability_contract() -> None:
    manifest = _manifest_copy()
    manifest["authority_capability_contract"][
        "default_unknown_authority_decision"
    ] = "ask"
    manifest["authority_capability_contract"]["policy_decisions"] = [
        "allow",
        "ask",
        "deny",
    ]

    failures = verify_contracts(manifest_override=manifest)

    assert any(
        "authority capability contract must deny unknown authority by default"
        in failure
        for failure in failures
    )
    assert any(
        "authority capability contract policy decisions drifted" in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_capability_policy_decisions() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    modules["action_inbox"]["authority_capabilities"][0]["policy_decisions"] = [
        "allow",
        "ask",
        "deny",
    ]

    failures = verify_contracts(manifest_override=manifest)

    assert any(
        "action_inbox:authority-capability:action-inbox:local-task-create "
        "authority capability policy decisions drifted"
        in failure
        for failure in failures
    )
    assert any(
        "local_task_create authority capability policy decisions drifted" in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_local_task_repeatability_gate() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    capability = modules["action_inbox"]["authority_capabilities"][0]
    capability["repeatability_gate_ref"] = None
    capability["focused_test_refs"] = []
    capability["frontend_repeatability_test_refs"] = []
    capability["verifier_repeatability_refs"] = []

    failures = verify_contracts(manifest_override=manifest)

    assert any(
        "local_task_create authority capability must declare FCC-ACTION-002"
        in failure
        for failure in failures
    )
    assert any(
        "local_task_create repeatability gate missing tests/test_fcc_v1_003_founder_loop_vertical_slice.py::test_founder_loop_cli_commits_local_task_with_safe_refs"
        in failure
        for failure in failures
    )
    assert any(
        "local_task_create repeatability gate missing frontend test apps/control-center/src/App.test.tsx::commits only the eligible Action Inbox local-task create lane through the typed route"
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
    capability = modules["action_inbox"]["authority_capabilities"][0]
    capability["rollback_or_safe_disable_refs"] = []

    failures = verify_contracts(manifest_override=manifest)

    assert any(
        "action_inbox:authority-capability:action-inbox:local-task-create "
        "authority capability requires posture refs"
        in failure
        for failure in failures
    )
    assert any(
        "local_task_create authority capability missing "
        f"{LOCAL_TASK_SAFE_DISABLE_REF}"
        in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_rollback_execution_blocked() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    capability = modules["action_inbox"]["authority_capabilities"][0]
    capability["blocked_authorities"] = [
        authority
        for authority in capability["blocked_authorities"]
        if authority != "rollback_execution"
    ]

    failures = verify_contracts(manifest_override=manifest)

    assert any(
        "local_task_create authority capability must keep rollback_execution blocked"
        in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_memory_context_pack_refs() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    memory = modules["memory"]
    memory["backend_routes"] = [
        route
        for route in memory["backend_routes"]
        if route not in {MEMORY_CONTEXT_PACK_ROUTE, MEMORY_CONTEXT_PACK_PREVIEW_ROUTE}
    ]
    memory["test_refs"] = [
        ref for ref in memory["test_refs"] if ref not in MEMORY_CONTEXT_PACK_TEST_REFS
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
        f"memory context-pack readiness missing route {MEMORY_CONTEXT_PACK_PREVIEW_ROUTE}"
        in failure
        for failure in failures
    )
    assert any(
        "memory context-pack readiness missing test" in failure for failure in failures
    )
    assert any(
        "memory context-pack readiness missing verifier" in failure
        for failure in failures
    )


def test_operational_maturity_verifier_rejects_patch_apply_claim_without_gates() -> (
    None
):
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    patch = modules[PATCH_WORKBENCH_MODULE_ID]
    patch["current_rank"] = 4
    patch["current_rank_label"] = "execution_ready_contract"
    patch["honest_status"] = "execution_ready_contract"
    patch["missing_contracts"] = []
    patch["backend_routes"] = [
        route
        for route in patch["backend_routes"]
        if route != PATCH_WORKBENCH_APPLY_ROUTE
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

    assert any(
        "must keep apply_blocked honest_status" in failure for failure in failures
    )
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


def test_authority_candidate_scorecard_declares_memory_write_graduation() -> None:
    scorecard = load_json(AUTHORITY_SCORECARD_PATH)

    assert (
        scorecard["schema_version"]
        == "uaa-control-center-authority-candidate-scorecard.v2"
    )
    assert scorecard["status"] == "active authority candidate scorecard"
    assert {
        lane["foundation_id"] for lane in scorecard["proposal_foundation"]
    } == EXPECTED_AUTHORITY_FOUNDATIONS
    first_lane = scorecard["first_implementation_lane"]
    assert first_lane["lane_id"] == FIRST_IMPLEMENTATION_LANE_ID
    assert first_lane["prompt_ref"] == FIRST_IMPLEMENTATION_PROMPT_REF
    assert first_lane["foundation_ref"] == FIRST_IMPLEMENTATION_LANE_ID
    assert first_lane["status"] == "implemented"
    assert FIRST_IMPLEMENTATION_REQUIRED_ALLOWED_SCOPE.issubset(
        set(first_lane["allowed_scope"])
    )
    assert FIRST_IMPLEMENTATION_REQUIRED_BLOCKED_AUTHORITIES.issubset(
        set(first_lane["blocked_authorities"])
    )
    assert FIRST_IMPLEMENTATION_REQUIRED_VERIFICATION_REFS.issubset(
        set(first_lane["verification_refs"])
    )
    assert {
        candidate["candidate_id"] for candidate in scorecard["authority_candidates"]
    } == EXPECTED_AUTHORITY_CANDIDATES
    ranking = scorecard["follow_on_candidate_ranking"]
    assert ranking["status"] == "ranked_with_selected_authority_capability"
    assert ranking["fixed_first_lane_ref"] == FIRST_IMPLEMENTATION_LANE_ID
    assert (
        tuple(ranking["ranked_candidate_ids"]) == EXPECTED_FOLLOW_ON_CANDIDATE_RANKING
    )
    assert ranking["safest_candidate_id"] == EXPECTED_FOLLOW_ON_CANDIDATE_RANKING[0]
    assert ranking["safest_candidate_status"] == "implemented"
    assert ranking["no_authority_granted"] is False
    assert "memory_write" in ranking["selection_blocked_reason"]
    selected = [
        candidate
        for candidate in scorecard["authority_candidates"]
        if candidate["selected_for_authority_capability"] is True
    ]
    assert [candidate["candidate_id"] for candidate in selected] == ["memory_write"]
    assert selected[0]["status"] == "implemented"
    assert (
        "scripts/dev/uaa_founder_loop.py"
        in selected[0]["prerequisite_refs"]["cli_api_core_parity_refs"]
    )
    assert scorecard["first_authority_capability_decision"]["status"] == "selected"
    assert (
        scorecard["first_authority_capability_decision"]["selected_candidate_id"]
        == "memory_write"
    )
    assert (
        scorecard["first_authority_capability_decision"]["decision_ref"]
        == "decision-ref:fcc-auth-ramp-002:memory-write-reviewed-recall-capability"
    )
    assert scorecard["first_authority_capability_decision"]["no_go_reason"] is None
    assert "local_task_create" not in {
        candidate["candidate_id"] for candidate in scorecard["authority_candidates"]
    }
    assert FIRST_IMPLEMENTATION_LANE_ID not in {
        candidate["candidate_id"] for candidate in scorecard["authority_candidates"]
    }


def test_authority_scorecard_declares_context_injection_contract_ready_only() -> None:
    scorecard = load_json(AUTHORITY_SCORECARD_PATH)
    context = next(
        candidate
        for candidate in scorecard["authority_candidates"]
        if candidate["candidate_id"] == CONTEXT_INJECTION_CANDIDATE_ID
    )

    assert context["status"] == "contract_ready"
    assert context["selected_for_authority_capability"] is False
    refs = context["prerequisite_refs"]
    assert refs["backend_core_owner_ref"] == CONTEXT_INJECTION_CONTRACT_DOC_REF
    assert refs["route_side_effect_ref"] == MEMORY_CONTEXT_MANIFEST_ROUTE
    assert refs["exact_scope_ref"].startswith(CONTEXT_INJECTION_CONTRACT_DOC_REF)
    assert CONTEXT_INJECTION_CLI_REF in refs["cli_api_core_parity_refs"]
    assert CONTEXT_INJECTION_REQUIRED_TEST_REFS.issubset(set(refs["focused_test_refs"]))
    assert CONTEXT_INJECTION_REQUIRED_VERIFIER_REFS.issubset(set(refs["verifier_refs"]))
    assert CONTEXT_INJECTION_REQUIRED_BLOCKED_AUTHORITIES.issubset(
        set(context["blocked_authorities"])
    )


def test_authority_scorecard_rejects_context_injection_selection_or_missing_contract_refs() -> (
    None
):
    scorecard = _scorecard_copy()
    context = next(
        candidate
        for candidate in scorecard["authority_candidates"]
        if candidate["candidate_id"] == CONTEXT_INJECTION_CANDIDATE_ID
    )
    context["selected_for_authority_capability"] = True
    context["prerequisite_refs"]["exact_scope_ref"] = None
    context["prerequisite_refs"]["cli_api_core_parity_refs"] = []
    context["blocked_authorities"] = [
        authority
        for authority in context["blocked_authorities"]
        if authority != "runtime_prompt_context_injection"
    ]

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        "context_injection must remain unselected" in failure for failure in failures
    )
    assert any(
        "context_injection contract_ready requires exact_scope_ref" in failure
        for failure in failures
    )
    assert any(
        "context_injection missing memory-context-manifest CLI ref" in failure
        for failure in failures
    )
    assert any(
        "context_injection must block runtime_prompt_context_injection" in failure
        for failure in failures
    )


def test_operational_maturity_rejects_context_injection_authority_capability() -> None:
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    memory = modules["memory"]
    memory["authority_capabilities"].append(
        {
            "capability_id": "authority-capability:memory:context-injection",
            "legacy_lane_id": "context_injection",
            "rank": 5,
            "honest_status": "runtime_context_injection",
            "authority_domain_ref": "authority-domain-ref:memory",
            "authority_capability_ref": "authority-capability-ref:execute",
            "required_mode_ref": "authority-mode-ref:ask-before-changes",
            "authority_lease_requirement_ref": (
                "authority-lease-requirement-ref:memory-context-injection:memory:execute"
            ),
            "lease_scope": "session",
            "active_lease_required": True,
            "exact_approval_required": True,
            "idempotency_required": True,
            "receipts_required": True,
            "audit_required": True,
            "redaction_required": True,
            "policy_decisions": list(EXPECTED_POLICY_DECISIONS),
            "backend_routes": [MEMORY_CONTEXT_MANIFEST_ROUTE],
            "receipt_refs": ["receipt:context-injection:*"],
            "evidence_refs": ["evidence-ref:context-injection"],
            "blocked_authorities": [],
            "rollback_or_safe_disable_refs": [
                "rollback-ref:context-injection:test",
                "safe-disable-ref:context-injection:test",
            ],
            "cli_parity_ref": CONTEXT_INJECTION_CLI_REF,
            "focused_test_refs": list(CONTEXT_INJECTION_REQUIRED_TEST_REFS),
            "operator_copy": (
                "Context injection would require an active AuthorityLease and remains blocked."
            ),
        }
    )

    failures: list[str] = []
    _append_memory_context_pack_manifest_failures(failures, memory)

    context_injection_failure = (
        "memory must not mark context_injection as implemented authority capability"
    )
    assert any(
        context_injection_failure in failure for failure in failures
    )


def test_authority_scorecard_rejects_missing_first_implementation_lane() -> None:
    scorecard = _scorecard_copy()
    scorecard.pop("first_implementation_lane")

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        "authority scorecard requires first_implementation_lane" in failure
        for failure in failures
    )


def test_authority_scorecard_rejects_first_lane_as_follow_on_candidate() -> None:
    scorecard = _scorecard_copy()
    scorecard["authority_candidates"][0]["candidate_id"] = FIRST_IMPLEMENTATION_LANE_ID

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        "fixed first implementation lane must not be a follow-on authority candidate"
        in failure
        for failure in failures
    )


def test_authority_scorecard_rejects_first_lane_in_follow_on_ranking() -> None:
    scorecard = _scorecard_copy()
    scorecard["follow_on_candidate_ranking"]["ranked_candidate_ids"][0] = (
        FIRST_IMPLEMENTATION_LANE_ID
    )

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        "follow-on candidate ranking order drifted" in failure for failure in failures
    )
    assert any(
        "follow-on ranking must not include the fixed first lane" in failure
        for failure in failures
    )


def test_authority_scorecard_rejects_ranking_authority_claim() -> None:
    scorecard = _scorecard_copy()
    memory = next(
        candidate
        for candidate in scorecard["authority_candidates"]
        if candidate["candidate_id"] == "memory_write"
    )
    memory["status"] = "proposal_only_ready"
    memory["selected_for_authority_capability"] = False
    scorecard["follow_on_candidate_ranking"]["status"] = "ranked_no_authority_granted"
    scorecard["follow_on_candidate_ranking"]["safest_candidate_status"] = (
        "proposal_only_ready"
    )
    scorecard["follow_on_candidate_ranking"]["no_authority_granted"] = False
    scorecard["first_authority_capability_decision"]["status"] = "no_go"
    scorecard["first_authority_capability_decision"]["selected_candidate_id"] = None
    scorecard["first_authority_capability_decision"]["no_go_reason"] = (
        "memory_write remains proposal_only_ready until exact scope, "
        "LocalApprovalAuthority, rollback/safe-disable, CLI parity, and tests exist."
    )

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        "follow-on ranking must not grant authority" in failure for failure in failures
    )


def test_authority_scorecard_rejects_duplicate_or_missing_follow_on_ranking_ids() -> (
    None
):
    scorecard = _scorecard_copy()
    ranked_ids = scorecard["follow_on_candidate_ranking"]["ranked_candidate_ids"]
    ranked_ids[-1] = ranked_ids[0]

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        "follow-on candidate ranking order drifted" in failure for failure in failures
    )
    assert any(
        "follow-on ranking contains duplicate candidates" in failure
        for failure in failures
    )


def test_authority_scorecard_rejects_mismatched_safest_candidate() -> None:
    scorecard = _scorecard_copy()
    scorecard["follow_on_candidate_ranking"]["safest_candidate_id"] = (
        "context_injection"
    )

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        "follow-on ranking safest candidate must match rank 1" in failure
        for failure in failures
    )


def test_authority_scorecard_rejects_mismatched_safest_candidate_status() -> None:
    scorecard = _scorecard_copy()
    scorecard["follow_on_candidate_ranking"]["safest_candidate_status"] = (
        "authority_capability_candidate"
    )

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        "follow-on ranking safest candidate status drifted" in failure
        for failure in failures
    )


def test_authority_scorecard_rejects_first_lane_missing_blockers() -> None:
    scorecard = _scorecard_copy()
    first_lane = scorecard["first_implementation_lane"]
    first_lane["allowed_scope"] = []
    first_lane["blocked_authorities"] = []
    first_lane["verification_refs"] = []
    first_lane["status"] = "partial"
    first_lane["next_safe_action"] = "Pick a different lane."

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        "first implementation lane missing allowed scope https_get_only" in failure
        for failure in failures
    )
    assert any(
        "first implementation lane must block provider_sdk_call" in failure
        for failure in failures
    )
    assert any(
        "first implementation lane missing verification ref tests/test_m72_read_only_http_fetch_tool.py"
        in failure
        for failure in failures
    )
    assert any(
        "first implementation lane next_safe_action must point to Prompt 02" in failure
        for failure in failures
    )


def test_authority_scorecard_rejects_selected_candidate_without_capability_status() -> (
    None
):
    scorecard = _scorecard_copy()
    candidate = scorecard["authority_candidates"][0]
    candidate["selected_for_authority_capability"] = True
    candidate["status"] = "contract_ready"
    scorecard["first_authority_capability_decision"]["status"] = "selected"
    scorecard["first_authority_capability_decision"]["selected_candidate_id"] = (
        candidate["candidate_id"]
    )
    scorecard["first_authority_capability_decision"]["no_go_reason"] = None

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        f"{candidate['candidate_id']} selected authority capability must be authority_capability_candidate or implemented"
        in failure
        for failure in failures
    )


def test_authority_scorecard_rejects_capability_candidate_missing_required_refs() -> (
    None
):
    scorecard = _scorecard_copy()
    for item in scorecard["authority_candidates"]:
        item["selected_for_authority_capability"] = False
        if item["candidate_id"] == "memory_write":
            item["status"] = "contract_ready"
    candidate = scorecard["authority_candidates"][1]
    candidate["status"] = "authority_capability_candidate"
    candidate["selected_for_authority_capability"] = True
    candidate["prerequisite_refs"]["exact_scope_ref"] = None
    candidate["prerequisite_refs"]["rollback_safe_disable_plan_ref"] = None
    candidate["prerequisite_refs"]["cli_api_core_parity_refs"] = []
    scorecard["first_authority_capability_decision"]["status"] = "selected"
    scorecard["first_authority_capability_decision"]["selected_candidate_id"] = (
        candidate["candidate_id"]
    )
    scorecard["first_authority_capability_decision"]["no_go_reason"] = None

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        f"{candidate['candidate_id']} authority capability candidate requires exact_scope_ref"
        in failure
        for failure in failures
    )
    assert any(
        f"{candidate['candidate_id']} authority capability candidate requires rollback_safe_disable_plan_ref"
        in failure
        for failure in failures
    )
    assert any(
        f"{candidate['candidate_id']} authority capability candidate requires cli_api_core_parity_refs"
        in failure
        for failure in failures
    )


def test_authority_scorecard_rejects_multiple_selected_candidates() -> None:
    scorecard = _scorecard_copy()
    for candidate in scorecard["authority_candidates"][:2]:
        candidate["status"] = "authority_capability_candidate"
        candidate["selected_for_authority_capability"] = True
    scorecard["first_authority_capability_decision"]["status"] = "selected"
    scorecard["first_authority_capability_decision"]["selected_candidate_id"] = (
        scorecard["authority_candidates"][0]["candidate_id"]
    )
    scorecard["first_authority_capability_decision"]["no_go_reason"] = None

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        "authority scorecard must select at most one authority capability candidate"
        in failure
        for failure in failures
    )


def test_authority_scorecard_requires_documented_no_go_when_none_selected() -> None:
    scorecard = _scorecard_copy()
    for candidate in scorecard["authority_candidates"]:
        candidate["selected_for_authority_capability"] = False
    scorecard["first_authority_capability_decision"]["status"] = "selected"
    scorecard["first_authority_capability_decision"]["selected_candidate_id"] = None
    scorecard["first_authority_capability_decision"]["no_go_reason"] = None
    scorecard["first_authority_capability_decision"]["smallest_next_safe_action"] = ""

    failures = verify_contracts(scorecard_override=scorecard)

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


def test_authority_scorecard_no_go_must_explain_top_ranked_candidate_blocker() -> None:
    scorecard = _scorecard_copy()
    for candidate in scorecard["authority_candidates"]:
        candidate["selected_for_authority_capability"] = False
    scorecard["first_authority_capability_decision"]["status"] = "no_go"
    scorecard["first_authority_capability_decision"]["selected_candidate_id"] = None
    scorecard["first_authority_capability_decision"]["no_go_reason"] = (
        "No candidate is ready."
    )
    scorecard["first_authority_capability_decision"]["smallest_next_safe_action"] = (
        "Keep planning."
    )

    failures = verify_contracts(scorecard_override=scorecard)

    assert any(
        "no_go authority decision must explain the top-ranked candidate blocker"
        in failure
        for failure in failures
    )
    assert any(
        "no_go authority decision must include the top-ranked candidate status"
        in failure
        for failure in failures
    )
    assert any(
        "no_go authority decision missing blocker fragment exact scope" in failure
        for failure in failures
    )


def test_operational_maturity_verifier_requires_ui_status_binding_for_rank2_status_route() -> (
    None
):
    manifest = _manifest_copy()
    modules = {module["module_id"]: module for module in manifest["modules"]}
    modules["settings"].pop("ui_status_binding")

    failures = verify_contracts(manifest_override=manifest)

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

    failures = verify_contracts(manifest_override=manifest)

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

    assert verify_contracts(manifest_override=manifest) == []


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


def _manifest_copy() -> dict:
    return deepcopy(load_json(MANIFEST_PATH))


def _scorecard_copy() -> dict:
    return deepcopy(load_json(AUTHORITY_SCORECARD_PATH))
