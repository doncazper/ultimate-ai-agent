from pathlib import Path
import json
import re
from typing import Callable, Dict, Iterable, List, Optional

from pydantic import ValidationError

from ultimate_ai_agent.core.consent import ConsentLedger
from ultimate_ai_agent.core.consent.enums import DataBoundary
from ultimate_ai_agent.core.files import FileKind, FileRef, FileSensitivity
from ultimate_ai_agent.core.gate.criteria import FoundationGateCriterion, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.reports import FoundationGateReport, FoundationGateResult, build_foundation_gate_report
from ultimate_ai_agent.core.gate.shadow_replay import run_m5_shadow_replay
from ultimate_ai_agent.core.context_budget import ContextBudget
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.costs import BudgetScope, BudgetStatus, CostBudget, CostEstimate, CostGovernor
from ultimate_ai_agent.core.model_router import (
    ModelCapabilityProfile,
    ModelPrivacyClass,
    ModelProviderKind,
    ModelRouteStatus,
    ModelRouter,
    ModelRouteRequest,
    ModelRoutingPolicy,
    ModelTaskCapability,
)
from ultimate_ai_agent.core.memory import MemoryRecord
from ultimate_ai_agent.core.memory.enums import MemoryAuthority, MemoryScope, MemorySensitivity, MemoryType
from ultimate_ai_agent.core.memory.records import MemorySourceRef
from ultimate_ai_agent.core.tools import (
    CapabilityFirewallPolicy,
    ToolBroker,
    ToolCategory,
    ToolDecisionStatus,
    ToolExecutionMode,
    ToolManifest,
    ToolRegistry,
    ToolRequest,
    ToolRiskLevel,
)
from ultimate_ai_agent.core.truth import EvidenceItem, EvidenceManifest, TruthSourceManifest
from ultimate_ai_agent.core.truth.claims import ClaimEvidence
from ultimate_ai_agent.core.truth.enums import (
    ClaimVerificationStatus,
    SourceFreshnessStatus,
    TruthAuthorityLevel,
    TruthSourceType,
)


class FoundationGateEvaluator:
    def __init__(self, root: Optional[Path] = None):
        self.root = root or Path(__file__).resolve().parents[4]
        self.src_root = self.root / "src" / "ultimate_ai_agent"

    def evaluate(self, criteria: Optional[List[FoundationGateCriterion]] = None) -> FoundationGateReport:
        criteria = criteria or default_foundation_gate_criteria()
        evaluator_map: Dict[str, Callable[[FoundationGateCriterion], FoundationGateResult]] = {
            "versioning_consistent": self.check_versioning_consistent,
            "release_docs_present": self.check_release_docs_present,
            "foundation_modules_present": self.check_foundation_modules_present,
            "blocked_modules_absent": self.check_blocked_modules_absent,
            "forbidden_runtime_integrations_absent": self.check_forbidden_runtime_integrations_absent,
            "shell_execution_absent": self.check_shell_execution_absent,
            "broad_filesystem_scanning_absent": self.check_broad_filesystem_scanning_absent,
            "secret_hygiene_clean": self.check_secret_hygiene_clean,
            "tool_broker_blocks_advanced_adapters": self.check_tool_broker_blocks_advanced_adapters,
            "truth_evidence_contracts_valid": self.check_truth_evidence_contracts_valid,
            "memory_file_contracts_valid": self.check_memory_file_contracts_valid,
            "m5_shadow_replay_passes": self.check_m5_shadow_replay_passes,
            "m7_modules_present": self.check_m7_modules_present,
            "model_router_decision_only": self.check_model_router_decision_only,
            "cost_governor_blocks_over_budget": self.check_cost_governor_blocks_over_budget,
            "m7_arbitrary_approval_ref_rejected": self.check_m7_arbitrary_approval_ref_rejected,
            "m7_context_budget_exhaustion_blocks_route": self.check_m7_context_budget_exhaustion_blocks_route,
            "m7_soft_budget_warning_allows_route": self.check_m7_soft_budget_warning_allows_route,
            "m7_hard_budget_denies_route": self.check_m7_hard_budget_denies_route,
            "m7_cost_warnings_visible_in_route_decision": self.check_m7_cost_warnings_visible_in_route_decision,
            "api_manifest_endpoint_present": self.check_api_manifest_endpoint_present,
            "openapi_contract_valid": self.check_openapi_contract_valid,
            "api_operation_ids_unique": self.check_api_operation_ids_unique,
            "forbidden_runtime_routes_absent": self.check_forbidden_runtime_routes_absent,
            "agents_md_guidance_present": self.check_agents_md_guidance_present,
            "runtime_agent_config_loading_absent": self.check_runtime_agent_config_loading_absent,
            "m8_model_runtime_files_present": self.check_m8_model_runtime_files_present,
            "m8_runtime_kinds_stub_only": self.check_m8_runtime_kinds_stub_only,
            "m8_model_runtime_no_real_calls": self.check_m8_model_runtime_no_real_calls,
            "m8_simulation_endpoint_safe": self.check_m8_simulation_endpoint_safe,
            "m8_runtime_responses_simulated_only": self.check_m8_runtime_responses_simulated_only,
            "m8_runtime_secret_prompt_blocked": self.check_m8_runtime_secret_prompt_blocked,
            "m8_api_validation_secret_echo_absent": self.check_m8_api_validation_secret_echo_absent,
            "m85_approval_authority_files_present": self.check_m85_approval_authority_files_present,
            "m85_arbitrary_approval_refs_rejected": self.check_m85_arbitrary_approval_refs_rejected,
            "m85_local_approval_grant_validates": self.check_m85_local_approval_grant_validates,
            "m85_expired_revoked_approval_denies": self.check_m85_expired_revoked_approval_denies,
            "m85_router_uses_valid_approval_grant": self.check_m85_router_uses_valid_approval_grant,
            "m85_runtime_factory_rejects_arbitrary_approval": self.check_m85_runtime_factory_rejects_arbitrary_approval,
            "m85_tool_broker_rejects_arbitrary_approval": self.check_m85_tool_broker_rejects_arbitrary_approval,
            "m85_no_real_auth_oauth_network": self.check_m85_no_real_auth_oauth_network,
            "m85_approval_api_secret_echo_absent": self.check_m85_approval_api_secret_echo_absent,
            "m9_loopback_runtime_files_present": self.check_m9_loopback_runtime_files_present,
            "m9_non_loopback_endpoints_denied": self.check_m9_non_loopback_endpoints_denied,
            "m9_non_loopback_policy_override_denied": self.check_m9_non_loopback_policy_override_denied,
            "m9_loopback_policy_model_rejects_hostile_inputs": self.check_m9_loopback_policy_model_rejects_hostile_inputs,
            "m9_public_and_private_ip_endpoints_denied": self.check_m9_public_and_private_ip_endpoints_denied,
            "m9_approval_api_uses_public_authority_helper": self.check_m9_approval_api_uses_public_authority_helper,
            "m9_arbitrary_approval_refs_denied": self.check_m9_arbitrary_approval_refs_denied,
            "m9_fake_transport_only_in_gate": self.check_m9_fake_transport_only_in_gate,
            "m9_simulated_fallback_available": self.check_m9_simulated_fallback_available,
            "m9_model_output_not_truth_authority": self.check_m9_model_output_not_truth_authority,
            "m10_manual_smoke_files_present": self.check_m10_manual_smoke_files_present,
            "m10_stdlib_network_isolated": self.check_m10_stdlib_network_isolated,
            "m10_gate_and_verify_do_not_call_smoke_script": self.check_m10_gate_and_verify_do_not_call_smoke_script,
            "m10_public_api_has_no_smoke_execute_endpoint": self.check_m10_public_api_has_no_smoke_execute_endpoint,
            "m10_fixed_prompt_and_loopback_policy_enforced": self.check_m10_fixed_prompt_and_loopback_policy_enforced,
            "m10_smoke_approval_required": self.check_m10_smoke_approval_required,
            "m10_smoke_response_not_truth_authority": self.check_m10_smoke_response_not_truth_authority,
            "m105_remote_worker_files_present": self.check_m105_remote_worker_files_present,
            "m105_remote_capabilities_default_safe": self.check_m105_remote_capabilities_default_safe,
            "m105_unknown_node_and_transport_denied": self.check_m105_unknown_node_and_transport_denied,
            "m105_planned_transports_disabled": self.check_m105_planned_transports_disabled,
            "m105_dry_run_dispatches_nothing": self.check_m105_dry_run_dispatches_nothing,
            "m105_no_remote_network_or_background_execution": self.check_m105_no_remote_network_or_background_execution,
            "m105_no_remote_subagents_tools_or_approvals": self.check_m105_no_remote_subagents_tools_or_approvals,
            "m105_remote_output_untrusted": self.check_m105_remote_output_untrusted,
            "m105_api_routes_are_dry_run_only": self.check_m105_api_routes_are_dry_run_only,
            "m105_docs_foundation_only": self.check_m105_docs_foundation_only,
            "m105_remote_tailnet_enable_flag_rejected": self.check_m105_remote_tailnet_enable_flag_rejected,
            "m105_remote_personal_data_enable_flag_rejected": self.check_m105_remote_personal_data_enable_flag_rejected,
            "m105_remote_worker_api_extra_fields_forbidden": self.check_m105_remote_worker_api_extra_fields_forbidden,
            "m143_private_mesh_taxonomy_open_source_first": self.check_m143_private_mesh_taxonomy_open_source_first,
            "m143_planned_mesh_transports_disabled": self.check_m143_planned_mesh_transports_disabled,
            "m143_no_live_mesh_integrations": self.check_m143_no_live_mesh_integrations,
            "m11_runtime_readiness_files_present": self.check_m11_runtime_readiness_files_present,
            "m11_runtime_capability_matrix_safe": self.check_m11_runtime_capability_matrix_safe,
            "m11_manual_smoke_report_validation_safe": self.check_m11_manual_smoke_report_validation_safe,
            "m11_no_production_readiness_claim": self.check_m11_no_production_readiness_claim,
            "m11_runtime_api_status_validation_only": self.check_m11_runtime_api_status_validation_only,
            "m11_no_smoke_script_execution_in_gate": self.check_m11_no_smoke_script_execution_in_gate,
            "m11_no_runtime_expansion_imports": self.check_m11_no_runtime_expansion_imports,
            "m11_no_remote_mesh_mobile_or_plugin_enablement": self.check_m11_no_remote_mesh_mobile_or_plugin_enablement,
            "m12_control_center_files_present": self.check_m12_control_center_files_present,
            "m12_control_center_manifest_read_only": self.check_m12_control_center_manifest_read_only,
            "m12_control_center_dashboard_secret_safe": self.check_m12_control_center_dashboard_secret_safe,
            "m12_control_center_action_preview_no_execution": self.check_m12_control_center_action_preview_no_execution,
            "m12_control_center_api_read_only": self.check_m12_control_center_api_read_only,
            "m12_no_frontend_dependencies": self.check_m12_no_frontend_dependencies,
            "m12_no_runtime_network_mobile_plugin_expansion": self.check_m12_no_runtime_network_mobile_plugin_expansion,
            "m13_web_control_center_files_present": self.check_m13_web_control_center_files_present,
            "m13_web_shell_read_only_preview_only": self.check_m13_web_shell_read_only_preview_only,
            "m13_action_preview_ui_posts_only_to_preview": self.check_m13_action_preview_ui_posts_only_to_preview,
            "m13_mock_data_safe_non_authoritative": self.check_m13_mock_data_safe_non_authoritative,
            "m13_no_tracked_generated_or_native_artifacts": self.check_m13_no_tracked_generated_or_native_artifacts,
            "m13_backend_api_contract_unchanged": self.check_m13_backend_api_contract_unchanged,
            "m13_frontend_no_sensitive_browser_apis": self.check_m13_frontend_no_sensitive_browser_apis,
            "m13_control_center_frontend_safety_verifier_passes": self.check_m13_control_center_frontend_safety_verifier_passes,
            "documentation_integrity_current": self.check_documentation_integrity_current,
            "codex_plugin_governance_docs_present": self.check_codex_plugin_governance_docs_present,
        }
        results = [
            evaluator_map.get(criterion.criterion_id, self._skipped)(criterion)
            for criterion in criteria
        ]
        version = self._active_version() or "unknown"
        return build_foundation_gate_report(version=version, results=results, trace_id="trace_foundation_gate")

    def check_versioning_consistent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        version = self._active_version()
        if not version:
            failures.append("VERSION.md active baseline missing")
        else:
            pyproject_version = self._regex_first(self.root / "pyproject.toml", r"(?m)^version\s*=\s*['\"]([^'\"]+)['\"]")
            init_version = self._regex_first(
                self.root / "src/ultimate_ai_agent/__init__.py",
                r"(?m)^__version__\s*=\s*['\"]([^'\"]+)['\"]",
            )
            readme = self._read(self.root / "README.md")
            expected_underscored = version.replace(".", "_")
            if pyproject_version != version:
                failures.append("pyproject.toml version mismatch")
            if init_version != version:
                failures.append("package __version__ mismatch")
            if f"v{version}" not in readme:
                failures.append("README.md missing active version")
            if f"README_IMPORT_v{expected_underscored}.md" not in readme:
                failures.append("README.md missing active import README")
            if f"ultimate_ai_agent_master_plan_v{expected_underscored}.md" not in readme:
                failures.append("README.md missing active master plan")
        return self._result(criterion, failures, ["VERSION.md", "pyproject.toml", "README.md"])

    def check_release_docs_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        version = self._active_version()
        version_key = (version or "0.0.0").replace(".", "_")
        required = [
            f"README_IMPORT_v{version_key}.md",
            f"ultimate_ai_agent_master_plan_v{version_key}.md",
            f"docs/release_notes/v{version_key}.md",
            f"docs/implementation/foundation_gate_implementation_plan_v{version_key}.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_foundation_modules_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/contracts/execution_contract.py",
            "src/ultimate_ai_agent/core/contracts/context_pack.py",
            "src/ultimate_ai_agent/core/ledger/events.py",
            "src/ultimate_ai_agent/core/world_state/models.py",
            "src/ultimate_ai_agent/core/context_budget/models.py",
            "src/ultimate_ai_agent/core/runtime/local_runtime.py",
            "src/ultimate_ai_agent/core/adapters/sdk_manifest.py",
            "src/ultimate_ai_agent/core/consent/grants.py",
            "src/ultimate_ai_agent/core/tools/broker.py",
            "src/ultimate_ai_agent/core/secrets/broker.py",
            "src/ultimate_ai_agent/core/providers/registry.py",
            "src/ultimate_ai_agent/core/memory/store.py",
            "src/ultimate_ai_agent/core/files/manager.py",
            "src/ultimate_ai_agent/core/truth/evidence.py",
            "src/ultimate_ai_agent/core/kernel/runner.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/gate/shadow_replay.py",
            "scripts/run_foundation_gate.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m7_modules_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_router/__init__.py",
            "src/ultimate_ai_agent/core/model_router/enums.py",
            "src/ultimate_ai_agent/core/model_router/profiles.py",
            "src/ultimate_ai_agent/core/model_router/policies.py",
            "src/ultimate_ai_agent/core/model_router/requests.py",
            "src/ultimate_ai_agent/core/model_router/decisions.py",
            "src/ultimate_ai_agent/core/model_router/router.py",
            "src/ultimate_ai_agent/core/model_router/validation.py",
            "src/ultimate_ai_agent/core/costs/__init__.py",
            "src/ultimate_ai_agent/core/costs/enums.py",
            "src/ultimate_ai_agent/core/costs/budgets.py",
            "src/ultimate_ai_agent/core/costs/estimates.py",
            "src/ultimate_ai_agent/core/costs/decisions.py",
            "src/ultimate_ai_agent/core/costs/governor.py",
            "src/ultimate_ai_agent/core/costs/validation.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_blocked_modules_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        blocked_paths = [
            "src/ultimate_ai_agent/core/scanners",
            "src/ultimate_ai_agent/core/companion",
            "src/ultimate_ai_agent/core/skill_factory",
            "src/ultimate_ai_agent/core/self_improvement",
            "src/ultimate_ai_agent/core/autopilot",
            "src/ultimate_ai_agent/core/browser_automation",
            "src/ultimate_ai_agent/core/sdk_runtime_delegation",
            "src/ultimate_ai_agent/core/a2a_runtime_delegation",
        ]
        failures = [f"blocked module exists: {path}" for path in blocked_paths if (self.root / path).exists()]
        return self._result(criterion, failures, blocked_paths)

    def check_forbidden_runtime_integrations_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden_starts = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "urllib.request",
            "from " + "urllib import request",
            "import " + "boto3",
            "import " + "ollama",
            "import " + "vllm",
            "import " + "llama_cpp",
            "import " + "sglang",
            "import " + "openai",
            "import " + "anthropic",
            "import " + "google.generativeai",
            "import " + "chromadb",
            "import " + "faiss",
            "import " + "pgvector",
            "import " + "pinecone",
            "import " + "psycopg",
            "import " + "sentence_transformers",
            "import " + "weaviate",
        ]
        forbidden_contains = [
            "from " + "openai import",
            "from " + "anthropic import",
            "http" + "://",
            "https" + "://",
        ]
        failures = []
        allowed_manual_smoke_network_files = {
            "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
        }
        for path, line_no, stripped in self._runtime_lines():
            if self._is_static_scanner_text(stripped):
                continue
            if any(stripped.startswith(pattern) for pattern in forbidden_starts):
                if path in allowed_manual_smoke_network_files and stripped.startswith(
                    ("import urllib.request", "from urllib import request", "from urllib import error")
                ):
                    continue
                failures.append(f"{path}:{line_no} forbidden import")
            if any(pattern in stripped for pattern in forbidden_contains):
                failures.append(f"{path}:{line_no} forbidden integration reference")
            if ".get(" in stripped and any(marker in stripped for marker in forbidden_contains[-2:]):
                failures.append(f"{path}:{line_no} possible network call")
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_shell_execution_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden = [
            "import " + "subprocess",
            "from " + "subprocess import",
            "os." + "system(",
            "po" + "pen(",
            "sub" + "process.",
        ]
        failures = [
            f"{path}:{line_no} shell execution"
            for path, line_no, stripped in self._runtime_lines()
            if not self._is_static_scanner_text(stripped) and any(fragment in stripped for fragment in forbidden)
        ]
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_broad_filesystem_scanning_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden = [
            ".rglob(" + '"*"' + ")",
            ".rglob(" + "'*'" + ")",
            "os." + "walk(",
            "Path." + "home(",
        ]
        failures = [
            f"{path}:{line_no} broad filesystem scan"
            for path, line_no, stripped in self._runtime_lines()
            if not self._is_static_scanner_text(stripped) and any(fragment in stripped for fragment in forbidden)
        ]
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_secret_hygiene_clean(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        secret_assignment = re.compile(
            r"(?i)(api_key|password|client_secret|private_key|token|auth_token)\s*=\s*['\"][A-Za-z0-9_\-.:/]{16,}['\"]"
        )
        failures = []
        private_key_begin = "-----" + "BEGIN"
        private_key_end = "PRIVATE" + " KEY-----"
        for rel_path in self._tracked_runtime_files():
            content = self._read(self.root / rel_path)
            if private_key_begin in content and private_key_end in content:
                failures.append(f"{rel_path}: private key header")
            for match in secret_assignment.finditer(content):
                value = match.group(0).lower()
                if any(
                    marker in value
                    for marker in ["mock", "dummy", "example", "placeholder", "oauth_refresh_token", "token_secret"]
                ):
                    continue
                failures.append(f"{rel_path}: secret-like assignment")
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_tool_broker_blocks_advanced_adapters(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        for category in (ToolCategory.mcp, ToolCategory.a2a, ToolCategory.sdk_adapter, ToolCategory.skill):
            registry = ToolRegistry()
            tool_id = f"{category.value}.gate_check"
            registry.register_tool(
                ToolManifest(
                    tool_id=tool_id,
                    display_name="Gate Check",
                    category=category,
                    description="Foundation Gate category block check.",
                    execution_mode=ToolExecutionMode.mock,
                    risk_level=ToolRiskLevel.low,
                    capability_flag=f"{category.value}_gate_check",
                    owner="core.gate",
                    source="local",
                    version="0.0.0",
                )
            )
            decision = ToolBroker(registry, CapabilityFirewallPolicy()).evaluate_request(
                ToolRequest(
                    request_id=f"req_{category.value}_gate",
                    run_id="run_foundation_gate",
                    tool_id=tool_id,
                    actor_context=self._actor(),
                    requested_action="execute",
                    purpose="foundation_gate_check",
                    data_classification=DataBoundary.project_private,
                ),
                ConsentLedger(),
            )
            if decision.status != ToolDecisionStatus.blocked_by_foundation_gate:
                failures.append(f"{category.value} was not blocked")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/tools/broker.py"])

    def check_truth_evidence_contracts_valid(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        try:
            source = TruthSourceManifest(
                source_id="truth_gate",
                source_type=TruthSourceType.canonical_file,
                authority_level=TruthAuthorityLevel.authoritative,
                display_name="Gate Truth Source",
                owner="core.gate",
                data_classification="project_private",
            )
            item = EvidenceItem(
                evidence_id="evidence_gate",
                source_id=source.source_id,
                source_type=TruthSourceType.canonical_file,
                summary="Gate evidence contract check.",
                freshness_status=SourceFreshnessStatus.current,
            )
            claim = ClaimEvidence(
                claim_id="claim_gate",
                claim_text="Foundation Gate is verification only.",
                verification_status=ClaimVerificationStatus.supported,
                evidence_refs=[item.evidence_id],
                source_ids=[source.source_id],
                freshness_status=SourceFreshnessStatus.current,
            )
            EvidenceManifest(
                manifest_id="evm_gate",
                run_id="run_foundation_gate",
                claims=[claim],
                evidence_items=[item],
            )
        except (ValidationError, ValueError) as exc:
            failures.append(str(exc))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/truth"])

    def check_memory_file_contracts_valid(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        try:
            MemoryRecord(
                memory_id="mem_gate",
                memory_type=MemoryType.artifact_summary,
                scope=MemoryScope.project,
                scope_id="workspace_gate",
                authority=MemoryAuthority.event_ledger_derived,
                sensitivity=MemorySensitivity.project_private,
                content="Recall only: gate check. Canonical files and event ledger outrank memory.",
                source_refs=[
                    MemorySourceRef(
                        source_id="notes/m5.md",
                        source_type="file_change",
                        file_ref="notes/m5.md",
                        event_ref="evt_gate",
                    )
                ],
            )
            FileRef(
                file_ref="file_gate",
                path="notes/m5.md",
                kind=FileKind.generated,
                sensitivity=FileSensitivity.project_private,
                source_event_ref="evt_gate",
            )
        except (ValidationError, ValueError) as exc:
            failures.append(str(exc))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/memory", "src/ultimate_ai_agent/core/files"])

    def check_m5_shadow_replay_passes(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        replay = run_m5_shadow_replay()
        failures = list(replay.failures)
        warnings = list(replay.warnings)
        if not replay.passed and not failures:
            failures.append("shadow replay did not pass")
        status = FoundationGateStatus.passed if not failures else FoundationGateStatus.failed
        return FoundationGateResult(
            criterion_id=criterion.criterion_id,
            status=status,
            safe_message="M5 shadow replay passed." if status == FoundationGateStatus.passed else criterion.failure_message,
            evidence_refs=[*replay.event_ids, replay.receipt_ref or "receipt_missing"],
            failures=failures,
            warnings=warnings,
        )

    def check_model_router_decision_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        try:
            profile = ModelCapabilityProfile(
                model_profile_id="m7_gate_local",
                provider_kind=ModelProviderKind.local_runtime,
                runtime_id="rt_gate",
                model_id="local_policy_model",
                display_name="Local Policy Model",
                capabilities=[ModelTaskCapability.chat, ModelTaskCapability.coding],
                privacy_class=ModelPrivacyClass.local_only,
                max_context_tokens=8192,
                enabled=True,
                owner="core.gate",
                source="foundation_gate",
                version="0.0.0",
            )
            request = ModelRouteRequest(
                request_id="m7_gate_route",
                run_id="run_foundation_gate",
                actor_context=self._actor(),
                task_class="coding",
                prompt_summary="Foundation Gate model routing metadata check.",
                data_classification=DataClassification(classification=ClassificationValue.project_private, source="foundation_gate"),
                required_capabilities=[ModelTaskCapability.chat],
                estimated_input_tokens=256,
                estimated_output_tokens=128,
                routing_policy=ModelRoutingPolicy(
                    policy_id="m7_gate_policy",
                    required_capabilities=[ModelTaskCapability.chat],
                    prefer_local=True,
                    allow_cloud=False,
                    allow_paid=False,
                ),
                available_profiles=[profile],
            )
            decision = ModelRouter().route(request)
            if decision.status != ModelRouteStatus.selected:
                failures.append(f"route status was {decision.status}")
            if decision.selected_profile_id != profile.model_profile_id:
                failures.append("local policy profile was not selected")
        except (ValidationError, ValueError) as exc:
            failures.append(str(exc))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_router"])

    def check_cost_governor_blocks_over_budget(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        decision = CostGovernor().evaluate(
            CostEstimate(
                estimate_id="m7_gate_estimate",
                input_tokens=100,
                output_tokens=100,
                total_tokens=200,
                estimated_cost_usd=2,
            ),
            [CostBudget(budget_id="m7_gate_budget", scope=BudgetScope.run, max_cost_usd=1)],
        )
        if decision.status != BudgetStatus.denied or decision.allowed:
            failures.append("over-budget route was not denied")
        if "COST_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("cost denial reason missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/costs"])

    def check_m7_arbitrary_approval_ref_rejected(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        profile = self._gate_cloud_profile()
        request = self._gate_route_request(
            profile,
            data_classification=ClassificationValue.sensitive_personal,
            approval_ref="arbitrary-string",
            policy=ModelRoutingPolicy(
                policy_id="m7_gate_approval_policy",
                required_capabilities=[ModelTaskCapability.chat],
                allow_cloud=True,
                allow_paid=True,
                require_human_approval_for_cloud=True,
            ),
        )
        decision = ModelRouter().route(request)
        if decision.status != ModelRouteStatus.approval_required:
            failures.append(f"route status was {decision.status}")
        if decision.selected_profile_id is not None:
            failures.append("arbitrary approval_ref selected a cloud profile")
        if "APPROVAL_REF_UNVALIDATED" not in decision.reason_codes:
            failures.append("unvalidated approval reason missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"])

    def check_m7_context_budget_exhaustion_blocks_route(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        profile = self._gate_local_profile()
        request = self._gate_route_request(
            profile,
            context_budget=ContextBudget(
                model_context_limit=4096,
                system_prompt_tokens=1000,
                tool_schema_tokens=1000,
                world_state_tokens=1000,
                context_pack_tokens=1000,
                completion_reserve_tokens=96,
                safety_margin_tokens=0,
            ),
        )
        decision = ModelRouter().route(request)
        if decision.status != ModelRouteStatus.context_too_small:
            failures.append(f"route status was {decision.status}")
        if decision.selected_profile_id is not None:
            failures.append("exhausted context budget selected a profile")
        if "CONTEXT_BUDGET_EXHAUSTED" not in decision.reason_codes:
            failures.append("context budget exhaustion reason missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"])

    def check_m7_soft_budget_warning_allows_route(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        decision = CostGovernor().evaluate(
            CostEstimate(
                estimate_id="m7_gate_soft_estimate",
                input_tokens=100,
                output_tokens=100,
                total_tokens=200,
                estimated_cost_usd=2,
            ),
            [CostBudget(budget_id="m7_gate_soft_budget", scope=BudgetScope.run, max_cost_usd=1, hard_limit=False)],
        )
        if not decision.allowed or decision.status != BudgetStatus.warning:
            failures.append("soft budget overage was not allowed with warning")
        if "SOFT_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("soft budget reason missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/costs/governor.py"])

    def check_m7_hard_budget_denies_route(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        decision = CostGovernor().evaluate(
            CostEstimate(
                estimate_id="m7_gate_hard_estimate",
                input_tokens=100,
                output_tokens=100,
                total_tokens=200,
                estimated_cost_usd=2,
            ),
            [CostBudget(budget_id="m7_gate_hard_budget", scope=BudgetScope.run, max_cost_usd=1, hard_limit=True)],
        )
        if decision.allowed or decision.status != BudgetStatus.denied:
            failures.append("hard budget overage was not denied")
        if "HARD_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("hard budget reason missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/costs/governor.py"])

    def check_m7_cost_warnings_visible_in_route_decision(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures: List[str] = []
        profile = self._gate_local_profile(cost_per_1k_input_tokens=0.02, cost_per_1k_output_tokens=0.02)
        request = self._gate_route_request(
            profile,
            policy=ModelRoutingPolicy(
                policy_id="m7_gate_soft_route_policy",
                required_capabilities=[ModelTaskCapability.chat],
                prefer_local=True,
                allow_paid=True,
                max_estimated_cost_usd=0.01,
                max_estimated_cost_hard_limit=False,
            ),
        )
        decision = ModelRouter().route(request)
        if decision.status != ModelRouteStatus.selected:
            failures.append(f"route status was {decision.status}")
        if "SOFT_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("soft budget warning was not visible in route decision")
        if "with policy warnings" not in decision.safe_message:
            failures.append("route decision safe_message did not mention warnings")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"])

    def check_api_manifest_endpoint_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import build_api_manifest

        failures: List[str] = []
        manifest = build_api_manifest(app)
        paths = {route.path for route in manifest.routes}
        if "/api/manifest" not in paths:
            failures.append("/api/manifest missing from route inventory")
        if manifest.api_version != (self._active_version() or ""):
            failures.append("manifest api_version does not match active baseline")
        if not manifest.no_runtime_integrations:
            failures.append("manifest does not declare no_runtime_integrations")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/manifest.py", "src/ultimate_ai_agent/api/app.py"])

    def check_openapi_contract_valid(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.openapi import verify_openapi_contract

        status = verify_openapi_contract(app)
        failures = list(status.errors)
        if not status.openapi_generated:
            failures.append("OpenAPI schema was not generated")
        if not status.version_consistent:
            failures.append("OpenAPI version mismatch")
        if not status.route_inventory_valid:
            failures.append("route inventory invalid")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/openapi.py"], status.warnings)

    def check_api_operation_ids_unique(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items

        routes = iter_api_route_items(app)
        operation_ids = [route.operation_id for route in routes]
        duplicates = sorted({operation_id for operation_id in operation_ids if operation_ids.count(operation_id) > 1})
        failures = [f"duplicate operation ID: {operation_id}" for operation_id in duplicates]
        if any(not operation_id for operation_id in operation_ids):
            failures.append("missing operation ID")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/openapi.py"])

    def check_forbidden_runtime_routes_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items
        from ultimate_ai_agent.api.openapi import FORBIDDEN_ROUTE_FRAGMENTS

        failures = []
        for route in iter_api_route_items(app):
            if any(fragment in route.path for fragment in FORBIDDEN_ROUTE_FRAGMENTS):
                failures.append(f"forbidden route: {route.method} {route.path}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/openapi.py"])

    def check_agents_md_guidance_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "AGENTS.md",
            "docs/api/README.md",
            "docs/api/openapi_contract.md",
            "docs/api/route_inventory.md",
            "docs/standards/agents_md_support.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        agents_md = self._read(self.root / "AGENTS.md")
        for marker in ["Ultimate AI Agent", "/api/manifest", "OpenAPI", "Do not add runtime model calls"]:
            if marker not in agents_md:
                failures.append(f"AGENTS.md missing marker: {marker}")
        return self._result(criterion, failures, required)

    def check_runtime_agent_config_loading_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden = [
            "AGENTS" + ".md",
            "agent_config",
            "agent-config",
            "runtime_config",
            "workspace_config",
            "load_agent_config",
        ]
        failures = [
            f"{path}:{line_no} runtime agent config loading reference"
            for path, line_no, stripped in self._runtime_lines()
            if path not in {"src/ultimate_ai_agent/api/openapi.py", "src/ultimate_ai_agent/core/gate/evaluators.py"}
            and not self._is_static_scanner_text(stripped)
            and any(fragment in stripped for fragment in forbidden)
        ]
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_m8_model_runtime_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_runtime/__init__.py",
            "src/ultimate_ai_agent/core/model_runtime/enums.py",
            "src/ultimate_ai_agent/core/model_runtime/manifests.py",
            "src/ultimate_ai_agent/core/model_runtime/requests.py",
            "src/ultimate_ai_agent/core/model_runtime/responses.py",
            "src/ultimate_ai_agent/core/model_runtime/simulator.py",
            "src/ultimate_ai_agent/core/model_runtime/adapters.py",
            "src/ultimate_ai_agent/core/model_runtime/validation.py",
            "src/ultimate_ai_agent/core/model_runtime/redaction.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m8_runtime_kinds_stub_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeKind

        allowed = {"simulated", "local_stub", "cloud_stub", "openai_compatible_stub", "sdk_adapter_stub"}
        actual = {kind.value for kind in ModelRuntimeKind}
        failures = [f"unexpected runtime kind: {kind}" for kind in sorted(actual - allowed)]
        missing = allowed - actual
        failures.extend(f"missing runtime kind: {kind}" for kind in sorted(missing))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/enums.py"])

    def check_m8_model_runtime_no_real_calls(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        runtime_root = self.src_root / "core" / "model_runtime"
        forbidden = [
            "import " + "openai",
            "from " + "openai import",
            "import " + "anthropic",
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "socket",
            "sub" + "process",
            "token" + "izer",
            "tiktoken",
            "sentencepiece",
            "bill" + "ing",
            "api" + "_key",
            "API" + "_KEY",
        ]
        failures = []
        for path in sorted(runtime_root.rglob("*.py")):
            rel_path = str(path.relative_to(self.root))
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(f"{rel_path}:{line_no} real runtime fragment")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime"])

    def check_m8_simulation_endpoint_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app

        schema = app.openapi()
        failures = []
        route = schema.get("paths", {}).get("/model-runtime/simulate", {}).get("post")
        if not route:
            failures.append("/model-runtime/simulate missing")
        elif route.get("operationId") != "post_model_runtime_simulate":
            failures.append("simulate endpoint operation ID is not stable")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m8_runtime_responses_simulated_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import (
            ModelRuntimeOutputFormat,
            ModelRuntimeResponse,
            ModelRuntimeResponseStatus,
            response_is_truth_authority,
        )

        failures = []
        response = ModelRuntimeResponse(
            runtime_response_id="m8_gate_response",
            runtime_request_id="m8_gate_request",
            run_id="run_foundation_gate",
            status=ModelRuntimeResponseStatus.simulated_success,
            output_format=ModelRuntimeOutputFormat.text,
            output_summary="Simulated response for request m8_gate_request; no model was called.",
            model_profile_id="m8_gate_profile",
            adapter_id="m8_gate_adapter",
            metadata={"simulated": True, "truth_authority": False},
        )
        if response.status != ModelRuntimeResponseStatus.simulated_success:
            failures.append("response status was not simulated_success")
        if response_is_truth_authority(response):
            failures.append("response became truth authority")
        if "no model was called" not in response.output_summary:
            failures.append("simulated response marker missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/responses.py"])

    def check_m8_runtime_secret_prompt_blocked(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeOutputFormat, ModelRuntimeRequest, ModelRuntimeSafetyMode

        failures = []
        try:
            ModelRuntimeRequest(
                runtime_request_id="m8_gate_secret_request",
                run_id="run_foundation_gate",
                model_profile_id="m8_gate_profile",
                model_id="m8_gate_model",
                adapter_id="m8_gate_adapter",
                actor_context=self._actor(),
                prompt_summary="api_" + "key='ABCDEFGHIJKLMNOP'",
                input_refs=["context_pack:m8_gate"],
                output_format=ModelRuntimeOutputFormat.text,
                estimated_input_tokens=10,
                max_output_tokens=10,
                safety_mode=ModelRuntimeSafetyMode.simulated,
                data_classification=DataClassification(
                    classification=ClassificationValue.project_private,
                    source="foundation_gate",
                ),
            )
            failures.append("secret-like prompt summary was accepted")
        except (ValidationError, ValueError):
            pass
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/requests.py"])

    def check_m8_api_validation_secret_echo_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from fastapi.testclient import TestClient

        from ultimate_ai_agent.api.app import app

        failures = []
        client = TestClient(app)
        secret = "sk_" + "test_" + "secret_" + "value"
        assignment = "api_" + "key=" + secret
        manifest = self._m8_gate_manifest()
        manifest_with_secret = {**manifest, "metadata": {"note": assignment}}
        request = self._m8_gate_request()
        cases = [
            ("/model-runtime/manifests/validate", manifest_with_secret),
            ("/model-runtime/manifests/validate", {**manifest, "api_" + "key": secret}),
            ("/model-runtime/requests/validate", {"request": request, "manifest": manifest_with_secret}),
            ("/model-runtime/simulate", {"request": request, "manifest": manifest_with_secret}),
        ]
        for path, payload in cases:
            response = client.post(path, json=payload)
            if response.status_code not in {200, 422}:
                failures.append(f"{path} returned unexpected status {response.status_code}")
            if secret in response.text or assignment in response.text:
                failures.append(f"{path} echoed secret-like input")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m85_approval_authority_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/approvals/__init__.py",
            "src/ultimate_ai_agent/core/approvals/enums.py",
            "src/ultimate_ai_agent/core/approvals/requests.py",
            "src/ultimate_ai_agent/core/approvals/grants.py",
            "src/ultimate_ai_agent/core/approvals/decisions.py",
            "src/ultimate_ai_agent/core/approvals/authority.py",
            "src/ultimate_ai_agent/core/approvals/policies.py",
            "src/ultimate_ai_agent/core/approvals/validation.py",
            "src/ultimate_ai_agent/core/approvals/receipts.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m85_arbitrary_approval_refs_rejected(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, LocalApprovalAuthority

        request = self._m85_gate_approval_request()
        authority = LocalApprovalAuthority()
        authority.create_request(request)
        decision = authority.validate_for_request(request, "human_approved_ref_123")
        failures = []
        if decision.allowed:
            failures.append("arbitrary approval_ref was allowed")
        if decision.status != ApprovalDecisionStatus.invalid:
            failures.append("arbitrary approval_ref did not return invalid")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/approvals/authority.py"])

    def check_m85_local_approval_grant_validates(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, LocalApprovalAuthority

        request = self._m85_gate_approval_request()
        authority = LocalApprovalAuthority()
        authority.create_request(request)
        grant = authority.grant(request.approval_request_id, approved_by_actor_id="foundation_gate")
        decision = authority.validate_for_request(request, grant.approval_ref)
        failures = []
        if not decision.allowed:
            failures.append("valid approval grant was denied")
        if decision.status != ApprovalDecisionStatus.approved:
            failures.append("valid approval grant did not return approved")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/approvals/authority.py"])

    def check_m85_expired_revoked_approval_denies(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from datetime import timedelta

        from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, LocalApprovalAuthority
        from ultimate_ai_agent.core.time import utc_now

        failures = []
        expired_request = self._m85_gate_approval_request("m85_gate_expired")
        expired_authority = LocalApprovalAuthority()
        expired_authority.create_request(expired_request)
        expired = expired_authority.grant(
            expired_request.approval_request_id,
            approved_by_actor_id="foundation_gate",
            expires_at=utc_now() - timedelta(seconds=1),
        )
        expired_decision = expired_authority.validate_for_request(expired_request, expired.approval_ref)
        if expired_decision.allowed or expired_decision.status != ApprovalDecisionStatus.expired:
            failures.append("expired approval was accepted")

        revoked_request = self._m85_gate_approval_request("m85_gate_revoked")
        revoked_authority = LocalApprovalAuthority()
        revoked_authority.create_request(revoked_request)
        revoked = revoked_authority.grant(revoked_request.approval_request_id, approved_by_actor_id="foundation_gate")
        revoked_authority.revoke(revoked.approval_ref, "foundation gate check")
        revoked_decision = revoked_authority.validate_for_request(revoked_request, revoked.approval_ref)
        if revoked_decision.allowed or revoked_decision.status != ApprovalDecisionStatus.revoked:
            failures.append("revoked approval was accepted")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/approvals/authority.py"])

    def check_m85_router_uses_valid_approval_grant(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority

        profile = self._gate_cloud_profile()
        request = self._gate_route_request(
            profile,
            data_classification=ClassificationValue.sensitive_personal,
            policy=ModelRoutingPolicy(
                policy_id="m85_gate_cloud_policy",
                required_capabilities=[ModelTaskCapability.chat],
                prefer_local=False,
                allow_cloud=True,
                allow_paid=True,
                require_human_approval_for_cloud=True,
            ),
        )
        authority = LocalApprovalAuthority()
        approval_request = authority.create_request(LocalApprovalAuthority.request_for_model_route(request, resource_refs=[profile.model_profile_id]))
        grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="foundation_gate")
        decision = ModelRouter(approval_authority=authority).route(request.model_copy(update={"approval_ref": grant.approval_ref}))
        failures = []
        if decision.status != ModelRouteStatus.selected:
            failures.append("valid approval grant did not permit selected route")
        if "APPROVAL_VALIDATED" not in decision.reason_codes:
            failures.append("route decision did not expose approval validation reason")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"])

    def check_m85_runtime_factory_rejects_arbitrary_approval(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeRequestFactory

        route = self._gate_route_request(self._gate_cloud_profile(), approval_ref="human_approved_ref_123")
        decision = ModelRouter().route(route.model_copy(update={"approval_ref": None}))
        failures = []
        try:
            ModelRuntimeRequestFactory.from_route_decision(decision, route, self._m85_runtime_manifest())
            failures.append("runtime factory accepted arbitrary approval_ref")
        except ValueError:
            pass
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/adapters.py"])

    def check_m85_tool_broker_rejects_arbitrary_approval(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.consent import ConsentGrant, ConsentScopeType, ConsentSubjectType
        from ultimate_ai_agent.core.consent.enums import PermissionAction
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority

        registry = ToolRegistry()
        registry.register_tool(
            ToolManifest(
                tool_id="m85_gate_tool",
                display_name="M8.5 Gate Tool",
                category=ToolCategory.mock,
                description="Approval authority gate check.",
                execution_mode=ToolExecutionMode.dry_run,
                risk_level=ToolRiskLevel.high,
                capability_flag="m85_gate_tool",
                owner="core.gate",
                source="foundation_gate",
                version="0.0.0",
            )
        )
        ledger = ConsentLedger()
        ledger.add_grant(
            ConsentGrant(
                consent_id="m85_gate_consent",
                subject_type=ConsentSubjectType.tool,
                subject_id="m85_gate_tool",
                granted_to_actor="foundation_gate",
                on_behalf_of_user_id="foundation_gate",
                scope_type=ConsentScopeType.project,
                allowed_actions=[PermissionAction.execute],
                source="foundation_gate",
            )
        )
        decision = ToolBroker(
            registry,
            CapabilityFirewallPolicy(max_risk_level=ToolRiskLevel.high),
            approval_authority=LocalApprovalAuthority(),
        ).evaluate_request(
            ToolRequest(
                request_id="m85_gate_tool_request",
                run_id="run_foundation_gate",
                tool_id="m85_gate_tool",
                actor_context=self._actor(),
                requested_action="execute",
                purpose="foundation_gate_check",
                data_classification=DataBoundary.project_private,
                approval_ref="human_approved_ref_123",
            ),
            ledger,
        )
        failures = []
        if decision.status != ToolDecisionStatus.approval_required:
            failures.append("tool broker did not keep arbitrary approval_ref approval-required")
        if "APPROVAL_REF_UNKNOWN" not in decision.reason_codes:
            failures.append("tool broker did not report unknown approval ref")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/tools/broker.py"])

    def check_m85_no_real_auth_oauth_network(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        approval_root = self.src_root / "core" / "approvals"
        forbidden = [
            "import " + "requests",
            "import " + "httpx",
            "urllib",
            "socket",
            "oauth",
            "OAuth",
            "OpenID",
            "session_cookie",
            "jwt",
            "sqlite",
            "psycopg",
            "sub" + "process",
        ]
        failures = []
        for path in sorted(approval_root.rglob("*.py")):
            rel_path = str(path.relative_to(self.root))
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(f"{rel_path}:{line_no} forbidden auth/network/persistence fragment")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/approvals"])

    def check_m85_approval_api_secret_echo_absent(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from fastapi.testclient import TestClient

        from ultimate_ai_agent.api.app import app

        client = TestClient(app)
        secret = "sk_" + "test_" + "secret_" + "value"
        assignment = "api_" + "key=" + secret
        payload = self._m85_gate_approval_request().model_dump(mode="json")
        payload["metadata"] = {"note": assignment}
        response = client.post("/approvals/requests/validate", json=payload)
        failures = []
        if response.status_code not in {200, 422}:
            failures.append(f"unexpected approval API status {response.status_code}")
        if secret in response.text or assignment in response.text or "api_key" in response.text:
            failures.append("approval API echoed secret-like input")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m9_loopback_runtime_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_runtime/loopback.py",
            "src/ultimate_ai_agent/core/model_runtime/execution_policy.py",
            "src/ultimate_ai_agent/core/model_runtime/transports.py",
            "src/ultimate_ai_agent/core/model_runtime/local_adapter.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m9_non_loopback_endpoints_denied(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter, LoopbackRuntimeEndpoint, LoopbackRuntimePolicy, ModelRuntimeKind

        adapter = LocalLoopbackModelRuntimeAdapter()
        policy = LoopbackRuntimePolicy(policy_id="m9_gate_policy", allow_real_loopback_execution=True)
        def endpoint(base_url: str):
            return LoopbackRuntimeEndpoint(
                endpoint_id="m9_gate_endpoint",
                base_url=base_url,
                allowed_hosts=["127.0.0.1", "localhost", "::1"],
                runtime_kind=ModelRuntimeKind.local_stub,
                model_id="m9_gate_model",
                enabled=True,
                owner="foundation_gate",
                source="foundation_gate",
                version="0.0.0",
            )

        failures = []
        remote = adapter.validate_endpoint(endpoint("http" + "://example.com/api/generate"), policy)
        credentials = adapter.validate_endpoint(endpoint("http" + "://user:pass@127.0.0.1:11434/api/generate"), policy)
        query = adapter.validate_endpoint(endpoint("http" + "://127.0.0.1:11434/api/generate?token=abc"), policy)
        if remote.allowed or "NON_LOOPBACK_HOST_DENIED" not in remote.reason_codes:
            failures.append("remote host was not denied")
        if credentials.allowed or "URL_CREDENTIALS_DENIED" not in credentials.reason_codes:
            failures.append("URL credentials were not denied")
        if query.allowed or "SECRET_QUERY_DENIED" not in query.reason_codes:
            failures.append("secret-like query parameter was not denied")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"])

    def check_m9_non_loopback_policy_override_denied(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter, LoopbackRuntimeEndpoint, LoopbackRuntimePolicy, ModelRuntimeKind

        adapter = LocalLoopbackModelRuntimeAdapter()
        policy = LoopbackRuntimePolicy(
            policy_id="m9_gate_override_policy",
            allow_real_loopback_execution=True,
        ).model_copy(
            update={
                "allowed_hosts": ["example.com"],
                "deny_non_loopback": False,
            }
        )
        endpoint = LoopbackRuntimeEndpoint(
            endpoint_id="m9_gate_override_endpoint",
            base_url="http" + "://example.com/api/generate",
            allowed_hosts=["example.com"],
            runtime_kind=ModelRuntimeKind.local_stub,
            model_id="m9_gate_model",
            enabled=True,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
        )
        decision = adapter.validate_endpoint(endpoint, policy)
        failures = []
        if decision.allowed:
            failures.append("caller override allowed a remote endpoint")
        for reason in ("NON_LOOPBACK_HOST_DENIED", "POLICY_CANNOT_DISABLE_LOOPBACK_GUARD"):
            if reason not in decision.reason_codes:
                failures.append(f"override decision missing {reason}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"])

    def check_m9_loopback_policy_model_rejects_hostile_inputs(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LoopbackRuntimePolicy

        failures = []
        hostile_inputs = [
            {"deny_non_loopback": False},
            {"allowed_hosts": ["example.com"]},
            {"allowed_hosts": ["192.168.1.5"]},
            {"allowed_hosts": ["10.0.0.5"]},
            {"allowed_hosts": ["8.8.8.8"]},
            {"allowed_hosts": ["127.0.0.1", "example.com"]},
        ]
        for payload in hostile_inputs:
            try:
                LoopbackRuntimePolicy(policy_id="m9_gate_hostile_policy", **payload)
            except ValueError:
                continue
            failures.append(f"hostile policy accepted: {payload}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/execution_policy.py"])

    def check_m9_public_and_private_ip_endpoints_denied(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter, LoopbackRuntimeEndpoint, LoopbackRuntimePolicy, ModelRuntimeKind

        adapter = LocalLoopbackModelRuntimeAdapter()
        policy = LoopbackRuntimePolicy(policy_id="m9_gate_ip_policy", allow_real_loopback_execution=True)
        failures = []
        for host in ["192.168.1.5", "10.0.0.5", "8.8.8.8"]:
            endpoint = LoopbackRuntimeEndpoint(
                endpoint_id=f"m9_gate_{host.replace('.', '_')}",
                base_url="http" + f"://{host}/api/generate",
                allowed_hosts=[host],
                runtime_kind=ModelRuntimeKind.local_stub,
                model_id="m9_gate_model",
                enabled=True,
                owner="foundation_gate",
                source="foundation_gate",
                version="0.0.0",
            )
            decision = adapter.validate_endpoint(endpoint, policy)
            if decision.allowed or "NON_LOOPBACK_HOST_DENIED" not in decision.reason_codes:
                failures.append(f"{host} was not denied")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"])

    def check_m9_approval_api_uses_public_authority_helper(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        app_source = self._read(self.root / "src/ultimate_ai_agent/api/app.py")
        authority_source = self._read(self.root / "src/ultimate_ai_agent/core/approvals/authority.py")
        failures = []
        if "authority._grants" in app_source:
            failures.append("approval API mutates private _grants")
        if "load_grant_for_validation" not in app_source:
            failures.append("approval API does not use public grant-loading helper")
        if "def load_grant_for_validation" not in authority_source:
            failures.append("LocalApprovalAuthority helper is missing")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/api/app.py", "src/ultimate_ai_agent/core/approvals/authority.py"],
        )

    def check_m9_arbitrary_approval_refs_denied(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter

        request = self._m9_runtime_request(approval_ref="human_approved_ref_123")
        decision = LocalLoopbackModelRuntimeAdapter().validate_execution(
            request,
            self._m9_runtime_manifest(),
            self._m9_loopback_endpoint(),
            self._m9_loopback_policy(),
            approval_decision=None,
        )
        failures = []
        if decision.allowed:
            failures.append("arbitrary approval_ref allowed execution")
        if "APPROVAL_DECISION_REQUIRED" not in decision.reason_codes:
            failures.append("arbitrary approval_ref did not require validated approval decision")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"])

    def check_m9_fake_transport_only_in_gate(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        runtime_root = self.src_root / "core" / "model_runtime"
        forbidden = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "openai",
            "import " + "anthropic",
            "tiktoken",
            "tokenizers",
            "billing",
            "sub" + "process",
        ]
        failures = []
        for path in sorted(runtime_root.rglob("*.py")):
            rel_path = str(path.relative_to(self.root))
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(f"{rel_path}:{line_no} forbidden M9 runtime fragment")
                if "DisabledNetworkTransport().send(" in stripped:
                    failures.append(f"{rel_path}:{line_no} disabled transport send call in gate path")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime"])

    def check_m9_simulated_fallback_available(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter, ModelRuntimeResponseStatus

        response = LocalLoopbackModelRuntimeAdapter().execute_dev(
            self._m9_runtime_request(approval_ref="human_approved_ref_123"),
            self._m9_runtime_manifest(),
            self._m9_loopback_endpoint(),
            self._m9_loopback_policy(),
            approval_decision=None,
        )
        failures = []
        if response.status != ModelRuntimeResponseStatus.simulated_success:
            failures.append("blocked execution did not return simulated fallback")
        if response.response_origin != "simulated":
            failures.append("fallback response origin was not simulated")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"])

    def check_m9_model_output_not_truth_authority(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import ApprovalRiskLevel, ApprovalSubjectType, LocalApprovalAuthority
        from ultimate_ai_agent.core.model_runtime import FakeModelRuntimeTransport, LocalLoopbackModelRuntimeAdapter, response_is_truth_authority

        request = self._m9_runtime_request()
        approval_request = LocalApprovalAuthority.request_for_model_route(
            self._gate_route_request(self._gate_local_profile()),
            subject_type=ApprovalSubjectType.model_runtime_request,
            subject_id=request.runtime_request_id,
            requested_action="execute_local_loopback_model",
            resource_refs=[request.adapter_id, request.model_profile_id],
            risk_level=ApprovalRiskLevel.high,
        )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="foundation_gate")
        approval = authority.validate_for_request(approval_request, grant.approval_ref)
        response = LocalLoopbackModelRuntimeAdapter().execute_dev(
            request.model_copy(update={"approval_ref": grant.approval_ref}),
            self._m9_runtime_manifest(),
            self._m9_loopback_endpoint(),
            self._m9_loopback_policy(),
            approval,
            transport=FakeModelRuntimeTransport(),
        )
        failures = []
        if response_is_truth_authority(response):
            failures.append("local loopback response is truth authority")
        if response.metadata.get("truth_authority") is not False:
            failures.append("local loopback metadata did not mark non-authoritative")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/responses.py"])

    def check_m10_manual_smoke_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_runtime/smoke_policy.py",
            "src/ultimate_ai_agent/core/model_runtime/smoke.py",
            "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
            "scripts/local_loopback_smoke.py",
            "tests/test_manual_loopback_smoke_policy.py",
            "tests/test_manual_loopback_smoke_transport.py",
            "tests/test_manual_loopback_smoke_script.py",
            "tests/test_manual_loopback_smoke_api_routes.py",
            "tests/test_m10_gate_integration.py",
        ]
        failures = [f"missing {rel_path}" for rel_path in required if not (self.root / rel_path).exists()]
        return self._result(criterion, failures, required)

    def check_m10_stdlib_network_isolated(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        allowed = {
            "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
            "scripts/local_loopback_smoke.py",
        }
        forbidden = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "openai",
            "import " + "anthropic",
            "tiktoken",
            "tokenizers",
            "billing",
            "socket",
            "subprocess",
        ]
        failures = []
        paths = [*list((self.root / "src/ultimate_ai_agent/core/model_runtime").rglob("*.py")), self.root / "scripts/local_loopback_smoke.py"]
        for path in paths:
            if not path.exists():
                continue
            rel_path = str(path.relative_to(self.root))
            source = self._read(path)
            if ("urllib.request" in source or "from urllib import request" in source) and rel_path not in allowed:
                failures.append(f"urllib request outside isolated smoke file: {rel_path}")
            for line in source.splitlines():
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(f"forbidden runtime fragment in {rel_path}: {stripped}")
        return self._result(criterion, failures, sorted(allowed))

    def check_m10_gate_and_verify_do_not_call_smoke_script(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        for rel_path in ["scripts/run_foundation_gate.py", "scripts/verify_all.py"]:
            source = self._read(self.root / rel_path)
            if "scripts/local_loopback_smoke.py" in source:
                failures.append(f"{rel_path} references manual smoke script")
        return self._result(criterion, failures, ["scripts/run_foundation_gate.py", "scripts/verify_all.py"])

    def check_m10_public_api_has_no_smoke_execute_endpoint(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app

        paths = {route.path for route in app.routes}
        failures = []
        if "/model-runtime/local/smoke/validate" not in paths:
            failures.append("smoke validation endpoint missing")
        for forbidden in ["/model-runtime/local/smoke/execute", "/model-runtime/local/execute"]:
            if forbidden in paths:
                failures.append(f"forbidden execute endpoint present: {forbidden}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m10_fixed_prompt_and_loopback_policy_enforced(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        try:
            self._m10_smoke_request(fixed_prompt="Summarize this user file content.")
            failures.append("arbitrary user-content prompt accepted")
        except ValueError:
            pass
        try:
            self._m10_smoke_request(endpoint=self._m10_smoke_endpoint(base_url="http" + "://example.com/api/generate", allowed_hosts=["example.com"]))
            failures.append("remote smoke endpoint accepted")
        except ValueError:
            pass
        try:
            self._m10_smoke_request()
        except ValueError as exc:
            failures.append(f"safe fixed smoke request rejected: {exc}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/smoke_policy.py"])

    def check_m10_smoke_approval_required(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
        from ultimate_ai_agent.core.model_runtime import smoke_approval_request, validate_manual_loopback_smoke_request

        request = self._m10_smoke_request()
        missing = validate_manual_loopback_smoke_request(request.model_copy(update={"approval_ref": None}), None)
        arbitrary = validate_manual_loopback_smoke_request(request.model_copy(update={"approval_ref": "human_approved_ref_123"}), None)
        approval = smoke_approval_request(request)
        authority = LocalApprovalAuthority()
        authority.create_request(approval)
        grant = authority.grant(approval.approval_request_id, approved_by_actor_id="human_reviewer")
        decision = authority.validate_for_request(approval, grant.approval_ref)
        allowed = validate_manual_loopback_smoke_request(request.model_copy(update={"approval_ref": grant.approval_ref}), decision)
        failures = []
        if missing.allowed or "APPROVAL_REQUIRED" not in missing.reason_codes:
            failures.append("missing approval was not denied")
        if arbitrary.allowed or "APPROVAL_DECISION_REQUIRED" not in arbitrary.reason_codes:
            failures.append("arbitrary approval ref was not denied")
        if not allowed.allowed:
            failures.append("valid scoped approval did not permit smoke validation")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/smoke.py"])

    def check_m10_smoke_response_not_truth_authority(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
        from ultimate_ai_agent.core.model_runtime import FakeManualLoopbackSmokeTransport, smoke_approval_request

        request = self._m10_smoke_request()
        approval = smoke_approval_request(request)
        authority = LocalApprovalAuthority()
        authority.create_request(approval)
        grant = authority.grant(approval.approval_request_id, approved_by_actor_id="human_reviewer")
        decision = authority.validate_for_request(approval, grant.approval_ref)
        result = FakeManualLoopbackSmokeTransport().send_smoke(request.model_copy(update={"approval_ref": grant.approval_ref}), decision)
        failures = []
        if result.metadata.get("truth_authority") is not False:
            failures.append("smoke result metadata does not mark truth_authority false")
        if result.response_preview == request.fixed_prompt or request.fixed_prompt in result.model_dump_json():
            failures.append("smoke result leaked fixed prompt content")
        if result.response_origin != "fake_manual_loopback_smoke":
            failures.append("gate did not use fake manual smoke transport")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/smoke.py"])

    def check_m105_remote_worker_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/remote_workers/__init__.py",
            "src/ultimate_ai_agent/core/remote_workers/enums.py",
            "src/ultimate_ai_agent/core/remote_workers/nodes.py",
            "src/ultimate_ai_agent/core/remote_workers/transports.py",
            "src/ultimate_ai_agent/core/remote_workers/registry.py",
            "src/ultimate_ai_agent/core/remote_workers/policy.py",
            "src/ultimate_ai_agent/core/remote_workers/jobs.py",
            "src/ultimate_ai_agent/core/remote_workers/results.py",
            "src/ultimate_ai_agent/core/remote_workers/audit.py",
            "src/ultimate_ai_agent/core/remote_workers/status.py",
            "src/ultimate_ai_agent/core/remote_workers/validation.py",
            "src/ultimate_ai_agent/core/remote_workers/dry_run.py",
            "tests/test_remote_worker_models.py",
            "tests/test_remote_worker_registry.py",
            "tests/test_remote_worker_policy.py",
            "tests/test_remote_worker_transports.py",
            "tests/test_remote_worker_dry_run.py",
            "tests/test_remote_worker_api_routes.py",
            "tests/test_remote_worker_no_network.py",
            "tests/test_remote_worker_gate_integration.py",
        ]
        failures = [f"missing {rel_path}" for rel_path in required if not (self.root / rel_path).exists()]
        return self._result(criterion, failures, required)

    def check_m105_remote_capabilities_default_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import NodeCapabilitySet

        capabilities = NodeCapabilitySet()
        failures = []
        for name, value in capabilities.model_dump().items():
            if value is not False:
                failures.append(f"{name} defaulted to {value}")
        for field, value in {"can_approve_actions": True, "can_run_critical": True}.items():
            try:
                NodeCapabilitySet(**{field: value})
                failures.append(f"{field} accepted true")
            except ValueError:
                pass
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/nodes.py"])

    def check_m105_unknown_node_and_transport_denied(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteNodeRegistry, RemoteTransportRegistry

        node = RemoteNodeRegistry().validate_node("missing_node")
        transport = RemoteTransportRegistry().validate_transport("missing_transport")
        failures = []
        if node.allowed or "REMOTE_NODE_UNKNOWN" not in node.reason_codes:
            failures.append("unknown node was not denied")
        if transport.allowed or "REMOTE_TRANSPORT_UNKNOWN" not in transport.reason_codes:
            failures.append("unknown transport was not denied")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/registry.py"])

    def check_m105_planned_transports_disabled(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import default_remote_transport_registry

        registry = default_remote_transport_registry()
        failures = []
        for transport_id in ["tailnet_planned", "lan_planned"]:
            descriptor = registry.get_transport(transport_id)
            decision = registry.validate_transport(transport_id)
            if descriptor is None:
                failures.append(f"{transport_id} missing")
                continue
            if descriptor.enabled:
                failures.append(f"{transport_id} enabled")
            if decision.allowed:
                failures.append(f"{transport_id} allowed")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/registry.py"])

    def check_m105_dry_run_dispatches_nothing(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import (
            RemoteDryRunBuilder,
            RemoteExecutionPolicy,
            default_remote_node_registry,
            default_remote_transport_registry,
        )

        policy = RemoteExecutionPolicy(
            policy_id="m105_gate_policy",
            remote_workers_enabled=True,
            remote_transports_enabled=True,
            remote_accept_jobs=True,
        )
        envelope = RemoteDryRunBuilder().build_envelope(
            task_summary="Validate remote worker dry-run metadata.",
            node_id="mock_node",
            transport_id="mock_metadata",
            actor_context=self._actor(),
            policy=policy,
        )
        result = RemoteDryRunBuilder().dry_run(envelope, default_remote_node_registry(), default_remote_transport_registry(), policy)
        failures = []
        if result.dispatch_performed:
            failures.append("dry-run marked dispatch performed")
        if result.remote_execution_performed:
            failures.append("dry-run marked remote execution performed")
        if result.subagent_launched:
            failures.append("dry-run launched subagent")
        if result.tools_executed:
            failures.append("dry-run executed tools")
        if result.network_connections_opened:
            failures.append("dry-run opened network connections")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/dry_run.py"])

    def check_m105_no_remote_network_or_background_execution(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        root = self.root / "src/ultimate_ai_agent/core/remote_workers"
        forbidden_imports = {"socket", "subprocess", "threading", "asyncio", "requests", "httpx", "urllib"}
        forbidden_fragments = ["Popen", "os.system", "Thread(", "urlopen", "dispatch_job(", "execute_remote(", "launch_subagent("]
        failures = []
        for path in root.rglob("*.py"):
            source = self._read(path)
            for line in source.splitlines():
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    if any(fragment in stripped for fragment in forbidden_imports):
                        failures.append(f"{path.relative_to(self.root)} forbidden import: {stripped}")
                if any(fragment in stripped for fragment in forbidden_fragments):
                    failures.append(f"{path.relative_to(self.root)} forbidden fragment: {stripped}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers"])

    def check_m105_no_remote_subagents_tools_or_approvals(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteExecutionPolicy, evaluate_remote_job_policy

        failures = []
        policy = RemoteExecutionPolicy(
            policy_id="m105_gate_policy",
            remote_workers_enabled=True,
            remote_transports_enabled=True,
            remote_accept_jobs=True,
        )
        for capability, reason in [
            ("subagent", "REMOTE_SUBAGENT_DENIED"),
            ("tools", "REMOTE_TOOL_EXECUTION_DENIED"),
            ("approve", "REMOTE_APPROVAL_DENIED"),
            ("personal_data", "REMOTE_PERSONAL_DATA_DENIED"),
            ("write", "REMOTE_WRITE_DENIED"),
            ("send", "REMOTE_SEND_DENIED"),
        ]:
            envelope = self._m105_remote_job(requested_capabilities=[capability])
            decision = evaluate_remote_job_policy(envelope, self._m105_node_registry(), self._m105_transport_registry(), policy)
            if decision.allowed or reason not in decision.reason_codes:
                failures.append(f"{capability} not denied")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/policy.py"])

    def check_m105_remote_output_untrusted(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteDryRunBuilder, RemoteExecutionPolicy, RemoteOutputTrustLevel

        policy = RemoteExecutionPolicy(
            policy_id="m105_gate_policy",
            remote_workers_enabled=True,
            remote_transports_enabled=True,
            remote_accept_jobs=True,
        )
        result = RemoteDryRunBuilder().dry_run(
            self._m105_remote_job(),
            self._m105_node_registry(),
            self._m105_transport_registry(),
            policy,
        )
        failures = []
        if result.output_trust_level != RemoteOutputTrustLevel.untrusted_remote_output:
            failures.append("remote output not marked untrusted")
        if result.metadata.get("foundation_only") is not True:
            failures.append("remote result missing foundation_only marker")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/results.py"])

    def check_m105_api_routes_are_dry_run_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app

        paths = {route.path for route in app.routes}
        failures = []
        required = {
            "/remote-workers/nodes/validate",
            "/remote-workers/transports/validate",
            "/remote-workers/policy/validate",
            "/remote-workers/jobs/validate",
            "/remote-workers/dry-run",
            "/remote-workers/status",
            "/remote-workers/tailnet/status",
            "/remote-workers/mesh/status",
        }
        for path in required:
            if path not in paths:
                failures.append(f"missing route {path}")
        for forbidden in ["/remote-workers/dispatch", "/remote-workers/execute", "/remote-workers/subagents/launch"]:
            if forbidden in paths:
                failures.append(f"forbidden route present: {forbidden}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m105_docs_foundation_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        docs = [
            "docs/remote/REMOTE_WORKER_FOUNDATION.md",
            "docs/remote/REMOTE_NODE_SECURITY_MODEL.md",
            "docs/remote/REMOTE_JOB_ENVELOPE.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/decisions/remote_worker_tailnet_foundation.md",
            "docs/release_notes/v0_14_2.md",
        ]
        failures = []
        required_phrases = ["foundation-only", "No live networking", "No job dispatch", "No remote approvals"]
        for rel_path in docs:
            path = self.root / rel_path
            if not path.exists():
                failures.append(f"missing {rel_path}")
                continue
            source = self._read(path)
            for phrase in required_phrases:
                if phrase not in source:
                    failures.append(f"{rel_path} missing phrase: {phrase}")
        return self._result(criterion, failures, docs)

    def check_m105_remote_tailnet_enable_flag_rejected(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteExecutionPolicy

        failures = []
        try:
            RemoteExecutionPolicy(policy_id="m105_tailnet_policy", remote_tailnet_enabled=True)
            failures.append("remote_tailnet_enabled=true was accepted")
        except ValueError as exc:
            if "REMOTE_TAILNET_NOT_SUPPORTED_IN_M10_5" not in str(exc):
                failures.append("remote_tailnet_enabled=true failed without the expected reason code")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/policy.py"])

    def check_m105_remote_personal_data_enable_flag_rejected(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteExecutionPolicy

        failures = []
        try:
            RemoteExecutionPolicy(policy_id="m105_personal_data_policy", remote_personal_data_enabled=True)
            failures.append("remote_personal_data_enabled=true was accepted")
        except ValueError as exc:
            if "REMOTE_PERSONAL_DATA_NOT_SUPPORTED_IN_M10_5" not in str(exc):
                failures.append("remote_personal_data_enabled=true failed without the expected reason code")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/policy.py"])

    def check_m105_remote_worker_api_extra_fields_forbidden(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from fastapi.testclient import TestClient

        from ultimate_ai_agent.api.app import app

        failures = []
        client = TestClient(app)
        response = client.post(
            "/remote-workers/policy/validate",
            json={"policy": {"policy_id": "m105_extra_policy"}, "api_key": "sk_secret_value_123456"},
        )
        body = response.json()
        if response.status_code != 422:
            failures.append(f"extra top-level field returned status {response.status_code}")
        if body.get("success") is not False:
            failures.append("extra top-level field did not produce failure envelope")
        if "api_key" in response.text or "sk_secret_value_123456" in response.text:
            failures.append("extra top-level secret-like field leaked in validation response")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m143_private_mesh_taxonomy_open_source_first(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import (
            PrivateMeshProviderKind,
            RemoteTransportSelectionPolicy,
            default_remote_transport_registry,
        )

        policy = RemoteTransportSelectionPolicy(policy_id="m143_private_mesh_policy")
        registry = default_remote_transport_registry()
        failures = []
        for transport_id in ["headscale_planned", "generic_wireguard_planned", "tailscale_planned", "private_mesh_planned"]:
            if registry.get_transport(transport_id) is None:
                failures.append(f"{transport_id} missing")
        if policy.prefer_open_source_first is not True:
            failures.append("open-source-first preference disabled")
        if policy.prefer_self_hosted_control_plane is not True:
            failures.append("self-hosted control-plane preference disabled")
        if policy.allow_proprietary_control_plane:
            failures.append("proprietary control plane allowed by default")
        if policy.allowed_provider_kinds[:2] != [
            PrivateMeshProviderKind.headscale_planned,
            PrivateMeshProviderKind.generic_wireguard_planned,
        ]:
            failures.append("planned provider order does not evaluate Headscale and generic WireGuard first")
        if PrivateMeshProviderKind.tailscale_planned not in policy.blocked_provider_kinds:
            failures.append("Tailscale planned provider was not blocked by default")
        docs = [
            "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/decisions/ADR-open-source-first-private-networking.md",
            "docs/release_notes/v0_14_3.md",
        ]
        required_phrases = ["open-source-first", "Headscale", "generic WireGuard", "Tailscale", "planned"]
        for rel_path in docs:
            source = self._read(self.root / rel_path)
            if not source:
                failures.append(f"missing {rel_path}")
                continue
            for phrase in required_phrases:
                if phrase.lower() not in source.lower():
                    failures.append(f"{rel_path} missing phrase: {phrase}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers", *docs])

    def check_m143_planned_mesh_transports_disabled(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import default_remote_transport_registry

        registry = default_remote_transport_registry()
        failures = []
        for transport_id in ["private_mesh_planned", "headscale_planned", "generic_wireguard_planned", "tailscale_planned", "tailnet_planned", "lan_planned"]:
            descriptor = registry.get_transport(transport_id)
            decision = registry.validate_transport(transport_id)
            if descriptor is None:
                failures.append(f"{transport_id} missing")
                continue
            if descriptor.enabled:
                failures.append(f"{transport_id} enabled")
            if descriptor.requires_network:
                failures.append(f"{transport_id} requires network")
            if descriptor.requires_credentials:
                failures.append(f"{transport_id} requires credentials")
            if descriptor.supports_dispatch:
                failures.append(f"{transport_id} supports dispatch")
            if decision.allowed:
                failures.append(f"{transport_id} allowed")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/registry.py"])

    def check_m143_no_live_mesh_integrations(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        forbidden_runtime_fragments = [
            "tailscaled",
            "tailscale.",
            "tailscale(",
            "headscale.",
            "headscale(",
            "wireguard.",
            "wireguard(",
            "wg ",
            "wg-quick",
            "serve",
            "funnel",
            "urlopen",
            "socket.",
            "dispatch_job(",
            "execute_remote(",
            "launch_subagent(",
        ]
        for path in (self.root / "src/ultimate_ai_agent/core/remote_workers").rglob("*.py"):
            source = self._read(path).lower()
            for fragment in forbidden_runtime_fragments:
                if fragment in source:
                    failures.append(f"{path.relative_to(self.root)} contains live mesh fragment: {fragment}")
        docs_to_scan = [
            self.root / "docs/remote",
            self.root / "docs/decisions",
            self.root / "docs/release_notes",
            self.root / "docs/implementation",
        ]
        tracked = "\n".join(self._read(path) for path in (self.root / "src/ultimate_ai_agent/core/remote_workers").rglob("*.py"))
        for doc_root in docs_to_scan:
            tracked += "\n" + "\n".join(self._read(path) for path in doc_root.rglob("*.md"))
        private_ip = re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b")
        if private_ip.search(tracked):
            failures.append("private IP literal found in runtime/docs")
        for forbidden_secretish in ["authkey-", "nodekey:", "tailnet name:", "oauth_client_secret"]:
            if forbidden_secretish in tracked.lower():
                failures.append(f"secret/private mesh config marker found: {forbidden_secretish}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/remote_workers", "docs/remote"])

    def check_documentation_integrity_current(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        version = self._active_version()
        version_key = (version or "0.0.0").replace(".", "_")
        required = [
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/maintenance/documentation_integrity_checklist.md",
            "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
            "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
            "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
            "docs/backlog/codex_plugin_enablement_backlog.md",
            f"README_IMPORT_v{version_key}.md",
            f"ultimate_ai_agent_master_plan_v{version_key}.md",
            f"docs/release_notes/v{version_key}.md",
            f"docs/implementation/foundation_gate_implementation_plan_v{version_key}.md",
            "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
            "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
            "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        readme = self._read(self.root / "README.md")
        if version and f"README_IMPORT_v{version_key}.md" not in readme:
            failures.append("README.md missing active import README")
        if version and f"ultimate_ai_agent_master_plan_v{version_key}.md" not in readme:
            failures.append("README.md missing active master plan")
        if "docs/DOCUMENTATION_INDEX.md" not in readme:
            failures.append("README.md missing documentation index")
        if "docs/canonical/CANONICAL_DOC_MAP.md" not in readme:
            failures.append("README.md missing canonical doc map")

        unsafe_claims = [
            "tailscale integration is implemented",
            "headscale integration is implemented",
            "remote execution is supported",
            "mobile camera access is implemented",
            "microphone capture is implemented",
            "gps access is implemented",
            "skill factory is implemented",
            "scanner runtime is implemented",
            "production_ready=true",
            "real_model_runtime_ready=true",
            "remote_execution_ready=true",
            "mobile_sensor_ready=true",
            "plugin_or_native_build_ready=true",
        ]
        active_docs = [
            "README.md",
            "VERSION.md",
            "AGENTS.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/canonical/09_roadmap.md",
            "docs/api/README.md",
            "docs/api/openapi_contract.md",
            "docs/api/route_inventory.md",
            "docs/runtime/model_runtime_adapter_harness.md",
            "docs/runtime/local_loopback_model_runtime.md",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
            "docs/remote/REMOTE_WORKER_FOUNDATION.md",
            "docs/remote/REMOTE_NODE_SECURITY_MODEL.md",
            "docs/remote/REMOTE_JOB_ENVELOPE.md",
            "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
            "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
            "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
            "docs/backlog/mobile_companion_backlog.md",
            "docs/backlog/device_capability_broker_backlog.md",
            "docs/backlog/codex_plugin_enablement_backlog.md",
            "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
            "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
        ]
        for rel_path in active_docs:
            path = self.root / rel_path
            if not path.exists():
                continue
            source = self._read(path).lower()
            for phrase in unsafe_claims:
                if phrase in source:
                    failures.append(f"{rel_path} contains unsafe implementation claim: {phrase}")
        return self._result(criterion, failures, required)

    def check_codex_plugin_governance_docs_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
            "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
            "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
            "docs/backlog/codex_plugin_enablement_backlog.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        combined = "\n".join(self._read(self.root / path).lower() for path in required if (self.root / path).exists())
        expectations = {
            "iOS/macOS build plugins disabled": ["build ios apps", "build macos apps", "disabled"],
            "Computer Use disabled": ["computer use", "disabled"],
            "Chrome authenticated profile disabled": ["chrome authenticated", "disabled"],
            "plugin/skill installers disabled": ["plugin/skill installers", "disabled"],
            "Browser + Build Web Apps approval boundary": ["browser + build web apps", "approval"],
        }
        for label, fragments in expectations.items():
            if not all(fragment in combined for fragment in fragments):
                failures.append(f"missing policy phrase: {label}")
        forbidden_enablement_claims = [
            "plugins are enabled",
            "xcode workflow is enabled",
            "computer use is enabled",
            "chrome authenticated profile control is enabled",
            "plugin installers are enabled",
        ]
        for phrase in forbidden_enablement_claims:
            if phrase in combined:
                failures.append(f"unsafe plugin enablement claim: {phrase}")
        return self._result(criterion, failures, required)

    def check_m11_runtime_readiness_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/runtime_readiness/__init__.py",
            "src/ultimate_ai_agent/core/runtime_readiness/enums.py",
            "src/ultimate_ai_agent/core/runtime_readiness/matrix.py",
            "src/ultimate_ai_agent/core/runtime_readiness/reports.py",
            "src/ultimate_ai_agent/core/runtime_readiness/smoke_reports.py",
            "src/ultimate_ai_agent/core/runtime_readiness/validators.py",
            "src/ultimate_ai_agent/core/runtime_readiness/gate.py",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
            "tests/test_runtime_capability_matrix.py",
            "tests/test_manual_smoke_report_validation.py",
            "tests/test_runtime_readiness_report.py",
            "tests/test_runtime_readiness_api_routes.py",
            "tests/test_runtime_readiness_no_execution.py",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m11_runtime_capability_matrix_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.runtime_readiness import RuntimeCapabilityStatus, RuntimeSurface, build_matrix

        matrix = build_matrix()
        entries = {entry.surface: entry for entry in matrix.entries}
        expected = {
            RuntimeSurface.remote_worker_foundation.value: RuntimeCapabilityStatus.dry_run_only.value,
            RuntimeSurface.private_mesh_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.tailnet_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.headscale_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.generic_wireguard_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.tailscale_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.cloud_provider_runtime.value: RuntimeCapabilityStatus.blocked.value,
            RuntimeSurface.manual_loopback_smoke.value: RuntimeCapabilityStatus.manual_only.value,
            RuntimeSurface.mobile_companion_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.device_capability_broker_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.codex_plugin_governance.value: RuntimeCapabilityStatus.planned_disabled.value,
        }
        failures = []
        for surface, status in expected.items():
            entry = entries.get(surface)
            if entry is None:
                failures.append(f"missing matrix surface: {surface}")
            elif entry.status != status:
                failures.append(f"{surface} status is {entry.status}, expected {status}")
        if not matrix.assert_no_runtime_expansion():
            failures.append("matrix allows runtime expansion")
        if not matrix.assert_foundation_gate_coverage():
            failures.append("matrix entry missing Foundation Gate coverage")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/runtime_readiness/matrix.py"])

    def check_m11_manual_smoke_report_validation_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.runtime_readiness import validate_manual_smoke_report
        from ultimate_ai_agent.core.runtime_readiness.gate import m11_gate_safe_smoke_report_payload

        safe = validate_manual_smoke_report(m11_gate_safe_smoke_report_payload())
        unsafe_payloads = [
            ("raw prompt", {**m11_gate_safe_smoke_report_payload(), "raw_prompt": "user prompt"}),
            (
                "secret response",
                {**m11_gate_safe_smoke_report_payload(), "response_preview": "api" + "_key='abcdefghijklmnop'"},
            ),
            ("remote endpoint", {**m11_gate_safe_smoke_report_payload(), "endpoint_summary": "https" + "://api.example.com"}),
            (
                "cloud claim",
                {**m11_gate_safe_smoke_report_payload(), "metadata": {"claim": "cloud provider model call executed"}},
            ),
            (
                "authoritative output",
                {**m11_gate_safe_smoke_report_payload(), "model_output_authoritative": True},
            ),
        ]
        failures = []
        if not safe.allowed:
            failures.append("safe manual smoke report was rejected")
        for label, payload in unsafe_payloads:
            validation = validate_manual_smoke_report(payload)
            if validation.allowed:
                failures.append(f"unsafe manual smoke report accepted: {label}")
            if "abcdefghijklmnop" in validation.safe_message:
                failures.append("unsafe secret echoed in validation message")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/runtime_readiness/smoke_reports.py"])

    def check_m11_no_production_readiness_claim(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.runtime_readiness import build_readiness_report

        report = build_readiness_report()
        failures = []
        checks = {
            "production_ready": report.production_ready,
            "real_model_runtime_ready": report.real_model_runtime_ready,
            "remote_execution_ready": report.remote_execution_ready,
            "mobile_sensor_ready": report.mobile_sensor_ready,
            "plugin_or_native_build_ready": report.plugin_or_native_build_ready,
            "model_output_authoritative": report.model_output_authoritative,
        }
        failures.extend(f"{name} is true" for name, value in checks.items() if value is True)
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/runtime_readiness/reports.py"])

    def check_m11_runtime_api_status_validation_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items
        from ultimate_ai_agent.api.openapi import FORBIDDEN_ROUTE_FRAGMENTS

        routes = iter_api_route_items(app)
        paths = {route.path: route for route in routes}
        required = {
            "/runtime/readiness",
            "/runtime/capability-matrix",
            "/runtime/smoke-reports/validate",
        }
        failures = [f"missing runtime route: {path}" for path in sorted(required - set(paths))]
        for path in sorted(path for path in paths if path.startswith("/runtime")):
            route = paths[path]
            if "runtime-readiness" not in route.tags:
                failures.append(f"{path} has unexpected tags {route.tags}")
            if not route.validation_only:
                failures.append(f"{path} is not validation/status only")
        unsafe_routes = [
            path
            for path in paths
            if path.startswith("/runtime") and any(fragment in path for fragment in FORBIDDEN_ROUTE_FRAGMENTS)
        ]
        failures.extend(f"forbidden runtime route present: {path}" for path in sorted(unsafe_routes))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py", "src/ultimate_ai_agent/api/openapi.py"])

    def check_m11_no_smoke_script_execution_in_gate(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        failures = []
        for rel_path in ["scripts/verify_all.py", "scripts/run_foundation_gate.py"]:
            source = self._read(self.root / rel_path)
            if "local_loopback_smoke.py" in source:
                failures.append(f"{rel_path} references local_loopback_smoke.py")
        return self._result(criterion, failures, ["scripts/verify_all.py", "scripts/run_foundation_gate.py"])

    def check_m11_no_runtime_expansion_imports(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        package = self.root / "src/ultimate_ai_agent/core/runtime_readiness"
        forbidden_starts = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "urllib",
            "from " + "urllib import",
            "import " + "socket",
            "import " + "subprocess",
            "import " + "openai",
            "import " + "anthropic",
            "import " + "tiktoken",
            "import " + "tokenizers",
        ]
        forbidden_fragments = ["billing", "eval(", "exec("]
        failures = []
        for path in sorted(package.glob("*.py")):
            rel_path = str(path.relative_to(self.root))
            for line_no, stripped in enumerate(self._read(path).splitlines(), start=1):
                stripped = stripped.strip()
                if self._is_static_scanner_text(stripped) or stripped.startswith("["):
                    continue
                if any(stripped.startswith(pattern) for pattern in forbidden_starts):
                    failures.append(f"{rel_path}:{line_no} forbidden import")
                if any(fragment in stripped for fragment in forbidden_fragments):
                    failures.append(f"{rel_path}:{line_no} forbidden runtime fragment")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/runtime_readiness"])

    def check_m11_no_remote_mesh_mobile_or_plugin_enablement(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        sources = [
            "src/ultimate_ai_agent/core/runtime_readiness",
            "src/ultimate_ai_agent/api/app.py",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
        ]
        forbidden_claims = [
            "remote_execution_ready=true",
            "live mesh is enabled",
            "tailnet is enabled",
            "headscale is connected",
            "wireguard is connected",
            "mobile sensors are enabled",
            "camera access is implemented",
            "plugin enablement is implemented",
            "native build execution is enabled",
            "computer use automation is enabled",
        ]
        combined = ""
        for source in sources:
            path = self.root / source
            if path.is_dir():
                combined += "\n".join(self._read(child) for child in path.glob("*.py"))
            else:
                combined += "\n" + self._read(path)
        lowered = combined.lower()
        failures = [f"unsafe enablement claim: {phrase}" for phrase in forbidden_claims if phrase in lowered]
        return self._result(criterion, failures, sources)

    def check_m12_control_center_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/control_center/__init__.py",
            "src/ultimate_ai_agent/core/control_center/enums.py",
            "src/ultimate_ai_agent/core/control_center/manifest.py",
            "src/ultimate_ai_agent/core/control_center/dashboard.py",
            "src/ultimate_ai_agent/core/control_center/actions.py",
            "src/ultimate_ai_agent/core/control_center/summaries.py",
            "src/ultimate_ai_agent/core/control_center/validation.py",
            "src/ultimate_ai_agent/core/control_center/policy.py",
            "tests/test_control_center_manifest.py",
            "tests/test_control_center_dashboard.py",
            "tests/test_control_center_action_preview.py",
            "tests/test_control_center_api_routes.py",
            "tests/test_control_center_no_execution.py",
            "tests/test_m12_gate_integration.py",
            "docs/control_center/CONTROL_CENTER_CONTRACT.md",
            "docs/control_center/DASHBOARD_SNAPSHOT.md",
            "docs/control_center/ACTION_PREVIEW_POLICY.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m12_control_center_manifest_read_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.control_center import ControlCenterCapabilityStatus, build_control_center_manifest

        manifest = build_control_center_manifest()
        allowed_statuses = {
            ControlCenterCapabilityStatus.available_read_only.value,
            ControlCenterCapabilityStatus.preview_only.value,
            ControlCenterCapabilityStatus.validation_only.value,
            ControlCenterCapabilityStatus.planned_disabled.value,
            ControlCenterCapabilityStatus.blocked.value,
            ControlCenterCapabilityStatus.not_implemented.value,
        }
        failures = []
        for surface in manifest.surfaces:
            if surface.status not in allowed_statuses:
                failures.append(f"{surface.surface} has unsafe status {surface.status}")
            if surface.execution_allowed:
                failures.append(f"{surface.surface} allows execution")
        for capability in [
            "runtime_execution",
            "model_execution",
            "provider_invocation",
            "remote_dispatch",
            "mobile_sensor_access",
            "plugin_enablement",
            "frontend_build_tooling",
        ]:
            if capability not in manifest.blocked_capabilities:
                failures.append(f"missing blocked capability: {capability}")
        if manifest.metadata.get("frontend_implemented") is not False:
            failures.append("manifest does not mark frontend unimplemented")
        if manifest.metadata.get("production_control_center") is not False:
            failures.append("manifest implies production Control Center")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/control_center/manifest.py"])

    def check_m12_control_center_dashboard_secret_safe(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.control_center import build_control_center_dashboard
        from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like

        snapshot = build_control_center_dashboard(api_route_count=74, foundation_gate_status="passed")
        failures = []
        if contains_secret_like(snapshot.model_dump(mode="json")):
            failures.append("dashboard contains secret-like values")
        if snapshot.runtime_readiness_summary.production_ready:
            failures.append("dashboard claims production runtime readiness")
        if snapshot.remote_worker_summary.execution_enabled:
            failures.append("dashboard enables remote worker execution")
        if snapshot.mobile_planning_summary.sensor_access_enabled:
            failures.append("dashboard enables mobile sensors")
        if snapshot.plugin_governance_summary.plugin_enablement_allowed:
            failures.append("dashboard enables plugins")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/control_center/dashboard.py"])

    def check_m12_control_center_action_preview_no_execution(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.core.control_center import (
            ControlCenterActionKind,
            ControlCenterRiskLevel,
            preview_control_center_action,
        )

        base = {
            "request_id": "m12_gate_preview",
            "actor_context": {"actor_type": "user", "actor_id": "local_operator"},
            "action_kind": ControlCenterActionKind.view_status,
            "target_ref": "dashboard",
            "purpose": "review status",
            "risk_level": ControlCenterRiskLevel.safe,
            "data_classification": "system_internal",
            "consent_refs": [],
        }
        failures = []
        safe = preview_control_center_action(base)
        if not safe.allowed:
            failures.append("safe preview was not allowed")
        unsafe_cases = [
            ("execute action", {**base, "action_kind": ControlCenterActionKind.disabled_execute}),
            ("runtime execute", {**base, "target_ref": "runtime/execute/model"}),
            ("remote dispatch", {**base, "target_ref": "remote-workers/dispatch/job"}),
            ("plugin enable", {**base, "target_ref": "plugins/enable/build-web-apps"}),
            ("mobile sensor", {**base, "target_ref": "mobile/sensors/camera"}),
            ("provider invocation", {**base, "metadata": {"claim": "provider invocation requested"}}),
            ("credential use", {**base, "metadata": {"claim": "credential use requested"}}),
            ("mutation", {**base, "metadata": {"claim": "mutate file requested"}}),
            ("arbitrary approval", {**base, "approval_ref": "approval_any_string"}),
        ]
        for label, payload in unsafe_cases:
            decision = preview_control_center_action(payload)
            if decision.allowed:
                failures.append(f"unsafe preview allowed: {label}")
            if decision.metadata.get("executed") is not False:
                failures.append(f"preview execution marker unsafe: {label}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/control_center/actions.py"])

    def check_m12_control_center_api_read_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items
        from ultimate_ai_agent.api.openapi import FORBIDDEN_ROUTE_FRAGMENTS

        routes = iter_api_route_items(app)
        paths = {route.path: route for route in routes}
        required = {
            "/control-center/manifest",
            "/control-center/dashboard",
            "/control-center/status",
            "/control-center/routes",
            "/control-center/approvals/summary",
            "/control-center/runtime-readiness/summary",
            "/control-center/foundation-gate/summary",
            "/control-center/actions/preview",
        }
        failures = [f"missing control-center route: {path}" for path in sorted(required - set(paths))]
        for path in sorted(path for path in paths if path.startswith("/control-center")):
            route = paths[path]
            if "control-center" not in route.tags:
                failures.append(f"{path} has unexpected tags {route.tags}")
            if not route.validation_only:
                failures.append(f"{path} is not read-only/preview-only")
        unsafe_routes = [
            path
            for path in paths
            if path.startswith("/control-center") and any(fragment in path for fragment in FORBIDDEN_ROUTE_FRAGMENTS)
        ]
        failures.extend(f"forbidden control-center route present: {path}" for path in sorted(unsafe_routes))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py", "src/ultimate_ai_agent/api/openapi.py"])

    def check_m12_no_frontend_dependencies(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden_paths = [
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "vite.config.ts",
            "vite.config.js",
            "next.config.js",
            "next.config.ts",
            "tailwind.config.js",
            "tailwind.config.ts",
            "components.json",
            "node_modules",
        ]
        failures = [f"frontend artifact exists: {path}" for path in forbidden_paths if (self.root / path).exists()]
        pyproject = self._read(self.root / "pyproject.toml").lower()
        for dependency in ["react", "next", "vite", "tailwind", "shadcn"]:
            if dependency in pyproject:
                failures.append(f"frontend dependency marker in pyproject: {dependency}")
        return self._result(criterion, failures, forbidden_paths + ["pyproject.toml"])

    def check_m12_no_runtime_network_mobile_plugin_expansion(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        package = self.root / "src/ultimate_ai_agent/core/control_center"
        forbidden_starts = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "urllib",
            "from " + "urllib import",
            "import " + "socket",
            "from " + "socket import",
            "import " + "subprocess",
            "from " + "subprocess import",
            "import " + "openai",
            "from " + "openai import",
            "import " + "anthropic",
            "from " + "anthropic import",
            "import " + "tiktoken",
            "import " + "tokenizers",
        ]
        forbidden_fragments = [
            "urlopen",
            "billing",
            "eval(",
            "exec(",
            "enable_plugin(",
            "dispatch_remote",
            "mobile_sensor_access=true",
            "runtime_execution=true",
            "provider_invocation=true",
            "browser automation is enabled",
        ]
        failures = []
        for path in sorted(package.glob("*.py")):
            rel_path = str(path.relative_to(self.root))
            for line_no, stripped in enumerate(self._read(path).splitlines(), start=1):
                stripped = stripped.strip().lower()
                if stripped.startswith("[") or self._is_static_scanner_text(stripped):
                    continue
                if any(stripped.startswith(pattern) for pattern in forbidden_starts):
                    failures.append(f"{rel_path}:{line_no} forbidden import")
                if any(fragment in stripped for fragment in forbidden_fragments):
                    failures.append(f"{rel_path}:{line_no} forbidden runtime expansion fragment")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/control_center"])

    def check_m13_web_control_center_files_present(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        required = [
            "apps/control-center/package.json",
            "apps/control-center/package-lock.json",
            "apps/control-center/index.html",
            "apps/control-center/vite.config.ts",
            "apps/control-center/tsconfig.json",
            "apps/control-center/src/App.tsx",
            "apps/control-center/src/main.tsx",
            "apps/control-center/src/api/client.ts",
            "apps/control-center/src/api/endpoints.ts",
            "apps/control-center/src/api/redaction.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "apps/control-center/src/components/ActionPreviewForm.tsx",
            "apps/control-center/src/App.test.tsx",
            "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
            "docs/control_center/FRONTEND_SAFETY_POLICY.md",
            "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
        ]
        failures = [f"missing {path}" for path in required if not (self.root / path).exists()]
        return self._result(criterion, failures, required)

    def check_m13_web_shell_read_only_preview_only(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        app_root = self.root / "apps/control-center"
        package = json.loads(self._read(app_root / "package.json") or "{}")
        deps = set(package.get("dependencies", {})) | set(package.get("devDependencies", {}))
        allowed_deps = {
            "react",
            "react-dom",
            "@vitejs/plugin-react",
            "vite",
            "typescript",
            "@types/react",
            "@types/react-dom",
            "@types/node",
            "vitest",
            "@testing-library/react",
            "@testing-library/jest-dom",
            "jsdom",
        }
        forbidden_deps = {
            "next",
            "tailwindcss",
            "stripe",
            "@stripe/stripe-js",
            "@supabase/supabase-js",
            "firebase",
            "auth0-js",
            "openai",
            "anthropic",
            "expo",
            "react-native",
            "electron",
            "playwright",
            "puppeteer",
        }
        failures = [f"unexpected frontend dependency: {dep}" for dep in sorted(deps - allowed_deps)]
        failures.extend(f"forbidden frontend dependency: {dep}" for dep in sorted(deps & forbidden_deps))
        source_paths = [
            *sorted((app_root / "src").rglob("*.ts")),
            *sorted((app_root / "src").rglob("*.tsx")),
            *sorted((app_root / "src").rglob("*.css")),
        ]
        source_text = "\n".join(
            self._read(path).lower()
            for path in source_paths
            if path.is_file() and ".test." not in path.name
        )
        forbidden = [
            "/control-center/actions/execute",
            "/control-center/plugins/enable",
            "/control-center/runtime/execute",
            "/control-center/remote-workers/dispatch",
            "/control-center/mobile/sensors",
            "/model-runtime/execute",
            "document.cookie",
            "localstorage",
            "sessionstorage",
            "navigator.geolocation",
            "mediadevices",
            "getusermedia",
            "chrome.",
            "computer use",
            "xcode",
            "app store connect",
            "keychain",
        ]
        failures.extend(f"forbidden frontend source fragment: {fragment}" for fragment in forbidden if fragment in source_text)
        if "no authority to run actions" not in source_text:
            failures.append("frontend does not visibly mark no action authority")
        return self._result(criterion, failures, ["apps/control-center/package.json", "apps/control-center/src"])

    def check_m13_action_preview_ui_posts_only_to_preview(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        app_root = self.root / "apps/control-center/src"
        endpoints = self._read(app_root / "api/endpoints.ts")
        client = self._read(app_root / "api/client.ts")
        failures = []
        if 'actionPreview: "/control-center/actions/preview"' not in endpoints:
            failures.append("action preview endpoint declaration missing")
        if endpoints.count("/control-center/actions/preview") != 1:
            failures.append("action preview endpoint should appear exactly once in endpoint declarations")
        if "method: \"POST\"" not in client:
            failures.append("frontend client does not declare preview POST")
        if "API_ENDPOINTS.actionPreview" not in client:
            failures.append("frontend client does not post to actionPreview endpoint constant")
        post_count = sum(1 for path in app_root.rglob("*.ts*") if "method: \"POST\"" in self._read(path))
        if post_count != 1:
            failures.append(f"unexpected frontend POST declaration count: {post_count}")
        return self._result(criterion, failures, ["apps/control-center/src/api/endpoints.ts", "apps/control-center/src/api/client.ts"])

    def check_m13_mock_data_safe_non_authoritative(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        mock_path = self.root / "apps/control-center/src/mocks/controlCenterData.ts"
        text = self._read(mock_path).lower()
        failures = []
        required_safe_fragments = [
            "mock: true",
            "production_control_center: false",
            "production_ready: false",
            "real_model_runtime_ready: false",
            "remote_execution_ready: false",
            "mobile_sensor_ready: false",
            "plugin_or_native_build_ready: false",
            "execution_enabled: false",
            "dispatch_enabled: false",
            "sensor_access_enabled: false",
            "plugin_enablement_allowed: false",
            "native_build_tools_enabled: false",
            "model_output_authoritative: false",
        ]
        for fragment in required_safe_fragments:
            if fragment not in text:
                failures.append(f"mock data missing safe fragment: {fragment}")
        forbidden = [
            "production_ready: true",
            "real_model_runtime_ready: true",
            "remote_execution_ready: true",
            "mobile_sensor_ready: true",
            "plugin_or_native_build_ready: true",
            "execution_enabled: true",
            "dispatch_enabled: true",
            "sensor_access_enabled: true",
            "plugin_enablement_allowed: true",
            "native_build_tools_enabled: true",
            "api_key",
            "password",
            "authorization",
            "cookie",
        ]
        failures.extend(f"unsafe mock data fragment: {fragment}" for fragment in forbidden if fragment in text)
        return self._result(criterion, failures, ["apps/control-center/src/mocks/controlCenterData.ts"])

    def check_m13_no_tracked_generated_or_native_artifacts(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        forbidden_paths = [
            "apps/control-center/.next",
            "apps/control-center/ios",
            "apps/control-center/android",
            "apps/control-center/Podfile",
            "apps/control-center/Package.swift",
            "apps/control-center/electron",
        ]
        failures = [f"forbidden frontend/native artifact exists: {path}" for path in forbidden_paths if (self.root / path).exists()]
        gitignore = self._read(self.root / ".gitignore")
        for required_ignore in ["node_modules/", "dist/", "coverage/", ".env"]:
            if required_ignore not in gitignore:
                failures.append(f".gitignore missing frontend artifact guard: {required_ignore}")
        return self._result(criterion, failures, forbidden_paths + [".gitignore"])

    def check_m13_backend_api_contract_unchanged(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items

        routes = iter_api_route_items(app)
        paths = {route.path: route for route in routes}
        failures = []
        if len(paths) != 74:
            failures.append(f"API path count changed from M12 contract: {len(paths)}")
        control_center_routes = [path for path in paths if path.startswith("/control-center")]
        if len(control_center_routes) != 8:
            failures.append(f"unexpected Control Center route count: {len(control_center_routes)}")
        forbidden = [
            "/control-center/actions/execute",
            "/control-center/plugins/enable",
            "/control-center/runtime/execute",
            "/control-center/remote-workers/dispatch",
            "/control-center/mobile/sensors",
            "/control-center/frontend",
        ]
        failures.extend(f"forbidden Control Center route present: {path}" for path in forbidden if path in paths)
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py", "apps/control-center"])

    def check_m13_frontend_no_sensitive_browser_apis(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        app_root = self.root / "apps/control-center/src"
        forbidden = [
            "localstorage",
            "sessionstorage",
            "document.cookie",
            "indexeddb",
            "cachestorage",
            "serviceworker",
            "navigator.credentials",
            "clipboard.write",
            "navigator.geolocation",
            "navigator.mediadevices",
            "notification.requestpermission",
            "pushmanager",
        ]
        failures = []
        for path in [*app_root.rglob("*.ts"), *app_root.rglob("*.tsx")]:
            if ".test." in path.name or "test" in path.parts:
                continue
            lowered = self._read(path).lower()
            rel = path.relative_to(self.root)
            failures.extend(f"{rel} forbidden browser API: {fragment}" for fragment in forbidden if fragment in lowered)
        return self._result(criterion, failures, ["apps/control-center/src"])

    def check_m13_control_center_frontend_safety_verifier_passes(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        import importlib.util

        script = self.root / "scripts/verify_control_center_frontend.py"
        failures = []
        if not script.exists():
            failures.append("scripts/verify_control_center_frontend.py missing")
            return self._result(criterion, failures, [str(script.relative_to(self.root))])
        spec = importlib.util.spec_from_file_location("verify_control_center_frontend", script)
        if spec is None or spec.loader is None:
            failures.append("could not load frontend safety verifier")
            return self._result(criterion, failures, [str(script.relative_to(self.root))])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        failures.extend(module.verify(self.root))
        return self._result(criterion, failures, ["scripts/verify_control_center_frontend.py", "apps/control-center"])

    def _skipped(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        return FoundationGateResult(
            criterion_id=criterion.criterion_id,
            status=FoundationGateStatus.skipped,
            safe_message="No evaluator registered for criterion.",
            warnings=["missing evaluator"],
        )

    def _result(
        self,
        criterion: FoundationGateCriterion,
        failures: List[str],
        evidence_refs: List[str],
        warnings: Optional[List[str]] = None,
    ) -> FoundationGateResult:
        status = FoundationGateStatus.failed if failures else FoundationGateStatus.passed
        return FoundationGateResult(
            criterion_id=criterion.criterion_id,
            status=status,
            safe_message=criterion.failure_message if failures else f"{criterion.name} passed.",
            evidence_refs=evidence_refs,
            failures=failures,
            warnings=warnings or [],
        )

    def _active_version(self) -> Optional[str]:
        return self._regex_first(self.root / "VERSION.md", r"Current active baseline:\s*\*\*v?(\d+\.\d+\.\d+)\*\*")

    def _regex_first(self, path: Path, pattern: str) -> Optional[str]:
        match = re.search(pattern, self._read(path))
        return match.group(1) if match else None

    def _runtime_lines(self) -> Iterable[tuple[str, int, str]]:
        for rel_path in self._tracked_runtime_files():
            for line_no, line in enumerate(self._read(self.root / rel_path).splitlines(), start=1):
                yield rel_path, line_no, line.strip()

    def _tracked_runtime_files(self) -> List[str]:
        if not self.src_root.exists():
            return []
        files = []
        for path in sorted(self.src_root.rglob("*.py")):
            rel_path = str(path.relative_to(self.root))
            if "__pycache__" not in rel_path:
                files.append(rel_path)
        return files

    def _read(self, path: Path) -> str:
        if not path.exists() or not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def _is_static_scanner_text(self, stripped: str) -> bool:
        return (
            stripped.startswith(('"', "'", "#"))
            or " = [" in stripped
            or " = (" in stripped
            or stripped.startswith(("forbidden = ", "forbidden_starts = ", "forbidden_contains = "))
            or stripped.startswith('if ".get(" in stripped')
        )

    def _m8_gate_manifest(self) -> dict:
        return {
            "adapter_id": "m8_gate_adapter",
            "runtime_kind": "simulated",
            "display_name": "M8 Gate Simulated Adapter",
            "description": "Deterministic simulated adapter for Foundation Gate checks.",
            "supported_provider_kinds": ["local_runtime"],
            "supported_capabilities": ["chat"],
            "safety_mode": "simulated",
            "accepts_model_profile_ids": ["m8_gate_profile"],
            "requires_credential_ref": False,
            "allowed_credential_refs": [],
            "supports_streaming": False,
            "supports_tools": False,
            "supports_json_mode": True,
            "supports_structured_output": True,
            "max_context_tokens": 8192,
            "max_input_tokens": 1024,
            "max_output_tokens": 512,
            "owner": "foundation_gate",
            "source": "foundation_gate",
            "version": "0.0.0",
            "enabled": True,
        }

    def _m8_gate_request(self) -> dict:
        return {
            "runtime_request_id": "m8_gate_request",
            "run_id": "run_foundation_gate",
            "model_profile_id": "m8_gate_profile",
            "model_id": "m8_gate_model",
            "adapter_id": "m8_gate_adapter",
            "actor_context": self._actor().model_dump(mode="json"),
            "prompt_summary": "Summarize referenced context safely.",
            "input_refs": ["context_pack:m8_gate"],
            "output_format": "text",
            "estimated_input_tokens": 10,
            "max_output_tokens": 10,
            "safety_mode": "simulated",
            "data_classification": {
                "classification": "project_private",
                "source": "foundation_gate",
            },
        }

    def _m85_gate_approval_request(self, subject_id: str = "m85_gate_subject"):
        from datetime import timedelta

        from ultimate_ai_agent.core.approvals import ApprovalRequest, ApprovalRiskLevel, ApprovalSubjectType
        from ultimate_ai_agent.core.time import utc_now

        return ApprovalRequest(
            approval_request_id=f"areq_{subject_id}",
            run_id="run_foundation_gate",
            subject_type=ApprovalSubjectType.model_route,
            subject_id=subject_id,
            actor_context=self._actor(),
            requested_action="route_cloud_model",
            purpose="Foundation Gate approval authority check.",
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(classification=ClassificationValue.sensitive_personal, source="foundation_gate"),
            resource_refs=["m7_gate_cloud"],
            consent_refs=["consent_foundation_gate"],
            expires_at=utc_now() + timedelta(minutes=30),
        )

    def _m85_runtime_manifest(self):
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeAdapterManifest, ModelRuntimeKind, ModelRuntimeSafetyMode

        return ModelRuntimeAdapterManifest(
            adapter_id="m85_gate_adapter",
            runtime_kind=ModelRuntimeKind.simulated,
            display_name="M8.5 Gate Simulated Adapter",
            description="Simulated adapter for M8.5 approval checks.",
            supported_provider_kinds=["cloud_provider", "local_runtime"],
            supported_capabilities=["chat"],
            safety_mode=ModelRuntimeSafetyMode.simulated,
            accepts_model_profile_ids=["m7_gate_cloud"],
            requires_credential_ref=False,
            allowed_credential_refs=[],
            supports_streaming=False,
            supports_tools=False,
            supports_json_mode=True,
            supports_structured_output=True,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
            enabled=True,
        )

    def _m9_loopback_endpoint(self):
        from ultimate_ai_agent.core.model_runtime import LoopbackRuntimeEndpoint, ModelRuntimeKind

        return LoopbackRuntimeEndpoint(
            endpoint_id="m9_gate_loopback",
            base_url="http" + "://127.0.0.1:11434/api/generate",
            allowed_hosts=["127.0.0.1", "localhost", "::1"],
            runtime_kind=ModelRuntimeKind.local_stub,
            model_id="local_policy_model",
            enabled=True,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
        )

    def _m9_loopback_policy(self):
        from ultimate_ai_agent.core.model_runtime import LoopbackRuntimePolicy

        return LoopbackRuntimePolicy(
            policy_id="m9_gate_policy",
            allow_real_loopback_execution=True,
            max_input_tokens=4096,
            max_output_tokens=1024,
        )

    def _m9_runtime_manifest(self):
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeAdapterManifest, ModelRuntimeKind, ModelRuntimeSafetyMode

        return ModelRuntimeAdapterManifest(
            adapter_id="m9_gate_adapter",
            runtime_kind=ModelRuntimeKind.local_stub,
            display_name="M9 Gate Local Loopback Adapter",
            description="Local/dev loopback adapter for Foundation Gate checks.",
            supported_provider_kinds=["local_runtime"],
            supported_capabilities=["chat"],
            safety_mode=ModelRuntimeSafetyMode.local_loopback_dev,
            accepts_model_profile_ids=["m7_gate_local"],
            requires_credential_ref=False,
            allowed_credential_refs=[],
            supports_streaming=False,
            supports_tools=False,
            supports_json_mode=True,
            supports_structured_output=True,
            max_context_tokens=8192,
            max_input_tokens=4096,
            max_output_tokens=1024,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
            enabled=True,
        )

    def _m9_runtime_request(self, approval_ref: Optional[str] = None):
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeOutputFormat, ModelRuntimeRequest, ModelRuntimeSafetyMode

        return ModelRuntimeRequest(
            runtime_request_id="m9_gate_runtime_request",
            run_id="run_foundation_gate",
            route_decision_ref="m9_gate_selected_route",
            model_profile_id="m7_gate_local",
            model_id="local_policy_model",
            adapter_id="m9_gate_adapter",
            actor_context=self._actor(),
            prompt_summary="Foundation Gate local loopback metadata check.",
            input_refs=["context_pack:m9_gate"],
            output_format=ModelRuntimeOutputFormat.text,
            estimated_input_tokens=100,
            max_output_tokens=50,
            safety_mode=ModelRuntimeSafetyMode.local_loopback_dev,
            data_classification=DataClassification(classification=ClassificationValue.project_private, source="foundation_gate"),
            consent_refs=["consent_foundation_gate"],
            approval_ref=approval_ref,
            secret_handle_refs=[],
            event_ref="evt_m9_gate",
            trace_id="trace_m9_gate",
            metadata={"route_reason_codes": ["SELECTED_PROFILE"]},
        )

    def _m10_smoke_endpoint(self, **overrides):
        from ultimate_ai_agent.core.model_runtime import LoopbackRuntimeEndpoint, ModelRuntimeKind

        payload = {
            "endpoint_id": "m10_gate_smoke_endpoint",
            "base_url": "http" + "://127.0.0.1:11434/api/generate",
            "allowed_hosts": ["127.0.0.1", "localhost", "::1"],
            "runtime_kind": ModelRuntimeKind.local_stub,
            "model_id": "m10_gate_smoke_model",
            "enabled": True,
            "owner": "foundation_gate",
            "source": "foundation_gate",
            "version": "0.0.0",
        }
        payload.update(overrides)
        return LoopbackRuntimeEndpoint(**payload)

    def _m10_smoke_request(self, **overrides):
        from ultimate_ai_agent.core.model_runtime import DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT, ManualLoopbackSmokePolicy, ManualLoopbackSmokeRequest

        payload = {
            "smoke_request_id": "m10_gate_smoke_request",
            "run_id": "run_foundation_gate",
            "endpoint": self._m10_smoke_endpoint(),
            "model_id": "m10_gate_smoke_model",
            "approval_ref": "approval_m10_gate",
            "fixed_prompt": DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT,
            "expected_marker": "UAA_LOCAL_SMOKE_OK",
            "policy": ManualLoopbackSmokePolicy(policy_id="m10_gate_smoke_policy", enable_manual_smoke=True),
            "actor_context": self._actor(),
            "data_classification": DataClassification(classification=ClassificationValue.public, source="foundation_gate"),
        }
        payload.update(overrides)
        return ManualLoopbackSmokeRequest(**payload)

    def _m105_node_registry(self):
        from ultimate_ai_agent.core.remote_workers import (
            NodeCapabilitySet,
            NodeIdentity,
            RemoteNode,
            RemoteNodeRegistry,
            RemoteNodeStatus,
        )

        registry = RemoteNodeRegistry()
        registry.register_node(
            RemoteNode(
                node_id="mock_node",
                identity=NodeIdentity(
                    node_id="mock_node",
                    display_name="Mock Node",
                    owner="foundation_gate",
                    source="foundation_gate",
                    version="0.0.0",
                ),
                status=RemoteNodeStatus.mock_available,
                capabilities=NodeCapabilitySet(),
                allowed_transport_ids=["mock_metadata"],
            )
        )
        return registry

    def _m105_transport_registry(self):
        from ultimate_ai_agent.core.remote_workers import default_remote_transport_registry

        return default_remote_transport_registry()

    def _m105_remote_job(self, **overrides):
        from ultimate_ai_agent.core.remote_workers import RemoteAuditContext, RemoteJobEnvelope, RemoteRiskLevel

        payload = {
            "job_id": "m105_gate_job",
            "correlation_id": "m105_gate_corr",
            "node_id": "mock_node",
            "transport_id": "mock_metadata",
            "task_summary": "Validate remote worker dry-run metadata.",
            "requested_capabilities": ["dry_run"],
            "risk_level": RemoteRiskLevel.low,
            "audit_context": RemoteAuditContext(
                run_id="run_foundation_gate",
                correlation_id="m105_gate_corr",
                actor_context=self._actor(),
            ),
        }
        payload.update(overrides)
        return RemoteJobEnvelope(**payload)

    def _actor(self) -> ActorContext:
        return ActorContext(
            actor_type=ActorType.system_worker,
            actor_id="foundation_gate",
            authority_source=AuthoritySource.system_policy,
        )

    def _gate_local_profile(
        self,
        cost_per_1k_input_tokens: Optional[float] = None,
        cost_per_1k_output_tokens: Optional[float] = None,
    ) -> ModelCapabilityProfile:
        return ModelCapabilityProfile(
            model_profile_id="m7_gate_local",
            provider_kind=ModelProviderKind.local_runtime,
            runtime_id="rt_gate",
            model_id="local_policy_model",
            display_name="Local Policy Model",
            capabilities=[ModelTaskCapability.chat, ModelTaskCapability.coding],
            privacy_class=ModelPrivacyClass.local_only,
            max_context_tokens=8192,
            cost_per_1k_input_tokens=cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=cost_per_1k_output_tokens,
            enabled=True,
            owner="core.gate",
            source="foundation_gate",
            version="0.0.0",
        )

    def _gate_cloud_profile(self) -> ModelCapabilityProfile:
        return ModelCapabilityProfile(
            model_profile_id="m7_gate_cloud",
            provider_kind=ModelProviderKind.cloud_provider,
            provider_id="provider_gate",
            model_id="cloud_policy_model",
            display_name="Cloud Policy Model",
            capabilities=[ModelTaskCapability.chat],
            privacy_class=ModelPrivacyClass.cloud_allowed,
            max_context_tokens=8192,
            cost_per_1k_input_tokens=0.01,
            cost_per_1k_output_tokens=0.03,
            enabled=True,
            owner="core.gate",
            source="foundation_gate",
            version="0.0.0",
        )

    def _gate_route_request(
        self,
        profile: ModelCapabilityProfile,
        data_classification: ClassificationValue = ClassificationValue.project_private,
        approval_ref: Optional[str] = None,
        context_budget: Optional[ContextBudget] = None,
        policy: Optional[ModelRoutingPolicy] = None,
    ) -> ModelRouteRequest:
        return ModelRouteRequest(
            request_id="m7_gate_route_policy",
            run_id="run_foundation_gate",
            actor_context=self._actor(),
            task_class="coding",
            prompt_summary="Foundation Gate model routing metadata check.",
            data_classification=DataClassification(classification=data_classification, source="foundation_gate"),
            required_capabilities=[ModelTaskCapability.chat],
            estimated_input_tokens=1000,
            estimated_output_tokens=500,
            context_budget=context_budget,
            routing_policy=policy
            or ModelRoutingPolicy(
                policy_id="m7_gate_route_policy",
                required_capabilities=[ModelTaskCapability.chat],
                prefer_local=True,
                allow_cloud=False,
                allow_paid=False,
            ),
            available_profiles=[profile],
            approval_ref=approval_ref,
        )
