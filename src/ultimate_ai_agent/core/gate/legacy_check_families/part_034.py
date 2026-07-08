from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart034Mixin:
    """Legacy checks from m127_roadmap_currentness through m130_connector_safety_freeze_route_boundary."""
    def check_m127_roadmap_currentness(
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
            f"missing M127 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m127" not in text
            or "connector write dry-run planner" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M127 Connector Write Dry-Run Planner"
            )
        if (
            "m127 is implemented/released" not in text
            and "checkpoint m127 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M127 implemented/released")
        for version_label, product_target, milestone, title, status in [
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
                    f"active docs missing expected M127/M128-M130 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "revocation execution is implemented",
            "kill switch execution is implemented",
            "live connector runtime is implemented",
            "account auth is implemented",
            "network access is implemented",
            "credential handling is implemented",
            "raw connector content is implemented",
            "full content read is implemented",
            "connector export is implemented",
            "attachment download is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "beta is released",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M127 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m128_connector_write_execution_low_risk_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/connectors/connector_write_execution_low_risk.py",
            "src/ultimate_ai_agent/core/connectors/connector_write_dry_run_planner.py",
            "src/ultimate_ai_agent/core/connectors/connector_approval_capture.py",
            "src/ultimate_ai_agent/core/connectors/connector_read_only_runtime.py",
            "tests/test_m128_connector_write_execution_low_risk.py",
            "tests/test_m128_gate_integration.py",
            "docs/connectors/CONNECTOR_WRITE_EXECUTION_LOW_RISK.md",
            "docs/connectors/CONNECTOR_WRITE_EXECUTION_LOW_RISK_AUTHORITY_BOUNDARY.md",
            "docs/connectors/CONNECTOR_WRITE_EXECUTION_LOW_RISK_RECEIPT_PLAN.md",
            "docs/connectors/CONNECTOR_WRITE_EXECUTION_LOW_RISK_NON_GOALS.md",
            "docs/connectors/M128_TO_M129_BOUNDARY.md",
            "docs/release_notes/checkpoint_m128.md",
            "docs/archive/checkpoints/m128/README_IMPORT.md",
            "docs/archive/checkpoints/m128/master_plan.md",
        ]
        failures = [
            f"missing M128 connector write execution low-risk file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m128_connector_write_execution_low_risk import (
                _request,
                _transport,
            )
            from ultimate_ai_agent.core.connectors import (
                ConnectorWriteExecutionLowRiskStatus,
                build_connector_write_execution_decision,
                perform_low_risk_connector_write,
                validate_connector_write_execution_decision,
                validate_connector_write_execution_result,
            )

            decision = build_connector_write_execution_decision(_request())
            result = perform_low_risk_connector_write(decision, transport=_transport)
            if (
                decision.status
                != ConnectorWriteExecutionLowRiskStatus.write_allowed_for_low_risk_transport
                or not decision.low_risk_write_allowed
                or not decision.exact_m127_dry_run_bound
                or not decision.exact_connector_write_approval_bound
                or not decision.transport_required
                or not decision.safe_refs_only
                or not decision.local_only
                or not decision.audit_bound
                or not decision.replay_bound
                or not decision.revocation_bound
                or decision.write_performed
                or decision.live_connector_runtime_performed
                or decision.account_auth_performed
                or decision.network_access_performed
                or decision.credential_handling_performed
                or decision.raw_connector_content_returned
                or decision.full_connector_content_returned
                or decision.connector_send_performed
                or decision.connector_delete_performed
                or decision.connector_export_performed
                or decision.connector_bulk_export_performed
                or decision.attachment_download_performed
                or decision.model_call_performed
                or decision.memory_write_performed
                or decision.context_injection_performed
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.production_authority_granted
                or decision.side_effects_performed
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or result.status != ConnectorWriteExecutionLowRiskStatus.write_completed
                or not result.write_performed
                or result.safe_result_ref != decision.safe_result_ref
                or result.live_connector_runtime_performed
                or result.account_auth_performed
                or result.network_access_performed
                or result.credential_handling_performed
                or result.raw_connector_content_returned
                or result.full_connector_content_returned
                or result.connector_send_performed
                or result.connector_delete_performed
                or result.connector_export_performed
                or result.connector_bulk_export_performed
                or result.attachment_download_performed
                or result.model_call_performed
                or result.memory_write_performed
                or result.context_injection_performed
                or result.backend_route_added
                or result.control_center_control_added
                or result.dependency_added
                or result.production_authority_granted
                or result.side_effects_performed
                or "M128_LOW_RISK_CONNECTOR_WRITE_ALLOWED" not in decision.reason_codes
                or "M129_REMAINS_FUTURE" not in decision.reason_codes
                or "M128_LOW_RISK_CONNECTOR_WRITE_COMPLETED" not in result.reason_codes
            ):
                failures.append(
                    "M128 connector write execution decision/result is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"write_performed": True}, "M128_WRITE_NOT_ALLOWED_IN_DECISION"),
                ({"network_access_performed": True}, "M128_NETWORK_ACCESS_DENIED"),
                ({"connector_send_performed": True}, "M128_CONNECTOR_SEND_DENIED"),
                ({"connector_delete_performed": True}, "M128_CONNECTOR_DELETE_DENIED"),
                ({"backend_route_added": True}, "M128_BACKEND_ROUTE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M128_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_connector_write_execution_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M128 unsafe decision mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M128 unsafe decision mutation raised {exc!s}")
            for update, reason in [
                ({"network_access_performed": True}, "M128_NETWORK_ACCESS_DENIED"),
                (
                    {"raw_connector_content_returned": True},
                    "M128_RAW_CONNECTOR_CONTENT_DENIED",
                ),
                ({"connector_export_performed": True}, "M128_CONNECTOR_EXPORT_DENIED"),
                ({"backend_route_added": True}, "M128_BACKEND_ROUTE_DENIED"),
            ]:
                try:
                    validate_connector_write_execution_result(
                        result.model_copy(update=update)
                    )
                    failures.append(
                        f"M128 unsafe result mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M128 unsafe result mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M128 connector write execution validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "connector write execution",
            "low-risk-only",
            "local-only",
            "safe-ref-only",
            "exact-bound",
            "injected safe transport",
            "safe result ref",
            "safe summary",
            "exact connector write approval",
            "approval refs remain identifiers, not authority",
            "m127 connector write dry-run planner",
            "m126 connector approval capture",
            "m125 connector read-only runtime",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no live connector runtime",
            "no account auth",
            "no network access",
            "no credential handling",
            "no raw connector content",
            "no full content read",
            "no connector send execution",
            "no connector delete execution",
            "no connector export",
            "no connector bulk export",
            "no attachment download",
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "m129 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M128 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m128_connector_write_execution_low_risk_static_safety(
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
            "connector_send_enabled=True",
            "connector_delete_enabled=True",
            "connector_export_enabled=True",
            "connector_bulk_export_enabled=True",
            "attachment_download_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "live_connector_runtime_requested=True",
            "account_auth_requested=True",
            "network_access_requested=True",
            "credential_handling_requested=True",
            "raw_connector_content_requested=True",
            "full_content_read_requested=True",
            "connector_send_requested=True",
            "connector_delete_requested=True",
            "connector_export_requested=True",
            "connector_bulk_export_requested=True",
            "attachment_download_requested=True",
            "model_call_requested=True",
            "memory_write_requested=True",
            "context_injection_requested=True",
            "backend_route_requested=True",
            "control_center_control_requested=True",
            "dependency_requested=True",
            "production_authority_requested=True",
            "high_risk_write_requested=True",
            "live_connector_runtime_performed=True",
            "account_auth_performed=True",
            "network_access_performed=True",
            "credential_handling_performed=True",
            "raw_connector_content_returned=True",
            "full_connector_content_returned=True",
            "connector_send_performed=True",
            "connector_delete_performed=True",
            "connector_export_performed=True",
            "connector_bulk_export_performed=True",
            "attachment_download_performed=True",
            "model_call_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "store_raw_connector_content=True",
            "store_full_connector_content=True",
            "store_credential_material=True",
            "/connectors/write/execute",
            "/connectors/write/low-risk",
            "/connectors/write/result",
            "/connectors/send",
            "/connectors/delete",
            "/connectors/export",
            "/connectors/audit/hardening",
            "/connectors/revocation/execute",
            "/connectors/kill-switch/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/connector_write_execution_low_risk.py",
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
                            f"M128 forbidden connector write execution fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m128_connector_write_execution_low_risk_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m128_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M128 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m128_roadmap_currentness(
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
            f"missing M128 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m128" not in text
            or "connector write execution, low-risk only" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M128 Connector Write Execution, Low-Risk Only"
            )
        if (
            "m128 is implemented/released" not in text
            and "checkpoint m128 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M128 implemented/released")
        for version_label, product_target, milestone, title, status in [
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
                    f"active docs missing expected M128/M129-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "revocation execution is implemented",
            "kill switch execution is implemented",
            "connector export is implemented",
            "connector send execution is implemented",
            "connector delete execution is implemented",
            "live connector runtime is implemented",
            "account auth is implemented",
            "network access is implemented",
            "credential handling is implemented",
            "raw connector content is implemented",
            "full content read is implemented",
            "attachment download is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "beta is released",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M128 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m129_connector_audit_revocation_hardening_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/connectors/connector_audit_revocation_hardening.py",
            "src/ultimate_ai_agent/core/connectors/connector_write_execution_low_risk.py",
            "src/ultimate_ai_agent/core/connectors/connector_write_dry_run_planner.py",
            "src/ultimate_ai_agent/core/connectors/connector_approval_capture.py",
            "src/ultimate_ai_agent/core/connectors/connector_read_only_runtime.py",
            "tests/test_m129_connector_audit_revocation_hardening.py",
            "tests/test_m129_gate_integration.py",
            "docs/connectors/CONNECTOR_AUDIT_REVOCATION_HARDENING.md",
            "docs/connectors/CONNECTOR_AUDIT_REVOCATION_HARDENING_AUTHORITY_BOUNDARY.md",
            "docs/connectors/CONNECTOR_AUDIT_REVOCATION_HARDENING_RECEIPT_PLAN.md",
            "docs/connectors/CONNECTOR_AUDIT_REVOCATION_HARDENING_NON_GOALS.md",
            "docs/connectors/M129_TO_M130_BOUNDARY.md",
            "docs/release_notes/checkpoint_m129.md",
            "docs/archive/checkpoints/m129/README_IMPORT.md",
            "docs/archive/checkpoints/m129/master_plan.md",
        ]
        failures = [
            f"missing M129 connector audit revocation hardening file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m129_connector_audit_revocation_hardening import _request
            from ultimate_ai_agent.core.connectors import (
                ConnectorAuditRevocationHardeningStatus,
                build_connector_audit_revocation_hardening_report,
                validate_connector_audit_ledger_entry,
                validate_connector_audit_revocation_hardening_report,
                validate_connector_revocation_hardening_record,
            )

            report = build_connector_audit_revocation_hardening_report(_request())
            if (
                report.status
                != ConnectorAuditRevocationHardeningStatus.hardened_for_governed_review
                or not report.exact_m128_execution_bound
                or not report.audit_hardened
                or not report.revocation_hardened
                or not report.audit_bound
                or not report.replay_bound
                or not report.revocation_ready
                or not report.local_only
                or not report.safe_refs_only
                or not report.review_only
                or report.live_connector_runtime_performed
                or report.account_auth_performed
                or report.network_access_performed
                or report.credential_handling_performed
                or report.raw_connector_content_returned
                or report.full_connector_content_returned
                or report.connector_write_performed
                or report.connector_send_performed
                or report.connector_delete_performed
                or report.connector_export_performed
                or report.connector_bulk_export_performed
                or report.attachment_download_performed
                or report.audit_export_performed
                or report.revocation_executed
                or report.kill_switch_executed
                or report.model_call_performed
                or report.memory_write_performed
                or report.context_injection_performed
                or report.backend_route_added
                or report.control_center_control_added
                or report.dependency_added
                or report.production_authority_granted
                or report.side_effects_performed
                or not report.audit_ledger_entry.store_safe_refs_only
                or not report.audit_ledger_entry.store_safe_summary_only
                or report.audit_ledger_entry.raw_audit_payload_stored
                or report.audit_ledger_entry.audit_exported
                or not report.revocation_record.revocation_ready
                or not report.revocation_record.revocation_review_only
                or report.revocation_record.revocation_executed
                or report.revocation_record.kill_switch_executed
                or report.revocation_record.connector_approval_revoked
                or "M129_CONNECTOR_AUDIT_REVOCATION_HARDENED" not in report.reason_codes
                or "M130_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M129 connector audit revocation hardening report is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"revocation_executed": True},
                    "M129_REVOCATION_EXECUTION_DENIED",
                ),
                (
                    {"kill_switch_executed": True},
                    "M129_KILL_SWITCH_EXECUTION_DENIED",
                ),
                (
                    {"audit_export_performed": True},
                    "M129_AUDIT_EXPORT_DENIED",
                ),
                ({"backend_route_added": True}, "M129_BACKEND_ROUTE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M129_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_connector_audit_revocation_hardening_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M129 unsafe report mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M129 unsafe report mutation raised {exc!s}")
            for target, update, reason in [
                (
                    "audit ledger entry",
                    {"raw_audit_payload_stored": True},
                    "M129_RAW_AUDIT_PAYLOAD_DENIED",
                ),
                (
                    "audit ledger entry",
                    {"audit_exported": True},
                    "M129_AUDIT_EXPORT_DENIED",
                ),
                (
                    "revocation record",
                    {"connector_approval_revoked": True},
                    "M129_APPROVAL_REVOCATION_EXECUTION_DENIED",
                ),
                (
                    "revocation record",
                    {"connector_session_stopped": True},
                    "M129_CONNECTOR_SESSION_STOP_DENIED",
                ),
            ]:
                try:
                    if target == "audit ledger entry":
                        validate_connector_audit_ledger_entry(
                            report.audit_ledger_entry.model_copy(update=update)
                        )
                    else:
                        validate_connector_revocation_hardening_record(
                            report.revocation_record.model_copy(update=update)
                        )
                    failures.append(
                        f"M129 unsafe {target} mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M129 unsafe {target} mutation raised {exc!s}")
        except Exception as exc:
            failures.append(
                f"M129 connector audit revocation hardening validation failed: {exc}"
            )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "connector audit + revocation hardening",
            "review-only",
            "hardening-only",
            "local-only",
            "safe-ref-only",
            "exact-bound",
            "m128 connector write execution",
            "safe audit ledger",
            "revocation readiness",
            "safe refs only",
            "safe summaries only",
            "audit ref",
            "replay ref",
            "revocation ref",
            "kill-switch ref",
            "retention policy ref",
            "redaction ref",
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
            "no connector bulk export",
            "no attachment download",
            "no audit export",
            "no revocation execution",
            "no kill-switch execution",
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "m130 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M129 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m129_connector_audit_revocation_hardening_static_safety(
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
            "audit_export_enabled=True",
            "revocation_execution_enabled=True",
            "kill_switch_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "live_connector_runtime_requested=True",
            "account_auth_requested=True",
            "network_access_requested=True",
            "credential_handling_requested=True",
            "raw_connector_content_requested=True",
            "full_content_read_requested=True",
            "connector_write_requested=True",
            "connector_send_requested=True",
            "connector_delete_requested=True",
            "connector_export_requested=True",
            "connector_bulk_export_requested=True",
            "attachment_download_requested=True",
            "audit_export_requested=True",
            "revocation_execution_requested=True",
            "kill_switch_execution_requested=True",
            "model_call_requested=True",
            "memory_write_requested=True",
            "context_injection_requested=True",
            "backend_route_requested=True",
            "control_center_control_requested=True",
            "dependency_requested=True",
            "production_authority_requested=True",
            "raw_audit_payload_stored=True",
            "audit_exported=True",
            "revocation_executed=True",
            "kill_switch_executed=True",
            "connector_approval_revoked=True",
            "connector_session_stopped=True",
            "connector_write_performed=True",
            "connector_send_performed=True",
            "connector_delete_performed=True",
            "connector_export_performed=True",
            "connector_bulk_export_performed=True",
            "attachment_download_performed=True",
            "/connectors/audit",
            "/connectors/audit/export",
            "/connectors/revocation",
            "/connectors/revocation/execute",
            "/connectors/kill-switch",
            "/connectors/kill-switch/execute",
            "/connectors/safety/freeze",
            "/connectors/freeze",
            "/connectors/export",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/connector_safety_freeze.py",
            "src/ultimate_ai_agent/core/connectors/connector_audit_revocation_hardening.py",
            "src/ultimate_ai_agent/core/connectors/connector_write_execution_low_risk.py",
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
                            f"M129 forbidden connector audit revocation fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m129_connector_audit_revocation_hardening_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m129_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M129 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m129_roadmap_currentness(
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
            f"missing M129 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m129" not in text
            or "connector audit + revocation hardening" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M129 Connector Audit + Revocation Hardening"
            )
        if (
            "m129 is implemented/released" not in text
            and "checkpoint m129 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M129 implemented/released")
        for version_label, product_target, milestone, title, status in [
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
                    f"active docs missing expected M129/M130-M131 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "freeze acceptance is implemented",
            "revocation execution is implemented",
            "kill switch execution is implemented",
            "connector export is implemented",
            "connector send execution is implemented",
            "connector delete execution is implemented",
            "live connector runtime is implemented",
            "account auth is implemented",
            "network access is implemented",
            "credential handling is implemented",
            "raw connector content is implemented",
            "full content read is implemented",
            "attachment download is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "beta is released",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M129 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m130_connector_safety_freeze_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/connectors/connector_safety_freeze.py",
            "src/ultimate_ai_agent/core/connectors/connector_audit_revocation_hardening.py",
            "src/ultimate_ai_agent/core/connectors/connector_write_execution_low_risk.py",
            "tests/test_m130_connector_safety_freeze.py",
            "tests/test_m130_gate_integration.py",
            "docs/connectors/CONNECTOR_SAFETY_FREEZE.md",
            "docs/connectors/CONNECTOR_SAFETY_FREEZE_POLICY.md",
            "docs/connectors/CONNECTOR_SAFETY_FREEZE_AUTHORITY_BOUNDARY.md",
            "docs/connectors/CONNECTOR_SAFETY_FREEZE_RECEIPT_PLAN.md",
            "docs/connectors/CONNECTOR_SAFETY_FREEZE_NON_GOALS.md",
            "docs/connectors/M130_TO_M131_BOUNDARY.md",
            "docs/release_notes/checkpoint_m130.md",
            "docs/archive/checkpoints/m130/README_IMPORT.md",
            "docs/archive/checkpoints/m130/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M130 connector safety freeze file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m130_connector_safety_freeze import _source_report
            from ultimate_ai_agent.core.connectors import (
                ConnectorSafetyFreezeStatus,
                build_connector_safety_freeze_record,
                validate_connector_safety_freeze_record,
            )

            record = build_connector_safety_freeze_record(
                source_report=_source_report()
            )
            if (
                record.status != ConnectorSafetyFreezeStatus.frozen_for_review
                or not record.contract_only
                or not record.review_only
                or not record.freeze_only
                or not record.deterministic
                or not record.local_only
                or not record.safe_refs_only
                or not record.exact_m129_hardening_bound
                or not record.connector_surface_frozen
                or not record.audit_replay_bound
                or not record.revocation_readiness_bound
                or not record.no_effect_receipt_required
                or record.accepted_checkpoint_refs
                != [
                    "checkpoint:m121",
                    "checkpoint:m122",
                    "checkpoint:m123",
                    "checkpoint:m124",
                    "checkpoint:m125",
                    "checkpoint:m126",
                    "checkpoint:m127",
                    "checkpoint:m128",
                    "checkpoint:m129",
                ]
                or record.live_connector_runtime_enabled
                or record.live_connector_runtime_performed
                or record.account_auth_enabled
                or record.account_auth_performed
                or record.network_access_enabled
                or record.network_access_performed
                or record.credential_handling_enabled
                or record.credential_handling_performed
                or record.raw_connector_content_enabled
                or record.raw_connector_content_returned
                or record.full_content_read_enabled
                or record.full_connector_content_returned
                or record.connector_write_enabled
                or record.connector_write_performed
                or record.connector_send_enabled
                or record.connector_send_performed
                or record.connector_delete_enabled
                or record.connector_delete_performed
                or record.connector_export_enabled
                or record.connector_export_performed
                or record.connector_bulk_export_enabled
                or record.connector_bulk_export_performed
                or record.attachment_download_enabled
                or record.attachment_download_performed
                or record.audit_export_enabled
                or record.audit_export_performed
                or record.revocation_execution_enabled
                or record.revocation_executed
                or record.kill_switch_execution_enabled
                or record.kill_switch_executed
                or record.connector_approval_revoked
                or record.connector_session_stopped
                or record.background_worker_started
                or record.scheduler_started
                or record.external_service_called
                or record.model_call_performed
                or record.memory_write_performed
                or record.context_injection_performed
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.beta_release_enabled
                or record.production_authority_granted
                or record.side_effects_performed
                or "M130_CONNECTOR_SAFETY_FREEZE" not in record.reason_codes
                or "M131_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M130 connector safety freeze record is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"revocation_executed": True}, "M130_REVOCATION_EXECUTION_DENIED"),
                ({"kill_switch_executed": True}, "M130_KILL_SWITCH_EXECUTION_DENIED"),
                ({"connector_export_performed": True}, "M130_CONNECTOR_EXPORT_DENIED"),
                ({"audit_export_performed": True}, "M130_AUDIT_EXPORT_DENIED"),
                ({"backend_route_added": True}, "M130_BACKEND_ROUTE_DENIED"),
                ({"beta_release_enabled": True}, "M130_BETA_RELEASE_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M130_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_connector_safety_freeze_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M130 unsafe freeze mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M130 unsafe freeze mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M130 connector safety freeze validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "connector safety freeze",
            "contract-only",
            "review-only",
            "freeze-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "exact m129",
            "accepted checkpoint refs",
            "safety checklist ref",
            "audit ref",
            "replay ref",
            "revocation ref",
            "kill-switch ref",
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
            "no connector bulk export",
            "no attachment download",
            "no audit export",
            "no revocation execution",
            "no kill-switch execution",
            "no approval revocation",
            "no session stop",
            "no backend route",
            "no control center control",
            "no dependency",
            "m131 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M130 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m130_connector_safety_freeze_static_safety(
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
            "audit_export_enabled=True",
            "revocation_execution_enabled=True",
            "kill_switch_execution_enabled=True",
            "connector_approval_revocation_enabled=True",
            "connector_session_stop_enabled=True",
            "background_worker_enabled=True",
            "scheduler_enabled=True",
            "external_service_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "beta_release_enabled=True",
            "production_authority_granted=True",
            "live_connector_runtime_performed=True",
            "account_auth_performed=True",
            "network_access_performed=True",
            "credential_handling_performed=True",
            "raw_connector_content_returned=True",
            "full_connector_content_returned=True",
            "connector_write_performed=True",
            "connector_send_performed=True",
            "connector_delete_performed=True",
            "connector_export_performed=True",
            "connector_bulk_export_performed=True",
            "attachment_download_performed=True",
            "audit_export_performed=True",
            "revocation_executed=True",
            "kill_switch_executed=True",
            "connector_approval_revoked=True",
            "connector_session_stopped=True",
            "background_worker_started=True",
            "scheduler_started=True",
            "external_service_called=True",
            "model_call_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "/connectors/safety/freeze",
            "/connectors/freeze",
            "/connectors/freeze/accept",
            "/connectors/runtime",
            "/connectors/auth",
            "/connectors/export",
            "/connectors/audit/export",
            "/connectors/revocation/execute",
            "/connectors/kill-switch/execute",
            "/autonomy/mode4",
            "/autonomy/scoped-work-session",
            "/automation/session/start",
            "/memory/write",
            "/context/inject",
            "/tools/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/connector_safety_freeze.py",
            "src/ultimate_ai_agent/core/connectors/connector_audit_revocation_hardening.py",
            "src/ultimate_ai_agent/core/connectors/connector_write_execution_low_risk.py",
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
                            f"M130 forbidden connector freeze fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m130_connector_safety_freeze_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m130_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M130 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
