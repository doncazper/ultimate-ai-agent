from ultimate_ai_agent.core.context_budget import (
    ContextItem,
    ContextTrimPolicy,
    trim_context,
)

def test_tool_result_trimming_order():
    items = [
        ContextItem(item_id="user_inst", item_type="user_instruction", content="Run tasks", tokens=100),
        ContextItem(item_id="exec_contract", item_type="execution_contract", content="Contract v0", tokens=200),
        ContextItem(item_id="tool_small", item_type="tool_output", content="small output", tokens=300, ledger_ref="evt_small"),
        ContextItem(item_id="tool_large", item_type="tool_output", content="extremely large tool output", tokens=1000, ledger_ref="evt_large"),
        ContextItem(item_id="chat_msg", item_type="chat_message", content="Hello agent", tokens=150)
    ]
    policy = ContextTrimPolicy(
        trim_large_tool_outputs_first=True,
        preserve_user_instructions=True,
        preserve_execution_contract=True
    )
    
    # Target is 1200 tokens (original is 1750)
    # The largest tool output (tool_large) should be trimmed first.
    trimmed_items, events = trim_context(
        items=items,
        target_tokens=1200,
        policy=policy,
        run_id="run_trim_1"
    )
    
    assert len(events) == 1
    assert events[0].trimmed_component_ref == "tool_large"
    assert events[0].reference_to_ledger_id == "evt_large"
    
    # Check that tool_large was trimmed (replaced by ref)
    trimmed_large = next(item for item in trimmed_items if item.item_id == "tool_large")
    assert "[Trimmed tool output. Refer to Event ID: evt_large]" in trimmed_large.content

def test_protected_components_never_trimmed():
    items = [
        ContextItem(item_id="user_inst", item_type="user_instruction", content="Critical user goal", tokens=500),
        ContextItem(item_id="safety", item_type="safety_constraint", content="Do not delete files", tokens=400),
        ContextItem(item_id="chat_msg", item_type="chat_message", content="User chit chat", tokens=300)
    ]
    policy = ContextTrimPolicy(
        preserve_user_instructions=True,
        preserve_safety_constraints=True
    )
    
    # Target is 600 tokens (original is 1200)
    # Since user_inst and safety are protected, chat_msg must be trimmed first, even if it is smaller.
    trimmed_items, events = trim_context(
        items=items,
        target_tokens=600,
        policy=policy,
        run_id="run_trim_2"
    )
    
    assert len(events) == 1
    assert events[0].trimmed_component_ref == "chat_msg"
    
    # Critical components must remain unmodified
    user_inst = next(item for item in trimmed_items if item.item_id == "user_inst")
    assert user_inst.content == "Critical user goal"
    assert user_inst.tokens == 500
