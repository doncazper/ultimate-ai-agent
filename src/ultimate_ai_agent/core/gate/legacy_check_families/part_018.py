from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart018Mixin:
    """Legacy checks from m73_browser_automation_contract_route_boundary through m77_openwebui_safe_handoff_route_boundary."""
    def check_m73_browser_automation_contract_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m73_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M73 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m73_roadmap_currentness(
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
            f"missing M73 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.77.0" not in text
            or "m73" not in text
            or "browser automation contract review" not in text
        ):
            failures.append(
                "active docs do not identify v0.77.0/M73 Browser Automation Contract Review"
            )
        if (
            "m73 is implemented/released" not in text
            and "v0.77.0 implements m73" not in text
        ):
            failures.append("active docs do not mark M73 implemented/released")
        for version_label, milestone, title in [
            ("v0.78.0", "M74", "Browser Observe-Only Adapter"),
            ("v0.79.0", "M75", "Browser Action Dry-Run Planner"),
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
                    f"active docs missing planned M74-M100 row: {version_label} / {milestone} — {title}"
                )
        version_tuple = self._active_version_tuple()
        forbidden_fragments = [
            "m74 is implemented",
            "browser observe-only adapter is implemented",
            "browser action dry-run planner is implemented",
            "browser click execution is implemented",
            "browser automation execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
        ]
        if version_tuple >= (0, 78, 0):
            forbidden_fragments = [
                fragment
                for fragment in forbidden_fragments
                if fragment
                not in {
                    "m74 is implemented",
                    "browser observe-only adapter is implemented",
                }
            ]
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M73 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m74_browser_observe_only_adapter(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/browser/__init__.py",
            "src/ultimate_ai_agent/core/browser/observe.py",
            "docs/browser/BROWSER_OBSERVE_ONLY_ADAPTER.md",
            "docs/browser/BROWSER_OBSERVE_ONLY_POLICY.md",
            "docs/browser/BROWSER_OBSERVE_ONLY_RESULT_CONTRACT.md",
            "docs/browser/BROWSER_OBSERVE_ONLY_AUTHORITY_BOUNDARY.md",
            "docs/browser/BROWSER_OBSERVE_ONLY_RECEIPT_PLAN.md",
            "docs/browser/M74_TO_M75_BOUNDARY.md",
            "tests/test_m74_browser_observe_only_adapter.py",
            "tests/test_m74_gate_integration.py",
        ]
        failures = [
            f"missing M74 browser observe-only adapter file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.browser import (
                BrowserObserveOnlyAdapter,
                BrowserObserveOnlyObservation,
                BrowserObserveOnlyPolicy,
                BrowserObserveOnlyRequest,
                BrowserObserveOnlyStatus,
            )

            request = BrowserObserveOnlyRequest(
                request_ref="browser-observe-request:m74-gate",
                target_ref="browser-target:m74-safe-doc",
                safe_url_ref="browser-url:m74-safe-doc",
                safe_summary="Observe an injected safe browser page snapshot without browser control.",
            )

            def transport(_request: Any, _policy: Any) -> Any:
                return BrowserObserveOnlyObservation(
                    title="M74 safe page",
                    safe_url_ref="browser-url:m74-safe-doc",
                    text_preview="Visible status ok\napi_key=gate-secret-value\n",
                    visible_text_bytes=43,
                )

            output = BrowserObserveOnlyAdapter(BrowserObserveOnlyPolicy()).observe(
                request,
                observe_transport=transport,
            )
            if (
                output.status != BrowserObserveOnlyStatus.observation_ready
                or not output.observe_allowed
                or not output.observe_performed
                or output.browser_automation_performed
                or output.navigation_performed
                or output.click_performed
                or output.form_fill_performed
                or output.screenshot_returned
                or output.raw_dom_returned
                or output.authenticated_profile_used
                or output.cookies_or_credentials_used
                or output.network_call_performed
                or output.tool_execution_performed
                or output.memory_write_performed
                or output.context_injection_performed
                or output.backend_route_used
                or output.control_center_control_used
                or output.production_authority_granted
                or output.side_effects_performed
                or "gate-secret-value" in output.redacted_text_preview
                or "BROWSER_OBSERVE_ONLY_ADAPTER_OUTPUT" not in output.reason_codes
                or "M75_REMAINS_FUTURE" not in output.reason_codes
            ):
                failures.append(
                    "M74 browser observe-only adapter output is unsafe or unredacted"
                )

            no_transport = BrowserObserveOnlyAdapter().observe(request)
            if (
                no_transport.status != BrowserObserveOnlyStatus.transport_unavailable
                or no_transport.observe_allowed
                or "BROWSER_OBSERVE_TRANSPORT_REQUIRED" not in no_transport.reason_codes
            ):
                failures.append(
                    "M74 browser observe-only adapter did not require explicit transport"
                )

            for update, reason in [
                ({"click_requested": True}, "BROWSER_CLICK_DENIED"),
                ({"navigation_requested": True}, "BROWSER_NAVIGATION_DENIED"),
                ({"raw_dom_requested": True}, "RAW_DOM_DENIED"),
                ({"screenshot_requested": True}, "SCREENSHOT_DENIED"),
                ({"approval_ref": "approval:m74"}, "APPROVAL_REF_NOT_AUTHORITY"),
                ({"approval_ref": "approval_test_m74"}, "APPROVAL_TEST_REF_DENIED"),
                (
                    {"authority_refs": ["context-pack:m74"]},
                    "AUTHORITY_REF_NOT_BROWSER_OBSERVE_AUTHORITY",
                ),
            ]:
                denied = BrowserObserveOnlyAdapter().observe(
                    request.model_copy(update=update),
                    observe_transport=transport,
                )
                if denied.observe_allowed or reason not in denied.reason_codes:
                    failures.append(
                        f"M74 unsafe browser observe request was not denied with {reason}"
                    )
        except Exception as exc:
            failures.append(
                f"M74 browser observe-only adapter validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "browser observe-only adapter",
            "observe-only",
            "injected observation",
            "redacted visible text",
            "safe refs only",
            "no browser automation",
            "no browser navigation",
            "no browser click",
            "no form fill",
            "no screenshot",
            "no raw dom",
            "no authenticated browser profile",
            "no cookies or credentials",
            "no download or upload",
            "no remote browser",
            "no network interception",
            "no backend route",
            "no control center control",
            "no memory write",
            "no context injection",
            "no production authority",
            "m75 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M74 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m74_browser_observe_only_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "browser_automation_performed=True",
            "browser_navigation_performed=True",
            "browser_click_performed=True",
            "click_performed=True",
            "form_fill_performed=True",
            "screenshot_returned=True",
            "screenshot_stored=True",
            "raw_dom_returned=True",
            "raw_dom_stored=True",
            "authenticated_profile_used=True",
            "cookies_or_credentials_used=True",
            "download_or_upload_performed=True",
            "remote_browser_control_performed=True",
            "network_interception_performed=True",
            "network_call_performed=True",
            "model_call_performed=True",
            "tool_execution_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "backend_route_used=True",
            "control_center_control_used=True",
            "production_authority_granted=True",
            "/browser/observe",
            "/browser/click",
            "/browser/navigate",
            "/browser/type",
            "/browser/screenshot",
            "/browser/dom/raw",
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
            "src/ultimate_ai_agent/core/browser/observe.py",
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
        for root in [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]:
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
                    if fragment in text and not _is_web_hybrid_promoted_static_fragment(
                        rel, fragment, text
                    ):
                        failures.append(
                            f"M74 forbidden browser observe/control fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m74_browser_observe_only_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m74_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M74 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m74_roadmap_currentness(
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
            f"missing M74 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.78.0" not in text
            or "m74" not in text
            or "browser observe-only adapter" not in text
        ):
            failures.append(
                "active docs do not identify v0.78.0/M74 Browser Observe-Only Adapter"
            )
        if (
            "m74 is implemented/released" not in text
            and "v0.78.0 implements m74" not in text
        ):
            failures.append("active docs do not mark M74 implemented/released")
        for version_label, milestone, title in [
            ("v0.79.0", "M75", "Browser Action Dry-Run Planner"),
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
                    f"active docs missing planned M75-M100 row: {version_label} / {milestone} — {title}"
                )
        version_tuple = self._active_version_tuple()
        forbidden_fragments = [
            "m75 is implemented",
            "browser action dry-run planner is implemented",
            "browser click execution is implemented",
            "browser automation execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
        ]
        if version_tuple >= (0, 79, 0):
            forbidden_fragments = [
                fragment
                for fragment in forbidden_fragments
                if fragment
                not in {
                    "m75 is implemented",
                    "browser action dry-run planner is implemented",
                }
            ]
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M74 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m75_browser_action_dry_run_planner(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/browser/__init__.py",
            "src/ultimate_ai_agent/core/browser/action_dry_run.py",
            "docs/browser/BROWSER_ACTION_DRY_RUN_PLANNER.md",
            "docs/browser/BROWSER_ACTION_DRY_RUN_POLICY.md",
            "docs/browser/BROWSER_ACTION_DRY_RUN_RESULT_CONTRACT.md",
            "docs/browser/BROWSER_ACTION_DRY_RUN_AUTHORITY_BOUNDARY.md",
            "docs/browser/BROWSER_ACTION_DRY_RUN_RECEIPT_PLAN.md",
            "docs/browser/M75_TO_M76_BOUNDARY.md",
            "tests/test_m75_browser_action_dry_run_planner.py",
            "tests/test_m75_browser_action_gate_integration.py",
        ]
        failures = [
            f"missing M75 browser action dry-run planner file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.browser import (
                BrowserActionDryRunActionKind,
                BrowserActionDryRunPlannerRequest,
                BrowserActionDryRunPlannerStatus,
                BrowserActionDryRunStep,
                build_browser_action_dry_run_plan_via_web_access_gateway,
            )

            request = BrowserActionDryRunPlannerRequest(
                plan_ref="browser-action-plan:m75-gate",
                actor_ref="actor:m75-gate",
                target_ref="browser-target:m75-gate",
                source_observation_ref="browser-observe-output:m74-gate",
                safe_url_ref="browser-url:m75-gate",
                safe_summary="Plan a dry-run browser action without executing browser control.",
                steps=[
                    BrowserActionDryRunStep(
                        step_ref="browser-action-step:m75-gate-click",
                        action_kind=BrowserActionDryRunActionKind.click,
                        safe_target_ref="browser-target:m75-gate-button",
                        safe_intent="Dry-run plan to click a reviewed safe target.",
                    )
                ],
            )
            plan = build_browser_action_dry_run_plan_via_web_access_gateway(request)
            if (
                plan.status != BrowserActionDryRunPlannerStatus.plan_ready
                or not plan.plan_valid_for_review
                or not plan.dry_run_only
                or plan.browser_action_execution_allowed
                or plan.browser_action_execution_performed
                or plan.browser_session_started
                or plan.navigation_performed
                or plan.click_performed
                or plan.form_fill_performed
                or plan.screenshot_returned
                or plan.raw_dom_returned
                or plan.authenticated_profile_used
                or plan.cookies_or_credentials_used
                or plan.network_call_performed
                or plan.tool_execution_performed
                or plan.memory_write_performed
                or plan.context_injection_performed
                or plan.backend_route_used
                or plan.control_center_control_used
                or plan.production_authority_granted
                or plan.side_effects_performed
                or "M75_BROWSER_ACTION_DRY_RUN_PLAN" not in plan.reason_codes
                or "M76_REMAINS_FUTURE" not in plan.reason_codes
            ):
                failures.append(
                    "M75 browser action dry-run plan is unsafe or executing"
                )

            for update, reason in [
                (
                    {"browser_action_execution_requested": True},
                    "BROWSER_ACTION_EXECUTION_DENIED",
                ),
                ({"click_execution_requested": True}, "BROWSER_CLICK_EXECUTION_DENIED"),
                ({"raw_dom_requested": True}, "RAW_DOM_DENIED"),
                ({"screenshot_requested": True}, "SCREENSHOT_DENIED"),
                ({"approval_ref": "approval:m75"}, "APPROVAL_REF_NOT_AUTHORITY"),
                ({"approval_ref": "approval_test_m75"}, "APPROVAL_TEST_REF_DENIED"),
                (
                    {"authority_refs": ["context-pack:m75"]},
                    "AUTHORITY_REF_NOT_BROWSER_ACTION_AUTHORITY",
                ),
            ]:
                denied = build_browser_action_dry_run_plan_via_web_access_gateway(
                    request.model_copy(update=update)
                )
                if denied.plan_valid_for_review or reason not in denied.reason_codes:
                    failures.append(
                        f"M75 unsafe browser action plan request was not denied with {reason}"
                    )
        except Exception as exc:
            failures.append(
                f"M75 browser action dry-run planner validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "browser action dry-run planner",
            "dry-run only",
            "reviewable action plan",
            "safe refs only",
            "no browser action execution",
            "no browser session start",
            "no browser navigation execution",
            "no browser click execution",
            "no form fill execution",
            "no screenshot",
            "no raw dom",
            "no authenticated browser profile",
            "no cookies or credentials",
            "no download or upload",
            "no remote browser",
            "no network interception",
            "no backend route",
            "no control center control",
            "no memory write",
            "no context injection",
            "no dependency",
            "no production authority",
            "m76 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M75 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m75_browser_action_dry_run_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "browser_action_execution_performed=True",
            "browser_session_started=True",
            "navigation_performed=True",
            "click_performed=True",
            "form_fill_performed=True",
            "screenshot_returned=True",
            "screenshot_stored=True",
            "raw_dom_returned=True",
            "raw_dom_stored=True",
            "authenticated_profile_used=True",
            "cookies_or_credentials_used=True",
            "download_or_upload_performed=True",
            "remote_browser_control_performed=True",
            "network_interception_performed=True",
            "network_call_performed=True",
            "model_call_performed=True",
            "tool_execution_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "backend_route_used=True",
            "control_center_control_used=True",
            "production_authority_granted=True",
            "/browser/actions/plan",
            "/browser/actions/run",
            "/browser/actions/execute",
            "/browser/action/execute",
            "/browser/click",
            "/browser/navigate",
            "/browser/type",
            "/browser/screenshot",
            "/browser/dom/raw",
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
            "src/ultimate_ai_agent/core/browser/action_dry_run.py",
            "src/ultimate_ai_agent/core/browser/observe.py",
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
        for root in [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]:
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
                    if fragment in text and not _is_web_hybrid_promoted_static_fragment(
                        rel, fragment, text
                    ):
                        failures.append(
                            f"M75 forbidden browser action fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m75_browser_action_dry_run_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m75_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M75 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m75_roadmap_currentness(
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
            f"missing M75 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.79.0" not in text
            or "m75" not in text
            or "browser action dry-run planner" not in text
        ):
            failures.append(
                "active docs do not identify v0.79.0/M75 Browser Action Dry-Run Planner"
            )
        if (
            "m75 is implemented/released" not in text
            and "v0.79.0 implements m75" not in text
        ):
            failures.append("active docs do not mark M75 implemented/released")
        for version_label, milestone, title in [
            ("v0.80.0", "M76", "OpenWebUI Runtime Bridge v1"),
            ("v0.81.0", "M77", "OpenWebUI Safe Handoff Execution"),
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
                    f"active docs missing planned M76-M100 row: {version_label} / {milestone} — {title}"
                )
        forbidden_fragments = [
            "browser click execution is implemented",
            "browser automation execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
        ]
        if (self._active_version_tuple() or (0, 0, 0)) < (0, 80, 0):
            forbidden_fragments.extend(
                [
                    "m76 is implemented",
                    "openwebui runtime bridge v1 is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M75 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m76_openwebui_runtime_bridge_v1(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/openwebui_bridge/__init__.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/runtime.py",
            "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_V1.md",
            "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_POLICY.md",
            "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_RESULT_CONTRACT.md",
            "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_AUTHORITY_BOUNDARY.md",
            "docs/openwebui/OPENWEBUI_RUNTIME_BRIDGE_RECEIPT_PLAN.md",
            "docs/openwebui/M76_TO_M77_BOUNDARY.md",
            "tests/test_m76_openwebui_runtime_bridge.py",
            "tests/test_m76_openwebui_runtime_bridge_gate_integration.py",
        ]
        failures = [
            f"missing M76 OpenWebUI runtime bridge file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.openwebui_bridge import (
                OpenWebUIRuntimeBridgeRequest,
                OpenWebUIRuntimeBridgeStatus,
                build_openwebui_runtime_bridge_envelope,
            )

            request = OpenWebUIRuntimeBridgeRequest(
                bridge_request_ref="openwebui-runtime-bridge-request:m76-gate",
                session_ref="openwebui-session:m76-gate",
                safe_conversation_ref="openwebui-safe-conversation:m76-gate",
                actor_ref="actor:m76-gate",
                safe_intent_summary="Prepare a review-only OpenWebUI bridge envelope.",
            )
            envelope = build_openwebui_runtime_bridge_envelope(request)
            if (
                envelope.status != OpenWebUIRuntimeBridgeStatus.review_envelope_ready
                or envelope.raw_prompt_returned
                or envelope.raw_provider_payload_returned
                or envelope.raw_content_returned
                or envelope.model_output_authoritative
                or envelope.openwebui_called
                or envelope.provider_called
                or envelope.model_called
                or envelope.tool_executed
                or envelope.memory_written
                or envelope.context_injected
                or envelope.network_called
                or envelope.credential_cookie_accessed
                or envelope.approval_granted
                or envelope.handoff_executed
                or envelope.production_authority_granted
                or envelope.side_effects_performed
                or envelope.receipt_plan.openwebui_runtime_call_performed
                or envelope.receipt_plan.raw_prompt_stored
                or envelope.receipt_plan.raw_provider_payload_stored
                or envelope.receipt_plan.raw_content_stored
                or "M76_OPENWEBUI_RUNTIME_BRIDGE_V1" not in envelope.reason_codes
                or "M77_REMAINS_FUTURE" not in envelope.reason_codes
            ):
                failures.append(
                    "M76 OpenWebUI runtime bridge envelope is unsafe or executing"
                )

            for update, reason in [
                ({"raw_prompt_present": True}, "RAW_PROMPT_DENIED"),
                ({"raw_provider_payload_present": True}, "RAW_PROVIDER_PAYLOAD_DENIED"),
                (
                    {"openwebui_runtime_call_requested": True},
                    "OPENWEBUI_RUNTIME_CALL_DENIED",
                ),
                ({"openwebui_handoff_requested": True}, "OPENWEBUI_HANDOFF_DENIED"),
                ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
                ({"model_authority_requested": True}, "MODEL_AUTHORITY_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
                ({"network_call_requested": True}, "OPENWEBUI_NETWORK_CALL_DENIED"),
                (
                    {"credential_cookie_access_requested": True},
                    "CREDENTIAL_COOKIE_ACCESS_DENIED",
                ),
                (
                    {"production_authority_requested": True},
                    "PRODUCTION_AUTHORITY_DENIED",
                ),
                ({"approval_ref": "approval_test_m76"}, "APPROVAL_TEST_REF_DENIED"),
            ]:
                try:
                    build_openwebui_runtime_bridge_envelope(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M76 unsafe OpenWebUI bridge request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M76 unsafe OpenWebUI bridge request raised {exc!s}, expected {reason}"
                        )
        except Exception as exc:
            failures.append(f"M76 OpenWebUI runtime bridge validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "openwebui runtime bridge v1",
            "review-only bridge envelope",
            "safe refs only",
            "redacted summary only",
            "python agent core remains authority",
            "openwebui is a shell/bridge, not the brain",
            "no live openwebui connection",
            "no openwebui runtime call",
            "no provider call",
            "no model call",
            "no model authority",
            "no tool execution",
            "no memory write",
            "no context injection",
            "no network call",
            "no credentials or cookies",
            "no raw prompt",
            "no raw provider payload",
            "no raw content",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
            "m77 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M76 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m76_openwebui_runtime_bridge_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "openwebui_runtime_call_performed=True",
            "openwebui_called=True",
            "provider_called=True",
            "provider_call_performed=True",
            "model_called=True",
            "model_call_performed=True",
            "model_output_authoritative=True",
            "tool_executed=True",
            "tool_execution_performed=True",
            "memory_written=True",
            "memory_write_performed=True",
            "context_injected=True",
            "context_injection_performed=True",
            "network_called=True",
            "network_call_performed=True",
            "credential_cookie_accessed=True",
            "credential_cookie_access_performed=True",
            "raw_prompt_returned=True",
            "raw_provider_payload_returned=True",
            "raw_content_returned=True",
            "handoff_executed=True",
            "production_authority_granted=True",
            "/openwebui/runtime/bridge",
            "/openwebui/runtime/handoff",
            "/openwebui/runtime/execute",
            "/openwebui/chat/send",
            "/openwebui/model/call",
            "/openwebui/provider/call",
            "/openwebui/tools/execute",
            "/openwebui/memory/write",
            "/openwebui/context/inject",
            "/openwebui/raw-payload",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/__init__.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/adapter.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/conversation.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/enums.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/manifests.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/policy.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/receipts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/runtime.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/openapi.py",
        }
        for root in [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]:
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
                    if fragment in text and not _is_web_hybrid_promoted_static_fragment(
                        rel, fragment, text
                    ):
                        failures.append(
                            f"M76 forbidden OpenWebUI runtime fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m76_openwebui_runtime_bridge_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m76_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M76 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m76_roadmap_currentness(
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
            f"missing M76 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.80.0" not in text
            or "m76" not in text
            or "openwebui runtime bridge v1" not in text
        ):
            failures.append(
                "active docs do not identify v0.80.0/M76 OpenWebUI Runtime Bridge v1"
            )
        if (
            "m76 is implemented/released" not in text
            and "v0.80.0 implements m76" not in text
        ):
            failures.append("active docs do not mark M76 implemented/released")
        for version_label, milestone, title in [
            ("v0.81.0", "M77", "OpenWebUI Safe Handoff Execution"),
            ("v0.82.0", "M78", "Plugin Manifest Security Model"),
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
                    f"active docs missing planned M77-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "openwebui safe handoff execution is implemented",
            "openwebui runtime calls are implemented",
            "model authority is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M76 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m77_openwebui_safe_handoff_execution(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/openwebui_bridge/__init__.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/runtime.py",
            "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_EXECUTION.md",
            "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_POLICY.md",
            "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_RESULT_CONTRACT.md",
            "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_AUTHORITY_BOUNDARY.md",
            "docs/openwebui/OPENWEBUI_SAFE_HANDOFF_RECEIPT_PLAN.md",
            "docs/openwebui/M77_TO_M78_BOUNDARY.md",
            "tests/test_m77_openwebui_safe_handoff_execution.py",
            "tests/test_m77_openwebui_safe_handoff_gate_integration.py",
        ]
        failures = [
            f"missing M77 OpenWebUI safe handoff file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.openwebui_bridge import (
                OpenWebUIRuntimeBridgeRequest,
                OpenWebUISafeHandoffRequest,
                OpenWebUISafeHandoffStatus,
                build_openwebui_runtime_bridge_envelope,
                build_openwebui_safe_handoff_result,
            )

            envelope = build_openwebui_runtime_bridge_envelope(
                OpenWebUIRuntimeBridgeRequest(
                    bridge_request_ref="openwebui-runtime-bridge-request:m77-gate",
                    session_ref="openwebui-session:m77-gate",
                    safe_conversation_ref="openwebui-safe-conversation:m77-gate",
                    actor_ref="actor:m77-gate",
                    safe_intent_summary="Prepare a safe OpenWebUI handoff.",
                )
            )
            request = OpenWebUISafeHandoffRequest(
                handoff_request_ref="openwebui-safe-handoff-request:m77-gate",
                bridge_envelope_ref=envelope.bridge_envelope_ref,
                session_ref=envelope.session_ref,
                safe_conversation_ref=envelope.safe_conversation_ref,
                actor_ref=envelope.actor_ref,
                approval_ref="approval:m77-gate",
                approved_bridge_envelope_ref=envelope.bridge_envelope_ref,
                approved_session_ref=envelope.session_ref,
                approved_safe_conversation_ref=envelope.safe_conversation_ref,
                approved_actor_ref=envelope.actor_ref,
                safe_handoff_summary="Record an exact-bound safe handoff inside Agent Core.",
            )
            result = build_openwebui_safe_handoff_result(request)
            if (
                result.status != OpenWebUISafeHandoffStatus.safe_handoff_executed
                or not result.safe_handoff_executed
                or result.raw_prompt_returned
                or result.raw_provider_payload_returned
                or result.raw_content_returned
                or result.model_output_authoritative
                or result.openwebui_called
                or result.provider_called
                or result.model_called
                or result.tool_executed
                or result.memory_written
                or result.context_injected
                or result.network_called
                or result.credential_cookie_accessed
                or result.production_authority_granted
                or result.side_effects_performed
                or not result.receipt_plan.safe_handoff_recorded
                or result.receipt_plan.openwebui_runtime_call_performed
                or result.receipt_plan.raw_prompt_stored
                or result.receipt_plan.raw_provider_payload_stored
                or result.receipt_plan.raw_content_stored
                or "M77_OPENWEBUI_SAFE_HANDOFF_EXECUTION" not in result.reason_codes
                or "M78_REMAINS_FUTURE" not in result.reason_codes
            ):
                failures.append(
                    "M77 OpenWebUI safe handoff result is unsafe or over-authoritative"
                )

            for update, reason in [
                ({"approval_ref": None}, "APPROVAL_REF_REQUIRED"),
                ({"approval_ref": "approval_test_m77"}, "APPROVAL_TEST_REF_DENIED"),
                (
                    {
                        "approved_bridge_envelope_ref": "openwebui-runtime-bridge-envelope:other"
                    },
                    "APPROVAL_BINDING_MISMATCH",
                ),
                ({"approval_expired": True}, "APPROVAL_EXPIRED_DENIED"),
                ({"approval_revoked": True}, "APPROVAL_REVOKED_DENIED"),
                ({"approval_replayed": True}, "APPROVAL_REPLAY_DENIED"),
                ({"raw_provider_payload_present": True}, "RAW_PROVIDER_PAYLOAD_DENIED"),
                (
                    {"openwebui_runtime_call_requested": True},
                    "OPENWEBUI_RUNTIME_CALL_DENIED",
                ),
                ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
                ({"model_authority_requested": True}, "MODEL_AUTHORITY_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
                ({"network_call_requested": True}, "OPENWEBUI_NETWORK_CALL_DENIED"),
                (
                    {"credential_cookie_access_requested": True},
                    "CREDENTIAL_COOKIE_ACCESS_DENIED",
                ),
                (
                    {"production_authority_requested": True},
                    "PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    build_openwebui_safe_handoff_result(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M77 unsafe OpenWebUI handoff request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M77 unsafe OpenWebUI handoff request raised {exc!s}, expected {reason}"
                        )
        except Exception as exc:
            failures.append(f"M77 OpenWebUI safe handoff validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "openwebui safe handoff execution",
            "exact approval binding",
            "safe handoff result",
            "agent core remains authority",
            "openwebui is a shell/bridge, not the brain",
            "no live openwebui connection",
            "no openwebui runtime call",
            "no provider call",
            "no model call",
            "no model authority",
            "no tool execution",
            "no memory write",
            "no context injection",
            "no network call",
            "no credentials or cookies",
            "no raw prompt",
            "no raw provider payload",
            "no raw content",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
            "m78 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M77 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m77_openwebui_safe_handoff_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "openwebui_runtime_call_performed=True",
            "openwebui_called=True",
            "provider_called=True",
            "provider_call_performed=True",
            "model_called=True",
            "model_call_performed=True",
            "model_output_authoritative=True",
            "tool_executed=True",
            "tool_execution_performed=True",
            "memory_written=True",
            "memory_write_performed=True",
            "context_injected=True",
            "context_injection_performed=True",
            "network_called=True",
            "network_call_performed=True",
            "credential_cookie_accessed=True",
            "credential_cookie_access_performed=True",
            "raw_prompt_returned=True",
            "raw_provider_payload_returned=True",
            "raw_content_returned=True",
            "production_authority_granted=True",
            "/openwebui/runtime/handoff",
            "/openwebui/runtime/execute",
            "/openwebui/handoff/execute",
            "/openwebui/chat/send",
            "/openwebui/model/call",
            "/openwebui/provider/call",
            "/openwebui/tools/execute",
            "/openwebui/memory/write",
            "/openwebui/context/inject",
            "/openwebui/raw-payload",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/__init__.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/enums.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/runtime.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/openapi.py",
        }
        for root in [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]:
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
                    if fragment in text and not _is_web_hybrid_promoted_static_fragment(
                        rel, fragment, text
                    ):
                        failures.append(
                            f"M77 forbidden OpenWebUI handoff fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m77_openwebui_safe_handoff_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m77_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M77 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
