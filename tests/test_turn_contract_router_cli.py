import json

from scripts.dev import uaa_turn_router
from ultimate_ai_agent.core.decision_router import (
    TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS,
    TurnRouterPreviewRequest,
    build_turn_router_preview,
)


def test_turn_router_preview_samples_match_expected_contracts() -> None:
    expected = {
        "diy-desk": "answer_directly",
        "office-memory": "answer_with_reviewed_memory",
        "shopping-list": "draft_or_plan",
        "current-lumber-prices": "prepare_tool_or_action",
        "order-materials": "approval_required",
        "card-pickup": "approval_required",
        "base-answer-bypass": "approval_required",
    }

    for sample_id, selected_contract in expected.items():
        preview = build_turn_router_preview(TurnRouterPreviewRequest(sample_id=sample_id))

        assert preview.selected_turn_contract == selected_contract
        assert preview.request_kind == "sample"
        assert preview.sample_id == sample_id
        assert preview.no_effect_proof.no_runtime_model_call_performed is True
        assert preview.no_effect_proof.no_tool_execution_performed is True
        assert preview.no_effect_proof.no_action_execution_performed is True
        assert preview.no_effect_proof.no_browser_network_performed is True
        assert preview.no_effect_proof.raw_request_text_persisted is False


def test_turn_router_preview_ephemeral_text_omits_raw_request() -> None:
    raw_text = "How do I build a DIY desk?"
    preview = build_turn_router_preview(TurnRouterPreviewRequest(text=raw_text))
    serialized = json.dumps(preview.model_dump(mode="json"))

    assert preview.selected_turn_contract == "answer_directly"
    assert preview.request_kind == "ephemeral_text"
    assert preview.sample_id is None
    assert preview.ephemeral_request_text_omitted is True
    assert raw_text not in serialized


def test_turn_router_preview_secret_like_text_is_redacted_and_approval_bound() -> None:
    secret_text = "api_key='abcdefghijklmnop'"
    preview = build_turn_router_preview(TurnRouterPreviewRequest(text=secret_text))
    serialized = json.dumps(preview.model_dump(mode="json"))

    assert preview.selected_turn_contract == "approval_required"
    assert "secret_like_input_safely_summarized" in preview.redactions_applied
    assert secret_text not in serialized
    assert preview.policy_summary.approval_required is True
    assert preview.policy_summary.tool_execution_allowed is False


def test_turn_router_cli_preview_sample_outputs_safe_json(capsys) -> None:
    exit_code = uaa_turn_router.main(["preview", "--sample", "diy-desk"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["selected_turn_contract"] == "answer_directly"
    assert payload["sample_id"] == "diy-desk"
    assert TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS["diy-desk"] not in json.dumps(payload)


def test_turn_router_cli_preview_text_omits_raw_text(capsys) -> None:
    raw_text = "How do I build a DIY desk?"
    exit_code = uaa_turn_router.main(["preview", "--text", raw_text])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert exit_code == 0
    assert payload["selected_turn_contract"] == "answer_directly"
    assert payload["request_kind"] == "ephemeral_text"
    assert raw_text not in output


def test_turn_router_cli_golden_cases_outputs_all_samples(capsys) -> None:
    exit_code = uaa_turn_router.main(["golden-cases"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert set(payload) == set(TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS)
    assert payload["card-pickup"]["selected_turn_contract"] == "approval_required"
