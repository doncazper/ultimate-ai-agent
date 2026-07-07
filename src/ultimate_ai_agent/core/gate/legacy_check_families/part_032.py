from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart032Mixin:
    """Legacy checks from m122_calendar_connector_contract_refresh_contracts through m124_roadmap_currentness."""
    def check_m122_calendar_connector_contract_refresh_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/calendar_connector_contract_refresh.py",
            "docs/connectors/CALENDAR_CONNECTOR_CONTRACT_REFRESH.md",
            "docs/connectors/CALENDAR_CONNECTOR_AUTHORITY_BOUNDARY.md",
            "docs/connectors/CALENDAR_CONNECTOR_RECEIPT_PLAN.md",
            "docs/connectors/CALENDAR_CONNECTOR_NON_GOALS.md",
            "docs/connectors/M122_TO_M123_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m122_calendar_connector_contract_refresh.py",
            "tests/test_m122_gate_integration.py",
        ]
        failures = [
            f"missing M122 calendar connector refresh file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.connectors import (
                CalendarConnectorContractRefreshStatus,
                build_calendar_connector_contract_refresh_record,
                build_email_connector_contract_refresh_record,
                validate_calendar_connector_contract_refresh_record,
            )
            from ultimate_ai_agent.core.mobile_companion import (
                build_mobile_approval_renewal_ux_report,
                build_mobile_kill_switch_revocation_record,
                build_mobile_sensor_audit_ledger_record,
                build_mobile_sensor_hardening_freeze_record,
            )
            from ultimate_ai_agent.core.production_readiness import (
                build_account_connector_contract_review_record,
                build_deployment_mode_matrix_record,
                build_production_audit_retention_policy_record,
                build_production_authority_readiness_review_record,
                build_production_red_team_harness_record,
                build_production_threat_model_record,
                build_remote_agent_coordination_contract_record,
                build_role_based_authority_model_record,
                build_secrets_boundary_record,
                build_user_workspace_identity_record,
            )

            m120_record = build_production_authority_readiness_review_record(
                source_record=build_production_red_team_harness_record(
                    source_record=build_deployment_mode_matrix_record(
                        source_record=build_remote_agent_coordination_contract_record(
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
                    )
                )
            )
            source_record = build_email_connector_contract_refresh_record(
                source_record=m120_record
            )
            record = build_calendar_connector_contract_refresh_record(
                source_record=source_record
            )
            if (
                record.status
                != CalendarConnectorContractRefreshStatus.calendar_connector_contract_refresh
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_email_connector_contract_refresh_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.calendar_scope_bound
                or not record.calendar_boundary_bound
                or not record.event_boundary_bound
                or not record.consent_boundary_bound
                or not record.data_classification_bound
                or not record.retention_boundary_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_email_connector_contract_refresh_ref
                != source_record.email_connector_contract_refresh_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.user_ref != source_record.user_ref
                or record.workspace_ref != source_record.workspace_ref
                or "checkpoint:m121" not in record.accepted_checkpoint_refs
                or not record.calendar_scope_refs
                or not record.calendar_boundary_refs
                or not record.event_boundary_refs
                or not record.consent_boundary_refs
                or not record.data_classification_refs
                or not record.retention_boundary_refs
                or record.calendar_connector_runtime_enabled
                or record.calendar_account_auth_enabled
                or record.calendar_read_enabled
                or record.calendar_search_enabled
                or record.calendar_event_create_enabled
                or record.calendar_event_update_enabled
                or record.calendar_event_delete_enabled
                or record.calendar_invite_send_enabled
                or record.calendar_attachment_download_enabled
                or record.raw_calendar_content_enabled
                or record.credential_handling_enabled
                or record.network_access_enabled
                or record.account_action_enabled
                or record.model_call_enabled
                or record.memory_write_enabled
                or record.context_injection_enabled
                or record.execution_enabled
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.side_effects_performed
                or "M122_CALENDAR_CONNECTOR_CONTRACT_REFRESH" not in record.reason_codes
                or "M123_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M122 calendar connector refresh contract is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M122_REVIEW_ONLY_REQUIRED"),
                ({"calendar_scope_refs": []}, "M122_CALENDAR_SCOPE_REF_REQUIRED"),
                ({"calendar_boundary_refs": []}, "M122_CALENDAR_BOUNDARY_REF_REQUIRED"),
                ({"event_boundary_refs": []}, "M122_EVENT_BOUNDARY_REF_REQUIRED"),
                (
                    {"calendar_connector_runtime_enabled": True},
                    "CALENDAR_CONNECTOR_RUNTIME_DENIED",
                ),
                (
                    {"calendar_account_auth_enabled": True},
                    "CALENDAR_ACCOUNT_AUTH_DENIED",
                ),
                ({"calendar_read_enabled": True}, "CALENDAR_READ_DENIED"),
                (
                    {"calendar_event_create_enabled": True},
                    "CALENDAR_EVENT_CREATE_DENIED",
                ),
                ({"raw_calendar_content_enabled": True}, "RAW_CALENDAR_CONTENT_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_added": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_calendar_connector_contract_refresh_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M122 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M122 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M122 calendar connector refresh validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "calendar connector contract refresh",
            "contract-only",
            "review-only",
            "safe refs",
            "email connector contract refresh",
            "calendar scope refs",
            "calendar boundary refs",
            "event boundary refs",
            "consent boundary refs",
            "data classification refs",
            "retention boundary refs",
            "actor-bound",
            "baseline-bound",
            "source-email-connector-contract-refresh-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no calendar connector runtime",
            "no calendar account auth",
            "no calendar read",
            "no calendar search",
            "no calendar event create",
            "no calendar event update",
            "no calendar event delete",
            "no calendar invite send",
            "no raw calendar content",
            "no credential handling",
            "no network access",
            "no backend route",
            "no control center control",
            "no dependency",
            "m123 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M122 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m122_calendar_connector_contract_refresh_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "calendar_connector_runtime_enabled=True",
            "calendar_account_auth_enabled=True",
            "calendar_read_enabled=True",
            "calendar_search_enabled=True",
            "calendar_event_create_enabled=True",
            "calendar_event_update_enabled=True",
            "calendar_event_delete_enabled=True",
            "calendar_invite_send_enabled=True",
            "calendar_attachment_download_enabled=True",
            "raw_calendar_content_enabled=True",
            "credential_handling_enabled=True",
            "network_access_enabled=True",
            "account_action_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/connectors/calendar/auth",
            "/connectors/calendar/read",
            "/connectors/calendar/search",
            "/connectors/calendar/events/create",
            "/connectors/calendar/events/update",
            "/connectors/calendar/events/delete",
            "/connectors/calendar/invites/send",
            "/connectors/calendar/attachments/download",
            "/calendar/events/create",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/calendar_connector_contract_refresh.py",
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
                            f"M122 forbidden calendar connector fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m122_calendar_connector_contract_refresh_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m122_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M122 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m122_roadmap_currentness(
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
            f"missing M122 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m122" not in text
            or "calendar connector contract refresh" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M122 Calendar Connector Contract Refresh"
            )
        if (
            "m122 is implemented/released" not in text
            and "checkpoint m122 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M122 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m122",
                "pre-alpha checkpoint",
                "m122",
                "calendar connector contract refresh",
                "implemented/released",
            ),
            (
                "checkpoint m123",
                "pre-alpha checkpoint",
                "m123",
                "contacts connector contract refresh",
                "implemented/released",
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
                    f"active docs missing expected M122-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = {
            "m124 is implemented",
            "checkpoint m124 implements m124",
            "messages connector contract review is implemented",
            "calendar connector runtime is implemented",
            "calendar account auth is implemented",
            "calendar read is implemented",
            "calendar event create is implemented",
            "network access is implemented",
            "beta is released",
            "broad autonomy is implemented",
        }
        if (
            "checkpoint m124 is implemented/released" in text
            or "m124 is implemented/released" in text
        ):
            forbidden_fragments -= {
                "m124 is implemented",
                "messages connector contract review is implemented",
            }
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M122 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m123_contacts_connector_contract_refresh_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/contacts_connector_contract_refresh.py",
            "docs/connectors/CONTACTS_CONNECTOR_CONTRACT_REFRESH.md",
            "docs/connectors/CONTACTS_CONNECTOR_AUTHORITY_BOUNDARY.md",
            "docs/connectors/CONTACTS_CONNECTOR_RECEIPT_PLAN.md",
            "docs/connectors/CONTACTS_CONNECTOR_NON_GOALS.md",
            "docs/connectors/M123_TO_M124_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m123_contacts_connector_contract_refresh.py",
            "tests/test_m123_gate_integration.py",
        ]
        failures = [
            f"missing M123 contacts connector refresh file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.connectors import (
                ContactsConnectorContractRefreshStatus,
                build_calendar_connector_contract_refresh_record,
                build_contacts_connector_contract_refresh_record,
                build_email_connector_contract_refresh_record,
                validate_contacts_connector_contract_refresh_record,
            )
            from ultimate_ai_agent.core.mobile_companion import (
                build_mobile_approval_renewal_ux_report,
                build_mobile_kill_switch_revocation_record,
                build_mobile_sensor_audit_ledger_record,
                build_mobile_sensor_hardening_freeze_record,
            )
            from ultimate_ai_agent.core.production_readiness import (
                build_account_connector_contract_review_record,
                build_deployment_mode_matrix_record,
                build_production_audit_retention_policy_record,
                build_production_authority_readiness_review_record,
                build_production_red_team_harness_record,
                build_production_threat_model_record,
                build_remote_agent_coordination_contract_record,
                build_role_based_authority_model_record,
                build_secrets_boundary_record,
                build_user_workspace_identity_record,
            )

            m120_record = build_production_authority_readiness_review_record(
                source_record=build_production_red_team_harness_record(
                    source_record=build_deployment_mode_matrix_record(
                        source_record=build_remote_agent_coordination_contract_record(
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
                    )
                )
            )
            email_record = build_email_connector_contract_refresh_record(
                source_record=m120_record
            )
            source_record = build_calendar_connector_contract_refresh_record(
                source_record=email_record
            )
            record = build_contacts_connector_contract_refresh_record(
                source_record=source_record
            )
            if (
                record.status
                != ContactsConnectorContractRefreshStatus.contacts_connector_contract_refresh
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_calendar_connector_contract_refresh_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.contacts_scope_bound
                or not record.contacts_boundary_bound
                or not record.contact_boundary_bound
                or not record.consent_boundary_bound
                or not record.data_classification_bound
                or not record.retention_boundary_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_calendar_connector_contract_refresh_ref
                != source_record.calendar_connector_contract_refresh_ref
                or "checkpoint:m122" not in record.accepted_checkpoint_refs
                or not record.contacts_scope_refs
                or not record.contacts_boundary_refs
                or not record.contact_boundary_refs
                or not record.consent_boundary_refs
                or not record.data_classification_refs
                or not record.retention_boundary_refs
                or record.contacts_connector_runtime_enabled
                or record.contacts_account_auth_enabled
                or record.contacts_read_enabled
                or record.contacts_search_enabled
                or record.contacts_lookup_enabled
                or record.contacts_create_enabled
                or record.contacts_update_enabled
                or record.contacts_delete_enabled
                or record.contacts_export_enabled
                or record.contacts_bulk_export_enabled
                or record.raw_contacts_content_enabled
                or record.credential_handling_enabled
                or record.network_access_enabled
                or record.account_action_enabled
                or record.model_call_enabled
                or record.memory_write_enabled
                or record.context_injection_enabled
                or record.execution_enabled
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.side_effects_performed
                or "M123_CONTACTS_CONNECTOR_CONTRACT_REFRESH" not in record.reason_codes
                or "M124_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M123 contacts connector refresh contract is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M123_REVIEW_ONLY_REQUIRED"),
                ({"contacts_scope_refs": []}, "M123_CONTACTS_SCOPE_REF_REQUIRED"),
                ({"contacts_boundary_refs": []}, "M123_CONTACTS_BOUNDARY_REF_REQUIRED"),
                ({"contact_boundary_refs": []}, "M123_CONTACT_BOUNDARY_REF_REQUIRED"),
                (
                    {"contacts_connector_runtime_enabled": True},
                    "CONTACTS_CONNECTOR_RUNTIME_DENIED",
                ),
                (
                    {"contacts_account_auth_enabled": True},
                    "CONTACTS_ACCOUNT_AUTH_DENIED",
                ),
                ({"contacts_read_enabled": True}, "CONTACTS_READ_DENIED"),
                ({"contacts_lookup_enabled": True}, "CONTACTS_LOOKUP_DENIED"),
                ({"contacts_create_enabled": True}, "CONTACTS_CREATE_DENIED"),
                ({"contacts_export_enabled": True}, "CONTACTS_EXPORT_DENIED"),
                ({"raw_contacts_content_enabled": True}, "RAW_CONTACTS_CONTENT_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_added": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_contacts_connector_contract_refresh_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M123 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M123 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M123 contacts connector refresh validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "contacts connector contract refresh",
            "contract-only",
            "review-only",
            "safe refs",
            "calendar connector contract refresh",
            "contacts scope refs",
            "contacts boundary refs",
            "contact boundary refs",
            "consent boundary refs",
            "data classification refs",
            "retention boundary refs",
            "actor-bound",
            "baseline-bound",
            "source-calendar-connector-contract-refresh-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no contacts connector runtime",
            "no contacts account auth",
            "no contacts read",
            "no contacts search",
            "no contacts lookup",
            "no contacts create",
            "no contacts update",
            "no contacts delete",
            "no contacts export",
            "no raw contacts content",
            "no credential handling",
            "no network access",
            "no backend route",
            "no control center control",
            "no dependency",
            "m124 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M123 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m123_contacts_connector_contract_refresh_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "contacts_connector_runtime_enabled=True",
            "contacts_account_auth_enabled=True",
            "contacts_read_enabled=True",
            "contacts_search_enabled=True",
            "contacts_lookup_enabled=True",
            "contacts_create_enabled=True",
            "contacts_update_enabled=True",
            "contacts_delete_enabled=True",
            "contacts_export_enabled=True",
            "contacts_bulk_export_enabled=True",
            "raw_contacts_content_enabled=True",
            "credential_handling_enabled=True",
            "network_access_enabled=True",
            "account_action_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/connectors/contacts/auth",
            "/connectors/contacts/read",
            "/connectors/contacts/search",
            "/connectors/contacts/lookup",
            "/connectors/contacts/create",
            "/connectors/contacts/update",
            "/connectors/contacts/delete",
            "/connectors/contacts/export",
            "/connectors/contacts/bulk-export",
            "/contacts/export",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/contacts_connector_contract_refresh.py",
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
                            f"M123 forbidden contacts connector fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m123_contacts_connector_contract_refresh_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m123_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M123 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m123_roadmap_currentness(
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
            f"missing M123 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m123" not in text
            or "contacts connector contract refresh" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M123 Contacts Connector Contract Refresh"
            )
        if (
            "m123 is implemented/released" not in text
            and "checkpoint m123 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M123 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m123",
                "pre-alpha checkpoint",
                "m123",
                "contacts connector contract refresh",
                "implemented/released",
            ),
            (
                "checkpoint m124",
                "pre-alpha checkpoint",
                "m124",
                "messages connector contract review",
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
                    f"active docs missing expected M123-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = {
            "m124 is implemented",
            "checkpoint m124 implements m124",
            "messages connector contract review is implemented",
            "contacts connector runtime is implemented",
            "contacts account auth is implemented",
            "contacts read is implemented",
            "contacts export is implemented",
            "network access is implemented",
            "beta is released",
            "broad autonomy is implemented",
        }
        if (
            "checkpoint m124 is implemented/released" in text
            or "m124 is implemented/released" in text
        ):
            forbidden_fragments -= {
                "m124 is implemented",
                "messages connector contract review is implemented",
            }
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M123 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m124_messages_connector_contract_review_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/messages_connector_contract_review.py",
            "docs/connectors/MESSAGES_CONNECTOR_CONTRACT_REVIEW.md",
            "docs/connectors/MESSAGES_CONNECTOR_AUTHORITY_BOUNDARY.md",
            "docs/connectors/MESSAGES_CONNECTOR_RECEIPT_PLAN.md",
            "docs/connectors/MESSAGES_CONNECTOR_NON_GOALS.md",
            "docs/connectors/M124_TO_M125_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m124_messages_connector_contract_review.py",
            "tests/test_m124_gate_integration.py",
        ]
        failures = [
            f"missing M124 messages connector review file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.connectors import (
                MessagesConnectorContractReviewStatus,
                build_calendar_connector_contract_refresh_record,
                build_contacts_connector_contract_refresh_record,
                build_email_connector_contract_refresh_record,
                build_messages_connector_contract_review_record,
                validate_messages_connector_contract_review_record,
            )
            from ultimate_ai_agent.core.mobile_companion import (
                build_mobile_approval_renewal_ux_report,
                build_mobile_kill_switch_revocation_record,
                build_mobile_sensor_audit_ledger_record,
                build_mobile_sensor_hardening_freeze_record,
            )
            from ultimate_ai_agent.core.production_readiness import (
                build_account_connector_contract_review_record,
                build_deployment_mode_matrix_record,
                build_production_audit_retention_policy_record,
                build_production_authority_readiness_review_record,
                build_production_red_team_harness_record,
                build_production_threat_model_record,
                build_remote_agent_coordination_contract_record,
                build_role_based_authority_model_record,
                build_secrets_boundary_record,
                build_user_workspace_identity_record,
            )

            m120_record = build_production_authority_readiness_review_record(
                source_record=build_production_red_team_harness_record(
                    source_record=build_deployment_mode_matrix_record(
                        source_record=build_remote_agent_coordination_contract_record(
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
                    )
                )
            )
            email_record = build_email_connector_contract_refresh_record(
                source_record=m120_record
            )
            calendar_record = build_calendar_connector_contract_refresh_record(
                source_record=email_record
            )
            source_record = build_contacts_connector_contract_refresh_record(
                source_record=calendar_record
            )
            record = build_messages_connector_contract_review_record(
                source_record=source_record
            )
            if (
                record.status
                != MessagesConnectorContractReviewStatus.messages_connector_contract_review
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_contacts_connector_contract_refresh_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.messages_scope_bound
                or not record.messages_boundary_bound
                or not record.message_thread_boundary_bound
                or not record.consent_boundary_bound
                or not record.data_classification_bound
                or not record.retention_boundary_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_contacts_connector_contract_refresh_ref
                != source_record.contacts_connector_contract_refresh_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.user_ref != source_record.user_ref
                or record.workspace_ref != source_record.workspace_ref
                or "checkpoint:m123" not in record.accepted_checkpoint_refs
                or not record.messages_scope_refs
                or not record.messages_boundary_refs
                or not record.message_thread_boundary_refs
                or not record.consent_boundary_refs
                or not record.data_classification_refs
                or not record.retention_boundary_refs
                or record.messages_connector_runtime_enabled
                or record.messages_account_auth_enabled
                or record.messages_read_enabled
                or record.messages_search_enabled
                or record.messages_lookup_enabled
                or record.messages_send_enabled
                or record.message_thread_access_enabled
                or record.messages_create_enabled
                or record.messages_update_enabled
                or record.messages_delete_enabled
                or record.messages_export_enabled
                or record.messages_bulk_export_enabled
                or record.attachment_download_enabled
                or record.raw_messages_content_enabled
                or record.credential_handling_enabled
                or record.network_access_enabled
                or record.account_action_enabled
                or record.model_call_enabled
                or record.memory_write_enabled
                or record.context_injection_enabled
                or record.execution_enabled
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.side_effects_performed
                or "M124_MESSAGES_CONNECTOR_CONTRACT_REVIEW" not in record.reason_codes
                or "M125_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M124 messages connector review contract is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M124_REVIEW_ONLY_REQUIRED"),
                ({"messages_scope_refs": []}, "M124_MESSAGES_SCOPE_REF_REQUIRED"),
                ({"messages_boundary_refs": []}, "M124_MESSAGES_BOUNDARY_REF_REQUIRED"),
                (
                    {"message_thread_boundary_refs": []},
                    "M124_MESSAGE_THREAD_BOUNDARY_REF_REQUIRED",
                ),
                (
                    {"messages_connector_runtime_enabled": True},
                    "MESSAGES_CONNECTOR_RUNTIME_DENIED",
                ),
                (
                    {"messages_account_auth_enabled": True},
                    "MESSAGES_ACCOUNT_AUTH_DENIED",
                ),
                ({"messages_read_enabled": True}, "MESSAGES_READ_DENIED"),
                ({"messages_lookup_enabled": True}, "MESSAGES_LOOKUP_DENIED"),
                ({"messages_send_enabled": True}, "MESSAGES_SEND_DENIED"),
                (
                    {"message_thread_access_enabled": True},
                    "MESSAGE_THREAD_ACCESS_DENIED",
                ),
                ({"messages_create_enabled": True}, "MESSAGES_CREATE_DENIED"),
                ({"messages_export_enabled": True}, "MESSAGES_EXPORT_DENIED"),
                (
                    {"attachment_download_enabled": True},
                    "ATTACHMENT_DOWNLOAD_DENIED",
                ),
                ({"raw_messages_content_enabled": True}, "RAW_MESSAGES_CONTENT_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_added": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_messages_connector_contract_review_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M124 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M124 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M124 messages connector review validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "messages connector contract review",
            "contract-only",
            "review-only",
            "safe refs",
            "contacts connector contract refresh",
            "messages scope refs",
            "messages boundary refs",
            "message thread boundary refs",
            "consent boundary refs",
            "data classification refs",
            "retention boundary refs",
            "actor-bound",
            "baseline-bound",
            "source-contacts-connector-contract-refresh-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no messages connector runtime",
            "no messages account auth",
            "no messages read",
            "no messages search",
            "no messages lookup",
            "no messages send",
            "no message thread access",
            "no messages create",
            "no messages update",
            "no messages delete",
            "no messages export",
            "no attachment download",
            "no raw messages content",
            "no credential handling",
            "no network access",
            "no backend route",
            "no control center control",
            "no dependency",
            "m125 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M124 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m124_messages_connector_contract_review_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "messages_connector_runtime_enabled=True",
            "messages_account_auth_enabled=True",
            "messages_read_enabled=True",
            "messages_search_enabled=True",
            "messages_lookup_enabled=True",
            "messages_send_enabled=True",
            "message_thread_access_enabled=True",
            "messages_create_enabled=True",
            "messages_update_enabled=True",
            "messages_delete_enabled=True",
            "messages_export_enabled=True",
            "messages_bulk_export_enabled=True",
            "attachment_download_enabled=True",
            "raw_messages_content_enabled=True",
            "credential_handling_enabled=True",
            "network_access_enabled=True",
            "account_action_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/connectors/messages/auth",
            "/connectors/messages/read",
            "/connectors/messages/search",
            "/connectors/messages/lookup",
            "/connectors/messages/send",
            "/connectors/messages/thread",
            "/connectors/messages/attachments/download",
            "/connectors/messages/create",
            "/connectors/messages/update",
            "/connectors/messages/delete",
            "/connectors/messages/export",
            "/connectors/messages/bulk-export",
            "/messages/export",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/messages_connector_contract_review.py",
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
                            f"M124 forbidden messages connector fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m124_messages_connector_contract_review_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m124_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M124 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m124_roadmap_currentness(
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
            f"missing M124 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m124" not in text
            or "messages connector contract review" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M124 Messages Connector Contract Review"
            )
        if (
            "m124 is implemented/released" not in text
            and "checkpoint m124 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M124 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m124",
                "pre-alpha checkpoint",
                "m124",
                "messages connector contract review",
                "implemented/released",
            ),
            (
                "checkpoint m125",
                "pre-alpha checkpoint",
                "m125",
                "connector read-only runtime",
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
            if version_label == "checkpoint m125":
                implemented_row = (
                    "| checkpoint m125 | pre-alpha checkpoint | m125 | "
                    "connector read-only runtime | implemented/released |"
                )
                if not (
                    _roadmap_row_present(text, row)
                    or _roadmap_row_present(text, implemented_row)
                ):
                    failures.append(
                        f"active docs missing expected M124-M150 row: {version_label} / {milestone.upper()} - {title}"
                    )
                continue
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing expected M124-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "messages connector runtime is implemented",
            "messages account auth is implemented",
            "messages read is implemented",
            "messages send is implemented",
            "messages export is implemented",
            "message thread access is implemented",
            "network access is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M124 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
