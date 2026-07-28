#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts.verification.repo import (  # noqa: E402
    append_missing_doc_snippets,
    load_json,
    print_failures_or_success,
    read_text,
    repo_path,
)
from ultimate_ai_agent.core.cua import (  # noqa: E402
    ComputerUseActionEnvelope,
    ComputerUseActionKind,
    ComputerUseActionMode,
    ComputerUseCapabilityStatus,
    ComputerUseDriverPresence,
    build_blocked_computer_use_action_envelope,
    build_default_computer_use_capability_contract,
    build_default_computer_use_doctor_result,
    validate_computer_use_action_envelope,
    validate_computer_use_capability_contract,
    validate_computer_use_doctor_result,
)


CONTRACT_DOC = "docs/cua/COMPUTER_USE_CUA_CONTRACT.md"
RELEASE_MANIFEST = "docs/cua/cua_release_surface_manifest.json"
CONTRACT_MODULE = "src/ultimate_ai_agent/core/cua/contracts.py"
ROUTE_SURFACES = [
    "docs/api/openapi_contract.md",
    "docs/api/route_inventory.md",
    "docs/control_center/route_status_manifest.json",
]
CUA_RUNTIME_SCAN_ROOTS = [
    "src/ultimate_ai_agent",
    "apps/control-center/src",
]
CUA_MODULE_SCAN_ROOTS = [
    "src/ultimate_ai_agent/core/cua",
]

REQUIRED_PROOFS = {
    "no_runtime_driver",
    "no_click_type_route",
    "no_screenshot_capture",
    "no_os_accessibility_access",
    "no_subprocess_cua_launch",
    "no_browser_automation_under_cua",
    "no_connector_write",
    "contracts_verifiers_docs_only",
}

RUNTIME_MARKERS = {
    "cua-driver": "CUA driver runtime marker",
    "cua_driver": "CUA driver runtime marker",
    "computer_use(action=": "computer-use action invocation",
    "computer-use-driver": "computer-use driver marker",
    "/cua/click": "CUA click route",
    "/cua/type": "CUA type route",
    "/cua/drag": "CUA drag route",
    "/cua/scroll": "CUA scroll route",
    "/cua/capture": "CUA capture route",
    "/computer-use/click": "computer-use click route",
    "/computer-use/type": "computer-use type route",
    "/computer-use/drag": "computer-use drag route",
    "/computer-use/scroll": "computer-use scroll route",
    "/computer-use/capture": "computer-use capture route",
}

CUA_MODULE_FORBIDDEN_MARKERS = {
    "from playwright": "Playwright import under CUA",
    "import playwright": "Playwright import under CUA",
    "selenium": "Selenium use under CUA",
    "chromedriver": "browser driver use under CUA",
    "puppeteer": "browser driver use under CUA",
    "pyautogui": "OS automation import under CUA",
    "pynput": "OS automation import under CUA",
    "axuielement": "accessibility API use under CUA",
    "cgwindowlistcreateimage": "screen capture API use under CUA",
    "quartz": "macOS automation framework use under CUA",
    "applicationservices": "macOS automation framework use under CUA",
    "imagegrab.grab": "screen capture API use under CUA",
    "mss.": "screen capture API use under CUA",
    "subprocess.": "subprocess launch under CUA",
    "os.system(": "shell launch under CUA",
}

FORBIDDEN_RELEASE_CLAIMS = {
    "cua is shipped": "CUA shipped claim",
    "computer use is shipped": "Computer Use shipped claim",
    "production-ready cua": "CUA production-readiness claim",
    "cua production ready": "CUA production-readiness claim",
    "click/type execution enabled": "CUA execution claim",
    "cua real computer control is enabled": "CUA enabled-control claim",
}


def verify(extra_scan_paths: Iterable[Path] = ()) -> list[str]:
    failures: list[str] = []
    _append_required_file_failures(failures)
    _append_contract_model_failures(failures)
    _append_manifest_failures(failures)
    _append_doc_failures(failures)
    _append_route_surface_failures(failures)
    _append_runtime_marker_failures(failures, extra_scan_paths)
    _append_cua_module_marker_failures(failures)
    _append_release_claim_failures(failures, extra_scan_paths)
    return failures


def _append_required_file_failures(failures: list[str]) -> None:
    for rel_path in [
        CONTRACT_DOC,
        RELEASE_MANIFEST,
        CONTRACT_MODULE,
        "src/ultimate_ai_agent/core/cua/__init__.py",
        "tests/test_cua_contract_models.py",
        "tests/test_cua_contract_lane_verifier.py",
    ]:
        if not repo_path(rel_path).exists():
            failures.append(f"missing required CUA contract lane file: {rel_path}")


def _append_contract_model_failures(failures: list[str]) -> None:
    try:
        capability = build_default_computer_use_capability_contract()
        validate_computer_use_capability_contract(capability)
        if capability.status != ComputerUseCapabilityStatus.blocked:
            failures.append("default CUA capability contract must remain blocked")
        if capability.driver_presence != ComputerUseDriverPresence.absent:
            failures.append("default CUA driver presence must remain absent")
    except Exception as exc:  # pragma: no cover - failure path prints safe summary
        failures.append(f"CUA capability contract validation failed: {type(exc).__name__}")

    try:
        envelope = build_blocked_computer_use_action_envelope()
        validate_computer_use_action_envelope(envelope)
        unsafe = ComputerUseActionEnvelope(
            **{
                **envelope.model_dump(mode="python"),
                "proposed_action": ComputerUseActionKind.click,
                "action_mode": ComputerUseActionMode.proposal_only,
            }
        )
        validate_computer_use_action_envelope(unsafe)
        failures.append("CUA mutating action proposal was not rejected")
    except ValueError:
        pass
    except Exception as exc:  # pragma: no cover - failure path prints safe summary
        failures.append(f"CUA action envelope validation failed: {type(exc).__name__}")

    try:
        validate_computer_use_doctor_result(build_default_computer_use_doctor_result())
    except Exception as exc:  # pragma: no cover - failure path prints safe summary
        failures.append(f"CUA doctor contract validation failed: {type(exc).__name__}")


def _append_manifest_failures(failures: list[str]) -> None:
    try:
        manifest = load_json(RELEASE_MANIFEST)
    except Exception as exc:
        failures.append(f"CUA release-surface manifest is not readable JSON: {type(exc).__name__}")
        return
    if manifest.get("schema_version") != "uaa-cua-release-surface.v1":
        failures.append("CUA release-surface manifest schema version is missing or stale")
    if manifest.get("status") not in {"blocked", "experimental"}:
        failures.append("CUA release-surface manifest must remain blocked or experimental")
    if manifest.get("implementation_status") != "contracts_verifiers_docs_only":
        failures.append("CUA release-surface manifest must stay contracts/verifiers/docs only")
    if manifest.get("driver_presence") not in {"absent", "noop", "external_unverified"}:
        failures.append("CUA release-surface manifest must not claim a trusted driver")
    proofs = manifest.get("proofs")
    if not isinstance(proofs, dict):
        failures.append("CUA release-surface manifest proofs must be an object")
        return
    for proof in sorted(REQUIRED_PROOFS):
        if proofs.get(proof) is not True:
            failures.append(f"CUA release-surface manifest proof must be true: {proof}")
    if "available_untrusted" not in manifest.get("driver_lifecycle_states", []):
        failures.append("CUA release-surface manifest must name available_untrusted lifecycle")


def _append_doc_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(
        failures,
        {
            CONTRACT_DOC: [
                "CUA is an external capability adapter, not core authority.",
                "Browser automation and native desktop CUA remain separate lanes",
                "Element identifiers are ephemeral and bound to snapshot refs.",
                "Every future proposed action must flow through Action Envelope",
                "The lane has no runtime driver, click/type route, screenshot capture",
                "password typing, credential entry, 2FA handling",
                "contract-only",
                "observe-only redacted capture proposal",
                "manual handoff receipt",
                "exact-approved proposal-only actions",
                "narrow low-risk execution only after a future accepted milestone",
            ],
            "docs/README.md": [CONTRACT_DOC, RELEASE_MANIFEST],
            "docs/DOCUMENTATION_INDEX.md": [CONTRACT_DOC, RELEASE_MANIFEST],
        },
    )


def _append_route_surface_failures(failures: list[str]) -> None:
    for rel_path in ROUTE_SURFACES:
        path = repo_path(rel_path)
        if not path.exists():
            failures.append(f"missing route surface for CUA route check: {rel_path}")
            continue
        text = read_text(path).lower()
        for marker in [
            "/cua/",
            "/computer-use/",
            "cua-click",
            "cua-type",
            "computer-use-click",
            "computer-use-type",
        ]:
            if marker in text:
                failures.append(f"{rel_path} exposes forbidden CUA route marker: {marker}")


def _append_runtime_marker_failures(
    failures: list[str],
    extra_scan_paths: Iterable[Path],
) -> None:
    for path in _iter_scan_files([*(repo_path(root) for root in CUA_RUNTIME_SCAN_ROOTS), *extra_scan_paths]):
        rel = _relative(path)
        if _is_allowed_static_contract_file(rel):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for marker, label in RUNTIME_MARKERS.items():
            if marker in text:
                failures.append(f"{rel} contains forbidden {label}: {marker}")


def _append_cua_module_marker_failures(failures: list[str]) -> None:
    for path in _iter_scan_files(repo_path(root) for root in CUA_MODULE_SCAN_ROOTS):
        rel = _relative(path)
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for marker, label in CUA_MODULE_FORBIDDEN_MARKERS.items():
            if marker in text:
                failures.append(f"{rel} contains forbidden {label}: {marker}")


def _append_release_claim_failures(
    failures: list[str],
    extra_scan_paths: Iterable[Path],
) -> None:
    scan_paths = [
        repo_path(CONTRACT_DOC),
        repo_path(RELEASE_MANIFEST),
        repo_path("docs/README.md"),
        repo_path("docs/DOCUMENTATION_INDEX.md"),
        *extra_scan_paths,
    ]
    for path in _iter_scan_files(scan_paths):
        rel = _relative(path)
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for claim, label in FORBIDDEN_RELEASE_CLAIMS.items():
            if claim in text:
                failures.append(f"{rel} contains forbidden {label}: {claim}")


def _iter_scan_files(paths: Iterable[Path]) -> Iterable[Path]:
    allowed_suffixes = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md"}
    seen: set[Path] = set()
    for path in paths:
        if not path.exists():
            continue
        candidates = [path] if path.is_file() else path.rglob("*")
        for candidate in candidates:
            if (
                candidate in seen
                or not candidate.is_file()
                or candidate.suffix not in allowed_suffixes
                or "__pycache__" in candidate.parts
            ):
                continue
            seen.add(candidate)
            yield candidate


def _is_allowed_static_contract_file(rel_path: str) -> bool:
    return rel_path in {
        "src/ultimate_ai_agent/core/cua/contracts.py",
        "scripts/verify_cua_contract_lane.py",
    }


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    return print_failures_or_success(
        verify(),
        "CUA contract lane verification passed.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
