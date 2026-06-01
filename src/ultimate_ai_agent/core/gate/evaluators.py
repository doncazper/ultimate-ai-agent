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
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
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
        for rel_path in self._tracked_runtime_files():
            content = self._read(self.root / rel_path)
            if rel_path != "src/ultimate_ai_agent/core/gate/evaluators.py" and "-----BEGIN" in content and "PRIVATE KEY-----" in content:
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

    def _actor(self) -> ActorContext:
        return ActorContext(
            actor_type=ActorType.system_worker,
            actor_id="foundation_gate",
            authority_source=AuthoritySource.system_policy,
        )
