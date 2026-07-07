from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart021Mixin:
    """Legacy checks from m84_roadmap_currentness through m87_sandboxed_command_audit_replay_contract."""
    def check_m84_roadmap_currentness(
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
            f"missing M84 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.88.0" not in text
            or "m84" not in text
            or "sandboxed echo/no-op command" not in text
        ):
            failures.append(
                "active docs do not identify v0.88.0/M84 Sandboxed Echo/No-Op Command"
            )
        if (
            "m84 is implemented/released" not in text
            and "v0.88.0 implements m84" not in text
        ):
            failures.append("active docs do not mark M84 implemented/released")
        for version_label, milestone, title in [
            ("v0.89.0", "M85", "Read-Only Command Allowlist"),
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
                    f"active docs missing planned M85-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "subprocess execution is implemented",
            "shell execution is implemented",
            "process spawn is implemented",
            "filesystem mutation is implemented",
            "network access is implemented",
            "browser click is implemented",
            "plugin execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M84 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m85_read_only_command_allowlist_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/read_only_command_allowlist.py",
            "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST.md",
            "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_POLICY.md",
            "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_RECEIPT_PLAN.md",
            "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_NON_GOALS.md",
            "docs/sandbox/M85_TO_M86_BOUNDARY.md",
            "docs/release_notes/v0_89_0.md",
            "docs/archive/releases/v0_89_0/README_IMPORT.md",
            "docs/archive/releases/v0_89_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_89_0.md",
            "tests/test_m85_read_only_command_allowlist.py",
            "tests/test_m85_gate_integration.py",
        ]
        failures = [
            f"missing M85 read-only command allowlist file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.sandbox import (
                CommandProposalRequest,
                ReadOnlyCommandAllowlistEntry,
                ReadOnlyCommandAllowlistRequest,
                ReadOnlyCommandAllowlistStatus,
                SandboxedEchoNoOpCommandRequest,
                ShellDryRunClassifierRequest,
                build_command_proposal,
                build_read_only_command_allowlist_decision,
                build_sandboxed_echo_noop_command,
                build_shell_dry_run_classification,
            )

            proposal = build_command_proposal(
                CommandProposalRequest(
                    request_ref="command-proposal-request:gate-m85",
                    proposal_ref="command-proposal:gate-m85",
                    sandbox_spec_ref="runtime-sandbox-spec:m81",
                    baseline_ref="baseline:v0.88.0",
                    actor_ref="actor:gate-m85",
                    prior_milestone_refs=[
                        "milestone:M57",
                        "milestone:M58",
                        "milestone:M80",
                        "milestone:M81",
                    ],
                    command_ref="command-ref:gate-noop",
                    safe_purpose="Gate verifies a no-effect command proposal for read-only allowlist review.",
                    safe_command_label="gate noop review",
                    argv_preview=["gate-noop", "--dry-summary"],
                )
            )
            classification = build_shell_dry_run_classification(
                ShellDryRunClassifierRequest(
                    request_ref="shell-dry-run-classifier-request:gate-m85",
                    classifier_ref="shell-dry-run-classifier:gate-m85",
                    command_proposal_ref=proposal.proposal_ref,
                    sandbox_spec_ref=proposal.sandbox_spec_ref,
                    baseline_ref="baseline:v0.88.0",
                    actor_ref=proposal.actor_ref,
                    prior_milestone_refs=[
                        "milestone:M57",
                        "milestone:M58",
                        "milestone:M80",
                        "milestone:M81",
                        "milestone:M82",
                    ],
                    command_proposal=proposal,
                )
            )
            sandboxed = build_sandboxed_echo_noop_command(
                SandboxedEchoNoOpCommandRequest(
                    request_ref="sandboxed-echo-noop-command-request:gate-m85",
                    sandboxed_command_ref="sandboxed-echo-noop-command:gate-m85",
                    shell_dry_run_classifier_ref=classification.classifier_ref,
                    shell_dry_run_decision_ref=classification.decision_ref,
                    command_proposal_ref=classification.command_proposal_ref,
                    sandbox_spec_ref=classification.sandbox_spec_ref,
                    baseline_ref="baseline:v0.88.0",
                    actor_ref=classification.actor_ref,
                    prior_milestone_refs=[
                        "milestone:M57",
                        "milestone:M58",
                        "milestone:M80",
                        "milestone:M81",
                        "milestone:M82",
                        "milestone:M83",
                    ],
                    safe_echo_text="Gate verifies M85 upstream safe no-op text.",
                    shell_dry_run_classification=classification,
                )
            )
            request = ReadOnlyCommandAllowlistRequest(
                request_ref="read-only-command-allowlist-request:gate-m85",
                allowlist_ref="read-only-command-allowlist:gate-m85",
                sandboxed_command_ref=sandboxed.sandboxed_command_ref,
                sandboxed_echo_noop_decision_ref=sandboxed.decision_ref,
                shell_dry_run_decision_ref=sandboxed.shell_dry_run_decision_ref,
                command_proposal_ref=sandboxed.command_proposal_ref,
                command_ref="command-ref:gate-noop",
                sandbox_spec_ref=sandboxed.sandbox_spec_ref,
                baseline_ref="baseline:v0.88.0",
                actor_ref=sandboxed.actor_ref,
                prior_milestone_refs=[
                    "milestone:M57",
                    "milestone:M58",
                    "milestone:M80",
                    "milestone:M81",
                    "milestone:M82",
                    "milestone:M83",
                    "milestone:M84",
                ],
                sandboxed_echo_noop_decision=sandboxed,
                entries=[
                    ReadOnlyCommandAllowlistEntry(
                        entry_ref="read-only-command-allowlist-entry:gate-m85",
                        command_ref="command-ref:gate-noop",
                        safe_command_label="gate noop review",
                        safe_argument_profile_ref="safe-argument-profile:gate-m85",
                        reviewed_by_actor_ref=sandboxed.actor_ref,
                    )
                ],
                requested_command_ref="command-ref:gate-noop",
                safe_purpose="Gate verifies read-only command allowlist contracts.",
            )
            decision = build_read_only_command_allowlist_decision(request)
            if (
                decision.status != ReadOnlyCommandAllowlistStatus.allowlisted_for_review
                or not decision.allowlist_match_found
                or not decision.contract_only
                or not decision.review_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.read_only_only
                or decision.command_execution_authorized
                or decision.shell_execution_authorized
                or decision.subprocess_execution_authorized
                or decision.process_spawn_authorized
                or decision.command_execution_performed
                or decision.subprocess_execution_performed
                or decision.shell_execution_performed
                or decision.process_spawn_performed
                or decision.filesystem_mutation_performed
                or decision.network_access_performed
                or decision.tool_execution_performed
                or decision.browser_automation_performed
                or decision.plugin_execution_performed
                or decision.remote_execution_performed
                or decision.model_call_performed
                or decision.memory_write_performed
                or decision.context_injection_performed
                or decision.background_worker_started
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.production_authority_granted
                or decision.side_effects_performed
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_allowlist_refs_only
                or decision.receipt_plan.store_raw_command
                or decision.receipt_plan.store_shell_string
                or decision.receipt_plan.store_raw_output
                or "M85_READ_ONLY_COMMAND_ALLOWLIST_CONTRACT_ONLY"
                not in decision.reason_codes
                or "M85_EXACT_M84_BINDING_REQUIRED" not in decision.reason_codes
                or "M85_NO_COMMAND_EXECUTION" not in decision.reason_codes
                or "M86_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M85 read-only command allowlist decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"command_execution_requested": True}, "COMMAND_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"contains_shell_string": True}, "M85_SHELL_STRING_DENIED"),
                ({"contains_raw_command": True}, "M85_RAW_COMMAND_DENIED"),
                ({"contains_raw_output": True}, "M85_RAW_OUTPUT_DENIED"),
                (
                    {"contains_secret": True},
                    "SECRET_LIKE_COMMAND_ALLOWLIST_CONTENT_DENIED",
                ),
            ]:
                try:
                    build_read_only_command_allowlist_decision(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M85 unsafe command allowlist request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M85 unsafe command allowlist request raised {exc!s}, expected {reason}"
                        )
        except Exception as exc:
            failures.append(f"M85 read-only command allowlist validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "read-only command allowlist",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "m84 sandboxed echo/no-op command",
            "exact m84 binding",
            "safe refs only",
            "no shell string",
            "no raw command",
            "no raw output",
            "no command execution",
            "no subprocess execution",
            "no shell execution",
            "no process spawn",
            "no filesystem mutation",
            "no network access",
            "no tool execution",
            "no browser automation",
            "no plugin execution",
            "no remote execution",
            "no model call",
            "no memory write",
            "no context injection",
            "no background worker",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "safe summary only",
            "evaluator boundaries revalidate",
            "m86 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M85 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m85_read_only_command_allowlist_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "command_execution_enabled=True",
            "command_execution_requested=True",
            "subprocess_execution_enabled=True",
            "subprocess_execution_requested=True",
            "shell_execution_enabled=True",
            "shell_execution_requested=True",
            "process_spawn_enabled=True",
            "process_spawn_requested=True",
            "filesystem_mutation_enabled=True",
            "network_access_enabled=True",
            "tool_execution_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "remote_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "background_worker_enabled=True",
            "backend_route_enabled=True",
            "control_center_control_enabled=True",
            "dependency_change_enabled=True",
            "production_authority_enabled=True",
            "command_execution_authorized=True",
            "shell_execution_authorized=True",
            "subprocess_execution_authorized=True",
            "process_spawn_authorized=True",
            "command_execution_performed=True",
            "subprocess_execution_performed=True",
            "shell_execution_performed=True",
            "process_spawn_performed=True",
            "filesystem_mutation_performed=True",
            "network_access_performed=True",
            "tool_execution_performed=True",
            "browser_automation_performed=True",
            "plugin_execution_performed=True",
            "remote_execution_performed=True",
            "model_call_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "background_worker_started=True",
            "production_authority_granted=True",
            "store_raw_command=True",
            "store_shell_string=True",
            "store_raw_output=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/command_proposal.py",
            "src/ultimate_ai_agent/core/sandbox/runtime_spec.py",
            "src/ultimate_ai_agent/core/sandbox/shell_dry_run_classifier.py",
            "src/ultimate_ai_agent/core/sandbox/sandboxed_echo_noop_command.py",
            "src/ultimate_ai_agent/core/sandbox/read_only_command_allowlist.py",
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
                            f"M85 forbidden read-only command allowlist fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m85_read_only_command_allowlist_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m85_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M85 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m85_roadmap_currentness(
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
            f"missing M85 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.89.0" not in text
            or "m85" not in text
            or "read-only command allowlist" not in text
        ):
            failures.append(
                "active docs do not identify v0.89.0/M85 Read-Only Command Allowlist"
            )
        if (
            "m85 is implemented/released" not in text
            and "v0.89.0 implements m85" not in text
        ):
            failures.append("active docs do not mark M85 implemented/released")
        for version_label, milestone, title in [
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
                    f"active docs missing planned M86-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "subprocess execution is implemented",
            "shell execution is implemented",
            "process spawn is implemented",
            "filesystem mutation is implemented",
            "network access is implemented",
            "browser click is implemented",
            "plugin execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M85 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m86_shell_approval_gate_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/shell_approval_gate.py",
            "docs/sandbox/SHELL_APPROVAL_GATE.md",
            "docs/sandbox/SHELL_APPROVAL_GATE_POLICY.md",
            "docs/sandbox/SHELL_APPROVAL_GATE_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/SHELL_APPROVAL_GATE_RECEIPT_PLAN.md",
            "docs/sandbox/SHELL_APPROVAL_GATE_NON_GOALS.md",
            "docs/sandbox/M86_TO_M87_BOUNDARY.md",
            "docs/release_notes/v0_90_0.md",
            "docs/archive/releases/v0_90_0/README_IMPORT.md",
            "docs/archive/releases/v0_90_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_90_0.md",
            "tests/test_m86_shell_approval_gate.py",
            "tests/test_m86_gate_integration.py",
        ]
        failures = [
            f"missing M86 shell approval gate file: {path}"
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
                AutonomousPlanSimulationRequest,
                AutonomousPlanSimulationStep,
                ScopedAutonomySessionRequest,
                ScopedAutonomySessionScope,
                build_autonomous_plan_simulation_result,
                build_autonomy_audit_replay_view,
                build_autonomy_policy_decision,
                build_scoped_approval_bundle,
            )
            from ultimate_ai_agent.core.sandbox import (
                CommandProposalRequest,
                ReadOnlyCommandAllowlistEntry,
                ReadOnlyCommandAllowlistRequest,
                SandboxedEchoNoOpCommandRequest,
                ShellApprovalGateRequest,
                ShellApprovalGateStatus,
                ShellDryRunClassifierRequest,
                build_command_proposal,
                build_read_only_command_allowlist_decision,
                build_sandboxed_echo_noop_command,
                build_shell_approval_gate_decision,
                build_shell_dry_run_classification,
            )

            proposal = build_command_proposal(
                CommandProposalRequest(
                    request_ref="command-proposal-request:gate-m86",
                    proposal_ref="command-proposal:gate-m86",
                    sandbox_spec_ref="runtime-sandbox-spec:m81",
                    baseline_ref="baseline:v0.89.0",
                    actor_ref="actor:gate-m86",
                    prior_milestone_refs=[
                        "milestone:M57",
                        "milestone:M58",
                        "milestone:M80",
                        "milestone:M81",
                    ],
                    command_ref="command-ref:gate-m86-noop",
                    safe_purpose="Gate verifies a no-effect command proposal for shell approval gate review.",
                    safe_command_label="gate m86 noop review",
                    argv_preview=["gate-noop", "--dry-summary"],
                )
            )
            classification = build_shell_dry_run_classification(
                ShellDryRunClassifierRequest(
                    request_ref="shell-dry-run-classifier-request:gate-m86",
                    classifier_ref="shell-dry-run-classifier:gate-m86",
                    command_proposal_ref=proposal.proposal_ref,
                    sandbox_spec_ref=proposal.sandbox_spec_ref,
                    baseline_ref="baseline:v0.89.0",
                    actor_ref=proposal.actor_ref,
                    prior_milestone_refs=[
                        "milestone:M57",
                        "milestone:M58",
                        "milestone:M80",
                        "milestone:M81",
                        "milestone:M82",
                    ],
                    command_proposal=proposal,
                )
            )
            sandboxed = build_sandboxed_echo_noop_command(
                SandboxedEchoNoOpCommandRequest(
                    request_ref="sandboxed-echo-noop-command-request:gate-m86",
                    sandboxed_command_ref="sandboxed-echo-noop-command:gate-m86",
                    shell_dry_run_classifier_ref=classification.classifier_ref,
                    shell_dry_run_decision_ref=classification.decision_ref,
                    command_proposal_ref=classification.command_proposal_ref,
                    sandbox_spec_ref=classification.sandbox_spec_ref,
                    baseline_ref="baseline:v0.89.0",
                    actor_ref=classification.actor_ref,
                    prior_milestone_refs=[
                        "milestone:M57",
                        "milestone:M58",
                        "milestone:M80",
                        "milestone:M81",
                        "milestone:M82",
                        "milestone:M83",
                    ],
                    safe_echo_text="Gate verifies M86 upstream safe no-op text.",
                    shell_dry_run_classification=classification,
                )
            )
            allowlist_decision = build_read_only_command_allowlist_decision(
                ReadOnlyCommandAllowlistRequest(
                    request_ref="read-only-command-allowlist-request:gate-m86",
                    allowlist_ref="read-only-command-allowlist:gate-m86",
                    sandboxed_command_ref=sandboxed.sandboxed_command_ref,
                    sandboxed_echo_noop_decision_ref=sandboxed.decision_ref,
                    shell_dry_run_decision_ref=sandboxed.shell_dry_run_decision_ref,
                    command_proposal_ref=sandboxed.command_proposal_ref,
                    command_ref="command-ref:gate-m86-noop",
                    sandbox_spec_ref=sandboxed.sandbox_spec_ref,
                    baseline_ref="baseline:v0.89.0",
                    actor_ref=sandboxed.actor_ref,
                    prior_milestone_refs=[
                        "milestone:M57",
                        "milestone:M58",
                        "milestone:M80",
                        "milestone:M81",
                        "milestone:M82",
                        "milestone:M83",
                        "milestone:M84",
                    ],
                    sandboxed_echo_noop_decision=sandboxed,
                    entries=[
                        ReadOnlyCommandAllowlistEntry(
                            entry_ref="read-only-command-allowlist-entry:gate-m86",
                            command_ref="command-ref:gate-m86-noop",
                            safe_command_label="gate m86 noop review",
                            safe_argument_profile_ref="safe-argument-profile:gate-m86",
                            reviewed_by_actor_ref=sandboxed.actor_ref,
                        )
                    ],
                    requested_command_ref="command-ref:gate-m86-noop",
                    safe_purpose="Gate verifies read-only command allowlist before shell approval.",
                )
            )
            scope = ScopedAutonomySessionScope(
                scope_ref="autonomy-session-scope:gate-m86",
                actor_ref=allowlist_decision.actor_ref,
                resource_refs=[
                    allowlist_decision.command_ref,
                    allowlist_decision.sandbox_spec_ref,
                ],
                capability_refs=["capability:shell-approval-gate-review"],
                allowlist_refs=[allowlist_decision.allowlist_ref],
                max_duration_seconds=900,
                risk_class=AutonomyRiskClass.low,
                revocation_ref="revocation:gate-m86",
                audit_ref="audit:gate-m86",
                replay_ref="replay:gate-m86",
            )
            policy_decision = build_autonomy_policy_decision(
                AutonomyPolicyEvaluationRequest(
                    evaluation_request_ref="autonomy-policy-evaluation:gate-m86",
                    policy=AutonomyPolicyEnginePolicy(
                        policy_ref="autonomy-policy:gate-m86",
                        policy_version_ref="autonomy-policy-version:gate-m86-v1",
                        rules=[
                            AutonomyPolicyRule(
                                rule_ref="autonomy-policy-rule:gate-m86",
                                allowed_actor_refs=[scope.actor_ref],
                                allowed_resource_refs=list(scope.resource_refs),
                                allowed_capability_refs=list(scope.capability_refs),
                                required_allowlist_refs=list(scope.allowlist_refs),
                                max_mode=AutonomyAuthorityMode.dry_run_plan,
                                max_risk_class=AutonomyRiskClass.low,
                                max_duration_seconds=900,
                            )
                        ],
                    ),
                    session_request=ScopedAutonomySessionRequest(
                        session_request_ref="autonomy-session-request:gate-m86",
                        requested_mode=AutonomyAuthorityMode.dry_run_plan,
                        scope=scope,
                    ),
                )
            )
            simulation = build_autonomous_plan_simulation_result(
                AutonomousPlanSimulationRequest(
                    simulation_request_ref="autonomy-plan-simulation-request:gate-m86",
                    policy_decision=policy_decision,
                    steps=[
                        AutonomousPlanSimulationStep(
                            step_ref="autonomy-simulation-step:gate-m86-review",
                            intent_ref="intent:shell-approval-gate-review",
                            capability_ref="capability:shell-approval-gate-review",
                            resource_ref=allowlist_decision.command_ref,
                            simulated_outcome_ref="simulation-outcome:gate-m86-review-only",
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
                audit_view_ref="autonomy-audit-replay-view:gate-m86",
                simulation_result=simulation,
                actor_ref=scope.actor_ref,
                audit_ref=scope.audit_ref,
                replay_ref=scope.replay_ref,
            )
            bundle = build_scoped_approval_bundle(
                bundle_ref="scoped-approval-bundle:gate-m86",
                source_scope=scope,
                audit_replay_view=audit_view,
                approval_refs=["approval:gate-m86"],
                actor_ref=scope.actor_ref,
                resource_refs=list(scope.resource_refs),
                capability_refs=list(scope.capability_refs),
                allowlist_refs=list(scope.allowlist_refs),
                max_duration_seconds=scope.max_duration_seconds,
                risk_class=scope.risk_class,
                revocation_ref=scope.revocation_ref,
                audit_ref=scope.audit_ref,
                replay_ref=scope.replay_ref,
            )
            request = ShellApprovalGateRequest(
                request_ref="shell-approval-gate-request:gate-m86",
                gate_ref="shell-approval-gate:gate-m86",
                read_only_command_allowlist_decision_ref=allowlist_decision.decision_ref,
                allowlist_ref=allowlist_decision.allowlist_ref,
                sandboxed_command_ref=allowlist_decision.sandboxed_command_ref,
                sandboxed_echo_noop_decision_ref=(
                    allowlist_decision.sandboxed_echo_noop_decision_ref
                ),
                shell_dry_run_decision_ref=allowlist_decision.shell_dry_run_decision_ref,
                command_proposal_ref=allowlist_decision.command_proposal_ref,
                command_ref=allowlist_decision.command_ref,
                sandbox_spec_ref=allowlist_decision.sandbox_spec_ref,
                baseline_ref="baseline:v0.89.0",
                actor_ref=allowlist_decision.actor_ref,
                approval_bundle_ref=bundle.bundle_ref,
                approval_ref="approval:gate-m86",
                revocation_ref=bundle.revocation_ref,
                audit_ref=bundle.audit_ref,
                replay_ref=bundle.replay_ref,
                prior_milestone_refs=[
                    "milestone:M57",
                    "milestone:M58",
                    "milestone:M80",
                    "milestone:M81",
                    "milestone:M82",
                    "milestone:M83",
                    "milestone:M84",
                    "milestone:M85",
                ],
                read_only_command_allowlist_decision=allowlist_decision,
                approval_bundle=bundle,
                safe_purpose="Gate verifies M86 shell approval gate contracts.",
            )
            decision = build_shell_approval_gate_decision(request)
            if (
                decision.status != ShellApprovalGateStatus.approved_for_review
                or not decision.approval_valid_for_review
                or not decision.contract_only
                or not decision.review_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.read_only_only
                or not decision.approval_ref_is_identifier_only
                or not decision.approval_bound_to_allowlist
                or not decision.approval_bound_to_command
                or not decision.approval_bound_to_actor
                or not decision.approval_bound_to_sandbox
                or decision.command_execution_authorized
                or decision.shell_execution_authorized
                or decision.subprocess_execution_authorized
                or decision.process_spawn_authorized
                or decision.command_execution_performed
                or decision.subprocess_execution_performed
                or decision.shell_execution_performed
                or decision.process_spawn_performed
                or decision.filesystem_mutation_performed
                or decision.network_access_performed
                or decision.tool_execution_performed
                or decision.browser_automation_performed
                or decision.plugin_execution_performed
                or decision.remote_execution_performed
                or decision.model_call_performed
                or decision.memory_write_performed
                or decision.context_injection_performed
                or decision.background_worker_started
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.production_authority_granted
                or decision.side_effects_performed
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or decision.receipt_plan.store_raw_command
                or decision.receipt_plan.store_shell_string
                or decision.receipt_plan.store_raw_output
                or "M86_SHELL_APPROVAL_GATE_REVIEW_ONLY" not in decision.reason_codes
                or "M86_EXACT_M85_ALLOWLIST_BINDING_REQUIRED"
                not in decision.reason_codes
                or "M86_NO_SHELL_EXECUTION" not in decision.reason_codes
                or "M87_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M86 shell approval gate decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"command_execution_requested": True}, "COMMAND_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"contains_shell_string": True}, "M86_SHELL_STRING_DENIED"),
                ({"contains_raw_command": True}, "M86_RAW_COMMAND_DENIED"),
                ({"contains_raw_output": True}, "M86_RAW_OUTPUT_DENIED"),
                (
                    {"contains_secret": True},
                    "SECRET_LIKE_SHELL_APPROVAL_GATE_CONTENT_DENIED",
                ),
            ]:
                try:
                    build_shell_approval_gate_decision(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M86 unsafe shell approval gate request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M86 unsafe shell approval gate request raised {exc!s}, expected {reason}"
                        )
        except Exception as exc:
            failures.append(f"M86 shell approval gate validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "shell approval gate",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "m85 read-only command allowlist",
            "exact m85 binding",
            "scoped approval bundle",
            "approval refs are identifiers only",
            "safe refs only",
            "no shell string",
            "no raw command",
            "no raw output",
            "no command execution",
            "no subprocess execution",
            "no shell execution",
            "no process spawn",
            "no filesystem mutation",
            "no network access",
            "no tool execution",
            "no browser automation",
            "no plugin execution",
            "no remote execution",
            "no model call",
            "no memory write",
            "no context injection",
            "no background worker",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "safe summary only",
            "evaluator boundaries revalidate",
            "m87 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M86 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m86_shell_approval_gate_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "command_execution_enabled=True",
            "command_execution_requested=True",
            "subprocess_execution_enabled=True",
            "subprocess_execution_requested=True",
            "shell_execution_enabled=True",
            "shell_execution_requested=True",
            "process_spawn_enabled=True",
            "process_spawn_requested=True",
            "filesystem_mutation_enabled=True",
            "network_access_enabled=True",
            "tool_execution_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "remote_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "background_worker_enabled=True",
            "backend_route_enabled=True",
            "control_center_control_enabled=True",
            "dependency_change_enabled=True",
            "production_authority_enabled=True",
            "command_execution_authorized=True",
            "shell_execution_authorized=True",
            "subprocess_execution_authorized=True",
            "process_spawn_authorized=True",
            "command_execution_performed=True",
            "subprocess_execution_performed=True",
            "shell_execution_performed=True",
            "process_spawn_performed=True",
            "filesystem_mutation_performed=True",
            "network_access_performed=True",
            "tool_execution_performed=True",
            "browser_automation_performed=True",
            "plugin_execution_performed=True",
            "remote_execution_performed=True",
            "model_call_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "background_worker_started=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "store_raw_command=True",
            "store_shell_string=True",
            "store_raw_output=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/command_proposal.py",
            "src/ultimate_ai_agent/core/sandbox/runtime_spec.py",
            "src/ultimate_ai_agent/core/sandbox/shell_dry_run_classifier.py",
            "src/ultimate_ai_agent/core/sandbox/sandboxed_echo_noop_command.py",
            "src/ultimate_ai_agent/core/sandbox/read_only_command_allowlist.py",
            "src/ultimate_ai_agent/core/sandbox/shell_approval_gate.py",
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
                            f"M86 forbidden shell approval gate fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m86_shell_approval_gate_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m86_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M86 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m86_roadmap_currentness(
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
            f"missing M86 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.90.0" not in text
            or "m86" not in text
            or "shell approval gate v1" not in text
        ):
            failures.append(
                "active docs do not identify v0.90.0/M86 Shell Approval Gate v1"
            )
        if (
            "m86 is implemented/released" not in text
            and "v0.90.0 implements m86" not in text
        ):
            failures.append("active docs do not mark M86 implemented/released")
        for version_label, milestone, title in [
            ("v0.91.0", "M87", "Sandboxed Command Audit Replay"),
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
                    f"active docs missing planned M87-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "subprocess execution is implemented",
            "shell execution is implemented",
            "process spawn is implemented",
            "filesystem mutation is implemented",
            "network access is implemented",
            "browser click is implemented",
            "plugin execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M86 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m87_sandboxed_command_audit_replay_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/command_audit_replay.py",
            "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY.md",
            "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_POLICY.md",
            "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_RECEIPT_PLAN.md",
            "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_NON_GOALS.md",
            "docs/sandbox/M87_TO_M88_BOUNDARY.md",
            "docs/release_notes/v0_91_0.md",
            "docs/archive/releases/v0_91_0/README_IMPORT.md",
            "docs/archive/releases/v0_91_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_91_0.md",
            "tests/test_m87_sandboxed_command_audit_replay.py",
            "tests/test_m87_gate_integration.py",
        ]
        failures = [
            f"missing M87 sandboxed command audit replay file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.sandbox import (
                SandboxedCommandAuditReplayRequest,
                SandboxedCommandAuditReplayStep,
                SandboxedCommandAuditReplayStatus,
                ShellApprovalGateDecision,
                ShellApprovalGateReceiptPlan,
                build_sandboxed_command_audit_replay,
                validate_sandboxed_command_audit_replay_decision,
                validate_shell_approval_gate_decision,
            )

            gate = validate_shell_approval_gate_decision(
                ShellApprovalGateDecision(
                    decision_ref="shell-approval-gate-decision:gate-m87",
                    gate_ref="shell-approval-gate:gate-m87",
                    request_ref="shell-approval-gate-request:gate-m87",
                    read_only_command_allowlist_decision_ref=(
                        "read-only-command-allowlist-decision:gate-m87"
                    ),
                    approval_bundle_ref="scoped-approval-bundle:gate-m87",
                    approval_ref="approval:gate-m87",
                    allowlist_ref="read-only-command-allowlist:gate-m87",
                    sandboxed_command_ref="sandboxed-echo-noop-command:gate-m87",
                    sandboxed_echo_noop_decision_ref=(
                        "sandboxed-echo-noop-command-decision:gate-m87"
                    ),
                    shell_dry_run_decision_ref="shell-dry-run-decision:gate-m87",
                    command_proposal_ref="command-proposal:gate-m87",
                    command_ref="command-ref:gate-m87-noop",
                    sandbox_spec_ref="runtime-sandbox-spec:gate-m87",
                    baseline_ref="baseline:v0.90.0",
                    actor_ref="actor:foundation-gate",
                    reason_codes=[
                        "M86_SHELL_APPROVAL_GATE_REVIEW_ONLY",
                        "M86_EXACT_M85_ALLOWLIST_BINDING_REQUIRED",
                        "M86_APPROVAL_BUNDLE_EXACT_SCOPE_REQUIRED",
                        "M86_NO_SHELL_EXECUTION",
                        "M87_REMAINS_FUTURE",
                    ],
                    safe_summary=(
                        "Foundation Gate M87 fixture represents an M86 shell approval "
                        "gate decision for review only and grants no command, shell, "
                        "subprocess, process, filesystem, network, tool, browser, "
                        "plugin, remote, model, memory, context, route, Control Center, "
                        "dependency, or production authority."
                    ),
                    receipt_plan=ShellApprovalGateReceiptPlan(
                        receipt_plan_ref="shell-approval-gate-receipt-plan:gate-m87",
                        gate_ref="shell-approval-gate:gate-m87",
                        read_only_command_allowlist_decision_ref=(
                            "read-only-command-allowlist-decision:gate-m87"
                        ),
                        approval_bundle_ref="scoped-approval-bundle:gate-m87",
                        approval_ref="approval:gate-m87",
                        allowlist_ref="read-only-command-allowlist:gate-m87",
                        command_ref="command-ref:gate-m87-noop",
                        sandbox_spec_ref="runtime-sandbox-spec:gate-m87",
                    ),
                )
            )
            step = SandboxedCommandAuditReplayStep(
                step_ref="sandboxed-command-audit-replay-step:gate-m87",
                event_ref="audit-event:gate-m87-shell-gate-reviewed",
                source_decision_ref=gate.decision_ref,
                safe_summary=(
                    "Foundation Gate M87 fixture records a replay view step over an "
                    "M86 shell approval gate decision only."
                ),
                reason_codes=["M87_REPLAY_VIEW_STEP_ONLY", "M87_NO_COMMAND_EXECUTION"],
            )
            request = SandboxedCommandAuditReplayRequest(
                request_ref="sandboxed-command-audit-replay-request:gate-m87",
                replay_view_ref="sandboxed-command-audit-replay:gate-m87",
                shell_approval_gate_decision_ref=gate.decision_ref,
                read_only_command_allowlist_decision_ref=(
                    gate.read_only_command_allowlist_decision_ref
                ),
                approval_bundle_ref=gate.approval_bundle_ref,
                approval_ref=gate.approval_ref,
                allowlist_ref=gate.allowlist_ref,
                command_ref=gate.command_ref,
                sandbox_spec_ref=gate.sandbox_spec_ref,
                baseline_ref="baseline:v0.90.0",
                actor_ref=gate.actor_ref,
                audit_ref="audit:gate-m87",
                replay_ref="replay:gate-m87",
                replay_step_refs=[step.step_ref],
                prior_milestone_refs=[
                    "milestone:M57",
                    "milestone:M58",
                    "milestone:M80",
                    "milestone:M81",
                    "milestone:M82",
                    "milestone:M83",
                    "milestone:M84",
                    "milestone:M85",
                    "milestone:M86",
                ],
                shell_approval_gate_decision=gate,
                replay_steps=[step],
                safe_purpose=(
                    "Foundation Gate validates M87 sandboxed command audit replay "
                    "contracts without running or retrying commands."
                ),
            )
            decision = build_sandboxed_command_audit_replay(request)
            if (
                decision.status != SandboxedCommandAuditReplayStatus.ready_for_review
                or not decision.contract_only
                or not decision.review_only
                or not decision.replay_view_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.shell_approval_gate_decision_revalidated
                or not decision.replay_steps_bound
                or decision.replay_runner_started
                or decision.replay_execution_performed
                or decision.command_execution_authorized
                or decision.shell_execution_authorized
                or decision.subprocess_execution_authorized
                or decision.process_spawn_authorized
                or decision.command_execution_performed
                or decision.subprocess_execution_performed
                or decision.shell_execution_performed
                or decision.process_spawn_performed
                or decision.filesystem_mutation_performed
                or decision.network_access_performed
                or decision.tool_execution_performed
                or decision.browser_automation_performed
                or decision.plugin_execution_performed
                or decision.remote_execution_performed
                or decision.model_call_performed
                or decision.memory_write_performed
                or decision.context_injection_performed
                or decision.background_worker_started
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.production_authority_granted
                or decision.side_effects_performed
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or not decision.receipt_plan.store_replay_step_refs_only
                or decision.receipt_plan.store_raw_command
                or decision.receipt_plan.store_shell_string
                or decision.receipt_plan.store_raw_output
                or "M87_SANDBOXED_COMMAND_AUDIT_REPLAY_VIEW_ONLY"
                not in decision.reason_codes
                or "M87_EXACT_M86_SHELL_APPROVAL_GATE_BINDING_REQUIRED"
                not in decision.reason_codes
                or "M87_NO_REPLAY_RUNNER" not in decision.reason_codes
                or "M88_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M87 sandboxed command audit replay decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"command_execution_requested": True}, "COMMAND_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"replay_runner_requested": True}, "M87_REPLAY_RUNNER_DENIED"),
                ({"replay_execution_requested": True}, "M87_REPLAY_EXECUTION_DENIED"),
                ({"contains_shell_string": True}, "M87_SHELL_STRING_DENIED"),
                ({"contains_raw_command": True}, "M87_RAW_COMMAND_DENIED"),
                ({"contains_raw_output": True}, "M87_RAW_OUTPUT_DENIED"),
                (
                    {"contains_secret": True},
                    "SECRET_LIKE_SANDBOXED_COMMAND_AUDIT_REPLAY_CONTENT_DENIED",
                ),
            ]:
                try:
                    build_sandboxed_command_audit_replay(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M87 unsafe audit replay request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M87 unsafe audit replay request raised {exc!s}, expected {reason}"
                        )
            try:
                validate_sandboxed_command_audit_replay_decision(
                    decision.model_copy(update={"replay_runner_started": True})
                )
                failures.append("M87 mutated replay runner flag was not denied")
            except ValueError as exc:
                if "M87_REPLAY_RUNNER_DENIED" not in str(exc):
                    failures.append(
                        f"M87 mutated replay runner flag raised {exc!s}, expected M87_REPLAY_RUNNER_DENIED"
                    )
        except Exception as exc:
            failures.append(
                f"M87 sandboxed command audit replay validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "sandboxed command audit replay",
            "contract-only",
            "review-only",
            "replay-view-only",
            "deterministic",
            "local-only",
            "m86 shell approval gate",
            "exact m86",
            "exact replay step",
            "safe refs only",
            "no replay runner",
            "no replay execution",
            "no shell string",
            "no raw command",
            "no raw output",
            "no command execution",
            "no subprocess execution",
            "no shell execution",
            "no process spawn",
            "no filesystem mutation",
            "no network access",
            "no tool execution",
            "no browser automation",
            "no plugin execution",
            "no remote execution",
            "no model call",
            "no memory write",
            "no context injection",
            "no background worker",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "safe summary only",
            "evaluator boundaries revalidate",
            "m88 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M87 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)
