import json
import time
from typing import Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request

from ultimate_ai_agent.core.model_runtime.local_call_contracts import (
    LocalModelCallRequest,
    LocalModelCallTransportResult,
)
from ultimate_ai_agent.core.model_runtime.local_call_policy import redact_local_model_response


class LocalModelCallTransport(Protocol):
    def send(self, request: LocalModelCallRequest) -> LocalModelCallTransportResult:
        ...


class FakeLocalModelCallTransport:
    def __init__(self, response_text: str = "UAA_M23_LOCAL_MODEL_CALL_OK", status_code: int = 200):
        self.response_text = response_text
        self.status_code = status_code
        self.calls = 0

    def send(self, request: LocalModelCallRequest) -> LocalModelCallTransportResult:
        self.calls += 1
        safe_text, safe_summary, redaction_applied, truncated, redaction_status = redact_local_model_response(
            self.response_text,
            request.max_response_chars,
        )
        if redaction_status == "blocked":
            return LocalModelCallTransportResult(
                transport_result_id=f"m23_transport_{request.request_id}",
                request_id=request.request_id,
                transport_kind="fake",
                call_performed=True,
                endpoint_contacted=True,
                network_scope="loopback",
                status_code=self.status_code,
                response_received=True,
                raw_response_stored=False,
                response_truncated=False,
                redaction_applied=True,
                safe_response_text=None,
                safe_response_summary=None,
                metadata={"reason_codes": ["M23_RESPONSE_SECRET_BLOCKED"]},
            )
        return LocalModelCallTransportResult(
            transport_result_id=f"m23_transport_{request.request_id}",
            request_id=request.request_id,
            transport_kind="fake",
            call_performed=True,
            endpoint_contacted=True,
            network_scope="loopback",
            status_code=self.status_code,
            response_received=True,
            raw_response_stored=False,
            response_truncated=truncated,
            redaction_applied=redaction_applied,
            safe_response_text=safe_text,
            safe_response_summary=safe_summary,
        )


class ManualStdlibLoopbackLocalModelCallTransport:
    """Manual M23 CLI-only fixed-prompt local loopback transport."""

    def __init__(self, opener=None):
        self._opener = opener or urllib_request.urlopen

    def send(self, request: LocalModelCallRequest) -> LocalModelCallTransportResult:
        started = time.monotonic()
        payload = json.dumps(
            {
                "model": request.model_ref,
                "prompt": request.prompt_text,
                "stream": False,
            }
        ).encode("utf-8")
        http_request = urllib_request.Request(
            request.endpoint_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener(http_request, timeout=request.timeout_seconds) as response:
                status_code = getattr(response, "status", None) or getattr(response, "code", None)
                body = response.read(request.max_response_chars + 1)
        except urllib_error.URLError:
            return LocalModelCallTransportResult(
                transport_result_id=f"m23_transport_{request.request_id}",
                request_id=request.request_id,
                transport_kind="manual_stdlib_loopback",
                call_performed=True,
                endpoint_contacted=True,
                network_scope="loopback",
                response_received=False,
                raw_response_stored=False,
                safe_response_text=None,
                safe_response_summary=None,
                metadata={"reason_codes": ["M23_TRANSPORT_FAILED"], "elapsed_ms": _elapsed_ms(started)},
            )

        text = body.decode("utf-8", errors="replace")
        safe_text, safe_summary, redaction_applied, truncated, redaction_status = redact_local_model_response(
            text,
            request.max_response_chars,
        )
        metadata = {"elapsed_ms": _elapsed_ms(started)}
        if redaction_status == "blocked":
            metadata["reason_codes"] = ["M23_RESPONSE_SECRET_BLOCKED"]
        return LocalModelCallTransportResult(
            transport_result_id=f"m23_transport_{request.request_id}",
            request_id=request.request_id,
            transport_kind="manual_stdlib_loopback",
            call_performed=True,
            endpoint_contacted=True,
            network_scope="loopback",
            status_code=status_code,
            response_received=True,
            raw_response_stored=False,
            response_truncated=truncated,
            redaction_applied=redaction_applied,
            safe_response_text=safe_text,
            safe_response_summary=safe_summary,
            metadata=metadata,
        )


def _elapsed_ms(started: float) -> int:
    return max(0, int((time.monotonic() - started) * 1000))

