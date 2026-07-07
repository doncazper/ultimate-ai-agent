from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart024Mixin:
    """Legacy checks from m94_roadmap_currentness through m98_roadmap_currentness."""
    def check_m94_roadmap_currentness(
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
            f"missing M94 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.98.0" not in text
            or "m94" not in text
            or "autonomous browser clicks, low-risk only" not in text
        ):
            failures.append(
                "active docs do not identify v0.98.0/M94 Autonomous Browser Clicks, Low-Risk Only"
            )
        if (
            "m94 is implemented/released" not in text
            and "v0.98.0 implements m94" not in text
        ):
            failures.append("active docs do not mark M94 implemented/released")
        for version_label, milestone, title in [
            ("v0.99.0", "M95", "Network Tool Expansion, Authless Only"),
            ("v1.0.0", "M96", "Plugin Execution Sandbox, No External Plugins"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M95-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "browser form is implemented",
            "browser download is implemented",
            "browser authentication is implemented",
            "unrestricted network is implemented",
            "network mutation is implemented",
            "plugin execution is implemented",
            "recurring automation is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M94 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m95_authless_network_tool_expansion(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/network/authless_expansion.py",
            "src/ultimate_ai_agent/core/network/__init__.py",
            "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION.md",
            "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_POLICY.md",
            "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md",
            "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_RECEIPT_PLAN.md",
            "docs/network/AUTHLESS_NETWORK_TOOL_EXPANSION_NON_GOALS.md",
            "docs/network/M95_TO_M96_BOUNDARY.md",
            "tests/test_m95_network_tool_expansion_authless.py",
            "tests/test_m95_gate_integration.py",
        ]
        failures = [
            f"missing M95 authless network expansion file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m95_network_tool_expansion_authless import _policy, _request
            from ultimate_ai_agent.core.network import (
                AuthlessNetworkExpansionStatus,
                build_authless_network_expansion_decision,
                validate_authless_network_expansion_decision,
            )

            decision = build_authless_network_expansion_decision(_request(), _policy())
            if (
                decision.status
                != AuthlessNetworkExpansionStatus.authless_read_only_allowed
                or not decision.authless_read_only_allowed
                or not decision.disabled_by_default
                or not decision.exact_scope_bound
                or not decision.exact_approval_bound
                or not decision.allowlisted_domain_bound
                or not decision.redirect_policy_bound
                or not decision.bounded_output_bound
                or not decision.redaction_bound
                or not decision.audit_bound
                or not decision.revocation_bound
                or not decision.transport_injection_required
                or decision.network_call_performed
                or decision.unrestricted_network_allowed
                or decision.authenticated_network_allowed
                or decision.credential_headers_allowed
                or decision.cookies_allowed
                or decision.request_body_allowed
                or decision.mutation_method_allowed
                or decision.private_network_allowed
                or decision.account_action_allowed
                or decision.download_or_export_allowed
                or decision.browser_form_allowed
                or decision.provider_model_call_allowed
                or decision.shell_execution_allowed
                or decision.plugin_execution_allowed
                or decision.memory_write_allowed
                or decision.context_injection_allowed
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.production_authority_granted
                or not decision.receipt_plan.store_safe_refs_only
                or not decision.receipt_plan.store_redacted_preview_only
                or decision.receipt_plan.raw_response_stored
                or decision.receipt_plan.raw_headers_stored
                or decision.receipt_plan.credential_headers_stored
                or decision.receipt_plan.cookies_stored
                or decision.receipt_plan.query_string_stored
                or decision.receipt_plan.side_effects_performed
                or "M95_AUTHLESS_READ_ONLY_NETWORK_EXPANSION_ALLOWED"
                not in decision.reason_codes
                or "M96_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M95 authless network expansion decision is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"network_call_performed": True},
                    "NETWORK_CALL_PERFORMED_DENIED_IN_DECISION",
                ),
                (
                    {"authenticated_network_allowed": True},
                    "AUTHENTICATED_NETWORK_DENIED",
                ),
                ({"credential_headers_allowed": True}, "CREDENTIAL_HEADERS_DENIED"),
                ({"request_body_allowed": True}, "REQUEST_BODY_DENIED"),
                ({"mutation_method_allowed": True}, "MUTATION_METHOD_DENIED"),
                ({"private_network_allowed": True}, "PRIVATE_NETWORK_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                ({"production_authority_granted": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_authless_network_expansion_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M95 unsafe decision mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M95 unsafe decision mutation raised {exc!s}")
            try:
                validate_authless_network_expansion_decision(
                    decision.model_copy(
                        update={
                            "receipt_plan": decision.receipt_plan.model_copy(
                                update={"raw_response_stored": True}
                            )
                        }
                    )
                )
                failures.append("M95 raw response receipt mutation was not denied")
            except ValueError as exc:
                if "RAW_RESPONSE_DENIED" not in str(exc):
                    failures.append(f"M95 raw response receipt mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M95 authless network expansion validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "network tool expansion, authless only",
            "authless",
            "read-only",
            "allowlisted domain",
            "https",
            "get only",
            "redirect controls",
            "bounded output",
            "redaction",
            "exact scope",
            "audit",
            "revocation",
            "transport injection",
            "safe refs only",
            "redacted preview only",
            "no credentials",
            "no cookies",
            "no credential headers",
            "no request body",
            "no post",
            "no put",
            "no patch",
            "no delete",
            "no account action",
            "no private network",
            "no download",
            "no export",
            "no browser form",
            "no provider model call",
            "no shell execution",
            "no plugin execution",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
            "m96 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M95 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m95_authless_network_tool_expansion_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "unrestricted_network_allowed=True",
            "authenticated_network_allowed=True",
            "credential_headers_allowed=True",
            "cookies_allowed=True",
            "request_body_allowed=True",
            "mutation_method_allowed=True",
            "private_network_allowed=True",
            "account_action_allowed=True",
            "download_or_export_allowed=True",
            "browser_form_allowed=True",
            "provider_model_call_allowed=True",
            "shell_execution_allowed=True",
            "plugin_execution_allowed=True",
            "memory_write_allowed=True",
            "context_injection_allowed=True",
            "backend_route_allowed=True",
            "control_center_control_allowed=True",
            "dependency_change_allowed=True",
            "production_authority_allowed=True",
            "unrestricted_network_requested=True",
            "authenticated_network_requested=True",
            "credentials_or_cookies_requested=True",
            "credential_headers_requested=True",
            "mutation_method_requested=True",
            "private_network_requested=True",
            "account_action_requested=True",
            "download_or_export_requested=True",
            "browser_form_requested=True",
            "provider_model_call_requested=True",
            "shell_execution_requested=True",
            "plugin_execution_requested=True",
            "memory_write_requested=True",
            "context_injection_requested=True",
            "backend_route_requested=True",
            "control_center_control_requested=True",
            "dependency_requested=True",
            "production_authority_requested=True",
            "network_call_performed=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "network_post_enabled=True",
            "network_mutation_enabled=True",
            "credential_header_enabled=True",
            "store_raw_response=True",
            "store_raw_headers=True",
            "store_credentials=True",
            "store_cookies=True",
            "store_raw_prompt=True",
            "store_raw_provider_payload=True",
            "store_secret=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/network/__init__.py",
            "src/ultimate_ai_agent/core/network/authless_expansion.py",
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
                            f"M95 forbidden authless network fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m95_authless_network_tool_expansion_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m95_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M95 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m95_roadmap_currentness(
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
            f"missing M95 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.99.0" not in text
            or "m95" not in text
            or "network tool expansion, authless only" not in text
        ):
            failures.append(
                "active docs do not identify v0.99.0/M95 Network Tool Expansion, Authless Only"
            )
        if (
            "m95 is implemented/released" not in text
            and "v0.99.0 implements m95" not in text
        ):
            failures.append("active docs do not mark M95 implemented/released")
        for version_label, milestone, title in [
            ("v1.0.0", "M96", "Plugin Execution Sandbox, No External Plugins"),
            ("v1.1.0", "M97", "Recurring Automation Contracts"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M96-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "external plugin execution is implemented",
            "recurring automation is implemented",
            "mobile permission runtime is implemented",
            "mobile sensor access is implemented",
            "network mutation is implemented",
            "authenticated network is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M95 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m96_plugin_execution_sandbox(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/plugin_execution_sandbox/__init__.py",
            "src/ultimate_ai_agent/core/plugin_execution_sandbox/builtin_test_plugin.py",
            "docs/tooling/PLUGIN_EXECUTION_SANDBOX.md",
            "docs/tooling/PLUGIN_EXECUTION_SANDBOX_POLICY.md",
            "docs/tooling/PLUGIN_EXECUTION_SANDBOX_AUTHORITY_BOUNDARY.md",
            "docs/tooling/PLUGIN_EXECUTION_SANDBOX_RECEIPT_PLAN.md",
            "docs/tooling/PLUGIN_EXECUTION_SANDBOX_NON_GOALS.md",
            "docs/tooling/M96_TO_M97_BOUNDARY.md",
            "tests/test_m96_plugin_execution_sandbox.py",
            "tests/test_m96_gate_integration.py",
        ]
        failures = [
            f"missing M96 plugin execution sandbox file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m96_plugin_execution_sandbox import _request
            from ultimate_ai_agent.core.plugin_execution_sandbox import (
                BuiltInPluginExecutionSandboxStatus,
                build_builtin_plugin_execution_sandbox_decision,
                validate_builtin_plugin_execution_sandbox_decision,
            )

            decision = build_builtin_plugin_execution_sandbox_decision(_request())
            if (
                decision.status
                != BuiltInPluginExecutionSandboxStatus.builtin_test_plugin_allowed
                or not decision.capability_exists
                or not decision.disabled_by_default
                or not decision.builtin_test_plugin_only
                or not decision.sandbox_enforced
                or not decision.manifest_permissions_enforced
                or not decision.audit_receipt_created
                or not decision.revocation_bound
                or not decision.deterministic_result
                or not decision.safe_refs_only
                or not decision.built_in_test_plugin_invoked
                or decision.external_plugin_loading_allowed
                or decision.marketplace_plugin_allowed
                or decision.arbitrary_plugin_code_allowed
                or decision.runtime_import_allowed
                or decision.networked_plugin_fetch_allowed
                or decision.plugin_secret_access_allowed
                or decision.raw_plugin_payload_allowed
                or decision.shell_execution_allowed
                or decision.network_access_allowed
                or decision.browser_automation_allowed
                or decision.filesystem_mutation_allowed
                or decision.model_provider_call_allowed
                or decision.memory_write_allowed
                or decision.context_injection_allowed
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.production_authority_granted
                or not decision.receipt_plan.store_safe_refs_only
                or decision.receipt_plan.store_raw_plugin_payload
                or decision.receipt_plan.store_secret_material
                or decision.receipt_plan.external_plugin_loaded
                or decision.receipt_plan.runtime_import_performed
                or decision.receipt_plan.network_fetch_performed
                or decision.receipt_plan.shell_execution_performed
                or decision.receipt_plan.filesystem_mutation_performed
                or decision.receipt_plan.side_effects_performed
                or "M96_BUILTIN_TEST_PLUGIN_SANDBOX_ALLOWED"
                not in decision.reason_codes
                or "M97_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M96 plugin execution sandbox decision is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"external_plugin_loading_allowed": True},
                    "EXTERNAL_PLUGIN_LOADING_DENIED",
                ),
                ({"marketplace_plugin_allowed": True}, "MARKETPLACE_PLUGIN_DENIED"),
                (
                    {"arbitrary_plugin_code_allowed": True},
                    "ARBITRARY_PLUGIN_CODE_DENIED",
                ),
                ({"runtime_import_allowed": True}, "PLUGIN_RUNTIME_IMPORT_DENIED"),
                (
                    {"networked_plugin_fetch_allowed": True},
                    "NETWORKED_PLUGIN_FETCH_DENIED",
                ),
                ({"raw_plugin_payload_allowed": True}, "RAW_PLUGIN_PAYLOAD_DENIED"),
                ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
                ({"production_authority_granted": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_builtin_plugin_execution_sandbox_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M96 unsafe decision mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M96 unsafe decision mutation raised {exc!s}")
            try:
                validate_builtin_plugin_execution_sandbox_decision(
                    decision.model_copy(
                        update={
                            "receipt_plan": decision.receipt_plan.model_copy(
                                update={"external_plugin_loaded": True}
                            )
                        }
                    )
                )
                failures.append("M96 external plugin receipt mutation was not denied")
            except ValueError as exc:
                if "EXTERNAL_PLUGIN_LOADING_DENIED" not in str(exc):
                    failures.append(
                        f"M96 external plugin receipt mutation raised {exc!s}"
                    )
        except Exception as exc:
            failures.append(f"M96 plugin execution sandbox validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "plugin execution sandbox, no external plugins",
            "built-in test plugin",
            "sandbox",
            "manifest permission",
            "audit receipt",
            "revocation",
            "deterministic",
            "safe refs only",
            "no external plugin loading",
            "no marketplace plugin",
            "no arbitrary plugin code",
            "no runtime import",
            "no networked plugin fetch",
            "no plugin secret access",
            "no raw plugin payload",
            "no shell execution",
            "no network access",
            "no browser automation",
            "no filesystem mutation",
            "no model provider call",
            "no memory write",
            "no context injection",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
            "m97 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M96 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m96_plugin_execution_sandbox_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "external_plugin_loading_allowed=True",
            "marketplace_plugin_allowed=True",
            "arbitrary_plugin_code_allowed=True",
            "runtime_import_allowed=True",
            "networked_plugin_fetch_allowed=True",
            "plugin_secret_access_allowed=True",
            "raw_plugin_payload_allowed=True",
            "shell_execution_allowed=True",
            "network_access_allowed=True",
            "browser_automation_allowed=True",
            "filesystem_mutation_allowed=True",
            "model_provider_call_allowed=True",
            "memory_write_allowed=True",
            "context_injection_allowed=True",
            "backend_route_allowed=True",
            "control_center_control_allowed=True",
            "dependency_change_allowed=True",
            "production_authority_allowed=True",
            "external_plugin_requested=True",
            "marketplace_plugin_requested=True",
            "arbitrary_plugin_code_requested=True",
            "runtime_import_requested=True",
            "networked_plugin_fetch_requested=True",
            "plugin_secret_access_requested=True",
            "raw_plugin_payload_requested=True",
            "backend_route_requested=True",
            "control_center_control_requested=True",
            "dependency_requested=True",
            "production_authority_requested=True",
            "external_plugin_loaded=True",
            "runtime_import_performed=True",
            "network_fetch_performed=True",
            "shell_execution_performed=True",
            "filesystem_mutation_performed=True",
            "store_raw_plugin_payload=True",
            "store_secret_material=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/plugin_execution_sandbox/__init__.py",
            "src/ultimate_ai_agent/core/plugin_execution_sandbox/builtin_test_plugin.py",
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
                            f"M96 forbidden plugin sandbox fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m96_plugin_execution_sandbox_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m96_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M96 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m96_roadmap_currentness(
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
            f"missing M96 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v1.0.0" not in text
            or "m96" not in text
            or "plugin execution sandbox, no external plugins" not in text
        ):
            failures.append(
                "active docs do not identify v1.0.0/M96 Plugin Execution Sandbox, No External Plugins"
            )
        if (
            "m96 is implemented/released" not in text
            and "v1.0.0 implements m96" not in text
        ):
            failures.append("active docs do not mark M96 implemented/released")
        for version_label, milestone, title in [
            ("v1.1.0", "M97", "Recurring Automation Contracts"),
            ("v1.2.0", "M98", "Scoped Recurring Low-Risk Automation"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M97-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "external plugin loading is implemented",
            "marketplace plugin is implemented",
            "arbitrary plugin code is implemented",
            "recurring automation is implemented",
            "mobile permission runtime is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M96 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m97_recurring_automation_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/recurring_automation_contracts/__init__.py",
            "src/ultimate_ai_agent/core/recurring_automation_contracts/contracts.py",
            "docs/automation/RECURRING_AUTOMATION_CONTRACTS.md",
            "docs/automation/RECURRING_AUTOMATION_RENEWAL_POLICY.md",
            "docs/automation/RECURRING_AUTOMATION_STOP_CONDITIONS.md",
            "docs/automation/RECURRING_AUTOMATION_AUTHORITY_BOUNDARY.md",
            "docs/automation/RECURRING_AUTOMATION_RECEIPT_PLAN.md",
            "docs/automation/RECURRING_AUTOMATION_NON_GOALS.md",
            "docs/automation/M97_TO_M98_BOUNDARY.md",
            "tests/test_m97_recurring_automation_contracts.py",
            "tests/test_m97_gate_integration.py",
        ]
        failures = [
            f"missing M97 recurring automation contracts file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m97_recurring_automation_contracts import _request
            from ultimate_ai_agent.core.recurring_automation_contracts import (
                RecurringAutomationContractStatus,
                build_recurring_automation_contract_decision,
                validate_recurring_automation_contract_decision,
            )

            decision = build_recurring_automation_contract_decision(_request())
            if (
                decision.status
                != RecurringAutomationContractStatus.contract_ready_disabled
                or not decision.capability_exists
                or not decision.disabled_by_default
                or not decision.contract_only
                or not decision.approval_renewal_required
                or not decision.expiration_required
                or not decision.stop_conditions_required
                or not decision.audit_required
                or not decision.revocation_required
                or not decision.safe_refs_only
                or decision.recurrence_runtime_enabled
                or decision.background_worker_enabled
                or decision.cron_daemon_enabled
                or decision.scheduler_enabled
                or decision.recurring_execution_enabled
                or decision.side_effects_allowed
                or decision.shell_execution_allowed
                or decision.network_access_allowed
                or decision.browser_automation_allowed
                or decision.plugin_execution_allowed
                or decision.memory_write_allowed
                or decision.context_injection_allowed
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.production_authority_granted
                or not decision.receipt_plan.store_safe_refs_only
                or decision.receipt_plan.store_raw_payload
                or decision.receipt_plan.recurrence_runtime_started
                or decision.receipt_plan.background_worker_started
                or decision.receipt_plan.cron_daemon_started
                or decision.receipt_plan.scheduler_started
                or decision.receipt_plan.recurring_execution_performed
                or "M97_RECURRING_AUTOMATION_CONTRACT_READY_DISABLED"
                not in decision.reason_codes
                or "M98_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M97 recurring automation decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"recurrence_runtime_enabled": True}, "RECURRENCE_RUNTIME_DENIED"),
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                ({"cron_daemon_enabled": True}, "CRON_DAEMON_DENIED"),
                ({"scheduler_enabled": True}, "SCHEDULER_DENIED"),
                ({"production_authority_granted": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_recurring_automation_contract_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M97 unsafe decision mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M97 unsafe decision mutation raised {exc!s}")
        except Exception as exc:
            failures.append(
                f"M97 recurring automation contract validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "recurring automation contracts",
            "contract-only",
            "disabled by default",
            "approval renewal required",
            "expiration required",
            "stop conditions required",
            "no recurrence runtime",
            "no background execution",
            "no cron",
            "no daemon",
            "no scheduler",
            "no side effects",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
            "m98 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M97 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m97_recurring_automation_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "recurrence_runtime_allowed=True",
            "background_worker_allowed=True",
            "cron_daemon_allowed=True",
            "scheduler_allowed=True",
            "actual_recurring_execution_allowed=True",
            "side_effects_allowed=True",
            "shell_execution_allowed=True",
            "network_access_allowed=True",
            "browser_automation_allowed=True",
            "plugin_execution_allowed=True",
            "memory_write_allowed=True",
            "context_injection_allowed=True",
            "backend_route_allowed=True",
            "control_center_control_allowed=True",
            "dependency_change_allowed=True",
            "production_authority_allowed=True",
            "recurrence_runtime_requested=True",
            "background_worker_requested=True",
            "cron_daemon_requested=True",
            "scheduler_requested=True",
            "actual_recurring_execution_requested=True",
            "background_worker_enabled=True",
            "cron_daemon_enabled=True",
            "scheduler_enabled=True",
            "recurring_execution_enabled=True",
            "recurrence_runtime_started=True",
            "background_worker_started=True",
            "cron_daemon_started=True",
            "scheduler_started=True",
            "recurring_execution_performed=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/recurring_automation_contracts/__init__.py",
            "src/ultimate_ai_agent/core/recurring_automation_contracts/contracts.py",
        }
        allowed_fragments_by_file = {
            "src/ultimate_ai_agent/core/decision_router/turn_contracts.py": {
                "side_effects_allowed=True",
            },
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
                    if (
                        fragment in text
                        and fragment not in allowed_fragments_by_file.get(rel, set())
                    ):
                        failures.append(
                            f"M97 forbidden recurring automation fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m97_recurring_automation_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m97_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M97 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m97_roadmap_currentness(
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
            f"missing M97 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v1.1.0" not in text
            or "m97" not in text
            or "recurring automation contracts" not in text
        ):
            failures.append(
                "active docs do not identify v1.1.0/M97 Recurring Automation Contracts"
            )
        if (
            "m97 is implemented/released" not in text
            and "v1.1.0 implements m97" not in text
        ):
            failures.append("active docs do not mark M97 implemented/released")
        for version_label, milestone, title in [
            ("v1.2.0", "M98", "Scoped Recurring Low-Risk Automation"),
            ("v1.3.0", "M99", "Autonomy v1 Safety Freeze"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M98-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "recurrence runtime is implemented",
            "background worker is implemented",
            "cron daemon is implemented",
            "scheduler is implemented",
            "recurring execution is implemented",
            "mobile permission runtime is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M97 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m98_scoped_recurring_low_risk_automation(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/scoped_recurring_low_risk_automation/__init__.py",
            "src/ultimate_ai_agent/core/scoped_recurring_low_risk_automation/contracts.py",
            "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION.md",
            "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_POLICY.md",
            "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_AUTHORITY_BOUNDARY.md",
            "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_RECEIPT_PLAN.md",
            "docs/automation/SCOPED_RECURRING_LOW_RISK_AUTOMATION_NON_GOALS.md",
            "docs/automation/M98_TO_M99_BOUNDARY.md",
            "tests/test_m98_scoped_recurring_low_risk_automation.py",
            "tests/test_m98_gate_integration.py",
        ]
        failures = [
            f"missing M98 scoped recurring low-risk automation file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m98_scoped_recurring_low_risk_automation import _request
            from ultimate_ai_agent.core.scoped_recurring_low_risk_automation import (
                ScopedRecurringLowRiskAutomationStatus,
                build_scoped_recurring_low_risk_automation_decision,
                validate_scoped_recurring_low_risk_automation_decision,
            )

            decision = build_scoped_recurring_low_risk_automation_decision(_request())
            if (
                decision.status
                != ScopedRecurringLowRiskAutomationStatus.scoped_low_risk_ready_for_review
                or not decision.low_risk_only
                or not decision.read_only_only
                or not decision.strict_cadence_required
                or not decision.renewal_required
                or not decision.renewal_not_expired
                or not decision.stop_conditions_required
                or not decision.audit_required
                or not decision.revocation_required
                or not decision.kill_switch_required
                or not decision.kill_switch_available
                or not decision.no_secret_access
                or not decision.safe_refs_only
                or decision.runtime_started
                or decision.scheduler_enabled
                or decision.background_worker_enabled
                or decision.recurring_execution_performed
                or decision.secret_access_performed
                or decision.memory_write_performed
                or decision.context_injection_performed
                or decision.export_performed
                or decision.backend_route_added
                or decision.control_center_control_added
                or decision.dependency_added
                or decision.production_authority_granted
                or not decision.receipt_plan.store_safe_refs_only
                or decision.receipt_plan.store_raw_payload
                or decision.receipt_plan.scheduler_started
                or decision.receipt_plan.background_worker_started
                or decision.receipt_plan.recurring_execution_performed
                or decision.receipt_plan.secret_access_performed
                or "M98_SCOPED_RECURRING_LOW_RISK_READY_FOR_REVIEW"
                not in decision.reason_codes
                or "M99_REMAINS_FUTURE" not in decision.reason_codes
            ):
                failures.append(
                    "M98 scoped recurring low-risk decision is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"scheduler_enabled": True}, "SCHEDULER_DENIED"),
                ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
                ({"secret_access_performed": True}, "SECRET_ACCESS_DENIED"),
                ({"production_authority_granted": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_scoped_recurring_low_risk_automation_decision(
                        decision.model_copy(update=update)
                    )
                    failures.append(
                        f"M98 unsafe decision mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M98 unsafe decision mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M98 scoped recurring low-risk validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "scoped recurring low-risk automation",
            "low-risk read-only",
            "strict cadence",
            "approval renewal required",
            "renewal expiry",
            "stop conditions required",
            "kill switch",
            "audit trail",
            "revocation",
            "no scheduler",
            "no background worker",
            "no recurring execution runtime",
            "no mutating tasks",
            "no credential or account actions",
            "no shell write",
            "no network write",
            "no browser write",
            "no silent background collection",
            "no secret access",
            "no backend route",
            "no dependency",
            "no production authority",
            "evaluator boundaries revalidate",
            "m99 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M98 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m98_scoped_recurring_low_risk_automation_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "runtime_allowed=True",
            "scheduler_allowed=True",
            "background_worker_allowed=True",
            "recurring_execution_allowed=True",
            "mutating_tasks_allowed=True",
            "credential_access_allowed=True",
            "secret_access_allowed=True",
            "account_actions_allowed=True",
            "shell_write_allowed=True",
            "network_write_allowed=True",
            "browser_write_allowed=True",
            "silent_background_collection_allowed=True",
            "runtime_requested=True",
            "scheduler_requested=True",
            "background_worker_requested=True",
            "recurring_execution_requested=True",
            "mutating_task_requested=True",
            "credential_access_requested=True",
            "account_action_requested=True",
            "shell_write_requested=True",
            "network_write_requested=True",
            "browser_write_requested=True",
            "silent_background_collection_requested=True",
            "runtime_started=True",
            "scheduler_enabled=True",
            "background_worker_enabled=True",
            "scheduler_started=True",
            "background_worker_started=True",
            "recurring_execution_performed=True",
            "secret_access_performed=True",
            "production_authority_granted=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/scoped_recurring_low_risk_automation/__init__.py",
            "src/ultimate_ai_agent/core/scoped_recurring_low_risk_automation/contracts.py",
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
                            f"M98 forbidden recurring automation fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m98_scoped_recurring_low_risk_automation_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m98_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M98 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m98_roadmap_currentness(
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
            f"missing M98 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v1.2.0" not in text
            or "m98" not in text
            or "scoped recurring low-risk automation" not in text
        ):
            failures.append(
                "active docs do not identify v1.2.0/M98 Scoped Recurring Low-Risk Automation"
            )
        if (
            "m98 is implemented/released" not in text
            and "v1.2.0 implements m98" not in text
        ):
            failures.append("active docs do not mark M98 implemented/released")
        for version_label, milestone, title in [
            ("v1.3.0", "M99", "Autonomy v1 Safety Freeze"),
            ("v1.4.0", "M100", "Mobile Permission Model v1"),
        ]:
            if (
                version_label.lower() not in text
                or milestone.lower() not in text
                or title.lower() not in text
            ):
                failures.append(
                    f"active docs missing planned M99-M100 row: {version_label} / {milestone} — {title}"
                )
        for fragment in (
            "scheduler is implemented",
            "background worker is implemented",
            "cron daemon is implemented",
            "recurring execution runtime is implemented",
            "mutating recurring task is implemented",
            "credential account automation is implemented",
            "mobile permission runtime is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M98 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
