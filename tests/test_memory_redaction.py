from ultimate_ai_agent.core.memory import redact_memory_content


def test_memory_redaction_masks_secret_like_values():
    redacted, applied = redact_memory_content("api_key='abcdefghijklmnop' should not be stored")

    assert "abcdefghijklmnop" not in redacted
    assert "[REDACTED_SECRET]" in redacted
    assert applied == ["secret_value"]
