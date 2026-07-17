# ruff: noqa: E402,F401,F403,F405
import importlib.util
from pathlib import Path
import json
import os
import re
import sys
import tempfile
from typing import Any, Callable, Dict, Iterable, List, Optional

from pydantic import ValidationError

from ultimate_ai_agent.core.consent import ConsentLedger
from ultimate_ai_agent.core.consent.enums import DataBoundary
from ultimate_ai_agent.core.files import FileKind, FileRef, FileSensitivity
from ultimate_ai_agent.core.gate.criteria import (
    FoundationGateCriterion,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.evaluation_context import GateEvaluationContext
from ultimate_ai_agent.core.gate.reports import (
    FoundationGateReport,
    FoundationGateResult,
    build_foundation_gate_report,
)
from ultimate_ai_agent.core.gate.web_hybrid_static_policy import (
    WEB_HYBRID_EXACT_ADAPTER_FILES,
    _is_web_hybrid_promoted_static_fragment,
)
from ultimate_ai_agent.core.gate.evaluator_modules.route_side_effects import (
    forbidden_route_fragment_failures,
    operation_id_failures,
)
from ultimate_ai_agent.core.gate.shadow_replay import run_m5_shadow_replay
from ultimate_ai_agent.core.sandbox_calculation.static_safety import (
    sealed_backend_fragment_allowed as sealed_fragment_allowed,
)
from ultimate_ai_agent.core.evidence_signing.static_safety import (
    portable_evidence_helper_fragment_allowed,
)
from ultimate_ai_agent.core.communications.matrix_harness.static_safety import (
    is_exact_matrix_harness_shell_scan_line,
    matrix_harness_fragment_allowed,
)
from ultimate_ai_agent.core.communications.matrix_session.static_safety import (
    matrix_session_fragment_allowed,
)
from ultimate_ai_agent.core.communications.matrix_sync.static_safety import (
    matrix_sync_fragment_allowed,
)
from ultimate_ai_agent.core.communications.matrix_messaging.static_safety import (
    matrix_messaging_fragment_allowed,
)
from ultimate_ai_agent.core.context_budget import ContextBudget
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.costs import (
    BudgetScope,
    BudgetStatus,
    CostBudget,
    CostEstimate,
    CostGovernor,
)
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
from ultimate_ai_agent.core.memory.enums import (
    MemoryAuthority,
    MemoryScope,
    MemorySensitivity,
    MemoryType,
)
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
from ultimate_ai_agent.core.truth import (
    EvidenceItem,
    EvidenceManifest,
    TruthSourceManifest,
)
from ultimate_ai_agent.core.truth.claims import ClaimEvidence
from ultimate_ai_agent.core.truth.enums import (
    ClaimVerificationStatus,
    SourceFreshnessStatus,
    TruthAuthorityLevel,
    TruthSourceType,
)


def _roadmap_row_present(text: str, row: str) -> bool:
    return (
        row in text
        or row.replace("planned/provisional", "implemented/released") in text
    )


def _version_doc_marks_milestone_implemented(text: str, milestone: str) -> bool:
    return (
        f"checkpoint {milestone} is implemented/released" in text
        or f"{milestone} is implemented/released" in text
        or re.search(
            rf"\b{re.escape(milestone)}\b[^.\n]*\bare implemented/released\b", text
        )
        is not None
    )


# Route-boundary evaluators are imported here to preserve the historical public facade.
from ultimate_ai_agent.core.gate.evaluator_modules.route_boundaries import *  # noqa: F401,F403

EXPECTED_M13_CONTROL_CENTER_ROUTE_COUNT = 170

STATIC_SAFETY_EVALUATOR_DATA_FILES = frozenset(
    {
        "src/ultimate_ai_agent/core/gate/criteria.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/gate/legacy_checks.py",
        "src/ultimate_ai_agent/core/gate/evaluator_modules/route_boundaries.py",
        "src/ultimate_ai_agent/core/gate/legacy_support.py",
        "src/ultimate_ai_agent/core/gate/web_hybrid_static_policy.py",
    }
    | {
        "src/ultimate_ai_agent/core/gate/legacy_check_families/"
        f"part_{part_number:03d}.py"
        for part_number in range(1, 45)
    }
    | {
        f"src/ultimate_ai_agent/core/gate/criteria_families/{family_name}.py"
        for family_name in (
            "foundation_core",
            "runtime_authority_bootstrap",
            "control_center_shell",
            "product_spine_m21_m66",
            "safety_expansion_m67_m98",
            "post_m100_m99_m130",
            "autonomy_alpha_m131_m150",
            "local_model_m151_m167",
            "cross_release_docs",
        )
    }
)
STATIC_SAFETY_EVALUATOR_DATA_PREFIXES = (
    "src/ultimate_ai_agent/core/gate/checkpoint_builders/",
)
GOVERNED_RUNTIME_COMMAND_ADAPTER_STATIC_SCAN_ALLOWED_FILES = frozenset(
    {"src/ultimate_ai_agent/core/runtime_gateway/command.py"}
)


def runtime_subprocess_fragment_allowed(rel: str, text: str, fragment: str) -> bool:
    return (
        sealed_fragment_allowed(rel, text, fragment)
        or portable_evidence_helper_fragment_allowed(rel, text, fragment)
        or matrix_harness_fragment_allowed(rel, text, fragment)
        or matrix_session_fragment_allowed(rel, text, fragment)
        or matrix_sync_fragment_allowed(rel, text, fragment)
        or matrix_messaging_fragment_allowed(rel, text, fragment)
    )


def _is_static_safety_scan_allowed_file(rel: str, allowed_files: Iterable[str]) -> bool:
    return (
        rel in allowed_files
        or rel in STATIC_SAFETY_EVALUATOR_DATA_FILES
        or rel.startswith(STATIC_SAFETY_EVALUATOR_DATA_PREFIXES)
        or rel in GOVERNED_RUNTIME_COMMAND_ADAPTER_STATIC_SCAN_ALLOWED_FILES
    )


def _context_rglob(
    context: GateEvaluationContext | None, root: Path, pattern: str
) -> Iterable[Path]:
    return context.rglob(root, pattern) if context else root.rglob(pattern)


def _context_read_text(context: GateEvaluationContext | None, path: Path) -> str:
    return (
        context.read_text(path, encoding="utf-8")
        if context
        else path.read_text(encoding="utf-8")
    )


M36_SAFE_REF_PREFIXES = {
    "reviewPacketRef": "file-review-packet:",
    "previewResultRef": "redacted-file-preview-output:",
    "redactionSummaryRef": "file-review-redaction-summary:",
    "fileRef": "file-ref:",
    "safePathRef": "filesystem-preview-path:safe-root_",
}
M36_SAFE_REF_LABELS = {
    "reviewPacketRef": "review_packet_ref",
    "previewResultRef": "preview_result_ref",
    "redactionSummaryRef": "redaction_summary_ref",
    "fileRef": "file_ref",
    "safePathRef": "safe_path_ref",
}
M36_PRIVATE_OR_RAW_PATH_FRAGMENT = re.compile(
    r"(/Users/|/home/|[A-Za-z]:\\|\.\./|absolute_path|raw_absolute_path|raw file path)",
    re.IGNORECASE,
)
M36_MUTATING_FILE_REVIEW_REQUEST = re.compile(
    r"fetch\([^)]*(?:/files/review|/files/read|/context/propose|/context/inject|/memory/write|/tools/execute)[^)]*"
    r"method\s*:\s*['\"](?:POST|PUT|PATCH|DELETE)['\"]",
    re.IGNORECASE | re.DOTALL,
)


def m36_file_review_surface_failures(component_text: str, mock_text: str) -> List[str]:
    failures: List[str] = []
    for match in M36_MUTATING_FILE_REVIEW_REQUEST.finditer(component_text):
        failures.append(f"mutating M36 file review request: {match.group(0).strip()}")

    m36_index = mock_text.lower().find("m36filereview")
    m36_text = mock_text[m36_index:] if m36_index != -1 else mock_text
    for match in M36_PRIVATE_OR_RAW_PATH_FRAGMENT.finditer(m36_text):
        failures.append(
            f"private path fragment in M36 file review fixture: {match.group(0)}"
        )
    for field_name, prefix in M36_SAFE_REF_PREFIXES.items():
        for match in re.finditer(rf"{field_name}\s*:\s*['\"]([^'\"]+)['\"]", m36_text):
            value = match.group(1)
            if not value.startswith(prefix):
                label = M36_SAFE_REF_LABELS[field_name]
                failures.append(f"unsafe M36 {label} value: expected prefix {prefix}")
    return failures


def m37_control_center_surface_failures(component_text: str) -> List[str]:
    failures: List[str] = []
    lowered = component_text.lower()
    required = {
        "approve review-only control missing": "approve review-only",
        "deny review-only control missing": "deny review-only",
        "review-only persistence copy missing": "review-only persistence",
        "exact packet binding copy missing": "exact selected packet",
        "raw authority denial missing": "raw file access",
        "context proposal denial missing": "context proposal",
        "memory write denial missing": "memory writes",
        "export denial missing": "export",
        "execution denial missing": "execution",
    }
    for message, fragment in required.items():
        if fragment not in lowered:
            failures.append(message)
    for fragment in (
        "export raw",
        "download",
        "copy raw",
        "file picker",
        "root selector",
        "open raw file",
        "inject context",
        "write memory",
        "execute tool",
        "run tool",
        "call model",
    ):
        if fragment in lowered:
            failures.append(f"M37 component exposes forbidden control/copy: {fragment}")
    return failures


def _normalize_m34_active_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("|", " | ").lower()).strip()


def m34_active_currentness_failures(active_docs: Dict[str, str]) -> List[str]:
    failures: List[str] = []
    readme = _normalize_m34_active_text(active_docs.get("README.md", ""))
    if "v0.38.0 | m34 - broader file capability review | planned/provisional" in readme:
        failures.append("README.md must not list v0.38.0/M34 as planned/provisional")

    stale_m33_docs = sorted(
        rel_path
        for rel_path, text in active_docs.items()
        if rel_path.startswith(
            (
                "docs/tools/REDACTED_FILE_PREVIEW_",
                "docs/files/LOCAL_FILE_REDACTED_PREVIEW_",
            )
        )
        and "m34 remains planned/provisional" in text.lower()
    )
    if stale_m33_docs:
        failures.append(
            "active M33 docs must not say M34 remains planned/provisional after v0.38.0: "
            + ", ".join(stale_m33_docs)
        )

    return failures


def m22_local_runtime_forbidden_fragment_failures(
    root: Path, context: GateEvaluationContext | None = None
) -> List[str]:
    failures: List[str] = []
    runtime_root = root / "src" / "ultimate_ai_agent" / "core" / "model_runtime"
    if not runtime_root.exists():
        return failures
    for path in _context_rglob(context, runtime_root, "*.py"):
        rel = path.relative_to(root).as_posix()
        if any(part in M22_LOCAL_RUNTIME_SCAN_EXCLUDED_DIRS for part in path.parts):
            continue
        if rel in M22_LOCAL_RUNTIME_ALLOWED_SOURCE_FILES:
            continue
        text = _context_read_text(context, path).lower()
        for fragment in M22_FORBIDDEN_LOCAL_RUNTIME_FRAGMENTS:
            if fragment in text:
                failures.append(
                    f"M22 forbidden local runtime fragment in {rel}: {fragment}"
                )
    return failures


def m152_local_model_management_forbidden_fragment_failures(
    root: Path, context: GateEvaluationContext | None = None
) -> List[str]:
    failures: List[str] = []
    for rel_root in M152_STATIC_SCAN_ROOTS:
        scan_root = root / rel_root
        if not scan_root.exists():
            continue
        candidate_files: list[Path] = []
        for pattern in (
            "*.py",
            "*.ts",
            "*.tsx",
            "*.js",
            "*.jsx",
            "*.swift",
            "*.yml",
            "*.yaml",
            "*.json",
        ):
            candidate_files.extend(_context_rglob(context, scan_root, pattern))
        for path in sorted(candidate_files):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if _is_static_safety_scan_allowed_file(rel, M152_STATIC_SCAN_ALLOWED_FILES):
                continue
            text = _context_read_text(context, path)
            for fragment in M152_FORBIDDEN_SOURCE_FRAGMENTS:
                if fragment in text and not runtime_subprocess_fragment_allowed(
                    rel, text, fragment
                ):
                    failures.append(
                        f"M152 forbidden local model management fragment in {rel}: {fragment}"
                    )
    for rel in ["pyproject.toml", "apps/control-center/package.json"]:
        path = root / rel
        if not path.exists():
            continue
        text = _context_read_text(context, path).lower()
        for fragment in M152_FORBIDDEN_DEPENDENCY_FRAGMENTS:
            if fragment in text:
                failures.append(
                    f"M152 forbidden dependency fragment in {rel}: {fragment}"
                )
    return failures


def _is_doc_path(rel_path: str) -> bool:
    return rel_path == "docs" or rel_path.startswith("docs/")


def _iter_m21_openwebui_non_doc_paths(root: Path) -> Iterable[Path]:
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            children = list(current.iterdir())
        except OSError:
            continue
        for path in children:
            rel = path.relative_to(root).as_posix()
            if path.name in M21_OPENWEBUI_SCAN_EXCLUDED_DIRS or _is_doc_path(rel):
                continue
            yield path
            if path.is_dir():
                pending.append(path)


def m21_forbidden_openwebui_config_path_matches(root: Path) -> List[str]:
    matches: set[str] = set()
    for path in _iter_m21_openwebui_non_doc_paths(root):
        rel = path.relative_to(root).as_posix()
        lowered = rel.lower()
        if any(
            fragment in lowered
            for fragment in M21_FORBIDDEN_OPENWEBUI_CONFIG_PATH_FRAGMENTS
        ):
            matches.add(rel)
    return sorted(matches)


def m21_forbidden_openwebui_runtime_fragment_failures(
    root: Path, context: GateEvaluationContext | None = None
) -> List[str]:
    failures: List[str] = []
    implementation_roots = [root / "src", root / "apps", root / "scripts"]
    for implementation_root in implementation_roots:
        if not implementation_root.exists():
            continue
        candidate_files: list[Path] = []
        if implementation_root.name in {"src", "scripts"}:
            candidate_files.extend(_context_rglob(context, implementation_root, "*.py"))
        else:
            for pattern in ("*.ts", "*.tsx", "*.js", "*.jsx", "*.json"):
                candidate_files.extend(
                    _context_rglob(context, implementation_root, pattern)
                )
        for path in candidate_files:
            rel = path.relative_to(root).as_posix()
            if not path.is_file() or any(
                part in M21_OPENWEBUI_SCAN_EXCLUDED_DIRS for part in path.parts
            ):
                continue
            if _is_static_safety_scan_allowed_file(
                rel, M21_OPENWEBUI_ALLOWED_FRAGMENT_SCAN_FILES
            ):
                continue
            text = _context_read_text(context, path).lower()
            allowed_fragments = M21_OPENWEBUI_ALLOWED_FRAGMENT_SCAN_EXCEPTIONS.get(
                rel,
                frozenset(),
            )
            for pattern in M21_FORBIDDEN_OPENWEBUI_RUNTIME_PATTERNS:
                if pattern.search(text):
                    failures.append(
                        f"M21 forbidden OpenWebUI runtime/config import in {rel}: {pattern.pattern}"
                    )
            for fragment in M21_FORBIDDEN_OPENWEBUI_RUNTIME_FRAGMENTS:
                if fragment in text and fragment not in allowed_fragments:
                    failures.append(
                        f"M21 forbidden OpenWebUI runtime/config fragment in {rel}: {fragment}"
                    )
    return failures


def _control_center_frontend_verifier_failures(evaluator: Any) -> List[str]:
    script = evaluator.root / "scripts/verify_control_center_frontend.py"
    if not script.exists():
        return ["scripts/verify_control_center_frontend.py missing"]

    def run_verifier() -> List[str]:
        spec = importlib.util.spec_from_file_location(
            "verify_control_center_frontend", script
        )
        if spec is None or spec.loader is None:
            return ["could not load frontend safety verifier"]
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return list(module.verify(evaluator.root))

    return list(
        evaluator._context.cached_value(
            "control_center_frontend_verifier_failures",
            run_verifier,
        )
    )


# Export single-underscore historical helpers for compatibility modules.
__all__ = [name for name in globals() if not name.startswith("__")]
