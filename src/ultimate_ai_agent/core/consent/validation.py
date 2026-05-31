from ultimate_ai_agent.core.consent.grants import ConsentGrant

def validate_consent_grant(grant: ConsentGrant) -> bool:
    """Validate that the consent grant is logically consistent.

    Raises ValueError if invalid, returns True if valid.
    """
    if not grant.consent_id:
        raise ValueError("Consent Grant must have a valid non-empty consent_id.")
        
    if grant.expires_at and grant.expires_at <= grant.created_at:
        raise ValueError("Consent Grant expires_at must be in the future relative to created_at.")
        
    if not grant.allowed_actions and not grant.denied_actions:
        raise ValueError("Consent Grant must specify either allowed_actions or denied_actions.")
        
    # Check that allowed and denied actions do not overlap
    overlap = set(grant.allowed_actions).intersection(set(grant.denied_actions))
    if overlap:
        raise ValueError(f"Consent Grant contains overlapping actions in both allowed and denied lists: {overlap}")
        
    return True
