"""Dependency-light policy shared by the legacy static verifier."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
WEB_HYBRID_POLICY_PATH = (
    ROOT
    / "src"
    / "ultimate_ai_agent"
    / "core"
    / "gate"
    / "web_hybrid_static_policy.py"
)
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
        "src/ultimate_ai_agent/core/gate/criteria_families/"
        f"{family_name}.py"
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
PORTABLE_EVIDENCE_KEYCHAIN_HELPER_FILES = frozenset(
    {
        "tools/macos/portable-evidence-keychain-helper/Package.swift",
        "tools/macos/portable-evidence-keychain-helper/README.md",
        "tools/macos/portable-evidence-keychain-helper/Sources/UAAPortableEvidenceKeychainHelper/main.swift",
    }
)


def _load_web_hybrid_policy() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "_uaa_web_hybrid_static_policy",
        WEB_HYBRID_POLICY_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("web-hybrid static policy could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_WEB_HYBRID_POLICY = _load_web_hybrid_policy()
WEB_HYBRID_EXACT_ADAPTER_FILES = _WEB_HYBRID_POLICY.WEB_HYBRID_EXACT_ADAPTER_FILES
_is_web_hybrid_promoted_static_fragment = (
    _WEB_HYBRID_POLICY._is_web_hybrid_promoted_static_fragment
)


def is_static_gate_scan_allowed_file(
    rel_path: str,
    allowed_files: Iterable[str],
) -> bool:
    return (
        rel_path in allowed_files
        or rel_path in STATIC_SAFETY_EVALUATOR_DATA_FILES
        or rel_path.startswith(STATIC_SAFETY_EVALUATOR_DATA_PREFIXES)
        or rel_path in GOVERNED_RUNTIME_COMMAND_ADAPTER_STATIC_SCAN_ALLOWED_FILES
    )


def is_exact_portable_evidence_keychain_helper_file(rel_path: str) -> bool:
    return rel_path in PORTABLE_EVIDENCE_KEYCHAIN_HELPER_FILES


def is_unapproved_static_fragment(
    *,
    rel: str,
    fragment: str,
    source: str,
    allowed_fragments: Iterable[str] = frozenset(),
) -> bool:
    return (
        fragment in source
        and fragment not in allowed_fragments
        and not _is_web_hybrid_promoted_static_fragment(rel, fragment, source)
    )


def repo_source_env(
    root: Path,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = dict(os.environ if environ is None else environ)
    src_path = str(root / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        src_path
        if not existing_pythonpath
        else f"{src_path}{os.pathsep}{existing_pythonpath}"
    )
    return env
