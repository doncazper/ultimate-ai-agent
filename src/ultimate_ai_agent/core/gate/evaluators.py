from pathlib import Path
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
        for path, line_no, stripped in self._runtime_lines():
            if self._is_static_scanner_text(stripped):
                continue
            if any(stripped.startswith(pattern) for pattern in forbidden_starts):
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
            "import " + "httpx",
            "urllib",
            "socket",
            "sub" + "process",
            "token" + "izer",
            "tiktoken",
            "sentencepiece",
            "bill" + "ing",
            "base" + "_url",
            ".post(",
            ".get(",
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
