#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import (  # noqa: E402
    command_registry,
    lane_registry,
)

SMOKE_DOC = "docs/control_center/LOCAL_BROWSER_SMOKE.md"
SMOKE_REPORTING_DOC = "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md"
FRONTEND_PACKAGE = "apps/control-center/package.json"
FRONTEND_APP_TEST = "apps/control-center/src/App.test.tsx"
CI_WORKFLOW = ".github/workflows/ci.yml"
ALLOWED_CI_PLAYWRIGHT_LINES = {
    "- name: install playwright chromium",
    "playwright_browsers_path: ${{ runner.temp }}/playwright-browsers",
    "run: npx playwright install chromium",
    "run: npx playwright install --with-deps chromium",
}

REQUIRED_DOC_WORDING = [
    "status: active uaa-p1-032 browser smoke readiness",
    "first product loop readiness",
    "real",
    "mocked",
    "skipped",
    "blocked",
    "manual local browser smoke",
    "local-only",
    "localhost",
    "127.0.0.1",
    "::1",
    "no authenticated browser profile",
    "no chrome authenticated profile control",
    "no computer use",
    "no external sites",
    "no production backend",
    "no screenshots with secrets",
    "preview-only",
    "no execute button",
    "no plugin enable button",
    "no mobile sensor button",
    "no remote dispatch button",
    "mock data marked mock",
    "non-authoritative",
    "open control center",
    "inspect runtime health and model readiness",
    "select or approve local gguf model",
    "use chat shell through uaa `/v1`",
    "create a task decomposition plan",
    "approve one safe registered capability",
    "inspect receipt/audit/latency/rollback status",
    "raw json must not be the primary ui",
    "make frontend-check",
]

REQUIRED_FRONTEND_SCRIPTS = ["dev", "preview", "typecheck", "lint", "test", "build"]
REQUIRED_CI_FRAGMENTS = [
    "apps/control-center",
    "npm ci",
    "scripts/verification/run_ci_lane.py",
    "--lane ci-control-center-frontend",
]
REQUIRED_FRONTEND_MAKE_FRAGMENTS = [
    "frontend-check:",
    "npm run typecheck --if-present",
    "npm run lint --if-present",
    "npm run test --if-present -- --run",
    "npm run build --if-present",
]

FORBIDDEN_CI_FRAGMENTS = [
    "playwright",
    "puppeteer",
    "selenium",
    "webdriver",
    "chrome --user-data-dir",
    "google-chrome",
    "computer use",
    "xcodebuild",
    "app-store-connect",
    "fastlane",
    "deploy",
    "vercel",
    "netlify",
    "firebase deploy",
    "https://",
]

FORBIDDEN_DOC_FRAGMENTS = [
    "use chrome authenticated profile control",
    "use computer use",
    "external sites are allowed",
    "production backend is allowed",
    "screenshots may include secrets",
    "execute actions",
    "enable plugins",
    "dispatch remote workers",
    "access mobile sensors",
]

REQUIRED_REPORTING_WORDING = [
    "status: active uaa-p1-032 browser smoke readiness reporting",
    "first product loop",
    "real, mocked, skipped, or blocked",
    "local browser smoke report",
    "local-only",
    "localhost",
    "127.0.0.1",
    "::1",
    "no authenticated browser profile",
    "no computer use",
    "no screenshots with secrets",
    "non-authoritative",
    "mock fallback",
    "preview-only",
    "no action was executed",
    "do not include secrets",
    "do not commit generated screenshots",
    "open_control_center",
    "inspect_runtime_health_and_model_readiness",
    "select_or_approve_local_gguf_model",
    "chat_shell_through_uaa_v1",
    "create_task_decomposition_plan",
    "approve_safe_registered_capability",
    "inspect_receipt_audit_latency_rollback",
    "no_raw_json_primary_ui",
    "blocked_prerequisites_visible",
    "release_readiness_claimed: no",
]

REQUIRED_APP_TEST_WORDING = [
    "covers first product loop browser smoke readiness with truthful backend-bound states",
    'openControlCenter: "mock_fallback"',
    'inspectRuntimeHealthAndModelReadiness: "route_ready"',
    'selectOrApproveLocalGgufModel: "backend_gated"',
    'chatShellThroughUaaV1: "gateway_gated"',
    'createTaskDecompositionPlan: "backend_gated"',
    'approveSafeRegisteredCapability: "backend_authority"',
    'inspectReceiptAuditLatencyRollback: "inspection_ready"',
    "Preview only action request",
    "No approval was granted from this UI",
    "Trace detail is redacted summary metadata only",
]

FORBIDDEN_TRACKED_FRAGMENTS = [
    "apps/control-center/node_modules/",
    "apps/control-center/dist/",
    "apps/control-center/build/",
    "apps/control-center/coverage/",
    "apps/control-center/.next/",
    "apps/control-center/.env",
    "apps/control-center/ios/",
    "apps/control-center/android/",
    "apps/control-center/Package.swift",
    "apps/control-center/Podfile",
]


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    failures.extend(_doc_failures(root))
    failures.extend(_package_failures(root))
    failures.extend(_app_test_failures(root))
    failures.extend(_ci_failures(root))
    failures.extend(_tracked_artifact_failures(root))
    return failures


def _doc_failures(root: Path) -> list[str]:
    failures: list[str] = []
    doc_specs = [
        (SMOKE_DOC, REQUIRED_DOC_WORDING, "smoke doc"),
        (SMOKE_REPORTING_DOC, REQUIRED_REPORTING_WORDING, "smoke reporting doc"),
    ]
    for rel_path, required_wording, label in doc_specs:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing browser smoke readiness doc: {rel_path}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        failures.extend(
            f"{label} missing required safety wording: {fragment}" for fragment in required_wording if fragment not in text
        )
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            for fragment in FORBIDDEN_DOC_FRAGMENTS:
                if fragment in stripped and not _line_is_negative_policy(stripped):
                    failures.append(f"forbidden {label} fragment: {fragment}")
    return failures


def _package_failures(root: Path) -> list[str]:
    path = root / FRONTEND_PACKAGE
    if not path.exists():
        return [f"missing frontend package: {FRONTEND_PACKAGE}"]
    try:
        package = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"could not parse frontend package.json: {exc}"]
    scripts = package.get("scripts", {})
    return [
        f"frontend package missing smoke-readiness script support: {script}"
        for script in REQUIRED_FRONTEND_SCRIPTS
        if script not in scripts
    ]


def _app_test_failures(root: Path) -> list[str]:
    path = root / FRONTEND_APP_TEST
    if not path.exists():
        return [f"missing frontend browser smoke test file: {FRONTEND_APP_TEST}"]
    text = path.read_text(encoding="utf-8")
    return [
        f"frontend browser smoke test missing first-loop marker: {fragment}"
        for fragment in REQUIRED_APP_TEST_WORDING
        if fragment not in text
    ]


def _ci_failures(root: Path) -> list[str]:
    path = root / CI_WORKFLOW
    if not path.exists():
        return [f"missing CI workflow: {CI_WORKFLOW}"]
    text = path.read_text(encoding="utf-8").lower()
    failures = [f"CI missing frontend check fragment: {fragment}" for fragment in REQUIRED_CI_FRAGMENTS if fragment not in text]
    failures.extend(_canonical_frontend_command_failures(root))
    forbidden_scan_text = _ci_text_without_allowed_proof_lane_browser_setup(text)
    failures.extend(
        f"forbidden CI browser automation fragment: {fragment}"
        for fragment in FORBIDDEN_CI_FRAGMENTS
        if fragment in forbidden_scan_text
    )
    return failures


def _canonical_frontend_command_failures(root: Path) -> list[str]:
    failures: list[str] = []
    lanes = lane_registry()
    commands = command_registry()
    lane = lanes.get("ci-control-center-frontend")
    if lane is None or lane.command_refs != ("command:frontend.check",):
        failures.append("canonical CI manifest frontend lane is missing or drifted")
    command = commands.get("command:frontend.check")
    if command is None or command.argv != ("make", "frontend-check"):
        failures.append("canonical CI manifest frontend command is missing or drifted")

    makefile = root / "Makefile"
    if not makefile.exists():
        failures.append("canonical frontend Make target is missing: Makefile")
        return failures
    make_text = makefile.read_text(encoding="utf-8").lower()
    failures.extend(
        f"canonical frontend Make target missing check fragment: {fragment}"
        for fragment in REQUIRED_FRONTEND_MAKE_FRAGMENTS
        if fragment not in make_text
    )
    return failures


def _ci_text_without_allowed_proof_lane_browser_setup(text: str) -> str:
    allowed_lines: list[str] = []
    for line in text.splitlines():
        if line.strip() in ALLOWED_CI_PLAYWRIGHT_LINES:
            continue
        allowed_lines.append(line)
    return "\n".join(allowed_lines)


def _tracked_artifact_failures(root: Path) -> list[str]:
    try:
        tracked = subprocess.check_output(["git", "ls-files"], cwd=root, text=True, stderr=subprocess.DEVNULL).splitlines()
    except (subprocess.SubprocessError, FileNotFoundError):
        tracked = [str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()]
    failures = []
    for rel_path in tracked:
        if rel_path.endswith("/.env.example") or rel_path == ".env.example":
            continue
        if any(fragment in rel_path for fragment in FORBIDDEN_TRACKED_FRAGMENTS):
            failures.append(f"forbidden tracked browser-smoke artifact: {rel_path}")
    return failures


def _line_is_negative_policy(line: str) -> bool:
    return any(marker in line for marker in ["no ", "not ", "never", "disabled", "disallowed", "off-limits", "excluded"])


def main() -> int:
    print("=== Ultimate AI Agent Control Center Browser Smoke Readiness Verification ===")
    failures = verify(ROOT)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Control Center browser smoke readiness verification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
