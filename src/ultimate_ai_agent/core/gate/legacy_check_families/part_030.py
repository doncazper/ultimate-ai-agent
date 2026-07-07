from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart030Mixin:
    """Legacy checks from m116_role_based_authority_contracts through m118_roadmap_currentness."""
    def check_m116_role_based_authority_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/role_based_authority.py",
            "docs/production/ROLE_BASED_AUTHORITY_MODEL.md",
            "docs/production/ROLE_BASED_AUTHORITY_BOUNDARY.md",
            "docs/production/ROLE_BASED_AUTHORITY_RECEIPT_PLAN.md",
            "docs/production/ROLE_BASED_AUTHORITY_NON_GOALS.md",
            "docs/production/M116_TO_M117_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m116_role_based_authority_model.py",
            "tests/test_m116_gate_integration.py",
        ]
        failures = [
            f"missing M116 role-based authority file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                build_mobile_approval_renewal_ux_report,
                build_mobile_kill_switch_revocation_record,
                build_mobile_sensor_audit_ledger_record,
                build_mobile_sensor_hardening_freeze_record,
            )
            from ultimate_ai_agent.core.production_readiness import (
                RoleBasedAuthorityModelStatus,
                build_account_connector_contract_review_record,
                build_production_audit_retention_policy_record,
                build_production_threat_model_record,
                build_role_based_authority_model_record,
                build_secrets_boundary_record,
                build_user_workspace_identity_record,
                validate_role_based_authority_model_record,
            )

            source_record = build_production_audit_retention_policy_record(
                source_record=build_account_connector_contract_review_record(
                    source_record=build_secrets_boundary_record(
                        source_record=build_user_workspace_identity_record(
                            source_record=build_production_threat_model_record(
                                source_record=build_mobile_sensor_hardening_freeze_record(
                                    source_record=build_mobile_sensor_audit_ledger_record(
                                        source_record=build_mobile_kill_switch_revocation_record(
                                            source_report=build_mobile_approval_renewal_ux_report()
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
            record = build_role_based_authority_model_record(
                source_record=source_record
            )
            if (
                record.status != RoleBasedAuthorityModelStatus.authority_model
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_production_audit_retention_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.role_bound
                or not record.authority_scope_bound
                or not record.permission_boundary_bound
                or not record.separation_of_duty_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_production_audit_retention_ref
                != source_record.audit_retention_policy_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.user_ref != source_record.user_ref
                or record.workspace_ref != source_record.workspace_ref
                or not record.role_refs
                or not record.authority_scope_refs
                or not record.permission_boundary_refs
                or not record.separation_of_duty_refs
                or not record.break_glass_boundary_ref.startswith(
                    "break-glass-boundary-ref:"
                )
                or "checkpoint:m115" not in record.accepted_checkpoint_refs
                or record.production_authority_enabled
                or record.production_runtime_enabled
                or record.authority_runtime_enabled
                or record.role_enforcement_enabled
                or record.permission_enforcement_enabled
                or record.auth_runtime_enabled
                or record.login_enabled
                or record.session_cookie_handling_enabled
                or record.oauth_flow_enabled
                or record.token_exchange_enabled
                or record.credential_handling_enabled
                or record.account_action_enabled
                or record.network_access_enabled
                or record.model_call_enabled
                or record.memory_write_enabled
                or record.context_injection_enabled
                or record.execution_enabled
                or record.tool_execution_enabled
                or record.shell_execution_enabled
                or record.browser_automation_enabled
                or record.plugin_execution_enabled
                or record.mobile_sensor_enabled
                or record.background_worker_enabled
                or record.remote_execution_enabled
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.side_effects_performed
                or "M116_ROLE_BASED_AUTHORITY_MODEL" not in record.reason_codes
                or "M117_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M116 role-based authority model is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M116_REVIEW_ONLY_REQUIRED"),
                ({"authority_runtime_enabled": True}, "AUTHORITY_RUNTIME_DENIED"),
                ({"role_enforcement_enabled": True}, "ROLE_ENFORCEMENT_DENIED"),
                (
                    {"permission_enforcement_enabled": True},
                    "PERMISSION_ENFORCEMENT_DENIED",
                ),
                ({"auth_runtime_enabled": True}, "AUTH_RUNTIME_DENIED"),
                ({"login_enabled": True}, "LOGIN_DENIED"),
                (
                    {"session_cookie_handling_enabled": True},
                    "SESSION_COOKIE_HANDLING_DENIED",
                ),
                ({"oauth_flow_enabled": True}, "OAUTH_FLOW_DENIED"),
                ({"token_exchange_enabled": True}, "TOKEN_EXCHANGE_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"account_action_enabled": True}, "ACCOUNT_ACTION_DENIED"),
                ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
                ({"model_call_enabled": True}, "MODEL_CALL_DENIED"),
                ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_added": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_role_based_authority_model_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M116 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M116 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M116 role-based authority validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "role-based authority model",
            "contract-only",
            "review-only",
            "safe refs",
            "production audit retention policy",
            "role refs",
            "authority scope refs",
            "permission boundary refs",
            "separation-of-duty refs",
            "break-glass boundary ref",
            "actor-bound",
            "baseline-bound",
            "source-production-audit-retention-bound",
            "user-bound",
            "workspace-bound",
            "role-bound",
            "authority-scope-bound",
            "permission-boundary-bound",
            "separation-of-duty-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no production authority",
            "no production runtime",
            "no authority runtime",
            "no role enforcement",
            "no permission enforcement",
            "no auth runtime",
            "no login",
            "no session cookie handling",
            "no oauth flow",
            "no token exchange",
            "no credential handling",
            "no account action",
            "no network access",
            "no model call",
            "no memory write",
            "no context injection",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no browser automation",
            "no plugin execution",
            "no mobile sensor",
            "no background worker",
            "no remote execution",
            "no backend route",
            "no control center control",
            "no dependency",
            "m117 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M116 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m116_role_based_authority_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "production_authority_enabled=True",
            "production_runtime_enabled=True",
            "authority_runtime_enabled=True",
            "role_enforcement_enabled=True",
            "permission_enforcement_enabled=True",
            "auth_runtime_enabled=True",
            "login_enabled=True",
            "session_cookie_handling_enabled=True",
            "oauth_flow_enabled=True",
            "token_exchange_enabled=True",
            "credential_handling_enabled=True",
            "account_action_enabled=True",
            "network_access_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "mobile_sensor_enabled=True",
            "background_worker_enabled=True",
            "remote_execution_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/authority/roles",
            "/authority/enforce",
            "/authority/permissions",
            "/rbac/enforce",
            "/roles/assign",
            "/auth/login",
            "/auth/session",
            "/auth/oauth",
            "/credentials/read",
            "/account/action",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
            "src/ultimate_ai_agent/core/production_readiness/role_based_authority.py",
            "src/ultimate_ai_agent/core/production_readiness/production_audit_retention.py",
            "src/ultimate_ai_agent/core/production_readiness/account_connector_review.py",
            "src/ultimate_ai_agent/core/production_readiness/secrets_boundary.py",
            "src/ultimate_ai_agent/core/production_readiness/user_workspace_identity.py",
            "src/ultimate_ai_agent/core/production_readiness/production_threat_model.py",
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
                            f"M116 forbidden role authority fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m116_role_based_authority_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m116_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M116 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m116_roadmap_currentness(
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
            f"missing M116 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m116" not in text or "role-based authority model" not in text:
            failures.append(
                "active docs do not identify Checkpoint M116 Role-Based Authority Model"
            )
        if (
            "m116 is implemented/released" not in text
            and "checkpoint m116 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M116 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m117",
                "pre-alpha checkpoint",
                "m117",
                "remote agent coordination contract",
                "implemented/released",
            ),
            (
                "checkpoint m118",
                "pre-alpha checkpoint",
                "m118",
                "deployment mode matrix",
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
                    f"active docs missing expected M117-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "role enforcement is implemented",
            "permission enforcement is implemented",
            "auth runtime is implemented",
            "login is implemented",
            "account action is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M116 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m117_remote_agent_coordination_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/remote_agent_coordination.py",
            "docs/production/REMOTE_AGENT_COORDINATION_CONTRACT.md",
            "docs/production/REMOTE_AGENT_COORDINATION_BOUNDARY.md",
            "docs/production/REMOTE_AGENT_COORDINATION_RECEIPT_PLAN.md",
            "docs/production/REMOTE_AGENT_COORDINATION_NON_GOALS.md",
            "docs/production/M117_TO_M118_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m117_remote_agent_coordination_contract.py",
            "tests/test_m117_gate_integration.py",
        ]
        failures = [
            f"missing M117 remote agent coordination file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                build_mobile_approval_renewal_ux_report,
                build_mobile_kill_switch_revocation_record,
                build_mobile_sensor_audit_ledger_record,
                build_mobile_sensor_hardening_freeze_record,
            )
            from ultimate_ai_agent.core.production_readiness import (
                RemoteAgentCoordinationContractStatus,
                build_account_connector_contract_review_record,
                build_production_audit_retention_policy_record,
                build_production_threat_model_record,
                build_remote_agent_coordination_contract_record,
                build_role_based_authority_model_record,
                build_secrets_boundary_record,
                build_user_workspace_identity_record,
                validate_remote_agent_coordination_contract_record,
            )

            source_record = build_role_based_authority_model_record(
                source_record=build_production_audit_retention_policy_record(
                    source_record=build_account_connector_contract_review_record(
                        source_record=build_secrets_boundary_record(
                            source_record=build_user_workspace_identity_record(
                                source_record=build_production_threat_model_record(
                                    source_record=build_mobile_sensor_hardening_freeze_record(
                                        source_record=build_mobile_sensor_audit_ledger_record(
                                            source_record=build_mobile_kill_switch_revocation_record(
                                                source_report=build_mobile_approval_renewal_ux_report()
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
            record = build_remote_agent_coordination_contract_record(
                source_record=source_record
            )
            if (
                record.status
                != RemoteAgentCoordinationContractStatus.coordination_contract
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_role_authority_model_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.remote_agent_bound
                or not record.coordination_scope_bound
                or not record.trust_boundary_bound
                or not record.handoff_protocol_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_role_authority_model_ref
                != source_record.role_authority_model_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.user_ref != source_record.user_ref
                or record.workspace_ref != source_record.workspace_ref
                or not record.remote_agent_refs
                or not record.coordination_scope_refs
                or not record.trust_boundary_refs
                or not record.handoff_protocol_refs
                or not record.communication_channel_refs
                or "checkpoint:m116" not in record.accepted_checkpoint_refs
                or record.production_authority_enabled
                or record.remote_agent_runtime_enabled
                or record.remote_dispatch_enabled
                or record.remote_execution_enabled
                or record.live_connection_enabled
                or record.network_access_enabled
                or record.agent_spawn_enabled
                or record.background_worker_enabled
                or record.credential_handling_enabled
                or record.account_action_enabled
                or record.model_call_enabled
                or record.memory_write_enabled
                or record.context_injection_enabled
                or record.execution_enabled
                or record.tool_execution_enabled
                or record.shell_execution_enabled
                or record.browser_automation_enabled
                or record.plugin_execution_enabled
                or record.mobile_sensor_enabled
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.side_effects_performed
                or "M117_REMOTE_AGENT_COORDINATION_CONTRACT" not in record.reason_codes
                or "M118_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M117 remote agent coordination contract is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M117_REVIEW_ONLY_REQUIRED"),
                (
                    {"source_role_authority_model_bound": False},
                    "M117_SOURCE_ROLE_AUTHORITY_MODEL_BINDING_REQUIRED",
                ),
                (
                    {"remote_agent_refs": []},
                    "M117_REMOTE_AGENT_REF_REQUIRED",
                ),
                (
                    {"coordination_scope_refs": []},
                    "M117_COORDINATION_SCOPE_REF_REQUIRED",
                ),
                (
                    {"trust_boundary_refs": []},
                    "M117_TRUST_BOUNDARY_REF_REQUIRED",
                ),
                (
                    {"handoff_protocol_refs": []},
                    "M117_HANDOFF_PROTOCOL_REF_REQUIRED",
                ),
                (
                    {"communication_channel_refs": []},
                    "M117_COMMUNICATION_CHANNEL_REF_REQUIRED",
                ),
                (
                    {"remote_agent_runtime_enabled": True},
                    "REMOTE_AGENT_RUNTIME_DENIED",
                ),
                ({"remote_dispatch_enabled": True}, "REMOTE_DISPATCH_DENIED"),
                ({"remote_execution_enabled": True}, "REMOTE_EXECUTION_DENIED"),
                ({"live_connection_enabled": True}, "LIVE_CONNECTION_DENIED"),
                ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
                ({"agent_spawn_enabled": True}, "AGENT_SPAWN_DENIED"),
                (
                    {"background_worker_enabled": True},
                    "BACKGROUND_WORKER_DENIED",
                ),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_added": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_remote_agent_coordination_contract_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M117 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M117 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M117 remote agent coordination validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "remote agent coordination contract",
            "contract-only",
            "review-only",
            "safe refs",
            "role-based authority model",
            "remote agent refs",
            "coordination scope refs",
            "trust boundary refs",
            "handoff protocol refs",
            "communication channel refs",
            "actor-bound",
            "baseline-bound",
            "source-role-authority-model-bound",
            "user-bound",
            "workspace-bound",
            "remote-agent-bound",
            "coordination-scope-bound",
            "trust-boundary-bound",
            "handoff-protocol-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no production authority",
            "no remote agent runtime",
            "no remote dispatch",
            "no remote execution",
            "no live connection",
            "no network access",
            "no agent spawn",
            "no background worker",
            "no credential handling",
            "no account action",
            "no model call",
            "no memory write",
            "no context injection",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no browser automation",
            "no plugin execution",
            "no mobile sensor",
            "no backend route",
            "no control center control",
            "no dependency",
            "m118 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M117 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m117_remote_agent_coordination_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "production_authority_enabled=True",
            "remote_agent_runtime_enabled=True",
            "remote_dispatch_enabled=True",
            "remote_execution_enabled=True",
            "live_connection_enabled=True",
            "network_access_enabled=True",
            "agent_spawn_enabled=True",
            "background_worker_enabled=True",
            "credential_handling_enabled=True",
            "account_action_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "mobile_sensor_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/remote-agents/coordinate",
            "/remote-agents/dispatch",
            "/remote-agents/connect",
            "/remote-agents/spawn",
            "/remote/execute",
            "/agent-mesh/dispatch",
            "/agents/remote/handoff",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
            "src/ultimate_ai_agent/core/production_readiness/remote_agent_coordination.py",
            "src/ultimate_ai_agent/core/production_readiness/role_based_authority.py",
            "src/ultimate_ai_agent/core/production_readiness/production_audit_retention.py",
            "src/ultimate_ai_agent/core/production_readiness/account_connector_review.py",
            "src/ultimate_ai_agent/core/production_readiness/secrets_boundary.py",
            "src/ultimate_ai_agent/core/production_readiness/user_workspace_identity.py",
            "src/ultimate_ai_agent/core/production_readiness/production_threat_model.py",
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
                            f"M117 forbidden remote coordination fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m117_remote_agent_coordination_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m117_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M117 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m117_roadmap_currentness(
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
            f"missing M117 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m117" not in text
            or "remote agent coordination contract" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M117 Remote Agent Coordination Contract"
            )
        if (
            "m117 is implemented/released" not in text
            and "checkpoint m117 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M117 implemented/released")
        for version_label, product_target, milestone, title in [
            (
                "checkpoint m118",
                "pre-alpha checkpoint",
                "m118",
                "deployment mode matrix",
            ),
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M118-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "checkpoint m118 implements m118",
            "deployment runtime is implemented",
            "remote agent runtime is implemented",
            "remote dispatch is implemented",
            "live connection is implemented",
            "agent spawn is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M117 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m118_deployment_mode_matrix_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/deployment_mode_matrix.py",
            "docs/production/DEPLOYMENT_MODE_MATRIX.md",
            "docs/production/DEPLOYMENT_MODE_MATRIX_BOUNDARY.md",
            "docs/production/DEPLOYMENT_MODE_MATRIX_RECEIPT_PLAN.md",
            "docs/production/DEPLOYMENT_MODE_MATRIX_NON_GOALS.md",
            "docs/production/M118_TO_M119_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m118_deployment_mode_matrix.py",
            "tests/test_m118_gate_integration.py",
        ]
        failures = [
            f"missing M118 deployment mode matrix file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                build_mobile_approval_renewal_ux_report,
                build_mobile_kill_switch_revocation_record,
                build_mobile_sensor_audit_ledger_record,
                build_mobile_sensor_hardening_freeze_record,
            )
            from ultimate_ai_agent.core.production_readiness import (
                DeploymentModeMatrixStatus,
                build_account_connector_contract_review_record,
                build_deployment_mode_matrix_record,
                build_production_audit_retention_policy_record,
                build_production_threat_model_record,
                build_remote_agent_coordination_contract_record,
                build_role_based_authority_model_record,
                build_secrets_boundary_record,
                build_user_workspace_identity_record,
                validate_deployment_mode_matrix_record,
            )

            source_record = build_remote_agent_coordination_contract_record(
                source_record=build_role_based_authority_model_record(
                    source_record=build_production_audit_retention_policy_record(
                        source_record=build_account_connector_contract_review_record(
                            source_record=build_secrets_boundary_record(
                                source_record=build_user_workspace_identity_record(
                                    source_record=build_production_threat_model_record(
                                        source_record=build_mobile_sensor_hardening_freeze_record(
                                            source_record=build_mobile_sensor_audit_ledger_record(
                                                source_record=build_mobile_kill_switch_revocation_record(
                                                    source_report=build_mobile_approval_renewal_ux_report()
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
            record = build_deployment_mode_matrix_record(source_record=source_record)
            if (
                record.status != DeploymentModeMatrixStatus.deployment_mode_matrix
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_remote_agent_coordination_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.deployment_mode_bound
                or not record.environment_bound
                or not record.authority_tier_bound
                or not record.rollout_stage_bound
                or not record.rollback_boundary_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_remote_agent_coordination_ref
                != source_record.remote_coordination_contract_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.user_ref != source_record.user_ref
                or record.workspace_ref != source_record.workspace_ref
                or not record.deployment_mode_refs
                or not record.environment_refs
                or not record.authority_tier_refs
                or not record.rollout_stage_refs
                or "checkpoint:m117" not in record.accepted_checkpoint_refs
                or record.production_authority_enabled
                or record.deployment_runtime_enabled
                or record.deployment_execution_enabled
                or record.release_automation_enabled
                or record.external_distribution_enabled
                or record.infrastructure_provisioning_enabled
                or record.ci_cd_execution_enabled
                or record.signing_or_notarization_enabled
                or record.remote_agent_runtime_enabled
                or record.remote_dispatch_enabled
                or record.network_access_enabled
                or record.credential_handling_enabled
                or record.account_action_enabled
                or record.model_call_enabled
                or record.memory_write_enabled
                or record.context_injection_enabled
                or record.execution_enabled
                or record.tool_execution_enabled
                or record.shell_execution_enabled
                or record.browser_automation_enabled
                or record.plugin_execution_enabled
                or record.mobile_sensor_enabled
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.side_effects_performed
                or "M118_DEPLOYMENT_MODE_MATRIX" not in record.reason_codes
                or "M119_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M118 deployment mode matrix contract is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M118_REVIEW_ONLY_REQUIRED"),
                (
                    {"source_remote_agent_coordination_bound": False},
                    "M118_SOURCE_REMOTE_AGENT_COORDINATION_BINDING_REQUIRED",
                ),
                ({"deployment_mode_refs": []}, "M118_DEPLOYMENT_MODE_REF_REQUIRED"),
                ({"environment_refs": []}, "M118_ENVIRONMENT_REF_REQUIRED"),
                ({"authority_tier_refs": []}, "M118_AUTHORITY_TIER_REF_REQUIRED"),
                ({"rollout_stage_refs": []}, "M118_ROLLOUT_STAGE_REF_REQUIRED"),
                ({"deployment_runtime_enabled": True}, "DEPLOYMENT_RUNTIME_DENIED"),
                (
                    {"deployment_execution_enabled": True},
                    "DEPLOYMENT_EXECUTION_DENIED",
                ),
                ({"release_automation_enabled": True}, "RELEASE_AUTOMATION_DENIED"),
                (
                    {"external_distribution_enabled": True},
                    "EXTERNAL_DISTRIBUTION_DENIED",
                ),
                (
                    {"infrastructure_provisioning_enabled": True},
                    "INFRASTRUCTURE_PROVISIONING_DENIED",
                ),
                ({"ci_cd_execution_enabled": True}, "CI_CD_EXECUTION_DENIED"),
                (
                    {"signing_or_notarization_enabled": True},
                    "SIGNING_OR_NOTARIZATION_DENIED",
                ),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_added": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_deployment_mode_matrix_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M118 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M118 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M118 deployment mode matrix validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "deployment mode matrix",
            "contract-only",
            "review-only",
            "safe refs",
            "remote agent coordination contract",
            "deployment mode refs",
            "environment refs",
            "authority tier refs",
            "rollout stage refs",
            "rollback boundary ref",
            "actor-bound",
            "baseline-bound",
            "source-remote-agent-coordination-bound",
            "user-bound",
            "workspace-bound",
            "deployment-mode-bound",
            "environment-bound",
            "authority-tier-bound",
            "rollout-stage-bound",
            "rollback-boundary-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no production authority",
            "no deployment runtime",
            "no deployment execution",
            "no release automation",
            "no external distribution",
            "no infrastructure provisioning",
            "no ci/cd execution",
            "no signing or notarization",
            "no credential handling",
            "no network access",
            "no execution",
            "no backend route",
            "no control center control",
            "no dependency",
            "m119 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M118 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m118_deployment_mode_matrix_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "production_authority_enabled=True",
            "deployment_runtime_enabled=True",
            "deployment_execution_enabled=True",
            "release_automation_enabled=True",
            "external_distribution_enabled=True",
            "infrastructure_provisioning_enabled=True",
            "ci_cd_execution_enabled=True",
            "signing_or_notarization_enabled=True",
            "credential_handling_enabled=True",
            "network_access_enabled=True",
            "execution_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/deployment/modes/apply",
            "/deployment/run",
            "/deployment/release",
            "/deployment/promote",
            "/deployment/rollback",
            "/production/deploy",
            "/ci-cd/run",
            "/infra/provision",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
            "src/ultimate_ai_agent/core/production_readiness/deployment_mode_matrix.py",
            "src/ultimate_ai_agent/core/production_readiness/remote_agent_coordination.py",
            "src/ultimate_ai_agent/core/production_readiness/role_based_authority.py",
            "src/ultimate_ai_agent/core/production_readiness/production_audit_retention.py",
            "src/ultimate_ai_agent/core/production_readiness/account_connector_review.py",
            "src/ultimate_ai_agent/core/production_readiness/secrets_boundary.py",
            "src/ultimate_ai_agent/core/production_readiness/user_workspace_identity.py",
            "src/ultimate_ai_agent/core/production_readiness/production_threat_model.py",
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
                            f"M118 forbidden deployment matrix fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m118_deployment_mode_matrix_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m118_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M118 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m118_roadmap_currentness(
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
            f"missing M118 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m118" not in text or "deployment mode matrix" not in text:
            failures.append(
                "active docs do not identify Checkpoint M118 Deployment Mode Matrix"
            )
        if (
            "m118 is implemented/released" not in text
            and "checkpoint m118 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M118 implemented/released")
        for version_label, product_target, milestone, title in [
            (
                "checkpoint m119",
                "pre-alpha checkpoint",
                "m119",
                "production red-team harness",
            ),
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]:
            planned_row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            implemented_row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | implemented/released |"
            )
            if not (
                _roadmap_row_present(text, planned_row)
                or _roadmap_row_present(text, implemented_row)
            ):
                failures.append(
                    f"active docs missing planned M119-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "deployment runtime is implemented",
            "release automation is implemented",
            "external distribution is implemented",
            "infrastructure provisioning is implemented",
            "ci/cd execution is implemented",
            "signing or notarization is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M118 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
