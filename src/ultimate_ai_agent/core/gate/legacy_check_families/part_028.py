from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart028Mixin:
    """Legacy checks from m109_roadmap_currentness through m112_roadmap_currentness."""
    def check_m109_roadmap_currentness(
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
            f"missing M109 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m109" not in text or "mobile sensor audit ledger" not in text:
            failures.append(
                "active docs do not identify Checkpoint M109 Mobile Sensor Audit Ledger"
            )
        if (
            "m109 is implemented/released" not in text
            and "checkpoint m109 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M109 implemented/released")
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
                    f"active docs missing planned M110-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = [
            "sensor access is implemented",
            "sensor read is implemented",
            "raw sensor payload is implemented",
            "background collection is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ]
        if implemented_m110_row not in text:
            forbidden_fragments.extend(
                [
                    "m110 is implemented",
                    "checkpoint m110 implements m110",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M109 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m110_mobile_sensor_hardening_freeze_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/mobile_sensor_hardening_freeze.py",
            "docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE.md",
            "docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_POLICY.md",
            "docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_AUTHORITY_BOUNDARY.md",
            "docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_RECEIPT_PLAN.md",
            "docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_NON_GOALS.md",
            "docs/mobile/M110_TO_M111_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m110_mobile_sensor_hardening_freeze.py",
            "tests/test_m110_gate_integration.py",
        ]
        failures = [
            f"missing M110 sensor hardening file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                MobileSensorHardeningFreezeStatus,
                build_mobile_approval_renewal_ux_report,
                build_mobile_kill_switch_revocation_record,
                build_mobile_sensor_audit_ledger_record,
                build_mobile_sensor_hardening_freeze_record,
                validate_mobile_sensor_hardening_freeze_record,
            )

            source_record = build_mobile_sensor_audit_ledger_record(
                source_record=build_mobile_kill_switch_revocation_record(
                    source_report=build_mobile_approval_renewal_ux_report()
                )
            )
            record = build_mobile_sensor_hardening_freeze_record(
                source_record=source_record
            )
            if (
                record.status != MobileSensorHardeningFreezeStatus.freeze_only_contract
                or not record.contract_only
                or not record.review_only
                or not record.freeze_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.device_bound
                or not record.sensor_scope_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_ledger_ref != source_record.ledger_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.safe_device_ref != source_record.safe_device_ref
                or record.sensor_scope_ref != source_record.sensor_scope_ref
                or not record.accepted_checkpoint_refs
                or record.hardening_runtime_enabled
                or record.sensor_access_performed
                or record.sensor_read_enabled
                or record.raw_sensor_payload_enabled
                or record.location_access_enabled
                or record.camera_access_enabled
                or record.photos_access_enabled
                or record.microphone_access_enabled
                or record.background_collection_enabled
                or record.native_mobile_ui_enabled
                or record.notification_delivery_enabled
                or record.push_trigger_enabled
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
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.side_effects_performed
                or "M110_MOBILE_SENSOR_HARDENING_FREEZE" not in record.reason_codes
                or "M111_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M110 sensor hardening freeze is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"freeze_only": False}, "M110_FREEZE_ONLY_REQUIRED"),
                ({"hardening_runtime_enabled": True}, "HARDENING_RUNTIME_DENIED"),
                ({"sensor_access_performed": True}, "SENSOR_ACCESS_DENIED"),
                ({"sensor_read_enabled": True}, "SENSOR_READ_DENIED"),
                ({"raw_sensor_payload_enabled": True}, "RAW_SENSOR_PAYLOAD_DENIED"),
                ({"location_access_enabled": True}, "LOCATION_ACCESS_DENIED"),
                ({"camera_access_enabled": True}, "CAMERA_ACCESS_DENIED"),
                (
                    {"background_collection_enabled": True},
                    "BACKGROUND_COLLECTION_DENIED",
                ),
                ({"native_mobile_ui_enabled": True}, "NATIVE_MOBILE_UI_DENIED"),
                ({"raw_audit_payload_enabled": True}, "RAW_AUDIT_PAYLOAD_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_mobile_sensor_hardening_freeze_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M110 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M110 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M110 sensor hardening freeze validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mobile sensor hardening freeze",
            "contract-only",
            "review-only",
            "freeze-only",
            "safe refs",
            "safe sensor refs",
            "safe sensor scope refs",
            "hardening checklist refs",
            "mobile sensor audit ledger",
            "actor-bound",
            "device-bound",
            "sensor-scope-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no hardening runtime",
            "no sensor access",
            "no sensor read",
            "no raw sensor payload",
            "no location access",
            "no camera access",
            "no photos access",
            "no microphone access",
            "no background collection",
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
            "no raw audit payload",
            "no dependency",
            "no memory write",
            "no context injection",
            "no execution",
            "no production authority",
            "m111 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M110 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m110_mobile_sensor_hardening_freeze_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "hardening_runtime_enabled=True",
            "sensor_access_enabled=True",
            "sensor_access_performed=True",
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
            "dependency_added=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_sensor_hardening_freeze.py",
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
                            f"M110 forbidden sensor hardening fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m110_mobile_sensor_hardening_freeze_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m110_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M110 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m110_roadmap_currentness(
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
            f"missing M110 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m110" not in text
            or "mobile sensor hardening freeze" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M110 Mobile Sensor Hardening Freeze"
            )
        if (
            "m110 is implemented/released" not in text
            and "checkpoint m110 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M110 implemented/released")
        implemented_m111_row = (
            "| checkpoint m111 | pre-alpha checkpoint | m111 | "
            "production threat model | implemented/released |"
        )
        expected_rows = [
            (
                "checkpoint m111",
                "pre-alpha checkpoint",
                "m111",
                "production threat model",
                "implemented/released"
                if implemented_m111_row in text
                else "planned/provisional",
            ),
            (
                "v1.2.0-alpha",
                "alpha",
                "m150",
                "ultimate ai agent v1.2.0-alpha",
                "planned/provisional",
            ),
        ]
        for version_label, product_target, milestone, title, status in expected_rows:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | {status} |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M111-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = {
            "m111 is implemented",
            "checkpoint m111 implements m111",
            "production threat model is implemented",
        }
        if implemented_m111_row in text:
            forbidden_fragments = set()
        forbidden_fragments.update(
            {
                "sensor access is implemented",
                "sensor read is implemented",
                "raw sensor payload is implemented",
                "background collection is implemented",
                "production authority is implemented",
                "beta is released",
                "broad autonomy is implemented",
            }
        )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M110 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m111_production_threat_model_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/production_threat_model.py",
            "docs/production/PRODUCTION_THREAT_MODEL.md",
            "docs/production/PRODUCTION_THREAT_MODEL_POLICY.md",
            "docs/production/PRODUCTION_THREAT_MODEL_AUTHORITY_BOUNDARY.md",
            "docs/production/PRODUCTION_THREAT_MODEL_RECEIPT_PLAN.md",
            "docs/production/PRODUCTION_THREAT_MODEL_NON_GOALS.md",
            "docs/production/M111_TO_M112_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m111_production_threat_model.py",
            "tests/test_m111_gate_integration.py",
        ]
        failures = [
            f"missing M111 production threat model file: {path}"
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
                ProductionThreatModelStatus,
                build_production_threat_model_record,
                validate_production_threat_model_record,
            )

            source_record = build_mobile_sensor_hardening_freeze_record(
                source_record=build_mobile_sensor_audit_ledger_record(
                    source_record=build_mobile_kill_switch_revocation_record(
                        source_report=build_mobile_approval_renewal_ux_report()
                    )
                )
            )
            record = build_production_threat_model_record(source_record=source_record)
            if (
                record.status != ProductionThreatModelStatus.threat_model_contract
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_freeze_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_freeze_ref != source_record.freeze_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or not record.threat_surface_refs
                or not record.mitigation_plan_refs
                or "checkpoint:m110" not in record.accepted_checkpoint_refs
                or record.production_authority_enabled
                or record.production_runtime_enabled
                or record.external_distribution_enabled
                or record.deployment_enabled
                or record.credential_handling_enabled
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
                or "M111_PRODUCTION_THREAT_MODEL" not in record.reason_codes
                or "M112_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M111 production threat model is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M111_REVIEW_ONLY_REQUIRED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
                ({"production_runtime_enabled": True}, "PRODUCTION_RUNTIME_DENIED"),
                (
                    {"external_distribution_enabled": True},
                    "EXTERNAL_DISTRIBUTION_DENIED",
                ),
                ({"deployment_enabled": True}, "DEPLOYMENT_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
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
                    validate_production_threat_model_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M111 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M111 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M111 production threat model validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "production threat model",
            "contract-only",
            "review-only",
            "safe refs",
            "threat surface refs",
            "mitigation plan refs",
            "mobile sensor hardening freeze",
            "actor-bound",
            "baseline-bound",
            "source-freeze-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no production authority",
            "no production runtime",
            "no external distribution",
            "no deployment",
            "no credential handling",
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
            "m112 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M111 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m111_production_threat_model_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "production_authority_enabled=True",
            "production_runtime_enabled=True",
            "external_distribution_enabled=True",
            "deployment_enabled=True",
            "credential_handling_enabled=True",
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
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
            "src/ultimate_ai_agent/core/production_readiness/production_threat_model.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_sensor_hardening_freeze.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_sensor_audit_ledger.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_kill_switch_revocation.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_approval_renewal_ux.py",
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
                            f"M111 forbidden production threat model fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m111_production_threat_model_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m111_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M111 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m111_roadmap_currentness(
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
            f"missing M111 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m111" not in text or "production threat model" not in text:
            failures.append(
                "active docs do not identify Checkpoint M111 Production Threat Model"
            )
        if (
            "m111 is implemented/released" not in text
            and "checkpoint m111 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M111 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m112",
                "pre-alpha checkpoint",
                "m112",
                "user/workspace identity model",
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
                    f"active docs missing current M112-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "production runtime is implemented",
            "production authority is implemented",
            "credential handling is implemented",
            "deployment is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M111 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m112_user_workspace_identity_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/user_workspace_identity.py",
            "docs/production/USER_WORKSPACE_IDENTITY_MODEL.md",
            "docs/production/USER_WORKSPACE_IDENTITY_POLICY.md",
            "docs/production/USER_WORKSPACE_IDENTITY_AUTHORITY_BOUNDARY.md",
            "docs/production/USER_WORKSPACE_IDENTITY_RECEIPT_PLAN.md",
            "docs/production/USER_WORKSPACE_IDENTITY_NON_GOALS.md",
            "docs/production/M112_TO_M113_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m112_user_workspace_identity_model.py",
            "tests/test_m112_gate_integration.py",
        ]
        failures = [
            f"missing M112 user/workspace identity file: {path}"
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
                UserWorkspaceIdentityStatus,
                build_production_threat_model_record,
                build_user_workspace_identity_record,
                validate_user_workspace_identity_record,
            )

            source_record = build_production_threat_model_record(
                source_record=build_mobile_sensor_hardening_freeze_record(
                    source_record=build_mobile_sensor_audit_ledger_record(
                        source_record=build_mobile_kill_switch_revocation_record(
                            source_report=build_mobile_approval_renewal_ux_report()
                        )
                    )
                )
            )
            record = build_user_workspace_identity_record(source_record=source_record)
            if (
                record.status != UserWorkspaceIdentityStatus.identity_model_contract
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_threat_model_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_threat_model_ref != source_record.threat_model_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or not record.user_ref.startswith("user-ref:")
                or not record.workspace_ref.startswith("workspace-ref:")
                or not record.identity_boundary_refs
                or "checkpoint:m111" not in record.accepted_checkpoint_refs
                or record.production_authority_enabled
                or record.production_runtime_enabled
                or record.auth_runtime_enabled
                or record.login_enabled
                or record.session_cookie_enabled
                or record.credential_handling_enabled
                or record.persistent_identity_store_enabled
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
                or "M112_USER_WORKSPACE_IDENTITY_MODEL" not in record.reason_codes
                or "M113_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M112 user/workspace identity model is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M112_REVIEW_ONLY_REQUIRED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
                ({"production_runtime_enabled": True}, "PRODUCTION_RUNTIME_DENIED"),
                ({"auth_runtime_enabled": True}, "AUTH_RUNTIME_DENIED"),
                ({"login_enabled": True}, "LOGIN_DENIED"),
                ({"session_cookie_enabled": True}, "SESSION_COOKIE_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                (
                    {"persistent_identity_store_enabled": True},
                    "PERSISTENT_IDENTITY_STORE_DENIED",
                ),
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
                    validate_user_workspace_identity_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M112 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M112 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M112 user/workspace identity validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "user/workspace identity model",
            "contract-only",
            "review-only",
            "safe refs",
            "user refs",
            "workspace refs",
            "identity boundary refs",
            "production threat model",
            "actor-bound",
            "baseline-bound",
            "source-threat-model-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no production authority",
            "no production runtime",
            "no auth runtime",
            "no login",
            "no session cookie",
            "no credential handling",
            "no persistent identity store",
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
            "m113 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M112 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m112_user_workspace_identity_static_safety(
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
            "persistent_identity_store_enabled=True",
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
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
            "src/ultimate_ai_agent/core/production_readiness/user_workspace_identity.py",
            "src/ultimate_ai_agent/core/production_readiness/production_threat_model.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_sensor_hardening_freeze.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_sensor_audit_ledger.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_kill_switch_revocation.py",
            "src/ultimate_ai_agent/core/mobile_companion/mobile_approval_renewal_ux.py",
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
                            f"M112 forbidden user/workspace identity fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m112_user_workspace_identity_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m112_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M112 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m112_roadmap_currentness(
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
            f"missing M112 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m112" not in text or "user/workspace identity model" not in text:
            failures.append(
                "active docs do not identify Checkpoint M112 User/Workspace Identity Model"
            )
        if (
            "m112 is implemented/released" not in text
            and "checkpoint m112 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M112 implemented/released")
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
        planned_rows = [
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]
        implemented_m116_row = (
            "| checkpoint m116 | pre-alpha checkpoint | m116 | "
            "role-based authority model | implemented/released |"
        )
        implemented_m117_row = (
            "| checkpoint m117 | pre-alpha checkpoint | m117 | "
            "remote agent coordination contract | implemented/released |"
        )
        if implemented_m117_row in text:
            planned_rows.append(
                (
                    "checkpoint m118",
                    "pre-alpha checkpoint",
                    "m118",
                    "deployment mode matrix",
                )
            )
        elif implemented_m116_row in text:
            planned_rows.append(
                (
                    "checkpoint m117",
                    "pre-alpha checkpoint",
                    "m117",
                    "remote agent coordination contract",
                )
            )
        elif implemented_m115_row in text:
            planned_rows.append(
                (
                    "checkpoint m116",
                    "pre-alpha checkpoint",
                    "m116",
                    "role-based authority model",
                )
            )
        elif implemented_m114_row in text:
            planned_rows.append(
                (
                    "checkpoint m115",
                    "pre-alpha checkpoint",
                    "m115",
                    "production audit retention policy",
                )
            )
        elif implemented_m113_row in text:
            planned_rows.append(
                (
                    "checkpoint m114",
                    "pre-alpha checkpoint",
                    "m114",
                    "account connector contract review",
                )
            )
        else:
            planned_rows.append(
                (
                    "checkpoint m113",
                    "pre-alpha checkpoint",
                    "m113",
                    "secrets boundary + credential vault contract",
                )
            )
        for version_label, product_target, milestone, title in planned_rows:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M113-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "auth runtime is implemented",
            "login is implemented",
            "session cookie is implemented",
            "credential handling is implemented",
            "persistent identity store is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M112 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
