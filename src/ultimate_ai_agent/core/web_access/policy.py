"""Deny-by-default policy for WebAccessGateway."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlparse

from .contracts import (
    WebAccessAuthorityMode,
    WebAccessNetworkLane,
    WebAccessPolicyDecision,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
    WebAccessRiskClass,
)


READ_ONLY_KINDS = {
    WebAccessRequestKind.GOVERNED_WEB_EVIDENCE,
    WebAccessRequestKind.READ_ONLY_FETCH,
    WebAccessRequestKind.BROWSER_OBSERVE,
}

FUTURE_DENIED_KINDS = {
    WebAccessRequestKind.SEARCH,
    WebAccessRequestKind.EXTRACT_SCHEMA,
    WebAccessRequestKind.BROWSER_ACTION_DRY_RUN,
    WebAccessRequestKind.BROWSER_CLICK,
    WebAccessRequestKind.FORM_FILL,
    WebAccessRequestKind.DOWNLOAD,
    WebAccessRequestKind.UPLOAD,
    WebAccessRequestKind.AUTHENTICATED_SESSION,
}

ALLOWED_PHASE_1_LANES = {
    WebAccessNetworkLane.AGENT_PUBLIC_WEB,
    WebAccessNetworkLane.GOVERNED_WEB_EVIDENCE,
    WebAccessNetworkLane.TOOL_RUNTIME_READ_ONLY_FETCH,
    WebAccessNetworkLane.BROWSER_OBSERVE_ONLY,
}


@dataclass(frozen=True)
class WebAccessPolicy:
    """Default policy for the first WebAccessGateway boundary PR.

    The policy intentionally permits only HTTPS GET read-only/governed-evidence
    requests. Browser observe/dry-run types exist in contracts, but are denied
    until later milestone PRs promote them.
    """

    allow_read_only_fetch: bool = False
    allow_governed_web_evidence: bool = True
    allow_browser_observe: bool = False
    deny_private_networks: bool = True

    def evaluate(self, request: WebAccessRequest) -> WebAccessPolicyDecision:
        reasons: list[str] = []
        risk = self._risk_for(request)

        if request.authority_mode == WebAccessAuthorityMode.OFF:
            return self._deny(risk, "authority_mode_off")

        if request.network_lane not in ALLOWED_PHASE_1_LANES:
            return self._deny(
                WebAccessRiskClass.MEDIUM,
                f"network_lane_not_gateway_phase_1:{request.network_lane.value}",
            )
        lane_kind_reason = _lane_kind_reason(request)
        if lane_kind_reason:
            return self._deny(WebAccessRiskClass.MEDIUM, lane_kind_reason)

        if request.kind in FUTURE_DENIED_KINDS:
            return self._deny(risk, f"request_kind_not_enabled:{request.kind.value}")

        if request.kind == WebAccessRequestKind.READ_ONLY_FETCH and not self.allow_read_only_fetch:
            return self._deny(WebAccessRiskClass.LOW, "read_only_fetch_not_enabled")

        if request.kind == WebAccessRequestKind.GOVERNED_WEB_EVIDENCE and not self.allow_governed_web_evidence:
            return self._deny(WebAccessRiskClass.LOW, "governed_web_evidence_not_enabled")

        if request.kind == WebAccessRequestKind.BROWSER_OBSERVE:
            if not self.allow_browser_observe:
                return self._deny(WebAccessRiskClass.MEDIUM, "browser_observe_not_enabled")
            return self._evaluate_browser_observe(request)

        if request.kind not in READ_ONLY_KINDS:
            return self._deny(risk, f"unknown_or_unsupported_kind:{request.kind.value}")

        if request.method != "GET":
            return self._deny(self._method_risk(request.method), f"method_not_allowed:{request.method}")

        if not request.url:
            return self._deny(WebAccessRiskClass.LOW, "missing_url")

        parsed = urlparse(request.url)
        if parsed.scheme != "https":
            return self._deny(WebAccessRiskClass.MEDIUM, "only_https_urls_allowed")

        host = (parsed.hostname or "").lower()
        if not host:
            return self._deny(WebAccessRiskClass.MEDIUM, "missing_url_host")

        if self.deny_private_networks and _is_private_or_local_host(host):
            return self._deny(WebAccessRiskClass.HIGH, "private_or_local_network_denied")

        if request.allowed_domains and not _host_matches_allowed_domains(host, request.allowed_domains):
            return self._deny(WebAccessRiskClass.MEDIUM, "host_not_in_allowed_domains")

        if _truthy_metadata(request, "uses_auth", "cookies", "request_body", "download", "upload"):
            reasons.append("auth_cookies_body_download_upload_denied")

        if reasons:
            return self._deny(WebAccessRiskClass.HIGH, *reasons)

        return WebAccessPolicyDecision(
            status=WebAccessPolicyStatus.ALLOWED,
            risk_class=WebAccessRiskClass.LOW,
            reasons=("phase_1_read_only_get_allowed",),
            allowed_methods=("GET",),
            requires_approval=False,
        )

    def _evaluate_browser_observe(self, request: WebAccessRequest) -> WebAccessPolicyDecision:
        if request.authority_mode != WebAccessAuthorityMode.BROWSER_OBSERVE_ONLY:
            return self._deny(WebAccessRiskClass.MEDIUM, "browser_observe_authority_mode_required")
        if request.network_lane != WebAccessNetworkLane.BROWSER_OBSERVE_ONLY:
            return self._deny(WebAccessRiskClass.MEDIUM, "browser_observe_lane_required")
        if request.method != "GET":
            return self._deny(self._method_risk(request.method), f"method_not_allowed:{request.method}")
        if request.url is not None:
            return self._deny(WebAccessRiskClass.MEDIUM, "browser_observe_raw_url_denied")
        safe_url_ref = request.metadata.get("safe_url_ref")
        if not isinstance(safe_url_ref, str) or not safe_url_ref.startswith("browser-url:"):
            return self._deny(WebAccessRiskClass.LOW, "browser_observe_safe_url_ref_required")
        denied_capability_reasons = _browser_observe_capability_reasons(request)
        if denied_capability_reasons:
            return self._deny(WebAccessRiskClass.HIGH, *denied_capability_reasons)
        return WebAccessPolicyDecision(
            status=WebAccessPolicyStatus.ALLOWED,
            risk_class=WebAccessRiskClass.MEDIUM,
            reasons=("browser_observe_only_injected_observation_allowed",),
            allowed_methods=("GET",),
            requires_approval=False,
        )

    @staticmethod
    def _deny(risk_class: WebAccessRiskClass, *reasons: str) -> WebAccessPolicyDecision:
        return WebAccessPolicyDecision(
            status=WebAccessPolicyStatus.DENIED,
            risk_class=risk_class,
            reasons=tuple(reasons) or ("denied_by_default",),
            allowed_methods=(),
            requires_approval=False,
        )

    @staticmethod
    def _method_risk(method: str) -> WebAccessRiskClass:
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            return WebAccessRiskClass.HIGH
        return WebAccessRiskClass.MEDIUM

    @staticmethod
    def _risk_for(request: WebAccessRequest) -> WebAccessRiskClass:
        if request.kind in {
            WebAccessRequestKind.BROWSER_CLICK,
            WebAccessRequestKind.FORM_FILL,
            WebAccessRequestKind.DOWNLOAD,
            WebAccessRequestKind.UPLOAD,
            WebAccessRequestKind.AUTHENTICATED_SESSION,
        }:
            return WebAccessRiskClass.CRITICAL
        if request.kind in {
            WebAccessRequestKind.BROWSER_OBSERVE,
            WebAccessRequestKind.BROWSER_ACTION_DRY_RUN,
            WebAccessRequestKind.EXTRACT_SCHEMA,
        }:
            return WebAccessRiskClass.MEDIUM
        return WebAccessRiskClass.LOW


def _truthy_metadata(request: WebAccessRequest, *keys: str) -> bool:
    return any(bool(request.metadata.get(key)) for key in keys)


def _lane_kind_reason(request: WebAccessRequest) -> str | None:
    allowed_by_kind = {
        WebAccessRequestKind.GOVERNED_WEB_EVIDENCE: {
            WebAccessNetworkLane.AGENT_PUBLIC_WEB,
            WebAccessNetworkLane.GOVERNED_WEB_EVIDENCE,
        },
        WebAccessRequestKind.READ_ONLY_FETCH: {
            WebAccessNetworkLane.AGENT_PUBLIC_WEB,
            WebAccessNetworkLane.TOOL_RUNTIME_READ_ONLY_FETCH,
        },
        WebAccessRequestKind.BROWSER_OBSERVE: {
            WebAccessNetworkLane.BROWSER_OBSERVE_ONLY,
        },
    }
    allowed_lanes = allowed_by_kind.get(request.kind)
    if allowed_lanes is None or request.network_lane in allowed_lanes:
        return None
    return f"network_lane_not_valid_for_kind:{request.kind.value}:{request.network_lane.value}"


def _browser_observe_capability_reasons(request: WebAccessRequest) -> tuple[str, ...]:
    capability_reasons = [
        ("navigation", "browser_observe_navigation_denied"),
        ("click", "browser_observe_click_denied"),
        ("form_fill", "browser_observe_form_fill_denied"),
        ("screenshot", "browser_observe_screenshot_denied"),
        ("raw_dom", "browser_observe_raw_dom_denied"),
        ("uses_auth", "browser_observe_authenticated_profile_denied"),
        ("cookies", "browser_observe_cookies_or_credentials_denied"),
        ("download", "browser_observe_download_or_upload_denied"),
        ("upload", "browser_observe_download_or_upload_denied"),
        ("network_interception", "browser_observe_network_interception_denied"),
        ("network_call", "browser_observe_network_call_denied"),
        ("model_call", "browser_observe_model_call_denied"),
        ("tool_execution", "browser_observe_tool_execution_denied"),
        ("memory_write", "browser_observe_memory_write_denied"),
        ("context_injection", "browser_observe_context_injection_denied"),
        ("backend_route", "browser_observe_backend_route_denied"),
        ("control_center_control", "browser_observe_control_center_control_denied"),
        ("production_authority", "browser_observe_production_authority_denied"),
        ("request_body", "browser_observe_request_body_denied"),
    ]
    reasons = [reason for key, reason in capability_reasons if bool(request.metadata.get(key))]
    return tuple(dict.fromkeys(reasons))


def _host_matches_allowed_domains(host: str, allowed_domains: tuple[str, ...]) -> bool:
    normalized = tuple(domain.lower().lstrip(".") for domain in allowed_domains)
    return any(host == domain or host.endswith(f".{domain}") for domain in normalized)


def _is_private_or_local_host(host: str) -> bool:
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return True

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False

    return any(
        (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        )
    )
