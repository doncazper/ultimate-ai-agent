from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart039Mixin:
    """Legacy checks from m140_higher_autonomy_red_team_freeze_contracts through m143_alpha_ui_app_readiness_contracts."""
    def check_m140_higher_autonomy_red_team_freeze_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/higher_autonomy_red_team_freeze.py",
            "docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE.md",
            "docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_POLICY.md",
            "docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_RECEIPT_PLAN.md",
            "docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_NON_GOALS.md",
            "docs/autonomy/M140_TO_M141_BOUNDARY.md",
            "docs/release_notes/checkpoint_m140.md",
            "docs/archive/checkpoints/m140/README_IMPORT.md",
            "docs/archive/checkpoints/m140/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m140_higher_autonomy_red_team_freeze.py",
            "tests/test_m140_gate_integration.py",
        ]
        failures = [
            f"missing M140 higher-autonomy red-team freeze file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m140_higher_autonomy_red_team_freeze import _request
            from ultimate_ai_agent.core.autonomy import (
                HigherAutonomyRedTeamFreezeStatus,
                build_higher_autonomy_red_team_freeze_report,
                validate_higher_autonomy_red_team_freeze_report,
            )

            report = build_higher_autonomy_red_team_freeze_report(_request())
            if (
                report.status != HigherAutonomyRedTeamFreezeStatus.frozen_for_review
                or not report.contract_only
                or not report.review_only
                or not report.freeze_only
                or not report.deterministic
                or not report.local_only
                or not report.safe_refs_only
                or not report.m131_m139_covered
                or not report.red_team_review_bound
                or not report.audit_replay_bound
                or not report.revocation_readiness_bound
                or not report.no_effect_receipt_required
                or not report.no_broad_unsandboxed_autonomy
                or not report.no_production_authority
                or report.red_team_runtime_started
                or report.red_team_harness_execution_performed
                or report.adversarial_test_execution_performed
                or report.autonomous_execution_performed
                or report.broad_autonomy_granted
                or report.global_autonomy_switch_enabled
                or report.execution_performed
                or report.tool_execution_performed
                or report.shell_execution_performed
                or report.browser_action_performed
                or report.connector_action_performed
                or report.network_access_performed
                or report.plugin_execution_performed
                or report.background_worker_started
                or report.scheduler_started
                or report.mobile_sensor_performed
                or report.remote_execution_performed
                or report.model_call_performed
                or report.memory_write_performed
                or report.context_injection_performed
                or report.raw_prompt_payload_exposed
                or report.credential_cookie_access_performed
                or report.backend_route_added
                or report.control_center_control_added
                or report.dependency_added
                or report.alpha_release_enabled
                or report.beta_release_enabled
                or report.production_authority_granted
                or report.side_effects_performed
                or "M140_HIGHER_AUTONOMY_RED_TEAM_FREEZE_REVIEW_ONLY"
                not in report.reason_codes
                or "M140_M131_M139_COVERED" not in report.reason_codes
                or "M140_NO_RED_TEAM_RUNTIME" not in report.reason_codes
                or "M140_NO_BROAD_UNSANDBOXED_AUTONOMY" not in report.reason_codes
                or "M140_NO_PRODUCTION_AUTHORITY" not in report.reason_codes
                or "M141_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M140 higher-autonomy red-team freeze report is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"red_team_runtime_started": True}, "M140_RED_TEAM_RUNTIME_DENIED"),
                (
                    {"red_team_harness_execution_performed": True},
                    "M140_RED_TEAM_HARNESS_EXECUTION_DENIED",
                ),
                (
                    {"adversarial_test_execution_performed": True},
                    "M140_ADVERSARIAL_TEST_EXECUTION_DENIED",
                ),
                (
                    {"autonomous_execution_performed": True},
                    "M140_AUTONOMOUS_EXECUTION_DENIED",
                ),
                ({"tool_execution_performed": True}, "M140_TOOL_EXECUTION_DENIED"),
                ({"browser_action_performed": True}, "M140_BROWSER_ACTION_DENIED"),
                (
                    {"connector_action_performed": True},
                    "M140_CONNECTOR_ACTION_DENIED",
                ),
                ({"backend_route_added": True}, "M140_BACKEND_ROUTE_DENIED"),
                ({"alpha_release_enabled": True}, "M140_ALPHA_RELEASE_DENIED"),
                ({"beta_release_enabled": True}, "M140_BETA_RELEASE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M140_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_higher_autonomy_red_team_freeze_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M140 unsafe red-team freeze mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M140 unsafe red-team freeze mutation raised {exc!s}"
                        )
        except Exception as exc:
            failures.append(f"M140 red-team freeze validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "higher-autonomy red-team freeze",
            "contract-only",
            "review-only",
            "freeze-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "accepted m131-m139",
            "red-team checklist",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no red-team runtime",
            "no red-team harness execution",
            "no adversarial test execution",
            "no autonomous execution",
            "no broad autonomy",
            "no global autonomy switch",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no browser action",
            "no connector action",
            "no network access",
            "no plugin execution",
            "no background worker",
            "no scheduler",
            "no mobile sensor",
            "no remote execution",
            "no model call",
            "no memory write",
            "no context injection",
            "no raw prompt",
            "no credential",
            "no backend route",
            "no control center control",
            "no dependency",
            "m141 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M140 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m140_higher_autonomy_red_team_freeze_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "red_team_runtime_enabled=True",
            "red_team_harness_execution_enabled=True",
            "adversarial_test_execution_enabled=True",
            "autonomous_execution_enabled=True",
            "broad_autonomy_enabled=True",
            "global_autonomy_switch_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_action_enabled=True",
            "connector_action_enabled=True",
            "network_access_enabled=True",
            "plugin_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "red_team_runtime_started=True",
            "red_team_harness_execution_performed=True",
            "adversarial_test_execution_performed=True",
            "autonomous_execution_performed=True",
            "tool_execution_performed=True",
            "browser_action_performed=True",
            "connector_action_performed=True",
            "/autonomy/higher-autonomy-red-team-freeze/start",
            "/red-team/run",
            "/red-team/harness/run",
            "/adversarial-tests/run",
            "/autonomy/execute",
            "/multi-user/enable",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/higher_autonomy_red_team_freeze.py",
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
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if ".test." in rel or _is_static_safety_scan_allowed_file(
                    rel, allowed_files
                ):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M140 forbidden red-team freeze fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m140_higher_autonomy_red_team_freeze_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m140_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M140 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m140_roadmap_currentness(
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
            f"missing M140 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m140" not in text
            or "higher-autonomy red-team freeze" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M140 Higher-Autonomy Red-Team Freeze"
            )
        if (
            "m140 is implemented/released" not in text
            and "checkpoint m140 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M140 implemented/released")
        for version_label, product_target, milestone, title, status in [
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
                    f"active docs missing expected M140/M141-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "multi-user product boundary is implemented",
            "m141 multi-user product boundary is implemented",
            "multi-user runtime is implemented",
            "tenant runtime is implemented",
            "workspace sharing is implemented",
            "identity federation is implemented",
            "red-team runtime is implemented",
            "red-team harness execution is implemented",
            "adversarial test execution is implemented",
            "autonomous execution is implemented",
            "broad autonomy is implemented",
            "global autonomy switch is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser action execution is implemented",
            "connector action execution is implemented",
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
                    f"active docs imply forbidden M140 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m141_multi_user_product_boundary_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/productization/__init__.py",
            "src/ultimate_ai_agent/core/productization/multi_user_product_boundary.py",
            "docs/productization/MULTI_USER_PRODUCT_BOUNDARY.md",
            "docs/productization/MULTI_USER_PRODUCT_BOUNDARY_POLICY.md",
            "docs/productization/MULTI_USER_PRODUCT_BOUNDARY_AUTHORITY_BOUNDARY.md",
            "docs/productization/MULTI_USER_PRODUCT_BOUNDARY_RECEIPT_PLAN.md",
            "docs/productization/MULTI_USER_PRODUCT_BOUNDARY_NON_GOALS.md",
            "docs/productization/M141_TO_M142_BOUNDARY.md",
            "docs/release_notes/checkpoint_m141.md",
            "docs/archive/checkpoints/m141/README_IMPORT.md",
            "docs/archive/checkpoints/m141/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m141_multi_user_product_boundary.py",
            "tests/test_m141_gate_integration.py",
        ]
        failures = [
            f"missing M141 multi-user product boundary file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m141_multi_user_product_boundary import _request
            from ultimate_ai_agent.core.productization import (
                MultiUserProductBoundaryStatus,
                build_multi_user_product_boundary_record,
                validate_multi_user_product_boundary_record,
            )

            record = build_multi_user_product_boundary_record(_request())
            if (
                record.status != MultiUserProductBoundaryStatus.product_boundary_review
                or not record.contract_only
                or not record.review_only
                or not record.deterministic
                or not record.local_only
                or not record.safe_refs_only
                or not record.product_boundary_only
                or not record.m101_m140_covered
                or not record.actor_boundary_bound
                or not record.workspace_boundary_bound
                or not record.tenant_boundary_bound
                or not record.role_boundary_bound
                or not record.privacy_boundary_bound
                or not record.audit_replay_bound
                or not record.revocation_readiness_bound
                or not record.no_effect_receipt_required
                or not record.no_multi_user_runtime
                or not record.no_account_tenancy
                or not record.no_auth_runtime
                or not record.no_workspace_sharing
                or not record.no_production_authority
                or record.multi_user_runtime_started
                or record.account_tenancy_enabled
                or record.tenant_runtime_started
                or record.workspace_sharing_enabled
                or record.identity_federation_enabled
                or record.auth_runtime_started
                or record.login_enabled
                or record.session_cookie_enabled
                or record.credential_handling_performed
                or record.persistent_identity_store_enabled
                or record.account_connector_enabled
                or record.production_runtime_enabled
                or record.execution_performed
                or record.tool_execution_performed
                or record.shell_execution_performed
                or record.browser_action_performed
                or record.connector_action_performed
                or record.network_access_performed
                or record.plugin_execution_performed
                or record.background_worker_started
                or record.scheduler_started
                or record.mobile_sensor_performed
                or record.remote_execution_performed
                or record.model_call_performed
                or record.memory_write_performed
                or record.context_injection_performed
                or record.raw_prompt_payload_exposed
                or record.credential_cookie_access_performed
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.alpha_privacy_review_enabled
                or record.alpha_release_enabled
                or record.beta_release_enabled
                or record.production_authority_granted
                or record.side_effects_performed
                or "M141_MULTI_USER_PRODUCT_BOUNDARY_REVIEW_ONLY"
                not in record.reason_codes
                or "M141_M101_M140_COVERED" not in record.reason_codes
                or "M141_NO_MULTI_USER_RUNTIME" not in record.reason_codes
                or "M141_NO_ACCOUNT_TENANCY" not in record.reason_codes
                or "M141_NO_AUTH_OR_IDENTITY_FEDERATION" not in record.reason_codes
                or "M141_NO_WORKSPACE_SHARING" not in record.reason_codes
                or "M141_NO_PRODUCTION_AUTHORITY" not in record.reason_codes
                or "M142_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M141 multi-user product boundary record is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"multi_user_runtime_started": True},
                    "M141_MULTI_USER_RUNTIME_DENIED",
                ),
                ({"account_tenancy_enabled": True}, "M141_ACCOUNT_TENANCY_DENIED"),
                ({"tenant_runtime_started": True}, "M141_TENANT_RUNTIME_DENIED"),
                ({"workspace_sharing_enabled": True}, "M141_WORKSPACE_SHARING_DENIED"),
                (
                    {"identity_federation_enabled": True},
                    "M141_IDENTITY_FEDERATION_DENIED",
                ),
                ({"auth_runtime_started": True}, "M141_AUTH_RUNTIME_DENIED"),
                ({"login_enabled": True}, "M141_LOGIN_DENIED"),
                (
                    {"persistent_identity_store_enabled": True},
                    "M141_PERSISTENT_IDENTITY_STORE_DENIED",
                ),
                ({"tool_execution_performed": True}, "M141_TOOL_EXECUTION_DENIED"),
                ({"browser_action_performed": True}, "M141_BROWSER_ACTION_DENIED"),
                (
                    {"connector_action_performed": True},
                    "M141_CONNECTOR_ACTION_DENIED",
                ),
                ({"backend_route_added": True}, "M141_BACKEND_ROUTE_DENIED"),
                (
                    {"alpha_privacy_review_enabled": True},
                    "M141_ALPHA_PRIVACY_REVIEW_DENIED",
                ),
                ({"beta_release_enabled": True}, "M141_BETA_RELEASE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M141_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_multi_user_product_boundary_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M141 unsafe product boundary mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M141 unsafe product boundary mutation raised {exc!s}"
                        )
        except Exception as exc:
            failures.append(f"M141 product boundary validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "multi-user product boundary",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "product-boundary-only",
            "route-free",
            "no-effect",
            "accepted m101-m140",
            "user boundary refs",
            "workspace boundary refs",
            "tenant boundary refs",
            "role boundary refs",
            "privacy boundary refs",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no multi-user runtime",
            "no account tenancy",
            "no tenant runtime",
            "no workspace sharing",
            "no identity federation",
            "no organization admin runtime",
            "no cross-workspace access",
            "no auth runtime",
            "no login",
            "no session material runtime",
            "no private auth material",
            "no persistent identity store",
            "no account connector runtime",
            "no production runtime",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no browser action",
            "no connector action",
            "no network access",
            "no plugin execution",
            "no background worker",
            "no scheduler",
            "no mobile sensor",
            "no remote execution",
            "no model call",
            "no memory write",
            "no context injection",
            "no raw prompt",
            "no backend route",
            "no control center control",
            "no dependency",
            "no alpha privacy review",
            "no beta release",
            "no production authority",
            "m142 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M141 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m141_multi_user_product_boundary_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "multi_user_runtime_enabled=True",
            "account_tenancy_enabled=True",
            "tenant_runtime_enabled=True",
            "workspace_sharing_enabled=True",
            "identity_federation_enabled=True",
            "org_admin_runtime_enabled=True",
            "cross_workspace_access_enabled=True",
            "auth_runtime_enabled=True",
            "login_enabled=True",
            "session_cookie_enabled=True",
            "credential_handling_enabled=True",
            "persistent_identity_store_enabled=True",
            "account_connector_enabled=True",
            "production_runtime_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_action_enabled=True",
            "connector_action_enabled=True",
            "network_access_enabled=True",
            "plugin_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "dependency_added=True",
            "alpha_privacy_review_enabled=True",
            "beta_release_enabled=True",
            "production_authority_granted=True",
            "multi_user_runtime_started=True",
            "tenant_runtime_started=True",
            "auth_runtime_started=True",
            "tool_execution_performed=True",
            "browser_action_performed=True",
            "connector_action_performed=True",
            "/multi-user/enable",
            "/tenants/create",
            "/workspaces/share",
            "/identity/federation/enable",
            "/auth/login",
            "/alpha/privacy-review/start",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/productization/__init__.py",
            "src/ultimate_ai_agent/core/productization/multi_user_product_boundary.py",
            "src/ultimate_ai_agent/core/autonomy/higher_autonomy_red_team_freeze.py",
            "src/ultimate_ai_agent/core/autonomy/abuse_loop_detection.py",
            "src/ultimate_ai_agent/core/autonomy/error_handling_guardrails.py",
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
                if ".test." in rel or _is_static_safety_scan_allowed_file(
                    rel, allowed_files
                ):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M141 forbidden product boundary fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m141_multi_user_product_boundary_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m141_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M141 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m141_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
        ]
        failures = [
            f"missing M141 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m141" not in text or "multi-user product boundary" not in text:
            failures.append(
                "active docs do not identify Checkpoint M141 Multi-User Product Boundary"
            )
        if (
            "m141 is implemented/released" not in text
            and "checkpoint m141 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M141 implemented/released")
        for version_label, product_target, milestone, title, status in [
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
                "implemented/released",
            ),
            (
                "checkpoint m142",
                "pre-alpha checkpoint",
                "m142",
                "alpha privacy review",
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
                    f"active docs missing expected M141/M142-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "alpha privacy review is implemented",
            "m142 alpha privacy review is implemented",
            "alpha privacy runtime is implemented",
            "privacy review runtime is implemented",
            "alpha ui runtime is implemented",
            "multi-user runtime is implemented",
            "account tenancy is implemented",
            "tenant runtime is implemented",
            "workspace sharing is implemented",
            "identity federation is implemented",
            "auth runtime is implemented",
            "login is implemented",
            "production runtime is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser action execution is implemented",
            "connector action execution is implemented",
            "network access is implemented",
            "plugin execution is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m142 dependency is added",
            "beta is released",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M141 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m142_alpha_privacy_review_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/productization/alpha_privacy_review.py",
            "docs/productization/ALPHA_PRIVACY_REVIEW.md",
            "docs/productization/ALPHA_PRIVACY_REVIEW_POLICY.md",
            "docs/productization/ALPHA_PRIVACY_REVIEW_AUTHORITY_BOUNDARY.md",
            "docs/productization/ALPHA_PRIVACY_REVIEW_RECEIPT_PLAN.md",
            "docs/productization/ALPHA_PRIVACY_REVIEW_NON_GOALS.md",
            "docs/productization/M142_TO_M143_BOUNDARY.md",
            "docs/release_notes/checkpoint_m142.md",
            "docs/archive/checkpoints/m142/README_IMPORT.md",
            "docs/archive/checkpoints/m142/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m142_alpha_privacy_review.py",
            "tests/test_m142_gate_integration.py",
        ]
        failures = [
            f"missing M142 alpha privacy review file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m142_alpha_privacy_review import _request
            from ultimate_ai_agent.core.productization import (
                AlphaPrivacyReviewStatus,
                build_alpha_privacy_review_record,
                validate_alpha_privacy_review_record,
            )

            record = build_alpha_privacy_review_record(_request())
            if (
                record.status != AlphaPrivacyReviewStatus.privacy_review_recorded
                or not record.contract_only
                or not record.review_only
                or not record.deterministic
                or not record.local_only
                or not record.safe_refs_only
                or not record.alpha_privacy_review_only
                or not record.m101_m141_covered
                or not record.privacy_review_bound
                or not record.data_boundary_bound
                or not record.disclosure_review_bound
                or not record.consent_review_bound
                or not record.retention_review_bound
                or not record.audit_replay_bound
                or not record.revocation_readiness_bound
                or not record.no_effect_receipt_required
                or not record.no_privacy_review_execution
                or not record.no_alpha_signoff
                or not record.no_alpha_ui_runtime
                or not record.no_production_authority
                or record.privacy_review_execution_performed
                or record.alpha_privacy_signoff_enabled
                or record.alpha_ui_runtime_started
                or record.raw_private_content_accessed
                or record.execution_performed
                or record.tool_execution_performed
                or record.browser_action_performed
                or record.connector_action_performed
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.beta_release_enabled
                or record.production_authority_granted
                or "M142_ALPHA_PRIVACY_REVIEW_REVIEW_ONLY" not in record.reason_codes
                or "M142_M101_M141_COVERED" not in record.reason_codes
                or "M142_NO_PRIVACY_REVIEW_EXECUTION" not in record.reason_codes
                or "M142_NO_ALPHA_PRIVACY_SIGNOFF" not in record.reason_codes
                or "M142_NO_ALPHA_UI_RUNTIME" not in record.reason_codes
                or "M142_NO_RAW_PRIVATE_CONTENT" not in record.reason_codes
                or "M142_NO_PRODUCTION_AUTHORITY" not in record.reason_codes
                or "M143_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M142 alpha privacy review record is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"privacy_review_execution_performed": True},
                    "M142_PRIVACY_REVIEW_EXECUTION_DENIED",
                ),
                (
                    {"alpha_privacy_signoff_enabled": True},
                    "M142_ALPHA_PRIVACY_SIGNOFF_DENIED",
                ),
                ({"alpha_ui_runtime_started": True}, "M142_ALPHA_UI_RUNTIME_DENIED"),
                (
                    {"raw_private_content_accessed": True},
                    "M142_RAW_PRIVATE_CONTENT_DENIED",
                ),
                ({"backend_route_added": True}, "M142_BACKEND_ROUTE_DENIED"),
                ({"dependency_added": True}, "M142_DEPENDENCY_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M142_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_alpha_privacy_review_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M142 unsafe privacy review mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M142 unsafe privacy review mutation raised {exc!s}"
                        )
        except Exception as exc:
            failures.append(f"M142 privacy review validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "alpha privacy review",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "alpha-privacy-review-only",
            "route-free",
            "no-effect",
            "accepted m101-m141",
            "privacy review refs",
            "data boundary refs",
            "disclosure review refs",
            "consent review refs",
            "retention review refs",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no privacy review execution",
            "no alpha privacy sign-off",
            "no alpha ui runtime",
            "no raw private content access",
            "no raw prompt",
            "no backend route",
            "no control center control",
            "no dependency",
            "no beta release",
            "no production authority",
            "m143 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M142 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m142_alpha_privacy_review_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "privacy_review_execution_enabled=True",
            "alpha_privacy_signoff_enabled=True",
            "alpha_ui_runtime_enabled=True",
            "alpha_release_enabled=True",
            "beta_release_enabled=True",
            "production_authority_granted=True",
            "raw_private_content_access_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_action_enabled=True",
            "connector_action_enabled=True",
            "network_access_enabled=True",
            "plugin_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "dependency_added=True",
            "privacy_review_execution_performed=True",
            "alpha_ui_runtime_started=True",
            "raw_private_content_accessed=True",
            "/alpha/privacy-review/start",
            "/alpha/privacy-review/signoff",
            "/alpha/ui/start",
            "/privacy-review/execute",
            "/privacy/raw-content",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/productization/__init__.py",
            "src/ultimate_ai_agent/core/productization/alpha_privacy_review.py",
            "src/ultimate_ai_agent/core/productization/multi_user_product_boundary.py",
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
                if ".test." in rel or _is_static_safety_scan_allowed_file(
                    rel, allowed_files
                ):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M142 forbidden alpha privacy fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m142_alpha_privacy_review_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m142_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M142 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m142_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
        ]
        failures = [
            f"missing M142 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m142" not in text or "alpha privacy review" not in text:
            failures.append("active docs do not identify Checkpoint M142")
        if (
            "m142 is implemented/released" not in text
            and "checkpoint m142 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M142 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m141",
                "pre-alpha checkpoint",
                "m141",
                "multi-user product boundary",
                "implemented/released",
            ),
            (
                "checkpoint m142",
                "pre-alpha checkpoint",
                "m142",
                "alpha privacy review",
                "implemented/released",
            ),
            (
                "checkpoint m143",
                "pre-alpha checkpoint",
                "m143",
                "alpha ui and app readiness",
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
                    f"active docs missing expected M142/M143-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "alpha ui runtime is implemented",
            "alpha app readiness runtime is implemented",
            "alpha release is implemented",
            "beta is released",
            "production authority is implemented",
            "privacy review execution is implemented",
            "raw private content access is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m143 dependency is added",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M142 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m143_alpha_ui_app_readiness_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/productization/alpha_ui_app_readiness.py",
            "docs/productization/ALPHA_UI_APP_READINESS.md",
            "docs/productization/ALPHA_UI_APP_READINESS_POLICY.md",
            "docs/productization/ALPHA_UI_APP_READINESS_AUTHORITY_BOUNDARY.md",
            "docs/productization/ALPHA_UI_APP_READINESS_RECEIPT_PLAN.md",
            "docs/productization/ALPHA_UI_APP_READINESS_NON_GOALS.md",
            "docs/productization/M143_TO_M144_BOUNDARY.md",
            "docs/release_notes/checkpoint_m143.md",
            "docs/archive/checkpoints/m143/README_IMPORT.md",
            "docs/archive/checkpoints/m143/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m143_alpha_ui_app_readiness.py",
            "tests/test_m143_gate_integration.py",
        ]
        failures = [
            f"missing M143 alpha UI/app readiness file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m143_alpha_ui_app_readiness import _request
            from ultimate_ai_agent.core.productization import (
                AlphaUiAppReadinessStatus,
                build_alpha_ui_app_readiness_record,
                validate_alpha_ui_app_readiness_record,
            )

            record = build_alpha_ui_app_readiness_record(_request())
            if (
                record.status != AlphaUiAppReadinessStatus.readiness_review_recorded
                or not record.contract_only
                or not record.review_only
                or not record.deterministic
                or not record.local_only
                or not record.safe_refs_only
                or not record.alpha_ui_app_readiness_only
                or not record.m101_m142_covered
                or not record.ui_readiness_bound
                or not record.app_readiness_bound
                or not record.privacy_review_bound
                or not record.accessibility_review_bound
                or not record.release_blocker_bound
                or not record.audit_replay_bound
                or not record.revocation_readiness_bound
                or not record.no_effect_receipt_required
                or not record.no_alpha_ui_runtime
                or not record.no_app_readiness_execution
                or not record.no_app_build
                or not record.no_app_store_connect
                or not record.no_alpha_release
                or not record.no_production_authority
                or record.alpha_ui_runtime_started
                or record.app_readiness_execution_performed
                or record.app_build_performed
                or record.app_store_connect_performed
                or record.testflight_upload_performed
                or record.alpha_release_enabled
                or record.beta_release_enabled
                or record.raw_private_content_accessed
                or record.execution_performed
                or record.tool_execution_performed
                or record.browser_action_performed
                or record.connector_action_performed
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.production_authority_granted
                or "M143_ALPHA_UI_APP_READINESS_REVIEW_ONLY" not in record.reason_codes
                or "M143_M101_M142_COVERED" not in record.reason_codes
                or "M143_NO_ALPHA_UI_RUNTIME" not in record.reason_codes
                or "M143_NO_APP_READINESS_EXECUTION" not in record.reason_codes
                or "M143_NO_APP_BUILD" not in record.reason_codes
                or "M143_NO_APP_STORE_CONNECT" not in record.reason_codes
                or "M143_NO_ALPHA_RELEASE" not in record.reason_codes
                or "M143_NO_PRODUCTION_AUTHORITY" not in record.reason_codes
                or "M144_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M143 alpha UI/app readiness record is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"alpha_ui_runtime_started": True}, "M143_ALPHA_UI_RUNTIME_DENIED"),
                (
                    {"app_readiness_execution_performed": True},
                    "M143_APP_READINESS_EXECUTION_DENIED",
                ),
                ({"app_build_performed": True}, "M143_APP_BUILD_DENIED"),
                (
                    {"app_store_connect_performed": True},
                    "M143_APP_STORE_CONNECT_DENIED",
                ),
                (
                    {"testflight_upload_performed": True},
                    "M143_TESTFLIGHT_UPLOAD_DENIED",
                ),
                ({"alpha_release_enabled": True}, "M143_ALPHA_RELEASE_DENIED"),
                (
                    {"raw_private_content_accessed": True},
                    "M143_RAW_PRIVATE_CONTENT_DENIED",
                ),
                ({"backend_route_added": True}, "M143_BACKEND_ROUTE_DENIED"),
                ({"dependency_added": True}, "M143_DEPENDENCY_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M143_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_alpha_ui_app_readiness_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M143 unsafe readiness mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M143 unsafe readiness mutation raised {exc!s}"
                        )
        except Exception as exc:
            failures.append(f"M143 readiness validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "alpha ui and app readiness",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "alpha-ui-app-readiness-only",
            "route-free",
            "no-effect",
            "accepted m101-m142",
            "ui readiness refs",
            "app readiness refs",
            "privacy review refs",
            "accessibility review refs",
            "release blocker refs",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no alpha ui runtime",
            "no app readiness execution",
            "no app build",
            "no app store connect",
            "no alpha release",
            "no raw private content access",
            "no backend route",
            "no control center control",
            "no dependency",
            "no beta release",
            "no production authority",
            "m144 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M143 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)
