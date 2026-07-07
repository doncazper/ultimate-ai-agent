from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart027Mixin:
    """Legacy checks from m106_mobile_background_read_only_status_sync_static_safety through m109_mobile_sensor_audit_ledger_route_boundary."""
    def check_m106_mobile_background_read_only_status_sync_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "background_worker_enabled=True",
            "scheduler_enabled=True",
            "daemon_enabled=True",
            "os_background_fetch_enabled=True",
            "os_background_permission_prompt_enabled=True",
            "push_trigger_enabled=True",
            "device_token_handling_enabled=True",
            "external_service_enabled=True",
            "network_sync_enabled=True",
            "raw_status_payload_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_change_enabled=True",
            "dependency_added=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "production_authority_enabled=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
            "src/ultimate_ai_agent/core/mobile_companion/background_task_contract_no_execution.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_background_read_only_status_sync.py",
            "src/ultimate_ai_agent/core/mobile_companion/camera_photos_metadata_only.py",
            "src/ultimate_ai_agent/core/mobile_companion/location_sensor_off_by_default.py",
            "src/ultimate_ai_agent/core/mobile_companion/notification_planning_no_push.py",
            "src/ultimate_ai_agent/core/mobile_companion/permission_model_v1.py",
            "src/ultimate_ai_agent/core/mobile_companion/sensor_contract_review.py",
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
                            f"M106 forbidden background status fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m106_mobile_background_read_only_status_sync_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m106_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M106 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m106_roadmap_currentness(
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
            f"missing M106 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m106" not in text
            or "mobile background read-only status sync" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M106 Mobile Background Read-Only Status Sync"
            )
        if (
            "m106 is implemented/released" not in text
            and "checkpoint m106 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M106 implemented/released")
        implemented_m107_row = (
            "| checkpoint m107 | pre-alpha checkpoint | m107 | "
            "mobile approval renewal ux | implemented/released |"
        )
        implemented_m108_row = (
            "| checkpoint m108 | pre-alpha checkpoint | m108 | "
            "mobile kill switch + revocation | implemented/released |"
        )
        if implemented_m107_row not in text:
            failures.append("active docs missing implemented Checkpoint M107 row")
        planned_rows = [
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]
        if implemented_m108_row not in text:
            planned_rows.insert(
                0,
                (
                    "checkpoint m108",
                    "pre-alpha checkpoint",
                    "m108",
                    "mobile kill switch + revocation",
                ),
            )
        for version_label, product_target, milestone, title in planned_rows:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M108-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "background task execution is implemented",
            "background worker is implemented",
            "scheduler is implemented",
            "daemon is implemented",
            "network sync is implemented",
            "push trigger is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M106 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m107_mobile_approval_renewal_ux_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/mobile_approval_renewal_ux.py",
            "docs/mobile/MOBILE_APPROVAL_RENEWAL_UX.md",
            "docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_POLICY.md",
            "docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_AUTHORITY_BOUNDARY.md",
            "docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_RECEIPT_PLAN.md",
            "docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_NON_GOALS.md",
            "docs/mobile/M107_TO_M108_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m107_mobile_approval_renewal_ux.py",
            "tests/test_m107_gate_integration.py",
        ]
        failures = [
            f"missing M107 approval renewal UX file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                MobileApprovalRenewalUxStatus,
                build_mobile_approval_renewal_ux_report,
                validate_mobile_approval_renewal_ux_report,
            )

            report = build_mobile_approval_renewal_ux_report()
            if (
                report.status != MobileApprovalRenewalUxStatus.review_only_contract
                or not report.contract_only
                or not report.review_only
                or not report.safe_refs_required
                or not report.audit_required
                or not report.revocation_required
                or not report.consent_required
                or report.approval_capture_enabled
                or report.approval_persistence_enabled
                or report.approval_renewal_execution_enabled
                or report.approval_renewal_runtime_prompt_enabled
                or report.native_mobile_ui_enabled
                or report.control_center_control_added
                or report.backend_route_added
                or report.notification_delivery_enabled
                or report.push_trigger_enabled
                or report.background_worker_enabled
                or report.scheduler_enabled
                or report.daemon_enabled
                or report.device_token_handling_enabled
                or report.external_service_enabled
                or report.network_sync_enabled
                or report.raw_approval_payload_enabled
                or report.memory_write_enabled
                or report.context_injection_enabled
                or report.execution_enabled
                or report.production_authority_enabled
                or report.kill_switch_enabled
                or report.side_effects_performed
                or "M107_MOBILE_APPROVAL_RENEWAL_UX" not in report.reason_codes
                or "M108_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M107 approval renewal UX report is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"approval_capture_enabled": True}, "APPROVAL_CAPTURE_DENIED"),
                ({"approval_persistence_enabled": True}, "APPROVAL_PERSISTENCE_DENIED"),
                (
                    {"approval_renewal_execution_enabled": True},
                    "APPROVAL_RENEWAL_EXECUTION_DENIED",
                ),
                (
                    {"approval_renewal_runtime_prompt_enabled": True},
                    "APPROVAL_RENEWAL_RUNTIME_PROMPT_DENIED",
                ),
                ({"native_mobile_ui_enabled": True}, "NATIVE_MOBILE_UI_DENIED"),
                ({"push_trigger_enabled": True}, "PUSH_TRIGGER_DENIED"),
                ({"network_sync_enabled": True}, "NETWORK_SYNC_DENIED"),
                ({"raw_approval_payload_enabled": True}, "RAW_APPROVAL_PAYLOAD_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"kill_switch_enabled": True}, "KILL_SWITCH_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_mobile_approval_renewal_ux_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M107 unsafe report mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M107 unsafe report mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M107 approval renewal UX validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mobile approval renewal ux",
            "contract-only",
            "review-only",
            "safe refs",
            "safe renewal refs",
            "safe renewal copy refs",
            "safe renewal window refs",
            "safe expiration refs",
            "consent",
            "revocation",
            "audit",
            "no approval capture",
            "no approval persistence",
            "no approval renewal execution",
            "no runtime prompt",
            "no native mobile ui",
            "no backend route",
            "no control center control",
            "no notification delivery",
            "no push trigger",
            "no background worker",
            "no scheduler",
            "no daemon",
            "no device token handling",
            "no external service",
            "no network sync",
            "no raw approval payload",
            "no dependency",
            "no memory write",
            "no context injection",
            "no execution",
            "no kill switch execution",
            "no production authority",
            "m108 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M107 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m107_mobile_approval_renewal_ux_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "approval_capture_enabled=True",
            "approval_persistence_enabled=True",
            "approval_renewal_execution_enabled=True",
            "approval_renewal_runtime_prompt_enabled=True",
            "native_mobile_ui_enabled=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "notification_delivery_enabled=True",
            "push_trigger_enabled=True",
            "background_worker_enabled=True",
            "scheduler_enabled=True",
            "daemon_enabled=True",
            "device_token_handling_enabled=True",
            "external_service_enabled=True",
            "network_sync_enabled=True",
            "raw_approval_payload_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "production_authority_enabled=True",
            "kill_switch_enabled=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_approval_renewal_ux.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_background_read_only_status_sync.py",
            "src/ultimate_ai_agent/core/mobile_companion/background_task_contract_no_execution.py",
            "src/ultimate_ai_agent/core/mobile_companion/camera_photos_metadata_only.py",
            "src/ultimate_ai_agent/core/mobile_companion/location_sensor_off_by_default.py",
            "src/ultimate_ai_agent/core/mobile_companion/notification_planning_no_push.py",
            "src/ultimate_ai_agent/core/mobile_companion/permission_model_v1.py",
            "src/ultimate_ai_agent/core/mobile_companion/sensor_contract_review.py",
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
                            f"M107 forbidden approval renewal UX fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m107_mobile_approval_renewal_ux_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m107_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M107 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m107_roadmap_currentness(
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
            f"missing M107 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m107" not in text or "mobile approval renewal ux" not in text:
            failures.append(
                "active docs do not identify Checkpoint M107 Mobile Approval Renewal UX"
            )
        if (
            "m107 is implemented/released" not in text
            and "checkpoint m107 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M107 implemented/released")
        implemented_m108_row = (
            "| checkpoint m108 | pre-alpha checkpoint | m108 | "
            "mobile kill switch + revocation | implemented/released |"
        )
        implemented_m109_row = (
            "| checkpoint m109 | pre-alpha checkpoint | m109 | "
            "mobile sensor audit ledger | implemented/released |"
        )
        implemented_m110_row = (
            "| checkpoint m110 | pre-alpha checkpoint | m110 | "
            "mobile sensor hardening freeze | implemented/released |"
        )
        implemented_m111_row = (
            "| checkpoint m111 | pre-alpha checkpoint | m111 | "
            "production threat model | implemented/released |"
        )
        implemented_m112_row = (
            "| checkpoint m112 | pre-alpha checkpoint | m112 | "
            "user/workspace identity model | implemented/released |"
        )
        planned_rows = [
            (
                "checkpoint m110",
                "pre-alpha checkpoint",
                "m110",
                "mobile sensor hardening freeze",
            ),
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]
        if implemented_m108_row not in text:
            planned_rows.insert(
                0,
                (
                    "checkpoint m108",
                    "pre-alpha checkpoint",
                    "m108",
                    "mobile kill switch + revocation",
                ),
            )
        if implemented_m109_row not in text:
            planned_rows.insert(
                0,
                (
                    "checkpoint m109",
                    "pre-alpha checkpoint",
                    "m109",
                    "mobile sensor audit ledger",
                ),
            )
        implemented_m113_row = (
            "| checkpoint m113 | pre-alpha checkpoint | m113 | "
            "secrets boundary + credential vault contract | implemented/released |"
        )
        implemented_m114_row = (
            "| checkpoint m114 | pre-alpha checkpoint | m114 | "
            "account connector contract review | implemented/released |"
        )
        implemented_m115_row = (
            "| checkpoint m115 | pre-alpha checkpoint | m115 | "
            "production audit retention policy | implemented/released |"
        )
        implemented_m116_row = (
            "| checkpoint m116 | pre-alpha checkpoint | m116 | "
            "role-based authority model | implemented/released |"
        )
        implemented_m117_row = (
            "| checkpoint m117 | pre-alpha checkpoint | m117 | "
            "remote agent coordination contract | implemented/released |"
        )
        if implemented_m117_row in text:
            planned_rows = [
                (
                    "checkpoint m118",
                    "pre-alpha checkpoint",
                    "m118",
                    "deployment mode matrix",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m116_row in text:
            planned_rows = [
                (
                    "checkpoint m117",
                    "pre-alpha checkpoint",
                    "m117",
                    "remote agent coordination contract",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m115_row in text:
            planned_rows = [
                (
                    "checkpoint m116",
                    "pre-alpha checkpoint",
                    "m116",
                    "role-based authority model",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m114_row in text:
            planned_rows = [
                (
                    "checkpoint m115",
                    "pre-alpha checkpoint",
                    "m115",
                    "production audit retention policy",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m113_row in text:
            planned_rows = [
                (
                    "checkpoint m114",
                    "pre-alpha checkpoint",
                    "m114",
                    "account connector contract review",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m112_row in text:
            planned_rows = [
                (
                    "checkpoint m113",
                    "pre-alpha checkpoint",
                    "m113",
                    "secrets boundary + credential vault contract",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m111_row in text:
            planned_rows = [
                (
                    "checkpoint m112",
                    "pre-alpha checkpoint",
                    "m112",
                    "user/workspace identity model",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m110_row in text:
            planned_rows = [
                (
                    "checkpoint m111",
                    "pre-alpha checkpoint",
                    "m111",
                    "production threat model",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        for version_label, product_target, milestone, title in planned_rows:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M108-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = [
            "approval renewal execution is implemented",
            "approval persistence runtime is implemented",
            "approval capture runtime is implemented",
            "runtime prompt is implemented",
            "revocation execution is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ]
        if implemented_m108_row not in text:
            forbidden_fragments.extend(
                [
                    "m108 is implemented",
                    "checkpoint m108 implements m108",
                    "kill switch is implemented",
                ]
            )
        if implemented_m109_row not in text:
            forbidden_fragments.extend(
                [
                    "m109 is implemented",
                    "checkpoint m109 implements m109",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M107 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m108_mobile_kill_switch_revocation_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/mobile_kill_switch_revocation.py",
            "docs/mobile/MOBILE_KILL_SWITCH_REVOCATION.md",
            "docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_POLICY.md",
            "docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_AUTHORITY_BOUNDARY.md",
            "docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_RECEIPT_PLAN.md",
            "docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_NON_GOALS.md",
            "docs/mobile/M108_TO_M109_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m108_mobile_kill_switch_revocation.py",
            "tests/test_m108_gate_integration.py",
        ]
        failures = [
            f"missing M108 kill-switch/revocation file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                MobileKillSwitchRevocationStatus,
                build_mobile_approval_renewal_ux_report,
                build_mobile_kill_switch_revocation_record,
                validate_mobile_kill_switch_revocation_record,
            )

            source_report = build_mobile_approval_renewal_ux_report()
            record = build_mobile_kill_switch_revocation_record(
                source_report=source_report
            )
            if (
                record.status != MobileKillSwitchRevocationStatus.review_only_contract
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.device_bound
                or not record.approval_bound
                or not record.revocation_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_report_ref != source_report.report_ref
                or record.source_baseline_ref != source_report.baseline_ref
                or record.actor_ref != source_report.actor_ref
                or not record.revocation_requested
                or not record.kill_switch_requested
                or record.revocation_performed
                or record.kill_switch_activated
                or record.session_stopped
                or record.approval_revoked
                or record.notification_delivery_enabled
                or record.push_trigger_enabled
                or record.background_worker_enabled
                or record.scheduler_enabled
                or record.daemon_enabled
                or record.device_token_handling_enabled
                or record.external_service_enabled
                or record.network_sync_enabled
                or record.raw_approval_payload_enabled
                or record.memory_write_enabled
                or record.context_injection_enabled
                or record.execution_enabled
                or record.production_authority_enabled
                or record.side_effects_performed
                or "M108_MOBILE_KILL_SWITCH_REVOCATION" not in record.reason_codes
                or "M109_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M108 kill-switch/revocation record is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"revocation_performed": True}, "REVOCATION_ACTION_DENIED"),
                ({"kill_switch_activated": True}, "KILL_SWITCH_ACTIVATION_DENIED"),
                ({"session_stopped": True}, "SESSION_STOP_DENIED"),
                ({"approval_revoked": True}, "APPROVAL_REVOCATION_DENIED"),
                ({"revocation_execution_enabled": True}, "REVOCATION_EXECUTION_DENIED"),
                (
                    {"kill_switch_execution_enabled": True},
                    "KILL_SWITCH_EXECUTION_DENIED",
                ),
                ({"raw_approval_payload_enabled": True}, "RAW_APPROVAL_PAYLOAD_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_mobile_kill_switch_revocation_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M108 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M108 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M108 kill-switch/revocation validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mobile kill switch + revocation",
            "contract-only",
            "review-only",
            "safe refs",
            "safe revocation refs",
            "safe kill switch refs",
            "safe revocation reason refs",
            "safe kill switch reason refs",
            "approval renewal ux",
            "actor-bound",
            "device-bound",
            "approval-bound",
            "revocation-bound",
            "audit",
            "replay",
            "no revocation execution",
            "no kill switch execution",
            "no approval revocation",
            "no session stop",
            "no notification delivery",
            "no push trigger",
            "no background worker",
            "no scheduler",
            "no daemon",
            "no device token handling",
            "no external service",
            "no network sync",
            "no raw approval payload",
            "no dependency",
            "no memory write",
            "no context injection",
            "no execution",
            "no backend route",
            "no control center control",
            "no production authority",
            "m109 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M108 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m108_mobile_kill_switch_revocation_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "revocation_execution_enabled=True",
            "kill_switch_execution_enabled=True",
            "approval_revocation_enabled=True",
            "session_stop_enabled=True",
            "revocation_performed=True",
            "kill_switch_activated=True",
            "session_stopped=True",
            "approval_revoked=True",
            "native_mobile_ui_enabled=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "notification_delivery_enabled=True",
            "push_trigger_enabled=True",
            "background_worker_enabled=True",
            "scheduler_enabled=True",
            "daemon_enabled=True",
            "device_token_handling_enabled=True",
            "external_service_enabled=True",
            "network_sync_enabled=True",
            "raw_approval_payload_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "production_authority_enabled=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_kill_switch_revocation.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_approval_renewal_ux.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_background_read_only_status_sync.py",
            "src/ultimate_ai_agent/core/mobile_companion/background_task_contract_no_execution.py",
            "src/ultimate_ai_agent/core/mobile_companion/camera_photos_metadata_only.py",
            "src/ultimate_ai_agent/core/mobile_companion/location_sensor_off_by_default.py",
            "src/ultimate_ai_agent/core/mobile_companion/notification_planning_no_push.py",
            "src/ultimate_ai_agent/core/mobile_companion/permission_model_v1.py",
            "src/ultimate_ai_agent/core/mobile_companion/sensor_contract_review.py",
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
                            f"M108 forbidden kill-switch/revocation fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m108_mobile_kill_switch_revocation_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m108_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M108 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m108_roadmap_currentness(
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
            f"missing M108 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m108" not in text
            or "mobile kill switch + revocation" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M108 Mobile Kill Switch + Revocation"
            )
        if (
            "m108 is implemented/released" not in text
            and "checkpoint m108 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M108 implemented/released")
        implemented_m109_row = (
            "| checkpoint m109 | pre-alpha checkpoint | m109 | "
            "mobile sensor audit ledger | implemented/released |"
        )
        implemented_m110_row = (
            "| checkpoint m110 | pre-alpha checkpoint | m110 | "
            "mobile sensor hardening freeze | implemented/released |"
        )
        implemented_m111_row = (
            "| checkpoint m111 | pre-alpha checkpoint | m111 | "
            "production threat model | implemented/released |"
        )
        implemented_m112_row = (
            "| checkpoint m112 | pre-alpha checkpoint | m112 | "
            "user/workspace identity model | implemented/released |"
        )
        planned_rows = [
            (
                "checkpoint m110",
                "pre-alpha checkpoint",
                "m110",
                "mobile sensor hardening freeze",
            ),
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]
        if implemented_m109_row not in text:
            planned_rows.insert(
                0,
                (
                    "checkpoint m109",
                    "pre-alpha checkpoint",
                    "m109",
                    "mobile sensor audit ledger",
                ),
            )
        implemented_m113_row = (
            "| checkpoint m113 | pre-alpha checkpoint | m113 | "
            "secrets boundary + credential vault contract | implemented/released |"
        )
        implemented_m114_row = (
            "| checkpoint m114 | pre-alpha checkpoint | m114 | "
            "account connector contract review | implemented/released |"
        )
        implemented_m115_row = (
            "| checkpoint m115 | pre-alpha checkpoint | m115 | "
            "production audit retention policy | implemented/released |"
        )
        implemented_m116_row = (
            "| checkpoint m116 | pre-alpha checkpoint | m116 | "
            "role-based authority model | implemented/released |"
        )
        implemented_m117_row = (
            "| checkpoint m117 | pre-alpha checkpoint | m117 | "
            "remote agent coordination contract | implemented/released |"
        )
        if implemented_m117_row in text:
            planned_rows = [
                (
                    "checkpoint m118",
                    "pre-alpha checkpoint",
                    "m118",
                    "deployment mode matrix",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m116_row in text:
            planned_rows = [
                (
                    "checkpoint m117",
                    "pre-alpha checkpoint",
                    "m117",
                    "remote agent coordination contract",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m115_row in text:
            planned_rows = [
                (
                    "checkpoint m116",
                    "pre-alpha checkpoint",
                    "m116",
                    "role-based authority model",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m114_row in text:
            planned_rows = [
                (
                    "checkpoint m115",
                    "pre-alpha checkpoint",
                    "m115",
                    "production audit retention policy",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m113_row in text:
            planned_rows = [
                (
                    "checkpoint m114",
                    "pre-alpha checkpoint",
                    "m114",
                    "account connector contract review",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m112_row in text:
            planned_rows = [
                (
                    "checkpoint m113",
                    "pre-alpha checkpoint",
                    "m113",
                    "secrets boundary + credential vault contract",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m111_row in text:
            planned_rows = [
                (
                    "checkpoint m112",
                    "pre-alpha checkpoint",
                    "m112",
                    "user/workspace identity model",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        elif implemented_m110_row in text:
            planned_rows = [
                (
                    "checkpoint m111",
                    "pre-alpha checkpoint",
                    "m111",
                    "production threat model",
                ),
                ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
            ]
        for version_label, product_target, milestone, title in planned_rows:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M109-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = [
            "kill switch execution is implemented",
            "revocation execution is implemented",
            "approval revocation runtime is implemented",
            "session stop is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ]
        if implemented_m109_row not in text:
            forbidden_fragments.extend(
                [
                    "m109 is implemented",
                    "checkpoint m109 implements m109",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M108 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m109_mobile_sensor_audit_ledger_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/mobile_sensor_audit_ledger.py",
            "docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER.md",
            "docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_POLICY.md",
            "docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_AUTHORITY_BOUNDARY.md",
            "docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_RECEIPT_PLAN.md",
            "docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_NON_GOALS.md",
            "docs/mobile/M109_TO_M110_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m109_mobile_sensor_audit_ledger.py",
            "tests/test_m109_gate_integration.py",
        ]
        failures = [
            f"missing M109 sensor audit file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                MobileSensorAuditLedgerStatus,
                build_mobile_approval_renewal_ux_report,
                build_mobile_kill_switch_revocation_record,
                build_mobile_sensor_audit_ledger_record,
                validate_mobile_sensor_audit_ledger_record,
            )

            source_record = build_mobile_kill_switch_revocation_record(
                source_report=build_mobile_approval_renewal_ux_report()
            )
            record = build_mobile_sensor_audit_ledger_record(
                source_record=source_record
            )
            if (
                record.status != MobileSensorAuditLedgerStatus.review_only_contract
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.device_bound
                or not record.sensor_scope_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_record_ref != source_record.record_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or not record.sensor_audit_entries
                or record.sensor_access_performed
                or record.sensor_read_enabled
                or record.raw_sensor_payload_enabled
                or record.location_access_enabled
                or record.camera_access_enabled
                or record.photos_access_enabled
                or record.microphone_access_enabled
                or record.background_collection_enabled
                or record.background_worker_enabled
                or record.scheduler_enabled
                or record.daemon_enabled
                or record.device_token_handling_enabled
                or record.external_service_enabled
                or record.network_sync_enabled
                or record.raw_audit_payload_enabled
                or record.memory_write_enabled
                or record.context_injection_enabled
                or record.execution_enabled
                or record.production_authority_enabled
                or record.side_effects_performed
                or "M109_MOBILE_SENSOR_AUDIT_LEDGER" not in record.reason_codes
                or "M110_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M109 sensor audit ledger is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"sensor_access_performed": True}, "SENSOR_ACCESS_DENIED"),
                ({"sensor_read_enabled": True}, "SENSOR_READ_DENIED"),
                ({"raw_sensor_payload_enabled": True}, "RAW_SENSOR_PAYLOAD_DENIED"),
                ({"location_access_enabled": True}, "LOCATION_ACCESS_DENIED"),
                ({"camera_access_enabled": True}, "CAMERA_ACCESS_DENIED"),
                (
                    {"background_collection_enabled": True},
                    "BACKGROUND_COLLECTION_DENIED",
                ),
                ({"raw_audit_payload_enabled": True}, "RAW_AUDIT_PAYLOAD_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_mobile_sensor_audit_ledger_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M109 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M109 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M109 sensor audit ledger validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mobile sensor audit ledger",
            "contract-only",
            "review-only",
            "safe refs",
            "safe sensor refs",
            "safe sensor audit entry refs",
            "safe sensor scope refs",
            "mobile kill switch + revocation",
            "actor-bound",
            "device-bound",
            "sensor-scope-bound",
            "audit",
            "replay",
            "no sensor access",
            "no sensor read",
            "no raw sensor payload",
            "no location access",
            "no camera access",
            "no photos access",
            "no microphone access",
            "no background collection",
            "no background worker",
            "no scheduler",
            "no daemon",
            "no device token handling",
            "no external service",
            "no network sync",
            "no raw audit payload",
            "no dependency",
            "no memory write",
            "no context injection",
            "no execution",
            "no backend route",
            "no control center control",
            "no production authority",
            "m110 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M109 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m109_mobile_sensor_audit_ledger_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "sensor_access_enabled=True",
            "sensor_read_enabled=True",
            "raw_sensor_payload_enabled=True",
            "location_access_enabled=True",
            "camera_access_enabled=True",
            "photos_access_enabled=True",
            "microphone_access_enabled=True",
            "background_collection_enabled=True",
            "native_mobile_ui_enabled=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "notification_delivery_enabled=True",
            "push_trigger_enabled=True",
            "background_worker_enabled=True",
            "scheduler_enabled=True",
            "daemon_enabled=True",
            "device_token_handling_enabled=True",
            "external_service_enabled=True",
            "network_sync_enabled=True",
            "raw_audit_payload_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "production_authority_enabled=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_sensor_audit_ledger.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_kill_switch_revocation.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_approval_renewal_ux.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_background_read_only_status_sync.py",
            "src/ultimate_ai_agent/core/mobile_companion/background_task_contract_no_execution.py",
            "src/ultimate_ai_agent/core/mobile_companion/camera_photos_metadata_only.py",
            "src/ultimate_ai_agent/core/mobile_companion/location_sensor_off_by_default.py",
            "src/ultimate_ai_agent/core/mobile_companion/notification_planning_no_push.py",
            "src/ultimate_ai_agent/core/mobile_companion/permission_model_v1.py",
            "src/ultimate_ai_agent/core/mobile_companion/sensor_contract_review.py",
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
                            f"M109 forbidden sensor audit fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m109_mobile_sensor_audit_ledger_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m109_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M109 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
