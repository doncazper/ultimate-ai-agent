#!/usr/bin/env python3
"""Local setup assistant for UAA developer/OpenWebUI bootstrapping.

The setup assistant is intentionally local, bounded, and explicit. The doctor
path detects developer prerequisites and writes only gitignored local
diagnostic artifacts when requested. The separate M167 OpenWebUI installer path
may pull only the configured OpenWebUI Docker image after explicit approval. It
does not install Python, Node/npm deps, llama.cpp, providers, models, plugins,
browser tooling, credentials, mutate OpenWebUI internals, or enable
provider/model authority.
"""
from __future__ import annotations


import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request


SetupStatus = Literal["pass", "warn", "blocked", "manual", "not-scoped"]
SetupProfile = Literal["minimal", "frontend-only", "openwebui-smoke", "local-llama"]

DEFAULT_MODEL_ID = "uaa-llama-cpp-local"
DEFAULT_HF_REPO = "ggml-org/gemma-3-1b-it-GGUF"
DEFAULT_HF_FILE = "gemma-3-1b-it-Q4_K_M.gguf"
DEFAULT_LLAMA_BASE_URL = "http://127.0.0.1:8080"
DEFAULT_UAA_GATEWAY_KEY = "uaa-local-llama-cpp-dev"
DEFAULT_LLAMA_BACKEND_KEY = "uaa-llama-backend-dev"
DEFAULT_HF_HOME = "$HOME/Models/huggingface"
DEFAULT_HF_HUB_CACHE = "$HF_HOME/hub"
DEFAULT_OLLAMA_MODELS = "$HOME/Models/ollama/models"
DEFAULT_LLAMA_CPP_MODEL_CACHE_ROOT = "$HOME/Models/llama.cpp/model-cache"
LOCAL_ENV_PATH = Path(".uaa") / "dev" / "local-llama.env"
DEFAULT_REPORT_PATH = Path(".uaa") / "dev" / "setup-report.json"
SETUP_INSTALL_RECEIPT_DIR = Path(".uaa") / "dev" / "setup-install-receipts"
SETUP_BOOTSTRAP_RECEIPT_DIR = Path(".uaa") / "dev" / "setup-bootstrap-receipts"
SETUP_APPROVAL_RECEIPT_DIR = Path(".uaa") / "dev" / "setup-approval-receipts"
FRONTIER_PROVIDERS = {"openai", "anthropic", "gemini"}
SETUP_PROFILES: tuple[SetupProfile, ...] = ("minimal", "frontend-only", "openwebui-smoke", "local-llama")
SETUP_INSTALL_TARGETS = ("openwebui",)
SETUP_INSTALL_MILESTONE_REF = "milestone:m167-openwebui-local-installer"
SETUP_BOOTSTRAP_TARGETS = ("openwebui",)
SETUP_BOOTSTRAP_MILESTONE_REF = "milestone:m167-github-bootstrap-local-installer"
SETUP_INSTALL_CONFIRMATION = "install openwebui"
SETUP_BOOTSTRAP_CONFIRMATION = "install uaa openwebui bootstrap"
SETUP_INSTALL_APPROVAL_TOKEN_SCHEMA = "uaa.setup_install_approval_token.v1"
SETUP_INSTALL_APPROVAL_TOKEN_TTL_SECONDS = 900
SETUP_BOOTSTRAP_APPROVAL_TOKEN_SCHEMA = "uaa.setup_bootstrap_approval_token.v1"
SETUP_BOOTSTRAP_APPROVAL_TOKEN_TTL_SECONDS = 900
SETUP_APPROVAL_RECEIPT_SCHEMA = "uaa.setup_approval_receipt.v1"
SETUP_APPROVAL_AUTHORITY_LABEL = "PolicyEngine+LocalApprovalAuthority"
BOOTSTRAP_REPO_URL = "https://github.com/doncazper/ultimate-ai-agent"
BOOTSTRAP_RELEASE_BASE_URL = f"{BOOTSTRAP_REPO_URL}/releases/download"
BOOTSTRAP_TRUST_ROOT_REF = "docs/production/UAA_BOOTSTRAP_TRUST_ROOT.md"
BOOTSTRAP_MINISIGN_PUBLIC_KEY_REF = "docs/production/UAA_BOOTSTRAP_MINISIGN.pub"
BOOTSTRAP_MINISIGN_PUBLIC_KEY_SHA256 = "26b78663c6ca99add07177eaaefd7cd9dfad5a7d09fbb74e9ab0c3112a6c06c3"
BOOTSTRAP_MINISIGN_TRUST_ROOT_IDENTITY = "uaa-m167-bootstrap-minisign-key-5541414d31363701"
BOOTSTRAP_PROVENANCE_SCHEMA = "uaa.bootstrap.provenance.v1"
BOOTSTRAP_MINISIGN_STATEMENT_SCHEMA = "uaa.bootstrap.minisign_statement.v1"
BOOTSTRAP_AUTHORITY = "openwebui-local-dev-bootstrap-only"
BOOTSTRAP_PROVENANCE_MODES = ("minisign", "local-dev-json")
BOOTSTRAP_INSTALLER_NAME = "uaa-bootstrap"
BOOTSTRAP_RELEASE_TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
BOOTSTRAP_RELEASE_TAG_POLICY_RE = re.compile(r"^v\d+\.\d+\.\d+-m167(?:[._+-][A-Za-z0-9._+-]+)?$")
BOOTSTRAP_ASSET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,191}$")
BOOTSTRAP_ALLOWED_ASSETS = frozenset({"uaa-bootstrap-darwin-arm64.tar.gz"})
BOOTSTRAP_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
MIN_PYTHON = (3, 10)
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 5173
OPENWEBUI_HOST = "127.0.0.1"
OPENWEBUI_PORT = 3000
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
FRONTEND_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"
OPENWEBUI_URL = f"http://{OPENWEBUI_HOST}:{OPENWEBUI_PORT}"
UAA_LAUNCHER_BACKEND_HOST_ENV = "UAA_LAUNCHER_BACKEND_HOST"
UAA_LAUNCHER_BACKEND_PORT_ENV = "UAA_LAUNCHER_BACKEND_PORT"
UAA_LAUNCHER_FRONTEND_HOST_ENV = "UAA_LAUNCHER_FRONTEND_HOST"
UAA_LAUNCHER_FRONTEND_PORT_ENV = "UAA_LAUNCHER_FRONTEND_PORT"
UAA_LAUNCHER_OPENWEBUI_HOST_ENV = "UAA_LAUNCHER_OPENWEBUI_HOST"
UAA_LAUNCHER_OPENWEBUI_PORT_ENV = "UAA_LAUNCHER_OPENWEBUI_PORT"
OPENWEBUI_IMAGE_REPOSITORY = "ghcr.io/open-webui/open-webui"
OPENWEBUI_IMAGE_DIGEST = "sha256:7f1b0a1a50cfbac23da3b16f96bc968fd757b26dc9e54e93813d61768ea9184e"
OPENWEBUI_IMAGE = f"{OPENWEBUI_IMAGE_REPOSITORY}@{OPENWEBUI_IMAGE_DIGEST}"
OPENWEBUI_SMOKE_MODEL_ID = "uaa-safe-local"
DOCKER_PULL_TIMEOUT_SECONDS = 1800.0
BOOTSTRAP_DOWNLOAD_TIMEOUT_SECONDS = 60.0
BOOTSTRAP_INSTALL_TIMEOUT_SECONDS = 900.0
UAA_OPENWEBUI_TEST_GATEWAY_ENV = "UAA_OPENWEBUI_TEST_GATEWAY_ENABLED"
UAA_LLAMA_CPP_GATEWAY_ENV = "UAA_LLAMA_CPP_GATEWAY_ENABLED"
UAA_LLAMA_CPP_GATEWAY_KEY_ENV = "UAA_LLAMA_CPP_GATEWAY_KEY"
UAA_LLAMA_CPP_BASE_URL_ENV = "UAA_LLAMA_CPP_BASE_URL"
UAA_LLAMA_CPP_MODEL_ID_ENV = "UAA_LLAMA_CPP_MODEL_ID"
UAA_LLAMA_CPP_API_KEY_ENV = "UAA_LLAMA_CPP_API_KEY"
DEVELOPER_TOOL_PATHS = (
    Path("/opt/homebrew/bin"),
    Path("/opt/homebrew/sbin"),
    Path("/usr/local/bin"),
    Path("/Applications/Docker.app/Contents/Resources/bin"),
)
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
LAUNCHER_HOSTS = {"127.0.0.1", "localhost"}


@dataclass(frozen=True)
class SetupFinding:
    name: str
    status: SetupStatus
    summary: str
    action: str
    why: str = ""
    authority_boundary: str = ""


@dataclass(frozen=True)
class SetupReport:
    mode: str
    system_summary: dict[str, str]
    findings: list[SetupFinding]
    model_id: str
    next_steps: list[str]
    repair_plan: list[str] = field(default_factory=list)
    plan_commands: list[str] = field(default_factory=list)
    platform_hints: list[str] = field(default_factory=list)
    profile: str = "local-llama"
    selected_model_alias: str | None = None
    env_template: str | None = None
    report_path: str | None = None

    @property
    def overall_status(self) -> SetupStatus:
        statuses = {finding.status for finding in self.findings}
        if "blocked" in statuses:
            return "blocked"
        if "warn" in statuses:
            return "warn"
        if "manual" in statuses or "not-scoped" in statuses:
            return "manual"
        return "pass"

    @property
    def blocked_next_steps(self) -> list[str]:
        return _actions_for_status(self.findings, "blocked")

    @property
    def manual_next_steps(self) -> list[str]:
        return _actions_for_status(self.findings, "manual") + _actions_for_status(self.findings, "not-scoped")


def add_setup_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("setup")
    parser.add_argument(
        "--profile",
        choices=list(SETUP_PROFILES),
        default=None,
        help="Readiness profile. Keeps the doctor focused on the first-run path you intend to use.",
    )
    parser.add_argument(
        "--mode",
        choices=["smoke", "local-llama", "frontier"],
        default="local-llama",
        help="Compatibility setup target. Prefer --profile for new first-run checks.",
    )
    parser.add_argument("--provider", choices=sorted(FRONTIER_PROVIDERS), default=None)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--hf-repo", default=DEFAULT_HF_REPO)
    parser.add_argument("--hf-file", default=DEFAULT_HF_FILE)
    parser.add_argument("--write-env", action="store_true", help="Write .uaa/dev/local-llama.env")
    parser.add_argument("--overwrite-env", action="store_true", help="Replace an existing local env template")
    parser.add_argument("--check-env", default=None, help="Check a local llama env file without printing secret values")
    parser.add_argument(
        "--write-report",
        nargs="?",
        const=str(DEFAULT_REPORT_PATH),
        default=None,
        help="Write a redacted JSON diagnostic bundle. Defaults to .uaa/dev/setup-report.json.",
    )
    parser.add_argument("--explain", action="store_true", help="Show why each check matters and what it does not grant")
    parser.add_argument("--plan", action="store_true", help="Print an honest manual command preview without running commands")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable safe summary")
    setup_subparsers = parser.add_subparsers(dest="setup_action")
    install_parser = setup_subparsers.add_parser(
        "install",
        help="Explicitly install a scoped local-dev setup asset after approval.",
    )
    install_parser.add_argument("--target", choices=list(SETUP_INSTALL_TARGETS), required=True)
    install_parser.add_argument(
        "--yes",
        action="store_true",
        help="Run noninteractively only with a matching preview-bound --approval-token.",
    )
    install_parser.add_argument("--approval-token", default=None)
    install_parser.add_argument("--write-approval-token", default=None)
    install_parser.add_argument(
        "--receipt",
        default=None,
        help="Write the setup install receipt to an explicit existing-safe path.",
    )
    bootstrap_parser = setup_subparsers.add_parser(
        "bootstrap",
        help="Download and run a pinned, verified UAA GitHub Release bootstrap artifact after approval.",
    )
    bootstrap_parser.add_argument("--release-tag", required=True, type=_bootstrap_release_tag_arg)
    bootstrap_parser.add_argument("--asset", required=True, type=_bootstrap_asset_arg)
    bootstrap_parser.add_argument("--sha256", required=True, type=_bootstrap_sha256_arg)
    bootstrap_parser.add_argument("--signature", required=True)
    bootstrap_parser.add_argument("--target", choices=list(SETUP_BOOTSTRAP_TARGETS), required=True)
    bootstrap_parser.add_argument("--bin-dir", default=str(Path.home() / ".local" / "bin"))
    bootstrap_parser.add_argument("--install-dir", default=str(Path.home() / ".local" / "share" / "uaa"))
    bootstrap_parser.add_argument("--receipt", default=None)
    bootstrap_parser.add_argument("--approval-token", default=None)
    bootstrap_parser.add_argument("--write-approval-token", default=None)
    bootstrap_parser.add_argument(
        "--provenance-mode",
        choices=list(BOOTSTRAP_PROVENANCE_MODES),
        default="minisign",
        help="Use cryptographic public bootstrap verification, or explicit local-dev JSON provenance for tests.",
    )
    bootstrap_parser.add_argument(
        "--yes",
        action="store_true",
        help="Run noninteractively only with a matching preview-bound --approval-token.",
    )


def command_setup(root: Path, args: argparse.Namespace) -> int:
    if getattr(args, "setup_action", None) == "bootstrap":
        return command_setup_bootstrap(root, args)
    if getattr(args, "setup_action", None) == "install":
        return command_setup_install(root, args)
    report = build_setup_report(
        root,
        mode=args.mode,
        profile=args.profile,
        provider=args.provider,
        model_id=args.model_id,
        hf_repo=args.hf_repo,
        hf_file=args.hf_file,
        check_env=Path(args.check_env) if args.check_env else None,
    )
    env_path: Path | None = None
    if args.write_env:
        env_path, write_finding = prepare_local_llama_env(
            root,
            model_id=args.model_id,
            overwrite=args.overwrite_env,
        )
        findings = _enrich_findings([*report.findings, write_finding])
        report = SetupReport(
            profile=report.profile,
            mode=report.mode,
            system_summary=report.system_summary,
            findings=findings,
            model_id=report.model_id,
            next_steps=report.next_steps,
            repair_plan=_repair_plan(findings),
            plan_commands=report.plan_commands,
            platform_hints=report.platform_hints,
            selected_model_alias=report.selected_model_alias,
            env_template=str(env_path.relative_to(root)),
            report_path=report.report_path,
        )
    if args.write_report:
        requested_report_path = Path(args.write_report)
        report_path = requested_report_path if requested_report_path.is_absolute() else root / requested_report_path
        report = SetupReport(
            profile=report.profile,
            mode=report.mode,
            system_summary=report.system_summary,
            findings=report.findings,
            model_id=report.model_id,
            next_steps=report.next_steps,
            repair_plan=report.repair_plan,
            plan_commands=report.plan_commands,
            platform_hints=report.platform_hints,
            selected_model_alias=report.selected_model_alias,
            env_template=report.env_template,
            report_path=_display_path(root, report_path),
        )
        write_setup_report(root, Path(args.write_report), report)
    if args.json:
        print(json.dumps(serialize_report(report), indent=2, sort_keys=True))
    elif args.plan:
        print(render_plan(report))
    else:
        print(render_report(report, hf_repo=args.hf_repo, hf_file=args.hf_file, explain=args.explain))
    return 1 if report.overall_status == "blocked" else 0


def command_setup_install(root: Path, args: argparse.Namespace) -> int:
    target = getattr(args, "target", "")
    if target != "openwebui":
        print(f"Unsupported setup install target: {target}")
        return 2
    plan = _openwebui_install_plan(root)
    try:
        _attach_install_approval_paths(root, plan, args)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 2
    print(render_install_plan(plan))

    if getattr(args, "write_approval_token", None):
        if getattr(args, "yes", False):
            receipt_path = write_setup_install_receipt(
                root,
                plan,
                status="failed",
                result_summary="Approval-token writing cannot be combined with --yes; no pull command was run.",
            )
            print("FAIL: --write-approval-token cannot be combined with --yes.")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1
        if not _read_install_approval():
            _record_setup_approval_decision(
                root,
                plan,
                action_ref="openwebui-image-pull",
                status="denied",
                approval_mode="refused",
                reason_codes=["OPERATOR_APPROVAL_REFUSED"],
            )
            receipt_path = write_setup_install_receipt(
                root,
                plan,
                status="refused",
                result_summary="Operator approval was not provided; no approval token was written.",
            )
            print("Install approval token refused. No download or install command was run.")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1
        token_path = write_setup_install_approval_token(root, plan, plan["write_approval_token_path"])
        print(f"Preview-bound approval token written: {_safe_path_summary(token_path)}")
        print("No download or install command was run.")
        return 0

    try:
        _reserve_custom_install_receipt(root, plan)
    except (OSError, ValueError):
        print("FAIL: Custom receipt destination could not be reserved safely; no install command was run.")
        return 2

    approval_mode = "typed"
    if getattr(args, "yes", False):
        if plan.get("approval_token_path") is None:
            _record_setup_approval_decision(
                root,
                plan,
                action_ref="openwebui-image-pull",
                status="denied",
                approval_mode="not-approved",
                reason_codes=["APPROVAL_TOKEN_REQUIRED"],
            )
            receipt_path = write_setup_install_receipt(
                root,
                plan,
                status="failed",
                result_summary="--yes requires a matching preview-bound approval token; no image pull command was run.",
            )
            print("FAIL: --yes requires an approval token from --approval-token with a matching preview hash.")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1
        try:
            _consume_setup_install_approval_token(root, plan, plan["approval_token_path"])
        except ValueError as exc:
            _record_setup_approval_decision(
                root,
                plan,
                action_ref="openwebui-image-pull",
                status="denied",
                approval_mode="preview-token",
                reason_codes=["APPROVAL_TOKEN_INVALID"],
            )
            safe_error = _safe_summary_text(str(exc))
            receipt_path = write_setup_install_receipt(
                root,
                plan,
                status="failed",
                result_summary=f"Approval token was rejected: {safe_error}",
            )
            print(f"FAIL: Approval token was rejected: {safe_error}")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1
        approval_mode = "preview-token"
    elif not _read_install_approval():
        _record_setup_approval_decision(
            root,
            plan,
            action_ref="openwebui-image-pull",
            status="denied",
            approval_mode="refused",
            reason_codes=["OPERATOR_APPROVAL_REFUSED"],
        )
        receipt_path = write_setup_install_receipt(
            root,
            plan,
            status="refused",
            result_summary="Operator approval was not provided; no download or install command was run.",
        )
        print("Install refused. No download or install command was run.")
        print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
        return 1
    plan["approval_mode"] = approval_mode

    try:
        _authorize_setup_action(root, plan, action_ref="openwebui-image-pull", approval_mode=approval_mode)
    except ValueError as exc:
        safe_error = _safe_summary_text(str(exc))
        receipt_path = write_setup_install_receipt(
            root,
            plan,
            status="failed",
            result_summary=f"Approval authority denied the scoped image pull: {safe_error}",
        )
        print(f"FAIL: Approval authority denied the scoped image pull: {safe_error}")
        print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
        return 1

    docker = _resolve_command("docker")
    if docker is None:
        receipt_path = write_setup_install_receipt(
            root,
            plan,
            status="failed",
            result_summary="Docker CLI was not available; no image pull command was run.",
        )
        print("FAIL: Docker CLI is not available on PATH.")
        print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
        return 1
    engine = _run_probe([str(docker), "info", "--format", "{{.ServerVersion}}"], timeout_seconds=3.0)
    if engine["returncode"] != 0:
        receipt_path = write_setup_install_receipt(
            root,
            plan,
            status="failed",
            result_summary="Docker engine was not ready; no image pull command was run.",
        )
        print("FAIL: Docker engine is not ready. Open Docker Desktop, finish setup, then retry.")
        print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
        return 1

    command = [str(docker), "pull", OPENWEBUI_IMAGE]
    print("Running approved scoped command:")
    print(f"- {_shell_preview(command)}")
    result = _run_install_command(command)
    if result["returncode"] != 0:
        safe_summary = _safe_summary_text(result["summary"])
        receipt_path = write_setup_install_receipt(
            root,
            plan,
            status="failed",
            result_summary=f"Docker pull failed safely: {safe_summary}",
        )
        print(f"FAIL: Docker pull failed safely: {safe_summary}")
        print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
        return 1

    receipt_path = write_setup_install_receipt(
        root,
        plan,
        status="installed",
        result_summary="Configured OpenWebUI Docker image pull completed.",
    )
    print("OpenWebUI local image install completed.")
    print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
    print("Rollback:")
    for step in plan["rollback_steps"]:
        print(f"- {step}")
    return 0


def command_setup_bootstrap(root: Path, args: argparse.Namespace) -> int:
    try:
        plan = _bootstrap_plan(root, args)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 2

    print(render_bootstrap_plan(plan))
    if getattr(args, "write_approval_token", None):
        if getattr(args, "yes", False):
            receipt_path = write_setup_bootstrap_receipt(
                root,
                plan,
                status="failed",
                result="approval-token-write-conflict",
                result_summary="Approval-token writing cannot be combined with --yes.",
                checksum_status="not-run",
                provenance_status="not-run",
                exact_commands=[],
            )
            print("FAIL: --write-approval-token cannot be combined with --yes.")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1
        if not _read_bootstrap_approval():
            _record_setup_approval_decision(
                root,
                plan,
                action_ref="github-bootstrap",
                status="denied",
                approval_mode="refused",
                reason_codes=["OPERATOR_APPROVAL_REFUSED"],
            )
            receipt_path = write_setup_bootstrap_receipt(
                root,
                plan,
                status="refused",
                result="approval-refused",
                result_summary="Operator approval was not provided; no approval token was written.",
                checksum_status="not-run",
                provenance_status="not-run",
                exact_commands=[],
            )
            print("Bootstrap approval token refused. No download or install command was run.")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1
        token_path = write_setup_bootstrap_approval_token(root, plan, plan["write_approval_token_path"])
        print(f"Preview-bound approval token written: {_safe_path_summary(token_path)}")
        print("No download or install command was run.")
        return 0

    approval_mode = "typed"
    if getattr(args, "yes", False):
        if plan.get("approval_token_path") is None:
            _record_setup_approval_decision(
                root,
                plan,
                action_ref="github-bootstrap",
                status="denied",
                approval_mode="not-approved",
                reason_codes=["APPROVAL_TOKEN_REQUIRED"],
            )
            receipt_path = write_setup_bootstrap_receipt(
                root,
                plan,
                status="failed",
                result="approval-token-required",
                result_summary="--yes requires a matching preview-bound approval token; no download or install command was run.",
                checksum_status="not-run",
                provenance_status="not-run",
                exact_commands=[],
            )
            print("FAIL: --yes requires an approval token from --approval-token with a matching preview hash.")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1
        try:
            _consume_bootstrap_approval_token(root, plan, plan["approval_token_path"])
        except ValueError as exc:
            safe_error = _safe_summary_text(str(exc))
            _record_setup_approval_decision(
                root,
                plan,
                action_ref="github-bootstrap",
                status="denied",
                approval_mode="preview-token",
                reason_codes=["APPROVAL_TOKEN_INVALID"],
            )
            receipt_path = write_setup_bootstrap_receipt(
                root,
                plan,
                status="failed",
                result="approval-token-invalid",
                result_summary=f"Approval token was rejected: {safe_error}",
                checksum_status="not-run",
                provenance_status="not-run",
                exact_commands=[],
            )
            print(f"FAIL: Approval token was rejected: {safe_error}")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1
        approval_mode = "preview-token"
    else:
        approved = _read_bootstrap_approval()
        if not approved:
            _record_setup_approval_decision(
                root,
                plan,
                action_ref="github-bootstrap",
                status="denied",
                approval_mode="refused",
                reason_codes=["OPERATOR_APPROVAL_REFUSED"],
            )
            receipt_path = write_setup_bootstrap_receipt(
                root,
                plan,
                status="refused",
                result="approval-refused",
                result_summary="Operator approval was not provided; no download or install command was run.",
                checksum_status="not-run",
                provenance_status="not-run",
                exact_commands=[],
            )
            print("Bootstrap refused. No download or install command was run.")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1
    plan["approval_mode"] = approval_mode

    try:
        _authorize_setup_action(root, plan, action_ref="github-bootstrap", approval_mode=approval_mode)
    except ValueError as exc:
        safe_error = _safe_summary_text(str(exc))
        receipt_path = write_setup_bootstrap_receipt(
            root,
            plan,
            status="failed",
            result="approval-authority-denied",
            result_summary=f"Approval authority denied the scoped bootstrap: {safe_error}",
            checksum_status="not-run",
            provenance_status="not-run",
            exact_commands=[],
        )
        print(f"FAIL: Approval authority denied the scoped bootstrap: {safe_error}")
        print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
        return 1

    platform_ok, platform_summary = _bootstrap_platform_status()
    plan["platform"] = platform_summary
    if not platform_ok:
        receipt_path = write_setup_bootstrap_receipt(
            root,
            plan,
            status="failed",
            result="unsupported-platform",
            result_summary="Unsupported platform; no download or install command was run.",
            checksum_status="not-run",
            provenance_status="not-run",
            exact_commands=[],
        )
        print(f"FAIL: {platform_summary}. No download or install command was run.")
        print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
        return 1

    with tempfile.TemporaryDirectory(prefix="uaa-bootstrap-") as temp_name:
        temp_dir = Path(temp_name)
        artifact_path = temp_dir / plan["asset"]
        provenance_path = temp_dir / plan["signature_asset"]
        try:
            _download_bootstrap_file(plan["asset_url"], artifact_path)
        except RuntimeError as exc:
            receipt_path = write_setup_bootstrap_receipt(
                root,
                plan,
                status="failed",
                result="artifact-download-failed",
                result_summary=str(exc),
                checksum_status="not-run",
                provenance_status="not-run",
                exact_commands=[],
            )
            print(f"FAIL: {exc}")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1

        actual_digest = _sha256_file(artifact_path)
        if actual_digest != plan["sha256"]:
            receipt_path = write_setup_bootstrap_receipt(
                root,
                plan,
                status="failed",
                result="checksum-mismatch",
                result_summary="Artifact checksum verification failed before execution.",
                checksum_status="mismatch",
                provenance_status="not-run",
                exact_commands=[],
            )
            print("FAIL: Artifact checksum verification failed before execution.")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1

        try:
            if plan["signature_source"] == "release-asset":
                _download_bootstrap_file(plan["signature_url"], provenance_path)
            else:
                provenance_path = plan["signature_path"]
            _verify_bootstrap_provenance(provenance_path, plan)
        except (RuntimeError, ValueError) as exc:
            safe_error = _safe_summary_text(str(exc))
            receipt_path = write_setup_bootstrap_receipt(
                root,
                plan,
                status="failed",
                result="provenance-mismatch",
                result_summary=f"Provenance verification failed: {safe_error}",
                checksum_status="verified",
                provenance_status="mismatch",
                exact_commands=[],
            )
            print(f"FAIL: Provenance verification failed: {safe_error}")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1

        extract_dir = temp_dir / "installer"
        try:
            _safe_extract_bootstrap_artifact(artifact_path, extract_dir)
            installer_path = _verified_bootstrap_installer_path(extract_dir)
        except (RuntimeError, ValueError, OSError, tarfile.TarError) as exc:
            receipt_path = write_setup_bootstrap_receipt(
                root,
                plan,
                status="failed",
                result="artifact-unpack-failed",
                result_summary=f"Artifact unpack failed safely: {exc}",
                checksum_status="verified",
                provenance_status="verified",
                exact_commands=[],
            )
            print(f"FAIL: Artifact unpack failed safely: {exc}")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1

        command = _bootstrap_installer_command(plan, installer_path)
        print("Running approved verified local installer command:")
        print(f"- {_redacted_command_preview(command)}")
        result = _run_bootstrap_installer_command(command)
        if result["returncode"] != 0:
            safe_summary = _safe_summary_text(result["summary"])
            receipt_path = write_setup_bootstrap_receipt(
                root,
                plan,
                status="failed",
                result="installer-failed",
                result_summary=f"Verified local installer failed safely: {safe_summary}",
                checksum_status="verified",
                provenance_status="verified",
                exact_commands=[command],
            )
            print(f"FAIL: Verified local installer failed safely: {safe_summary}")
            print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
            return 1

        receipt_path = write_setup_bootstrap_receipt(
            root,
            plan,
            status="installed",
            result="completed",
            result_summary="Verified local OpenWebUI bootstrap installer completed.",
            checksum_status="verified",
            provenance_status="verified",
            exact_commands=[command],
        )
        print("GitHub bootstrap local installer completed.")
        print(f"Redacted receipt written: {_safe_path_summary(receipt_path)}")
        print("Rollback:")
        for step in _bootstrap_rollback_hints(plan):
            print(f"- {step}")
        return 0


def render_bootstrap_plan(plan: dict[str, Any]) -> str:
    lines = [
        "M167 GitHub bootstrap local installer preview",
        f"Target: {plan['target']}",
        f"Milestone: {plan['milestone_ref']}",
        f"Approved repository: {BOOTSTRAP_REPO_URL}",
        f"Release tag: {plan['release_tag']}",
        f"Asset: {plan['asset']}",
        "SHA-256: provided as a 64-character digest; value is not echoed in full.",
        f"Signature/provenance: {plan['signature_summary']}",
        f"Provenance mode: {plan['provenance_mode']}",
        f"Preview hash: {plan['preview_hash']}",
        f"Install directory: {_safe_path_summary(plan['install_dir'])}",
        f"Bin directory: {_safe_path_summary(plan['bin_dir'])}",
        f"Receipt: {_safe_path_summary(plan['receipt_path'])}",
        "",
        "Download URL derived from approved repo and explicit release tag:",
        f"- {plan['asset_url']}",
    ]
    if plan["signature_source"] == "release-asset":
        lines.append(f"- {plan['signature_url']}")
    if plan["provenance_mode"] == "minisign":
        lines.extend(
            [
                "",
                "Public trust root:",
                f"- {BOOTSTRAP_MINISIGN_PUBLIC_KEY_REF}",
                f"- SHA-256 {BOOTSTRAP_MINISIGN_PUBLIC_KEY_SHA256}",
            ]
        )
    lines.extend(
        [
            "",
            "Verified local command shape after unpack:",
            f"- <verified-temp>/{BOOTSTRAP_INSTALLER_NAME} install --target {plan['target']} --bin-dir {_safe_path_summary(plan['bin_dir'])} --install-dir {_safe_path_summary(plan['install_dir'])} --receipt {_safe_path_summary(plan['receipt_path'])} --yes",
            "",
            "Authority boundary:",
            "- Downloads only the exact UAA GitHub Release artifact and provenance artifact named above.",
            "- Verifies SHA-256 and the selected provenance mode before any installer code runs.",
            "- Runs only the verified local OpenWebUI bootstrap installer argv.",
            "- Does not install Python, Node/npm dependencies, Homebrew packages, Docker Desktop, llama.cpp, providers, models, plugins, browser tooling, mobile tooling, remote workers, credentials, launch agents, daemons, or background services.",
            "- Does not start OpenWebUI, call UAA /v1, call providers/models, grant OpenWebUI tool/function authority, write memory, or mutate OpenWebUI internals.",
            "",
            "Consent:",
            f'- Type "{SETUP_BOOTSTRAP_CONFIRMATION}" to approve interactively.',
            "- Noninteractive --yes requires a matching preview-bound --approval-token.",
            "",
            "Rollback:",
        ]
    )
    for step in _bootstrap_rollback_hints(plan):
        lines.append(f"- {step}")
    return "\n".join(lines)


def write_setup_bootstrap_receipt(
    root: Path,
    plan: dict[str, Any],
    *,
    status: str,
    result: str,
    result_summary: str,
    checksum_status: str,
    provenance_status: str,
    exact_commands: list[list[str]],
) -> Path:
    _ = root
    target = plan["receipt_path"]
    payload = {
        "schema": "uaa.setup_bootstrap_receipt.v1",
        "milestone_ref": plan["milestone_ref"],
        "repo": BOOTSTRAP_REPO_URL,
        "release_tag": plan["release_tag"],
        "asset": plan["asset"],
        "asset_sha256": plan["sha256"],
        "signature": plan["signature_summary"],
        "provenance_mode": plan["provenance_mode"],
        "target": plan["target"],
        "installer": BOOTSTRAP_INSTALLER_NAME,
        "authority": BOOTSTRAP_AUTHORITY,
        "platform": plan.get("platform", "not-checked"),
        "bin_dir": _safe_path_summary(plan["bin_dir"]),
        "install_dir": _safe_path_summary(plan["install_dir"]),
        "receipt": _safe_path_summary(target),
        "preview_hash": plan["preview_hash"],
        "approval_mode": plan.get("approval_mode", "not-approved"),
        "approval_authority": plan.get("approval_authority", SETUP_APPROVAL_AUTHORITY_LABEL),
        "approval_decision_ref": plan.get("approval_decision_ref"),
        "path_mutation_status": "delegated-to-verified-local-installer",
        "installed_assets": [BOOTSTRAP_INSTALLER_NAME] if status == "installed" else [],
        "openwebui_image_status": "delegated-to-existing-m167-openwebui-installer-boundary",
        "checksum_status": checksum_status,
        "provenance_status": provenance_status,
        "status": status,
        "result": result,
        "result_summary": _safe_summary_text(result_summary),
        "exact_commands": [_redacted_command_preview(command) for command in exact_commands],
        "rollback_hints": _bootstrap_rollback_hints(plan),
        "created_at": _utc_timestamp(),
        "redaction": "safe summary only; no credentials, provider keys, usernames, environment dump, raw prompts, raw responses, raw provider payloads, raw logs, cookies, or shell history",
    }
    _write_json_0600(target, payload)
    return target


def _bootstrap_plan(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    release_tag = _validate_bootstrap_release_tag(str(args.release_tag))
    asset = _validate_bootstrap_asset_name(str(args.asset), option_name="--asset")
    sha256 = _validate_bootstrap_sha256(str(args.sha256))
    target = str(getattr(args, "target", ""))
    if target != "openwebui":
        raise ValueError(f"Unsupported bootstrap target: {target}")
    bin_dir = _validate_bootstrap_dir_path(root, Path(str(args.bin_dir)).expanduser(), option_name="--bin-dir")
    install_dir = _validate_bootstrap_dir_path(root, Path(str(args.install_dir)).expanduser(), option_name="--install-dir")
    _validate_bootstrap_launcher_slot(bin_dir)
    receipt = getattr(args, "receipt", None)
    receipt_path = (
        _validate_bootstrap_receipt_path(root, Path(str(receipt)).expanduser())
        if receipt
        else _validate_bootstrap_receipt_path(root, _bootstrap_receipt_path(root, target=target, release_tag=release_tag))
    )
    approval_token = getattr(args, "approval_token", None)
    approval_token_path = (
        _validate_bootstrap_existing_file_path(root, Path(str(approval_token)).expanduser(), option_name="--approval-token")
        if approval_token
        else None
    )
    write_approval_token = getattr(args, "write_approval_token", None)
    write_approval_token_path = (
        _validate_bootstrap_receipt_path(root, Path(str(write_approval_token)).expanduser())
        if write_approval_token
        else None
    )
    signature = _bootstrap_signature_reference(root, str(args.signature), release_tag=release_tag)
    provenance_mode = str(getattr(args, "provenance_mode", "minisign"))
    if provenance_mode not in BOOTSTRAP_PROVENANCE_MODES:
        raise ValueError(f"Unsupported provenance mode: {provenance_mode}")
    plan = {
        "target": target,
        "milestone_ref": SETUP_BOOTSTRAP_MILESTONE_REF,
        "release_tag": release_tag,
        "asset": asset,
        "asset_url": _bootstrap_release_asset_url(release_tag, asset),
        "sha256": sha256,
        "signature_source": signature["source"],
        "signature_asset": signature["asset"],
        "signature_url": signature.get("url"),
        "signature_path": signature.get("path"),
        "signature_summary": signature["summary"],
        "provenance_mode": provenance_mode,
        "bin_dir": bin_dir,
        "install_dir": install_dir,
        "receipt_path": receipt_path,
        "approval_token_path": approval_token_path,
        "write_approval_token_path": write_approval_token_path,
        "approval_mode": "not-approved",
        "platform": "not-checked",
        "openwebui_image": OPENWEBUI_IMAGE,
    }
    plan["preview_hash"] = _bootstrap_preview_hash(plan)
    return plan


def _bootstrap_preview_hash(plan: dict[str, Any]) -> str:
    payload = {
        "schema": "uaa.setup_bootstrap_preview.v1",
        "milestone_ref": plan["milestone_ref"],
        "repo": BOOTSTRAP_REPO_URL,
        "release_tag": plan["release_tag"],
        "asset": plan["asset"],
        "sha256": plan["sha256"],
        "signature_source": plan["signature_source"],
        "signature_asset": plan["signature_asset"],
        "signature_summary": plan["signature_summary"],
        "provenance_mode": plan["provenance_mode"],
        "target": plan["target"],
        "bin_dir": _safe_path_summary(plan["bin_dir"]),
        "install_dir": _safe_path_summary(plan["install_dir"]),
        "receipt": _safe_path_summary(plan["receipt_path"]),
        "openwebui_image": OPENWEBUI_IMAGE,
    }
    if plan["provenance_mode"] == "minisign":
        payload["minisign_public_key_ref"] = BOOTSTRAP_MINISIGN_PUBLIC_KEY_REF
        payload["minisign_public_key_sha256"] = BOOTSTRAP_MINISIGN_PUBLIC_KEY_SHA256
        payload["minisign_trust_root_identity"] = BOOTSTRAP_MINISIGN_TRUST_ROOT_IDENTITY
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_setup_bootstrap_approval_token(
    root: Path,
    plan: dict[str, Any],
    token_path: Path,
    *,
    ttl_seconds: int = SETUP_BOOTSTRAP_APPROVAL_TOKEN_TTL_SECONDS,
) -> Path:
    now = int(time.time())
    payload = {
        "schema": SETUP_BOOTSTRAP_APPROVAL_TOKEN_SCHEMA,
        "milestone_ref": plan["milestone_ref"],
        "target": plan["target"],
        "release_tag": plan["release_tag"],
        "asset": plan["asset"],
        "provenance_mode": plan["provenance_mode"],
        "preview_hash": plan["preview_hash"],
        "expires_at_epoch": now + ttl_seconds,
        "created_at": _utc_timestamp(),
        "used_at": None,
        "redaction": "safe approval metadata only; no credentials, env values, usernames, raw logs, prompts, or provider payloads",
    }
    token_path = _validate_bootstrap_receipt_path(root, token_path)
    _write_json_0600(token_path, payload)
    return token_path


def _consume_bootstrap_approval_token(root: Path, plan: dict[str, Any], token_path: Path) -> None:
    expected = {
        "schema": SETUP_BOOTSTRAP_APPROVAL_TOKEN_SCHEMA,
        "milestone_ref": plan["milestone_ref"],
        "target": plan["target"],
        "release_tag": plan["release_tag"],
        "asset": plan["asset"],
        "provenance_mode": plan["provenance_mode"],
    }
    _consume_setup_approval_token(
        root,
        plan,
        token_path,
        schema=SETUP_BOOTSTRAP_APPROVAL_TOKEN_SCHEMA,
        expected=expected,
    )


def _consume_setup_approval_token(
    root: Path,
    plan: dict[str, Any],
    token_path: Path,
    *,
    schema: str,
    expected: dict[str, str],
) -> None:
    _ = (root, plan, schema)
    if token_path.is_symlink():
        raise ValueError("approval token must not be a symlink")
    if stat.S_IMODE(token_path.stat().st_mode) & 0o077:
        raise ValueError("approval token must be chmod 0600")
    lock_path = token_path.with_name(f"{token_path.name}.lock")
    lock_fd: int | None = None
    try:
        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ValueError("approval token is already being consumed") from exc
        try:
            payload = json.loads(token_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("approval token is missing or malformed") from exc
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                raise ValueError(f"approval token field {key} mismatch")
        if payload.get("preview_hash") != plan["preview_hash"]:
            raise ValueError("approval token preview hash mismatch")
        if payload.get("used_at"):
            raise ValueError("approval token was already used")
        try:
            expires_at = int(payload["expires_at_epoch"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("approval token expiration is missing or malformed") from exc
        if expires_at < int(time.time()):
            raise ValueError("approval token expired")
        payload["used_at"] = _utc_timestamp()
        _write_json_0600(token_path, payload)
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def _authorize_setup_action(root: Path, plan: dict[str, Any], *, action_ref: str, approval_mode: str) -> None:
    decision = _policy_engine_approval_decision(root, plan, action_ref=action_ref, approval_mode=approval_mode)
    receipt_path = _record_setup_approval_decision(
        root,
        plan,
        action_ref=action_ref,
        status="allowed" if decision["allowed"] else "denied",
        approval_mode=approval_mode,
        reason_codes=decision["reason_codes"],
        policy_decision=decision,
    )
    plan["approval_authority"] = SETUP_APPROVAL_AUTHORITY_LABEL
    plan["approval_decision_ref"] = decision["decision_ref"]
    plan["approval_receipt"] = _display_path(root, receipt_path)
    if not decision["allowed"]:
        raise ValueError("; ".join(decision["reason_codes"]) or "approval policy denied")


def _policy_engine_approval_decision(
    root: Path,
    plan: dict[str, Any],
    *,
    action_ref: str,
    approval_mode: str,
) -> dict[str, Any]:
    try:
        _ensure_src_on_path()
        from ultimate_ai_agent.core.capabilities.approval import CapabilityApprovalGrant, LocalApprovalAuthority
        from ultimate_ai_agent.core.capabilities.enums import CapabilityKind, CoordinationMode, RiskLevel, SideEffectLevel
        from ultimate_ai_agent.core.capabilities.models import CapabilityManifest, SafetyPolicy, TaskEnvelope
        from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
    except Exception as exc:
        return {
            "allowed": False,
            "decision_ref": _setup_approval_decision_ref(action_ref, plan),
            "reason_codes": ["APPROVAL_AUTHORITY_IMPORT_FAILED"],
            "safe_message": f"Approval authority import failed safely: {exc.__class__.__name__}",
            "capability_id": _setup_capability_id(action_ref),
            "task_id": _setup_task_id(action_ref, plan),
        }

    capability_id = _setup_capability_id(action_ref)
    task_id = _setup_task_id(action_ref, plan)
    approval_ref = f"approval:m167:{action_ref}:{plan['preview_hash'][:16]}"
    manifest = CapabilityManifest(
        id=capability_id,
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name=capability_id,
        description="Exact-scope local-dev setup approval gate for M167.",
        tags=["m167", "setup", "local-dev"],
        examples=["Approve the exact preview hash for the scoped OpenWebUI setup action."],
        anti_examples=["Treat OpenWebUI or provider output as approval authority."],
        input_schema={"type": "object", "additionalProperties": False},
        output_schema={"type": "object", "additionalProperties": False},
        input_modes=["local_dev_setup_preview"],
        output_modes=["redacted_approval_decision"],
        side_effects=SideEffectLevel.external,
        risk_level=RiskLevel.high,
        approval_required=True,
        allowed_coordination_modes=[CoordinationMode.human_gate],
        concurrency_safe=False,
        single_writer_required=True,
        safety=SafetyPolicy(
            approval_required=True,
            require_single_writer=True,
            max_risk_level=RiskLevel.high,
            max_side_effect_level=SideEffectLevel.external,
        ),
    )
    task = TaskEnvelope(
        task_id=task_id,
        user_request="Approve exact M167 local-dev setup preview.",
        objective="Authorize only the scoped setup action described by the preview hash.",
        scope=[action_ref, plan["target"], plan["preview_hash"]],
        out_of_scope=[
            "provider/model authority",
            "OpenWebUI admin/plugin mutation",
            "broad system dependency install",
            "background service launch",
        ],
        selected_capability_ids=[capability_id],
        context={
            "approval_ref": approval_ref,
            "preview_hash": plan["preview_hash"],
            "approval_mode": approval_mode,
            "idempotency_key": plan["preview_hash"],
        },
    )
    grant = CapabilityApprovalGrant(
        approval_ref=approval_ref,
        capability_id=capability_id,
        granted_by="local-operator",
        task_id=task_id,
        max_risk_level=RiskLevel.high,
        max_side_effect_level=SideEffectLevel.external,
        reason="Operator approval captured for exact M167 local-dev setup scope.",
        metadata={
            "preview_hash": plan["preview_hash"],
            "approval_mode": approval_mode,
            "target": plan["target"],
            "action_ref": action_ref,
        },
    )
    authority = LocalApprovalAuthority([grant])
    decision = PolicyEngine(approval_authority=authority).can_execute(
        manifest,
        task,
        {
            "approval_ref": approval_ref,
            "approval_grants": [grant],
            "coordination_mode": CoordinationMode.human_gate.value,
            "external_side_effect": True,
            "idempotency_key": plan["preview_hash"],
        },
    )
    return {
        "allowed": bool(decision.allowed),
        "decision_ref": _setup_approval_decision_ref(action_ref, plan),
        "reason_codes": list(decision.reason_codes),
        "safe_message": decision.safe_message,
        "capability_id": capability_id,
        "task_id": task_id,
    }


def _record_setup_approval_decision(
    root: Path,
    plan: dict[str, Any],
    *,
    action_ref: str,
    status: str,
    approval_mode: str,
    reason_codes: list[str],
    policy_decision: dict[str, Any] | None = None,
) -> Path:
    decision_ref = (policy_decision or {}).get("decision_ref") or _setup_approval_decision_ref(action_ref, plan)
    plan["approval_authority"] = SETUP_APPROVAL_AUTHORITY_LABEL
    plan["approval_decision_ref"] = decision_ref
    receipt_path = root / SETUP_APPROVAL_RECEIPT_DIR / f"{action_ref}-{plan['preview_hash'][:16]}-{_utc_timestamp()}.json"
    payload = {
        "schema": SETUP_APPROVAL_RECEIPT_SCHEMA,
        "authority": SETUP_APPROVAL_AUTHORITY_LABEL,
        "decision_ref": decision_ref,
        "status": status,
        "reason_codes": list(dict.fromkeys(reason_codes)),
        "capability_id": (policy_decision or {}).get("capability_id", _setup_capability_id(action_ref)),
        "task_id": (policy_decision or {}).get("task_id", _setup_task_id(action_ref, plan)),
        "approval_mode": approval_mode,
        "actor": "local-operator",
        "scope": _setup_approval_scope(plan, action_ref=action_ref),
        "revocation": {
            "revocable": True,
            "method": "Delete or disregard this exact local-dev receipt; it grants no reusable runtime authority.",
        },
        "replay": {
            "preview_hash": plan["preview_hash"],
            "single_use_token_required_for_yes": True,
            "typed_approval_not_reusable": True,
        },
        "created_at": _utc_timestamp(),
        "redaction": "safe summary only; no credentials, provider keys, usernames, env dumps, raw prompts, raw responses, raw provider payloads, raw logs, cookies, or token secrets",
    }
    _write_json_0600(receipt_path, payload)
    return receipt_path


def _setup_approval_scope(plan: dict[str, Any], *, action_ref: str) -> dict[str, Any]:
    scope: dict[str, Any] = {
        "milestone_ref": plan["milestone_ref"],
        "action_ref": action_ref,
        "target": plan["target"],
        "preview_hash": plan["preview_hash"],
    }
    if action_ref == "openwebui-image-pull":
        scope.update(
            {
                "image_ref": plan["image_ref"],
                "commands": [_shell_preview(command) for command in plan["commands"]],
                "rollback_steps": plan["rollback_steps"],
            }
        )
    else:
        scope.update(
            {
                "repo": BOOTSTRAP_REPO_URL,
                "release_tag": plan["release_tag"],
                "asset": plan["asset"],
                "asset_sha256": plan["sha256"],
                "signature": plan["signature_summary"],
                "provenance_mode": plan["provenance_mode"],
                "bin_dir": _safe_path_summary(plan["bin_dir"]),
                "install_dir": _safe_path_summary(plan["install_dir"]),
                "receipt": _safe_path_summary(plan["receipt_path"]),
                "openwebui_image": plan["openwebui_image"],
            }
        )
        if plan["provenance_mode"] == "minisign":
            scope.update(
                {
                    "public_key_ref": BOOTSTRAP_MINISIGN_PUBLIC_KEY_REF,
                    "public_key_sha256": BOOTSTRAP_MINISIGN_PUBLIC_KEY_SHA256,
                    "trust_root_identity": BOOTSTRAP_MINISIGN_TRUST_ROOT_IDENTITY,
                }
            )
    return scope


def _setup_capability_id(action_ref: str) -> str:
    if action_ref == "openwebui-image-pull":
        return "setup.openwebui_image_pull.v1"
    return "setup.github_bootstrap.v1"


def _setup_task_id(action_ref: str, plan: dict[str, Any]) -> str:
    return f"task:m167:{action_ref}:{plan['preview_hash'][:16]}"


def _setup_approval_decision_ref(action_ref: str, plan: dict[str, Any]) -> str:
    return f"setup-approval:{action_ref}:{plan['preview_hash'][:16]}"


def _ensure_src_on_path() -> None:
    src = Path(__file__).resolve().parents[2] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _bootstrap_signature_reference(root: Path, value: str, *, release_tag: str) -> dict[str, Any]:
    reference = value.strip()
    if not reference:
        raise ValueError("--signature is required")
    if _looks_like_url(reference):
        raise ValueError("--signature must be an exact release asset name or a canonical user-scope local path")
    if _looks_like_path(reference):
        path = _validate_bootstrap_existing_file_path(root, Path(reference).expanduser(), option_name="--signature")
        return {
            "source": "local-file",
            "asset": path.name,
            "path": path,
            "summary": f"local provenance file {_safe_path_summary(path)}",
        }
    asset = _validate_bootstrap_asset_name(reference, option_name="--signature")
    return {
        "source": "release-asset",
        "asset": asset,
        "url": _bootstrap_release_asset_url(release_tag, asset),
        "summary": f"release asset {asset}",
    }


def _bootstrap_release_tag_arg(value: str) -> str:
    try:
        return _validate_bootstrap_release_tag(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _bootstrap_asset_arg(value: str) -> str:
    try:
        return _validate_bootstrap_asset_name(value, option_name="--asset")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _bootstrap_sha256_arg(value: str) -> str:
    try:
        return _validate_bootstrap_sha256(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _validate_bootstrap_release_tag(value: str) -> str:
    tag = value.strip()
    if not tag:
        raise ValueError("--release-tag is required")
    lowered = tag.lower()
    if lowered in {"main", "master", "latest", "head"} or lowered.startswith("refs/") or "/" in tag or "\\" in tag:
        raise ValueError("--release-tag must be an explicit immutable release tag; mutable refs are denied")
    if ".." in tag or not BOOTSTRAP_RELEASE_TAG_RE.fullmatch(tag):
        raise ValueError("--release-tag contains unsupported characters")
    if not BOOTSTRAP_RELEASE_TAG_POLICY_RE.fullmatch(tag):
        raise ValueError("--release-tag must match the reviewed M167 release tag policy")
    return tag


def _validate_bootstrap_asset_name(value: str, *, option_name: str) -> str:
    asset = value.strip()
    if not asset:
        raise ValueError(f"{option_name} is required")
    if _looks_like_url(asset):
        raise ValueError(f"{option_name} must be an exact release asset name, not a URL")
    if "/" in asset or "\\" in asset or ".." in asset:
        raise ValueError(f"{option_name} must be an exact asset name without path traversal")
    if not BOOTSTRAP_ASSET_RE.fullmatch(asset):
        raise ValueError(f"{option_name} contains unsupported characters")
    if option_name == "--asset" and asset not in BOOTSTRAP_ALLOWED_ASSETS:
        raise ValueError(f"{option_name} is not in the reviewed M167 platform asset allowlist")
    return asset


def _validate_bootstrap_sha256(value: str) -> str:
    digest = value.strip().lower()
    if not BOOTSTRAP_SHA256_RE.fullmatch(digest):
        raise ValueError("--sha256 must be a 64-character hexadecimal digest")
    return digest


def _validate_bootstrap_dir_path(root: Path, value: Path | str, *, option_name: str) -> Path:
    path = _canonical_user_scope_path(root, value, option_name=option_name)
    if path.exists() and not path.is_dir():
        raise ValueError(f"{option_name} must be a directory path; unrelated existing files are denied")
    _reject_world_writable_bootstrap_path(path, expect_directory=True, option_name=option_name)
    return path


def _validate_bootstrap_receipt_path(root: Path, value: Path | str) -> Path:
    raw = Path(value)
    candidate = raw if raw.is_absolute() else root / raw
    if candidate.is_symlink():
        raise ValueError("--receipt must not be a symlink")
    if any(parent.is_symlink() for parent in candidate.parents):
        raise ValueError("--receipt could not be resolved safely")
    try:
        path = _canonical_user_scope_path(root, value, option_name="--receipt")
    except (OSError, RuntimeError) as exc:
        raise ValueError("--receipt could not be resolved safely") from exc
    if path.exists():
        raise ValueError("--receipt already exists; refusing to overwrite an unrelated receipt file")
    if path.parent.exists() and not path.parent.is_dir():
        raise ValueError("--receipt parent must be a directory")
    _reject_world_writable_bootstrap_path(path.parent, expect_directory=True, option_name="--receipt")
    return path


def _validate_bootstrap_existing_file_path(root: Path, value: Path | str, *, option_name: str) -> Path:
    path = _canonical_user_scope_path(root, value, option_name=option_name)
    raw = Path(value)
    candidate = raw if raw.is_absolute() else root / raw
    if candidate.is_symlink():
        raise ValueError(f"{option_name} must not be a symlink")
    if not path.is_file():
        raise ValueError(f"{option_name} local path must exist and be a file")
    _reject_world_writable_bootstrap_path(path.parent, expect_directory=True, option_name=option_name)
    return path


def _validate_bootstrap_launcher_slot(bin_dir: Path) -> None:
    launcher = bin_dir / "uaa"
    if launcher.exists() or launcher.is_symlink():
        raise ValueError("--bin-dir has an existing uaa launcher; refusing to overwrite unrelated existing uaa files")


def _canonical_user_scope_path(root: Path, value: Path | str, *, option_name: str) -> Path:
    path_value = Path(value)
    raw = path_value if path_value.is_absolute() else root / path_value
    resolved = raw.resolve(strict=False)
    home = _bootstrap_user_home().resolve(strict=False)
    try:
        resolved.relative_to(home)
    except ValueError as exc:
        raise ValueError(f"{option_name} must be a canonical user-scope path under the current user's home directory") from exc
    return resolved


def _reject_world_writable_bootstrap_path(path: Path, *, expect_directory: bool, option_name: str) -> None:
    home = _bootstrap_user_home().resolve(strict=False)
    resolved = path.resolve(strict=False)
    check_path = resolved if expect_directory else resolved.parent
    try:
        relative = check_path.relative_to(home)
    except ValueError:
        return
    current = home
    for part in relative.parts:
        if current.exists() and current.is_dir() and stat.S_IMODE(current.stat().st_mode) & stat.S_IWOTH:
            raise ValueError(f"{option_name} crosses a world-writable directory")
        current = current / part
    if current.exists() and current.is_dir() and stat.S_IMODE(current.stat().st_mode) & stat.S_IWOTH:
        raise ValueError(f"{option_name} crosses a world-writable directory")


def _bootstrap_user_home() -> Path:
    return Path.home()


def _bootstrap_platform_status() -> tuple[bool, str]:
    system = platform.system()
    machine = platform.machine()
    if system == "Darwin" and machine == "arm64":
        return True, "macOS arm64 supported"
    return False, f"unsupported platform ({system or 'unknown'} {machine or 'unknown'})"


def _bootstrap_release_asset_url(release_tag: str, asset: str) -> str:
    quoted_tag = urllib_parse.quote(release_tag, safe="")
    quoted_asset = urllib_parse.quote(asset, safe="")
    return f"{BOOTSTRAP_RELEASE_BASE_URL}/{quoted_tag}/{quoted_asset}"


def _download_bootstrap_file(url: str, destination: Path) -> None:
    parsed = urllib_parse.urlparse(url)
    approved_prefix = "/doncazper/ultimate-ai-agent/releases/download/"
    if parsed.scheme != "https" or parsed.netloc != "github.com" or not parsed.path.startswith(approved_prefix):
        raise RuntimeError("bootstrap download source is outside the approved GitHub repository")
    request = urllib_request.Request(url, headers={"User-Agent": "uaa-setup-bootstrap"})
    try:
        with urllib_request.urlopen(request, timeout=BOOTSTRAP_DOWNLOAD_TIMEOUT_SECONDS) as response:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    handle.write(chunk)
    except (OSError, TimeoutError, urllib_error.URLError, urllib_error.HTTPError) as exc:
        raise RuntimeError(f"bootstrap download failed safely: {exc.__class__.__name__}") from exc


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _verify_bootstrap_provenance(path: Path, plan: dict[str, Any]) -> None:
    if plan["provenance_mode"] != "local-dev-json":
        _verify_bootstrap_cryptographic_provenance(path, plan)
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("provenance manifest is missing or malformed") from exc
    expected = {
        "schema": BOOTSTRAP_PROVENANCE_SCHEMA,
        "repo": BOOTSTRAP_REPO_URL,
        "release_tag": plan["release_tag"],
        "asset": plan["asset"],
        "sha256": plan["sha256"],
        "target": plan["target"],
        "installer": BOOTSTRAP_INSTALLER_NAME,
        "trust_root": BOOTSTRAP_TRUST_ROOT_REF,
        "authority": BOOTSTRAP_AUTHORITY,
    }
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            raise ValueError(f"provenance field {key} mismatch")


def _verify_bootstrap_cryptographic_provenance(path: Path, plan: dict[str, Any]) -> None:
    if plan["provenance_mode"] != "minisign":
        raise ValueError("unsupported cryptographic provenance mode")
    if not path.is_file():
        raise ValueError("minisign detached signature is missing")
    public_key = _bootstrap_minisign_public_key(_bootstrap_repo_root())
    statement = _bootstrap_minisign_statement(plan)
    with tempfile.TemporaryDirectory(prefix="uaa-bootstrap-minisign-") as temp_name:
        statement_path = Path(temp_name) / "uaa-bootstrap-statement.json"
        statement_path.write_bytes(statement)
        result = _run_minisign_verify(statement_path, path, public_key)
    if result.get("raw_output_retained"):
        raise ValueError("minisign verifier returned untrusted raw output")
    plan["provenance_verifier"] = "minisign"


def _bootstrap_minisign_statement(plan: dict[str, Any]) -> bytes:
    payload = {
        "schema": BOOTSTRAP_MINISIGN_STATEMENT_SCHEMA,
        "repo": BOOTSTRAP_REPO_URL,
        "release_tag": plan["release_tag"],
        "asset": plan["asset"],
        "sha256": plan["sha256"],
        "target": plan["target"],
        "installer": BOOTSTRAP_INSTALLER_NAME,
        "trust_root": BOOTSTRAP_TRUST_ROOT_REF,
        "trust_root_identity": BOOTSTRAP_MINISIGN_TRUST_ROOT_IDENTITY,
        "public_key_ref": BOOTSTRAP_MINISIGN_PUBLIC_KEY_REF,
        "public_key_sha256": BOOTSTRAP_MINISIGN_PUBLIC_KEY_SHA256,
        "authority": BOOTSTRAP_AUTHORITY,
        "provenance_mode": "minisign",
    }
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _bootstrap_minisign_public_key(root: Path) -> str:
    key_path = root / BOOTSTRAP_MINISIGN_PUBLIC_KEY_REF
    if not key_path.exists():
        key_path = _bootstrap_repo_root() / BOOTSTRAP_MINISIGN_PUBLIC_KEY_REF
    try:
        key_text = key_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError("repo-pinned minisign public key is missing") from exc
    actual = hashlib.sha256(key_text.encode("utf-8")).hexdigest()
    if actual != BOOTSTRAP_MINISIGN_PUBLIC_KEY_SHA256:
        raise ValueError("repo-pinned minisign public key fingerprint mismatch")
    lines = [line.strip() for line in key_text.splitlines() if line.strip() and not line.startswith("untrusted comment:")]
    if len(lines) != 1 or not re.fullmatch(r"[A-Za-z0-9+/=]{40,120}", lines[0]):
        raise ValueError("repo-pinned minisign public key is malformed")
    return lines[0]


def _run_minisign_verify(statement_path: Path, signature_path: Path, public_key: str) -> dict[str, Any]:
    minisign = _resolve_command("minisign")
    if minisign is None:
        raise ValueError("cryptographic minisign verifier is unavailable; public bootstrap mode fails closed")
    if signature_path.is_symlink():
        raise ValueError("minisign signature must not be a symlink")
    command = [
        str(minisign),
        "-Vm",
        str(statement_path),
        "-P",
        public_key,
        "-x",
        str(signature_path),
        "-q",
    ]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=30.0,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("minisign verification timed out; public bootstrap mode fails closed") from exc
    except OSError as exc:
        raise ValueError(f"minisign verifier could not start: {exc.__class__.__name__}") from exc
    if result.returncode != 0:
        raise ValueError("minisign verification failed; public bootstrap mode fails closed")
    return {"verifier": "minisign", "raw_output_retained": False}


def _bootstrap_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _safe_extract_bootstrap_artifact(archive_path: Path, extract_dir: Path) -> None:
    extract_root = extract_dir.resolve(strict=False)
    extract_root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, mode="r:*") as archive:
        for member in archive.getmembers():
            member_path = Path(member.name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError("archive contains path traversal")
            destination = (extract_root / member_path).resolve(strict=False)
            try:
                destination.relative_to(extract_root)
            except ValueError as exc:
                raise ValueError("archive entry escapes the temporary installer directory") from exc
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise ValueError("archive contains unsupported non-regular entries")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError("archive member could not be read")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with source, destination.open("wb") as handle:
                shutil.copyfileobj(source, handle)
            destination.chmod(member.mode & 0o777)


def _verified_bootstrap_installer_path(extract_dir: Path) -> Path:
    installer = (extract_dir / BOOTSTRAP_INSTALLER_NAME).resolve(strict=False)
    extract_root = extract_dir.resolve(strict=False)
    try:
        installer.relative_to(extract_root)
    except ValueError as exc:
        raise ValueError("verified installer path escapes the temporary installer directory") from exc
    if not _is_executable_file(installer):
        raise ValueError("verified installer executable is missing or not executable")
    return installer


def _bootstrap_installer_command(plan: dict[str, Any], installer_path: Path) -> list[str]:
    return [
        str(installer_path),
        "install",
        "--target",
        plan["target"],
        "--bin-dir",
        str(plan["bin_dir"]),
        "--install-dir",
        str(plan["install_dir"]),
        "--receipt",
        str(plan["receipt_path"]),
        "--yes",
    ]


def _run_bootstrap_installer_command(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=BOOTSTRAP_INSTALL_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": 1, "summary": "verified local installer timed out"}
    except OSError as exc:
        return {"returncode": 1, "summary": f"verified local installer could not start: {exc.__class__.__name__}"}
    summary = "completed" if result.returncode == 0 else f"installer exited with code {result.returncode}"
    return {"returncode": result.returncode, "summary": summary}


def _bootstrap_rollback_hints(plan: dict[str, Any]) -> list[str]:
    _ = plan
    return [
        "Remove only receipt-bound or marker-owned uaa launcher files; refuse unrelated existing files.",
        "Remove only receipt-bound or marker-owned files under the user-scope UAA install directory.",
        "Restore only shell profile backups and marked PATH blocks created by the verified local installer.",
        f"OpenWebUI image rollback remains separate and explicit: docker image rm {OPENWEBUI_IMAGE}.",
        "OpenWebUI data reset remains separate and requires explicit canonical-path approval before any removal.",
    ]


def _bootstrap_receipt_path(root: Path, *, target: str, release_tag: str) -> Path:
    safe_tag = re.sub(r"[^A-Za-z0-9._+-]", "_", release_tag)
    return root / SETUP_BOOTSTRAP_RECEIPT_DIR / f"{target}-{safe_tag}-{_utc_timestamp()}.json"


def _read_bootstrap_approval() -> bool:
    print(f'Type "{SETUP_BOOTSTRAP_CONFIRMATION}" to approve this GitHub bootstrap: ', end="")
    try:
        return sys.stdin.readline().strip() == SETUP_BOOTSTRAP_CONFIRMATION
    except OSError:
        return False


def _looks_like_url(value: str) -> bool:
    parsed = urllib_parse.urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def _looks_like_path(value: str) -> bool:
    return value.startswith((".", "~", os.sep)) or os.sep in value or ("\\" in value)


def build_setup_report(
    root: Path,
    *,
    mode: str,
    profile: str | None = None,
    provider: str | None,
    model_id: str,
    hf_repo: str,
    hf_file: str,
    check_env: Path | None = None,
) -> SetupReport:
    effective_profile = _effective_profile(mode=mode, profile=profile)
    effective_mode = _effective_mode(mode=mode, profile=effective_profile)
    docker_finding = (
        _probe_docker()
        if effective_profile in {"openwebui-smoke", "local-llama"}
        else SetupFinding("docker", "pass", "Docker not checked for this profile.", "No action needed.")
    )
    findings = _profile_findings(root, profile=effective_profile, docker_finding=docker_finding)
    if check_env is not None:
        findings.extend(check_local_llama_env_file(root, check_env, model_id=model_id))
    if effective_mode == "local-llama" and effective_profile == "local-llama":
        findings.extend(
            [
                _probe_local_llama_gateway_env(model_id),
                _probe_model_alias(mode=effective_mode, model_id=model_id),
                _probe_uaa_gateway_status(root, mode=effective_mode),
                _probe_llama_server(),
                _probe_llama_server_port(),
            ]
        )
    elif effective_mode == "smoke" and effective_profile == "openwebui-smoke":
        findings.extend(
            [
                _probe_smoke_gateway_env(),
                _probe_model_alias(mode=effective_mode, model_id=model_id),
                _probe_uaa_gateway_status(root, mode=effective_mode),
            ]
        )
    elif mode == "frontier":
        findings.extend([_probe_model_alias(mode=mode, model_id=model_id), *_frontier_findings(provider)])
    findings = _enrich_findings(findings)
    selected_alias = _selected_model_alias(mode=effective_mode, model_id=model_id)
    return SetupReport(
        profile=effective_profile,
        mode=effective_mode,
        system_summary=_system_summary(),
        findings=findings,
        model_id=model_id,
        next_steps=_next_steps(
            profile=effective_profile,
            mode=effective_mode,
            model_id=selected_alias,
            hf_repo=hf_repo,
            hf_file=hf_file,
        ),
        repair_plan=_repair_plan(findings),
        plan_commands=_plan_commands(profile=effective_profile, mode=effective_mode, model_id=selected_alias, hf_repo=hf_repo, hf_file=hf_file),
        platform_hints=_platform_hints(profile=effective_profile),
        selected_model_alias=selected_alias,
    )


def write_local_llama_env(root: Path, *, model_id: str, overwrite: bool = False) -> Path:
    target = root / LOCAL_ENV_PATH
    if target.exists() and not overwrite:
        raise RuntimeError(f"{LOCAL_ENV_PATH} already exists; rerun with --overwrite-env to replace it")
    target.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(
        [
            "# Local UAA llama.cpp gateway template.",
            "# Gitignored local-dev file. Do not put provider API keys here.",
            "export UAA_LLAMA_CPP_GATEWAY_ENABLED=1",
            f"export UAA_LLAMA_CPP_GATEWAY_KEY={DEFAULT_UAA_GATEWAY_KEY}",
            f"export UAA_LLAMA_CPP_BASE_URL={DEFAULT_LLAMA_BASE_URL}",
            f"export UAA_LLAMA_CPP_MODEL_ID={model_id}",
            f"export UAA_LLAMA_CPP_API_KEY={DEFAULT_LLAMA_BACKEND_KEY}",
            "",
            "# Consolidated local model storage.",
            f'export HF_HOME="${{HF_HOME:-{DEFAULT_HF_HOME}}}"',
            f'export HF_HUB_CACHE="${{HF_HUB_CACHE:-{DEFAULT_HF_HUB_CACHE}}}"',
            f'export OLLAMA_MODELS="${{OLLAMA_MODELS:-{DEFAULT_OLLAMA_MODELS}}}"',
            f'export UAA_LLAMA_CPP_MODEL_CACHE_ROOT="${{UAA_LLAMA_CPP_MODEL_CACHE_ROOT:-{DEFAULT_LLAMA_CPP_MODEL_CACHE_ROOT}}}"',
            "",
            "# Optional active GGUF path for direct llama-server --model launchers.",
            '# export UAA_LLAMA_CPP_MODEL_PATH="$UAA_LLAMA_CPP_MODEL_CACHE_ROOT/path/to/model.gguf"',
            "",
        ]
    )
    target.write_text(content, encoding="utf-8")
    target.chmod(0o600)
    return target


def prepare_local_llama_env(root: Path, *, model_id: str, overwrite: bool = False) -> tuple[Path, SetupFinding]:
    target = root / LOCAL_ENV_PATH
    if target.exists() and not overwrite:
        checks = check_local_llama_env_file(root, LOCAL_ENV_PATH, model_id=model_id)
        summary = _env_summary_from_findings(checks)
        return target, SetupFinding(
            "local env template",
            "manual",
            f"Existing local env template kept; {summary}.",
            "Rerun with --overwrite-env only if you intend to replace the local template.",
        )
    written = write_local_llama_env(root, model_id=model_id, overwrite=overwrite)
    action = "Existing template replaced." if overwrite else "Template created."
    return written, SetupFinding(
        "local env template",
        "pass",
        f"{action} Safe local llama gateway env template is available.",
        f"Run: source {LOCAL_ENV_PATH}",
    )


def write_setup_report(root: Path, report_path: Path, report: SetupReport) -> Path:
    target = report_path if report_path.is_absolute() else root / report_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(serialize_report(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    target.chmod(0o600)
    return target


def check_local_llama_env_file(root: Path, path: Path, *, model_id: str) -> list[SetupFinding]:
    target = path if path.is_absolute() else root / path
    if not target.exists():
        return [
            SetupFinding(
                "env file",
                "manual",
                f"{_display_path(root, target)} does not exist.",
                f"Run uaa setup --profile local-llama --write-env to create {LOCAL_ENV_PATH}.",
            )
        ]
    values = _parse_env_file(target)
    checks = [
        _env_value_check(values, UAA_LLAMA_CPP_GATEWAY_ENV, expected="1", secret=False),
        _env_value_check(values, UAA_LLAMA_CPP_GATEWAY_KEY_ENV, expected=None, secret=True),
        _env_value_check(values, UAA_LLAMA_CPP_API_KEY_ENV, expected=None, secret=True),
        _env_value_check(values, UAA_LLAMA_CPP_BASE_URL_ENV, expected=DEFAULT_LLAMA_BASE_URL, secret=False, loopback=True),
        _env_value_check(values, UAA_LLAMA_CPP_MODEL_ID_ENV, expected=model_id, secret=False),
    ]
    return [
        SetupFinding(
            "env file",
            "pass" if all(check.status == "pass" for check in checks) else "manual",
            f"{_display_path(root, target)} parsed with {len(checks)} safe checks.",
            "No secret values were printed; review individual env check summaries below.",
        ),
        *checks,
    ]


def render_install_plan(plan: dict[str, Any]) -> str:
    lines = [
        "M167 scoped local-dev installer/downloader preview",
        f"Target: {plan['target']}",
        f"Milestone: {plan['milestone_ref']}",
        f"Preview hash: {plan['preview_hash']}",
        "",
        "Exact command that may run after approval:",
    ]
    for command in plan["commands"]:
        lines.append(f"- {_shell_preview(command)}")
    lines.extend(
        [
            "",
            "Authority boundary:",
            "- Downloads only the configured OpenWebUI Docker image for the local-dev OpenWebUI path.",
            "- Does not install Python, Node/npm dependencies, Homebrew packages, llama.cpp, providers, models, plugins, browser tooling, or credentials.",
            "- Does not start OpenWebUI, call UAA /v1, call providers/models, grant OpenWebUI tool/function authority, write memory, or mutate OpenWebUI internals.",
            "",
            "Consent:",
            f'- Type "{SETUP_INSTALL_CONFIRMATION}" to approve interactively.',
            "- Noninteractive --yes requires a matching preview-bound --approval-token.",
            "- Use --write-approval-token PATH after typed approval to create a single-use token without pulling the image.",
            "",
            "Receipt:",
            f"- A redacted local receipt will be written to {_safe_path_summary(plan['receipt_path'])}.",
            "",
            "Rollback:",
        ]
    )
    for step in plan["rollback_steps"]:
        lines.append(f"- {step}")
    return "\n".join(lines)


def write_setup_install_receipt(
    root: Path,
    plan: dict[str, Any],
    *,
    status: str,
    result_summary: str,
) -> Path:
    target = plan["receipt_path"]
    payload = {
        "schema": "uaa.setup_install_receipt.v1",
        "target": plan["target"],
        "milestone_ref": plan["milestone_ref"],
        "authority_boundary": plan["authority_boundary"],
        "action": plan["action"],
        "status": status,
        "result_summary": _safe_summary_text(result_summary),
        "receipt": _safe_path_summary(target),
        "receipt_scope_ref": plan["receipt_scope_ref"],
        "image_ref": plan["image_ref"],
        "preview_hash": plan["preview_hash"],
        "approval_mode": plan.get("approval_mode", "not-approved"),
        "approval_authority": plan.get("approval_authority", SETUP_APPROVAL_AUTHORITY_LABEL),
        "approval_decision_ref": plan.get("approval_decision_ref"),
        "exact_commands": [_shell_preview(command) for command in plan["commands"]],
        "side_effects_allowed": plan["side_effects_allowed"],
        "side_effects_denied": plan["side_effects_denied"],
        "rollback_steps": plan["rollback_steps"],
        "created_at": _utc_timestamp(),
        "redaction": "safe summary only; no credentials, provider keys, environment dump, raw prompts, raw responses, or raw logs",
    }
    _write_json_0600(
        target,
        payload,
        exclusive=(
            plan["receipt_scope_ref"] != "receipt-scope:default-generated"
            and not plan.get("receipt_reserved", False)
        ),
    )
    return target


def render_report(report: SetupReport, *, hf_repo: str, hf_file: str, explain: bool = False) -> str:
    lines = [
        "Ultimate AI Agent first-run setup doctor",
        f"Profile: {report.profile}",
        f"Mode: {report.mode}",
        f"Overall: {report.overall_status}",
        f"Selected model alias: {_report_model_alias(report)}",
        "",
        "System summary:",
    ]
    for key, value in report.system_summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "Checks:"])
    for finding in report.findings:
        lines.append(f"- [{finding.status}] {finding.name}: {finding.summary}")
        lines.append(f"  Action: {finding.action}")
        if explain:
            lines.append(f"  Why: {finding.why or 'This check keeps first-run readiness explicit and reviewable.'}")
            lines.append(
                "  Authority boundary: "
                f"{finding.authority_boundary or 'This diagnostic does not grant runtime, provider, tool, shell, browser, plugin, memory, or production authority.'}"
            )
    if report.env_template:
        lines.extend(["", f"Env template written: {report.env_template}"])
    if report.report_path:
        lines.extend(["", f"Redacted report written: {report.report_path}"])
    lines.extend(["", "Blocked next steps:"])
    if report.blocked_next_steps:
        for step in report.blocked_next_steps:
            lines.append(f"- {step}")
    else:
        lines.append("- None.")
    lines.extend(["", "Manual next steps:"])
    if report.manual_next_steps:
        for step in report.manual_next_steps:
            lines.append(f"- {step}")
    else:
        lines.append("- None.")
    lines.extend(["", "Ordered repair plan:"])
    if report.repair_plan:
        for index, step in enumerate(report.repair_plan, start=1):
            lines.append(f"{index}. {step}")
    else:
        lines.append("1. No blocked or manual repair steps were found for this profile.")
    if report.mode == "local-llama":
        lines.extend(["", "Recommended local llama.cpp command:"])
        lines.extend(
            [
                f"source {LOCAL_ENV_PATH}",
                "llama-server -lv 1 \\",
                "  --host 127.0.0.1 \\",
                "  --port 8080 \\",
                f"  --hf-repo {hf_repo} \\",
                f"  --hf-file {hf_file} \\",
                f'  --alias "${{UAA_LLAMA_CPP_MODEL_ID:-{_report_model_alias(report)}}}" \\',
                f'  --api-key "${{UAA_LLAMA_CPP_API_KEY:-{DEFAULT_LLAMA_BACKEND_KEY}}}"',
            ]
        )
    lines.extend(["", "Suggested run order:"])
    for step in report.next_steps:
        lines.append(f"- {step}")
    lines.extend(["", "Honest command preview:"])
    for command in report.plan_commands:
        lines.append(f"- {command}")
    lines.append("- Preview only; uaa setup did not run these commands.")
    if report.platform_hints:
        lines.extend(["", "Platform hints:"])
        for hint in report.platform_hints:
            lines.append(f"- {hint}")
    lines.extend(
        [
            "",
            "Boundary:",
            "- The setup doctor does not install packages, download models, collect provider credentials, or configure frontier-provider APIs.",
            "- Docker/OpenWebUI checks inspect local readiness only and never pull container images.",
            "- The only setup downloader path is explicit: uaa setup install --target openwebui may pull the configured OpenWebUI image after approval.",
            "- OpenWebUI model switching comes from OpenWebUI's model selector and the models exposed by UAA's /v1 gateway.",
            "- UAA currently exposes the configured local model ID for the M164 llama.cpp path; multi-provider UAA routing needs a later scoped milestone.",
        ]
    )
    return "\n".join(lines)


def render_plan(report: SetupReport) -> str:
    lines = [
        "Ultimate AI Agent setup command preview",
        f"Profile: {report.profile}",
        f"Overall: {report.overall_status}",
        "",
        "Ordered repair plan:",
    ]
    if report.repair_plan:
        for index, step in enumerate(report.repair_plan, start=1):
            lines.append(f"{index}. {step}")
    else:
        lines.append("1. No blocked or manual repair steps were found for this profile.")
    lines.extend(["", "Manual commands you may choose to run:"])
    for command in report.plan_commands:
        lines.append(f"- {command}")
    lines.extend(
        [
            "",
            "Boundary:",
            "- Preview only. uaa setup did not run commands, install packages, download models, pull images, start services, or collect credentials.",
            "- Image pulls are allowed only through explicit uaa setup install --target openwebui approval.",
        ]
    )
    return "\n".join(lines)


def serialize_report(report: SetupReport) -> dict[str, Any]:
    return {
        "profile": report.profile,
        "mode": report.mode,
        "overall_status": report.overall_status,
        "system_summary": report.system_summary,
        "findings": [asdict(finding) for finding in report.findings],
        "model_id": report.model_id,
        "selected_model_alias": _report_model_alias(report),
        "blocked_next_steps": report.blocked_next_steps,
        "manual_next_steps": report.manual_next_steps,
        "repair_plan": report.repair_plan,
        "plan_commands": report.plan_commands,
        "platform_hints": report.platform_hints,
        "next_steps": report.next_steps,
        "env_template": report.env_template,
        "report_path": report.report_path,
    }


def _effective_profile(*, mode: str, profile: str | None) -> SetupProfile:
    if profile in SETUP_PROFILES:
        return profile  # type: ignore[return-value]
    if mode == "smoke":
        return "openwebui-smoke"
    return "local-llama"


def _effective_mode(*, mode: str, profile: str) -> str:
    if profile == "openwebui-smoke":
        return "smoke"
    if profile == "local-llama":
        return "local-llama"
    return mode


def _profile_findings(root: Path, *, profile: str, docker_finding: SetupFinding) -> list[SetupFinding]:
    common = [_probe_python(root), _probe_uaa_shell_command(root)]
    if profile == "minimal":
        return [*common, _probe_backend_port()]
    if profile == "frontend-only":
        return [common[0], _probe_frontend_deps(root), common[1], _probe_backend_port(), _probe_frontend_port()]
    if profile == "openwebui-smoke":
        return [
            *common,
            docker_finding,
            _probe_backend_port(),
            _probe_openwebui_port(),
            _probe_openwebui_data_dir(root),
            _probe_openwebui_image(docker_finding),
        ]
    return [
        common[0],
        _probe_frontend_deps(root),
        common[1],
        docker_finding,
        _probe_backend_port(),
        _probe_frontend_port(),
        _probe_openwebui_port(),
        _probe_openwebui_data_dir(root),
        _probe_openwebui_image(docker_finding),
    ]


def _repair_plan(findings: list[SetupFinding]) -> list[str]:
    actionable = [
        finding
        for finding in findings
        if finding.status in {"blocked", "manual", "warn", "not-scoped"} and finding.action != "No action needed."
    ]
    actionable.sort(key=lambda finding: (_repair_rank(finding.name), finding.name))
    steps: list[str] = []
    for finding in actionable:
        step = f"[{finding.status}] {finding.name}: {finding.action}"
        if step not in steps:
            steps.append(step)
    return steps


def _repair_rank(name: str) -> int:
    ranks = {
        "python environment": 10,
        "frontend dependencies": 20,
        "uaa shell command": 25,
        "docker": 30,
        "env file": 35,
        "env: UAA_LLAMA_CPP_GATEWAY_ENABLED": 36,
        "env: UAA_LLAMA_CPP_GATEWAY_KEY": 37,
        "env: UAA_LLAMA_CPP_API_KEY": 38,
        "env: UAA_LLAMA_CPP_BASE_URL": 39,
        "env: UAA_LLAMA_CPP_MODEL_ID": 40,
        "local env template": 42,
        "local gateway env": 45,
        "selected model alias": 50,
        "llama-server": 60,
        "llama.cpp port": 70,
        "backend port": 80,
        "UAA local gateway": 90,
        "OpenWebUI image": 100,
        "OpenWebUI data directory": 105,
        "OpenWebUI port": 110,
    }
    return ranks.get(name, 500)


def _plan_commands(*, profile: str, mode: str, model_id: str, hf_repo: str, hf_file: str) -> list[str]:
    if profile == "minimal":
        return [
            'python3 -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"',
            "./scripts/dev/uaa doctor",
            "./scripts/dev/uaa start",
        ]
    if profile == "frontend-only":
        return [
            'python3 -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"',
            "cd apps/control-center && npm install",
            "./scripts/dev/uaa start",
        ]
    if profile == "openwebui-smoke" or mode == "smoke":
        return [
            'python3 -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"',
            "UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1 ./scripts/dev/uaa start",
            "./scripts/dev/uaa openwebui doctor",
            "./scripts/dev/uaa openwebui start",
        ]
    return [
        'python3 -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"',
        "cd apps/control-center && npm install",
        f"source {LOCAL_ENV_PATH}",
        f'llama-server -lv 1 --host 127.0.0.1 --port 8080 --hf-repo {hf_repo} --hf-file {hf_file} --alias "${{UAA_LLAMA_CPP_MODEL_ID:-{model_id}}}" --api-key "${{UAA_LLAMA_CPP_API_KEY:-{DEFAULT_LLAMA_BACKEND_KEY}}}"',
        "./scripts/dev/uaa start",
        "./scripts/dev/uaa openwebui doctor",
        "./scripts/dev/uaa openwebui start",
    ]


def _platform_hints(*, profile: str) -> list[str]:
    hints: list[str] = []
    if platform.system() == "Darwin":
        hints.append("macOS: Homebrew installs are commonly under /opt/homebrew/bin on Apple Silicon and /usr/local/bin on Intel.")
        if profile in {"openwebui-smoke", "local-llama"}:
            hints.append("macOS: Docker Desktop usually provides the Docker engine; open Docker Desktop manually if the engine is not ready.")
        if profile == "local-llama" and platform.machine() == "arm64":
            hints.append("Apple Silicon: use a llama.cpp build and GGUF compatible with arm64 local execution.")
    if profile in {"frontend-only", "local-llama"}:
        hints.append("Node/npm are only checked; setup does not install frontend dependencies.")
    if profile in {"openwebui-smoke", "local-llama"}:
        hints.append("Docker/OpenWebUI checks are readiness probes only; use uaa setup install --target openwebui for the explicit image pull.")
    return hints


def _system_summary() -> dict[str, str]:
    return {
        "os": platform.system() or "unknown",
        "architecture": platform.machine() or "unknown",
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }


def _probe_python(root: Path) -> SetupFinding:
    python_path = root / ".venv" / "bin" / "python"
    if not python_path.exists():
        return SetupFinding(
            "python environment",
            "blocked",
            "Repo virtual environment is missing.",
            'Run python3 -m venv .venv && .venv/bin/python -m pip install -e ".[dev]".',
        )
    result = _run_probe([str(python_path), "--version"], timeout_seconds=3.0)
    if result["returncode"] != 0:
        return SetupFinding(
            "python environment",
            "blocked",
            "Repo virtual environment exists but Python did not answer a version probe.",
            'Recreate .venv with python3 -m venv .venv && .venv/bin/python -m pip install -e ".[dev]".',
        )
    version_text = (result["stdout"] or result["stderr"]).strip() or "Python version detected"
    version_tuple = _parse_python_version(version_text)
    if version_tuple is not None and version_tuple[:2] < MIN_PYTHON:
        return SetupFinding(
            "python environment",
            "blocked",
            f"{version_text}; project requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer.",
            "Recreate .venv with Python 3.10 or newer.",
        )
    return SetupFinding(
        "python environment",
        "pass",
        f"Repo virtual environment is present ({version_text}).",
        "No action needed.",
    )


def _probe_frontend_deps(root: Path) -> SetupFinding:
    app_root = root / "apps" / "control-center"
    if not (app_root / "package.json").exists():
        return SetupFinding(
            "frontend dependencies",
            "blocked",
            "Control Center package.json is missing.",
            "Restore apps/control-center/package.json before running the frontend.",
        )
    if _resolve_command("npm") is None:
        return SetupFinding(
            "frontend dependencies",
            "blocked",
            "npm is not available on PATH.",
            "Install Node.js/npm externally, then rerun uaa setup.",
        )
    if app_root.joinpath("node_modules").exists():
        return SetupFinding(
            "frontend dependencies",
            "pass",
            "Control Center package.json, npm, and node_modules are present.",
            "No action needed.",
        )
    return SetupFinding(
        "frontend dependencies",
        "blocked",
        "Control Center dependencies are missing.",
        "Run cd apps/control-center && npm install.",
    )


def _probe_uaa_shell_command(root: Path) -> SetupFinding:
    wrapper = root / "scripts" / "dev" / "uaa"
    resolved = _resolve_command("uaa")
    if resolved:
        return SetupFinding("uaa shell command", "pass", f"uaa is available on PATH at {resolved}.", "No action needed.")
    if wrapper.exists():
        return SetupFinding(
            "uaa shell command",
            "manual",
            "uaa is not available on PATH, but the repo wrapper exists.",
            "Run ./scripts/dev/uaa install-shell-command or use ./scripts/dev/uaa from the repo.",
        )
    return SetupFinding(
        "uaa shell command",
        "blocked",
        "Neither uaa on PATH nor the repo wrapper was found.",
        "Restore scripts/dev/uaa before using the local launcher.",
    )


def _probe_uua_shell_command(root: Path) -> SetupFinding:
    return _probe_uaa_shell_command(root)


def _probe_docker() -> SetupFinding:
    docker = _resolve_command("docker")
    if docker is None:
        return SetupFinding(
            "docker",
            "blocked",
            "Docker CLI is missing; OpenWebUI container launch is unavailable.",
            "Install Docker Desktop or use OpenWebUI's direct-host path from docs/openwebui.",
        )
    result = _run_probe([str(docker), "info", "--format", "{{.ServerVersion}}"], timeout_seconds=3.0)
    if result["returncode"] == 0:
        version = (result["stdout"] or "").strip() or "version unknown"
        return SetupFinding("docker", "pass", f"Docker engine is reachable ({version}).", "No action needed.")
    detail = _last_probe_line(result) or "engine did not answer readiness probe"
    return SetupFinding(
        "docker",
        "blocked",
        f"Docker CLI exists but the engine is not ready: {detail}.",
        "Open Docker Desktop, finish setup, then rerun uaa setup.",
    )


def _probe_llama_server() -> SetupFinding:
    llama_server = _resolve_command("llama-server")
    if llama_server is None:
        return SetupFinding(
            "llama-server",
            "blocked",
            "llama-server is missing from PATH.",
            "Install llama.cpp externally, then rerun uaa setup.",
        )
    result = _run_probe([str(llama_server), "--version"], timeout_seconds=5.0)
    if result["returncode"] == 0:
        combined = "\n".join(part for part in [result["stdout"], result["stderr"]] if part).strip()
        first_line = (combined.splitlines() or ["version detected"])[0]
        return SetupFinding("llama-server", "pass", first_line[:120], "No action needed.")
    return SetupFinding("llama-server", "blocked", "llama-server did not answer version probe.", "Run llama-server --version.")


def _probe_llama_server_port() -> SetupFinding:
    base_url = os.environ.get(UAA_LLAMA_CPP_BASE_URL_ENV, DEFAULT_LLAMA_BASE_URL).strip() or DEFAULT_LLAMA_BASE_URL
    parsed = urllib_parse.urlparse(base_url)
    if not _is_loopback_url(base_url):
        return SetupFinding(
            "llama.cpp port",
            "blocked",
            f"{UAA_LLAMA_CPP_BASE_URL_ENV} is not a loopback HTTP URL.",
            f"Set {UAA_LLAMA_CPP_BASE_URL_ENV}={DEFAULT_LLAMA_BASE_URL}.",
        )
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if _is_port_open(parsed.hostname or "127.0.0.1", port):
        return SetupFinding(
            "llama.cpp port",
            "pass",
            f"llama-server loopback port is listening at {base_url}.",
            "No action needed if this is the intended llama-server process.",
        )
    return SetupFinding(
        "llama.cpp port",
        "manual",
        f"llama-server is not listening at {base_url}.",
        "Start llama-server in terminal 1 and leave it running; use the command printed below.",
    )


def _launcher_endpoint(
    host_env: str,
    port_env: str,
    default_host: str,
    default_port: int,
) -> tuple[str, int, str]:
    host = (os.environ.get(host_env, "").strip() or default_host).lower()
    if host not in LAUNCHER_HOSTS:
        raise ValueError(f"{host_env} must be 127.0.0.1 or localhost.")
    if host == "localhost":
        host = BACKEND_HOST
    raw_port = os.environ.get(port_env, "").strip()
    if raw_port:
        if not raw_port.isdigit():
            raise ValueError(f"{port_env} must be an integer port value.")
        port = int(raw_port)
        if not 1 <= port <= 65535:
            raise ValueError(f"{port_env} must be between 1 and 65535.")
    else:
        port = default_port
    return host, port, f"http://{host}:{port}"


def _probe_backend_port() -> SetupFinding:
    host, port, url = _launcher_endpoint(
        UAA_LAUNCHER_BACKEND_HOST_ENV,
        UAA_LAUNCHER_BACKEND_PORT_ENV,
        BACKEND_HOST,
        BACKEND_PORT,
    )
    if not _is_port_open(host, port):
        return SetupFinding(
            "backend port",
            "pass",
            f"Backend port is free at {url}.",
            "Run uaa start after blocked prerequisites are resolved.",
        )
    health_status = _url_status(f"{url}/health")
    if health_status == 200:
        return SetupFinding(
            "backend port",
            "pass",
            f"UAA likely running; /health answered HTTP 200 at {url}.",
            "Run uaa status to confirm it is the expected local UAA backend.",
        )
    root_status = _url_status(url)
    if root_status is not None:
        return SetupFinding(
            "backend port",
            "warn",
            f"HTTP server answered on backend port, but UAA /health returned {health_status or 'no status'}.",
            f"Confirm the process on {host}:{port} before running uaa start.",
        )
    return SetupFinding(
        "backend port",
        "warn",
        f"Socket is open on backend port, but no HTTP response was confirmed at {url}.",
        f"Confirm the process on {host}:{port} before running uaa start.",
    )


def _probe_frontend_port() -> SetupFinding:
    host, port, url = _launcher_endpoint(
        UAA_LAUNCHER_FRONTEND_HOST_ENV,
        UAA_LAUNCHER_FRONTEND_PORT_ENV,
        FRONTEND_HOST,
        FRONTEND_PORT,
    )
    if not _is_port_open(host, port):
        return SetupFinding(
            "frontend port",
            "pass",
            f"Control Center port is free at {url}.",
            "Run uaa start after blocked prerequisites are resolved.",
        )
    status = _url_status(url)
    if status is not None:
        return SetupFinding(
            "frontend port",
            "pass",
            f"HTTP server answered on Control Center port with HTTP {status}.",
            "Run uaa status to confirm it is the expected Vite server.",
        )
    return SetupFinding(
        "frontend port",
        "warn",
        f"Socket is open on Control Center port, but no HTTP response was confirmed at {url}.",
        f"Confirm the process on {host}:{port} before running uaa start.",
    )


def _probe_openwebui_port() -> SetupFinding:
    host, port, url = _launcher_endpoint(
        UAA_LAUNCHER_OPENWEBUI_HOST_ENV,
        UAA_LAUNCHER_OPENWEBUI_PORT_ENV,
        OPENWEBUI_HOST,
        OPENWEBUI_PORT,
    )
    if not _is_port_open(host, port):
        return SetupFinding(
            "OpenWebUI port",
            "pass",
            f"OpenWebUI is not listening; port is free at {url}.",
            "Run uaa openwebui start only after the local UAA gateway checks pass.",
        )
    status = _url_status(url)
    if status is None:
        return SetupFinding(
            "OpenWebUI port",
            "warn",
            f"Port {port} is listening, but OpenWebUI did not answer an HTTP status probe.",
            f"Confirm the process on {host}:{port} before starting OpenWebUI again.",
        )
    return SetupFinding(
        "OpenWebUI port",
        "pass",
        f"HTTP server answered on OpenWebUI port with HTTP {status} at {url}.",
        "No action needed if this is the intended local OpenWebUI shell.",
    )


def _probe_openwebui_data_dir(root: Path) -> SetupFinding:
    data_dir = root / ".uaa" / "dev" / "openwebui-data"
    if data_dir.exists():
        if data_dir.is_dir():
            return SetupFinding(
                "OpenWebUI data directory",
                "pass",
                "Prior local OpenWebUI data directory exists.",
                "No action needed unless you intentionally want to reset local OpenWebUI state.",
            )
        return SetupFinding(
            "OpenWebUI data directory",
            "blocked",
            ".uaa/dev/openwebui-data exists but is not a directory.",
            "Move or remove .uaa/dev/openwebui-data before starting OpenWebUI.",
        )
    parent = data_dir.parent
    if parent.exists() and not os.access(parent, os.W_OK):
        return SetupFinding(
            "OpenWebUI data directory",
            "blocked",
            ".uaa/dev exists but is not writable for the current user.",
            "Fix local permissions before starting OpenWebUI.",
        )
    return SetupFinding(
        "OpenWebUI data directory",
        "pass",
        "No prior OpenWebUI data directory was found; uaa openwebui start will create it when requested.",
        "No action needed for the doctor; setup does not create OpenWebUI state.",
    )


def _probe_openwebui_image(docker_finding: SetupFinding) -> SetupFinding:
    docker = _resolve_command("docker")
    if docker_finding.status != "pass" or docker is None:
        return SetupFinding(
            "OpenWebUI image",
            "manual",
            "OpenWebUI image was not inspected because Docker is not ready.",
            "Resolve Docker readiness first; this assistant will not pull images.",
        )
    result = _run_probe([str(docker), "image", "inspect", "--format", "{{.Id}}", OPENWEBUI_IMAGE], timeout_seconds=3.0)
    if result["returncode"] == 0:
        return SetupFinding(
            "OpenWebUI image",
            "pass",
            f"OpenWebUI container image is present locally ({OPENWEBUI_IMAGE}).",
            "No action needed.",
        )
    return SetupFinding(
        "OpenWebUI image",
        "manual",
        f"OpenWebUI container image is not present locally ({OPENWEBUI_IMAGE}).",
        "Run uaa setup install --target openwebui when you are ready to approve the scoped image pull.",
    )


def _probe_smoke_gateway_env() -> SetupFinding:
    if _is_truthy(os.environ.get(UAA_OPENWEBUI_TEST_GATEWAY_ENV, "")):
        return SetupFinding(
            "local gateway env",
            "pass",
            f"{UAA_OPENWEBUI_TEST_GATEWAY_ENV}=1 is exported for the deterministic smoke gateway.",
            "No action needed.",
        )
    return SetupFinding(
        "local gateway env",
        "manual",
        f"{UAA_OPENWEBUI_TEST_GATEWAY_ENV} is not enabled for smoke mode.",
        f"Start the backend with {UAA_OPENWEBUI_TEST_GATEWAY_ENV}=1 uaa start.",
    )


def _probe_local_llama_gateway_env(model_id: str) -> SetupFinding:
    base_url = os.environ.get(UAA_LLAMA_CPP_BASE_URL_ENV, DEFAULT_LLAMA_BASE_URL).strip() or DEFAULT_LLAMA_BASE_URL
    env_model_id = os.environ.get(UAA_LLAMA_CPP_MODEL_ID_ENV, "").strip()
    missing = []
    if not _is_truthy(os.environ.get(UAA_LLAMA_CPP_GATEWAY_ENV, "")):
        missing.append(UAA_LLAMA_CPP_GATEWAY_ENV)
    if not os.environ.get(UAA_LLAMA_CPP_GATEWAY_KEY_ENV, "").strip():
        missing.append(UAA_LLAMA_CPP_GATEWAY_KEY_ENV)
    if not os.environ.get(UAA_LLAMA_CPP_API_KEY_ENV, "").strip():
        missing.append(UAA_LLAMA_CPP_API_KEY_ENV)
    if not env_model_id:
        missing.append(UAA_LLAMA_CPP_MODEL_ID_ENV)
    if not _is_loopback_url(base_url):
        return SetupFinding(
            "local gateway env",
            "blocked",
            f"{UAA_LLAMA_CPP_BASE_URL_ENV} is set but is not a loopback HTTP URL.",
            f"Set {UAA_LLAMA_CPP_BASE_URL_ENV}={DEFAULT_LLAMA_BASE_URL}.",
        )
    selected = env_model_id or model_id
    if missing:
        return SetupFinding(
            "local gateway env",
            "manual",
            f"Local llama.cpp gateway env is incomplete; selected alias would be {selected}; missing {', '.join(missing)}.",
            f"Run uaa setup --profile local-llama --write-env, then source {LOCAL_ENV_PATH}.",
        )
    return SetupFinding(
        "local gateway env",
        "pass",
        f"Local llama.cpp gateway env is complete; selected alias is {selected}; base URL is {base_url}.",
        "No action needed.",
    )


def _probe_model_alias(*, mode: str, model_id: str) -> SetupFinding:
    if mode == "smoke":
        return SetupFinding(
            "selected model alias",
            "pass",
            f"OpenWebUI smoke mode selects {OPENWEBUI_SMOKE_MODEL_ID}.",
            "Use OpenWebUI's model selector only for models exposed by UAA's local /v1 gateway.",
        )
    if mode == "frontier":
        return SetupFinding(
            "selected model alias",
            "not-scoped",
            "Frontier provider aliases are not selected by UAA setup.",
            "Use a scoped milestone before adding governed frontier model selection.",
        )
    env_model_id = os.environ.get(UAA_LLAMA_CPP_MODEL_ID_ENV, "").strip()
    if env_model_id and env_model_id != model_id:
        return SetupFinding(
            "selected model alias",
            "warn",
            f"Setup selected {model_id}, but current env selects {env_model_id}.",
            f"Export {UAA_LLAMA_CPP_MODEL_ID_ENV}={model_id} or rerun setup with --model-id {env_model_id}.",
        )
    return SetupFinding(
        "selected model alias",
        "pass",
        f"Setup selected {model_id}.",
        "Use the same alias in llama-server --alias, UAA_LLAMA_CPP_MODEL_ID, and OpenWebUI.",
    )


def _selected_model_alias(*, mode: str, model_id: str) -> str:
    if mode == "smoke":
        return OPENWEBUI_SMOKE_MODEL_ID
    if mode == "local-llama":
        return os.environ.get(UAA_LLAMA_CPP_MODEL_ID_ENV, "").strip() or model_id
    return model_id


def _report_model_alias(report: SetupReport) -> str:
    if report.selected_model_alias:
        return report.selected_model_alias
    if report.mode == "smoke":
        return OPENWEBUI_SMOKE_MODEL_ID
    return report.model_id


def _launcher_owns_backend(root: Path, url: str) -> bool:
    pid_file = root / ".uaa" / "dev" / "pids" / "backend.pid"
    metadata_file = root / ".uaa" / "dev" / "backend.json"
    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, UnicodeDecodeError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, OverflowError):
        return False
    except PermissionError:
        pass
    try:
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(metadata, dict):
        return False
    parsed = urllib_parse.urlsplit(url)
    expected_command = [
        str(root / ".venv" / "bin" / "python"),
        "-m",
        "uvicorn",
        "ultimate_ai_agent.api.app:app",
        "--host",
        parsed.hostname or BACKEND_HOST,
        "--port",
        str(parsed.port or BACKEND_PORT),
    ]
    return (
        metadata.get("name") == "backend"
        and metadata.get("pid") == pid
        and metadata.get("command") == expected_command
        and metadata.get("cwd") == str(root)
        and metadata.get("url") == url
    )


def _probe_uaa_gateway_status(root: Path, *, mode: str) -> SetupFinding:
    if mode == "frontier":
        return SetupFinding(
            "UAA local gateway",
            "not-scoped",
            "Frontier provider routing is not exposed through setup.",
            "Create a scoped milestone before adding governed frontier provider gateway checks.",
        )
    host, port, url = _launcher_endpoint(
        UAA_LAUNCHER_BACKEND_HOST_ENV,
        UAA_LAUNCHER_BACKEND_PORT_ENV,
        BACKEND_HOST,
        BACKEND_PORT,
    )
    if not _is_port_open(host, port):
        return SetupFinding(
            "UAA local gateway",
            "manual",
            "UAA backend is not running, so /v1/models was not checked.",
            "Run uaa start after prerequisites and local gateway env are ready.",
        )
    gateway_key = DEFAULT_UAA_GATEWAY_KEY if mode == "local-llama" else "uaa-local-test"
    if mode == "local-llama":
        gateway_key = os.environ.get(UAA_LLAMA_CPP_GATEWAY_KEY_ENV, "").strip()
    if not gateway_key:
        return SetupFinding(
            "UAA local gateway",
            "manual",
            f"{UAA_LLAMA_CPP_GATEWAY_KEY_ENV} is not exported, so /v1/models was not checked.",
            f"Source {LOCAL_ENV_PATH} before running uaa start.",
        )
    if not _launcher_owns_backend(root, url):
        return SetupFinding(
            "UAA local gateway",
            "manual",
            "UAA backend ownership is unproven, so the configured local bearer was not sent.",
            "Run uaa status and restart the backend with the requested endpoint before retrying setup.",
        )
    status = _url_status(
        f"{url}/v1/models",
        headers={"Authorization": f"Bearer {gateway_key}"},
    )
    if status == 200:
        return SetupFinding("UAA local gateway", "pass", "UAA /v1/models accepted the configured local bearer.", "No action needed.")
    if status == 401:
        return SetupFinding(
            "UAA local gateway",
            "blocked",
            "UAA /v1/models rejected the configured local bearer.",
            "Restart the backend with the same local gateway env that OpenWebUI will use.",
        )
    if status == 403:
        env_name = UAA_LLAMA_CPP_GATEWAY_ENV if mode == "local-llama" else UAA_OPENWEBUI_TEST_GATEWAY_ENV
        return SetupFinding(
            "UAA local gateway",
            "manual",
            "UAA /v1/models is reachable but the selected local gateway is disabled.",
            f"Restart the backend with {env_name}=1.",
        )
    if status is None:
        return SetupFinding(
            "UAA local gateway",
            "manual",
            "UAA backend port is open, but /v1/models did not answer.",
            "Run uaa status and inspect backend logs before starting OpenWebUI.",
        )
    return SetupFinding(
        "UAA local gateway",
        "warn",
        f"UAA /v1/models returned HTTP {status}.",
        "Run uaa openwebui doctor for the focused gateway check.",
    )


def _frontier_findings(provider: str | None) -> list[SetupFinding]:
    provider_name = provider or "frontier provider"
    return [
        SetupFinding(
            "frontier provider setup",
            "not-scoped",
            f"{provider_name} API credential setup is not implemented in UAA's governed setup path.",
            "Use OpenWebUI's own provider settings outside UAA governance, or add a scoped UAA milestone for provider credentials.",
        ),
        SetupFinding(
            "provider authority",
            "not-scoped",
            "Provider/model output is not UAA production authority.",
            "Add exact policy, approval, redaction, audit, and rollback gates before enabling governed provider routing.",
        ),
    ]


def _next_steps(*, profile: str, mode: str, model_id: str, hf_repo: str, hf_file: str) -> list[str]:
    if profile == "minimal":
        return [
            "Resolve blocked Python or launcher checks first.",
            "Run: uaa doctor",
            "Run: uaa start",
        ]
    if profile == "frontend-only":
        frontend_url = _launcher_endpoint(
            UAA_LAUNCHER_FRONTEND_HOST_ENV,
            UAA_LAUNCHER_FRONTEND_PORT_ENV,
            FRONTEND_HOST,
            FRONTEND_PORT,
        )[2]
        return [
            "Resolve Python and Control Center dependency checks first.",
            "Run: uaa start",
            f"Open {frontend_url}.",
        ]
    if mode == "smoke":
        openwebui_url = _launcher_endpoint(
            UAA_LAUNCHER_OPENWEBUI_HOST_ENV,
            UAA_LAUNCHER_OPENWEBUI_PORT_ENV,
            OPENWEBUI_HOST,
            OPENWEBUI_PORT,
        )[2]
        return [
            "UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1 uaa start",
            "uaa openwebui doctor",
            "uaa openwebui start",
            f"Open {openwebui_url} and select uaa-safe-local.",
        ]
    if mode == "frontier":
        return [
            "Do not put frontier provider API keys in UAA setup files.",
            "Use OpenWebUI's own provider configuration only if you accept that it is outside UAA-governed routing.",
            "Create a scoped milestone before adding governed provider setup to UAA.",
        ]
    openwebui_url = _launcher_endpoint(
        UAA_LAUNCHER_OPENWEBUI_HOST_ENV,
        UAA_LAUNCHER_OPENWEBUI_PORT_ENV,
        OPENWEBUI_HOST,
        OPENWEBUI_PORT,
    )[2]
    return [
        f"Source {LOCAL_ENV_PATH} so consolidated model cache paths are active.",
        f"Start llama-server with --hf-repo {hf_repo}, --hf-file {hf_file}, and --alias {model_id}.",
        "Run: uaa start",
        "Run: uaa openwebui doctor",
        "Run: uaa openwebui start",
        f"Open {openwebui_url} and select {model_id}.",
    ]


def _run_probe(command: list[str], *, timeout_seconds: float) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"returncode": 1, "stdout": "", "stderr": exc.__class__.__name__}
    return {
        "returncode": result.returncode,
        "stdout": (result.stdout or "")[:4000],
        "stderr": (result.stderr or "")[:1000],
    }


def _run_install_command(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=DOCKER_PULL_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": 1, "summary": "docker pull timed out before completion"}
    except OSError as exc:
        return {"returncode": 1, "summary": f"docker pull could not start: {exc.__class__.__name__}"}
    summary = "completed" if result.returncode == 0 else _safe_process_summary(result)
    return {"returncode": result.returncode, "summary": summary}


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _env_value_check(
    values: dict[str, str],
    key: str,
    *,
    expected: str | None,
    secret: bool,
    loopback: bool = False,
) -> SetupFinding:
    name = f"env: {key}"
    if key not in values or not values[key].strip():
        return SetupFinding(name, "manual", f"{key} is missing.", f"Add {key} to {LOCAL_ENV_PATH}.")
    value = values[key].strip()
    if loopback and not _is_loopback_url(value):
        return SetupFinding(name, "blocked", f"{key} is present but is not a loopback HTTP URL.", f"Set {key}={DEFAULT_LLAMA_BASE_URL}.")
    if expected is not None and value != expected:
        if secret:
            return SetupFinding(name, "pass", f"{key} is present; value is intentionally redacted.", "No action needed.")
        return SetupFinding(name, "manual", f"{key} differs from expected safe value {expected}.", f"Set {key}={expected}.")
    if secret:
        return SetupFinding(name, "pass", f"{key} is present; value is intentionally redacted.", "No action needed.")
    return SetupFinding(name, "pass", f"{key} matches expected safe value.", "No action needed.")


def _env_summary_from_findings(findings: list[SetupFinding]) -> str:
    statuses: dict[str, int] = {}
    for finding in findings:
        statuses[finding.status] = statuses.get(finding.status, 0) + 1
    parts = [f"{count} {status}" for status, count in sorted(statuses.items())]
    return "safe env comparison found " + ", ".join(parts)


def _openwebui_install_plan(root: Path) -> dict[str, Any]:
    command = ["docker", "pull", OPENWEBUI_IMAGE]
    plan = {
        "target": "openwebui",
        "milestone_ref": SETUP_INSTALL_MILESTONE_REF,
        "action": "docker-image-pull",
        "image_ref": OPENWEBUI_IMAGE,
        "commands": [command],
        "approval_mode": "not-approved",
        "approval_token_path": None,
        "write_approval_token_path": None,
        "authority_boundary": (
            "OpenWebUI local-dev image acquisition only; no broad package install, "
            "model download, provider setup, credential collection, service start, "
            "OpenWebUI admin mutation, or runtime authority."
        ),
        "side_effects_allowed": [
            "Docker may download and store the configured OpenWebUI image in the local Docker image cache.",
            "A redacted local receipt may be written under .uaa/dev/setup-install-receipts by default, or to --receipt.",
        ],
        "side_effects_denied": [
            "Python install",
            "Node/npm install",
            "Homebrew install",
            "llama.cpp install",
            "model download",
            "provider credential collection",
            "OpenWebUI plugin/admin mutation",
            "service launch",
            "browser automation",
            "tool/function authority",
            "memory write",
        ],
        "receipt_path": _install_receipt_path(root, target="openwebui"),
        "receipt_scope_ref": _install_receipt_scope_ref(None),
        "rollback_steps": [
            "./scripts/dev/uaa openwebui stop",
            f"Optional image rollback after review: docker image rm {OPENWEBUI_IMAGE}",
            "OpenWebUI data reset requires explicit canonical-path review before removing .uaa/dev/openwebui-data.",
            f"Receipt cleanup should remove only receipt files under {SETUP_INSTALL_RECEIPT_DIR}.",
        ],
    }
    plan["preview_hash"] = _install_preview_hash(plan)
    return plan


def _attach_install_approval_paths(root: Path, plan: dict[str, Any], args: argparse.Namespace) -> None:
    approval_token = getattr(args, "approval_token", None)
    if approval_token:
        plan["approval_token_path"] = _validate_bootstrap_existing_file_path(
            root,
            Path(str(approval_token)).expanduser(),
            option_name="--approval-token",
        )
    write_approval_token = getattr(args, "write_approval_token", None)
    if write_approval_token:
        plan["write_approval_token_path"] = _validate_bootstrap_receipt_path(
            root,
            Path(str(write_approval_token)).expanduser(),
        )
    receipt_path = getattr(args, "receipt", None)
    if receipt_path:
        plan["receipt_path"] = _validate_bootstrap_receipt_path(
            root,
            Path(str(receipt_path)).expanduser(),
        )
        for token_option, token_path in (
            ("--approval-token", plan.get("approval_token_path")),
            ("--write-approval-token", plan.get("write_approval_token_path")),
        ):
            if token_path is not None and token_path == plan["receipt_path"]:
                raise ValueError(f"--receipt must not alias {token_option}")
        plan["receipt_scope_ref"] = _install_receipt_scope_ref(plan["receipt_path"])
        plan["rollback_steps"][-1] = (
            "Receipt cleanup should remove only the exact reviewed receipt at "
            f"{_safe_path_summary(plan['receipt_path'])}."
        )
        plan["preview_hash"] = _install_preview_hash(plan)


def _reserve_custom_install_receipt(root: Path, plan: dict[str, Any]) -> None:
    if plan["receipt_scope_ref"] == "receipt-scope:default-generated":
        return
    write_setup_install_receipt(
        root,
        plan,
        status="reserved",
        result_summary="Custom receipt destination reserved; no install command has run.",
    )
    plan["receipt_reserved"] = True


def _install_preview_hash(plan: dict[str, Any]) -> str:
    payload = {
        "schema": "uaa.setup_install_preview.v1",
        "milestone_ref": plan["milestone_ref"],
        "target": plan["target"],
        "action": plan["action"],
        "image_ref": plan["image_ref"],
        "commands": [_shell_preview(command) for command in plan["commands"]],
        "receipt_scope_ref": plan["receipt_scope_ref"],
        "rollback_steps": plan["rollback_steps"],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _install_receipt_scope_ref(receipt_path: Path | None) -> str:
    if receipt_path is None:
        return "receipt-scope:default-generated"
    digest = hashlib.sha256(
        str(receipt_path.resolve(strict=False)).encode("utf-8")
    ).hexdigest()
    return f"receipt-path-sha256:{digest}"


def write_setup_install_approval_token(
    root: Path,
    plan: dict[str, Any],
    token_path: Path,
    *,
    ttl_seconds: int = SETUP_INSTALL_APPROVAL_TOKEN_TTL_SECONDS,
) -> Path:
    now = int(time.time())
    token_path = _validate_bootstrap_receipt_path(root, token_path)
    payload = {
        "schema": SETUP_INSTALL_APPROVAL_TOKEN_SCHEMA,
        "milestone_ref": plan["milestone_ref"],
        "target": plan["target"],
        "action": plan["action"],
        "image_ref": plan["image_ref"],
        "preview_hash": plan["preview_hash"],
        "expires_at_epoch": now + ttl_seconds,
        "created_at": _utc_timestamp(),
        "used_at": None,
        "redaction": "safe approval metadata only; no credentials, env values, usernames, raw logs, prompts, or provider payloads",
    }
    _write_json_0600(token_path, payload, exclusive=True)
    return token_path


def _consume_setup_install_approval_token(root: Path, plan: dict[str, Any], token_path: Path) -> None:
    expected = {
        "schema": SETUP_INSTALL_APPROVAL_TOKEN_SCHEMA,
        "milestone_ref": plan["milestone_ref"],
        "target": plan["target"],
        "action": plan["action"],
        "image_ref": plan["image_ref"],
    }
    _consume_setup_approval_token(
        root,
        plan,
        token_path,
        schema=SETUP_INSTALL_APPROVAL_TOKEN_SCHEMA,
        expected=expected,
    )


def _read_install_approval() -> bool:
    print(f'Type "{SETUP_INSTALL_CONFIRMATION}" to approve this scoped image pull: ', end="")
    try:
        return sys.stdin.readline().strip() == SETUP_INSTALL_CONFIRMATION
    except OSError:
        return False


def _install_receipt_path(root: Path, *, target: str) -> Path:
    return root / SETUP_INSTALL_RECEIPT_DIR / f"{target}-{_utc_timestamp()}.json"


def _utc_timestamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _shell_preview(command: list[str]) -> str:
    return " ".join(_quote_shell_arg(part) for part in command)


def _quote_shell_arg(value: str) -> str:
    if value and all(character.isalnum() or character in "-_./:=@" for character in value):
        return value
    return "'" + value.replace("'", "'\\''") + "'"


def _safe_process_summary(result: subprocess.CompletedProcess[str]) -> str:
    return f"process exited with code {result.returncode}; external output omitted"


def _safe_summary_text(value: str) -> str:
    text = str(value or "")
    patterns = [
        re.compile(
            r"(?i)(api[_-]?key|client[_-]?secret|auth[_-]?token|secret|password|passwd|credential|cookie|authorization)\s*[:=]\s*['\"]?[^'\"\s,;]+"
        ),
        re.compile(r"(?i)(bearer)\s+[A-Za-z0-9._~+/=-]{8,}"),
    ]
    safe = text
    for pattern in patterns:
        safe = pattern.sub(lambda match: f"{match.group(1)}=<redacted>", safe)
    return safe[:500]


def _write_json_0600(
    target: Path,
    payload: dict[str, Any],
    *,
    exclusive: bool = False,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    flags = os.O_WRONLY | os.O_CREAT
    flags |= os.O_EXCL if exclusive else os.O_TRUNC
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(target, flags, 0o600)
    except FileExistsError as exc:
        raise ValueError("refusing to overwrite an existing setup evidence file") from exc
    except OSError as exc:
        if target.is_symlink():
            raise ValueError("refusing to follow a setup evidence symlink") from exc
        raise
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(data)


def _display_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _safe_path_summary(path: Path) -> str:
    resolved = path.resolve(strict=False)
    home = _bootstrap_user_home().resolve(strict=False)
    try:
        relative = resolved.relative_to(home)
    except ValueError:
        return "<user-scope-path>"
    if not relative.parts:
        return "~"
    return "~/" + str(relative)


def _redacted_command_preview(command: list[str]) -> str:
    redacted: list[str] = []
    home = _bootstrap_user_home().resolve(strict=False)
    for part in command:
        replacement = part
        part_path = Path(part)
        if part_path.name == BOOTSTRAP_INSTALLER_NAME:
            replacement = f"<verified-temp>/{BOOTSTRAP_INSTALLER_NAME}"
        elif _looks_like_path(part):
            try:
                resolved = part_path.resolve(strict=False)
                relative = resolved.relative_to(home)
                replacement = "~" if not relative.parts else "~/" + str(relative)
            except (OSError, ValueError):
                replacement = part
        redacted.append(replacement)
    return _shell_preview(redacted)


def _enrich_findings(findings: list[SetupFinding]) -> list[SetupFinding]:
    return [
        SetupFinding(
            name=finding.name,
            status=finding.status,
            summary=finding.summary,
            action=finding.action,
            why=finding.why or _why_for_finding(finding.name),
            authority_boundary=finding.authority_boundary or _authority_boundary_for_finding(finding.name),
        )
        for finding in findings
    ]


def _why_for_finding(name: str) -> str:
    if name.startswith("env:") or name in {"local gateway env", "env file", "local env template"}:
        return "Local gateway env must be explicit and reviewable so OpenWebUI and UAA use the same loopback-only model path."
    explanations = {
        "python environment": "The backend and test tooling run from the repo virtual environment.",
        "frontend dependencies": "The Control Center dev server needs local Node dependencies before it can start.",
        "uaa shell command": "The launcher wrapper gives first-run users a stable command entry point.",
        "docker": "The local OpenWebUI shell uses Docker when launched through the dev launcher.",
        "backend port": "The backend port check prevents confusing duplicate services or hidden port conflicts.",
        "frontend port": "The frontend port check prevents duplicate Vite servers and makes local UI readiness clear.",
        "OpenWebUI port": "The OpenWebUI port check distinguishes normal first-run free state from an existing local shell or conflict.",
        "OpenWebUI image": "The image check tells you whether Docker already has the image without pulling it.",
        "OpenWebUI data directory": "The data-dir check reports prior local OpenWebUI state without creating or mutating it.",
        "selected model alias": "The selected alias must match llama-server, UAA, and OpenWebUI so requests do not drift.",
        "UAA local gateway": "The gateway check verifies that the already-running backend exposes the intended local /v1 route.",
        "llama-server": "The local llama.cpp path needs llama-server available before UAA can forward requests.",
        "llama.cpp port": "The llama.cpp port check verifies that the loopback backend model server is actually listening.",
        "frontier provider setup": "Frontier provider credentials need a scoped milestone before UAA can govern them.",
        "provider authority": "Provider output is not production authority without policy, approval, audit, and rollback controls.",
    }
    return explanations.get(name, "This check keeps first-run readiness explicit and reviewable.")


def _authority_boundary_for_finding(name: str) -> str:
    if name.startswith("env:") or name in {"local gateway env", "env file", "local env template"}:
        return "Env checks never print secret values and do not collect provider credentials or enable provider authority."
    if name in {"docker", "OpenWebUI image", "OpenWebUI port", "OpenWebUI data directory"}:
        return "Docker/OpenWebUI checks do not pull images, start containers, mutate OpenWebUI internals, or grant model/tool authority."
    if name in {"llama-server", "llama.cpp port", "UAA local gateway", "selected model alias"}:
        return "Local model checks stay loopback-only and do not download models, call providers, stream tools, write memory, or treat model output as authority."
    return "This diagnostic does not grant runtime, provider, tool, shell, browser, plugin, memory, or production authority."


def _actions_for_status(findings: list[SetupFinding], status: SetupStatus) -> list[str]:
    actions: list[str] = []
    for finding in findings:
        if finding.status == status and finding.action not in actions:
            actions.append(f"[{finding.name}] {finding.action}")
    return actions


def _last_probe_line(result: dict[str, Any]) -> str:
    combined = "\n".join(part for part in [result.get("stderr", ""), result.get("stdout", "")] if part).strip()
    return (combined.splitlines() or [""])[-1][:160]


def _resolve_command(command: str) -> Path | None:
    for directory in DEVELOPER_TOOL_PATHS:
        candidate = directory / command
        if _is_executable_file(candidate):
            return candidate
    resolved = shutil.which(command)
    return Path(resolved) if resolved else None


def _is_executable_file(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _is_port_open(host: str, port: int, *, timeout_seconds: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def _url_status(url: str, *, headers: dict[str, str] | None = None, timeout_seconds: float = 1.0) -> int | None:
    if not _is_loopback_url(url):
        return None
    request = urllib_request.Request(url, headers=headers or {})
    try:
        with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
            return int(response.status)
    except urllib_error.HTTPError as exc:
        return int(exc.code)
    except (OSError, urllib_error.URLError, TimeoutError):
        return None


def _is_loopback_url(url: str) -> bool:
    parsed = urllib_parse.urlparse(url)
    return parsed.scheme == "http" and (parsed.hostname or "").lower() in LOOPBACK_HOSTS and parsed.port is not None


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_python_version(version_text: str) -> tuple[int, int, int] | None:
    parts = version_text.strip().split()
    if len(parts) < 2 or parts[0] != "Python":
        return None
    number_parts = parts[1].split(".")
    if len(number_parts) < 2:
        return None
    try:
        major = int(number_parts[0])
        minor = int(number_parts[1])
        patch = int(number_parts[2]) if len(number_parts) > 2 else 0
    except ValueError:
        return None
    return major, minor, patch


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="uaa_setup")
    add_setup_parser(parser.add_subparsers(dest="command"))
    parsed = parser.parse_args()
    if parsed.command != "setup":
        parser.print_help()
        raise SystemExit(0)
    raise SystemExit(command_setup(Path.cwd(), parsed))
