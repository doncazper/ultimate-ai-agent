from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart031Mixin:
    """Legacy checks from m119_production_red_team_harness_contracts through m121_roadmap_currentness."""
    def check_m119_production_red_team_harness_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/production_red_team_harness.py",
            "docs/production/PRODUCTION_RED_TEAM_HARNESS.md",
            "docs/production/PRODUCTION_RED_TEAM_HARNESS_BOUNDARY.md",
            "docs/production/PRODUCTION_RED_TEAM_HARNESS_RECEIPT_PLAN.md",
            "docs/production/PRODUCTION_RED_TEAM_HARNESS_NON_GOALS.md",
            "docs/production/M119_TO_M120_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m119_production_red_team_harness.py",
            "tests/test_m119_gate_integration.py",
        ]
        failures = [
            f"missing M119 production red-team harness file: {path}"
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
                ProductionRedTeamHarnessStatus,
                build_account_connector_contract_review_record,
                build_deployment_mode_matrix_record,
                build_production_audit_retention_policy_record,
                build_production_red_team_harness_record,
                build_production_threat_model_record,
                build_remote_agent_coordination_contract_record,
                build_role_based_authority_model_record,
                build_secrets_boundary_record,
                build_user_workspace_identity_record,
                validate_production_red_team_harness_record,
            )

            source_record = build_deployment_mode_matrix_record(
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
            record = build_production_red_team_harness_record(
                source_record=source_record
            )
            if (
                record.status
                != ProductionRedTeamHarnessStatus.production_red_team_harness
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_deployment_mode_matrix_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.deployment_mode_bound
                or not record.environment_bound
                or not record.authority_tier_bound
                or not record.red_team_scenario_bound
                or not record.abuse_case_bound
                or not record.threat_model_bound
                or not record.safety_control_bound
                or not record.mitigation_plan_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_deployment_mode_matrix_ref
                != source_record.deployment_mode_matrix_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.user_ref != source_record.user_ref
                or record.workspace_ref != source_record.workspace_ref
                or not record.red_team_scenario_refs
                or not record.abuse_case_refs
                or not record.threat_model_refs
                or not record.safety_control_refs
                or not record.mitigation_plan_refs
                or "checkpoint:m118" not in record.accepted_checkpoint_refs
                or record.production_authority_enabled
                or record.red_team_execution_enabled
                or record.attack_automation_enabled
                or record.external_probe_enabled
                or record.exploit_generation_enabled
                or record.security_scan_runtime_enabled
                or record.network_access_enabled
                or record.credential_handling_enabled
                or record.account_action_enabled
                or record.model_call_enabled
                or record.memory_write_enabled
                or record.context_injection_enabled
                or record.execution_enabled
                or record.tool_execution_enabled
                or record.shell_execution_enabled
                or record.browser_automation_enabled
                or record.plugin_execution_enabled
                or record.mobile_sensor_enabled
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.side_effects_performed
                or "M119_PRODUCTION_RED_TEAM_HARNESS" not in record.reason_codes
                or "M120_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M119 production red-team harness contract is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M119_REVIEW_ONLY_REQUIRED"),
                (
                    {"source_deployment_mode_matrix_bound": False},
                    "M119_SOURCE_DEPLOYMENT_MODE_MATRIX_BINDING_REQUIRED",
                ),
                (
                    {"red_team_scenario_refs": []},
                    "M119_RED_TEAM_SCENARIO_REF_REQUIRED",
                ),
                ({"abuse_case_refs": []}, "M119_ABUSE_CASE_REF_REQUIRED"),
                ({"threat_model_refs": []}, "M119_THREAT_MODEL_REF_REQUIRED"),
                ({"safety_control_refs": []}, "M119_SAFETY_CONTROL_REF_REQUIRED"),
                ({"mitigation_plan_refs": []}, "M119_MITIGATION_PLAN_REF_REQUIRED"),
                ({"red_team_execution_enabled": True}, "RED_TEAM_EXECUTION_DENIED"),
                ({"attack_automation_enabled": True}, "ATTACK_AUTOMATION_DENIED"),
                ({"external_probe_enabled": True}, "EXTERNAL_PROBE_DENIED"),
                ({"exploit_generation_enabled": True}, "EXPLOIT_GENERATION_DENIED"),
                (
                    {"security_scan_runtime_enabled": True},
                    "SECURITY_SCAN_RUNTIME_DENIED",
                ),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_added": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_production_red_team_harness_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M119 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M119 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(
                f"M119 production red-team harness validation failed: {exc}"
            )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "production red-team harness",
            "contract-only",
            "review-only",
            "safe refs",
            "deployment mode matrix",
            "red-team scenario refs",
            "abuse case refs",
            "threat model refs",
            "safety control refs",
            "mitigation plan refs",
            "actor-bound",
            "baseline-bound",
            "source-deployment-mode-matrix-bound",
            "user-bound",
            "workspace-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no production authority",
            "no red-team execution",
            "no attack automation",
            "no scanner runtime",
            "no external probing",
            "no exploit generation",
            "no credential handling",
            "no network access",
            "no execution",
            "no backend route",
            "no control center control",
            "no dependency",
            "m120 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M119 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m119_production_red_team_harness_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "production_authority_enabled=True",
            "red_team_execution_enabled=True",
            "attack_automation_enabled=True",
            "external_probe_enabled=True",
            "exploit_generation_enabled=True",
            "security_scan_runtime_enabled=True",
            "credential_handling_enabled=True",
            "network_access_enabled=True",
            "execution_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/red-team/run",
            "/red-team/execute",
            "/red-team/attack",
            "/red-team/probe",
            "/red-team/exploit",
            "/red-team/report/export",
            "/production/red-team/run",
            "/security/scan/run",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
            "src/ultimate_ai_agent/core/production_readiness/production_red_team_harness.py",
            "src/ultimate_ai_agent/core/production_readiness/deployment_mode_matrix.py",
            "src/ultimate_ai_agent/core/production_readiness/remote_agent_coordination.py",
            "src/ultimate_ai_agent/core/production_readiness/role_based_authority.py",
            "src/ultimate_ai_agent/core/production_readiness/production_audit_retention.py",
            "src/ultimate_ai_agent/core/production_readiness/account_connector_review.py",
            "src/ultimate_ai_agent/core/production_readiness/secrets_boundary.py",
            "src/ultimate_ai_agent/core/production_readiness/user_workspace_identity.py",
            "src/ultimate_ai_agent/core/production_readiness/production_threat_model.py",
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
                            f"M119 forbidden red-team harness fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m119_production_red_team_harness_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m119_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M119 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m119_roadmap_currentness(
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
            f"missing M119 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "checkpoint m119" not in text or "production red-team harness" not in text:
            failures.append(
                "active docs do not identify Checkpoint M119 Production Red-Team Harness"
            )
        if (
            "m119 is implemented/released" not in text
            and "checkpoint m119 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M119 implemented/released")
        for version_label, product_target, milestone, title in [
            (
                "checkpoint m120",
                "pre-alpha checkpoint",
                "m120",
                "production authority readiness review",
            ),
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | "
                f"{'implemented/released' if milestone == 'm120' else 'planned/provisional'} |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing expected M120-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "red-team execution is implemented",
            "attack automation is implemented",
            "scanner runtime is implemented",
            "external probing is implemented",
            "exploit generation is implemented",
            "production authority is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M119 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m120_production_authority_readiness_review_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/production_authority_readiness.py",
            "docs/production/PRODUCTION_AUTHORITY_READINESS_REVIEW.md",
            "docs/production/PRODUCTION_AUTHORITY_READINESS_BOUNDARY.md",
            "docs/production/PRODUCTION_AUTHORITY_READINESS_RECEIPT_PLAN.md",
            "docs/production/PRODUCTION_AUTHORITY_READINESS_NON_GOALS.md",
            "docs/production/M120_TO_M121_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m120_production_authority_readiness_review.py",
            "tests/test_m120_gate_integration.py",
        ]
        failures = [
            f"missing M120 production authority readiness file: {path}"
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
                ProductionAuthorityReadinessReviewStatus,
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
                validate_production_authority_readiness_review_record,
            )

            source_record = build_production_red_team_harness_record(
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
            record = build_production_authority_readiness_review_record(
                source_record=source_record
            )
            if (
                record.status
                != ProductionAuthorityReadinessReviewStatus.production_authority_readiness_review
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_production_red_team_harness_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.deployment_mode_bound
                or not record.environment_bound
                or not record.authority_tier_bound
                or not record.readiness_check_bound
                or not record.launch_blocker_bound
                or not record.rollback_readiness_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_production_red_team_harness_ref
                != source_record.production_red_team_harness_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.user_ref != source_record.user_ref
                or record.workspace_ref != source_record.workspace_ref
                or not record.readiness_check_refs
                or not record.launch_blocker_refs
                or not record.rollback_readiness_refs
                or "checkpoint:m119" not in record.accepted_checkpoint_refs
                or record.production_authority_enabled
                or record.production_runtime_enabled
                or record.go_live_enabled
                or record.production_deployment_enabled
                or record.external_distribution_enabled
                or record.traffic_routing_enabled
                or record.account_action_enabled
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
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.side_effects_performed
                or "M120_PRODUCTION_AUTHORITY_READINESS_REVIEW"
                not in record.reason_codes
                or "M121_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M120 production authority readiness review contract is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M120_REVIEW_ONLY_REQUIRED"),
                (
                    {"source_production_red_team_harness_bound": False},
                    "M120_SOURCE_PRODUCTION_RED_TEAM_HARNESS_BINDING_REQUIRED",
                ),
                ({"readiness_check_refs": []}, "M120_READINESS_CHECK_REF_REQUIRED"),
                ({"launch_blocker_refs": []}, "M120_LAUNCH_BLOCKER_REF_REQUIRED"),
                (
                    {"rollback_readiness_refs": []},
                    "M120_ROLLBACK_READINESS_REF_REQUIRED",
                ),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
                ({"production_runtime_enabled": True}, "PRODUCTION_RUNTIME_DENIED"),
                ({"go_live_enabled": True}, "GO_LIVE_DENIED"),
                (
                    {"production_deployment_enabled": True},
                    "PRODUCTION_DEPLOYMENT_DENIED",
                ),
                ({"traffic_routing_enabled": True}, "TRAFFIC_ROUTING_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_added": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_production_authority_readiness_review_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M120 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M120 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(
                f"M120 production authority readiness validation failed: {exc}"
            )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "production authority readiness review",
            "contract-only",
            "review-only",
            "safe refs",
            "production red-team harness",
            "readiness check refs",
            "launch blocker refs",
            "rollback readiness refs",
            "actor-bound",
            "baseline-bound",
            "source-production-red-team-harness-bound",
            "user-bound",
            "workspace-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no production authority",
            "no production runtime",
            "no go-live",
            "no production deployment",
            "no traffic routing",
            "no credential handling",
            "no network access",
            "no execution",
            "no backend route",
            "no control center control",
            "no dependency",
            "m121 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M120 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m120_production_authority_readiness_review_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "production_authority_enabled=True",
            "production_runtime_enabled=True",
            "go_live_enabled=True",
            "production_deployment_enabled=True",
            "traffic_routing_enabled=True",
            "credential_handling_enabled=True",
            "network_access_enabled=True",
            "execution_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/production/authority/enable",
            "/production/go-live",
            "/production/deploy",
            "/production/traffic/route",
            "/production/rollback/execute",
            "/production/readiness/approve",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
            "src/ultimate_ai_agent/core/production_readiness/production_authority_readiness.py",
            "src/ultimate_ai_agent/core/production_readiness/production_red_team_harness.py",
            "src/ultimate_ai_agent/core/production_readiness/deployment_mode_matrix.py",
            "src/ultimate_ai_agent/core/production_readiness/remote_agent_coordination.py",
            "src/ultimate_ai_agent/core/production_readiness/role_based_authority.py",
            "src/ultimate_ai_agent/core/production_readiness/production_audit_retention.py",
            "src/ultimate_ai_agent/core/production_readiness/account_connector_review.py",
            "src/ultimate_ai_agent/core/production_readiness/secrets_boundary.py",
            "src/ultimate_ai_agent/core/production_readiness/user_workspace_identity.py",
            "src/ultimate_ai_agent/core/production_readiness/production_threat_model.py",
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
                            f"M120 forbidden production authority readiness fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m120_production_authority_readiness_review_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m120_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M120 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m120_roadmap_currentness(
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
            f"missing M120 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m120" not in text
            or "production authority readiness review" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M120 Production Authority Readiness Review"
            )
        if (
            "m120 is implemented/released" not in text
            and "checkpoint m120 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M120 implemented/released")
        for version_label, product_target, milestone, title in [
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M121-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "production authority is implemented",
            "go-live is implemented",
            "production runtime is implemented",
            "production deployment is implemented",
            "traffic routing is implemented",
            "credential handling is implemented",
            "network access is implemented",
            "beta is released",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M120 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m121_email_connector_contract_refresh_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/email_connector_contract_refresh.py",
            "docs/connectors/EMAIL_CONNECTOR_CONTRACT_REFRESH.md",
            "docs/connectors/EMAIL_CONNECTOR_AUTHORITY_BOUNDARY.md",
            "docs/connectors/EMAIL_CONNECTOR_RECEIPT_PLAN.md",
            "docs/connectors/EMAIL_CONNECTOR_NON_GOALS.md",
            "docs/connectors/M121_TO_M122_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m121_email_connector_contract_refresh.py",
            "tests/test_m121_gate_integration.py",
        ]
        failures = [
            f"missing M121 email connector refresh file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.connectors import (
                EmailConnectorContractRefreshStatus,
                build_email_connector_contract_refresh_record,
                validate_email_connector_contract_refresh_record,
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

            source_record = build_production_authority_readiness_review_record(
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
            record = build_email_connector_contract_refresh_record(
                source_record=source_record
            )
            if (
                record.status
                != EmailConnectorContractRefreshStatus.email_connector_contract_refresh
                or not record.contract_only
                or not record.review_only
                or not record.safe_refs_required
                or not record.actor_bound
                or not record.baseline_bound
                or not record.source_production_authority_readiness_bound
                or not record.user_bound
                or not record.workspace_bound
                or not record.email_scope_bound
                or not record.mailbox_boundary_bound
                or not record.consent_boundary_bound
                or not record.data_classification_bound
                or not record.retention_boundary_bound
                or not record.audit_required
                or not record.replay_safe
                or record.source_production_authority_readiness_ref
                != source_record.production_authority_readiness_review_ref
                or record.source_baseline_ref != source_record.source_baseline_ref
                or record.actor_ref != source_record.actor_ref
                or record.user_ref != source_record.user_ref
                or record.workspace_ref != source_record.workspace_ref
                or "checkpoint:m120" not in record.accepted_checkpoint_refs
                or not record.email_scope_refs
                or not record.mailbox_boundary_refs
                or not record.consent_boundary_refs
                or not record.data_classification_refs
                or not record.retention_boundary_refs
                or record.email_connector_runtime_enabled
                or record.email_account_auth_enabled
                or record.email_read_enabled
                or record.email_search_enabled
                or record.email_send_enabled
                or record.email_write_enabled
                or record.email_delete_enabled
                or record.email_attachment_download_enabled
                or record.raw_email_content_enabled
                or record.credential_handling_enabled
                or record.network_access_enabled
                or record.account_action_enabled
                or record.model_call_enabled
                or record.memory_write_enabled
                or record.context_injection_enabled
                or record.execution_enabled
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.side_effects_performed
                or "M121_EMAIL_CONNECTOR_CONTRACT_REFRESH" not in record.reason_codes
                or "M122_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M121 email connector refresh contract is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"review_only": False}, "M121_REVIEW_ONLY_REQUIRED"),
                ({"email_scope_refs": []}, "M121_EMAIL_SCOPE_REF_REQUIRED"),
                ({"mailbox_boundary_refs": []}, "M121_MAILBOX_BOUNDARY_REF_REQUIRED"),
                ({"consent_boundary_refs": []}, "M121_CONSENT_BOUNDARY_REF_REQUIRED"),
                (
                    {"email_connector_runtime_enabled": True},
                    "EMAIL_CONNECTOR_RUNTIME_DENIED",
                ),
                ({"email_account_auth_enabled": True}, "EMAIL_ACCOUNT_AUTH_DENIED"),
                ({"email_read_enabled": True}, "EMAIL_READ_DENIED"),
                ({"email_send_enabled": True}, "EMAIL_SEND_DENIED"),
                ({"raw_email_content_enabled": True}, "RAW_EMAIL_CONTENT_DENIED"),
                ({"credential_handling_enabled": True}, "CREDENTIAL_HANDLING_DENIED"),
                ({"network_access_enabled": True}, "NETWORK_ACCESS_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                (
                    {"control_center_control_added": True},
                    "CONTROL_CENTER_CONTROL_DENIED",
                ),
                ({"dependency_added": True}, "DEPENDENCY_DENIED"),
            ]:
                try:
                    validate_email_connector_contract_refresh_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M121 unsafe record mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M121 unsafe record mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M121 email connector refresh validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "email connector contract refresh",
            "contract-only",
            "review-only",
            "safe refs",
            "production authority readiness review",
            "email scope refs",
            "mailbox boundary refs",
            "consent boundary refs",
            "data classification refs",
            "retention boundary refs",
            "actor-bound",
            "baseline-bound",
            "source-production-authority-readiness-bound",
            "audit",
            "replay",
            "no-effect receipt plan",
            "no email connector runtime",
            "no email account auth",
            "no email read",
            "no email search",
            "no email send",
            "no email write",
            "no email delete",
            "no raw email content",
            "no credential handling",
            "no network access",
            "no backend route",
            "no control center control",
            "no dependency",
            "m122 remains future",
            "v1.2.0-alpha",
        ]:
            if fragment not in docs_text:
                failures.append(f"M121 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m121_email_connector_contract_refresh_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "email_connector_runtime_enabled=True",
            "email_account_auth_enabled=True",
            "email_read_enabled=True",
            "email_search_enabled=True",
            "email_send_enabled=True",
            "email_write_enabled=True",
            "email_delete_enabled=True",
            "email_attachment_download_enabled=True",
            "raw_email_content_enabled=True",
            "credential_handling_enabled=True",
            "network_access_enabled=True",
            "account_action_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "execution_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "control_center_control_enabled=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/connectors/email/auth",
            "/connectors/email/read",
            "/connectors/email/search",
            "/connectors/email/send",
            "/connectors/email/write",
            "/connectors/email/delete",
            "/connectors/email/attachments/download",
            "/email/send",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/connectors/__init__.py",
            "src/ultimate_ai_agent/core/connectors/email_connector_contract_refresh.py",
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
                            f"M121 forbidden email connector fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m121_email_connector_contract_refresh_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m121_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M121 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m121_roadmap_currentness(
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
            f"missing M121 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "checkpoint m121" not in text
            or "email connector contract refresh" not in text
        ):
            failures.append(
                "active docs do not identify Checkpoint M121 Email Connector Contract Refresh"
            )
        if (
            "m121 is implemented/released" not in text
            and "checkpoint m121 is implemented/released" not in text
        ):
            failures.append("active docs do not mark M121 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m121",
                "pre-alpha checkpoint",
                "m121",
                "email connector contract refresh",
                "implemented/released",
            ),
            (
                "checkpoint m122",
                "pre-alpha checkpoint",
                "m122",
                "calendar connector contract refresh",
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
            m122_is_current = (
                "checkpoint m122 is implemented/released" in text
                or "m122 is implemented/released" in text
            )
            if milestone == "m122" and m122_is_current:
                continue
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing expected M121-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = {
            "m122 is implemented",
            "checkpoint m122 implements m122",
            "calendar connector contract refresh is implemented",
            "email connector runtime is implemented",
            "email account auth is implemented",
            "email read is implemented",
            "email send is implemented",
            "network access is implemented",
            "beta is released",
            "broad autonomy is implemented",
        }
        if (
            "checkpoint m122 is implemented/released" in text
            or "m122 is implemented/released" in text
        ):
            forbidden_fragments -= {
                "m122 is implemented",
                "calendar connector contract refresh is implemented",
            }
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M121 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
