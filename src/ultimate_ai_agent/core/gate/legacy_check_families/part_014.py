from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart014Mixin:
    """Legacy checks from m58_roadmap_currentness through m62_roadmap_currentness."""
    def check_m58_roadmap_currentness(
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
            f"missing M58 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.62.0" not in text
            or "m58" not in text
            or "dry-run execution audit harness" not in text
        ):
            failures.append(
                "active docs do not identify v0.62.0/M58 Dry-Run Execution Audit Harness"
            )
        if (
            "m58 is implemented/released" not in text
            and "v0.62.0 implements m58" not in text
        ):
            failures.append("active docs do not mark M58 implemented/released")
        if self._active_version_tuple() >= (0, 63, 0):
            if (
                "m59 is implemented/released" not in text
                and "v0.63.0 implements m59" not in text
            ):
                failures.append("active docs do not mark M59 implemented/released")
            if not self._m60_currentness_marker_present(text):
                failures.append("M60 currentness marker is missing after M59")
        elif "m59-m60 remain planned/provisional" not in text:
            failures.append("M59-M60 must remain planned/provisional after M58")
        for fragment in (
            "m59 is implemented",
            "v0.63.0 implements m59",
            "public github readiness is implemented",
            "m60 is implemented",
            "v0.64.0 implements m60",
            "local developer beta freeze is implemented",
            "production authority is implemented",
            "real execution is implemented",
        ):
            if self._active_version_tuple() >= (0, 63, 0) and fragment in {
                "m59 is implemented",
                "v0.63.0 implements m59",
                "public github readiness is implemented",
            }:
                continue
            if self._active_version_tuple() >= (0, 64, 0) and fragment in {
                "m60 is implemented",
                "v0.64.0 implements m60",
                "local developer beta freeze is implemented",
            }:
                continue
            if fragment in text:
                failures.append(
                    f"M58 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m59_public_github_readiness_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/public_readiness/__init__.py",
            "src/ultimate_ai_agent/core/public_readiness/review.py",
            "docs/public_readiness/PUBLIC_GITHUB_READINESS.md",
            "docs/public_readiness/PUBLIC_GITHUB_READINESS_POLICY.md",
            "docs/public_readiness/PUBLIC_GITHUB_READINESS_AUTHORITY_BOUNDARY.md",
            "docs/public_readiness/M59_TO_M60_BOUNDARY.md",
            "tests/test_m59_public_github_readiness.py",
            "tests/test_m59_gate_integration.py",
        ]
        failures = [
            f"missing M59 public GitHub readiness file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.public_readiness import (
                PublicGitHubReadinessPolicy,
                PublicGitHubReadinessRequest,
                PublicGitHubReadinessStatus,
                build_public_github_readiness_report,
                validate_public_github_readiness_policy,
                validate_public_github_readiness_request,
            )

            request = PublicGitHubReadinessRequest(
                request_ref="public-readiness-request:m59-gate",
                readiness_ref="public-readiness:m59-gate",
                repository_ref="repo:ultimate-ai-agent",
                baseline_ref="baseline:v0.63.0",
                actor_ref="actor:gate-reviewer",
                checklist_refs=[
                    "readiness:docs-current",
                    "readiness:secret-hygiene",
                    "readiness:artifact-hygiene",
                    "readiness:route-boundary",
                    "readiness:dependency-boundary",
                ],
                safe_summary="Gate safe public GitHub readiness review.",
            )
            report = build_public_github_readiness_report(request)
            if report.status != PublicGitHubReadinessStatus.reviewed:
                failures.append(
                    "M59 public readiness report did not return reviewed status"
                )
            if (
                not report.review_only
                or report.publication_performed
                or report.github_push_performed
                or report.github_release_performed
                or report.wiki_automation_performed
                or report.external_service_performed
                or report.production_authority_granted
                or report.side_effects_performed
            ):
                failures.append(
                    "M59 public readiness report performed publication or authority side effects"
                )
            if report.receipt_plan is None:
                failures.append(
                    "M59 public readiness report did not include no-effect receipt plan"
                )
            elif (
                report.receipt_plan.publication_performed
                or report.receipt_plan.side_effects_performed
            ):
                failures.append(
                    "M59 public readiness receipt performed publication side effects"
                )
            for request_update, reason in [
                ({"publication_requested": True}, "PUBLICATION_DENIED"),
                ({"github_push_requested": True}, "GITHUB_PUSH_DENIED"),
                ({"github_release_requested": True}, "GITHUB_RELEASE_DENIED"),
                ({"wiki_automation_requested": True}, "WIKI_AUTOMATION_DENIED"),
                ({"artifact_upload_requested": True}, "ARTIFACT_UPLOAD_DENIED"),
                ({"credential_handling_requested": True}, "CREDENTIAL_HANDLING_DENIED"),
                (
                    {"production_authority_requested": True},
                    "PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                mutated_request = request.model_copy(update=request_update)
                try:
                    validate_public_github_readiness_request(mutated_request)
                    failures.append(
                        f"M59 unsafe public readiness mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M59 unsafe public readiness reason drifted for {reason}: {exc}"
                        )
            try:
                validate_public_github_readiness_policy(
                    PublicGitHubReadinessPolicy(github_push_enabled=True)
                )
                failures.append(
                    "M59 unsafe public readiness policy flag was not denied"
                )
            except ValueError as exc:
                if "GITHUB_PUSH_DENIED" not in str(exc):
                    failures.append(f"M59 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M59 public GitHub readiness validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "public github readiness",
            "review-only",
            "contract-only",
            "no github push",
            "no github release",
            "no wiki automation",
            "no artifact upload",
            "no external service",
            "no credential handling",
            "no production authority",
            "no backend route",
            "no dependency",
            "m60 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M59 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m59_public_github_readiness_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "publication_enabled=True",
            "github_push_enabled=True",
            "github_release_enabled=True",
            "wiki_automation_enabled=True",
            "artifact_upload_enabled=True",
            "external_service_enabled=True",
            "credential_handling_enabled=True",
            "network_access_enabled=True",
            "production_authority_enabled=True",
            "m60_beta_freeze_enabled=True",
            "publication_performed=True",
            "github_push_performed=True",
            "github_release_performed=True",
            "wiki_automation_performed=True",
            "artifact_upload_performed=True",
            "external_service_performed=True",
            "production_authority_granted=True",
            "/github/publish",
            "/github/release",
            "/github/wiki/update",
            "/public/artifacts/upload",
            "/public/release/publish",
            "/release/upload",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/public_readiness/review.py",
            "tests/test_m59_public_github_readiness.py",
            "tests/test_m59_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
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
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M59 forbidden public readiness fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m59_public_github_readiness_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m59_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M59 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m59_roadmap_currentness(
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
            f"missing M59 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.63.0" not in text
            or "m59" not in text
            or "public github readiness" not in text
        ):
            failures.append(
                "active docs do not identify v0.63.0/M59 Public GitHub Readiness"
            )
        if (
            "m59 is implemented/released" not in text
            and "v0.63.0 implements m59" not in text
        ):
            failures.append("active docs do not mark M59 implemented/released")
        if not self._m60_currentness_marker_present(text):
            failures.append("M60 currentness marker is missing after M59")
        for fragment in (
            "m60 is implemented",
            "v0.64.0 implements m60",
            "local developer beta freeze is implemented",
            "production authority is implemented",
            "github publish automation is implemented",
            "wiki automation is implemented",
        ):
            if self._active_version_tuple() >= (0, 64, 0) and fragment in {
                "m60 is implemented",
                "v0.64.0 implements m60",
                "local developer beta freeze is implemented",
            }:
                continue
            if fragment in text:
                failures.append(
                    f"M59 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m60_local_developer_beta_freeze_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/beta_freeze/__init__.py",
            "src/ultimate_ai_agent/core/beta_freeze/review.py",
            "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE.md",
            "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_POLICY.md",
            "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_AUTHORITY_BOUNDARY.md",
            "docs/beta/POST_M60_AUTONOMY_BOUNDARY.md",
            "tests/test_m60_local_developer_beta_freeze.py",
            "tests/test_m60_gate_integration.py",
        ]
        failures = [
            f"missing M60 local developer beta freeze file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.beta_freeze import (
                LocalDeveloperBetaFreezePolicy,
                LocalDeveloperBetaFreezeRequest,
                LocalDeveloperBetaFreezeStatus,
                build_local_developer_beta_freeze_report,
                validate_local_developer_beta_freeze_policy,
                validate_local_developer_beta_freeze_request,
            )

            request = LocalDeveloperBetaFreezeRequest(
                request_ref="beta-freeze-request:m60-gate",
                freeze_ref="beta-freeze:m60-gate",
                baseline_ref="baseline:v0.64.0",
                actor_ref="actor:gate-reviewer",
                checklist_refs=[
                    "beta-freeze:validation-green",
                    "beta-freeze:docs-current",
                    "beta-freeze:route-stable",
                    "beta-freeze:dependency-stable",
                    "beta-freeze:artifact-clean",
                    "beta-freeze:authority-frozen",
                ],
                safe_summary="Gate safe local developer beta freeze review.",
            )
            report = build_local_developer_beta_freeze_report(request)
            if report.status != LocalDeveloperBetaFreezeStatus.frozen:
                failures.append("M60 beta freeze report did not return frozen status")
            if (
                not report.freeze_only
                or not report.local_developer_beta_only
                or report.production_authority_granted
                or report.public_release_performed
                or report.external_distribution_performed
                or report.execution_performed
                or report.post_m60_autonomy_enabled
                or report.side_effects_performed
            ):
                failures.append(
                    "M60 beta freeze report performed release/autonomy/authority side effects"
                )
            if report.receipt_plan is None:
                failures.append(
                    "M60 beta freeze report did not include no-effect receipt plan"
                )
            elif (
                report.receipt_plan.public_release_performed
                or report.receipt_plan.side_effects_performed
            ):
                failures.append(
                    "M60 beta freeze receipt performed release side effects"
                )
            for request_update, reason in [
                ({"public_release_requested": True}, "PUBLIC_RELEASE_DENIED"),
                (
                    {"external_distribution_requested": True},
                    "EXTERNAL_DISTRIBUTION_DENIED",
                ),
                ({"post_m60_autonomy_requested": True}, "POST_M60_AUTONOMY_DENIED"),
                (
                    {"production_authority_requested": True},
                    "PRODUCTION_AUTHORITY_DENIED",
                ),
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                ({"credential_handling_requested": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
            ]:
                mutated_request = request.model_copy(update=request_update)
                try:
                    validate_local_developer_beta_freeze_request(mutated_request)
                    failures.append(
                        f"M60 unsafe beta freeze mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M60 unsafe beta freeze reason drifted for {reason}: {exc}"
                        )
            try:
                validate_local_developer_beta_freeze_policy(
                    LocalDeveloperBetaFreezePolicy(public_release_enabled=True)
                )
                failures.append("M60 unsafe beta freeze policy flag was not denied")
            except ValueError as exc:
                if "PUBLIC_RELEASE_DENIED" not in str(exc):
                    failures.append(f"M60 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M60 local developer beta freeze validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "local developer beta freeze",
            "freeze-only",
            "local developer beta only",
            "review-only",
            "no public release",
            "no external distribution",
            "no post-m60 autonomy",
            "no production authority",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no network tools",
            "no browser automation",
            "no plugin execution",
            "no mobile sensor access",
            "no remote execution",
            "no credential handling",
            "no memory writes",
            "no context injection",
            "no model/provider calls",
            "no backend route",
            "no control center control",
            "no dependency",
            "m61+ remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M60 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m60_local_developer_beta_freeze_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "public_release_enabled=True",
            "external_distribution_enabled=True",
            "post_m60_autonomy_enabled=True",
            "production_authority_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "network_tool_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "mobile_sensor_enabled=True",
            "remote_execution_enabled=True",
            "credential_handling_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "model_provider_call_enabled=True",
            "public_release_performed=True",
            "external_distribution_performed=True",
            "execution_performed=True",
            "production_authority_granted=True",
            "/public/beta/release",
            "/github/release",
            "/autonomy/enable",
            "/remote/execute",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m60_local_developer_beta_freeze.py",
            "tests/test_m60_gate_integration.py",
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
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
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M60 forbidden beta freeze fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m60_local_developer_beta_freeze_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m60_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M60 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m60_final_roadmap_currentness(
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
            f"missing M60 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.64.0" not in text
            or "m60" not in text
            or "local developer beta freeze" not in text
        ):
            failures.append(
                "active docs do not identify v0.64.0/M60 Local Developer Beta Freeze"
            )
        if (
            "m60 is implemented/released" not in text
            and "v0.64.0 implements m60" not in text
        ):
            failures.append("active docs do not mark M60 implemented/released")
        forbidden_fragments = [
            "post-m60 autonomy is implemented",
            "production authority is implemented",
            "public release is implemented",
            "external distribution is implemented",
        ]
        if self._active_version_tuple() < (0, 65, 0):
            forbidden_fragments.extend(["m61 is implemented", "m61-m80 is active"])
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M60 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m61_autonomy_mode_charter_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/modes.py",
            "tests/test_m61_autonomy_mode_charter.py",
            "docs/autonomy/AUTONOMY_MODE_CHARTER.md",
            "docs/autonomy/AUTHORITY_LEVELS.md",
            "docs/autonomy/CAPABILITY_TOGGLE_REGISTRY.md",
            "docs/autonomy/AUTONOMY_CONSENT_REVOCATION_POLICY.md",
            "docs/autonomy/M61_TO_M62_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
        ]
        failures = [
            f"missing M61 autonomy mode charter file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyCapabilityToggle,
                AutonomyModeCharter,
                AutonomyRiskClass,
                build_autonomy_mode_decision,
                validate_autonomy_capability_toggle,
                validate_autonomy_mode_charter,
            )

            charter = validate_autonomy_mode_charter(AutonomyModeCharter())
            if charter.default_mode != AutonomyAuthorityMode.off:
                failures.append("M61 autonomy charter default mode is not OFF")
            if not {
                AutonomyAuthorityMode.off,
                AutonomyAuthorityMode.observe_only,
                AutonomyAuthorityMode.dry_run_plan,
                AutonomyAuthorityMode.ask_before_every_action,
                AutonomyAuthorityMode.scoped_autonomy_window,
                AutonomyAuthorityMode.trusted_recurring_automation,
                AutonomyAuthorityMode.production_authority_later,
            }.issubset(set(charter.available_modes)):
                failures.append("M61 autonomy authority modes are incomplete")
            toggle = AutonomyCapabilityToggle(
                toggle_ref="autonomy-toggle:m61-gate",
                capability_ref="capability:observe-only-review",
                requested_mode=AutonomyAuthorityMode.off,
                actor_ref="actor:gate-reviewer",
                scope_ref="scope:m61-gate",
                resource_refs=["resource:local-prototype"],
                duration_seconds=0,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m61-gate",
                audit_ref="audit:m61-gate",
            )
            decision = build_autonomy_mode_decision(toggle, charter)
            if (
                decision.selected_mode != AutonomyAuthorityMode.off
                or decision.allowed
                or not decision.dry_run_only
                or decision.side_effects_performed
            ):
                failures.append(
                    "M61 autonomy decision granted authority or side effects"
                )
            for update, reason in [
                ({"enabled": True}, "AUTONOMY_TOGGLE_ENABLEMENT_DENIED"),
                (
                    {
                        "requested_mode": AutonomyAuthorityMode.ask_before_every_action,
                        "duration_seconds": 300,
                    },
                    "AUTONOMY_MODE_ENABLEMENT_DENIED",
                ),
                (
                    {"approval_test_ref": "approval_test_:m61"},
                    "APPROVAL_TEST_REF_DENIED",
                ),
                ({"tool_execution_enabled": True}, "TOOL_EXECUTION_DENIED"),
                ({"shell_execution_enabled": True}, "SHELL_EXECUTION_DENIED"),
                ({"network_tool_enabled": True}, "NETWORK_TOOL_DENIED"),
                ({"browser_automation_enabled": True}, "BROWSER_AUTOMATION_DENIED"),
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                mutated_toggle = toggle.model_copy(update=update)
                try:
                    validate_autonomy_capability_toggle(mutated_toggle)
                    failures.append(
                        f"M61 unsafe autonomy toggle mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M61 unsafe autonomy toggle reason drifted for {reason}: {exc}"
                        )
            for update, reason in [
                (
                    {"default_mode": AutonomyAuthorityMode.dry_run_plan},
                    "AUTONOMY_DEFAULT_MODE_OFF_REQUIRED",
                ),
                (
                    {"global_autonomy_switch_enabled": True},
                    "GLOBAL_AUTONOMY_SWITCH_DENIED",
                ),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
                ({"backend_routes_enabled": True}, "BACKEND_ROUTE_DENIED"),
                ({"dependencies_added": True}, "DEPENDENCY_ADDITION_DENIED"),
            ]:
                mutated_charter = charter.model_copy(update=update)
                try:
                    validate_autonomy_mode_charter(mutated_charter)
                    failures.append(
                        f"M61 unsafe autonomy charter mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M61 unsafe autonomy charter reason drifted for {reason}: {exc}"
                        )
        except Exception as exc:
            failures.append(f"M61 autonomy mode charter validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "autonomy mode charter",
            "authority levels",
            "mode 0",
            "mode 1",
            "mode 2",
            "mode 3",
            "mode 4",
            "mode 5",
            "mode 6",
            "default mode off",
            "disabled by default",
            "dry-run first",
            "limited allowlist",
            "explicit approval",
            "scoped autonomy window",
            "audit/replay",
            "revocation",
            "no global autonomy switch",
            "no production authority",
            "no execution",
            "no tool execution",
            "no browser automation",
            "no shell execution",
            "no network tools",
            "no background worker",
            "no autonomous session",
            "no backend route",
            "no dependency",
            "m62 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M61 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m61_autonomy_mode_charter_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "global_autonomy_switch_enabled=True",
            "production_authority_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "network_tool_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "mobile_sensor_enabled=True",
            "remote_execution_enabled=True",
            "background_worker_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "model_provider_call_enabled=True",
            "backend_routes_enabled=True",
            "dependencies_added=True",
            "execution_performed=True",
            "production_authority_granted=True",
            "/autonomy/enable",
            "/autonomy/session/start",
            "/autonomy/execute",
            "/network/fetch",
            "/shell/execute",
            "/browser/click",
            "/plugins/execute",
            "/background/start",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/autonomy/modes.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m61_autonomy_mode_charter.py",
            "tests/test_m61_gate_integration.py",
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
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
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M61 forbidden autonomy fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m61_autonomy_mode_charter_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m61_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M61 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m61_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M61 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.65.0" not in text
            or "m61" not in text
            or "autonomy mode charter" not in text
        ):
            failures.append(
                "active docs do not identify v0.65.0/M61 Autonomy Mode Charter"
            )
        if (
            "m61 is implemented/released" not in text
            and "v0.65.0 implements m61" not in text
        ):
            failures.append("active docs do not mark M61 implemented/released")
        for version_label, milestone, title in [
            ("v0.66.0", "M62", "Scoped Autonomy Session Contracts"),
            ("v0.67.0", "M63", "Autonomy Policy Engine v1"),
            ("v0.68.0", "M64", "Autonomous Plan Simulator"),
            ("v0.69.0", "M65", "Autonomy Audit + Replay Viewer"),
            ("v0.74.0", "M70", "Autonomy Foundation Freeze"),
            ("v0.80.0", "M76", "OpenWebUI Runtime Bridge v1"),
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
                    f"active docs missing planned M61-M100 row: {version_label} / {milestone} — {title}"
                )
        forbidden_fragments = [
            "production authority is implemented",
            "global autonomy switch is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ]
        if self._active_version_tuple() < (0, 66, 0):
            forbidden_fragments.append("m62 is implemented")
        if self._active_version_tuple() < (0, 67, 0):
            forbidden_fragments.append("m63 is implemented")
        if self._active_version_tuple() < (0, 68, 0):
            forbidden_fragments.append("m64 is implemented")
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M61 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m62_scoped_autonomy_session_contract_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "tests/test_m62_scoped_autonomy_session_contracts.py",
            "docs/autonomy/SCOPED_AUTONOMY_SESSION_CONTRACTS.md",
            "docs/autonomy/SCOPED_AUTONOMY_SESSION_SCOPE_POLICY.md",
            "docs/autonomy/SCOPED_AUTONOMY_SESSION_NON_GOALS.md",
            "docs/autonomy/M62_TO_M63_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
        ]
        failures = [
            f"missing M62 scoped autonomy session file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyRiskClass,
                ScopedAutonomySessionRequest,
                ScopedAutonomySessionScope,
                build_scoped_autonomy_session_decision,
                validate_scoped_autonomy_session_request,
                validate_scoped_autonomy_session_scope,
            )

            scope = ScopedAutonomySessionScope(
                scope_ref="autonomy-session-scope:m62-gate",
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m62-gate"],
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m62-gate",
                audit_ref="audit:m62-gate",
                replay_ref="replay:m62-gate",
            )
            validate_scoped_autonomy_session_scope(scope)
            request = ScopedAutonomySessionRequest(
                session_request_ref="autonomy-session-request:m62-gate",
                requested_mode=AutonomyAuthorityMode.dry_run_plan,
                scope=scope,
                approval_ref="approval:m62-review-only",
            )
            validated = validate_scoped_autonomy_session_request(request)
            decision = build_scoped_autonomy_session_decision(validated)
            if (
                not decision.contract_valid_for_review
                or decision.session_started
                or decision.session_active
                or decision.execution_performed
                or decision.side_effects_performed
            ):
                failures.append(
                    "M62 scoped session decision granted authority or side effects"
                )
            for update, reason in [
                ({"start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
                ({"session_active": True}, "AUTONOMY_SESSION_ACTIVATION_DENIED"),
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                (
                    {"approval_test_ref": "approval_test_:m62"},
                    "APPROVAL_TEST_REF_DENIED",
                ),
                (
                    {"requested_mode": AutonomyAuthorityMode.ask_before_every_action},
                    "AUTONOMY_MODE_ENABLEMENT_DENIED",
                ),
                (
                    {"requested_mode": AutonomyAuthorityMode.scoped_autonomy_window},
                    "AUTONOMY_MODE_FUTURE_MILESTONE_DENIED",
                ),
            ]:
                try:
                    validate_scoped_autonomy_session_request(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M62 unsafe session request mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M62 unsafe session request reason drifted for {reason}: {exc}"
                        )
            for update, reason in [
                ({"session_start_enabled": True}, "AUTONOMY_SESSION_START_DENIED"),
                (
                    {"session_activation_enabled": True},
                    "AUTONOMY_SESSION_ACTIVATION_DENIED",
                ),
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_scoped_autonomy_session_scope(
                        scope.model_copy(update=update)
                    )
                    failures.append(
                        f"M62 unsafe session scope mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M62 unsafe session scope reason drifted for {reason}: {exc}"
                        )
        except Exception as exc:
            failures.append(f"M62 scoped autonomy session validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "scoped autonomy session contracts",
            "contract-only",
            "review-only",
            "actor-bound",
            "resource-bound",
            "duration-bound",
            "allowlist",
            "revocation",
            "audit/replay",
            "no session start",
            "no session activation",
            "no autonomous actions",
            "no background worker",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no network tools",
            "no browser automation",
            "no backend route",
            "no dependency",
            "m63 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M62 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m62_scoped_autonomy_session_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "session_start_enabled=True",
            "session_activation_enabled=True",
            "start_requested=True",
            "session_active=True",
            "execution_requested=True",
            "autonomous_actions_enabled=True",
            "background_worker_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "network_tool_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "mobile_sensor_enabled=True",
            "remote_execution_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "production_authority_enabled=True",
            "execution_performed=True",
            "/autonomy/session/start",
            "/autonomy/session/activate",
            "/autonomy/session/run",
            "/autonomy/session/execute",
            "/autonomy/session/stop",
            "/background/start",
            "/network/fetch",
            "/shell/execute",
            "/browser/click",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m62_scoped_autonomy_session_contracts.py",
            "tests/test_m62_gate_integration.py",
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
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
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M62 forbidden scoped session fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m62_scoped_autonomy_session_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m62_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M62 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m62_roadmap_currentness(
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
            f"missing M62 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.66.0" not in text
            or "m62" not in text
            or "scoped autonomy session contracts" not in text
        ):
            failures.append(
                "active docs do not identify v0.66.0/M62 Scoped Autonomy Session Contracts"
            )
        if (
            "m62 is implemented/released" not in text
            and "v0.66.0 implements m62" not in text
        ):
            failures.append("active docs do not mark M62 implemented/released")
        for version_label, milestone, title in [
            ("v0.67.0", "M63", "Autonomy Policy Engine v1"),
            ("v0.68.0", "M64", "Autonomous Plan Simulator"),
            ("v0.69.0", "M65", "Autonomy Audit + Replay Viewer"),
            ("v0.70.0", "M66", "Scoped Approval Bundles"),
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M62-M100 row: {version_label} / {milestone} — {title}"
                )
        forbidden_fragments = [
            "autonomy policy engine is implemented",
            "session start is implemented",
            "session activation is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ]
        if self._active_version_tuple() < (0, 67, 0):
            forbidden_fragments.append("m63 is implemented")
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M62 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
