from ultimate_ai_agent.core.decision_router import build_turn_harness_binding


def test_harness_binding_for_diy_table_has_no_tools_memory_or_state() -> None:
    binding = build_turn_harness_binding(
        "How do I build a DIY table?",
        binding_ref="turn-harness-binding:diy-table",
        decision_ref="turn-decision:harness-diy-table",
    )

    assert binding.turn_contract == "answer_directly"
    assert binding.memory_touched is False
    assert binding.reviewed_memory_refs_allowed is False
    assert binding.memory_content_retrieved is False
    assert binding.memory_write_allowed is False
    assert binding.tools_exposed_count == 0
    assert binding.tool_refs == []
    assert binding.execution_tools_exposed_count == 0
    assert binding.planner is False
    assert binding.durable_state is False
    assert binding.approval_required is False
    assert binding.raw_prompt_persisted is False
    assert binding.raw_response_persisted is False
    assert binding.raw_memory_body_persisted is False


def test_harness_binding_for_memory_prompt_allows_reviewed_refs_without_write() -> None:
    binding = build_turn_harness_binding(
        "Design one for my office using what you know.",
        binding_ref="turn-harness-binding:office-memory",
        decision_ref="turn-decision:harness-office-memory",
    )

    assert binding.turn_contract == "answer_with_reviewed_memory"
    assert binding.memory_scope == "reviewed_relevant_only"
    assert binding.reviewed_memory_refs_allowed is True
    assert binding.memory_touched is False
    assert binding.memory_content_retrieved is False
    assert binding.memory_write_allowed is False
    assert binding.memory_write_performed is False
    assert binding.tools_exposed_count == 0
    assert binding.execution_tools_exposed_count == 0
    assert binding.approval_required is False


def test_harness_binding_for_home_depot_card_requires_envelope_without_execution_tools() -> None:
    binding = build_turn_harness_binding(
        "Use my card and book pickup at Home Depot.",
        binding_ref="turn-harness-binding:home-depot-card",
        decision_ref="turn-decision:harness-home-depot-card",
    )

    assert binding.turn_contract == "approval_required"
    assert binding.approval_required is True
    assert binding.approval_envelope_required is True
    assert binding.tool_policy == "envelope_only_no_execution"
    assert binding.tools_exposed_count == 1
    assert binding.tool_refs == ["tool-category:approval-envelope-builder"]
    assert binding.execution_tools_exposed_count == 0
    assert binding.side_effects_allowed is False
    assert binding.execution_ready is False
    assert binding.receipt_required is False
    assert binding.memory_content_retrieved is False
    assert binding.no_tool_execution_performed is True
    assert binding.no_action_execution_performed is True


def test_harness_binding_does_not_persist_request_text() -> None:
    prompt = "How do I build a DIY table?"
    binding = build_turn_harness_binding(
        prompt,
        binding_ref="turn-harness-binding:no-request-text",
        decision_ref="turn-decision:harness-no-request-text",
    )

    assert prompt.lower() not in repr(binding.model_dump(mode="json")).lower()
