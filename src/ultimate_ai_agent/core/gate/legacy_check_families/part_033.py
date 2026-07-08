from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart033Mixin:
    """Legacy checks from m125_connector_read_only_runtime_contracts through m127_connector_write_dry_run_planner_route_boundary."""
    def check_m125_connector_read_only_runtime_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/connectors/connector_read_only_runtime.py",
            "src/ultimate_ai_agent/core/connectors/messages_connector_contract_review.py",
            "tests/test_m125_connector_read_only_runtime.py",
            "docs/connectors/CONNECTOR_READ_ONLY_RUNTIME.md",
            "docs/connectors/CONNECTOR_READ_ONLY_RUNTIME_AUTHORITY_BOUNDARY.md",
            "docs/connectors/CONNECTOR_READ_ONLY_RUNTIME_RECEIPT_PLAN.md",
            "docs/connectors/CONNECTOR_READ_ONLY_RUNTIME_NON_GOALS.md",
            "docs/connectors/M125_TO_M126_BOUNDARY.md",
            "docs/release_notes/checkpoint_m125.md",
            "docs/archive/checkpoints/m125/README_IMPORT.md",
            "docs/archive/checkpoints/m125/master_plan.md",
        ]
        failures = [
            f"missing M125 connector read-only runtime file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.connectors import (
                build_calendar_connector_contract_refresh_record,
                build_connector_read_only_runtime_record,
                build_contacts_connector_contract_refresh_record,
                build_email_connector_contract_refresh_record,
                build_messages_connector_contract_review_record,
                validate_connector_read_only_runtime_record,
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

            source_record = build_messages_connector_contract_review_record(
                source_record=build_contacts_connector_contract_refresh_record(
                    source_record=build_calendar_connector_contract_refresh_record(
                        source_record=build_email_connector_contract_refresh_record(
                            source_record=build_production_authority_readiness_review_record(
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
                        )
                    )
                )
            )
            record = build_connector_read_only_runtime_record(
                source_record=source_record
            )
            if (
                not record.read_only_runtime
                or not record.safe_refs_required
                or not record.source_messages_connector_contract_review_bound
                or record.source_messages_connector_contract_review_ref
                != source_record.messages_connector_contract_review_ref
                or "checkpoint:m124" not in record.accepted_checkpoint_refs
                or record.live_connector_runtime_enabled
                or record.account_auth_enabled
                or record.network_access_enabled
                or record.credential_handling_enabled
                or record.raw_connector_content_enabled
                or record.full_content_read_enabled
                or record.connector_write_enabled
                or record.connector_send_enabled
                or record.connector_delete_enabled
                or record.connector_export_enabled
                or record.connector_bulk_export_enabled
                or record.attachment_download_enabled
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or "M126_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M125 connector read-only runtime contract is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"read_only_runtime": False}, "M125_READ_ONLY_RUNTIME_REQUIRED"),
                (
                    {
                        "source_messages_connector_contract_review_ref": "messages-connector-contract-review:mismatch"
                    },
                    "M125_SOURCE_MESSAGES_CONNECTOR_CONTRACT_REVIEW_REF_MISMATCH",
                ),
                ({"connector_scope_refs": []}, "M125_CONNECTOR_SCOPE_REF_REQUIRED"),
                (
                    {"connector_allowlist_refs": []},
                    "M125_CONNECTOR_ALLOWLIST_REF_REQUIRED",
                ),
                (
                    {"operation_allowlist_refs": []},
                    "M125_OPERATION_ALLOWLIST_REF_REQUIRED",
                ),
                (
                    {"data_minimization_refs": []},
                    "M125_DATA_MINIMIZATION_REF_REQUIRED",
                ),
                ({"redaction_refs": []}, "M125_REDACTION_REF_REQUIRED"),
                (
                    {"live_connector_runtime_enabled": True},
                    "LIVE_CONNECTOR_RUNTIME_DENIED",
                ),
                ({"account_auth_enabled": True}, "ACCOUNT_AUTH_DENIED"),
                ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                (
                    {"raw_connector_content_enabled": True},
                    "RAW_CONNECTOR_CONTENT_DENIED",
                ),
                ({"full_content_read_enabled": True}, "FULL_CONTENT_READ_DENIED"),
                ({"connector_write_enabled": True}, "CONNECTOR_WRITE_DENIED"),
                ({"connector_send_enabled": True}, "CONNECTOR_SEND_DENIED"),
                ({"connector_delete_enabled": True}, "CONNECTOR_DELETE_DENIED"),
                ({"connector_export_enabled": True}, "CONNECTOR_EXPORT_DENIED"),
                (
                    {"connector_bulk_export_enabled": True},
                    "CONNECTOR_BULK_EXPORT_DENIED",
                ),
                ({"attachment_download_enabled": True}, "ATTACHMENT_DOWNLOAD_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_added": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_connector_read_only_runtime_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M125 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M125 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(
                f"M125 connector read-only runtime validation failed: {exc}"
            )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "connector read-only runtime",
            "safe metadata preview refs",
            "safe refs",
            "messages connector contract review",
            "source-messages-connector-contract-review-bound",
            "connector scope refs",
            "connector allowlist refs",
            "operation allowlist refs",
            "data minimization refs",
            "redaction refs",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no live connector runtime",
            "no account auth",
            "no network access",
            "no credential handling",
            "no raw connector content",
            "no full content read",
            "no connector write",
            "no connector send",
            "no connector delete",
            "no connector export",
            "no attachment download",
            "no backend route",
            "no control center control",
            "no dependency",
            "m126 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M125 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m125_connector_read_only_runtime_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "live_connector_runtime_enabled=True",
            "account_auth_enabled=True",
            "network_access_enabled=True",
            "credential_handling_enabled=True",
            "raw_connector_content_enabled=True",
            "full_content_read_enabled=True",
            "connector_write_enabled=True",
            "connector_send_enabled=True",
            "connector_delete_enabled=True",
            "connector_export_enabled=True",
            "connector_bulk_export_enabled=True",
            "attachment_download_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/connectors/read",
            "/connectors/runtime/read",
            "/connectors/email/read",
            "/connectors/calendar/read",
            "/connectors/contacts/read",
            "/connectors/messages/read",
            "/connectors/messages/send",
            "/connectors/export",
            "/connectors/attachments/download",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/connector_read_only_runtime.py",
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
                            f"M125 forbidden connector read-only runtime fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m125_connector_read_only_runtime_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m125_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M125 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m125_roadmap_currentness(
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
            f"missing M125 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m125" not in text or "connector read-only runtime" not in text:
            failures.append(
                "active docs do not identify Checkpoint M125 Connector Read-Only Runtime"
            )
        if (
            "m125 is implemented/released" not in text
            and "checkpoint m125 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M125 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m125",
                "pre-alpha checkpoint",
                "m125",
                "connector read-only runtime",
                "implemented/released",
            ),
            (
                "checkpoint m126",
                "pre-alpha checkpoint",
                "m126",
                "connector approval capture",
                "implemented/released",
            ),
            (
                "checkpoint m127",
                "pre-alpha checkpoint",
                "m127",
                "connector write dry-run planner",
                "implemented/released",
            ),
            (
                "checkpoint m128",
                "pre-alpha checkpoint",
                "m128",
                "connector write execution, low-risk only",
                "implemented/released",
            ),
            (
                "checkpoint m129",
                "pre-alpha checkpoint",
                "m129",
                "connector audit + revocation hardening",
                "implemented/released",
            ),
            (
                "checkpoint m130",
                "pre-alpha checkpoint",
                "m130",
                "connector safety freeze",
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
                    f"active docs missing expected M125-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "live connector runtime is implemented",
            "account auth is implemented",
            "network access is implemented",
            "connector export is implemented",
            "beta is released",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M125 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m126_connector_approval_capture_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/connectors/connector_approval_capture.py",
            "src/ultimate_ai_agent/core/connectors/connector_read_only_runtime.py",
            "tests/test_m126_connector_approval_capture.py",
            "docs/connectors/CONNECTOR_APPROVAL_CAPTURE.md",
            "docs/connectors/CONNECTOR_APPROVAL_CAPTURE_AUTHORITY_BOUNDARY.md",
            "docs/connectors/CONNECTOR_APPROVAL_CAPTURE_RECEIPT_PLAN.md",
            "docs/connectors/CONNECTOR_APPROVAL_CAPTURE_NON_GOALS.md",
            "docs/connectors/M126_TO_M127_BOUNDARY.md",
            "docs/release_notes/checkpoint_m126.md",
            "docs/archive/checkpoints/m126/README_IMPORT.md",
            "docs/archive/checkpoints/m126/master_plan.md",
        ]
        failures = [
            f"missing M126 connector approval capture file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from datetime import timedelta

            from ultimate_ai_agent.core.connectors import (
                ConnectorApprovalDecisionKind,
                ConnectorApprovalCaptureDecisionStatus,
                ConnectorApprovalCaptureRequest,
                build_calendar_connector_contract_refresh_record,
                build_connector_read_only_runtime_record,
                build_contacts_connector_contract_refresh_record,
                build_email_connector_contract_refresh_record,
                build_messages_connector_contract_review_record,
                capture_connector_approval,
                validate_connector_approval_capture_record,
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
            from ultimate_ai_agent.core.time import utc_now

            source_record = build_messages_connector_contract_review_record(
                source_record=build_contacts_connector_contract_refresh_record(
                    source_record=build_calendar_connector_contract_refresh_record(
                        source_record=build_email_connector_contract_refresh_record(
                            source_record=build_production_authority_readiness_review_record(
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
                        )
                    )
                )
            )
            runtime_record = build_connector_read_only_runtime_record(
                source_record=source_record
            )
            request = ConnectorApprovalCaptureRequest(
                approval_ref="connector-approval-capture:m126:gate",
                actor_ref=runtime_record.actor_ref,
                user_ref=runtime_record.user_ref,
                workspace_ref=runtime_record.workspace_ref,
                connector_read_only_runtime_ref=(
                    runtime_record.connector_read_only_runtime_ref
                ),
                source_messages_connector_contract_review_ref=(
                    runtime_record.source_messages_connector_contract_review_ref
                ),
                source_baseline_ref=runtime_record.source_baseline_ref,
                connector_scope_refs=runtime_record.connector_scope_refs,
                connector_allowlist_refs=runtime_record.connector_allowlist_refs,
                operation_allowlist_refs=runtime_record.operation_allowlist_refs,
                redacted_metadata_preview_refs=(
                    runtime_record.redacted_metadata_preview_refs
                ),
                audit_ref="audit-ref:m126:gate",
                replay_ref="replay-ref:m126:gate",
                no_effect_receipt_plan_ref="receipt-plan-ref:m126:gate:no-effect",
                decision=ConnectorApprovalDecisionKind.approve_review_only,
                idempotency_key="idempotency-ref:m126:gate",
                expires_at=utc_now() + timedelta(minutes=5),
                safe_reason="Gate reviewed safe connector metadata refs only.",
            )
            decision = capture_connector_approval(
                runtime_record, request, current_time=utc_now()
            )
            if (
                decision.status
                != ConnectorApprovalCaptureDecisionStatus.approved_for_review_only
                or not decision.captured
                or not decision.persisted
                or not decision.review_only
                or decision.record is None
                or decision.receipt_plan is None
                or decision.live_connector_runtime_authorized
                or decision.account_auth_authorized
                or decision.network_access_authorized
                or decision.credential_handling_authorized
                or decision.raw_connector_content_authorized
                or decision.full_content_read_authorized
                or decision.connector_write_authorized
                or decision.connector_send_authorized
                or decision.connector_delete_authorized
                or decision.connector_export_authorized
                or decision.attachment_download_authorized
                or decision.memory_write_authorized
                or decision.context_injection_authorized
                or decision.execution_authorized
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
            ):
                failures.append(
                    "M126 connector approval capture decision is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {
                        "connector_read_only_runtime_ref": "connector-read-only-runtime:mismatch"
                    },
                    "M126_CONNECTOR_APPROVAL_RUNTIME_REF_MISMATCH",
                ),
                (
                    {"approval_ref": "approval_test_m126"},
                    "M126_CONNECTOR_APPROVAL_TEST_REF_DENIED",
                ),
                (
                    {"expires_at": utc_now() - timedelta(minutes=1)},
                    "M126_CONNECTOR_APPROVAL_EXPIRED",
                ),
                ({"revoked_at": utc_now()}, "M126_CONNECTOR_APPROVAL_REVOKED"),
                (
                    {"live_connector_runtime_enabled": True},
                    "M126_LIVE_CONNECTOR_RUNTIME_DENIED",
                ),
                (
                    {"raw_connector_content_enabled": True},
                    "M126_RAW_CONNECTOR_CONTENT_DENIED",
                ),
                ({"full_content_read_enabled": True}, "M126_FULL_CONTENT_READ_DENIED"),
                ({"connector_write_enabled": True}, "M126_CONNECTOR_WRITE_DENIED"),
                ({"connector_send_enabled": True}, "M126_CONNECTOR_SEND_DENIED"),
                ({"connector_delete_enabled": True}, "M126_CONNECTOR_DELETE_DENIED"),
                ({"connector_export_enabled": True}, "M126_CONNECTOR_EXPORT_DENIED"),
                (
                    {"attachment_download_enabled": True},
                    "M126_ATTACHMENT_DOWNLOAD_DENIED",
                ),
                ({"memory_write_enabled": True}, "M126_MEMORY_WRITE_DENIED"),
                ({"context_injection_enabled": True}, "M126_CONTEXT_INJECTION_DENIED"),
                ({"execution_enabled": True}, "M126_EXECUTION_DENIED"),
            ]:
                mutated = request.model_copy(update=update)
                rejected = capture_connector_approval(
                    runtime_record, mutated, current_time=utc_now()
                )
                if (
                    rejected.status != ConnectorApprovalCaptureDecisionStatus.rejected
                    or reason not in rejected.reason_codes
                    or rejected.captured
                    or rejected.persisted
                    or rejected.execution_authorized
                ):
                    failures.append(
                        f"M126 unsafe approval mutation was not denied with {reason}"
                    )
            if decision.record is not None:
                for update, reason in [
                    (
                        {"raw_connector_content": True},
                        "M126_RAW_CONNECTOR_CONTENT_DENIED",
                    ),
                    ({"full_connector_content": True}, "M126_FULL_CONTENT_READ_DENIED"),
                    (
                        {"connector_export_enabled": True},
                        "M126_CONNECTOR_EXPORT_DENIED",
                    ),
                    ({"execution_enabled": True}, "M126_EXECUTION_DENIED"),
                ]:
                    try:
                        validate_connector_approval_capture_record(
                            decision.record.model_copy(update=update)
                        )
                        failures.append(
                            f"M126 unsafe record mutation was not denied with {reason}"
                        )
                    except ValueError as exc:
                        if reason not in str(exc):
                            failures.append(
                                f"M126 unsafe record mutation raised {exc!s}"
                            )
        except Exception as exc:
            failures.append(f"M126 connector approval capture validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "connector approval capture",
            "exact-bound",
            "review-only",
            "safe refs only",
            "approval refs remain identifiers, not authority",
            "approval_test_",
            "m125 connector read-only runtime",
            "actor-bound",
            "user-bound",
            "workspace-bound",
            "replay-safe",
            "revocable",
            "no live connector runtime",
            "no account auth",
            "no network access",
            "no credential handling",
            "no raw connector content",
            "no full content read",
            "no connector write",
            "no connector send",
            "no connector delete",
            "no connector export",
            "no attachment download",
            "no model call",
            "no memory write",
            "no context injection",
            "no execution",
            "no backend route",
            "no control center control",
            "no dependency",
            "m127 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M126 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m126_connector_approval_capture_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "live_connector_runtime_enabled=True",
            "account_auth_enabled=True",
            "network_access_enabled=True",
            "credential_handling_enabled=True",
            "raw_connector_content_enabled=True",
            "full_content_read_enabled=True",
            "connector_write_enabled=True",
            "connector_send_enabled=True",
            "connector_delete_enabled=True",
            "connector_export_enabled=True",
            "connector_bulk_export_enabled=True",
            "attachment_download_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/connectors/approvals/capture",
            "/connectors/approve",
            "/connectors/read",
            "/connectors/runtime/read",
            "/connectors/messages/read",
            "/connectors/messages/send",
            "/connectors/export",
            "/connectors/attachments/download",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/connector_approval_capture.py",
            "src/ultimate_ai_agent/core/connectors/connector_read_only_runtime.py",
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
                            f"M126 forbidden connector approval capture fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m126_connector_approval_capture_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m126_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M126 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m126_roadmap_currentness(
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
            f"missing M126 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m126" not in text or "connector approval capture" not in text:
            failures.append(
                "active docs do not identify Checkpoint M126 Connector Approval Capture"
            )
        if (
            "m126 is implemented/released" not in text
            and "checkpoint m126 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M126 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m126",
                "pre-alpha checkpoint",
                "m126",
                "connector approval capture",
                "implemented/released",
            ),
            (
                "checkpoint m127",
                "pre-alpha checkpoint",
                "m127",
                "connector write dry-run planner",
                "implemented/released",
            ),
            (
                "checkpoint m128",
                "pre-alpha checkpoint",
                "m128",
                "connector write execution, low-risk only",
                "implemented/released",
            ),
            (
                "checkpoint m129",
                "pre-alpha checkpoint",
                "m129",
                "connector audit + revocation hardening",
                "implemented/released",
            ),
            (
                "checkpoint m130",
                "pre-alpha checkpoint",
                "m130",
                "connector safety freeze",
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
                    f"active docs missing expected M126/M127-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "live connector runtime is implemented",
            "account auth is implemented",
            "network access is implemented",
            "connector export is implemented",
            "beta is released",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M126 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m127_connector_write_dry_run_planner_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/connectors/connector_write_dry_run_planner.py",
            "src/ultimate_ai_agent/core/connectors/connector_approval_capture.py",
            "src/ultimate_ai_agent/core/connectors/connector_read_only_runtime.py",
            "tests/test_m127_connector_write_dry_run_planner.py",
            "tests/test_m127_gate_integration.py",
            "docs/connectors/CONNECTOR_WRITE_DRY_RUN_PLANNER.md",
            "docs/connectors/CONNECTOR_WRITE_DRY_RUN_PLANNER_AUTHORITY_BOUNDARY.md",
            "docs/connectors/CONNECTOR_WRITE_DRY_RUN_PLANNER_RECEIPT_PLAN.md",
            "docs/connectors/CONNECTOR_WRITE_DRY_RUN_PLANNER_NON_GOALS.md",
            "docs/connectors/M127_TO_M128_BOUNDARY.md",
            "docs/release_notes/checkpoint_m127.md",
            "docs/archive/checkpoints/m127/README_IMPORT.md",
            "docs/archive/checkpoints/m127/master_plan.md",
        ]
        failures = [
            f"missing M127 connector write dry-run planner file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from datetime import timedelta

            from ultimate_ai_agent.core.connectors import (
                ConnectorApprovalDecisionKind,
                ConnectorWriteDryRunActionKind,
                ConnectorWriteDryRunRequest,
                ConnectorWriteDryRunStatus,
                build_calendar_connector_contract_refresh_record,
                build_connector_read_only_runtime_record,
                build_contacts_connector_contract_refresh_record,
                build_email_connector_contract_refresh_record,
                build_messages_connector_contract_review_record,
                capture_connector_approval,
                plan_connector_write_dry_run,
                validate_connector_write_dry_run_plan,
            )
            from ultimate_ai_agent.core.connectors.connector_approval_capture import (
                ConnectorApprovalCaptureDecisionStatus,
                ConnectorApprovalCaptureRequest,
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
            from ultimate_ai_agent.core.time import utc_now

            source_record = build_messages_connector_contract_review_record(
                source_record=build_contacts_connector_contract_refresh_record(
                    source_record=build_calendar_connector_contract_refresh_record(
                        source_record=build_email_connector_contract_refresh_record(
                            source_record=build_production_authority_readiness_review_record(
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
                        )
                    )
                )
            )
            runtime_record = build_connector_read_only_runtime_record(
                source_record=source_record
            )
            approval_request = ConnectorApprovalCaptureRequest(
                approval_ref="connector-approval-capture:m126:m127-gate",
                actor_ref=runtime_record.actor_ref,
                user_ref=runtime_record.user_ref,
                workspace_ref=runtime_record.workspace_ref,
                connector_read_only_runtime_ref=(
                    runtime_record.connector_read_only_runtime_ref
                ),
                source_messages_connector_contract_review_ref=(
                    runtime_record.source_messages_connector_contract_review_ref
                ),
                source_baseline_ref=runtime_record.source_baseline_ref,
                connector_scope_refs=runtime_record.connector_scope_refs,
                connector_allowlist_refs=runtime_record.connector_allowlist_refs,
                operation_allowlist_refs=runtime_record.operation_allowlist_refs,
                redacted_metadata_preview_refs=(
                    runtime_record.redacted_metadata_preview_refs
                ),
                audit_ref="audit-ref:m126:m127-gate",
                replay_ref="replay-ref:m126:m127-gate",
                no_effect_receipt_plan_ref="receipt-plan-ref:m126:m127-gate:no-effect",
                decision=ConnectorApprovalDecisionKind.approve_review_only,
                idempotency_key="idempotency-ref:m126:m127-gate",
                expires_at=utc_now() + timedelta(minutes=5),
                safe_reason="Gate reviewed safe connector metadata refs only.",
            )
            approval_decision = capture_connector_approval(
                runtime_record, approval_request, current_time=utc_now()
            )
            if approval_decision.record is None:
                failures.append("M127 source M126 approval record was not captured")
            else:
                request = ConnectorWriteDryRunRequest(
                    dry_run_request_ref="connector-write-dry-run-request:m127:gate",
                    approval_ref=approval_decision.record.approval_ref,
                    connector_read_only_runtime_ref=(
                        approval_decision.record.connector_read_only_runtime_ref
                    ),
                    source_messages_connector_contract_review_ref=(
                        approval_decision.record.source_messages_connector_contract_review_ref
                    ),
                    source_baseline_ref=approval_decision.record.source_baseline_ref,
                    actor_ref=approval_decision.record.actor_ref,
                    user_ref=approval_decision.record.user_ref,
                    workspace_ref=approval_decision.record.workspace_ref,
                    connector_scope_refs=approval_decision.record.connector_scope_refs,
                    connector_allowlist_refs=(
                        approval_decision.record.connector_allowlist_refs
                    ),
                    source_operation_allowlist_refs=(
                        approval_decision.record.operation_allowlist_refs
                    ),
                    redacted_metadata_preview_refs=(
                        approval_decision.record.redacted_metadata_preview_refs
                    ),
                    dry_run_operation_refs=[
                        "connector-write-dry-run-operation-ref:m127:plan-email-draft"
                    ],
                    write_target_refs=[
                        "connector-write-target-ref:m127:gate-email-draft"
                    ],
                    safe_payload_summary_refs=[
                        "safe-payload-summary-ref:m127:gate-email-draft"
                    ],
                    data_minimization_refs=[
                        "data-minimization-ref:m127:safe-summary-only"
                    ],
                    redaction_refs=["redaction-ref:m127:gate-no-raw-body"],
                    audit_ref="audit-ref:m127:gate",
                    replay_ref="replay-ref:m127:gate",
                    idempotency_key="idempotency-ref:m127:gate",
                    dry_run_receipt_plan_ref="receipt-plan-ref:m127:gate:no-effect",
                    action_kind=ConnectorWriteDryRunActionKind.plan_email_draft,
                    expires_at=utc_now() + timedelta(minutes=5),
                    safe_reason="Plan a connector write draft from safe refs only.",
                )
                decision = plan_connector_write_dry_run(
                    approval_decision, request, current_time=utc_now()
                )
                if (
                    decision.status != ConnectorWriteDryRunStatus.planned_for_review
                    or not decision.planned
                    or not decision.persisted
                    or not decision.dry_run_only
                    or decision.plan is None
                    or decision.receipt_plan is None
                    or decision.live_connector_runtime_authorized
                    or decision.account_auth_authorized
                    or decision.network_access_authorized
                    or decision.credential_handling_authorized
                    or decision.raw_connector_content_authorized
                    or decision.full_content_read_authorized
                    or decision.connector_write_authorized
                    or decision.connector_send_authorized
                    or decision.connector_delete_authorized
                    or decision.connector_export_authorized
                    or decision.connector_bulk_export_authorized
                    or decision.attachment_download_authorized
                    or decision.model_call_authorized
                    or decision.memory_write_authorized
                    or decision.context_injection_authorized
                    or decision.execution_authorized
                    or decision.execution_performed
                    or decision.backend_route_added
                    or decision.control_center_control_added
                    or decision.dependency_added
                ):
                    failures.append(
                        "M127 connector write dry-run decision is unsafe or over-authoritative"
                    )
                for update, reason in [
                    (
                        {"approval_ref": "connector-approval-capture:m126:other"},
                        "M127_CONNECTOR_WRITE_DRY_RUN_APPROVAL_REF_MISMATCH",
                    ),
                    (
                        {
                            "connector_read_only_runtime_ref": "connector-read-only-runtime:mismatch"
                        },
                        "M127_CONNECTOR_WRITE_DRY_RUN_RUNTIME_REF_MISMATCH",
                    ),
                    (
                        {"approval_ref": "approval_test_m127"},
                        "M127_CONNECTOR_WRITE_DRY_RUN_TEST_APPROVAL_DENIED",
                    ),
                    (
                        {"expires_at": utc_now() - timedelta(minutes=1)},
                        "M127_CONNECTOR_WRITE_DRY_RUN_EXPIRED",
                    ),
                    ({"revoked_at": utc_now()}, "M127_CONNECTOR_WRITE_DRY_RUN_REVOKED"),
                    (
                        {
                            "dry_run_operation_refs": [
                                "connector-write-dry-run-operation-ref:m127:unknown"
                            ]
                        },
                        "M127_CONNECTOR_WRITE_DRY_RUN_ACTION_OPERATION_REQUIRED",
                    ),
                    (
                        {"connector_write_enabled": True},
                        "M127_CONNECTOR_WRITE_EXECUTION_DENIED",
                    ),
                    ({"connector_send_enabled": True}, "M127_CONNECTOR_SEND_DENIED"),
                    (
                        {"connector_delete_enabled": True},
                        "M127_CONNECTOR_DELETE_DENIED",
                    ),
                    (
                        {"connector_export_enabled": True},
                        "M127_CONNECTOR_EXPORT_DENIED",
                    ),
                    ({"network_access_enabled": True}, "M127_NETWORK_ACCESS_DENIED"),
                    ({"model_call_enabled": True}, "M127_MODEL_CALL_DENIED"),
                    ({"execution_enabled": True}, "M127_EXECUTION_DENIED"),
                ]:
                    rejected = plan_connector_write_dry_run(
                        approval_decision,
                        request.model_copy(update=update),
                        current_time=utc_now(),
                    )
                    if (
                        rejected.status != ConnectorWriteDryRunStatus.rejected
                        or reason not in rejected.reason_codes
                        or rejected.planned
                        or rejected.persisted
                        or rejected.execution_authorized
                    ):
                        failures.append(
                            f"M127 unsafe dry-run mutation was not denied with {reason}"
                        )
                if decision.plan is not None:
                    for update, reason in [
                        (
                            {"raw_connector_content": True},
                            "M127_RAW_CONNECTOR_CONTENT_DENIED",
                        ),
                        (
                            {"full_connector_content": True},
                            "M127_FULL_CONTENT_READ_DENIED",
                        ),
                        (
                            {"side_effects_performed": ["write executed"]},
                            "M127_CONNECTOR_WRITE_DRY_RUN_SIDE_EFFECTS_DENIED",
                        ),
                        (
                            {"connector_write_enabled": True},
                            "M127_CONNECTOR_WRITE_EXECUTION_DENIED",
                        ),
                        ({"execution_enabled": True}, "M127_EXECUTION_DENIED"),
                    ]:
                        try:
                            validate_connector_write_dry_run_plan(
                                decision.plan.model_copy(update=update)
                            )
                            failures.append(
                                f"M127 unsafe plan mutation was not denied with {reason}"
                            )
                        except ValueError as exc:
                            if reason not in str(exc):
                                failures.append(
                                    f"M127 unsafe plan mutation raised {exc!s}"
                                )
            denied_approval = capture_connector_approval(
                runtime_record,
                approval_request.model_copy(
                    update={"decision": ConnectorApprovalDecisionKind.deny_review_only}
                ),
                current_time=utc_now(),
            )
            if (
                denied_approval.status
                != ConnectorApprovalCaptureDecisionStatus.denied_for_review
                and denied_approval.status
                != ConnectorApprovalCaptureDecisionStatus.rejected
            ):
                failures.append("M127 source denied approval did not deny safely")
        except Exception as exc:
            failures.append(
                f"M127 connector write dry-run planner validation failed: {exc}"
            )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "connector write dry-run planner",
            "dry-run-only",
            "review-only",
            "safe refs only",
            "exact-bound",
            "approval refs remain identifiers, not authority",
            "m126 connector approval capture",
            "m125 connector read-only runtime",
            "actor-bound",
            "user-bound",
            "workspace-bound",
            "replay-safe",
            "revocable",
            "no-effect receipt",
            "no live connector runtime",
            "no account auth",
            "no network access",
            "no credential handling",
            "no raw connector content",
            "no full content read",
            "no connector write execution",
            "no connector send execution",
            "no connector delete execution",
            "no connector export",
            "no attachment download",
            "no model call",
            "no memory write",
            "no context injection",
            "no execution",
            "no backend route",
            "no control center control",
            "no dependency",
            "m128 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M127 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m127_connector_write_dry_run_planner_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "live_connector_runtime_enabled=True",
            "account_auth_enabled=True",
            "network_access_enabled=True",
            "credential_handling_enabled=True",
            "raw_connector_content_enabled=True",
            "full_content_read_enabled=True",
            "connector_write_enabled=True",
            "connector_send_enabled=True",
            "connector_delete_enabled=True",
            "connector_export_enabled=True",
            "connector_bulk_export_enabled=True",
            "attachment_download_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/connectors/write/dry-run",
            "/connectors/dry-run/write",
            "/connectors/write/plan",
            "/connectors/write/execute",
            "/connectors/send/execute",
            "/connectors/messages/reply",
            "/connectors/email/draft",
            "/connectors/calendar/events/create",
            "/connectors/contacts/update",
            "/connectors/attachments/download",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/connector_write_dry_run_planner.py",
            "src/ultimate_ai_agent/core/connectors/connector_approval_capture.py",
            "src/ultimate_ai_agent/core/connectors/connector_read_only_runtime.py",
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
                            f"M127 forbidden connector write dry-run fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m127_connector_write_dry_run_planner_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m127_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M127 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
