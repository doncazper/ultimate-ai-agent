from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.world_state.models import StructuredWorldState

def validate_world_state_secrets(state: StructuredWorldState) -> bool:
    """Validate that the structured world state contains no raw secrets or credentials.

    Returns True if valid (clean), False if secrets are detected.
    """
    payload = state.model_dump()
    return not scan_payload_for_secrets(payload)
