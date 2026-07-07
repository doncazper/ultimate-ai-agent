from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart019Mixin:
    """Legacy checks from m77_roadmap_currentness through m80_roadmap_currentness."""
    def check_m77_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M77 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.81.0" not in text
            or "m77" not in text
            or "openwebui safe handoff execution" not in text
        ):
            failures.append(
                "active docs do not identify v0.81.0/M77 OpenWebUI Safe Handoff Execution"
            )
        if (
            "m77 is implemented/released" not in text
            and "v0.81.0 implements m77" not in text
        ):
            failures.append("active docs do not mark M77 implemented/released")
        for version_label, milestone, title in [
            ("v0.82.0", "M78", "Plugin Manifest Security Model"),
            ("v0.83.0", "M79", "Plugin Install Review, Disabled by Default"),
            ("v0.94.0", "M90", "Shell/Subprocess Hardening Freeze"),
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M78-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "plugin execution is implemented",
            "openwebui runtime calls are implemented",
            "model authority is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M77 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m78_plugin_manifest_security_model(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/plugin_manifest/__init__.py",
            "src/ultimate_ai_agent/core/plugin_manifest/contracts.py",
            "src/ultimate_ai_agent/core/plugin_manifest/enums.py",
            "src/ultimate_ai_agent/core/plugin_manifest/runtime.py",
            "src/ultimate_ai_agent/core/plugin_manifest/validation.py",
            "docs/tooling/PLUGIN_MANIFEST_SECURITY_MODEL.md",
            "docs/tooling/PLUGIN_MANIFEST_POLICY.md",
            "docs/tooling/PLUGIN_PERMISSION_MODEL.md",
            "docs/tooling/PLUGIN_PROVENANCE_REVIEW.md",
            "docs/tooling/PLUGIN_SANDBOX_TEST_PLAN.md",
            "docs/tooling/PLUGIN_MANIFEST_AUTHORITY_BOUNDARY.md",
            "docs/tooling/PLUGIN_MANIFEST_RECEIPT_PLAN.md",
            "docs/tooling/M78_TO_M79_BOUNDARY.md",
            "docs/release_notes/v0_82_0.md",
            "docs/archive/releases/v0_82_0/README_IMPORT.md",
            "docs/archive/releases/v0_82_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_82_0.md",
            "tests/test_m78_plugin_manifest_security_model.py",
            "tests/test_m78_plugin_manifest_gate_integration.py",
        ]
        failures = [
            f"missing M78 plugin manifest security file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.plugin_manifest import (
                PluginManifestApprovalBinding,
                PluginManifestDeclaredPermission,
                PluginManifestPermissionKind,
                PluginManifestRiskLevel,
                PluginManifestSecurityDecisionStatus,
                PluginManifestSecurityReviewRequest,
                build_plugin_manifest_security_decision,
            )

            permission = PluginManifestDeclaredPermission(
                permission_ref="plugin-permission:m78-gate",
                kind=PluginManifestPermissionKind.read_only_local_docs,
                risk_level=PluginManifestRiskLevel.low,
                safe_purpose="Review plugin manifest metadata only.",
                tool_broker_capability_ref="tool-broker-capability:m78-gate",
            )
            request = PluginManifestSecurityReviewRequest(
                review_request_ref="plugin-manifest-review-request:m78-gate",
                manifest_ref="plugin-manifest:m78-gate",
                plugin_ref="plugin:m78-gate",
                plugin_name="m78-reviewed-disabled-plugin",
                plugin_version="1.0.0",
                actor_ref="actor:m78-gate",
                source_ref="plugin-source:m78-gate",
                provenance_ref="plugin-provenance:m78-gate",
                declared_permissions=[permission],
                static_review_ref="plugin-static-review:m78-gate",
                sandbox_test_plan_ref="plugin-sandbox-test-plan:m78-gate",
                tool_broker_mapping_ref="plugin-tool-broker-map:m78-gate",
                event_ledger_plan_ref="event-ledger-plan:m78-gate",
                version_pin_ref="plugin-version-pin:m78-gate-1.0.0",
                revocation_plan_ref="plugin-revocation-plan:m78-gate",
                human_approval=PluginManifestApprovalBinding(
                    approval_ref="approval:m78-gate",
                    approved_manifest_ref="plugin-manifest:m78-gate",
                    approved_plugin_ref="plugin:m78-gate",
                    approved_version="1.0.0",
                    approved_actor_ref="actor:m78-gate",
                ),
                safe_manifest_summary="Reviewed disabled plugin manifest metadata.",
            )
            decision = build_plugin_manifest_security_decision(request)
            if (
                decision.status
                != PluginManifestSecurityDecisionStatus.review_ready_disabled
                or not decision.manifest_reviewed
                or decision.plugin_install_enabled
                or decision.plugin_enablement_enabled
                or decision.plugin_execution_enabled
                or decision.runtime_import_enabled
                or decision.network_access_enabled
                or decision.model_provider_call_enabled
                or decision.browser_automation_enabled
                or decision.shell_execution_enabled
                or decision.mobile_device_access_enabled
                or decision.remote_execution_enabled
                or decision.credential_cookie_access_enabled
                or decision.raw_prompt_exposure_enabled
                or decision.raw_provider_payload_exposure_enabled
                or decision.production_authority_granted
                or decision.side_effects_performed
                or decision.receipt_plan.plugin_install_performed
                or decision.receipt_plan.plugin_enablement_performed
                or decision.receipt_plan.plugin_execution_performed
                or decision.receipt_plan.raw_manifest_content_stored
                or not decision.receipt_plan.revocation_supported
                or "M78_PLUGIN_MANIFEST_SECURITY_MODEL" not in decision.reason_codes
                or "M79_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M78 plugin manifest decision is unsafe or over-authoritative"
                )

            for update, reason in [
                ({"source_ref": None}, "PLUGIN_SOURCE_REF_REQUIRED"),
                ({"provenance_ref": None}, "PLUGIN_PROVENANCE_REF_REQUIRED"),
                ({"static_review_ref": None}, "PLUGIN_STATIC_REVIEW_REQUIRED"),
                ({"sandbox_test_plan_ref": None}, "PLUGIN_SANDBOX_TEST_PLAN_REQUIRED"),
                ({"tool_broker_mapping_ref": None}, "TOOL_BROKER_MAPPING_REQUIRED"),
                ({"event_ledger_plan_ref": None}, "EVENT_LEDGER_PLAN_REQUIRED"),
                ({"version_pin_ref": None}, "PLUGIN_VERSION_PIN_REQUIRED"),
                ({"revocation_plan_ref": None}, "PLUGIN_REVOCATION_PLAN_REQUIRED"),
                ({"plugin_install_requested": True}, "PLUGIN_INSTALL_DENIED"),
                ({"plugin_enablement_requested": True}, "PLUGIN_ENABLEMENT_DENIED"),
                ({"plugin_execution_requested": True}, "PLUGIN_EXECUTION_DENIED"),
                ({"runtime_import_requested": True}, "PLUGIN_RUNTIME_IMPORT_DENIED"),
                ({"network_access_requested": True}, "PLUGIN_NETWORK_ACCESS_DENIED"),
                (
                    {"model_provider_call_requested": True},
                    "PLUGIN_MODEL_PROVIDER_CALL_DENIED",
                ),
                (
                    {"browser_automation_requested": True},
                    "PLUGIN_BROWSER_AUTOMATION_DENIED",
                ),
                ({"shell_execution_requested": True}, "PLUGIN_SHELL_EXECUTION_DENIED"),
                (
                    {"mobile_device_access_requested": True},
                    "PLUGIN_MOBILE_DEVICE_ACCESS_DENIED",
                ),
                (
                    {"remote_execution_requested": True},
                    "PLUGIN_REMOTE_EXECUTION_DENIED",
                ),
                (
                    {"credential_cookie_access_requested": True},
                    "PLUGIN_CREDENTIAL_COOKIE_ACCESS_DENIED",
                ),
                ({"raw_prompt_exposure_requested": True}, "RAW_PROMPT_EXPOSURE_DENIED"),
                (
                    {"raw_provider_payload_exposure_requested": True},
                    "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED",
                ),
                (
                    {"production_authority_requested": True},
                    "PRODUCTION_AUTHORITY_DENIED",
                ),
                ({"approval_ref": "approval_test_m78"}, "APPROVAL_TEST_REF_DENIED"),
                (
                    {"model_output_authority_claimed": True},
                    "MODEL_OUTPUT_AUTHORITY_DENIED",
                ),
                (
                    {"openwebui_output_authority_claimed": True},
                    "OPENWEBUI_OUTPUT_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    build_plugin_manifest_security_decision(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M78 unsafe plugin manifest request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M78 unsafe plugin manifest request raised {exc!s}, expected {reason}"
                        )
        except Exception as exc:
            failures.append(f"M78 plugin manifest security validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "plugin manifest security model",
            "manifest",
            "declared permissions",
            "source/provenance metadata",
            "static review",
            "sandbox test plan",
            "tool broker permission mapping",
            "event ledger logging",
            "version pinning",
            "revocation",
            "human approval for high-risk capabilities",
            "plugins remain disabled",
            "no plugin install",
            "no plugin enablement",
            "no plugin execution",
            "no runtime import",
            "no network access",
            "no model/provider call",
            "no browser automation",
            "no shell execution",
            "no mobile device access",
            "no remote execution",
            "no credentials or cookies",
            "no raw prompt",
            "no raw provider payload",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
            "m79 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M78 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m78_plugin_manifest_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "plugin_install_enabled=True",
            "plugin_enablement_enabled=True",
            "plugin_execution_enabled=True",
            "runtime_import_enabled=True",
            "network_access_enabled=True",
            "model_provider_call_enabled=True",
            "browser_automation_enabled=True",
            "shell_execution_enabled=True",
            "mobile_device_access_enabled=True",
            "remote_execution_enabled=True",
            "credential_cookie_access_enabled=True",
            "raw_prompt_exposure_enabled=True",
            "raw_provider_payload_exposure_enabled=True",
            "production_authority_enabled=True",
            "production_authority_granted=True",
            "plugin_install_performed=True",
            "plugin_enablement_performed=True",
            "plugin_execution_performed=True",
            "/plugins/install",
            "/plugins/enable",
            "/plugins/execute",
            "/plugin-runtime/import",
            "/plugin-runtime/execute",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/plugin_manifest/__init__.py",
            "src/ultimate_ai_agent/core/plugin_manifest/contracts.py",
            "src/ultimate_ai_agent/core/plugin_manifest/enums.py",
            "src/ultimate_ai_agent/core/plugin_manifest/runtime.py",
            "src/ultimate_ai_agent/core/plugin_manifest/validation.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/openapi.py",
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
                            f"M78 forbidden plugin manifest fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m78_plugin_manifest_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m78_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M78 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m78_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M78 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.82.0" not in text
            or "m78" not in text
            or "plugin manifest security model" not in text
        ):
            failures.append(
                "active docs do not identify v0.82.0/M78 Plugin Manifest Security Model"
            )
        if (
            "m78 is implemented/released" not in text
            and "v0.82.0 implements m78" not in text
        ):
            failures.append("active docs do not mark M78 implemented/released")
        for version_label, milestone, title in [
            ("v0.83.0", "M79", "Plugin Install Review, Disabled by Default"),
            ("v0.84.0", "M80", "Network/Browser/OpenWebUI Hardening Freeze"),
            ("v0.94.0", "M90", "Shell/Subprocess Hardening Freeze"),
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M79-M100 row: {version_label} / {milestone} — {title}"
                )
        forbidden_fragments = [
            "plugin install is implemented",
            "plugin enablement is implemented",
            "plugin execution is implemented",
            "shell execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ]
        version_tuple = self._active_version_tuple()
        if version_tuple < (0, 83, 0):
            forbidden_fragments.append("m79 is implemented")
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M78 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m79_plugin_install_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/plugin_install_review/__init__.py",
            "src/ultimate_ai_agent/core/plugin_install_review/contracts.py",
            "src/ultimate_ai_agent/core/plugin_install_review/enums.py",
            "src/ultimate_ai_agent/core/plugin_install_review/runtime.py",
            "src/ultimate_ai_agent/core/plugin_install_review/validation.py",
            "docs/tooling/PLUGIN_INSTALL_REVIEW.md",
            "docs/tooling/PLUGIN_INSTALL_REVIEW_POLICY.md",
            "docs/tooling/PLUGIN_INSTALL_REVIEW_AUTHORITY_BOUNDARY.md",
            "docs/tooling/PLUGIN_INSTALL_REVIEW_RECEIPT_PLAN.md",
            "docs/tooling/M79_TO_M80_BOUNDARY.md",
            "docs/release_notes/v0_83_0.md",
            "docs/archive/releases/v0_83_0/README_IMPORT.md",
            "docs/archive/releases/v0_83_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_83_0.md",
            "tests/test_m79_plugin_install_review_disabled.py",
            "tests/test_m79_plugin_install_review_gate_integration.py",
        ]
        failures = [
            f"missing M79 plugin install review file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.plugin_install_review import (
                PluginInstallReviewApprovalBinding,
                PluginInstallReviewDecisionStatus,
                PluginInstallReviewRequest,
                build_plugin_install_review_decision,
            )
            from ultimate_ai_agent.core.plugin_manifest import (
                PluginManifestApprovalBinding,
                PluginManifestDeclaredPermission,
                PluginManifestPermissionKind,
                PluginManifestRiskLevel,
                PluginManifestSecurityReviewRequest,
                build_plugin_manifest_security_decision,
            )

            manifest_decision = build_plugin_manifest_security_decision(
                PluginManifestSecurityReviewRequest(
                    review_request_ref="plugin-manifest-review-request:m79-gate",
                    manifest_ref="plugin-manifest:m79-gate",
                    plugin_ref="plugin:m79-gate",
                    plugin_name="m79-install-review-disabled-plugin",
                    plugin_version="1.0.0",
                    actor_ref="actor:m79-gate",
                    source_ref="plugin-source:m79-gate",
                    provenance_ref="plugin-provenance:m79-gate",
                    declared_permissions=[
                        PluginManifestDeclaredPermission(
                            permission_ref="plugin-permission:m79-gate",
                            kind=PluginManifestPermissionKind.read_only_local_docs,
                            risk_level=PluginManifestRiskLevel.low,
                            safe_purpose="Review plugin install metadata only.",
                            tool_broker_capability_ref="tool-broker-capability:m79-gate",
                        )
                    ],
                    static_review_ref="plugin-static-review:m79-gate",
                    sandbox_test_plan_ref="plugin-sandbox-test-plan:m79-gate",
                    tool_broker_mapping_ref="plugin-tool-broker-map:m79-gate",
                    event_ledger_plan_ref="event-ledger-plan:m79-gate",
                    version_pin_ref="plugin-version-pin:m79-gate-1.0.0",
                    revocation_plan_ref="plugin-revocation-plan:m79-gate",
                    human_approval=PluginManifestApprovalBinding(
                        approval_ref="approval:m79-manifest-gate",
                        approved_manifest_ref="plugin-manifest:m79-gate",
                        approved_plugin_ref="plugin:m79-gate",
                        approved_version="1.0.0",
                        approved_actor_ref="actor:m79-gate",
                    ),
                    safe_manifest_summary="Reviewed disabled plugin manifest metadata.",
                )
            )
            request = PluginInstallReviewRequest(
                install_review_request_ref="plugin-install-review-request:m79-gate",
                manifest_security_decision=manifest_decision,
                manifest_ref=manifest_decision.manifest_ref,
                plugin_ref=manifest_decision.plugin_ref,
                plugin_version=manifest_decision.plugin_version,
                actor_ref=manifest_decision.actor_ref,
                source_package_ref="plugin-package:m79-gate-reviewed",
                provenance_ref="plugin-provenance:m79-gate",
                static_review_ref="plugin-static-review:m79-gate",
                sandbox_test_plan_ref="plugin-sandbox-test-plan:m79-gate",
                tool_broker_mapping_ref="plugin-tool-broker-map:m79-gate",
                event_ledger_plan_ref="event-ledger-plan:m79-gate-install-review",
                version_pin_ref="plugin-version-pin:m79-gate-1.0.0",
                revocation_plan_ref="plugin-revocation-plan:m79-gate",
                approval=PluginInstallReviewApprovalBinding(
                    approval_ref="approval:m79-install-review-gate",
                    approved_install_review_request_ref="plugin-install-review-request:m79-gate",
                    approved_manifest_security_decision_ref=manifest_decision.decision_ref,
                    approved_manifest_ref=manifest_decision.manifest_ref,
                    approved_plugin_ref=manifest_decision.plugin_ref,
                    approved_version=manifest_decision.plugin_version,
                    approved_actor_ref=manifest_decision.actor_ref,
                ),
                safe_install_review_summary="Review plugin install candidate metadata while disabled.",
            )
            decision = build_plugin_install_review_decision(request)
            if (
                decision.status
                != PluginInstallReviewDecisionStatus.install_review_ready_disabled
                or not decision.install_reviewed
                or decision.plugin_install_enabled
                or decision.plugin_enablement_enabled
                or decision.plugin_execution_enabled
                or decision.runtime_import_enabled
                or decision.network_access_enabled
                or decision.model_provider_call_enabled
                or decision.browser_automation_enabled
                or decision.shell_execution_enabled
                or decision.mobile_device_access_enabled
                or decision.remote_execution_enabled
                or decision.credential_cookie_access_enabled
                or decision.raw_manifest_content_returned
                or decision.raw_package_content_returned
                or decision.raw_prompt_exposure_enabled
                or decision.raw_provider_payload_exposure_enabled
                or decision.production_authority_granted
                or decision.side_effects_performed
                or decision.receipt_plan.plugin_install_performed
                or decision.receipt_plan.plugin_enablement_performed
                or decision.receipt_plan.plugin_execution_performed
                or decision.receipt_plan.runtime_import_performed
                or decision.receipt_plan.raw_manifest_content_stored
                or decision.receipt_plan.raw_package_content_stored
                or "M79_PLUGIN_INSTALL_REVIEW_DISABLED_BY_DEFAULT"
                not in decision.reason_codes
                or "M80_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M79 plugin install review decision is unsafe or over-authoritative"
                )

            for update, reason in [
                ({"source_package_ref": None}, "PLUGIN_SOURCE_PACKAGE_REF_REQUIRED"),
                ({"static_review_ref": None}, "PLUGIN_STATIC_REVIEW_REQUIRED"),
                ({"sandbox_test_plan_ref": None}, "PLUGIN_SANDBOX_TEST_PLAN_REQUIRED"),
                ({"approval": None}, "PLUGIN_INSTALL_REVIEW_APPROVAL_REQUIRED"),
                ({"approval_ref": "approval_test_m79"}, "APPROVAL_TEST_REF_DENIED"),
                ({"plugin_install_requested": True}, "PLUGIN_INSTALL_DENIED"),
                ({"plugin_enablement_requested": True}, "PLUGIN_ENABLEMENT_DENIED"),
                ({"plugin_execution_requested": True}, "PLUGIN_EXECUTION_DENIED"),
                ({"runtime_import_requested": True}, "PLUGIN_RUNTIME_IMPORT_DENIED"),
                ({"network_access_requested": True}, "PLUGIN_NETWORK_ACCESS_DENIED"),
                (
                    {"model_provider_call_requested": True},
                    "PLUGIN_MODEL_PROVIDER_CALL_DENIED",
                ),
                (
                    {"browser_automation_requested": True},
                    "PLUGIN_BROWSER_AUTOMATION_DENIED",
                ),
                ({"shell_execution_requested": True}, "PLUGIN_SHELL_EXECUTION_DENIED"),
                (
                    {"mobile_device_access_requested": True},
                    "PLUGIN_MOBILE_DEVICE_ACCESS_DENIED",
                ),
                (
                    {"remote_execution_requested": True},
                    "PLUGIN_REMOTE_EXECUTION_DENIED",
                ),
                (
                    {"credential_cookie_access_requested": True},
                    "PLUGIN_CREDENTIAL_COOKIE_ACCESS_DENIED",
                ),
                ({"raw_package_content_requested": True}, "RAW_PACKAGE_CONTENT_DENIED"),
                (
                    {"production_authority_requested": True},
                    "PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    build_plugin_install_review_decision(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M79 unsafe plugin install review request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M79 unsafe plugin install review request raised {exc!s}, expected {reason}"
                        )
        except Exception as exc:
            failures.append(f"M79 plugin install review validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "plugin install review",
            "disabled by default",
            "exact approval binding",
            "manifest security decision",
            "source package ref",
            "static review",
            "sandbox test plan",
            "tool broker mapping",
            "event ledger",
            "version pin",
            "revocation",
            "no plugin install",
            "no plugin enablement",
            "no plugin execution",
            "no runtime import",
            "no network access",
            "no model/provider call",
            "no browser automation",
            "no shell execution",
            "no mobile device access",
            "no remote execution",
            "no credentials or cookies",
            "no raw package content",
            "no raw prompt",
            "no raw provider payload",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
            "m80 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M79 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m79_plugin_install_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "plugin_install_enabled=True",
            "plugin_enablement_enabled=True",
            "plugin_execution_enabled=True",
            "runtime_import_enabled=True",
            "network_access_enabled=True",
            "model_provider_call_enabled=True",
            "browser_automation_enabled=True",
            "shell_execution_enabled=True",
            "mobile_device_access_enabled=True",
            "remote_execution_enabled=True",
            "credential_cookie_access_enabled=True",
            "raw_manifest_content_enabled=True",
            "raw_package_content_enabled=True",
            "raw_prompt_exposure_enabled=True",
            "raw_provider_payload_exposure_enabled=True",
            "production_authority_enabled=True",
            "production_authority_granted=True",
            "plugin_install_performed=True",
            "plugin_enablement_performed=True",
            "plugin_execution_performed=True",
            "runtime_import_performed=True",
            "raw_package_content_stored=True",
            "/plugins/install",
            "/plugins/enable",
            "/plugins/execute",
            "/plugins/review/install/submit",
            "/plugin-runtime/import",
            "/plugin-runtime/execute",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/plugin_manifest/__init__.py",
            "src/ultimate_ai_agent/core/plugin_manifest/contracts.py",
            "src/ultimate_ai_agent/core/plugin_manifest/enums.py",
            "src/ultimate_ai_agent/core/plugin_manifest/runtime.py",
            "src/ultimate_ai_agent/core/plugin_manifest/validation.py",
            "src/ultimate_ai_agent/core/plugin_install_review/__init__.py",
            "src/ultimate_ai_agent/core/plugin_install_review/contracts.py",
            "src/ultimate_ai_agent/core/plugin_install_review/enums.py",
            "src/ultimate_ai_agent/core/plugin_install_review/runtime.py",
            "src/ultimate_ai_agent/core/plugin_install_review/validation.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/openapi.py",
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
                            f"M79 forbidden plugin install review fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m79_plugin_install_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m79_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M79 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m79_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M79 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.83.0" not in text
            or "m79" not in text
            or "plugin install review, disabled by default" not in text
        ):
            failures.append(
                "active docs do not identify v0.83.0/M79 Plugin Install Review, Disabled by Default"
            )
        if (
            "m79 is implemented/released" not in text
            and "v0.83.0 implements m79" not in text
        ):
            failures.append("active docs do not mark M79 implemented/released")
        for version_label, milestone, title in [
            ("v0.84.0", "M80", "Network/Browser/OpenWebUI Hardening Freeze"),
            ("v0.94.0", "M90", "Shell/Subprocess Hardening Freeze"),
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M80-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "plugin install is implemented",
            "plugin enablement is implemented",
            "plugin execution is implemented",
            "runtime import is implemented",
            "shell execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M79 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m80_network_browser_openwebui_hardening_freeze_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/hardening_freeze/__init__.py",
            "src/ultimate_ai_agent/core/hardening_freeze/network_browser_openwebui.py",
            "docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE.md",
            "docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_CONTRACTS.md",
            "docs/hardening/NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_NON_GOALS.md",
            "docs/hardening/M80_TO_M81_BOUNDARY.md",
            "docs/release_notes/v0_84_0.md",
            "docs/archive/releases/v0_84_0/README_IMPORT.md",
            "docs/archive/releases/v0_84_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_84_0.md",
            "tests/test_m80_network_browser_openwebui_hardening_freeze.py",
            "tests/test_m80_gate_integration.py",
        ]
        failures = [
            f"missing M80 hardening freeze file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.hardening_freeze import (
                NetworkBrowserOpenWebUIFreezeRequest,
                NetworkBrowserOpenWebUIFreezeStatus,
                build_network_browser_openwebui_freeze_report,
            )

            request = NetworkBrowserOpenWebUIFreezeRequest(
                request_ref="network-browser-openwebui-freeze-request:m80-gate",
                freeze_ref="network-browser-openwebui-freeze:m80-gate",
                baseline_ref="baseline:v0.83.0",
                actor_ref="actor:m80-gate",
                accepted_milestone_refs=[
                    f"milestone:M{index}" for index in range(71, 80)
                ],
                checklist_refs=[
                    "m80-freeze:m71-network-contract-reviewed",
                    "m80-freeze:m72-allowlisted-redacted-fetch-only",
                    "m80-freeze:m74-browser-observe-only",
                    "m80-freeze:m75-browser-action-dry-run-only",
                    "m80-freeze:m76-openwebui-bridge-review-only",
                    "m80-freeze:m77-openwebui-handoff-exact-bound",
                    "m80-freeze:m78-m79-plugin-disabled-by-default",
                    "m80-freeze:route-stable",
                    "m80-freeze:dependency-stable",
                ],
                safe_summary="Freeze accepted network browser openwebui and plugin boundaries.",
            )
            report = build_network_browser_openwebui_freeze_report(request)
            if (
                report.status != NetworkBrowserOpenWebUIFreezeStatus.frozen
                or not report.freeze_only
                or not report.review_only
                or not report.network_browser_openwebui_only
                or not report.deterministic
                or report.unrestricted_network_performed
                or report.authenticated_network_action_performed
                or report.raw_network_response_returned
                or report.browser_navigation_performed
                or report.browser_action_performed
                or report.browser_screenshot_performed
                or report.raw_dom_returned
                or report.authenticated_browser_profile_accessed
                or report.openwebui_model_authority_granted
                or report.openwebui_tool_execution_performed
                or report.openwebui_memory_write_performed
                or report.openwebui_context_injection_performed
                or report.raw_prompt_exposed
                or report.raw_provider_payload_exposed
                or report.plugin_install_performed
                or report.plugin_enablement_performed
                or report.plugin_execution_performed
                or report.plugin_runtime_import_performed
                or report.shell_execution_performed
                or report.background_worker_started
                or report.remote_execution_performed
                or report.backend_route_added
                or report.control_center_control_added
                or report.dependency_added
                or report.production_authority_granted
                or report.side_effects_performed
                or "M80_NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_REVIEW_ONLY"
                not in report.reason_codes
                or "M80_NO_NEW_RUNTIME_AUTHORITY" not in report.reason_codes
                or "M81_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M80 hardening freeze report is unsafe or over-authoritative"
                )

            for update, reason in [
                (
                    {"network_tool_expansion_requested": True},
                    "NETWORK_TOOL_EXPANSION_DENIED",
                ),
                (
                    {"unrestricted_network_requested": True},
                    "UNRESTRICTED_NETWORK_DENIED",
                ),
                (
                    {"authenticated_network_action_requested": True},
                    "AUTHENTICATED_NETWORK_ACTION_DENIED",
                ),
                (
                    {"raw_network_response_requested": True},
                    "RAW_NETWORK_RESPONSE_DENIED",
                ),
                ({"browser_navigation_requested": True}, "BROWSER_NAVIGATION_DENIED"),
                ({"browser_click_requested": True}, "BROWSER_CLICK_DENIED"),
                (
                    {"browser_action_execution_requested": True},
                    "BROWSER_ACTION_EXECUTION_DENIED",
                ),
                ({"browser_screenshot_requested": True}, "BROWSER_SCREENSHOT_DENIED"),
                ({"raw_dom_requested": True}, "RAW_DOM_DENIED"),
                (
                    {"authenticated_browser_profile_requested": True},
                    "AUTHENTICATED_BROWSER_PROFILE_DENIED",
                ),
                (
                    {"openwebui_model_authority_requested": True},
                    "OPENWEBUI_MODEL_AUTHORITY_DENIED",
                ),
                (
                    {"openwebui_tool_execution_requested": True},
                    "OPENWEBUI_TOOL_EXECUTION_DENIED",
                ),
                (
                    {"openwebui_memory_write_requested": True},
                    "OPENWEBUI_MEMORY_WRITE_DENIED",
                ),
                (
                    {"openwebui_context_injection_requested": True},
                    "OPENWEBUI_CONTEXT_INJECTION_DENIED",
                ),
                ({"raw_prompt_exposure_requested": True}, "RAW_PROMPT_EXPOSURE_DENIED"),
                (
                    {"raw_provider_payload_exposure_requested": True},
                    "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED",
                ),
                ({"plugin_install_requested": True}, "PLUGIN_INSTALL_DENIED"),
                ({"plugin_enablement_requested": True}, "PLUGIN_ENABLEMENT_DENIED"),
                ({"plugin_execution_requested": True}, "PLUGIN_EXECUTION_DENIED"),
                (
                    {"plugin_runtime_import_requested": True},
                    "PLUGIN_RUNTIME_IMPORT_DENIED",
                ),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                ({"background_worker_requested": True}, "BACKGROUND_WORKER_DENIED"),
                ({"remote_execution_requested": True}, "REMOTE_EXECUTION_DENIED"),
                (
                    {"credential_cookie_access_requested": True},
                    "CREDENTIAL_COOKIE_ACCESS_DENIED",
                ),
                ({"backend_route_requested": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_requested": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_requested": True}, "DEPENDENCY_CHANGE_DENIED"),
                (
                    {"production_authority_requested": True},
                    "PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    build_network_browser_openwebui_freeze_report(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M80 unsafe freeze request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M80 unsafe freeze request raised {exc!s}, expected {reason}"
                        )
        except Exception as exc:
            failures.append(f"M80 hardening freeze validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "network/browser/openwebui hardening freeze",
            "m71-m79",
            "freeze-only",
            "review-only",
            "deterministic",
            "accepted milestone refs",
            "checklist refs",
            "no unrestricted network",
            "no authenticated network action",
            "no raw network response",
            "no browser navigation",
            "no browser click",
            "no browser screenshot",
            "no raw dom",
            "no authenticated browser profile",
            "no openwebui model authority",
            "no openwebui tool execution",
            "no openwebui memory write",
            "no openwebui context injection",
            "no raw prompt",
            "no raw provider payload",
            "no plugin install",
            "no plugin enablement",
            "no plugin execution",
            "no runtime import",
            "no shell execution",
            "no background worker",
            "no remote execution",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
            "m81 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M80 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m80_network_browser_openwebui_hardening_freeze_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "network_tool_expansion_enabled=True",
            "unrestricted_network_enabled=True",
            "authenticated_network_action_enabled=True",
            "raw_network_response_enabled=True",
            "browser_navigation_enabled=True",
            "browser_click_enabled=True",
            "browser_action_execution_enabled=True",
            "browser_screenshot_enabled=True",
            "raw_dom_enabled=True",
            "authenticated_browser_profile_enabled=True",
            "openwebui_model_authority_enabled=True",
            "openwebui_tool_execution_enabled=True",
            "openwebui_memory_write_enabled=True",
            "openwebui_context_injection_enabled=True",
            "raw_prompt_exposure_enabled=True",
            "raw_provider_payload_exposure_enabled=True",
            "plugin_install_enabled=True",
            "plugin_enablement_enabled=True",
            "plugin_execution_enabled=True",
            "plugin_runtime_import_enabled=True",
            "shell_execution_enabled=True",
            "background_worker_enabled=True",
            "remote_execution_enabled=True",
            "credential_cookie_access_enabled=True",
            "production_authority_enabled=True",
            "unrestricted_network_performed=True",
            "browser_action_performed=True",
            "openwebui_tool_execution_performed=True",
            "plugin_runtime_import_performed=True",
            "remote_execution_performed=True",
            "production_authority_granted=True",
            "/network/fetch/unrestricted",
            "/network/post",
            "/browser/navigate",
            "/browser/click",
            "/browser/screenshot",
            "/openwebui/tools/execute",
            "/openwebui/context/inject",
            "/openwebui/memory/write",
            "/plugins/install",
            "/plugins/enable",
            "/plugins/execute",
            "/plugin-runtime/import",
            "/plugin-runtime/execute",
            "/shell/execute",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/hardening_freeze/__init__.py",
            "src/ultimate_ai_agent/core/hardening_freeze/network_browser_openwebui.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/openapi.py",
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
                            f"M80 forbidden hardening freeze fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m80_network_browser_openwebui_hardening_freeze_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m80_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M80 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m80_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M80 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.84.0" not in text
            or "m80" not in text
            or "network/browser/openwebui hardening freeze" not in text
        ):
            failures.append(
                "active docs do not identify v0.84.0/M80 Network/Browser/OpenWebUI Hardening Freeze"
            )
        if (
            "m80 is implemented/released" not in text
            and "v0.84.0 implements m80" not in text
        ):
            failures.append("active docs do not mark M80 implemented/released")
        for version_label, milestone, title in [
            ("v0.85.0", "M81", "Runtime Sandbox Spec"),
            ("v0.90.0", "M86", "Shell Approval Gate v1"),
            ("v0.94.0", "M90", "Shell/Subprocess Hardening Freeze"),
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M81-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "unrestricted network is implemented",
            "browser click is implemented",
            "browser action execution is implemented",
            "openwebui model authority is implemented",
            "openwebui tool execution is implemented",
            "plugin execution is implemented",
            "shell execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M80 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
