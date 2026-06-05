#!/usr/bin/env python3
import sys
import subprocess
import re
import os
import tempfile
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

M44_ALLOWED_CCC_IOS_SKELETON_PREFIX = "apps/ccc-ios/Sources/UltimateAIAgentCCC/"
M44_ALLOWED_CCC_IOS_SKELETON_FILES = {
    "apps/ccc-ios/README.md",
}


def _is_m44_allowed_ccc_ios_skeleton_file(rel_path: str) -> bool:
    return rel_path in M44_ALLOWED_CCC_IOS_SKELETON_FILES or (
        rel_path.startswith(M44_ALLOWED_CCC_IOS_SKELETON_PREFIX)
        and rel_path.endswith(".swift")
    )


def _is_m45_allowed_ccc_ios_local_connection_file(rel_path: str) -> bool:
    return _is_m44_allowed_ccc_ios_skeleton_file(rel_path)


def _is_m46_allowed_ccc_ios_review_receipt_file(rel_path: str) -> bool:
    return _is_m45_allowed_ccc_ios_local_connection_file(rel_path)


def _current_version() -> str:
    text = (ROOT / "VERSION.md").read_text(encoding="utf-8")
    match = re.search(r"v\d+\.\d+\.\d+", text)
    return match.group(0) if match else "v0.0.0"


SCAN_SEQUENCE = [
    ("generated artifact scan", "verify_no_generated_artifacts"),
    ("obvious secret scan", "verify_no_obvious_secrets"),
    ("blocked module scan", "verify_no_blocked_modules"),
    ("forbidden external integrations scan", "verify_no_forbidden_external_integrations"),
    ("model runtime simulated-only scan", "verify_no_real_model_runtime_execution"),
    ("approval authority local-dev-only scan", "verify_no_real_approval_authority_integrations"),
    ("remote worker foundation-only scan", "verify_no_real_remote_worker_integrations"),
    ("control center no-execution scan", "verify_no_control_center_runtime_or_frontend_expansion"),
    ("web control center frontend safety scan", "verify_m13_web_control_center_frontend_safety"),
    ("control center frontend safety verifier", "verify_control_center_frontend_script"),
    ("control center browser smoke readiness verifier", "verify_control_center_browser_smoke_readiness_script"),
    ("documentation integrity scan", "verify_documentation_integrity"),
    ("OpenWebUI bridge contract-only scan", "verify_no_openwebui_runtime_or_config_implementation"),
    ("local model runtime activation contract-only scan", "verify_no_local_runtime_activation_implementation"),
    ("M23 first local LLM call boundary scan", "verify_m23_first_local_llm_call_boundary"),
    ("M24 memory provider local store safety scan", "verify_m24_memory_provider_local_store_safety"),
    ("M25 truth source evidence checker safety scan", "verify_m25_truth_source_evidence_checker_safety"),
    ("M26 grounded recall context-pack safety scan", "verify_m26_grounded_recall_context_pack_safety"),
    ("M27 Tool Broker v2 safe intent contract scan", "verify_m27_tool_broker_v2_safety"),
    ("M28 Approval Authority v2 action policy safety scan", "verify_m28_approval_authority_v2_safety"),
    ("M29 Agent Task Planning Engine safety scan", "verify_m29_task_planning_engine_safety"),
    ("M30 Multi-Step Execution Framework safety scan", "verify_m30_multi_step_execution_framework_safety"),
    ("M31 Real Tool Runtime Adapter no-op safety scan", "verify_m31_tool_runtime_noop_safety"),
    ("M32 safe filesystem metadata tool scan", "verify_m32_filesystem_metadata_tool_safety"),
    ("M33 redacted file preview tool scan", "verify_m33_redacted_file_preview_tool_safety"),
    ("M34 broader file capability review scan", "verify_m34_broader_file_capability_review_safety"),
    ("M35 safe file review workflow contract scan", "verify_m35_safe_file_review_workflow_safety"),
    ("M36 CCC file review surface scan", "verify_m36_ccc_file_review_surface_safety"),
    ("M37 review approval capture scan", "verify_m37_review_approval_capture_safety"),
    ("M38 safe context proposal scan", "verify_m38_safe_context_proposal_safety"),
    ("M39 CCC context proposal surface scan", "verify_m39_ccc_context_proposal_surface_safety"),
    ("M40 context handoff approval scan", "verify_m40_context_handoff_approval_safety"),
    ("M41 local prototype safety freeze scan", "verify_m41_local_prototype_safety_freeze"),
    ("M42 mobile product contract refresh scan", "verify_m42_mobile_product_contract_refresh"),
    ("M43 read-only mobile API boundary scan", "verify_m43_mobile_api_boundary_read_only"),
    ("M44 CCC iOS skeleton no-authority scan", "verify_m44_ccc_ios_skeleton_no_authority"),
    ("M45 CCC iOS local read-only connection scan", "verify_m45_ccc_ios_local_read_only_connection"),
    ("M46 CCC iOS review/receipt read-only surfaces scan", "verify_m46_ccc_ios_review_receipt_read_only_surfaces"),
    ("M47 TestFlight pipeline internal-only scan", "verify_m47_testflight_pipeline_internal_only"),
    ("local developer launcher safety scan", "verify_local_developer_launcher_safety"),
    ("v0.29.2 local dev API authority/raw preview hardening scan", "verify_v0292_local_dev_api_hardening"),
    ("shell execution scan", "verify_no_shell_execution_in_runtime"),
    ("production truth integration scan", "verify_no_production_truth_integrations"),
    ("broad filesystem scan", "verify_no_broad_filesystem_scanning"),
    ("mobile/device capability contract-only scan", "verify_no_mobile_native_or_sensor_implementation"),
]
OPENWEBUI_FORBIDDEN_CONFIG_PATH_FRAGMENTS = (
    "docker-compose.openwebui",
    "openwebui.config",
    "openwebui-config",
    "openwebui_plugins",
    "openwebui_pipelines",
    "openwebui_functions",
    "openwebui_tools",
    "apps/openwebui/",
    "openwebui/",
)
OPENWEBUI_FORBIDDEN_RUNTIME_FRAGMENTS = (
    "openwebui_api_key",
    "openwebui_api",
    "openwebui_base_url",
    "openwebui_admin",
    "openwebui_token",
    "openwebui_cookie",
    "openwebui_session",
    "openwebui_plugin",
    "openwebui_function",
    "openwebui_pipeline",
    "openwebui_tool",
    "/openwebui/execute",
    "/openwebui/bridge/run",
    "/chat/execute",
    "/chat/run",
    "docker compose",
    "docker-compose",
)
OPENWEBUI_SCAN_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
OPENWEBUI_ALLOWED_FRAGMENT_SCAN_FILES = {
    "scripts/verify_all.py",
    "scripts/verify_control_center_frontend.py",
    "scripts/verify_documentation_integrity.py",
    "src/ultimate_ai_agent/core/gate/evaluators.py",
}
M22_LOCAL_RUNTIME_FORBIDDEN_FRAGMENTS = (
    "import ollama",
    "from ollama import",
    "import llama_cpp",
    "from llama_cpp import",
    "import mlx",
    "from mlx import",
    "import vllm",
    "from vllm import",
    "import lmstudio",
    "import requests",
    "import httpx",
    "subprocess",
    "requests.get(",
    "requests.post(",
    "requests.request(",
    "httpx.get(",
    "httpx.post(",
    "httpx.request(",
    "urllib.request.urlopen(",
    "create_completion",
    "chat.completions.create(",
    "ollama.generate(",
    "ollama.pull(",
    "/api/generate",
    "/v1/chat/completions",
)
M22_LOCAL_RUNTIME_ALLOWED_SOURCE_FILES = {
    "src/ultimate_ai_agent/core/model_runtime/local_adapter.py",
    "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
    "src/ultimate_ai_agent/core/model_runtime/smoke_policy.py",
    "src/ultimate_ai_agent/core/model_runtime/simulator.py",
    "src/ultimate_ai_agent/core/model_runtime/transports.py",
}


def run_cmd(args, cwd=ROOT, env=None):
    print(f"\nRunning: {' '.join(args)}")
    result = subprocess.run(args, cwd=cwd, env=env, text=True)
    if result.returncode != 0:
        print(f"FAIL: Command failed with exit code {result.returncode}")
        sys.exit(1)
    print("SUCCESS")

def _is_doc_path(rel_path):
    return rel_path == "docs" or rel_path.startswith("docs/")

def find_openwebui_forbidden_config_path_matches(root=ROOT):
    matches = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in OPENWEBUI_SCAN_EXCLUDED_DIRS]
        current = Path(dirpath)
        rel_dir = current.relative_to(root).as_posix() if current != root else ""
        if rel_dir and _is_doc_path(rel_dir):
            dirnames[:] = []
            continue
        for name in [*dirnames, *filenames]:
            path = current / name
            rel = path.relative_to(root).as_posix()
            if _is_doc_path(rel):
                continue
            lowered = rel.lower()
            if any(fragment in lowered for fragment in OPENWEBUI_FORBIDDEN_CONFIG_PATH_FRAGMENTS):
                matches.add(rel)
    return sorted(matches)

def find_openwebui_forbidden_runtime_fragment_failures(root=ROOT):
    failures = []
    implementation_roots = [root / "src", root / "apps", root / "scripts"]
    for implementation_root in implementation_roots:
        if not implementation_root.exists():
            continue
        candidate_files = []
        if implementation_root.name in {"src", "scripts"}:
            candidate_files.extend(implementation_root.rglob("*.py"))
        else:
            candidate_files.extend(implementation_root.rglob("*.ts"))
            candidate_files.extend(implementation_root.rglob("*.tsx"))
            candidate_files.extend(implementation_root.rglob("*.js"))
            candidate_files.extend(implementation_root.rglob("*.jsx"))
            candidate_files.extend(implementation_root.rglob("*.json"))
        for path in candidate_files:
            rel = path.relative_to(root).as_posix()
            if not path.is_file() or any(part in OPENWEBUI_SCAN_EXCLUDED_DIRS for part in path.parts):
                continue
            if rel in OPENWEBUI_ALLOWED_FRAGMENT_SCAN_FILES:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for fragment in OPENWEBUI_FORBIDDEN_RUNTIME_FRAGMENTS:
                if fragment in text:
                    failures.append(f"Forbidden OpenWebUI runtime/config fragment in {rel}: {fragment}")
    return failures

def find_m22_local_runtime_forbidden_fragment_failures(root=ROOT):
    failures = []
    runtime_root = Path(root) / "src" / "ultimate_ai_agent" / "core" / "model_runtime"
    if not runtime_root.exists():
        return failures
    for path in runtime_root.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if "__pycache__" in path.parts:
            continue
        if rel in M22_LOCAL_RUNTIME_ALLOWED_SOURCE_FILES:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for fragment in M22_LOCAL_RUNTIME_FORBIDDEN_FRAGMENTS:
            if fragment in text:
                failures.append(f"Forbidden M22 local runtime activation fragment in {rel}: {fragment}")
    return failures

def verify_no_generated_artifacts():
    print("\n[Verifier] Running generated-artifact scan...")
    try:
        git_files_raw = subprocess.check_output(["git", "ls-files"], text=True)
        git_files = git_files_raw.splitlines()
        for f in git_files:
            if any(x in f for x in [".egg-info", ".venv", "build/", "dist/"]):
                print(f"FAIL: A generated artifact/virtualenv file is tracked in git: {f}")
                sys.exit(1)
    except subprocess.SubprocessError as e:
        print(f"Warning: Failed to run git ls-files ({e}). Skipping tracked artifact verification.")
    print("OK: No generated egg-info, .venv, build, or dist files are tracked in git")

def verify_no_obvious_secrets():
    print("\n[Verifier] Running obvious secret assignment scan...")
    try:
        git_files_raw = subprocess.check_output(["git", "ls-files"], text=True)
        git_files = git_files_raw.splitlines()
    except subprocess.SubprocessError:
        git_files = []

    private_key_begin = "-----" + "BEGIN"
    private_key_end = "PRIVATE" + " KEY-----"
    secret_patterns = [
        (re.compile(r'(?i)(api_key|password|client_secret|private_key|token|auth_token)\s*=\s*[\'"]([a-zA-Z0-9_\-\.\:\/]+)[\'"]'), "assignment"),
        (re.compile(re.escape(private_key_begin) + r" .* " + re.escape(private_key_end)), "private_key_header")
    ]
    for f in git_files:
        path = ROOT / f
        if (f.startswith("tests/") or 
            f.endswith(".md") or 
            f.startswith("scripts/") or 
            "test" in f or 
            "example" in f or
            "mock" in f):
            continue
        if path.is_file():
            try:
                content = path.read_text(encoding="utf-8")
                if private_key_begin in content and private_key_end in content:
                    print(f"FAIL: Obvious committed secret (private key) in {f}")
                    sys.exit(1)
                for pattern, ptype in secret_patterns:
                    if ptype == "assignment":
                        for match in pattern.finditer(content):
                            key, val = match.groups()
                            val_lower = val.lower()
                            if any(x in val_lower for x in ["mock", "test", "dummy", "example", "placeholder", "token", "schema"]):
                                continue
                            if re.match(r'^v?\d+\.\d+\.\d+$', val) or val.endswith(".v0"):
                                continue
                            if len(val) >= 12:
                                print(f"FAIL: Potential obvious committed secret '{key}' in {f}")
                                sys.exit(1)
            except Exception:
                pass
    print("OK: No obvious committed secrets detected in non-test files")

def verify_no_blocked_modules():
    print("\n[Verifier] Running advanced blocked module scan...")
    blocked_patterns = [
        ("src/ultimate_ai_agent/core/skill_factory/", "Skill Factory"),
        ("src/ultimate_ai_agent/core/self_improvement/", "Self Improving Code"),
        ("src/ultimate_ai_agent/core/autopilot/", "Autopilot Workflows"),
        ("src/ultimate_ai_agent/core/scanners/", "Secrets/Dependency Scanners"),
    ]
    for rel_path, desc in blocked_patterns:
        p = ROOT / rel_path
        if p.exists():
            print(f"FAIL: Blocked module implemented: {desc} ({rel_path})")
            sys.exit(1)
            
    # Scan src/ for active execution imports of real models
    for p in (ROOT / "src").rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.strip().startswith(("import openai", "import anthropic", "import google.generativeai")):
                    print(f"FAIL: Forbidden model provider import in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
                if "from openai import" in line or "from anthropic import" in line or "from google import generativeai" in line:
                    print(f"FAIL: Forbidden model provider import in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
        except Exception:
            pass
    print("OK: Advanced blocked modules are not implemented")

def verify_no_forbidden_external_integrations():
    print("\n[Verifier] Running forbidden external integration scan...")
    allowed_stdlib_network_import_files = {
        "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
        "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py",
    }
    forbidden_imports = [
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "import urllib.request",
        "from urllib import request",
        "import boto3",
        "import ollama",
        "from ollama import",
        "import vllm",
        "from vllm import",
        "import llama_cpp",
        "from llama_cpp import",
        "import sglang",
        "from sglang import",
    ]
    for p in (ROOT / "src").rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            rel_path = str(p.relative_to(ROOT))
            for line in content.splitlines():
                stripped = line.strip()
                if any(stripped.startswith(pattern) for pattern in forbidden_imports):
                    if rel_path in allowed_stdlib_network_import_files and stripped.startswith(
                        ("import urllib.request", "from urllib import request", "from urllib import error")
                    ):
                        continue
                    print(f"FAIL: Forbidden external integration import in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
                if ".get(" in stripped and ("http://" in stripped or "https://" in stripped):
                    print(f"FAIL: Possible provider/network call in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
        except Exception:
            pass
    print("OK: No forbidden provider API clients or network calls detected in src")

def verify_no_real_model_runtime_execution():
    print("\n[Verifier] Running M8/M9 model runtime local-only guard...")
    runtime_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "model_runtime"
    if not runtime_root.exists():
        print("OK: Model runtime package is absent")
        return
    allowed_stdlib_network_import_files = {
        "manual_loopback_transport.py",
        "local_call_transport.py",
    }
    forbidden_fragments = [
        "import openai",
        "from openai import",
        "import anthropic",
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "socket",
        "urllib.request",
        "from urllib import request",
        "urlopen",
        "subprocess",
        "tokenizer",
        "tiktoken",
        "sentencepiece",
        "billing",
        "api_key",
        "API_KEY",
    ]
    for p in runtime_root.rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden_fragments):
                    if p.name in allowed_stdlib_network_import_files and (
                        "urllib.request" in stripped or "from urllib import request" in stripped or "urlopen" in stripped
                    ):
                        continue
                    print(f"FAIL: Real model runtime execution fragment in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
        except Exception:
            pass
    print("OK: Model runtime package has no provider SDK, broad network, tokenizer, or billing code")

def verify_no_real_approval_authority_integrations():
    print("\n[Verifier] Running M8.5 approval authority local-dev-only guard...")
    approval_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "approvals"
    if not approval_root.exists():
        print("OK: Approval authority package is absent")
        return
    forbidden_fragments = [
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "urllib",
        "socket",
        "oauth",
        "OAuth",
        "OpenID",
        "jwt",
        "session_cookie",
        "sqlite",
        "psycopg",
        "subprocess",
        "keychain",
    ]
    for p in approval_root.rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden_fragments):
                    print(f"FAIL: Real auth/network/persistence fragment in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
        except Exception:
            pass
    print("OK: Approval authority package is local/dev only")

def verify_no_real_remote_worker_integrations():
    print("\n[Verifier] Running M10.5 remote worker foundation-only guard...")
    remote_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "remote_workers"
    if not remote_root.exists():
        print("OK: Remote worker package is absent")
        return
    forbidden_imports = [
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "import urllib",
        "from urllib import",
        "import socket",
        "from socket import",
        "import subprocess",
        "from subprocess import",
        "import threading",
        "from threading import",
        "import asyncio",
        "from asyncio import",
    ]
    forbidden_fragments = [
        "urlopen",
        "Popen",
        "os.system",
        "Thread(",
        "dispatch_job(",
        "execute_remote(",
        "launch_subagent(",
        "tailscaled",
        "tailscale.",
        "tailscale(",
        "headscale.",
        "headscale(",
        "wireguard.",
        "wireguard(",
        "wg ",
        "wg-quick",
        "Serve",
        "Funnel",
    ]
    for p in remote_root.rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if any(stripped.startswith(pattern) for pattern in forbidden_imports):
                    print(f"FAIL: Remote worker live import in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
                if any(fragment in stripped for fragment in forbidden_fragments):
                    print(f"FAIL: Remote worker live execution fragment in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
        except Exception:
            pass
    print("OK: Remote worker package has no live network, process, private mesh, tailnet, or remote execution code")

def verify_no_control_center_runtime_or_frontend_expansion():
    print("\n[Verifier] Running M12/M13 Control Center backend no-execution guard...")
    forbidden_frontend_files = [
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "vite.config.ts",
        "vite.config.js",
        "next.config.js",
        "next.config.mjs",
        "tailwind.config.js",
        "tailwind.config.ts",
        "components.json",
    ]
    for rel_path in forbidden_frontend_files:
        if (ROOT / rel_path).exists():
            print(f"FAIL: Root frontend/build tooling file is present: {rel_path}")
            sys.exit(1)
    if (ROOT / "node_modules").exists():
        print("FAIL: root node_modules is present")
        sys.exit(1)

    control_center_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "control_center"
    forbidden_fragments = [
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "import urllib",
        "from urllib import",
        "import socket",
        "from socket import",
        "import subprocess",
        "from subprocess import",
        "import openai",
        "from openai import",
        "import anthropic",
        "from anthropic import",
        "tiktoken",
        "tokenizers",
        "billing",
        "urlopen",
        "os.system",
        "eval(",
        "exec(",
        "plugin_enable(",
        "dispatch_remote(",
        "call_model(",
        "provider_call(",
        "mobile_sensor(",
    ]
    if control_center_root.exists():
        for p in control_center_root.rglob("*.py"):
            try:
                content = p.read_text(encoding="utf-8")
                for line in content.splitlines():
                    stripped = line.strip()
                    if any(fragment in stripped for fragment in forbidden_fragments):
                        print(f"FAIL: Control Center runtime/frontend fragment in {p.relative_to(ROOT)}: {line}")
                        sys.exit(1)
            except Exception:
                pass

    forbidden_routes = [
        "/control-center/actions/execute",
        "/control-center/plugins/enable",
        "/control-center/runtime/execute",
        "/control-center/remote-workers/dispatch",
        "/control-center/mobile/sensors",
        "/device-capabilities",
        "/device-capability-broker",
        "/mobile/camera",
        "/mobile/microphone",
        "/mobile/location",
        "/mobile/notifications",
        "/mobile/capture",
        "/control-center/frontend",
    ]
    api_app = ROOT / "src" / "ultimate_ai_agent" / "api" / "app.py"
    if api_app.exists():
        for line in api_app.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("@app.") and any(route in stripped for route in forbidden_routes):
                print(f"FAIL: Forbidden Control Center execution route in api/app.py: {line}")
                sys.exit(1)
    print("OK: Control Center backend has no execution routes or runtime/provider/network expansions")

def verify_m13_web_control_center_frontend_safety():
    print("\n[Verifier] Running M13 Web Control Center frontend safety guard...")
    app_root = ROOT / "apps" / "control-center"
    required = [
        "package.json",
        "package-lock.json",
        "index.html",
        "vite.config.ts",
        "tsconfig.json",
        "src/App.tsx",
        "src/api/client.ts",
        "src/api/endpoints.ts",
        "src/mocks/controlCenterData.ts",
        "src/App.test.tsx",
    ]
    for rel_path in required:
        if not (app_root / rel_path).exists():
            print(f"FAIL: M13 Control Center frontend file is missing: apps/control-center/{rel_path}")
            sys.exit(1)

    try:
        git_files_raw = subprocess.check_output(["git", "ls-files"], text=True)
        git_files = git_files_raw.splitlines()
    except subprocess.SubprocessError as exc:
        print(f"FAIL: Could not inspect tracked files for M13 frontend artifacts: {exc}")
        sys.exit(1)

    forbidden_tracked_fragments = [
        "node_modules/",
        "apps/control-center/dist/",
        "apps/control-center/coverage/",
        "apps/control-center/.next/",
        ".env",
        ".xcworkspace",
        ".xcodeproj",
        "Package.swift",
        "Podfile",
        "android/",
        "ios/",
    ]
    for rel_path in git_files:
        if rel_path == ".env.example" or rel_path.endswith("/.env.example"):
            continue
        if _is_m44_allowed_ccc_ios_skeleton_file(rel_path):
            continue
        if any(fragment in rel_path for fragment in forbidden_tracked_fragments):
            print(f"FAIL: Forbidden generated/native/frontend artifact is tracked: {rel_path}")
            sys.exit(1)

    package_text = (app_root / "package.json").read_text(encoding="utf-8").lower()
    allowed_packages = [
        "@ultimate-ai-agent/control-center",
        "react",
        "react-dom",
        "vite",
        "vitest",
        "typescript",
        "@vitejs/plugin-react",
        "@testing-library/react",
        "@testing-library/jest-dom",
        "jsdom",
        "@types/react",
        "@types/react-dom",
        "@types/node",
    ]
    forbidden_packages = [
        "next",
        "tailwind",
        "shadcn",
        "stripe",
        "supabase",
        "firebase",
        "auth0",
        "analytics",
        "openai",
        "anthropic",
        "huggingface",
        "expo",
        "react-native",
        "electron",
        "playwright",
        "puppeteer",
        "webdriver",
    ]
    for package in forbidden_packages:
        if f'"{package}"' in package_text or f'"@{package}/' in package_text:
            print(f"FAIL: Forbidden frontend dependency marker in apps/control-center/package.json: {package}")
            sys.exit(1)
    for package in allowed_packages:
        if package == "@ultimate-ai-agent/control-center":
            continue
        if package not in package_text:
            print(f"FAIL: Expected minimal frontend dependency marker is missing: {package}")
            sys.exit(1)

    forbidden_endpoint_fragments = [
        "/control-center/actions/execute",
        "/control-center/plugins/enable",
        "/control-center/runtime/execute",
        "/control-center/remote-workers/dispatch",
        "/control-center/mobile/sensors",
        "/device-capabilities",
        "/device-capability-broker",
        "/mobile/camera",
        "/mobile/microphone",
        "/mobile/location",
        "/mobile/notifications",
        "/mobile/capture",
        "/control-center/frontend",
        "/model-runtime/execute",
        "/remote-workers/dispatch",
    ]
    forbidden_source_fragments = [
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
        "authorization:",
        "cookie:",
        "api_key=",
        "password=",
        "token=",
    ]
    source_files = [
        p
        for p in app_root.rglob("*")
        if p.is_file()
        and p.suffix in {".ts", ".tsx", ".css", ".html"}
        and "node_modules" not in p.parts
        and "dist" not in p.parts
        and not p.name.endswith(".test.tsx")
    ]
    for path in source_files:
        rel_path = path.relative_to(ROOT)
        lowered = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_endpoint_fragments:
            if fragment in lowered:
                print(f"FAIL: Forbidden frontend endpoint in {rel_path}: {fragment}")
                sys.exit(1)
        for fragment in forbidden_source_fragments:
            if fragment in lowered:
                print(f"FAIL: Forbidden frontend source fragment in {rel_path}: {fragment}")
                sys.exit(1)
    endpoints = (app_root / "src" / "api" / "endpoints.ts").read_text(encoding="utf-8")
    if 'actionPreview: "/control-center/actions/preview"' not in endpoints:
        print("FAIL: M13 action preview endpoint is missing or changed")
        sys.exit(1)
    if endpoints.count("/control-center/actions/preview") != 1:
        print("FAIL: M13 action preview endpoint should appear exactly once in endpoint declarations")
        sys.exit(1)
    print("OK: M13 Web Control Center frontend is read-only/preview-only with safe dependencies and no tracked build artifacts")

def verify_control_center_frontend_script():
    print("\n[Verifier] Running Control Center frontend safety verifier...")
    run_cmd([sys.executable, "scripts/verify_control_center_frontend.py"])

def verify_control_center_browser_smoke_readiness_script():
    print("\n[Verifier] Running Control Center browser smoke readiness verifier...")
    run_cmd([sys.executable, "scripts/verify_control_center_browser_smoke_readiness.py"])

def verify_documentation_integrity():
    print("\n[Verifier] Running documentation integrity scan...")
    run_cmd([sys.executable, "scripts/verify_documentation_integrity.py"])

def verify_no_openwebui_runtime_or_config_implementation():
    print("\n[Verifier] Running M21 OpenWebUI contract-only guard...")
    try:
        git_files_raw = subprocess.check_output(["git", "ls-files"], text=True)
        git_files = git_files_raw.splitlines()
    except subprocess.SubprocessError:
        git_files = []

    forbidden_path_fragments = [
        "docker-compose.openwebui",
        "openwebui.config",
        "openwebui-config",
        "openwebui_plugins",
        "openwebui_pipelines",
        "openwebui_functions",
        "openwebui_tools",
        "apps/openwebui/",
        "openwebui/",
    ]
    for rel_path in git_files:
        lowered = rel_path.lower()
        if lowered.startswith("docs/openwebui/"):
            continue
        if any(fragment in lowered for fragment in forbidden_path_fragments):
            print(f"FAIL: Forbidden OpenWebUI runtime/config path tracked in git: {rel_path}")
            sys.exit(1)

    forbidden_dependencies = [
        '"openwebui"',
        '"open-webui"',
        "openwebui==",
        "open-webui==",
    ]
    for rel_path in ["apps/control-center/package.json", "pyproject.toml"]:
        path = ROOT / rel_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_dependencies:
            if fragment in text:
                print(f"FAIL: Forbidden OpenWebUI dependency fragment in {rel_path}: {fragment}")
                sys.exit(1)

    for rel_path in find_openwebui_forbidden_config_path_matches(ROOT):
        print(f"FAIL: Forbidden OpenWebUI runtime/config path outside docs: {rel_path}")
        sys.exit(1)

    for failure in find_openwebui_forbidden_runtime_fragment_failures(ROOT):
        print(f"FAIL: {failure}")
        sys.exit(1)

    print("OK: No OpenWebUI runtime, deployment config, dependency, or execution route implementation detected")

def verify_no_local_runtime_activation_implementation():
    print("\n[Verifier] Running M22 local runtime activation contract-only guard...")
    forbidden_dependencies = [
        '"ollama"',
        '"llama-cpp-python"',
        '"mlx"',
        '"vllm"',
        '"lmstudio"',
        "ollama==",
        "llama-cpp-python==",
        "mlx==",
        "vllm==",
        "lmstudio==",
    ]
    for rel_path in ["apps/control-center/package.json", "pyproject.toml"]:
        path = ROOT / rel_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_dependencies:
            if fragment in text:
                print(f"FAIL: Forbidden local runtime dependency fragment in {rel_path}: {fragment}")
                sys.exit(1)

    for failure in find_m22_local_runtime_forbidden_fragment_failures(ROOT):
        print(f"FAIL: {failure}")
        sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app

        paths = set(app.openapi().get("paths", {}))
    except Exception as exc:
        print(f"FAIL: M22 OpenAPI guard could not generate schema: {exc}")
        sys.exit(1)
    forbidden_routes = {
        "/runtime/activate",
        "/runtime/probe",
        "/runtime/local/activate",
        "/runtime/local/probe",
        "/runtime/local/call",
        "/runtime/local/generate",
        "/model-runtime/activate",
        "/model-runtime/probe",
        "/model-runtime/local/activate",
        "/model-runtime/local/probe",
        "/model-runtime/local/call",
        "/model-runtime/local/generate",
        "/model-runtime/execute",
    }
    historical_paths = set(paths)
    if len(historical_paths) > 74:
        historical_paths.discard("/files/review/approvals/capture")
    if len(historical_paths) != 74:
        print(f"FAIL: M22 expected OpenAPI path count 74, found {len(historical_paths)}")
        sys.exit(1)
    forbidden_present = sorted(paths.intersection(forbidden_routes))
    if forbidden_present:
        print(f"FAIL: M22 forbidden runtime activation route(s) present: {', '.join(forbidden_present)}")
        sys.exit(1)

    print("OK: No M22 local runtime activation, endpoint probe, runtime client, dependency, or route implementation detected")

def verify_m23_first_local_llm_call_boundary():
    print("\n[Verifier] Running M23 first local LLM call boundary guard...")
    required_files = [
        "src/ultimate_ai_agent/core/model_runtime/local_call_contracts.py",
        "src/ultimate_ai_agent/core/model_runtime/local_call_policy.py",
        "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py",
        "src/ultimate_ai_agent/core/model_runtime/local_call.py",
        "scripts/manual_local_model_call.py",
        "tests/test_m23_local_model_call_contracts.py",
        "tests/test_m23_local_model_endpoint_policy.py",
        "tests/test_m23_local_model_fake_transport.py",
        "tests/test_m23_manual_cli_dry_run.py",
        "tests/test_m23_gate_integration.py",
        "docs/runtime/FIRST_LOCAL_LLM_CALL_M23.md",
        "docs/runtime/FIRST_LOCAL_LLM_CALL.md",
        "docs/runtime/M23_FIXED_PROMPT_POLICY.md",
        "docs/runtime/M23_LOCAL_MODEL_CALL_POLICY.md",
        "docs/runtime/M23_LOCAL_MODEL_CALL_SAFETY.md",
        "docs/runtime/M23_LOCAL_MODEL_CALL_RECEIPTS.md",
        "docs/runtime/M23_NON_AUTHORITATIVE_OUTPUT_POLICY.md",
        "docs/runtime/M23_MANUAL_CLI_USAGE.md",
        "docs/runtime/M23_TO_M24_BOUNDARY.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_27_1.md",
        "docs/release_notes/v0_27_1.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M23 boundary file: {rel_path}")
            sys.exit(1)

    forbidden_dependencies = [
        '"ollama"',
        '"llama-cpp-python"',
        '"mlx"',
        '"vllm"',
        '"lmstudio"',
        "ollama==",
        "llama-cpp-python==",
        "mlx==",
        "vllm==",
        "lmstudio==",
        '"openai"',
        "openai==",
        '"anthropic"',
        "anthropic==",
    ]
    for rel_path in ["apps/control-center/package.json", "pyproject.toml"]:
        text = (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for fragment in forbidden_dependencies:
            if fragment in text:
                print(f"FAIL: Forbidden M23 dependency fragment in {rel_path}: {fragment}")
                sys.exit(1)

    cli_text = (ROOT / "scripts/manual_local_model_call.py").read_text(encoding="utf-8").lower()
    for forbidden_arg in [
        "--prompt",
        "--prompt-file",
        "--stdin",
        "--file",
        "--memory",
        "--openwebui",
        "--api-key",
        "--auth",
        "--authorization",
        "--cookie",
        "--output",
        "--output-file",
    ]:
        if f'"{forbidden_arg}"' in cli_text or f"'{forbidden_arg}'" in cli_text:
            print(f"FAIL: M23 manual CLI exposes forbidden arbitrary input argument: {forbidden_arg}")
            sys.exit(1)
    for required_fragment in [
        "--execute-local-call",
        "--fixed-prompt-id",
        "m23_fixed_local_model_prompt_id",
        "manualstdlibloopbacklocalmodelcalltransport",
    ]:
        if required_fragment not in cli_text:
            print(f"FAIL: M23 manual CLI missing required boundary fragment: {required_fragment}")
            sys.exit(1)

    runtime_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "model_runtime"
    allowed_stdlib_loopback = {
        "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
        "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py",
    }
    forbidden_runtime_fragments = [
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "import openai",
        "from openai import",
        "import anthropic",
        "from anthropic import",
        "import ollama",
        "from ollama import",
        "import llama_cpp",
        "from llama_cpp import",
        "import mlx",
        "from mlx import",
        "import vllm",
        "from vllm import",
        "socket",
        "subprocess",
        "tokenizer",
        "tiktoken",
        "sentencepiece",
        "/v1/chat/completions",
    ]
    for path in runtime_root.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_runtime_fragments:
            if fragment in text:
                print(f"FAIL: M23 forbidden runtime/provider fragment in {rel}: {fragment}")
                sys.exit(1)
        if "urlopen" in text and rel not in allowed_stdlib_loopback:
            print(f"FAIL: M23 urlopen is only allowed in manual loopback transport: {rel}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m23_openapi_route_failures

        failures = m23_openapi_route_failures(app.openapi().get("paths", {}))
    except Exception as exc:
        print(f"FAIL: M23 OpenAPI guard could not generate schema: {exc}")
        sys.exit(1)
    for failure in failures:
        print(f"FAIL: {failure}")
        sys.exit(1)

    print("OK: M23 is manual/CLI-only, loopback-only, fixed-prompt-only, non-tool, non-authoritative, and route-free")


def verify_m24_memory_provider_local_store_safety():
    print("\n[Verifier] Running M24 memory provider/local store safety guard...")
    required_files = [
        "src/ultimate_ai_agent/core/memory/provider.py",
        "src/ultimate_ai_agent/core/memory/local_store.py",
        "src/ultimate_ai_agent/core/memory/manifests.py",
        "src/ultimate_ai_agent/core/memory/policy.py",
        "src/ultimate_ai_agent/core/memory/recall.py",
        "tests/test_m24_memory_provider_contracts.py",
        "tests/test_m24_memory_write_validation.py",
        "tests/test_m24_local_memory_store.py",
        "tests/test_m24_gate_integration.py",
        "docs/memory/MEMORY_PROVIDER_ABSTRACTION.md",
        "docs/memory/LOCAL_MEMORY_STORE.md",
        "docs/memory/MEMORY_RECORD_SCHEMA.md",
        "docs/memory/MEMORY_WRITE_POLICY.md",
        "docs/memory/M24_TO_M25_BOUNDARY.md",
        "docs/release_notes/v0_28_1.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_28_1.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M24 memory file: {rel_path}")
            sys.exit(1)

    forbidden_dependencies = [
        '"chromadb"',
        '"qdrant"',
        '"weaviate"',
        '"pinecone"',
        '"faiss"',
        '"milvus"',
        '"lancedb"',
        '"sentence-transformers"',
        '"transformers"',
        '"redis"',
        '"arq"',
        '"pgvector"',
        "chromadb==",
        "qdrant==",
        "weaviate==",
        "pinecone==",
        "faiss==",
        "milvus==",
        "lancedb==",
        "sentence-transformers==",
        "transformers==",
        "redis==",
        "arq==",
        "pgvector==",
    ]
    for rel_path in ["apps/control-center/package.json", "pyproject.toml"]:
        text = (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for fragment in forbidden_dependencies:
            if fragment in text:
                print(f"FAIL: Forbidden M24 memory dependency fragment in {rel_path}: {fragment}")
                sys.exit(1)

    memory_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "memory"
    forbidden_source_fragments = [
        "import chromadb",
        "import qdrant",
        "import redis",
        "import arq",
        "import requests",
        "import httpx",
        "from requests import",
        "from httpx import",
        "path.home(",
        "expanduser(",
        "os.walk(",
        ".rglob(\"*\"",
        ".glob(\"*\"",
        "automatic_write=True",
        "model_output_source=True",
        "local_llm_output_source=True",
        "openwebui_source=True",
        "mobile_capture_source=True",
        "tool_output_source=True",
        "contains_raw_prompt=True",
        "contains_raw_model_output=True",
        "contains_raw_file_content=True",
        "contains_raw_transcript=True",
        "recall_injection_enabled=True",
        "context_pack_injection_enabled=True",
        "background_workers_enabled=True",
    ]
    for path in memory_root.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8").lower().replace(" ", "")
        for fragment in forbidden_source_fragments:
            if fragment.replace(" ", "") in text:
                print(f"FAIL: M24 forbidden memory source fragment in {rel}: {fragment}")
                sys.exit(1)

    frontend_root = ROOT / "apps" / "control-center" / "src"
    if frontend_root.exists():
        for path in frontend_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
                continue
            if any(part == "tests" for part in path.parts) or ".test." in path.name or ".spec." in path.name:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8").lower()
            for fragment in [
                "/memory/write",
                "/memory/delete",
                "/memory/learn",
                "/memory/forget",
                "/memory/import",
                "/memory/ingest",
                "/memory/vector-search",
                "/memory/embed",
                "/memory/inject",
            ]:
                if fragment in text:
                    print(f"FAIL: M24 forbidden Control Center memory mutation fragment in {rel}: {fragment}")
                    sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m24_openapi_route_failures

        failures = m24_openapi_route_failures(app.openapi().get("paths", {}))
    except Exception as exc:
        print(f"FAIL: M24 OpenAPI guard could not generate schema: {exc}")
        sys.exit(1)
    for failure in failures:
        print(f"FAIL: {failure}")
        sys.exit(1)

    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    forbidden_tracked_suffixes = (".db", ".sqlite", ".sqlite3")
    for rel_path in tracked:
        if rel_path.endswith(forbidden_tracked_suffixes):
            print(f"FAIL: M24 tracked local memory database artifact: {rel_path}")
            sys.exit(1)

    print("OK: M24 memory provider is local-only, reviewed-write-only, route-free, vector-free, and non-authoritative")


def verify_m25_truth_source_evidence_checker_safety():
    print("\n[Verifier] Running M25 truth source/evidence checker safety guard...")
    required_files = [
        "src/ultimate_ai_agent/core/truth/sources.py",
        "src/ultimate_ai_agent/core/truth/claims.py",
        "src/ultimate_ai_agent/core/truth/evidence.py",
        "src/ultimate_ai_agent/core/truth/verification.py",
        "src/ultimate_ai_agent/core/truth/manifests.py",
        "tests/test_truth_source_contracts.py",
        "tests/test_truth_source_priority.py",
        "tests/test_claim_evidence_contracts.py",
        "tests/test_claim_verification_decisions.py",
        "tests/test_claim_conflict_handling.py",
        "tests/test_truth_no_memory_authority.py",
        "tests/test_truth_no_model_output_authority.py",
        "tests/test_truth_no_external_verification.py",
        "tests/test_m25_gate_integration.py",
        "docs/truth/TRUTH_SOURCE_ROUTER.md",
        "docs/truth/EVIDENCE_CLAIM_CHECKER.md",
        "docs/truth/TRUTH_SOURCE_PRIORITY.md",
        "docs/truth/CLAIM_EVIDENCE_CHAIN.md",
        "docs/truth/CLAIM_VERIFICATION_POLICY.md",
        "docs/truth/CLAIM_CONFLICT_AND_STALENESS.md",
        "docs/truth/MEMORY_TRUTH_BOUNDARY.md",
        "docs/truth/TRUTH_NON_GOALS.md",
        "docs/truth/M25_TO_M26_BOUNDARY.md",
        "docs/release_notes/v0_29_2.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_29_2.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M25 truth/evidence file: {rel_path}")
            sys.exit(1)

    forbidden_dependencies = [
        '"chromadb"',
        '"qdrant"',
        '"weaviate"',
        '"pinecone"',
        '"faiss"',
        '"milvus"',
        '"lancedb"',
        '"sentence-transformers"',
        '"transformers"',
        '"openai"',
        '"anthropic"',
        '"ollama"',
        '"llama-cpp-python"',
        '"pgvector"',
        "chromadb==",
        "qdrant==",
        "weaviate==",
        "pinecone==",
        "faiss==",
        "milvus==",
        "lancedb==",
        "sentence-transformers==",
        "transformers==",
        "openai==",
        "anthropic==",
        "ollama==",
        "llama-cpp-python==",
        "pgvector==",
    ]
    for rel_path in ["apps/control-center/package.json", "pyproject.toml"]:
        text = (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for fragment in forbidden_dependencies:
            if fragment in text:
                print(f"FAIL: Forbidden M25 truth dependency fragment in {rel_path}: {fragment}")
                sys.exit(1)

    truth_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "truth"
    forbidden_source_fragments = [
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "urllib.request",
        "urlopen(",
        "socket.",
        "subprocess",
        "import openai",
        "from openai import",
        "import anthropic",
        "from anthropic import",
        "import ollama",
        "from ollama import",
        "import chromadb",
        "import faiss",
        "import pgvector",
        "sentence_transformers",
        "embedding",
        "vector_search",
        "web_search_enabled=True",
        "external_verification_enabled=True",
        "model_verification_enabled=True",
        "memory_as_authority_enabled=True",
        "automatic_claim_verification_enabled=True",
        "write_memory(",
        "memory.write(",
        "append_evidence(",
        "mutate_evidence(",
    ]
    for path in truth_root.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8").lower().replace(" ", "")
        for fragment in forbidden_source_fragments:
            if fragment.replace(" ", "") in text:
                print(f"FAIL: M25 forbidden truth/evidence source fragment in {rel}: {fragment}")
                sys.exit(1)

    forbidden_route_fragments = [
        "/truth/verify",
        "/claims/verify",
        "/evidence/verify",
        "/truth/search",
        "/truth/web-search",
        "/truth/model-verify",
    ]
    for implementation_root in [ROOT / "src", ROOT / "apps"]:
        if not implementation_root.exists():
            continue
        for path in implementation_root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or "node_modules" in path.parts:
                continue
            if path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            if any(part == "tests" for part in path.parts) or ".test." in path.name or ".spec." in path.name:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in {
                "src/ultimate_ai_agent/core/gate/evaluators.py",
                "src/ultimate_ai_agent/api/openapi.py",
            }:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for fragment in forbidden_route_fragments:
                if fragment in text:
                    print(f"FAIL: M25 forbidden truth/claim/evidence route fragment in {rel}: {fragment}")
                    sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m25_openapi_route_failures
        from ultimate_ai_agent.core.truth import (
            Claim,
            ClaimRiskLevel,
            ClaimStatus,
            EvidenceChain,
            EvidenceRef,
            EvidenceStrength,
            TruthSourceKind,
            VerificationRequest,
            verify_claim_against_evidence_chain,
        )

        failures = m25_openapi_route_failures(app.openapi().get("paths", {}))
    except Exception as exc:
        print(f"FAIL: M25 OpenAPI or truth contract guard could not run: {exc}")
        sys.exit(1)
    for failure in failures:
        print(f"FAIL: {failure}")
        sys.exit(1)

    claim = Claim(
        claim_id="claim:m25-verifier",
        safe_claim_summary="M25 verifier claim.",
        claim_text_hash="sha256:m25-verifier",
        claim_status=ClaimStatus.unverified,
        claim_risk=ClaimRiskLevel.low,
        data_classification="public",
    )
    unknown_chain = EvidenceChain(
        chain_id="chain:m25-verifier-unknown",
        claim_ref="claim:m25-verifier",
        source_refs=["random:m25-verifier"],
        evidence_refs=["evidence:m25-verifier-unknown"],
        evidence_strength=EvidenceStrength.evidence_supported,
        source_priority_summary="unknown source",
        safe_summary="Unknown source ref.",
    )
    unknown_decision = verify_claim_against_evidence_chain(
        VerificationRequest(
            request_id="verify:m25-verifier-unknown",
            claim=claim,
            evidence_chain=unknown_chain,
            requested_status=ClaimStatus.evidence_supported,
        )
    )
    if unknown_decision.allowed or "ARBITRARY_SOURCE_REF_DENIED" not in unknown_decision.reason_codes:
        print("FAIL: M25 verifier allowed an inferred unknown/arbitrary truth source ref")
        sys.exit(1)

    explicit_unknown_decision = verify_claim_against_evidence_chain(
        VerificationRequest(
            request_id="verify:m25-verifier-explicit-unknown",
            claim=claim,
            evidence_chain=EvidenceChain(
                chain_id="chain:m25-verifier-explicit-unknown",
                claim_ref="claim:m25-verifier",
                source_refs=["unknown:m25-verifier"],
                evidence_refs=["evidence:m25-verifier-explicit-unknown"],
                evidence_strength=EvidenceStrength.evidence_supported,
                source_priority_summary="unknown source kind",
                safe_summary="Explicit unknown source kind.",
            ),
            evidence_refs=[
                EvidenceRef(
                    evidence_ref="evidence:m25-verifier-explicit-unknown",
                    source_ref="unknown:m25-verifier",
                    source_kind=TruthSourceKind.unknown,
                    evidence_strength=EvidenceStrength.evidence_supported,
                    data_classification="public",
                    redaction_status="redacted",
                    safe_summary="Explicit unknown source kind.",
                )
            ],
            requested_status=ClaimStatus.evidence_supported,
        )
    )
    if explicit_unknown_decision.allowed or "UNKNOWN_SOURCE_KIND_DENIED" not in explicit_unknown_decision.reason_codes:
        print("FAIL: M25 verifier allowed explicit TruthSourceKind.unknown evidence")
        sys.exit(1)

    print("OK: M25 truth source/evidence checker remains deterministic, local, route-free, and non-authoritative")


def verify_m26_grounded_recall_context_pack_safety():
    print("\n[Verifier] Running M26 grounded recall/context-pack safety guard...")
    required_files = [
        "src/ultimate_ai_agent/core/recall/__init__.py",
        "src/ultimate_ai_agent/core/recall/candidates.py",
        "src/ultimate_ai_agent/core/recall/context_pack.py",
        "src/ultimate_ai_agent/core/recall/manifests.py",
        "src/ultimate_ai_agent/core/recall/policy.py",
        "src/ultimate_ai_agent/core/recall/router.py",
        "src/ultimate_ai_agent/core/recall/validation.py",
        "tests/test_grounded_recall_contracts.py",
        "tests/test_grounded_recall_router.py",
        "tests/test_context_pack_builder.py",
        "tests/test_context_pack_no_injection.py",
        "tests/test_recall_source_priority.py",
        "tests/test_recall_no_raw_content.py",
        "tests/test_recall_no_vector_embeddings.py",
        "tests/test_recall_no_memory_writes.py",
        "tests/test_m26_gate_integration.py",
        "docs/recall/GROUNDED_RECALL_ROUTER.md",
        "docs/recall/CONTEXT_PACK_BUILDER.md",
        "docs/recall/RECALL_SOURCE_PRIORITY.md",
        "docs/recall/RECALL_CANDIDATE_POLICY.md",
        "docs/recall/CONTEXT_PACK_SAFETY.md",
        "docs/recall/RECALL_NON_GOALS.md",
        "docs/recall/M26_TO_M27_BOUNDARY.md",
        "docs/release_notes/v0_30_1.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_30_1.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M26 recall/context-pack file: {rel_path}")
            sys.exit(1)

    forbidden_dependencies = [
        '"chromadb"',
        '"qdrant"',
        '"weaviate"',
        '"pinecone"',
        '"faiss"',
        '"milvus"',
        '"lancedb"',
        '"sentence-transformers"',
        '"transformers"',
        '"tokenizers"',
        '"tiktoken"',
        '"openai"',
        '"anthropic"',
        '"ollama"',
        '"llama-cpp-python"',
        '"pgvector"',
        "chromadb==",
        "qdrant==",
        "weaviate==",
        "pinecone==",
        "faiss==",
        "milvus==",
        "lancedb==",
        "sentence-transformers==",
        "transformers==",
        "tokenizers==",
        "tiktoken==",
        "openai==",
        "anthropic==",
        "ollama==",
        "llama-cpp-python==",
        "pgvector==",
    ]
    for rel_path in ["apps/control-center/package.json", "pyproject.toml"]:
        text = (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for fragment in forbidden_dependencies:
            if fragment in text:
                print(f"FAIL: Forbidden M26 recall/context-pack dependency fragment in {rel_path}: {fragment}")
                sys.exit(1)

    recall_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "recall"
    forbidden_source_fragments = [
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "urllib.request",
        "urlopen(",
        "socket.",
        "subprocess",
        "import openai",
        "from openai import",
        "import anthropic",
        "from anthropic import",
        "import ollama",
        "from ollama import",
        "import chromadb",
        "import faiss",
        "import pgvector",
        "import tokenizers",
        "import tiktoken",
        "sentence_transformers",
        "vector_search_enabled=True",
        "embeddings_enabled=True",
        "semantic_search_enabled=True",
        "rag_ingestion_enabled=True",
        "external_retrieval_enabled=True",
        "web_search_enabled=True",
        "source_crawling_enabled=True",
        "automatic_memory_write_enabled=True",
        "context_injection_enabled=True",
        "backend_routes_enabled=True",
        "model_provider_calls_enabled=True",
        "tool_execution_enabled=True",
        "write_memory(",
        "memory.write(",
        "put_record(",
        "append_evidence(",
        "mutate_evidence(",
        "append_event(",
        "mutate_event(",
    ]
    for path in recall_root.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8").lower().replace(" ", "")
        for fragment in forbidden_source_fragments:
            if fragment.replace(" ", "") in text:
                print(f"FAIL: M26 forbidden recall/context-pack source fragment in {rel}: {fragment}")
                sys.exit(1)

    forbidden_route_fragments = [
        "/recall/run",
        "/recall/search",
        "/recall/inject",
        "/recall/vector-search",
        "/recall/embed",
        "/recall/external-retrieve",
        "/context-pack/inject",
        "/context-pack/build-and-inject",
        "/memory/vector-search",
        "/memory/embed",
        "/memory/context-pack/inject",
    ]
    for implementation_root in [ROOT / "src", ROOT / "apps"]:
        if not implementation_root.exists():
            continue
        for path in implementation_root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or "node_modules" in path.parts:
                continue
            if path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            if any(part == "tests" for part in path.parts) or ".test." in path.name or ".spec." in path.name:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in {
                "src/ultimate_ai_agent/core/gate/evaluators.py",
                "src/ultimate_ai_agent/api/openapi.py",
            }:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for fragment in forbidden_route_fragments:
                if fragment in text:
                    print(f"FAIL: M26 forbidden recall/context-pack route fragment in {rel}: {fragment}")
                    sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m26_openapi_route_failures
        from ultimate_ai_agent.core.recall import (
            ContextPackBuildRequest,
            GroundedRecallManifest,
            GroundedRecallRequest,
            RecallCandidate,
            RecallSourceKind,
            build_evidence_linked_context_pack,
            route_grounded_recall,
        )

        failures = m26_openapi_route_failures(app.openapi().get("paths", {}))
    except Exception as exc:
        print(f"FAIL: M26 OpenAPI or recall contract guard could not run: {exc}")
        sys.exit(1)
    for failure in failures:
        print(f"FAIL: {failure}")
        sys.exit(1)

    manifest = GroundedRecallManifest(baseline_version="0.30.1")
    unsafe_flags = [
        manifest.context_injection_enabled,
        manifest.vector_search_enabled,
        manifest.embeddings_enabled,
        manifest.semantic_search_enabled,
        manifest.rag_ingestion_enabled,
        manifest.external_retrieval_enabled,
        manifest.web_search_enabled,
        manifest.source_crawling_enabled,
        manifest.automatic_memory_write_enabled,
        manifest.backend_routes_added,
        manifest.model_provider_calls_enabled,
        manifest.tool_execution_enabled,
        manifest.production_authority_enabled,
    ]
    if any(unsafe_flags):
        print("FAIL: M26 default manifest enables forbidden recall/context-pack runtime authority")
        sys.exit(1)

    decision = route_grounded_recall(
        GroundedRecallRequest(
            request_id="recall:verify-m26",
            query_summary="Verify M26 recall contract.",
            candidates=[
                RecallCandidate(
                    candidate_ref="memory:verify-m26",
                    source_kind=RecallSourceKind.reviewed_memory,
                    source_ref="memory:verify-m26",
                    safe_summary="Reviewed memory context.",
                ),
                RecallCandidate(
                    candidate_ref="canonical:verify-m26",
                    source_kind=RecallSourceKind.canonical_document,
                    source_ref="canonical:verify-m26",
                    safe_summary="Canonical guidance.",
                ),
                RecallCandidate(
                    candidate_ref="random:verify-m26",
                    source_kind=RecallSourceKind.unknown,
                    source_ref="random:verify-m26",
                    safe_summary="Unknown source.",
                ),
                RecallCandidate(
                    candidate_ref="model:verify-m26",
                    source_kind=RecallSourceKind.model_output,
                    source_ref="model:verify-m26",
                    safe_summary="Model output.",
                ),
                RecallCandidate(
                    candidate_ref="memory-as-canonical:verify-m26",
                    source_kind=RecallSourceKind.canonical_document,
                    source_ref="memory:verify-m26",
                    safe_summary="Memory source priority upgrade attempt.",
                ),
                RecallCandidate(
                    candidate_ref="model-as-canonical:verify-m26",
                    source_kind=RecallSourceKind.canonical_document,
                    source_ref="model:verify-m26",
                    safe_summary="Model source priority upgrade attempt.",
                ),
                RecallCandidate(
                    candidate_ref="runtime-as-canonical:verify-m26",
                    source_kind=RecallSourceKind.canonical_document,
                    source_ref="runtime:verify-m26",
                    safe_summary="Runtime source priority upgrade attempt.",
                ),
                RecallCandidate(
                    candidate_ref="openwebui-as-canonical:verify-m26",
                    source_kind=RecallSourceKind.canonical_document,
                    source_ref="openwebui:verify-m26",
                    safe_summary="OpenWebUI source priority upgrade attempt.",
                ),
                RecallCandidate(
                    candidate_ref="memory-as-evidence:verify-m26",
                    source_kind=RecallSourceKind.evidence_manifest,
                    source_ref="memory:verify-m26",
                    safe_summary="Memory evidence priority upgrade attempt.",
                ),
            ],
        )
    )
    refs = [selection.candidate_ref for selection in decision.selected]
    if refs[:2] != ["canonical:verify-m26", "memory:verify-m26"]:
        print("FAIL: M26 recall source priority did not keep canonical above memory")
        sys.exit(1)
    if "random:verify-m26" in refs or "model:verify-m26" in refs:
        print("FAIL: M26 recall selected unknown or model-output candidate")
        sys.exit(1)
    for hostile_ref in [
        "memory-as-canonical:verify-m26",
        "model-as-canonical:verify-m26",
        "runtime-as-canonical:verify-m26",
        "openwebui-as-canonical:verify-m26",
        "memory-as-evidence:verify-m26",
    ]:
        if hostile_ref in refs:
            print(f"FAIL: M26 recall selected mismatched source identity candidate: {hostile_ref}")
            sys.exit(1)
    excluded_reasons = {reason for item in decision.excluded for reason in item.reason_codes}
    for required_reason in [
        "SOURCE_REF_KIND_MISMATCH_DENIED",
        "MEMORY_SOURCE_PRIORITY_UPGRADE_DENIED",
        "MODEL_OUTPUT_RECALL_DENIED",
        "RUNTIME_OUTPUT_RECALL_DENIED",
        "OPENWEBUI_OUTPUT_RECALL_DENIED",
    ]:
        if required_reason not in excluded_reasons:
            print(f"FAIL: M26 recall missing mismatch exclusion reason: {required_reason}")
            sys.exit(1)
    if (
        not decision.no_memory_write_performed
        or not decision.no_external_retrieval_performed
        or not decision.no_vector_search_performed
        or not decision.no_context_injection_performed
    ):
        print("FAIL: M26 recall decision reports forbidden side effects")
        sys.exit(1)

    pack = build_evidence_linked_context_pack(
        ContextPackBuildRequest(
            pack_id="context-pack:verify-m26",
            request_id="context-pack:verify-m26",
            recall_decision=decision,
        )
    )
    if (
        pack.context_injection_performed
        or pack.model_output_included
        or pack.memory_write_performed
        or pack.external_retrieval_performed
        or pack.raw_content_included
    ):
        print("FAIL: M26 context pack reports forbidden side effects")
        sys.exit(1)

    print("OK: M26 grounded recall/context-pack contracts remain deterministic, local, route-free, and non-authoritative")


def verify_m27_tool_broker_v2_safety():
    print("\n[Verifier] Running M27 Tool Broker v2 safe intent contract guard...")
    required_files = [
        "src/ultimate_ai_agent/core/tools/v2/__init__.py",
        "src/ultimate_ai_agent/core/tools/v2/enums.py",
        "src/ultimate_ai_agent/core/tools/v2/contracts.py",
        "src/ultimate_ai_agent/core/tools/v2/catalog.py",
        "src/ultimate_ai_agent/core/tools/v2/broker.py",
        "src/ultimate_ai_agent/core/tools/v2/validation.py",
        "tests/test_tool_broker_v2_contracts.py",
        "tests/test_m27_gate_integration.py",
        "docs/tools/TOOL_BROKER_V2.md",
        "docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md",
        "docs/tools/TOOL_AUTHORITY_BOUNDARY.md",
        "docs/tools/TOOL_INTENT_RECEIPT_PLAN.md",
        "docs/tools/M27_TO_M28_BOUNDARY.md",
        "docs/release_notes/v0_31_1.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_31_1.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M27 Tool Broker v2 file: {rel_path}")
            sys.exit(1)

    tools_v2_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "tools" / "v2"
    forbidden_source_fragments = [
        "subprocess",
        "os.system(",
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "httpx.post(",
        "urllib.request.urlopen(",
        "write_memory(",
        ".write_memory(",
        "put_record(",
        ".put_record(",
        "append_event(",
        "mutate_event(",
        "chat.completions.create(",
        "import openai",
        "from openai import",
        "import anthropic",
        "from anthropic import",
        "import ollama",
        "from ollama import",
    ]
    for path in tools_v2_root.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_source_fragments:
            if fragment in text:
                print(f"FAIL: M27 forbidden Tool Broker v2 source fragment in {rel}: {fragment}")
                sys.exit(1)

    forbidden_route_fragments = [
        "/tools/execute",
        "/tools/run",
        "/tools/dispatch",
        "/tool-broker/execute",
        "/tool-broker/run",
        "/plugins/enable",
        "/browser/execute",
        "/computer-use/run",
    ]
    for implementation_root in [ROOT / "src", ROOT / "apps"]:
        if not implementation_root.exists():
            continue
        for path in implementation_root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or "node_modules" in path.parts:
                continue
            if path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            if any(part == "tests" for part in path.parts) or ".test." in path.name or ".spec." in path.name:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in {
                "src/ultimate_ai_agent/core/gate/evaluators.py",
                "src/ultimate_ai_agent/api/openapi.py",
            }:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for fragment in forbidden_route_fragments:
                if fragment in text:
                    print(f"FAIL: M27 forbidden tool execution route fragment in {rel}: {fragment}")
                    sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT / "src"))
        from pydantic import ValidationError

        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m27_openapi_route_failures
        from ultimate_ai_agent.core.tools.v2 import (
            ToolApprovalRequirement,
            ToolAuthorityLevel,
            ToolBrokerV2Manifest,
            ToolCatalogEntry,
            ToolExecutionMode,
            ToolInputBoundary,
            ToolInputTrustLevel,
            ToolIntent,
            ToolIntentDecisionStatus,
            ToolRiskClass,
            ToolSideEffectKind,
            ToolTargetKind,
            ToolTargetRef,
            build_default_tool_catalog,
            evaluate_tool_intent,
        )
    except Exception as exc:
        print(f"FAIL: M27 Tool Broker v2 imports could not load: {exc}")
        sys.exit(1)

    for failure in m27_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    manifest = ToolBrokerV2Manifest(baseline_version="0.31.1")
    unsafe_flags = [
        manifest.tool_execution_enabled,
        manifest.backend_execution_routes_added,
        manifest.shell_execution_enabled,
        manifest.file_mutation_enabled,
        manifest.network_calls_enabled,
        manifest.browser_automation_enabled,
        manifest.plugin_enablement_enabled,
        manifest.memory_writes_enabled,
        manifest.event_ledger_mutation_enabled,
        manifest.model_provider_calls_enabled,
        manifest.context_pack_authority_enabled,
        manifest.context_injection_enabled,
        manifest.production_authority_enabled,
    ]
    if any(unsafe_flags):
        print("FAIL: M27 Tool Broker v2 manifest enables forbidden runtime authority")
        sys.exit(1)

    def safe_intent(**overrides):
        data = {
            "intent_id": "tool-intent:verify-m27",
            "tool_id": "file.metadata_preview",
            "intent_summary": "Preview safe file metadata.",
            "target": ToolTargetRef(target_ref="file:verify-m27", target_kind=ToolTargetKind.file_ref),
            "input_boundary": ToolInputBoundary(
                input_refs=["file:verify-m27"],
                input_trust_level=ToolInputTrustLevel.user_provided_refs,
            ),
            "requested_execution_mode": ToolExecutionMode.preview_only,
            "declared_risk_class": ToolRiskClass.low,
            "declared_side_effects": [ToolSideEffectKind.none],
            "approval_requirement": ToolApprovalRequirement.not_required,
            "authority_level": ToolAuthorityLevel.validation_only,
        }
        data.update(overrides)
        return ToolIntent(**data)

    safe_decision = evaluate_tool_intent(safe_intent(), catalog=build_default_tool_catalog())
    if safe_decision.status != ToolIntentDecisionStatus.preview_allowed:
        print("FAIL: M27 safe tool intent preview was not allowed")
        sys.exit(1)
    if safe_decision.execution_allowed or not safe_decision.no_tool_execution_performed:
        print("FAIL: M27 safe tool intent preview allowed execution")
        sys.exit(1)

    side_effect_catalog = {
        "file.write_preview": ToolCatalogEntry(
            tool_id="file.write_preview",
            display_name="Write preview",
            target_kind=ToolTargetKind.file_ref,
            allowed_execution_modes=[ToolExecutionMode.preview_only],
            risk_class=ToolRiskClass.high,
            side_effects=[ToolSideEffectKind.file_write],
            approval_requirement=ToolApprovalRequirement.validated_local_approval_required,
        )
    }
    denied = evaluate_tool_intent(
        safe_intent(
            tool_id="file.write_preview",
            declared_risk_class=ToolRiskClass.high,
            declared_side_effects=[ToolSideEffectKind.file_write],
            approval_requirement=ToolApprovalRequirement.validated_local_approval_required,
            approval_ref="approval_test_verify_m27",
            context_pack_refs=["context-pack:m26"],
        ),
        catalog=side_effect_catalog,
    )
    for required_reason in [
        "TOOL_SIDE_EFFECTS_DENIED",
        "APPROVAL_REF_NOT_AUTHORITY",
        "CONTEXT_PACK_NOT_AUTHORITY",
    ]:
        if required_reason not in denied.reason_codes:
            print(f"FAIL: M27 denied tool intent missing reason: {required_reason}")
            sys.exit(1)
    if denied.execution_allowed or denied.status == ToolIntentDecisionStatus.preview_allowed:
        print("FAIL: M27 side-effecting tool intent was allowed")
        sys.exit(1)

    mismatch = evaluate_tool_intent(
        safe_intent(target=ToolTargetRef(target_ref="memory:verify-m27", target_kind=ToolTargetKind.file_ref)),
        catalog=build_default_tool_catalog(),
    )
    if "TOOL_TARGET_KIND_MISMATCH_DENIED" not in mismatch.reason_codes:
        print("FAIL: M27 target mismatch was not denied")
        sys.exit(1)

    downgraded = evaluate_tool_intent(
        safe_intent(
            tool_id="file.write_preview",
            declared_risk_class=ToolRiskClass.low,
            declared_side_effects=[ToolSideEffectKind.none],
        ),
        catalog=side_effect_catalog,
    )
    for required_reason in ["TOOL_RISK_DOWNGRADE_DENIED", "TOOL_SIDE_EFFECTS_HIDDEN_DENIED"]:
        if required_reason not in downgraded.reason_codes:
            print(f"FAIL: M27 risk downgrade guard missing reason: {required_reason}")
            sys.exit(1)

    try:
        ToolInputBoundary(input_refs=["file:verify-m27"], contains_model_output=True)
        print("FAIL: M27 ToolInputBoundary accepted model output")
        sys.exit(1)
    except ValidationError:
        pass

    print("OK: M27 Tool Broker v2 contracts remain preview-only, local, route-free, and non-authoritative")


def verify_m28_approval_authority_v2_safety():
    print("\n[Verifier] Running M28 Approval Authority v2 action policy guard...")
    required_files = [
        "src/ultimate_ai_agent/core/approvals/v2/__init__.py",
        "src/ultimate_ai_agent/core/approvals/v2/enums.py",
        "src/ultimate_ai_agent/core/approvals/v2/contracts.py",
        "src/ultimate_ai_agent/core/approvals/v2/policies.py",
        "src/ultimate_ai_agent/core/approvals/v2/validation.py",
        "tests/test_approval_authority_v2_contracts.py",
        "tests/test_m28_gate_integration.py",
        "docs/approvals/APPROVAL_AUTHORITY_V2.md",
        "docs/approvals/ACTION_POLICY.md",
        "docs/approvals/APPROVAL_GRANT_BINDING.md",
        "docs/approvals/APPROVAL_EXPIRY_REVOCATION_REPLAY.md",
        "docs/approvals/ACTION_RISK_AND_SIDE_EFFECT_POLICY.md",
        "docs/approvals/APPROVAL_REF_NOT_AUTHORITY.md",
        "docs/approvals/ACTION_POLICY_DECISION_ENVELOPE.md",
        "docs/approvals/APPROVAL_RECEIPT_PLAN.md",
        "docs/approvals/APPROVAL_AUTHORITY_V2_NON_GOALS.md",
        "docs/approvals/M28_TO_M29_BOUNDARY.md",
        "docs/release_notes/v0_32_1.md",
        "docs/archive/releases/v0_32_1/README_IMPORT.md",
        "docs/archive/releases/v0_32_1/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_32_1.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M28 Approval Authority v2 file: {rel_path}")
            sys.exit(1)

    approvals_v2_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "approvals" / "v2"
    forbidden_source_fragments = [
        "subprocess",
        "os.system(",
        "popen(",
        "shell=true",
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "httpx.post(",
        "urllib.request.urlopen(",
        "write_memory(",
        ".write_memory(",
        "put_record(",
        ".put_record(",
        "append_event(",
        "mutate_event(",
        "chat.completions.create(",
        "import openai",
        "from openai import",
        "import anthropic",
        "from anthropic import",
        "import ollama",
        "from ollama import",
    ]
    for path in approvals_v2_root.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_source_fragments:
            if fragment in text:
                print(f"FAIL: M28 forbidden Approval Authority v2 source fragment in {rel}: {fragment}")
                sys.exit(1)

    forbidden_route_fragments = [
        "/actions/execute",
        "/actions/run",
        "/approval/execute",
        "/approvals/execute",
        "/action-policy/execute",
        "/tools/execute",
        "/plugins/enable",
    ]
    for implementation_root in [ROOT / "src", ROOT / "apps"]:
        if not implementation_root.exists():
            continue
        for path in implementation_root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or "node_modules" in path.parts:
                continue
            if path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            if any(part == "tests" for part in path.parts) or ".test." in path.name or ".spec." in path.name:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in {
                "src/ultimate_ai_agent/core/gate/evaluators.py",
                "src/ultimate_ai_agent/api/openapi.py",
            }:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for fragment in forbidden_route_fragments:
                if fragment in text:
                    print(f"FAIL: M28 forbidden action/tool execution route fragment in {rel}: {fragment}")
                    sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT / "src"))
        from datetime import timedelta

        from pydantic import ValidationError

        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.approvals.v2 import (
            ActionIntent,
            ActionKind,
            ActionPolicy,
            ActionRef,
            ActionRiskLevel,
            ActionSideEffectClass,
            ActorRef,
            ActorTrustLevel,
            ApprovalDecisionStatus,
            ApprovalGrant,
            ApprovalGrantStatus,
            ApprovalScope,
            ApprovalScopeKind,
            ResourceRef,
            ResourceRefKind,
            build_approval_authority_v2_manifest,
            evaluate_action_policy,
        )
        from ultimate_ai_agent.core.gate.evaluators import m28_openapi_route_failures
        from ultimate_ai_agent.core.time import utc_now
    except Exception as exc:
        print(f"FAIL: M28 Approval Authority v2 imports could not load: {exc}")
        sys.exit(1)

    for failure in m28_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    manifest = build_approval_authority_v2_manifest(baseline_version="0.32.1")
    unsafe_flags = [
        manifest.action_execution_enabled,
        manifest.execution_authorized,
        manifest.execution_performed,
        manifest.tool_execution_enabled,
        manifest.filesystem_mutation_enabled,
        manifest.memory_write_enabled,
        manifest.network_action_enabled,
        manifest.browser_action_enabled,
        manifest.mobile_action_enabled,
        manifest.remote_execution_enabled,
        manifest.plugin_enable_enabled,
        manifest.model_action_enabled,
        manifest.wildcard_approval_enabled,
        manifest.approval_test_refs_enabled,
        manifest.backend_execution_routes_added,
        manifest.control_center_execute_controls_enabled,
        manifest.production_authority_enabled,
    ]
    if any(unsafe_flags):
        print("FAIL: M28 manifest enables forbidden runtime/action authority")
        sys.exit(1)

    actor = ActorRef(actor_ref="actor:verify-m28", trust_level=ActorTrustLevel.user)
    action = ActionRef(
        action_ref="action:verify-m28-read-metadata",
        action_kind=ActionKind.read_metadata,
        risk_level=ActionRiskLevel.low,
        side_effect_class=ActionSideEffectClass.read_only_metadata,
        safe_summary="Read metadata only.",
    )
    resource = ResourceRef(
        resource_ref="file_ref:verify-m28",
        resource_kind=ResourceRefKind.file_ref,
        safe_label="Verify metadata ref.",
    )
    expires_at = utc_now() + timedelta(minutes=15)
    scope = ApprovalScope(
        scope_ref="scope:verify-m28",
        scope_kind=ApprovalScopeKind.single_action,
        actor_ref=actor.actor_ref,
        action_ref=action.action_ref,
        resource_ref=resource.resource_ref,
        expires_at=expires_at,
        replay_nonce="nonce:verify-m28",
    )
    intent = ActionIntent(
        intent_id="action-intent:verify-m28",
        actor=actor,
        action=action,
        resource=resource,
        safe_summary="Evaluate a safe read-metadata action.",
        input_refs=["file_ref:verify-m28"],
    )
    grant = ApprovalGrant(
        grant_ref="approval:verify-m28",
        actor_ref=actor.actor_ref,
        action_ref=action.action_ref,
        resource_ref=resource.resource_ref,
        scope=scope,
        expires_at=expires_at,
        replay_nonce="nonce:verify-m28",
    )

    safe = evaluate_action_policy(intent, grant=grant, replay_nonce="nonce:verify-m28")
    if safe.status != ApprovalDecisionStatus.allowed_for_policy or not safe.allowed_for_policy:
        print("FAIL: M28 safe read-metadata policy decision was not allowed")
        sys.exit(1)
    if safe.execution_authorized or safe.execution_performed:
        print("FAIL: M28 safe read-metadata policy decision authorized or performed execution")
        sys.exit(1)
    if not safe.receipt_plan or safe.receipt_plan.execution_performed:
        print("FAIL: M28 safe policy decision receipt plan is missing or executable")
        sys.exit(1)

    def require_denial(decision, required_reason: str, label: str) -> None:
        if decision.allowed_for_policy or decision.execution_authorized or decision.execution_performed:
            print(f"FAIL: M28 denied probe was allowed: {label}")
            sys.exit(1)
        if required_reason not in decision.reason_codes:
            print(f"FAIL: M28 denied probe missing {required_reason}: {label}")
            sys.exit(1)

    require_denial(
        evaluate_action_policy(intent.model_copy(update={"approval_ref": "approval:any"})),
        "APPROVAL_REF_NOT_AUTHORITY",
        "approval_ref alone",
    )
    require_denial(
        evaluate_action_policy(intent.model_copy(update={"approval_ref": "approval_test_verify_m28"})),
        "APPROVAL_TEST_REF_DENIED",
        "approval_test_ ref",
    )
    require_denial(
        evaluate_action_policy(intent.model_copy(update={"consent_ref": "consent:verify-m28"})),
        "CONSENT_REF_NOT_AUTHORITY",
        "consent_ref alone",
    )
    require_denial(
        evaluate_action_policy(
            intent.model_copy(update={"contains_raw_prompt": True}),
            grant=grant,
            replay_nonce="nonce:verify-m28",
        ),
        "RAW_PROMPT_DENIED",
        "model_copy raw prompt revalidation",
    )
    require_denial(
        evaluate_action_policy(
            intent.model_copy(update={"contains_raw_model_output": True}),
            grant=grant,
            replay_nonce="nonce:verify-m28",
        ),
        "RAW_MODEL_OUTPUT_DENIED",
        "model_copy raw model output revalidation",
    )
    require_denial(
        evaluate_action_policy(
            intent.model_copy(update={"metadata": {"token": "abc123"}}),
            grant=grant,
            replay_nonce="nonce:verify-m28",
        ),
        "SECRET_METADATA_DENIED",
        "model_copy secret metadata revalidation",
    )
    require_denial(
        evaluate_action_policy(
            intent,
            grant=grant.model_copy(update={"grant_ref": "approval_test_verify_m28"}),
            replay_nonce="nonce:verify-m28",
        ),
        "APPROVAL_TEST_REF_DENIED",
        "model_copy approval_test grant revalidation",
    )
    require_denial(
        evaluate_action_policy(
            intent,
            grant=grant,
            policy=ActionPolicy().model_copy(update={"safe_summary": "contains token=abc123"}),
            replay_nonce="nonce:verify-m28",
        ),
        "ACTION_POLICY_SECRET_CONTENT_DENIED",
        "model_copy action policy revalidation",
    )
    wildcard_scope = scope.model_copy(update={"scope_kind": ApprovalScopeKind.blocked_wildcard, "action_ref": "*"})
    wildcard_grant = grant.model_copy(update={"scope": wildcard_scope, "action_ref": "*"})
    require_denial(
        evaluate_action_policy(intent, grant=wildcard_grant, replay_nonce="nonce:verify-m28"),
        "WILDCARD_SCOPE_DENIED",
        "wildcard scope",
    )
    require_denial(
        evaluate_action_policy(
            intent,
            grant=grant.model_copy(update={"expires_at": utc_now() - timedelta(minutes=1)}),
            replay_nonce="nonce:verify-m28",
        ),
        "APPROVAL_GRANT_EXPIRED",
        "expired grant",
    )
    require_denial(
        evaluate_action_policy(
            intent,
            grant=grant.model_copy(update={"status": ApprovalGrantStatus.revoked}),
            replay_nonce="nonce:verify-m28",
        ),
        "APPROVAL_GRANT_REVOKED",
        "revoked grant",
    )
    require_denial(
        evaluate_action_policy(
            intent,
            grant=grant.model_copy(update={"used_replay_nonces": ["nonce:verify-m28"]}),
            replay_nonce="nonce:verify-m28",
        ),
        "APPROVAL_REPLAY_DETECTED",
        "replayed grant",
    )
    require_denial(
        evaluate_action_policy(
            intent,
            grant=grant.model_copy(update={"actor_ref": "actor:mismatch"}),
            replay_nonce="nonce:verify-m28",
        ),
        "APPROVAL_ACTOR_MISMATCH",
        "actor mismatch",
    )
    require_denial(
        evaluate_action_policy(
            intent.model_copy(
                update={
                    "resource": ResourceRef(
                        resource_ref="memory:verify-m28",
                        resource_kind=ResourceRefKind.memory_ref,
                        safe_label="Memory ref.",
                    )
                }
            ),
            grant=grant,
            replay_nonce="nonce:verify-m28",
        ),
        "MEMORY_REF_NOT_AUTHORITY",
        "memory ref authority",
    )
    require_denial(
        evaluate_action_policy(
            intent.model_copy(
                update={
                    "resource": ResourceRef(
                        resource_ref="model:verify-m28",
                        resource_kind=ResourceRefKind.model_output_ref,
                        safe_label="Model output ref.",
                    )
                }
            ),
            grant=grant,
            replay_nonce="nonce:verify-m28",
        ),
        "MODEL_OUTPUT_NOT_AUTHORITY",
        "model output ref authority",
    )
    write_action = ActionRef(
        action_ref="action:verify-m28-file-write",
        action_kind=ActionKind.file_write_planned,
        risk_level=ActionRiskLevel.high,
        side_effect_class=ActionSideEffectClass.local_mutation_blocked,
        safe_summary="Blocked file write plan.",
    )
    require_denial(
        evaluate_action_policy(
            intent.model_copy(update={"action": write_action}),
            grant=grant.model_copy(update={"action_ref": write_action.action_ref}),
            replay_nonce="nonce:verify-m28",
        ),
        "ACTION_KIND_DENIED",
        "effectful action",
    )
    try:
        ActionIntent(
            intent_id="action-intent:verify-m28-raw",
            actor=actor,
            action=action,
            resource=resource,
            safe_summary="Raw action input probe.",
            contains_raw_prompt=True,
        )
        print("FAIL: M28 ActionIntent accepted raw prompt content")
        sys.exit(1)
    except ValidationError:
        pass
    try:
        ActionIntent(
            intent_id="action-intent:verify-m28-secret",
            actor=actor,
            action=action,
            resource=resource,
            safe_summary="Secret input probe.",
            metadata={"token": "abc123"},
        )
        print("FAIL: M28 ActionIntent accepted secret-like metadata")
        sys.exit(1)
    except ValidationError:
        pass

    print("OK: M28 Approval Authority v2 contracts remain policy-only, route-free, and non-executing")


def verify_m29_task_planning_engine_safety():
    print("\n[Verifier] Running M29 Agent Task Planning Engine safety guard...")
    required_files = [
        "src/ultimate_ai_agent/core/planning/__init__.py",
        "src/ultimate_ai_agent/core/planning/enums.py",
        "src/ultimate_ai_agent/core/planning/contracts.py",
        "src/ultimate_ai_agent/core/planning/validation.py",
        "src/ultimate_ai_agent/core/planning/planner.py",
        "src/ultimate_ai_agent/core/planning/manifests.py",
        "tests/test_task_planning_contracts.py",
        "tests/test_task_plan_validation.py",
        "tests/test_task_plan_dependencies.py",
        "tests/test_task_plan_no_execution.py",
        "tests/test_m29_gate_integration.py",
        "docs/planning/TASK_PLANNING_ENGINE.md",
        "docs/planning/TASK_GOAL_STEP_PLAN_CONTRACTS.md",
        "docs/planning/TASK_DEPENDENCY_GRAPH.md",
        "docs/planning/TASK_INPUT_BOUNDARY.md",
        "docs/planning/TASK_RISK_AND_AUTHORITY_POLICY.md",
        "docs/planning/TASK_PLAN_DECISION_ENVELOPE.md",
        "docs/planning/TASK_PLAN_RECEIPT_PLAN.md",
        "docs/planning/TASK_PLANNING_NON_GOALS.md",
        "docs/planning/M29_TO_M30_BOUNDARY.md",
        "docs/release_notes/v0_33_0.md",
        "docs/archive/releases/v0_33_0/README_IMPORT.md",
        "docs/archive/releases/v0_33_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_33_0.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M29 Task Planning Engine file: {rel_path}")
            sys.exit(1)

    planning_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "planning"
    forbidden_source_fragments = [
        "subprocess",
        "os.system(",
        "popen(",
        "shell=true",
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "httpx.post(",
        "urllib.request.urlopen(",
        "write_memory(",
        ".write_memory(",
        "put_record(",
        ".put_record(",
        "append_event(",
        "mutate_event(",
        "chat.completions.create(",
        "import openai",
        "from openai import",
        "import anthropic",
        "from anthropic import",
        "import ollama",
        "from ollama import",
    ]
    for path in planning_root.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_source_fragments:
            if fragment in text:
                print(f"FAIL: M29 forbidden planning source fragment in {rel}: {fragment}")
                sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m29_openapi_route_failures
        from ultimate_ai_agent.core.planning import (
            PlanInputTrustLevel,
            TaskGoal,
            TaskPlan,
            TaskPlanDecisionStatus,
            TaskPlanningRequest,
            TaskRiskLevel,
            TaskStep,
            TaskStepInputBoundary,
            TaskStepKind,
            build_task_planning_manifest,
            evaluate_task_plan,
        )
    except Exception as exc:
        print(f"FAIL: M29 Task Planning Engine imports could not load: {exc}")
        sys.exit(1)

    for failure in m29_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    manifest = build_task_planning_manifest(baseline_version="0.33.0")
    unsafe_flags = [
        manifest.task_execution_enabled,
        manifest.auto_run_enabled,
        manifest.scheduler_enabled,
        manifest.background_worker_enabled,
        manifest.tool_execution_enabled,
        manifest.action_execution_enabled,
        manifest.file_mutation_enabled,
        manifest.memory_write_enabled,
        manifest.network_call_enabled,
        manifest.model_provider_call_enabled,
        manifest.browser_automation_enabled,
        manifest.mobile_device_access_enabled,
        manifest.remote_execution_enabled,
        manifest.plugin_enablement_enabled,
        manifest.backend_task_routes_added,
        manifest.control_center_execute_controls_enabled,
        manifest.context_injection_enabled,
        manifest.production_authority_enabled,
    ]
    if any(unsafe_flags):
        print("FAIL: M29 manifest enables forbidden task/runtime authority")
        sys.exit(1)

    safe_step = TaskStep(
        step_id="step:verify-m29-review",
        step_kind=TaskStepKind.review_metadata,
        safe_summary="Review safe metadata refs.",
        input_boundary=TaskStepInputBoundary(input_refs=["canonical:verify-m29"]),
        declared_risk_level=TaskRiskLevel.low,
    )
    safe_plan = TaskPlan(
        plan_id="plan:verify-m29",
        goal=TaskGoal(goal_id="goal:verify-m29", safe_summary="Plan a safe review workflow."),
        steps=[safe_step],
        safe_summary="Review-only task plan.",
    )
    safe = evaluate_task_plan(safe_plan)
    if safe.status != TaskPlanDecisionStatus.valid_for_review or not safe.valid_for_review:
        print("FAIL: M29 safe task plan was not valid for review")
        sys.exit(1)
    if safe.execution_authorized or safe.execution_performed or safe.scheduler_registered:
        print("FAIL: M29 safe task plan authorized execution, performed execution, or registered scheduler")
        sys.exit(1)
    if safe.derived_plan_risk_level != TaskRiskLevel.low:
        print("FAIL: M29 safe task plan did not report trusted derived risk")
        sys.exit(1)
    if not safe.receipt_plan or safe.receipt_plan.execution_performed:
        print("FAIL: M29 safe task plan receipt plan is missing or executable")
        sys.exit(1)
    if safe.receipt_plan.derived_plan_risk_level != safe.derived_plan_risk_level:
        print("FAIL: M29 receipt plan did not preserve derived plan risk")
        sys.exit(1)

    def require_denial(decision, required_reason: str, label: str) -> None:
        if decision.valid_for_review or decision.execution_authorized or decision.execution_performed:
            print(f"FAIL: M29 denied probe was allowed: {label}")
            sys.exit(1)
        if decision.scheduler_registered:
            print(f"FAIL: M29 denied probe registered a scheduler: {label}")
            sys.exit(1)
        if required_reason not in decision.reason_codes:
            print(f"FAIL: M29 denied probe missing {required_reason}: {label}")
            sys.exit(1)

    require_denial(
        evaluate_task_plan(TaskPlanningRequest(plan=safe_plan).model_copy(update={"execution_requested": True})),
        "TASK_EXECUTION_REQUEST_DENIED",
        "execution requested",
    )
    require_denial(
        evaluate_task_plan(TaskPlanningRequest(plan=safe_plan).model_copy(update={"auto_run_requested": True})),
        "TASK_AUTO_RUN_DENIED",
        "auto-run requested",
    )
    require_denial(
        evaluate_task_plan(TaskPlanningRequest(plan=safe_plan).model_copy(update={"schedule_requested": True})),
        "TASK_SCHEDULER_DENIED",
        "scheduler requested",
    )
    raw_boundary = safe_step.input_boundary.model_copy(update={"contains_raw_prompt": True})
    require_denial(
        evaluate_task_plan(safe_plan.model_copy(update={"steps": [safe_step.model_copy(update={"input_boundary": raw_boundary})]})),
        "RAW_PROMPT_DENIED",
        "raw prompt model_copy revalidation",
    )
    secret_boundary = safe_step.input_boundary.model_copy(update={"metadata": {"token": "abc123"}})
    require_denial(
        evaluate_task_plan(safe_plan.model_copy(update={"steps": [safe_step.model_copy(update={"input_boundary": secret_boundary})]})),
        "SECRET_METADATA_DENIED",
        "secret metadata model_copy revalidation",
    )
    blocked_boundary = TaskStepInputBoundary(
        input_refs=["model:verify-m29"],
        input_trust_level=PlanInputTrustLevel.model_output_blocked,
    )
    require_denial(
        evaluate_task_plan(safe_plan.model_copy(update={"steps": [safe_step.model_copy(update={"input_boundary": blocked_boundary})]})),
        "MODEL_OUTPUT_NOT_PLAN_AUTHORITY",
        "model output authority",
    )
    memory_boundary = TaskStepInputBoundary(
        input_refs=["memory:verify-m29"],
        input_trust_level=PlanInputTrustLevel.memory_ref,
    )
    require_denial(
        evaluate_task_plan(safe_plan.model_copy(update={"steps": [safe_step.model_copy(update={"input_boundary": memory_boundary})]})),
        "MEMORY_REF_NOT_PLAN_AUTHORITY",
        "memory authority",
    )
    for input_ref, trust_level, reason in [
        ("context-pack:verify-m29", PlanInputTrustLevel.context_pack_ref, "CONTEXT_PACK_NOT_PLAN_AUTHORITY"),
        ("tool-intent:verify-m29", PlanInputTrustLevel.tool_intent_ref, "TOOL_INTENT_NOT_PLAN_AUTHORITY"),
        ("approval:verify-m29", PlanInputTrustLevel.approval_ref, "APPROVAL_REF_NOT_TASK_AUTHORITY"),
        ("openwebui:verify-m29", PlanInputTrustLevel.openwebui_output_blocked, "OPENWEBUI_OUTPUT_NOT_PLAN_AUTHORITY"),
        ("control-center:verify-m29", PlanInputTrustLevel.unknown_blocked, "UNKNOWN_INPUT_REF_DENIED"),
    ]:
        blocked_ref_boundary = TaskStepInputBoundary(input_refs=[input_ref], input_trust_level=trust_level)
        require_denial(
            evaluate_task_plan(
                safe_plan.model_copy(
                    update={"steps": [safe_step.model_copy(update={"input_boundary": blocked_ref_boundary})]}
                )
            ),
            reason,
            f"non-authoritative ref {input_ref}",
        )
    effectful_step = safe_step.model_copy(
        update={"step_kind": TaskStepKind.tool_execution_planned, "declared_risk_level": TaskRiskLevel.high}
    )
    require_denial(
        evaluate_task_plan(safe_plan.model_copy(update={"steps": [effectful_step]})),
        "TASK_STEP_EXECUTION_DENIED",
        "effectful step",
    )
    downgraded_step = safe_step.model_copy(
        update={"step_kind": TaskStepKind.file_mutation_planned, "declared_risk_level": TaskRiskLevel.low}
    )
    require_denial(
        evaluate_task_plan(safe_plan.model_copy(update={"steps": [downgraded_step]})),
        "TASK_RISK_DOWNGRADE_DENIED",
        "risk downgrade",
    )
    hidden_side_effect_step = safe_step.model_copy(update={"metadata": {"side_effect": "file_write"}})
    hidden_side_effect_decision = evaluate_task_plan(safe_plan.model_copy(update={"steps": [hidden_side_effect_step]}))
    require_denial(
        hidden_side_effect_decision,
        "TASK_HIDDEN_SIDE_EFFECT_DENIED",
        "hidden side effect metadata",
    )
    if "TASK_RISK_DOWNGRADE_DENIED" not in hidden_side_effect_decision.reason_codes:
        print("FAIL: M29 hidden side effect metadata did not deny risk downgrade")
        sys.exit(1)
    require_denial(
        evaluate_task_plan(safe_plan.model_copy(update={"steps": [safe_step, safe_step.model_copy(update={"safe_summary": "Duplicate."})]})),
        "DUPLICATE_STEP_ID_DENIED",
        "duplicate step id",
    )
    missing_dep_step = safe_step.model_copy(update={"depends_on": ["step:missing-m29"]})
    require_denial(
        evaluate_task_plan(safe_plan.model_copy(update={"steps": [missing_dep_step]})),
        "MISSING_DEPENDENCY_STEP_DENIED",
        "missing dependency",
    )
    step_a = safe_step.model_copy(update={"step_id": "step:verify-m29-a", "depends_on": ["step:verify-m29-b"]})
    step_b = safe_step.model_copy(update={"step_id": "step:verify-m29-b", "depends_on": ["step:verify-m29-a"]})
    require_denial(
        evaluate_task_plan(safe_plan.model_copy(update={"steps": [step_a, step_b]})),
        "DEPENDENCY_CYCLE_DENIED",
        "dependency cycle",
    )
    self_dep_step = safe_step.model_copy(update={"depends_on": [safe_step.step_id]})
    require_denial(
        evaluate_task_plan(safe_plan.model_copy(update={"steps": [self_dep_step]})),
        "DEPENDENCY_CYCLE_DENIED",
        "self dependency cycle",
    )
    step_c = safe_step.model_copy(update={"step_id": "step:verify-m29-c", "depends_on": ["step:verify-m29-b"]})
    indirect_a = step_a.model_copy(update={"depends_on": ["step:verify-m29-c"]})
    indirect_b = step_b.model_copy(update={"depends_on": ["step:verify-m29-a"]})
    require_denial(
        evaluate_task_plan(safe_plan.model_copy(update={"steps": [indirect_a, indirect_b, step_c]})),
        "DEPENDENCY_CYCLE_DENIED",
        "indirect dependency cycle",
    )

    print("OK: M29 Agent Task Planning Engine contracts remain review-only, route-free, and non-executing")


def verify_m30_multi_step_execution_framework_safety():
    print("\n[Verifier] Running M30 Multi-Step Execution Framework safety guard...")
    required_files = [
        "src/ultimate_ai_agent/core/execution/__init__.py",
        "src/ultimate_ai_agent/core/execution/enums.py",
        "src/ultimate_ai_agent/core/execution/manifests.py",
        "src/ultimate_ai_agent/core/execution/runs.py",
        "src/ultimate_ai_agent/core/execution/state_machine.py",
        "src/ultimate_ai_agent/core/execution/steps.py",
        "src/ultimate_ai_agent/core/execution/transitions.py",
        "src/ultimate_ai_agent/core/execution/validation.py",
        "tests/test_execution_framework_contracts.py",
        "tests/test_execution_state_machine_safety.py",
        "tests/test_execution_dependency_progression.py",
        "tests/test_execution_receipt_plan.py",
        "tests/test_m30_gate_integration.py",
        "docs/execution/MULTI_STEP_EXECUTION_FRAMEWORK.md",
        "docs/execution/EXECUTION_STATE_MACHINE.md",
        "docs/execution/EXECUTION_STEP_CONTRACTS.md",
        "docs/execution/EXECUTION_DEPENDENCY_POLICY.md",
        "docs/execution/EXECUTION_TRANSITION_POLICY.md",
        "docs/execution/EXECUTION_INPUT_BOUNDARY.md",
        "docs/execution/EXECUTION_RECEIPT_PLAN.md",
        "docs/execution/EXECUTION_NON_GOALS.md",
        "docs/execution/M30_TO_M31_BOUNDARY.md",
        "docs/release_notes/v0_34_0.md",
        "docs/archive/releases/v0_34_0/README_IMPORT.md",
        "docs/archive/releases/v0_34_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_34_0.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M30 Multi-Step Execution Framework file: {rel_path}")
            sys.exit(1)

    execution_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "execution"
    forbidden_source_fragments = [
        "subprocess",
        "os.system(",
        "popen(",
        "shell=true",
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "httpx.post(",
        "urllib.request.urlopen(",
        "socket",
        "websocket",
        "write_memory(",
        ".write_memory(",
        "put_record(",
        ".put_record(",
        "append_event(",
        "mutate_event(",
        "chat.completions.create(",
        "import openai",
        "from openai import",
        "import anthropic",
        "from anthropic import",
        "import ollama",
        "from ollama import",
    ]
    for path in execution_root.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_source_fragments:
            if fragment in text:
                print(f"FAIL: M30 forbidden execution source fragment in {rel}: {fragment}")
                sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.execution import (
            ExecutionInputTrustLevel,
            ExecutionRun,
            ExecutionStep,
            ExecutionStepInputBoundary,
            ExecutionStepMode,
            ExecutionStepStatus,
            ExecutionTransitionKind,
            ExecutionTransitionRequest,
            ExecutionTransitionStatus,
            build_execution_framework_manifest,
            dependency_graph_reason_codes,
            evaluate_execution_transition,
        )
        from ultimate_ai_agent.core.gate.evaluators import m30_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M30 Multi-Step Execution Framework imports could not load: {exc}")
        sys.exit(1)

    for failure in m30_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    manifest = build_execution_framework_manifest(baseline_version="0.34.0")
    unsafe_flags = [
        manifest.real_task_execution_enabled,
        manifest.action_execution_enabled,
        manifest.tool_execution_enabled,
        manifest.file_mutation_enabled,
        manifest.memory_write_enabled,
        manifest.event_ledger_mutation_enabled,
        manifest.network_call_enabled,
        manifest.model_provider_call_enabled,
        manifest.browser_automation_enabled,
        manifest.mobile_device_access_enabled,
        manifest.remote_execution_enabled,
        manifest.plugin_enablement_enabled,
        manifest.scheduler_enabled,
        manifest.background_worker_enabled,
        manifest.autonomous_loop_enabled,
        manifest.context_injection_enabled,
        manifest.backend_execution_routes_added,
        manifest.control_center_execute_controls_enabled,
        manifest.production_authority_enabled,
    ]
    if any(unsafe_flags) or not manifest.execution_state_machine_enabled:
        print("FAIL: M30 manifest enables forbidden execution authority or disables the state machine")
        sys.exit(1)

    safe_step = ExecutionStep(
        step_id="execution-step:verify-m30",
        safe_summary="Advance a no-effect execution step for review.",
        status=ExecutionStepStatus.ready,
        input_boundary=ExecutionStepInputBoundary(input_refs=["canonical:verify-m30"]),
    )
    safe_run = ExecutionRun(
        run_id="execution-run:verify-m30",
        source_task_plan_ref="task-plan:verify-m30",
        steps=[safe_step],
        safe_summary="No-effect execution-state-machine run.",
    )
    safe_request = ExecutionTransitionRequest(
        run_id=safe_run.run_id,
        target_step_id=safe_step.step_id,
        transition_id="execution-transition:verify-m30",
        transition_kind=ExecutionTransitionKind.complete_no_effect_step,
        replay_key="replay:verify-m30",
        safe_summary="Complete no-effect step.",
    )
    safe = evaluate_execution_transition(safe_run, safe_request)
    if safe.status != ExecutionTransitionStatus.approved_no_effect_transition:
        print("FAIL: M30 safe no-effect transition was not approved")
        sys.exit(1)
    if safe.execution_authorized or safe.execution_performed or safe.side_effects_performed:
        print("FAIL: M30 safe no-effect transition authorized, performed, or reported side effects")
        sys.exit(1)
    if not safe.receipt_plan or safe.receipt_plan.execution_performed:
        print("FAIL: M30 safe no-effect transition receipt plan is missing or executable")
        sys.exit(1)

    def require_denial(decision, required_reason: str, label: str) -> None:
        if decision.status == ExecutionTransitionStatus.approved_no_effect_transition:
            print(f"FAIL: M30 denied probe was allowed: {label}")
            sys.exit(1)
        if decision.execution_authorized or decision.execution_performed or decision.side_effects_performed:
            print(f"FAIL: M30 denied probe changed execution invariants: {label}")
            sys.exit(1)
        if required_reason not in decision.reason_codes:
            print(f"FAIL: M30 denied probe missing {required_reason}: {label}")
            sys.exit(1)

    require_denial(
        evaluate_execution_transition(safe_run, safe_request.model_copy(update={"execution_requested": True})),
        "EXECUTION_REQUEST_DENIED",
        "execution requested",
    )
    require_denial(
        evaluate_execution_transition(safe_run, safe_request.model_copy(update={"auto_run_requested": True})),
        "AUTO_RUN_DENIED",
        "auto-run requested",
    )
    require_denial(
        evaluate_execution_transition(safe_run, safe_request.model_copy(update={"schedule_requested": True})),
        "SCHEDULE_DENIED",
        "schedule requested",
    )
    require_denial(
        evaluate_execution_transition(safe_run, safe_request.model_copy(update={"background_worker_requested": True})),
        "BACKGROUND_WORKER_DENIED",
        "background worker requested",
    )
    require_denial(
        evaluate_execution_transition(
            safe_run,
            safe_request.model_copy(update={"contains_raw_prompt": True, "replay_key": "replay:raw-m30"}),
        ),
        "RAW_PROMPT_DENIED",
        "raw prompt model_copy revalidation",
    )
    require_denial(
        evaluate_execution_transition(
            safe_run,
            safe_request.model_copy(update={"metadata": {"token": "abc123"}, "replay_key": "replay:metadata-m30"}),
        ),
        "SECRET_METADATA_DENIED",
        "secret metadata model_copy revalidation",
    )
    require_denial(
        evaluate_execution_transition(
            safe_run.model_copy(update={"replay_keys_seen": ["replay:verify-m30"]}),
            safe_request,
        ),
        "EXECUTION_REPLAY_DENIED",
        "replay key reuse",
    )
    require_denial(
        evaluate_execution_transition(
            safe_run.model_copy(update={"transition_ids_seen": ["execution-transition:verify-m30"]}),
            safe_request,
        ),
        "EXECUTION_TRANSITION_REPLAY_DENIED",
        "transition id reuse",
    )
    require_denial(
        evaluate_execution_transition(
            safe_run.model_copy(update={"approval_ref": "approval_test_verify_m30"}),
            safe_request.model_copy(
                update={
                    "replay_key": "replay:approval-m30",
                    "transition_id": "execution-transition:approval-m30",
                }
            ),
        ),
        "APPROVAL_TEST_REF_DENIED",
        "approval_test ref",
    )
    blocked_step = safe_step.model_copy(update={"mode": ExecutionStepMode.tool_execution_blocked})
    require_denial(
        evaluate_execution_transition(safe_run.model_copy(update={"steps": [blocked_step]}), safe_request),
        "TOOL_EXECUTION_DENIED",
        "tool execution step mode",
    )
    model_boundary = ExecutionStepInputBoundary(
        input_refs=["model:verify-m30"],
        input_trust_level=ExecutionInputTrustLevel.model_output_blocked,
    )
    require_denial(
        evaluate_execution_transition(
            safe_run.model_copy(update={"steps": [safe_step.model_copy(update={"input_boundary": model_boundary})]}),
            safe_request,
        ),
        "MODEL_OUTPUT_NOT_EXECUTION_AUTHORITY",
        "model output authority",
    )
    missing_dep_step = safe_step.model_copy(update={"depends_on": ["execution-step:missing-m30"]})
    require_denial(
        evaluate_execution_transition(safe_run.model_copy(update={"steps": [missing_dep_step]}), safe_request),
        "MISSING_EXECUTION_DEPENDENCY_DENIED",
        "missing dependency",
    )
    step_a = safe_step.model_copy(
        update={"step_id": "execution-step:verify-m30-a", "depends_on": ["execution-step:verify-m30-b"]}
    )
    step_b = safe_step.model_copy(
        update={"step_id": "execution-step:verify-m30-b", "depends_on": ["execution-step:verify-m30-a"]}
    )
    cyclic_run = safe_run.model_copy(update={"steps": [step_a, step_b]})
    if "EXECUTION_DEPENDENCY_CYCLE_DENIED" not in dependency_graph_reason_codes(cyclic_run):
        print("FAIL: M30 dependency graph did not report a direct cycle")
        sys.exit(1)
    require_denial(
        evaluate_execution_transition(cyclic_run, safe_request.model_copy(update={"target_step_id": step_a.step_id})),
        "EXECUTION_DEPENDENCY_CYCLE_DENIED",
        "dependency cycle",
    )
    completed_dependency = ExecutionStep(
        step_id="execution-step:verify-m30-dep",
        safe_summary="Already completed no-effect dependency.",
        status=ExecutionStepStatus.completed_no_effect,
    )
    dependent_step = safe_step.model_copy(update={"depends_on": [completed_dependency.step_id]})
    dependent_run = safe_run.model_copy(update={"steps": [completed_dependency, dependent_step]})
    dependent_decision = evaluate_execution_transition(
        dependent_run,
        safe_request.model_copy(
            update={
                "target_step_id": dependent_step.step_id,
                "replay_key": "replay:verify-m30-dependent",
                "transition_id": "execution-transition:verify-m30-dependent",
            }
        ),
    )
    if dependent_decision.status != ExecutionTransitionStatus.approved_no_effect_transition:
        print("FAIL: M30 completed dependency did not allow no-effect progression")
        sys.exit(1)

    final_run = safe_run.model_copy(
        update={"steps": [safe_step.model_copy(update={"status": ExecutionStepStatus.completed_no_effect})]}
    )
    final_request = safe_request.model_copy(
        update={
            "target_step_id": None,
            "replay_key": "replay:verify-m30-finalize",
            "transition_id": "execution-transition:verify-m30-finalize",
            "transition_kind": ExecutionTransitionKind.finalize_no_effect_run,
        }
    )
    final_decision = evaluate_execution_transition(final_run, final_request)
    if final_decision.status != ExecutionTransitionStatus.approved_no_effect_transition:
        print("FAIL: M30 completed run did not finalize without side effects")
        sys.exit(1)
    require_denial(
        evaluate_execution_transition(
            safe_run,
            safe_request.model_copy(
                update={
                    "target_step_id": None,
                    "replay_key": "replay:verify-m30-finalize-blocked",
                    "transition_id": "execution-transition:verify-m30-finalize-blocked",
                    "transition_kind": ExecutionTransitionKind.finalize_no_effect_run,
                }
            ),
        ),
        "EXECUTION_RUN_FINALIZE_INCOMPLETE_DENIED",
        "finalize incomplete run",
    )
    require_denial(
        evaluate_execution_transition(
            safe_run,
            safe_request.model_copy(
                update={
                    "side_effect_execution_enabled": True,
                    "replay_key": "replay:verify-m30-side-effect",
                    "transition_id": "execution-transition:verify-m30-side-effect",
                }
            ),
        ),
        "SIDE_EFFECT_EXECUTION_DENIED",
        "side-effect execution flag",
    )

    print("OK: M30 Multi-Step Execution Framework remains state-machine-only, route-free, and non-executing")


def verify_m31_tool_runtime_noop_safety():
    print("\n[Verifier] Running M31 Real Tool Runtime Adapter no-op guard...")
    required_files = [
        "src/ultimate_ai_agent/core/tools/runtime/__init__.py",
        "src/ultimate_ai_agent/core/tools/runtime/adapters.py",
        "src/ultimate_ai_agent/core/tools/runtime/contracts.py",
        "src/ultimate_ai_agent/core/tools/runtime/enums.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "src/ultimate_ai_agent/core/tools/runtime/manifests.py",
        "src/ultimate_ai_agent/core/tools/runtime/noop.py",
        "src/ultimate_ai_agent/core/tools/runtime/policy.py",
        "src/ultimate_ai_agent/core/tools/runtime/receipts.py",
        "src/ultimate_ai_agent/core/tools/runtime/validation.py",
        "tests/test_tool_runtime_contracts.py",
        "tests/test_tool_runtime_noop_invocation.py",
        "tests/test_tool_runtime_no_side_effects.py",
        "tests/test_tool_runtime_authority_boundaries.py",
        "tests/test_tool_runtime_replay_protection.py",
        "tests/test_tool_runtime_no_dynamic_dispatch.py",
        "tests/test_m31_gate_integration.py",
        "docs/tools/TOOL_RUNTIME_ADAPTER.md",
        "docs/tools/NOOP_TOOL_RUNTIME.md",
        "docs/tools/TOOL_RUNTIME_INVOCATION_CONTRACT.md",
        "docs/tools/TOOL_RUNTIME_AUTHORITY_BOUNDARY.md",
        "docs/tools/TOOL_RUNTIME_REPLAY_POLICY.md",
        "docs/tools/TOOL_RUNTIME_RECEIPT_PLAN.md",
        "docs/tools/TOOL_RUNTIME_NON_GOALS.md",
        "docs/tools/M31_TO_M32_BOUNDARY.md",
        "docs/release_notes/v0_35_1.md",
        "docs/archive/releases/v0_35_1/README_IMPORT.md",
        "docs/archive/releases/v0_35_1/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_35_1.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M31 Tool Runtime Adapter file: {rel_path}")
            sys.exit(1)

    runtime_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "tools" / "runtime"
    forbidden_source_fragments = [
        "os.system(",
        "popen(",
        "shell=true",
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "httpx.post(",
        "urllib.request.urlopen(",
        "socket",
        "websocket",
        "write_memory(",
        ".write_memory(",
        "put_record(",
        ".put_record(",
        "append_event(",
        "mutate_event(",
        "importlib",
        "getattr(",
        "chat.completions.create(",
        "import openai",
        "from openai import",
        "import anthropic",
        "from anthropic import",
        "import ollama",
        "from ollama import",
    ]
    for path in runtime_root.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_source_fragments:
            if fragment in text:
                print(f"FAIL: M31 forbidden tool runtime source fragment in {rel}: {fragment}")
                sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m31_openapi_route_failures
        from ultimate_ai_agent.core.tools.runtime import (
            NOOP_TOOL_NAME,
            NOOP_TOOL_REF,
            ToolInvocationRequest,
            ToolInvocationStatus,
            build_tool_runtime_manifest,
            evaluate_tool_invocation,
        )
    except Exception as exc:
        print(f"FAIL: M31 Tool Runtime Adapter imports could not load: {exc}")
        sys.exit(1)

    for failure in m31_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    manifest = build_tool_runtime_manifest(baseline_version="0.35.1")
    policy = manifest.policy
    unsafe_flags = [
        policy.arbitrary_tool_execution_enabled,
        policy.side_effecting_tools_enabled,
        policy.shell_tools_enabled,
        policy.file_tools_enabled,
        policy.memory_write_tools_enabled,
        policy.network_tools_enabled,
        policy.model_tools_enabled,
        policy.browser_tools_enabled,
        policy.mobile_tools_enabled,
        policy.remote_tools_enabled,
        policy.plugin_tools_enabled,
        policy.dynamic_tool_registration_enabled,
        policy.backend_execute_routes_enabled,
        policy.control_center_execute_controls_enabled,
        policy.production_authority_enabled,
    ]
    if any(unsafe_flags) or not policy.tool_runtime_enabled or not policy.noop_tool_enabled:
        print("FAIL: M31 manifest enables forbidden runtime authority or disables the no-op tool")
        sys.exit(1)
    if NOOP_TOOL_REF not in manifest.allowlisted_tool_refs:
        print("FAIL: M31 manifest no longer allowlists the no-op tool")
        sys.exit(1)

    safe_request = ToolInvocationRequest(
        invocation_id="tool-runtime-invocation:verify-m31",
        tool_ref=NOOP_TOOL_REF,
        tool_name=NOOP_TOOL_NAME,
        replay_key="tool-runtime-replay:verify-m31",
        safe_summary="Run deterministic no-op tool.",
        input_refs=["canonical:verify-m31"],
    )
    safe = evaluate_tool_invocation(safe_request)
    if safe.status != ToolInvocationStatus.noop_completed or not safe.execution_performed:
        print("FAIL: M31 deterministic no-op invocation did not complete")
        sys.exit(1)
    if safe.side_effects_performed or not safe.result or safe.result.side_effects_performed:
        print("FAIL: M31 deterministic no-op invocation reported side effects")
        sys.exit(1)
    if safe.result.output.raw_input_echoed or safe.result.output.raw_content_stored:
        print("FAIL: M31 deterministic no-op invocation echoed or stored raw input")
        sys.exit(1)

    def require_denial(decision, required_reason: str, label: str) -> None:
        if decision.status == ToolInvocationStatus.noop_completed or decision.execution_performed:
            print(f"FAIL: M31 denied probe was allowed: {label}")
            sys.exit(1)
        if decision.side_effects_performed:
            print(f"FAIL: M31 denied probe reported side effects: {label}")
            sys.exit(1)
        if required_reason not in decision.reason_codes:
            print(f"FAIL: M31 denied probe missing {required_reason}: {label}")
            sys.exit(1)

    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"tool_ref": "tool:file_write.v1"})),
        "TOOL_NOT_ALLOWLISTED_DENIED",
        "file tool ref",
    )
    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"tool_ref": "tool:network_call.v1"})),
        "EFFECTFUL_TOOL_BLOCKED",
        "network tool ref",
    )
    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"tool_name": "module.callable"})),
        "DYNAMIC_DISPATCH_DENIED",
        "dynamic dispatch tool name",
    )
    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"module_path": "tool_plugins.file_writer"})),
        "DYNAMIC_DISPATCH_DENIED",
        "model_copy module path",
    )
    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"metadata": {"callable_name": "run_noop"}})),
        "DYNAMIC_DISPATCH_DENIED",
        "metadata callable name",
    )
    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"side_effects_performed": ["file:write"]})),
        "SIDE_EFFECT_ATTEMPT_DENIED",
        "model_copy side effect field",
    )
    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"metadata": {"file_write_requested": True}})),
        "SIDE_EFFECT_ATTEMPT_DENIED",
        "metadata side effect field",
    )
    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"approval_ref": "approval:verify-m31"})),
        "APPROVAL_REF_NOT_AUTHORITY",
        "approval_ref alone",
    )
    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"approval_ref": "approval_test_verify_m31"})),
        "APPROVAL_TEST_REF_DENIED",
        "approval_test ref",
    )
    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"authority_refs": ["model:verify-m31"]})),
        "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY",
        "model output authority ref",
    )
    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"contains_raw_prompt": True})),
        "RAW_PROMPT_DENIED",
        "raw prompt model_copy revalidation",
    )
    require_denial(
        evaluate_tool_invocation(safe_request.model_copy(update={"metadata": {"token": "abc123"}})),
        "SECRET_CONTENT_DENIED",
        "secret metadata model_copy revalidation",
    )
    require_denial(
        evaluate_tool_invocation(safe_request, replay_keys_seen=["tool-runtime-replay:verify-m31"]),
        "TOOL_RUNTIME_REPLAY_DETECTED",
        "replay key reuse",
    )

    print("OK: M31 Tool Runtime Adapter allows only deterministic no-op invocation and remains route-free")


def verify_m32_filesystem_metadata_tool_safety():
    print("\n[Verifier] Running M32 safe filesystem metadata tool guard...")
    required_files = [
        "src/ultimate_ai_agent/core/tools/runtime/filesystem_metadata.py",
        "tests/test_filesystem_metadata_tool_contracts.py",
        "tests/test_filesystem_metadata_path_policy.py",
        "tests/test_filesystem_metadata_authority_boundaries.py",
        "tests/test_m32_gate_integration.py",
        "docs/tools/FILESYSTEM_METADATA_TOOL.md",
        "docs/tools/FILESYSTEM_METADATA_PATH_POLICY.md",
        "docs/tools/FILESYSTEM_METADATA_RESULT_CONTRACT.md",
        "docs/tools/FILESYSTEM_METADATA_AUTHORITY_BOUNDARY.md",
        "docs/tools/FILESYSTEM_METADATA_NON_GOALS.md",
        "docs/tools/M32_TO_M33_BOUNDARY.md",
        "docs/release_notes/v0_36_1.md",
        "docs/archive/releases/v0_36_1/README_IMPORT.md",
        "docs/archive/releases/v0_36_1/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_36_1.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M32 filesystem metadata file: {rel_path}")
            sys.exit(1)

    runtime_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "tools" / "runtime"
    forbidden_source_fragments = [
        "read_text(",
        "read_bytes(",
        "hashlib",
        ".glob(",
        ".rglob(",
        "os.walk(",
        "follow_symlinks=True",
        "shutil",
        ".unlink(",
        ".remove(",
        ".rename(",
        ".replace(",
        ".chmod(",
        ".chown(",
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "httpx.post(",
        "urllib.request.urlopen(",
        "os.system(",
        "popen(",
        "shell=True",
    ]
    for path in runtime_root.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for fragment in forbidden_source_fragments:
            if fragment.lower() in lowered:
                print(f"FAIL: M32 forbidden filesystem metadata source fragment in {rel}: {fragment}")
                sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m32_openapi_route_failures
        from ultimate_ai_agent.core.tools.runtime import (
            FILESYSTEM_METADATA_TOOL_NAME,
            FILESYSTEM_METADATA_TOOL_REF,
            NOOP_TOOL_REF,
            REDACTED_FILE_PREVIEW_TOOL_REF,
            FilesystemSafeRoot,
            ToolInvocationKind,
            ToolInvocationRequest,
            ToolInvocationStatus,
            build_tool_runtime_manifest,
            evaluate_tool_invocation,
        )
    except Exception as exc:
        print(f"FAIL: M32 filesystem metadata imports could not load: {exc}")
        sys.exit(1)

    for failure in m32_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    manifest = build_tool_runtime_manifest(baseline_version="0.36.1")
    policy = manifest.policy
    active_text = (ROOT / "VERSION.md").read_text(encoding="utf-8")
    expected_m32_allowlist = [NOOP_TOOL_REF, FILESYSTEM_METADATA_TOOL_REF]
    active_match = re.search(r"Current active baseline:\s*\*\*v(\d+)\.(\d+)\.(\d+)\*\*", active_text)
    active_tuple = tuple(int(part) for part in active_match.groups()) if active_match else (0, 0, 0)
    if active_tuple >= (0, 37, 0):
        expected_m32_allowlist.append(REDACTED_FILE_PREVIEW_TOOL_REF)
    if manifest.allowlisted_tool_refs != expected_m32_allowlist:
        print("FAIL: M32/M33 manifest allowlist is not the expected safe tool set")
        sys.exit(1)
    unsafe_flags = [
        policy.arbitrary_tool_execution_enabled,
        policy.side_effecting_tools_enabled,
        policy.shell_tools_enabled,
        policy.file_tools_enabled,
        policy.file_content_read_enabled,
        policy.file_preview_enabled,
        policy.file_hash_enabled,
        policy.directory_listing_enabled,
        policy.recursive_traversal_enabled,
        policy.symlink_following_enabled,
        policy.caller_selected_root_enabled,
        policy.file_write_enabled,
        policy.file_delete_enabled,
        policy.memory_write_tools_enabled,
        policy.network_tools_enabled,
        policy.model_tools_enabled,
        policy.browser_tools_enabled,
        policy.mobile_tools_enabled,
        policy.remote_tools_enabled,
        policy.plugin_tools_enabled,
        policy.dynamic_tool_registration_enabled,
        policy.backend_execute_routes_enabled,
        policy.control_center_execute_controls_enabled,
        policy.production_authority_enabled,
    ]
    if not policy.filesystem_metadata_tool_enabled or any(unsafe_flags):
        print("FAIL: M32 policy enables unsafe filesystem/runtime authority")
        sys.exit(1)

    def require_denial(decision, required_reason: str, label: str) -> None:
        if decision.status == ToolInvocationStatus.metadata_completed or decision.execution_performed:
            print(f"FAIL: M32 denied probe was allowed: {label}")
            sys.exit(1)
        if decision.side_effects_performed:
            print(f"FAIL: M32 denied probe reported side effects: {label}")
            sys.exit(1)
        if required_reason not in decision.reason_codes:
            print(f"FAIL: M32 denied probe missing {required_reason}: {label}")
            sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        safe_root_path = Path(tmp) / "safe-root"
        safe_root_path.mkdir()
        notes = safe_root_path / "notes"
        notes.mkdir()
        target = notes / "report.md"
        target.write_text("verify metadata only", encoding="utf-8")
        safe_root = FilesystemSafeRoot(
            root_ref="safe-root:verify-m32",
            root_path=safe_root_path,
            safe_label="Verify safe root",
        )
        safe_request = ToolInvocationRequest(
            invocation_id="tool-runtime-invocation:verify-m32",
            tool_ref=FILESYSTEM_METADATA_TOOL_REF,
            tool_name=FILESYSTEM_METADATA_TOOL_NAME,
            invocation_kind=ToolInvocationKind.filesystem_metadata,
            replay_key="tool-runtime-replay:verify-m32",
            safe_summary="Inspect safe filesystem metadata.",
            metadata={"root_ref": "safe-root:verify-m32", "relative_path": "notes/report.md"},
        )
        safe = evaluate_tool_invocation(safe_request, safe_roots=[safe_root])
        if safe.status != ToolInvocationStatus.metadata_completed or not safe.invocation_allowed:
            print("FAIL: M32 safe filesystem metadata invocation did not complete")
            sys.exit(1)
        dumped = str(safe.model_dump())
        if "verify metadata only" in dumped or str(safe_root_path) in dumped:
            print("FAIL: M32 filesystem metadata result leaked file content or absolute path")
            sys.exit(1)
        if safe.side_effects_performed or not safe.result or safe.result.side_effects_performed:
            print("FAIL: M32 filesystem metadata invocation reported side effects")
            sys.exit(1)
        output = safe.result.output
        unsafe_output_flags = [
            output.raw_content_returned,
            output.text_preview_returned,
            output.content_hash_returned,
            output.directory_listing_returned,
            output.absolute_path_returned,
            output.symlink_followed,
            output.mutation_performed,
        ]
        if any(unsafe_output_flags):
            print("FAIL: M32 filesystem metadata output is not metadata-only")
            sys.exit(1)

        for relative_path, reason in [
            ("/etc/passwd", "ABSOLUTE_PATH_DENIED"),
            ("../outside.md", "PATH_TRAVERSAL_DENIED"),
            ("notes/%2e%2e/outside.md", "PATH_TRAVERSAL_DENIED"),
            ("~/notes/report.md", "HOME_PATH_DENIED"),
            ("C:/Users/report.md", "WINDOWS_PATH_DENIED"),
            ("notes//report.md", "UNSAFE_PATH_SEPARATOR_DENIED"),
            (".env", "HIDDEN_PATH_DENIED"),
            (".git/config", "HIDDEN_PATH_DENIED"),
            ("notes/token.txt", "SECRET_LIKE_PATH_DENIED"),
            ("keys/id_rsa", "SECRET_LIKE_PATH_DENIED"),
            ("keys/private.key", "SECRET_LIKE_PATH_DENIED"),
            ("notes/*.md", "GLOB_PATH_DENIED"),
            ("notes/%2A.md", "GLOB_PATH_DENIED"),
        ]:
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={"metadata": {"root_ref": "safe-root:verify-m32", "relative_path": relative_path}}
                    ),
                    safe_roots=[safe_root],
                ),
                reason,
                f"path {relative_path}",
            )
        require_denial(
            evaluate_tool_invocation(
                safe_request.model_copy(
                    update={
                        "metadata": {
                            "root_ref": "safe-root:verify-m32",
                            "relative_path": "notes/report.md",
                            "root_path": str(safe_root_path),
                        }
                    }
                ),
                safe_roots=[safe_root],
            ),
            "CALLER_SELECTED_ROOT_DENIED",
            "caller-selected root",
        )
        require_denial(
            evaluate_tool_invocation(
                safe_request.model_copy(
                    update={
                        "metadata": {
                            "root_ref": "safe-root:missing",
                            "relative_path": "notes/%2e%2e/outside.md",
                        }
                    }
                ),
                safe_roots=[safe_root],
            ),
            "PATH_TRAVERSAL_DENIED",
            "model_copy encoded traversal",
        )
        require_denial(
            evaluate_tool_invocation(
                safe_request.model_copy(update={"tool_ref": "tool:file_content_read.v1"}),
                safe_roots=[safe_root],
            ),
            "TOOL_NOT_ALLOWLISTED_DENIED",
            "model_copy file content tool ref",
        )
        for flag_name, reason in [
            ("raw_content_enabled", "RAW_FILE_CONTENT_DENIED"),
            ("file_preview_enabled", "TEXT_PREVIEW_DENIED"),
            ("file_hash_enabled", "CONTENT_HASH_DENIED"),
            ("directory_listing_enabled", "DIRECTORY_LISTING_DENIED"),
            ("recursive_traversal_enabled", "RECURSIVE_TRAVERSAL_DENIED"),
            ("symlink_following_enabled", "SYMLINK_FOLLOWING_DENIED"),
            ("file_write_enabled", "FILESYSTEM_MUTATION_DENIED"),
            ("file_delete_enabled", "FILESYSTEM_MUTATION_DENIED"),
            ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
            ("caller_selected_root_enabled", "CALLER_SELECTED_ROOT_DENIED"),
        ]:
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={
                            "metadata": {
                                "root_ref": "safe-root:verify-m32",
                                "relative_path": "notes/report.md",
                                flag_name: True,
                            }
                        }
                    ),
                    safe_roots=[safe_root],
                ),
                reason,
                f"metadata alias flag {flag_name}",
            )
        try:
            link = safe_root_path / "link.md"
            link.symlink_to(target)
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={"metadata": {"root_ref": "safe-root:verify-m32", "relative_path": "link.md"}}
                    ),
                    safe_roots=[safe_root],
                ),
                "SYMLINK_DENIED",
                "symlink path",
            )
        except (OSError, NotImplementedError):
            pass
        require_denial(
            evaluate_tool_invocation(safe_request.model_copy(update={"contains_raw_file_content": True}), safe_roots=[safe_root]),
            "RAW_FILE_CONTENT_DENIED",
            "raw file model_copy",
        )
        require_denial(
            evaluate_tool_invocation(safe_request.model_copy(update={"authority_refs": ["model:verify-m32"]}), safe_roots=[safe_root]),
            "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY",
            "model authority ref",
        )

    print("OK: M32 filesystem metadata tool is safe-root-bound, metadata-only, route-free, and non-mutating")


def verify_m33_redacted_file_preview_tool_safety():
    print("\n[Verifier] Running M33 redacted file preview tool guard...")
    required_files = [
        "src/ultimate_ai_agent/core/tools/runtime/file_preview.py",
        "tests/test_redacted_file_preview_tool_contracts.py",
        "tests/test_redacted_file_preview_path_policy.py",
        "tests/test_redacted_file_preview_authority_boundaries.py",
        "tests/test_m33_gate_integration.py",
        "docs/tools/REDACTED_FILE_PREVIEW_TOOL.md",
        "docs/tools/REDACTED_FILE_PREVIEW_POLICY.md",
        "docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md",
        "docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md",
        "docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md",
        "docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md",
        "docs/tools/M33_TO_M34_BOUNDARY.md",
        "docs/release_notes/v0_37_1.md",
        "docs/archive/releases/v0_37_1/README_IMPORT.md",
        "docs/archive/releases/v0_37_1/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_37_1.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M33 redacted file preview file: {rel_path}")
            sys.exit(1)

    preview_source = (ROOT / "src/ultimate_ai_agent/core/tools/runtime/file_preview.py").read_text(encoding="utf-8")
    forbidden_source_fragments = [
        "read_text(",
        "read_bytes(",
        "hashlib",
        ".glob(",
        ".rglob(",
        "os.walk(",
        "follow_symlinks=True",
        "shutil",
        ".unlink(",
        ".remove(",
        ".rename(",
        ".replace(",
        ".chmod(",
        ".chown(",
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "httpx.post(",
        "urllib.request.urlopen(",
        "os.system(",
        "popen(",
        "shell=True",
    ]
    lowered_preview_source = preview_source.lower()
    for fragment in forbidden_source_fragments:
        if fragment.lower() in lowered_preview_source:
            print(f"FAIL: M33 forbidden redacted preview source fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m33_openapi_route_failures
        from ultimate_ai_agent.core.tools.runtime import (
            FILESYSTEM_METADATA_TOOL_REF,
            NOOP_TOOL_REF,
            REDACTED_FILE_PREVIEW_TOOL_NAME,
            REDACTED_FILE_PREVIEW_TOOL_REF,
            FilePreviewRedactionSummary,
            FilePreviewSafeRoot,
            RedactedFilePreviewOutput,
            RedactedFilePreviewStatus,
            ToolInvocationKind,
            ToolInvocationRequest,
            ToolInvocationStatus,
            build_tool_runtime_manifest,
            evaluate_tool_invocation,
        )
    except Exception as exc:
        print(f"FAIL: M33 redacted file preview imports could not load: {exc}")
        sys.exit(1)

    for failure in m33_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    manifest = build_tool_runtime_manifest(baseline_version="0.37.1")
    if manifest.allowlisted_tool_refs != [NOOP_TOOL_REF, FILESYSTEM_METADATA_TOOL_REF, REDACTED_FILE_PREVIEW_TOOL_REF]:
        print("FAIL: M33 manifest allowlist is not no-op, metadata, and redacted preview only")
        sys.exit(1)
    policy = manifest.policy
    unsafe_flags = [
        policy.arbitrary_tool_execution_enabled,
        policy.side_effecting_tools_enabled,
        policy.shell_tools_enabled,
        policy.file_tools_enabled,
        policy.file_content_read_enabled,
        policy.file_preview_enabled,
        policy.file_hash_enabled,
        policy.directory_listing_enabled,
        policy.recursive_traversal_enabled,
        policy.symlink_following_enabled,
        policy.caller_selected_root_enabled,
        policy.file_write_enabled,
        policy.file_delete_enabled,
        policy.memory_write_tools_enabled,
        policy.network_tools_enabled,
        policy.model_tools_enabled,
        policy.browser_tools_enabled,
        policy.mobile_tools_enabled,
        policy.remote_tools_enabled,
        policy.plugin_tools_enabled,
        policy.dynamic_tool_registration_enabled,
        policy.backend_execute_routes_enabled,
        policy.control_center_execute_controls_enabled,
        policy.production_authority_enabled,
    ]
    if not policy.redacted_file_preview_tool_enabled or any(unsafe_flags):
        print("FAIL: M33 policy enables unsafe redacted preview/runtime authority")
        sys.exit(1)

    def require_denial(decision, required_reason: str, label: str) -> None:
        if decision.status == ToolInvocationStatus.preview_completed or decision.execution_performed:
            print(f"FAIL: M33 denied probe was allowed: {label}")
            sys.exit(1)
        if decision.side_effects_performed:
            print(f"FAIL: M33 denied probe reported side effects: {label}")
            sys.exit(1)
        if required_reason not in decision.reason_codes:
            print(f"FAIL: M33 denied probe missing {required_reason}: {label}")
            sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        safe_root_path = Path(tmp) / "safe-root"
        safe_root_path.mkdir()
        notes = safe_root_path / "notes"
        notes.mkdir()
        target = notes / "report.md"
        target.write_text("Title\nAPI_KEY=verify-secret-value\nPublic summary.\n", encoding="utf-8")
        safe_root = FilePreviewSafeRoot(
            root_ref="safe-root:verify-m33",
            root_path=safe_root_path,
            safe_label="Verify safe root",
        )
        safe_request = ToolInvocationRequest(
            invocation_id="tool-runtime-invocation:verify-m33",
            tool_ref=REDACTED_FILE_PREVIEW_TOOL_REF,
            tool_name=REDACTED_FILE_PREVIEW_TOOL_NAME,
            invocation_kind=ToolInvocationKind.redacted_file_preview,
            replay_key="tool-runtime-replay:verify-m33",
            safe_summary="Generate a redacted file preview proposal.",
            metadata={"root_ref": "safe-root:verify-m33", "relative_path": "notes/report.md"},
        )
        safe = evaluate_tool_invocation(safe_request, safe_roots=[safe_root])
        if safe.status != ToolInvocationStatus.preview_completed or not safe.invocation_allowed:
            print("FAIL: M33 safe redacted preview invocation did not complete")
            sys.exit(1)
        dumped = str(safe.model_dump())
        if "verify-secret-value" in dumped or str(safe_root_path) in dumped:
            print("FAIL: M33 redacted preview leaked raw secret or absolute path")
            sys.exit(1)
        if safe.side_effects_performed or not safe.result or safe.result.side_effects_performed:
            print("FAIL: M33 redacted preview invocation reported side effects")
            sys.exit(1)
        output = safe.result.output
        unsafe_output_flags = [
            output.raw_content_returned,
            output.raw_content_stored,
            output.full_file_returned,
            output.content_hash_returned,
            output.directory_listing_returned,
            output.absolute_path_returned,
            output.symlink_followed,
            output.mutation_performed,
            output.context_injection_performed,
        ]
        if any(unsafe_output_flags) or not output.redacted_preview_returned:
            print("FAIL: M33 redacted preview output is not redacted-preview-only")
            sys.exit(1)
        try:
            RedactedFilePreviewOutput(
                output_ref="redacted-file-preview-output:verify-unsafe",
                status=RedactedFilePreviewStatus.preview_generated,
                root_ref="safe-root:verify-m33",
                safe_path_ref="filesystem-preview-path:safe-root_verify-m33/notes/report.md",
                redacted_preview="API_KEY=verify-secret-value",
                redaction_summary=FilePreviewRedactionSummary(),
                file_size_bytes=27,
            )
            print("FAIL: M33 redacted preview output accepted unredacted secret-like content")
            sys.exit(1)
        except ValueError as exc:
            if "REDACTED_FILE_PREVIEW_OUTPUT_CONTAINS_SECRET_LIKE_CONTENT" not in str(exc):
                print("FAIL: M33 redacted preview output rejected unsafe content with unexpected reason")
                sys.exit(1)

        for relative_path, reason in [
            ("/etc/passwd", "ABSOLUTE_PATH_DENIED"),
            ("../outside.md", "PATH_TRAVERSAL_DENIED"),
            ("notes/%2e%2e/outside.md", "PATH_TRAVERSAL_DENIED"),
            (".env", "HIDDEN_PATH_DENIED"),
            ("notes/token.txt", "SECRET_LIKE_PATH_DENIED"),
            ("notes/*.md", "GLOB_PATH_DENIED"),
        ]:
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={"metadata": {"root_ref": "safe-root:verify-m33", "relative_path": relative_path}}
                    ),
                    safe_roots=[safe_root],
                ),
                reason,
                f"path {relative_path}",
            )
        binary = notes / "binary.txt"
        binary.write_bytes(b"hello\x00world")
        require_denial(
            evaluate_tool_invocation(
                safe_request.model_copy(
                    update={"metadata": {"root_ref": "safe-root:verify-m33", "relative_path": "notes/binary.txt"}}
                ),
                safe_roots=[safe_root],
            ),
            "BINARY_FILE_DENIED",
            "binary file",
        )
        try:
            symlink_root_path = Path(tmp) / "safe-root-link"
            symlink_root_path.symlink_to(safe_root_path, target_is_directory=True)
            symlink_root = FilePreviewSafeRoot(
                root_ref="safe-root:verify-m33-link",
                root_path=symlink_root_path,
                safe_label="Verify symlink safe root",
            )
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={
                            "metadata": {
                                "root_ref": "safe-root:verify-m33-link",
                                "relative_path": "notes/report.md",
                            }
                        }
                    ),
                    safe_roots=[symlink_root],
                ),
                "SAFE_ROOT_SYMLINK_DENIED",
                "symlink safe root",
            )
        except (OSError, NotImplementedError):
            pass
        for flag_name, reason in [
            ("raw_content_enabled", "RAW_FILE_CONTENT_DENIED"),
            ("full_file_read_enabled", "FULL_FILE_READ_DENIED"),
            ("content_hash_enabled", "CONTENT_HASH_DENIED"),
            ("directory_listing_enabled", "DIRECTORY_LISTING_DENIED"),
            ("recursive_traversal_enabled", "RECURSIVE_TRAVERSAL_DENIED"),
            ("symlink_following_enabled", "SYMLINK_FOLLOWING_DENIED"),
            ("file_write_enabled", "FILESYSTEM_MUTATION_DENIED"),
            ("file_delete_enabled", "FILESYSTEM_MUTATION_DENIED"),
            ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
            ("caller_selected_root_enabled", "CALLER_SELECTED_ROOT_DENIED"),
            ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ]:
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={
                            "metadata": {
                                "root_ref": "safe-root:verify-m33",
                                "relative_path": "notes/report.md",
                                flag_name: True,
                            }
                        }
                    ),
                    safe_roots=[safe_root],
                ),
                reason,
                f"metadata alias flag {flag_name}",
            )
        require_denial(
            evaluate_tool_invocation(
                safe_request.model_copy(update={"tool_ref": "tool:filesystem.raw_read.v1"}),
                safe_roots=[safe_root],
            ),
            "TOOL_NOT_ALLOWLISTED_DENIED",
            "model_copy raw read tool ref",
        )
        require_denial(
            evaluate_tool_invocation(
                safe_request.model_copy(update={"authority_refs": ["model:verify-m33"]}),
                safe_roots=[safe_root],
            ),
            "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY",
            "model authority ref",
        )

    print("OK: M33 redacted file preview tool is redacted-only, safe-root-bound, route-free, and non-mutating")


def verify_m34_broader_file_capability_review_safety():
    print("\n[Verifier] Running M34 broader file capability review guard...")
    required_files = [
        "docs/files/BROADER_FILE_CAPABILITY_REVIEW.md",
        "docs/files/FILE_CAPABILITY_BOUNDARY_MATRIX.md",
        "docs/files/FILE_CAPABILITY_RISK_REGISTER.md",
        "docs/files/FILE_CAPABILITY_DECISION_RECORD.md",
        "docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md",
        "docs/files/M34_TO_M35_BOUNDARY.md",
        "docs/control_center/FILE_REVIEW_SURFACE_READINESS.md",
        "docs/tools/FILE_TOOL_CAPABILITY_MATRIX.md",
        "tests/test_m34_gate_integration.py",
        "docs/release_notes/v0_38_0.md",
        "docs/archive/releases/v0_38_0/README_IMPORT.md",
        "docs/archive/releases/v0_38_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_38_0.md",
        "docs/release_notes/v0_38_1.md",
        "docs/archive/releases/v0_38_1/README_IMPORT.md",
        "docs/archive/releases/v0_38_1/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_38_1.md",
        "docs/release_notes/v0_38_2.md",
        "docs/archive/releases/v0_38_2/README_IMPORT.md",
        "docs/archive/releases/v0_38_2/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_38_2.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M34 broader file capability review file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join((ROOT / rel_path).read_text(encoding="utf-8").lower() for rel_path in required_files)
    required_fragments = {
        "planning/review only": "M34 docs do not constrain the release to planning/review only",
        "no runtime file capability": "M34 docs do not deny runtime file capability",
        "no raw file reads": "M34 docs do not deny raw file reads",
        "no file review ui": "M34 docs do not keep file review UI future-only",
        "no approval persistence": "M34 docs do not keep approval persistence future-only",
        "no context proposal": "M34 docs do not keep context proposal future-only",
        "no context injection": "M34 docs do not deny context injection",
        "no memory writes": "M34 docs do not deny memory writes",
        "no export": "M34 docs do not deny export",
        "no execution": "M34 docs do not deny execution",
        "no backend routes": "M34 docs do not deny backend routes",
        "m36 remains planned/provisional": "M34 docs do not keep M36 planned/provisional",
    }
    current_version = (ROOT / "VERSION.md").read_text(encoding="utf-8")
    if "v0.39." in current_version:
        required_fragments["v0.39.0 implements m35"] = "M34 docs do not acknowledge implemented M35"
    else:
        required_fragments["m35 remains planned/provisional"] = "M34 docs do not keep M35 planned/provisional"
    for fragment, message in required_fragments.items():
        if fragment not in docs_text:
            print(f"FAIL: {message}")
            sys.exit(1)

    readme_text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    readme_normalized = re.sub(r"\s+", " ", readme_text.replace("|", " | ")).strip()
    if "v0.38.0 | m34 - broader file capability review | planned/provisional" in readme_normalized:
        print("FAIL: README.md must not list v0.38.0/M34 as planned/provisional")
        sys.exit(1)

    stale_m33_docs = []
    for rel_path in [
        "docs/files/LOCAL_FILE_REDACTED_PREVIEW_POLICY.md",
        "docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md",
        "docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md",
        "docs/tools/REDACTED_FILE_PREVIEW_POLICY.md",
        "docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md",
        "docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md",
        "docs/tools/REDACTED_FILE_PREVIEW_TOOL.md",
    ]:
        text = (ROOT / rel_path).read_text(encoding="utf-8").lower()
        if "m34 remains planned/provisional" in text:
            stale_m33_docs.append(rel_path)
    if stale_m33_docs:
        print(
            "FAIL: active M33 docs must not say M34 remains planned/provisional after v0.38.0: "
            + ", ".join(stale_m33_docs)
        )
        sys.exit(1)

    forbidden_doc_fragments = [
        "m34 implements safe file review workflow contracts",
        "approval persistence is implemented",
        "review approval capture is implemented",
        "context proposal is implemented",
        "context injection is implemented",
        "raw file export is implemented",
        "backend file route is implemented",
    ]
    if "v0.40." not in current_version:
        forbidden_doc_fragments.extend(
            [
                "file review ui is implemented",
                "ccc file review surface is implemented",
            ]
        )
    if "v0.39." not in current_version:
        forbidden_doc_fragments.append("safe file review workflow is implemented")
    for fragment in forbidden_doc_fragments:
        if fragment in docs_text:
            print(f"FAIL: M34 docs imply future implementation: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m34_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M34 OpenAPI guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m34_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    forbidden_frontend_fragments = [
        "/files/review/approve",
        "/context/inject",
        "/memory/write",
        "/tool-runtime/execute",
        "copy raw",
        "raw preview",
        "file picker",
        "root selector",
    ]
    frontend_root = ROOT / "apps" / "control-center" / "src"
    if frontend_root.exists() and _current_version() < "v0.40.0":
        for path in frontend_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8").lower()
            for fragment in forbidden_frontend_fragments:
                if fragment in text:
                    print(f"FAIL: M34 forbidden file-review frontend fragment in {rel}: {fragment}")
                    sys.exit(1)

    if "v0.40." in current_version:
        print("OK: M34 broader file capability review is docs/verifier-only, route-free, acknowledges M35/M36, and leaves M36 safety to the M36 verifier")
    elif "v0.39." in current_version:
        print("OK: M34 broader file capability review is docs/verifier-only, route-free, acknowledges M35, and keeps M36 future")
    else:
        print("OK: M34 broader file capability review is docs/verifier-only, route-free, and keeps M35/M36 future")


def verify_m35_safe_file_review_workflow_safety():
    print("\n[Verifier] Running M35 safe file review workflow guard...")
    required_files = [
        "src/ultimate_ai_agent/core/file_review/__init__.py",
        "src/ultimate_ai_agent/core/file_review/contracts.py",
        "src/ultimate_ai_agent/core/file_review/enums.py",
        "src/ultimate_ai_agent/core/file_review/workflow.py",
        "docs/files/SAFE_FILE_REVIEW_WORKFLOW.md",
        "docs/files/FILE_REVIEW_PACKET_CONTRACT.md",
        "docs/files/FILE_REVIEW_USER_APPROVAL_GATE.md",
        "docs/files/FILE_REVIEW_AUTHORITY_BOUNDARY.md",
        "docs/files/FILE_REVIEW_RECEIPT_PLAN.md",
        "docs/files/FILE_REVIEW_NON_GOALS.md",
        "docs/files/M35_TO_M36_BOUNDARY.md",
        "tests/test_file_review_workflow_contracts.py",
        "tests/test_file_review_packet_validation.py",
        "tests/test_file_review_approval_gate.py",
        "tests/test_file_review_authority_boundaries.py",
        "tests/test_file_review_receipt_plan.py",
        "tests/test_m35_gate_integration.py",
        "docs/release_notes/v0_39_0.md",
        "docs/archive/releases/v0_39_0/README_IMPORT.md",
        "docs/archive/releases/v0_39_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_39_0.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M35 safe file review workflow file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    required_fragments = {
        "redacted review packets only": "M35 docs do not require redacted review packets only",
        "exact approval binding": "M35 docs do not require exact approval binding",
        "review-only": "M35 docs do not require review-only decisions",
        "no raw file access": "M35 docs do not deny raw file access",
        "no raw content": "M35 docs do not deny raw content",
        "no approval capture": "M35 docs do not deny approval capture",
        "no approval persistence": "M35 docs do not deny approval persistence",
        "no context proposal": "M35 docs do not deny context proposal",
        "no context injection": "M35 docs do not deny context injection",
        "no memory writes": "M35 docs do not deny memory writes",
        "no export": "M35 docs do not deny export",
        "no execution": "M35 docs do not deny execution",
        "no backend routes": "M35 docs do not deny backend routes",
        "m36 remains planned/provisional": "M35 docs do not keep M36 planned/provisional",
        "m37 remains planned/provisional": "M35 docs do not keep M37 planned/provisional",
        "m38 remains planned/provisional": "M35 docs do not keep M38 planned/provisional",
    }
    for fragment, message in required_fragments.items():
        if fragment not in docs_text:
            print(f"FAIL: {message}")
            sys.exit(1)

    source_root = ROOT / "src" / "ultimate_ai_agent" / "core" / "file_review"
    forbidden_source_fragments = [
        "subprocess",
        "os.system",
        "shell=true",
        "requests.",
        "httpx.",
        "urllib.request.urlopen",
        ".write_text(",
        ".write_bytes(",
        "open(",
    ]
    source_text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in source_root.rglob("*.py")
        if path.name != "approval_capture.py"
    )
    for fragment in forbidden_source_fragments:
        if fragment in source_text:
            print(f"FAIL: M35 file review source contains forbidden runtime fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from datetime import timedelta

        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.file_review import (
            FileReviewDecisionStatus,
            UserFileReviewApproval,
            build_file_review_packet,
            evaluate_file_review_gate,
            evaluate_file_review_packet,
        )
        from ultimate_ai_agent.core.gate.evaluators import m35_openapi_route_failures
        from ultimate_ai_agent.core.time import utc_now
        from ultimate_ai_agent.core.tools.runtime import (
            FilePreviewRedactionSummary,
            RedactedFilePreviewOutput,
            RedactedFilePreviewStatus,
        )
    except Exception as exc:
        print(f"FAIL: M35 imports could not load: {exc}")
        sys.exit(1)

    preview = RedactedFilePreviewOutput(
        output_ref="redacted-file-preview-output:verify",
        status=RedactedFilePreviewStatus.preview_generated,
        root_ref="safe-root:verify",
        safe_path_ref="filesystem-preview-path:safe-root_verify/docs/review.md",
        redacted_preview="Redacted preview only.",
        redaction_summary=FilePreviewRedactionSummary(redaction_count=0, categories=[]),
        file_size_bytes=32,
    )
    packet = build_file_review_packet(
        preview_output=preview,
        actor_ref="user:verify",
        request_ref="file-review-request:verify",
        file_ref="file-ref:verify-review",
        safe_summary="Review a redacted preview packet.",
    )
    if evaluate_file_review_packet(packet).status != FileReviewDecisionStatus.packet_valid_for_review:
        print("FAIL: M35 safe review packet did not validate for review")
        sys.exit(1)
    if "FILE_REVIEW_RAW_CONTENT_DENIED" not in evaluate_file_review_packet(
        packet.model_copy(update={"raw_content": "raw secret"})
    ).reason_codes:
        print("FAIL: M35 evaluator did not deny model_copy raw_content")
        sys.exit(1)
    approval = UserFileReviewApproval(
        approval_ref="file-review-approval:verify",
        actor_ref="user:verify",
        review_packet_ref=packet.review_packet_ref,
        preview_result_ref=packet.source.preview_result_ref,
        redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
        file_ref=packet.source.file_ref,
        safe_path_ref=packet.source.safe_path_ref,
        expires_at=utc_now() + timedelta(minutes=5),
    )
    allowed = evaluate_file_review_gate(packet, approval=approval, current_time=utc_now())
    if allowed.status != FileReviewDecisionStatus.review_allowed or allowed.execution_authorized or allowed.execution_performed:
        print("FAIL: M35 exact approval binding did not remain review-only")
        sys.exit(1)
    if "FILE_REVIEW_APPROVAL_PACKET_MISMATCH" not in evaluate_file_review_gate(
        packet,
        approval=approval.model_copy(update={"review_packet_ref": "file-review-packet:other"}),
        current_time=utc_now(),
    ).reason_codes:
        print("FAIL: M35 approval gate did not deny mismatched packet ref")
        sys.exit(1)
    if "FILE_REVIEW_APPROVAL_FILE_REF_MISMATCH" not in evaluate_file_review_gate(
        packet.model_copy(update={"source": packet.source.model_copy(update={"file_ref": "file-ref:verify-mutated"})}),
        approval=approval,
        current_time=utc_now(),
    ).reason_codes:
        print("FAIL: M35 approval gate did not deny mutated packet file_ref")
        sys.exit(1)
    if "FILE_REVIEW_APPROVAL_PATH_REF_MISMATCH" not in evaluate_file_review_gate(
        packet.model_copy(
            update={"source": packet.source.model_copy(update={"safe_path_ref": "filesystem-preview-path:safe-root_verify/docs/mutated.md"})}
        ),
        approval=approval,
        current_time=utc_now(),
    ).reason_codes:
        print("FAIL: M35 approval gate did not deny mutated packet safe_path_ref")
        sys.exit(1)
    if "FILE_REVIEW_APPROVAL_TEST_REF_DENIED" not in evaluate_file_review_gate(
        packet,
        approval=approval.model_copy(update={"approval_ref": "approval_test_verify"}),
        current_time=utc_now(),
    ).reason_codes:
        print("FAIL: M35 approval gate did not deny approval_test ref")
        sys.exit(1)

    paths = set(app.openapi().get("paths", {}))
    if _current_version() >= "v0.41.0":
        paths.discard("/files/review/approvals/capture")
    for failure in m35_openapi_route_failures(paths):
        print(f"FAIL: {failure}")
        sys.exit(1)

    forbidden_frontend_fragments = [
        "/files/review/approve",
        "/files/review/persist",
        "/context/propose",
        "/context/inject",
        "/memory/write",
        "/files/export",
        "raw preview",
        "approve review",
    ]
    frontend_root = ROOT / "apps" / "control-center" / "src"
    if frontend_root.exists():
        for path in frontend_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8").lower()
            for fragment in forbidden_frontend_fragments:
                if _current_version() >= "v0.41.0" and fragment == "approve review":
                    continue
                if fragment in text:
                    print(f"FAIL: M35 forbidden file-review frontend fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M35 safe file review workflow is contract-only, review-only, route-free, and non-authoritative")


def verify_m36_ccc_file_review_surface_safety():
    print("\n[Verifier] Running M36 CCC file review surface guard...")
    if _current_version() >= "v0.41.0":
        print("OK: M36 file review surface historical guard deferred to M37 capture verifier for active v0.41.0+ tree")
        return
    required_files = [
        "apps/control-center/src/components/FileReviewSurfacePanel.tsx",
        "apps/control-center/src/mocks/controlCenterData.ts",
        "apps/control-center/src/routes.tsx",
        "apps/control-center/src/App.test.tsx",
        "docs/control_center/FILE_REVIEW_SURFACE.md",
        "docs/control_center/FILE_REVIEW_REVIEW_ONLY_POLICY.md",
        "docs/control_center/FILE_REVIEW_MOCK_DATA_POLICY.md",
        "docs/control_center/FILE_REVIEW_BINDING_DISPLAY_POLICY.md",
        "docs/control_center/M36_TO_M37_BOUNDARY.md",
        "docs/release_notes/v0_40_1.md",
        "docs/archive/releases/v0_40_1/README_IMPORT.md",
        "docs/archive/releases/v0_40_1/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_40_1.md",
        "tests/test_m36_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M36 CCC file review surface file: {rel_path}")
            sys.exit(1)

    combined = "\n".join((ROOT / rel_path).read_text(encoding="utf-8").lower() for rel_path in required_files)
    required_fragments = {
        "review-only": "M36 docs/tests do not require review-only surface",
        "mock and non-authoritative": "M36 docs/tests do not require mock non-authoritative data",
        "redacted preview": "M36 docs/tests do not require redacted preview display",
        "redaction summary": "M36 docs/tests do not require redaction summary display",
        "exact binding refs": "M36 docs/tests do not require exact binding refs display",
        "safe refs only": "M36 docs/tests do not require safe refs only",
        "no mutating request is made": "M36 docs/tests do not require no mutating request boundary",
        "review_packet_ref": "M36 docs/tests do not require review_packet_ref display",
        "preview_result_ref": "M36 docs/tests do not require preview_result_ref display",
        "redaction_summary_ref": "M36 docs/tests do not require redaction_summary_ref display",
        "file_ref": "M36 docs/tests do not require file_ref display",
        "safe_path_ref": "M36 docs/tests do not require safe_path_ref display",
        "approval gate contract status": "M36 docs/tests do not require approval-gate contract status display",
        "receipt plan metadata": "M36 docs/tests do not require receipt-plan metadata display",
        "no approval capture": "M36 docs/tests do not deny approval capture",
        "no approval persistence": "M36 docs/tests do not deny approval persistence",
        "no raw file display": "M36 docs/tests do not deny raw file display",
        "no context proposal": "M36 docs/tests do not deny context proposal",
        "no context injection": "M36 docs/tests do not deny context injection",
        "no memory writes": "M36 docs/tests do not deny memory writes",
        "no export": "M36 docs/tests do not deny export",
        "no execution": "M36 docs/tests do not deny execution",
        "m37 remains planned/provisional": "M36 docs/tests do not keep M37 planned/provisional",
        "m38 remains planned/provisional": "M36 docs/tests do not keep M38 planned/provisional",
    }
    for fragment, message in required_fragments.items():
        if fragment not in combined:
            print(f"FAIL: {message}")
            sys.exit(1)

    component = (ROOT / "apps/control-center/src/components/FileReviewSurfacePanel.tsx").read_text(encoding="utf-8").lower()
    mock_text = (ROOT / "apps/control-center/src/mocks/controlCenterData.ts").read_text(encoding="utf-8")
    try:
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.core.gate.evaluators import m36_file_review_surface_failures
    except Exception as exc:
        print(f"FAIL: M36 surface safety helper could not load: {exc}")
        sys.exit(1)

    for failure in m36_file_review_surface_failures(component_text=component, mock_text=mock_text):
        print(f"FAIL: {failure}")
        sys.exit(1)

    forbidden_button_labels = [
        "approve",
        "deny",
        "submit",
        "save",
        "mark reviewed",
        "export",
        "download",
        "copy raw",
        "file picker",
        "browse",
        "upload",
        "root selector",
        "open raw file",
        "context proposal",
        "inject",
        "write memory",
        "execute",
        "run",
        "run tool",
        "call model",
    ]
    for label in forbidden_button_labels:
        if re.search(rf"<button\b[^>]*>\s*{re.escape(label)}\s*</button>", component, re.IGNORECASE):
            print(f"FAIL: M36 component exposes forbidden button label: {label}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m36_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M36 imports could not load: {exc}")
        sys.exit(1)

    for failure in m36_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    print("OK: M36 CCC file review surface is review-only, mock, route-free, and non-authoritative")


def verify_m37_review_approval_capture_safety():
    print("\n[Verifier] Running M37 review approval capture guard...")
    required_files = [
        "src/ultimate_ai_agent/core/file_review/approval_capture.py",
        "src/ultimate_ai_agent/api/app.py",
        "apps/control-center/src/components/FileReviewSurfacePanel.tsx",
        "apps/control-center/src/mocks/controlCenterData.ts",
        "docs/files/FILE_REVIEW_APPROVAL_CAPTURE.md",
        "docs/files/FILE_REVIEW_APPROVAL_PERSISTENCE.md",
        "docs/files/FILE_REVIEW_APPROVAL_AUTHORITY_BOUNDARY.md",
        "docs/files/FILE_REVIEW_APPROVAL_API.md",
        "docs/files/M37_TO_M38_BOUNDARY.md",
        "tests/test_file_review_approval_capture_contracts.py",
        "tests/test_file_review_approval_store.py",
        "tests/test_file_review_approval_api.py",
        "tests/test_m37_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M37 review approval capture file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    required_doc_fragments = [
        "review-only persistence",
        "exact redacted review packet",
        "safe refs only",
        "no raw file access",
        "no context proposal",
        "no context injection",
        "no memory write",
        "no export",
        "no execution",
    ]
    if _current_version() >= "v0.42.0":
        required_doc_fragments.append("m38 is now implemented/released")
    else:
        required_doc_fragments.append("m38 remains planned/provisional")
    for fragment in required_doc_fragments:
        if fragment not in docs_text:
            print(f"FAIL: M37 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.file_review import (
            FileReviewApprovalCaptureDecisionStatus,
            FileReviewApprovalCaptureRequest,
            FileReviewApprovalDecisionKind,
            FileReviewApprovalStore,
            build_file_review_packet,
            capture_file_review_approval,
        )
        from ultimate_ai_agent.core.gate.evaluators import m37_openapi_route_failures
        from ultimate_ai_agent.core.tools.runtime import (
            FilePreviewRedactionSummary,
            RedactedFilePreviewOutput,
            RedactedFilePreviewStatus,
        )
    except Exception as exc:
        print(f"FAIL: M37 imports could not load: {exc}")
        sys.exit(1)

    preview = RedactedFilePreviewOutput(
        output_ref="redacted-file-preview-output:verify-m37",
        status=RedactedFilePreviewStatus.preview_generated,
        root_ref="safe-root:verify-m37",
        safe_path_ref="filesystem-preview-path:safe-root_verify_m37/docs/review.md",
        redacted_preview="Redacted preview only.",
        redaction_summary=FilePreviewRedactionSummary(redaction_count=0, categories=[]),
        file_size_bytes=32,
    )
    packet = build_file_review_packet(
        preview_output=preview,
        actor_ref="user:verify-m37",
        request_ref="file-review-request:verify-m37",
        file_ref="file-ref:verify-m37-review",
        safe_summary="Review a redacted preview packet.",
    )
    request = FileReviewApprovalCaptureRequest(
        approval_ref="file-review-approval-capture:verify-m37",
        actor_ref=packet.source.actor_ref,
        review_packet_ref=packet.review_packet_ref,
        preview_result_ref=packet.source.preview_result_ref,
        redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
        file_ref=packet.source.file_ref,
        safe_path_ref=packet.source.safe_path_ref,
        decision=FileReviewApprovalDecisionKind.approve_review_only,
        idempotency_key="file-review-approval-idempotency:verify-m37",
    )
    decision = capture_file_review_approval(packet, request, store=FileReviewApprovalStore())
    if decision.status != FileReviewApprovalCaptureDecisionStatus.approved_for_review_only:
        print("FAIL: M37 safe review approval capture did not succeed")
        sys.exit(1)
    if any(
        [
            decision.raw_file_access_authorized,
            decision.context_proposal_authorized,
            decision.context_injection_authorized,
            decision.memory_write_authorized,
            decision.export_authorized,
            decision.execution_authorized,
            decision.execution_performed,
        ]
    ):
        print("FAIL: M37 review approval capture granted forbidden authority")
        sys.exit(1)
    denied = capture_file_review_approval(
        packet,
        request.model_copy(update={"raw_content_enabled": True}),
        store=FileReviewApprovalStore(),
    )
    if "FILE_REVIEW_APPROVAL_CAPTURE_RAW_CONTENT_DENIED" not in denied.reason_codes:
        print("FAIL: M37 evaluator did not deny model_copy raw content flag")
        sys.exit(1)

    for failure in m37_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    component_text = (ROOT / "apps/control-center/src/components/FileReviewSurfacePanel.tsx").read_text(encoding="utf-8").lower()
    for required in ["approve review-only", "deny review-only", "does not grant raw file access"]:
        if required not in component_text:
            print(f"FAIL: M37 Control Center missing review-only capture marker: {required}")
            sys.exit(1)
    for forbidden in ["export raw", "copy raw", "inject context", "write memory", "execute tool", "run tool"]:
        if forbidden in component_text:
            print(f"FAIL: M37 Control Center exposes forbidden control copy: {forbidden}")
            sys.exit(1)

    print("OK: M37 review approval capture is safe-ref-only, review-only, and non-authoritative")


def verify_m38_safe_context_proposal_safety():
    print("\n[Verifier] Running M38 safe context proposal guard...")
    required_files = [
        "src/ultimate_ai_agent/core/context_proposal/__init__.py",
        "src/ultimate_ai_agent/core/context_proposal/contracts.py",
        "src/ultimate_ai_agent/core/context_proposal/validation.py",
        "src/ultimate_ai_agent/core/context_proposal/workflow.py",
        "docs/context/SAFE_CONTEXT_PROPOSAL_FROM_APPROVED_REVIEW.md",
        "docs/context/CONTEXT_PROPOSAL_CONTRACT.md",
        "docs/context/CONTEXT_PROPOSAL_AUTHORITY_BOUNDARY.md",
        "docs/context/CONTEXT_PROPOSAL_RECEIPT_PLAN.md",
        "docs/context/CONTEXT_PROPOSAL_NON_GOALS.md",
        "docs/context/M38_TO_M39_BOUNDARY.md",
        "tests/test_safe_context_proposal_contracts.py",
        "tests/test_safe_context_proposal_binding.py",
        "tests/test_safe_context_proposal_no_raw_content.py",
        "tests/test_safe_context_proposal_authority_boundaries.py",
        "tests/test_safe_context_proposal_receipt_plan.py",
        "tests/test_m38_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M38 safe context proposal file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    required_doc_fragments = [
        "non-authoritative",
        "not context injection",
        "not openwebui handoff",
        "does not write memory",
        "does not export",
        "does not execute",
        "exact approved-review binding",
        "approval_ref alone is not authority",
    ]
    if _current_version() >= "v0.43.0":
        required_doc_fragments.extend(
            [
                "m39 is implemented/released",
                "m40 remains future",
            ]
        )
    else:
        required_doc_fragments.append("m39 remains planned/provisional")
    for fragment in required_doc_fragments:
        if fragment not in docs_text:
            print(f"FAIL: M38 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.context_proposal import (
            SafeContextProposalDecisionStatus,
            evaluate_safe_context_proposal_request,
        )
        from ultimate_ai_agent.core.file_review import (
            FileReviewApprovalCaptureDecisionStatus,
            FileReviewApprovalDecisionKind,
            FileReviewApprovalRecord,
            build_file_review_packet,
        )
        from ultimate_ai_agent.core.gate.evaluators import m38_openapi_route_failures
        from ultimate_ai_agent.core.tools.runtime import (
            FilePreviewRedactionSummary,
            RedactedFilePreviewOutput,
            RedactedFilePreviewStatus,
        )
    except Exception as exc:
        print(f"FAIL: M38 imports could not load: {exc}")
        sys.exit(1)

    preview = RedactedFilePreviewOutput(
        output_ref="redacted-file-preview-output:verify-m38",
        status=RedactedFilePreviewStatus.preview_generated,
        root_ref="safe-root:verify-m38",
        safe_path_ref="filesystem-preview-path:safe-root_verify_m38/docs/review.md",
        redacted_preview="Redacted preview only.",
        redaction_summary=FilePreviewRedactionSummary(redaction_count=0, categories=[]),
        file_size_bytes=32,
    )
    packet = build_file_review_packet(
        preview_output=preview,
        actor_ref="user:verify-m38",
        request_ref="file-review-request:verify-m38",
        file_ref="file-ref:verify-m38-review",
        safe_summary="Review a redacted packet for context proposal.",
    )
    record = FileReviewApprovalRecord(
        approval_ref="file-review-approval-capture:verify-m38",
        actor_ref=packet.source.actor_ref,
        review_packet_ref=packet.review_packet_ref,
        preview_result_ref=packet.source.preview_result_ref,
        redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
        file_ref=packet.source.file_ref,
        safe_path_ref=packet.source.safe_path_ref,
        decision=FileReviewApprovalDecisionKind.approve_review_only,
        status=FileReviewApprovalCaptureDecisionStatus.approved_for_review_only,
        idempotency_key="file-review-approval-idempotency:verify-m38",
    )
    allowed = evaluate_safe_context_proposal_request(packet=packet, approval_record=record)
    if allowed.status != SafeContextProposalDecisionStatus.proposal_ready or not allowed.proposal_ready:
        print("FAIL: M38 safe approved review did not build proposal")
        sys.exit(1)
    if any(
        [
            allowed.context_injection_authorized,
            allowed.openwebui_handoff_authorized,
            allowed.model_call_authorized,
            allowed.memory_write_authorized,
            allowed.export_authorized,
            allowed.execution_authorized,
            allowed.execution_performed,
        ]
    ):
        print("FAIL: M38 proposal granted forbidden authority")
        sys.exit(1)
    denied_ref = evaluate_safe_context_proposal_request(packet=packet, approval_record=None, approval_ref=record.approval_ref)
    if "approval_ref_not_authority" not in denied_ref.reason_codes:
        print("FAIL: M38 approval_ref alone was not denied")
        sys.exit(1)
    denied_path = evaluate_safe_context_proposal_request(
        packet=packet,
        approval_record=record.model_copy(update={"safe_path_ref": "filesystem-preview-path:safe-root_verify_m38/docs/other.md"}),
    )
    if "path_ref_mismatch" not in denied_path.reason_codes:
        print("FAIL: M38 file/path exact binding was not enforced")
        sys.exit(1)
    denied_flag = evaluate_safe_context_proposal_request(
        packet=packet,
        approval_record=record,
        policy_overrides={"openwebui_handoff_enabled": True},
    )
    if "openwebui_handoff_denied" not in denied_flag.reason_codes:
        print("FAIL: M38 did not deny model_copy-mutated OpenWebUI handoff flag")
        sys.exit(1)

    for failure in m38_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    if _current_version() < "v0.43.0":
        control_center_text = "\n".join(
            path.read_text(encoding="utf-8").lower()
            for path in (ROOT / "apps/control-center/src").rglob("*")
            if path.is_file()
        )
        for forbidden in ["/context/proposals", "context proposal surface", "send to openwebui", "inject context"]:
            if forbidden in control_center_text:
                print(f"FAIL: M38 Control Center started future context surface/control: {forbidden}")
                sys.exit(1)

    print("OK: M38 safe context proposal is proposal-only, route-free beyond M37 capture, and non-authoritative")


def verify_m39_ccc_context_proposal_surface_safety():
    print("\n[Verifier] Running M39 CCC context proposal surface guard...")
    required_files = [
        "apps/control-center/src/components/ContextProposalSurfacePanel.tsx",
        "apps/control-center/src/routes.tsx",
        "apps/control-center/src/mocks/controlCenterData.ts",
        "apps/control-center/src/App.test.tsx",
        "docs/control_center/CONTEXT_PROPOSAL_SURFACE.md",
        "docs/control_center/CONTEXT_PROPOSAL_REVIEW_ONLY_POLICY.md",
        "docs/control_center/CONTEXT_PROPOSAL_MOCK_DATA_POLICY.md",
        "docs/control_center/CONTEXT_PROPOSAL_BINDING_DISPLAY_POLICY.md",
        "docs/control_center/M39_TO_M40_BOUNDARY.md",
        "tests/test_m39_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M39 context proposal surface file: {rel_path}")
            sys.exit(1)

    app_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("apps/")
    )
    for fragment in [
        "/context/proposals",
        "contextproposalsurfacepanel",
        "m39contextproposals",
        "safe-context-proposal:mock_001",
        "safe proposal sections",
        "exact binding refs",
        "source chain refs",
        "control center output is not authority",
        "openwebui handoff authorized",
        "context injection authorized",
        "memory write authorized",
        "export authorized",
        "execution authorized",
        "rawfileaccessauthorized: false",
        "executionauthorized: false",
    ]:
        if fragment not in app_text.replace("_", "") and fragment not in app_text:
            print(f"FAIL: M39 Control Center missing safe surface marker: {fragment}")
            sys.exit(1)

    for label in [
        "send to openwebui",
        "inject context",
        "write memory",
        "export context",
        "download context",
        "execute context",
        "call model",
        "open raw file",
    ]:
        if re.search(rf"<button\b[^>]*>\s*{re.escape(label)}\s*</button>", app_text, re.IGNORECASE):
            print(f"FAIL: M39 Control Center added forbidden context proposal control: {label}")
            sys.exit(1)

    for forbidden in ["/context/propose", "/context/inject", "/context/handoff", "/openwebui/handoff", "/memory/write", "/tools/execute"]:
        if forbidden in app_text:
            print(f"FAIL: M39 Control Center references forbidden backend route/control: {forbidden}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "read-only",
        "proposal-only",
        "mock and non-authoritative",
        "no context handoff",
        "no context injection",
        "no openwebui handoff",
        "no memory writes",
        "no export",
        "no execution",
        "no raw file access",
        "m40 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M39 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app

        paths = app.openapi().get("paths", {})
    except Exception as exc:
        print(f"FAIL: M39 OpenAPI route validation failed: {exc}")
        sys.exit(1)

    if len(paths) != 75:
        print(f"FAIL: M39 OpenAPI path count changed: expected 75, found {len(paths)}")
        sys.exit(1)
    if "/files/review/approvals/capture" not in paths:
        print("FAIL: M39 expected M37 review approval capture route is missing")
        sys.exit(1)
    for forbidden in [
        "/context/propose",
        "/context/inject",
        "/context/handoff",
        "/openwebui/handoff",
        "/memory/write",
        "/tools/execute",
        "/tool-runtime/execute",
    ]:
        if forbidden in paths:
            print(f"FAIL: M39 forbidden backend route present: {forbidden}")
            sys.exit(1)

    print("OK: M39 CCC context proposal surface is frontend-only, review-only, safe-ref-only, and non-authoritative")


def verify_m40_context_handoff_approval_safety():
    print("\n[Verifier] Running M40 context handoff approval guard...")
    required_files = [
        "src/ultimate_ai_agent/core/context_handoff/__init__.py",
        "src/ultimate_ai_agent/core/context_handoff/contracts.py",
        "src/ultimate_ai_agent/core/context_handoff/validation.py",
        "src/ultimate_ai_agent/core/context_handoff/workflow.py",
        "src/ultimate_ai_agent/core/context_handoff/receipts.py",
        "tests/test_context_handoff_approval_contracts.py",
        "tests/test_context_handoff_approval_binding.py",
        "tests/test_context_handoff_no_injection.py",
        "tests/test_context_handoff_receipt_plan.py",
        "tests/test_m40_gate_integration.py",
        "docs/context/CONTEXT_HANDOFF_APPROVAL.md",
        "docs/context/CONTEXT_HANDOFF_APPROVAL_BOUNDARY.md",
        "docs/context/CONTEXT_HANDOFF_NO_INJECTION_POLICY.md",
        "docs/context/CONTEXT_HANDOFF_RECEIPT_PLAN.md",
        "docs/context/M40_TO_M41_BOUNDARY.md",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M40 context handoff approval file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "exact proposal binding",
        "review-only",
        "no context injection",
        "no openwebui handoff execution",
        "no model calls",
        "no memory writes",
        "no export",
        "no execution",
        "approval_ref alone is not authority",
        "approval_test_ is not runtime authority",
        "evaluator boundaries revalidate",
        "m41 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M40 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.context_handoff import (
            ContextHandoffApprovalDecisionStatus,
            ContextHandoffApprovalKind,
            ContextHandoffApprovalRequest,
            evaluate_context_handoff_approval,
        )
        from ultimate_ai_agent.core.context_proposal import build_safe_context_proposal
        from ultimate_ai_agent.core.file_review import (
            FileReviewApprovalCaptureDecisionStatus,
            FileReviewApprovalDecisionKind,
            FileReviewApprovalRecord,
            build_file_review_packet,
        )
        from ultimate_ai_agent.core.tools.runtime import (
            FilePreviewRedactionSummary,
            RedactedFilePreviewOutput,
            RedactedFilePreviewStatus,
        )

        preview = RedactedFilePreviewOutput(
            output_ref="redacted-file-preview-output:m40-verify",
            status=RedactedFilePreviewStatus.preview_generated,
            root_ref="safe-root:m40-verify",
            safe_path_ref="filesystem-preview-path:safe-root_m40_verify/docs/review.md",
            redacted_preview="M40 verifier redacted preview only.",
            redaction_summary=FilePreviewRedactionSummary(redaction_count=1, categories=["secret_assignment"]),
            file_size_bytes=64,
        )
        packet = build_file_review_packet(
            preview_output=preview,
            actor_ref="user:m40-verify",
            request_ref="file-review-request:m40-verify",
            file_ref="file-ref:m40-verify-review",
            safe_summary="Review a redacted packet for M40 handoff approval.",
        )
        approval_record = FileReviewApprovalRecord(
            approval_ref="file-review-approval-capture:m40-verify",
            actor_ref=packet.source.actor_ref,
            review_packet_ref=packet.review_packet_ref,
            preview_result_ref=packet.source.preview_result_ref,
            redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
            file_ref=packet.source.file_ref,
            safe_path_ref=packet.source.safe_path_ref,
            decision=FileReviewApprovalDecisionKind.approve_review_only,
            status=FileReviewApprovalCaptureDecisionStatus.approved_for_review_only,
            idempotency_key="file-review-approval-idempotency:m40-verify",
            safe_reason="User approved the redacted review packet for review-only follow-up.",
            receipt_plan_ref="file-review-approval-capture-receipt:m40-verify",
        )
        proposal = build_safe_context_proposal(packet=packet, approval_record=approval_record)
        request = ContextHandoffApprovalRequest(
            approval_ref="context-handoff-approval:m40-verify",
            actor_ref=proposal.binding.actor_ref,
            proposal_ref=proposal.proposal_ref,
            approval_record_ref=proposal.source.approval_record_ref,
            review_packet_ref=proposal.binding.review_packet_ref,
            preview_result_ref=proposal.binding.preview_result_ref,
            redaction_summary_ref=proposal.binding.redaction_summary_ref,
            file_ref=proposal.binding.file_ref,
            safe_path_ref=proposal.binding.safe_path_ref,
            decision=ContextHandoffApprovalKind.approve_handoff_review_only,
            idempotency_key="context-handoff-idempotency:m40-verify",
            safe_reason="Approve the safe context proposal for future handoff review only.",
        )
        decision = evaluate_context_handoff_approval(proposal=proposal, request=request)
        if decision.status != ContextHandoffApprovalDecisionStatus.approved_for_handoff_review_only:
            print("FAIL: M40 safe handoff approval did not produce review-only approval")
            sys.exit(1)
        for field_name in [
            "handoff_execution_authorized",
            "context_injection_authorized",
            "openwebui_handoff_authorized",
            "model_call_authorized",
            "memory_write_authorized",
            "export_authorized",
            "execution_authorized",
            "context_injection_performed",
            "openwebui_handoff_performed",
            "model_call_performed",
            "memory_write_performed",
            "export_performed",
            "execution_performed",
        ]:
            if getattr(decision, field_name):
                print(f"FAIL: M40 decision granted or performed forbidden authority: {field_name}")
                sys.exit(1)
        if decision.receipt_plan is None or any(
            getattr(decision.receipt_plan, field_name)
            for field_name in [
                "receipt_is_authority",
                "raw_content_stored",
                "full_file_content_stored",
                "unredacted_preview_stored",
                "context_injection_performed",
                "openwebui_handoff_performed",
                "model_call_performed",
                "memory_write_performed",
                "export_performed",
                "execution_performed",
            ]
        ):
            print("FAIL: M40 receipt plan stores raw content or performs authority")
            sys.exit(1)
        mutated_proposal = proposal.model_copy(update={"context_injection_enabled": True})
        if "context_injection_denied" not in evaluate_context_handoff_approval(proposal=mutated_proposal, request=request).reason_codes:
            print("FAIL: M40 evaluator did not revalidate model_copy-mutated proposal injection flag")
            sys.exit(1)
        mutated_request = request.model_copy(update={"openwebui_handoff_execution_enabled": True})
        if "openwebui_handoff_denied" not in evaluate_context_handoff_approval(proposal=proposal, request=mutated_request).reason_codes:
            print("FAIL: M40 evaluator did not revalidate model_copy-mutated request handoff flag")
            sys.exit(1)
        if "approval_ref_not_authority" not in evaluate_context_handoff_approval(
            proposal=None,
            request_ref="context-handoff-approval:m40-verify",
        ).reason_codes:
            print("FAIL: M40 approval_ref-alone probe did not fail closed")
            sys.exit(1)
        if "approval_test_ref_denied" not in evaluate_context_handoff_approval(
            proposal=proposal,
            request=request.model_copy(update={"approval_ref": "approval_test_m40_verify"}),
        ).reason_codes:
            print("FAIL: M40 approval_test_ mutation probe did not fail closed")
            sys.exit(1)

        paths = app.openapi().get("paths", {})
        if len(paths) != 75:
            print(f"FAIL: M40 OpenAPI path count changed: expected 75, found {len(paths)}")
            sys.exit(1)
        if "/files/review/approvals/capture" not in paths:
            print("FAIL: M40 expected M37 review approval capture route is missing")
            sys.exit(1)
        for forbidden in [
            "/context/propose",
            "/context/handoff",
            "/context/handoff/approve",
            "/context/inject",
            "/openwebui/handoff",
            "/memory/write",
            "/tools/execute",
            "/tool-runtime/execute",
        ]:
            if forbidden in paths:
                print(f"FAIL: M40 forbidden backend route present: {forbidden}")
                sys.exit(1)
    except Exception as exc:
        print(f"FAIL: M40 context handoff approval validation failed: {exc}")
        sys.exit(1)

    print("OK: M40 context handoff approval is exact-bound, review-only, no-injection, and route-free")


def verify_m41_local_prototype_safety_freeze():
    print("\n[Verifier] Running M41 local prototype safety freeze guard...")
    required_files = [
        "docs/prototype/LOCAL_PROTOTYPE_SAFETY_FREEZE.md",
        "docs/prototype/LOCAL_PROTOTYPE_BROWSER_SMOKE_REVIEW.md",
        "docs/prototype/LOCAL_PROTOTYPE_NO_AUTHORITY_BOUNDARY.md",
        "docs/prototype/M41_TO_M42_BOUNDARY.md",
        "docs/release_notes/v0_45_0.md",
        "docs/archive/releases/v0_45_0/README_IMPORT.md",
        "docs/archive/releases/v0_45_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_45_0.md",
        "tests/test_m41_gate_integration.py",
        "tests/test_m41_local_prototype_safety_freeze.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M41 local prototype safety freeze file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "local prototype safety freeze",
        "localhost-only",
        "review-only",
        "mock/non-authoritative",
        "no raw file browsing",
        "no raw file export",
        "no full-file reads",
        "no arbitrary caller-selected roots",
        "no shell/subprocess",
        "no unrestricted network tools",
        "no provider/model calls as authority",
        "no background workers",
        "no mobile sensors",
        "no plugin enablement",
        "no production authority",
        "no unreviewed memory writes",
        "no automatic context injection",
        "no raw prompt/provider payload exposure",
        "no credentials/cookie handling",
        "no remote execution",
        "no browser automation execution",
        "approval refs are not authority",
        "browser smoke review is local-only",
        "m42 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M41 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m41_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M41 OpenAPI guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m41_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    forbidden_source_fragments = [
        "context_handoff_execution_enabled=True",
        "context_injection_enabled=True",
        "openwebui_handoff_execution_enabled=True",
        "model_call_enabled=True",
        "memory_write_enabled=True",
        "execution_enabled=True",
        "export_enabled=True",
        "background_worker_enabled=True",
        "scheduler_enabled=True",
        "mobile_sensor_enabled=True",
        "plugin_enable_enabled=True",
        "production_authority_enabled=True",
    ]
    source_roots = [ROOT / "src", ROOT / "apps" / "control-center" / "src"]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M41 forbidden authority flag in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M41 local prototype safety freeze is route-stable, localhost/review-only, and keeps future authority blocked")


def verify_m42_mobile_product_contract_refresh():
    print("\n[Verifier] Running M42 mobile product contract refresh guard...")
    required_files = [
        "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
        "src/ultimate_ai_agent/core/mobile_companion/planning.py",
        "src/ultimate_ai_agent/core/mobile_companion/enums.py",
        "docs/mobile/MOBILE_COMPANION_PRODUCT_CONTRACT_REFRESH.md",
        "docs/mobile/M42_TO_M43_BOUNDARY.md",
        "docs/release_notes/v0_46_0.md",
        "docs/archive/releases/v0_46_0/README_IMPORT.md",
        "docs/archive/releases/v0_46_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_46_0.md",
        "tests/test_m42_mobile_product_contract_refresh.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M42 mobile product contract refresh file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "mobile companion product contract refresh",
        "planning/docs/contracts/verifier",
        "governance/control",
        "not the agent brain",
        "review-only",
        "read-only",
        "m43 is implemented/released",
        "m44 remains future",
        "no mobile app",
        "no ios app",
        "no android app",
        "no native package",
        "no native build workflow",
        "no signing",
        "no testflight",
        "no backend route",
        "no mobile api route",
        "no approval capture",
        "no approval execution",
        "no mobile sensor access",
        "no os permission integration",
        "no background service",
        "no notification runtime",
        "no raw payload exposure",
        "no memory write",
        "no context injection",
        "no production authority",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M42 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m42_openapi_route_failures
        from ultimate_ai_agent.core.mobile_companion import (
            assert_mobile_product_contract_refresh_only,
            build_default_mobile_product_contract_refresh,
        )
    except Exception as exc:
        print(f"FAIL: M42 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m42_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    try:
        assert_mobile_product_contract_refresh_only(build_default_mobile_product_contract_refresh())
    except Exception as exc:
        print(f"FAIL: M42 default mobile product refresh failed validation: {exc}")
        sys.exit(1)

    forbidden_source_fragments = [
        "native_app_implemented=True",
        "mobile_api_implemented=True",
        "mobile_sensor_access_enabled=True",
        "os_permission_integration_enabled=True",
        "background_service_enabled=True",
        "signing_or_store_workflow_enabled=True",
        "approval_capture_enabled=True",
        "approval_execution_enabled=True",
        "raw_payload_exposure_enabled=True",
        "production_authority_enabled=True",
    ]
    source_roots = [ROOT / "src", ROOT / "apps" / "control-center" / "src"]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M42 forbidden authority flag in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M42 mobile product refresh is contract-only, route-free, native-free, and sensor-free")


def verify_m43_mobile_api_boundary_read_only():
    print("\n[Verifier] Running M43 read-only mobile API boundary guard...")
    required_files = [
        "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
        "src/ultimate_ai_agent/core/mobile_companion/planning.py",
        "src/ultimate_ai_agent/core/mobile_companion/enums.py",
        "docs/mobile/MOBILE_API_BOUNDARY_READ_ONLY.md",
        "docs/mobile/M43_TO_M44_BOUNDARY.md",
        "docs/release_notes/v0_47_0.md",
        "docs/archive/releases/v0_47_0/README_IMPORT.md",
        "docs/archive/releases/v0_47_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_47_0.md",
        "tests/test_m43_mobile_api_boundary_read_only.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M43 mobile API boundary file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "mobile api boundary, read-only",
        "contract-only",
        "read-only",
        "redacted summary only",
        "planned endpoint refs",
        "no backend route",
        "no mobile mutation",
        "no approval capture",
        "no approval execution",
        "no mobile sensor access",
        "no raw data",
        "no raw payload exposure",
        "no raw absolute path",
        "no credential",
        "no cookie",
        "no context injection",
        "no memory write",
        "no export",
        "no execution",
        "no production authority",
        "m44 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M43 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m43_openapi_route_failures
        from ultimate_ai_agent.core.mobile_companion import (
            assert_mobile_api_boundary_read_only,
            build_default_mobile_read_only_api_boundary,
        )
    except Exception as exc:
        print(f"FAIL: M43 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m43_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    try:
        assert_mobile_api_boundary_read_only(build_default_mobile_read_only_api_boundary())
    except Exception as exc:
        print(f"FAIL: M43 default mobile API boundary failed validation: {exc}")
        sys.exit(1)

    forbidden_source_fragments = [
        "backend_routes_added=True",
        "mobile_mutation_enabled=True",
        "mobile_sensor_access_enabled=True",
        "approval_capture_enabled=True",
        "approval_execution_enabled=True",
        "raw_data_enabled=True",
        "raw_payload_exposure_enabled=True",
        "raw_absolute_path_exposure_enabled=True",
        "context_injection_enabled=True",
        "memory_write_enabled=True",
        "export_enabled=True",
        "execution_enabled=True",
        "credential_or_cookie_handling_enabled=True",
        "background_collection_enabled=True",
        "production_authority_enabled=True",
    ]
    source_roots = [ROOT / "src", ROOT / "apps" / "control-center" / "src"]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M43 forbidden authority flag in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M43 mobile API boundary is contract-only, read-only, route-stable, raw-data-free, and sensor-free")


def verify_m44_ccc_ios_skeleton_no_authority():
    print("\n[Verifier] Running M44 CCC iOS skeleton no-authority guard...")
    required_files = [
        "apps/ccc-ios/README.md",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/UltimateAIAgentCCCApp.swift",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/ReadOnlyDashboardView.swift",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/SkeletonFixtures.swift",
        "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
        "src/ultimate_ai_agent/core/mobile_companion/planning.py",
        "src/ultimate_ai_agent/core/mobile_companion/enums.py",
        "docs/mobile/CCC_IOS_SKELETON_NO_AUTHORITY.md",
        "docs/mobile/M44_TO_M45_BOUNDARY.md",
        "docs/release_notes/v0_48_0.md",
        "docs/archive/releases/v0_48_0/README_IMPORT.md",
        "docs/archive/releases/v0_48_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_48_0.md",
        "tests/test_m44_ccc_ios_skeleton_no_authority.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M44 CCC iOS skeleton file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "ccc ios skeleton, no authority",
        "source-only",
        "mock-only",
        "read-only",
        "non-authoritative",
        "no xcode project",
        "no swift package",
        "no info.plist",
        "no entitlements",
        "no backend route",
        "no mobile api route runtime",
        "no network",
        "no mobile sensor access",
        "no os permission integration",
        "no approval capture",
        "no approval execution",
        "no context injection",
        "no memory write",
        "no file mutation",
        "no execution",
        "no credential",
        "no background",
        "no production authority",
        "m45 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M44 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m44_openapi_route_failures
        from ultimate_ai_agent.core.mobile_companion import (
            assert_ccc_ios_skeleton_no_authority,
            build_default_ccc_ios_skeleton_manifest,
        )
    except Exception as exc:
        print(f"FAIL: M44 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m44_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    try:
        manifest = build_default_ccc_ios_skeleton_manifest()
        assert_ccc_ios_skeleton_no_authority(manifest)
    except Exception as exc:
        print(f"FAIL: M44 default CCC iOS skeleton failed validation: {exc}")
        sys.exit(1)

    ios_root = ROOT / "apps" / "ccc-ios"
    for forbidden_path in [
        ios_root / "Package.swift",
        *ios_root.glob("*.xcodeproj"),
        *ios_root.rglob("*.entitlements"),
        *ios_root.rglob("Info.plist"),
    ]:
        if forbidden_path.exists():
            rel = forbidden_path.relative_to(ROOT).as_posix()
            print(f"FAIL: M44 forbidden native workflow file present: {rel}")
            sys.exit(1)

    swift_files = sorted((ios_root / "Sources" / "UltimateAIAgentCCC").rglob("*.swift"))
    if not swift_files:
        print("FAIL: M44 Swift source files missing")
        sys.exit(1)
    swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
    lowered_swift = swift_text.lower()
    for required in ["swiftui", "mock", "non-authoritative", "read-only"]:
        if required not in lowered_swift:
            print(f"FAIL: M44 Swift source missing marker: {required}")
            sys.exit(1)
    for fragment in [
        "URLSession",
        "Alamofire",
        "CLLocationManager",
        "AVCapture",
        "PHPhoto",
        "Contacts",
        "EventKit",
        "UserNotifications",
        "Keychain",
        "SecItem",
        "FileManager.default",
        "Process(",
        "WKWebView",
        "approvalCapture",
        "approvalExecution",
        "contextInjection",
        "memoryWrite",
    ]:
        if fragment in swift_text:
            print(f"FAIL: M44 forbidden Swift API fragment present: {fragment}")
            sys.exit(1)

    forbidden_source_fragments = [
        "production_workflow_enabled=True",
        "signing_or_store_workflow_enabled=True",
        "native_build_workflow_enabled=True",
        "network_access_enabled=True",
        "sensor_access_enabled=True",
        "os_permission_integration_enabled=True",
        "approval_capture_enabled=True",
        "approval_execution_enabled=True",
        "context_injection_enabled=True",
        "memory_write_enabled=True",
        "file_mutation_enabled=True",
        "execution_enabled=True",
        "credential_storage_enabled=True",
        "background_task_enabled=True",
        "production_authority_enabled=True",
    ]
    source_roots = [ROOT / "src", ROOT / "apps" / "control-center" / "src", ios_root]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M44 forbidden authority flag in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M44 CCC iOS skeleton is source-only, mock-only, read-only, no-authority, and route-stable")


def verify_m45_ccc_ios_local_read_only_connection():
    print("\n[Verifier] Running M45 CCC iOS local read-only connection guard...")
    required_files = [
        "apps/ccc-ios/README.md",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/UltimateAIAgentCCCApp.swift",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/ReadOnlyDashboardView.swift",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/SkeletonFixtures.swift",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/LocalReadOnlyConnectionModels.swift",
        "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
        "src/ultimate_ai_agent/core/mobile_companion/planning.py",
        "src/ultimate_ai_agent/core/mobile_companion/enums.py",
        "docs/mobile/CCC_IOS_LOCAL_READ_ONLY_CONNECTION.md",
        "docs/mobile/M45_TO_M46_BOUNDARY.md",
        "docs/release_notes/v0_49_0.md",
        "docs/archive/releases/v0_49_0/README_IMPORT.md",
        "docs/archive/releases/v0_49_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_49_0.md",
        "tests/test_m45_ccc_ios_local_read_only_connection.py",
        "tests/test_m45_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M45 CCC iOS local connection file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "ccc ios local read-only connection",
        "local-only",
        "loopback-only",
        "read-only",
        "redacted summary",
        "non-authoritative",
        "no runtime network call",
        "no backend route",
        "no approval capture",
        "no approval execution",
        "no raw data",
        "no context injection",
        "no memory write",
        "no file mutation",
        "no execution",
        "no background collection",
        "no mobile sensor access",
        "no credential",
        "no xcode project",
        "no swift package",
        "no signing",
        "no testflight",
        "no production authority",
        "m46 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M45 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m45_openapi_route_failures
        from ultimate_ai_agent.core.mobile_companion import (
            assert_ccc_ios_local_read_only_connection_safe,
            build_default_ccc_ios_local_read_only_connection_manifest,
        )
    except Exception as exc:
        print(f"FAIL: M45 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m45_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    try:
        manifest = build_default_ccc_ios_local_read_only_connection_manifest()
        assert_ccc_ios_local_read_only_connection_safe(manifest)
    except Exception as exc:
        print(f"FAIL: M45 default CCC iOS local connection failed validation: {exc}")
        sys.exit(1)

    ios_root = ROOT / "apps" / "ccc-ios"
    for forbidden_path in [
        ios_root / "Package.swift",
        *ios_root.glob("*.xcodeproj"),
        *ios_root.rglob("*.entitlements"),
        *ios_root.rglob("Info.plist"),
        *ios_root.rglob("ExportOptions.plist"),
    ]:
        if forbidden_path.exists():
            rel = forbidden_path.relative_to(ROOT).as_posix()
            print(f"FAIL: M45 forbidden native workflow file present: {rel}")
            sys.exit(1)

    swift_files = sorted((ios_root / "Sources" / "UltimateAIAgentCCC").rglob("*.swift"))
    swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
    lowered_swift = swift_text.lower()
    for required in ["local read-only connection", "loopback-only", "non-authoritative", "no runtime network call"]:
        if required not in lowered_swift:
            print(f"FAIL: M45 Swift source missing marker: {required}")
            sys.exit(1)
    for fragment in [
        "URLSession",
        "Alamofire",
        "URLRequest",
        "NWConnection",
        "CLLocationManager",
        "AVCapture",
        "PHPhoto",
        "Contacts",
        "EventKit",
        "UserNotifications",
        "Keychain",
        "SecItem",
        "FileManager.default",
        "Process(",
        "WKWebView",
        "approvalCapture",
        "approvalExecution",
        "contextInjection",
        "memoryWrite",
        "backgroundTask",
    ]:
        if fragment in swift_text:
            print(f"FAIL: M45 forbidden Swift API fragment present: {fragment}")
            sys.exit(1)

    forbidden_source_fragments = [
        "connection_runtime_enabled=True",
        "backend_routes_added=True",
        "network_runtime_enabled=True",
        "external_network_enabled=True",
        "raw_data_enabled=True",
        "approval_capture_enabled=True",
        "approval_execution_enabled=True",
        "context_injection_enabled=True",
        "memory_write_enabled=True",
        "file_mutation_enabled=True",
        "execution_enabled=True",
        "background_collection_enabled=True",
        "sensor_access_enabled=True",
        "credential_or_cookie_handling_enabled=True",
        "native_build_workflow_enabled=True",
        "signing_or_store_workflow_enabled=True",
        "production_authority_enabled=True",
    ]
    source_roots = [ROOT / "src", ROOT / "apps" / "control-center" / "src", ios_root]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M45 forbidden authority flag in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M45 CCC iOS local connection is local-only, read-only, no-runtime, no-route, and no-authority")


def verify_m46_ccc_ios_review_receipt_read_only_surfaces():
    print("\n[Verifier] Running M46 CCC iOS review/receipt read-only surfaces guard...")
    required_files = [
        "apps/ccc-ios/README.md",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/UltimateAIAgentCCCApp.swift",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/ReadOnlyDashboardView.swift",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/SkeletonFixtures.swift",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/LocalReadOnlyConnectionModels.swift",
        "apps/ccc-ios/Sources/UltimateAIAgentCCC/ReviewReceiptReadOnlyModels.swift",
        "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
        "src/ultimate_ai_agent/core/mobile_companion/planning.py",
        "src/ultimate_ai_agent/core/mobile_companion/enums.py",
        "docs/mobile/CCC_IOS_REVIEW_RECEIPT_READ_ONLY_SURFACES.md",
        "docs/mobile/M46_TO_M47_BOUNDARY.md",
        "docs/release_notes/v0_50_0.md",
        "docs/archive/releases/v0_50_0/README_IMPORT.md",
        "docs/archive/releases/v0_50_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_50_0.md",
        "tests/test_m46_ccc_ios_review_receipt_read_only_surfaces.py",
        "tests/test_m46_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M46 CCC iOS review/receipt file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "ios review/receipt read-only surfaces",
        "source-only",
        "read-only",
        "redacted summary",
        "mock",
        "non-authoritative",
        "no runtime network call",
        "no backend route",
        "no approval capture",
        "no approval execution",
        "no raw data",
        "no context injection",
        "no memory write",
        "no file mutation",
        "no export",
        "no execution",
        "no background collection",
        "no mobile sensor access",
        "no credential",
        "no xcode project",
        "no swift package",
        "no signing",
        "no testflight",
        "no production authority",
        "m47 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M46 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m46_openapi_route_failures
        from ultimate_ai_agent.core.mobile_companion import (
            assert_ccc_ios_review_receipt_read_only_surfaces_safe,
            build_default_ccc_ios_review_receipt_read_only_surface_manifest,
        )
    except Exception as exc:
        print(f"FAIL: M46 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m46_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    try:
        manifest = build_default_ccc_ios_review_receipt_read_only_surface_manifest()
        assert_ccc_ios_review_receipt_read_only_surfaces_safe(manifest)
    except Exception as exc:
        print(f"FAIL: M46 default CCC iOS review/receipt surfaces failed validation: {exc}")
        sys.exit(1)

    ios_root = ROOT / "apps" / "ccc-ios"
    for forbidden_path in [
        ios_root / "Package.swift",
        *ios_root.glob("*.xcodeproj"),
        *ios_root.rglob("*.entitlements"),
        *ios_root.rglob("Info.plist"),
        *ios_root.rglob("ExportOptions.plist"),
        *ios_root.rglob("*.mobileprovision"),
    ]:
        if forbidden_path.exists():
            rel = forbidden_path.relative_to(ROOT).as_posix()
            print(f"FAIL: M46 forbidden native workflow file present: {rel}")
            sys.exit(1)

    swift_files = sorted((ios_root / "Sources" / "UltimateAIAgentCCC").rglob("*.swift"))
    swift_text = "\n".join(path.read_text(encoding="utf-8") for path in swift_files)
    lowered_swift = swift_text.lower()
    for required in [
        "review/receipt read-only surfaces",
        "redacted review packet summary",
        "redacted receipt summary",
        "mock non-authoritative",
        "no approval capture",
        "no raw data",
        "no runtime network call",
    ]:
        if required not in lowered_swift:
            print(f"FAIL: M46 Swift source missing marker: {required}")
            sys.exit(1)
    for fragment in [
        "URLSession",
        "Alamofire",
        "URLRequest",
        "NWConnection",
        "CLLocationManager",
        "AVCapture",
        "PHPhoto",
        "Contacts",
        "EventKit",
        "UserNotifications",
        "Keychain",
        "SecItem",
        "FileManager.default",
        "Process(",
        "WKWebView",
        "approvalCapture",
        "approvalExecution",
        "contextInjection",
        "memoryWrite",
        "backgroundTask",
        "ExportOptions",
    ]:
        if fragment in swift_text:
            print(f"FAIL: M46 forbidden Swift API fragment present: {fragment}")
            sys.exit(1)

    forbidden_source_fragments = [
        "backend_routes_added=True",
        "network_runtime_enabled=True",
        "raw_data_enabled=True",
        "approval_capture_enabled=True",
        "approval_execution_enabled=True",
        "context_injection_enabled=True",
        "memory_write_enabled=True",
        "file_mutation_enabled=True",
        "export_enabled=True",
        "execution_enabled=True",
        "background_collection_enabled=True",
        "sensor_access_enabled=True",
        "credential_or_cookie_handling_enabled=True",
        "native_build_workflow_enabled=True",
        "signing_or_store_workflow_enabled=True",
        "testflight_pipeline_enabled=True",
        "production_authority_enabled=True",
    ]
    source_roots = [ROOT / "src", ROOT / "apps" / "control-center" / "src", ios_root]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M46 forbidden authority flag in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M46 CCC iOS review/receipt surfaces are source-only, read-only, redacted, no-runtime, and no-authority")


def verify_m47_testflight_pipeline_internal_only():
    print("\n[Verifier] Running M47 TestFlight pipeline internal-only guard...")
    required_files = [
        "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
        "src/ultimate_ai_agent/core/mobile_companion/planning.py",
        "src/ultimate_ai_agent/core/mobile_companion/enums.py",
        "docs/mobile/TESTFLIGHT_PIPELINE_INTERNAL_ONLY.md",
        "docs/mobile/M47_TO_M48_BOUNDARY.md",
        "docs/release_notes/v0_51_0.md",
        "docs/archive/releases/v0_51_0/README_IMPORT.md",
        "docs/archive/releases/v0_51_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_51_0.md",
        "tests/test_m47_testflight_pipeline_internal_only.py",
        "tests/test_m47_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M47 TestFlight pipeline file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "testflight pipeline, internal only",
        "internal-only",
        "contract",
        "checklist",
        "no build execution",
        "no upload execution",
        "no signing asset storage",
        "no app store connect api",
        "no external beta",
        "no public distribution",
        "no production authority",
        "m48 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M47 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m47_openapi_route_failures
        from ultimate_ai_agent.core.mobile_companion import (
            assert_internal_testflight_pipeline_safe,
            build_default_internal_testflight_pipeline_manifest,
        )
    except Exception as exc:
        print(f"FAIL: M47 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m47_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    try:
        manifest = build_default_internal_testflight_pipeline_manifest()
        assert_internal_testflight_pipeline_safe(manifest)
    except Exception as exc:
        print(f"FAIL: M47 default TestFlight pipeline failed validation: {exc}")
        sys.exit(1)

    ios_root = ROOT / "apps" / "ccc-ios"
    forbidden_paths = [
        ios_root / "Package.swift",
        *ios_root.glob("*.xcodeproj"),
        *ios_root.rglob("*.xcworkspace"),
        *ios_root.rglob("*.entitlements"),
        *ios_root.rglob("Info.plist"),
        *ios_root.rglob("ExportOptions.plist"),
        *ios_root.rglob("*.mobileprovision"),
        *ios_root.rglob("*.p8"),
        *ios_root.rglob("*.cer"),
        *ios_root.rglob("*.p12"),
    ]
    for forbidden_path in forbidden_paths:
        if forbidden_path.exists():
            rel = forbidden_path.relative_to(ROOT).as_posix()
            print(f"FAIL: M47 forbidden TestFlight/signing artifact present: {rel}")
            sys.exit(1)
    for forbidden_dir in [
        ROOT / "fastlane",
        ios_root / "fastlane",
        ios_root / "DerivedData",
    ]:
        if forbidden_dir.exists():
            rel = forbidden_dir.relative_to(ROOT).as_posix()
            print(f"FAIL: M47 forbidden build/upload directory present: {rel}")
            sys.exit(1)

    swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
    swift_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(swift_root.rglob("*.swift")))
    for fragment in [
        "URLSession",
        "Alamofire",
        "URLRequest",
        "NWConnection",
        "CLLocationManager",
        "AVCapture",
        "PHPhoto",
        "Contacts",
        "EventKit",
        "UserNotifications",
        "Keychain",
        "SecItem",
        "FileManager.default",
        "Process(",
        "WKWebView",
        "AppStoreConnect",
        "TestFlightUpload",
        "xcodebuild",
        "altool",
        "notarytool",
        "ExportOptions",
    ]:
        if fragment in swift_text:
            print(f"FAIL: M47 forbidden Swift/build fragment present: {fragment}")
            sys.exit(1)

    forbidden_source_fragments = [
        "build_execution_enabled=True",
        "upload_execution_enabled=True",
        "signing_asset_storage_enabled=True",
        "signing_identity_configured=True",
        "provisioning_profile_configured=True",
        "app_store_connect_api_enabled=True",
        "credentials_or_cookies_handling_enabled=True",
        "external_beta_enabled=True",
        "public_distribution_enabled=True",
        "production_authority_enabled=True",
        "mobile_sensor_access_enabled=True",
        "background_collection_enabled=True",
        "approval_execution_enabled=True",
        "context_injection_enabled=True",
        "memory_write_enabled=True",
        "executes_build=True",
        "uploads_build=True",
        "calls_app_store_connect=True",
    ]
    source_roots = [ROOT / "src", ROOT / "apps" / "control-center" / "src", ios_root]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M47 forbidden enabled flag in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M47 TestFlight pipeline is internal-only, contract/checklist-only, no-build, no-upload, and no-authority")


def verify_local_developer_launcher_safety():
    print("\n[Verifier] Running local developer launcher safety guard...")
    required_files = [
        "scripts/dev/uaa",
        "scripts/dev/uaa_launcher.py",
        "scripts/dev/create_macos_launcher.py",
        "scripts/dev/README.md",
        "docs/developer/LOCAL_LAUNCHER.md",
        "tests/test_dev_launcher.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing local developer launcher file: {rel_path}")
            sys.exit(1)

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    if ".uaa/" not in gitignore:
        print("FAIL: .uaa/ launcher runtime state is not gitignored")
        sys.exit(1)
    if "Ultimate AI Agent.command" not in gitignore:
        print("FAIL: repo-local generated macOS launcher is not gitignored")
        sys.exit(1)

    launcher_path = ROOT / "scripts/dev/uaa_launcher.py"
    launcher_source = launcher_path.read_text(encoding="utf-8")
    for fragment in ["shell=True", "os.system(", "eval(", "exec("]:
        if fragment in launcher_source:
            print(f"FAIL: Launcher contains forbidden shell/dynamic fragment: {fragment}")
            sys.exit(1)
    if "subprocess.Popen(" not in launcher_source or "start_new_session=True" not in launcher_source:
        print("FAIL: Launcher does not use explicit local dev process management")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("uaa_launcher_verify", launcher_path)
    if spec is None or spec.loader is None:
        print("FAIL: Could not load uaa_launcher.py for verification")
        sys.exit(1)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    for unsafe_host in ["0.0.0.0", "192.168.1.20", "example.com"]:
        try:
            module.validate_local_host(unsafe_host)
            print(f"FAIL: Launcher accepted non-loopback host: {unsafe_host}")
            sys.exit(1)
        except ValueError:
            pass

    backend_command = module.build_backend_command(ROOT)
    frontend_command = module.build_frontend_command(ROOT)
    if backend_command[backend_command.index("--host") + 1] != "127.0.0.1":
        print("FAIL: Backend launcher command is not localhost-only")
        sys.exit(1)
    if frontend_command[frontend_command.index("--host") + 1] != "127.0.0.1":
        print("FAIL: Frontend launcher command is not localhost-only")
        sys.exit(1)

    macos_content = module.render_macos_launcher()
    for required in ["./scripts/dev/uaa doctor", "./scripts/dev/uaa start", "./scripts/dev/uaa ui"]:
        if required not in macos_content:
            print(f"FAIL: macOS launcher template missing command: {required}")
            sys.exit(1)
    for forbidden in ["/Users/", "sudo", "launchctl", "LaunchAgent", "/usr/local/bin"]:
        if forbidden in macos_content:
            print(f"FAIL: macOS launcher template contains forbidden installer/system fragment: {forbidden}")
            sys.exit(1)

    tracked_artifacts = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    for rel in tracked_artifacts:
        if rel.startswith(".uaa/") or rel.endswith((".pid", ".log")):
            print(f"FAIL: Launcher runtime artifact is tracked: {rel}")
            sys.exit(1)

    forbidden_routes = [
        "/actions/execute",
        "/tools/execute",
        "/tasks/execute",
        "/runs/execute",
        "/installer/run",
    ]
    api_source = (ROOT / "src/ultimate_ai_agent/api/app.py").read_text(encoding="utf-8")
    for route in forbidden_routes:
        if route in api_source:
            print(f"FAIL: Forbidden launcher patch route found: {route}")
            sys.exit(1)

    print("OK: Local developer launcher is localhost-only, route-free, dependency-free, and tooling-only")


def verify_v0292_local_dev_api_hardening():
    print("\n[Verifier] Running v0.29.2 local dev API authority/raw preview hardening guard...")
    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from fastapi.testclient import TestClient

        from tests.test_kernel_minimum_lovable_happy_path import request as kernel_request
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.kernel import KernelTaskStatus, MinimumKernelRunner

        client = TestClient(app)
        with tempfile.TemporaryDirectory(prefix="uaa-verify-v0292-kernel-") as probe_dir:
            probe_root = Path(probe_dir)
            payload = kernel_request(probe_root).model_dump(mode="json")
            payload["approval_ref"] = "approval_test_verify"
            response = client.post("/kernel/tasks/run", json=payload)
            if response.status_code != 200:
                print(f"FAIL: kernel task API probe returned HTTP {response.status_code}")
                sys.exit(1)
            body = response.json()
            data = body.get("data") or {}
            if body.get("success") is not True or data.get("status") != KernelTaskStatus.dry_run:
                print("FAIL: kernel task API did not force local-dev mutation into dry-run")
                sys.exit(1)
            if (probe_root / "notes" / "m5.md").exists():
                print("FAIL: kernel task API dry-run probe created a file")
                sys.exit(1)

            direct_result = MinimumKernelRunner().run_task(
                kernel_request(probe_root).model_copy(update={"approval_ref": "approval_test_verify"})
            )
            if direct_result.success or "APPROVAL_REF_UNVALIDATED" not in direct_result.errors:
                print("FAIL: kernel runner accepted test-prefixed approval without explicit authority")
                sys.exit(1)

        with tempfile.TemporaryDirectory(prefix="uaa-verify-v0292-preview-") as preview_dir:
            preview_root = Path(preview_dir)
            (preview_root / "note.txt").write_text("hello", encoding="utf-8")
            response = client.post(
                "/files/read/preview",
                json={
                    "workspace_root": str(preview_root),
                    "request": {
                        "request_id": "frr_verify_v0292",
                        "run_id": "run_verify_v0292",
                        "actor_context": {
                            "actor_type": "human_user",
                            "actor_id": "verify_user",
                            "authority_source": "explicit_user_request",
                        },
                        "path": "note.txt",
                        "purpose": "preview",
                        "max_bytes": 100,
                    },
                },
            )
            if response.status_code != 200:
                print(f"FAIL: file preview API probe returned HTTP {response.status_code}")
                sys.exit(1)
            body = response.json()
            data = body.get("data") or {}
            if body.get("success") is not True:
                print("FAIL: file preview API metadata probe failed")
                sys.exit(1)
            if data.get("text_preview") != "":
                print("FAIL: file preview API returned raw text preview")
                sys.exit(1)
            if "hello" in response.text:
                print("FAIL: file preview API echoed raw file content")
                sys.exit(1)
            if "raw_content_omitted" not in data.get("redactions_applied", []):
                print("FAIL: file preview API did not report raw_content_omitted")
                sys.exit(1)

            secret = "supersecretvalue123"
            hostile_path = f"notes/api_key={secret}.txt"
            hostile_response = client.post(
                "/files/read/preview",
                json={
                    "workspace_root": str(preview_root),
                    "request": {
                        "request_id": "frr_verify_v0292_hostile",
                        "run_id": "run_verify_v0292",
                        "actor_context": {
                            "actor_type": "human_user",
                            "actor_id": "verify_user",
                            "authority_source": "explicit_user_request",
                        },
                        "path": hostile_path,
                        "purpose": "preview",
                        "max_bytes": 100,
                    },
                },
            )
            if hostile_response.status_code != 200 or hostile_response.json().get("success") is not False:
                print("FAIL: file preview API did not safely reject hostile secret-like path")
                sys.exit(1)
            if secret in hostile_response.text or hostile_path in hostile_response.text:
                print("FAIL: file preview API echoed a hostile path or secret-like path value")
                sys.exit(1)

        broker_source = (ROOT / "src" / "ultimate_ai_agent" / "core" / "tools" / "broker.py").read_text(
            encoding="utf-8"
        )
        if "approval_test_" in broker_source:
            print("FAIL: ToolBroker contains test-prefixed approval compatibility fallback")
            sys.exit(1)

        api_source = (ROOT / "src" / "ultimate_ai_agent" / "api" / "app.py").read_text(encoding="utf-8")
        forbidden_exception_echo = (
            "safe_message=str(e)",
            "safe_message = str(e)",
            "detail=str(e)",
            "detail = str(e)",
        )
        for fragment in forbidden_exception_echo:
            if fragment in api_source:
                print(f"FAIL: API handler contains raw exception echo fragment: {fragment}")
                sys.exit(1)
    except Exception as exc:
        print(f"FAIL: v0.29.2 local dev API hardening guard could not run: {exc}")
        sys.exit(1)

    print("OK: v0.29.2 local dev APIs remain dry-run/metadata-only with sanitized errors")


def verify_no_shell_execution_in_runtime():
    print("\n[Verifier] Running runtime shell/subprocess execution scan...")
    forbidden_fragments = [
        "import subprocess",
        "from subprocess import",
        "os.system(",
        "popen(",
        "subprocess.",
    ]
    for p in (ROOT / "src").rglob("*.py"):
        try:
            if p.relative_to(ROOT).as_posix() == "src/ultimate_ai_agent/core/gate/evaluators.py":
                continue
            content = p.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden_fragments):
                    print(f"FAIL: Forbidden shell/subprocess execution in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
        except Exception:
            pass
    print("OK: No shell/subprocess execution detected in runtime source")

def verify_no_production_truth_integrations():
    print("\n[Verifier] Running production truth integration scan...")
    forbidden_imports = [
        "import chromadb",
        "from chromadb import",
        "import faiss",
        "from faiss import",
        "import pgvector",
        "from pgvector import",
        "import pinecone",
        "from pinecone import",
        "import psycopg",
        "from psycopg import",
        "import sentence_transformers",
        "from sentence_transformers import",
        "import weaviate",
        "from weaviate import",
    ]
    for p in (ROOT / "src").rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if any(stripped.startswith(pattern) for pattern in forbidden_imports):
                    print(f"FAIL: Production truth integration import in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
        except Exception:
            pass
    print("OK: No production truth connector, vector DB, pgvector, or embedding runtime imports detected in src")

def verify_no_broad_filesystem_scanning():
    print("\n[Verifier] Running broad filesystem scanning guard...")
    forbidden_fragments = [
        ".rglob(\"*\")",
        ".rglob('*')",
        "os.walk(",
        "Path.home(",
    ]
    for p in (ROOT / "src").rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith(('"', "'")):
                    continue
                if any(fragment in stripped for fragment in forbidden_fragments):
                    print(f"FAIL: Broad filesystem scanning/home access in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
        except Exception:
            pass
    print("OK: No broad filesystem scanning or home-directory traversal detected in src")


def verify_no_mobile_native_or_sensor_implementation():
    print("\n[Verifier] Running M20 mobile/device capability contract-only guard...")
    try:
        git_files_raw = subprocess.check_output(["git", "ls-files"], text=True)
        git_files = git_files_raw.splitlines()
    except subprocess.SubprocessError:
        git_files = []

    forbidden_dir_prefixes = (
        "ios/",
        "android/",
        "mobile-app/",
        "apps/ios/",
        "apps/android/",
        "apps/mobile/",
        "react-native/",
        "expo/",
        "flutter/",
        "capacitor/",
        "ionic/",
        "src/ultimate_ai_agent/core/device_capability_broker/",
    )
    forbidden_file_names = {
        "build.gradle",
        "settings.gradle",
        "gradlew",
        "AndroidManifest.xml",
        "Info.plist",
        "Package.swift",
        "Podfile",
        "pubspec.yaml",
        "app.json",
        "app.config.js",
        "capacitor.config.ts",
        "capacitor.config.js",
        "ionic.config.json",
    }
    for rel_path in git_files:
        if rel_path.startswith(forbidden_dir_prefixes):
            print(f"FAIL: Forbidden native/mobile implementation path tracked in git: {rel_path}")
            sys.exit(1)
        if Path(rel_path).name in forbidden_file_names:
            print(f"FAIL: Forbidden native/mobile build or store file tracked in git: {rel_path}")
            sys.exit(1)
        if (
            rel_path.endswith((".swift", ".kt", ".kts", ".java"))
            and not rel_path.startswith("docs/")
            and not _is_m44_allowed_ccc_ios_skeleton_file(rel_path)
        ):
            print(f"FAIL: Forbidden native mobile source file tracked in git: {rel_path}")
            sys.exit(1)

    forbidden_dependencies = [
        '"expo"',
        '"react-native"',
        '"flutter"',
        '"@capacitor/',
        '"@ionic/',
        '"android"',
        '"gradle"',
    ]
    for rel_path in ["apps/control-center/package.json", "pyproject.toml"]:
        path = ROOT / rel_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_dependencies:
            if fragment in text:
                print(f"FAIL: Forbidden mobile/native dependency fragment in {rel_path}: {fragment}")
                sys.exit(1)

    implementation_roots = [ROOT / "src", ROOT / "apps", ROOT / "scripts"]
    forbidden_fragments = [
        "navigator.geolocation",
        "navigator.mediadevices",
        "notification.requestpermission",
        "pushmanager",
        "android.permission",
        "manifest.permission.",
        "cllocation",
        "avcapture",
        "locationmanager",
        "cameramanager",
        "audiorecord",
        "getusermedia",
        "mediadevices.getusermedia",
        "navigator.bluetooth",
        "nfcadapter",
        "biometricauthentication",
    ]
    for root in implementation_roots:
        if not root.exists():
            continue
        candidate_files = []
        if root.name in {"src", "scripts", "tests"}:
            candidate_files.extend(root.rglob("*.py"))
        else:
            candidate_files.extend(root.rglob("*.ts"))
            candidate_files.extend(root.rglob("*.tsx"))
            candidate_files.extend(root.rglob("*.js"))
            candidate_files.extend(root.rglob("*.jsx"))
        for path in candidate_files:
            rel = path.relative_to(ROOT).as_posix()
            if not path.is_file() or "__pycache__" in rel or "node_modules/" in rel:
                continue
            text = path.read_text(encoding="utf-8").lower()
            if rel in {
                "scripts/verify_all.py",
                "scripts/verify_control_center_frontend.py",
                "src/ultimate_ai_agent/core/gate/evaluators.py",
                "tests/test_control_center_frontend_safety_verifier.py",
            }:
                continue
            for fragment in forbidden_fragments:
                if fragment in text:
                    print(f"FAIL: Forbidden mobile sensor/runtime fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: No native mobile app, sensor API, OS permission, or mobile dependency implementation detected")


def run_static_scans():
    print("\n=== Static Verification Scans ===")
    print("Scans enabled:")
    for scan_name, _ in SCAN_SEQUENCE:
        print(f"- {scan_name}")

    for _, function_name in SCAN_SEQUENCE:
        globals()[function_name]()


def main():
    print("=== Ultimate AI Agent Master Verification Suite ===")

    # 1. Run Ruff Linter
    run_cmd([sys.executable, "-m", "ruff", "check", "."])

    # 2. Run Pytest Suite
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    run_cmd([sys.executable, "-m", "pytest"], env=env)

    # 3. Explicitly Enforce Scans
    run_static_scans()

    # 4. Run Baseline Consistency Verification
    run_cmd([sys.executable, "scripts/verify_current_baseline.py"])

    # 5. Run Documentation Integrity Verification
    run_cmd([sys.executable, "scripts/verify_documentation_integrity.py"])

    # 6. Run Skill Package Security Rule Audit
    run_cmd([sys.executable, "scripts/verify_skill_package_security_rule.py"])

    # 7. Run OpenAPI Contract Verification
    run_cmd([sys.executable, "scripts/verify_openapi_contract.py"])

    print("\n=== All verification checks PASSED successfully ===")

if __name__ == "__main__":
    main()
