from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.network import (
    AuthlessNetworkExpansionPolicy,
    AuthlessNetworkExpansionRequest,
)


def _policy(**overrides: Any) -> Any:
    data = {
        "allowed_hosts": ("docs.example.test", "status.example.test"),
        "allowed_redirect_hosts": ("status.example.test",),
    }
    data.update(overrides)
    return AuthlessNetworkExpansionPolicy(**data)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "network-authless-expansion-request:m95-safe",
        "actor_ref": "actor:local-reviewer",
        "scoped_session_ref": "autonomy-session:m95-single-session",
        "scope_ref": "scope:m95-docs-status",
        "network_tool_ref": "network-tool:m95-authless-read-only",
        "m72_fetch_tool_ref": "tool:http-fetch-read-only-m72",
        "allowed_host_policy_ref": "network-allowlist-policy:m95-authless",
        "target_host": "docs.example.test",
        "target_path": "/status",
        "exact_scope_approval_ref": "approval:m95-exact-scope",
        "audit_ref": "audit:m95-authless-read-only",
        "revocation_ref": "revocation:m95-authless-read-only",
        "safe_summary": "Allow an authless read-only GET preview for an allowlisted documentation host.",
    }
    data.update(overrides)
    return AuthlessNetworkExpansionRequest(**data)
