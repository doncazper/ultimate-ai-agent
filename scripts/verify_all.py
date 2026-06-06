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


def _current_version_tuple() -> tuple[int, int, int]:
    version = _current_version().lstrip("v")
    return tuple(int(part) for part in version.split("."))  # type: ignore[return-value]


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
    ("M48 first internal TestFlight build scan", "verify_m48_first_internal_testflight_build"),
    ("M49 mobile review approval capture scan", "verify_m49_mobile_review_approval_capture"),
    ("M50 mobile approval audit hardening scan", "verify_m50_mobile_approval_audit_hardening"),
    ("M51 OpenWebUI bridge adapter pilot scan", "verify_m51_openwebui_bridge_adapter_pilot"),
    ("M52 OpenWebUI safe conversation surface scan", "verify_m52_openwebui_safe_conversation_surface"),
    ("M53 controlled tool expansion review scan", "verify_m53_controlled_tool_expansion_review"),
    ("M54 safe media metadata inspector scan", "verify_m54_safe_media_metadata_inspector"),
    ("M55 redacted observability export scan", "verify_m55_redacted_observability_export"),
    ("M56 agent eval regression harness scan", "verify_m56_agent_eval_regression_harness"),
    ("M57 runtime sandbox architecture review scan", "verify_m57_runtime_sandbox_architecture_review"),
    ("M58 dry-run execution audit harness scan", "verify_m58_dry_run_execution_audit_harness"),
    ("M59 public GitHub readiness scan", "verify_m59_public_github_readiness"),
    ("M60 local developer beta freeze scan", "verify_m60_local_developer_beta_freeze"),
    ("M61 autonomy mode charter scan", "verify_m61_autonomy_mode_charter"),
    ("M62 scoped autonomy session scan", "verify_m62_scoped_autonomy_session"),
    ("M63 autonomy policy engine scan", "verify_m63_autonomy_policy_engine"),
    ("M64 autonomous plan simulator scan", "verify_m64_autonomous_plan_simulator"),
    ("M65 autonomy audit replay viewer scan", "verify_m65_autonomy_audit_replay_viewer"),
    ("M66 scoped approval bundles scan", "verify_m66_scoped_approval_bundles"),
    ("M67 revocation kill switch scan", "verify_m67_revocation_kill_switch"),
    ("M68 autonomy risk classifier scan", "verify_m68_autonomy_risk_classifier"),
    ("M69 low-risk autonomous dry run scan", "verify_m69_low_risk_autonomous_dry_run"),
    ("M70 autonomy foundation freeze scan", "verify_m70_autonomy_foundation_freeze"),
    ("M71 network tool contract review scan", "verify_m71_network_tool_contract_review"),
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
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "tests/test_m41_gate_integration.py",
        "tests/test_m41_local_prototype_safety_freeze.py",
    }
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
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
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "tests/test_m42_gate_integration.py",
        "tests/test_m42_mobile_product_contract_refresh.py",
    }
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
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
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "tests/test_m43_gate_integration.py",
        "tests/test_m43_mobile_api_boundary_read_only.py",
    }
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
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
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "tests/test_m44_gate_integration.py",
        "tests/test_m44_ccc_ios_skeleton_no_authority.py",
    }
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
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
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "tests/test_m45_gate_integration.py",
        "tests/test_m45_ccc_ios_local_read_only_connection.py",
    }
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
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
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "tests/test_m46_gate_integration.py",
        "tests/test_m46_ccc_ios_review_receipt_read_only_surfaces.py",
    }
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
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
    allowed_files = {
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "tests/test_m47_gate_integration.py",
        "tests/test_m47_testflight_pipeline_internal_only.py",
    }
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M47 forbidden enabled flag in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M47 TestFlight pipeline is internal-only, contract/checklist-only, no-build, no-upload, and no-authority")


def verify_m48_first_internal_testflight_build():
    print("\n[Verifier] Running M48 first internal TestFlight build guard...")
    required_files = [
        "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
        "src/ultimate_ai_agent/core/mobile_companion/planning.py",
        "src/ultimate_ai_agent/core/mobile_companion/enums.py",
        "docs/mobile/FIRST_INTERNAL_TESTFLIGHT_BUILD.md",
        "docs/mobile/M48_TO_M49_BOUNDARY.md",
        "docs/release_notes/v0_52_0.md",
        "docs/archive/releases/v0_52_0/README_IMPORT.md",
        "docs/archive/releases/v0_52_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_52_0.md",
        "tests/test_m48_first_internal_testflight_build.py",
        "tests/test_m48_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M48 first internal TestFlight build file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "first internal testflight build",
        "build candidate",
        "review-only",
        "internal-only",
        "no committed build artifact",
        "no ipa",
        "no signing material",
        "no app store connect",
        "no testflight upload",
        "no external beta",
        "no public distribution",
        "no production authority",
        "m49 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M48 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m48_openapi_route_failures
        from ultimate_ai_agent.core.mobile_companion import (
            assert_first_internal_testflight_build_candidate_safe,
            build_default_first_internal_testflight_build_candidate,
        )
    except Exception as exc:
        print(f"FAIL: M48 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m48_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    try:
        candidate = build_default_first_internal_testflight_build_candidate()
        assert_first_internal_testflight_build_candidate_safe(candidate)
    except Exception as exc:
        print(f"FAIL: M48 default first internal TestFlight build candidate failed validation: {exc}")
        sys.exit(1)

    ios_root = ROOT / "apps" / "ccc-ios"
    forbidden_paths = [
        ios_root / "Package.swift",
        *ios_root.glob("*.xcodeproj"),
        *ios_root.rglob("*.xcworkspace"),
        *ios_root.rglob("*.entitlements"),
        *ios_root.rglob("Info.plist"),
        *ios_root.rglob("ExportOptions.plist"),
        *ios_root.rglob("*.xcarchive"),
        *ios_root.rglob("*.ipa"),
        *ios_root.rglob("*.mobileprovision"),
        *ios_root.rglob("*.p8"),
        *ios_root.rglob("*.cer"),
        *ios_root.rglob("*.p12"),
    ]
    if (ROOT / ".github").exists():
        forbidden_paths.extend((ROOT / ".github").rglob("*testflight*"))
        forbidden_paths.extend((ROOT / ".github").rglob("*app-store-connect*"))
    for forbidden_path in forbidden_paths:
        if forbidden_path.exists():
            rel = forbidden_path.relative_to(ROOT).as_posix()
            print(f"FAIL: M48 forbidden TestFlight/signing/build artifact present: {rel}")
            sys.exit(1)
    for forbidden_dir in [
        ROOT / "fastlane",
        ios_root / "fastlane",
        ios_root / "DerivedData",
        ios_root / "Archives",
        ios_root / "build",
        ios_root / "dist",
    ]:
        if forbidden_dir.exists():
            rel = forbidden_dir.relative_to(ROOT).as_posix()
            print(f"FAIL: M48 forbidden build/upload directory present: {rel}")
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
        "App Store Connect",
        "TestFlightUpload",
        "xcodebuild",
        "altool",
        "notarytool",
        "ExportOptions",
        "XCArchive",
        ".ipa",
        "mobileprovision",
    ]:
        if fragment in swift_text:
            print(f"FAIL: M48 forbidden Swift/build fragment present: {fragment}")
            sys.exit(1)

    forbidden_source_fragments = [
        "build_execution_performed=True",
        "archive_created_in_repo=True",
        "ipa_created_in_repo=True",
        "testflight_upload_performed=True",
        "app_store_connect_api_called=True",
        "signing_asset_storage_enabled=True",
        "signing_identity_material_stored=True",
        "provisioning_profile_material_stored=True",
        "certificate_or_private_key_stored=True",
        "fastlane_workflow_enabled=True",
        "ci_upload_workflow_enabled=True",
        "external_beta_enabled=True",
        "public_distribution_enabled=True",
        "production_authority_enabled=True",
        "mobile_sensor_access_enabled=True",
        "background_collection_enabled=True",
        "approval_execution_enabled=True",
        "context_injection_enabled=True",
        "memory_write_enabled=True",
        "raw_data_export_enabled=True",
        "export_enabled=True",
        "execution_enabled=True",
    ]
    source_roots = [ROOT / "src", ROOT / "apps" / "control-center" / "src", ios_root]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel == "src/ultimate_ai_agent/core/gate/evaluators.py":
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M48 forbidden enabled flag in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M48 first internal TestFlight build is reviewed-candidate-only, no-build-artifact, no-upload, no-signing-material, and no-authority")


def verify_m49_mobile_review_approval_capture():
    print("\n[Verifier] Running M49 mobile review approval capture guard...")
    required_files = [
        "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
        "src/ultimate_ai_agent/core/mobile_companion/enums.py",
        "docs/mobile/MOBILE_REVIEW_APPROVAL_CAPTURE.md",
        "docs/mobile/M49_TO_M50_BOUNDARY.md",
        "docs/release_notes/v0_53_0.md",
        "docs/archive/releases/v0_53_0/README_IMPORT.md",
        "docs/archive/releases/v0_53_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_53_0.md",
        "tests/test_m49_mobile_review_approval_capture.py",
        "tests/test_m49_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M49 mobile review approval capture file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "mobile review approval capture",
        "review-only",
        "exact-scope",
        "actor-bound",
        "resource-bound",
        "replay-safe",
        "revocable",
        "safe refs only",
        "no raw file access",
        "no raw content",
        "no full-file content",
        "no unredacted preview",
        "no context proposal",
        "no context injection",
        "no memory write",
        "no export",
        "no execution",
        "no mobile sensor access",
        "no background collection",
        "no backend mobile approval route",
        "no native approval capture ui",
        "m50 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M49 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        from datetime import timedelta

        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m49_openapi_route_failures
        from ultimate_ai_agent.core.mobile_companion import (
            MobileReviewApprovalCaptureDecisionStatus,
            MobileReviewApprovalCaptureRequest,
            MobileReviewApprovalDecisionKind,
            capture_mobile_review_approval,
        )
        from ultimate_ai_agent.core.time import utc_now
    except Exception as exc:
        print(f"FAIL: M49 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m49_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    now = utc_now()
    request = MobileReviewApprovalCaptureRequest(
        approval_ref="mobile-review-approval-capture:verify-all",
        actor_ref="user:verify-all-mobile-reviewer",
        mobile_surface_ref="ccc-ios-review-surface:verify-all",
        review_packet_ref="file-review-packet:verify-all-mobile-review",
        preview_result_ref="redacted-file-preview-output:verify-all-mobile-review",
        redaction_summary_ref="file-review-redaction-summary:verify-all-mobile-review",
        file_ref="file-ref:verify-all-mobile-review",
        safe_path_ref="filesystem-preview-path:safe-root_mobile/verify-all/review.md",
        receipt_plan_ref="mobile-review-receipt-plan:verify-all-mobile-review",
        decision=MobileReviewApprovalDecisionKind.approve_review_only,
        idempotency_key="mobile-review-approval-idempotency:verify-all-mobile-review",
        expected_actor_ref="user:verify-all-mobile-reviewer",
        expected_mobile_surface_ref="ccc-ios-review-surface:verify-all",
        expected_review_packet_ref="file-review-packet:verify-all-mobile-review",
        expected_preview_result_ref="redacted-file-preview-output:verify-all-mobile-review",
        expected_redaction_summary_ref="file-review-redaction-summary:verify-all-mobile-review",
        expected_file_ref="file-ref:verify-all-mobile-review",
        expected_safe_path_ref="filesystem-preview-path:safe-root_mobile/verify-all/review.md",
        expires_at=now + timedelta(minutes=5),
    )
    decision = capture_mobile_review_approval(request, current_time=now)
    if decision.status != MobileReviewApprovalCaptureDecisionStatus.approved_for_mobile_review_only:
        print("FAIL: M49 safe mobile review approval capture did not approve review-only")
        sys.exit(1)
    if not decision.review_only or decision.execution_authorized or decision.execution_performed:
        print("FAIL: M49 capture decision granted execution or stopped being review-only")
        sys.exit(1)
    unsafe = capture_mobile_review_approval(
        request.model_copy(update={"execution_enabled": True}),
        current_time=now,
    )
    if unsafe.status != MobileReviewApprovalCaptureDecisionStatus.rejected:
        print("FAIL: M49 model_copy execution flag was not rejected")
        sys.exit(1)

    ios_root = ROOT / "apps" / "ccc-ios"
    swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
    swift_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(swift_root.rglob("*.swift")))
    for fragment in [
        "MobileReviewApprovalCapture",
        "approvalCapture",
        "approvalExecution",
        "contextProposal",
        "contextInjection",
        "memoryWrite",
        "exportReview",
        "SensorAccess",
        "BackgroundCollection",
    ]:
        if fragment in swift_text:
            print(f"FAIL: M49 forbidden Swift mobile approval/sensor fragment present: {fragment}")
            sys.exit(1)

    forbidden_source_fragments = [
        "raw_file_access_enabled=True",
        "raw_content_enabled=True",
        "full_file_content_enabled=True",
        "unredacted_preview_enabled=True",
        "context_proposal_enabled=True",
        "context_injection_enabled=True",
        "memory_write_enabled=True",
        "export_enabled=True",
        "execution_enabled=True",
        "approval_execution_enabled=True",
        "mobile_sensor_access_enabled=True",
        "background_collection_enabled=True",
        "/mobile/review/approvals/capture",
        "/mobile/review/approvals/execute",
        "/mobile/context/inject",
        "/mobile/memory/write",
        "/mobile/tools/execute",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
        "tests/test_m49_mobile_review_approval_capture.py",
        "tests/test_m49_gate_integration.py",
    }
    source_roots = [ROOT / "src", ROOT / "apps" / "control-center" / "src", ios_root]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M49 forbidden authority/route fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M49 mobile review approval capture is exact-scope, safe-ref-only, review-only, no-route, and no-authority")


def verify_m50_mobile_approval_audit_hardening():
    print("\n[Verifier] Running M50 mobile approval audit hardening guard...")
    required_files = [
        "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
        "src/ultimate_ai_agent/core/mobile_companion/enums.py",
        "docs/mobile/MOBILE_APPROVAL_AUDIT_HARDENING.md",
        "docs/mobile/M50_TO_M51_BOUNDARY.md",
        "docs/release_notes/v0_54_0.md",
        "docs/archive/releases/v0_54_0/README_IMPORT.md",
        "docs/archive/releases/v0_54_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_54_0.md",
        "tests/test_m50_mobile_approval_audit_hardening.py",
        "tests/test_m50_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M50 mobile approval audit file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "mobile approval audit hardening",
        "review-only",
        "safe-ref-only",
        "model_copy",
        "no raw content",
        "no context injection",
        "no memory write",
        "no export",
        "no execution",
        "no mobile sensor access",
        "no backend route",
        "m51 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M50 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        from datetime import timedelta

        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m50_openapi_route_failures
        from ultimate_ai_agent.core.mobile_companion import (
            MobileApprovalAuditStatus,
            MobileReviewApprovalCaptureRequest,
            MobileReviewApprovalDecisionKind,
            MobileReviewApprovalStore,
            audit_mobile_review_approval_records,
            audit_mobile_review_approval_store,
            capture_mobile_review_approval,
        )
        from ultimate_ai_agent.core.time import utc_now
    except Exception as exc:
        print(f"FAIL: M50 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m50_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    now = utc_now()
    request = MobileReviewApprovalCaptureRequest(
        approval_ref="mobile-review-approval-capture:verify-all-m50",
        actor_ref="user:verify-all-m50-mobile-reviewer",
        mobile_surface_ref="ccc-ios-review-surface:verify-all-m50",
        review_packet_ref="file-review-packet:verify-all-m50",
        preview_result_ref="redacted-file-preview-output:verify-all-m50",
        redaction_summary_ref="file-review-redaction-summary:verify-all-m50",
        file_ref="file-ref:verify-all-m50",
        safe_path_ref="filesystem-preview-path:safe-root_mobile/verify-all/m50.md",
        receipt_plan_ref="mobile-review-receipt-plan:verify-all-m50",
        decision=MobileReviewApprovalDecisionKind.approve_review_only,
        idempotency_key="mobile-review-approval-idempotency:verify-all-m50",
        expected_actor_ref="user:verify-all-m50-mobile-reviewer",
        expected_mobile_surface_ref="ccc-ios-review-surface:verify-all-m50",
        expected_review_packet_ref="file-review-packet:verify-all-m50",
        expected_preview_result_ref="redacted-file-preview-output:verify-all-m50",
        expected_redaction_summary_ref="file-review-redaction-summary:verify-all-m50",
        expected_file_ref="file-ref:verify-all-m50",
        expected_safe_path_ref="filesystem-preview-path:safe-root_mobile/verify-all/m50.md",
        expires_at=now + timedelta(minutes=5),
    )
    store = MobileReviewApprovalStore()
    decision = capture_mobile_review_approval(request, store=store, current_time=now)
    report = audit_mobile_review_approval_store(store)
    if report.status != MobileApprovalAuditStatus.passed or report.record_count != 1:
        print(f"FAIL: M50 safe mobile approval audit did not pass: {report.reason_codes}")
        sys.exit(1)
    if report.memory_write_performed or report.export_performed or report.execution_performed:
        print("FAIL: M50 audit report performed forbidden side effect")
        sys.exit(1)
    if decision.record is None:
        print("FAIL: M50 capture setup did not produce a record")
        sys.exit(1)
    unsafe = audit_mobile_review_approval_records([decision.record.model_copy(update={"execution_enabled": True})])
    if unsafe.status != MobileApprovalAuditStatus.failed:
        print("FAIL: M50 model_copy execution field was not rejected")
        sys.exit(1)
    if "MOBILE_APPROVAL_AUDIT_EXECUTION_DENIED" not in unsafe.reason_codes:
        print("FAIL: M50 execution audit rejection reason missing")
        sys.exit(1)

    ios_root = ROOT / "apps" / "ccc-ios"
    swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
    swift_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(swift_root.rglob("*.swift")))
    for fragment in [
        "MobileApprovalAudit",
        "approvalAuditExport",
        "auditRaw",
        "auditWrite",
        "approvalExecution",
        "SensorAccess",
        "BackgroundCollection",
    ]:
        if fragment in swift_text:
            print(f"FAIL: M50 forbidden Swift mobile audit/sensor fragment present: {fragment}")
            sys.exit(1)

    forbidden_source_fragments = [
        "raw_file_access_enabled=True",
        "raw_content_enabled=True",
        "full_file_content_enabled=True",
        "unredacted_preview_enabled=True",
        "context_proposal_enabled=True",
        "context_injection_enabled=True",
        "memory_write_enabled=True",
        "export_enabled=True",
        "execution_enabled=True",
        "approval_execution_enabled=True",
        "mobile_sensor_access_enabled=True",
        "background_collection_enabled=True",
        "/mobile/review/audit",
        "/mobile/review/audit/export",
        "/mobile/review/audit/raw",
        "/mobile/approvals/audit/write",
        "/mobile/context/inject",
        "/mobile/memory/write",
        "/mobile/tools/execute",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/mobile_companion/approval_capture.py",
        "tests/test_m49_mobile_review_approval_capture.py",
        "tests/test_m49_gate_integration.py",
        "tests/test_m50_mobile_approval_audit_hardening.py",
        "tests/test_m50_gate_integration.py",
    }
    source_roots = [ROOT / "src", ROOT / "apps" / "control-center" / "src", ios_root]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M50 forbidden authority/route fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M50 mobile approval audit is safe-ref-only, review-only, no-route, no-export, and no-authority")


def verify_m51_openwebui_bridge_adapter_pilot():
    print("\n[Verifier] Running M51 OpenWebUI bridge adapter pilot guard...")
    required_files = [
        "src/ultimate_ai_agent/core/openwebui_bridge/adapter.py",
        "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
        "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
        "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_PILOT.md",
        "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_POLICY.md",
        "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_AUTHORITY_BOUNDARY.md",
        "docs/openwebui/M51_TO_M52_BOUNDARY.md",
        "docs/release_notes/v0_55_0.md",
        "docs/archive/releases/v0_55_0/README_IMPORT.md",
        "docs/archive/releases/v0_55_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_55_0.md",
        "tests/test_m51_openwebui_bridge_adapter_pilot.py",
        "tests/test_m51_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M51 OpenWebUI bridge adapter file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "openwebui bridge adapter pilot",
        "safe-summary-only",
        "agent core remains authority",
        "openwebui is not the agent brain",
        "no raw prompt",
        "no raw provider payload",
        "no provider call",
        "no model authority",
        "no tool execution",
        "no memory write",
        "no context injection",
        "no backend route",
        "m52 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M51 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m51_openapi_route_failures
        from ultimate_ai_agent.core.openwebui_bridge import (
            OpenWebUIBridgeAdapterRequest,
            OpenWebUIBridgeAdapterStatus,
            adapt_openwebui_bridge_request,
        )
    except Exception as exc:
        print(f"FAIL: M51 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m51_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    request = OpenWebUIBridgeAdapterRequest(
        adapter_request_ref="openwebui-bridge-adapter-request:verify-all-m51",
        session_ref="openwebui-session:verify-all-m51",
        message_ref="openwebui-message:verify-all-m51",
        safe_user_summary="User asked for a safe governance summary.",
    )
    result = adapt_openwebui_bridge_request(request)
    if result.status != OpenWebUIBridgeAdapterStatus.safe_summary_ready:
        print(f"FAIL: M51 safe adapter did not return ready status: {result.reason_codes}")
        sys.exit(1)
    for field_name in [
        "raw_prompt_returned",
        "raw_provider_payload_returned",
        "raw_content_returned",
        "model_output_authoritative",
        "openwebui_called",
        "provider_called",
        "tool_executed",
        "memory_written",
        "context_injected",
        "approval_granted",
    ]:
        if getattr(result, field_name):
            print(f"FAIL: M51 adapter result enabled forbidden field: {field_name}")
            sys.exit(1)
    if result.side_effects_performed:
        print("FAIL: M51 adapter result performed side effects")
        sys.exit(1)
    try:
        adapt_openwebui_bridge_request(request.model_copy(update={"raw_provider_payload_present": True}))
        print("FAIL: M51 raw provider payload mutation was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "RAW_PROVIDER_PAYLOAD_DENIED" not in str(exc):
            print(f"FAIL: M51 raw provider payload rejection reason drifted: {exc}")
            sys.exit(1)
    try:
        adapt_openwebui_bridge_request(
            request.model_copy(
                update={
                    "approval_ref": "approval:verify-all-m51",
                    "tool_execution_requested": True,
                }
            )
        )
        print("FAIL: M51 approval_ref/tool execution mutation was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "APPROVAL_REF_NOT_AUTHORITY" not in str(exc):
            print(f"FAIL: M51 approval-ref rejection reason drifted: {exc}")
            sys.exit(1)

    forbidden_source_fragments = [
        "openwebui_runtime_call_requested=True",
        "live_openwebui_connection_enabled=True",
        "openwebui_network_call_enabled=True",
        "provider_call_enabled=True",
        "provider_call_requested=True",
        "model_authority_enabled=True",
        "model_authority_requested=True",
        "tool_execution_enabled=True",
        "tool_execution_requested=True",
        "memory_write_enabled=True",
        "memory_write_requested=True",
        "context_injection_enabled=True",
        "context_injection_requested=True",
        "raw_prompt_exposure_enabled=True",
        "raw_prompt_present=True",
        "raw_provider_payload_exposure_enabled=True",
        "raw_provider_payload_present=True",
        "raw_content_allowed=True",
        "raw_content_present=True",
        "openwebui_called=True",
        "provider_called=True",
        "tool_executed=True",
        "memory_written=True",
        "context_injected=True",
        "/openwebui/handoff",
        "/openwebui/runtime/call",
        "/openwebui/provider/call",
        "/openwebui/tools/execute",
        "/openwebui/memory/write",
        "/openwebui/context/inject",
        "/openwebui/raw-payload",
        "import openwebui\n",
        "from openwebui",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
        "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
        "tests/test_m51_openwebui_bridge_adapter_pilot.py",
        "tests/test_m51_gate_integration.py",
    }
    source_roots = [
        ROOT / "src",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M51 forbidden OpenWebUI adapter fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M51 OpenWebUI bridge adapter is safe-summary-only, no-route, no-runtime, and no-authority")


def verify_m52_openwebui_safe_conversation_surface():
    print("\n[Verifier] Running M52 OpenWebUI safe conversation surface guard...")
    required_files = [
        "src/ultimate_ai_agent/core/openwebui_bridge/conversation.py",
        "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
        "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
        "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_SURFACE.md",
        "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_POLICY.md",
        "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_AUTHORITY_BOUNDARY.md",
        "docs/openwebui/M52_TO_M53_BOUNDARY.md",
        "docs/release_notes/v0_56_0.md",
        "docs/archive/releases/v0_56_0/README_IMPORT.md",
        "docs/archive/releases/v0_56_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_56_0.md",
        "tests/test_m52_openwebui_safe_conversation_surface.py",
        "tests/test_m52_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M52 OpenWebUI safe conversation file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    docs_fragments = [
        "openwebui safe conversation surface",
        "safe-summary-only",
        "agent core remains authority",
        "openwebui is not the agent brain",
        "no raw prompt",
        "no raw provider payload",
        "no raw content",
        "no provider call",
        "no model call",
        "no model authority",
        "no tool execution",
        "no memory write",
        "no context injection",
        "no backend route",
    ]
    if _current_version_tuple() < (0, 57, 0):
        docs_fragments.append("m53 remains future")
    for fragment in docs_fragments:
        if fragment not in docs_text:
            print(f"FAIL: M52 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m52_openapi_route_failures
        from ultimate_ai_agent.core.openwebui_bridge import (
            OpenWebUIMessageDirection,
            OpenWebUISafeConversationSurfaceStatus,
            OpenWebUISafeConversationTurn,
            build_openwebui_safe_conversation_surface,
        )
    except Exception as exc:
        print(f"FAIL: M52 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m52_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    turn = OpenWebUISafeConversationTurn(
        turn_ref="openwebui-conversation-turn:verify-all-m52",
        session_ref="openwebui-session:verify-all-m52",
        message_ref="openwebui-message:verify-all-m52",
        direction=OpenWebUIMessageDirection.user_to_agent_core_planned,
        safe_summary="User asked for a safe OpenWebUI conversation summary.",
    )
    surface = build_openwebui_safe_conversation_surface(
        conversation_ref="openwebui-safe-conversation:verify-all-m52",
        session_ref="openwebui-session:verify-all-m52",
        safe_title="Governed OpenWebUI conversation preview",
        turns=[turn],
    )
    if surface.status != OpenWebUISafeConversationSurfaceStatus.safe_review_ready:
        print(f"FAIL: M52 safe conversation surface did not return ready status: {surface.reason_codes}")
        sys.exit(1)
    for field_name in [
        "openwebui_called",
        "provider_called",
        "model_called",
        "model_output_authoritative",
        "tool_executed",
        "memory_written",
        "context_injected",
        "approval_granted",
        "raw_prompt_returned",
        "raw_provider_payload_returned",
        "raw_content_returned",
    ]:
        if getattr(surface, field_name):
            print(f"FAIL: M52 surface enabled forbidden field: {field_name}")
            sys.exit(1)
    if surface.side_effects_performed:
        print("FAIL: M52 surface performed side effects")
        sys.exit(1)
    try:
        build_openwebui_safe_conversation_surface(
            conversation_ref="openwebui-safe-conversation:verify-all-m52-raw",
            session_ref="openwebui-session:verify-all-m52",
            safe_title="Mutated unsafe conversation",
            turns=[turn.model_copy(update={"raw_provider_payload_present": True})],
        )
        print("FAIL: M52 raw provider payload mutation was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "RAW_PROVIDER_PAYLOAD_DENIED" not in str(exc):
            print(f"FAIL: M52 raw provider payload rejection reason drifted: {exc}")
            sys.exit(1)
    try:
        build_openwebui_safe_conversation_surface(
            conversation_ref="openwebui-safe-conversation:verify-all-m52-approval",
            session_ref="openwebui-session:verify-all-m52",
            safe_title="Approval refs are not authority",
            turns=[
                turn.model_copy(
                    update={
                        "approval_ref": "approval:verify-all-m52",
                        "tool_execution_requested": True,
                    }
                )
            ],
        )
        print("FAIL: M52 approval_ref/tool execution mutation was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "APPROVAL_REF_NOT_AUTHORITY" not in str(exc):
            print(f"FAIL: M52 approval-ref rejection reason drifted: {exc}")
            sys.exit(1)

    forbidden_source_fragments = [
        "openwebui_runtime_call_requested=True",
        "live_openwebui_connection_enabled=True",
        "openwebui_network_call_enabled=True",
        "provider_call_enabled=True",
        "provider_call_requested=True",
        "model_call_enabled=True",
        "model_call_requested=True",
        "model_authority_enabled=True",
        "model_authority_requested=True",
        "tool_execution_enabled=True",
        "tool_execution_requested=True",
        "memory_write_enabled=True",
        "memory_write_requested=True",
        "context_injection_enabled=True",
        "context_injection_requested=True",
        "raw_prompt_exposure_enabled=True",
        "raw_prompt_present=True",
        "raw_provider_payload_exposure_enabled=True",
        "raw_provider_payload_present=True",
        "raw_content_allowed=True",
        "raw_content_present=True",
        "openwebui_called=True",
        "provider_called=True",
        "model_called=True",
        "tool_executed=True",
        "memory_written=True",
        "context_injected=True",
        "/openwebui/conversation",
        "/openwebui/runtime/call",
        "/openwebui/provider/call",
        "/openwebui/model/call",
        "/openwebui/tools/execute",
        "/openwebui/memory/write",
        "/openwebui/context/inject",
        "/openwebui/raw-payload",
        "import openwebui\n",
        "from openwebui",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
        "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
        "tests/test_m52_openwebui_safe_conversation_surface.py",
        "tests/test_m52_gate_integration.py",
    }
    source_roots = [
        ROOT / "src",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M52 forbidden OpenWebUI safe conversation fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M52 OpenWebUI safe conversation surface is safe-summary-only, no-route, no-runtime, and no-authority")


def verify_m53_controlled_tool_expansion_review():
    print("\n[Verifier] Running M53 controlled tool expansion review guard...")
    required_files = [
        "src/ultimate_ai_agent/core/tools/expansion_review.py",
        "docs/tools/CONTROLLED_TOOL_EXPANSION_REVIEW.md",
        "docs/tools/CONTROLLED_TOOL_EXPANSION_POLICY.md",
        "docs/tools/CONTROLLED_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md",
        "docs/tools/M53_TO_M54_BOUNDARY.md",
        "docs/release_notes/v0_57_0.md",
        "docs/archive/releases/v0_57_0/README_IMPORT.md",
        "docs/archive/releases/v0_57_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_57_0.md",
        "tests/test_m53_controlled_tool_expansion_review.py",
        "tests/test_m53_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M53 controlled tool expansion file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "controlled tool expansion review",
        "review-only",
        "planning-only",
        "no tool execution",
        "no tool enablement",
        "no shell execution",
        "no unrestricted network tool",
        "no provider model call",
        "no browser automation execution",
        "no plugin enablement",
        "no mobile sensor access",
        "no remote execution",
        "no raw file browsing",
        "no raw file export",
        "no full-file read",
        "no memory write",
        "no context injection",
        "no backend route",
        "m54 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M53 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m53_openapi_route_failures
        from ultimate_ai_agent.core.tools import (
            ControlledToolExpansionCandidate,
            ControlledToolExpansionPolicy,
            ControlledToolExpansionReviewStatus,
            ToolExpansionCapabilityKind,
            evaluate_controlled_tool_expansion_candidate,
            validate_controlled_tool_expansion_candidate,
            validate_controlled_tool_expansion_policy,
        )
    except Exception as exc:
        print(f"FAIL: M53 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m53_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    candidate = ControlledToolExpansionCandidate(
        candidate_ref="tool-expansion-candidate:verify-all-m53",
        safe_name="Metadata-only review candidate",
        capability_kind=ToolExpansionCapabilityKind.safe_metadata_review,
        safe_summary="Review future tool capability metadata without enablement.",
    )
    decision = evaluate_controlled_tool_expansion_candidate(candidate)
    if decision.status != ControlledToolExpansionReviewStatus.review_ready:
        print(f"FAIL: M53 safe candidate was not review-ready: {decision.reason_codes}")
        sys.exit(1)
    if not decision.review_allowed or decision.execution_allowed or decision.tool_enablement_allowed:
        print("FAIL: M53 decision did not remain review-only")
        sys.exit(1)
    if decision.receipt_plan is None or decision.receipt_plan.execution_performed or decision.receipt_plan.tool_enabled:
        print("FAIL: M53 receipt plan did not remain no-execution/no-enable")
        sys.exit(1)

    future_decision = evaluate_controlled_tool_expansion_candidate(
        ControlledToolExpansionCandidate(
            candidate_ref="tool-expansion-candidate:verify-all-m53-shell_execution",
            safe_name="Future shell execution review",
            capability_kind=ToolExpansionCapabilityKind.shell_execution,
            safe_summary="Review a future tool capability without enabling it.",
        )
    )
    if future_decision.status != ControlledToolExpansionReviewStatus.future_milestone:
        print("FAIL: M53 effectful candidate did not require a future milestone")
        sys.exit(1)

    for candidate_update, reason in [
        ({"execution_requested": True}, "TOOL_EXPANSION_EXECUTION_DENIED"),
        ({"tool_enablement_requested": True}, "TOOL_ENABLEMENT_DENIED"),
        ({"contains_raw_provider_payload": True}, "RAW_PROVIDER_PAYLOAD_DENIED"),
        ({"approval_ref": "approval:verify-all-m53"}, "APPROVAL_REF_NOT_AUTHORITY"),
    ]:
        try:
            validate_controlled_tool_expansion_candidate(candidate.model_copy(update=candidate_update))
            print(f"FAIL: M53 unsafe candidate mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M53 unsafe candidate reason drifted for {reason}: {exc}")
                sys.exit(1)

    try:
        validate_controlled_tool_expansion_policy(ControlledToolExpansionPolicy(shell_execution_enabled=True))
        print("FAIL: M53 unsafe policy flag was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "SHELL_EXECUTION_DENIED" not in str(exc):
            print(f"FAIL: M53 unsafe policy reason drifted: {exc}")
            sys.exit(1)

    print("OK: M53 controlled tool expansion review is review-only, no-route, and no-authority")


def verify_m54_safe_media_metadata_inspector():
    print("\n[Verifier] Running M54 safe media metadata inspector guard...")
    required_files = [
        "src/ultimate_ai_agent/core/media/__init__.py",
        "src/ultimate_ai_agent/core/media/metadata.py",
        "docs/media/SAFE_MEDIA_METADATA_INSPECTOR.md",
        "docs/media/SAFE_MEDIA_METADATA_POLICY.md",
        "docs/media/SAFE_MEDIA_METADATA_AUTHORITY_BOUNDARY.md",
        "docs/media/M54_TO_M55_BOUNDARY.md",
        "docs/release_notes/v0_58_0.md",
        "docs/archive/releases/v0_58_0/README_IMPORT.md",
        "docs/archive/releases/v0_58_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_58_0.md",
        "tests/test_m54_safe_media_metadata_inspector.py",
        "tests/test_m54_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M54 safe media metadata file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "safe media metadata inspector",
        "metadata-only",
        "no raw media export",
        "no raw media storage",
        "no full-file read",
        "no file mutation",
        "no original overwrite",
        "no ocio transform",
        "no ai gamut expansion",
        "no model call",
        "no context injection",
        "no backend route",
        "m55 remains future",
        "skill package security rule",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M54 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m54_openapi_route_failures
        from ultimate_ai_agent.core.media import (
            MediaInspectionKind,
            SafeMediaMetadataPolicy,
            SafeMediaMetadataRequest,
            SafeMediaMetadataStatus,
            inspect_safe_media_metadata,
            validate_safe_media_metadata_policy,
            validate_safe_media_metadata_request,
        )
    except Exception as exc:
        print(f"FAIL: M54 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m54_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    request = SafeMediaMetadataRequest(
        request_ref="media-metadata-request:verify-all-m54",
        media_ref="media:verify-all-m54",
        safe_path_ref="safe-path:verify-all-m54.jpg",
        inspection_kind=MediaInspectionKind.image_metadata,
        declared_media_type="image/jpeg",
        declared_byte_size=2048,
    )
    decision = inspect_safe_media_metadata(request)
    if decision.status != SafeMediaMetadataStatus.metadata_ready or not decision.metadata_ready:
        print(f"FAIL: M54 safe request was not metadata-ready: {decision.reason_codes}")
        sys.exit(1)
    if (
        decision.raw_media_returned
        or decision.raw_media_stored
        or decision.original_file_modified
        or decision.ocio_transform_performed
        or decision.ai_gamut_expansion_performed
        or decision.model_call_performed
        or decision.context_injection_performed
    ):
        print("FAIL: M54 decision performed raw media, mutation, transform, model, or context side effect")
        sys.exit(1)
    if decision.receipt_plan is None or decision.receipt_plan.side_effects_performed or decision.receipt_plan.raw_media_stored:
        print("FAIL: M54 receipt plan did not remain metadata-only/no-effect")
        sys.exit(1)

    denied = inspect_safe_media_metadata(
        request.model_copy(
            update={
                "request_ref": "media-metadata-request:verify-all-m54-unsupported",
                "declared_media_type": "application/octet-stream",
            }
        )
    )
    if denied.status != SafeMediaMetadataStatus.denied or denied.raw_media_returned:
        print("FAIL: M54 unsupported media type was not safely denied")
        sys.exit(1)

    for request_update, reason in [
        ({"raw_media_requested": True}, "RAW_MEDIA_EXPORT_DENIED"),
        ({"full_file_read_requested": True}, "FULL_FILE_READ_DENIED"),
        ({"file_mutation_requested": True}, "FILE_MUTATION_DENIED"),
        ({"original_overwrite_requested": True}, "ORIGINAL_OVERWRITE_DENIED"),
        ({"ocio_transform_requested": True}, "OCIO_TRANSFORM_DENIED"),
        ({"ai_gamut_expansion_requested": True}, "AI_GAMUT_EXPANSION_DENIED"),
        ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
        ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
        ({"contains_secret_like_metadata": True}, "SECRET_LIKE_METADATA_DENIED"),
    ]:
        try:
            validate_safe_media_metadata_request(request.model_copy(update=request_update))
            print(f"FAIL: M54 unsafe request mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M54 unsafe request reason drifted for {reason}: {exc}")
                sys.exit(1)

    try:
        validate_safe_media_metadata_policy(SafeMediaMetadataPolicy(raw_media_export_enabled=True))
        print("FAIL: M54 unsafe policy flag was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "RAW_MEDIA_EXPORT_DENIED" not in str(exc):
            print(f"FAIL: M54 unsafe policy reason drifted: {exc}")
            sys.exit(1)

    forbidden_source_fragments = [
        "raw_media_export_enabled=True",
        "raw_media_storage_enabled=True",
        "full_file_read_enabled=True",
        "file_mutation_enabled=True",
        "original_overwrite_enabled=True",
        "ocio_transform_enabled=True",
        "ai_gamut_expansion_enabled=True",
        "model_call_enabled=True",
        "context_injection_enabled=True",
        "production_authority_enabled=True",
        "raw_media_returned=True",
        "raw_media_stored=True",
        "original_file_modified=True",
        "ocio_transform_performed=True",
        "ai_gamut_expansion_performed=True",
        "model_call_performed=True",
        "context_injection_performed=True",
        "/media/read/raw",
        "/media/export",
        "/media/transform/ocio",
        "/media/gamut/expand",
        "/models/call",
        "/provider/call",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/api/app.py",
        "src/ultimate_ai_agent/api/openapi.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/media/metadata.py",
        "tests/test_m54_safe_media_metadata_inspector.py",
        "tests/test_m54_gate_integration.py",
    }
    source_roots = [
        ROOT / "src",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M54 forbidden media metadata fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M54 safe media metadata inspector is metadata-only, no-route, no-transform, and no-authority")


def verify_m55_redacted_observability_export():
    print("\n[Verifier] Running M55 redacted observability export guard...")
    required_files = [
        "src/ultimate_ai_agent/core/observability/__init__.py",
        "src/ultimate_ai_agent/core/observability/export.py",
        "docs/observability/REDACTED_OBSERVABILITY_EXPORT.md",
        "docs/observability/REDACTED_OBSERVABILITY_EXPORT_POLICY.md",
        "docs/observability/REDACTED_OBSERVABILITY_EXPORT_AUTHORITY_BOUNDARY.md",
        "docs/observability/M55_TO_M56_BOUNDARY.md",
        "docs/release_notes/v0_59_0.md",
        "docs/archive/releases/v0_59_0/README_IMPORT.md",
        "docs/archive/releases/v0_59_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_59_0.md",
        "tests/test_m55_redacted_observability_export.py",
        "tests/test_m55_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M55 redacted observability export file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "redacted observability export",
        "redacted-only",
        "contract-only",
        "no external saas",
        "no network delivery",
        "no raw prompt",
        "no raw provider payload",
        "no raw private content",
        "no secrets",
        "no forensic trace export",
        "no model call",
        "no memory write",
        "no context injection",
        "no backend route",
        "no control center control",
        "no dependency",
        "no production authority",
        "m56 remains future",
        "skill package security rule",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M55 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from datetime import UTC, datetime

        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m55_openapi_route_failures
        from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
        from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
        from ultimate_ai_agent.core.hygiene.temporal_context import (
            FreshnessClass,
            StalenessPolicy,
            TemporalContext,
        )
        from ultimate_ai_agent.core.ledger import EventLedgerEvent, EventName
        from ultimate_ai_agent.core.observability import (
            ObservabilityExportFormat,
            RedactedObservabilityExportPolicy,
            RedactedObservabilityExportRequest,
            RedactedObservabilityExportStatus,
            build_redacted_observability_export,
            validate_redacted_observability_export_policy,
            validate_redacted_observability_export_request,
        )
    except Exception as exc:
        print(f"FAIL: M55 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m55_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    event = EventLedgerEvent(
        event_id="evt_verify_all_m55",
        event_type="run",
        event_name=EventName.run_completed,
        run_id="run_verify_all_m55",
        trace_id="trace_verify_all_m55",
        span_id="span_verify_all_m55",
        correlation_id="corr_verify_all_m55",
        actor_context=ActorContext(
            actor_type=ActorType.orchestrator,
            actor_id="m55-verify-all",
            authority_source=AuthoritySource.explicit_user_request,
            created_at=datetime.now(UTC),
        ),
        temporal_context=TemporalContext(
            current_time_utc=datetime.now(UTC),
            freshness_class=FreshnessClass.daily,
            staleness_policy=StalenessPolicy.allow_with_label,
        ),
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="verify-all-m55",
        ),
        redaction_summary={"status": "redacted"},
        event_source="ultimate-ai-agent",
        subject="M55 verify all",
        action="summarize",
        outcome="completed",
        status="success",
        severity="info",
        evidence_refs=["evidence:verify-all-m55"],
        metadata={"safe_summary": "M55 verify-all redacted summary only."},
    )
    request = RedactedObservabilityExportRequest(
        request_ref="observability-export-request:verify-all-m55",
        run_ref="run:verify-all-m55",
        export_ref="observability-export:verify-all-m55",
        requested_formats=[ObservabilityExportFormat.internal_redacted_json],
        source_event_refs=["event:evt_verify_all_m55"],
        redaction_policy_ref="redaction-policy:verify-all-m55",
    )
    bundle = build_redacted_observability_export(request, [event])
    if bundle.status != RedactedObservabilityExportStatus.ready or bundle.export_performed:
        print(f"FAIL: M55 safe export bundle was not review-ready/no-effect: {bundle.status}")
        sys.exit(1)
    if (
        bundle.external_delivery_performed
        or bundle.raw_prompt_exported
        or bundle.raw_provider_payload_exported
        or bundle.raw_private_content_exported
        or bundle.secret_exported
        or bundle.saas_sdk_enabled
        or bundle.network_call_performed
        or bundle.memory_write_performed
        or bundle.model_call_performed
        or bundle.context_injection_performed
    ):
        print("FAIL: M55 bundle performed external, raw, model, memory, or context side effect")
        sys.exit(1)
    if bundle.receipt_plan is None or bundle.receipt_plan.side_effects_performed:
        print("FAIL: M55 receipt plan did not remain no-effect")
        sys.exit(1)

    for request_update, reason in [
        ({"raw_prompt_export_requested": True}, "RAW_PROMPT_EXPORT_DENIED"),
        ({"raw_provider_payload_export_requested": True}, "RAW_PROVIDER_PAYLOAD_EXPORT_DENIED"),
        ({"raw_private_content_export_requested": True}, "RAW_PRIVATE_CONTENT_EXPORT_DENIED"),
        ({"secret_export_requested": True}, "SECRET_EXPORT_DENIED"),
        ({"external_saas_export_requested": True}, "EXTERNAL_SAAS_EXPORT_DENIED"),
        ({"network_export_requested": True}, "NETWORK_EXPORT_DENIED"),
        ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
        ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
        ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
    ]:
        try:
            validate_redacted_observability_export_request(request.model_copy(update=request_update))
            print(f"FAIL: M55 unsafe request mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M55 unsafe request reason drifted for {reason}: {exc}")
                sys.exit(1)

    try:
        validate_redacted_observability_export_policy(
            RedactedObservabilityExportPolicy(external_saas_sdk_enabled=True)
        )
        print("FAIL: M55 unsafe policy flag was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "EXTERNAL_SAAS_SDK_DENIED" not in str(exc):
            print(f"FAIL: M55 unsafe policy reason drifted: {exc}")
            sys.exit(1)

    forbidden_source_fragments = [
        "external_saas_sdk_enabled=True",
        "network_delivery_enabled=True",
        "raw_prompt_export_enabled=True",
        "raw_provider_payload_export_enabled=True",
        "raw_private_content_export_enabled=True",
        "secret_export_enabled=True",
        "forensic_trace_export_enabled=True",
        "model_call_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "production_authority_enabled=True",
        "export_performed=True",
        "external_delivery_performed=True",
        "raw_prompt_exported=True",
        "raw_provider_payload_exported=True",
        "raw_private_content_exported=True",
        "secret_exported=True",
        "saas_sdk_enabled=True",
        "network_call_performed=True",
        "memory_write_performed=True",
        "model_call_performed=True",
        "context_injection_performed=True",
        "/observability/export",
        "/observability/export/raw",
        "/observability/export/prompts",
        "/observability/export/provider-payloads",
        "/observability/export/secrets",
        "/observability/export/saas",
        "/observability/export/network",
        "/otel/export",
        "/analytics/export",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/api/app.py",
        "src/ultimate_ai_agent/api/openapi.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/observability/export.py",
        "tests/test_m55_redacted_observability_export.py",
        "tests/test_m55_gate_integration.py",
    }
    source_roots = [
        ROOT / "src",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M55 forbidden observability export fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M55 redacted observability export is redacted-only, no-route, no-delivery, and no-authority")


def verify_m56_agent_eval_regression_harness():
    print("\n[Verifier] Running M56 agent eval regression harness guard...")
    required_files = [
        "src/ultimate_ai_agent/core/evals/__init__.py",
        "src/ultimate_ai_agent/core/evals/regression.py",
        "docs/evals/AGENT_EVAL_REGRESSION_HARNESS.md",
        "docs/evals/AGENT_EVAL_REGRESSION_POLICY.md",
        "docs/evals/AGENT_EVAL_REGRESSION_AUTHORITY_BOUNDARY.md",
        "docs/evals/M56_TO_M57_BOUNDARY.md",
        "docs/release_notes/v0_60_0.md",
        "docs/archive/releases/v0_60_0/README_IMPORT.md",
        "docs/archive/releases/v0_60_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_60_0.md",
        "tests/test_m56_agent_eval_regression_harness.py",
        "tests/test_m56_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M56 agent eval regression file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "agent eval regression harness",
        "deterministic",
        "contract-only",
        "no model call",
        "no provider call",
        "no tool execution",
        "no shell execution",
        "no browser automation",
        "no network access",
        "no memory write",
        "no context injection",
        "no raw prompt",
        "no raw provider payload",
        "no backend route",
        "no control center control",
        "no dependency",
        "no production authority",
        "m57 remains future",
        "skill package security rule",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M56 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.evals import (
            AgentEvalCase,
            AgentEvalCaseObservation,
            AgentEvalHarnessPolicy,
            AgentEvalRegressionRunRequest,
            AgentEvalRegressionStatus,
            AgentEvalSuite,
            build_agent_eval_regression_report,
            validate_agent_eval_harness_policy,
            validate_agent_eval_regression_request,
        )
        from ultimate_ai_agent.core.gate.evaluators import m56_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M56 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m56_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    case = AgentEvalCase(
        case_ref="eval-case:verify-all-m56",
        suite_ref="eval-suite:verify-all-m56",
        scenario_ref="scenario:verify-all-m56",
        expected_outcome_ref="outcome:contract-only",
        redacted_input_summary="Verify-all safe redacted eval case.",
        invariant_refs=["invariant:no-model-call", "invariant:no-tool-execution"],
        evidence_refs=["evidence:verify-all-m56"],
    )
    suite = AgentEvalSuite(
        suite_ref="eval-suite:verify-all-m56",
        baseline_ref="baseline:v0.59.0",
        case_refs=[case.case_ref],
        cases=[case],
        deterministic_seed_ref="seed:verify-all-m56",
    )
    request = AgentEvalRegressionRunRequest(
        request_ref="eval-request:verify-all-m56",
        run_ref="eval-run:verify-all-m56",
        suite_ref=suite.suite_ref,
        case_refs=[case.case_ref],
        baseline_ref=suite.baseline_ref,
    )
    report = build_agent_eval_regression_report(
        request,
        suite,
        [
            AgentEvalCaseObservation(
                case_ref=case.case_ref,
                observed_outcome_ref=case.expected_outcome_ref,
                safe_observation_summary="Verify-all explicit safe observation.",
                evidence_refs=["evidence:verify-all-m56-observed"],
            )
        ],
    )
    if report.status != AgentEvalRegressionStatus.passed or report.failed_cases:
        print(f"FAIL: M56 safe eval regression report did not pass: {report.status}")
        sys.exit(1)
    if (
        report.model_call_performed
        or report.provider_call_performed
        or report.tool_execution_performed
        or report.shell_execution_performed
        or report.browser_automation_performed
        or report.network_call_performed
        or report.memory_write_performed
        or report.context_injection_performed
    ):
        print("FAIL: M56 report performed model/provider/tool/network/memory/context side effect")
        sys.exit(1)
    if report.receipt_plan is None or report.receipt_plan.evaluation_performed:
        print("FAIL: M56 receipt plan did not remain no-effect")
        sys.exit(1)

    for request_update, reason in [
        ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
        ({"provider_call_requested": True}, "PROVIDER_CALL_DENIED"),
        ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
        ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
        ({"browser_automation_requested": True}, "BROWSER_AUTOMATION_DENIED"),
        ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
        ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
        ({"raw_prompt_capture_requested": True}, "RAW_PROMPT_CAPTURE_DENIED"),
        ({"raw_provider_payload_capture_requested": True}, "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
    ]:
        try:
            validate_agent_eval_regression_request(request.model_copy(update=request_update))
            print(f"FAIL: M56 unsafe request mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M56 unsafe request reason drifted for {reason}: {exc}")
                sys.exit(1)

    try:
        validate_agent_eval_harness_policy(AgentEvalHarnessPolicy(model_call_enabled=True))
        print("FAIL: M56 unsafe policy flag was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "MODEL_CALL_DENIED" not in str(exc):
            print(f"FAIL: M56 unsafe policy reason drifted: {exc}")
            sys.exit(1)

    forbidden_source_fragments = [
        "model_call_enabled=True",
        "provider_call_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "browser_automation_enabled=True",
        "network_access_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "raw_prompt_capture_enabled=True",
        "raw_provider_payload_capture_enabled=True",
        "external_dataset_fetch_enabled=True",
        "score_authority_enabled=True",
        "production_authority_enabled=True",
        "evaluation_performed=True",
        "model_call_performed=True",
        "provider_call_performed=True",
        "tool_execution_performed=True",
        "network_call_performed=True",
        "memory_write_performed=True",
        "context_injection_performed=True",
        "/evals/run",
        "/evals/execute",
        "/evals/model-call",
        "/evals/provider-call",
        "/evals/export/raw",
        "/models/call",
        "/provider/call",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/shell/execute",
        "/browser/click",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/api/app.py",
        "src/ultimate_ai_agent/api/openapi.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/evals/regression.py",
        "tests/test_m56_agent_eval_regression_harness.py",
        "tests/test_m56_gate_integration.py",
    }
    source_roots = [
        ROOT / "src",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M56 forbidden eval regression fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M56 agent eval regression harness is deterministic, no-route, no-execution, and no-authority")


def verify_m57_runtime_sandbox_architecture_review():
    print("\n[Verifier] Running M57 runtime sandbox architecture review guard...")
    required_files = [
        "src/ultimate_ai_agent/core/sandbox/__init__.py",
        "src/ultimate_ai_agent/core/sandbox/architecture.py",
        "docs/sandbox/RUNTIME_SANDBOX_ARCHITECTURE_REVIEW.md",
        "docs/sandbox/RUNTIME_SANDBOX_BOUNDARY_POLICY.md",
        "docs/sandbox/RUNTIME_SANDBOX_AUTHORITY_BOUNDARY.md",
        "docs/sandbox/M57_TO_M58_BOUNDARY.md",
        "docs/release_notes/v0_61_0.md",
        "docs/archive/releases/v0_61_0/README_IMPORT.md",
        "docs/archive/releases/v0_61_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_61_0.md",
        "tests/test_m57_runtime_sandbox_architecture_review.py",
        "tests/test_m57_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M57 runtime sandbox architecture file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "runtime sandbox architecture review",
        "architecture review only",
        "contract-only",
        "no sandbox execution",
        "no subprocess",
        "no shell execution",
        "no process spawn",
        "no file mutation",
        "no network access",
        "no tool execution",
        "no memory write",
        "no context injection",
        "no backend route",
        "no control center control",
        "no dependency",
        "no production authority",
        "m58 remains future",
        "skill package security rule",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M57 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m57_openapi_route_failures
        from ultimate_ai_agent.core.sandbox import (
            RuntimeSandboxArchitecturePolicy,
            RuntimeSandboxArchitectureRequest,
            RuntimeSandboxArchitectureStatus,
            build_runtime_sandbox_architecture_review,
            validate_runtime_sandbox_architecture_policy,
            validate_runtime_sandbox_architecture_request,
        )
    except Exception as exc:
        print(f"FAIL: M57 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m57_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    request = RuntimeSandboxArchitectureRequest(
        request_ref="sandbox-review-request:verify-all-m57",
        review_ref="sandbox-review:verify-all-m57",
        architecture_ref="sandbox-architecture:verify-all-m57",
        boundary_refs=["boundary:no-subprocess", "boundary:no-shell-execution"],
        threat_model_refs=["threat:process-spawn", "threat:network-egress"],
        audit_requirement_refs=["audit:dry-run-before-execution"],
        safe_summary="Verify-all runtime sandbox architecture review.",
    )
    review = build_runtime_sandbox_architecture_review(request)
    if review.status != RuntimeSandboxArchitectureStatus.reviewed:
        print(f"FAIL: M57 safe architecture review did not pass: {review.status}")
        sys.exit(1)
    if (
        not review.architecture_review_only
        or review.runtime_sandbox_enabled
        or review.execution_performed
        or review.subprocess_performed
        or review.shell_execution_performed
        or review.process_spawn_performed
        or review.filesystem_mutation_performed
        or review.network_access_performed
        or review.memory_write_performed
        or review.context_injection_performed
    ):
        print("FAIL: M57 review performed runtime sandbox execution or side effects")
        sys.exit(1)
    if review.receipt_plan is None or review.receipt_plan.side_effects_performed:
        print("FAIL: M57 receipt plan did not remain no-effect")
        sys.exit(1)

    for request_update, reason in [
        ({"sandbox_runtime_requested": True}, "SANDBOX_RUNTIME_DENIED"),
        ({"subprocess_execution_requested": True}, "SUBPROCESS_EXECUTION_DENIED"),
        ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
        ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
        ({"filesystem_mutation_requested": True}, "FILESYSTEM_MUTATION_DENIED"),
        ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
        ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
        ({"browser_automation_requested": True}, "BROWSER_AUTOMATION_DENIED"),
        ({"plugin_execution_requested": True}, "PLUGIN_EXECUTION_DENIED"),
        ({"remote_execution_requested": True}, "REMOTE_EXECUTION_DENIED"),
        ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
        ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
        ({"m58_dry_run_harness_requested": True}, "M58_DRY_RUN_HARNESS_DENIED"),
    ]:
        try:
            validate_runtime_sandbox_architecture_request(request.model_copy(update=request_update))
            print(f"FAIL: M57 unsafe request mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M57 unsafe request reason drifted for {reason}: {exc}")
                sys.exit(1)

    try:
        validate_runtime_sandbox_architecture_policy(RuntimeSandboxArchitecturePolicy(sandbox_runtime_enabled=True))
        print("FAIL: M57 unsafe policy flag was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "SANDBOX_RUNTIME_DENIED" not in str(exc):
            print(f"FAIL: M57 unsafe policy reason drifted: {exc}")
            sys.exit(1)

    forbidden_source_fragments = [
        "sandbox_runtime_enabled=True",
        "subprocess_execution_enabled=True",
        "shell_execution_enabled=True",
        "process_spawn_enabled=True",
        "filesystem_mutation_enabled=True",
        "network_access_enabled=True",
        "tool_execution_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "remote_execution_enabled=True",
        "model_call_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "side_effects_enabled=True",
        "production_authority_enabled=True",
        "m58_dry_run_harness_enabled=True",
        "subprocess_performed=True",
        "shell_execution_performed=True",
        "process_spawn_performed=True",
        "filesystem_mutation_performed=True",
        "network_access_performed=True",
        "subprocess.run(",
        "subprocess.Popen(",
        "os.system(",
        "shell=True",
        "/sandbox/run",
        "/sandbox/execute",
        "/process/spawn",
        "/subprocess/run",
        "/shell/execute",
        "/tools/execute",
        "/tool-runtime/execute",
        "/context/inject",
        "/memory/write",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/api/app.py",
        "src/ultimate_ai_agent/api/openapi.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/sandbox/architecture.py",
        "tests/test_m57_runtime_sandbox_architecture_review.py",
        "tests/test_m57_gate_integration.py",
    }
    source_roots = [
        ROOT / "src",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M57 forbidden runtime sandbox fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M57 runtime sandbox architecture review is contract-only, no-route, no-execution, and no-authority")


def verify_m58_dry_run_execution_audit_harness():
    print("\n[Verifier] Running M58 dry-run execution audit harness guard...")
    required_files = [
        "src/ultimate_ai_agent/core/dry_run_audit/__init__.py",
        "src/ultimate_ai_agent/core/dry_run_audit/harness.py",
        "docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_HARNESS.md",
        "docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_POLICY.md",
        "docs/dry_run_audit/DRY_RUN_EXECUTION_AUTHORITY_BOUNDARY.md",
        "docs/dry_run_audit/M58_TO_M59_BOUNDARY.md",
        "docs/release_notes/v0_62_0.md",
        "docs/archive/releases/v0_62_0/README_IMPORT.md",
        "docs/archive/releases/v0_62_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_62_0.md",
        "tests/test_m58_dry_run_execution_audit_harness.py",
        "tests/test_m58_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M58 dry-run execution audit file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "dry-run execution audit harness",
        "dry-run-only",
        "contract-only",
        "no real execution",
        "no tool execution",
        "no subprocess",
        "no shell execution",
        "no process spawn",
        "no file mutation",
        "no network access",
        "no memory write",
        "no context injection",
        "no backend route",
        "no control center control",
        "no dependency",
        "no production authority",
        "m59 remains future",
        "skill package security rule",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M58 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.dry_run_audit import (
            DryRunExecutionAuditIntent,
            DryRunExecutionAuditPolicy,
            DryRunExecutionAuditRequest,
            DryRunExecutionAuditStatus,
            build_dry_run_execution_audit_report,
            validate_dry_run_execution_audit_policy,
            validate_dry_run_execution_audit_request,
        )
        from ultimate_ai_agent.core.gate.evaluators import m58_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M58 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m58_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    intent = DryRunExecutionAuditIntent(
        intent_ref="dry-run-intent:verify-all-m58",
        operation_ref="operation:verify-all-preview",
        target_ref="target:verify-all-contract",
        requested_capability_refs=["capability:preview-only", "capability:no-side-effects"],
        safe_summary="Verify-all dry-run audit intent.",
    )
    request = DryRunExecutionAuditRequest(
        request_ref="dry-run-audit-request:verify-all-m58",
        audit_ref="dry-run-audit:verify-all-m58",
        sandbox_review_ref="sandbox-review:verify-all-m57",
        intent_refs=[intent.intent_ref],
        intents=[intent],
        actor_ref="actor:verify-all-reviewer",
        replay_key_ref="replay-key:verify-all-m58",
    )
    report = build_dry_run_execution_audit_report(request)
    if report.status != DryRunExecutionAuditStatus.reviewed:
        print(f"FAIL: M58 safe dry-run audit did not pass: {report.status}")
        sys.exit(1)
    if (
        not report.dry_run_only
        or report.execution_performed
        or report.tool_execution_performed
        or report.subprocess_performed
        or report.shell_execution_performed
        or report.process_spawn_performed
        or report.filesystem_mutation_performed
        or report.network_access_performed
        or report.memory_write_performed
        or report.context_injection_performed
    ):
        print("FAIL: M58 dry-run audit performed real execution or side effects")
        sys.exit(1)
    if report.receipt_plan is None or report.receipt_plan.side_effects_performed:
        print("FAIL: M58 receipt plan did not remain no-effect")
        sys.exit(1)

    for intent_update, reason in [
        ({"execution_requested": True}, "EXECUTION_DENIED"),
        ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
        ({"subprocess_execution_requested": True}, "SUBPROCESS_EXECUTION_DENIED"),
        ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
        ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
        ({"filesystem_mutation_requested": True}, "FILESYSTEM_MUTATION_DENIED"),
        ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
        ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
        ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
        ({"contains_raw_prompt": True}, "RAW_PROMPT_CAPTURE_DENIED"),
    ]:
        mutated_request = request.model_copy(update={"intents": [intent.model_copy(update=intent_update)]})
        try:
            validate_dry_run_execution_audit_request(mutated_request)
            print(f"FAIL: M58 unsafe intent mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M58 unsafe intent reason drifted for {reason}: {exc}")
                sys.exit(1)

    try:
        validate_dry_run_execution_audit_policy(DryRunExecutionAuditPolicy(execution_enabled=True))
        print("FAIL: M58 unsafe policy flag was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "EXECUTION_DENIED" not in str(exc):
            print(f"FAIL: M58 unsafe policy reason drifted: {exc}")
            sys.exit(1)

    forbidden_source_fragments = [
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "subprocess_execution_enabled=True",
        "shell_execution_enabled=True",
        "process_spawn_enabled=True",
        "filesystem_mutation_enabled=True",
        "network_access_enabled=True",
        "model_call_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "remote_execution_enabled=True",
        "side_effects_enabled=True",
        "production_authority_enabled=True",
        "m59_public_readiness_enabled=True",
        "execution_performed=True",
        "tool_execution_performed=True",
        "subprocess_performed=True",
        "shell_execution_performed=True",
        "process_spawn_performed=True",
        "filesystem_mutation_performed=True",
        "network_access_performed=True",
        "subprocess.run(",
        "subprocess.Popen(",
        "os.system(",
        "shell=True",
        "/dry-run/run",
        "/dry-run/execute",
        "/execution/audit/run",
        "/execution/audit/execute",
        "/process/spawn",
        "/subprocess/run",
        "/shell/execute",
        "/tools/execute",
        "/tool-runtime/execute",
        "/context/inject",
        "/memory/write",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/api/app.py",
        "src/ultimate_ai_agent/api/openapi.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/dry_run_audit/harness.py",
        "tests/test_m58_dry_run_execution_audit_harness.py",
        "tests/test_m58_gate_integration.py",
    }
    source_roots = [
        ROOT / "src",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M58 forbidden dry-run execution fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M58 dry-run execution audit harness is dry-run-only, no-route, no-execution, and no-authority")


def verify_m59_public_github_readiness():
    print("\n[Verifier] Running M59 public GitHub readiness guard...")
    required_files = [
        "src/ultimate_ai_agent/core/public_readiness/__init__.py",
        "src/ultimate_ai_agent/core/public_readiness/review.py",
        "docs/public_readiness/PUBLIC_GITHUB_READINESS.md",
        "docs/public_readiness/PUBLIC_GITHUB_READINESS_POLICY.md",
        "docs/public_readiness/PUBLIC_GITHUB_READINESS_AUTHORITY_BOUNDARY.md",
        "docs/public_readiness/M59_TO_M60_BOUNDARY.md",
        "docs/release_notes/v0_63_0.md",
        "docs/archive/releases/v0_63_0/README_IMPORT.md",
        "docs/archive/releases/v0_63_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_63_0.md",
        "tests/test_m59_public_github_readiness.py",
        "tests/test_m59_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M59 public GitHub readiness file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "public github readiness",
        "review-only",
        "contract-only",
        "no github push",
        "no github release",
        "no wiki automation",
        "no artifact upload",
        "no external service",
        "no credential handling",
        "no network access",
        "no backend route",
        "no control center control",
        "no dependency",
        "no production authority",
        "m60 remains future",
        "skill package security rule",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M59 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m59_openapi_route_failures
        from ultimate_ai_agent.core.public_readiness import (
            PublicGitHubReadinessPolicy,
            PublicGitHubReadinessRequest,
            PublicGitHubReadinessStatus,
            build_public_github_readiness_report,
            validate_public_github_readiness_policy,
            validate_public_github_readiness_request,
        )
    except Exception as exc:
        print(f"FAIL: M59 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m59_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    request = PublicGitHubReadinessRequest(
        request_ref="public-readiness-request:verify-all-m59",
        readiness_ref="public-readiness:verify-all-m59",
        repository_ref="repo:ultimate-ai-agent",
        baseline_ref="baseline:v0.63.0",
        actor_ref="actor:verify-all-reviewer",
        checklist_refs=[
            "readiness:docs-current",
            "readiness:secret-hygiene",
            "readiness:artifact-hygiene",
            "readiness:route-boundary",
            "readiness:dependency-boundary",
        ],
        safe_summary="Verify-all public GitHub readiness review.",
    )
    report = build_public_github_readiness_report(request)
    if report.status != PublicGitHubReadinessStatus.reviewed:
        print(f"FAIL: M59 safe public readiness report did not pass: {report.status}")
        sys.exit(1)
    if (
        not report.review_only
        or report.publication_performed
        or report.github_push_performed
        or report.github_release_performed
        or report.wiki_automation_performed
        or report.artifact_upload_performed
        or report.external_service_performed
        or report.credential_handling_performed
        or report.network_access_performed
        or report.production_authority_granted
        or report.side_effects_performed
    ):
        print("FAIL: M59 public readiness report performed publication or authority side effects")
        sys.exit(1)
    if report.receipt_plan is None or report.receipt_plan.side_effects_performed:
        print("FAIL: M59 receipt plan did not remain no-effect")
        sys.exit(1)

    for request_update, reason in [
        ({"publication_requested": True}, "PUBLICATION_DENIED"),
        ({"github_push_requested": True}, "GITHUB_PUSH_DENIED"),
        ({"github_release_requested": True}, "GITHUB_RELEASE_DENIED"),
        ({"wiki_automation_requested": True}, "WIKI_AUTOMATION_DENIED"),
        ({"artifact_upload_requested": True}, "ARTIFACT_UPLOAD_DENIED"),
        ({"external_service_requested": True}, "EXTERNAL_SERVICE_DENIED"),
        ({"credential_handling_requested": True}, "CREDENTIAL_HANDLING_DENIED"),
        ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
        ({"production_authority_requested": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"m60_beta_freeze_requested": True}, "M60_BETA_FREEZE_DENIED"),
    ]:
        try:
            validate_public_github_readiness_request(request.model_copy(update=request_update))
            print(f"FAIL: M59 unsafe request mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M59 unsafe request reason drifted for {reason}: {exc}")
                sys.exit(1)

    try:
        validate_public_github_readiness_policy(PublicGitHubReadinessPolicy(github_push_enabled=True))
        print("FAIL: M59 unsafe policy flag was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "GITHUB_PUSH_DENIED" not in str(exc):
            print(f"FAIL: M59 unsafe policy reason drifted: {exc}")
            sys.exit(1)

    forbidden_source_fragments = [
        "publication_enabled=True",
        "github_push_enabled=True",
        "github_release_enabled=True",
        "wiki_automation_enabled=True",
        "artifact_upload_enabled=True",
        "external_service_enabled=True",
        "credential_handling_enabled=True",
        "network_access_enabled=True",
        "production_authority_enabled=True",
        "m60_beta_freeze_enabled=True",
        "publication_performed=True",
        "github_push_performed=True",
        "github_release_performed=True",
        "wiki_automation_performed=True",
        "artifact_upload_performed=True",
        "external_service_performed=True",
        "credential_handling_performed=True",
        "network_access_performed=True",
        "production_authority_granted=True",
        "/github/publish",
        "/github/release",
        "/github/wiki/update",
        "/public/artifacts/upload",
        "/public/release/publish",
        "/release/upload",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/public_readiness/review.py",
        "tests/test_m59_public_github_readiness.py",
        "tests/test_m59_gate_integration.py",
    }
    for root in [ROOT / "src", ROOT / "apps" / "control-center" / "src", ROOT / "apps" / "ccc-ios"]:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M59 forbidden public readiness fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M59 public GitHub readiness is review-only, no-publication, no-route, and no-authority")


def verify_m60_local_developer_beta_freeze():
    print("\n[Verifier] Running M60 local developer beta freeze guard...")
    required_files = [
        "src/ultimate_ai_agent/core/beta_freeze/__init__.py",
        "src/ultimate_ai_agent/core/beta_freeze/review.py",
        "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE.md",
        "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_POLICY.md",
        "docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_AUTHORITY_BOUNDARY.md",
        "docs/beta/POST_M60_AUTONOMY_BOUNDARY.md",
        "docs/release_notes/v0_64_0.md",
        "docs/archive/releases/v0_64_0/README_IMPORT.md",
        "docs/archive/releases/v0_64_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_64_0.md",
        "tests/test_m60_local_developer_beta_freeze.py",
        "tests/test_m60_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M60 local developer beta freeze file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "local developer beta freeze",
        "freeze-only",
        "local developer beta only",
        "review-only",
        "no public release",
        "no external distribution",
        "no post-m60 autonomy",
        "no production authority",
        "no execution",
        "no tool execution",
        "no shell execution",
        "no network tools",
        "no browser automation",
        "no plugin execution",
        "no mobile sensor access",
        "no remote execution",
        "no credential handling",
        "no memory writes",
        "no context injection",
        "no model/provider calls",
        "no backend route",
        "no control center control",
        "no dependency",
        "m61+ remains future",
        "skill package security rule",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M60 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.beta_freeze import (
            LocalDeveloperBetaFreezePolicy,
            LocalDeveloperBetaFreezeRequest,
            LocalDeveloperBetaFreezeStatus,
            build_local_developer_beta_freeze_report,
            validate_local_developer_beta_freeze_policy,
            validate_local_developer_beta_freeze_request,
        )
        from ultimate_ai_agent.core.gate.evaluators import m60_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M60 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m60_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    request = LocalDeveloperBetaFreezeRequest(
        request_ref="beta-freeze-request:verify-all-m60",
        freeze_ref="beta-freeze:verify-all-m60",
        baseline_ref="baseline:v0.64.0",
        actor_ref="actor:verify-all-reviewer",
        checklist_refs=[
            "beta-freeze:validation-green",
            "beta-freeze:docs-current",
            "beta-freeze:route-stable",
            "beta-freeze:dependency-stable",
            "beta-freeze:artifact-clean",
            "beta-freeze:authority-frozen",
        ],
        safe_summary="Verify-all local developer beta freeze review.",
    )
    report = build_local_developer_beta_freeze_report(request)
    if report.status != LocalDeveloperBetaFreezeStatus.frozen:
        print(f"FAIL: M60 safe beta freeze report did not pass: {report.status}")
        sys.exit(1)
    if (
        not report.freeze_only
        or not report.local_developer_beta_only
        or report.public_release_performed
        or report.external_distribution_performed
        or report.execution_performed
        or report.post_m60_autonomy_enabled
        or report.production_authority_granted
        or report.side_effects_performed
    ):
        print("FAIL: M60 beta freeze report performed release/autonomy/authority side effects")
        sys.exit(1)
    if report.receipt_plan is None or report.receipt_plan.side_effects_performed:
        print("FAIL: M60 receipt plan did not remain no-effect")
        sys.exit(1)

    for request_update, reason in [
        ({"public_release_requested": True}, "PUBLIC_RELEASE_DENIED"),
        ({"external_distribution_requested": True}, "EXTERNAL_DISTRIBUTION_DENIED"),
        ({"post_m60_autonomy_requested": True}, "POST_M60_AUTONOMY_DENIED"),
        ({"production_authority_requested": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"execution_requested": True}, "EXECUTION_DENIED"),
        ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
        ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
        ({"credential_handling_requested": True}, "CREDENTIAL_HANDLING_DENIED"),
        ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
    ]:
        try:
            validate_local_developer_beta_freeze_request(request.model_copy(update=request_update))
            print(f"FAIL: M60 unsafe request mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M60 unsafe request reason drifted for {reason}: {exc}")
                sys.exit(1)

    try:
        validate_local_developer_beta_freeze_policy(LocalDeveloperBetaFreezePolicy(public_release_enabled=True))
        print("FAIL: M60 unsafe policy flag was not denied")
        sys.exit(1)
    except ValueError as exc:
        if "PUBLIC_RELEASE_DENIED" not in str(exc):
            print(f"FAIL: M60 unsafe policy reason drifted: {exc}")
            sys.exit(1)

    forbidden_source_fragments = [
        "public_release_enabled=True",
        "external_distribution_enabled=True",
        "post_m60_autonomy_enabled=True",
        "production_authority_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_tool_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "credential_handling_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "model_provider_call_enabled=True",
        "public_release_performed=True",
        "external_distribution_performed=True",
        "execution_performed=True",
        "production_authority_granted=True",
        "/public/beta/release",
        "/github/release",
        "/autonomy/enable",
        "/remote/execute",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m60_local_developer_beta_freeze.py",
        "tests/test_m60_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M60 forbidden beta freeze fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M60 local developer beta freeze is freeze-only, route-free, no-autonomy, and no-authority")


def verify_m61_autonomy_mode_charter():
    print("\n[Verifier] Running M61 autonomy mode charter guard...")
    required_files = [
        "src/ultimate_ai_agent/core/autonomy/__init__.py",
        "src/ultimate_ai_agent/core/autonomy/modes.py",
        "docs/autonomy/AUTONOMY_MODE_CHARTER.md",
        "docs/autonomy/AUTHORITY_LEVELS.md",
        "docs/autonomy/CAPABILITY_TOGGLE_REGISTRY.md",
        "docs/autonomy/AUTONOMY_CONSENT_REVOCATION_POLICY.md",
        "docs/autonomy/M61_TO_M62_BOUNDARY.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/release_notes/v0_65_0.md",
        "docs/archive/releases/v0_65_0/README_IMPORT.md",
        "docs/archive/releases/v0_65_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_65_0.md",
        "tests/test_m61_autonomy_mode_charter.py",
        "tests/test_m61_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M61 autonomy mode charter file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "autonomy mode charter",
        "authority levels",
        "mode 0",
        "mode 1",
        "mode 2",
        "mode 3",
        "mode 4",
        "mode 5",
        "mode 6",
        "default mode off",
        "disabled by default",
        "dry-run first",
        "limited allowlist",
        "explicit approval",
        "scoped autonomy window",
        "audit/replay",
        "revocation",
        "no global autonomy switch",
        "no production authority",
        "no execution",
        "no tool execution",
        "no browser automation",
        "no shell execution",
        "no network tools",
        "no background worker",
        "no autonomous session",
        "no backend route",
        "no dependency",
        "m62 remains future",
        "skill package security rule",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M61 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.autonomy import (
            AutonomyAuthorityMode,
            AutonomyCapabilityToggle,
            AutonomyModeCharter,
            AutonomyRiskClass,
            build_autonomy_mode_decision,
            validate_autonomy_capability_toggle,
            validate_autonomy_mode_charter,
        )
        from ultimate_ai_agent.core.gate.evaluators import m61_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M61 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m61_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    charter = validate_autonomy_mode_charter(AutonomyModeCharter())
    if charter.default_mode != AutonomyAuthorityMode.off:
        print("FAIL: M61 autonomy charter default mode is not OFF")
        sys.exit(1)
    toggle = AutonomyCapabilityToggle(
        toggle_ref="autonomy-toggle:verify-all-m61",
        capability_ref="capability:observe-only-review",
        requested_mode=AutonomyAuthorityMode.off,
        actor_ref="actor:verify-all-reviewer",
        scope_ref="scope:verify-all-m61",
        resource_refs=["resource:local-prototype"],
        duration_seconds=0,
        risk_class=AutonomyRiskClass.low,
        revocation_ref="revocation:verify-all-m61",
        audit_ref="audit:verify-all-m61",
    )
    decision = build_autonomy_mode_decision(toggle, charter)
    if decision.selected_mode != AutonomyAuthorityMode.off or decision.allowed or decision.side_effects_performed:
        print("FAIL: M61 autonomy decision granted authority or side effects")
        sys.exit(1)

    for update, reason in [
        ({"enabled": True}, "AUTONOMY_TOGGLE_ENABLEMENT_DENIED"),
        (
            {"requested_mode": AutonomyAuthorityMode.ask_before_every_action, "duration_seconds": 300},
            "AUTONOMY_MODE_ENABLEMENT_DENIED",
        ),
        ({"approval_test_ref": "approval_test_:m61"}, "APPROVAL_TEST_REF_DENIED"),
        ({"tool_execution_enabled": True}, "TOOL_EXECUTION_DENIED"),
        ({"shell_execution_enabled": True}, "SHELL_EXECUTION_DENIED"),
        ({"network_tool_enabled": True}, "NETWORK_TOOL_DENIED"),
        ({"browser_automation_enabled": True}, "BROWSER_AUTOMATION_DENIED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        try:
            validate_autonomy_capability_toggle(toggle.model_copy(update=update))
            print(f"FAIL: M61 unsafe toggle mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M61 unsafe toggle reason drifted for {reason}: {exc}")
                sys.exit(1)

    for update, reason in [
        ({"default_mode": AutonomyAuthorityMode.dry_run_plan}, "AUTONOMY_DEFAULT_MODE_OFF_REQUIRED"),
        ({"global_autonomy_switch_enabled": True}, "GLOBAL_AUTONOMY_SWITCH_DENIED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"backend_routes_enabled": True}, "BACKEND_ROUTE_DENIED"),
        ({"dependencies_added": True}, "DEPENDENCY_ADDITION_DENIED"),
    ]:
        try:
            validate_autonomy_mode_charter(charter.model_copy(update=update))
            print(f"FAIL: M61 unsafe charter mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M61 unsafe charter reason drifted for {reason}: {exc}")
                sys.exit(1)

    forbidden_source_fragments = [
        "global_autonomy_switch_enabled=True",
        "production_authority_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_tool_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "background_worker_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "model_provider_call_enabled=True",
        "backend_routes_enabled=True",
        "dependencies_added=True",
        "execution_performed=True",
        "production_authority_granted=True",
        "/autonomy/enable",
        "/autonomy/session/start",
        "/autonomy/execute",
        "/network/fetch",
        "/shell/execute",
        "/browser/click",
        "/plugins/execute",
        "/background/start",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/autonomy/modes.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m61_autonomy_mode_charter.py",
        "tests/test_m61_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M61 forbidden autonomy fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M61 autonomy mode charter is default-off, route-free, no-autonomy, and no-authority")


def verify_m62_scoped_autonomy_session():
    print("\n[Verifier] Running M62 scoped autonomy session guard...")
    required_files = [
        "src/ultimate_ai_agent/core/autonomy/sessions.py",
        "docs/autonomy/SCOPED_AUTONOMY_SESSION_CONTRACTS.md",
        "docs/autonomy/SCOPED_AUTONOMY_SESSION_SCOPE_POLICY.md",
        "docs/autonomy/SCOPED_AUTONOMY_SESSION_NON_GOALS.md",
        "docs/autonomy/M62_TO_M63_BOUNDARY.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/release_notes/v0_66_0.md",
        "docs/archive/releases/v0_66_0/README_IMPORT.md",
        "docs/archive/releases/v0_66_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_66_0.md",
        "tests/test_m62_scoped_autonomy_session_contracts.py",
        "tests/test_m62_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M62 scoped autonomy session file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "scoped autonomy session contracts",
        "contract-only",
        "review-only",
        "actor-bound",
        "resource-bound",
        "duration-bound",
        "allowlist",
        "revocation",
        "audit/replay",
        "no session start",
        "no session activation",
        "no autonomous actions",
        "no background worker",
        "no execution",
        "no tool execution",
        "no shell execution",
        "no network tools",
        "no browser automation",
        "no backend route",
        "no dependency",
        "m63 remains future",
        "skill package security rule",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M62 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.autonomy import (
            AutonomyAuthorityMode,
            AutonomyRiskClass,
            ScopedAutonomySessionRequest,
            ScopedAutonomySessionScope,
            build_scoped_autonomy_session_decision,
            validate_scoped_autonomy_session_request,
            validate_scoped_autonomy_session_scope,
        )
        from ultimate_ai_agent.core.gate.evaluators import m62_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M62 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m62_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    scope = ScopedAutonomySessionScope(
        scope_ref="autonomy-session-scope:verify-all-m62",
        actor_ref="actor:verify-all-reviewer",
        resource_refs=["resource:local-prototype"],
        capability_refs=["capability:observe-only-review"],
        allowlist_refs=["allowlist:verify-all-m62"],
        max_duration_seconds=900,
        risk_class=AutonomyRiskClass.low,
        revocation_ref="revocation:verify-all-m62",
        audit_ref="audit:verify-all-m62",
        replay_ref="replay:verify-all-m62",
    )
    validate_scoped_autonomy_session_scope(scope)
    request = ScopedAutonomySessionRequest(
        session_request_ref="autonomy-session-request:verify-all-m62",
        requested_mode=AutonomyAuthorityMode.dry_run_plan,
        scope=scope,
        approval_ref="approval:m62-review-only",
    )
    decision = build_scoped_autonomy_session_decision(request)
    if decision.session_started or decision.session_active or decision.execution_performed or decision.side_effects_performed:
        print("FAIL: M62 scoped autonomy session decision granted authority or side effects")
        sys.exit(1)

    for update, reason in [
        ({"start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
        ({"session_active": True}, "AUTONOMY_SESSION_ACTIVATION_DENIED"),
        ({"execution_requested": True}, "EXECUTION_DENIED"),
        ({"autonomous_actions_enabled": True}, "AUTONOMOUS_ACTIONS_DENIED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"approval_test_ref": "approval_test_:m62"}, "APPROVAL_TEST_REF_DENIED"),
        ({"requested_mode": AutonomyAuthorityMode.ask_before_every_action}, "AUTONOMY_MODE_ENABLEMENT_DENIED"),
        ({"requested_mode": AutonomyAuthorityMode.scoped_autonomy_window}, "AUTONOMY_MODE_FUTURE_MILESTONE_DENIED"),
    ]:
        try:
            validate_scoped_autonomy_session_request(request.model_copy(update=update))
            print(f"FAIL: M62 unsafe request mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M62 unsafe request reason drifted for {reason}: {exc}")
                sys.exit(1)

    forbidden_source_fragments = [
        "session_start_enabled=True",
        "session_activation_enabled=True",
        "start_requested=True",
        "session_active=True",
        "execution_requested=True",
        "autonomous_actions_enabled=True",
        "background_worker_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_tool_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "production_authority_enabled=True",
        "execution_performed=True",
        "/autonomy/session/start",
        "/autonomy/session/activate",
        "/autonomy/session/run",
        "/autonomy/session/execute",
        "/background/start",
        "/network/fetch",
        "/shell/execute",
        "/browser/click",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/autonomy/sessions.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m62_scoped_autonomy_session_contracts.py",
        "tests/test_m62_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M62 forbidden scoped session fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M62 scoped autonomy session is contract-only, route-free, no-session-start, and no-authority")


def verify_m63_autonomy_policy_engine():
    print("\n[Verifier] Running M63 autonomy policy engine guard...")
    required_files = [
        "src/ultimate_ai_agent/core/autonomy/policies.py",
        "docs/autonomy/AUTONOMY_POLICY_ENGINE_V1.md",
        "docs/autonomy/AUTONOMY_POLICY_RULE_CONTRACTS.md",
        "docs/autonomy/AUTONOMY_POLICY_ENGINE_NON_GOALS.md",
        "docs/autonomy/M63_TO_M64_BOUNDARY.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/release_notes/v0_67_0.md",
        "docs/archive/releases/v0_67_0/README_IMPORT.md",
        "docs/archive/releases/v0_67_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_67_0.md",
        "tests/test_m63_autonomy_policy_engine_contracts.py",
        "tests/test_m63_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M63 autonomy policy engine file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "autonomy policy engine v1",
        "contract-only",
        "review-only",
        "policy rules",
        "actor-bound",
        "resource-bound",
        "capability-bound",
        "allowlist",
        "risk ceiling",
        "duration ceiling",
        "revocation",
        "audit/replay",
        "approval refs are identifiers",
        "no policy activation",
        "no session start",
        "no autonomous actions",
        "no background worker",
        "no execution",
        "no tool execution",
        "no shell execution",
        "no network tools",
        "no browser automation",
        "no backend route",
        "no dependency",
        "m64 remains future",
        "skill package security rule",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M63 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.autonomy import (
            AutonomyAuthorityMode,
            AutonomyPolicyEvaluationRequest,
            AutonomyPolicyEnginePolicy,
            AutonomyPolicyRule,
            AutonomyRiskClass,
            ScopedAutonomySessionRequest,
            ScopedAutonomySessionScope,
            build_autonomy_policy_decision,
            validate_autonomy_policy_evaluation_request,
            validate_autonomy_policy_rule,
        )
        from ultimate_ai_agent.core.gate.evaluators import m63_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M63 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m63_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    scope = ScopedAutonomySessionScope(
        scope_ref="autonomy-session-scope:verify-all-m63",
        actor_ref="actor:verify-all-reviewer",
        resource_refs=["resource:local-prototype"],
        capability_refs=["capability:observe-only-review"],
        allowlist_refs=["allowlist:verify-all-m63"],
        max_duration_seconds=900,
        risk_class=AutonomyRiskClass.low,
        revocation_ref="revocation:verify-all-m63",
        audit_ref="audit:verify-all-m63",
        replay_ref="replay:verify-all-m63",
    )
    request = ScopedAutonomySessionRequest(
        session_request_ref="autonomy-session-request:verify-all-m63",
        requested_mode=AutonomyAuthorityMode.dry_run_plan,
        scope=scope,
        approval_ref="approval:m63-review-only",
    )
    rule = AutonomyPolicyRule(
        rule_ref="autonomy-policy-rule:verify-all-m63",
        allowed_actor_refs=["actor:verify-all-reviewer"],
        allowed_resource_refs=["resource:local-prototype"],
        allowed_capability_refs=["capability:observe-only-review"],
        required_allowlist_refs=["allowlist:verify-all-m63"],
        max_mode=AutonomyAuthorityMode.dry_run_plan,
        max_risk_class=AutonomyRiskClass.low,
        max_duration_seconds=900,
    )
    validate_autonomy_policy_rule(rule)
    evaluation_request = AutonomyPolicyEvaluationRequest(
        evaluation_request_ref="autonomy-policy-evaluation:verify-all-m63",
        policy=AutonomyPolicyEnginePolicy(
            policy_ref="autonomy-policy:verify-all-m63",
            policy_version_ref="autonomy-policy-version:m63-v1",
            rules=[rule],
        ),
        session_request=request,
    )
    validate_autonomy_policy_evaluation_request(evaluation_request)
    decision = build_autonomy_policy_decision(evaluation_request)
    if decision.authority_granted or decision.session_started or decision.execution_performed or decision.side_effects_performed:
        print("FAIL: M63 autonomy policy decision granted authority or side effects")
        sys.exit(1)

    for update, reason in [
        ({"approval_test_ref": "approval_test_:m63"}, "APPROVAL_TEST_REF_DENIED"),
        ({"policy_activation_requested": True}, "AUTONOMY_POLICY_ACTIVATION_DENIED"),
        ({"session_start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
        ({"execution_requested": True}, "EXECUTION_DENIED"),
    ]:
        try:
            validate_autonomy_policy_evaluation_request(evaluation_request.model_copy(update=update))
            print(f"FAIL: M63 unsafe policy request mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M63 unsafe policy request reason drifted for {reason}: {exc}")
                sys.exit(1)

    forbidden_source_fragments = [
        "policy_activation_enabled=True",
        "policy_activation_requested=True",
        "session_start_enabled=True",
        "session_activation_enabled=True",
        "start_requested=True",
        "session_active=True",
        "execution_requested=True",
        "autonomous_actions_enabled=True",
        "background_worker_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_tool_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "production_authority_enabled=True",
        "authority_granted=True",
        "execution_performed=True",
        "/autonomy/policy/evaluate",
        "/autonomy/policy/activate",
        "/autonomy/session/start",
        "/autonomy/execute",
        "/background/start",
        "/network/fetch",
        "/shell/execute",
        "/browser/click",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/autonomy/policies.py",
        "src/ultimate_ai_agent/core/autonomy/sessions.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m63_autonomy_policy_engine_contracts.py",
        "tests/test_m63_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M63 forbidden autonomy policy fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M63 autonomy policy engine is contract-only, route-free, no-policy-activation, and no-authority")


def verify_m64_autonomous_plan_simulator():
    print("\n[Verifier] Running M64 autonomous plan simulator guard...")
    required_files = [
        "src/ultimate_ai_agent/core/autonomy/simulator.py",
        "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR.md",
        "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_CONTRACTS.md",
        "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_NON_GOALS.md",
        "docs/autonomy/M64_TO_M65_BOUNDARY.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/release_notes/v0_68_0.md",
        "docs/archive/releases/v0_68_0/README_IMPORT.md",
        "docs/archive/releases/v0_68_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_68_0.md",
        "tests/test_m64_autonomous_plan_simulator_contracts.py",
        "tests/test_m64_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M64 autonomous plan simulator file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "autonomous plan simulator",
        "contract-only",
        "review-only",
        "dry-run-only",
        "deterministic",
        "dependency graph",
        "acyclic",
        "policy decision",
        "approval refs are identifiers",
        "no policy activation",
        "no session start",
        "no autonomous actions",
        "no background worker",
        "no execution",
        "no tool execution",
        "no shell execution",
        "no network tools",
        "no browser automation",
        "no backend route",
        "no dependency",
        "m65 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M64 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.autonomy import (
            AutonomyAuthorityMode,
            AutonomyPolicyEvaluationRequest,
            AutonomyPolicyEnginePolicy,
            AutonomyPolicyRule,
            AutonomyRiskClass,
            AutonomousPlanSimulationRequest,
            AutonomousPlanSimulationStep,
            ScopedAutonomySessionRequest,
            ScopedAutonomySessionScope,
            build_autonomous_plan_simulation_result,
            build_autonomy_policy_decision,
            validate_autonomous_plan_simulation_request,
        )
        from ultimate_ai_agent.core.gate.evaluators import m64_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M64 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m64_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    scope = ScopedAutonomySessionScope(
        scope_ref="autonomy-session-scope:verify-all-m64",
        actor_ref="actor:verify-all-reviewer",
        resource_refs=["resource:local-prototype"],
        capability_refs=["capability:observe-only-review"],
        allowlist_refs=["allowlist:verify-all-m64"],
        max_duration_seconds=900,
        risk_class=AutonomyRiskClass.low,
        revocation_ref="revocation:verify-all-m64",
        audit_ref="audit:verify-all-m64",
        replay_ref="replay:verify-all-m64",
    )
    session_request = ScopedAutonomySessionRequest(
        session_request_ref="autonomy-session-request:verify-all-m64",
        requested_mode=AutonomyAuthorityMode.dry_run_plan,
        scope=scope,
    )
    rule = AutonomyPolicyRule(
        rule_ref="autonomy-policy-rule:verify-all-m64",
        allowed_actor_refs=["actor:verify-all-reviewer"],
        allowed_resource_refs=["resource:local-prototype"],
        allowed_capability_refs=["capability:observe-only-review"],
        required_allowlist_refs=["allowlist:verify-all-m64"],
        max_mode=AutonomyAuthorityMode.dry_run_plan,
        max_risk_class=AutonomyRiskClass.low,
        max_duration_seconds=900,
    )
    policy_decision = build_autonomy_policy_decision(
        AutonomyPolicyEvaluationRequest(
            evaluation_request_ref="autonomy-policy-evaluation:verify-all-m64",
            policy=AutonomyPolicyEnginePolicy(
                policy_ref="autonomy-policy:verify-all-m64",
                policy_version_ref="autonomy-policy-version:m64-v1",
                rules=[rule],
            ),
            session_request=session_request,
        )
    )
    request = AutonomousPlanSimulationRequest(
        simulation_request_ref="autonomy-plan-simulation-request:verify-all-m64",
        policy_decision=policy_decision,
        steps=[
            AutonomousPlanSimulationStep(
                step_ref="autonomy-simulation-step:verify-all-m64",
                intent_ref="intent:inspect-redacted-review-packet",
                capability_ref="capability:observe-only-review",
                resource_ref="resource:local-prototype",
                simulated_outcome_ref="simulation-outcome:m64-review-only",
            )
        ],
        actor_ref="actor:verify-all-reviewer",
        resource_refs=["resource:local-prototype"],
        capability_refs=["capability:observe-only-review"],
        allowlist_refs=["allowlist:verify-all-m64"],
        audit_ref="audit:verify-all-m64",
        replay_ref="replay:verify-all-m64",
    )
    validate_autonomous_plan_simulation_request(request)
    result = build_autonomous_plan_simulation_result(request)
    if result.authority_granted or result.session_started or result.execution_performed or result.side_effects_performed:
        print("FAIL: M64 autonomous plan simulator granted authority or side effects")
        sys.exit(1)
    for update, reason in [
        ({"approval_test_ref": "approval_test_:m64"}, "APPROVAL_TEST_REF_DENIED"),
        ({"policy_activation_requested": True}, "AUTONOMY_POLICY_ACTIVATION_DENIED"),
        ({"session_start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
        ({"execution_requested": True}, "EXECUTION_DENIED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
    ]:
        try:
            validate_autonomous_plan_simulation_request(request.model_copy(update=update))
            print(f"FAIL: M64 unsafe simulation mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M64 unsafe simulation reason drifted for {reason}: {exc}")
                sys.exit(1)

    forbidden_source_fragments = [
        "policy_activation_enabled=True",
        "policy_activation_requested=True",
        "session_start_enabled=True",
        "session_start_requested=True",
        "session_active=True",
        "execution_requested=True",
        "execution_performed=True",
        "autonomous_actions_enabled=True",
        "background_worker_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_tool_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "production_authority_enabled=True",
        "authority_granted=True",
        "/autonomy/simulate",
        "/autonomy/simulator/run",
        "/autonomy/execute",
        "/background/start",
        "/network/fetch",
        "/shell/execute",
        "/browser/click",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/autonomy/policies.py",
        "src/ultimate_ai_agent/core/autonomy/sessions.py",
        "src/ultimate_ai_agent/core/autonomy/simulator.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m64_autonomous_plan_simulator_contracts.py",
        "tests/test_m64_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M64 forbidden autonomy simulation fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M64 autonomous plan simulator is contract-only, route-free, dry-run-only, and no-authority")


def verify_m65_autonomy_audit_replay_viewer():
    print("\n[Verifier] Running M65 autonomy audit replay viewer guard...")
    required_files = [
        "src/ultimate_ai_agent/core/autonomy/audit.py",
        "docs/autonomy/AUTONOMY_AUDIT_REPLAY_VIEWER.md",
        "docs/autonomy/AUTONOMY_AUDIT_REPLAY_CONTRACTS.md",
        "docs/autonomy/AUTONOMY_AUDIT_REPLAY_NON_GOALS.md",
        "docs/autonomy/M65_TO_M66_BOUNDARY.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/release_notes/v0_69_0.md",
        "docs/archive/releases/v0_69_0/README_IMPORT.md",
        "docs/archive/releases/v0_69_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_69_0.md",
        "tests/test_m65_autonomy_audit_replay_viewer_contracts.py",
        "tests/test_m65_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M65 autonomy audit replay viewer file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "autonomy audit",
        "replay viewer",
        "contract-only",
        "review-only",
        "replay-view-only",
        "deterministic",
        "exact simulation result",
        "exact replay step",
        "approval refs are identifiers",
        "no policy activation",
        "no session start",
        "no autonomous actions",
        "no background worker",
        "no execution",
        "no tool execution",
        "no shell execution",
        "no network tools",
        "no browser automation",
        "no backend route",
        "no dependency",
        "m66 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M65 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.autonomy import (
            AutonomyAuthorityMode,
            AutonomyPolicyEvaluationRequest,
            AutonomyPolicyEnginePolicy,
            AutonomyPolicyRule,
            AutonomyRiskClass,
            AutonomousPlanSimulationRequest,
            AutonomousPlanSimulationStep,
            ScopedAutonomySessionRequest,
            ScopedAutonomySessionScope,
            build_autonomous_plan_simulation_result,
            build_autonomy_audit_replay_view,
            build_autonomy_policy_decision,
            validate_autonomy_audit_replay_view,
        )
        from ultimate_ai_agent.core.gate.evaluators import m65_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M65 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m65_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    scope = ScopedAutonomySessionScope(
        scope_ref="autonomy-session-scope:verify-all-m65",
        actor_ref="actor:verify-all-reviewer",
        resource_refs=["resource:local-prototype"],
        capability_refs=["capability:observe-only-review"],
        allowlist_refs=["allowlist:verify-all-m65"],
        max_duration_seconds=900,
        risk_class=AutonomyRiskClass.low,
        revocation_ref="revocation:verify-all-m65",
        audit_ref="audit:verify-all-m65",
        replay_ref="replay:verify-all-m65",
    )
    session_request = ScopedAutonomySessionRequest(
        session_request_ref="autonomy-session-request:verify-all-m65",
        requested_mode=AutonomyAuthorityMode.dry_run_plan,
        scope=scope,
    )
    rule = AutonomyPolicyRule(
        rule_ref="autonomy-policy-rule:verify-all-m65",
        allowed_actor_refs=["actor:verify-all-reviewer"],
        allowed_resource_refs=["resource:local-prototype"],
        allowed_capability_refs=["capability:observe-only-review"],
        required_allowlist_refs=["allowlist:verify-all-m65"],
        max_mode=AutonomyAuthorityMode.dry_run_plan,
        max_risk_class=AutonomyRiskClass.low,
        max_duration_seconds=900,
    )
    policy_decision = build_autonomy_policy_decision(
        AutonomyPolicyEvaluationRequest(
            evaluation_request_ref="autonomy-policy-evaluation:verify-all-m65",
            policy=AutonomyPolicyEnginePolicy(
                policy_ref="autonomy-policy:verify-all-m65",
                policy_version_ref="autonomy-policy-version:m65-v1",
                rules=[rule],
            ),
            session_request=session_request,
        )
    )
    simulation_result = build_autonomous_plan_simulation_result(
        AutonomousPlanSimulationRequest(
            simulation_request_ref="autonomy-plan-simulation-request:verify-all-m65",
            policy_decision=policy_decision,
            steps=[
                AutonomousPlanSimulationStep(
                    step_ref="autonomy-simulation-step:verify-all-m65",
                    intent_ref="intent:inspect-redacted-review-packet",
                    capability_ref="capability:observe-only-review",
                    resource_ref="resource:local-prototype",
                    simulated_outcome_ref="simulation-outcome:m65-review-only",
                )
            ],
            actor_ref="actor:verify-all-reviewer",
            resource_refs=["resource:local-prototype"],
            capability_refs=["capability:observe-only-review"],
            allowlist_refs=["allowlist:verify-all-m65"],
            audit_ref="audit:verify-all-m65",
            replay_ref="replay:verify-all-m65",
        )
    )
    view = build_autonomy_audit_replay_view(
        audit_view_ref="autonomy-audit-replay-view:verify-all-m65",
        simulation_result=simulation_result,
        actor_ref="actor:verify-all-reviewer",
        audit_ref="audit:verify-all-m65",
        replay_ref="replay:verify-all-m65",
    )
    if view.authority_granted or view.session_started or view.execution_performed or view.side_effects_performed:
        print("FAIL: M65 autonomy audit replay viewer granted authority or side effects")
        sys.exit(1)
    if view.simulation_result_ref != simulation_result.simulation_result_ref:
        print("FAIL: M65 replay view did not bind exact simulation result")
        sys.exit(1)
    for update, reason in [
        ({"approval_test_ref": "approval_test_:m65"}, "APPROVAL_TEST_REF_DENIED"),
        ({"policy_activation_requested": True}, "AUTONOMY_POLICY_ACTIVATION_DENIED"),
        ({"session_start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
        ({"execution_requested": True}, "EXECUTION_DENIED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"model_provider_call_enabled": True}, "MODEL_PROVIDER_CALL_DENIED"),
        ({"metadata": {"api_key": "secret-value"}}, "SECRET_LIKE_AUTONOMY_AUDIT_REPLAY_CONTENT_DENIED"),
    ]:
        try:
            validate_autonomy_audit_replay_view(view.model_copy(update=update))
            print(f"FAIL: M65 unsafe replay view mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M65 unsafe replay view reason drifted for {reason}: {exc}")
                sys.exit(1)

    forbidden_source_fragments = [
        "policy_activation_enabled=True",
        "policy_activation_requested=True",
        "session_start_enabled=True",
        "session_start_requested=True",
        "session_active=True",
        "execution_requested=True",
        "execution_performed=True",
        "autonomous_actions_enabled=True",
        "background_worker_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_tool_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "model_provider_call_enabled=True",
        "production_authority_enabled=True",
        "authority_granted=True",
        "/autonomy/audit/replay",
        "/autonomy/replay/run",
        "/autonomy/replay/execute",
        "/autonomy/audit/export",
        "/autonomy/execute",
        "/background/start",
        "/network/fetch",
        "/shell/execute",
        "/browser/click",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/autonomy/audit.py",
        "src/ultimate_ai_agent/core/autonomy/policies.py",
        "src/ultimate_ai_agent/core/autonomy/sessions.py",
        "src/ultimate_ai_agent/core/autonomy/simulator.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m65_autonomy_audit_replay_viewer_contracts.py",
        "tests/test_m65_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M65 forbidden autonomy audit replay fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M65 autonomy audit replay viewer is contract-only, route-free, replay-view-only, and no-authority")


def verify_m66_scoped_approval_bundles():
    print("\n[Verifier] Running M66 scoped approval bundles guard...")
    required_files = [
        "src/ultimate_ai_agent/core/autonomy/approvals.py",
        "docs/autonomy/SCOPED_APPROVAL_BUNDLES.md",
        "docs/autonomy/SCOPED_APPROVAL_BUNDLE_CONTRACTS.md",
        "docs/autonomy/SCOPED_APPROVAL_BUNDLE_NON_GOALS.md",
        "docs/autonomy/M66_TO_M67_BOUNDARY.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/release_notes/v0_70_0.md",
        "docs/archive/releases/v0_70_0/README_IMPORT.md",
        "docs/archive/releases/v0_70_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_70_0.md",
        "tests/test_m66_scoped_approval_bundles.py",
        "tests/test_m66_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M66 scoped approval bundle file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "scoped approval bundles",
        "contract-only",
        "review-only",
        "exact-scope",
        "actor-bound",
        "resource-bound",
        "capability-bound",
        "allowlist-bound",
        "non-transferable",
        "revocable",
        "replay-safe",
        "approval refs are identifiers",
        "no policy activation",
        "no session start",
        "no autonomous actions",
        "no background worker",
        "no execution",
        "no tool execution",
        "no shell execution",
        "no network tools",
        "no browser automation",
        "no backend route",
        "no dependency",
        "m67 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M66 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.autonomy import (
            AutonomyAuthorityMode,
            AutonomyPolicyEvaluationRequest,
            AutonomyPolicyEnginePolicy,
            AutonomyPolicyRule,
            AutonomyRiskClass,
            AutonomousPlanSimulationRequest,
            AutonomousPlanSimulationStep,
            ScopedAutonomySessionRequest,
            ScopedAutonomySessionScope,
            build_autonomous_plan_simulation_result,
            build_autonomy_audit_replay_view,
            build_autonomy_policy_decision,
            build_scoped_approval_bundle,
            validate_scoped_approval_bundle,
        )
        from ultimate_ai_agent.core.gate.evaluators import m66_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M66 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m66_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    scope = ScopedAutonomySessionScope(
        scope_ref="autonomy-session-scope:verify-all-m66",
        actor_ref="actor:verify-all-reviewer",
        resource_refs=["resource:local-prototype"],
        capability_refs=["capability:observe-only-review"],
        allowlist_refs=["allowlist:verify-all-m66"],
        max_duration_seconds=900,
        risk_class=AutonomyRiskClass.low,
        revocation_ref="revocation:verify-all-m66",
        audit_ref="audit:verify-all-m66",
        replay_ref="replay:verify-all-m66",
    )
    policy_decision = build_autonomy_policy_decision(
        AutonomyPolicyEvaluationRequest(
            evaluation_request_ref="autonomy-policy-evaluation:verify-all-m66",
            policy=AutonomyPolicyEnginePolicy(
                policy_ref="autonomy-policy:verify-all-m66",
                policy_version_ref="autonomy-policy-version:m66-v1",
                rules=[
                    AutonomyPolicyRule(
                        rule_ref="autonomy-policy-rule:verify-all-m66",
                        allowed_actor_refs=["actor:verify-all-reviewer"],
                        allowed_resource_refs=["resource:local-prototype"],
                        allowed_capability_refs=["capability:observe-only-review"],
                        required_allowlist_refs=["allowlist:verify-all-m66"],
                        max_mode=AutonomyAuthorityMode.dry_run_plan,
                        max_risk_class=AutonomyRiskClass.low,
                        max_duration_seconds=900,
                    )
                ],
            ),
            session_request=ScopedAutonomySessionRequest(
                session_request_ref="autonomy-session-request:verify-all-m66",
                requested_mode=AutonomyAuthorityMode.dry_run_plan,
                scope=scope,
            ),
        )
    )
    simulation_result = build_autonomous_plan_simulation_result(
        AutonomousPlanSimulationRequest(
            simulation_request_ref="autonomy-plan-simulation-request:verify-all-m66",
            policy_decision=policy_decision,
            steps=[
                AutonomousPlanSimulationStep(
                    step_ref="autonomy-simulation-step:verify-all-m66",
                    intent_ref="intent:inspect-redacted-review-packet",
                    capability_ref="capability:observe-only-review",
                    resource_ref="resource:local-prototype",
                    simulated_outcome_ref="simulation-outcome:m66-review-only",
                )
            ],
            actor_ref="actor:verify-all-reviewer",
            resource_refs=["resource:local-prototype"],
            capability_refs=["capability:observe-only-review"],
            allowlist_refs=["allowlist:verify-all-m66"],
            audit_ref="audit:verify-all-m66",
            replay_ref="replay:verify-all-m66",
        )
    )
    replay_view = build_autonomy_audit_replay_view(
        audit_view_ref="autonomy-audit-replay-view:verify-all-m66",
        simulation_result=simulation_result,
        actor_ref="actor:verify-all-reviewer",
        audit_ref="audit:verify-all-m66",
        replay_ref="replay:verify-all-m66",
    )
    bundle = build_scoped_approval_bundle(
        bundle_ref="scoped-approval-bundle:verify-all-m66",
        source_scope=scope,
        audit_replay_view=replay_view,
        approval_refs=["approval:verify-all-m66-review", "approval:verify-all-m66-dry-run"],
        actor_ref="actor:verify-all-reviewer",
        resource_refs=["resource:local-prototype"],
        capability_refs=["capability:observe-only-review"],
        allowlist_refs=["allowlist:verify-all-m66"],
        max_duration_seconds=900,
        risk_class=AutonomyRiskClass.low,
        revocation_ref="revocation:verify-all-m66",
        audit_ref="audit:verify-all-m66",
        replay_ref="replay:verify-all-m66",
    )
    if bundle.authority_granted or bundle.session_started or bundle.execution_performed or bundle.side_effects_performed:
        print("FAIL: M66 scoped approval bundle granted authority or side effects")
        sys.exit(1)
    for update, reason in [
        ({"approval_test_ref": "approval_test_:m66"}, "APPROVAL_TEST_REF_DENIED"),
        ({"approval_refs": ["approval:verify-all-m66-review", "approval:verify-all-m66-review"]}, "APPROVAL_BUNDLE_DUPLICATE_REF_DENIED"),
        ({"revoked": True}, "APPROVAL_BUNDLE_REVOKED_DENIED"),
        ({"expired": True}, "APPROVAL_BUNDLE_EXPIRED_DENIED"),
        ({"replay_used": True}, "APPROVAL_BUNDLE_REPLAY_DENIED"),
        ({"authority_granted": True}, "AUTONOMY_POLICY_AUTHORITY_DENIED"),
        ({"execution_requested": True}, "EXECUTION_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"metadata": {"api_key": "secret-value"}}, "SECRET_LIKE_SCOPED_APPROVAL_BUNDLE_CONTENT_DENIED"),
    ]:
        try:
            validate_scoped_approval_bundle(bundle.model_copy(update=update))
            print(f"FAIL: M66 unsafe approval bundle mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M66 unsafe approval bundle reason drifted for {reason}: {exc}")
                sys.exit(1)

    forbidden_source_fragments = [
        "policy_activation_enabled=True",
        "policy_activation_requested=True",
        "session_start_enabled=True",
        "session_start_requested=True",
        "session_active=True",
        "execution_requested=True",
        "execution_performed=True",
        "autonomous_actions_enabled=True",
        "background_worker_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_tool_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "model_provider_call_enabled=True",
        "production_authority_enabled=True",
        "authority_granted=True",
        "/autonomy/approval-bundles",
        "/autonomy/approval-bundles/grant",
        "/autonomy/approval-bundles/activate",
        "/autonomy/approval-bundles/execute",
        "/autonomy/execute",
        "/background/start",
        "/network/fetch",
        "/shell/execute",
        "/browser/click",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/autonomy/approvals.py",
        "src/ultimate_ai_agent/core/autonomy/audit.py",
        "src/ultimate_ai_agent/core/autonomy/policies.py",
        "src/ultimate_ai_agent/core/autonomy/sessions.py",
        "src/ultimate_ai_agent/core/autonomy/simulator.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m66_scoped_approval_bundles.py",
        "tests/test_m66_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M66 forbidden scoped approval bundle fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M66 scoped approval bundles are contract-only, route-free, exact-scope, and no-authority")


def verify_m67_revocation_kill_switch():
    print("\n[Verifier] Running M67 revocation kill switch guard...")
    required_files = [
        "src/ultimate_ai_agent/core/autonomy/revocation.py",
        "docs/autonomy/REVOCATION_KILL_SWITCH.md",
        "docs/autonomy/REVOCATION_KILL_SWITCH_CONTRACTS.md",
        "docs/autonomy/REVOCATION_KILL_SWITCH_NON_GOALS.md",
        "docs/autonomy/M67_TO_M68_BOUNDARY.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/release_notes/v0_71_0.md",
        "docs/archive/releases/v0_71_0/README_IMPORT.md",
        "docs/archive/releases/v0_71_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_71_0.md",
        "tests/test_m67_revocation_kill_switch.py",
        "tests/test_m67_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M67 revocation kill switch file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "revocation + kill switch",
        "contract-only",
        "review-only",
        "exact-bound",
        "scoped approval bundle",
        "revocation requested",
        "kill-switch requested",
        "approval refs are identifiers",
        "no revocation action",
        "no kill-switch activation",
        "no session stop",
        "no process kill",
        "no policy activation",
        "no session start",
        "no autonomous actions",
        "no background worker",
        "no execution",
        "no tool execution",
        "no shell execution",
        "no network tools",
        "no browser automation",
        "no backend route",
        "no dependency",
        "m68 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M67 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.autonomy import (
            AutonomyAuthorityMode,
            AutonomyPolicyEvaluationRequest,
            AutonomyPolicyEnginePolicy,
            AutonomyPolicyRule,
            AutonomyRiskClass,
            AutonomousPlanSimulationRequest,
            AutonomousPlanSimulationStep,
            ScopedAutonomySessionRequest,
            ScopedAutonomySessionScope,
            build_autonomous_plan_simulation_result,
            build_autonomy_audit_replay_view,
            build_autonomy_policy_decision,
            build_revocation_kill_switch_record,
            build_scoped_approval_bundle,
            validate_revocation_kill_switch_record,
        )
        from ultimate_ai_agent.core.gate.evaluators import m67_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M67 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m67_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    scope = ScopedAutonomySessionScope(
        scope_ref="autonomy-session-scope:verify-all-m67",
        actor_ref="actor:verify-all-reviewer",
        resource_refs=["resource:local-prototype"],
        capability_refs=["capability:observe-only-review"],
        allowlist_refs=["allowlist:verify-all-m67"],
        max_duration_seconds=900,
        risk_class=AutonomyRiskClass.low,
        revocation_ref="revocation:verify-all-m67",
        audit_ref="audit:verify-all-m67",
        replay_ref="replay:verify-all-m67",
    )
    policy_decision = build_autonomy_policy_decision(
        AutonomyPolicyEvaluationRequest(
            evaluation_request_ref="autonomy-policy-evaluation:verify-all-m67",
            policy=AutonomyPolicyEnginePolicy(
                policy_ref="autonomy-policy:verify-all-m67",
                policy_version_ref="autonomy-policy-version:m67-v1",
                rules=[
                    AutonomyPolicyRule(
                        rule_ref="autonomy-policy-rule:verify-all-m67",
                        allowed_actor_refs=["actor:verify-all-reviewer"],
                        allowed_resource_refs=["resource:local-prototype"],
                        allowed_capability_refs=["capability:observe-only-review"],
                        required_allowlist_refs=["allowlist:verify-all-m67"],
                        max_mode=AutonomyAuthorityMode.dry_run_plan,
                        max_risk_class=AutonomyRiskClass.low,
                        max_duration_seconds=900,
                    )
                ],
            ),
            session_request=ScopedAutonomySessionRequest(
                session_request_ref="autonomy-session-request:verify-all-m67",
                requested_mode=AutonomyAuthorityMode.dry_run_plan,
                scope=scope,
            ),
        )
    )
    simulation_result = build_autonomous_plan_simulation_result(
        AutonomousPlanSimulationRequest(
            simulation_request_ref="autonomy-plan-simulation-request:verify-all-m67",
            policy_decision=policy_decision,
            steps=[
                AutonomousPlanSimulationStep(
                    step_ref="autonomy-simulation-step:verify-all-m67",
                    intent_ref="intent:inspect-redacted-review-packet",
                    capability_ref="capability:observe-only-review",
                    resource_ref="resource:local-prototype",
                    simulated_outcome_ref="simulation-outcome:m67-review-only",
                )
            ],
            actor_ref="actor:verify-all-reviewer",
            resource_refs=["resource:local-prototype"],
            capability_refs=["capability:observe-only-review"],
            allowlist_refs=["allowlist:verify-all-m67"],
            audit_ref="audit:verify-all-m67",
            replay_ref="replay:verify-all-m67",
        )
    )
    replay_view = build_autonomy_audit_replay_view(
        audit_view_ref="autonomy-audit-replay-view:verify-all-m67",
        simulation_result=simulation_result,
        actor_ref="actor:verify-all-reviewer",
        audit_ref="audit:verify-all-m67",
        replay_ref="replay:verify-all-m67",
    )
    bundle = build_scoped_approval_bundle(
        bundle_ref="scoped-approval-bundle:verify-all-m67",
        source_scope=scope,
        audit_replay_view=replay_view,
        approval_refs=["approval:verify-all-m67-review", "approval:verify-all-m67-dry-run"],
        actor_ref="actor:verify-all-reviewer",
        resource_refs=["resource:local-prototype"],
        capability_refs=["capability:observe-only-review"],
        allowlist_refs=["allowlist:verify-all-m67"],
        max_duration_seconds=900,
        risk_class=AutonomyRiskClass.low,
        revocation_ref="revocation:verify-all-m67",
        audit_ref="audit:verify-all-m67",
        replay_ref="replay:verify-all-m67",
    )
    record = build_revocation_kill_switch_record(
        revocation_record_ref="revocation-kill-switch-record:verify-all-m67",
        approval_bundle=bundle,
        actor_ref="actor:verify-all-reviewer",
        resource_refs=["resource:local-prototype"],
        capability_refs=["capability:observe-only-review"],
        allowlist_refs=["allowlist:verify-all-m67"],
        bundle_ref="scoped-approval-bundle:verify-all-m67",
        source_scope_ref="autonomy-session-scope:verify-all-m67",
        audit_view_ref="autonomy-audit-replay-view:verify-all-m67",
        simulation_result_ref="autonomy-plan-simulation-result:verify-all-m67",
        revocation_ref="revocation:verify-all-m67",
        audit_ref="audit:verify-all-m67",
        replay_ref="replay:verify-all-m67",
    )
    if record.authority_granted or record.revocation_performed or record.kill_switch_activated or record.session_stopped or record.execution_performed or record.side_effects_performed:
        print("FAIL: M67 revocation kill switch record granted authority or side effects")
        sys.exit(1)
    for update, reason in [
        ({"approval_test_ref": "approval_test_:m67"}, "APPROVAL_TEST_REF_DENIED"),
        ({"kill_switch_activated": True}, "KILL_SWITCH_ACTIVATION_DENIED"),
        ({"revocation_performed": True}, "REVOCATION_ACTION_DENIED"),
        ({"session_stopped": True}, "AUTONOMY_SESSION_STOP_DENIED"),
        ({"authority_granted": True}, "AUTONOMY_POLICY_AUTHORITY_DENIED"),
        ({"execution_requested": True}, "EXECUTION_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"metadata": {"api_key": "secret-value"}}, "SECRET_LIKE_REVOCATION_KILL_SWITCH_CONTENT_DENIED"),
    ]:
        try:
            validate_revocation_kill_switch_record(record.model_copy(update=update))
            print(f"FAIL: M67 unsafe revocation kill switch mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M67 unsafe revocation kill switch reason drifted for {reason}: {exc}")
                sys.exit(1)

    forbidden_source_fragments = [
        "kill_switch_activated=True",
        "revocation_performed=True",
        "session_stopped=True",
        "policy_activation_enabled=True",
        "policy_activation_requested=True",
        "session_start_enabled=True",
        "session_start_requested=True",
        "session_active=True",
        "execution_requested=True",
        "execution_performed=True",
        "autonomous_actions_enabled=True",
        "background_worker_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_tool_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "model_provider_call_enabled=True",
        "production_authority_enabled=True",
        "authority_granted=True",
        "/autonomy/revoke",
        "/autonomy/revocation/execute",
        "/autonomy/kill-switch",
        "/autonomy/kill-switch/activate",
        "/autonomy/session/stop",
        "/autonomy/session/terminate",
        "/process/kill",
        "/autonomy/execute",
        "/background/start",
        "/network/fetch",
        "/shell/execute",
        "/browser/click",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/autonomy/revocation.py",
        "src/ultimate_ai_agent/core/autonomy/approvals.py",
        "src/ultimate_ai_agent/core/autonomy/audit.py",
        "src/ultimate_ai_agent/core/autonomy/policies.py",
        "src/ultimate_ai_agent/core/autonomy/sessions.py",
        "src/ultimate_ai_agent/core/autonomy/simulator.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m67_revocation_kill_switch.py",
        "tests/test_m67_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M67 forbidden revocation kill switch fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M67 revocation kill switch is contract-only, route-free, exact-bound, and no-authority")


def verify_m68_autonomy_risk_classifier():
    print("\n[Verifier] Running M68 autonomy risk classifier guard...")
    required_files = [
        "src/ultimate_ai_agent/core/autonomy/risk.py",
        "docs/autonomy/AUTONOMY_RISK_CLASSIFIER.md",
        "docs/autonomy/AUTONOMY_RISK_CLASSIFIER_CONTRACTS.md",
        "docs/autonomy/AUTONOMY_RISK_CLASSIFIER_NON_GOALS.md",
        "docs/autonomy/M68_TO_M69_BOUNDARY.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/release_notes/v0_72_0.md",
        "docs/archive/releases/v0_72_0/README_IMPORT.md",
        "docs/archive/releases/v0_72_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_72_0.md",
        "tests/test_m68_autonomy_risk_classifier.py",
        "tests/test_m68_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M68 autonomy risk classifier file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "autonomy risk classifier",
        "contract-only",
        "review-only",
        "deterministic",
        "highest risk",
        "declared risk",
        "scoped approval bundle risk",
        "explicit risk signals",
        "risk downgrade is denied",
        "revocation + kill switch",
        "approval refs are identifiers",
        "evaluator boundaries revalidate",
        "no policy activation",
        "no session start",
        "no autonomous actions",
        "no background worker",
        "no execution",
        "no tool execution",
        "no shell execution",
        "no network tools",
        "no browser automation",
        "no backend route",
        "no dependency",
        "m69 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M68 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.autonomy import (
            AutonomyRiskClass,
            AutonomyRiskSignal,
            AutonomyRiskSignalKind,
            build_autonomy_risk_classification_decision,
            validate_autonomy_risk_classification_decision,
        )
        from ultimate_ai_agent.core.gate.evaluators import m68_openapi_route_failures

        test_spec = importlib.util.spec_from_file_location(
            "uaa_m68_contract_helpers",
            ROOT / "tests" / "test_m68_autonomy_risk_classifier.py",
        )
        if test_spec is None or test_spec.loader is None:
            print("FAIL: M68 contract helper test module could not be loaded")
            sys.exit(1)
        test_module = importlib.util.module_from_spec(test_spec)
        sys.modules[test_spec.name] = test_module
        test_spec.loader.exec_module(test_module)
    except Exception as exc:
        print(f"FAIL: M68 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m68_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    decision = build_autonomy_risk_classification_decision(
        test_module._request(declared_risk_class=AutonomyRiskClass.low)
    )
    if (
        decision.authority_granted
        or decision.risk_authority_granted
        or decision.policy_activation_requested
        or decision.session_start_requested
        or decision.execution_performed
        or decision.side_effects_performed
    ):
        print("FAIL: M68 autonomy risk classifier granted authority or side effects")
        sys.exit(1)
    if decision.derived_risk_class != AutonomyRiskClass.low:
        print("FAIL: M68 baseline classifier did not preserve low risk review result")
        sys.exit(1)

    elevated = build_autonomy_risk_classification_decision(
        test_module._request(
            declared_risk_class=AutonomyRiskClass.low,
            risk_signals=[
                AutonomyRiskSignal(
                    signal_ref="autonomy-risk-signal:verify-all-m68-critical",
                    signal_kind=AutonomyRiskSignalKind.shell_intent,
                    risk_class=AutonomyRiskClass.critical,
                    source_ref="intent:verify-all-shell-denied",
                    reason_code="M68_SIGNAL_SHELL_INTENT_CRITICAL",
                )
            ],
        )
    )
    if elevated.derived_risk_class != AutonomyRiskClass.critical:
        print("FAIL: M68 classifier did not derive highest risk from risk signals")
        sys.exit(1)

    for update, reason in [
        ({"derived_risk_class": AutonomyRiskClass.low}, "RISK_DOWNGRADE_DENIED"),
        ({"approval_test_ref": "approval_test_:m68"}, "APPROVAL_TEST_REF_DENIED"),
        ({"risk_authority_granted": True}, "AUTONOMY_RISK_CLASSIFIER_AUTHORITY_DENIED"),
        ({"policy_activation_requested": True}, "POLICY_ACTIVATION_DENIED"),
        ({"session_start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"execution_requested": True}, "EXECUTION_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"metadata": {"api_key": "secret-value"}}, "SECRET_LIKE_AUTONOMY_RISK_CONTENT_DENIED"),
    ]:
        try:
            validate_autonomy_risk_classification_decision(elevated.model_copy(update=update))
            print(f"FAIL: M68 unsafe autonomy risk mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M68 unsafe autonomy risk reason drifted for {reason}: {exc}")
                sys.exit(1)

    forbidden_source_fragments = [
        "risk_authority_granted=True",
        "policy_activation_enabled=True",
        "policy_activation_requested=True",
        "session_start_enabled=True",
        "session_start_requested=True",
        "session_active=True",
        "execution_requested=True",
        "execution_performed=True",
        "autonomous_actions_enabled=True",
        "background_worker_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_tool_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "model_provider_call_enabled=True",
        "production_authority_enabled=True",
        "authority_granted=True",
        "/autonomy/risk/classify",
        "/autonomy/risk/execute",
        "/autonomy/risk/activate",
        "/autonomy/session/start",
        "/autonomy/policy/activate",
        "/autonomy/execute",
        "/background/start",
        "/network/fetch",
        "/shell/execute",
        "/browser/click",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/autonomy/risk.py",
        "src/ultimate_ai_agent/core/autonomy/revocation.py",
        "src/ultimate_ai_agent/core/autonomy/approvals.py",
        "src/ultimate_ai_agent/core/autonomy/audit.py",
        "src/ultimate_ai_agent/core/autonomy/policies.py",
        "src/ultimate_ai_agent/core/autonomy/sessions.py",
        "src/ultimate_ai_agent/core/autonomy/simulator.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m68_autonomy_risk_classifier.py",
        "tests/test_m68_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M68 forbidden autonomy risk classifier fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M68 autonomy risk classifier is contract-only, route-free, highest-risk, and no-authority")


def verify_m69_low_risk_autonomous_dry_run():
    print("\n[Verifier] Running M69 low-risk autonomous dry-run guard...")
    required_files = [
        "src/ultimate_ai_agent/core/autonomy/dry_run.py",
        "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN.md",
        "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN_CONTRACTS.md",
        "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN_NON_GOALS.md",
        "docs/autonomy/M69_TO_M70_BOUNDARY.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/release_notes/v0_73_0.md",
        "docs/archive/releases/v0_73_0/README_IMPORT.md",
        "docs/archive/releases/v0_73_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_73_0.md",
        "tests/test_m69_low_risk_autonomous_dry_run.py",
        "tests/test_m69_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M69 low-risk autonomous dry-run file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "low-risk autonomous dry run",
        "contract-only",
        "review-only",
        "dry-run-only",
        "deterministic",
        "low risk",
        "risk ceiling",
        "autonomy risk classifier",
        "approval refs are identifiers",
        "evaluator boundaries revalidate",
        "no policy activation",
        "no session start",
        "no autonomous actions",
        "no background worker",
        "no execution",
        "no tool execution",
        "no shell execution",
        "no network tools",
        "no browser automation",
        "no backend route",
        "no dependency",
        "m70 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M69 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.autonomy import (
            AutonomyRiskClass,
            LowRiskAutonomousDryRunRequest,
            LowRiskAutonomousDryRunStep,
            build_low_risk_autonomous_dry_run_record,
            validate_low_risk_autonomous_dry_run_record,
        )
        from ultimate_ai_agent.core.gate.evaluators import m69_openapi_route_failures

        test_spec = importlib.util.spec_from_file_location(
            "uaa_m68_contract_helpers_for_m69",
            ROOT / "tests" / "test_m68_autonomy_risk_classifier.py",
        )
        if test_spec is None or test_spec.loader is None:
            print("FAIL: M69 contract helper test module could not be loaded")
            sys.exit(1)
        test_module = importlib.util.module_from_spec(test_spec)
        sys.modules[test_spec.name] = test_module
        test_spec.loader.exec_module(test_module)
    except Exception as exc:
        print(f"FAIL: M69 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m69_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    risk_decision = test_module._decision()
    record = build_low_risk_autonomous_dry_run_record(
        LowRiskAutonomousDryRunRequest(
            dry_run_request_ref="low-risk-autonomous-dry-run-request:verify-all-m69",
            risk_decision=risk_decision,
            risk_decision_ref=risk_decision.decision_ref,
            actor_ref=risk_decision.actor_ref,
            resource_refs=list(risk_decision.resource_refs),
            capability_refs=list(risk_decision.capability_refs),
            allowlist_refs=list(risk_decision.allowlist_refs),
            bundle_ref=risk_decision.bundle_ref,
            revocation_record_ref=risk_decision.revocation_record_ref,
            source_scope_ref=risk_decision.source_scope_ref,
            audit_ref=risk_decision.audit_ref,
            replay_ref=risk_decision.replay_ref,
            steps=[
                LowRiskAutonomousDryRunStep(
                    step_ref="low-risk-dry-run-step:verify-all-m69",
                    intent_ref="intent:inspect-redacted-review-packet",
                    capability_ref="capability:observe-only-review",
                    resource_ref="resource:local-prototype",
                    risk_class=AutonomyRiskClass.low,
                    dry_run_outcome_ref="dry-run-outcome:verify-all-m69",
                )
            ],
        )
    )
    if (
        record.authority_granted
        or record.low_risk_dry_run_authority_granted
        or record.policy_activation_requested
        or record.session_start_requested
        or record.background_worker_enabled
        or record.execution_requested
        or record.execution_performed
        or record.side_effects_performed
    ):
        print("FAIL: M69 low-risk autonomous dry-run granted authority or side effects")
        sys.exit(1)
    if record.derived_risk_class != AutonomyRiskClass.low:
        print("FAIL: M69 dry-run record did not preserve low risk")
        sys.exit(1)

    for update, reason in [
        ({"derived_risk_class": AutonomyRiskClass.medium}, "LOW_RISK_DRY_RUN_RISK_CEILING_DENIED"),
        ({"approval_test_ref": "approval_test_:m69"}, "APPROVAL_TEST_REF_DENIED"),
        ({"low_risk_dry_run_authority_granted": True}, "LOW_RISK_DRY_RUN_AUTHORITY_DENIED"),
        ({"policy_activation_requested": True}, "POLICY_ACTIVATION_DENIED"),
        ({"session_start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"execution_requested": True}, "EXECUTION_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"metadata": {"api_key": "secret-value"}}, "SECRET_LIKE_LOW_RISK_DRY_RUN_CONTENT_DENIED"),
    ]:
        try:
            validate_low_risk_autonomous_dry_run_record(record.model_copy(update=update))
            print(f"FAIL: M69 unsafe low-risk autonomous dry-run mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M69 unsafe low-risk autonomous dry-run reason drifted for {reason}: {exc}")
                sys.exit(1)

    try:
        high_risk_decision = test_module._decision(
            classification_request=test_module._request(
                declared_risk_class=AutonomyRiskClass.medium
            )
        )
        build_low_risk_autonomous_dry_run_record(
            LowRiskAutonomousDryRunRequest(
                dry_run_request_ref="low-risk-autonomous-dry-run-request:verify-all-m69-high-risk",
                risk_decision=high_risk_decision,
                risk_decision_ref=high_risk_decision.decision_ref,
                actor_ref=high_risk_decision.actor_ref,
                resource_refs=list(high_risk_decision.resource_refs),
                capability_refs=list(high_risk_decision.capability_refs),
                allowlist_refs=list(high_risk_decision.allowlist_refs),
                bundle_ref=high_risk_decision.bundle_ref,
                revocation_record_ref=high_risk_decision.revocation_record_ref,
                source_scope_ref=high_risk_decision.source_scope_ref,
                audit_ref=high_risk_decision.audit_ref,
                replay_ref=high_risk_decision.replay_ref,
                steps=[
                    LowRiskAutonomousDryRunStep(
                        step_ref="low-risk-dry-run-step:verify-all-m69-high-risk",
                        intent_ref="intent:inspect-redacted-review-packet",
                        capability_ref="capability:observe-only-review",
                        resource_ref="resource:local-prototype",
                        risk_class=AutonomyRiskClass.low,
                        dry_run_outcome_ref="dry-run-outcome:verify-all-m69-high-risk",
                    )
                ],
            )
        )
        print("FAIL: M69 accepted a higher-risk classifier decision")
        sys.exit(1)
    except ValueError as exc:
        if "LOW_RISK_DRY_RUN_RISK_CEILING_DENIED" not in str(exc):
            print(f"FAIL: M69 high-risk denial reason drifted: {exc}")
            sys.exit(1)

    forbidden_source_fragments = [
        "low_risk_dry_run_authority_granted=True",
        "dry_run_execution_performed=True",
        "policy_activation_requested=True",
        "session_start_requested=True",
        "session_active=True",
        "execution_requested=True",
        "execution_performed=True",
        "autonomous_actions_enabled=True",
        "background_worker_enabled=True",
        "execution_enabled=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_tool_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "model_provider_call_enabled=True",
        "production_authority_enabled=True",
        "authority_granted=True",
        "/autonomy/dry-run/start",
        "/autonomy/dry-run/execute",
        "/autonomy/dry-run/activate",
        "/autonomy/session/start",
        "/autonomy/policy/activate",
        "/network/fetch",
        "/shell/execute",
        "/browser/click",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/autonomy/dry_run.py",
        "src/ultimate_ai_agent/core/autonomy/risk.py",
        "src/ultimate_ai_agent/core/autonomy/revocation.py",
        "src/ultimate_ai_agent/core/autonomy/approvals.py",
        "src/ultimate_ai_agent/core/autonomy/audit.py",
        "src/ultimate_ai_agent/core/autonomy/policies.py",
        "src/ultimate_ai_agent/core/autonomy/sessions.py",
        "src/ultimate_ai_agent/core/autonomy/simulator.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m69_low_risk_autonomous_dry_run.py",
        "tests/test_m69_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M69 forbidden low-risk autonomous dry-run fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M69 low-risk autonomous dry run is contract-only, route-free, low-risk-only, and no-authority")


def verify_m70_autonomy_foundation_freeze():
    print("\n[Verifier] Running M70 autonomy foundation freeze guard...")
    required_files = [
        "src/ultimate_ai_agent/core/autonomy/foundation_freeze.py",
        "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE.md",
        "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE_CONTRACTS.md",
        "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE_NON_GOALS.md",
        "docs/autonomy/M70_TO_M71_BOUNDARY.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/release_notes/v0_74_0.md",
        "docs/archive/releases/v0_74_0/README_IMPORT.md",
        "docs/archive/releases/v0_74_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_74_0.md",
        "tests/test_m70_autonomy_foundation_freeze.py",
        "tests/test_m70_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M70 autonomy foundation freeze file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "autonomy foundation freeze",
        "m61-m69",
        "contract-only",
        "review-only",
        "freeze-only",
        "deterministic",
        "accepted milestone refs",
        "checklist refs",
        "evaluator boundaries revalidate",
        "no policy activation",
        "no session start",
        "no low-risk dry-run execution",
        "no autonomous actions",
        "no background worker",
        "no execution",
        "no tool execution",
        "no shell execution",
        "no network tool",
        "no browser automation",
        "no context injection",
        "no memory write",
        "no model/provider call",
        "no backend route",
        "no control center control",
        "no dependency",
        "no production authority",
        "m71 remains future",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M70 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.autonomy import (
            AutonomyFoundationFreezeRequest,
            AutonomyFoundationFreezeStatus,
            build_autonomy_foundation_freeze_report,
            validate_autonomy_foundation_freeze_request,
        )
        from ultimate_ai_agent.core.gate.evaluators import m70_openapi_route_failures
    except Exception as exc:
        print(f"FAIL: M70 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m70_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    request = AutonomyFoundationFreezeRequest(
        request_ref="autonomy-foundation-freeze-request:verify-all-m70",
        freeze_ref="autonomy-foundation-freeze:verify-all-m70",
        baseline_ref="baseline:v0.73.0",
        actor_ref="actor:verify-all",
        accepted_milestone_refs=[f"milestone:M{index}" for index in range(61, 70)],
        checklist_refs=[
            "autonomy-freeze:m61-m69-reviewed",
            "autonomy-freeze:route-stable",
            "autonomy-freeze:dependency-stable",
            "autonomy-freeze:authority-frozen",
            "autonomy-freeze:docs-current",
            "autonomy-freeze:gate-green",
        ],
        safe_summary="Freeze the M61-M69 autonomy foundation without adding authority.",
    )
    report = build_autonomy_foundation_freeze_report(request)
    if (
        report.status != AutonomyFoundationFreezeStatus.frozen
        or not report.freeze_only
        or not report.review_only
        or not report.autonomy_foundation_only
        or report.policy_activation_performed
        or report.session_start_performed
        or report.execution_performed
        or report.background_worker_started
        or report.production_authority_granted
        or report.side_effects_performed
    ):
        print("FAIL: M70 autonomy foundation freeze granted authority or side effects")
        sys.exit(1)

    for update, reason in [
        ({"policy_activation_requested": True}, "AUTONOMY_POLICY_ACTIVATION_DENIED"),
        ({"session_start_requested": True}, "AUTONOMY_SESSION_START_DENIED"),
        ({"low_risk_dry_run_execution_requested": True}, "LOW_RISK_DRY_RUN_EXECUTION_DENIED"),
        ({"autonomous_actions_requested": True}, "AUTONOMOUS_ACTIONS_DENIED"),
        ({"background_worker_requested": True}, "BACKGROUND_WORKER_DENIED"),
        ({"execution_requested": True}, "EXECUTION_DENIED"),
        ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
        ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
        ({"network_tool_requested": True}, "NETWORK_TOOL_DENIED"),
        ({"browser_automation_requested": True}, "BROWSER_AUTOMATION_DENIED"),
        ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
        ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
        ({"model_provider_call_requested": True}, "MODEL_PROVIDER_CALL_DENIED"),
        ({"backend_route_requested": True}, "BACKEND_ROUTE_DENIED"),
        ({"dependency_requested": True}, "DEPENDENCY_CHANGE_DENIED"),
        ({"production_authority_requested": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"metadata": {"api_key": "secret-value"}}, "SECRET_LIKE_AUTONOMY_FOUNDATION_FREEZE_CONTENT_DENIED"),
    ]:
        try:
            validate_autonomy_foundation_freeze_request(request.model_copy(update=update))
            print(f"FAIL: M70 unsafe autonomy foundation freeze mutation was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M70 unsafe autonomy foundation freeze reason drifted for {reason}: {exc}")
                sys.exit(1)

    forbidden_source_fragments = [
        "autonomy_foundation_authority_granted=True",
        "autonomy_foundation_freeze_authority_granted=True",
        "policy_activation_enabled=True",
        "policy_activation_requested=True",
        "session_start_enabled=True",
        "session_start_requested=True",
        "low_risk_dry_run_execution_enabled=True",
        "low_risk_dry_run_execution_requested=True",
        "autonomous_actions_enabled=True",
        "autonomous_actions_requested=True",
        "background_worker_enabled=True",
        "background_worker_requested=True",
        "execution_enabled=True",
        "execution_requested=True",
        "execution_performed=True",
        "tool_execution_enabled=True",
        "shell_execution_enabled=True",
        "network_tool_enabled=True",
        "browser_automation_enabled=True",
        "plugin_execution_enabled=True",
        "mobile_sensor_enabled=True",
        "remote_execution_enabled=True",
        "memory_write_enabled=True",
        "context_injection_enabled=True",
        "model_provider_call_enabled=True",
        "backend_route_enabled=True",
        "control_center_control_enabled=True",
        "dependency_change_enabled=True",
        "production_authority_enabled=True",
        "production_authority_granted=True",
        "/autonomy/freeze/activate",
        "/autonomy/freeze/start",
        "/autonomy/session/start",
        "/autonomy/policy/activate",
        "/autonomy/dry-run/execute",
        "/network/fetch",
        "/shell/execute",
        "/browser/click",
        "subprocess" + ".run(",
        "subprocess" + ".Popen(",
        "os.system(",
        "shell=True",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/autonomy/foundation_freeze.py",
        "src/ultimate_ai_agent/core/autonomy/dry_run.py",
        "src/ultimate_ai_agent/core/autonomy/risk.py",
        "src/ultimate_ai_agent/core/autonomy/revocation.py",
        "src/ultimate_ai_agent/core/autonomy/approvals.py",
        "src/ultimate_ai_agent/core/autonomy/audit.py",
        "src/ultimate_ai_agent/core/autonomy/policies.py",
        "src/ultimate_ai_agent/core/autonomy/sessions.py",
        "src/ultimate_ai_agent/core/autonomy/simulator.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m70_autonomy_foundation_freeze.py",
        "tests/test_m70_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M70 forbidden autonomy foundation freeze fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M70 autonomy foundation freeze is contract-only, route-free, freeze-only, and no-authority")


def verify_m71_network_tool_contract_review():
    print("\n[Verifier] Running M71 network tool contract review guard...")
    required_files = [
        "src/ultimate_ai_agent/core/network/contract_review.py",
        "src/ultimate_ai_agent/core/network/__init__.py",
        "docs/network/NETWORK_TOOL_CONTRACT_REVIEW.md",
        "docs/network/NETWORK_TOOL_CONTRACT_REVIEW_POLICY.md",
        "docs/network/NETWORK_TOOL_CONTRACT_AUTHORITY_BOUNDARY.md",
        "docs/network/M71_TO_M72_BOUNDARY.md",
        "docs/roadmap/M61_M100_ROADMAP.md",
        "docs/release_notes/v0_75_0.md",
        "docs/archive/releases/v0_75_0/README_IMPORT.md",
        "docs/archive/releases/v0_75_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_75_0.md",
        "tests/test_m71_network_tool_contract_review.py",
        "tests/test_m71_gate_integration.py",
    ]
    for rel_path in required_files:
        if not (ROOT / rel_path).exists():
            print(f"FAIL: Missing M71 network tool contract review file: {rel_path}")
            sys.exit(1)

    docs_text = "\n".join(
        (ROOT / rel_path).read_text(encoding="utf-8").lower()
        for rel_path in required_files
        if rel_path.startswith("docs/")
    )
    for fragment in [
        "network tool contract review",
        "contract-only",
        "review-only",
        "disabled by default",
        "m72 remains future",
        "no network call",
        "no http fetch",
        "no unrestricted network tool",
        "no authenticated network action",
        "no credentials or cookies",
        "no request body",
        "no non-get method",
        "no download or export",
        "no raw response body",
        "no backend route",
        "no control center control",
        "no dependency",
        "no production authority",
        "evaluator boundaries revalidate",
    ]:
        if fragment not in docs_text:
            print(f"FAIL: M71 docs missing fragment: {fragment}")
            sys.exit(1)

    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "src"))
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.gate.evaluators import m71_openapi_route_failures
        from ultimate_ai_agent.core.network import (
            NetworkToolCapabilityKind,
            NetworkToolContractReviewPolicy,
            NetworkToolContractReviewRequest,
            NetworkToolContractReviewStatus,
            build_network_tool_contract_review_decision,
            validate_network_tool_contract_review_policy,
            validate_network_tool_contract_review_request,
        )
    except Exception as exc:
        print(f"FAIL: M71 guard imports could not load: {exc}")
        sys.exit(1)

    for failure in m71_openapi_route_failures(app.openapi().get("paths", {})):
        print(f"FAIL: {failure}")
        sys.exit(1)

    request = NetworkToolContractReviewRequest(
        review_ref="network-tool-contract-review:verify-all-m71",
        candidate_ref="network-tool-candidate:verify-all-m71-read-only-http-fetch",
        actor_ref="actor:verify-all",
        proposed_tool_ref="tool:read-only-http-fetch-m72-candidate",
        safe_name="Allowlisted read-only HTTP fetch contract review",
        capability_kind=NetworkToolCapabilityKind.allowlisted_read_only_http_fetch,
        safe_summary="Review a future M72 allowlisted read-only HTTP fetch contract without enabling network calls.",
        allowed_host_policy_ref="network-allowlist-policy:m72-future",
        risk_ref="risk:network-low-read-only-review",
    )
    decision = build_network_tool_contract_review_decision(request)
    if (
        decision.status != NetworkToolContractReviewStatus.review_ready
        or not decision.review_allowed
        or not decision.contract_only
        or not decision.review_only
        or not decision.disabled_by_default
        or not decision.m72_candidate_only
        or not decision.future_milestone_required
        or decision.network_call_allowed
        or decision.http_fetch_allowed
        or decision.unrestricted_network_allowed
        or decision.authenticated_network_allowed
        or decision.credentials_or_cookies_allowed
        or decision.request_body_allowed
        or decision.non_get_method_allowed
        or decision.download_or_export_allowed
        or decision.browser_automation_allowed
        or decision.provider_model_call_allowed
        or decision.tool_execution_allowed
        or decision.memory_write_allowed
        or decision.context_injection_allowed
        or decision.backend_route_allowed
        or decision.control_center_control_allowed
        or decision.dependency_change_allowed
        or decision.production_authority_granted
        or decision.receipt_plan.network_call_performed
        or decision.receipt_plan.http_fetch_performed
        or decision.receipt_plan.raw_response_body_stored
        or decision.receipt_plan.credentials_or_cookies_used
        or decision.receipt_plan.side_effects_performed
    ):
        print("FAIL: M71 network tool contract review granted authority or side effects")
        sys.exit(1)

    future_decision = build_network_tool_contract_review_decision(
        request.model_copy(
            update={
                "candidate_ref": "network-tool-candidate:verify-all-m71-authenticated",
                "capability_kind": NetworkToolCapabilityKind.authenticated_network_action,
                "safe_name": "Future authenticated network action review",
            }
        )
    )
    if (
        future_decision.status != NetworkToolContractReviewStatus.future_milestone
        or future_decision.network_call_allowed
        or future_decision.http_fetch_allowed
        or "FUTURE_NETWORK_MILESTONE_REQUIRED" not in future_decision.reason_codes
    ):
        print("FAIL: M71 effectful network capability was not kept future-only")
        sys.exit(1)

    for update, reason in [
        ({"network_call_requested": True}, "NETWORK_CALL_DENIED"),
        ({"http_fetch_requested": True}, "HTTP_FETCH_DENIED"),
        ({"unrestricted_network_requested": True}, "UNRESTRICTED_NETWORK_DENIED"),
        ({"authenticated_network_requested": True}, "AUTHENTICATED_NETWORK_DENIED"),
        ({"credentials_or_cookies_requested": True}, "CREDENTIAL_OR_COOKIE_HANDLING_DENIED"),
        ({"request_body_requested": True}, "REQUEST_BODY_DENIED"),
        ({"non_get_method_requested": True}, "NON_GET_METHOD_DENIED"),
        ({"download_or_export_requested": True}, "DOWNLOAD_OR_EXPORT_DENIED"),
        ({"browser_automation_requested": True}, "BROWSER_AUTOMATION_DENIED"),
        ({"provider_model_call_requested": True}, "PROVIDER_MODEL_CALL_DENIED"),
        ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
        ({"backend_route_requested": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_requested": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_requested": True}, "DEPENDENCY_CHANGE_DENIED"),
        ({"production_authority_requested": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"contains_raw_response_body": True}, "RAW_RESPONSE_BODY_DENIED"),
        ({"approval_ref": "approval:m71-verify-all"}, "APPROVAL_REF_NOT_AUTHORITY"),
        ({"approval_test_ref": "approval_test_m71_verify_all"}, "APPROVAL_TEST_REF_DENIED"),
        ({"metadata": {"api_key": "secret-value"}}, "SECRET_LIKE_NETWORK_TOOL_CONTENT_DENIED"),
    ]:
        try:
            validate_network_tool_contract_review_request(request.model_copy(update=update))
            print(f"FAIL: M71 unsafe network tool request was not denied: {reason}")
            sys.exit(1)
        except ValueError as exc:
            if reason not in str(exc):
                print(f"FAIL: M71 unsafe network tool reason drifted for {reason}: {exc}")
                sys.exit(1)

    try:
        validate_network_tool_contract_review_policy(
            NetworkToolContractReviewPolicy(network_call_enabled=True)
        )
        print("FAIL: M71 unsafe network tool policy was not denied: NETWORK_CALL_DENIED")
        sys.exit(1)
    except ValueError as exc:
        if "NETWORK_CALL_DENIED" not in str(exc):
            print(f"FAIL: M71 unsafe network tool policy reason drifted: {exc}")
            sys.exit(1)

    forbidden_source_fragments = [
        "network_call_enabled=True",
        "network_call_requested=True",
        "http_fetch_enabled=True",
        "http_fetch_requested=True",
        "unrestricted_network_enabled=True",
        "unrestricted_network_requested=True",
        "authenticated_network_enabled=True",
        "authenticated_network_requested=True",
        "credentials_or_cookies_enabled=True",
        "credentials_or_cookies_requested=True",
        "request_body_enabled=True",
        "request_body_requested=True",
        "non_get_method_enabled=True",
        "non_get_method_requested=True",
        "download_or_export_enabled=True",
        "download_or_export_requested=True",
        "browser_automation_enabled=True",
        "browser_automation_requested=True",
        "provider_model_call_enabled=True",
        "provider_model_call_requested=True",
        "tool_execution_enabled=True",
        "tool_execution_requested=True",
        "memory_write_enabled=True",
        "memory_write_requested=True",
        "context_injection_enabled=True",
        "context_injection_requested=True",
        "backend_route_enabled=True",
        "backend_route_requested=True",
        "control_center_control_enabled=True",
        "control_center_control_requested=True",
        "dependency_change_enabled=True",
        "dependency_requested=True",
        "production_authority_enabled=True",
        "production_authority_requested=True",
        "production_authority_granted=True",
        "raw_response_body_stored=True",
        "credentials_or_cookies_used=True",
        "/network/fetch",
        "/network/request",
        "/http/fetch",
        "/http/request",
        "/tools/network/execute",
        "/tools/execute",
        "/tool-runtime/execute",
        "/browser/click",
        "/plugins/execute",
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "httpx.post(",
        "urllib.request.urlopen",
        "websocket",
        "socket.",
    ]
    allowed_files = {
        "scripts/verify_all.py",
        "src/ultimate_ai_agent/core/network/contract_review.py",
        "src/ultimate_ai_agent/core/network/__init__.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/api/openapi.py",
        "src/ultimate_ai_agent/core/autonomy/foundation_freeze.py",
        "src/ultimate_ai_agent/core/autonomy/dry_run.py",
        "src/ultimate_ai_agent/core/autonomy/risk.py",
        "src/ultimate_ai_agent/core/autonomy/revocation.py",
        "src/ultimate_ai_agent/core/autonomy/approvals.py",
        "src/ultimate_ai_agent/core/autonomy/audit.py",
        "src/ultimate_ai_agent/core/autonomy/policies.py",
        "src/ultimate_ai_agent/core/autonomy/sessions.py",
        "src/ultimate_ai_agent/core/autonomy/simulator.py",
        "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
        "tests/test_m71_network_tool_contract_review.py",
        "tests/test_m71_gate_integration.py",
        "tests/test_m70_autonomy_foundation_freeze.py",
        "tests/test_m70_gate_integration.py",
    }
    source_roots = [
        ROOT / "src" / "ultimate_ai_agent",
        ROOT / "apps" / "control-center" / "src",
        ROOT / "apps" / "ccc-ios",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".swift"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in allowed_files:
                continue
            text = path.read_text(encoding="utf-8")
            for fragment in forbidden_source_fragments:
                if fragment in text:
                    print(f"FAIL: M71 forbidden network tool contract fragment in {rel}: {fragment}")
                    sys.exit(1)

    print("OK: M71 network tool contract review is contract-only, route-free, disabled-by-default, and no-authority")


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
