from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart017Mixin:
    """Legacy checks from m70_autonomy_foundation_freeze_review through m73_browser_automation_contract_static_safety."""
    def check_m70_autonomy_foundation_freeze_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/foundation_freeze.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE.md",
            "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE_CONTRACTS.md",
            "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE_NON_GOALS.md",
            "docs/autonomy/M70_TO_M71_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "tests/test_m70_autonomy_foundation_freeze.py",
            "tests/test_m70_gate_integration.py",
        ]
        failures = [
            f"missing M70 autonomy foundation freeze file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.autonomy import (
                AutonomyFoundationFreezeRequest,
                AutonomyFoundationFreezeStatus,
                build_autonomy_foundation_freeze_report,
                validate_autonomy_foundation_freeze_request,
            )

            request = AutonomyFoundationFreezeRequest(
                request_ref="autonomy-foundation-freeze-request:m70-gate",
                freeze_ref="autonomy-foundation-freeze:m70-gate",
                baseline_ref="baseline:v0.73.0",
                actor_ref="actor:foundation-gate",
                accepted_milestone_refs=[
                    f"milestone:M{index}" for index in range(61, 70)
                ],
                checklist_refs=[
                    "autonomy-freeze:m61-m69-reviewed",
                    "autonomy-freeze:route-stable",
                    "autonomy-freeze:dependency-stable",
                    "autonomy-freeze:authority-frozen",
                    "autonomy-freeze:docs-current",
                    "autonomy-freeze:gate-green",
                ],
                safe_summary="Freeze the M61-M69 autonomy foundation without adding authority.",
            )
            report = build_autonomy_foundation_freeze_report(request)
            if (
                report.status != AutonomyFoundationFreezeStatus.frozen
                or not report.freeze_only
                or not report.review_only
                or not report.autonomy_foundation_only
                or report.policy_activation_performed
                or report.session_start_performed
                or report.execution_performed
                or report.background_worker_started
                or report.production_authority_granted
                or report.side_effects_performed
            ):
                failures.append(
                    "M70 autonomy foundation freeze report did not remain review-only and no-authority"
                )
            for update, reason in [
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                (
                    {"policy_activation_requested": True},
                    "AUTONOMY_POLICY_ACTIVATION_DENIED",
                ),
                ({"session_start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
                (
                    {"low_risk_dry_run_execution_requested": True},
                    "LOW_RISK_DRY_RUN_EXECUTION_DENIED",
                ),
                ({"background_worker_requested": True}, "BACKGROUND_WORKER_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"model_provider_call_requested": True}, "MODEL_PROVIDER_CALL_DENIED"),
                ({"backend_route_requested": True}, "BACKEND_ROUTE_DENIED"),
                ({"dependency_requested": True}, "DEPENDENCY_CHANGE_DENIED"),
                (
                    {"production_authority_requested": True},
                    "PRODUCTION_AUTHORITY_DENIED",
                ),
                (
                    {"metadata": {"api_key": "secret-value"}},
                    "SECRET_LIKE_AUTONOMY_FOUNDATION_FREEZE_CONTENT_DENIED",
                ),
            ]:
                try:
                    validate_autonomy_foundation_freeze_request(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M70 unsafe autonomy foundation freeze mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M70 unsafe autonomy foundation freeze reason drifted for {reason}: {exc}"
                        )
        except Exception as exc:
            failures.append(f"M70 autonomy foundation freeze validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "autonomy foundation freeze",
            "m61-m69",
            "contract-only",
            "review-only",
            "freeze-only",
            "deterministic",
            "no policy activation",
            "no session start",
            "no low-risk dry-run execution",
            "no autonomous actions",
            "no background worker",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no network tool",
            "no browser automation",
            "no context injection",
            "no memory write",
            "no model/provider call",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "m71 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M70 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m70_autonomy_foundation_freeze_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "autonomy_foundation_authority_granted=True",
            "autonomy_foundation_freeze_authority_granted=True",
            "policy_activation_enabled=True",
            "policy_activation_requested=True",
            "session_start_enabled=True",
            "session_start_requested=True",
            "low_risk_dry_run_execution_enabled=True",
            "low_risk_dry_run_execution_requested=True",
            "autonomous_actions_enabled=True",
            "autonomous_actions_requested=True",
            "background_worker_enabled=True",
            "background_worker_requested=True",
            "execution_enabled=True",
            "execution_requested=True",
            "execution_performed=True",
            "tool_execution_enabled=True",
            "tool_execution_requested=True",
            "shell_execution_enabled=True",
            "shell_execution_requested=True",
            "network_tool_enabled=True",
            "network_tool_requested=True",
            "browser_automation_enabled=True",
            "browser_automation_requested=True",
            "plugin_execution_enabled=True",
            "plugin_execution_requested=True",
            "mobile_sensor_enabled=True",
            "mobile_sensor_requested=True",
            "remote_execution_enabled=True",
            "remote_execution_requested=True",
            "memory_write_enabled=True",
            "memory_write_requested=True",
            "context_injection_enabled=True",
            "context_injection_requested=True",
            "model_provider_call_enabled=True",
            "model_provider_call_requested=True",
            "backend_route_enabled=True",
            "backend_route_requested=True",
            "control_center_control_enabled=True",
            "control_center_control_requested=True",
            "dependency_change_enabled=True",
            "dependency_requested=True",
            "production_authority_enabled=True",
            "production_authority_requested=True",
            "production_authority_granted=True",
            "/autonomy/freeze/activate",
            "/autonomy/freeze/start",
            "/autonomy/session/start",
            "/autonomy/policy/activate",
            "/autonomy/dry-run/execute",
            "/network/fetch",
            "/shell/execute",
            "/browser/click",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/autonomy/foundation_freeze.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run.py",
            "src/ultimate_ai_agent/core/autonomy/risk.py",
            "src/ultimate_ai_agent/core/autonomy/revocation.py",
            "src/ultimate_ai_agent/core/autonomy/approvals.py",
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/simulator.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m70_autonomy_foundation_freeze.py",
            "tests/test_m70_gate_integration.py",
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in (
                "*.py",
                "*.ts",
                "*.tsx",
                "*.js",
                "*.jsx",
                "*.swift",
                "*.yml",
                "*.yaml",
            ):
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        if runtime_subprocess_fragment_allowed(rel, text, fragment):
                            continue
                        failures.append(
                            f"M70 forbidden autonomy foundation freeze fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m70_autonomy_foundation_freeze_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m70_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M70 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m70_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M70 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.74.0" not in text
            or "m70" not in text
            or "autonomy foundation freeze" not in text
        ):
            failures.append(
                "active docs do not identify v0.74.0/M70 Autonomy Foundation Freeze"
            )
        if (
            "m70 is implemented/released" not in text
            and "v0.74.0 implements m70" not in text
        ):
            failures.append("active docs do not mark M70 implemented/released")
        for version_label, milestone, title in [
            ("v0.75.0", "M71", "Network Tool Contract Review"),
            ("v0.80.0", "M76", "OpenWebUI Runtime Bridge v1"),
            ("v0.94.0", "M90", "Shell/Subprocess Hardening Freeze"),
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M71-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M70 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m71_network_tool_contract_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/network/contract_review.py",
            "src/ultimate_ai_agent/core/network/__init__.py",
            "docs/network/NETWORK_TOOL_CONTRACT_REVIEW.md",
            "docs/network/NETWORK_TOOL_CONTRACT_REVIEW_POLICY.md",
            "docs/network/NETWORK_TOOL_CONTRACT_AUTHORITY_BOUNDARY.md",
            "docs/network/M71_TO_M72_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "tests/test_m71_network_tool_contract_review.py",
            "tests/test_m71_gate_integration.py",
        ]
        failures = [
            f"missing M71 network tool contract review file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.network import (
                NetworkToolCapabilityKind,
                NetworkToolContractReviewPolicy,
                NetworkToolContractReviewRequest,
                NetworkToolContractReviewStatus,
                build_network_tool_contract_review_decision,
                validate_network_tool_contract_review_policy,
                validate_network_tool_contract_review_request,
            )

            request = NetworkToolContractReviewRequest(
                review_ref="network-tool-contract-review:m71-gate",
                candidate_ref="network-tool-candidate:m71-read-only-http-fetch",
                actor_ref="actor:foundation-gate",
                proposed_tool_ref="tool:read-only-http-fetch-m72-candidate",
                safe_name="Allowlisted read-only HTTP fetch contract review",
                capability_kind=NetworkToolCapabilityKind.allowlisted_read_only_http_fetch,
                safe_summary="Review a future M72 allowlisted read-only HTTP fetch contract without enabling network calls.",
                allowed_host_policy_ref="network-allowlist-policy:m72-future",
                risk_ref="risk:network-low-read-only-review",
            )
            decision = build_network_tool_contract_review_decision(request)
            if (
                decision.status != NetworkToolContractReviewStatus.review_ready
                or not decision.review_allowed
                or not decision.contract_only
                or not decision.review_only
                or not decision.disabled_by_default
                or not decision.m72_candidate_only
                or not decision.future_milestone_required
                or decision.network_call_allowed
                or decision.http_fetch_allowed
                or decision.tool_execution_allowed
                or decision.backend_route_allowed
                or decision.control_center_control_allowed
                or decision.production_authority_granted
                or decision.receipt_plan.network_call_performed
                or decision.receipt_plan.raw_response_body_stored
                or decision.receipt_plan.credentials_or_cookies_used
                or decision.receipt_plan.side_effects_performed
            ):
                failures.append(
                    "M71 network tool contract review granted network authority or side effects"
                )

            future_decision = build_network_tool_contract_review_decision(
                request.model_copy(
                    update={
                        "candidate_ref": "network-tool-candidate:m71-authenticated-network-action",
                        "capability_kind": NetworkToolCapabilityKind.authenticated_network_action,
                        "safe_name": "Future authenticated network action review",
                    }
                )
            )
            if (
                future_decision.status
                != NetworkToolContractReviewStatus.future_milestone
                or future_decision.network_call_allowed
                or future_decision.http_fetch_allowed
                or "FUTURE_NETWORK_MILESTONE_REQUIRED"
                not in future_decision.reason_codes
            ):
                failures.append(
                    "M71 effectful network capability was not kept future-only"
                )

            for update, reason in [
                ({"network_call_requested": True}, "NETWORK_CALL_DENIED"),
                ({"http_fetch_requested": True}, "HTTP_FETCH_DENIED"),
                (
                    {"unrestricted_network_requested": True},
                    "UNRESTRICTED_NETWORK_DENIED",
                ),
                (
                    {"authenticated_network_requested": True},
                    "AUTHENTICATED_NETWORK_DENIED",
                ),
                (
                    {"credentials_or_cookies_requested": True},
                    "CREDENTIAL_OR_COOKIE_HANDLING_DENIED",
                ),
                ({"request_body_requested": True}, "REQUEST_BODY_DENIED"),
                ({"non_get_method_requested": True}, "NON_GET_METHOD_DENIED"),
                ({"download_or_export_requested": True}, "DOWNLOAD_OR_EXPORT_DENIED"),
                ({"browser_automation_requested": True}, "BROWSER_AUTOMATION_DENIED"),
                ({"provider_model_call_requested": True}, "PROVIDER_MODEL_CALL_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"backend_route_requested": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_requested": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_requested": True}, "DEPENDENCY_CHANGE_DENIED"),
                (
                    {"production_authority_requested": True},
                    "PRODUCTION_AUTHORITY_DENIED",
                ),
                ({"contains_raw_response_body": True}, "RAW_RESPONSE_BODY_DENIED"),
                ({"approval_ref": "approval:m71-gate"}, "APPROVAL_REF_NOT_AUTHORITY"),
                (
                    {"approval_test_ref": "approval_test_m71_gate"},
                    "APPROVAL_TEST_REF_DENIED",
                ),
                (
                    {"metadata": {"api_key": "secret-value"}},
                    "SECRET_LIKE_NETWORK_TOOL_CONTENT_DENIED",
                ),
            ]:
                try:
                    validate_network_tool_contract_review_request(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M71 unsafe network tool request was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M71 unsafe network tool reason drifted for {reason}: {exc}"
                        )

            try:
                validate_network_tool_contract_review_policy(
                    NetworkToolContractReviewPolicy(network_call_enabled=True)
                )
                failures.append(
                    "M71 unsafe network tool policy was not denied: NETWORK_CALL_DENIED"
                )
            except ValueError as exc:
                if "NETWORK_CALL_DENIED" not in str(exc):
                    failures.append(
                        f"M71 unsafe network tool policy reason drifted: {exc}"
                    )
        except Exception as exc:
            failures.append(
                f"M71 network tool contract review validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "network tool contract review",
            "contract-only",
            "review-only",
            "disabled by default",
            "m72 remains future",
            "no network call",
            "no http fetch",
            "no network tool",
            "no authenticated network action",
            "no credentials or cookies",
            "no request body",
            "no non-get method",
            "no download or export",
            "no raw response body",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
        ]:
            if fragment not in docs_text:
                failures.append(f"M71 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m71_network_tool_contract_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "network_call_enabled=True",
            "network_call_requested=True",
            "http_fetch_enabled=True",
            "http_fetch_requested=True",
            "unrestricted_network_enabled=True",
            "unrestricted_network_requested=True",
            "authenticated_network_enabled=True",
            "authenticated_network_requested=True",
            "credentials_or_cookies_enabled=True",
            "credentials_or_cookies_requested=True",
            "request_body_enabled=True",
            "request_body_requested=True",
            "non_get_method_enabled=True",
            "non_get_method_requested=True",
            "download_or_export_enabled=True",
            "download_or_export_requested=True",
            "browser_automation_enabled=True",
            "browser_automation_requested=True",
            "provider_model_call_enabled=True",
            "provider_model_call_requested=True",
            "tool_execution_enabled=True",
            "tool_execution_requested=True",
            "memory_write_enabled=True",
            "memory_write_requested=True",
            "context_injection_enabled=True",
            "context_injection_requested=True",
            "backend_route_enabled=True",
            "backend_route_requested=True",
            "control_center_control_enabled=True",
            "control_center_control_requested=True",
            "dependency_change_enabled=True",
            "dependency_requested=True",
            "production_authority_enabled=True",
            "production_authority_requested=True",
            "production_authority_granted=True",
            "raw_response_body_stored=True",
            "credentials_or_cookies_used=True",
            "/network/fetch",
            "/network/request",
            "/http/fetch",
            "/http/request",
            "/tools/network/execute",
            "/tools/execute",
            "/tool-runtime/execute",
            "/browser/click",
            "/plugins/execute",
            "requests.get(",
            "requests.post(",
            "httpx.get(",
            "httpx.post(",
            "urllib.request.urlopen",
            "websocket",
            "socket.",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/network/contract_review.py",
            "src/ultimate_ai_agent/core/network/__init__.py",
            "src/ultimate_ai_agent/core/tools/runtime/http_fetch.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/autonomy/foundation_freeze.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run.py",
            "src/ultimate_ai_agent/core/autonomy/risk.py",
            "src/ultimate_ai_agent/core/autonomy/revocation.py",
            "src/ultimate_ai_agent/core/autonomy/approvals.py",
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/simulator.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "src/ultimate_ai_agent/core/tools/runtime/adapters.py",
            "src/ultimate_ai_agent/core/tools/runtime/contracts.py",
            "src/ultimate_ai_agent/core/tools/runtime/enums.py",
            "src/ultimate_ai_agent/core/tools/runtime/policy.py",
            "src/ultimate_ai_agent/core/tools/runtime/validation.py",
            "tests/test_m71_network_tool_contract_review.py",
            "tests/test_m71_gate_integration.py",
            "tests/test_m70_autonomy_foundation_freeze.py",
            "tests/test_m70_gate_integration.py",
        }
        allowed_fragments_by_file = {
            "src/ultimate_ai_agent/core/web_access/read_only_http_fetch_transport.py": {
                "socket.",
            },
            "src/ultimate_ai_agent/core/authority/contracts.py": {"websocket"},
            "src/ultimate_ai_agent/core/authority/lane_registry.py": {"websocket"},
            "src/ultimate_ai_agent/core/runtime_gateway/streaming_progress.py": {
                "websocket",
            },
            "apps/control-center/src/api/client.summaryEndpoints.test.ts": {
                "websocket",
            },
            "apps/control-center/src/api/client.ts": {"websocket"},
            "apps/control-center/src/api/types.ts": {"websocket"},
            "apps/control-center/src/components/RuntimeReadinessPanel.tsx": {
                "websocket",
            },
            "apps/control-center/src/mocks/controlCenterData.ts": {"websocket"},
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in (
                "*.py",
                "*.ts",
                "*.tsx",
                "*.js",
                "*.jsx",
                "*.swift",
                "*.yml",
                "*.yaml",
            ):
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if (
                        fragment in text
                        and fragment not in allowed_fragments_by_file.get(rel, set())
                        and not matrix_messaging_fragment_allowed(rel, text, fragment)
                        and not _is_web_hybrid_promoted_static_fragment(
                            rel, fragment, text
                        )
                    ):
                        failures.append(
                            f"M71 forbidden network tool contract fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m71_network_tool_contract_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m71_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M71 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m71_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M71 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.75.0" not in text
            or "m71" not in text
            or "network tool contract review" not in text
        ):
            failures.append(
                "active docs do not identify v0.75.0/M71 Network Tool Contract Review"
            )
        if (
            "m71 is implemented/released" not in text
            and "v0.75.0 implements m71" not in text
        ):
            failures.append("active docs do not mark M71 implemented/released")
        for version_label, milestone, title in [
            ("v0.76.0", "M72", "Read-Only HTTP Fetch Tool, Allowlisted"),
            ("v0.80.0", "M76", "OpenWebUI Runtime Bridge v1"),
            ("v0.94.0", "M90", "Shell/Subprocess Hardening Freeze"),
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M72-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "unrestricted network tool is implemented",
            "authenticated network action is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M71 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m72_read_only_http_fetch_tool(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/runtime/http_fetch.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "src/ultimate_ai_agent/core/tools/runtime/contracts.py",
            "docs/network/READ_ONLY_HTTP_FETCH_TOOL.md",
            "docs/network/READ_ONLY_HTTP_FETCH_POLICY.md",
            "docs/network/READ_ONLY_HTTP_FETCH_AUTHORITY_BOUNDARY.md",
            "docs/network/READ_ONLY_HTTP_FETCH_RECEIPT_PLAN.md",
            "docs/network/M72_TO_M73_BOUNDARY.md",
            "tests/test_m72_read_only_http_fetch_tool.py",
            "tests/test_m72_gate_integration.py",
        ]
        failures = [
            f"missing M72 read-only HTTP fetch file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.tools.runtime import (
                READ_ONLY_HTTP_FETCH_TOOL_NAME,
                READ_ONLY_HTTP_FETCH_TOOL_REF,
                ReadOnlyHttpFetchPolicy,
                ReadOnlyHttpFetchTransportResponse,
                ToolInvocationKind,
                ToolInvocationRequest,
                ToolInvocationStatus,
                ToolRuntimeAdapter,
            )

            def fake_transport(_request: Any, _policy: Any) -> Any:
                return ReadOnlyHttpFetchTransportResponse(
                    status_code=200,
                    content_type="text/plain",
                    body=b"public status\napi_key=hidden-value\n",
                )

            request = ToolInvocationRequest(
                invocation_id="tool-runtime-invocation:m72-gate",
                tool_ref=READ_ONLY_HTTP_FETCH_TOOL_REF,
                tool_name=READ_ONLY_HTTP_FETCH_TOOL_NAME,
                invocation_kind=ToolInvocationKind.read_only_http_fetch,
                replay_key="tool-runtime-replay:m72-gate",
                safe_summary="Allowlisted read-only HTTP fetch.",
                metadata={
                    "request_ref": "http-fetch-request:m72-gate",
                    "url": "https://docs.example.test/status",
                    "allowed_hosts": ["docs.example.test"],
                    "allowed_host_policy_ref": "http-fetch-policy:m72-read-only-allowlisted",
                    "safe_summary": "Fetch a bounded redacted preview from an allowlisted documentation endpoint.",
                },
            )
            decision = ToolRuntimeAdapter().invoke(
                request, http_fetch_transport=fake_transport
            )
            if (
                decision.status != ToolInvocationStatus.http_fetch_completed
                or not decision.invocation_allowed
                or not decision.execution_performed
                or decision.network_call_performed
                or decision.raw_content_stored
                or decision.memory_write_performed
                or decision.model_call_performed
                or decision.shell_execution_performed
                or decision.result is None
                or "hidden-value" in str(decision.result.output)
                or decision.result.output.raw_response_body_stored
                or decision.result.output.raw_headers_stored
                or decision.result.output.absolute_url_returned
                or decision.result.output.context_injection_performed
                or decision.result.output.memory_write_performed
                or decision.result.output.tool_execution_performed
                or decision.result.output.production_authority_granted
                or decision.result.output.side_effects_performed
            ):
                failures.append(
                    "M72 read-only HTTP fetch did not remain bounded, redacted, and non-authoritative"
                )

            no_transport = ToolRuntimeAdapter().invoke(request)
            if (
                no_transport.invocation_allowed
                or "HTTP_FETCH_TRANSPORT_REQUIRED" not in no_transport.reason_codes
            ):
                failures.append(
                    "M72 HTTP fetch without explicit transport was not denied"
                )

            for update, reason in [
                ({"url": "http://docs.example.test/status"}, "HTTPS_ONLY_REQUIRED"),
                ({"url": "https://evil.example/status"}, "HOST_NOT_ALLOWLISTED_DENIED"),
                (
                    {"url": "https://docs.example.test/status?token=value"},
                    "QUERY_STRING_DENIED",
                ),
                ({"method": "POST"}, "NON_GET_METHOD_DENIED"),
                ({"include_raw_response_body": True}, "RAW_RESPONSE_BODY_DENIED"),
                ({"include_raw_headers": True}, "RAW_HEADERS_DENIED"),
                ({"request_body": "payload"}, "REQUEST_BODY_DENIED"),
                ({"request_headers": {"X-Test": "value"}}, "REQUEST_HEADERS_DENIED"),
                ({"download_requested": True}, "DOWNLOAD_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
                ({"browser_automation_requested": True}, "BROWSER_AUTOMATION_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                (
                    {"production_authority_requested": True},
                    "PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                unsafe = request.model_copy(
                    update={"metadata": {**request.metadata, **update}}
                )
                denied = ToolRuntimeAdapter().invoke(
                    unsafe, http_fetch_transport=fake_transport
                )
                if denied.invocation_allowed or reason not in denied.reason_codes:
                    failures.append(
                        f"M72 unsafe HTTP fetch request was not denied with {reason}"
                    )

            try:
                ReadOnlyHttpFetchPolicy(allowed_hosts=("*",))
                failures.append("M72 wildcard allowlist host was not denied")
            except ValueError as exc:
                if "WILDCARD_HOST_DENIED" not in str(exc):
                    failures.append(f"M72 wildcard allowlist reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M72 read-only HTTP fetch validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "read-only http fetch",
            "allowlisted",
            "bounded redacted preview",
            "redaction before return",
            "no credentials or cookies",
            "no request body",
            "no non-get method",
            "no raw response body",
            "no raw headers",
            "no download or export",
            "no context injection",
            "no memory write",
            "no model call",
            "no browser automation",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "m73 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M72 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m72_read_only_http_fetch_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "credentials_allowed=True",
            "cookies_allowed=True",
            "request_body_allowed=True",
            "request_headers_allowed=True",
            "query_string_allowed=True",
            "raw_response_body_allowed=True",
            "raw_headers_allowed=True",
            "download_allowed=True",
            "context_injection_allowed=True",
            "memory_write_allowed=True",
            "model_call_allowed=True",
            "browser_automation_allowed=True",
            "tool_execution_allowed=True",
            "backend_route_allowed=True",
            "production_authority_allowed=True",
            "include_raw_response_body=True",
            "include_raw_headers=True",
            "download_requested=True",
            "context_injection_requested=True",
            "memory_write_requested=True",
            "model_call_requested=True",
            "browser_automation_requested=True",
            "tool_execution_requested=True",
            "backend_route_requested=True",
            "production_authority_requested=True",
            "raw_response_body_stored=True",
            "raw_headers_stored=True",
            "credentials_or_cookies_used=True",
            "/network/fetch",
            "/network/request",
            "/http/fetch",
            "/http/request",
            "/tools/network/execute",
            "/tools/execute",
            "/tool-runtime/execute",
            "/browser/click",
            "/plugins/execute",
            "requests.get(",
            "requests.post(",
            "httpx.get(",
            "httpx.post(",
            "urllib.request.urlopen",
            "websocket",
            "socket.",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/tools/runtime/http_fetch.py",
        }
        allowed_fragments_by_file = {
            "src/ultimate_ai_agent/core/web_access/read_only_http_fetch_transport.py": {
                "socket.",
            },
            "src/ultimate_ai_agent/core/decision_router/turn_contracts.py": {
                "tool_execution_allowed=True",
            },
            "src/ultimate_ai_agent/core/authority/contracts.py": {"websocket"},
            "src/ultimate_ai_agent/core/authority/lane_registry.py": {"websocket"},
            "src/ultimate_ai_agent/core/runtime_gateway/streaming_progress.py": {
                "websocket",
            },
            "apps/control-center/src/api/client.summaryEndpoints.test.ts": {
                "websocket",
            },
            "apps/control-center/src/api/client.ts": {"websocket"},
            "apps/control-center/src/api/types.ts": {"websocket"},
            "apps/control-center/src/components/RuntimeReadinessPanel.tsx": {
                "websocket",
            },
            "apps/control-center/src/mocks/controlCenterData.ts": {"websocket"},
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in (
                "*.py",
                "*.ts",
                "*.tsx",
                "*.js",
                "*.jsx",
                "*.swift",
                "*.yml",
                "*.yaml",
            ):
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if (
                        fragment in text
                        and fragment not in allowed_fragments_by_file.get(rel, set())
                        and not matrix_messaging_fragment_allowed(rel, text, fragment)
                        and not _is_web_hybrid_promoted_static_fragment(
                            rel, fragment, text
                        )
                    ):
                        failures.append(
                            f"M72 forbidden HTTP fetch fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m72_read_only_http_fetch_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m72_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M72 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m72_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M72 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.76.0" not in text
            or "m72" not in text
            or "read-only http fetch tool, allowlisted" not in text
        ):
            failures.append(
                "active docs do not identify v0.76.0/M72 Read-Only HTTP Fetch Tool, Allowlisted"
            )
        if (
            "m72 is implemented/released" not in text
            and "v0.76.0 implements m72" not in text
        ):
            failures.append("active docs do not mark M72 implemented/released")
        for version_label, milestone, title in [
            ("v0.77.0", "M73", "Browser Automation Contract Review"),
            ("v0.80.0", "M76", "OpenWebUI Runtime Bridge v1"),
            ("v0.94.0", "M90", "Shell/Subprocess Hardening Freeze"),
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M73-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "unrestricted network tool is implemented",
            "authenticated network action is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M72 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m73_browser_automation_contract_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/browser/__init__.py",
            "src/ultimate_ai_agent/core/browser/contract_review.py",
            "docs/browser/BROWSER_AUTOMATION_CONTRACT_REVIEW.md",
            "docs/browser/BROWSER_AUTOMATION_CONTRACT_REVIEW_POLICY.md",
            "docs/browser/BROWSER_AUTOMATION_AUTHORITY_BOUNDARY.md",
            "docs/browser/BROWSER_AUTOMATION_RECEIPT_PLAN.md",
            "docs/browser/M73_TO_M74_BOUNDARY.md",
            "tests/test_m73_browser_automation_contract_review.py",
            "tests/test_m73_gate_integration.py",
        ]
        failures = [
            f"missing M73 browser automation contract review file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.browser import (
                BrowserAutomationCapabilityKind,
                BrowserAutomationContractReviewPolicy,
                BrowserAutomationContractReviewRequest,
                BrowserAutomationContractReviewStatus,
                build_browser_automation_contract_review_decision,
                validate_browser_automation_contract_review_policy,
            )

            request = BrowserAutomationContractReviewRequest(
                review_ref="browser-contract-review:m73-gate",
                candidate_ref="browser-contract-candidate:m73-observe-only-adapter",
                actor_ref="actor:foundation-gate",
                proposed_adapter_ref="browser-adapter:m74-observe-only-candidate",
                safe_name="Browser observe-only adapter contract review",
                capability_kind=BrowserAutomationCapabilityKind.observe_only_adapter,
                safe_summary=(
                    "Review a future M74 observe-only browser adapter contract without enabling "
                    "browser automation."
                ),
                safe_browser_policy_ref="browser-policy:m74-future-observe-only",
                risk_ref="risk:browser-review-only",
            )
            decision = build_browser_automation_contract_review_decision(request)
            if (
                decision.status != BrowserAutomationContractReviewStatus.review_ready
                or not decision.review_allowed
                or not decision.contract_only
                or not decision.review_only
                or not decision.disabled_by_default
                or not decision.deterministic
                or not decision.m74_candidate_only
                or not decision.future_milestone_required
                or decision.browser_automation_allowed
                or decision.browser_observe_allowed
                or decision.browser_navigation_allowed
                or decision.browser_click_allowed
                or decision.form_fill_allowed
                or decision.screenshot_allowed
                or decision.dom_read_allowed
                or decision.network_call_allowed
                or decision.tool_execution_allowed
                or decision.backend_route_allowed
                or decision.control_center_control_allowed
                or decision.production_authority_granted
                or decision.receipt_plan.browser_automation_performed
                or decision.receipt_plan.raw_dom_stored
                or decision.receipt_plan.screenshot_stored
                or decision.receipt_plan.side_effects_performed
            ):
                failures.append("M73 browser contract review granted unsafe authority")
            if "M74_REMAINS_FUTURE" not in decision.reason_codes:
                failures.append("M73 decision does not keep M74 future")

            future = build_browser_automation_contract_review_decision(
                request.model_copy(
                    update={
                        "candidate_ref": "browser-contract-candidate:m73-click",
                        "capability_kind": BrowserAutomationCapabilityKind.click,
                    }
                )
            )
            if (
                future.status != BrowserAutomationContractReviewStatus.future_milestone
                or future.browser_click_allowed
                or "FUTURE_BROWSER_MILESTONE_REQUIRED" not in future.reason_codes
            ):
                failures.append(
                    "M73 effectful browser capability was not future-milestone only"
                )

            for update, reason in [
                ({"browser_click_requested": True}, "BROWSER_CLICK_DENIED"),
                ({"browser_navigation_requested": True}, "BROWSER_NAVIGATION_DENIED"),
                ({"form_fill_requested": True}, "FORM_FILL_DENIED"),
                ({"contains_raw_dom": True}, "RAW_DOM_DENIED"),
                ({"contains_screenshot_bytes": True}, "SCREENSHOT_BYTES_DENIED"),
                ({"approval_ref": "approval:m73"}, "APPROVAL_REF_NOT_AUTHORITY"),
                (
                    {"approval_test_ref": "approval_test_m73"},
                    "APPROVAL_TEST_REF_DENIED",
                ),
                (
                    {"authority_refs": ["context-pack:m73"]},
                    "AUTHORITY_REF_NOT_BROWSER_AUTHORITY",
                ),
            ]:
                try:
                    build_browser_automation_contract_review_decision(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M73 unsafe browser review request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M73 reason drift for {reason}: {exc}")

            try:
                validate_browser_automation_contract_review_policy(
                    BrowserAutomationContractReviewPolicy(browser_click_enabled=True)
                )
                failures.append("M73 policy did not deny browser click enablement")
            except ValueError as exc:
                if "BROWSER_CLICK_DENIED" not in str(exc):
                    failures.append(f"M73 policy denial reason drifted: {exc}")
        except Exception as exc:
            failures.append(
                f"M73 browser automation contract review validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "browser automation contract review",
            "contract-only",
            "review-only",
            "disabled by default",
            "m74 remains future",
            "no browser automation",
            "no browser observe",
            "no browser navigation",
            "no browser click",
            "no form fill",
            "no screenshot",
            "no raw dom",
            "no authenticated browser profile",
            "no download or upload",
            "no remote browser",
            "no network interception",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
        ]:
            if fragment not in docs_text:
                failures.append(f"M73 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m73_browser_automation_contract_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "browser_automation_enabled=True",
            "browser_automation_requested=True",
            "browser_observe_enabled=True",
            "browser_observe_requested=True",
            "browser_navigation_enabled=True",
            "browser_navigation_requested=True",
            "browser_click_enabled=True",
            "browser_click_requested=True",
            "form_fill_enabled=True",
            "form_fill_requested=True",
            "screenshot_enabled=True",
            "screenshot_requested=True",
            "dom_read_enabled=True",
            "dom_read_requested=True",
            "authenticated_profile_enabled=True",
            "authenticated_profile_requested=True",
            "download_or_upload_enabled=True",
            "download_or_upload_requested=True",
            "remote_browser_enabled=True",
            "remote_browser_requested=True",
            "network_interception_enabled=True",
            "network_interception_requested=True",
            "network_call_enabled=True",
            "network_call_requested=True",
            "model_call_enabled=True",
            "model_call_requested=True",
            "tool_execution_enabled=True",
            "tool_execution_requested=True",
            "memory_write_enabled=True",
            "memory_write_requested=True",
            "context_injection_enabled=True",
            "context_injection_requested=True",
            "backend_route_enabled=True",
            "backend_route_requested=True",
            "control_center_control_enabled=True",
            "control_center_control_requested=True",
            "dependency_change_enabled=True",
            "dependency_requested=True",
            "production_authority_enabled=True",
            "production_authority_requested=True",
            "production_authority_granted=True",
            "browser_automation_performed=True",
            "browser_click_performed=True",
            "form_fill_performed=True",
            "screenshot_stored=True",
            "raw_dom_stored=True",
            "authenticated_profile_used=True",
            "cookies_or_credentials_used=True",
            "/browser/observe",
            "/browser/click",
            "/browser/navigate",
            "/browser/type",
            "/browser/screenshot",
            "/browser/execute",
            "/browser/run",
            "/browser/session/start",
            "/browser/profile/authenticated",
            "/tools/browser/execute",
            "/tools/execute",
            "/tool-runtime/execute",
            "playwright.",
            "selenium",
            "browser_use",
            "chromedriver",
            "puppeteer",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/browser/contract_review.py",
            "src/ultimate_ai_agent/core/browser/__init__.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/autonomy/foundation_freeze.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run.py",
            "src/ultimate_ai_agent/core/autonomy/risk.py",
            "src/ultimate_ai_agent/core/autonomy/revocation.py",
            "src/ultimate_ai_agent/core/autonomy/approvals.py",
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/simulator.py",
            "src/ultimate_ai_agent/core/autonomy/browser_connector_combined_workflow.py",
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in (
                "*.py",
                "*.ts",
                "*.tsx",
                "*.js",
                "*.jsx",
                "*.swift",
                "*.yml",
                "*.yaml",
            ):
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M73 forbidden browser contract fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])
