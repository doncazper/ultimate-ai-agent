from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart015Mixin:
    """Legacy checks from m63_autonomy_policy_engine_contract_review through m66_scoped_approval_bundles_contract_review."""
    def check_m63_autonomy_policy_engine_contract_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "tests/test_m63_autonomy_policy_engine_contracts.py",
            "docs/autonomy/AUTONOMY_POLICY_ENGINE_V1.md",
            "docs/autonomy/AUTONOMY_POLICY_RULE_CONTRACTS.md",
            "docs/autonomy/AUTONOMY_POLICY_ENGINE_NON_GOALS.md",
            "docs/autonomy/M63_TO_M64_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
        ]
        failures = [
            f"missing M63 autonomy policy engine file: {path}"
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
                ScopedAutonomySessionRequest,
                ScopedAutonomySessionScope,
                build_autonomy_policy_decision,
                validate_autonomy_policy_evaluation_request,
                validate_autonomy_policy_rule,
            )

            scope = ScopedAutonomySessionScope(
                scope_ref="autonomy-session-scope:m63-gate",
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m63-gate"],
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m63-gate",
                audit_ref="audit:m63-gate",
                replay_ref="replay:m63-gate",
            )
            request = ScopedAutonomySessionRequest(
                session_request_ref="autonomy-session-request:m63-gate",
                requested_mode=AutonomyAuthorityMode.dry_run_plan,
                scope=scope,
                approval_ref="approval:m63-review-only",
            )
            rule = AutonomyPolicyRule(
                rule_ref="autonomy-policy-rule:m63-gate",
                allowed_actor_refs=["actor:gate-reviewer"],
                allowed_resource_refs=["resource:local-prototype"],
                allowed_capability_refs=["capability:observe-only-review"],
                required_allowlist_refs=["allowlist:m63-gate"],
                max_mode=AutonomyAuthorityMode.dry_run_plan,
                max_risk_class=AutonomyRiskClass.low,
                max_duration_seconds=900,
            )
            validate_autonomy_policy_rule(rule)
            evaluation_request = AutonomyPolicyEvaluationRequest(
                evaluation_request_ref="autonomy-policy-evaluation:m63-gate",
                policy=AutonomyPolicyEnginePolicy(
                    policy_ref="autonomy-policy:m63-gate",
                    policy_version_ref="autonomy-policy-version:m63-v1",
                    rules=[rule],
                ),
                session_request=request,
            )
            validate_autonomy_policy_evaluation_request(evaluation_request)
            decision = build_autonomy_policy_decision(evaluation_request)
            if (
                not decision.contract_valid_for_review
                or not decision.policy_matched
                or not decision.policy_allows_review
                or decision.authority_granted
                or decision.session_started
                or decision.execution_performed
                or decision.side_effects_performed
            ):
                failures.append(
                    "M63 autonomy policy decision granted authority or side effects"
                )
            for update, reason in [
                (
                    {"approval_test_ref": "approval_test_:m63"},
                    "APPROVAL_TEST_REF_DENIED",
                ),
                (
                    {"policy_activation_requested": True},
                    "AUTONOMY_POLICY_ACTIVATION_DENIED",
                ),
                ({"session_start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
                ({"execution_requested": True}, "EXECUTION_DENIED"),
            ]:
                try:
                    validate_autonomy_policy_evaluation_request(
                        evaluation_request.model_copy(update=update)
                    )
                    failures.append(
                        f"M63 unsafe policy request mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M63 unsafe policy request reason drifted for {reason}: {exc}"
                        )
            for update, reason in [
                (
                    {"policy_activation_enabled": True},
                    "AUTONOMY_POLICY_ACTIVATION_DENIED",
                ),
                ({"session_start_enabled": True}, "AUTONOMY_SESSION_START_DENIED"),
                ({"execution_enabled": True}, "EXECUTION_DENIED"),
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
            ]:
                try:
                    validate_autonomy_policy_rule(rule.model_copy(update=update))
                    failures.append(
                        f"M63 unsafe policy rule mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M63 unsafe policy rule reason drifted for {reason}: {exc}"
                        )
        except Exception as exc:
            failures.append(f"M63 autonomy policy engine validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "autonomy policy engine v1",
            "contract-only",
            "review-only",
            "policy rules",
            "actor-bound",
            "resource-bound",
            "capability-bound",
            "allowlist",
            "risk ceiling",
            "duration ceiling",
            "revocation",
            "audit/replay",
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
            "no backend route",
            "no dependency",
            "m64 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M63 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m63_autonomy_policy_engine_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "policy_activation_enabled=True",
            "policy_activation_requested=True",
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
            "authority_granted=True",
            "execution_performed=True",
            "/autonomy/policy/evaluate",
            "/autonomy/policy/activate",
            "/autonomy/policy/run",
            "/autonomy/session/start",
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
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m63_autonomy_policy_engine_contracts.py",
            "tests/test_m63_gate_integration.py",
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
                        if sealed_fragment_allowed(rel, text, fragment):
                            continue
                        failures.append(
                            f"M63 forbidden autonomy policy fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m63_autonomy_policy_engine_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m63_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M63 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m63_roadmap_currentness(
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
            f"missing M63 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.67.0" not in text
            or "m63" not in text
            or "autonomy policy engine v1" not in text
        ):
            failures.append(
                "active docs do not identify v0.67.0/M63 Autonomy Policy Engine v1"
            )
        if (
            "m63 is implemented/released" not in text
            and "v0.67.0 implements m63" not in text
        ):
            failures.append("active docs do not mark M63 implemented/released")
        for version_label, milestone, title in [
            ("v0.68.0", "M64", "Autonomous Plan Simulator"),
            ("v0.69.0", "M65", "Autonomy Audit + Replay Viewer"),
            ("v0.70.0", "M66", "Scoped Approval Bundles"),
            ("v0.71.0", "M67", "Revocation + Kill Switch"),
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M63-M100 row: {version_label} / {milestone} — {title}"
                )
        forbidden_fragments = [
            "policy activation is implemented",
            "session start is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ]
        if self._active_version_tuple() < (0, 68, 0):
            forbidden_fragments.extend(
                [
                    "m64 is implemented",
                    "autonomous plan simulator is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M63 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m64_autonomous_plan_simulator_contract_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/simulator.py",
            "tests/test_m64_autonomous_plan_simulator_contracts.py",
            "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR.md",
            "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_CONTRACTS.md",
            "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_NON_GOALS.md",
            "docs/autonomy/M64_TO_M65_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
        ]
        failures = [
            f"missing M64 autonomous plan simulator file: {path}"
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
                build_autonomy_policy_decision,
                validate_autonomous_plan_simulation_request,
            )

            scope = ScopedAutonomySessionScope(
                scope_ref="autonomy-session-scope:m64-gate",
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m64-gate"],
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m64-gate",
                audit_ref="audit:m64-gate",
                replay_ref="replay:m64-gate",
            )
            session_request = ScopedAutonomySessionRequest(
                session_request_ref="autonomy-session-request:m64-gate",
                requested_mode=AutonomyAuthorityMode.dry_run_plan,
                scope=scope,
            )
            rule = AutonomyPolicyRule(
                rule_ref="autonomy-policy-rule:m64-gate",
                allowed_actor_refs=["actor:gate-reviewer"],
                allowed_resource_refs=["resource:local-prototype"],
                allowed_capability_refs=["capability:observe-only-review"],
                required_allowlist_refs=["allowlist:m64-gate"],
                max_mode=AutonomyAuthorityMode.dry_run_plan,
                max_risk_class=AutonomyRiskClass.low,
                max_duration_seconds=900,
            )
            policy_decision = build_autonomy_policy_decision(
                AutonomyPolicyEvaluationRequest(
                    evaluation_request_ref="autonomy-policy-evaluation:m64-gate",
                    policy=AutonomyPolicyEnginePolicy(
                        policy_ref="autonomy-policy:m64-gate",
                        policy_version_ref="autonomy-policy-version:m64-v1",
                        rules=[rule],
                    ),
                    session_request=session_request,
                )
            )
            request = AutonomousPlanSimulationRequest(
                simulation_request_ref="autonomy-plan-simulation-request:m64-gate",
                policy_decision=policy_decision,
                steps=[
                    AutonomousPlanSimulationStep(
                        step_ref="autonomy-simulation-step:m64-gate",
                        intent_ref="intent:inspect-redacted-review-packet",
                        capability_ref="capability:observe-only-review",
                        resource_ref="resource:local-prototype",
                        simulated_outcome_ref="simulation-outcome:m64-review-only",
                    )
                ],
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m64-gate"],
                audit_ref="audit:m64-gate",
                replay_ref="replay:m64-gate",
            )
            validate_autonomous_plan_simulation_request(request)
            result = build_autonomous_plan_simulation_result(request)
            if (
                not result.contract_valid_for_review
                or not result.review_only
                or not result.dry_run_only
                or not result.deterministic
                or result.authority_granted
                or result.session_started
                or result.execution_performed
                or result.side_effects_performed
            ):
                failures.append(
                    "M64 autonomous plan simulator granted authority or side effects"
                )
            for update, reason in [
                (
                    {"approval_test_ref": "approval_test_:m64"},
                    "APPROVAL_TEST_REF_DENIED",
                ),
                (
                    {"policy_activation_requested": True},
                    "AUTONOMY_POLICY_ACTIVATION_DENIED",
                ),
                ({"session_start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
                ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
            ]:
                try:
                    validate_autonomous_plan_simulation_request(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M64 unsafe simulation mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M64 unsafe simulation reason drifted for {reason}: {exc}"
                        )
            for update, reason in [
                ({"authority_granted": True}, "AUTONOMY_POLICY_AUTHORITY_DENIED"),
                ({"session_started": True}, "AUTONOMY_SESSION_START_DENIED"),
                ({"execution_performed": True}, "EXECUTION_DENIED"),
            ]:
                try:
                    validate_autonomous_plan_simulation_request(
                        request.model_copy(
                            update={
                                "policy_decision": policy_decision.model_copy(
                                    update=update
                                )
                            }
                        )
                    )
                    failures.append(
                        f"M64 unsafe policy decision mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M64 unsafe policy decision reason drifted for {reason}: {exc}"
                        )
        except Exception as exc:
            failures.append(f"M64 autonomous plan simulator validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "autonomous plan simulator",
            "contract-only",
            "review-only",
            "dry-run-only",
            "deterministic",
            "dependency graph",
            "acyclic",
            "policy decision",
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
            "m65 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M64 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m64_autonomous_plan_simulator_static_safety(
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
            "production_authority_enabled=True",
            "authority_granted=True",
            "/autonomy/simulate",
            "/autonomy/simulator/run",
            "/autonomy/simulator/execute",
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
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/simulator.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m64_autonomous_plan_simulator_contracts.py",
            "tests/test_m64_gate_integration.py",
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
                        if sealed_fragment_allowed(rel, text, fragment):
                            continue
                        failures.append(
                            f"M64 forbidden autonomy simulation fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m64_autonomous_plan_simulator_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m64_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M64 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m64_roadmap_currentness(
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
            f"missing M64 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.68.0" not in text
            or "m64" not in text
            or "autonomous plan simulator" not in text
        ):
            failures.append(
                "active docs do not identify v0.68.0/M64 Autonomous Plan Simulator"
            )
        if (
            "m64 is implemented/released" not in text
            and "v0.68.0 implements m64" not in text
        ):
            failures.append("active docs do not mark M64 implemented/released")
        for version_label, milestone, title in [
            ("v0.69.0", "M65", "Autonomy Audit + Replay Viewer"),
            ("v0.70.0", "M66", "Scoped Approval Bundles"),
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
                    f"active docs missing planned M64-M100 row: {version_label} / {milestone} — {title}"
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
                    f"M64 docs imply forbidden/future capability: {fragment}"
                )
        version_tuple = self._active_version_tuple()
        if version_tuple < (0, 69, 0):
            for fragment in (
                "m65 is implemented",
                "autonomy audit + replay viewer is implemented",
            ):
                if fragment in text:
                    failures.append(
                        f"M64 docs imply forbidden/future capability: {fragment}"
                    )
        return self._result(criterion, failures, required_docs)

    def check_m65_autonomy_audit_replay_viewer_contract_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/simulator.py",
            "tests/test_m65_autonomy_audit_replay_viewer_contracts.py",
            "docs/autonomy/AUTONOMY_AUDIT_REPLAY_VIEWER.md",
            "docs/autonomy/AUTONOMY_AUDIT_REPLAY_CONTRACTS.md",
            "docs/autonomy/AUTONOMY_AUDIT_REPLAY_NON_GOALS.md",
            "docs/autonomy/M65_TO_M66_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
        ]
        failures = [
            f"missing M65 autonomy audit replay viewer file: {path}"
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
                validate_autonomy_audit_replay_view,
            )

            scope = ScopedAutonomySessionScope(
                scope_ref="autonomy-session-scope:m65-gate",
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m65-gate"],
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m65-gate",
                audit_ref="audit:m65-gate",
                replay_ref="replay:m65-gate",
            )
            session_request = ScopedAutonomySessionRequest(
                session_request_ref="autonomy-session-request:m65-gate",
                requested_mode=AutonomyAuthorityMode.dry_run_plan,
                scope=scope,
            )
            rule = AutonomyPolicyRule(
                rule_ref="autonomy-policy-rule:m65-gate",
                allowed_actor_refs=["actor:gate-reviewer"],
                allowed_resource_refs=["resource:local-prototype"],
                allowed_capability_refs=["capability:observe-only-review"],
                required_allowlist_refs=["allowlist:m65-gate"],
                max_mode=AutonomyAuthorityMode.dry_run_plan,
                max_risk_class=AutonomyRiskClass.low,
                max_duration_seconds=900,
            )
            policy_decision = build_autonomy_policy_decision(
                AutonomyPolicyEvaluationRequest(
                    evaluation_request_ref="autonomy-policy-evaluation:m65-gate",
                    policy=AutonomyPolicyEnginePolicy(
                        policy_ref="autonomy-policy:m65-gate",
                        policy_version_ref="autonomy-policy-version:m65-v1",
                        rules=[rule],
                    ),
                    session_request=session_request,
                )
            )
            simulation_result = build_autonomous_plan_simulation_result(
                AutonomousPlanSimulationRequest(
                    simulation_request_ref="autonomy-plan-simulation-request:m65-gate",
                    policy_decision=policy_decision,
                    steps=[
                        AutonomousPlanSimulationStep(
                            step_ref="autonomy-simulation-step:m65-gate-first",
                            intent_ref="intent:inspect-redacted-review-packet",
                            capability_ref="capability:observe-only-review",
                            resource_ref="resource:local-prototype",
                            simulated_outcome_ref="simulation-outcome:m65-review-only",
                        )
                    ],
                    actor_ref="actor:gate-reviewer",
                    resource_refs=["resource:local-prototype"],
                    capability_refs=["capability:observe-only-review"],
                    allowlist_refs=["allowlist:m65-gate"],
                    audit_ref="audit:m65-gate",
                    replay_ref="replay:m65-gate",
                )
            )
            view = build_autonomy_audit_replay_view(
                audit_view_ref="autonomy-audit-replay-view:m65-gate",
                simulation_result=simulation_result,
                actor_ref="actor:gate-reviewer",
                audit_ref="audit:m65-gate",
                replay_ref="replay:m65-gate",
            )
            if (
                not view.contract_valid_for_review
                or not view.review_only
                or not view.replay_view_only
                or not view.deterministic
                or view.authority_granted
                or view.session_started
                or view.execution_performed
                or view.side_effects_performed
            ):
                failures.append(
                    "M65 autonomy audit replay viewer granted authority or side effects"
                )
            if view.simulation_result_ref != simulation_result.simulation_result_ref:
                failures.append(
                    "M65 replay view does not bind exact simulation result ref"
                )
            if (
                view.replay_steps[0].step_ref
                != simulation_result.simulated_step_refs[0]
            ):
                failures.append(
                    "M65 replay view does not bind exact simulated step refs"
                )
            for update, reason in [
                (
                    {"approval_test_ref": "approval_test_:m65"},
                    "APPROVAL_TEST_REF_DENIED",
                ),
                (
                    {"policy_activation_requested": True},
                    "AUTONOMY_POLICY_ACTIVATION_DENIED",
                ),
                ({"session_start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
                ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
                ({"model_provider_call_enabled": True}, "MODEL_PROVIDER_CALL_DENIED"),
                (
                    {"metadata": {"api_key": "secret-value"}},
                    "SECRET_LIKE_AUTONOMY_AUDIT_REPLAY_CONTENT_DENIED",
                ),
            ]:
                try:
                    validate_autonomy_audit_replay_view(view.model_copy(update=update))
                    failures.append(
                        f"M65 unsafe replay view mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M65 unsafe replay view reason drifted for {reason}: {exc}"
                        )
            for update, reason in [
                ({"authority_granted": True}, "AUTONOMY_POLICY_AUTHORITY_DENIED"),
                ({"session_started": True}, "AUTONOMY_SESSION_START_DENIED"),
                ({"execution_performed": True}, "EXECUTION_DENIED"),
                (
                    {"side_effects_performed": ["tool:unsafe"]},
                    "AUTONOMY_SIDE_EFFECTS_DENIED",
                ),
            ]:
                try:
                    validate_autonomy_audit_replay_view(
                        view.model_copy(
                            update={
                                "simulation_result": simulation_result.model_copy(
                                    update=update
                                )
                            }
                        )
                    )
                    failures.append(
                        f"M65 unsafe simulation-result mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M65 unsafe simulation-result reason drifted for {reason}: {exc}"
                        )
        except Exception as exc:
            failures.append(
                f"M65 autonomy audit replay viewer validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "autonomy audit",
            "replay viewer",
            "contract-only",
            "review-only",
            "replay-view-only",
            "deterministic",
            "exact simulation result",
            "exact replay step",
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
            "m66 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M65 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m65_autonomy_audit_replay_viewer_static_safety(
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
            "/autonomy/audit/replay",
            "/autonomy/replay/run",
            "/autonomy/replay/execute",
            "/autonomy/audit/export",
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
            "src/ultimate_ai_agent/core/autonomy/audit.py",
            "src/ultimate_ai_agent/core/autonomy/policies.py",
            "src/ultimate_ai_agent/core/autonomy/sessions.py",
            "src/ultimate_ai_agent/core/autonomy/simulator.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "tests/test_m65_autonomy_audit_replay_viewer_contracts.py",
            "tests/test_m65_gate_integration.py",
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
                        if sealed_fragment_allowed(rel, text, fragment):
                            continue
                        failures.append(
                            f"M65 forbidden autonomy audit replay fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m65_autonomy_audit_replay_viewer_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m65_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M65 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m65_roadmap_currentness(
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
            f"missing M65 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.69.0" not in text
            or "m65" not in text
            or "autonomy audit + replay viewer" not in text
        ):
            failures.append(
                "active docs do not identify v0.69.0/M65 Autonomy Audit + Replay Viewer"
            )
        if (
            "m65 is implemented/released" not in text
            and "v0.69.0 implements m65" not in text
        ):
            failures.append("active docs do not mark M65 implemented/released")
        for version_label, milestone, title in [
            ("v0.70.0", "M66", "Scoped Approval Bundles"),
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
                    f"active docs missing planned M65-M100 row: {version_label} / {milestone} — {title}"
                )
        forbidden_fragments = [
            "m66 is implemented",
            "scoped approval bundles are implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "tool execution is implemented",
            "shell execution is implemented",
            "browser automation is implemented",
        ]
        if self._active_version_tuple() >= (0, 70, 0):
            forbidden_fragments = [
                fragment
                for fragment in forbidden_fragments
                if fragment
                not in {"m66 is implemented", "scoped approval bundles are implemented"}
            ]
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M65 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m66_scoped_approval_bundles_contract_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/approvals.py",
            "tests/test_m66_scoped_approval_bundles.py",
            "docs/autonomy/SCOPED_APPROVAL_BUNDLES.md",
            "docs/autonomy/SCOPED_APPROVAL_BUNDLE_CONTRACTS.md",
            "docs/autonomy/SCOPED_APPROVAL_BUNDLE_NON_GOALS.md",
            "docs/autonomy/M66_TO_M67_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
        ]
        failures = [
            f"missing M66 scoped approval bundle file: {path}"
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
                build_scoped_approval_bundle,
                validate_scoped_approval_bundle,
            )

            scope = ScopedAutonomySessionScope(
                scope_ref="autonomy-session-scope:m66-gate",
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m66-gate"],
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m66-gate",
                audit_ref="audit:m66-gate",
                replay_ref="replay:m66-gate",
            )
            session_request = ScopedAutonomySessionRequest(
                session_request_ref="autonomy-session-request:m66-gate",
                requested_mode=AutonomyAuthorityMode.dry_run_plan,
                scope=scope,
            )
            rule = AutonomyPolicyRule(
                rule_ref="autonomy-policy-rule:m66-gate",
                allowed_actor_refs=["actor:gate-reviewer"],
                allowed_resource_refs=["resource:local-prototype"],
                allowed_capability_refs=["capability:observe-only-review"],
                required_allowlist_refs=["allowlist:m66-gate"],
                max_mode=AutonomyAuthorityMode.dry_run_plan,
                max_risk_class=AutonomyRiskClass.low,
                max_duration_seconds=900,
            )
            policy_decision = build_autonomy_policy_decision(
                AutonomyPolicyEvaluationRequest(
                    evaluation_request_ref="autonomy-policy-evaluation:m66-gate",
                    policy=AutonomyPolicyEnginePolicy(
                        policy_ref="autonomy-policy:m66-gate",
                        policy_version_ref="autonomy-policy-version:m66-v1",
                        rules=[rule],
                    ),
                    session_request=session_request,
                )
            )
            simulation_result = build_autonomous_plan_simulation_result(
                AutonomousPlanSimulationRequest(
                    simulation_request_ref="autonomy-plan-simulation-request:m66-gate",
                    policy_decision=policy_decision,
                    steps=[
                        AutonomousPlanSimulationStep(
                            step_ref="autonomy-simulation-step:m66-gate",
                            intent_ref="intent:inspect-redacted-review-packet",
                            capability_ref="capability:observe-only-review",
                            resource_ref="resource:local-prototype",
                            simulated_outcome_ref="simulation-outcome:m66-review-only",
                        )
                    ],
                    actor_ref="actor:gate-reviewer",
                    resource_refs=["resource:local-prototype"],
                    capability_refs=["capability:observe-only-review"],
                    allowlist_refs=["allowlist:m66-gate"],
                    audit_ref="audit:m66-gate",
                    replay_ref="replay:m66-gate",
                )
            )
            replay_view = build_autonomy_audit_replay_view(
                audit_view_ref="autonomy-audit-replay-view:m66-gate",
                simulation_result=simulation_result,
                actor_ref="actor:gate-reviewer",
                audit_ref="audit:m66-gate",
                replay_ref="replay:m66-gate",
            )
            bundle = build_scoped_approval_bundle(
                bundle_ref="scoped-approval-bundle:m66-gate",
                source_scope=scope,
                audit_replay_view=replay_view,
                approval_refs=["approval:m66-gate-review", "approval:m66-gate-dry-run"],
                actor_ref="actor:gate-reviewer",
                resource_refs=["resource:local-prototype"],
                capability_refs=["capability:observe-only-review"],
                allowlist_refs=["allowlist:m66-gate"],
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:m66-gate",
                audit_ref="audit:m66-gate",
                replay_ref="replay:m66-gate",
            )
            if (
                not bundle.bundle_valid_for_review
                or not bundle.review_only
                or not bundle.approval_refs_are_identifiers_only
                or not bundle.non_transferable
                or not bundle.revocable
                or not bundle.replay_safe
                or bundle.authority_granted
                or bundle.session_started
                or bundle.execution_performed
                or bundle.side_effects_performed
            ):
                failures.append(
                    "M66 scoped approval bundle granted authority or side effects"
                )
            for update, reason in [
                (
                    {"approval_test_ref": "approval_test_:m66"},
                    "APPROVAL_TEST_REF_DENIED",
                ),
                (
                    {
                        "approval_refs": [
                            "approval:m66-gate-review",
                            "approval:m66-gate-review",
                        ]
                    },
                    "APPROVAL_BUNDLE_DUPLICATE_REF_DENIED",
                ),
                ({"revoked": True}, "APPROVAL_BUNDLE_REVOKED_DENIED"),
                ({"expired": True}, "APPROVAL_BUNDLE_EXPIRED_DENIED"),
                ({"replay_used": True}, "APPROVAL_BUNDLE_REPLAY_DENIED"),
                ({"authority_granted": True}, "AUTONOMY_POLICY_AUTHORITY_DENIED"),
                ({"session_start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
                ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
                (
                    {"metadata": {"api_key": "secret-value"}},
                    "SECRET_LIKE_SCOPED_APPROVAL_BUNDLE_CONTENT_DENIED",
                ),
            ]:
                try:
                    validate_scoped_approval_bundle(bundle.model_copy(update=update))
                    failures.append(
                        f"M66 unsafe approval bundle mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M66 unsafe approval bundle reason drifted for {reason}: {exc}"
                        )
            try:
                validate_scoped_approval_bundle(
                    bundle.model_copy(update={"actor_ref": "actor:other-reviewer"})
                )
                failures.append("M66 actor binding drift was not denied")
            except ValueError as exc:
                if "APPROVAL_BUNDLE_ACTOR_BINDING_MISMATCH_DENIED" not in str(exc):
                    failures.append(f"M66 actor binding reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M66 scoped approval bundle validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "scoped approval bundles",
            "contract-only",
            "review-only",
            "exact-scope",
            "actor-bound",
            "resource-bound",
            "capability-bound",
            "allowlist-bound",
            "non-transferable",
            "revocable",
            "replay-safe",
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
            "m67 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M66 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)
