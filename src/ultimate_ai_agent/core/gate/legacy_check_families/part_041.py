from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart041Mixin:
    """Legacy checks from m146_roadmap_currentness through m149_roadmap_currentness."""
    def check_m146_roadmap_currentness(
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
            f"missing M146 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m146" not in text or "billing/plan boundary" not in text:
            failures.append("active docs do not identify Checkpoint M146")
        if (
            "m146 is implemented/released" not in text
            and "checkpoint m146 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M146 implemented/released")
        for version_label, product_target, milestone, title, status in [
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
                    f"active docs missing expected M146/M147/M148-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "payment processing is implemented",
            "checkout runtime is implemented",
            "subscription management is implemented",
            "plan enforcement is implemented",
            "billing runtime is implemented",
            "external billing provider is implemented",
            "account plan runtime is implemented",
            "entitlement runtime is implemented",
            "pricing runtime is implemented",
            "beta is released",
            "production authority is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m147 dependency is added",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M146 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m147_public_docs_wiki_readiness_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/productization/public_docs_wiki_readiness.py",
            "docs/productization/PUBLIC_DOCS_WIKI_READINESS.md",
            "docs/productization/PUBLIC_DOCS_WIKI_READINESS_POLICY.md",
            "docs/productization/PUBLIC_DOCS_WIKI_READINESS_AUTHORITY_BOUNDARY.md",
            "docs/productization/PUBLIC_DOCS_WIKI_READINESS_RECEIPT_PLAN.md",
            "docs/productization/PUBLIC_DOCS_WIKI_READINESS_NON_GOALS.md",
            "docs/productization/M147_TO_M148_BOUNDARY.md",
            "docs/release_notes/checkpoint_m147.md",
            "docs/archive/checkpoints/m147/README_IMPORT.md",
            "docs/archive/checkpoints/m147/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m147_public_docs_wiki_readiness.py",
            "tests/test_m147_gate_integration.py",
        ]
        failures = [
            f"missing M147 public docs + wiki readiness file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m147_public_docs_wiki_readiness import _request
            from ultimate_ai_agent.core.productization import (
                PublicDocsWikiReadinessStatus,
                build_public_docs_wiki_readiness_record,
                validate_public_docs_wiki_readiness_record,
            )

            record = build_public_docs_wiki_readiness_record(_request())
            if (
                record.status != PublicDocsWikiReadinessStatus.readiness_recorded
                or not record.contract_only
                or not record.review_only
                or not record.deterministic
                or not record.local_only
                or not record.safe_refs_only
                or not record.docs_readiness_only
                or not record.disabled_by_default
                or not record.m101_m146_covered
                or not record.public_docs_bound
                or not record.wiki_readiness_bound
                or not record.docs_indexes_bound
                or not record.canonical_maps_bound
                or not record.release_notes_bound
                or not record.disclosure_reviews_bound
                or not record.publishing_checklists_bound
                or not record.no_public_publish
                or not record.no_wiki_publish
                or not record.no_wiki_automation
                or not record.no_github_wiki_runtime
                or not record.no_docs_site_deploy
                or not record.no_external_distribution
                or not record.no_artifact_upload
                or not record.no_release_publish
                or not record.no_docs_runtime
                or not record.no_auth_runtime
                or not record.no_backend_route
                or not record.no_control_center_control
                or not record.no_dependency
                or not record.no_production_authority
                or record.public_publish_started
                or record.wiki_publish_started
                or record.wiki_automation_started
                or record.github_wiki_runtime_performed
                or record.docs_site_deploy_started
                or record.external_distribution_performed
                or record.artifact_upload_started
                or record.release_publish_started
                or record.docs_runtime_performed
                or record.auth_runtime_started
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.beta_release_enabled
                or record.production_authority_granted
                or "M147_PUBLIC_DOCS_WIKI_READINESS_REVIEW_ONLY"
                not in record.reason_codes
                or "M147_M101_M146_COVERED" not in record.reason_codes
                or "M147_DISABLED_BY_DEFAULT" not in record.reason_codes
                or "M147_NO_PUBLIC_PUBLISH" not in record.reason_codes
                or "M147_NO_WIKI_PUBLISH" not in record.reason_codes
                or "M147_NO_WIKI_AUTOMATION" not in record.reason_codes
                or "M147_NO_GITHUB_WIKI_RUNTIME" not in record.reason_codes
                or "M147_NO_DOCS_SITE_DEPLOY" not in record.reason_codes
                or "M147_NO_EXTERNAL_DISTRIBUTION" not in record.reason_codes
                or "M147_NO_ARTIFACT_UPLOAD" not in record.reason_codes
                or "M147_NO_RELEASE_PUBLISH" not in record.reason_codes
                or "M147_NO_DOCS_RUNTIME" not in record.reason_codes
                or "M147_NO_AUTH_RUNTIME" not in record.reason_codes
                or "M147_NO_BACKEND_ROUTE" not in record.reason_codes
                or "M147_NO_PRODUCTION_AUTHORITY" not in record.reason_codes
                or "M148_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M147 public docs + wiki readiness record is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"public_publish_started": True}, "M147_PUBLIC_PUBLISH_DENIED"),
                ({"wiki_publish_started": True}, "M147_WIKI_PUBLISH_DENIED"),
                ({"wiki_automation_started": True}, "M147_WIKI_AUTOMATION_DENIED"),
                (
                    {"github_wiki_runtime_performed": True},
                    "M147_GITHUB_WIKI_RUNTIME_DENIED",
                ),
                ({"docs_site_deploy_started": True}, "M147_DOCS_SITE_DEPLOY_DENIED"),
                (
                    {"external_distribution_performed": True},
                    "M147_EXTERNAL_DISTRIBUTION_DENIED",
                ),
                ({"artifact_upload_started": True}, "M147_ARTIFACT_UPLOAD_DENIED"),
                ({"release_publish_started": True}, "M147_RELEASE_PUBLISH_DENIED"),
                ({"docs_runtime_performed": True}, "M147_DOCS_RUNTIME_DENIED"),
                ({"auth_runtime_started": True}, "M147_AUTH_RUNTIME_DENIED"),
                ({"backend_route_added": True}, "M147_BACKEND_ROUTE_DENIED"),
                ({"dependency_added": True}, "M147_DEPENDENCY_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M147_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_public_docs_wiki_readiness_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M147 unsafe public-docs mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M147 unsafe public-docs mutation raised {exc!s}"
                        )
        except Exception as exc:
            failures.append(f"M147 public docs + wiki validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "public docs + wiki readiness",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "docs-readiness-only",
            "disabled by default",
            "route-free",
            "no-effect",
            "accepted m101-m146",
            "public doc refs",
            "wiki readiness refs",
            "docs index refs",
            "canonical map refs",
            "release note refs",
            "disclosure review refs",
            "publishing checklist refs",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no public publishing",
            "no wiki publishing",
            "no wiki automation",
            "no github wiki runtime",
            "no docs-site deploy",
            "no external distribution",
            "no artifact upload",
            "no release publishing",
            "no docs runtime",
            "no auth runtime",
            "no backend route",
            "no control center control",
            "no dependency",
            "no beta release",
            "no production authority",
            "m148 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M147 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m147_public_docs_wiki_readiness_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "public_publish_enabled=True",
            "wiki_publish_enabled=True",
            "wiki_automation_enabled=True",
            "github_wiki_runtime_enabled=True",
            "docs_site_deploy_enabled=True",
            "external_distribution_enabled=True",
            "artifact_upload_enabled=True",
            "release_publish_enabled=True",
            "docs_runtime_enabled=True",
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
            "public_publish_started=True",
            "wiki_publish_started=True",
            "wiki_automation_started=True",
            "github_wiki_runtime_performed=True",
            "docs_site_deploy_started=True",
            "external_distribution_performed=True",
            "artifact_upload_started=True",
            "release_publish_started=True",
            "docs_runtime_performed=True",
            "auth_runtime_started=True",
            "/public-docs/publish",
            "/public-docs/deploy",
            "/docs/publish",
            "/docs/deploy",
            "/wiki/publish",
            "/wiki/sync",
            "/wiki/automation",
            "/github/wiki",
            "/artifacts/upload",
            "/release/publish",
            "/distribution/publish",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/productization/__init__.py",
            "src/ultimate_ai_agent/core/productization/public_docs_wiki_readiness.py",
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
                            f"M147 forbidden public-docs/wiki fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m147_public_docs_wiki_readiness_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m147_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M147 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m147_roadmap_currentness(
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
            f"missing M147 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m147" not in text or "public docs + wiki readiness" not in text:
            failures.append("active docs do not identify Checkpoint M147")
        if (
            "m147 is implemented/released" not in text
            and "checkpoint m147 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M147 implemented/released")
        for version_label, product_target, milestone, title, status in [
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
                    f"active docs missing expected M147/M148-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "public publishing is implemented",
            "wiki publishing is implemented",
            "wiki automation is implemented",
            "github wiki runtime is implemented",
            "docs-site deploy is implemented",
            "external distribution is implemented",
            "artifact upload is implemented",
            "release publishing is implemented",
            "docs runtime is implemented",
            "beta is released",
            "production authority is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m148 dependency is added",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M147 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m148_external_security_review_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/productization/external_security_review.py",
            "docs/productization/EXTERNAL_SECURITY_REVIEW.md",
            "docs/productization/EXTERNAL_SECURITY_REVIEW_POLICY.md",
            "docs/productization/EXTERNAL_SECURITY_REVIEW_AUTHORITY_BOUNDARY.md",
            "docs/productization/EXTERNAL_SECURITY_REVIEW_RECEIPT_PLAN.md",
            "docs/productization/EXTERNAL_SECURITY_REVIEW_NON_GOALS.md",
            "docs/productization/M148_TO_M149_BOUNDARY.md",
            "docs/release_notes/checkpoint_m148.md",
            "docs/archive/checkpoints/m148/README_IMPORT.md",
            "docs/archive/checkpoints/m148/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m148_external_security_review.py",
            "tests/test_m148_gate_integration.py",
        ]
        failures = [
            f"missing M148 external security review file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m148_external_security_review import _request
            from ultimate_ai_agent.core.productization import (
                ExternalSecurityReviewStatus,
                build_external_security_review_record,
                validate_external_security_review_record,
            )

            record = build_external_security_review_record(_request())
            if (
                record.status != ExternalSecurityReviewStatus.readiness_recorded
                or not record.contract_only
                or not record.review_only
                or not record.deterministic
                or not record.local_only
                or not record.safe_refs_only
                or not record.external_security_review_only
                or not record.disabled_by_default
                or not record.m101_m147_covered
                or not record.security_reviews_bound
                or not record.threat_model_bound
                or not record.review_scopes_bound
                or not record.evidence_indexes_bound
                or not record.finding_summaries_bound
                or not record.disclosure_reviews_bound
                or not record.remediation_plans_bound
                or not record.no_external_vendor_handoff
                or not record.no_security_vendor_handoff
                or not record.no_external_review_automation
                or not record.no_scanner_runtime
                or not record.no_vulnerability_scan
                or not record.no_repository_export
                or not record.no_artifact_export
                or not record.no_issue_export
                or not record.no_security_review_runtime
                or not record.no_auth_runtime
                or not record.no_backend_route
                or not record.no_control_center_control
                or not record.no_dependency
                or not record.no_production_authority
                or record.external_vendor_handoff_started
                or record.security_vendor_handoff_started
                or record.external_review_automation_started
                or record.scanner_runtime_performed
                or record.vulnerability_scan_started
                or record.repository_export_performed
                or record.artifact_export_started
                or record.issue_export_started
                or record.security_review_runtime_performed
                or record.auth_runtime_started
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.beta_release_enabled
                or record.production_authority_granted
                or "M148_EXTERNAL_SECURITY_REVIEW_REVIEW_ONLY"
                not in record.reason_codes
                or "M148_M101_M147_COVERED" not in record.reason_codes
                or "M148_DISABLED_BY_DEFAULT" not in record.reason_codes
                or "M148_NO_EXTERNAL_VENDOR_HANDOFF" not in record.reason_codes
                or "M148_NO_SECURITY_VENDOR_HANDOFF" not in record.reason_codes
                or "M148_NO_EXTERNAL_REVIEW_AUTOMATION" not in record.reason_codes
                or "M148_NO_SCANNER_RUNTIME" not in record.reason_codes
                or "M148_NO_VULNERABILITY_SCAN" not in record.reason_codes
                or "M148_NO_REPOSITORY_EXPORT" not in record.reason_codes
                or "M148_NO_ARTIFACT_EXPORT" not in record.reason_codes
                or "M148_NO_ISSUE_EXPORT" not in record.reason_codes
                or "M148_NO_SECURITY_REVIEW_RUNTIME" not in record.reason_codes
                or "M148_NO_AUTH_RUNTIME" not in record.reason_codes
                or "M148_NO_BACKEND_ROUTE" not in record.reason_codes
                or "M148_NO_PRODUCTION_AUTHORITY" not in record.reason_codes
                or "M149_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M148 external security review record is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"external_vendor_handoff_started": True},
                    "M148_EXTERNAL_VENDOR_HANDOFF_DENIED",
                ),
                (
                    {"security_vendor_handoff_started": True},
                    "M148_SECURITY_VENDOR_HANDOFF_DENIED",
                ),
                (
                    {"external_review_automation_started": True},
                    "M148_EXTERNAL_REVIEW_AUTOMATION_DENIED",
                ),
                ({"scanner_runtime_performed": True}, "M148_SCANNER_RUNTIME_DENIED"),
                (
                    {"vulnerability_scan_started": True},
                    "M148_VULNERABILITY_SCAN_DENIED",
                ),
                (
                    {"repository_export_performed": True},
                    "M148_REPOSITORY_EXPORT_DENIED",
                ),
                ({"artifact_export_started": True}, "M148_ARTIFACT_EXPORT_DENIED"),
                ({"issue_export_started": True}, "M148_ISSUE_EXPORT_DENIED"),
                (
                    {"security_review_runtime_performed": True},
                    "M148_SECURITY_REVIEW_RUNTIME_DENIED",
                ),
                ({"auth_runtime_started": True}, "M148_AUTH_RUNTIME_DENIED"),
                ({"backend_route_added": True}, "M148_BACKEND_ROUTE_DENIED"),
                ({"dependency_added": True}, "M148_DEPENDENCY_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M148_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_external_security_review_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M148 unsafe security-review mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M148 unsafe security-review mutation raised {exc!s}"
                        )
        except Exception as exc:
            failures.append(f"M148 external security review validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "external security review",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "external-security-review-only",
            "disabled by default",
            "route-free",
            "no-effect",
            "accepted m101-m147",
            "security review refs",
            "threat model refs",
            "review scope refs",
            "evidence index refs",
            "finding summary refs",
            "disclosure review refs",
            "remediation plan refs",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no external vendor handoff",
            "no security vendor handoff",
            "no external review automation",
            "no scanner runtime",
            "no vulnerability scan",
            "no repository export",
            "no artifact export",
            "no issue export",
            "no security review runtime",
            "no auth runtime",
            "no backend route",
            "no control center control",
            "no dependency",
            "no beta release",
            "no production authority",
            "m149 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M148 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m148_external_security_review_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "external_vendor_handoff_enabled=True",
            "security_vendor_handoff_enabled=True",
            "external_review_automation_enabled=True",
            "scanner_runtime_enabled=True",
            "vulnerability_scan_enabled=True",
            "repository_export_enabled=True",
            "artifact_export_enabled=True",
            "issue_export_enabled=True",
            "security_review_runtime_enabled=True",
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
            "external_vendor_handoff_started=True",
            "security_vendor_handoff_started=True",
            "external_review_automation_started=True",
            "scanner_runtime_performed=True",
            "vulnerability_scan_started=True",
            "repository_export_performed=True",
            "artifact_export_started=True",
            "issue_export_started=True",
            "security_review_runtime_performed=True",
            "auth_runtime_started=True",
            "/external-security-review",
            "/security/review/start",
            "/security/review/export",
            "/security/review/runtime",
            "/security/vendor",
            "/security/scanner/run",
            "/security/vulnerability-scan",
            "/security/findings/export",
            "/security/audit/upload",
            "/repository/export",
            "/source/export",
            "/issues/export",
            "/artifacts/export",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/productization/__init__.py",
            "src/ultimate_ai_agent/core/productization/external_security_review.py",
            "src/ultimate_ai_agent/core/productization/public_docs_wiki_readiness.py",
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
                            f"M148 forbidden external-security fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m148_external_security_review_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m148_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M148 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m148_roadmap_currentness(
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
            f"missing M148 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m148" not in text or "external security review" not in text:
            failures.append("active docs do not identify Checkpoint M148")
        if (
            "m148 is implemented/released" not in text
            and "checkpoint m148 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M148 implemented/released")
        for version_label, product_target, milestone, title, status in [
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
                "checkpoint m149",
                "pre-alpha checkpoint",
                "m149",
                "alpha release candidate freeze",
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
                    f"active docs missing expected M148/M149/M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "external vendor handoff is implemented",
            "security vendor handoff is implemented",
            "external review automation is implemented",
            "scanner runtime is implemented",
            "vulnerability scan is implemented",
            "repository export is implemented",
            "artifact export is implemented",
            "issue export is implemented",
            "security review runtime is implemented",
            "beta is released",
            "production authority is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m149 dependency is added",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M148 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m149_alpha_release_candidate_freeze_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/productization/alpha_release_candidate_freeze.py",
            "docs/productization/ALPHA_RELEASE_CANDIDATE_FREEZE.md",
            "docs/productization/ALPHA_RELEASE_CANDIDATE_FREEZE_POLICY.md",
            "docs/productization/ALPHA_RELEASE_CANDIDATE_FREEZE_AUTHORITY_BOUNDARY.md",
            "docs/productization/ALPHA_RELEASE_CANDIDATE_FREEZE_RECEIPT_PLAN.md",
            "docs/productization/ALPHA_RELEASE_CANDIDATE_FREEZE_NON_GOALS.md",
            "docs/productization/M149_TO_M150_BOUNDARY.md",
            "docs/release_notes/checkpoint_m149.md",
            "docs/archive/checkpoints/m149/README_IMPORT.md",
            "docs/archive/checkpoints/m149/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m149_alpha_release_candidate_freeze.py",
            "tests/test_m149_gate_integration.py",
        ]
        failures = [
            f"missing M149 alpha release candidate freeze file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m149_alpha_release_candidate_freeze import _request
            from ultimate_ai_agent.core.productization import (
                AlphaReleaseCandidateFreezeStatus,
                build_alpha_release_candidate_freeze_record,
                validate_alpha_release_candidate_freeze_record,
            )

            record = build_alpha_release_candidate_freeze_record(_request())
            if (
                record.status != AlphaReleaseCandidateFreezeStatus.freeze_recorded
                or not record.contract_only
                or not record.review_only
                or not record.freeze_only
                or not record.deterministic
                or not record.local_only
                or not record.safe_refs_only
                or not record.alpha_release_candidate_freeze_only
                or not record.disabled_by_default
                or not record.m101_m148_covered
                or not record.release_candidates_bound
                or not record.freeze_checklists_bound
                or not record.alpha_readiness_bound
                or not record.evidence_indexes_bound
                or not record.blocker_summaries_bound
                or not record.signoff_reviews_bound
                or not record.m150_promotion_gates_bound
                or not record.no_release_publication
                or not record.no_release_tag
                or not record.no_tag_creation
                or not record.no_artifact_build
                or not record.no_artifact_upload
                or not record.no_artifact_export
                or not record.no_external_distribution
                or not record.no_app_store_submission
                or not record.no_testflight_submission
                or not record.no_beta_release
                or not record.no_m150_release
                or not record.no_release_automation
                or not record.no_backend_route
                or not record.no_control_center_control
                or not record.no_dependency
                or not record.no_production_authority
                or record.release_publication_started
                or record.release_tag_created
                or record.tag_creation_performed
                or record.artifact_build_performed
                or record.artifact_upload_started
                or record.artifact_export_started
                or record.external_distribution_started
                or record.app_store_submission_started
                or record.testflight_submission_started
                or record.beta_release_enabled
                or record.m150_release_performed
                or record.release_automation_started
                or record.auth_runtime_started
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.production_authority_granted
                or "M149_ALPHA_RELEASE_CANDIDATE_FREEZE_REVIEW_ONLY"
                not in record.reason_codes
                or "M149_M101_M148_COVERED" not in record.reason_codes
                or "M149_FREEZE_ONLY" not in record.reason_codes
                or "M149_DISABLED_BY_DEFAULT" not in record.reason_codes
                or "M149_NO_RELEASE_PUBLICATION" not in record.reason_codes
                or "M149_NO_RELEASE_TAG" not in record.reason_codes
                or "M149_NO_TAG_CREATION" not in record.reason_codes
                or "M149_NO_ARTIFACT_BUILD" not in record.reason_codes
                or "M149_NO_ARTIFACT_UPLOAD" not in record.reason_codes
                or "M149_NO_ARTIFACT_EXPORT" not in record.reason_codes
                or "M149_NO_EXTERNAL_DISTRIBUTION" not in record.reason_codes
                or "M149_NO_APP_STORE_SUBMISSION" not in record.reason_codes
                or "M149_NO_TESTFLIGHT_SUBMISSION" not in record.reason_codes
                or "M149_NO_BETA_RELEASE" not in record.reason_codes
                or "M149_NO_M150_RELEASE" not in record.reason_codes
                or "M149_NO_RELEASE_AUTOMATION" not in record.reason_codes
                or "M149_NO_BACKEND_ROUTE" not in record.reason_codes
                or "M149_NO_PRODUCTION_AUTHORITY" not in record.reason_codes
                or "M150_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M149 alpha release candidate freeze record is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"release_publication_started": True},
                    "M149_RELEASE_PUBLICATION_DENIED",
                ),
                ({"release_tag_created": True}, "M149_RELEASE_TAG_DENIED"),
                ({"tag_creation_performed": True}, "M149_TAG_CREATION_DENIED"),
                ({"artifact_build_performed": True}, "M149_ARTIFACT_BUILD_DENIED"),
                ({"artifact_upload_started": True}, "M149_ARTIFACT_UPLOAD_DENIED"),
                ({"artifact_export_started": True}, "M149_ARTIFACT_EXPORT_DENIED"),
                (
                    {"external_distribution_started": True},
                    "M149_EXTERNAL_DISTRIBUTION_DENIED",
                ),
                (
                    {"app_store_submission_started": True},
                    "M149_APP_STORE_SUBMISSION_DENIED",
                ),
                (
                    {"testflight_submission_started": True},
                    "M149_TESTFLIGHT_SUBMISSION_DENIED",
                ),
                ({"m150_release_performed": True}, "M149_M150_RELEASE_DENIED"),
                (
                    {"release_automation_started": True},
                    "M149_RELEASE_AUTOMATION_DENIED",
                ),
                ({"auth_runtime_started": True}, "M149_AUTH_RUNTIME_DENIED"),
                ({"backend_route_added": True}, "M149_BACKEND_ROUTE_DENIED"),
                ({"dependency_added": True}, "M149_DEPENDENCY_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M149_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_alpha_release_candidate_freeze_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M149 unsafe release-freeze mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M149 unsafe release-freeze mutation raised {exc!s}"
                        )
        except Exception as exc:
            failures.append(
                f"M149 alpha release candidate freeze validation failed: {exc}"
            )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "alpha release candidate freeze",
            "contract-only",
            "review-only",
            "freeze-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "alpha-release-candidate-freeze-only",
            "disabled by default",
            "route-free",
            "no-effect",
            "accepted m101-m148",
            "release candidate refs",
            "freeze checklist refs",
            "alpha readiness refs",
            "evidence index refs",
            "blocker summary refs",
            "signoff review refs",
            "m150 promotion gate refs",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no release publication",
            "no release tag",
            "no tag creation",
            "no artifact build",
            "no artifact upload",
            "no artifact export",
            "no external distribution",
            "no app store submission",
            "no testflight submission",
            "no beta release",
            "no m150 release",
            "no release automation",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "m150 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M149 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m149_alpha_release_candidate_freeze_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "release_publication_enabled=True",
            "release_tag_enabled=True",
            "tag_creation_enabled=True",
            "artifact_build_enabled=True",
            "artifact_upload_enabled=True",
            "artifact_export_enabled=True",
            "external_distribution_enabled=True",
            "app_store_submission_enabled=True",
            "testflight_submission_enabled=True",
            "beta_release_enabled=True",
            "m150_release_enabled=True",
            "release_automation_enabled=True",
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
            "production_authority_granted=True",
            "release_publication_started=True",
            "release_tag_created=True",
            "tag_creation_performed=True",
            "artifact_build_performed=True",
            "artifact_upload_started=True",
            "artifact_export_started=True",
            "external_distribution_started=True",
            "app_store_submission_started=True",
            "testflight_submission_started=True",
            "m150_release_performed=True",
            "release_automation_started=True",
            "auth_runtime_started=True",
            "/alpha-release-candidate-freeze",
            "/release/publish",
            "/release/tag",
            "/release/create-tag",
            "/release/artifact/build",
            "/release/artifact/upload",
            "/release/artifact/export",
            "/distribution/publish",
            "/external-distribution",
            "/app-store/submit",
            "/testflight/submit",
            "/beta/release",
            "/v1-alpha/release",
            "/m150/release",
            "/release/automation",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/productization/__init__.py",
            "src/ultimate_ai_agent/core/productization/alpha_release_candidate_freeze.py",
            "src/ultimate_ai_agent/core/productization/external_security_review.py",
            "src/ultimate_ai_agent/core/productization/public_docs_wiki_readiness.py",
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
                            f"M149 forbidden release-freeze fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m149_alpha_release_candidate_freeze_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m149_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M149 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m149_roadmap_currentness(
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
            f"missing M149 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m149" not in text
            or "alpha release candidate freeze" not in text
        ):
            failures.append("active docs do not identify Checkpoint M149")
        if (
            "m149 is implemented/released" not in text
            and "checkpoint m149 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M149 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m148",
                "pre-alpha checkpoint",
                "m148",
                "external security review",
                "implemented/released",
            ),
            (
                "checkpoint m149",
                "pre-alpha checkpoint",
                "m149",
                "alpha release candidate freeze",
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
                    f"active docs missing expected M149/M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "release publication is implemented",
            "release tag is implemented",
            "tag creation is implemented",
            "artifact build is implemented",
            "artifact upload is implemented",
            "artifact export is implemented",
            "external distribution is implemented",
            "app store submission is implemented",
            "testflight submission is implemented",
            "m150 release is implemented",
            "release automation is implemented",
            "beta is released",
            "production authority is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m150 dependency is added",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M149 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
