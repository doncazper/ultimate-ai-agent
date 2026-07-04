from pathlib import Path
from time import perf_counter

from ultimate_ai_agent.core.decision_router import (
    TurnContractKind,
    build_turn_harness_binding,
    classify_turn_contract,
    compile_invocation_policy,
)


ARCHITECTURE_DOC = Path("docs/architecture/TURN_CONTRACT_ROUTER.md")


def test_normal_informational_prompts_do_not_route_to_ceremony() -> None:
    prompts = [
        "Explain how photosynthesis works.",
        "What is a clean way to organize a closet?",
        "How do I build a wood shelf?",
        "Build me a Python function that sorts rows.",
    ]

    for index, prompt in enumerate(prompts):
        decision = classify_turn_contract(prompt, decision_ref=f"turn-decision:quality-direct-{index}")
        policy = compile_invocation_policy(decision)

        assert decision.turn_contract == TurnContractKind.answer_directly.value
        assert policy.output_contract == "plain_answer"
        assert policy.planner is False
        assert policy.approval_required is False
        assert policy.side_effects_allowed is False
        assert "approval" not in " ".join(decision.reason_refs)


def test_direct_and_base_answer_bindings_do_not_touch_memory_or_tools() -> None:
    prompts = [
        ("How do I build a DIY table?", "answer_directly"),
        ("Ask the base answer path: how do I build a DIY table?", "base_answer"),
    ]

    for index, (prompt, expected_contract) in enumerate(prompts):
        binding = build_turn_harness_binding(
            prompt,
            binding_ref=f"turn-harness-binding:quality-answer-{index}",
            decision_ref=f"turn-decision:quality-answer-{index}",
        )

        assert binding.turn_contract == expected_contract
        assert binding.memory_touched is False
        assert binding.reviewed_memory_refs_allowed is False
        assert binding.memory_content_retrieved is False
        assert binding.memory_write_allowed is False
        assert binding.tools_exposed_count == 0
        assert binding.execution_tools_exposed_count == 0
        assert binding.approval_required is False
        assert binding.approval_envelope_required is False


def test_classifier_runs_in_low_milliseconds_without_external_work() -> None:
    prompts = [
        "How do I build a DIY table?",
        "Build me a React table component.",
        "Use my card and book pickup at Home Depot.",
        "Find current lumber prices near me.",
        "Design one for my office using what you know.",
    ]
    iterations = 500

    start = perf_counter()
    for index in range(iterations):
        classify_turn_contract(prompts[index % len(prompts)], decision_ref=f"turn-decision:latency-{index}")
    elapsed_ms_per_turn = ((perf_counter() - start) * 1000) / iterations

    assert elapsed_ms_per_turn < 5.0


def test_turn_contract_router_product_language_keeps_authority_blocked() -> None:
    text = ARCHITECTURE_DOC.read_text(encoding="utf-8")
    lowered = text.lower()

    assert "base_answer" in text
    assert "answer_profile_hint" in text
    assert "is public beta" not in lowered
    assert "public beta ready" not in lowered
    assert "production-ready" not in lowered
    assert "broad autonomy" not in lowered
    assert "Payment action" in text
    assert "Booking action" in text
    assert "Still blocked:" in text
