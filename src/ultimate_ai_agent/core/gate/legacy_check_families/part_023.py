from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart023Mixin:
    """Legacy checks from m90_roadmap_currentness through m94_low_risk_browser_clicks_route_boundary."""
    def check_m90_roadmap_currentness(
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
            f"missing M90 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.94.0" not in text
            or "m90" not in text
            or "shell/subprocess hardening freeze" not in text
        ):
            failures.append(
                "active docs do not identify v0.94.0/M90 Shell/Subprocess Hardening Freeze"
            )
        if (
            "m90 is implemented/released" not in text
            and "v0.94.0 implements m90" not in text
        ):
            failures.append("active docs do not mark M90 implemented/released")
        for version_label, milestone, title in [
            ("v0.95.0", "M91", "Autonomous Tool Execution Contract"),
            ("v0.96.0", "M92", "Low-Risk Tool Autonomy, Single Session"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M91-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "command execution is implemented",
            "filesystem mutation is implemented",
            "subprocess execution is implemented",
            "shell execution is implemented",
            "process spawn is implemented",
            "process kill is implemented",
            "emergency stop execution is implemented",
            "network access is implemented",
            "browser click is implemented",
            "plugin execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M90 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m91_autonomous_tool_execution_contract(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/autonomous_execution_contract.py",
            "src/ultimate_ai_agent/core/tools/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/shell_subprocess_hardening_freeze.py",
            "docs/tools/AUTONOMOUS_TOOL_EXECUTION_CONTRACT.md",
            "docs/tools/AUTONOMOUS_TOOL_EXECUTION_CONTRACT_POLICY.md",
            "docs/tools/AUTONOMOUS_TOOL_EXECUTION_AUTHORITY_BOUNDARY.md",
            "docs/tools/AUTONOMOUS_TOOL_EXECUTION_RECEIPT_PLAN.md",
            "docs/tools/AUTONOMOUS_TOOL_EXECUTION_NON_GOALS.md",
            "docs/tools/M91_TO_M92_BOUNDARY.md",
            "tests/test_m91_autonomous_tool_execution_contract.py",
            "tests/test_m91_gate_integration.py",
        ]
        failures = [
            f"missing M91 autonomous tool execution contract file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m91_autonomous_tool_execution_contract import _request
            from ultimate_ai_agent.core.tools import (
                AutonomousToolExecutionContractStatus,
                build_autonomous_tool_execution_contract,
                validate_autonomous_tool_execution_contract_decision,
            )

            decision = build_autonomous_tool_execution_contract(_request())
            if (
                decision.status
                != AutonomousToolExecutionContractStatus.contract_ready_for_review
                or not decision.autonomous_tool_execution_contract_defined
                or not decision.contract_only
                or not decision.review_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.approval_refs_are_identifiers_only
                or not decision.dry_run_plan_only
                or not decision.m90_hardening_freeze_revalidated
                or decision.execution_authorized
                or decision.tool_execution_authorized
                or decision.autonomous_execution_authorized
                or decision.session_start_authorized
                or decision.background_worker_authorized
                or decision.execution_performed
                or decision.tool_execution_performed
                or decision.autonomous_execution_performed
                or decision.session_start_performed
                or decision.background_worker_started
                or decision.command_execution_performed
                or decision.shell_execution_performed
                or decision.subprocess_execution_performed
                or decision.filesystem_mutation_performed
                or decision.network_access_performed
                or decision.browser_automation_performed
                or decision.plugin_execution_performed
                or decision.remote_execution_performed
                or decision.model_call_performed
                or decision.memory_write_performed
                or decision.context_injection_performed
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.production_authority_granted
                or decision.side_effects_performed
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or decision.receipt_plan.store_raw_tool_payload
                or decision.receipt_plan.store_raw_provider_payload
                or "M91_AUTONOMOUS_TOOL_EXECUTION_CONTRACT_REVIEW_ONLY"
                not in decision.reason_codes
                or "M91_EXACT_M90_HARDENING_BINDING_REQUIRED"
                not in decision.reason_codes
                or "M91_NO_REAL_TOOL_EXECUTION" not in decision.reason_codes
                or "M91_NO_AUTONOMOUS_SESSION_START" not in decision.reason_codes
                or "M92_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M91 autonomous tool execution contract decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                (
                    {"autonomous_execution_requested": True},
                    "AUTONOMOUS_EXECUTION_DENIED",
                ),
                ({"session_start_requested": True}, "SESSION_START_DENIED"),
                ({"background_worker_requested": True}, "BACKGROUND_WORKER_DENIED"),
                ({"contains_raw_tool_payload": True}, "M91_RAW_TOOL_PAYLOAD_DENIED"),
                (
                    {"contains_raw_provider_payload": True},
                    "M91_RAW_PROVIDER_PAYLOAD_DENIED",
                ),
            ]:
                try:
                    build_autonomous_tool_execution_contract(_request(**update))
                    failures.append(
                        f"M91 unsafe contract request was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M91 unsafe contract request raised {exc!s}, expected {reason}"
                        )
            try:
                validate_autonomous_tool_execution_contract_decision(
                    decision.model_copy(update={"tool_execution_authorized": True})
                )
                failures.append(
                    "M91 mutated tool execution authority flag was not denied"
                )
            except ValueError as exc:
                if "TOOL_EXECUTION_DENIED" not in str(exc):
                    failures.append(
                        f"M91 mutated tool execution authority flag raised {exc!s}"
                    )
        except Exception as exc:
            failures.append(
                f"M91 autonomous tool execution contract validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "autonomous tool execution contract",
            "contract-only",
            "review-only",
            "deterministic",
            "local-only",
            "exact m90",
            "shell/subprocess hardening freeze",
            "safe refs only",
            "approval refs are identifiers only",
            "dry-run plan only",
            "no real tool execution",
            "no autonomous session start",
            "no command execution",
            "no shell execution",
            "no subprocess execution",
            "no filesystem mutation",
            "no network access",
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
            "no raw tool payload",
            "no raw provider payload",
            "safe summary only",
            "evaluator boundaries revalidate",
            "m92 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M91 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m91_autonomous_tool_execution_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "autonomous_tool_execution_enabled=True",
            "autonomous_execution_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "session_start_enabled=True",
            "background_worker_enabled=True",
            "execution_requested=True",
            "tool_execution_requested=True",
            "autonomous_execution_requested=True",
            "session_start_requested=True",
            "background_worker_requested=True",
            "execution_authorized=True",
            "tool_execution_authorized=True",
            "autonomous_execution_authorized=True",
            "session_start_authorized=True",
            "background_worker_authorized=True",
            "execution_performed=True",
            "tool_execution_performed=True",
            "autonomous_execution_performed=True",
            "session_start_performed=True",
            "background_worker_started=True",
            "command_execution_enabled=True",
            "command_execution_requested=True",
            "command_execution_performed=True",
            "shell_execution_enabled=True",
            "shell_execution_requested=True",
            "shell_execution_performed=True",
            "subprocess_execution_enabled=True",
            "subprocess_execution_requested=True",
            "subprocess_execution_performed=True",
            "filesystem_mutation_enabled=True",
            "filesystem_mutation_requested=True",
            "network_access_enabled=True",
            "network_access_requested=True",
            "browser_automation_enabled=True",
            "browser_automation_requested=True",
            "plugin_execution_enabled=True",
            "plugin_execution_requested=True",
            "remote_execution_enabled=True",
            "remote_execution_requested=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "control_center_control_enabled=True",
            "dependency_change_enabled=True",
            "production_authority_enabled=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "store_raw_tool_payload=True",
            "store_raw_provider_payload=True",
            "store_raw_prompt=True",
            "store_secret=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/__init__.py",
            "src/ultimate_ai_agent/core/tools/autonomous_execution_contract.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "src/ultimate_ai_agent/core/sandbox/shell_subprocess_hardening_freeze.py",
            "src/ultimate_ai_agent/core/sandbox/emergency_stop_process_kill_safety.py",
            "src/ultimate_ai_agent/core/sandbox/mutating_command_proposal.py",
            "src/ultimate_ai_agent/core/sandbox/command_audit_replay.py",
            "src/ultimate_ai_agent/core/sandbox/shell_approval_gate.py",
            "src/ultimate_ai_agent/core/sandbox/read_only_command_allowlist.py",
            "src/ultimate_ai_agent/core/sandbox/sandboxed_echo_noop_command.py",
            "src/ultimate_ai_agent/core/sandbox/shell_dry_run_classifier.py",
            "src/ultimate_ai_agent/core/sandbox/command_proposal.py",
            "src/ultimate_ai_agent/core/sandbox/runtime_spec.py",
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
                            f"M91 forbidden autonomous tool execution fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m91_autonomous_tool_execution_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m91_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M91 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m91_roadmap_currentness(
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
            f"missing M91 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.95.0" not in text
            or "m91" not in text
            or "autonomous tool execution contract" not in text
        ):
            failures.append(
                "active docs do not identify v0.95.0/M91 Autonomous Tool Execution Contract"
            )
        if (
            "m91 is implemented/released" not in text
            and "v0.95.0 implements m91" not in text
        ):
            failures.append("active docs do not mark M91 implemented/released")
        for version_label, milestone, title in [
            ("v0.96.0", "M92", "Low-Risk Tool Autonomy, Single Session"),
            ("v0.97.0", "M93", "Multi-Tool Dry-Run to Real Run Promotion"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M92-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "real tool execution is implemented",
            "autonomous session start is implemented",
            "command execution is implemented",
            "filesystem mutation is implemented",
            "subprocess execution is implemented",
            "shell execution is implemented",
            "network access is implemented",
            "browser click is implemented",
            "plugin execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M91 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m92_low_risk_tool_autonomy_single_session(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/tool_autonomy_single_session.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/tools/autonomous_execution_contract.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run.py",
            "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION.md",
            "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_POLICY.md",
            "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_RECEIPT_PLAN.md",
            "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_NON_GOALS.md",
            "docs/autonomy/M92_TO_M93_BOUNDARY.md",
            "tests/test_m92_low_risk_tool_autonomy_single_session.py",
            "tests/test_m92_gate_integration.py",
        ]
        failures = [
            f"missing M92 low-risk tool autonomy file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m92_low_risk_tool_autonomy_single_session import _request
            from ultimate_ai_agent.core.autonomy import (
                LowRiskToolAutonomySingleSessionStatus,
                build_low_risk_tool_autonomy_single_session_decision,
                validate_low_risk_tool_autonomy_single_session_decision,
            )

            decision = build_low_risk_tool_autonomy_single_session_decision(_request())
            if (
                decision.status
                != LowRiskToolAutonomySingleSessionStatus.single_session_ready_for_review
                or not decision.review_only
                or not decision.low_risk_only
                or not decision.single_session_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.m91_contract_revalidated
                or not decision.low_risk_dry_run_revalidated
                or not decision.single_session_scope_defined
                or decision.execution_authorized
                or decision.tool_execution_authorized
                or decision.autonomous_execution_authorized
                or decision.session_start_authorized
                or decision.background_worker_authorized
                or decision.execution_performed
                or decision.tool_execution_performed
                or decision.session_start_performed
                or decision.background_worker_started
                or decision.side_effects_performed
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or decision.receipt_plan.store_raw_tool_payload
                or decision.receipt_plan.execution_performed
                or "M92_LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_REVIEW_ONLY"
                not in decision.reason_codes
                or "M92_EXACT_M91_CONTRACT_BINDING_REQUIRED"
                not in decision.reason_codes
                or "M92_EXACT_LOW_RISK_DRY_RUN_BINDING_REQUIRED"
                not in decision.reason_codes
                or "M92_SINGLE_SESSION_ONLY" not in decision.reason_codes
                or "M92_NO_REAL_TOOL_EXECUTION" not in decision.reason_codes
                or "M93_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M92 low-risk tool autonomy decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"execution_authorized": True}, "EXECUTION_DENIED"),
                ({"tool_execution_authorized": True}, "TOOL_EXECUTION_DENIED"),
                ({"session_start_authorized": True}, "SESSION_START_DENIED"),
                ({"background_worker_started": True}, "BACKGROUND_WORKER_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
            ]:
                try:
                    validate_low_risk_tool_autonomy_single_session_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M92 unsafe decision mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M92 unsafe decision mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M92 low-risk tool autonomy validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "low-risk tool autonomy, single session",
            "review-only",
            "low-risk only",
            "single-session only",
            "deterministic",
            "local-only",
            "safe refs only",
            "exact m91",
            "autonomous tool execution contract",
            "exact low-risk autonomous dry run",
            "no real tool execution",
            "no autonomous execution",
            "no session start",
            "no additional session",
            "no multi-tool",
            "no command execution",
            "no shell execution",
            "no subprocess execution",
            "no filesystem mutation",
            "no network access",
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
            "no raw tool payload",
            "no raw provider payload",
            "safe summary only",
            "evaluator boundaries revalidate",
            "m93 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M92 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m92_low_risk_tool_autonomy_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "low_risk_tool_autonomy_enabled=True",
            "real_tool_execution_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "autonomous_execution_enabled=True",
            "session_start_enabled=True",
            "additional_session_enabled=True",
            "background_worker_enabled=True",
            "multi_tool_enabled=True",
            "command_execution_enabled=True",
            "shell_execution_enabled=True",
            "subprocess_execution_enabled=True",
            "filesystem_mutation_enabled=True",
            "network_access_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "remote_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "control_center_control_enabled=True",
            "dependency_change_enabled=True",
            "production_authority_enabled=True",
            "execution_requested=True",
            "tool_execution_requested=True",
            "autonomous_execution_requested=True",
            "session_start_requested=True",
            "additional_session_requested=True",
            "background_worker_requested=True",
            "multi_tool_requested=True",
            "execution_authorized=True",
            "tool_execution_authorized=True",
            "autonomous_execution_authorized=True",
            "session_start_authorized=True",
            "background_worker_authorized=True",
            "execution_performed=True",
            "tool_execution_performed=True",
            "session_start_performed=True",
            "background_worker_started=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "store_raw_tool_payload=True",
            "store_raw_provider_payload=True",
            "store_raw_prompt=True",
            "store_secret=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/tool_autonomy_single_session.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run.py",
            "src/ultimate_ai_agent/core/tools/autonomous_execution_contract.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
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
                            f"M92 forbidden low-risk tool autonomy fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m92_low_risk_tool_autonomy_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m92_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M92 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m92_roadmap_currentness(
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
            f"missing M92 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.96.0" not in text
            or "m92" not in text
            or "low-risk tool autonomy, single session" not in text
        ):
            failures.append(
                "active docs do not identify v0.96.0/M92 Low-Risk Tool Autonomy, Single Session"
            )
        if (
            "m92 is implemented/released" not in text
            and "v0.96.0 implements m92" not in text
        ):
            failures.append("active docs do not mark M92 implemented/released")
        for version_label, milestone, title in [
            ("v0.97.0", "M93", "Multi-Tool Dry-Run to Real Run Promotion"),
            ("v0.98.0", "M94", "Autonomous Browser Clicks, Low-Risk Only"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M93-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "real tool execution is implemented",
            "autonomous session start is implemented",
            "multi-tool real run is implemented",
            "command execution is implemented",
            "filesystem mutation is implemented",
            "subprocess execution is implemented",
            "shell execution is implemented",
            "network access is implemented",
            "browser click is implemented",
            "plugin execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M92 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m93_multi_tool_dry_run_promotion(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/dry_run_promotion.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/tool_autonomy_single_session.py",
            "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION.md",
            "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_POLICY.md",
            "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_RECEIPT_PLAN.md",
            "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_NON_GOALS.md",
            "docs/autonomy/M93_TO_M94_BOUNDARY.md",
            "tests/test_m93_multi_tool_dry_run_promotion.py",
            "tests/test_m93_gate_integration.py",
        ]
        failures = [
            f"missing M93 multi-tool dry-run promotion file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m93_multi_tool_dry_run_promotion import _request
            from ultimate_ai_agent.core.autonomy import (
                MultiToolDryRunPromotionStatus,
                build_multi_tool_dry_run_promotion_decision,
                validate_multi_tool_dry_run_promotion_decision,
            )

            decision = build_multi_tool_dry_run_promotion_decision(_request())
            if (
                decision.status
                != MultiToolDryRunPromotionStatus.promotion_ready_for_review
                or not decision.review_only
                or not decision.deterministic
                or not decision.local_only
                or not decision.safe_refs_only
                or not decision.m92_single_session_revalidated
                or not decision.dry_run_plan_bound
                or not decision.real_run_plan_bound
                or not decision.dry_run_real_run_equivalent
                or not decision.exact_promotion_approval_bound
                or not decision.wildcard_approval_denied
                or not decision.promotion_allowed_for_review
                or decision.execution_authorized
                or decision.real_run_execution_authorized
                or decision.tool_execution_authorized
                or decision.session_start_authorized
                or decision.execution_performed
                or decision.real_run_execution_performed
                or decision.tool_execution_performed
                or decision.side_effects_performed
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or not decision.receipt_plan.store_plan_hash_refs_only
                or decision.receipt_plan.execution_performed
                or "M93_MULTI_TOOL_DRY_RUN_REAL_RUN_PROMOTION_REVIEW_ONLY"
                not in decision.reason_codes
                or "M93_DRY_RUN_REAL_RUN_EQUIVALENCE_REQUIRED"
                not in decision.reason_codes
                or "M93_EXACT_PROMOTION_APPROVAL_REQUIRED" not in decision.reason_codes
                or "M93_PLAN_HASH_BINDING_REQUIRED" not in decision.reason_codes
                or "M93_NO_UNAPPROVED_REAL_EXECUTION" not in decision.reason_codes
                or "M94_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M93 dry-run promotion decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"execution_authorized": True}, "EXECUTION_DENIED"),
                (
                    {"real_run_execution_authorized": True},
                    "M93_REAL_RUN_EXECUTION_DENIED",
                ),
                ({"tool_execution_authorized": True}, "TOOL_EXECUTION_DENIED"),
                ({"session_start_authorized": True}, "SESSION_START_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
            ]:
                try:
                    validate_multi_tool_dry_run_promotion_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M93 unsafe decision mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M93 unsafe decision mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M93 dry-run promotion validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "multi-tool dry-run to real run promotion",
            "review-only",
            "dry-run plan",
            "real-run plan",
            "exact m92",
            "exact promotion approval",
            "wildcard approval denied",
            "plan hash",
            "dry-run and real-run equivalence",
            "no unapproved real execution",
            "no real-run execution",
            "no tool execution",
            "no autonomous execution",
            "no session start",
            "no command execution",
            "no shell execution",
            "no subprocess execution",
            "no filesystem mutation",
            "no network access",
            "no browser click",
            "no browser form",
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
            "safe refs only",
            "safe summary only",
            "evaluator boundaries revalidate",
            "m94 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M93 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m93_multi_tool_dry_run_promotion_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "real_run_promotion_enabled=True",
            "real_run_execution_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "autonomous_execution_enabled=True",
            "session_start_enabled=True",
            "background_worker_enabled=True",
            "command_execution_enabled=True",
            "shell_execution_enabled=True",
            "subprocess_execution_enabled=True",
            "filesystem_mutation_enabled=True",
            "network_access_enabled=True",
            "browser_click_enabled=True",
            "browser_form_enabled=True",
            "plugin_execution_enabled=True",
            "remote_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "control_center_control_enabled=True",
            "dependency_change_enabled=True",
            "production_authority_enabled=True",
            "execution_requested=True",
            "real_run_execution_requested=True",
            "tool_execution_requested=True",
            "session_start_requested=True",
            "execution_authorized=True",
            "real_run_execution_authorized=True",
            "tool_execution_authorized=True",
            "session_start_authorized=True",
            "execution_performed=True",
            "real_run_execution_performed=True",
            "tool_execution_performed=True",
            "session_start_performed=True",
            "background_worker_started=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "store_raw_tool_payload=True",
            "store_raw_provider_payload=True",
            "store_raw_prompt=True",
            "store_secret=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run_promotion.py",
            "src/ultimate_ai_agent/core/autonomy/tool_autonomy_single_session.py",
            "src/ultimate_ai_agent/core/autonomy/dry_run.py",
            "src/ultimate_ai_agent/core/tools/autonomous_execution_contract.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
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
                            f"M93 forbidden dry-run promotion fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m93_multi_tool_dry_run_promotion_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m93_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M93 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m93_roadmap_currentness(
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
            f"missing M93 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.97.0" not in text
            or "m93" not in text
            or "multi-tool dry-run to real run promotion" not in text
        ):
            failures.append(
                "active docs do not identify v0.97.0/M93 Multi-Tool Dry-Run to Real Run Promotion"
            )
        if (
            "m93 is implemented/released" not in text
            and "v0.97.0 implements m93" not in text
        ):
            failures.append("active docs do not mark M93 implemented/released")
        for version_label, milestone, title in [
            ("v0.98.0", "M94", "Autonomous Browser Clicks, Low-Risk Only"),
            ("v0.99.0", "M95", "Network Tool Expansion, Authless Only"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M94-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "real-run execution is implemented",
            "real tool execution is implemented",
            "browser click is implemented",
            "browser form is implemented",
            "command execution is implemented",
            "shell execution is implemented",
            "subprocess execution is implemented",
            "filesystem mutation is implemented",
            "network access is implemented",
            "plugin execution is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M93 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m94_low_risk_browser_clicks(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/browser/low_risk_click.py",
            "src/ultimate_ai_agent/core/browser/__init__.py",
            "docs/browser/LOW_RISK_BROWSER_CLICKS.md",
            "docs/browser/LOW_RISK_BROWSER_CLICK_POLICY.md",
            "docs/browser/LOW_RISK_BROWSER_CLICK_AUTHORITY_BOUNDARY.md",
            "docs/browser/LOW_RISK_BROWSER_CLICK_RECEIPT_PLAN.md",
            "docs/browser/LOW_RISK_BROWSER_CLICK_NON_GOALS.md",
            "docs/browser/M94_TO_M95_BOUNDARY.md",
            "tests/test_m94_low_risk_browser_clicks.py",
            "tests/test_m94_gate_integration.py",
        ]
        failures = [
            f"missing M94 low-risk browser click file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m94_low_risk_browser_clicks import _request, _transport
            from ultimate_ai_agent.core.browser import (
                LowRiskBrowserClickStatus,
                build_low_risk_browser_click_decision,
                perform_low_risk_browser_click,
                validate_low_risk_browser_click_decision,
            )

            decision = build_low_risk_browser_click_decision(_request())
            result = perform_low_risk_browser_click(decision, transport=_transport)
            if (
                decision.status
                != LowRiskBrowserClickStatus.click_allowed_for_scoped_session
                or not decision.low_risk_click_allowed
                or not decision.scoped_session_bound
                or not decision.allowlisted_page_bound
                or not decision.allowlisted_action_bound
                or not decision.exact_m93_promotion_bound
                or not decision.exact_click_approval_bound
                or not decision.audit_bound
                or not decision.revocation_bound
                or decision.click_performed
                or decision.form_submission_performed
                or decision.typing_performed
                or decision.purchase_performed
                or decision.download_performed
                or decision.authentication_performed
                or decision.credential_or_cookie_access_performed
                or decision.raw_dom_returned
                or decision.screenshot_returned
                or decision.external_network_performed
                or decision.memory_write_performed
                or decision.context_injection_performed
                or decision.backend_route_added
                or decision.production_authority_granted
                or decision.side_effects_performed
                or not decision.receipt_plan.store_safe_summary_only
                or not decision.receipt_plan.store_safe_refs_only
                or result.status != LowRiskBrowserClickStatus.click_completed
                or not result.click_performed
                or result.raw_dom_returned
                or result.screenshot_returned
                or result.form_submission_performed
                or result.typing_performed
                or result.purchase_performed
                or result.download_performed
                or result.authentication_performed
                or result.credential_or_cookie_access_performed
                or result.external_network_performed
                or result.memory_write_performed
                or result.context_injection_performed
                or result.production_authority_granted
                or result.side_effects_performed
                or "M94_LOW_RISK_BROWSER_CLICK_ALLOWED" not in decision.reason_codes
                or "M95_REMAINS_FUTURE" not in decision.reason_codes
                or "M94_LOW_RISK_BROWSER_CLICK_COMPLETED" not in result.reason_codes
            ):
                failures.append(
                    "M94 low-risk browser click decision/result is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"click_performed": True}, "M94_CLICK_NOT_ALLOWED_IN_DECISION"),
                ({"form_submission_performed": True}, "FORM_SUBMISSION_DENIED"),
                ({"raw_dom_returned": True}, "RAW_DOM_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                ({"production_authority_granted": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_low_risk_browser_click_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M94 unsafe decision mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M94 unsafe decision mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M94 low-risk browser click validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "autonomous browser clicks, low-risk only",
            "low-risk click",
            "scoped session",
            "allowlisted page",
            "allowlisted action",
            "exact m93",
            "exact click approval",
            "audit",
            "revocation",
            "injected transport",
            "safe refs only",
            "safe summary only",
            "no form submission",
            "no typing",
            "no purchase",
            "no download",
            "no upload",
            "no authentication",
            "no account change",
            "no destructive action",
            "no credential or cookie access",
            "no raw dom",
            "no screenshot",
            "no broad navigation",
            "no external network",
            "no shell execution",
            "no plugin execution",
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
            "m95 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M94 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m94_low_risk_browser_clicks_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "form_submission_allowed=True",
            "typing_allowed=True",
            "purchase_allowed=True",
            "download_allowed=True",
            "upload_allowed=True",
            "authentication_allowed=True",
            "account_change_allowed=True",
            "destructive_action_allowed=True",
            "credential_or_cookie_access_allowed=True",
            "raw_dom_allowed=True",
            "screenshot_allowed=True",
            "broad_navigation_allowed=True",
            "external_network_allowed=True",
            "shell_execution_allowed=True",
            "plugin_execution_allowed=True",
            "model_call_allowed=True",
            "memory_write_allowed=True",
            "context_injection_allowed=True",
            "backend_route_allowed=True",
            "control_center_control_allowed=True",
            "dependency_change_allowed=True",
            "production_authority_allowed=True",
            "form_submission_requested=True",
            "typing_requested=True",
            "purchase_requested=True",
            "download_requested=True",
            "authentication_requested=True",
            "credential_or_cookie_access_requested=True",
            "raw_dom_requested=True",
            "screenshot_requested=True",
            "browser_form_enabled=True",
            "browser_click_enabled=True",
            "browser_click_performed=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "store_raw_dom=True",
            "store_screenshot=True",
            "store_credentials_or_cookies=True",
            "store_raw_prompt=True",
            "store_raw_provider_payload=True",
            "store_secret=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/browser/__init__.py",
            "src/ultimate_ai_agent/core/browser/low_risk_click.py",
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
                            f"M94 forbidden browser click fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m94_low_risk_browser_clicks_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m94_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M94 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
