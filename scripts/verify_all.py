#!/usr/bin/env python3
import sys
import subprocess
import re
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
    ("shell execution scan", "verify_no_shell_execution_in_runtime"),
    ("production truth integration scan", "verify_no_production_truth_integrations"),
    ("broad filesystem scan", "verify_no_broad_filesystem_scanning"),
    ("mobile/device capability contract-only scan", "verify_no_mobile_native_or_sensor_implementation"),
]


def run_cmd(args, cwd=ROOT, env=None):
    print(f"\nRunning: {' '.join(args)}")
    result = subprocess.run(args, cwd=cwd, env=env, text=True)
    if result.returncode != 0:
        print(f"FAIL: Command failed with exit code {result.returncode}")
        sys.exit(1)
    print("SUCCESS")

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
