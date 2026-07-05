import pytest

from ultimate_ai_agent.core.decision_router import (
    PromptProfilePolicy,
    RiskFlag,
    TurnContractKind,
    TurnPreflightArbitrationInput,
    TurnPreflightArbitrationResult,
    TurnPreflightBundle,
    TurnPreflightLaneKind,
    TurnPreflightLaneResult,
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
