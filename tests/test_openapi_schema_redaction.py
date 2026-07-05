from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.openapi import (
    forbidden_raw_provider_schema_fields,
    forbidden_raw_secret_schema_fields,
)


def test_openapi_schema_has_no_raw_secret_request_fields() -> None:
    findings = forbidden_raw_secret_schema_fields(app.openapi())

    assert findings == []


def test_openapi_schema_has_no_raw_provider_payload_fields() -> None:
    schema = app.openapi()
    findings = forbidden_raw_provider_schema_fields(schema)
    chat_schema = schema["components"]["schemas"]["V1ChatCompletionAPIRequest"]

    assert findings == []
    assert "model" in chat_schema["properties"]
    assert "messages" in chat_schema["properties"]
