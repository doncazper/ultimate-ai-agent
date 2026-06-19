from typing import List, Optional, Tuple
from pydantic import BaseModel
from ultimate_ai_agent.core.context_budget.models import ContextTrimPolicy, ContextTrimEvent

class ContextItem(BaseModel):
    item_id: str
    item_type: str  # "user_instruction", "execution_contract", "context_pack", "world_state", "safety_constraint", "tool_output", "chat_message"
    content: str
    tokens: int
    ledger_ref: Optional[str] = None

def trim_context(
    items: List[ContextItem],
    target_tokens: int,
    policy: ContextTrimPolicy,
    run_id: str,
    event_id_prefix: str = "trim_"
) -> Tuple[List[ContextItem], List[ContextTrimEvent]]:
    """Trim items sequentially until the total tokens are within target_tokens.

    Rules:
    - User instructions are never trimmed if policy.preserve_user_instructions is True.
    - Execution Contract, Context Pack, World State, and active safety constraints are never trimmed if preserved.
    - Large tool outputs are trimmed or externalized first.
    - Trimmed items must leave references to the Event Ledger.
    """
    total_tokens = sum(item.tokens for item in items)
    if total_tokens <= target_tokens:
        return items, []

    trimmed_events: List[ContextTrimEvent] = []
    current_items = [item.model_copy() for item in items]
    current_total_tokens = total_tokens

    # Strategy: Trim large tool outputs first
    if policy.trim_large_tool_outputs_first:
        # Get all eligible tool outputs
        tool_indices = [
            i for i, item in enumerate(current_items)
            if item.item_type == "tool_output"
        ]
        # Sort by tokens descending
        tool_indices.sort(key=lambda idx: current_items[idx].tokens, reverse=True)
        
        for idx in tool_indices:
            if current_total_tokens <= target_tokens:
                break
            item = current_items[idx]
            original_tokens = item.tokens
            
            # Trim it (replace content with reference)
            ref_str = f"[Trimmed tool output. Refer to Event ID: {item.ledger_ref or 'N/A'}]"
            trimmed_tokens = len(ref_str) // 4 + 1  # rough estimate for trimmed token count
            current_items[idx] = item.model_copy(update={"content": ref_str, "tokens": trimmed_tokens})
            current_total_tokens += trimmed_tokens - original_tokens
            
            trimmed_events.append(ContextTrimEvent(
                event_id=f"{event_id_prefix}{item.item_id}",
                run_id=run_id,
                trimmed_component_ref=item.item_id,
                original_token_count=original_tokens,
                trimmed_token_count=trimmed_tokens,
                reference_to_ledger_id=item.ledger_ref,
                reason="Trimmed large tool output to save context budget"
            ))

    # If still over target, try trimming non-preserved messages/items
    if current_total_tokens > target_tokens:
        # Candidate items for trimming (excluding protected items)
        for idx in range(len(current_items)):
            if current_total_tokens <= target_tokens:
                break
            item = current_items[idx]
            
            # Skip protected items
            if item.item_type == "user_instruction" and policy.preserve_user_instructions:
                continue
            if item.item_type == "execution_contract" and policy.preserve_execution_contract:
                continue
            if item.item_type == "context_pack" and policy.preserve_context_pack:
                continue
            if item.item_type == "world_state" and policy.preserve_world_state:
                continue
            if item.item_type == "safety_constraint" and policy.preserve_safety_constraints:
                continue
            if item.item_type == "tool_output" and policy.trim_large_tool_outputs_first:
                # Already trimmed in first phase
                continue

            original_tokens = item.tokens
            ref_str = f"[Trimmed {item.item_type}. Refer to Event ID: {item.ledger_ref or 'N/A'}]"
            trimmed_tokens = len(ref_str) // 4 + 1
            current_items[idx] = item.model_copy(update={"content": ref_str, "tokens": trimmed_tokens})
            current_total_tokens += trimmed_tokens - original_tokens

            trimmed_events.append(ContextTrimEvent(
                event_id=f"{event_id_prefix}{item.item_id}",
                run_id=run_id,
                trimmed_component_ref=item.item_id,
                original_token_count=original_tokens,
                trimmed_token_count=trimmed_tokens,
                reference_to_ledger_id=item.ledger_ref,
                reason=f"Trimmed {item.item_type} to satisfy context budget"
            ))

    return current_items, trimmed_events
