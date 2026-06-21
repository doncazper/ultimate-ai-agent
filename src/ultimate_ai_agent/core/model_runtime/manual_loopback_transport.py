from typing import Any
import json
import time
from urllib import error as urllib_error
from urllib import request as urllib_request

from ultimate_ai_agent.core.approvals import ApprovalValidationDecision
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.model_runtime.smoke import _result, _safe_preview, validate_manual_loopback_smoke_request
from ultimate_ai_agent.core.model_runtime.smoke_policy import ManualLoopbackSmokeRequest


class StdlibLoopbackSmokeTransport:
    """Manual local-dev smoke only; not production model execution and never for user data."""

    def __init__(self, opener: Any | None = None) -> None:
        self._opener = opener or urllib_request.urlopen

    def preview_request(self, request: ManualLoopbackSmokeRequest) -> dict:
        return {
            "endpoint_id": request.endpoint.endpoint_id,
            "host": request.endpoint.host,
            "model_id": request.model_id,
            "manual_only": True,
            "would_send_user_content": False,
            "fixed_prompt_used": True,
            "truth_authority": False,
        }

    def send_smoke(
        self,
        request: ManualLoopbackSmokeRequest,
        approval_decision: ApprovalValidationDecision | None = None,
    ) -> Any:
        decision = validate_manual_loopback_smoke_request(request, approval_decision)
        if not decision.allowed:
            return decision

        started = time.monotonic()
        payload = json.dumps(
            {
                "model": request.model_id,
                "prompt": request.fixed_prompt,
                "stream": False,
            }
        ).encode("utf-8")
        http_request = urllib_request.Request(
            request.endpoint.base_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener(http_request, timeout=request.policy.timeout_seconds) as response:
                body = response.read(request.policy.max_response_bytes + 1)
        except urllib_error.URLError:
            return _result(
                request,
                allowed=True,
                success=False,
                status="failed",
                reason_codes=["SMOKE_TRANSPORT_FAILED"],
                safe_message="Manual local loopback smoke transport failed.",
                response_preview=None,
                response_origin="local_loopback_smoke",
                elapsed_ms=_elapsed_ms(started),
            )

        if len(body) > request.policy.max_response_bytes:
            return _result(
                request,
                allowed=True,
                success=False,
                status="blocked",
                reason_codes=["SMOKE_RESPONSE_TOO_LARGE"],
                safe_message="Manual local loopback smoke response exceeded the configured byte cap.",
                response_preview=None,
                response_origin="local_loopback_smoke",
                elapsed_ms=_elapsed_ms(started),
            )

        text = body.decode("utf-8", errors="replace")
        if contains_secret_like(text):
            return _result(
                request,
                allowed=False,
                success=False,
                status="blocked",
                reason_codes=["SMOKE_RESPONSE_SECRET_BLOCKED"],
                safe_message="Manual local loopback smoke response was blocked by secret hygiene.",
                response_preview=None,
                response_origin="local_loopback_smoke",
                elapsed_ms=_elapsed_ms(started),
                redactions_applied=["response_preview"],
            )
        if request.expected_marker and request.expected_marker not in text:
            return _result(
                request,
                allowed=True,
                success=False,
                status="failed",
                reason_codes=["EXPECTED_MARKER_MISSING"],
                safe_message="Manual local loopback smoke response did not contain the expected marker.",
                response_preview=_safe_preview(text, request.policy.max_response_bytes),
                response_origin="local_loopback_smoke",
                elapsed_ms=_elapsed_ms(started),
            )
        return _result(
            request,
            allowed=True,
            success=True,
            status="smoke_passed",
            reason_codes=["SMOKE_OK"],
            safe_message="Manual local loopback smoke completed; model output is not authoritative evidence.",
            response_preview=_safe_preview(text, request.policy.max_response_bytes),
            response_origin="local_loopback_smoke",
            elapsed_ms=_elapsed_ms(started),
        )


def _elapsed_ms(started: float) -> int:
    return max(0, int((time.monotonic() - started) * 1000))
