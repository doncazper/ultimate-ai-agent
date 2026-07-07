from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart022Mixin:
    """Legacy checks from m87_sandboxed_command_audit_replay_static_safety through m90_shell_subprocess_route_boundary."""
    def check_m87_sandboxed_command_audit_replay_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "replay_runner_enabled=True",
            "replay_runner_requested=True",
            "replay_runner_started=True",
            "replay_execution_enabled=True",
            "replay_execution_requested=True",
            "replay_execution_performed=True",
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
            "src/ultimate_ai_agent/core/sandbox/command_audit_replay.py",
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
                            f"M87 forbidden sandboxed command audit replay fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m87_sandboxed_command_audit_replay_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m87_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M87 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m87_roadmap_currentness(
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
            f"missing M87 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.91.0" not in text
            or "m87" not in text
            or "sandboxed command audit replay" not in text
        ):
            failures.append(
                "active docs do not identify v0.91.0/M87 Sandboxed Command Audit Replay"
            )
        if (
            "m87 is implemented/released" not in text
            and "v0.91.0 implements m87" not in text
        ):
            failures.append("active docs do not mark M87 implemented/released")
        for version_label, milestone, title in [
            ("v0.92.0", "M88", "Mutating Command Proposal, No Execution"),
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
                    f"active docs missing planned M88-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "replay runner is implemented",
            "replay execution is implemented",
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
                    f"M87 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m88_mutating_command_proposal_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/mutating_command_proposal.py",
            "src/ultimate_ai_agent/core/sandbox/command_audit_replay.py",
            "docs/sandbox/MUTATING_COMMAND_PROPOSAL.md",
            "docs/sandbox/MUTATING_COMMAND_PROPOSAL_POLICY.md",
            "docs/sandbox/MUTATING_COMMAND_PROPOSAL_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/MUTATING_COMMAND_PROPOSAL_RECEIPT_PLAN.md",
            "docs/sandbox/MUTATING_COMMAND_PROPOSAL_NON_GOALS.md",
            "docs/sandbox/M88_TO_M89_BOUNDARY.md",
            "tests/test_m88_mutating_command_proposal.py",
            "tests/test_m88_gate_integration.py",
        ]
        failures = [
            f"missing M88 mutating command proposal file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.sandbox import (
                MutatingCommandProposalRequest,
                MutatingCommandProposalStatus,
                SandboxedCommandAuditReplayRequest,
                SandboxedCommandAuditReplayStep,
                ShellApprovalGateDecision,
                ShellApprovalGateReceiptPlan,
                build_mutating_command_proposal,
                build_sandboxed_command_audit_replay,
                validate_mutating_command_proposal_decision,
                validate_shell_approval_gate_decision,
            )

            gate = validate_shell_approval_gate_decision(
                ShellApprovalGateDecision(
                    decision_ref="shell-approval-gate-decision:gate-m88",
                    gate_ref="shell-approval-gate:gate-m88",
                    request_ref="shell-approval-gate-request:gate-m88",
                    read_only_command_allowlist_decision_ref=(
                        "read-only-command-allowlist-decision:gate-m88"
                    ),
                    approval_bundle_ref="scoped-approval-bundle:gate-m88",
                    approval_ref="approval:gate-m88",
                    allowlist_ref="read-only-command-allowlist:gate-m88",
                    sandboxed_command_ref="sandboxed-echo-noop-command:gate-m88",
                    sandboxed_echo_noop_decision_ref=(
                        "sandboxed-echo-noop-command-decision:gate-m88"
                    ),
                    shell_dry_run_decision_ref="shell-dry-run-decision:gate-m88",
                    command_proposal_ref="command-proposal:gate-m88",
                    command_ref="command-ref:gate-m88-noop",
                    sandbox_spec_ref="runtime-sandbox-spec:gate-m88",
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
                        "Foundation Gate M88 fixture represents an M86 shell approval "
                        "gate decision for review only and grants no execution or mutation."
                    ),
                    receipt_plan=ShellApprovalGateReceiptPlan(
                        receipt_plan_ref="shell-approval-gate-receipt-plan:gate-m88",
                        gate_ref="shell-approval-gate:gate-m88",
                        read_only_command_allowlist_decision_ref=(
                            "read-only-command-allowlist-decision:gate-m88"
                        ),
                        approval_bundle_ref="scoped-approval-bundle:gate-m88",
                        approval_ref="approval:gate-m88",
                        allowlist_ref="read-only-command-allowlist:gate-m88",
                        command_ref="command-ref:gate-m88-noop",
                        sandbox_spec_ref="runtime-sandbox-spec:gate-m88",
                    ),
                )
            )
            step = SandboxedCommandAuditReplayStep(
                step_ref="sandboxed-command-audit-replay-step:gate-m88",
                event_ref="audit-event:gate-m88-shell-gate-reviewed",
                source_decision_ref=gate.decision_ref,
                safe_summary="Foundation Gate M88 fixture records a safe replay view step only.",
                reason_codes=["M87_REPLAY_VIEW_STEP_ONLY", "M87_NO_COMMAND_EXECUTION"],
            )
            replay = build_sandboxed_command_audit_replay(
                SandboxedCommandAuditReplayRequest(
                    request_ref="sandboxed-command-audit-replay-request:gate-m88",
                    replay_view_ref="sandboxed-command-audit-replay:gate-m88",
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
                    audit_ref="audit:gate-m88",
                    replay_ref="replay:gate-m88",
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
                    safe_purpose="Foundation Gate validates M87 replay contracts for M88.",
                )
            )
            request = MutatingCommandProposalRequest(
                request_ref="mutating-command-proposal-request:gate-m88",
                mutating_proposal_ref="mutating-command-proposal:gate-m88",
                sandboxed_command_audit_replay_decision_ref=replay.decision_ref,
                shell_approval_gate_decision_ref=replay.shell_approval_gate_decision_ref,
                approval_bundle_ref=replay.approval_bundle_ref,
                approval_ref=replay.approval_ref,
                command_ref=replay.command_ref,
                sandbox_spec_ref=replay.sandbox_spec_ref,
                baseline_ref="baseline:v0.91.0",
                actor_ref=replay.actor_ref,
                audit_ref=replay.audit_ref,
                replay_ref=replay.replay_ref,
                mutation_intent_ref="mutation-intent:gate-m88-review-only",
                mutation_scope_ref="mutation-scope:gate-m88-safe-summary",
                safe_mutation_summary="Foundation Gate reviews a mutating command proposal as safe metadata only.",
                safe_argument_refs=["argument-ref:gate-m88-review-only"],
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
                    "milestone:M87",
                ],
                sandboxed_command_audit_replay_decision=replay,
            )
            decision = build_mutating_command_proposal(request)
            if (
                decision.status != MutatingCommandProposalStatus.proposed_for_review
                or not decision.contract_only
                or not decision.proposal_only
                or not decision.review_only
                or not decision.mutating_command_review_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.audit_replay_decision_revalidated
                or not decision.mutation_scope_bound
                or decision.command_execution_authorized
                or decision.filesystem_mutation_authorized
                or decision.command_execution_performed
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
                or not decision.receipt_plan.store_mutation_scope_ref_only
                or decision.receipt_plan.store_raw_command
                or decision.receipt_plan.store_raw_output
                or "M88_MUTATING_COMMAND_PROPOSAL_REVIEW_ONLY"
                not in decision.reason_codes
                or "M88_EXACT_M87_AUDIT_REPLAY_BINDING_REQUIRED"
                not in decision.reason_codes
                or "M88_NO_COMMAND_EXECUTION" not in decision.reason_codes
                or "M89_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M88 mutating command proposal decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"command_execution_requested": True}, "COMMAND_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"filesystem_mutation_requested": True}, "FILESYSTEM_MUTATION_DENIED"),
                ({"contains_shell_string": True}, "M88_SHELL_STRING_DENIED"),
                ({"contains_raw_command": True}, "M88_RAW_COMMAND_DENIED"),
                ({"contains_raw_output": True}, "M88_RAW_OUTPUT_DENIED"),
                (
                    {"contains_secret": True},
                    "SECRET_LIKE_MUTATING_COMMAND_PROPOSAL_CONTENT_DENIED",
                ),
            ]:
                try:
                    build_mutating_command_proposal(request.model_copy(update=update))
                    failures.append(
                        f"M88 unsafe mutating proposal request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M88 unsafe mutating proposal request raised {exc!s}, expected {reason}"
                        )
            try:
                validate_mutating_command_proposal_decision(
                    decision.model_copy(update={"filesystem_mutation_authorized": True})
                )
                failures.append(
                    "M88 mutated filesystem mutation authority flag was not denied"
                )
            except ValueError as exc:
                if "FILESYSTEM_MUTATION_DENIED" not in str(exc):
                    failures.append(
                        f"M88 mutated filesystem mutation authority flag raised {exc!s}"
                    )
        except Exception as exc:
            failures.append(f"M88 mutating command proposal validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mutating command proposal",
            "contract-only",
            "proposal-only",
            "review-only",
            "deterministic",
            "local-only",
            "m87 sandboxed command audit replay",
            "exact m87",
            "safe mutation scope",
            "safe refs only",
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
            "m89 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M88 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m88_mutating_command_proposal_static_safety(
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
            "filesystem_mutation_requested=True",
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
            "filesystem_mutation_authorized=True",
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
            "src/ultimate_ai_agent/core/sandbox/command_audit_replay.py",
            "src/ultimate_ai_agent/core/sandbox/mutating_command_proposal.py",
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
                            f"M88 forbidden mutating command proposal fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m88_mutating_command_proposal_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m88_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M88 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m88_roadmap_currentness(
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
            f"missing M88 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.92.0" not in text
            or "m88" not in text
            or "mutating command proposal" not in text
        ):
            failures.append(
                "active docs do not identify v0.92.0/M88 Mutating Command Proposal"
            )
        if (
            "m88 is implemented/released" not in text
            and "v0.92.0 implements m88" not in text
        ):
            failures.append("active docs do not mark M88 implemented/released")
        for version_label, milestone, title in [
            ("v0.93.0", "M89", "Emergency Stop + Process Kill Safety"),
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
                    f"active docs missing planned M89-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "command execution is implemented",
            "filesystem mutation is implemented",
            "subprocess execution is implemented",
            "shell execution is implemented",
            "process spawn is implemented",
            "network access is implemented",
            "browser click is implemented",
            "plugin execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M88 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m89_emergency_stop_process_kill_safety_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/emergency_stop_process_kill_safety.py",
            "src/ultimate_ai_agent/core/sandbox/mutating_command_proposal.py",
            "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY.md",
            "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_POLICY.md",
            "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_RECEIPT_PLAN.md",
            "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_NON_GOALS.md",
            "docs/sandbox/M89_TO_M90_BOUNDARY.md",
            "tests/test_m89_emergency_stop_process_kill_safety.py",
            "tests/test_m89_gate_integration.py",
        ]
        failures = [
            f"missing M89 emergency stop/process kill safety file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m89_emergency_stop_process_kill_safety import _request
            from ultimate_ai_agent.core.sandbox import (
                EmergencyStopProcessKillSafetyStatus,
                build_emergency_stop_process_kill_safety,
                validate_emergency_stop_process_kill_safety_decision,
            )

            decision = build_emergency_stop_process_kill_safety(_request())
            if (
                decision.status
                != EmergencyStopProcessKillSafetyStatus.reviewed_for_safety
                or not decision.contract_only
                or not decision.review_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.mutating_command_proposal_decision_revalidated
                or not decision.process_target_ref_bound
                or not decision.emergency_scope_ref_bound
                or decision.emergency_stop_authorized
                or decision.emergency_stop_performed
                or decision.process_kill_authorized
                or decision.process_kill_performed
                or decision.process_signal_authorized
                or decision.process_signal_performed
                or decision.command_execution_authorized
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
                or not decision.receipt_plan.store_process_target_ref_only
                or decision.receipt_plan.store_raw_pid
                or decision.receipt_plan.store_raw_signal
                or "M89_EMERGENCY_STOP_PROCESS_KILL_SAFETY_REVIEW_ONLY"
                not in decision.reason_codes
                or "M89_EXACT_M88_MUTATING_PROPOSAL_BINDING_REQUIRED"
                not in decision.reason_codes
                or "M89_NO_PROCESS_KILL_EXECUTION" not in decision.reason_codes
                or "M90_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M89 emergency stop/process kill safety decision is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"emergency_stop_requested": True},
                    "M89_EMERGENCY_STOP_EXECUTION_DENIED",
                ),
                ({"process_kill_requested": True}, "M89_PROCESS_KILL_DENIED"),
                ({"process_signal_requested": True}, "M89_PROCESS_SIGNAL_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"contains_pid": True}, "M89_RAW_PID_DENIED"),
                ({"contains_raw_signal": True}, "M89_RAW_SIGNAL_DENIED"),
            ]:
                try:
                    build_emergency_stop_process_kill_safety(_request(**update))
                    failures.append(
                        f"M89 unsafe safety request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M89 unsafe safety request raised {exc!s}, expected {reason}"
                        )
            try:
                validate_emergency_stop_process_kill_safety_decision(
                    decision.model_copy(update={"process_kill_authorized": True})
                )
                failures.append(
                    "M89 mutated process kill authority flag was not denied"
                )
            except ValueError as exc:
                if "M89_PROCESS_KILL_DENIED" not in str(exc):
                    failures.append(
                        f"M89 mutated process kill authority flag raised {exc!s}"
                    )
        except Exception as exc:
            failures.append(
                f"M89 emergency stop/process kill safety validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "emergency stop + process kill safety",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "m88 mutating command proposal",
            "exact m88",
            "safe target process ref",
            "safe emergency scope ref",
            "safe refs only",
            "no emergency stop execution",
            "no process kill",
            "no process signal",
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
            "no raw pid",
            "no raw signal",
            "safe summary only",
            "evaluator boundaries revalidate",
            "m90 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M89 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m89_emergency_stop_process_kill_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "emergency_stop_execution_enabled=True",
            "process_kill_enabled=True",
            "process_signal_enabled=True",
            "emergency_stop_requested=True",
            "process_kill_requested=True",
            "process_signal_requested=True",
            "emergency_stop_authorized=True",
            "process_kill_authorized=True",
            "process_signal_authorized=True",
            "emergency_stop_performed=True",
            "process_kill_performed=True",
            "process_signal_performed=True",
            "command_execution_enabled=True",
            "command_execution_requested=True",
            "subprocess_execution_enabled=True",
            "subprocess_execution_requested=True",
            "shell_execution_enabled=True",
            "shell_execution_requested=True",
            "process_spawn_enabled=True",
            "process_spawn_requested=True",
            "filesystem_mutation_enabled=True",
            "filesystem_mutation_requested=True",
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
            "filesystem_mutation_authorized=True",
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
            "store_raw_pid=True",
            "store_raw_signal=True",
            "store_raw_command=True",
            "store_shell_string=True",
            "store_raw_output=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/command_proposal.py",
            "src/ultimate_ai_agent/core/sandbox/runtime_spec.py",
            "src/ultimate_ai_agent/core/sandbox/shell_dry_run_classifier.py",
            "src/ultimate_ai_agent/core/sandbox/sandboxed_echo_noop_command.py",
            "src/ultimate_ai_agent/core/sandbox/read_only_command_allowlist.py",
            "src/ultimate_ai_agent/core/sandbox/shell_approval_gate.py",
            "src/ultimate_ai_agent/core/sandbox/command_audit_replay.py",
            "src/ultimate_ai_agent/core/sandbox/mutating_command_proposal.py",
            "src/ultimate_ai_agent/core/sandbox/emergency_stop_process_kill_safety.py",
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
                            f"M89 forbidden emergency stop/process kill fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m89_emergency_stop_process_kill_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m89_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M89 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m89_roadmap_currentness(
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
            f"missing M89 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.93.0" not in text
            or "m89" not in text
            or "emergency stop + process kill safety" not in text
        ):
            failures.append(
                "active docs do not identify v0.93.0/M89 Emergency Stop + Process Kill Safety"
            )
        if (
            "m89 is implemented/released" not in text
            and "v0.93.0 implements m89" not in text
        ):
            failures.append("active docs do not mark M89 implemented/released")
        for version_label, milestone, title in [
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
                    f"active docs missing planned M90-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "process kill is implemented",
            "process signal is implemented",
            "emergency stop execution is implemented",
            "command execution is implemented",
            "filesystem mutation is implemented",
            "subprocess execution is implemented",
            "shell execution is implemented",
            "process spawn is implemented",
            "network access is implemented",
            "browser click is implemented",
            "plugin execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M89 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m90_shell_subprocess_hardening_freeze_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/shell_subprocess_hardening_freeze.py",
            "src/ultimate_ai_agent/core/sandbox/emergency_stop_process_kill_safety.py",
            "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE.md",
            "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_POLICY.md",
            "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_RECEIPT_PLAN.md",
            "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_NON_GOALS.md",
            "docs/sandbox/M90_TO_M91_BOUNDARY.md",
            "tests/test_m90_shell_subprocess_hardening_freeze.py",
            "tests/test_m90_gate_integration.py",
        ]
        failures = [
            f"missing M90 shell/subprocess hardening freeze file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m90_shell_subprocess_hardening_freeze import _request
            from ultimate_ai_agent.core.sandbox import (
                ShellSubprocessHardeningFreezeStatus,
                build_shell_subprocess_hardening_freeze,
                validate_shell_subprocess_hardening_freeze_decision,
            )

            decision = build_shell_subprocess_hardening_freeze(_request())
            if (
                decision.status
                != ShellSubprocessHardeningFreezeStatus.frozen_for_review
                or not decision.contract_only
                or not decision.review_only
                or not decision.freeze_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.m89_safety_decision_revalidated
                or not decision.shell_boundary_frozen
                or not decision.subprocess_boundary_frozen
                or not decision.process_spawn_boundary_frozen
                or not decision.emergency_stop_boundary_frozen
                or decision.command_execution_authorized
                or decision.shell_execution_authorized
                or decision.subprocess_execution_authorized
                or decision.process_spawn_authorized
                or decision.emergency_stop_authorized
                or decision.process_kill_authorized
                or decision.process_signal_authorized
                or decision.command_execution_performed
                or decision.shell_execution_performed
                or decision.subprocess_execution_performed
                or decision.process_spawn_performed
                or decision.emergency_stop_performed
                or decision.process_kill_performed
                or decision.process_signal_performed
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
                or decision.receipt_plan.store_raw_pid
                or "M90_SHELL_SUBPROCESS_HARDENING_FREEZE_REVIEW_ONLY"
                not in decision.reason_codes
                or "M90_EXACT_M89_SAFETY_BINDING_REQUIRED" not in decision.reason_codes
                or "M90_NO_SHELL_SUBPROCESS_EXECUTION" not in decision.reason_codes
                or "M90_NO_PROCESS_OR_EMERGENCY_EXECUTION" not in decision.reason_codes
                or "M91_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M90 shell/subprocess hardening freeze decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"command_execution_requested": True}, "COMMAND_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                (
                    {"emergency_stop_requested": True},
                    "M90_EMERGENCY_STOP_EXECUTION_DENIED",
                ),
                ({"process_kill_requested": True}, "M90_PROCESS_KILL_DENIED"),
                ({"process_signal_requested": True}, "M90_PROCESS_SIGNAL_DENIED"),
                ({"contains_shell_string": True}, "M90_SHELL_STRING_DENIED"),
                ({"contains_raw_command": True}, "M90_RAW_COMMAND_DENIED"),
                ({"contains_pid": True}, "M90_RAW_PID_DENIED"),
            ]:
                try:
                    build_shell_subprocess_hardening_freeze(_request(**update))
                    failures.append(
                        f"M90 unsafe freeze request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M90 unsafe freeze request raised {exc!s}, expected {reason}"
                        )
            try:
                validate_shell_subprocess_hardening_freeze_decision(
                    decision.model_copy(update={"shell_execution_authorized": True})
                )
                failures.append(
                    "M90 mutated shell execution authority flag was not denied"
                )
            except ValueError as exc:
                if "SHELL_EXECUTION_DENIED" not in str(exc):
                    failures.append(
                        f"M90 mutated shell execution authority flag raised {exc!s}"
                    )
        except Exception as exc:
            failures.append(
                f"M90 shell/subprocess hardening freeze validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "shell/subprocess hardening freeze",
            "contract-only",
            "review-only",
            "freeze-only",
            "deterministic",
            "local-only",
            "m89 emergency stop + process kill safety",
            "exact m89",
            "safe refs only",
            "no command execution",
            "no shell execution",
            "no subprocess execution",
            "no process spawn",
            "no emergency stop execution",
            "no process kill",
            "no process signal",
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
            "no shell string",
            "no raw command",
            "no raw pid",
            "safe summary only",
            "evaluator boundaries revalidate",
            "m91 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M90 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m90_shell_subprocess_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "command_execution_enabled=True",
            "command_execution_requested=True",
            "command_execution_authorized=True",
            "command_execution_performed=True",
            "shell_execution_enabled=True",
            "shell_execution_requested=True",
            "shell_execution_authorized=True",
            "shell_execution_performed=True",
            "subprocess_execution_enabled=True",
            "subprocess_execution_requested=True",
            "subprocess_execution_authorized=True",
            "subprocess_execution_performed=True",
            "process_spawn_enabled=True",
            "process_spawn_requested=True",
            "process_spawn_authorized=True",
            "process_spawn_performed=True",
            "emergency_stop_execution_enabled=True",
            "emergency_stop_requested=True",
            "emergency_stop_authorized=True",
            "emergency_stop_performed=True",
            "process_kill_enabled=True",
            "process_kill_requested=True",
            "process_kill_authorized=True",
            "process_kill_performed=True",
            "process_signal_enabled=True",
            "process_signal_requested=True",
            "process_signal_authorized=True",
            "process_signal_performed=True",
            "filesystem_mutation_enabled=True",
            "filesystem_mutation_requested=True",
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
            "background_worker_started=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "store_raw_pid=True",
            "store_raw_signal=True",
            "store_raw_command=True",
            "store_shell_string=True",
            "store_raw_output=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/command_proposal.py",
            "src/ultimate_ai_agent/core/sandbox/runtime_spec.py",
            "src/ultimate_ai_agent/core/sandbox/shell_dry_run_classifier.py",
            "src/ultimate_ai_agent/core/sandbox/sandboxed_echo_noop_command.py",
            "src/ultimate_ai_agent/core/sandbox/read_only_command_allowlist.py",
            "src/ultimate_ai_agent/core/sandbox/shell_approval_gate.py",
            "src/ultimate_ai_agent/core/sandbox/command_audit_replay.py",
            "src/ultimate_ai_agent/core/sandbox/mutating_command_proposal.py",
            "src/ultimate_ai_agent/core/sandbox/emergency_stop_process_kill_safety.py",
            "src/ultimate_ai_agent/core/sandbox/shell_subprocess_hardening_freeze.py",
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
                            f"M90 forbidden shell/subprocess hardening fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m90_shell_subprocess_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m90_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M90 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
