#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "uaa-changed-verification-selection.v1"
FULL_COMMAND_REF = "command-ref:verification:full-local-gate"
CRITICAL_PATHS = {
    "Makefile",
    "apps/control-center/package-lock.json",
    "apps/control-center/package.json",
    "pyproject.toml",
    "package-lock.json",
    "scripts/verify_all.py",
    "scripts/run_foundation_gate.py",
}
CRITICAL_PREFIXES = (
    ".github/",
    "scripts/verification/",
    "src/ultimate_ai_agent/core/gate/",
    "tests/conftest.py",
)
FOCUSED_PYTEST_REFS_BY_SOURCE = {
    "src/ultimate_ai_agent/core/evals/capability_metrics.py": (
        "tests/test_agent_capability_evaluation.py",
    ),
    "src/ultimate_ai_agent/core/evals/capability_maturity.py": (
        "tests/test_capability_maturity_integrity.py",
    ),
    "src/ultimate_ai_agent/core/evals/regression.py": (
        "tests/test_m56_agent_eval_regression_harness.py",
    ),
}


@dataclass(frozen=True)
class Selection:
    tier: str
    changed_paths: tuple[str, ...]
    matched_rule_refs: tuple[str, ...]
    selected_command_refs: tuple[str, ...]
    selected_test_refs: tuple[str, ...]
    unknown_paths: tuple[str, ...]
    fallback_reason_refs: tuple[str, ...]
    status: str
    release_gate_equivalent: bool = False

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "mode": "local_dev_advisory",
            "tier": self.tier,
            "status": self.status,
            "changed_paths": list(self.changed_paths),
            "matched_rule_refs": list(self.matched_rule_refs),
            "selected_command_refs": list(self.selected_command_refs),
            "selected_test_refs": list(self.selected_test_refs),
            "unknown_paths": list(self.unknown_paths),
            "fallback_reason_refs": list(self.fallback_reason_refs),
            "release_gate_equivalent": self.release_gate_equivalent,
        }


def normalize_path(raw_path: str) -> str:
    if not raw_path or "\x00" in raw_path or "\\" in raw_path:
        raise ValueError("VERIFICATION_CHANGED_PATH_INVALID")
    path = PurePosixPath(raw_path)
    if path.is_absolute() or ".." in path.parts or raw_path.startswith("./"):
        raise ValueError("VERIFICATION_CHANGED_PATH_INVALID")
    normalized = path.as_posix()
    if normalized in {"", "."}:
        raise ValueError("VERIFICATION_CHANGED_PATH_INVALID")
    return normalized


def _safe_regular_repo_file(repo: Path, ref: str) -> bool:
    try:
        metadata = (repo / ref).lstat()
    except OSError:
        return False
    return stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)


def _rule_for_path(
    path: str,
    tier: str,
    *,
    repo: Path,
) -> tuple[str, tuple[str, ...], tuple[str, ...]] | None:
    if path in CRITICAL_PATHS or path.startswith(CRITICAL_PREFIXES):
        return ("rule-ref:verification-topology-full", (FULL_COMMAND_REF,), ())
    if path == "docs/verification/verifier_value_measurements.json":
        return (
            "rule-ref:verifier-value-measurement",
            ("command-ref:verifier-value-audit",),
            (),
        )
    if path.startswith(
        (
            "src/ultimate_ai_agent/core/authority/",
            "src/ultimate_ai_agent/core/approvals/",
            "src/ultimate_ai_agent/core/execution/",
            "src/ultimate_ai_agent/core/hygiene/",
        )
    ):
        return (
            "rule-ref:authority-orchestration",
            ("command-ref:ruff-changed", "command-ref:authority-focused"),
            ("tests/test_authority_leases.py", "tests/test_authority_dispatcher.py"),
        )
    if path.startswith("src/ultimate_ai_agent/api/") or path.startswith(
        ("docs/api/", "docs/schemas/api_", "tests/fixtures/api_route_")
    ):
        commands = [
            "command-ref:ruff-changed",
            "command-ref:api-contract-snapshot",
            "command-ref:api-lane",
        ]
        if tier == "affected":
            commands.append("command-ref:openapi")
        return (
            "rule-ref:api-openapi-routes",
            tuple(commands),
            (
                "tests/test_api_manifest.py",
                "tests/test_api_route_inventory_fixture.py",
                "tests/test_openapi_contract.py",
            ),
        )
    if path.startswith("apps/control-center/"):
        return (
            "rule-ref:control-center-frontend",
            (
                ("command-ref:frontend-safety",)
                if tier == "fast"
                else ("command-ref:frontend-check", "command-ref:frontend-safety")
            ),
            (),
        )
    if "web_access" in path or path.startswith(
        ("docs/network/", "scripts/verify_web_hybrid", ".uaa/local-web-services/")
    ):
        return (
            "rule-ref:web-hybrid",
            ("command-ref:ruff-changed", "command-ref:web-hybrid"),
            (
                "tests/test_searxng_search.py",
                "tests/test_firecrawl_markdown.py",
                "tests/test_web_hybrid_execution.py",
            ),
        )
    if "/memory" in path or path.startswith("docs/memory/"):
        return (
            "rule-ref:memory-context",
            ("command-ref:ruff-changed",),
            ("tests/test_memory_store.py", "tests/test_memory_retrieval.py"),
        )
    if "/providers" in path:
        return (
            "rule-ref:providers",
            ("command-ref:ruff-changed",),
            (
                "tests/test_provider_manifests.py",
                "tests/test_provider_result_envelope.py",
            ),
        )
    if "extension_catalog" in path or path.startswith("docs/extensions/"):
        return (
            "rule-ref:extensions",
            ("command-ref:ruff-changed",),
            (
                "tests/test_inspectable_extension_catalog.py",
                "tests/test_extension_catalog_storage_hardening.py",
            ),
        )
    if path.startswith("docs/") or path in {"README.md", "SECURITY.md", "VERSION.md"}:
        return (
            "rule-ref:documentation-product-truth",
            (
                ("command-ref:documentation",)
                if tier == "fast"
                else (
                    "command-ref:documentation",
                    "command-ref:product-truth",
                    "command-ref:redaction",
                )
            ),
            (),
        )
    if path.startswith(("packaging/", "scripts/package", "apps/macos/")):
        return (
            "rule-ref:packaging",
            ("command-ref:packaging-focused",),
            (),
        )
    if path.startswith("tests/test_") and path.endswith(".py"):
        return (
            "rule-ref:direct-test",
            ("command-ref:ruff-changed",),
            (path,),
        )
    if path.startswith("src/ultimate_ai_agent/") and path.endswith(".py"):
        owned_refs = FOCUSED_PYTEST_REFS_BY_SOURCE.get(path)
        if owned_refs is not None:
            return (
                "rule-ref:python-module-focused",
                ("command-ref:ruff-changed",),
                owned_refs,
            )
        candidate = f"tests/test_{PurePosixPath(path).stem}.py"
        if _safe_regular_repo_file(repo, candidate):
            return (
                "rule-ref:python-module-focused",
                ("command-ref:ruff-changed",),
                (candidate,),
            )
    return None


def select_paths(
    paths: list[str],
    *,
    tier: str = "affected",
    repo: Path = ROOT,
) -> Selection:
    if tier not in {"fast", "affected"}:
        raise ValueError("VERIFICATION_SELECTION_TIER_INVALID")
    try:
        root_metadata = repo.lstat()
    except OSError as exc:
        raise ValueError("VERIFICATION_REPOSITORY_ROOT_INVALID") from exc
    if not stat.S_ISDIR(root_metadata.st_mode) or stat.S_ISLNK(root_metadata.st_mode):
        raise ValueError("VERIFICATION_REPOSITORY_ROOT_INVALID")
    normalized = tuple(sorted({normalize_path(path) for path in paths}))
    if not normalized:
        return Selection(tier, (), (), (), (), (), (), "no_changes")
    rules: set[str] = set()
    commands: set[str] = set()
    tests: set[str] = set()
    unknown: list[str] = []
    missing_refs: list[str] = []
    for path in normalized:
        rule = _rule_for_path(path, tier, repo=repo)
        if rule is None:
            unknown.append(path)
            continue
        rule_ref, command_refs, test_refs = rule
        rules.add(rule_ref)
        commands.update(command_refs)
        for ref in test_refs:
            if _safe_regular_repo_file(repo, ref):
                tests.add(ref)
            else:
                missing_refs.append(ref)
    fallback_reasons: tuple[str, ...] = ()
    if missing_refs:
        commands = {FULL_COMMAND_REF}
        tests.clear()
        rules.add("rule-ref:missing-test-ref-full")
        fallback_reasons = ("reason-ref:verification:missing-test-ref",)
    elif unknown:
        commands = {FULL_COMMAND_REF}
        tests.clear()
        rules.add("rule-ref:unknown-path-full")
        fallback_reasons = ("reason-ref:verification:unknown-path",)
    elif FULL_COMMAND_REF in commands:
        commands = {FULL_COMMAND_REF}
        tests.clear()
        fallback_reasons = ("reason-ref:verification:critical-topology-change",)
    return Selection(
        tier=tier,
        changed_paths=normalized,
        matched_rule_refs=tuple(sorted(rules)),
        selected_command_refs=tuple(sorted(commands)),
        selected_test_refs=tuple(sorted(tests)),
        unknown_paths=tuple(unknown),
        fallback_reason_refs=fallback_reasons,
        status=("full_gate_required" if fallback_reasons else "selected"),
    )


def _parse_name_status(output: bytes) -> tuple[set[str], bool]:
    fields = [field.decode("utf-8") for field in output.split(b"\x00") if field]
    paths: set[str] = set()
    destructive = False
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        path_count = 2 if status.startswith(("R", "C")) else 1
        if index + path_count > len(fields):
            raise ValueError("VERIFICATION_GIT_STATUS_INVALID")
        paths.update(fields[index : index + path_count])
        destructive = destructive or status.startswith(("D", "R", "C"))
        index += path_count
    return paths, destructive


def _git_paths(base_ref: str) -> tuple[list[str], bool]:
    commands = (
        ["git", "diff", "--name-status", "-z", f"{base_ref}...HEAD"],
        ["git", "diff", "--name-status", "-z"],
        ["git", "diff", "--cached", "--name-status", "-z"],
    )
    paths: set[str] = set()
    destructive = False
    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError("VERIFICATION_GIT_DIFF_FAILED")
        command_paths, command_destructive = _parse_name_status(result.stdout)
        paths.update(command_paths)
        destructive = destructive or command_destructive
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if untracked.returncode != 0:
        raise ValueError("VERIFICATION_GIT_DIFF_FAILED")
    paths.update(
        item.decode("utf-8") for item in untracked.stdout.split(b"\x00") if item
    )
    return sorted(paths), destructive


COMMANDS: dict[str, tuple[str, ...]] = {
    "command-ref:api-contract-snapshot": (
        sys.executable,
        "scripts/verification/api_contract_snapshot.py",
        "--check",
    ),
    "command-ref:api-lane": (sys.executable, "scripts/verification/api_lane.py"),
    "command-ref:openapi": (sys.executable, "scripts/verify_openapi_contract.py"),
    "command-ref:documentation": (
        sys.executable,
        "scripts/verify_documentation_integrity.py",
    ),
    "command-ref:product-truth": (sys.executable, "scripts/verify_product_truth.py"),
    "command-ref:redaction": (
        sys.executable,
        "scripts/verify_security_redaction_artifacts.py",
    ),
    "command-ref:frontend-check": ("make", "frontend-check"),
    "command-ref:frontend-safety": (
        sys.executable,
        "scripts/verify_control_center_frontend.py",
    ),
    "command-ref:web-hybrid": (
        sys.executable,
        "scripts/verify_web_hybrid_contracts.py",
    ),
    "command-ref:authority-focused": (
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_authority_leases.py",
        "tests/test_authority_dispatcher.py",
    ),
    "command-ref:packaging-focused": (
        sys.executable,
        "scripts/verify_local_runtime_packaging_proof.py",
    ),
    "command-ref:verifier-value-audit": (
        sys.executable,
        "scripts/verification/verifier_value_audit.py",
    ),
    FULL_COMMAND_REF: ("make", "verify-dev-sharded"),
}


def execute_selection(selection: Selection) -> int:
    env = {**os.environ, "PYTHONPATH": "src", "PYTHONHASHSEED": "0"}
    python_paths = [
        path
        for path in selection.changed_paths
        if path.endswith(".py") and (ROOT / path).is_file()
    ]
    if "command-ref:ruff-changed" in selection.selected_command_refs and python_paths:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", *python_paths],
            cwd=ROOT,
            env=env,
            check=False,
        )
        if result.returncode:
            return result.returncode
    if selection.selected_test_refs:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *selection.selected_test_refs],
            cwd=ROOT,
            env=env,
            check=False,
        )
        if result.returncode:
            return result.returncode
    for command_ref in selection.selected_command_refs:
        if command_ref == "command-ref:ruff-changed":
            continue
        result = subprocess.run(COMMANDS[command_ref], cwd=ROOT, env=env, check=False)
        if result.returncode:
            return result.returncode
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Select deterministic fail-closed local verification from changed paths."
    )
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--tier", choices=("fast", "affected"), default="affected")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if args.json and args.execute:
        parser.error("--json and --execute cannot be combined")
    try:
        git_paths, destructive = _git_paths(args.base_ref)
        paths = sorted({*git_paths, *args.path})
        selection = select_paths(paths, tier=args.tier)
        if destructive:
            selection = Selection(
                args.tier,
                tuple(paths),
                ("rule-ref:rename-delete-full",),
                (FULL_COMMAND_REF,),
                (),
                (),
                ("reason-ref:verification:rename-delete",),
                "full_gate_required",
            )
    except (UnicodeDecodeError, ValueError):
        selection = Selection(
            args.tier,
            (),
            ("rule-ref:selector-error-full",),
            (FULL_COMMAND_REF,),
            (),
            (),
            ("reason-ref:verification:selector-error",),
            "full_gate_required",
        )
    if args.json:
        print(json.dumps(selection.payload(), sort_keys=True))
    else:
        print(f"Verification selection: {selection.status}")
        for path in selection.changed_paths:
            print(f"  changed: {path}")
        for ref in selection.selected_command_refs:
            print(f"  command: {ref}")
        for ref in selection.selected_test_refs:
            print(f"  test: {ref}")
        if selection.fallback_reason_refs:
            print("  Full local verification is required before merge or release.")
        else:
            print("  Advisory fast checks do not replace merge or release gates.")
    return execute_selection(selection) if args.execute else 0


if __name__ == "__main__":
    raise SystemExit(main())
