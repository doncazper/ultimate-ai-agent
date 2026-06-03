#!/usr/bin/env python3
import sys
import subprocess
import re
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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
    if len(paths) != 74:
        print(f"FAIL: M22 expected OpenAPI path count 74, found {len(paths)}")
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
            rel = path.relative_to(ROOT).as_posix()
            if rel == "src/ultimate_ai_agent/core/gate/evaluators.py":
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
        "docs/release_notes/v0_30_0.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_30_0.md",
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
            rel = path.relative_to(ROOT).as_posix()
            if rel == "src/ultimate_ai_agent/core/gate/evaluators.py":
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

    manifest = GroundedRecallManifest(baseline_version="0.30.0")
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
        if rel_path.endswith((".swift", ".kt", ".kts", ".java")) and not rel_path.startswith("docs/"):
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

    implementation_roots = [ROOT / "src", ROOT / "apps", ROOT / "scripts", ROOT / "tests"]
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
