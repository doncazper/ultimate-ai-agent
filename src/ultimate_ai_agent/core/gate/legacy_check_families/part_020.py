from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart020Mixin:
    """Legacy checks from m81_runtime_sandbox_spec_contract through m84_sandboxed_echo_noop_route_boundary."""
    def check_m81_runtime_sandbox_spec_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/runtime_spec.py",
            "docs/sandbox/RUNTIME_SANDBOX_SPEC.md",
            "docs/sandbox/RUNTIME_SANDBOX_SPEC_CONTRACTS.md",
            "docs/sandbox/RUNTIME_SANDBOX_SPEC_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/RUNTIME_SANDBOX_SPEC_NON_GOALS.md",
            "docs/sandbox/M81_TO_M82_BOUNDARY.md",
            "docs/release_notes/v0_85_0.md",
            "docs/archive/releases/v0_85_0/README_IMPORT.md",
            "docs/archive/releases/v0_85_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_85_0.md",
            "tests/test_m81_runtime_sandbox_spec.py",
            "tests/test_m81_gate_integration.py",
        ]
        failures = [
            f"missing M81 runtime sandbox spec file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.sandbox import (
                RuntimeSandboxSpecRequest,
                RuntimeSandboxSpecStatus,
                build_runtime_sandbox_spec,
            )

            request = RuntimeSandboxSpecRequest(
                request_ref="runtime-sandbox-spec-request:m81-gate",
                spec_ref="runtime-sandbox-spec:m81-gate",
                baseline_ref="baseline:v0.84.1",
                actor_ref="actor:m81-gate",
                prior_milestone_refs=[
                    "milestone:M57",
                    "milestone:M58",
                    "milestone:M80",
                ],
                boundary_refs=[
                    "sandbox-boundary:m57-architecture-review",
                    "sandbox-boundary:m58-dry-run-audit",
                    "sandbox-boundary:m80-freeze",
                ],
                threat_model_refs=[
                    "threat-model:no-process-spawn",
                    "threat-model:no-network-runtime",
                ],
                audit_requirement_refs=[
                    "audit-requirement:deterministic-spec",
                    "audit-requirement:no-side-effects",
                ],
                safe_summary="Runtime sandbox spec only, no runtime authority.",
            )
            report = build_runtime_sandbox_spec(request)
            if (
                report.status != RuntimeSandboxSpecStatus.specified
                or not report.spec_only
                or not report.review_only
                or not report.deterministic
                or not report.local_only
                or report.runtime_sandbox_started
                or report.command_proposal_created
                or report.command_execution_performed
                or report.subprocess_execution_performed
                or report.shell_execution_performed
                or report.process_spawn_performed
                or report.filesystem_mutation_performed
                or report.network_access_performed
                or report.tool_execution_performed
                or report.browser_automation_performed
                or report.plugin_execution_performed
                or report.remote_execution_performed
                or report.model_call_performed
                or report.memory_write_performed
                or report.context_injection_performed
                or report.background_worker_started
                or report.backend_route_added
                or report.control_center_control_added
                or report.dependency_added
                or report.production_authority_granted
                or report.side_effects_performed
                or "M81_RUNTIME_SANDBOX_SPEC_ONLY" not in report.reason_codes
                or "M81_NO_RUNTIME_SANDBOX_EXECUTION" not in report.reason_codes
                or "M82_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M81 runtime sandbox spec report is unsafe or over-authoritative"
                )

            for update, reason in [
                (
                    {"runtime_sandbox_requested": True},
                    "RUNTIME_SANDBOX_EXECUTION_DENIED",
                ),
                ({"command_proposal_requested": True}, "COMMAND_PROPOSAL_DENIED"),
                ({"command_execution_requested": True}, "COMMAND_EXECUTION_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"filesystem_mutation_requested": True}, "FILESYSTEM_MUTATION_DENIED"),
                ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"browser_automation_requested": True}, "BROWSER_AUTOMATION_DENIED"),
                ({"plugin_execution_requested": True}, "PLUGIN_EXECUTION_DENIED"),
                ({"remote_execution_requested": True}, "REMOTE_EXECUTION_DENIED"),
                ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
                ({"background_worker_requested": True}, "BACKGROUND_WORKER_DENIED"),
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
                ({"contains_raw_prompt": True}, "RAW_PROMPT_CAPTURE_DENIED"),
                (
                    {"contains_raw_provider_payload": True},
                    "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED",
                ),
                ({"contains_secret": True}, "SECRET_LIKE_SANDBOX_SPEC_CONTENT_DENIED"),
            ]:
                try:
                    build_runtime_sandbox_spec(request.model_copy(update=update))
                    failures.append(
                        f"M81 unsafe runtime sandbox spec request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M81 unsafe runtime sandbox spec request raised {exc!s}, expected {reason}"
                        )
        except Exception as exc:
            failures.append(f"M81 runtime sandbox spec validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "runtime sandbox spec",
            "spec-only",
            "review-only",
            "deterministic",
            "local-only",
            "prior milestone refs",
            "boundary refs",
            "threat model refs",
            "audit requirement refs",
            "no runtime sandbox execution",
            "no command proposal",
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
            "evaluator boundaries revalidate",
            "m82 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M81 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m81_runtime_sandbox_spec_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "runtime_sandbox_enabled=True",
            "command_proposal_enabled=True",
            "command_execution_enabled=True",
            "subprocess_execution_enabled=True",
            "shell_execution_enabled=True",
            "process_spawn_enabled=True",
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
            "runtime_sandbox_started=True",
            "command_proposal_created=True",
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
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/runtime_spec.py",
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
                            f"M81 forbidden runtime sandbox spec fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m81_runtime_sandbox_spec_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m81_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M81 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m81_roadmap_currentness(
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
            f"missing M81 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.85.0" not in text
            or "m81" not in text
            or "runtime sandbox spec" not in text
        ):
            failures.append(
                "active docs do not identify v0.85.0/M81 Runtime Sandbox Spec"
            )
        if (
            "m81 is implemented/released" not in text
            and "v0.85.0 implements m81" not in text
        ):
            failures.append("active docs do not mark M81 implemented/released")
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
                    f"active docs missing planned M82-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "runtime sandbox execution is implemented",
            "command execution is implemented",
            "subprocess execution is implemented",
            "shell execution is implemented",
            "process spawn is implemented",
            "browser click is implemented",
            "plugin execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M81 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m82_command_proposal_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/command_proposal.py",
            "docs/sandbox/COMMAND_PROPOSAL_CONTRACTS.md",
            "docs/sandbox/COMMAND_PROPOSAL_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/COMMAND_PROPOSAL_RECEIPT_PLAN.md",
            "docs/sandbox/COMMAND_PROPOSAL_NON_GOALS.md",
            "docs/sandbox/M82_TO_M83_BOUNDARY.md",
            "docs/release_notes/v0_86_0.md",
            "docs/archive/releases/v0_86_0/README_IMPORT.md",
            "docs/archive/releases/v0_86_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_86_0.md",
            "tests/test_m82_command_proposal_contracts.py",
            "tests/test_m82_gate_integration.py",
        ]
        failures = [
            f"missing M82 command proposal file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.sandbox import (
                CommandProposalRequest,
                CommandProposalStatus,
                build_command_proposal,
            )

            request = CommandProposalRequest(
                request_ref="command-proposal-request:gate-m82",
                proposal_ref="command-proposal:gate-m82",
                sandbox_spec_ref="runtime-sandbox-spec:m81",
                baseline_ref="baseline:v0.85.0",
                actor_ref="actor:gate-m82",
                prior_milestone_refs=[
                    "milestone:M57",
                    "milestone:M58",
                    "milestone:M80",
                    "milestone:M81",
                ],
                command_ref="command-ref:gate-noop",
                safe_purpose="Gate verifies a no-effect command proposal contract.",
                safe_command_label="gate noop metadata",
                argv_preview=["gate-noop", "--dry-summary"],
            )
            decision = build_command_proposal(request)
            if (
                decision.status != CommandProposalStatus.proposed_for_review
                or not decision.proposal_only
                or not decision.review_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.structured_args_only
                or decision.execution_authorized
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
                or decision.receipt_plan.store_raw_command
                or decision.receipt_plan.store_shell_string
                or "M82_COMMAND_PROPOSAL_CONTRACT_ONLY" not in decision.reason_codes
                or "M82_NO_COMMAND_EXECUTION" not in decision.reason_codes
                or "M83_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M82 command proposal decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"execution_requested": True}, "EXECUTION_REQUEST_DENIED"),
                ({"command_execution_requested": True}, "COMMAND_EXECUTION_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"filesystem_mutation_requested": True}, "FILESYSTEM_MUTATION_DENIED"),
                ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"browser_automation_requested": True}, "BROWSER_AUTOMATION_DENIED"),
                ({"plugin_execution_requested": True}, "PLUGIN_EXECUTION_DENIED"),
                ({"remote_execution_requested": True}, "REMOTE_EXECUTION_DENIED"),
                ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
                ({"contains_shell_string": True}, "M82_SHELL_STRING_DENIED"),
                (
                    {"contains_secret": True},
                    "SECRET_LIKE_COMMAND_PROPOSAL_CONTENT_DENIED",
                ),
            ]:
                try:
                    build_command_proposal(request.model_copy(update=update))
                    failures.append(
                        f"M82 unsafe command proposal request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M82 unsafe command proposal request raised {exc!s}, expected {reason}"
                        )
        except Exception as exc:
            failures.append(f"M82 command proposal validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "command proposal contracts",
            "proposal-only",
            "review-only",
            "deterministic",
            "local-only",
            "structured argv preview",
            "no shell string",
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
            "m83 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M82 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m82_command_proposal_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "command_execution_enabled=True",
            "subprocess_execution_enabled=True",
            "shell_execution_enabled=True",
            "process_spawn_enabled=True",
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
            "execution_authorized=True",
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
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/command_proposal.py",
            "src/ultimate_ai_agent/core/sandbox/runtime_spec.py",
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
                            f"M82 forbidden command proposal fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m82_command_proposal_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m82_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M82 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m82_roadmap_currentness(
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
            f"missing M82 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.86.0" not in text
            or "m82" not in text
            or "command proposal contracts" not in text
        ):
            failures.append(
                "active docs do not identify v0.86.0/M82 Command Proposal Contracts"
            )
        if (
            "m82 is implemented/released" not in text
            and "v0.86.0 implements m82" not in text
        ):
            failures.append("active docs do not mark M82 implemented/released")
        for version_label, milestone, title in [
            ("v0.87.0", "M83", "Shell Dry-Run Classifier"),
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
                    f"active docs missing planned M83-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "command execution is implemented",
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
                    f"M82 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m83_shell_dry_run_classifier_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/shell_dry_run_classifier.py",
            "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER.md",
            "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_POLICY.md",
            "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_RECEIPT_PLAN.md",
            "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_NON_GOALS.md",
            "docs/sandbox/M83_TO_M84_BOUNDARY.md",
            "docs/release_notes/v0_87_0.md",
            "docs/archive/releases/v0_87_0/README_IMPORT.md",
            "docs/archive/releases/v0_87_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_87_0.md",
            "tests/test_m83_shell_dry_run_classifier.py",
            "tests/test_m83_gate_integration.py",
        ]
        failures = [
            f"missing M83 shell dry-run classifier file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.sandbox import (
                CommandProposalRequest,
                ShellDryRunClassificationStatus,
                build_command_proposal,
                build_shell_dry_run_classification,
            )

            proposal = build_command_proposal(
                CommandProposalRequest(
                    request_ref="command-proposal-request:gate-m83",
                    proposal_ref="command-proposal:gate-m83",
                    sandbox_spec_ref="runtime-sandbox-spec:m81",
                    baseline_ref="baseline:v0.86.0",
                    actor_ref="actor:gate-m83",
                    prior_milestone_refs=[
                        "milestone:M57",
                        "milestone:M58",
                        "milestone:M80",
                        "milestone:M81",
                    ],
                    command_ref="command-ref:gate-noop",
                    safe_purpose="Gate verifies a no-effect command proposal for classification.",
                    safe_command_label="gate noop metadata",
                    argv_preview=["gate-noop", "--dry-summary"],
                )
            )
            from ultimate_ai_agent.core.sandbox import ShellDryRunClassifierRequest

            request = ShellDryRunClassifierRequest(
                request_ref="shell-dry-run-classifier-request:gate-m83",
                classifier_ref="shell-dry-run-classifier:gate-m83",
                command_proposal_ref=proposal.proposal_ref,
                sandbox_spec_ref=proposal.sandbox_spec_ref,
                baseline_ref="baseline:v0.86.0",
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
            decision = build_shell_dry_run_classification(request)
            if (
                decision.status != ShellDryRunClassificationStatus.classified_for_review
                or not decision.classifier_only
                or not decision.review_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.dry_run_classification_allowed
                or decision.dry_run_execution_authorized
                or decision.command_execution_authorized
                or decision.shell_execution_authorized
                or decision.subprocess_execution_performed
                or decision.shell_execution_performed
                or decision.process_spawn_performed
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
                or decision.receipt_plan.store_raw_command
                or decision.receipt_plan.store_shell_string
                or decision.receipt_plan.dry_run_execution_performed
                or "M83_SHELL_DRY_RUN_CLASSIFIER_CONTRACT_ONLY"
                not in decision.reason_codes
                or "M83_NO_SHELL_EXECUTION" not in decision.reason_codes
                or "M84_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M83 shell dry-run classifier decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"dry_run_execution_requested": True}, "DRY_RUN_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"command_execution_requested": True}, "COMMAND_EXECUTION_DENIED"),
                ({"contains_shell_string": True}, "M83_SHELL_STRING_DENIED"),
                (
                    {"contains_secret": True},
                    "SECRET_LIKE_SHELL_DRY_RUN_CLASSIFIER_CONTENT_DENIED",
                ),
            ]:
                try:
                    build_shell_dry_run_classification(
                        request.model_copy(update=update)
                    )
                    failures.append(
                        f"M83 unsafe classifier request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M83 unsafe classifier request raised {exc!s}, expected {reason}"
                        )
        except Exception as exc:
            failures.append(f"M83 shell dry-run classifier validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "shell dry-run classifier",
            "classifier-only",
            "review-only",
            "deterministic",
            "local-only",
            "m82 command proposal",
            "no dry-run execution",
            "no shell string",
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
            "m84 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M83 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m83_shell_dry_run_classifier_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "dry_run_execution_enabled=True",
            "dry_run_execution_requested=True",
            "shell_execution_enabled=True",
            "shell_execution_requested=True",
            "subprocess_execution_enabled=True",
            "subprocess_execution_requested=True",
            "process_spawn_enabled=True",
            "process_spawn_requested=True",
            "command_execution_enabled=True",
            "command_execution_requested=True",
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
            "dry_run_execution_authorized=True",
            "command_execution_authorized=True",
            "shell_execution_authorized=True",
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
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/command_proposal.py",
            "src/ultimate_ai_agent/core/sandbox/runtime_spec.py",
            "src/ultimate_ai_agent/core/sandbox/shell_dry_run_classifier.py",
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
                            f"M83 forbidden shell dry-run fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m83_shell_dry_run_classifier_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m83_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M83 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m83_roadmap_currentness(
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
            f"missing M83 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.87.0" not in text
            or "m83" not in text
            or "shell dry-run classifier" not in text
        ):
            failures.append(
                "active docs do not identify v0.87.0/M83 Shell Dry-Run Classifier"
            )
        if (
            "m83 is implemented/released" not in text
            and "v0.87.0 implements m83" not in text
        ):
            failures.append("active docs do not mark M83 implemented/released")
        for version_label, milestone, title in [
            ("v0.88.0", "M84", "Sandboxed Echo/No-Op Command"),
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
                    f"active docs missing planned M84-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "dry-run execution is implemented",
            "command execution is implemented",
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
                    f"M83 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m84_sandboxed_echo_noop_command_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/sandboxed_echo_noop_command.py",
            "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND.md",
            "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_POLICY.md",
            "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_RECEIPT_PLAN.md",
            "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_NON_GOALS.md",
            "docs/sandbox/M84_TO_M85_BOUNDARY.md",
            "docs/release_notes/v0_88_0.md",
            "docs/archive/releases/v0_88_0/README_IMPORT.md",
            "docs/archive/releases/v0_88_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_88_0.md",
            "tests/test_m84_sandboxed_echo_noop_command.py",
            "tests/test_m84_gate_integration.py",
        ]
        failures = [
            f"missing M84 sandboxed echo/no-op command file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.sandbox import (
                CommandProposalRequest,
                SandboxedEchoNoOpCommandRequest,
                SandboxedEchoNoOpCommandStatus,
                ShellDryRunClass,
                ShellDryRunClassifierRequest,
                build_command_proposal,
                build_sandboxed_echo_noop_command,
                build_shell_dry_run_classification,
            )

            proposal = build_command_proposal(
                CommandProposalRequest(
                    request_ref="command-proposal-request:gate-m84",
                    proposal_ref="command-proposal:gate-m84",
                    sandbox_spec_ref="runtime-sandbox-spec:m81",
                    baseline_ref="baseline:v0.87.0",
                    actor_ref="actor:gate-m84",
                    prior_milestone_refs=[
                        "milestone:M57",
                        "milestone:M58",
                        "milestone:M80",
                        "milestone:M81",
                    ],
                    command_ref="command-ref:gate-noop",
                    safe_purpose="Gate verifies a no-effect command proposal for sandboxed echo/no-op.",
                    safe_command_label="gate noop metadata",
                    argv_preview=["gate-noop", "--dry-summary"],
                )
            )
            classification = build_shell_dry_run_classification(
                ShellDryRunClassifierRequest(
                    request_ref="shell-dry-run-classifier-request:gate-m84",
                    classifier_ref="shell-dry-run-classifier:gate-m84",
                    command_proposal_ref=proposal.proposal_ref,
                    sandbox_spec_ref=proposal.sandbox_spec_ref,
                    baseline_ref="baseline:v0.87.0",
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
            request = SandboxedEchoNoOpCommandRequest(
                request_ref="sandboxed-echo-noop-command-request:gate-m84",
                sandboxed_command_ref="sandboxed-echo-noop-command:gate-m84",
                shell_dry_run_classifier_ref=classification.classifier_ref,
                shell_dry_run_decision_ref=classification.decision_ref,
                command_proposal_ref=classification.command_proposal_ref,
                sandbox_spec_ref=classification.sandbox_spec_ref,
                baseline_ref="baseline:v0.87.0",
                actor_ref=classification.actor_ref,
                prior_milestone_refs=[
                    "milestone:M57",
                    "milestone:M58",
                    "milestone:M80",
                    "milestone:M81",
                    "milestone:M82",
                    "milestone:M83",
                ],
                safe_echo_text="Gate verifies M84 safe in-process echo/no-op text.",
                shell_dry_run_classification=classification,
            )
            decision = build_sandboxed_echo_noop_command(request)
            if (
                decision.status != SandboxedEchoNoOpCommandStatus.completed_for_review
                or decision.classification != ShellDryRunClass.no_effect_review
                or not decision.sandboxed_echo_noop_allowed
                or not decision.in_process_only
                or not decision.deterministic
                or not decision.local_only
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
                or decision.receipt_plan.store_raw_command
                or decision.receipt_plan.store_shell_string
                or decision.receipt_plan.store_raw_output
                or "M84_SANDBOXED_ECHO_NOOP_COMMAND_ONLY" not in decision.reason_codes
                or "M84_IN_PROCESS_ONLY" not in decision.reason_codes
                or "M84_NO_SHELL_OR_SUBPROCESS_EXECUTION" not in decision.reason_codes
                or "M85_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M84 sandboxed echo/no-op decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"command_execution_requested": True}, "COMMAND_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"contains_shell_string": True}, "M84_SHELL_STRING_DENIED"),
                (
                    {"contains_secret": True},
                    "SECRET_LIKE_SANDBOXED_ECHO_NOOP_CONTENT_DENIED",
                ),
            ]:
                try:
                    build_sandboxed_echo_noop_command(request.model_copy(update=update))
                    failures.append(
                        f"M84 unsafe sandboxed echo/no-op request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M84 unsafe sandboxed echo/no-op request raised {exc!s}, expected {reason}"
                        )
        except Exception as exc:
            failures.append(f"M84 sandboxed echo/no-op validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "sandboxed echo/no-op command",
            "in-process only",
            "deterministic",
            "local-only",
            "m83 shell dry-run classifier",
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
            "m85 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M84 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m84_sandboxed_echo_noop_static_safety(
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
                            f"M84 forbidden sandboxed echo/no-op fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m84_sandboxed_echo_noop_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m84_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M84 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
