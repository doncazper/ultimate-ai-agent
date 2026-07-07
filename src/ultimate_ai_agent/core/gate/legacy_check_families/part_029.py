from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart029Mixin:
    """Legacy checks from m113_secrets_boundary_contracts through m115_roadmap_currentness."""
    def check_m113_secrets_boundary_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/secrets_boundary.py",
            "docs/production/SECRETS_BOUNDARY_CREDENTIAL_VAULT_CONTRACT.md",
            "docs/production/SECRETS_BOUNDARY_POLICY.md",
            "docs/production/SECRETS_BOUNDARY_AUTHORITY_BOUNDARY.md",
            "docs/production/SECRETS_BOUNDARY_RECEIPT_PLAN.md",
            "docs/production/SECRETS_BOUNDARY_NON_GOALS.md",
            "docs/production/M113_TO_M114_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m113_secrets_boundary_credential_vault.py",
            "tests/test_m113_gate_integration.py",
        ]
        failures = [
            f"missing M113 secrets boundary file: {path}"
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
                SecretsBoundaryStatus,
                build_production_threat_model_record,
                build_secrets_boundary_record,
                build_user_workspace_identity_record,
                validate_secrets_boundary_record,
            )

            source_record = build_user_workspace_identity_record(
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
            record = build_secrets_boundary_record(source_record=source_record)
            if (
                record.status != SecretsBoundaryStatus.credential_vault_contract
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_identity_model_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.credential_vault_contract_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_identity_model_ref != source_record.identity_model_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.user_ref != source_record.user_ref
                or record.workspace_ref != source_record.workspace_ref
                or not record.credential_vault_contract_ref.startswith(
                    "credential-vault-contract:"
                )
                or not record.secret_boundary_refs
                or not record.credential_scope_refs
                or "checkpoint:m112" not in record.accepted_checkpoint_refs
                or record.production_authority_enabled
                or record.production_runtime_enabled
                or record.auth_runtime_enabled
                or record.login_enabled
                or record.session_cookie_enabled
                or record.credential_handling_enabled
                or record.credential_storage_enabled
                or record.credential_read_enabled
                or record.credential_write_enabled
                or record.secret_material_access_enabled
                or record.secret_export_enabled
                or record.vault_runtime_enabled
                or record.account_connector_enabled
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
                or "M113_SECRETS_BOUNDARY_CREDENTIAL_VAULT_CONTRACT"
                not in record.reason_codes
                or "M114_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M113 secrets boundary contract is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M113_REVIEW_ONLY_REQUIRED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
                ({"production_runtime_enabled": True}, "PRODUCTION_RUNTIME_DENIED"),
                ({"auth_runtime_enabled": True}, "AUTH_RUNTIME_DENIED"),
                ({"login_enabled": True}, "LOGIN_DENIED"),
                ({"session_cookie_enabled": True}, "SESSION_COOKIE_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"credential_storage_enabled": True}, "CREDENTIAL_STORAGE_DENIED"),
                ({"credential_read_enabled": True}, "CREDENTIAL_READ_DENIED"),
                ({"credential_write_enabled": True}, "CREDENTIAL_WRITE_DENIED"),
                (
                    {"secret_material_access_enabled": True},
                    "SECRET_MATERIAL_ACCESS_DENIED",
                ),
                ({"secret_export_enabled": True}, "SECRET_EXPORT_DENIED"),
                ({"vault_runtime_enabled": True}, "VAULT_RUNTIME_DENIED"),
                ({"account_connector_enabled": True}, "ACCOUNT_CONNECTOR_DENIED"),
                ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
                ({"model_call_enabled": True}, "MODEL_CALL_DENIED"),
                ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"tool_execution_enabled": True}, "TOOL_EXECUTION_DENIED"),
                ({"shell_execution_enabled": True}, "SHELL_EXECUTION_DENIED"),
                ({"browser_automation_enabled": True}, "BROWSER_AUTOMATION_DENIED"),
                ({"plugin_execution_enabled": True}, "PLUGIN_EXECUTION_DENIED"),
                ({"mobile_sensor_enabled": True}, "MOBILE_SENSOR_DENIED"),
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                ({"remote_execution_enabled": True}, "REMOTE_EXECUTION_DENIED"),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_secrets_boundary_record(record.model_copy(update=update))
                    failures.append(
                        f"M113 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M113 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M113 secrets boundary validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "secrets boundary",
            "credential vault contract",
            "contract-only",
            "review-only",
            "safe refs",
            "user/workspace identity model",
            "user refs",
            "workspace refs",
            "secret boundary refs",
            "credential scope refs",
            "redaction policy ref",
            "actor-bound",
            "baseline-bound",
            "source-identity-model-bound",
            "user-bound",
            "workspace-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no production authority",
            "no production runtime",
            "no auth runtime",
            "no login",
            "no session cookie",
            "no credential handling",
            "no credential storage",
            "no credential read",
            "no credential write",
            "no secret material access",
            "no secret export",
            "no vault runtime",
            "no account connector",
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
            "m114 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M113 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m113_secrets_boundary_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "production_authority_enabled=True",
            "production_runtime_enabled=True",
            "auth_runtime_enabled=True",
            "login_enabled=True",
            "session_cookie_enabled=True",
            "credential_handling_enabled=True",
            "credential_storage_enabled=True",
            "credential_read_enabled=True",
            "credential_write_enabled=True",
            "secret_material_access_enabled=True",
            "secret_export_enabled=True",
            "vault_runtime_enabled=True",
            "account_connector_enabled=True",
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
            "/credentials/read",
            "/credentials/write",
            "/credentials/vault",
            "/secrets/read",
            "/secrets/write",
            "/secrets/export",
            "/vault/runtime",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
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
                            f"M113 forbidden secrets boundary fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m113_secrets_boundary_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m113_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M113 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m113_roadmap_currentness(
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
            f"missing M113 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m113" not in text
            or "secrets boundary + credential vault contract" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M113 Secrets Boundary + Credential Vault Contract"
            )
        if (
            "m113 is implemented/released" not in text
            and "checkpoint m113 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M113 implemented/released")
        m114_is_current = (
            "checkpoint m114 is implemented/released" in text
            or "m114 is implemented/released" in text
        )
        planned_rows = [
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]
        if not m114_is_current:
            planned_rows.append(
                (
                    "checkpoint m114",
                    "pre-alpha checkpoint",
                    "m114",
                    "account connector contract review",
                )
            )
        for version_label, product_target, milestone, title in planned_rows:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M114-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = {
            "credential vault runtime is implemented",
            "credential handling is implemented",
            "credential storage is implemented",
            "credential read is implemented",
            "secret material access is implemented",
            "secret export is implemented",
            "auth runtime is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        }
        if not m114_is_current:
            forbidden_fragments.update(
                {
                    "m114 is implemented",
                    "checkpoint m114 implements m114",
                    "account connector contract review is implemented",
                }
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M113 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m114_account_connector_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/account_connector_review.py",
            "docs/production/ACCOUNT_CONNECTOR_CONTRACT_REVIEW.md",
            "docs/production/ACCOUNT_CONNECTOR_POLICY.md",
            "docs/production/ACCOUNT_CONNECTOR_AUTHORITY_BOUNDARY.md",
            "docs/production/ACCOUNT_CONNECTOR_RECEIPT_PLAN.md",
            "docs/production/ACCOUNT_CONNECTOR_NON_GOALS.md",
            "docs/production/M114_TO_M115_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m114_account_connector_contract_review.py",
            "tests/test_m114_gate_integration.py",
        ]
        failures = [
            f"missing M114 account connector file: {path}"
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
                AccountConnectorContractReviewStatus,
                build_account_connector_contract_review_record,
                build_production_threat_model_record,
                build_secrets_boundary_record,
                build_user_workspace_identity_record,
                validate_account_connector_contract_review_record,
            )

            source_record = build_secrets_boundary_record(
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
            record = build_account_connector_contract_review_record(
                source_record=source_record
            )
            if (
                record.status != AccountConnectorContractReviewStatus.contract_review
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_secrets_boundary_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.credential_boundary_bound
                or not record.auth_boundary_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_secrets_boundary_ref
                != source_record.secrets_boundary_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.user_ref != source_record.user_ref
                or record.workspace_ref != source_record.workspace_ref
                or not record.connector_contract_refs
                or not record.connector_scope_refs
                or not record.credential_boundary_ref.startswith(
                    "credential-boundary-ref:"
                )
                or not record.auth_boundary_ref.startswith("auth-boundary-ref:")
                or not record.data_access_boundary_refs
                or "checkpoint:m113" not in record.accepted_checkpoint_refs
                or record.production_authority_enabled
                or record.production_runtime_enabled
                or record.auth_runtime_enabled
                or record.login_enabled
                or record.session_cookie_enabled
                or record.oauth_flow_enabled
                or record.token_exchange_enabled
                or record.credential_handling_enabled
                or record.credential_storage_enabled
                or record.credential_read_enabled
                or record.credential_write_enabled
                or record.secret_material_access_enabled
                or record.secret_export_enabled
                or record.vault_runtime_enabled
                or record.account_connector_runtime_enabled
                or record.account_connector_enabled
                or record.network_access_enabled
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
                or record.background_worker_enabled
                or record.remote_execution_enabled
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.side_effects_performed
                or "M114_ACCOUNT_CONNECTOR_CONTRACT_REVIEW" not in record.reason_codes
                or "M115_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M114 account connector review contract is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M114_REVIEW_ONLY_REQUIRED"),
                ({"oauth_flow_enabled": True}, "OAUTH_FLOW_DENIED"),
                ({"token_exchange_enabled": True}, "TOKEN_EXCHANGE_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"credential_storage_enabled": True}, "CREDENTIAL_STORAGE_DENIED"),
                ({"credential_read_enabled": True}, "CREDENTIAL_READ_DENIED"),
                ({"credential_write_enabled": True}, "CREDENTIAL_WRITE_DENIED"),
                (
                    {"secret_material_access_enabled": True},
                    "SECRET_MATERIAL_ACCESS_DENIED",
                ),
                ({"secret_export_enabled": True}, "SECRET_EXPORT_DENIED"),
                ({"vault_runtime_enabled": True}, "VAULT_RUNTIME_DENIED"),
                (
                    {"account_connector_runtime_enabled": True},
                    "ACCOUNT_CONNECTOR_RUNTIME_DENIED",
                ),
                ({"account_connector_enabled": True}, "ACCOUNT_CONNECTOR_DENIED"),
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
                    validate_account_connector_contract_review_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M114 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M114 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M114 account connector validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "account connector contract review",
            "contract-only",
            "review-only",
            "safe refs",
            "secrets boundary",
            "connector contract refs",
            "connector scope refs",
            "credential boundary ref",
            "auth boundary ref",
            "data access boundary refs",
            "actor-bound",
            "baseline-bound",
            "source-secrets-boundary-bound",
            "user-bound",
            "workspace-bound",
            "credential-boundary-bound",
            "auth-boundary-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no production authority",
            "no production runtime",
            "no auth runtime",
            "no login",
            "no session cookie",
            "no oauth flow",
            "no token exchange",
            "no credential handling",
            "no credential storage",
            "no credential read",
            "no credential write",
            "no secret material access",
            "no secret export",
            "no vault runtime",
            "no account connector runtime",
            "no account connector",
            "no network access",
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
            "no background worker",
            "no remote execution",
            "no backend route",
            "no control center control",
            "no dependency",
            "m115 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M114 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m114_account_connector_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "production_authority_enabled=True",
            "production_runtime_enabled=True",
            "auth_runtime_enabled=True",
            "login_enabled=True",
            "session_cookie_enabled=True",
            "oauth_flow_enabled=True",
            "token_exchange_enabled=True",
            "credential_handling_enabled=True",
            "credential_storage_enabled=True",
            "credential_read_enabled=True",
            "credential_write_enabled=True",
            "secret_material_access_enabled=True",
            "secret_export_enabled=True",
            "vault_runtime_enabled=True",
            "account_connector_runtime_enabled=True",
            "account_connector_enabled=True",
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
            "/accounts/connect",
            "/accounts/oauth/start",
            "/accounts/oauth/callback",
            "/connectors/accounts/read",
            "/connectors/accounts/write",
            "/credentials/read",
            "/credentials/write",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
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
                            f"M114 forbidden account connector fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m114_account_connector_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m114_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M114 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m114_roadmap_currentness(
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
            f"missing M114 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m114" not in text
            or "account connector contract review" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M114 Account Connector Contract Review"
            )
        if (
            "m114 is implemented/released" not in text
            and "checkpoint m114 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M114 implemented/released")
        m115_row_fragment = (
            "| checkpoint m115 | pre-alpha checkpoint | m115 | "
            "production audit retention policy |"
        )
        if m115_row_fragment not in text:
            failures.append("active docs missing Checkpoint M115 row")
        m150_row = (
            "| v1.2.0-alpha | alpha | m150 | ultimate ai agent v1.2.0-alpha | "
            "planned/provisional |"
        )
        if not _roadmap_row_present(text, m150_row):
            failures.append("active docs missing M150 alpha row")
        for fragment in (
            "account connector runtime is implemented",
            "account connector is implemented",
            "account action is implemented",
            "credential handling is implemented",
            "auth runtime is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M114 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m115_production_audit_retention_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/production_audit_retention.py",
            "docs/production/PRODUCTION_AUDIT_RETENTION_POLICY.md",
            "docs/production/PRODUCTION_AUDIT_RETENTION_AUTHORITY_BOUNDARY.md",
            "docs/production/PRODUCTION_AUDIT_RETENTION_RECEIPT_PLAN.md",
            "docs/production/PRODUCTION_AUDIT_RETENTION_NON_GOALS.md",
            "docs/production/M115_TO_M116_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m115_production_audit_retention_policy.py",
            "tests/test_m115_gate_integration.py",
        ]
        failures = [
            f"missing M115 production audit retention file: {path}"
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
                ProductionAuditRetentionPolicyStatus,
                build_account_connector_contract_review_record,
                build_production_audit_retention_policy_record,
                build_production_threat_model_record,
                build_secrets_boundary_record,
                build_user_workspace_identity_record,
                validate_production_audit_retention_policy_record,
            )

            source_record = build_account_connector_contract_review_record(
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
            record = build_production_audit_retention_policy_record(
                source_record=source_record
            )
            if (
                record.status != ProductionAuditRetentionPolicyStatus.retention_policy
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_account_connector_review_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.retention_schedule_bound
                or not record.redaction_boundary_bound
                or not record.deletion_window_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_account_connector_review_ref
                != source_record.account_connector_review_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.user_ref != source_record.user_ref
                or record.workspace_ref != source_record.workspace_ref
                or not record.retention_policy_refs
                or not record.retention_schedule_refs
                or not record.audit_data_class_refs
                or not record.redaction_policy_ref.startswith("redaction-policy-ref:")
                or not record.deletion_window_ref.startswith("deletion-window-ref:")
                or not record.legal_hold_boundary_ref.startswith(
                    "legal-hold-boundary-ref:"
                )
                or "checkpoint:m114" not in record.accepted_checkpoint_refs
                or record.production_authority_enabled
                or record.production_runtime_enabled
                or record.audit_runtime_enabled
                or record.audit_store_enabled
                or record.audit_export_enabled
                or record.raw_log_storage_enabled
                or record.raw_prompt_storage_enabled
                or record.raw_provider_payload_storage_enabled
                or record.secret_storage_enabled
                or record.external_saas_export_enabled
                or record.network_delivery_enabled
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
                or "M115_PRODUCTION_AUDIT_RETENTION_POLICY" not in record.reason_codes
                or "M116_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M115 production audit retention policy is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M115_REVIEW_ONLY_REQUIRED"),
                ({"audit_runtime_enabled": True}, "AUDIT_RUNTIME_DENIED"),
                ({"audit_store_enabled": True}, "AUDIT_STORE_DENIED"),
                ({"audit_export_enabled": True}, "AUDIT_EXPORT_DENIED"),
                ({"raw_log_storage_enabled": True}, "RAW_LOG_STORAGE_DENIED"),
                ({"raw_prompt_storage_enabled": True}, "RAW_PROMPT_STORAGE_DENIED"),
                (
                    {"raw_provider_payload_storage_enabled": True},
                    "RAW_PROVIDER_PAYLOAD_STORAGE_DENIED",
                ),
                ({"external_saas_export_enabled": True}, "EXTERNAL_SAAS_EXPORT_DENIED"),
                ({"network_delivery_enabled": True}, "NETWORK_DELIVERY_DENIED"),
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
                    validate_production_audit_retention_policy_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M115 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M115 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M115 production audit retention validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "production audit retention policy",
            "contract-only",
            "review-only",
            "safe refs",
            "account connector contract review",
            "retention policy refs",
            "retention schedule refs",
            "audit data class refs",
            "redaction policy ref",
            "deletion window ref",
            "legal hold boundary ref",
            "actor-bound",
            "baseline-bound",
            "source-account-connector-review-bound",
            "user-bound",
            "workspace-bound",
            "retention-schedule-bound",
            "redaction-boundary-bound",
            "deletion-window-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no production authority",
            "no production runtime",
            "no audit runtime",
            "no audit store",
            "no audit export",
            "no raw log storage",
            "no raw prompt storage",
            "no raw provider payload storage",
            "no secret storage",
            "no external saas export",
            "no network delivery",
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
            "m116 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M115 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m115_production_audit_retention_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "production_authority_enabled=True",
            "production_runtime_enabled=True",
            "audit_runtime_enabled=True",
            "audit_store_enabled=True",
            "audit_export_enabled=True",
            "raw_log_storage_enabled=True",
            "raw_prompt_storage_enabled=True",
            "raw_provider_payload_storage_enabled=True",
            "secret_storage_enabled=True",
            "external_saas_export_enabled=True",
            "network_delivery_enabled=True",
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
            "/audit/retention",
            "/audit/export",
            "/audit/logs/raw",
            "/logs/export",
            "/observability/export",
            "/siem/export",
            "/network/post",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
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
                            f"M115 forbidden audit retention fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m115_production_audit_retention_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m115_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M115 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m115_roadmap_currentness(
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
            f"missing M115 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m115" not in text
            or "production audit retention policy" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M115 Production Audit Retention Policy"
            )
        if (
            "m115 is implemented/released" not in text
            and "checkpoint m115 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M115 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m116",
                "pre-alpha checkpoint",
                "m116",
                "role-based authority model",
                "implemented/released",
            ),
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
                    f"active docs missing expected M116-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "audit runtime is implemented",
            "audit export is implemented",
            "raw log storage is implemented",
            "role enforcement is implemented",
            "permission enforcement is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M115 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
