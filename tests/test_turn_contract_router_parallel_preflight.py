from time import perf_counter

import pytest

import ultimate_ai_agent.core.decision_router.parallel_preflight as preflight_module
from ultimate_ai_agent.core.decision_router import (
    PromptProfilePolicy,
    RiskFlag,
    TurnContractKind,
    TurnPreflightArbitrationInput,
    TurnPreflightArbitrationResult,
    TurnPreflightBundle,
    TurnPreflightLaneKind,
    TurnPreflightLaneResult,
    TurnPreflightRunResult,
    run_parallel_turn_preflight,
)


RAW_PROMPT = "How do I build a DIY desk?"


def _lane(
    lane_kind: TurnPreflightLaneKind,
    *,
    lane_result_ref: str | None = None,
    candidate_turn_contract: TurnContractKind | None = TurnContractKind.answer_directly,
) -> TurnPreflightLaneResult:
    return TurnPreflightLaneResult(
        lane_result_ref=lane_result_ref or f"turn-preflight-lane:{lane_kind.value}",
        lane_kind=lane_kind,
        candidate_turn_contract=candidate_turn_contract,
        answer_profile_hint=PromptProfilePolicy.minimal_answer
        if lane_kind == TurnPreflightLaneKind.answer_profile_lane
        else None,
        confidence=0.75,
        safe_summary="Parallel preflight lane produced bounded safe refs only.",
        reason_refs=[f"reason-ref:turn-preflight:{lane_kind.value}"],
        source_refs=[f"source:turn-preflight:{lane_kind.value}"],
        evidence_refs=[f"evidence:turn-preflight:{lane_kind.value}"],
        signal_refs=[f"signal-ref:turn-preflight:{lane_kind.value}"],
        memory_ref_candidates=["memory-ref:turn-preflight:reviewed-office"]
        if lane_kind == TurnPreflightLaneKind.memory_relevance_lane
        else [],
        tool_category_refs=["tool-category:turn-preflight:read-only"]
        if lane_kind == TurnPreflightLaneKind.tool_manifest_lane
        else [],
        risk_flags=[RiskFlag.low_risk],
    )


def test_parallel_preflight_contract_covers_every_lane_kind() -> None:
    assert {lane.value for lane in TurnPreflightLaneKind} == {
        "intent_lane",
        "risk_action_lane",
        "memory_trigger_lane",
        "memory_relevance_lane",
        "tool_manifest_lane",
        "answer_profile_lane",
        "direct_answer_draft",
    }

    for lane_kind in TurnPreflightLaneKind:
        result = _lane(lane_kind)

        assert result.lane_kind == lane_kind.value
        assert result.safe_refs_only is True
        assert result.raw_content_included is False
        assert result.authority_granted is False
        assert result.execution_permitted is False
        assert result.user_visible is False
        assert result.no_runtime_model_call_performed is True
        assert result.no_provider_call_performed is True
        assert result.no_tool_execution_performed is True
        assert result.no_action_execution_performed is True
        assert result.no_workflow_execution_performed is True
        assert result.no_context_injection_performed is True
        assert result.no_memory_content_retrieved is True
        assert result.no_memory_write_performed is True
        assert result.no_durable_state_write_performed is True
        assert result.no_shell_subprocess_performed is True
        assert result.no_browser_network_performed is True
        assert result.no_connector_write_performed is True


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    [
        ("safe_refs_only", False, "safe-ref only"),
        ("raw_content_included", True, "raw content"),
        ("authority_granted", True, "grant authority"),
        ("execution_permitted", True, "permit execution"),
        ("no_runtime_model_call_performed", False, "no-effect proof flag"),
        ("no_provider_call_performed", False, "no-effect proof flag"),
        ("no_tool_execution_performed", False, "no-effect proof flag"),
        ("no_action_execution_performed", False, "no-effect proof flag"),
        ("no_workflow_execution_performed", False, "no-effect proof flag"),
        ("no_context_injection_performed", False, "no-effect proof flag"),
        ("no_memory_content_retrieved", False, "no-effect proof flag"),
        ("no_memory_write_performed", False, "no-effect proof flag"),
        ("no_durable_state_write_performed", False, "no-effect proof flag"),
        ("no_shell_subprocess_performed", False, "no-effect proof flag"),
        ("no_browser_network_performed", False, "no-effect proof flag"),
        ("no_connector_write_performed", False, "no-effect proof flag"),
    ],
)
def test_lane_result_rejects_authority_and_runtime_expansion(
    field_name: str,
    value: object,
    message: str,
) -> None:
    payload = _lane(TurnPreflightLaneKind.risk_action_lane).model_dump(mode="json")
    payload[field_name] = value

    with pytest.raises(ValueError, match=message):
        TurnPreflightLaneResult(**payload)


def test_direct_answer_draft_lane_is_never_user_visible_before_arbitration() -> None:
    payload = _lane(TurnPreflightLaneKind.direct_answer_draft).model_dump(mode="json")
    payload["user_visible"] = True

    with pytest.raises(ValueError, match="direct_answer_draft lane result must not be user-visible"):
        TurnPreflightLaneResult(**payload)

    payload["user_visible"] = False
    payload["direct_answer_draft_visible_to_user"] = True

    with pytest.raises(ValueError, match="direct_answer_draft cannot be visible"):
        TurnPreflightLaneResult(**payload)


def test_direct_answer_draft_lane_rejects_approval_or_execution_candidate() -> None:
    with pytest.raises(ValueError, match="direct/base answer candidates"):
        _lane(
            TurnPreflightLaneKind.direct_answer_draft,
            candidate_turn_contract=TurnContractKind.approval_required,
        )


def test_preflight_lane_rejects_execute_approved_action_candidate() -> None:
    with pytest.raises(ValueError, match="cannot select execute_approved_action"):
        _lane(
            TurnPreflightLaneKind.intent_lane,
            candidate_turn_contract=TurnContractKind.execute_approved_action,
        )


@pytest.mark.parametrize(
    ("safe_summary", "message"),
    [
        (RAW_PROMPT, "raw turn text"),
        ("api_key=unsafe-example", "unsafe content"),
        ("/" + "Users" + "/example/project", "unsafe content"),
    ],
)
def test_lane_summary_rejects_raw_turn_or_sensitive_content(safe_summary: str, message: str) -> None:
    payload = _lane(TurnPreflightLaneKind.intent_lane).model_dump(mode="json")
    payload["safe_summary"] = safe_summary

    with pytest.raises(ValueError, match=message):
        TurnPreflightLaneResult(**payload)


def test_fixture_request_text_is_not_in_serialized_lane_bundle_or_arbitration() -> None:
    lane_results = [_lane(lane_kind) for lane_kind in TurnPreflightLaneKind]
    bundle = TurnPreflightBundle(
        bundle_ref="turn-preflight-bundle:all-lanes",
        safe_summary="Parallel preflight bundle contains safe refs for all lane outputs.",
        lane_results=lane_results,
        reason_refs=["reason-ref:turn-preflight:bundle"],
        source_refs=["source:turn-preflight:bundle"],
        evidence_refs=["evidence:turn-preflight:bundle"],
    )
    arbitration_input = TurnPreflightArbitrationInput(
        arbitration_input_ref="turn-preflight-arbitration-input:all-lanes",
        bundle=bundle,
        safe_summary="Arbitration input prepared safe lane refs for central selection.",
        candidate_decision_refs=["turn-decision:turn-preflight:candidate"],
    )
    arbitration_result = TurnPreflightArbitrationResult(
        arbitration_result_ref="turn-preflight-arbitration-result:all-lanes",
        arbitration_input_ref=arbitration_input.arbitration_input_ref,
        selected_turn_contract=TurnContractKind.answer_directly,
        selected_decision_ref="turn-decision:turn-preflight:selected",
        selected_policy_ref="policy-ref:turn-preflight:selected",
        confidence=0.8,
        safe_summary="Central arbitration selected one no-effect turn contract.",
        lane_result_refs=[lane.lane_result_ref for lane in lane_results],
        reason_refs=["reason-ref:turn-preflight:arbitrated"],
        evidence_refs=["evidence:turn-preflight:arbitrated"],
    )

    serialized = repr(
        {
            "bundle": bundle.model_dump(mode="json"),
            "arbitration_input": arbitration_input.model_dump(mode="json"),
            "arbitration_result": arbitration_result.model_dump(mode="json"),
        }
    ).lower()

    assert RAW_PROMPT.lower() not in serialized
    assert bundle.authority_granted is False
    assert arbitration_input.execution_permitted is False
    assert arbitration_result.authority_granted is False
    assert arbitration_result.execution_permitted is False


def test_bundle_rejects_duplicate_lane_kinds() -> None:
    with pytest.raises(ValueError, match="duplicate turn preflight lane kind"):
        TurnPreflightBundle(
            bundle_ref="turn-preflight-bundle:duplicate",
            safe_summary="Parallel preflight bundle contains duplicate lane refs.",
            lane_results=[
                _lane(TurnPreflightLaneKind.intent_lane, lane_result_ref="turn-preflight-lane:intent-one"),
                _lane(TurnPreflightLaneKind.intent_lane, lane_result_ref="turn-preflight-lane:intent-two"),
            ],
            reason_refs=["reason-ref:turn-preflight:duplicate"],
            source_refs=["source:turn-preflight:duplicate"],
        )


def test_arbitration_result_only_clears_direct_draft_for_direct_or_base_answer() -> None:
    with pytest.raises(ValueError, match="direct_answer_draft can only be cleared"):
        TurnPreflightArbitrationResult(
            arbitration_result_ref="turn-preflight-arbitration-result:unsafe-clear",
            arbitration_input_ref="turn-preflight-arbitration-input:unsafe-clear",
            selected_turn_contract=TurnContractKind.approval_required,
            selected_decision_ref="turn-decision:turn-preflight:unsafe-clear",
            selected_policy_ref="policy-ref:turn-preflight:unsafe-clear",
            confidence=0.9,
            safe_summary="Central arbitration selected approval posture.",
            lane_result_refs=["turn-preflight-lane:direct_answer_draft"],
            reason_refs=["reason-ref:turn-preflight:unsafe-clear"],
            direct_answer_draft_cleared_for_display=True,
        )


def test_arbitration_result_rejects_execute_approved_action_selection() -> None:
    with pytest.raises(ValueError, match="cannot select execute_approved_action"):
        TurnPreflightArbitrationResult(
            arbitration_result_ref="turn-preflight-arbitration-result:execute",
            arbitration_input_ref="turn-preflight-arbitration-input:execute",
            selected_turn_contract=TurnContractKind.execute_approved_action,
            selected_decision_ref="turn-decision:turn-preflight:execute",
            selected_policy_ref="policy-ref:turn-preflight:execute",
            confidence=0.9,
            safe_summary="Central arbitration denied execution posture.",
            lane_result_refs=["turn-preflight-lane:intent_lane"],
            reason_refs=["reason-ref:turn-preflight:execute-denied"],
        )


def test_arbitration_result_rejects_direct_draft_clearance_with_risk_flags() -> None:
    with pytest.raises(ValueError, match="non-low-risk flags"):
        TurnPreflightArbitrationResult(
            arbitration_result_ref="turn-preflight-arbitration-result:risky-clear",
            arbitration_input_ref="turn-preflight-arbitration-input:risky-clear",
            selected_turn_contract=TurnContractKind.answer_directly,
            selected_decision_ref="turn-decision:turn-preflight:risky-clear",
            selected_policy_ref="policy-ref:turn-preflight:risky-clear",
            confidence=0.9,
            safe_summary="Central arbitration selected direct posture.",
            lane_result_refs=["turn-preflight-lane:direct_answer_draft"],
            reason_refs=["reason-ref:turn-preflight:risky-clear"],
            risk_flags=[RiskFlag.external_side_effect],
            direct_answer_draft_cleared_for_display=True,
        )


def test_parallel_preflight_engine_is_deterministic_for_golden_cases() -> None:
    prompts = [
        ("How do I build a DIY desk?", "answer_directly"),
        ("How do I build a DIY table?", "answer_directly"),
        ("Explain how photosynthesis works.", "answer_directly"),
        ("What is a clean way to organize a closet?", "answer_directly"),
        ("Build me a small Python helper for sorting rows.", "answer_directly"),
        ("Use the base answer path: explain how to sharpen a chisel.", "base_answer"),
        ("Design one for my office using what you know.", "answer_with_reviewed_memory"),
        ("Make me a shopping list for this desk.", "draft_or_plan"),
        ("Find current lumber prices near me.", "prepare_tool_or_action"),
        ("Order the materials.", "approval_required"),
        ("Use my card and book pickup at Home Depot.", "approval_required"),
        ("Ask the base answer path: use my card and order this.", "approval_required"),
    ]

    for index, (prompt, expected_contract) in enumerate(prompts):
        first = run_parallel_turn_preflight(
            prompt,
            run_ref=f"turn-preflight-run:golden-{index}-first",
            decision_ref=f"turn-decision:preflight-golden-{index}",
        )
        second = run_parallel_turn_preflight(
            prompt,
            run_ref=f"turn-preflight-run:golden-{index}-second",
            decision_ref=f"turn-decision:preflight-golden-{index}",
        )

        assert first.turn_decision.turn_contract == expected_contract
        assert second.turn_decision.turn_contract == expected_contract
        assert first.invocation_policy.turn_contract == expected_contract
        assert second.invocation_policy.model_dump(mode="json") == first.invocation_policy.model_dump(mode="json")
        assert first.arbitration_result.selected_turn_contract == expected_contract
        assert first.raw_content_included is False
        assert first.authority_granted is False
        assert first.execution_permitted is False
        assert first.no_runtime_model_call_performed is True
        assert first.no_tool_execution_performed is True
        assert first.no_context_injection_performed is True


def test_risk_lane_veto_overrides_low_ceremony_intent() -> None:
    result = run_parallel_turn_preflight(
        "Ask the base answer path: use my card and order this.",
        run_ref="turn-preflight-run:risk-veto",
        decision_ref="turn-decision:preflight-risk-veto",
    )

    assert result.turn_decision.turn_contract == "approval_required"
    assert result.invocation_policy.approval_required is True
    assert result.invocation_policy.side_effects_allowed is False
    assert result.invocation_policy.tool_execution_allowed is False


def test_memory_lane_does_not_touch_memory_for_ordinary_prompt() -> None:
    result = run_parallel_turn_preflight(
        "How do I build a DIY desk?",
        run_ref="turn-preflight-run:ordinary-memory",
        decision_ref="turn-decision:preflight-ordinary-memory",
    )
    lanes = {lane.lane_kind: lane for lane in result.bundle.lane_results}

    assert lanes["memory_trigger_lane"].candidate_turn_contract == "answer_directly"
    assert lanes["memory_relevance_lane"].memory_ref_candidates == []
    assert result.invocation_policy.memory_scope == "none"
    assert result.invocation_policy.memory_read_allowed is False
    assert result.no_memory_content_retrieved is True


def test_reviewed_memory_preflight_uses_safe_refs_without_memory_retrieval() -> None:
    raw_prompt = "Design one for my office using what you know."
    result = run_parallel_turn_preflight(
        raw_prompt,
        run_ref="turn-preflight-run:reviewed-memory",
        decision_ref="turn-decision:preflight-reviewed-memory",
    )
    lanes = {lane.lane_kind: lane for lane in result.bundle.lane_results}

    assert result.turn_decision.turn_contract == "answer_with_reviewed_memory"
    assert lanes["memory_trigger_lane"].candidate_turn_contract == "answer_with_reviewed_memory"
    assert lanes["memory_relevance_lane"].memory_ref_candidates == [
        "memory-ref:turn-preflight:reviewed-relevance-candidate"
    ]
    assert result.invocation_policy.memory_read_allowed is True
    assert result.invocation_policy_compiled_only is True
    assert result.no_memory_content_retrieved is True
    assert result.no_memory_write_performed is True
    assert result.no_durable_state_write_performed is True
    assert raw_prompt.lower() not in repr(result.model_dump(mode="json")).lower()


def test_tool_manifest_lane_does_not_expose_tools_for_diy_advice() -> None:
    result = run_parallel_turn_preflight(
        "How do I build a DIY table?",
        run_ref="turn-preflight-run:diy-tools",
        decision_ref="turn-decision:preflight-diy-tools",
    )
    tool_lane = next(lane for lane in result.bundle.lane_results if lane.lane_kind == "tool_manifest_lane")

    assert tool_lane.tool_category_refs == []
    assert result.invocation_policy.tools == []
    assert result.invocation_policy.tool_choice == "none"


def test_tool_manifest_lane_keeps_current_info_read_only_or_proposal_only() -> None:
    result = run_parallel_turn_preflight(
        "Find current lumber prices near me.",
        run_ref="turn-preflight-run:current-info",
        decision_ref="turn-decision:preflight-current-info",
    )
    tool_lane = next(lane for lane in result.bundle.lane_results if lane.lane_kind == "tool_manifest_lane")

    assert result.turn_decision.turn_contract == "prepare_tool_or_action"
    assert tool_lane.tool_category_refs == ["tool-category:turn-preflight:read-only-or-proposal"]
    assert result.invocation_policy.tool_policy == "read_only_or_proposal_only"
    assert result.invocation_policy.side_effects_allowed is False
    assert result.invocation_policy.tool_execution_allowed is False


def test_failing_lane_fails_closed_without_expanding_authority(monkeypatch: pytest.MonkeyPatch) -> None:
    original_default_lane_result = preflight_module._default_lane_result

    def failing_default_lane(lane_kind, seed_decision) -> TurnPreflightLaneResult:
        if lane_kind == TurnPreflightLaneKind.intent_lane:
            raise RuntimeError("synthetic lane failure")
        return original_default_lane_result(lane_kind, seed_decision)

    monkeypatch.setattr(preflight_module, "_default_lane_result", failing_default_lane)

    result = run_parallel_turn_preflight(
        "How do I build a DIY desk?",
        run_ref="turn-preflight-run:failed-closed",
        decision_ref="turn-decision:preflight-failed-closed",
    )
    failed_lane = next(lane for lane in result.bundle.lane_results if lane.lane_kind == "intent_lane")

    assert failed_lane.candidate_turn_contract == "approval_required"
    assert "reason-ref:turn-preflight:lane-failed-closed" in failed_lane.reason_refs
    assert result.turn_decision.turn_contract == "approval_required"
    assert result.invocation_policy.side_effects_allowed is False
    assert result.invocation_policy.action_execution_allowed is False


def test_run_result_rejects_selected_decision_ref_drift() -> None:
    result = run_parallel_turn_preflight(
        "How do I build a DIY desk?",
        run_ref="turn-preflight-run:decision-ref-drift",
        decision_ref="turn-decision:preflight-decision-ref-drift",
    )
    payload = result.model_dump(mode="json")
    payload["arbitration_result"]["selected_decision_ref"] = "turn-decision:preflight:wrong"

    with pytest.raises(ValueError, match="selected decision ref drift"):
        TurnPreflightRunResult.model_validate(payload)


def test_run_result_rejects_selected_policy_ref_drift() -> None:
    result = run_parallel_turn_preflight(
        "How do I build a DIY desk?",
        run_ref="turn-preflight-run:policy-ref-drift",
        decision_ref="turn-decision:preflight-policy-ref-drift",
    )
    payload = result.model_dump(mode="json")
    payload["arbitration_result"]["selected_policy_ref"] = "policy-ref:turn-preflight:wrong"

    with pytest.raises(ValueError, match="selected policy ref drift"):
        TurnPreflightRunResult.model_validate(payload)


def test_run_result_rejects_non_advisory_invocation_policy() -> None:
    result = run_parallel_turn_preflight(
        "How do I build a DIY desk?",
        run_ref="turn-preflight-run:policy-advisory",
        decision_ref="turn-decision:preflight-policy-advisory",
    )
    payload = result.model_dump(mode="json")
    payload["invocation_policy_compiled_only"] = False

    with pytest.raises(ValueError, match="advisory only"):
        TurnPreflightRunResult.model_validate(payload)


def test_parallel_preflight_engine_emits_bounded_latency_bucket() -> None:
    result = run_parallel_turn_preflight(
        "How do I build a DIY desk?",
        run_ref="turn-preflight-run:latency-bucket",
        decision_ref="turn-decision:preflight-latency-bucket",
    )

    assert result.latency_ms_bucket in {"under_25_ms", "under_100_ms", "over_100_ms"}


def test_parallel_preflight_engine_has_no_public_lane_override_escape_hatch() -> None:
    with pytest.raises(TypeError):
        run_parallel_turn_preflight(
            "How do I build a DIY desk?",
            run_ref="turn-preflight-run:no-public-overrides",
            decision_ref="turn-decision:preflight-no-public-overrides",
            lane_overrides={},  # type: ignore[call-arg]
        )


def test_parallel_preflight_engine_stays_under_loose_local_latency_threshold() -> None:
    prompts = [
        "How do I build a DIY desk?",
        "Explain how photosynthesis works.",
        "Find current lumber prices near me.",
        "Use my card and book pickup at Home Depot.",
    ]
    start = perf_counter()

    for index, prompt in enumerate(prompts):
        run_parallel_turn_preflight(
            prompt,
            run_ref=f"turn-preflight-run:latency-{index}",
            decision_ref=f"turn-decision:preflight-latency-{index}",
        )

    elapsed_ms_per_turn = ((perf_counter() - start) * 1000) / len(prompts)
    assert elapsed_ms_per_turn < 250.0
