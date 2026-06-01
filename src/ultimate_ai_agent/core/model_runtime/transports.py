import hashlib
from typing import Any, Dict, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.loopback import LoopbackRuntimeEndpoint
from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean


class TransportResponse(BaseModel):
    status_code: int = Field(..., ge=100, le=599)
    body: Dict[str, Any] = Field(default_factory=dict)
    elapsed_ms: int = Field(..., ge=0)
    headers_summary: Dict[str, str] = Field(default_factory=dict)
    simulated: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def transport_response_must_be_safe(self):
        forbidden_headers = {"authorization", "cookie", "set-cookie", "x-api-key"}
        if forbidden_headers.intersection({key.lower() for key in self.headers_summary}):
            raise ValueError("Transport response headers must not include credential-bearing names.")
        assert_secret_clean(self.body, "Transport response body")
        assert_secret_clean(self.headers_summary, "Transport response headers_summary")
        return self


class ModelRuntimeTransport(Protocol):
    def send(
        self,
        request_payload: Dict[str, Any],
        endpoint: LoopbackRuntimeEndpoint,
        timeout_seconds: float,
    ) -> TransportResponse:
        ...


class FakeModelRuntimeTransport:
    def send(
        self,
        request_payload: Dict[str, Any],
        endpoint: LoopbackRuntimeEndpoint,
        timeout_seconds: float,
    ) -> TransportResponse:
        seed = f"{request_payload.get('runtime_request_id')}:{endpoint.endpoint_id}:{request_payload.get('output_format')}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
        return TransportResponse(
            status_code=200,
            body={
                "output_summary": f"Fake local loopback response {digest}; no remote model was called.",
                "structured_output": {
                    "runtime_request_id": request_payload.get("runtime_request_id"),
                    "response_digest": digest,
                    "simulated": False,
                },
            },
            elapsed_ms=5 + (len(digest) % 7),
            headers_summary={"content-type": "application/json"},
            simulated=False,
        )


class DisabledNetworkTransport:
    def send(
        self,
        request_payload: Dict[str, Any],
        endpoint: LoopbackRuntimeEndpoint,
        timeout_seconds: float,
    ) -> TransportResponse:
        return TransportResponse(
            status_code=403,
            body={
                "safe_message": "Network transport is disabled by default for M9.",
                "reason_codes": ["NETWORK_TRANSPORT_DISABLED"],
            },
            elapsed_ms=0,
            headers_summary={},
            simulated=True,
        )
