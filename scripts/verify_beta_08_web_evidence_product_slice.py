#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.control_center.trust_authority import (  # noqa: E402
    build_trust_authority_matrix_read_model,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (  # noqa: E402
    WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV,
    WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS,
    WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV,
    WEB_EVIDENCE_PRODUCT_SLICE_IDEMPOTENCY_POSTURE_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
    WebEvidenceProductSliceRequest,
    build_web_evidence_product_slice_receipt,
)
from ultimate_ai_agent.core.authority import (  # noqa: E402
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.storage import (  # noqa: E402
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
)
from ultimate_ai_agent.core.tools.runtime.http_fetch import (  # noqa: E402
    ReadOnlyHttpFetchTransportResponse,
)


PRODUCT_SLICE = ROOT / "src/ultimate_ai_agent/core/control_center/web_evidence_product_slice.py"
HTTP_FETCH = ROOT / "src/ultimate_ai_agent/core/tools/runtime/http_fetch.py"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
API = ROOT / "src/ultimate_ai_agent/api/founder_loop.py"
CLI = ROOT / "scripts/dev/uaa_founder_loop.py"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/ProofDetailPanel.tsx"
FRONTEND_APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"
FRONTEND_CLIENT_TEST = ROOT / "apps/control-center/src/api/client.web-evidence.test.ts"
FRONTEND_PANEL_TEST = ROOT / "apps/control-center/src/components/ProofDetailPanel.test.tsx"
FOCUSED_TEST = ROOT / "tests/test_web_evidence_product_slice.py"
VERIFIER_TEST = ROOT / "tests/test_beta_08_web_evidence_product_slice_verifier.py"
PLAN = ROOT / "docs/control_center/USABLE_AUTHORITY_GRADUATION_PLAN.md"
BOARD = ROOT / "docs/control_center/AUTHORITY_GRADUATION_BOARD.md"
RELEASE_SURFACE = ROOT / "docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"
FRONTEND_ROUTES = ROOT / "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
KANBAN = ROOT / "docs/kanban/current_board.md"

FORBIDDEN_TEXT = [
    "super-sensitive-value",
    "https://example.org/status",
    "https://example.org/changed",
    "/users/",
    "/home/",
    "raw prompt",
    "raw response",
    "provider payload",
]


def _fake_transport(_request: Any, _policy: Any) -> ReadOnlyHttpFetchTransportResponse:
    return ReadOnlyHttpFetchTransportResponse(
        status_code=200,
        content_type="text/plain",
        body=b"Public launch status. secret=super-sensitive-value",
    )


_fake_transport.transport_ref = "http-fetch-transport:beta-08-fake"
_fake_transport.real_world_transport_performed = True


def _browser_read_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:web-evidence-product-slice-verify",
        mode=TrustMode.read_only,
        domains={AuthorityDomain.browser: [AuthorityCapability.read]},
        constraints={
            "web_evidence_lane_ref": "lane-ref:web-evidence-product-slice",
            "https_get_only": True,
            "browser_actions_allowed": False,
        },
        safe_summary=(
            "Verifier lease grants Browser read authority for one "
            "WebAccessGateway preview."
        ),
    )


def _request(
    *,
    request_ref: str = "web-evidence-request:beta-08",
    url: str = "https://example.org/status",
) -> WebEvidenceProductSliceRequest:
    return WebEvidenceProductSliceRequest(
        request_ref=request_ref,
        url=url,
        allowed_host="example.org",
        evidence_refs=["evidence-ref:beta-08:web-evidence"],
        metadata_refs=["metadata-ref:beta-08:web-evidence"],
    )


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _with_env(hosts: str | None, disabled: str | None = None) -> None:
    if hosts is None:
        os.environ.pop(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV, None)
    else:
        os.environ[WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV] = hosts
    if disabled is None:
        os.environ.pop(WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV, None)
    else:
        os.environ[WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV] = disabled


def _restore_env(old_hosts: str | None, old_disabled: str | None) -> None:
    if old_hosts is None:
        os.environ.pop(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV, None)
    else:
        os.environ[WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV] = old_hosts
    if old_disabled is None:
        os.environ.pop(WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV, None)
    else:
        os.environ[WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV] = old_disabled


def _assert_safe_text(label: str, value: Any, failures: list[str]) -> None:
    text = json.dumps(value, sort_keys=True).lower()
    for snippet in FORBIDDEN_TEXT:
        if snippet in text:
            failures.append(f"{label} contains forbidden snippet {snippet!r}")


def _assert_receipt(receipt: Any, failures: list[str], label: str) -> None:
    payload = receipt.model_dump(mode="json") if hasattr(receipt, "model_dump") else dict(receipt)
    if payload.get("contract_ref") != WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF:
        failures.append(f"{label} contract ref drifted")
    if payload.get("route_ref") != WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF:
        failures.append(f"{label} route ref drifted")
    if payload.get("proof_ref") != WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF:
        failures.append(f"{label} proof ref drifted")
    if payload.get("safe_refs_only_for_durable_surfaces") is not True:
        failures.append(f"{label} must be safe-ref only for durable surfaces")
    for flag in [
        "raw_response_body_stored",
        "raw_headers_stored",
        "absolute_url_returned",
        "query_string_returned",
        "auth_session_state_used",
        "request_body_sent",
        "non_get_method_used",
        "redirect_followed",
        "download_performed",
        "browser_automation_performed",
        "context_injection_performed",
        "memory_write_performed",
        "model_call_performed",
        "connector_write_performed",
        "action_execution_performed",
        "production_authority_granted",
    ]:
        if payload.get(flag) is not False:
            failures.append(f"{label} unsafe flag drifted: {flag}")
    for flag in [
        "web_access_gateway_required",
        "configured_host_allowlist_required",
        "operator_supplied_host_scope_required",
        "request_ref_payload_idempotency",
    ]:
        if payload.get(flag) is not True:
            failures.append(f"{label} required posture missing: {flag}")
    safe_url_ref = str(payload.get("safe_url_ref", ""))
    if not safe_url_ref.startswith("http-fetch-url:example-org/path-"):
        failures.append(f"{label} safe_url_ref must hash non-root paths")
    if "/status" in safe_url_ref:
        failures.append(f"{label} safe_url_ref persisted raw path text")
    audit = payload.get("web_access_audit_summary")
    if not isinstance(audit, dict):
        failures.append(f"{label} missing web_access_audit_summary")
    else:
        expected = {
            "request_ref": payload.get("web_access_request_ref"),
            "safe_url_ref": payload.get("safe_url_ref"),
            "host_ref": payload.get("host_ref"),
            "adapter_kind": "local_fetch",
            "network_lane": "tool_runtime_read_only_fetch",
            "authority_mode": "read_only",
            "risk_class": "low",
            "policy_status": "allowed",
            "content_untrusted": True,
            "raw_url_omitted": True,
            "raw_headers_omitted": True,
            "raw_body_omitted": True,
        }
        for key, expected_value in expected.items():
            if audit.get(key) != expected_value:
                failures.append(f"{label} audit summary {key} drifted")
        for key in ["url", "final_url", "absolute_url", "raw_url"]:
            if key in audit:
                failures.append(f"{label} audit summary exposed {key}")
    for ref in WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS:
        if ref not in payload.get("blocked_authority_refs", []):
            failures.append(f"{label} missing blocked ref {ref}")
    _assert_safe_text(label, payload, failures)


def _runtime_failures() -> list[str]:
    failures: list[str] = []
    old_hosts = os.environ.get(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV)
    old_disabled = os.environ.get(WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV)
    try:
        _with_env("example.org")
        receipt = build_web_evidence_product_slice_receipt(
            _request(),
            transport=_fake_transport,
            active_authority_leases=[_browser_read_lease()],
        )
        _assert_receipt(receipt, failures, "receipt")

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = FounderLoopRepository(Path(temp_dir) / "founder_loop")
            durable = repo.record_web_evidence_attachment(receipt)
            replayed = repo.record_web_evidence_attachment(
                build_web_evidence_product_slice_receipt(
                    _request(),
                    transport=_fake_transport,
                    active_authority_leases=[_browser_read_lease()],
                )
            )
            try:
                repo.record_web_evidence_attachment(
                    build_web_evidence_product_slice_receipt(
                        _request(url="https://example.org/changed"),
                        transport=_fake_transport,
                        active_authority_leases=[_browser_read_lease()],
                    )
                )
                failures.append("storage accepted conflicting web evidence request_ref")
            except FounderLoopStorageDuplicateError:
                pass
            if replayed.get("replayed") is not True:
                failures.append("storage did not replay same request fingerprint")
            if "redacted_preview" in durable:
                failures.append("durable record stored redacted preview text")
            if durable.get("web_access_audit_summary", {}).get("raw_url_omitted") is not True:
                failures.append("durable record missing redacted audit summary")
            _assert_safe_text("durable record", durable, failures)

            cli = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "--state-dir",
                    str(Path(temp_dir) / "founder_loop"),
                    "inspect-web-evidence",
                    "--limit",
                    "5",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if cli.returncode != 0:
                failures.append(f"web evidence CLI inspect failed: {cli.stderr}")
            else:
                cli_payload = json.loads(cli.stdout)
                if cli_payload.get("redacted_preview_omitted") is not True:
                    failures.append("web evidence CLI inspect must omit preview")
                _assert_safe_text("web evidence CLI inspect", cli_payload, failures)

        _with_env(None)
        try:
            build_web_evidence_product_slice_receipt(
                _request(),
                transport=_fake_transport,
                active_authority_leases=[_browser_read_lease()],
            )
            failures.append("product slice allowed caller-controlled host scope")
        except ValueError as exc:
            if "CONFIGURED_ALLOWLIST_REQUIRED" not in str(exc):
                failures.append(f"unexpected missing-allowlist reason: {exc}")

        _with_env("example.org", disabled="1")
        called = False

        def tracking_transport(_request_obj: Any, _policy_obj: Any) -> ReadOnlyHttpFetchTransportResponse:
            nonlocal called
            called = True
            return _fake_transport(_request_obj, _policy_obj)

        try:
            build_web_evidence_product_slice_receipt(
                _request(),
                transport=tracking_transport,
                active_authority_leases=[_browser_read_lease()],
            )
            failures.append("safe-disable env did not block web evidence")
        except ValueError as exc:
            if "WEB_EVIDENCE_PRODUCT_SLICE_DISABLED" not in str(exc):
                failures.append(f"unexpected disabled reason: {exc}")
        if called:
            failures.append("safe-disable env still called transport")

        manifest = build_api_manifest(app).model_dump(mode="json")
        route = next(
            (
                item
                for item in manifest["routes"]
                if item["path"] == "/control-center/web-evidence/attach"
                and item["method"] == "POST"
            ),
            None,
        )
        if not route:
            failures.append("api manifest missing web evidence attach route")
        else:
            if route["side_effect_class"] != "governed_network_read_only":
                failures.append("web evidence attach side effect class drifted")
            if route["route_classification"] != "local_sensitive":
                failures.append("web evidence attach route classification drifted")
            if route["idempotency_policy_ref"] != WEB_EVIDENCE_PRODUCT_SLICE_IDEMPOTENCY_POSTURE_REF:
                failures.append("web evidence attach idempotency policy ref drifted")
            if "request_ref payload-idempotent" not in route["idempotency_reason"]:
                failures.append("web evidence attach idempotency reason drifted")

        with tempfile.TemporaryDirectory() as temp_dir:
            trust_repo = FounderLoopRepository(Path(temp_dir) / "trust")
            trust = build_trust_authority_matrix_read_model(
                today_summary=trust_repo.today_summary()
            )
        web_lane = next(
            lane
            for lane in trust["lanes"]
            if lane["lane_ref"] == "trust-lane:web-evidence-product-slice"
        )
        if web_lane["authority_state"] != "available_now":
            failures.append("Trust web evidence lane availability drifted")
        if WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF not in web_lane["route_refs"]:
            failures.append("Trust web evidence lane route ref missing")
    finally:
        _restore_env(old_hosts, old_disabled)
    return failures


def _static_failures() -> list[str]:
    failures: list[str] = []
    for path in [
        PRODUCT_SLICE,
        HTTP_FETCH,
        STORAGE,
        API,
        CLI,
        FRONTEND_CLIENT,
        FRONTEND_TYPES,
        FRONTEND_PANEL,
        FRONTEND_APP_TEST,
        FRONTEND_CLIENT_TEST,
        FRONTEND_PANEL_TEST,
        FOCUSED_TEST,
        VERIFIER_TEST,
        PLAN,
        BOARD,
        RELEASE_SURFACE,
        FRONTEND_ROUTES,
        TRUTH_PACKET,
        KANBAN,
    ]:
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)} is missing")
    if failures:
        return failures

    _require(
        PRODUCT_SLICE,
        [
            "WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV",
            "WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV",
            "configured_host_allowlist_required",
            "request_ref_payload_idempotency",
            "web_access_audit_summary",
            "build_read_only_http_fetch_output_via_web_access_gateway",
        ],
        failures,
    )
    _require(
        HTTP_FETCH,
        [
            "_redacted_web_access_audit_summary",
            "path-{hashlib.sha256",
            "raw_url_omitted",
            "network_lane",
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "isSafeWebEvidenceProductSliceReceipt",
            "WEB_EVIDENCE_RECEIPT_DENIED_FLAGS",
            "X-UAA-Idempotency-Ref",
            "Web evidence receipt was rejected safely.",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "stableRefDigest",
            "Blocked In This Receipt",
            "configured allowlist",
            "request ref",
        ],
        failures,
    )
    _require(
        FRONTEND_APP_TEST,
        [
            "renders backend-owned Web Evidence proof slice on the Proof route",
            "configured host allowlist HTTPS GET",
            "POST /control-center/web-evidence/attach",
        ],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_web_evidence_product_slice_requires_configured_allowlist",
            "test_web_evidence_product_slice_safe_disable_blocks_transport",
            "test_web_evidence_attach_route_uses_gateway_storage_replay_and_conflict",
            "test_web_evidence_cli_attach_failure_omits_raw_url_secret_and_paths",
        ],
        failures,
    )
    for doc in [PLAN, BOARD, RELEASE_SURFACE, FRONTEND_ROUTES, TRUTH_PACKET, KANBAN]:
        _require(
            doc,
            [
                "Beta 08 Web Evidence beta slice",
                "scripts/verify_beta_08_web_evidence_product_slice.py",
                "configured host",
                "allowlist",
                "durable",
                "broad runtime authority",
            ],
            failures,
        )
    return failures


def main() -> int:
    failures = [*_static_failures(), *_runtime_failures()]
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Beta 08 Web Evidence product slice verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
