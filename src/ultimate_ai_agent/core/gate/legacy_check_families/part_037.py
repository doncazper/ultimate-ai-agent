from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart037Mixin:
    """Legacy checks from m135_autonomous_recovery_planner_contracts through m136_roadmap_currentness."""
    def check_m135_autonomous_recovery_planner_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/autonomous_recovery_planner.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER.md",
            "docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_POLICY.md",
            "docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_RECEIPT_PLAN.md",
            "docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_NON_GOALS.md",
            "docs/autonomy/M135_TO_M136_BOUNDARY.md",
            "docs/release_notes/checkpoint_m135.md",
            "docs/archive/checkpoints/m135/README_IMPORT.md",
            "docs/archive/checkpoints/m135/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M135 autonomous recovery planner file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            sys.path.insert(0, str(self.root / "src"))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m135_autonomous_recovery_planner import _request
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyRiskClass,
                AutonomousRecoveryPlannerStatus,
                build_autonomous_recovery_planner_decision,
                validate_autonomous_recovery_planner_decision,
            )

            decision = build_autonomous_recovery_planner_decision(_request())
            if (
                decision.status != AutonomousRecoveryPlannerStatus.ready_for_review
                or decision.selected_mode
                != AutonomyAuthorityMode.trusted_recurring_automation
                or not decision.contract_only
                or not decision.review_only
                or not decision.autonomous_recovery_planner_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.exact_scope_bound
                or not decision.mode5_bound
                or not decision.m134_human_checkpoint_bound
                or not decision.m133_supervisor_bound
                or not decision.m132_trusted_workflow_bound
                or not decision.recovery_plan_bound
                or not decision.failure_signal_bound
                or not decision.recovery_trigger_bound
                or not decision.recovery_strategy_bound
                or not decision.recovery_steps_bound
                or not decision.rollback_plan_bound
                or not decision.resume_plan_bound
                or not decision.checkpoint_bound
                or not decision.human_checkpoint_bound
                or not decision.audit_replay_bound
                or not decision.revocation_bound
                or not decision.kill_switch_bound
                or not decision.no_effect_receipt_required
                or decision.max_risk_class != AutonomyRiskClass.low
                or decision.mode5_runtime_authorized
                or decision.recovery_planner_runtime_authorized
                or decision.recovery_execution_authorized
                or decision.recovery_execution_performed
                or decision.retry_execution_performed
                or decision.resume_execution_performed
                or decision.rollback_execution_performed
                or decision.supervisor_runtime_started
                or decision.checkpoint_scheduler_started
                or decision.human_checkpoint_scheduler_started
                or decision.human_checkpoint_prompt_sent
                or decision.notification_delivered
                or decision.scheduler_started
                or decision.background_worker_started
                or decision.autonomous_actions_authorized
                or decision.autonomous_actions_performed
                or decision.execution_authorized
                or decision.execution_performed
                or decision.tool_execution_authorized
                or decision.tool_execution_performed
                or decision.shell_execution_performed
                or decision.command_execution_performed
                or decision.subprocess_execution_performed
                or decision.filesystem_mutation_performed
                or decision.network_access_performed
                or decision.browser_automation_performed
                or decision.browser_form_performed
                or decision.authenticated_browser_performed
                or decision.download_performed
                or decision.upload_performed
                or decision.plugin_execution_performed
                or decision.connector_runtime_performed
                or decision.account_auth_performed
                or decision.mobile_sensor_performed
                or decision.remote_execution_performed
                or decision.model_call_performed
                or decision.memory_write_performed
                or decision.context_injection_performed
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.beta_release_enabled
                or decision.production_authority_granted
                or decision.side_effects_performed
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or decision.receipt_plan.store_raw_prompt
                or decision.receipt_plan.store_raw_provider_payload
                or decision.receipt_plan.recovery_executed
                or decision.receipt_plan.retry_executed
                or decision.receipt_plan.resume_executed
                or decision.receipt_plan.rollback_executed
                or decision.receipt_plan.supervisor_started
                or decision.receipt_plan.checkpoint_scheduled
                or decision.receipt_plan.prompt_sent
                or decision.receipt_plan.notification_delivered
                or decision.receipt_plan.execution_performed
                or "M135_AUTONOMOUS_RECOVERY_PLANNER_CONTRACT_ONLY"
                not in decision.reason_codes
                or "M135_EXACT_RECOVERY_SCOPE_REQUIRED" not in decision.reason_codes
                or "M135_HUMAN_CHECKPOINT_BINDING_REQUIRED" not in decision.reason_codes
                or "M135_NO_RECOVERY_EXECUTION" not in decision.reason_codes
                or "M136_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M135 autonomous recovery planner decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"mode5_runtime_authorized": True}, "M135_MODE5_RUNTIME_DENIED"),
                (
                    {"recovery_planner_runtime_authorized": True},
                    "M135_RECOVERY_PLANNER_RUNTIME_DENIED",
                ),
                (
                    {"recovery_execution_authorized": True},
                    "M135_RECOVERY_EXECUTION_DENIED",
                ),
                (
                    {"recovery_execution_performed": True},
                    "M135_RECOVERY_EXECUTION_DENIED",
                ),
                ({"retry_execution_performed": True}, "M135_RETRY_EXECUTION_DENIED"),
                ({"resume_execution_performed": True}, "M135_RESUME_EXECUTION_DENIED"),
                (
                    {"rollback_execution_performed": True},
                    "M135_ROLLBACK_EXECUTION_DENIED",
                ),
                (
                    {"supervisor_runtime_started": True},
                    "M135_SUPERVISOR_RUNTIME_DENIED",
                ),
                (
                    {"checkpoint_scheduler_started": True},
                    "M135_CHECKPOINT_SCHEDULER_DENIED",
                ),
                ({"execution_performed": True}, "M135_EXECUTION_DENIED"),
                ({"tool_execution_performed": True}, "M135_TOOL_EXECUTION_DENIED"),
                ({"backend_route_added": True}, "M135_BACKEND_ROUTE_DENIED"),
                ({"beta_release_enabled": True}, "M135_BETA_RELEASE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M135_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_autonomous_recovery_planner_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M135 unsafe recovery mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M135 unsafe recovery mutation raised {exc!s}")
            try:
                validate_autonomous_recovery_planner_decision(
                    decision.model_copy(
                        update={
                            "receipt_plan": decision.receipt_plan.model_copy(
                                update={"store_raw_prompt": True}
                            )
                        }
                    )
                )
                failures.append("M135 receipt plan allowed raw prompt storage")
            except ValueError as exc:
                if "M135_RAW_PROMPT_DENIED" not in str(exc):
                    failures.append(f"M135 raw prompt receipt mutation raised {exc!s}")
        except Exception as exc:
            failures.append(
                f"M135 autonomous recovery planner validation failed: {exc}"
            )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "autonomous recovery planner",
            "contract-only",
            "review-only",
            "autonomous-recovery-planner-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "exact scope",
            "mode 5",
            "m134 human checkpoint scheduling decision",
            "m133 supervisor decision",
            "m132 trusted workflow decision",
            "failure signal",
            "recovery trigger",
            "recovery strategy",
            "recovery step refs",
            "rollback plan",
            "resume plan",
            "checkpoint ref",
            "human checkpoint ref",
            "risk decision",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no recovery execution",
            "no retry execution",
            "no resume execution",
            "no rollback execution",
            "no supervisor runtime",
            "no checkpoint scheduler",
            "no human checkpoint scheduler",
            "no prompt",
            "no notification delivery",
            "no scheduler",
            "no background worker",
            "no autonomous actions",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no network access",
            "no browser automation",
            "no plugin execution",
            "no connector runtime",
            "no account auth",
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "m136 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M135 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m135_autonomous_recovery_planner_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "mode5_runtime_enabled=True",
            "recovery_planner_runtime_enabled=True",
            "recovery_execution_enabled=True",
            "retry_execution_enabled=True",
            "resume_execution_enabled=True",
            "rollback_execution_enabled=True",
            "supervisor_runtime_enabled=True",
            "checkpoint_scheduler_enabled=True",
            "human_checkpoint_scheduler_enabled=True",
            "human_checkpoint_prompt_enabled=True",
            "notification_delivery_enabled=True",
            "scheduler_enabled=True",
            "background_worker_enabled=True",
            "autonomous_actions_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "command_execution_enabled=True",
            "subprocess_execution_enabled=True",
            "filesystem_mutation_enabled=True",
            "network_access_enabled=True",
            "browser_automation_enabled=True",
            "browser_form_enabled=True",
            "authenticated_browser_enabled=True",
            "download_enabled=True",
            "upload_enabled=True",
            "plugin_execution_enabled=True",
            "connector_runtime_enabled=True",
            "account_auth_enabled=True",
            "mobile_sensor_enabled=True",
            "remote_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "control_center_control_enabled=True",
            "dependency_added=True",
            "beta_release_enabled=True",
            "production_authority_granted=True",
            "mode5_runtime_requested=True",
            "recovery_planner_runtime_requested=True",
            "recovery_execution_requested=True",
            "retry_execution_requested=True",
            "resume_execution_requested=True",
            "rollback_execution_requested=True",
            "supervisor_runtime_requested=True",
            "checkpoint_scheduler_requested=True",
            "human_checkpoint_scheduler_requested=True",
            "human_checkpoint_prompt_requested=True",
            "notification_delivery_requested=True",
            "scheduler_requested=True",
            "background_worker_requested=True",
            "autonomous_actions_requested=True",
            "execution_requested=True",
            "tool_execution_requested=True",
            "shell_execution_requested=True",
            "command_execution_requested=True",
            "subprocess_execution_requested=True",
            "filesystem_mutation_requested=True",
            "network_access_requested=True",
            "browser_automation_requested=True",
            "browser_form_requested=True",
            "authenticated_browser_requested=True",
            "download_requested=True",
            "upload_requested=True",
            "plugin_execution_requested=True",
            "connector_runtime_requested=True",
            "account_auth_requested=True",
            "mobile_sensor_requested=True",
            "remote_execution_requested=True",
            "model_call_requested=True",
            "memory_write_requested=True",
            "context_injection_requested=True",
            "backend_route_requested=True",
            "control_center_control_requested=True",
            "dependency_requested=True",
            "beta_release_requested=True",
            "production_authority_requested=True",
            "mode5_runtime_authorized=True",
            "recovery_planner_runtime_authorized=True",
            "recovery_execution_authorized=True",
            "recovery_execution_performed=True",
            "retry_execution_performed=True",
            "resume_execution_performed=True",
            "rollback_execution_performed=True",
            "supervisor_runtime_started=True",
            "checkpoint_scheduler_started=True",
            "human_checkpoint_scheduler_started=True",
            "human_checkpoint_prompt_sent=True",
            "notification_delivered=True",
            "scheduler_started=True",
            "background_worker_started=True",
            "autonomous_actions_performed=True",
            "execution_performed=True",
            "tool_execution_performed=True",
            "shell_execution_performed=True",
            "command_execution_performed=True",
            "subprocess_execution_performed=True",
            "filesystem_mutation_performed=True",
            "network_access_performed=True",
            "browser_automation_performed=True",
            "browser_form_performed=True",
            "authenticated_browser_performed=True",
            "download_performed=True",
            "upload_performed=True",
            "plugin_execution_performed=True",
            "connector_runtime_performed=True",
            "account_auth_performed=True",
            "mobile_sensor_performed=True",
            "remote_execution_performed=True",
            "model_call_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "/autonomy/autonomous-recovery-planner",
            "/autonomy/autonomous-recovery-planner/start",
            "/autonomy/recovery/execute",
            "/recovery/execute",
            "/recovery/retry",
            "/recovery/resume",
            "/recovery/rollback",
            "/supervisor/recover",
            "/supervisor/resume",
            "/supervisor/start",
            "/checkpoints/schedule",
            "/checkpoints/human/schedule",
            "/checkpoints/human/prompt",
            "/checkpoints/human/notify",
            "/scheduler/start",
            "/background/start",
            "/workers/start",
            "/shell/execute",
            "/commands/execute",
            "/browser/click",
            "/browser/form",
            "/browser/download",
            "/browser/upload",
            "/network/post",
            "/plugins/execute",
            "/connectors/runtime",
            "/connectors/auth",
            "/mobile/sensors",
            "/remote/execute",
            "/memory/write",
            "/context/inject",
            "/models/call",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/autonomous_recovery_planner.py",
            "src/ultimate_ai_agent/core/autonomy/human_checkpoint_scheduling.py",
            "src/ultimate_ai_agent/core/autonomy/long_running_task_supervisor.py",
            "src/ultimate_ai_agent/core/autonomy/trusted_recurring_workflow.py",
            "src/ultimate_ai_agent/core/autonomy/mode4_scoped_work_session.py",
            "src/ultimate_ai_agent/core/autonomy/modes.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/approvals.py",
            "src/ultimate_ai_agent/core/autonomy/risk.py",
            "src/ultimate_ai_agent/core/autonomy/revocation.py",
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run.py",
            "src/ultimate_ai_agent/core/autonomy/recurring.py",
            "src/ultimate_ai_agent/core/autonomy/scoped_recurring.py",
            "src/ultimate_ai_agent/core/autonomy/tool_autonomy_single_session.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run_promotion.py",
            "src/ultimate_ai_agent/core/autonomy/v1_safety_freeze.py",
            "src/ultimate_ai_agent/core/autonomy/foundation_freeze.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
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
                if ".test." in rel:
                    continue
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M135 forbidden autonomous recovery planner fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m135_autonomous_recovery_planner_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m135_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M135 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m135_roadmap_currentness(
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
            f"missing M135 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m135" not in text or "autonomous recovery planner" not in text:
            failures.append(
                "active docs do not identify Checkpoint M135 Autonomous Recovery Planner"
            )
        if (
            "m135 is implemented/released" not in text
            and "checkpoint m135 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M135 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m135",
                "pre-alpha checkpoint",
                "m135",
                "autonomous recovery planner",
                "implemented/released",
            ),
            (
                "checkpoint m136",
                "pre-alpha checkpoint",
                "m136",
                "cross-tool dependency execution",
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
                    f"active docs missing expected M135-M138/M139-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "autonomy abuse/loop detection is implemented",
            "m139 autonomy abuse/loop detection is implemented",
            "recovery execution is implemented",
            "retry execution is implemented",
            "resume execution is implemented",
            "rollback execution is implemented",
            "supervisor runtime is implemented",
            "checkpoint scheduler is implemented",
            "scheduler is implemented",
            "background worker is implemented",
            "autonomous actions are implemented",
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
                    f"active docs imply forbidden M135 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m136_cross_tool_dependency_execution_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/cross_tool_dependency_execution.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION.md",
            "docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_POLICY.md",
            "docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_RECEIPT_PLAN.md",
            "docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_NON_GOALS.md",
            "docs/autonomy/M136_TO_M137_BOUNDARY.md",
            "docs/release_notes/checkpoint_m136.md",
            "docs/archive/checkpoints/m136/README_IMPORT.md",
            "docs/archive/checkpoints/m136/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M136 cross-tool dependency execution file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            sys.path.insert(0, str(self.root / "src"))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m136_cross_tool_dependency_execution import _request
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyRiskClass,
                CrossToolDependencyExecutionStatus,
                build_cross_tool_dependency_execution_decision,
                validate_cross_tool_dependency_execution_decision,
            )

            decision = build_cross_tool_dependency_execution_decision(_request())
            if (
                decision.status != CrossToolDependencyExecutionStatus.ready_for_review
                or decision.selected_mode
                != AutonomyAuthorityMode.trusted_recurring_automation
                or not decision.contract_only
                or not decision.review_only
                or not decision.cross_tool_dependency_execution_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.exact_scope_bound
                or not decision.mode5_bound
                or not decision.m135_recovery_planner_bound
                or not decision.m134_human_checkpoint_bound
                or not decision.m133_supervisor_bound
                or not decision.m132_trusted_workflow_bound
                or not decision.dependency_graph_bound
                or not decision.acyclic_graph_validated
                or not decision.dependency_order_bound
                or not decision.cross_tool_scope_bound
                or not decision.dry_run_plan_bound
                or not decision.human_checkpoint_bound
                or not decision.audit_replay_bound
                or not decision.revocation_bound
                or not decision.kill_switch_bound
                or not decision.no_effect_receipt_required
                or len(decision.safe_tool_refs) < 2
                or decision.max_risk_class != AutonomyRiskClass.low
                or decision.mode5_runtime_authorized
                or decision.cross_tool_dependency_runtime_authorized
                or decision.dependency_execution_authorized
                or decision.dependency_execution_performed
                or decision.dependency_resolver_runtime_started
                or decision.cross_tool_runtime_started
                or decision.parallel_tool_execution_performed
                or decision.tool_state_handoff_performed
                or decision.tool_output_routing_performed
                or decision.recovery_execution_performed
                or decision.supervisor_runtime_started
                or decision.checkpoint_scheduler_started
                or decision.human_checkpoint_prompt_sent
                or decision.scheduler_started
                or decision.background_worker_started
                or decision.autonomous_actions_authorized
                or decision.autonomous_actions_performed
                or decision.execution_authorized
                or decision.execution_performed
                or decision.tool_execution_authorized
                or decision.tool_execution_performed
                or decision.shell_execution_performed
                or decision.command_execution_performed
                or decision.subprocess_execution_performed
                or decision.filesystem_mutation_performed
                or decision.network_access_performed
                or decision.browser_automation_performed
                or decision.browser_form_performed
                or decision.authenticated_browser_performed
                or decision.download_performed
                or decision.upload_performed
                or decision.plugin_execution_performed
                or decision.connector_runtime_performed
                or decision.account_auth_performed
                or decision.mobile_sensor_performed
                or decision.remote_execution_performed
                or decision.model_call_performed
                or decision.memory_write_performed
                or decision.context_injection_performed
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.beta_release_enabled
                or decision.production_authority_granted
                or decision.side_effects_performed
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or not decision.receipt_plan.store_dependency_order_refs_only
                or decision.receipt_plan.store_raw_tool_payload
                or decision.receipt_plan.store_raw_prompt
                or decision.receipt_plan.store_raw_provider_payload
                or decision.receipt_plan.dependency_execution_performed
                or decision.receipt_plan.dependency_resolver_started
                or decision.receipt_plan.cross_tool_runtime_started
                or decision.receipt_plan.parallel_tool_execution_performed
                or decision.receipt_plan.tool_state_handoff_performed
                or decision.receipt_plan.tool_output_routing_performed
                or decision.receipt_plan.tool_execution_performed
                or decision.receipt_plan.execution_performed
                or "M136_CROSS_TOOL_DEPENDENCY_EXECUTION_CONTRACT_ONLY"
                not in decision.reason_codes
                or "M136_ACYCLIC_DEPENDENCY_GRAPH_REQUIRED" not in decision.reason_codes
                or "M136_EXACT_TOOL_SCOPE_REQUIRED" not in decision.reason_codes
                or "M136_NO_DEPENDENCY_EXECUTION" not in decision.reason_codes
                or "M137_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M136 cross-tool dependency execution decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"mode5_runtime_authorized": True}, "M136_MODE5_RUNTIME_DENIED"),
                (
                    {"cross_tool_dependency_runtime_authorized": True},
                    "M136_CROSS_TOOL_RUNTIME_DENIED",
                ),
                (
                    {"dependency_execution_authorized": True},
                    "M136_DEPENDENCY_EXECUTION_DENIED",
                ),
                (
                    {"dependency_execution_performed": True},
                    "M136_DEPENDENCY_EXECUTION_DENIED",
                ),
                (
                    {"dependency_resolver_runtime_started": True},
                    "M136_DEPENDENCY_RESOLVER_DENIED",
                ),
                (
                    {"parallel_tool_execution_performed": True},
                    "M136_PARALLEL_TOOL_EXECUTION_DENIED",
                ),
                (
                    {"tool_state_handoff_performed": True},
                    "M136_TOOL_STATE_HANDOFF_DENIED",
                ),
                (
                    {"tool_output_routing_performed": True},
                    "M136_TOOL_OUTPUT_ROUTING_DENIED",
                ),
                ({"execution_performed": True}, "M136_EXECUTION_DENIED"),
                ({"tool_execution_performed": True}, "M136_TOOL_EXECUTION_DENIED"),
                ({"backend_route_added": True}, "M136_BACKEND_ROUTE_DENIED"),
                ({"beta_release_enabled": True}, "M136_BETA_RELEASE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M136_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_cross_tool_dependency_execution_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M136 unsafe dependency mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M136 unsafe dependency mutation raised {exc!s}"
                        )
            try:
                validate_cross_tool_dependency_execution_decision(
                    decision.model_copy(
                        update={
                            "receipt_plan": decision.receipt_plan.model_copy(
                                update={"store_raw_tool_payload": True}
                            )
                        }
                    )
                )
                failures.append("M136 receipt plan allowed raw tool payload storage")
            except ValueError as exc:
                if "M136_RAW_TOOL_PAYLOAD_DENIED" not in str(exc):
                    failures.append(
                        f"M136 raw tool payload receipt mutation raised {exc!s}"
                    )
        except Exception as exc:
            failures.append(
                f"M136 cross-tool dependency execution validation failed: {exc}"
            )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "cross-tool dependency execution",
            "contract-only",
            "review-only",
            "cross-tool-dependency-execution-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "exact scope",
            "mode 5",
            "m135 autonomous recovery planner decision",
            "m134 human checkpoint scheduling decision",
            "m133 supervisor decision",
            "m132 trusted workflow decision",
            "dependency graph",
            "dependency step refs",
            "dependency edge refs",
            "dependency order refs",
            "safe tool refs",
            "dry-run plan",
            "dependency resolution",
            "conflict policy",
            "failure policy",
            "recovery plan",
            "checkpoint ref",
            "human checkpoint ref",
            "risk decision",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no dependency execution",
            "no dependency resolver runtime",
            "no cross-tool runtime",
            "no parallel tool execution",
            "no tool state handoff",
            "no tool output routing",
            "no recovery execution",
            "no supervisor runtime",
            "no checkpoint scheduler",
            "no prompt",
            "no scheduler",
            "no background worker",
            "no autonomous actions",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no network access",
            "no browser automation",
            "no plugin execution",
            "no connector runtime",
            "no account auth",
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "m137 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M136 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m136_cross_tool_dependency_execution_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "mode5_runtime_enabled=True",
            "cross_tool_dependency_runtime_enabled=True",
            "dependency_execution_enabled=True",
            "dependency_resolver_runtime_enabled=True",
            "cross_tool_runtime_enabled=True",
            "parallel_tool_execution_enabled=True",
            "tool_state_handoff_enabled=True",
            "tool_output_routing_enabled=True",
            "recovery_execution_enabled=True",
            "supervisor_runtime_enabled=True",
            "checkpoint_scheduler_enabled=True",
            "human_checkpoint_prompt_enabled=True",
            "scheduler_enabled=True",
            "background_worker_enabled=True",
            "autonomous_actions_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "command_execution_enabled=True",
            "subprocess_execution_enabled=True",
            "filesystem_mutation_enabled=True",
            "network_access_enabled=True",
            "browser_automation_enabled=True",
            "browser_form_enabled=True",
            "authenticated_browser_enabled=True",
            "download_enabled=True",
            "upload_enabled=True",
            "plugin_execution_enabled=True",
            "connector_runtime_enabled=True",
            "account_auth_enabled=True",
            "mobile_sensor_enabled=True",
            "remote_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "control_center_control_enabled=True",
            "dependency_added=True",
            "beta_release_enabled=True",
            "production_authority_granted=True",
            "mode5_runtime_requested=True",
            "cross_tool_dependency_runtime_requested=True",
            "dependency_execution_requested=True",
            "dependency_resolver_runtime_requested=True",
            "cross_tool_runtime_requested=True",
            "parallel_tool_execution_requested=True",
            "tool_state_handoff_requested=True",
            "tool_output_routing_requested=True",
            "recovery_execution_requested=True",
            "supervisor_runtime_requested=True",
            "checkpoint_scheduler_requested=True",
            "human_checkpoint_prompt_requested=True",
            "scheduler_requested=True",
            "background_worker_requested=True",
            "autonomous_actions_requested=True",
            "execution_requested=True",
            "tool_execution_requested=True",
            "shell_execution_requested=True",
            "command_execution_requested=True",
            "subprocess_execution_requested=True",
            "filesystem_mutation_requested=True",
            "network_access_requested=True",
            "browser_automation_requested=True",
            "browser_form_requested=True",
            "authenticated_browser_requested=True",
            "download_requested=True",
            "upload_requested=True",
            "plugin_execution_requested=True",
            "connector_runtime_requested=True",
            "account_auth_requested=True",
            "mobile_sensor_requested=True",
            "remote_execution_requested=True",
            "model_call_requested=True",
            "memory_write_requested=True",
            "context_injection_requested=True",
            "backend_route_requested=True",
            "control_center_control_requested=True",
            "dependency_requested=True",
            "beta_release_requested=True",
            "production_authority_requested=True",
            "mode5_runtime_authorized=True",
            "cross_tool_dependency_runtime_authorized=True",
            "dependency_execution_authorized=True",
            "dependency_execution_performed=True",
            "dependency_resolver_runtime_started=True",
            "cross_tool_runtime_started=True",
            "parallel_tool_execution_performed=True",
            "tool_state_handoff_performed=True",
            "tool_output_routing_performed=True",
            "recovery_execution_performed=True",
            "supervisor_runtime_started=True",
            "checkpoint_scheduler_started=True",
            "human_checkpoint_prompt_sent=True",
            "scheduler_started=True",
            "background_worker_started=True",
            "autonomous_actions_performed=True",
            "execution_performed=True",
            "tool_execution_performed=True",
            "shell_execution_performed=True",
            "command_execution_performed=True",
            "subprocess_execution_performed=True",
            "filesystem_mutation_performed=True",
            "network_access_performed=True",
            "browser_automation_performed=True",
            "browser_form_performed=True",
            "authenticated_browser_performed=True",
            "download_performed=True",
            "upload_performed=True",
            "plugin_execution_performed=True",
            "connector_runtime_performed=True",
            "account_auth_performed=True",
            "mobile_sensor_performed=True",
            "remote_execution_performed=True",
            "model_call_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "/autonomy/cross-tool-dependency-execution",
            "/autonomy/cross-tool-dependency-execution/start",
            "/autonomy/cross-tool-dependency-execution/run",
            "/dependency-execution/execute",
            "/dependency-execution/run",
            "/dependency-execution/resolve",
            "/dependency-resolver/start",
            "/cross-tool/runtime",
            "/cross-tool/run",
            "/tools/execute",
            "/tools/run",
            "/tool-runtime/execute",
            "/tool-state/handoff",
            "/tool-output/route",
            "/connectors/runtime",
            "/connectors/write",
            "/browser/click",
            "/browser/form",
            "/browser/download",
            "/browser/upload",
            "/network/post",
            "/plugins/execute",
            "/scheduler/start",
            "/background/start",
            "/workers/start",
            "/models/call",
            "/memory/write",
            "/context/inject",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/cross_tool_dependency_execution.py",
            "src/ultimate_ai_agent/core/autonomy/autonomous_recovery_planner.py",
            "src/ultimate_ai_agent/core/autonomy/human_checkpoint_scheduling.py",
            "src/ultimate_ai_agent/core/autonomy/long_running_task_supervisor.py",
            "src/ultimate_ai_agent/core/autonomy/trusted_recurring_workflow.py",
            "src/ultimate_ai_agent/core/autonomy/mode4_scoped_work_session.py",
            "src/ultimate_ai_agent/core/autonomy/modes.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/approvals.py",
            "src/ultimate_ai_agent/core/autonomy/risk.py",
            "src/ultimate_ai_agent/core/autonomy/revocation.py",
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run.py",
            "src/ultimate_ai_agent/core/autonomy/recurring.py",
            "src/ultimate_ai_agent/core/autonomy/scoped_recurring.py",
            "src/ultimate_ai_agent/core/autonomy/tool_autonomy_single_session.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run_promotion.py",
            "src/ultimate_ai_agent/core/autonomy/v1_safety_freeze.py",
            "src/ultimate_ai_agent/core/autonomy/foundation_freeze.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
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
                if ".test." in rel:
                    continue
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M136 forbidden cross-tool dependency execution fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m136_cross_tool_dependency_execution_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m136_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M136 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m136_roadmap_currentness(
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
            f"missing M136 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m136" not in text
            or "cross-tool dependency execution" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M136 Cross-Tool Dependency Execution"
            )
        if (
            "m136 is implemented/released" not in text
            and "checkpoint m136 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M136 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m136",
                "pre-alpha checkpoint",
                "m136",
                "cross-tool dependency execution",
                "implemented/released",
            ),
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
                    f"active docs missing expected M136-M138/M139-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "autonomy abuse/loop detection is implemented",
            "m139 autonomy abuse/loop detection is implemented",
            "error handling guardrail runtime is implemented",
            "browser action is implemented",
            "connector write is implemented",
            "account auth is implemented",
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
                    f"active docs imply forbidden M136 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
