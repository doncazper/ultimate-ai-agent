from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart035Mixin:
    """Legacy checks from m130_roadmap_currentness through m132_roadmap_currentness."""
    def check_m130_roadmap_currentness(
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
            f"missing M130 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m130" not in text or "connector safety freeze" not in text:
            failures.append(
                "active docs do not identify Checkpoint M130 Connector Safety Freeze"
            )
        if (
            "m130 is implemented/released" not in text
            and "checkpoint m130 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M130 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m130",
                "pre-alpha checkpoint",
                "m130",
                "connector safety freeze",
                "implemented/released",
            ),
            (
                "checkpoint m131",
                "pre-alpha checkpoint",
                "m131",
                "autonomy mode 4, scoped work session",
                "implemented/released",
            ),
            (
                "checkpoint m132",
                "pre-alpha checkpoint",
                "m132",
                "autonomy mode 5, trusted recurring workflow",
                "implemented/released",
            ),
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
                    f"active docs missing expected M130/M131/M132-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "higher autonomy is implemented",
            "live connector runtime is implemented",
            "account auth is implemented",
            "network access is implemented",
            "credential handling is implemented",
            "raw connector content is implemented",
            "full content read is implemented",
            "connector export is implemented",
            "connector send execution is implemented",
            "connector delete execution is implemented",
            "revocation execution is implemented",
            "kill switch execution is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "beta is released",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M130 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m131_autonomy_mode4_scoped_work_session_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/mode4_scoped_work_session.py",
            "tests/test_m131_autonomy_mode4_scoped_work_session.py",
            "tests/test_m131_gate_integration.py",
            "docs/autonomy/AUTONOMY_MODE4_SCOPED_WORK_SESSION.md",
            "docs/autonomy/AUTONOMY_MODE4_SCOPED_WORK_SESSION_POLICY.md",
            "docs/autonomy/AUTONOMY_MODE4_SCOPED_WORK_SESSION_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/AUTONOMY_MODE4_SCOPED_WORK_SESSION_RECEIPT_PLAN.md",
            "docs/autonomy/AUTONOMY_MODE4_SCOPED_WORK_SESSION_NON_GOALS.md",
            "docs/autonomy/M131_TO_M132_BOUNDARY.md",
            "docs/release_notes/checkpoint_m131.md",
            "docs/archive/checkpoints/m131/README_IMPORT.md",
            "docs/archive/checkpoints/m131/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M131 Mode 4 scoped work session file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            sys.path.insert(0, str(self.root / "src"))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m131_autonomy_mode4_scoped_work_session import _request
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyRiskClass,
                Mode4ScopedWorkSessionStatus,
                build_mode4_scoped_work_session_decision,
                validate_mode4_scoped_work_session_decision,
            )

            decision = build_mode4_scoped_work_session_decision(_request())
            if (
                decision.status != Mode4ScopedWorkSessionStatus.ready_for_review
                or decision.selected_mode
                != AutonomyAuthorityMode.scoped_autonomy_window
                or not decision.contract_only
                or not decision.review_only
                or not decision.scoped_work_session_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.exact_scope_bound
                or not decision.actor_bound
                or not decision.resource_bound
                or not decision.capability_bound
                or not decision.allowlist_bound
                or not decision.policy_decision_bound
                or not decision.approval_bundle_bound
                or not decision.risk_decision_bound
                or not decision.audit_replay_bound
                or not decision.revocation_bound
                or not decision.kill_switch_bound
                or not decision.no_effect_receipt_required
                or decision.max_risk_class != AutonomyRiskClass.medium
                or decision.mode4_runtime_authorized
                or decision.scoped_work_session_start_authorized
                or decision.session_started
                or decision.session_active
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
                or decision.background_worker_started
                or decision.scheduler_started
                or decision.model_call_performed
                or decision.memory_write_performed
                or decision.context_injection_performed
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.beta_release_enabled
                or decision.production_authority_granted
                or decision.trusted_recurring_workflow_enabled
                or decision.side_effects_performed
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or decision.receipt_plan.store_raw_prompt
                or decision.receipt_plan.store_raw_provider_payload
                or decision.receipt_plan.session_started
                or decision.receipt_plan.execution_performed
                or "M131_MODE4_SCOPED_WORK_SESSION_CONTRACT_ONLY"
                not in decision.reason_codes
                or "M131_EXACT_SCOPE_REQUIRED" not in decision.reason_codes
                or "M131_APPROVAL_BUNDLE_REQUIRED" not in decision.reason_codes
                or "M131_NO_SESSION_START_OR_EXECUTION" not in decision.reason_codes
                or "M132_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M131 Mode 4 scoped work session decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"mode4_runtime_authorized": True}, "M131_MODE4_RUNTIME_DENIED"),
                (
                    {"scoped_work_session_start_authorized": True},
                    "M131_SESSION_START_DENIED",
                ),
                ({"session_started": True}, "M131_SESSION_START_DENIED"),
                ({"session_active": True}, "M131_SESSION_ACTIVE_DENIED"),
                (
                    {"autonomous_actions_performed": True},
                    "M131_AUTONOMOUS_ACTIONS_DENIED",
                ),
                ({"execution_performed": True}, "M131_EXECUTION_DENIED"),
                ({"tool_execution_performed": True}, "M131_TOOL_EXECUTION_DENIED"),
                ({"browser_form_performed": True}, "M131_BROWSER_FORM_DENIED"),
                ({"background_worker_started": True}, "M131_BACKGROUND_WORKER_DENIED"),
                ({"backend_route_added": True}, "M131_BACKEND_ROUTE_DENIED"),
                ({"beta_release_enabled": True}, "M131_BETA_RELEASE_DENIED"),
                (
                    {"trusted_recurring_workflow_enabled": True},
                    "M132_TRUSTED_RECURRING_WORKFLOW_DENIED",
                ),
                (
                    {"production_authority_granted": True},
                    "M131_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_mode4_scoped_work_session_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M131 unsafe scoped work session mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M131 unsafe scoped work session mutation raised {exc!s}"
                        )
            try:
                validate_mode4_scoped_work_session_decision(
                    decision.model_copy(
                        update={
                            "receipt_plan": decision.receipt_plan.model_copy(
                                update={"store_raw_prompt": True}
                            )
                        }
                    )
                )
                failures.append("M131 receipt plan allowed raw prompt storage")
            except ValueError as exc:
                if "M131_RAW_PROMPT_DENIED" not in str(exc):
                    failures.append(f"M131 raw prompt receipt mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M131 Mode 4 scoped work session validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "autonomy mode 4",
            "scoped work session",
            "contract-only",
            "review-only",
            "scoped-work-session-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "exact scope",
            "actor-bound",
            "resource-bound",
            "capability-bound",
            "allowlist-bound",
            "duration-bound",
            "policy decision ref",
            "approval bundle ref",
            "risk decision ref",
            "audit ref",
            "replay ref",
            "revocation ref",
            "kill-switch ref",
            "no-effect receipt",
            "no session start",
            "no autonomous actions",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no network access",
            "no browser automation",
            "no browser forms",
            "no authenticated browser",
            "no download",
            "no upload",
            "no plugin execution",
            "no connector runtime",
            "no account auth",
            "no background worker",
            "no scheduler",
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "m132 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M131 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m131_autonomy_mode4_scoped_work_session_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "mode4_runtime_enabled=True",
            "scoped_work_session_start_enabled=True",
            "session_active=True",
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
            "background_worker_enabled=True",
            "scheduler_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "control_center_control_enabled=True",
            "dependency_added=True",
            "beta_release_enabled=True",
            "production_authority_granted=True",
            "trusted_recurring_workflow_enabled=True",
            "mode4_runtime_requested=True",
            "scoped_work_session_start_requested=True",
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
            "background_worker_requested=True",
            "scheduler_requested=True",
            "model_call_requested=True",
            "memory_write_requested=True",
            "context_injection_requested=True",
            "backend_route_requested=True",
            "control_center_control_requested=True",
            "dependency_requested=True",
            "beta_release_requested=True",
            "production_authority_requested=True",
            "trusted_recurring_workflow_requested=True",
            "mode4_runtime_authorized=True",
            "scoped_work_session_start_authorized=True",
            "session_started=True",
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
            "background_worker_started=True",
            "scheduler_started=True",
            "model_call_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "/autonomy/mode4",
            "/autonomy/mode4/start",
            "/autonomy/scoped-work-session",
            "/autonomy/scoped-work-session/start",
            "/autonomy/session/start",
            "/autonomy/actions/execute",
            "/autonomy/tools/execute",
            "/automation/session/start",
            "/automation/mode4/start",
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
            "/workers/start",
            "/scheduler/start",
            "/memory/write",
            "/context/inject",
            "/models/call",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/mode4_scoped_work_session.py",
            "src/ultimate_ai_agent/core/autonomy/modes.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/approvals.py",
            "src/ultimate_ai_agent/core/autonomy/risk.py",
            "src/ultimate_ai_agent/core/autonomy/revocation.py",
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run.py",
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
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if ".test." in rel:
                    continue
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M131 forbidden Mode 4 scoped work session fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m131_autonomy_mode4_scoped_work_session_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m131_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M131 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m131_roadmap_currentness(
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
            f"missing M131 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m131" not in text
            or "autonomy mode 4, scoped work session" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M131 Autonomy Mode 4, Scoped Work Session"
            )
        if (
            "m131 is implemented/released" not in text
            and "checkpoint m131 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M131 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m131",
                "pre-alpha checkpoint",
                "m131",
                "autonomy mode 4, scoped work session",
                "implemented/released",
            ),
            (
                "checkpoint m132",
                "pre-alpha checkpoint",
                "m132",
                "autonomy mode 5, trusted recurring workflow",
                "implemented/released",
            ),
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
                    f"active docs missing expected M131-M138/M139-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "autonomy abuse/loop detection is implemented",
            "m139 autonomy abuse/loop detection is implemented",
            "recurring workflow runtime is implemented",
            "recovery execution is implemented",
            "m135 recovery is implemented",
            "session start is implemented",
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
                    f"active docs imply forbidden M131 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m132_trusted_recurring_workflow_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/trusted_recurring_workflow.py",
            "tests/test_m132_trusted_recurring_workflow.py",
            "tests/test_m132_gate_integration.py",
            "docs/autonomy/TRUSTED_RECURRING_WORKFLOW.md",
            "docs/autonomy/TRUSTED_RECURRING_WORKFLOW_POLICY.md",
            "docs/autonomy/TRUSTED_RECURRING_WORKFLOW_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/TRUSTED_RECURRING_WORKFLOW_RECEIPT_PLAN.md",
            "docs/autonomy/TRUSTED_RECURRING_WORKFLOW_NON_GOALS.md",
            "docs/autonomy/M132_TO_M133_BOUNDARY.md",
            "docs/release_notes/checkpoint_m132.md",
            "docs/archive/checkpoints/m132/README_IMPORT.md",
            "docs/archive/checkpoints/m132/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M132 trusted recurring workflow file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            sys.path.insert(0, str(self.root / "src"))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m132_trusted_recurring_workflow import _request
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyRiskClass,
                TrustedRecurringWorkflowStatus,
                build_trusted_recurring_workflow_decision,
                validate_trusted_recurring_workflow_decision,
            )

            decision = build_trusted_recurring_workflow_decision(_request())
            if (
                decision.status != TrustedRecurringWorkflowStatus.ready_for_review
                or decision.selected_mode
                != AutonomyAuthorityMode.trusted_recurring_automation
                or not decision.contract_only
                or not decision.review_only
                or not decision.trusted_recurring_workflow_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.exact_scope_bound
                or not decision.mode5_bound
                or not decision.m131_work_session_bound
                or not decision.recurring_contract_bound
                or not decision.scoped_low_risk_recurring_bound
                or not decision.cadence_bound
                or not decision.approval_bundle_bound
                or not decision.approval_renewal_bound
                or not decision.expiration_bound
                or not decision.stop_conditions_bound
                or not decision.audit_replay_bound
                or not decision.revocation_bound
                or not decision.kill_switch_bound
                or not decision.no_effect_receipt_required
                or decision.max_risk_class != AutonomyRiskClass.low
                or decision.mode5_runtime_authorized
                or decision.trusted_recurring_workflow_start_authorized
                or decision.workflow_started
                or decision.recurrence_active
                or decision.recurring_runtime_started
                or decision.scheduler_started
                or decision.background_worker_started
                or decision.long_running_supervisor_started
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
                or decision.receipt_plan.workflow_started
                or decision.receipt_plan.recurring_runtime_started
                or decision.receipt_plan.scheduler_started
                or decision.receipt_plan.execution_performed
                or "M132_TRUSTED_RECURRING_WORKFLOW_CONTRACT_ONLY"
                not in decision.reason_codes
                or "M132_EXACT_RECURRING_SCOPE_REQUIRED" not in decision.reason_codes
                or "M132_APPROVAL_RENEWAL_REQUIRED" not in decision.reason_codes
                or "M132_NO_SCHEDULER_OR_RUNTIME" not in decision.reason_codes
                or "M133_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M132 trusted recurring workflow decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"mode5_runtime_authorized": True}, "M132_MODE5_RUNTIME_DENIED"),
                (
                    {"trusted_recurring_workflow_start_authorized": True},
                    "M132_WORKFLOW_START_DENIED",
                ),
                ({"workflow_started": True}, "M132_WORKFLOW_START_DENIED"),
                ({"recurrence_active": True}, "M132_RECURRENCE_ACTIVE_DENIED"),
                (
                    {"recurring_runtime_started": True},
                    "M132_RECURRING_RUNTIME_DENIED",
                ),
                ({"scheduler_started": True}, "M132_SCHEDULER_DENIED"),
                ({"background_worker_started": True}, "M132_BACKGROUND_WORKER_DENIED"),
                (
                    {"long_running_supervisor_started": True},
                    "M133_LONG_RUNNING_SUPERVISOR_DENIED",
                ),
                (
                    {"autonomous_actions_performed": True},
                    "M132_AUTONOMOUS_ACTIONS_DENIED",
                ),
                ({"execution_performed": True}, "M132_EXECUTION_DENIED"),
                ({"tool_execution_performed": True}, "M132_TOOL_EXECUTION_DENIED"),
                ({"backend_route_added": True}, "M132_BACKEND_ROUTE_DENIED"),
                ({"beta_release_enabled": True}, "M132_BETA_RELEASE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M132_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_trusted_recurring_workflow_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M132 unsafe trusted recurring workflow mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M132 unsafe trusted recurring workflow mutation raised {exc!s}"
                        )
            try:
                validate_trusted_recurring_workflow_decision(
                    decision.model_copy(
                        update={
                            "receipt_plan": decision.receipt_plan.model_copy(
                                update={"store_raw_prompt": True}
                            )
                        }
                    )
                )
                failures.append("M132 receipt plan allowed raw prompt storage")
            except ValueError as exc:
                if "M132_RAW_PROMPT_DENIED" not in str(exc):
                    failures.append(f"M132 raw prompt receipt mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M132 trusted recurring workflow validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "autonomy mode 5",
            "trusted recurring workflow",
            "contract-only",
            "review-only",
            "trusted-recurring-workflow-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "exact scope",
            "mode 5",
            "m131 scoped work-session decision",
            "m97 recurring automation contract",
            "m98 scoped low-risk recurring",
            "cadence",
            "approval bundle",
            "approval renewal",
            "expiration",
            "stop condition",
            "risk decision",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no workflow start",
            "no active recurrence",
            "no recurring runtime",
            "no scheduler",
            "no background worker",
            "no long-running supervisor",
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
            "m133 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M132 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m132_trusted_recurring_workflow_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "mode5_runtime_enabled=True",
            "trusted_recurring_workflow_start_enabled=True",
            "recurring_runtime_enabled=True",
            "recurrence_active=True",
            "scheduler_enabled=True",
            "background_worker_enabled=True",
            "long_running_supervisor_enabled=True",
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
            "trusted_recurring_workflow_start_requested=True",
            "recurring_runtime_requested=True",
            "scheduler_requested=True",
            "background_worker_requested=True",
            "long_running_supervisor_requested=True",
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
            "trusted_recurring_workflow_start_authorized=True",
            "workflow_started=True",
            "recurring_runtime_started=True",
            "scheduler_started=True",
            "background_worker_started=True",
            "long_running_supervisor_started=True",
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
            "/autonomy/mode5",
            "/autonomy/mode5/start",
            "/autonomy/trusted-recurring-workflow",
            "/autonomy/trusted-recurring-workflow/start",
            "/autonomy/workflow/start",
            "/autonomy/recurrence/start",
            "/automation/trusted-recurring/start",
            "/automation/recurring/start",
            "/scheduler/create",
            "/scheduler/start",
            "/background/start",
            "/workers/start",
            "/supervisor/start",
            "/supervisor/long-running/start",
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
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if ".test." in rel:
                    continue
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M132 forbidden trusted recurring workflow fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m132_trusted_recurring_workflow_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m132_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M132 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m132_roadmap_currentness(
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
            f"missing M132 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m132" not in text
            or "autonomy mode 5, trusted recurring workflow" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M132 Autonomy Mode 5, Trusted Recurring Workflow"
            )
        if (
            "m132 is implemented/released" not in text
            and "checkpoint m132 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M132 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m132",
                "pre-alpha checkpoint",
                "m132",
                "autonomy mode 5, trusted recurring workflow",
                "implemented/released",
            ),
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
                    f"active docs missing expected M132-M138/M139-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "autonomy abuse/loop detection is implemented",
            "m139 autonomy abuse/loop detection is implemented",
            "recovery execution is implemented",
            "m135 recovery is implemented",
            "workflow start is implemented",
            "recurrence activation is implemented",
            "recurring runtime is implemented",
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
                    f"active docs imply forbidden M132 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
