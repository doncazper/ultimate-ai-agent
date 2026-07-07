from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart011Mixin:
    """Legacy checks from m45_mobile_route_boundary through m50_mobile_audit_route_boundary."""
    def check_m45_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m45_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M45 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m45_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M45 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.49.0" not in text
            or "m45" not in text
            or "ccc ios local read-only connection" not in text
        ):
            failures.append(
                "active docs do not identify v0.49.0/M45 CCC iOS Local Read-Only Connection"
            )
        if (
            "m45 is implemented/released" not in text
            and "v0.49.0 implements m45" not in text
        ):
            failures.append("active docs do not mark M45 implemented/released")
        current = self._active_version_tuple()
        if current >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif current >= (0, 50, 0):
            if "m47-m60 remain planned/provisional" not in text:
                failures.append("M47-M60 must remain planned/provisional after M46")
        elif "m46-m60 remain planned/provisional" not in text:
            failures.append("M46-M60 must remain planned/provisional after M45")
        forbidden_fragments: list[str] = []
        if current < (0, 50, 0):
            forbidden_fragments.extend(
                [
                    "m46 is implemented",
                    "v0.50.0 implements m46",
                    "review/receipt read-only surfaces are implemented",
                ]
            )
        forbidden_fragments.extend(
            [
                "testflight pipeline is implemented",
                "mobile sensors are implemented",
                "approval execution is implemented",
                "production authority is implemented",
            ]
        )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M45 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m46_ccc_ios_review_receipt_read_only_surfaces(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/ReviewReceiptReadOnlyModels.swift",
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/CCC_IOS_REVIEW_RECEIPT_READ_ONLY_SURFACES.md",
            "docs/mobile/M46_TO_M47_BOUNDARY.md",
            "tests/test_m46_ccc_ios_review_receipt_read_only_surfaces.py",
        ]
        failures = [
            f"missing M46 review/receipt file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_ccc_ios_review_receipt_read_only_surfaces_safe,
                build_default_ccc_ios_review_receipt_read_only_surface_manifest,
            )

            manifest = build_default_ccc_ios_review_receipt_read_only_surface_manifest()
            assert_ccc_ios_review_receipt_read_only_surfaces_safe(manifest)
        except Exception as exc:
            failures.append(f"M46 review/receipt surface validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "ios review/receipt read-only surfaces",
            "source-only",
            "read-only",
            "redacted summary",
            "mock",
            "non-authoritative",
            "no runtime network call",
            "no backend route",
            "no approval capture",
            "no approval execution",
            "no raw data",
            "no context injection",
            "no memory write",
            "no file mutation",
            "no export",
            "no execution",
            "no background collection",
            "no mobile sensor access",
            "no credential",
            "no production authority",
            "m47 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M46 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m46_ios_review_receipt_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        ios_root = self.root / "apps" / "ccc-ios"
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        failures: List[str] = []
        if not swift_root.exists():
            failures.append("M46 Swift source root missing")
            return self._result(
                criterion, failures, [str(swift_root.relative_to(self.root))]
            )
        for forbidden_path in [
            ios_root / "Package.swift",
            *ios_root.glob("*.xcodeproj"),
            *ios_root.rglob("*.entitlements"),
            *ios_root.rglob("Info.plist"),
            *ios_root.rglob("ExportOptions.plist"),
            *ios_root.rglob("*.mobileprovision"),
        ]:
            if forbidden_path.exists():
                failures.append(
                    f"M46 forbidden native workflow file present: {forbidden_path.relative_to(self.root)}"
                )
        swift_files = sorted(swift_root.rglob("*.swift"))
        if not swift_files:
            failures.append("M46 Swift source files missing")
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M46_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(f"M46 forbidden Swift API fragment present: {fragment}")
        lowered = swift_text.lower()
        for required in [
            "review/receipt read-only surfaces",
            "redacted review packet summary",
            "redacted receipt summary",
            "mock non-authoritative",
            "no approval capture",
            "no raw data",
            "no runtime network call",
        ]:
            if required not in lowered:
                failures.append(f"M46 Swift source missing required marker: {required}")
        return self._result(
            criterion,
            failures,
            [path.relative_to(self.root).as_posix() for path in swift_files],
        )

    def check_m46_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m46_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M46 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m46_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M46 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.50.0" not in text
            or "m46" not in text
            or "ios review/receipt read-only surfaces" not in text
        ):
            failures.append(
                "active docs do not identify v0.50.0/M46 iOS Review/Receipt Read-Only Surfaces"
            )
        if (
            "m46 is implemented/released" not in text
            and "v0.50.0 implements m46" not in text
        ):
            failures.append("active docs do not mark M46 implemented/released")
        current_tuple = self._active_version_tuple()
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current_tuple >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif "m47-m60 remain planned/provisional" not in text:
            failures.append("M47-M60 must remain planned/provisional after M46")
        forbidden_fragments = [
            "testflight pipeline is implemented",
            "mobile approval capture is implemented",
            "mobile sensors are implemented",
            "background collection is implemented",
            "production authority is implemented",
        ]
        if current_tuple < (0, 51, 0):
            forbidden_fragments.extend(["m47 is implemented", "v0.51.0 implements m47"])
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M46 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m47_internal_testflight_pipeline_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/TESTFLIGHT_PIPELINE_INTERNAL_ONLY.md",
            "docs/mobile/M47_TO_M48_BOUNDARY.md",
            "tests/test_m47_testflight_pipeline_internal_only.py",
        ]
        failures = [
            f"missing M47 TestFlight pipeline file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_internal_testflight_pipeline_safe,
                build_default_internal_testflight_pipeline_manifest,
            )

            manifest = build_default_internal_testflight_pipeline_manifest()
            assert_internal_testflight_pipeline_safe(manifest)
        except Exception as exc:
            failures.append(f"M47 TestFlight pipeline validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "testflight pipeline, internal only",
            "internal-only",
            "contract",
            "checklist",
            "no build execution",
            "no upload execution",
            "no signing asset storage",
            "no app store connect api",
            "no external beta",
            "no public distribution",
            "no production authority",
            "m48 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M47 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m47_testflight_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        ios_root = self.root / "apps" / "ccc-ios"
        failures: List[str] = []
        forbidden_paths = [
            ios_root / "Package.swift",
            *ios_root.glob("*.xcodeproj"),
            *ios_root.rglob("*.xcworkspace"),
            *ios_root.rglob("*.entitlements"),
            *ios_root.rglob("Info.plist"),
            *ios_root.rglob("ExportOptions.plist"),
            *ios_root.rglob("*.mobileprovision"),
            *ios_root.rglob("*.p8"),
            *ios_root.rglob("*.cer"),
            *ios_root.rglob("*.p12"),
        ]
        if (self.root / ".github").exists():
            forbidden_paths.extend((self.root / ".github").rglob("*testflight*"))
        for forbidden_path in forbidden_paths:
            if forbidden_path.exists():
                failures.append(
                    f"M47 forbidden pipeline artifact present: {forbidden_path.relative_to(self.root)}"
                )
        for forbidden_dir in [
            self.root / "fastlane",
            ios_root / "fastlane",
            ios_root / "DerivedData",
        ]:
            if forbidden_dir.exists():
                failures.append(
                    f"M47 forbidden build/upload directory present: {forbidden_dir.relative_to(self.root)}"
                )
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        swift_files = sorted(swift_root.rglob("*.swift")) if swift_root.exists() else []
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M47_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(
                    f"M47 forbidden Swift pipeline fragment present: {fragment}"
                )
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            ios_root,
        ]
        enabled = "{}=True".format
        forbidden_source_fragments = [
            enabled("build_execution_enabled"),
            enabled("upload_execution_enabled"),
            enabled("signing_asset_storage_enabled"),
            enabled("signing_identity_configured"),
            enabled("provisioning_profile_configured"),
            enabled("app_store_connect_api_enabled"),
            enabled("credentials_or_cookies_handling_enabled"),
            enabled("external_beta_enabled"),
            enabled("public_distribution_enabled"),
            enabled("production_authority_enabled"),
            enabled("mobile_sensor_access_enabled"),
            enabled("background_collection_enabled"),
            enabled("approval_execution_enabled"),
            enabled("context_injection_enabled"),
            enabled("memory_write_enabled"),
            enabled("executes_build"),
            enabled("uploads_build"),
            enabled("calls_app_store_connect"),
        ]
        for root in source_roots:
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
                if _is_static_safety_scan_allowed_file(rel, ()):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M47 forbidden enabled flag in {rel}: {fragment}"
                        )
        return self._result(
            criterion,
            failures,
            [path.relative_to(self.root).as_posix() for path in swift_files],
        )

    def check_m47_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m47_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M47 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m47_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M47 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.51.0" not in text
            or "m47" not in text
            or "testflight pipeline, internal only" not in text
        ):
            failures.append(
                "active docs do not identify v0.51.0/M47 TestFlight Pipeline, Internal Only"
            )
        if (
            "m47 is implemented/released" not in text
            and "v0.51.0 implements m47" not in text
        ):
            failures.append("active docs do not mark M47 implemented/released")
        current_tuple = self._active_version_tuple()
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif "m48-m60 remain planned/provisional" not in text:
            failures.append("M48-M60 must remain planned/provisional after M47")
        forbidden_fragments = [
            "mobile approval capture is implemented",
            "mobile sensors are implemented",
            "production authority is implemented",
        ]
        if current_tuple < (0, 52, 0):
            forbidden_fragments.extend(
                [
                    "m48 is implemented",
                    "v0.52.0 implements m48",
                    "first internal testflight build is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M47 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m48_first_internal_testflight_build_candidate(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/FIRST_INTERNAL_TESTFLIGHT_BUILD.md",
            "docs/mobile/M48_TO_M49_BOUNDARY.md",
            "tests/test_m48_first_internal_testflight_build.py",
        ]
        failures = [
            f"missing M48 first internal TestFlight build file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_first_internal_testflight_build_candidate_safe,
                build_default_first_internal_testflight_build_candidate,
            )

            candidate = build_default_first_internal_testflight_build_candidate()
            assert_first_internal_testflight_build_candidate_safe(candidate)
        except Exception as exc:
            failures.append(
                f"M48 first internal TestFlight build candidate validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "first internal testflight build",
            "build candidate",
            "review-only",
            "internal-only",
            "no committed build artifact",
            "no ipa",
            "no signing material",
            "no app store connect",
            "no testflight upload",
            "no external beta",
            "no production authority",
            "m49 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M48 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m48_testflight_build_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        ios_root = self.root / "apps" / "ccc-ios"
        failures: List[str] = []
        forbidden_paths = [
            ios_root / "Package.swift",
            *ios_root.glob("*.xcodeproj"),
            *ios_root.rglob("*.xcworkspace"),
            *ios_root.rglob("*.entitlements"),
            *ios_root.rglob("Info.plist"),
            *ios_root.rglob("ExportOptions.plist"),
            *ios_root.rglob("*.xcarchive"),
            *ios_root.rglob("*.ipa"),
            *ios_root.rglob("*.mobileprovision"),
            *ios_root.rglob("*.p8"),
            *ios_root.rglob("*.cer"),
            *ios_root.rglob("*.p12"),
        ]
        if (self.root / ".github").exists():
            forbidden_paths.extend((self.root / ".github").rglob("*testflight*"))
            forbidden_paths.extend((self.root / ".github").rglob("*app-store-connect*"))
        for forbidden_path in forbidden_paths:
            if forbidden_path.exists():
                failures.append(
                    f"M48 forbidden build/signing artifact present: {forbidden_path.relative_to(self.root)}"
                )
        for forbidden_dir in [
            self.root / "fastlane",
            ios_root / "fastlane",
            ios_root / "DerivedData",
            ios_root / "Archives",
            ios_root / "build",
            ios_root / "dist",
        ]:
            if forbidden_dir.exists():
                failures.append(
                    f"M48 forbidden build/upload directory present: {forbidden_dir.relative_to(self.root)}"
                )
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        swift_files = sorted(swift_root.rglob("*.swift")) if swift_root.exists() else []
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M48_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(
                    f"M48 forbidden Swift build fragment present: {fragment}"
                )
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            ios_root,
        ]
        enabled = "{}=True".format
        forbidden_source_fragments = [
            enabled("build_execution_performed"),
            enabled("archive_created_in_repo"),
            enabled("ipa_created_in_repo"),
            enabled("testflight_upload_performed"),
            enabled("app_store_connect_api_called"),
            enabled("signing_asset_storage_enabled"),
            enabled("signing_identity_material_stored"),
            enabled("provisioning_profile_material_stored"),
            enabled("certificate_or_private_key_stored"),
            enabled("fastlane_workflow_enabled"),
            enabled("ci_upload_workflow_enabled"),
            enabled("external_beta_enabled"),
            enabled("public_distribution_enabled"),
            enabled("production_authority_enabled"),
            enabled("mobile_sensor_access_enabled"),
            enabled("background_collection_enabled"),
            enabled("approval_execution_enabled"),
            enabled("context_injection_enabled"),
            enabled("memory_write_enabled"),
            enabled("raw_data_export_enabled"),
            enabled("export_enabled"),
            enabled("execution_enabled"),
        ]
        for root in source_roots:
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
                if _is_static_safety_scan_allowed_file(
                    rel,
                    {
                        "tests/test_m48_first_internal_testflight_build.py",
                        "tests/test_m48_gate_integration.py",
                    },
                ):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M48 forbidden enabled flag in {rel}: {fragment}"
                        )
        return self._result(
            criterion,
            failures,
            [path.relative_to(self.root).as_posix() for path in swift_files],
        )

    def check_m48_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m48_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M48 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m48_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M48 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.52.0" not in text
            or "m48" not in text
            or "first internal testflight build" not in text
        ):
            failures.append(
                "active docs do not identify v0.52.0/M48 First Internal TestFlight Build"
            )
        if (
            "m48 is implemented/released" not in text
            and "v0.52.0 implements m48" not in text
        ):
            failures.append("active docs do not mark M48 implemented/released")
        self._append_post_m48_mobile_status_failures(text, failures)
        forbidden_fragments = [
            "mobile approval execution is implemented",
            "mobile sensors are implemented",
            "external beta is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 53, 0):
            forbidden_fragments.extend(
                [
                    "m49 is implemented",
                    "v0.53.0 implements m49",
                    "mobile review approval capture is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M48 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m49_mobile_review_approval_capture(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/MOBILE_REVIEW_APPROVAL_CAPTURE.md",
            "docs/mobile/M49_TO_M50_BOUNDARY.md",
            "tests/test_m49_mobile_review_approval_capture.py",
        ]
        failures = [
            f"missing M49 mobile review approval capture file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from datetime import timedelta

            from ultimate_ai_agent.core.mobile_companion import (
                MobileReviewApprovalCaptureDecisionStatus,
                MobileReviewApprovalDecisionKind,
                MobileReviewApprovalCaptureRequest,
                capture_mobile_review_approval,
            )
            from ultimate_ai_agent.core.time import utc_now

            now = utc_now()
            request = MobileReviewApprovalCaptureRequest(
                approval_ref="mobile-review-approval-capture:gate",
                actor_ref="user:foundation-gate-mobile-reviewer",
                mobile_surface_ref="ccc-ios-review-surface:gate",
                review_packet_ref="file-review-packet:gate-mobile-review",
                preview_result_ref="redacted-file-preview-output:gate-mobile-review",
                redaction_summary_ref="file-review-redaction-summary:gate-mobile-review",
                file_ref="file-ref:gate-mobile-review",
                safe_path_ref="filesystem-preview-path:safe-root_mobile/gate/review.md",
                receipt_plan_ref="mobile-review-receipt-plan:gate-mobile-review",
                decision=MobileReviewApprovalDecisionKind.approve_review_only,
                idempotency_key="mobile-review-approval-idempotency:gate-mobile-review",
                expected_actor_ref="user:foundation-gate-mobile-reviewer",
                expected_mobile_surface_ref="ccc-ios-review-surface:gate",
                expected_review_packet_ref="file-review-packet:gate-mobile-review",
                expected_preview_result_ref="redacted-file-preview-output:gate-mobile-review",
                expected_redaction_summary_ref="file-review-redaction-summary:gate-mobile-review",
                expected_file_ref="file-ref:gate-mobile-review",
                expected_safe_path_ref="filesystem-preview-path:safe-root_mobile/gate/review.md",
                expires_at=now + timedelta(minutes=5),
            )
            decision = capture_mobile_review_approval(request, current_time=now)
            if (
                decision.status
                != MobileReviewApprovalCaptureDecisionStatus.approved_for_mobile_review_only
            ):
                failures.append(
                    "M49 safe mobile review approval capture did not produce review-only approval"
                )
            if (
                not decision.captured
                or not decision.persisted
                or not decision.review_only
            ):
                failures.append(
                    "M49 safe mobile review approval capture was not captured/persisted as review-only"
                )
            for field_name in [
                "raw_file_access_authorized",
                "context_proposal_authorized",
                "context_injection_authorized",
                "memory_write_authorized",
                "export_authorized",
                "execution_authorized",
                "execution_performed",
            ]:
                if getattr(decision, field_name):
                    failures.append(
                        f"M49 decision granted forbidden authority: {field_name}"
                    )

            unsafe = capture_mobile_review_approval(
                request.model_copy(update={"raw_content_enabled": True}),
                current_time=now,
            )
            if unsafe.status != MobileReviewApprovalCaptureDecisionStatus.rejected:
                failures.append("M49 model_copy raw-content mutation was not rejected")
            if (
                "MOBILE_REVIEW_APPROVAL_CAPTURE_RAW_CONTENT_DENIED"
                not in unsafe.reason_codes
            ):
                failures.append("M49 model_copy raw-content rejection reason missing")

            test_ref = capture_mobile_review_approval(
                request.model_copy(update={"approval_ref": "approval_test_m49_gate"}),
                current_time=now,
            )
            if test_ref.status != MobileReviewApprovalCaptureDecisionStatus.rejected:
                failures.append("M49 approval_test_ ref was not rejected")
        except Exception as exc:
            failures.append(
                f"M49 mobile review approval capture validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mobile review approval capture",
            "review-only",
            "exact-scope",
            "actor-bound",
            "resource-bound",
            "replay-safe",
            "revocable",
            "safe refs only",
            "no raw file access",
            "no context proposal",
            "no context injection",
            "no memory write",
            "no export",
            "no execution",
            "no mobile sensor access",
            "no background collection",
            "m50 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M49 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m49_mobile_approval_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        ios_root = self.root / "apps" / "ccc-ios"
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        swift_files = sorted(swift_root.rglob("*.swift")) if swift_root.exists() else []
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M49_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(
                    f"M49 forbidden Swift approval/sensor fragment present: {fragment}"
                )

        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            ios_root,
        ]
        enabled = "{}=True".format
        forbidden_source_fragments = [
            enabled("raw_file_access_enabled"),
            enabled("raw_content_enabled"),
            enabled("full_file_content_enabled"),
            enabled("unredacted_preview_enabled"),
            enabled("context_proposal_enabled"),
            enabled("context_injection_enabled"),
            enabled("memory_write_enabled"),
            enabled("export_enabled"),
            enabled("execution_enabled"),
            enabled("approval_execution_enabled"),
            enabled("mobile_sensor_access_enabled"),
            enabled("background_collection_enabled"),
            "/mobile/review/approvals/capture",
            "/mobile/review/approvals/execute",
            "/mobile/context/inject",
            "/mobile/memory/write",
            "/mobile/tools/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
            "tests/test_m49_mobile_review_approval_capture.py",
            "tests/test_m49_gate_integration.py",
        }
        for root in source_roots:
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
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M49 forbidden authority/route fragment in {rel}: {fragment}"
                        )
        return self._result(
            criterion,
            failures,
            [path.relative_to(self.root).as_posix() for path in swift_files],
        )

    def check_m49_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m49_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M49 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m49_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M49 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.53.0" not in text
            or "m49" not in text
            or "mobile review approval capture" not in text
        ):
            failures.append(
                "active docs do not identify v0.53.0/M49 Mobile Review Approval Capture"
            )
        if (
            "m49 is implemented/released" not in text
            and "v0.53.0 implements m49" not in text
        ):
            failures.append("active docs do not mark M49 implemented/released")
        if self._active_version_tuple() >= (0, 57, 0):
            if (
                "m50 is implemented/released" not in text
                and "v0.54.0 implements m50" not in text
            ):
                failures.append("M50 must be implemented/released after v0.54.0")
            if (
                "m51 is implemented/released" not in text
                and "v0.55.0 implements m51" not in text
            ):
                failures.append("M51 must be implemented/released after v0.55.0")
            if (
                "m52 is implemented/released" not in text
                and "v0.56.0 implements m52" not in text
            ):
                failures.append("M52 must be implemented/released after v0.56.0")
            if (
                "m53 is implemented/released" not in text
                and "v0.57.0 implements m53" not in text
            ):
                failures.append("M53 must be implemented/released after v0.57.0")
            if (
                "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M54-M60 must remain planned/provisional after M53")
        elif self._active_version_tuple() >= (0, 56, 0):
            if (
                "m50 is implemented/released" not in text
                and "v0.54.0 implements m50" not in text
            ):
                failures.append("M50 must be implemented/released after v0.54.0")
            if (
                "m51 is implemented/released" not in text
                and "v0.55.0 implements m51" not in text
            ):
                failures.append("M51 must be implemented/released after v0.55.0")
            if (
                "m52 is implemented/released" not in text
                and "v0.56.0 implements m52" not in text
            ):
                failures.append("M52 must be implemented/released after v0.56.0")
            if "m53-m60 remain planned/provisional" not in text:
                failures.append("M53-M60 must remain planned/provisional after M52")
        elif self._active_version_tuple() >= (0, 55, 0):
            if (
                "m50 is implemented/released" not in text
                and "v0.54.0 implements m50" not in text
            ):
                failures.append("M50 must be implemented/released after v0.54.0")
            if (
                "m51 is implemented/released" not in text
                and "v0.55.0 implements m51" not in text
            ):
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52-m60 remain planned/provisional" not in text:
                failures.append("M52-M60 must remain planned/provisional after M51")
        elif self._active_version_tuple() >= (0, 54, 0):
            if (
                "m50 is implemented/released" not in text
                and "v0.54.0 implements m50" not in text
            ):
                failures.append("M50 must be implemented/released after v0.54.0")
            if "m51-m60 remain planned/provisional" not in text:
                failures.append("M51-M60 must remain planned/provisional after M50")
        elif "m50-m60 remain planned/provisional" not in text:
            failures.append("M50-M60 must remain planned/provisional after M49")
        forbidden_fragments = [
            "mobile approval execution is implemented",
            "mobile sensors are implemented",
            "context injection is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 54, 0):
            forbidden_fragments.extend(
                [
                    "m50 is implemented",
                    "v0.54.0 implements m50",
                    "mobile approval audit hardening is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M49 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m50_mobile_approval_audit_hardening(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/MOBILE_APPROVAL_AUDIT_HARDENING.md",
            "docs/mobile/M50_TO_M51_BOUNDARY.md",
            "tests/test_m50_mobile_approval_audit_hardening.py",
        ]
        failures = [
            f"missing M50 mobile approval audit file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from datetime import timedelta

            from ultimate_ai_agent.core.mobile_companion import (
                MobileApprovalAuditStatus,
                MobileReviewApprovalDecisionKind,
                MobileReviewApprovalCaptureRequest,
                MobileReviewApprovalStore,
                audit_mobile_review_approval_records,
                audit_mobile_review_approval_store,
                capture_mobile_review_approval,
            )
            from ultimate_ai_agent.core.time import utc_now

            now = utc_now()
            request = MobileReviewApprovalCaptureRequest(
                approval_ref="mobile-review-approval-capture:m50-gate",
                actor_ref="user:m50-mobile-reviewer",
                mobile_surface_ref="ccc-ios-review-surface:m50-gate",
                review_packet_ref="file-review-packet:m50-mobile-review",
                preview_result_ref="redacted-file-preview-output:m50-mobile-review",
                redaction_summary_ref="file-review-redaction-summary:m50-mobile-review",
                file_ref="file-ref:m50-mobile-review",
                safe_path_ref="filesystem-preview-path:safe-root_mobile/m50/review.md",
                receipt_plan_ref="mobile-review-receipt-plan:m50-mobile-review",
                decision=MobileReviewApprovalDecisionKind.approve_review_only,
                idempotency_key="mobile-review-approval-idempotency:m50-mobile-review",
                expected_actor_ref="user:m50-mobile-reviewer",
                expected_mobile_surface_ref="ccc-ios-review-surface:m50-gate",
                expected_review_packet_ref="file-review-packet:m50-mobile-review",
                expected_preview_result_ref="redacted-file-preview-output:m50-mobile-review",
                expected_redaction_summary_ref="file-review-redaction-summary:m50-mobile-review",
                expected_file_ref="file-ref:m50-mobile-review",
                expected_safe_path_ref="filesystem-preview-path:safe-root_mobile/m50/review.md",
                expires_at=now + timedelta(minutes=5),
            )
            store = MobileReviewApprovalStore()
            decision = capture_mobile_review_approval(
                request, store=store, current_time=now
            )
            if decision.record is None:
                failures.append("M50 setup capture did not produce a safe record")
            safe_report = audit_mobile_review_approval_store(store)
            if safe_report.status != MobileApprovalAuditStatus.passed:
                failures.append(
                    f"M50 safe audit report did not pass: {safe_report.reason_codes}"
                )
            if safe_report.record_count != 1 or not safe_report.review_only:
                failures.append(
                    "M50 safe audit report did not remain review-only over one record"
                )
            for field_name in [
                "memory_write_performed",
                "export_performed",
                "execution_performed",
            ]:
                if getattr(safe_report, field_name):
                    failures.append(
                        f"M50 audit report performed forbidden effect: {field_name}"
                    )
            if decision.record is not None:
                raw_report = audit_mobile_review_approval_records(
                    [
                        decision.record.model_copy(
                            update={"raw_content": "secret raw mobile audit"}
                        )
                    ]
                )
                if raw_report.status != MobileApprovalAuditStatus.failed:
                    failures.append(
                        "M50 model_copy raw record was not rejected by audit"
                    )
                if (
                    "MOBILE_APPROVAL_AUDIT_RAW_CONTENT_DENIED"
                    not in raw_report.reason_codes
                ):
                    failures.append("M50 raw audit rejection reason missing")
                unsafe_report = audit_mobile_review_approval_records(
                    [decision.record.model_copy(update={"execution_enabled": True})]
                )
                if unsafe_report.status != MobileApprovalAuditStatus.failed:
                    failures.append(
                        "M50 model_copy execution record was not rejected by audit"
                    )
                if (
                    "MOBILE_APPROVAL_AUDIT_EXECUTION_DENIED"
                    not in unsafe_report.reason_codes
                ):
                    failures.append("M50 execution audit rejection reason missing")
        except Exception as exc:
            failures.append(f"M50 mobile approval audit validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mobile approval audit hardening",
            "review-only",
            "safe-ref-only",
            "model_copy",
            "no raw content",
            "no context injection",
            "no memory write",
            "no export",
            "no execution",
            "no mobile sensor access",
            "no backend route",
            "m51 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M50 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m50_mobile_audit_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        ios_root = self.root / "apps" / "ccc-ios"
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        swift_files = sorted(swift_root.rglob("*.swift")) if swift_root.exists() else []
        swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
        for fragment in M50_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(
                    f"M50 forbidden Swift audit/authority fragment present: {fragment}"
                )

        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            ios_root,
        ]
        enabled = "{}=True".format
        forbidden_source_fragments = [
            enabled("raw_file_access_enabled"),
            enabled("raw_content_enabled"),
            enabled("full_file_content_enabled"),
            enabled("unredacted_preview_enabled"),
            enabled("context_proposal_enabled"),
            enabled("context_injection_enabled"),
            enabled("memory_write_enabled"),
            enabled("export_enabled"),
            enabled("execution_enabled"),
            enabled("approval_execution_enabled"),
            enabled("mobile_sensor_access_enabled"),
            enabled("background_collection_enabled"),
            "/mobile/review/audit",
            "/mobile/review/audit/export",
            "/mobile/review/audit/raw",
            "/mobile/approvals/audit/write",
            "/mobile/context/inject",
            "/mobile/memory/write",
            "/mobile/tools/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
            "tests/test_m49_mobile_review_approval_capture.py",
            "tests/test_m49_gate_integration.py",
            "tests/test_m50_mobile_approval_audit_hardening.py",
            "tests/test_m50_gate_integration.py",
        }
        for root in source_roots:
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
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M50 forbidden authority/route fragment in {rel}: {fragment}"
                        )
        return self._result(
            criterion,
            failures,
            [path.relative_to(self.root).as_posix() for path in swift_files],
        )

    def check_m50_mobile_audit_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m50_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M50 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
