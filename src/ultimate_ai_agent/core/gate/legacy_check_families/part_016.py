from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart016Mixin:
    """Legacy checks from m66_scoped_approval_bundles_static_safety through m69_roadmap_currentness."""
    def check_m66_scoped_approval_bundles_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "policy_activation_enabled=True",
            "policy_activation_requested=True",
            "session_start_enabled=True",
            "session_start_requested=True",
            "session_active=True",
            "execution_requested=True",
            "execution_performed=True",
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
            "model_provider_call_enabled=True",
            "production_authority_enabled=True",
            "authority_granted=True",
            "/autonomy/approval-bundles",
            "/autonomy/approval-bundles/grant",
            "/autonomy/approval-bundles/activate",
            "/autonomy/approval-bundles/execute",
            "/autonomy/execute",
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
            "src/ultimate_ai_agent/core/autonomy/approvals.py",
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/simulator.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m66_scoped_approval_bundles.py",
            "tests/test_m66_gate_integration.py",
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
                            f"M66 forbidden scoped approval bundle fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m66_scoped_approval_bundles_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m66_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M66 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m66_roadmap_currentness(
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
            f"missing M66 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.70.0" not in text
            or "m66" not in text
            or "scoped approval bundles" not in text
        ):
            failures.append(
                "active docs do not identify v0.70.0/M66 Scoped Approval Bundles"
            )
        if (
            "m66 is implemented/released" not in text
            and "v0.70.0 implements m66" not in text
        ):
            failures.append("active docs do not mark M66 implemented/released")
        for version_label, milestone, title in [
            ("v0.71.0", "M67", "Revocation + Kill Switch"),
            ("v0.72.0", "M68", "Autonomy Risk Classifier"),
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
                    f"active docs missing planned M66-M100 row: {version_label} / {milestone} — {title}"
                )
        forbidden_fragments = [
            "m67 is implemented",
            "revocation + kill switch is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ]
        if self._active_version_tuple() >= (0, 71, 0):
            forbidden_fragments = [
                fragment
                for fragment in forbidden_fragments
                if fragment
                not in {"m67 is implemented", "revocation + kill switch is implemented"}
            ]
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M66 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m67_revocation_kill_switch_contract_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/revocation.py",
            "tests/test_m67_revocation_kill_switch.py",
            "docs/autonomy/REVOCATION_KILL_SWITCH.md",
            "docs/autonomy/REVOCATION_KILL_SWITCH_CONTRACTS.md",
            "docs/autonomy/REVOCATION_KILL_SWITCH_NON_GOALS.md",
            "docs/autonomy/M67_TO_M68_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
        ]
        failures = [
            f"missing M67 revocation kill switch file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyPolicyEvaluationRequest,
                AutonomyPolicyEnginePolicy,
                AutonomyPolicyRule,
                AutonomyRiskClass,
                AutonomousPlanSimulationRequest,
                AutonomousPlanSimulationStep,
                ScopedAutonomySessionRequest,
                ScopedAutonomySessionScope,
                build_autonomous_plan_simulation_result,
                build_autonomy_audit_replay_view,
                build_autonomy_policy_decision,
                build_revocation_kill_switch_record,
                build_scoped_approval_bundle,
                validate_revocation_kill_switch_record,
            )

            scope = ScopedAutonomySessionScope(
                scope_ref="autonomy-session-scope:m67-gate",
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m67-gate"],
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m67-gate",
                audit_ref="audit:m67-gate",
                replay_ref="replay:m67-gate",
            )
            policy_decision = build_autonomy_policy_decision(
                AutonomyPolicyEvaluationRequest(
                    evaluation_request_ref="autonomy-policy-evaluation:m67-gate",
                    policy=AutonomyPolicyEnginePolicy(
                        policy_ref="autonomy-policy:m67-gate",
                        policy_version_ref="autonomy-policy-version:m67-v1",
                        rules=[
                            AutonomyPolicyRule(
                                rule_ref="autonomy-policy-rule:m67-gate",
                                allowed_actor_refs=["actor:gate-reviewer"],
                                allowed_resource_refs=["resource:local-prototype"],
                                allowed_capability_refs=[
                                    "capability:observe-only-review"
                                ],
                                required_allowlist_refs=["allowlist:m67-gate"],
                                max_mode=AutonomyAuthorityMode.dry_run_plan,
                                max_risk_class=AutonomyRiskClass.low,
                                max_duration_seconds=900,
                            )
                        ],
                    ),
                    session_request=ScopedAutonomySessionRequest(
                        session_request_ref="autonomy-session-request:m67-gate",
                        requested_mode=AutonomyAuthorityMode.dry_run_plan,
                        scope=scope,
                    ),
                )
            )
            simulation_result = build_autonomous_plan_simulation_result(
                AutonomousPlanSimulationRequest(
                    simulation_request_ref="autonomy-plan-simulation-request:m67-gate",
                    policy_decision=policy_decision,
                    steps=[
                        AutonomousPlanSimulationStep(
                            step_ref="autonomy-simulation-step:m67-gate",
                            intent_ref="intent:inspect-redacted-review-packet",
                            capability_ref="capability:observe-only-review",
                            resource_ref="resource:local-prototype",
                            simulated_outcome_ref="simulation-outcome:m67-review-only",
                        )
                    ],
                    actor_ref="actor:gate-reviewer",
                    resource_refs=["resource:local-prototype"],
                    capability_refs=["capability:observe-only-review"],
                    allowlist_refs=["allowlist:m67-gate"],
                    audit_ref="audit:m67-gate",
                    replay_ref="replay:m67-gate",
                )
            )
            replay_view = build_autonomy_audit_replay_view(
                audit_view_ref="autonomy-audit-replay-view:m67-gate",
                simulation_result=simulation_result,
                actor_ref="actor:gate-reviewer",
                audit_ref="audit:m67-gate",
                replay_ref="replay:m67-gate",
            )
            bundle = build_scoped_approval_bundle(
                bundle_ref="scoped-approval-bundle:m67-gate",
                source_scope=scope,
                audit_replay_view=replay_view,
                approval_refs=["approval:m67-gate-review", "approval:m67-gate-dry-run"],
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m67-gate"],
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m67-gate",
                audit_ref="audit:m67-gate",
                replay_ref="replay:m67-gate",
            )
            record = build_revocation_kill_switch_record(
                revocation_record_ref="revocation-kill-switch-record:m67-gate",
                approval_bundle=bundle,
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m67-gate"],
                bundle_ref="scoped-approval-bundle:m67-gate",
                source_scope_ref="autonomy-session-scope:m67-gate",
                audit_view_ref="autonomy-audit-replay-view:m67-gate",
                simulation_result_ref="autonomy-plan-simulation-result:m67-gate",
                revocation_ref="revocation:m67-gate",
                audit_ref="audit:m67-gate",
                replay_ref="replay:m67-gate",
            )
            if (
                not record.record_valid_for_review
                or not record.review_only
                or not record.revocation_requested
                or not record.kill_switch_requested
                or not record.approval_refs_are_identifiers_only
                or record.authority_granted
                or record.revocation_performed
                or record.kill_switch_activated
                or record.session_stopped
                or record.execution_performed
                or record.side_effects_performed
            ):
                failures.append(
                    "M67 revocation kill switch record granted authority or side effects"
                )
            for update, reason in [
                (
                    {"approval_test_ref": "approval_test_:m67"},
                    "APPROVAL_TEST_REF_DENIED",
                ),
                ({"kill_switch_activated": True}, "KILL_SWITCH_ACTIVATION_DENIED"),
                ({"revocation_performed": True}, "REVOCATION_ACTION_DENIED"),
                ({"session_stopped": True}, "AUTONOMY_SESSION_STOP_DENIED"),
                ({"authority_granted": True}, "AUTONOMY_POLICY_AUTHORITY_DENIED"),
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
                ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
                (
                    {"metadata": {"api_key": "secret-value"}},
                    "SECRET_LIKE_REVOCATION_KILL_SWITCH_CONTENT_DENIED",
                ),
            ]:
                try:
                    validate_revocation_kill_switch_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M67 unsafe revocation kill switch mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M67 unsafe revocation kill switch reason drifted for {reason}: {exc}"
                        )
            try:
                validate_revocation_kill_switch_record(
                    record.model_copy(
                        update={"bundle_ref": "scoped-approval-bundle:other"}
                    )
                )
                failures.append("M67 bundle binding drift was not denied")
            except ValueError as exc:
                if "REVOCATION_KILL_SWITCH_BUNDLE_BINDING_MISMATCH_DENIED" not in str(
                    exc
                ):
                    failures.append(f"M67 bundle binding reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M67 revocation kill switch validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "revocation + kill switch",
            "contract-only",
            "review-only",
            "exact-bound",
            "scoped approval bundle",
            "revocation requested",
            "kill-switch requested",
            "no revocation action",
            "no kill-switch activation",
            "no session stop",
            "approval refs are identifiers",
            "no policy activation",
            "no session start",
            "no autonomous actions",
            "no background worker",
            "no process kill",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no network tools",
            "no browser automation",
            "no context injection",
            "no memory write",
            "no backend route",
            "no dependency",
            "m68 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M67 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m67_revocation_kill_switch_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "kill_switch_activated=True",
            "revocation_performed=True",
            "session_stopped=True",
            "policy_activation_enabled=True",
            "policy_activation_requested=True",
            "session_start_enabled=True",
            "session_start_requested=True",
            "session_active=True",
            "execution_requested=True",
            "execution_performed=True",
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
            "model_provider_call_enabled=True",
            "production_authority_enabled=True",
            "authority_granted=True",
            "/autonomy/revoke",
            "/autonomy/revocation/execute",
            "/autonomy/kill-switch",
            "/autonomy/kill-switch/activate",
            "/autonomy/session/stop",
            "/autonomy/session/terminate",
            "/process/kill",
            "/autonomy/execute",
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
            "src/ultimate_ai_agent/core/autonomy/revocation.py",
            "src/ultimate_ai_agent/core/autonomy/approvals.py",
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/simulator.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m67_revocation_kill_switch.py",
            "tests/test_m67_gate_integration.py",
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
                            f"M67 forbidden revocation kill switch fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m67_revocation_kill_switch_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m67_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M67 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m67_roadmap_currentness(
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
            f"missing M67 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.71.0" not in text
            or "m67" not in text
            or "revocation + kill switch" not in text
        ):
            failures.append(
                "active docs do not identify v0.71.0/M67 Revocation + Kill Switch"
            )
        if (
            "m67 is implemented/released" not in text
            and "v0.71.0 implements m67" not in text
        ):
            failures.append("active docs do not mark M67 implemented/released")
        for version_label, milestone, title in [
            ("v0.72.0", "M68", "Autonomy Risk Classifier"),
            ("v0.73.0", "M69", "Low-Risk Autonomous Dry Run"),
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
                    f"active docs missing planned M67-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M67 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m68_autonomy_risk_classifier_contract_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/risk.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "docs/autonomy/AUTONOMY_RISK_CLASSIFIER.md",
            "docs/autonomy/AUTONOMY_RISK_CLASSIFIER_CONTRACTS.md",
            "docs/autonomy/AUTONOMY_RISK_CLASSIFIER_NON_GOALS.md",
            "docs/autonomy/M68_TO_M69_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "tests/test_m68_autonomy_risk_classifier.py",
            "tests/test_m68_gate_integration.py",
        ]
        failures = [
            f"missing M68 autonomy risk classifier file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.autonomy import (
                AutonomyAuthorityMode,
                AutonomyPolicyEnginePolicy,
                AutonomyPolicyEvaluationRequest,
                AutonomyPolicyRule,
                AutonomyRiskClass,
                AutonomyRiskSignal,
                AutonomyRiskSignalKind,
                AutonomyRiskClassificationRequest,
                AutonomousPlanSimulationRequest,
                AutonomousPlanSimulationStep,
                ScopedAutonomySessionRequest,
                ScopedAutonomySessionScope,
                build_autonomous_plan_simulation_result,
                build_autonomy_audit_replay_view,
                build_autonomy_policy_decision,
                build_autonomy_risk_classification_decision,
                build_revocation_kill_switch_record,
                build_scoped_approval_bundle,
                validate_autonomy_risk_classification_decision,
            )

            scope = ScopedAutonomySessionScope(
                scope_ref="autonomy-session-scope:m68-gate",
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m68-gate"],
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m68-gate",
                audit_ref="audit:m68-gate",
                replay_ref="replay:m68-gate",
            )
            policy_decision = build_autonomy_policy_decision(
                AutonomyPolicyEvaluationRequest(
                    evaluation_request_ref="autonomy-policy-evaluation:m68-gate",
                    policy=AutonomyPolicyEnginePolicy(
                        policy_ref="autonomy-policy:m68-gate",
                        policy_version_ref="autonomy-policy-version:m68-v1",
                        rules=[
                            AutonomyPolicyRule(
                                rule_ref="autonomy-policy-rule:m68-gate",
                                allowed_actor_refs=[scope.actor_ref],
                                allowed_resource_refs=list(scope.resource_refs),
                                allowed_capability_refs=list(scope.capability_refs),
                                required_allowlist_refs=list(scope.allowlist_refs),
                                max_mode=AutonomyAuthorityMode.dry_run_plan,
                                max_risk_class=AutonomyRiskClass.high,
                                max_duration_seconds=900,
                            )
                        ],
                    ),
                    session_request=ScopedAutonomySessionRequest(
                        session_request_ref="autonomy-session-request:m68-gate",
                        requested_mode=AutonomyAuthorityMode.dry_run_plan,
                        scope=scope,
                    ),
                )
            )
            simulation_result = build_autonomous_plan_simulation_result(
                AutonomousPlanSimulationRequest(
                    simulation_request_ref="autonomy-plan-simulation-request:m68-gate",
                    policy_decision=policy_decision,
                    steps=[
                        AutonomousPlanSimulationStep(
                            step_ref="autonomy-simulation-step:m68-inspect",
                            intent_ref="intent:inspect-redacted-review-packet",
                            capability_ref="capability:observe-only-review",
                            resource_ref="resource:local-prototype",
                            simulated_outcome_ref="simulation-outcome:m68-review-only",
                        )
                    ],
                    actor_ref=scope.actor_ref,
                    resource_refs=list(scope.resource_refs),
                    capability_refs=list(scope.capability_refs),
                    allowlist_refs=list(scope.allowlist_refs),
                    audit_ref=scope.audit_ref,
                    replay_ref=scope.replay_ref,
                )
            )
            audit_view = build_autonomy_audit_replay_view(
                audit_view_ref="autonomy-audit-replay-view:m68-gate",
                simulation_result=simulation_result,
                actor_ref=scope.actor_ref,
                audit_ref=scope.audit_ref,
                replay_ref=scope.replay_ref,
            )
            bundle = build_scoped_approval_bundle(
                bundle_ref="scoped-approval-bundle:m68-gate",
                source_scope=scope,
                audit_replay_view=audit_view,
                approval_refs=["approval:m68-redacted-review"],
                actor_ref=scope.actor_ref,
                resource_refs=list(scope.resource_refs),
                capability_refs=list(scope.capability_refs),
                allowlist_refs=list(scope.allowlist_refs),
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref=scope.revocation_ref,
                audit_ref=scope.audit_ref,
                replay_ref=scope.replay_ref,
            )
            revocation_record = build_revocation_kill_switch_record(
                revocation_record_ref="revocation-kill-switch-record:m68-gate",
                approval_bundle=bundle,
                actor_ref=scope.actor_ref,
                resource_refs=list(scope.resource_refs),
                capability_refs=list(scope.capability_refs),
                allowlist_refs=list(scope.allowlist_refs),
                bundle_ref=bundle.bundle_ref,
                source_scope_ref=bundle.source_scope_ref,
                audit_view_ref=bundle.audit_view_ref,
                simulation_result_ref=bundle.simulation_result_ref,
                revocation_ref=bundle.revocation_ref,
                audit_ref=bundle.audit_ref,
                replay_ref=bundle.replay_ref,
            )
            request = AutonomyRiskClassificationRequest(
                classification_request_ref="autonomy-risk-classification-request:m68-gate",
                approval_bundle=bundle,
                revocation_record=revocation_record,
                declared_risk_class=AutonomyRiskClass.low,
                risk_signals=[
                    AutonomyRiskSignal(
                        signal_ref="autonomy-risk-signal:m68-shell-intent",
                        signal_kind=AutonomyRiskSignalKind.shell_intent,
                        risk_class=AutonomyRiskClass.critical,
                        source_ref="intent:shell-dry-run-review",
                        reason_code="M68_SIGNAL_SHELL_INTENT_CRITICAL",
                    )
                ],
                actor_ref=scope.actor_ref,
                resource_refs=list(scope.resource_refs),
                capability_refs=list(scope.capability_refs),
                allowlist_refs=list(scope.allowlist_refs),
                bundle_ref=bundle.bundle_ref,
                revocation_record_ref=revocation_record.revocation_record_ref,
                source_scope_ref=bundle.source_scope_ref,
                audit_ref=bundle.audit_ref,
                replay_ref=bundle.replay_ref,
            )
            decision = build_autonomy_risk_classification_decision(request)
            if (
                decision.derived_risk_class != AutonomyRiskClass.critical
                or not decision.classification_valid_for_review
                or not decision.review_only
                or decision.authority_granted
                or decision.execution_performed
                or decision.side_effects_performed
            ):
                failures.append(
                    "M68 risk classifier failed to derive highest risk without authority"
                )
            for update, reason in [
                (
                    {"derived_risk_class": AutonomyRiskClass.low},
                    "AUTONOMY_RISK_DOWNGRADE_DENIED",
                ),
                (
                    {"authority_granted": True},
                    "AUTONOMY_RISK_CLASSIFIER_AUTHORITY_DENIED",
                ),
                (
                    {"risk_authority_granted": True},
                    "AUTONOMY_RISK_CLASSIFIER_AUTHORITY_DENIED",
                ),
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
                ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
                (
                    {"metadata": {"api_key": "secret-value"}},
                    "SECRET_LIKE_AUTONOMY_RISK_CONTENT_DENIED",
                ),
            ]:
                try:
                    validate_autonomy_risk_classification_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M68 unsafe risk classifier mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M68 unsafe risk classifier reason drifted for {reason}: {exc}"
                        )
        except Exception as exc:
            failures.append(f"M68 autonomy risk classifier validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "autonomy risk classifier",
            "contract-only",
            "review-only",
            "deterministic",
            "highest risk",
            "declared risk",
            "scoped approval bundle",
            "revocation + kill switch",
            "risk downgrade denied",
            "approval refs are identifiers",
            "no policy activation",
            "no session start",
            "no autonomous actions",
            "no background worker",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no network tools",
            "no browser automation",
            "no context injection",
            "no memory write",
            "no backend route",
            "no dependency",
            "m69 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M68 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m68_autonomy_risk_classifier_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "risk_authority_granted=True",
            "policy_activation_requested=True",
            "session_start_requested=True",
            "session_active=True",
            "execution_requested=True",
            "execution_performed=True",
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
            "model_provider_call_enabled=True",
            "production_authority_enabled=True",
            "authority_granted=True",
            "/autonomy/risk/classify",
            "/autonomy/risk/execute",
            "/autonomy/risk/activate",
            "/autonomy/session/start",
            "/autonomy/policy/activate",
            "/network/fetch",
            "/shell/execute",
            "/browser/click",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/autonomy/risk.py",
            "src/ultimate_ai_agent/core/autonomy/revocation.py",
            "src/ultimate_ai_agent/core/autonomy/approvals.py",
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/simulator.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m68_autonomy_risk_classifier.py",
            "tests/test_m68_gate_integration.py",
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
                            f"M68 forbidden autonomy risk classifier fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m68_autonomy_risk_classifier_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m68_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M68 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m68_roadmap_currentness(
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
            f"missing M68 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.72.0" not in text
            or "m68" not in text
            or "autonomy risk classifier" not in text
        ):
            failures.append(
                "active docs do not identify v0.72.0/M68 Autonomy Risk Classifier"
            )
        if (
            "m68 is implemented/released" not in text
            and "v0.72.0 implements m68" not in text
        ):
            failures.append("active docs do not mark M68 implemented/released")
        for version_label, milestone, title in [
            ("v0.73.0", "M69", "Low-Risk Autonomous Dry Run"),
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
                    f"active docs missing planned M69-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M68 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m69_low_risk_autonomous_dry_run_contract_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/dry_run.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN.md",
            "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN_CONTRACTS.md",
            "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN_NON_GOALS.md",
            "docs/autonomy/M69_TO_M70_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "tests/test_m69_low_risk_autonomous_dry_run.py",
            "tests/test_m69_gate_integration.py",
        ]
        failures = [
            f"missing M69 low-risk autonomous dry-run file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.autonomy import (
                AutonomyRiskClass,
                LowRiskAutonomousDryRunRequest,
                LowRiskAutonomousDryRunStep,
                build_low_risk_autonomous_dry_run_record,
                validate_low_risk_autonomous_dry_run_record,
            )

            import importlib.util

            test_spec = importlib.util.spec_from_file_location(
                "uaa_m68_contract_helpers_for_m69",
                self.root / "tests" / "test_m68_autonomy_risk_classifier.py",
            )
            if test_spec is None or test_spec.loader is None:
                failures.append("M69 contract helper test module could not be loaded")
            else:
                test_module = importlib.util.module_from_spec(test_spec)
                test_spec.loader.exec_module(test_module)
                risk_decision = test_module._decision()
                request = LowRiskAutonomousDryRunRequest(
                    dry_run_request_ref="low-risk-autonomous-dry-run-request:m69-gate",
                    risk_decision=risk_decision,
                    risk_decision_ref=risk_decision.decision_ref,
                    actor_ref=risk_decision.actor_ref,
                    resource_refs=list(risk_decision.resource_refs),
                    capability_refs=list(risk_decision.capability_refs),
                    allowlist_refs=list(risk_decision.allowlist_refs),
                    bundle_ref=risk_decision.bundle_ref,
                    revocation_record_ref=risk_decision.revocation_record_ref,
                    source_scope_ref=risk_decision.source_scope_ref,
                    audit_ref=risk_decision.audit_ref,
                    replay_ref=risk_decision.replay_ref,
                    steps=[
                        LowRiskAutonomousDryRunStep(
                            step_ref="low-risk-dry-run-step:m69-gate",
                            intent_ref="intent:inspect-redacted-review-packet",
                            capability_ref="capability:observe-only-review",
                            resource_ref="resource:local-prototype",
                            risk_class=AutonomyRiskClass.low,
                            dry_run_outcome_ref="dry-run-outcome:m69-review-only",
                        )
                    ],
                )
                record = build_low_risk_autonomous_dry_run_record(request)
                if (
                    record.derived_risk_class != AutonomyRiskClass.low
                    or not record.dry_run_valid_for_review
                    or not record.review_only
                    or not record.dry_run_only
                    or not record.low_risk_only
                    or record.authority_granted
                    or record.execution_requested
                    or record.execution_performed
                    or record.side_effects_performed
                ):
                    failures.append(
                        "M69 low-risk dry-run record did not remain review-only and no-authority"
                    )
                for update, reason in [
                    (
                        {"derived_risk_class": AutonomyRiskClass.medium},
                        "LOW_RISK_DRY_RUN_RISK_CEILING_DENIED",
                    ),
                    ({"authority_granted": True}, "LOW_RISK_DRY_RUN_AUTHORITY_DENIED"),
                    (
                        {"policy_activation_requested": True},
                        "AUTONOMY_POLICY_ACTIVATION_DENIED",
                    ),
                    (
                        {"session_start_requested": True},
                        "AUTONOMY_SESSION_START_DENIED",
                    ),
                    ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                    ({"execution_requested": True}, "EXECUTION_DENIED"),
                    ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
                    ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
                    (
                        {"metadata": {"api_key": "secret-value"}},
                        "SECRET_LIKE_LOW_RISK_DRY_RUN_CONTENT_DENIED",
                    ),
                ]:
                    try:
                        validate_low_risk_autonomous_dry_run_record(
                            record.model_copy(update=update)
                        )
                        failures.append(
                            f"M69 unsafe low-risk dry-run mutation was not denied: {reason}"
                        )
                    except ValueError as exc:
                        if reason not in str(exc):
                            failures.append(
                                f"M69 unsafe low-risk dry-run reason drifted for {reason}: {exc}"
                            )
        except Exception as exc:
            failures.append(f"M69 low-risk autonomous dry-run validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "low-risk autonomous dry run",
            "contract-only",
            "review-only",
            "dry-run-only",
            "low risk",
            "risk ceiling",
            "autonomy risk classifier",
            "approval refs are identifiers",
            "no policy activation",
            "no session start",
            "no autonomous actions",
            "no background worker",
            "no execution",
            "no tool execution",
            "no shell execution",
            "no network tools",
            "no browser automation",
            "no context injection",
            "no memory write",
            "no backend route",
            "no dependency",
            "m70 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M69 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m69_low_risk_autonomous_dry_run_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "low_risk_dry_run_authority_granted=True",
            "dry_run_execution_performed=True",
            "policy_activation_requested=True",
            "session_start_requested=True",
            "session_active=True",
            "execution_requested=True",
            "execution_performed=True",
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
            "model_provider_call_enabled=True",
            "production_authority_enabled=True",
            "authority_granted=True",
            "/autonomy/dry-run/start",
            "/autonomy/dry-run/execute",
            "/autonomy/dry-run/activate",
            "/autonomy/session/start",
            "/autonomy/policy/activate",
            "/network/fetch",
            "/shell/execute",
            "/browser/click",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/autonomy/dry_run.py",
            "src/ultimate_ai_agent/core/autonomy/risk.py",
            "src/ultimate_ai_agent/core/autonomy/revocation.py",
            "src/ultimate_ai_agent/core/autonomy/approvals.py",
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/simulator.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m69_low_risk_autonomous_dry_run.py",
            "tests/test_m69_gate_integration.py",
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
                            f"M69 forbidden low-risk dry-run fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m69_low_risk_autonomous_dry_run_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m69_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M69 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m69_roadmap_currentness(
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
            f"missing M69 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.73.0" not in text
            or "m69" not in text
            or "low-risk autonomous dry run" not in text
        ):
            failures.append(
                "active docs do not identify v0.73.0/M69 Low-Risk Autonomous Dry Run"
            )
        if (
            "m69 is implemented/released" not in text
            and "v0.73.0 implements m69" not in text
        ):
            failures.append("active docs do not mark M69 implemented/released")
        for version_label, milestone, title in [
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
                    f"active docs missing planned M70-M100 row: {version_label} / {milestone} — {title}"
                )
        forbidden_fragments = [
            "m70 is implemented",
            "autonomy foundation freeze is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ]
        if self._active_version_tuple() >= (0, 74, 0):
            forbidden_fragments = [
                fragment
                for fragment in forbidden_fragments
                if fragment
                not in {
                    "m70 is implemented",
                    "autonomy foundation freeze is implemented",
                }
            ]
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M69 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
