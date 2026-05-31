from ultimate_ai_agent.core.ledger import scan_payload_for_secrets

def test_scan_payload_detects_secrets():
    # String contains secret pattern
    assert scan_payload_for_secrets("api_key='abcde12345678901234'") is True
    assert scan_payload_for_secrets("secret = \"mysecrettokenvalue\"") is True
    assert scan_payload_for_secrets("password='SuperSecurePassword123'") is True
    
    # Dict contain secret pattern
    assert scan_payload_for_secrets({"key": "val", "config": "token='abcde12345678901234'"}) is True
    assert scan_payload_for_secrets({"token='abcde12345678901234'": "val"}) is True
    
    # List contain secret pattern
    assert scan_payload_for_secrets(["public_val", "secret='abcde12345678901234'"]) is True

def test_scan_payload_ignores_safe_strings():
    assert scan_payload_for_secrets("This is a completely normal prompt instruction.") is False
    assert scan_payload_for_secrets({"cost": 0.05, "tokens": 120}) is False
    assert scan_payload_for_secrets(["value1", "value2"]) is False
