#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.tools.runtime import (  # noqa: E402
    READ_ONLY_HTTP_FETCH_TOOL_NAME,
    READ_ONLY_HTTP_FETCH_TOOL_REF,
    ToolInvocationKind,
    ToolInvocationRequest,
    ToolRuntimeAdapter,
)
from ultimate_ai_agent.core.web_access.read_only_http_fetch_transport import (  # noqa: E402
    build_read_only_real_world_http_fetch_transport,
)


def inspect_payload(
    *,
    url: str,
    allowed_host: str,
    request_ref: str = "http-fetch-request:cli-read-only-real-world",
    invocation_id: str = "tool-runtime-invocation:cli-read-only-real-world",
    replay_key: str = "tool-runtime-replay:cli-read-only-real-world",
    transport: Any | None = None,
) -> dict[str, Any]:
    active_transport = transport or build_read_only_real_world_http_fetch_transport()
    request = ToolInvocationRequest(
        invocation_id=invocation_id,
        tool_ref=READ_ONLY_HTTP_FETCH_TOOL_REF,
        tool_name=READ_ONLY_HTTP_FETCH_TOOL_NAME,
        invocation_kind=ToolInvocationKind.read_only_http_fetch,
        replay_key=replay_key,
        safe_summary=(
            "Inspect one allowlisted read-only HTTPS GET through WebAccessGateway."
        ),
        metadata={
            "request_ref": request_ref,
            "url": url,
            "allowed_hosts": [allowed_host],
            "allowed_host_policy_ref": "http-fetch-policy:cli-read-only-real-world",
            "safe_summary": (
                "Fetch a bounded redacted preview from one explicitly allowlisted public host."
            ),
        },
    )
    decision = ToolRuntimeAdapter().invoke(
        request,
        http_fetch_transport=active_transport,
    )
    output = None
    if decision.result is not None:
        output = decision.result.output.model_dump(mode="json")
    return {
        "decision_id": decision.decision_id,
        "invocation_id": decision.invocation_id,
        "tool_ref": decision.tool_ref,
        "status": decision.status.value,
        "invocation_allowed": decision.invocation_allowed,
        "network_call_performed": decision.network_call_performed,
        "reason_codes": decision.reason_codes,
        "safe_message": decision.safe_message,
        "authority_posture": {
            "backend_owned": True,
            "web_access_gateway_required": True,
            "read_only_https_get_only": True,
            "explicit_allowlist_required": True,
            "raw_url_returned": False,
            "raw_response_body_returned": False,
            "raw_headers_returned": False,
            "browser_automation_performed": False,
            "provider_sdk_call_performed": False,
            "connector_write_performed": False,
            "memory_write_performed": False,
            "context_injection_performed": False,
            "action_execution_performed": False,
            "production_authority_granted": False,
        },
        "output": output,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect one allowlisted read-only HTTPS GET through WebAccessGateway. "
            "The raw URL is accepted as input but is not echoed in output."
        )
    )
    parser.add_argument("--url", required=True, help="HTTPS URL to inspect.")
    parser.add_argument(
        "--allowed-host",
        required=True,
        help="Explicit public host allowlist entry for this one inspection.",
    )
    parser.add_argument(
        "--request-ref",
        default="http-fetch-request:cli-read-only-real-world",
        help="Safe request ref for the inspection.",
    )
    args = parser.parse_args(argv)
    payload = inspect_payload(
        url=args.url,
        allowed_host=args.allowed_host,
        request_ref=args.request_ref,
    )
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
