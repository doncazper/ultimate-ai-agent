from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart040Mixin:
    """Legacy checks from m143_alpha_ui_app_readiness_static_safety through m146_billing_plan_boundary_route_boundary."""
    def check_m143_alpha_ui_app_readiness_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "alpha_ui_runtime_enabled=True",
            "app_readiness_execution_enabled=True",
            "app_build_enabled=True",
            "app_signing_enabled=True",
            "app_store_connect_enabled=True",
            "testflight_upload_enabled=True",
            "alpha_release_enabled=True",
            "beta_release_enabled=True",
            "production_authority_granted=True",
            "raw_private_content_access_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_action_enabled=True",
            "connector_action_enabled=True",
            "network_access_enabled=True",
            "plugin_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "dependency_added=True",
            "alpha_ui_runtime_started=True",
            "app_readiness_execution_performed=True",
            "app_build_performed=True",
            "app_store_connect_performed=True",
            "testflight_upload_performed=True",
            "/alpha/ui/start",
            "/alpha/app-readiness/run",
            "/app/build",
            "/app-store/connect",
            "/testflight/upload",
            "/alpha/release",
            "/beta/release",
            "/plugin-marketplace/publish",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/productization/__init__.py",
            "src/ultimate_ai_agent/core/productization/alpha_ui_app_readiness.py",
            "src/ultimate_ai_agent/core/productization/alpha_privacy_review.py",
            "src/ultimate_ai_agent/core/productization/multi_user_product_boundary.py",
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
                if ".test." in rel or _is_static_safety_scan_allowed_file(
                    rel, allowed_files
                ):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M143 forbidden alpha UI/app readiness fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m143_alpha_ui_app_readiness_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m143_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M143 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m143_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
        ]
        failures = [
            f"missing M143 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m143" not in text or "alpha ui and app readiness" not in text:
            failures.append("active docs do not identify Checkpoint M143")
        if (
            "m143 is implemented/released" not in text
            and "checkpoint m143 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M143 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m142",
                "pre-alpha checkpoint",
                "m142",
                "alpha privacy review",
                "implemented/released",
            ),
            (
                "checkpoint m143",
                "pre-alpha checkpoint",
                "m143",
                "alpha ui and app readiness",
                "implemented/released",
            ),
            (
                "checkpoint m144",
                "pre-alpha checkpoint",
                "m144",
                "plugin marketplace policy draft",
                "implemented/released",
            ),
            (
                "checkpoint m145",
                "pre-alpha checkpoint",
                "m145",
                "enterprise/pro safety modes",
                "implemented/released",
            ),
            (
                "checkpoint m146",
                "pre-alpha checkpoint",
                "m146",
                "billing/plan boundary, if needed",
                "implemented/released",
            ),
            (
                "checkpoint m147",
                "pre-alpha checkpoint",
                "m147",
                "public docs + wiki readiness",
                "implemented/released",
            ),
            (
                "checkpoint m148",
                "pre-alpha checkpoint",
                "m148",
                "external security review",
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
                    f"active docs missing expected M143/M144/M145/M146/M147/M148-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "alpha ui runtime is implemented",
            "app readiness execution is implemented",
            "app build is implemented",
            "app signing is implemented",
            "app store connect is implemented",
            "testflight upload is implemented",
            "alpha release is implemented",
            "beta is released",
            "production authority is implemented",
            "plugin marketplace runtime is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m144 dependency is added",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M143 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m144_plugin_marketplace_policy_draft_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/productization/plugin_marketplace_policy_draft.py",
            "docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT.md",
            "docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_POLICY.md",
            "docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_AUTHORITY_BOUNDARY.md",
            "docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_RECEIPT_PLAN.md",
            "docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_NON_GOALS.md",
            "docs/productization/M144_TO_M145_BOUNDARY.md",
            "docs/release_notes/checkpoint_m144.md",
            "docs/archive/checkpoints/m144/README_IMPORT.md",
            "docs/archive/checkpoints/m144/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m144_plugin_marketplace_policy_draft.py",
            "tests/test_m144_gate_integration.py",
        ]
        failures = [
            f"missing M144 plugin marketplace policy draft file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m144_plugin_marketplace_policy_draft import _request
            from ultimate_ai_agent.core.productization import (
                PluginMarketplacePolicyDraftStatus,
                build_plugin_marketplace_policy_draft_record,
                validate_plugin_marketplace_policy_draft_record,
            )

            record = build_plugin_marketplace_policy_draft_record(_request())
            if (
                record.status
                != PluginMarketplacePolicyDraftStatus.policy_draft_recorded
                or not record.contract_only
                or not record.review_only
                or not record.deterministic
                or not record.local_only
                or not record.safe_refs_only
                or not record.policy_draft_only
                or not record.disabled_by_default
                or not record.m101_m143_covered
                or not record.marketplace_policy_bound
                or not record.publisher_policy_bound
                or not record.listing_review_bound
                or not record.provenance_review_bound
                or not record.signature_review_bound
                or not record.sandbox_review_bound
                or not record.permission_mapping_bound
                or not record.approval_policy_bound
                or not record.audit_replay_bound
                or not record.revocation_bound
                or not record.no_effect_receipt_required
                or not record.no_plugin_install
                or not record.no_plugin_enablement
                or not record.no_plugin_execution
                or not record.no_marketplace_runtime
                or not record.no_marketplace_publish
                or not record.no_external_plugin_authority
                or not record.no_package_import
                or not record.no_network_plugin_fetch
                or not record.no_dependency
                or not record.no_production_authority
                or record.plugin_marketplace_runtime_started
                or record.marketplace_publish_performed
                or record.plugin_install_performed
                or record.plugin_enablement_performed
                or record.plugin_execution_performed
                or record.external_plugin_authority_granted
                or record.external_plugin_loaded
                or record.package_import_performed
                or record.runtime_import_performed
                or record.network_plugin_fetch_performed
                or record.package_download_performed
                or record.artifact_upload_performed
                or record.execution_performed
                or record.tool_execution_performed
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.production_authority_granted
                or "M144_PLUGIN_MARKETPLACE_POLICY_DRAFT_REVIEW_ONLY"
                not in record.reason_codes
                or "M144_M101_M143_COVERED" not in record.reason_codes
                or "M144_DISABLED_BY_DEFAULT" not in record.reason_codes
                or "M144_NO_PLUGIN_INSTALL" not in record.reason_codes
                or "M144_NO_PLUGIN_ENABLEMENT" not in record.reason_codes
                or "M144_NO_PLUGIN_EXECUTION" not in record.reason_codes
                or "M144_NO_MARKETPLACE_RUNTIME" not in record.reason_codes
                or "M144_NO_MARKETPLACE_PUBLISH" not in record.reason_codes
                or "M144_NO_EXTERNAL_PLUGIN_AUTHORITY" not in record.reason_codes
                or "M144_NO_PACKAGE_IMPORT" not in record.reason_codes
                or "M144_NO_NETWORK_PLUGIN_FETCH" not in record.reason_codes
                or "M144_NO_PRODUCTION_AUTHORITY" not in record.reason_codes
                or "M145_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M144 plugin marketplace policy draft record is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"plugin_marketplace_runtime_started": True},
                    "M144_MARKETPLACE_RUNTIME_DENIED",
                ),
                (
                    {"marketplace_publish_performed": True},
                    "M144_MARKETPLACE_PUBLISH_DENIED",
                ),
                ({"plugin_install_performed": True}, "M144_PLUGIN_INSTALL_DENIED"),
                (
                    {"plugin_enablement_performed": True},
                    "M144_PLUGIN_ENABLEMENT_DENIED",
                ),
                ({"plugin_execution_performed": True}, "M144_PLUGIN_EXECUTION_DENIED"),
                (
                    {"external_plugin_authority_granted": True},
                    "M144_EXTERNAL_PLUGIN_AUTHORITY_DENIED",
                ),
                (
                    {"package_import_performed": True},
                    "M144_PACKAGE_IMPORT_DENIED",
                ),
                (
                    {"network_plugin_fetch_performed": True},
                    "M144_NETWORK_PLUGIN_FETCH_DENIED",
                ),
                ({"backend_route_added": True}, "M144_BACKEND_ROUTE_DENIED"),
                ({"dependency_added": True}, "M144_DEPENDENCY_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M144_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_plugin_marketplace_policy_draft_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M144 unsafe marketplace mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M144 unsafe marketplace mutation raised {exc!s}"
                        )
        except Exception as exc:
            failures.append(f"M144 marketplace policy validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "plugin marketplace policy draft",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "policy-draft-only",
            "disabled by default",
            "route-free",
            "no-effect",
            "accepted m101-m143",
            "marketplace policy refs",
            "publisher policy refs",
            "listing review refs",
            "provenance review refs",
            "signature review refs",
            "sandbox review refs",
            "permission mapping refs",
            "approval policy refs",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no plugin marketplace runtime",
            "no marketplace publish",
            "no plugin install",
            "no plugin enablement",
            "no plugin execution",
            "no external plugin authority",
            "no package import",
            "no network plugin fetch",
            "no backend route",
            "no control center control",
            "no dependency",
            "no beta release",
            "no production authority",
            "m145 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M144 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m144_plugin_marketplace_policy_draft_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "plugin_marketplace_runtime_enabled=True",
            "marketplace_publish_enabled=True",
            "plugin_install_enabled=True",
            "plugin_enablement_enabled=True",
            "plugin_execution_enabled=True",
            "external_plugin_authority_enabled=True",
            "external_plugin_loading_enabled=True",
            "marketplace_listing_mutation_enabled=True",
            "package_import_enabled=True",
            "runtime_import_enabled=True",
            "network_plugin_fetch_enabled=True",
            "package_download_enabled=True",
            "artifact_upload_enabled=True",
            "signature_verification_runtime_enabled=True",
            "credential_handling_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_action_enabled=True",
            "connector_action_enabled=True",
            "network_access_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "plugin_marketplace_runtime_started=True",
            "marketplace_publish_performed=True",
            "plugin_install_performed=True",
            "plugin_enablement_performed=True",
            "plugin_execution_performed=True",
            "external_plugin_authority_granted=True",
            "external_plugin_loaded=True",
            "package_import_performed=True",
            "network_plugin_fetch_performed=True",
            "package_download_performed=True",
            "artifact_upload_performed=True",
            "/plugin-marketplace/publish",
            "/plugin-marketplace/install",
            "/plugin-marketplace/enable",
            "/plugins/install",
            "/plugins/execute",
            "/plugins/load",
            "/plugin-runtime/import",
            "/plugin-runtime/execute",
            "/plugin-package/download",
            "/plugin-package/upload",
            "/marketplace/listings/write",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/productization/__init__.py",
            "src/ultimate_ai_agent/core/productization/plugin_marketplace_policy_draft.py",
            "src/ultimate_ai_agent/core/productization/alpha_ui_app_readiness.py",
            "src/ultimate_ai_agent/core/productization/alpha_privacy_review.py",
            "src/ultimate_ai_agent/core/productization/multi_user_product_boundary.py",
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
                if ".test." in rel or _is_static_safety_scan_allowed_file(
                    rel, allowed_files
                ):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M144 forbidden marketplace policy fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m144_plugin_marketplace_policy_draft_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m144_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M144 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m144_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
        ]
        failures = [
            f"missing M144 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m144" not in text
            or "plugin marketplace policy draft" not in text
        ):
            failures.append("active docs do not identify Checkpoint M144")
        if (
            "m144 is implemented/released" not in text
            and "checkpoint m144 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M144 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m143",
                "pre-alpha checkpoint",
                "m143",
                "alpha ui and app readiness",
                "implemented/released",
            ),
            (
                "checkpoint m144",
                "pre-alpha checkpoint",
                "m144",
                "plugin marketplace policy draft",
                "implemented/released",
            ),
            (
                "checkpoint m145",
                "pre-alpha checkpoint",
                "m145",
                "enterprise/pro safety modes",
                "implemented/released",
            ),
            (
                "checkpoint m146",
                "pre-alpha checkpoint",
                "m146",
                "billing/plan boundary, if needed",
                "implemented/released",
            ),
            (
                "checkpoint m147",
                "pre-alpha checkpoint",
                "m147",
                "public docs + wiki readiness",
                "implemented/released",
            ),
            (
                "checkpoint m148",
                "pre-alpha checkpoint",
                "m148",
                "external security review",
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
                    f"active docs missing expected M144/M145/M146/M147/M148-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "enterprise/pro safety runtime is implemented",
            "plan enforcement is implemented",
            "plugin marketplace runtime is implemented",
            "marketplace publish is implemented",
            "plugin install is implemented",
            "plugin enablement is implemented",
            "plugin execution is implemented",
            "package import is implemented",
            "network plugin fetch is implemented",
            "beta is released",
            "production authority is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m145 dependency is added",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M144 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m145_enterprise_pro_safety_modes_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/productization/enterprise_pro_safety_modes.py",
            "docs/productization/ENTERPRISE_PRO_SAFETY_MODES.md",
            "docs/productization/ENTERPRISE_PRO_SAFETY_MODES_POLICY.md",
            "docs/productization/ENTERPRISE_PRO_SAFETY_MODES_AUTHORITY_BOUNDARY.md",
            "docs/productization/ENTERPRISE_PRO_SAFETY_MODES_RECEIPT_PLAN.md",
            "docs/productization/ENTERPRISE_PRO_SAFETY_MODES_NON_GOALS.md",
            "docs/productization/M145_TO_M146_BOUNDARY.md",
            "docs/release_notes/checkpoint_m145.md",
            "docs/archive/checkpoints/m145/README_IMPORT.md",
            "docs/archive/checkpoints/m145/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m145_enterprise_pro_safety_modes.py",
            "tests/test_m145_gate_integration.py",
        ]
        failures = [
            f"missing M145 Enterprise/Pro safety modes file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m145_enterprise_pro_safety_modes import _request
            from ultimate_ai_agent.core.productization import (
                EnterpriseProSafetyModesStatus,
                build_enterprise_pro_safety_modes_record,
                validate_enterprise_pro_safety_modes_record,
            )

            record = build_enterprise_pro_safety_modes_record(_request())
            if (
                record.status != EnterpriseProSafetyModesStatus.safety_modes_recorded
                or not record.contract_only
                or not record.review_only
                or not record.deterministic
                or not record.local_only
                or not record.safe_refs_only
                or not record.safety_modes_only
                or not record.disabled_by_default
                or not record.m101_m144_covered
                or not record.enterprise_safety_modes_bound
                or not record.pro_safety_modes_bound
                or not record.workspace_boundaries_bound
                or not record.role_policies_bound
                or not record.authority_ceilings_bound
                or not record.feature_availability_bound
                or not record.escalation_policies_bound
                or not record.audit_replay_bound
                or not record.revocation_bound
                or not record.no_effect_receipt_required
                or not record.no_enterprise_runtime
                or not record.no_pro_runtime
                or not record.no_plan_enforcement
                or not record.no_billing_runtime
                or not record.no_account_tenant_runtime
                or not record.no_auth_runtime
                or not record.no_backend_route
                or not record.no_control_center_control
                or not record.no_dependency
                or not record.no_production_authority
                or record.enterprise_runtime_started
                or record.pro_runtime_started
                or record.plan_enforcement_performed
                or record.billing_runtime_started
                or record.account_tenant_runtime_started
                or record.auth_runtime_started
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.beta_release_enabled
                or record.production_authority_granted
                or "M145_ENTERPRISE_PRO_SAFETY_MODES_REVIEW_ONLY"
                not in record.reason_codes
                or "M145_M101_M144_COVERED" not in record.reason_codes
                or "M145_DISABLED_BY_DEFAULT" not in record.reason_codes
                or "M145_NO_ENTERPRISE_RUNTIME" not in record.reason_codes
                or "M145_NO_PRO_RUNTIME" not in record.reason_codes
                or "M145_NO_PLAN_ENFORCEMENT" not in record.reason_codes
                or "M145_NO_BILLING_RUNTIME" not in record.reason_codes
                or "M145_NO_ACCOUNT_TENANT_RUNTIME" not in record.reason_codes
                or "M145_NO_AUTH_RUNTIME" not in record.reason_codes
                or "M145_NO_BACKEND_ROUTE" not in record.reason_codes
                or "M145_NO_PRODUCTION_AUTHORITY" not in record.reason_codes
                or "M146_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M145 Enterprise/Pro safety modes record is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"enterprise_runtime_started": True},
                    "M145_ENTERPRISE_RUNTIME_DENIED",
                ),
                ({"pro_runtime_started": True}, "M145_PRO_RUNTIME_DENIED"),
                (
                    {"plan_enforcement_performed": True},
                    "M145_PLAN_ENFORCEMENT_DENIED",
                ),
                ({"billing_runtime_started": True}, "M145_BILLING_RUNTIME_DENIED"),
                (
                    {"account_tenant_runtime_started": True},
                    "M145_ACCOUNT_TENANT_RUNTIME_DENIED",
                ),
                ({"auth_runtime_started": True}, "M145_AUTH_RUNTIME_DENIED"),
                ({"backend_route_added": True}, "M145_BACKEND_ROUTE_DENIED"),
                ({"dependency_added": True}, "M145_DEPENDENCY_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M145_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_enterprise_pro_safety_modes_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M145 unsafe safety mode mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M145 unsafe safety mode mutation raised {exc!s}"
                        )
        except Exception as exc:
            failures.append(f"M145 safety mode validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "enterprise/pro safety modes",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "safety-modes-only",
            "disabled by default",
            "route-free",
            "no-effect",
            "accepted m101-m144",
            "enterprise safety mode refs",
            "pro safety mode refs",
            "workspace boundary refs",
            "role policy refs",
            "authority ceiling refs",
            "feature availability refs",
            "escalation policy refs",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no enterprise runtime",
            "no pro runtime",
            "no plan enforcement",
            "no billing runtime",
            "no billing plan boundary",
            "no account tenant runtime",
            "no auth runtime",
            "no backend route",
            "no control center control",
            "no dependency",
            "no beta release",
            "no production authority",
            "m146 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M145 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m145_enterprise_pro_safety_modes_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "enterprise_runtime_enabled=True",
            "pro_runtime_enabled=True",
            "safety_mode_runtime_enabled=True",
            "plan_enforcement_enabled=True",
            "billing_runtime_enabled=True",
            "billing_plan_boundary_enabled=True",
            "account_tenant_runtime_enabled=True",
            "role_runtime_enabled=True",
            "workspace_sharing_enabled=True",
            "auth_runtime_enabled=True",
            "login_enabled=True",
            "connector_runtime_enabled=True",
            "plugin_marketplace_runtime_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_action_enabled=True",
            "connector_action_enabled=True",
            "network_access_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "dependency_added=True",
            "beta_release_enabled=True",
            "production_authority_granted=True",
            "enterprise_runtime_started=True",
            "pro_runtime_started=True",
            "plan_enforcement_performed=True",
            "billing_runtime_started=True",
            "account_tenant_runtime_started=True",
            "auth_runtime_started=True",
            "/enterprise/runtime",
            "/enterprise/pro/enable",
            "/safety-modes/enable",
            "/safety-modes/enforce",
            "/plans/enforce",
            "/billing/runtime",
            "/billing/plans",
            "/accounts/tenants",
            "/auth/login",
            "/workspace/share",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/productization/__init__.py",
            "src/ultimate_ai_agent/core/productization/enterprise_pro_safety_modes.py",
            "src/ultimate_ai_agent/core/productization/plugin_marketplace_policy_draft.py",
            "src/ultimate_ai_agent/core/productization/alpha_ui_app_readiness.py",
            "src/ultimate_ai_agent/core/productization/alpha_privacy_review.py",
            "src/ultimate_ai_agent/core/productization/multi_user_product_boundary.py",
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
                if ".test." in rel or _is_static_safety_scan_allowed_file(
                    rel, allowed_files
                ):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M145 forbidden safety mode fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m145_enterprise_pro_safety_modes_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m145_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M145 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m145_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
        ]
        failures = [
            f"missing M145 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m145" not in text or "enterprise/pro safety modes" not in text:
            failures.append("active docs do not identify Checkpoint M145")
        if (
            "m145 is implemented/released" not in text
            and "checkpoint m145 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M145 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m144",
                "pre-alpha checkpoint",
                "m144",
                "plugin marketplace policy draft",
                "implemented/released",
            ),
            (
                "checkpoint m145",
                "pre-alpha checkpoint",
                "m145",
                "enterprise/pro safety modes",
                "implemented/released",
            ),
            (
                "checkpoint m146",
                "pre-alpha checkpoint",
                "m146",
                "billing/plan boundary, if needed",
                "implemented/released",
            ),
            (
                "checkpoint m147",
                "pre-alpha checkpoint",
                "m147",
                "public docs + wiki readiness",
                "implemented/released",
            ),
            (
                "checkpoint m148",
                "pre-alpha checkpoint",
                "m148",
                "external security review",
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
                    f"active docs missing expected M145/M146/M147/M148-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "billing runtime is implemented",
            "billing plan boundary is implemented",
            "plan enforcement is implemented",
            "enterprise runtime is implemented",
            "pro runtime is implemented",
            "account tenant runtime is implemented",
            "auth runtime is implemented",
            "beta is released",
            "production authority is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m146 dependency is added",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M145 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m146_billing_plan_boundary_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/productization/billing_plan_boundary.py",
            "docs/productization/BILLING_PLAN_BOUNDARY.md",
            "docs/productization/BILLING_PLAN_BOUNDARY_POLICY.md",
            "docs/productization/BILLING_PLAN_BOUNDARY_AUTHORITY_BOUNDARY.md",
            "docs/productization/BILLING_PLAN_BOUNDARY_RECEIPT_PLAN.md",
            "docs/productization/BILLING_PLAN_BOUNDARY_NON_GOALS.md",
            "docs/productization/M146_TO_M147_BOUNDARY.md",
            "docs/release_notes/checkpoint_m146.md",
            "docs/archive/checkpoints/m146/README_IMPORT.md",
            "docs/archive/checkpoints/m146/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m146_billing_plan_boundary.py",
            "tests/test_m146_gate_integration.py",
        ]
        failures = [
            f"missing M146 billing/plan boundary file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m146_billing_plan_boundary import _request
            from ultimate_ai_agent.core.productization import (
                BillingPlanBoundaryStatus,
                build_billing_plan_boundary_record,
                validate_billing_plan_boundary_record,
            )

            record = build_billing_plan_boundary_record(_request())
            if (
                record.status != BillingPlanBoundaryStatus.boundary_recorded
                or not record.contract_only
                or not record.review_only
                or not record.deterministic
                or not record.local_only
                or not record.safe_refs_only
                or not record.billing_boundary_only
                or not record.disabled_by_default
                or not record.m101_m145_covered
                or not record.billing_boundaries_bound
                or not record.plan_boundaries_bound
                or not record.entitlement_boundaries_bound
                or not record.pricing_disclosures_bound
                or not record.payment_provider_boundaries_bound
                or not record.upgrade_downgrade_policies_bound
                or not record.support_refund_policies_bound
                or not record.audit_replay_bound
                or not record.revocation_bound
                or not record.no_effect_receipt_required
                or not record.no_payment_processing
                or not record.no_checkout_runtime
                or not record.no_plan_enforcement
                or not record.no_billing_runtime
                or not record.no_account_plan_runtime
                or not record.no_entitlement_runtime
                or not record.no_auth_runtime
                or not record.no_backend_route
                or not record.no_control_center_control
                or not record.no_dependency
                or not record.no_production_authority
                or record.payment_processing_started
                or record.checkout_runtime_started
                or record.subscription_management_started
                or record.plan_enforcement_performed
                or record.billing_runtime_started
                or record.external_billing_provider_performed
                or record.account_plan_runtime_started
                or record.entitlement_runtime_started
                or record.pricing_runtime_performed
                or record.auth_runtime_started
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.beta_release_enabled
                or record.production_authority_granted
                or "M146_BILLING_PLAN_BOUNDARY_REVIEW_ONLY" not in record.reason_codes
                or "M146_M101_M145_COVERED" not in record.reason_codes
                or "M146_DISABLED_BY_DEFAULT" not in record.reason_codes
                or "M146_NO_PAYMENT_PROCESSING" not in record.reason_codes
                or "M146_NO_CHECKOUT_RUNTIME" not in record.reason_codes
                or "M146_NO_PLAN_ENFORCEMENT" not in record.reason_codes
                or "M146_NO_BILLING_RUNTIME" not in record.reason_codes
                or "M146_NO_ACCOUNT_PLAN_RUNTIME" not in record.reason_codes
                or "M146_NO_AUTH_RUNTIME" not in record.reason_codes
                or "M146_NO_BACKEND_ROUTE" not in record.reason_codes
                or "M146_NO_PRODUCTION_AUTHORITY" not in record.reason_codes
                or "M147_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M146 billing/plan boundary record is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"payment_processing_started": True},
                    "M146_PAYMENT_PROCESSING_DENIED",
                ),
                ({"checkout_runtime_started": True}, "M146_CHECKOUT_RUNTIME_DENIED"),
                (
                    {"subscription_management_started": True},
                    "M146_SUBSCRIPTION_MANAGEMENT_DENIED",
                ),
                (
                    {"plan_enforcement_performed": True},
                    "M146_PLAN_ENFORCEMENT_DENIED",
                ),
                ({"billing_runtime_started": True}, "M146_BILLING_RUNTIME_DENIED"),
                (
                    {"external_billing_provider_performed": True},
                    "M146_EXTERNAL_BILLING_PROVIDER_DENIED",
                ),
                (
                    {"account_plan_runtime_started": True},
                    "M146_ACCOUNT_PLAN_RUNTIME_DENIED",
                ),
                (
                    {"entitlement_runtime_started": True},
                    "M146_ENTITLEMENT_RUNTIME_DENIED",
                ),
                ({"pricing_runtime_performed": True}, "M146_PRICING_RUNTIME_DENIED"),
                ({"auth_runtime_started": True}, "M146_AUTH_RUNTIME_DENIED"),
                ({"backend_route_added": True}, "M146_BACKEND_ROUTE_DENIED"),
                ({"dependency_added": True}, "M146_DEPENDENCY_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M146_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_billing_plan_boundary_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M146 unsafe billing/plan mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M146 unsafe billing/plan mutation raised {exc!s}"
                        )
        except Exception as exc:
            failures.append(f"M146 billing/plan boundary validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "billing/plan boundary",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "billing-boundary-only",
            "disabled by default",
            "route-free",
            "no-effect",
            "accepted m101-m145",
            "billing boundary refs",
            "plan boundary refs",
            "entitlement boundary refs",
            "pricing disclosure refs",
            "payment provider boundary refs",
            "upgrade downgrade policy refs",
            "support refund policy refs",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no payment processing",
            "no checkout runtime",
            "no subscription management",
            "no plan enforcement",
            "no billing runtime",
            "no external billing provider",
            "no account plan runtime",
            "no entitlement runtime",
            "no auth runtime",
            "no backend route",
            "no control center control",
            "no dependency",
            "no beta release",
            "no production authority",
            "m147 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M146 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m146_billing_plan_boundary_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "payment_processing_enabled=True",
            "checkout_runtime_enabled=True",
            "subscription_management_enabled=True",
            "plan_enforcement_enabled=True",
            "billing_runtime_enabled=True",
            "external_billing_provider_enabled=True",
            "account_plan_runtime_enabled=True",
            "entitlement_runtime_enabled=True",
            "pricing_runtime_enabled=True",
            "auth_runtime_enabled=True",
            "login_enabled=True",
            "connector_runtime_enabled=True",
            "plugin_marketplace_runtime_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_action_enabled=True",
            "connector_action_enabled=True",
            "network_access_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "dependency_added=True",
            "beta_release_enabled=True",
            "production_authority_granted=True",
            "payment_processing_started=True",
            "checkout_runtime_started=True",
            "subscription_management_started=True",
            "plan_enforcement_performed=True",
            "billing_runtime_started=True",
            "external_billing_provider_performed=True",
            "account_plan_runtime_started=True",
            "entitlement_runtime_started=True",
            "pricing_runtime_performed=True",
            "auth_runtime_started=True",
            "/billing/runtime",
            "/billing/checkout",
            "/billing/subscriptions",
            "/billing/invoices",
            "/plans/enforce",
            "/payments/process",
            "/checkout/session",
            "/subscriptions/manage",
            "/entitlements/runtime",
            "/account/plans",
            "/external-billing-provider",
            "/stripe",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/productization/__init__.py",
            "src/ultimate_ai_agent/core/productization/billing_plan_boundary.py",
            "src/ultimate_ai_agent/core/productization/enterprise_pro_safety_modes.py",
            "src/ultimate_ai_agent/core/productization/plugin_marketplace_policy_draft.py",
            "src/ultimate_ai_agent/core/productization/alpha_ui_app_readiness.py",
            "src/ultimate_ai_agent/core/productization/alpha_privacy_review.py",
            "src/ultimate_ai_agent/core/productization/multi_user_product_boundary.py",
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
                if ".test." in rel or _is_static_safety_scan_allowed_file(
                    rel, allowed_files
                ):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M146 forbidden billing/plan fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m146_billing_plan_boundary_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m146_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M146 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
