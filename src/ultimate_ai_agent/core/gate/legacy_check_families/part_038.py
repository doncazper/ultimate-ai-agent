from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart038Mixin:
    """Legacy checks from m137_browser_connector_combined_workflow_contracts through m139_roadmap_currentness."""
    def check_m137_browser_connector_combined_workflow_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/browser_connector_combined_workflow.py",
            "docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW.md",
            "docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_POLICY.md",
            "docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_RECEIPT_PLAN.md",
            "docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_NON_GOALS.md",
            "docs/autonomy/M137_TO_M138_BOUNDARY.md",
            "docs/release_notes/checkpoint_m137.md",
            "docs/archive/checkpoints/m137/README_IMPORT.md",
            "docs/archive/checkpoints/m137/master_plan.md",
            "tests/test_m137_browser_connector_combined_workflow.py",
            "tests/test_m137_gate_integration.py",
        ]
        failures = [
            f"missing M137 browser connector combined workflow file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m137_browser_connector_combined_workflow import _request
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                BrowserConnectorCombinedWorkflowStatus,
                build_browser_connector_combined_workflow_decision,
                validate_browser_connector_combined_workflow_decision,
            )

            decision = build_browser_connector_combined_workflow_decision(_request())
            if (
                decision.status
                != BrowserConnectorCombinedWorkflowStatus.ready_for_review
                or decision.selected_mode
                != AutonomyAuthorityMode.trusted_recurring_automation
                or not decision.contract_only
                or not decision.review_only
                or not decision.browser_connector_combined_workflow_only
                or not decision.safe_refs_only
                or not decision.exact_scope_bound
                or not decision.mode5_bound
                or not decision.m136_dependency_execution_bound
                or not decision.m135_recovery_planner_bound
                or not decision.m134_human_checkpoint_bound
                or not decision.m133_supervisor_bound
                or not decision.m132_trusted_workflow_bound
                or not decision.browser_plan_bound
                or not decision.connector_plan_bound
                or not decision.combined_dependency_graph_bound
                or not decision.approval_bundle_bound
                or not decision.no_effect_receipt_required
                or decision.combined_workflow_runtime_authorized
                or decision.browser_action_authorized
                or decision.browser_action_performed
                or decision.connector_runtime_authorized
                or decision.connector_action_authorized
                or decision.connector_write_performed
                or decision.account_auth_performed
                or decision.dependency_execution_authorized
                or decision.dependency_execution_performed
                or decision.tool_execution_performed
                or decision.execution_performed
                or decision.backend_route_added
                or decision.dependency_added
                or decision.beta_release_enabled
                or decision.production_authority_granted
                or "M137_BROWSER_CONNECTOR_COMBINED_WORKFLOW_CONTRACT_ONLY"
                not in decision.reason_codes
                or "M138_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M137 browser connector combined workflow decision is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"combined_workflow_runtime_authorized": True},
                    "M137_COMBINED_WORKFLOW_RUNTIME_DENIED",
                ),
                ({"browser_action_authorized": True}, "M137_BROWSER_ACTION_DENIED"),
                ({"browser_action_performed": True}, "M137_BROWSER_ACTION_DENIED"),
                ({"browser_click_performed": True}, "M137_BROWSER_CLICK_DENIED"),
                ({"browser_form_performed": True}, "M137_BROWSER_FORM_DENIED"),
                (
                    {"connector_runtime_authorized": True},
                    "M137_CONNECTOR_RUNTIME_DENIED",
                ),
                ({"connector_action_authorized": True}, "M137_CONNECTOR_ACTION_DENIED"),
                ({"connector_write_performed": True}, "M137_CONNECTOR_WRITE_DENIED"),
                ({"account_auth_performed": True}, "M137_ACCOUNT_AUTH_DENIED"),
                (
                    {"dependency_execution_performed": True},
                    "M137_DEPENDENCY_EXECUTION_DENIED",
                ),
                ({"tool_execution_performed": True}, "M137_TOOL_EXECUTION_DENIED"),
                ({"backend_route_added": True}, "M137_BACKEND_ROUTE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M137_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_browser_connector_combined_workflow_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M137 unsafe workflow mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M137 unsafe workflow mutation raised {exc!s}")
            try:
                validate_browser_connector_combined_workflow_decision(
                    decision.model_copy(
                        update={
                            "receipt_plan": decision.receipt_plan.model_copy(
                                update={"store_raw_browser_dom": True}
                            )
                        }
                    )
                )
                failures.append("M137 receipt plan allowed raw browser DOM storage")
            except ValueError as exc:
                if "M137_RAW_BROWSER_DOM_DENIED" not in str(exc):
                    failures.append(
                        f"M137 raw browser DOM receipt mutation raised {exc!s}"
                    )
        except Exception as exc:
            failures.append(
                f"M137 browser connector combined workflow validation failed: {exc}"
            )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "autonomous browser + connector combined workflows",
            "contract-only",
            "review-only",
            "browser-connector-combined-workflow-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "exact scope",
            "mode 5",
            "m136 cross-tool dependency execution decision",
            "m135 autonomous recovery planner decision",
            "m134 human checkpoint scheduling decision",
            "m133 supervisor decision",
            "m132 trusted workflow decision",
            "browser workflow",
            "browser observation",
            "browser action plan refs",
            "connector workflow",
            "connector account scope",
            "connector action plan refs",
            "workflow step refs",
            "combined dependency graph",
            "dependency order refs",
            "safe handoff",
            "dry-run plan",
            "approval bundle",
            "human checkpoint",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no browser action",
            "no connector action",
            "no account auth",
            "no dependency execution",
            "no tool execution",
            "no shell execution",
            "no network access",
            "no plugin execution",
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "m138 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M137 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m137_browser_connector_combined_workflow_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "combined_workflow_runtime_enabled=True",
            "browser_action_enabled=True",
            "browser_navigation_enabled=True",
            "browser_click_enabled=True",
            "browser_form_enabled=True",
            "browser_download_enabled=True",
            "browser_upload_enabled=True",
            "authenticated_browser_enabled=True",
            "connector_runtime_enabled=True",
            "connector_read_runtime_enabled=True",
            "connector_write_enabled=True",
            "connector_send_enabled=True",
            "connector_delete_enabled=True",
            "account_auth_enabled=True",
            "dependency_execution_enabled=True",
            "tool_execution_enabled=True",
            "execution_enabled=True",
            "shell_execution_enabled=True",
            "network_access_enabled=True",
            "plugin_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "combined_workflow_runtime_authorized=True",
            "browser_action_authorized=True",
            "browser_action_performed=True",
            "browser_click_performed=True",
            "browser_form_performed=True",
            "connector_runtime_authorized=True",
            "connector_action_authorized=True",
            "connector_write_performed=True",
            "account_auth_performed=True",
            "dependency_execution_performed=True",
            "tool_execution_performed=True",
            "/autonomy/browser-connector-combined-workflow",
            "/autonomy/browser-connector-combined-workflow/start",
            "/combined-workflows/run",
            "/browser/actions/run",
            "/browser/navigate",
            "/browser/click",
            "/browser/form",
            "/browser/download",
            "/browser/upload",
            "/connectors/runtime",
            "/connectors/read",
            "/connectors/write",
            "/connectors/send",
            "/connectors/delete",
            "/connectors/auth",
            "/accounts/auth",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/browser_connector_combined_workflow.py",
            "src/ultimate_ai_agent/core/autonomy/cross_tool_dependency_execution.py",
            "src/ultimate_ai_agent/core/autonomy/autonomous_recovery_planner.py",
            "src/ultimate_ai_agent/core/autonomy/human_checkpoint_scheduling.py",
            "src/ultimate_ai_agent/core/autonomy/long_running_task_supervisor.py",
            "src/ultimate_ai_agent/core/autonomy/trusted_recurring_workflow.py",
            "src/ultimate_ai_agent/core/autonomy/mode4_scoped_work_session.py",
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
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if ".test." in rel or _is_static_safety_scan_allowed_file(
                    rel, allowed_files
                ):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M137 forbidden browser connector workflow fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m137_browser_connector_combined_workflow_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m137_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M137 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m137_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
        ]
        failures = [
            f"missing M137 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m137" not in text
            or "autonomous browser + connector combined workflows" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M137 Autonomous Browser + Connector Combined Workflows"
            )
        if (
            "m137 is implemented/released" not in text
            and "checkpoint m137 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M137 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m137",
                "pre-alpha checkpoint",
                "m137",
                "autonomous browser + connector combined workflows",
                "implemented/released",
            ),
            (
                "checkpoint m138",
                "pre-alpha checkpoint",
                "m138",
                "autonomous error handling guardrails",
                "planned/provisional",
            ),
            (
                "v1.2.0-alpha",
                "alpha",
                "m150",
                "ultimate ai agent v1.2.0-alpha",
                "planned/provisional",
            ),
        ]:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | {status} |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing expected M137-M138/M139-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "autonomy abuse/loop detection is implemented",
            "m139 autonomy abuse/loop detection is implemented",
            "error handling guardrail runtime is implemented",
            "browser action execution is implemented",
            "connector action execution is implemented",
            "combined workflow runtime is implemented",
            "dependency execution runtime is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "network access is implemented",
            "browser automation is implemented",
            "browser forms are implemented",
            "plugin execution is implemented",
            "connector runtime is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m139 dependency is added",
            "beta is released",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M137 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m138_autonomous_error_handling_guardrails_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/error_handling_guardrails.py",
            "docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS.md",
            "docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_POLICY.md",
            "docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_RECEIPT_PLAN.md",
            "docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_NON_GOALS.md",
            "docs/autonomy/M138_TO_M139_BOUNDARY.md",
            "docs/release_notes/checkpoint_m138.md",
            "docs/archive/checkpoints/m138/README_IMPORT.md",
            "docs/archive/checkpoints/m138/master_plan.md",
            "tests/test_m138_error_handling_guardrails.py",
            "tests/test_m138_gate_integration.py",
        ]
        failures = [
            f"missing M138 error handling guardrail file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m138_error_handling_guardrails import _request
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyRiskClass,
                ErrorHandlingGuardrailStatus,
                build_error_handling_guardrail_decision,
                validate_error_handling_guardrail_decision,
            )

            decision = build_error_handling_guardrail_decision(_request())
            if (
                decision.status != ErrorHandlingGuardrailStatus.ready_for_review
                or decision.selected_mode
                != AutonomyAuthorityMode.trusted_recurring_automation
                or decision.max_risk_class != AutonomyRiskClass.low
                or not decision.contract_only
                or not decision.review_only
                or not decision.autonomous_error_handling_guardrails_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.exact_scope_bound
                or not decision.mode5_bound
                or not decision.m137_browser_connector_workflow_bound
                or not decision.m136_dependency_execution_bound
                or not decision.m135_recovery_planner_bound
                or not decision.m134_human_checkpoint_bound
                or not decision.m133_supervisor_bound
                or not decision.m132_trusted_workflow_bound
                or not decision.error_signal_bound
                or not decision.guardrail_policy_bound
                or not decision.retry_policy_bound
                or not decision.fallback_policy_bound
                or not decision.escalation_policy_bound
                or not decision.recovery_plan_bound
                or not decision.rollback_plan_bound
                or not decision.resume_plan_bound
                or not decision.human_checkpoint_bound
                or not decision.audit_replay_bound
                or not decision.revocation_bound
                or not decision.kill_switch_bound
                or not decision.no_effect_receipt_required
                or decision.mode5_runtime_authorized
                or decision.error_handling_runtime_authorized
                or decision.error_guardrail_runtime_started
                or decision.autonomous_recovery_execution_authorized
                or decision.retry_execution_authorized
                or decision.retry_execution_performed
                or decision.rollback_execution_authorized
                or decision.rollback_execution_performed
                or decision.resume_execution_performed
                or decision.fallback_action_performed
                or decision.escalation_action_performed
                or decision.loop_recovery_performed
                or decision.dependency_execution_authorized
                or decision.dependency_execution_performed
                or decision.browser_action_performed
                or decision.connector_action_performed
                or decision.connector_write_performed
                or decision.account_auth_performed
                or decision.tool_execution_authorized
                or decision.tool_execution_performed
                or decision.execution_authorized
                or decision.execution_performed
                or decision.backend_route_added
                or decision.dependency_added
                or decision.beta_release_enabled
                or decision.production_authority_granted
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or decision.receipt_plan.store_raw_error_log
                or decision.receipt_plan.store_raw_stack_trace
                or decision.receipt_plan.retry_execution_performed
                or decision.receipt_plan.rollback_execution_performed
                or decision.receipt_plan.resume_execution_performed
                or decision.receipt_plan.recovery_execution_performed
                or "M138_AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_CONTRACT_ONLY"
                not in decision.reason_codes
                or "M138_EXACT_ERROR_SCOPE_REQUIRED" not in decision.reason_codes
                or "M138_NO_ERROR_HANDLING_RUNTIME" not in decision.reason_codes
                or "M138_NO_RETRY_OR_ROLLBACK_EXECUTION" not in decision.reason_codes
                or "M139_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M138 error handling guardrail decision is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"error_handling_runtime_authorized": True},
                    "M138_ERROR_HANDLING_RUNTIME_DENIED",
                ),
                (
                    {"error_guardrail_runtime_started": True},
                    "M138_ERROR_GUARDRAIL_RUNTIME_DENIED",
                ),
                (
                    {"autonomous_recovery_execution_authorized": True},
                    "M138_RECOVERY_EXECUTION_DENIED",
                ),
                ({"retry_execution_performed": True}, "M138_RETRY_EXECUTION_DENIED"),
                (
                    {"rollback_execution_performed": True},
                    "M138_ROLLBACK_EXECUTION_DENIED",
                ),
                ({"resume_execution_performed": True}, "M138_RESUME_EXECUTION_DENIED"),
                (
                    {"dependency_execution_performed": True},
                    "M138_DEPENDENCY_EXECUTION_DENIED",
                ),
                ({"browser_action_performed": True}, "M138_BROWSER_ACTION_DENIED"),
                ({"connector_action_performed": True}, "M138_CONNECTOR_ACTION_DENIED"),
                ({"tool_execution_performed": True}, "M138_TOOL_EXECUTION_DENIED"),
                ({"backend_route_added": True}, "M138_BACKEND_ROUTE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M138_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_error_handling_guardrail_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M138 unsafe error guardrail mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M138 unsafe error guardrail mutation raised {exc!s}"
                        )
            try:
                validate_error_handling_guardrail_decision(
                    decision.model_copy(
                        update={
                            "receipt_plan": decision.receipt_plan.model_copy(
                                update={"store_raw_error_log": True}
                            )
                        }
                    )
                )
                failures.append("M138 receipt plan allowed raw error log storage")
            except ValueError as exc:
                if "M138_RAW_ERROR_LOG_DENIED" not in str(exc):
                    failures.append(
                        f"M138 raw error log receipt mutation raised {exc!s}"
                    )
        except Exception as exc:
            failures.append(f"M138 error handling guardrail validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "autonomous error handling guardrails",
            "contract-only",
            "review-only",
            "autonomous-error-handling-guardrails-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "exact",
            "mode 5",
            "m137 browser connector combined workflow decision",
            "m136 cross-tool dependency execution decision",
            "m135 autonomous recovery planner decision",
            "m134 human checkpoint scheduling decision",
            "m133 supervisor decision",
            "m132 trusted workflow decision",
            "error signal refs",
            "guardrail policy refs",
            "retry policy refs",
            "fallback policy refs",
            "escalation policy refs",
            "recovery plan refs",
            "rollback plan refs",
            "resume plan refs",
            "human checkpoint",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no error handling runtime",
            "no error guardrail runtime",
            "no autonomous recovery execution",
            "no retry execution",
            "no rollback execution",
            "no resume execution",
            "no dependency execution",
            "no browser action",
            "no connector action",
            "no tool execution",
            "no shell execution",
            "no network access",
            "no plugin execution",
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "m139 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M138 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m138_autonomous_error_handling_guardrails_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "error_handling_runtime_enabled=True",
            "error_guardrail_runtime_enabled=True",
            "autonomous_recovery_execution_enabled=True",
            "retry_execution_enabled=True",
            "resume_execution_enabled=True",
            "rollback_execution_enabled=True",
            "fallback_action_enabled=True",
            "escalation_action_enabled=True",
            "loop_recovery_enabled=True",
            "dependency_execution_enabled=True",
            "browser_action_enabled=True",
            "connector_action_enabled=True",
            "connector_write_enabled=True",
            "account_auth_enabled=True",
            "tool_execution_enabled=True",
            "execution_enabled=True",
            "shell_execution_enabled=True",
            "network_access_enabled=True",
            "plugin_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "error_handling_runtime_authorized=True",
            "error_guardrail_runtime_started=True",
            "autonomous_recovery_execution_authorized=True",
            "retry_execution_performed=True",
            "rollback_execution_performed=True",
            "resume_execution_performed=True",
            "dependency_execution_performed=True",
            "browser_action_performed=True",
            "connector_action_performed=True",
            "tool_execution_performed=True",
            "/autonomy/error-handling-guardrails/start",
            "/error-handling/run",
            "/error-guardrails/run",
            "/recovery/retry",
            "/recovery/rollback",
            "/recovery/resume",
            "/fallback/execute",
            "/escalation/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/error_handling_guardrails.py",
            "src/ultimate_ai_agent/core/autonomy/browser_connector_combined_workflow.py",
            "src/ultimate_ai_agent/core/autonomy/cross_tool_dependency_execution.py",
            "src/ultimate_ai_agent/core/autonomy/autonomous_recovery_planner.py",
            "src/ultimate_ai_agent/core/autonomy/human_checkpoint_scheduling.py",
            "src/ultimate_ai_agent/core/autonomy/long_running_task_supervisor.py",
            "src/ultimate_ai_agent/core/autonomy/trusted_recurring_workflow.py",
            "src/ultimate_ai_agent/core/autonomy/mode4_scoped_work_session.py",
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
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if ".test." in rel or _is_static_safety_scan_allowed_file(
                    rel, allowed_files
                ):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M138 forbidden error handling guardrail fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m138_autonomous_error_handling_guardrails_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m138_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M138 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m138_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
        ]
        failures = [
            f"missing M138 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m138" not in text
            or "autonomous error handling guardrails" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M138 Autonomous Error Handling Guardrails"
            )
        if (
            "m138 is implemented/released" not in text
            and "checkpoint m138 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M138 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m138",
                "pre-alpha checkpoint",
                "m138",
                "autonomous error handling guardrails",
                "implemented/released",
            ),
            (
                "checkpoint m139",
                "pre-alpha checkpoint",
                "m139",
                "autonomy abuse/loop detection",
                "implemented/released",
            ),
            (
                "checkpoint m140",
                "pre-alpha checkpoint",
                "m140",
                "higher-autonomy red-team freeze",
                "implemented/released",
            ),
            (
                "checkpoint m141",
                "pre-alpha checkpoint",
                "m141",
                "multi-user product boundary",
                "planned/provisional",
            ),
            (
                "v1.2.0-alpha",
                "alpha",
                "m150",
                "ultimate ai agent v1.2.0-alpha",
                "planned/provisional",
            ),
        ]:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | {status} |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing expected M138/M140-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "higher-autonomy red-team freeze is implemented",
            "m140 higher-autonomy red-team freeze is implemented",
            "red-team runtime is implemented",
            "abuse detection runtime is implemented",
            "loop detection runtime is implemented",
            "error handling runtime is implemented",
            "retry execution is implemented",
            "rollback execution is implemented",
            "resume execution is implemented",
            "recovery execution is implemented",
            "dependency execution runtime is implemented",
            "browser action execution is implemented",
            "connector action execution is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "network access is implemented",
            "plugin execution is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m140 dependency is added",
            "beta is released",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M138 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m139_autonomy_abuse_loop_detection_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/abuse_loop_detection.py",
            "docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION.md",
            "docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_POLICY.md",
            "docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_RECEIPT_PLAN.md",
            "docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_NON_GOALS.md",
            "docs/autonomy/M139_TO_M140_BOUNDARY.md",
            "docs/release_notes/checkpoint_m139.md",
            "docs/archive/checkpoints/m139/README_IMPORT.md",
            "docs/archive/checkpoints/m139/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m139_abuse_loop_detection.py",
            "tests/test_m139_gate_integration.py",
        ]
        failures = [
            f"missing M139 autonomy abuse/loop detection file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m139_abuse_loop_detection import _request
            from ultimate_ai_agent.core.autonomy import (
                AbuseLoopDetectionStatus,
                AutonomyAuthorityMode,
                AutonomyRiskClass,
                build_abuse_loop_detection_decision,
                validate_abuse_loop_detection_decision,
            )

            decision = build_abuse_loop_detection_decision(_request())
            if (
                decision.status != AbuseLoopDetectionStatus.ready_for_review
                or decision.selected_mode
                != AutonomyAuthorityMode.trusted_recurring_automation
                or decision.max_risk_class != AutonomyRiskClass.low
                or not decision.contract_only
                or not decision.review_only
                or not decision.autonomy_abuse_loop_detection_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.exact_scope_bound
                or not decision.mode5_bound
                or not decision.m138_error_guardrail_bound
                or not decision.m137_browser_connector_workflow_bound
                or not decision.m136_dependency_execution_bound
                or not decision.m135_recovery_planner_bound
                or not decision.m134_human_checkpoint_bound
                or not decision.m133_supervisor_bound
                or not decision.m132_trusted_workflow_bound
                or not decision.abuse_signal_bound
                or not decision.loop_signal_bound
                or not decision.pattern_policy_bound
                or not decision.threshold_policy_bound
                or not decision.intervention_plan_bound
                or not decision.escalation_plan_bound
                or not decision.human_checkpoint_bound
                or not decision.audit_replay_bound
                or not decision.revocation_bound
                or not decision.kill_switch_bound
                or not decision.no_effect_receipt_required
                or decision.abuse_detection_runtime_authorized
                or decision.loop_detection_runtime_authorized
                or decision.loop_monitor_started
                or decision.detector_runtime_started
                or decision.loop_intervention_performed
                or decision.autonomous_recovery_execution_authorized
                or decision.retry_execution_performed
                or decision.rollback_execution_performed
                or decision.resume_execution_performed
                or decision.dependency_execution_performed
                or decision.browser_action_performed
                or decision.connector_action_performed
                or decision.tool_execution_performed
                or decision.execution_performed
                or decision.backend_route_added
                or decision.dependency_added
                or decision.beta_release_enabled
                or decision.production_authority_granted
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or decision.receipt_plan.store_raw_abuse_log
                or decision.receipt_plan.store_raw_loop_trace
                or decision.receipt_plan.detector_runtime_started
                or decision.receipt_plan.loop_intervention_performed
                or decision.receipt_plan.recovery_execution_performed
                or "M139_AUTONOMY_ABUSE_LOOP_DETECTION_CONTRACT_ONLY"
                not in decision.reason_codes
                or "M139_EXACT_DETECTION_SCOPE_REQUIRED" not in decision.reason_codes
                or "M139_NO_ABUSE_OR_LOOP_RUNTIME" not in decision.reason_codes
                or "M139_NO_INTERVENTION_OR_RECOVERY_EXECUTION"
                not in decision.reason_codes
                or "M140_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M139 autonomy abuse/loop detection decision is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"abuse_detection_runtime_authorized": True},
                    "M139_ABUSE_DETECTION_RUNTIME_DENIED",
                ),
                (
                    {"loop_detection_runtime_authorized": True},
                    "M139_LOOP_DETECTION_RUNTIME_DENIED",
                ),
                ({"loop_monitor_started": True}, "M139_LOOP_MONITOR_DENIED"),
                ({"detector_runtime_started": True}, "M139_DETECTOR_RUNTIME_DENIED"),
                (
                    {"loop_intervention_performed": True},
                    "M139_LOOP_INTERVENTION_DENIED",
                ),
                (
                    {"autonomous_recovery_execution_authorized": True},
                    "M139_RECOVERY_EXECUTION_DENIED",
                ),
                ({"retry_execution_performed": True}, "M139_RETRY_EXECUTION_DENIED"),
                (
                    {"rollback_execution_performed": True},
                    "M139_ROLLBACK_EXECUTION_DENIED",
                ),
                ({"resume_execution_performed": True}, "M139_RESUME_EXECUTION_DENIED"),
                (
                    {"dependency_execution_performed": True},
                    "M139_DEPENDENCY_EXECUTION_DENIED",
                ),
                ({"browser_action_performed": True}, "M139_BROWSER_ACTION_DENIED"),
                ({"connector_action_performed": True}, "M139_CONNECTOR_ACTION_DENIED"),
                ({"tool_execution_performed": True}, "M139_TOOL_EXECUTION_DENIED"),
                ({"backend_route_added": True}, "M139_BACKEND_ROUTE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M139_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_abuse_loop_detection_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M139 unsafe abuse/loop detection mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M139 unsafe abuse/loop detection mutation raised {exc!s}"
                        )
            try:
                validate_abuse_loop_detection_decision(
                    decision.model_copy(
                        update={
                            "receipt_plan": decision.receipt_plan.model_copy(
                                update={"store_raw_abuse_log": True}
                            )
                        }
                    )
                )
                failures.append("M139 receipt plan allowed raw abuse log storage")
            except ValueError as exc:
                if "M139_RAW_ABUSE_LOG_DENIED" not in str(exc):
                    failures.append(
                        f"M139 raw abuse log receipt mutation raised {exc!s}"
                    )
        except Exception as exc:
            failures.append(f"M139 abuse/loop detection validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "autonomy abuse/loop detection",
            "contract-only",
            "review-only",
            "autonomy-abuse-loop-detection-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "exact",
            "mode 5",
            "m138 error handling guardrail decision",
            "m137 browser connector combined workflow decision",
            "m136 cross-tool dependency execution decision",
            "m135 autonomous recovery planner decision",
            "m134 human checkpoint scheduling decision",
            "m133 supervisor decision",
            "m132 trusted workflow decision",
            "abuse signal refs",
            "loop signal refs",
            "pattern policy refs",
            "threshold policy refs",
            "intervention plan refs",
            "escalation plan refs",
            "human checkpoint",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no abuse detection runtime",
            "no loop detection runtime",
            "no loop monitor",
            "no detector runtime",
            "no loop intervention",
            "no autonomous recovery execution",
            "no retry execution",
            "no rollback execution",
            "no resume execution",
            "no dependency execution",
            "no browser action",
            "no connector action",
            "no tool execution",
            "no shell execution",
            "no network access",
            "no plugin execution",
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "m140 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M139 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m139_autonomy_abuse_loop_detection_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "abuse_detection_runtime_enabled=True",
            "loop_detection_runtime_enabled=True",
            "loop_monitor_enabled=True",
            "detector_runtime_enabled=True",
            "loop_intervention_enabled=True",
            "autonomous_recovery_execution_enabled=True",
            "retry_execution_enabled=True",
            "resume_execution_enabled=True",
            "rollback_execution_enabled=True",
            "dependency_execution_enabled=True",
            "browser_action_enabled=True",
            "connector_action_enabled=True",
            "connector_write_enabled=True",
            "account_auth_enabled=True",
            "tool_execution_enabled=True",
            "execution_enabled=True",
            "shell_execution_enabled=True",
            "network_access_enabled=True",
            "plugin_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "abuse_detection_runtime_authorized=True",
            "loop_detection_runtime_authorized=True",
            "loop_monitor_started=True",
            "detector_runtime_started=True",
            "loop_intervention_performed=True",
            "autonomous_recovery_execution_authorized=True",
            "retry_execution_performed=True",
            "rollback_execution_performed=True",
            "resume_execution_performed=True",
            "dependency_execution_performed=True",
            "browser_action_performed=True",
            "connector_action_performed=True",
            "tool_execution_performed=True",
            "/autonomy/abuse-loop-detection/start",
            "/abuse-detection/run",
            "/loop-detection/run",
            "/loop-detection/intervene",
            "/loop-monitor/start",
            "/loop-intervention/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/abuse_loop_detection.py",
            "src/ultimate_ai_agent/core/autonomy/error_handling_guardrails.py",
            "src/ultimate_ai_agent/core/autonomy/browser_connector_combined_workflow.py",
            "src/ultimate_ai_agent/core/autonomy/cross_tool_dependency_execution.py",
            "src/ultimate_ai_agent/core/autonomy/autonomous_recovery_planner.py",
            "src/ultimate_ai_agent/core/autonomy/human_checkpoint_scheduling.py",
            "src/ultimate_ai_agent/core/autonomy/long_running_task_supervisor.py",
            "src/ultimate_ai_agent/core/autonomy/trusted_recurring_workflow.py",
            "src/ultimate_ai_agent/core/autonomy/mode4_scoped_work_session.py",
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
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if ".test." in rel or _is_static_safety_scan_allowed_file(
                    rel, allowed_files
                ):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M139 forbidden abuse/loop detection fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m139_autonomy_abuse_loop_detection_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m139_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M139 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m139_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
        ]
        failures = [
            f"missing M139 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m139" not in text or "autonomy abuse/loop detection" not in text:
            failures.append(
                "active docs do not identify Checkpoint M139 Autonomy Abuse/Loop Detection"
            )
        if (
            "m139 is implemented/released" not in text
            and "checkpoint m139 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M139 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m139",
                "pre-alpha checkpoint",
                "m139",
                "autonomy abuse/loop detection",
                "implemented/released",
            ),
            (
                "checkpoint m140",
                "pre-alpha checkpoint",
                "m140",
                "higher-autonomy red-team freeze",
                "planned/provisional",
            ),
            (
                "v1.2.0-alpha",
                "alpha",
                "m150",
                "ultimate ai agent v1.2.0-alpha",
                "planned/provisional",
            ),
        ]:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | {status} |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing expected M139/M141-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "multi-user product boundary is implemented",
            "m141 multi-user product boundary is implemented",
            "multi-user runtime is implemented",
            "tenant runtime is implemented",
            "workspace sharing is implemented",
            "identity federation is implemented",
            "red-team runtime is implemented",
            "abuse detection runtime is implemented",
            "loop detection runtime is implemented",
            "loop monitor runtime is implemented",
            "loop intervention is implemented",
            "recovery execution is implemented",
            "dependency execution runtime is implemented",
            "browser action execution is implemented",
            "connector action execution is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "network access is implemented",
            "plugin execution is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m141 dependency is added",
            "beta is released",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M139 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
