from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart026Mixin:
    """Legacy checks from m102_location_sensor_off_by_default_contracts through m106_mobile_background_read_only_status_sync_contracts."""
    def check_m102_location_sensor_off_by_default_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/location_sensor_off_by_default.py",
            "docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT.md",
            "docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_POLICY.md",
            "docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_AUTHORITY_BOUNDARY.md",
            "docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_RECEIPT_PLAN.md",
            "docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_NON_GOALS.md",
            "docs/mobile/M102_TO_M103_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m102_location_sensor_off_by_default.py",
            "tests/test_m102_gate_integration.py",
        ]
        failures = [
            f"missing M102 location sensor off-by-default file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                LocationSensorOffByDefaultStatus,
                build_location_sensor_off_by_default_report,
                validate_location_sensor_off_by_default_report,
            )

            report = build_location_sensor_off_by_default_report()
            if (
                report.status != LocationSensorOffByDefaultStatus.contract_only
                or not report.contract_only
                or not report.location_sensor_default_off
                or not report.location_permission_scope_defined
                or not report.foreground_only_review_defined
                or not report.precise_location_separate_approval_required
                or not report.consent_required
                or not report.revocation_required
                or not report.audit_required
                or report.runtime_location_access_enabled
                or report.native_permission_prompt_enabled
                or report.background_location_enabled
                or report.raw_coordinates_enabled
                or report.location_history_enabled
                or report.geofence_enabled
                or report.location_export_enabled
                or report.backend_route_added
                or report.control_center_control_added
                or report.dependency_added
                or report.memory_write_enabled
                or report.context_injection_enabled
                or report.execution_enabled
                or report.production_authority_enabled
                or report.side_effects_performed
                or "M102_LOCATION_SENSOR_OFF_BY_DEFAULT" not in report.reason_codes
                or "M103_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M102 location sensor report is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"runtime_location_access_enabled": True},
                    "RUNTIME_LOCATION_ACCESS_DENIED",
                ),
                (
                    {"native_permission_prompt_enabled": True},
                    "NATIVE_PERMISSION_PROMPT_DENIED",
                ),
                ({"background_location_enabled": True}, "BACKGROUND_LOCATION_DENIED"),
                ({"raw_coordinates_enabled": True}, "RAW_COORDINATES_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_location_sensor_off_by_default_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M102 unsafe report mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M102 unsafe report mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M102 location sensor validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "location sensor, off by default",
            "contract-only",
            "location remains off by default",
            "foreground-only review",
            "separate precise-location approval",
            "consent",
            "revocation",
            "audit",
            "no runtime location access",
            "no native permission prompt",
            "no background location",
            "no raw coordinates",
            "no location history",
            "no geofence",
            "no location export",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "m103 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M102 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m102_location_sensor_off_by_default_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "runtime_location_access_enabled=True",
            "native_permission_prompt_enabled=True",
            "background_location_enabled=True",
            "raw_coordinates_enabled=True",
            "location_history_enabled=True",
            "geofence_enabled=True",
            "location_export_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "production_authority_enabled=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
            "src/ultimate_ai_agent/core/mobile_companion/location_sensor_off_by_default.py",
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
                            f"M102 forbidden location sensor fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m102_location_sensor_off_by_default_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m102_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M102 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m102_roadmap_currentness(
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
            f"missing M102 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v1.6.0" not in text
            or "m102" not in text
            or "location sensor, off by default" not in text
        ):
            failures.append(
                "active docs do not identify v1.6.0/M102 Location Sensor, Off by Default"
            )
        if (
            "m102 is implemented/released" not in text
            and "v1.6.0 implements m102" not in text
        ):
            failures.append("active docs do not mark M102 implemented/released")
        m103_implemented = "v1.7.0" in text and "m103" in text
        m104_implemented = (
            "checkpoint m104" in text
            and "notification planning, no push execution" in text
        )
        planned_rows = [
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]
        if not m104_implemented:
            planned_rows.insert(
                0,
                (
                    "checkpoint m104",
                    "pre-alpha checkpoint",
                    "m104",
                    "notification planning, no push execution",
                ),
            )
        else:
            implemented_m104_row = (
                "| checkpoint m104 | pre-alpha checkpoint | m104 | "
                "notification planning, no push execution | implemented/released |"
            )
            if implemented_m104_row not in text:
                failures.append("active docs missing implemented Checkpoint M104 row")
        if not m103_implemented:
            planned_rows.insert(
                0,
                (
                    "v1.7.0",
                    "pre-alpha internal",
                    "m103",
                    "camera/photos metadata-only contract",
                ),
            )
        for version_label, product_target, milestone, title in planned_rows:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M103-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = [
            "camera runtime is implemented",
            "photos runtime is implemented",
            "native permission prompt is implemented",
            "background collection is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ]
        if not m103_implemented:
            forbidden_fragments.extend(
                ["m103 is implemented", "v1.7.0 implements m103"]
            )
        if not m104_implemented:
            forbidden_fragments.extend(
                ["m104 is implemented", "checkpoint m104 implements m104"]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M102 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m103_camera_photos_metadata_only_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/camera_photos_metadata_only.py",
            "docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_CONTRACT.md",
            "docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_POLICY.md",
            "docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_AUTHORITY_BOUNDARY.md",
            "docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_RECEIPT_PLAN.md",
            "docs/mobile/CAMERA_PHOTOS_METADATA_ONLY_NON_GOALS.md",
            "docs/mobile/M103_TO_M104_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m103_camera_photos_metadata_only.py",
            "tests/test_m103_gate_integration.py",
        ]
        failures = [
            f"missing M103 camera/photos metadata-only file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                CameraPhotosMetadataOnlyStatus,
                build_camera_photos_metadata_only_report,
                validate_camera_photos_metadata_only_report,
            )

            report = build_camera_photos_metadata_only_report()
            if (
                report.status != CameraPhotosMetadataOnlyStatus.contract_only
                or not report.contract_only
                or not report.metadata_only
                or not report.camera_photos_default_off
                or not report.safe_metadata_refs_required
                or not report.raw_media_denied
                or not report.consent_required
                or not report.revocation_required
                or not report.audit_required
                or report.camera_runtime_access_enabled
                or report.photo_library_runtime_access_enabled
                or report.image_capture_enabled
                or report.video_capture_enabled
                or report.raw_media_content_enabled
                or report.exif_precise_location_enabled
                or report.face_recognition_enabled
                or report.ocr_enabled
                or report.media_export_enabled
                or report.native_permission_prompt_enabled
                or report.background_media_collection_enabled
                or report.backend_route_added
                or report.control_center_control_added
                or report.dependency_added
                or report.memory_write_enabled
                or report.context_injection_enabled
                or report.execution_enabled
                or report.production_authority_enabled
                or report.side_effects_performed
                or "M103_CAMERA_PHOTOS_METADATA_ONLY" not in report.reason_codes
                or "M104_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M103 camera/photos report is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"camera_runtime_access_enabled": True},
                    "CAMERA_RUNTIME_ACCESS_DENIED",
                ),
                (
                    {"photo_library_runtime_access_enabled": True},
                    "PHOTO_LIBRARY_RUNTIME_ACCESS_DENIED",
                ),
                ({"image_capture_enabled": True}, "IMAGE_CAPTURE_DENIED"),
                ({"video_capture_enabled": True}, "VIDEO_CAPTURE_DENIED"),
                ({"raw_media_content_enabled": True}, "RAW_MEDIA_CONTENT_DENIED"),
                (
                    {"exif_precise_location_enabled": True},
                    "EXIF_PRECISE_LOCATION_DENIED",
                ),
                ({"face_recognition_enabled": True}, "FACE_RECOGNITION_DENIED"),
                ({"ocr_enabled": True}, "OCR_DENIED"),
                ({"media_export_enabled": True}, "MEDIA_EXPORT_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_camera_photos_metadata_only_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M103 unsafe report mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M103 unsafe report mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M103 camera/photos metadata validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "camera/photos metadata-only contract",
            "contract-only",
            "metadata-only",
            "safe metadata refs",
            "camera and photos remain off by default",
            "consent",
            "revocation",
            "audit",
            "no camera runtime access",
            "no photo library runtime access",
            "no image capture",
            "no video capture",
            "no raw media content",
            "no precise exif location",
            "no face recognition",
            "no ocr",
            "no media export",
            "no native permission prompt",
            "no background media collection",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "m104 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M103 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m103_camera_photos_metadata_only_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "camera_runtime_access_enabled=True",
            "photo_library_runtime_access_enabled=True",
            "image_capture_enabled=True",
            "video_capture_enabled=True",
            "raw_media_content_enabled=True",
            "raw_absolute_path_enabled=True",
            "exif_precise_location_enabled=True",
            "face_recognition_enabled=True",
            "ocr_enabled=True",
            "media_export_enabled=True",
            "native_permission_prompt_enabled=True",
            "background_media_collection_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "production_authority_enabled=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
            "src/ultimate_ai_agent/core/mobile_companion/camera_photos_metadata_only.py",
            "src/ultimate_ai_agent/core/mobile_companion/location_sensor_off_by_default.py",
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
                            f"M103 forbidden camera/photos fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m103_camera_photos_metadata_only_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m103_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M103 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m103_roadmap_currentness(
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
            f"missing M103 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v1.7.0" not in text
            or "m103" not in text
            or "camera/photos metadata-only contract" not in text
        ):
            failures.append(
                "active docs do not identify v1.7.0/M103 Camera/Photos Metadata-Only Contract"
            )
        if (
            "m103 is implemented/released" not in text
            and "v1.7.0 implements m103" not in text
        ):
            failures.append("active docs do not mark M103 implemented/released")
        implemented_m104_row = (
            "| checkpoint m104 | pre-alpha checkpoint | m104 | "
            "notification planning, no push execution | implemented/released |"
        )
        if implemented_m104_row not in text:
            failures.append("active docs missing implemented Checkpoint M104 row")
        implemented_m105_row = (
            "| checkpoint m105 | pre-alpha checkpoint | m105 | "
            "background task contract, no execution | implemented/released |"
        )
        planned_rows = [
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]
        if implemented_m105_row not in text:
            planned_rows.insert(
                0,
                (
                    "checkpoint m105",
                    "pre-alpha checkpoint",
                    "m105",
                    "background task contract, no execution",
                ),
            )
        for version_label, product_target, milestone, title in planned_rows:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M105-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "v1.7.2 implements m104",
            "push execution is implemented",
            "background task execution is implemented",
            "native permission prompt is implemented",
            "background collection is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M103 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m104_notification_planning_no_push_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/notification_planning_no_push.py",
            "docs/mobile/NOTIFICATION_PLANNING_NO_PUSH.md",
            "docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_POLICY.md",
            "docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_AUTHORITY_BOUNDARY.md",
            "docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_RECEIPT_PLAN.md",
            "docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_NON_GOALS.md",
            "docs/mobile/M104_TO_M105_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m104_notification_planning_no_push.py",
            "tests/test_m104_gate_integration.py",
        ]
        failures = [
            f"missing M104 notification planning file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                MobileNotificationPlanningStatus,
                build_mobile_notification_planning_report,
                validate_mobile_notification_planning_report,
            )

            report = build_mobile_notification_planning_report()
            if (
                report.status != MobileNotificationPlanningStatus.contract_only
                or not report.contract_only
                or not report.planning_only
                or not report.safe_refs_required
                or not report.no_push_execution
                or not report.consent_required
                or not report.revocation_required
                or not report.audit_required
                or report.push_delivery_enabled
                or report.notification_permission_prompt_enabled
                or report.notification_scheduling_enabled
                or report.background_task_execution_enabled
                or report.device_token_handling_enabled
                or report.external_push_provider_enabled
                or report.raw_notification_body_enabled
                or report.backend_route_added
                or report.control_center_control_added
                or report.dependency_added
                or report.memory_write_enabled
                or report.context_injection_enabled
                or report.execution_enabled
                or report.production_authority_enabled
                or report.side_effects_performed
                or "M104_NOTIFICATION_PLANNING_NO_PUSH" not in report.reason_codes
                or "M105_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M104 notification planning report is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"push_delivery_enabled": True}, "PUSH_DELIVERY_DENIED"),
                (
                    {"notification_permission_prompt_enabled": True},
                    "NOTIFICATION_PERMISSION_PROMPT_DENIED",
                ),
                (
                    {"notification_scheduling_enabled": True},
                    "NOTIFICATION_SCHEDULING_DENIED",
                ),
                (
                    {"background_task_execution_enabled": True},
                    "BACKGROUND_TASK_EXECUTION_DENIED",
                ),
                (
                    {"device_token_handling_enabled": True},
                    "DEVICE_TOKEN_HANDLING_DENIED",
                ),
                (
                    {"external_push_provider_enabled": True},
                    "EXTERNAL_PUSH_PROVIDER_DENIED",
                ),
                (
                    {"raw_notification_body_enabled": True},
                    "RAW_NOTIFICATION_BODY_DENIED",
                ),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_mobile_notification_planning_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M104 unsafe report mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M104 unsafe report mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M104 notification planning validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "notification planning, no push execution",
            "contract-only",
            "planning-only",
            "safe refs",
            "safe message summaries",
            "consent",
            "revocation",
            "audit",
            "no push delivery",
            "no notification permission prompt",
            "no notification scheduling",
            "no background task execution",
            "no device token handling",
            "no external push provider",
            "no raw notification body",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "m105 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M104 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m104_notification_planning_no_push_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "push_delivery_enabled=True",
            "notification_permission_prompt_enabled=True",
            "notification_scheduling_enabled=True",
            "background_task_execution_enabled=True",
            "device_token_handling_enabled=True",
            "external_push_provider_enabled=True",
            "raw_notification_body_enabled=True",
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
                            f"M104 forbidden notification fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m104_notification_planning_no_push_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m104_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M104 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m104_roadmap_currentness(
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
            f"missing M104 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m104" not in text
            or "notification planning, no push execution" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M104 Notification Planning, No Push Execution"
            )
        if (
            "m104 is implemented/released" not in text
            and "checkpoint m104 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M104 implemented/released")
        implemented_m105_row = (
            "| checkpoint m105 | pre-alpha checkpoint | m105 | "
            "background task contract, no execution | implemented/released |"
        )
        implemented_m106_row = (
            "| checkpoint m106 | pre-alpha checkpoint | m106 | "
            "mobile background read-only status sync | implemented/released |"
        )
        implemented_m107_row = (
            "| checkpoint m107 | pre-alpha checkpoint | m107 | "
            "mobile approval renewal ux | implemented/released |"
        )
        planned_rows = [
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]
        if implemented_m105_row not in text:
            planned_rows.insert(
                0,
                (
                    "checkpoint m105",
                    "pre-alpha checkpoint",
                    "m105",
                    "background task contract, no execution",
                ),
            )
        if implemented_m106_row not in text:
            planned_rows.insert(
                1,
                (
                    "checkpoint m106",
                    "pre-alpha checkpoint",
                    "m106",
                    "mobile background read-only status sync",
                ),
            )
        if implemented_m107_row not in text:
            planned_rows.insert(
                2,
                (
                    "checkpoint m107",
                    "pre-alpha checkpoint",
                    "m107",
                    "mobile approval renewal ux",
                ),
            )
        for version_label, product_target, milestone, title in planned_rows:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M105-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = [
            "checkpoint m105 implements m105",
            "background task execution is implemented",
            "push execution is implemented",
            "push delivery is implemented",
            "notification permission prompt is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ]
        if implemented_m105_row not in text:
            forbidden_fragments.append("m105 is implemented")
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M104 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m105_background_task_contract_no_execution_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/background_task_contract_no_execution.py",
            "docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION.md",
            "docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_POLICY.md",
            "docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_AUTHORITY_BOUNDARY.md",
            "docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_RECEIPT_PLAN.md",
            "docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_NON_GOALS.md",
            "docs/mobile/M105_TO_M106_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m105_background_task_contract_no_execution.py",
            "tests/test_m105_gate_integration.py",
        ]
        failures = [
            f"missing M105 background task contract file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                MobileBackgroundTaskContractStatus,
                build_mobile_background_task_contract_report,
                validate_mobile_background_task_contract_report,
            )

            report = build_mobile_background_task_contract_report()
            if (
                report.status != MobileBackgroundTaskContractStatus.contract_only
                or not report.contract_only
                or not report.planning_only
                or not report.safe_refs_required
                or not report.no_background_execution
                or not report.consent_required
                or not report.revocation_required
                or not report.audit_required
                or report.background_worker_enabled
                or report.scheduler_enabled
                or report.daemon_enabled
                or report.os_background_permission_prompt_enabled
                or report.push_trigger_enabled
                or report.device_token_handling_enabled
                or report.external_service_enabled
                or report.raw_task_payload_enabled
                or report.backend_route_added
                or report.control_center_control_added
                or report.dependency_added
                or report.memory_write_enabled
                or report.context_injection_enabled
                or report.execution_enabled
                or report.production_authority_enabled
                or report.side_effects_performed
                or "M105_BACKGROUND_TASK_CONTRACT_NO_EXECUTION"
                not in report.reason_codes
                or "M106_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M105 background task report is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                ({"scheduler_enabled": True}, "SCHEDULER_DENIED"),
                ({"daemon_enabled": True}, "DAEMON_DENIED"),
                (
                    {"os_background_permission_prompt_enabled": True},
                    "OS_BACKGROUND_PERMISSION_PROMPT_DENIED",
                ),
                ({"push_trigger_enabled": True}, "PUSH_TRIGGER_DENIED"),
                (
                    {"device_token_handling_enabled": True},
                    "DEVICE_TOKEN_HANDLING_DENIED",
                ),
                ({"external_service_enabled": True}, "EXTERNAL_SERVICE_DENIED"),
                ({"raw_task_payload_enabled": True}, "RAW_TASK_PAYLOAD_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_mobile_background_task_contract_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M105 unsafe report mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M105 unsafe report mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M105 background task contract validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "background task contract, no execution",
            "contract-only",
            "planning-only",
            "safe refs",
            "safe task summaries",
            "safe cadence refs",
            "consent",
            "revocation",
            "audit",
            "no background worker",
            "no scheduler",
            "no daemon",
            "no os background permission prompt",
            "no push trigger",
            "no device token handling",
            "no external service",
            "no raw task payload",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "m106 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M105 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m105_background_task_contract_no_execution_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "background_worker_enabled=True",
            "scheduler_enabled=True",
            "daemon_enabled=True",
            "os_background_permission_prompt_enabled=True",
            "push_trigger_enabled=True",
            "device_token_handling_enabled=True",
            "external_service_enabled=True",
            "raw_task_payload_enabled=True",
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
                            f"M105 forbidden background task fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m105_background_task_contract_no_execution_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m105_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M105 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m105_roadmap_currentness(
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
            f"missing M105 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m105" not in text
            or "background task contract, no execution" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M105 Background Task Contract, No Execution"
            )
        if (
            "m105 is implemented/released" not in text
            and "checkpoint m105 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M105 implemented/released")
        implemented_m106_row = (
            "| checkpoint m106 | pre-alpha checkpoint | m106 | "
            "mobile background read-only status sync | implemented/released |"
        )
        implemented_m107_row = (
            "| checkpoint m107 | pre-alpha checkpoint | m107 | "
            "mobile approval renewal ux | implemented/released |"
        )
        planned_rows = [
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]
        if implemented_m106_row not in text:
            planned_rows.insert(
                0,
                (
                    "checkpoint m106",
                    "pre-alpha checkpoint",
                    "m106",
                    "mobile background read-only status sync",
                ),
            )
        if implemented_m107_row not in text:
            planned_rows.insert(
                1,
                (
                    "checkpoint m107",
                    "pre-alpha checkpoint",
                    "m107",
                    "mobile approval renewal ux",
                ),
            )
        for version_label, product_target, milestone, title in planned_rows:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M106-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = {
            "background task execution is implemented",
            "background worker is implemented",
            "scheduler is implemented",
            "daemon is implemented",
            "push trigger is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        }
        if implemented_m106_row not in text:
            forbidden_fragments.add("m106 is implemented")
            forbidden_fragments.add("checkpoint m106 implements m106")
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M105 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m106_mobile_background_read_only_status_sync_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/mobile_background_read_only_status_sync.py",
            "docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC.md",
            "docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_POLICY.md",
            "docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_AUTHORITY_BOUNDARY.md",
            "docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_RECEIPT_PLAN.md",
            "docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_NON_GOALS.md",
            "docs/mobile/M106_TO_M107_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m106_mobile_background_read_only_status_sync.py",
            "tests/test_m106_gate_integration.py",
        ]
        failures = [
            f"missing M106 background status sync file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                MobileBackgroundStatusSyncStatus,
                build_mobile_background_read_only_status_sync_report,
                validate_mobile_background_status_sync_report,
            )

            report = build_mobile_background_read_only_status_sync_report()
            if (
                report.status != MobileBackgroundStatusSyncStatus.read_only_contract
                or not report.contract_only
                or not report.read_only
                or not report.safe_refs_required
                or not report.no_background_collection
                or not report.no_background_execution
                or not report.audit_required
                or report.background_worker_enabled
                or report.scheduler_enabled
                or report.daemon_enabled
                or report.os_background_fetch_enabled
                or report.os_background_permission_prompt_enabled
                or report.push_trigger_enabled
                or report.device_token_handling_enabled
                or report.external_service_enabled
                or report.network_sync_enabled
                or report.raw_status_payload_enabled
                or report.backend_route_added
                or report.control_center_control_added
                or report.dependency_added
                or report.memory_write_enabled
                or report.context_injection_enabled
                or report.execution_enabled
                or report.production_authority_enabled
                or report.side_effects_performed
                or "M106_MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC"
                not in report.reason_codes
                or "M107_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M106 background status sync report is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                ({"scheduler_enabled": True}, "SCHEDULER_DENIED"),
                ({"daemon_enabled": True}, "DAEMON_DENIED"),
                ({"os_background_fetch_enabled": True}, "OS_BACKGROUND_FETCH_DENIED"),
                ({"push_trigger_enabled": True}, "PUSH_TRIGGER_DENIED"),
                ({"network_sync_enabled": True}, "NETWORK_SYNC_DENIED"),
                ({"raw_status_payload_enabled": True}, "RAW_STATUS_PAYLOAD_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_mobile_background_status_sync_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M106 unsafe report mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M106 unsafe report mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M106 background status sync validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mobile background read-only status sync",
            "contract-only",
            "read-only",
            "safe refs",
            "safe status refs",
            "safe status summaries",
            "safe observed-at refs",
            "audit",
            "no background collection",
            "no background execution",
            "no background worker",
            "no scheduler",
            "no daemon",
            "no os background fetch",
            "no os background permission prompt",
            "no push trigger",
            "no device token handling",
            "no external service",
            "no network sync",
            "no raw status payload",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "m107 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M106 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)
