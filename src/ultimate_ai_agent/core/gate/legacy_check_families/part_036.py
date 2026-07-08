from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart036Mixin:
    """Legacy checks from m133_long_running_task_supervisor_contracts through m134_roadmap_currentness."""
    def check_m133_long_running_task_supervisor_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/long_running_task_supervisor.py",
            "tests/test_m133_long_running_task_supervisor.py",
            "tests/test_m133_gate_integration.py",
            "docs/autonomy/LONG_RUNNING_TASK_SUPERVISOR.md",
            "docs/autonomy/LONG_RUNNING_TASK_SUPERVISOR_POLICY.md",
            "docs/autonomy/LONG_RUNNING_TASK_SUPERVISOR_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/LONG_RUNNING_TASK_SUPERVISOR_RECEIPT_PLAN.md",
            "docs/autonomy/LONG_RUNNING_TASK_SUPERVISOR_NON_GOALS.md",
            "docs/autonomy/M133_TO_M134_BOUNDARY.md",
            "docs/release_notes/checkpoint_m133.md",
            "docs/archive/checkpoints/m133/README_IMPORT.md",
            "docs/archive/checkpoints/m133/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M133 long-running task supervisor file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            sys.path.insert(0, str(self.root / "src"))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m133_long_running_task_supervisor import _request
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyRiskClass,
                LongRunningTaskSupervisorStatus,
                build_long_running_task_supervisor_decision,
                validate_long_running_task_supervisor_decision,
            )

            decision = build_long_running_task_supervisor_decision(_request())
            if (
                decision.status != LongRunningTaskSupervisorStatus.ready_for_review
                or decision.selected_mode
                != AutonomyAuthorityMode.trusted_recurring_automation
                or not decision.contract_only
                or not decision.review_only
                or not decision.long_running_supervisor_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.exact_scope_bound
                or not decision.mode5_bound
                or not decision.m132_trusted_workflow_bound
                or not decision.m131_work_session_bound
                or not decision.supervisor_plan_bound
                or not decision.task_state_bound
                or not decision.heartbeat_plan_bound
                or not decision.checkpoint_plan_bound
                or not decision.context_budget_bound
                or not decision.pause_resume_bound
                or not decision.audit_replay_bound
                or not decision.revocation_bound
                or not decision.kill_switch_bound
                or not decision.no_effect_receipt_required
                or decision.max_risk_class != AutonomyRiskClass.low
                or decision.mode5_runtime_authorized
                or decision.supervisor_runtime_authorized
                or decision.long_running_supervisor_start_authorized
                or decision.supervisor_started
                or decision.task_supervision_active
                or decision.heartbeat_monitor_started
                or decision.checkpoint_scheduler_started
                or decision.resume_execution_performed
                or decision.recovery_execution_performed
                or decision.human_checkpoint_scheduling_performed
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
                or decision.receipt_plan.supervisor_started
                or decision.receipt_plan.heartbeat_monitor_started
                or decision.receipt_plan.checkpoint_scheduler_started
                or decision.receipt_plan.resume_execution_performed
                or decision.receipt_plan.recovery_execution_performed
                or decision.receipt_plan.execution_performed
                or "M133_LONG_RUNNING_TASK_SUPERVISOR_CONTRACT_ONLY"
                not in decision.reason_codes
                or "M133_EXACT_SUPERVISOR_SCOPE_REQUIRED" not in decision.reason_codes
                or "M133_HEARTBEAT_AND_CHECKPOINT_REFS_REQUIRED"
                not in decision.reason_codes
                or "M133_NO_SUPERVISOR_RUNTIME" not in decision.reason_codes
                or "M134_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M133 long-running task supervisor decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"mode5_runtime_authorized": True}, "M133_MODE5_RUNTIME_DENIED"),
                (
                    {"supervisor_runtime_authorized": True},
                    "M133_SUPERVISOR_RUNTIME_DENIED",
                ),
                (
                    {"long_running_supervisor_start_authorized": True},
                    "M133_SUPERVISOR_START_DENIED",
                ),
                ({"supervisor_started": True}, "M133_SUPERVISOR_START_DENIED"),
                ({"task_supervision_active": True}, "M133_TASK_SUPERVISION_DENIED"),
                ({"heartbeat_monitor_started": True}, "M133_HEARTBEAT_MONITOR_DENIED"),
                (
                    {"checkpoint_scheduler_started": True},
                    "M133_CHECKPOINT_SCHEDULER_DENIED",
                ),
                ({"resume_execution_performed": True}, "M133_RESUME_EXECUTION_DENIED"),
                (
                    {"recovery_execution_performed": True},
                    "M135_RECOVERY_EXECUTION_DENIED",
                ),
                (
                    {"human_checkpoint_scheduling_performed": True},
                    "M134_HUMAN_CHECKPOINT_SCHEDULING_DENIED",
                ),
                ({"execution_performed": True}, "M133_EXECUTION_DENIED"),
                ({"tool_execution_performed": True}, "M133_TOOL_EXECUTION_DENIED"),
                ({"backend_route_added": True}, "M133_BACKEND_ROUTE_DENIED"),
                ({"beta_release_enabled": True}, "M133_BETA_RELEASE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M133_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_long_running_task_supervisor_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M133 unsafe long-running supervisor mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M133 unsafe long-running supervisor mutation raised {exc!s}"
                        )
            try:
                validate_long_running_task_supervisor_decision(
                    decision.model_copy(
                        update={
                            "receipt_plan": decision.receipt_plan.model_copy(
                                update={"store_raw_prompt": True}
                            )
                        }
                    )
                )
                failures.append("M133 receipt plan allowed raw prompt storage")
            except ValueError as exc:
                if "M133_RAW_PROMPT_DENIED" not in str(exc):
                    failures.append(f"M133 raw prompt receipt mutation raised {exc!s}")
        except Exception as exc:
            failures.append(
                f"M133 long-running task supervisor validation failed: {exc}"
            )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "long-running task supervisor",
            "contract-only",
            "review-only",
            "long-running-supervisor-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "exact scope",
            "mode 5",
            "m132 trusted workflow decision",
            "m131 scoped work-session decision",
            "supervisor plan",
            "task state",
            "run state",
            "heartbeat plan",
            "checkpoint plan",
            "checkpoint refs",
            "context budget",
            "pause condition",
            "resume condition",
            "stop condition",
            "risk decision",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no supervisor start",
            "no supervisor runtime",
            "no task supervision",
            "no heartbeat monitor",
            "no checkpoint scheduler",
            "no resume execution",
            "no recovery execution",
            "no human checkpoint scheduling",
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
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "m134 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M133 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m133_long_running_task_supervisor_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "supervisor_runtime_enabled=True",
            "long_running_supervisor_start_enabled=True",
            "task_supervision_enabled=True",
            "heartbeat_monitor_enabled=True",
            "checkpoint_scheduler_enabled=True",
            "resume_execution_enabled=True",
            "recovery_execution_enabled=True",
            "human_checkpoint_scheduling_enabled=True",
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
            "supervisor_runtime_requested=True",
            "long_running_supervisor_start_requested=True",
            "task_supervision_requested=True",
            "heartbeat_monitor_requested=True",
            "checkpoint_scheduler_requested=True",
            "resume_execution_requested=True",
            "recovery_execution_requested=True",
            "human_checkpoint_scheduling_requested=True",
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
            "supervisor_runtime_authorized=True",
            "long_running_supervisor_start_authorized=True",
            "supervisor_started=True",
            "task_supervision_active=True",
            "heartbeat_monitor_started=True",
            "checkpoint_scheduler_started=True",
            "resume_execution_performed=True",
            "recovery_execution_performed=True",
            "human_checkpoint_scheduling_performed=True",
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
            "/autonomy/long-running-supervisor",
            "/autonomy/long-running-supervisor/start",
            "/supervisor/long-running",
            "/supervisor/long-running/start",
            "/supervisor/tasks/start",
            "/supervisor/heartbeat/start",
            "/supervisor/checkpoints/schedule",
            "/supervisor/resume",
            "/supervisor/recover",
            "/checkpoints/human/schedule",
            "/tasks/long-running/start",
            "/background/supervisor/start",
            "/scheduler/start",
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
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/autonomous_recovery_planner.py",
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
                            f"M133 forbidden long-running supervisor fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m133_long_running_task_supervisor_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m133_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M133 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m133_roadmap_currentness(
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
            f"missing M133 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m133" not in text or "long-running task supervisor" not in text:
            failures.append(
                "active docs do not identify Checkpoint M133 Long-Running Task Supervisor"
            )
        if (
            "m133 is implemented/released" not in text
            and "checkpoint m133 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M133 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m133",
                "pre-alpha checkpoint",
                "m133",
                "long-running task supervisor",
                "implemented/released",
            ),
            (
                "checkpoint m134",
                "pre-alpha checkpoint",
                "m134",
                "human checkpoint scheduling",
                "implemented/released",
            ),
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
                    f"active docs missing expected M133-M138/M139-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "autonomy abuse/loop detection is implemented",
            "m139 autonomy abuse/loop detection is implemented",
            "recovery execution is implemented",
            "m135 recovery is implemented",
            "supervisor runtime is implemented",
            "supervisor start is implemented",
            "task supervision is implemented",
            "heartbeat monitor is implemented",
            "checkpoint scheduler is implemented",
            "resume execution is implemented",
            "scheduler is implemented",
            "background worker is implemented",
            "autonomous actions are implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "network access is implemented",
            "browser automation is implemented",
            "browser forms are implemented",
            "authenticated browser is implemented",
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
                    f"active docs imply forbidden M133 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m134_human_checkpoint_scheduling_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/human_checkpoint_scheduling.py",
            "tests/test_m134_human_checkpoint_scheduling.py",
            "tests/test_m134_gate_integration.py",
            "docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING.md",
            "docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_POLICY.md",
            "docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_RECEIPT_PLAN.md",
            "docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_NON_GOALS.md",
            "docs/autonomy/M134_TO_M135_BOUNDARY.md",
            "docs/release_notes/checkpoint_m134.md",
            "docs/archive/checkpoints/m134/README_IMPORT.md",
            "docs/archive/checkpoints/m134/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M134 human checkpoint scheduling file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            sys.path.insert(0, str(self.root / "src"))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m134_human_checkpoint_scheduling import _request
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyRiskClass,
                HumanCheckpointSchedulingStatus,
                build_human_checkpoint_scheduling_decision,
                validate_human_checkpoint_scheduling_decision,
            )

            decision = build_human_checkpoint_scheduling_decision(_request())
            if (
                decision.status != HumanCheckpointSchedulingStatus.ready_for_review
                or decision.selected_mode
                != AutonomyAuthorityMode.trusted_recurring_automation
                or not decision.contract_only
                or not decision.review_only
                or not decision.human_checkpoint_scheduling_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.exact_scope_bound
                or not decision.mode5_bound
                or not decision.m133_supervisor_bound
                or not decision.m132_trusted_workflow_bound
                or not decision.checkpoint_plan_bound
                or not decision.schedule_plan_bound
                or not decision.checkpoint_window_bound
                or not decision.reviewer_bound
                or not decision.consent_bound
                or not decision.expiration_bound
                or not decision.reminder_plan_bound
                or not decision.escalation_plan_bound
                or not decision.pause_stop_bound
                or not decision.audit_replay_bound
                or not decision.revocation_bound
                or not decision.kill_switch_bound
                or not decision.no_effect_receipt_required
                or decision.max_risk_class != AutonomyRiskClass.low
                or decision.mode5_runtime_authorized
                or decision.human_checkpoint_scheduler_authorized
                or decision.checkpoint_scheduled
                or decision.human_checkpoint_prompt_sent
                or decision.notification_delivered
                or decision.reminder_runtime_started
                or decision.calendar_written
                or decision.approval_captured
                or decision.escalation_runtime_started
                or decision.supervisor_runtime_started
                or decision.recovery_execution_performed
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
                or decision.receipt_plan.checkpoint_scheduled
                or decision.receipt_plan.prompt_sent
                or decision.receipt_plan.notification_delivered
                or decision.receipt_plan.calendar_written
                or decision.receipt_plan.approval_captured
                or decision.receipt_plan.escalation_started
                or decision.receipt_plan.execution_performed
                or "M134_HUMAN_CHECKPOINT_SCHEDULING_CONTRACT_ONLY"
                not in decision.reason_codes
                or "M134_EXACT_CHECKPOINT_SCOPE_REQUIRED" not in decision.reason_codes
                or "M134_HUMAN_REVIEWER_REFS_REQUIRED" not in decision.reason_codes
                or "M134_NO_SCHEDULER_OR_PROMPT_RUNTIME" not in decision.reason_codes
                or "M135_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M134 human checkpoint scheduling decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"mode5_runtime_authorized": True}, "M134_MODE5_RUNTIME_DENIED"),
                (
                    {"human_checkpoint_scheduler_authorized": True},
                    "M134_CHECKPOINT_SCHEDULER_DENIED",
                ),
                ({"checkpoint_scheduled": True}, "M134_CHECKPOINT_SCHEDULER_DENIED"),
                ({"human_checkpoint_prompt_sent": True}, "M134_PROMPT_RUNTIME_DENIED"),
                ({"notification_delivered": True}, "M134_NOTIFICATION_DELIVERY_DENIED"),
                ({"reminder_runtime_started": True}, "M134_REMINDER_RUNTIME_DENIED"),
                ({"calendar_written": True}, "M134_CALENDAR_WRITE_DENIED"),
                ({"approval_captured": True}, "M134_APPROVAL_CAPTURE_DENIED"),
                (
                    {"escalation_runtime_started": True},
                    "M134_ESCALATION_RUNTIME_DENIED",
                ),
                (
                    {"supervisor_runtime_started": True},
                    "M134_SUPERVISOR_RUNTIME_DENIED",
                ),
                (
                    {"recovery_execution_performed": True},
                    "M135_RECOVERY_EXECUTION_DENIED",
                ),
                ({"execution_performed": True}, "M134_EXECUTION_DENIED"),
                ({"tool_execution_performed": True}, "M134_TOOL_EXECUTION_DENIED"),
                ({"backend_route_added": True}, "M134_BACKEND_ROUTE_DENIED"),
                ({"beta_release_enabled": True}, "M134_BETA_RELEASE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M134_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_human_checkpoint_scheduling_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M134 unsafe checkpoint scheduling mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M134 unsafe checkpoint scheduling mutation raised {exc!s}"
                        )
            try:
                validate_human_checkpoint_scheduling_decision(
                    decision.model_copy(
                        update={
                            "receipt_plan": decision.receipt_plan.model_copy(
                                update={"store_raw_prompt": True}
                            )
                        }
                    )
                )
                failures.append("M134 receipt plan allowed raw prompt storage")
            except ValueError as exc:
                if "M134_RAW_PROMPT_DENIED" not in str(exc):
                    failures.append(f"M134 raw prompt receipt mutation raised {exc!s}")
        except Exception as exc:
            failures.append(
                f"M134 human checkpoint scheduling validation failed: {exc}"
            )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "human checkpoint scheduling",
            "contract-only",
            "review-only",
            "human-checkpoint-scheduling-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "exact scope",
            "mode 5",
            "m133 supervisor decision",
            "m132 trusted workflow decision",
            "checkpoint plan",
            "schedule plan",
            "checkpoint window",
            "reviewer ref",
            "consent",
            "expiration",
            "reminder plan",
            "escalation plan",
            "pause condition",
            "stop condition",
            "risk decision",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no checkpoint scheduled",
            "no scheduling",
            "no prompt",
            "no notification delivery",
            "no reminder runtime",
            "no calendar write",
            "no approval capture",
            "no escalation runtime",
            "no supervisor runtime",
            "no recovery execution",
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
            "m135 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M134 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m134_human_checkpoint_scheduling_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "mode5_runtime_enabled=True",
            "human_checkpoint_scheduler_enabled=True",
            "human_checkpoint_prompt_enabled=True",
            "notification_delivery_enabled=True",
            "reminder_runtime_enabled=True",
            "calendar_write_enabled=True",
            "approval_capture_enabled=True",
            "escalation_runtime_enabled=True",
            "supervisor_runtime_enabled=True",
            "recovery_execution_enabled=True",
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
            "human_checkpoint_scheduler_requested=True",
            "human_checkpoint_prompt_requested=True",
            "notification_delivery_requested=True",
            "reminder_runtime_requested=True",
            "calendar_write_requested=True",
            "approval_capture_requested=True",
            "escalation_runtime_requested=True",
            "supervisor_runtime_requested=True",
            "recovery_execution_requested=True",
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
            "human_checkpoint_scheduler_authorized=True",
            "checkpoint_scheduled=True",
            "human_checkpoint_prompt_sent=True",
            "notification_delivered=True",
            "reminder_runtime_started=True",
            "calendar_written=True",
            "approval_captured=True",
            "escalation_runtime_started=True",
            "supervisor_runtime_started=True",
            "recovery_execution_performed=True",
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
            "/autonomy/human-checkpoint-scheduling",
            "/autonomy/human-checkpoint-scheduling/start",
            "/checkpoints/human/schedule",
            "/checkpoints/human/prompt",
            "/checkpoints/human/notify",
            "/checkpoints/human/remind",
            "/calendar/write",
            "/approvals/capture",
            "/escalations/start",
            "/supervisor/recover",
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
                            f"M134 forbidden human checkpoint scheduling fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m134_human_checkpoint_scheduling_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m134_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M134 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m134_roadmap_currentness(
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
            f"missing M134 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m134" not in text or "human checkpoint scheduling" not in text:
            failures.append(
                "active docs do not identify Checkpoint M134 Human Checkpoint Scheduling"
            )
        if (
            "m134 is implemented/released" not in text
            and "checkpoint m134 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M134 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m134",
                "pre-alpha checkpoint",
                "m134",
                "human checkpoint scheduling",
                "implemented/released",
            ),
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
                    f"active docs missing expected M134-M138/M139-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "autonomy abuse/loop detection is implemented",
            "m139 autonomy abuse/loop detection is implemented",
            "checkpoint scheduler runtime is implemented",
            "prompt runtime is implemented",
            "notification delivery is implemented",
            "reminder runtime is implemented",
            "calendar write is implemented",
            "approval capture is implemented",
            "escalation runtime is implemented",
            "supervisor runtime is implemented",
            "scheduler is implemented",
            "background worker is implemented",
            "autonomous actions are implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "network access is implemented",
            "browser automation is implemented",
            "browser forms are implemented",
            "authenticated browser is implemented",
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
                    f"active docs imply forbidden M134 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
