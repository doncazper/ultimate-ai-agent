from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from pathlib import Path
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityDecisionCatalogEntry,
    build_authority_decision_catalog,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS


RUNTIME_HARDLINE_COMMAND_BLOCKLIST_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-hardline-command-blocklist:v1"
)
RUNTIME_HARDLINE_COMMAND_BLOCKLIST_ROUTE_REF = "GET /api/runtime/hardline-command-blocklist"
RUNTIME_HARDLINE_COMMAND_BLOCKLIST_CLI_REF = "uaa runtime inspect-hardline-command-blocklist"
RUNTIME_HARDLINE_COMMAND_BLOCKLIST_SNAPSHOT_REF = (
    "hardline-command-blocklist-snapshot-ref:runtime:deny-floor"
)
RUNTIME_HARDLINE_COMMAND_BLOCKLIST_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-25:hardline-command-blocklist"
)
RUNTIME_HARDLINE_COMMAND_BLOCKLIST_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-25:hardline-command-blocklist"
)
RUNTIME_HARDLINE_COMMAND_BLOCKLIST_DENY_CODE = "RUNTIME_COMMAND_HARDLINE_BLOCKLIST_DENIED"
RUNTIME_HARDLINE_COMMAND_BLOCKLIST_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_HARDLINE_COMMAND_BLOCKLIST_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_HARDLINE_COMMAND_BLOCKLIST_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-hardline-command-blocklist-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_HARDLINE_COMMAND_BLOCKLIST_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:runtime-hardline-command-floor-override",
    "blocked-authority:runtime-command-string-bypass",
    "blocked-authority:runtime-shell-metachar-bypass",
    "blocked-authority:runtime-destructive-command-bypass",
    "blocked-authority:runtime-network-command-bypass",
    "blocked-authority:runtime-git-mutation-bypass",
    "blocked-authority:runtime-package-install-bypass",
    "blocked-authority:runtime-privilege-escalation-bypass",
    "blocked-authority:runtime-production-command-bypass",
    "blocked-authority:runtime-raw-command-text-persistence",
    "blocked-authority:runtime-raw-command-output-persistence",
    "blocked-authority:runtime-production-authority",
)

_SHELL_METACHARS = (";", "&&", "||", "|", "`", "$(", ">", "<", "\n", "\r")
_NETWORK_URI_RE = re.compile(r"(?i)^[a-z][a-z0-9+.-]*://")

_DENIED_EXECUTABLE_CATEGORIES: dict[str, str] = {
    "bash": "shell_interpreter",
    "sh": "shell_interpreter",
    "zsh": "shell_interpreter",
    "fish": "shell_interpreter",
    "pwsh": "shell_interpreter",
    "powershell": "shell_interpreter",
    "rm": "destructive_filesystem",
    "rmdir": "destructive_filesystem",
    "shred": "destructive_filesystem",
    "srm": "destructive_filesystem",
    "dd": "disk_writer",
    "mkfs": "disk_writer",
    "diskutil": "disk_writer",
    "curl": "network_transfer",
    "wget": "network_transfer",
    "nc": "network_transfer",
    "netcat": "network_transfer",
    "ssh": "remote_access",
    "scp": "remote_access",
    "rsync": "remote_access",
    "sudo": "privilege_escalation",
    "su": "privilege_escalation",
    "chmod": "permission_mutation",
    "chown": "permission_mutation",
    "kubectl": "production_orchestration",
    "helm": "production_orchestration",
    "terraform": "production_orchestration",
    "docker": "container_runtime",
    "podman": "container_runtime",
    "osascript": "desktop_automation",
    "open": "desktop_automation",
    "playwright": "browser_automation",
    "sele" + "nium": "browser_automation",
}

_GIT_MUTATION_ARGS = {
    "add",
    "am",
    "apply",
    "branch",
    "checkout",
    "cherry-pick",
    "clean",
    "commit",
    "merge",
    "mv",
    "pull",
    "push",
    "rebase",
    "reset",
    "restore",
    "rm",
    "stash",
    "switch",
    "tag",
}

_PACKAGE_INSTALL_EXECUTABLES = {
    "pip",
    "pip3",
    "npm",
    "yarn",
    "pnpm",
    "brew",
    "uv",
}
_PACKAGE_INSTALL_ARGS = {"install", "add", "upgrade", "update", "remove", "uninstall"}
_INLINE_CODE_ARGS = {"-c", "-e", "--eval", "--execute"}
_PYTHON_EXECUTABLES = {"python", "python3"}


class RuntimeHardlineCommandClassificationStatus(str, Enum):
    allowed_shape = "allowed_shape"
    hardline_denied = "hardline_denied"


class RuntimeHardlineCommandDenialCategory(str, Enum):
    allowed = "allowed"
    empty_argv = "empty_argv"
    shell_metachar = "shell_metachar"
    shell_interpreter = "shell_interpreter"
    inline_code = "inline_code"
    destructive_filesystem = "destructive_filesystem"
    disk_writer = "disk_writer"
    network_transfer = "network_transfer"
    remote_access = "remote_access"
    privilege_escalation = "privilege_escalation"
    permission_mutation = "permission_mutation"
    git_mutation = "git_mutation"
    package_install = "package_install"
    production_orchestration = "production_orchestration"
    container_runtime = "container_runtime"
    desktop_automation = "desktop_automation"
    browser_automation = "browser_automation"


class RuntimeHardlineCommandClassification(BaseModel):
    candidate_ref: str = Field(..., min_length=1)
    source_ref: str = Field(..., min_length=1)
    status: RuntimeHardlineCommandClassificationStatus
    denial_category: RuntimeHardlineCommandDenialCategory
    denied: bool
    non_overridable: bool = True
    override_bypass_permitted: bool = False
    raw_command_text_persisted: bool = False
    raw_command_output_persisted: bool = False
    command_execution_performed: bool = False
    denial_reason_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=300)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_classification(self) -> "RuntimeHardlineCommandClassification":
        for value, field_name in [
            (self.candidate_ref, "candidate_ref"),
            (self.source_ref, "source_ref"),
            (self.denial_reason_ref, "denial_reason_ref"),
        ]:
            validate_execution_ref(value, field_name)
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if not self.non_overridable:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_FLOOR_MUST_BE_NON_OVERRIDABLE")
        if self.override_bypass_permitted:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_OVERRIDE_BYPASS_DENIED")
        if self.raw_command_text_persisted or self.raw_command_output_persisted:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_RAW_PERSISTENCE_DENIED")
        if self.command_execution_performed:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_CLASSIFICATION_MUST_NOT_EXECUTE")
        if self.denied and self.status != RuntimeHardlineCommandClassificationStatus.hardline_denied.value:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_DENIED_STATUS_REQUIRED")
        if not self.denied and self.denial_category != RuntimeHardlineCommandDenialCategory.allowed.value:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_ALLOWED_CATEGORY_REQUIRED")
        return self


class RuntimeHardlineCommandBlocklistReadModel(BaseModel):
    schema_version: str = "runtime_hardline_command_blocklist.v1"
    contract_ref: str = RUNTIME_HARDLINE_COMMAND_BLOCKLIST_CONTRACT_REF
    snapshot_ref: str = RUNTIME_HARDLINE_COMMAND_BLOCKLIST_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-hardline-command-blocklist:pending"
    route_ref: str = RUNTIME_HARDLINE_COMMAND_BLOCKLIST_ROUTE_REF
    cli_ref: str = RUNTIME_HARDLINE_COMMAND_BLOCKLIST_CLI_REF
    authority_state_route_ref: str
    authority_state_cli_ref: str
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    proof_ref: str = RUNTIME_HARDLINE_COMMAND_BLOCKLIST_PROOF_REF
    verifier_ref: str = RUNTIME_HARDLINE_COMMAND_BLOCKLIST_VERIFIER_REF
    status: str = "read_only_hardline_command_blocklist_floor"
    non_overridable_floor: bool = True
    override_bypass_permitted: bool = False
    command_execution_performed: bool = False
    raw_command_text_persisted: bool = False
    raw_command_output_persisted: bool = False
    route_classification_ref: str = "route-classification-ref:runtime-hardline-command-blocklist-readonly"
    foundation_gate_ref: str = "foundation-gate-ref:runtime-hardline-command-blocklist-floor"
    safe_disable_ref: str = "safe-disable-ref:runtime-command-floor-always-on"
    classification_count: int = 0
    denied_classification_count: int = 0
    allowed_classification_count: int = 0
    classifications: list[RuntimeHardlineCommandClassification] = Field(default_factory=list)
    hardline_rule_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS)
            + [
                "raw_command_text_omitted",
                "raw_command_output_omitted",
                "argv_examples_omitted",
            ]
        )
    )
    safe_summary: str = Field(..., min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeHardlineCommandBlocklistReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.proof_ref, "proof_ref"),
            (self.verifier_ref, "verifier_ref"),
            (self.route_classification_ref, "route_classification_ref"),
            (self.foundation_gate_ref, "foundation_gate_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.authority_state_route_ref, "authority_state_route_ref"),
            (self.authority_state_cli_ref, "authority_state_cli_ref"),
            (
                self.authority_state_decision_outcome,
                "authority_state_decision_outcome",
            ),
            (self.authority_state_status, "authority_state_status"),
            (
                self.authority_state_operator_message,
                "authority_state_operator_message",
            ),
        ]:
            validate_safe_execution_text(value, field_name)
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for ref in [
            *self.authority_state_reason_refs,
            *self.unsupported_adapter_refs,
            *self.hardline_rule_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
            *self.next_safe_action_refs,
        ]:
            validate_execution_ref(ref, "runtime_hardline_command_blocklist_ref")
        if (
            self.authority_state_mapping_ref
            != RUNTIME_HARDLINE_COMMAND_BLOCKLIST_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_HARDLINE_COMMAND_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_AUTHORITY_DECISION_INVALID")
        if not self.non_overridable_floor:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_FLOOR_MUST_BE_NON_OVERRIDABLE")
        if self.override_bypass_permitted:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_OVERRIDE_BYPASS_DENIED")
        if self.command_execution_performed:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_BLOCKLIST_MUST_NOT_EXECUTE")
        if self.raw_command_text_persisted or self.raw_command_output_persisted:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_RAW_PERSISTENCE_DENIED")
        if self.classification_count != len(self.classifications):
            raise ValueError("RUNTIME_HARDLINE_COMMAND_CLASSIFICATION_COUNT_MISMATCH")
        denied_count = sum(1 for item in self.classifications if item.denied)
        if self.denied_classification_count != denied_count:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_DENIED_COUNT_MISMATCH")
        if self.allowed_classification_count != self.classification_count - denied_count:
            raise ValueError("RUNTIME_HARDLINE_COMMAND_ALLOWED_COUNT_MISMATCH")
        for ref in RUNTIME_HARDLINE_COMMAND_BLOCKLIST_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_HARDLINE_COMMAND_BLOCKED_AUTHORITY_MISSING")
        return self


def classify_hardline_command_argv(
    argv: Sequence[str],
    *,
    source_ref: str = "test-corpus-ref:runtime-hardline-command-blocklist",
    candidate_ref: str | None = None,
) -> RuntimeHardlineCommandClassification:
    normalized = tuple(str(part) for part in argv)
    category = _deny_category(normalized)
    denied = category != RuntimeHardlineCommandDenialCategory.allowed
    status = (
        RuntimeHardlineCommandClassificationStatus.hardline_denied
        if denied
        else RuntimeHardlineCommandClassificationStatus.allowed_shape
    )
    reason_ref = (
        f"hardline-command-deny-ref:{category.value}"
        if denied
        else "hardline-command-allow-ref:exact-allowlisted-shape"
    )
    safe_summary = (
        f"Command shape is hardline denied as {category.value}."
        if denied
        else (
            "Command shape passes the hardline floor and still needs "
            "AuthorityLease capability checks."
        )
    )
    return RuntimeHardlineCommandClassification(
        candidate_ref=candidate_ref or _candidate_ref(normalized),
        source_ref=source_ref,
        status=status,
        denial_category=category,
        denied=denied,
        denial_reason_ref=reason_ref,
        safe_summary=safe_summary,
    )


def hardline_block_reason_for_argv(argv: Sequence[str]) -> str | None:
    classification = classify_hardline_command_argv(
        argv,
        source_ref="runtime-command-gateway-ref:hardline-floor",
    )
    if not classification.denied:
        return None
    return f"{RUNTIME_HARDLINE_COMMAND_BLOCKLIST_DENY_CODE}:{classification.denial_category}"


def build_runtime_hardline_command_blocklist_read_model() -> (
    RuntimeHardlineCommandBlocklistReadModel
):
    return build_runtime_hardline_command_blocklist_read_model_from_authority_catalog(
        authority_decision_catalog=build_authority_decision_catalog()
    )


def build_runtime_hardline_command_blocklist_read_model_from_authority_catalog(
    *,
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> RuntimeHardlineCommandBlocklistReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    classifications = [
        classify_hardline_command_argv(
            (
                "git",
                "--no-optional-locks",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.untrackedCache=false",
                "status",
                "--short",
                "--branch",
            ),
            source_ref="allowlisted-shape-ref:runtime-command-git-status",
            candidate_ref="hardline-command-candidate-ref:allowlisted-git-status",
        ),
        classify_hardline_command_argv(
            ("python", "-m", "pytest", "tests/test_governed_runtime_contracts.py", "-q"),
            source_ref="allowlisted-shape-ref:runtime-command-focused-pytest",
            candidate_ref="hardline-command-candidate-ref:allowlisted-focused-pytest",
        ),
        classify_hardline_command_argv(
            ("make", "doctor"),
            source_ref="allowlisted-shape-ref:runtime-command-repo-doctor",
            candidate_ref="hardline-command-candidate-ref:allowlisted-repo-doctor",
        ),
        *_blocked_corpus_classifications(),
    ]
    denied_count = sum(1 for item in classifications if item.denied)
    return RuntimeHardlineCommandBlocklistReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(
            {
                "classifications": [
                    {
                        "candidate_ref": classification.candidate_ref,
                        "status": classification.status,
                        "denial_category": classification.denial_category,
                        "denied": classification.denied,
                    }
                    for classification in classifications
                ],
                "authority_state_decision_ref": (
                    authority_entry.decision.decision_ref
                ),
                "authority_state_decision_outcome": _authority_value(
                    authority_entry.decision.outcome
                ),
            }
        ),
        authority_state_route_ref=(
            RUNTIME_HARDLINE_COMMAND_BLOCKLIST_AUTHORITY_STATE_ROUTE_REF
        ),
        authority_state_cli_ref=(
            RUNTIME_HARDLINE_COMMAND_BLOCKLIST_AUTHORITY_STATE_CLI_REF
        ),
        authority_state_mapping_ref=authority_entry.lane_ref,
        authority_state_catalog_ref=authority_entry.catalog_ref,
        authority_state_decision_ref=authority_entry.decision.decision_ref,
        authority_state_decision_outcome=_authority_value(
            authority_entry.decision.outcome
        ),
        authority_state_status=authority_entry.status,
        authority_state_operator_message=authority_entry.decision.operator_message,
        authority_state_reason_refs=list(authority_entry.decision.reason_refs),
        unsupported_adapter_refs=list(authority_entry.unsupported_adapter_refs),
        classification_count=len(classifications),
        denied_classification_count=denied_count,
        allowed_classification_count=len(classifications) - denied_count,
        classifications=classifications,
        hardline_rule_refs=[
            "hardline-command-rule-ref:no-shell-metachar",
            "hardline-command-rule-ref:no-shell-interpreter",
            "hardline-command-rule-ref:no-inline-code",
            "hardline-command-rule-ref:no-destructive-filesystem",
            "hardline-command-rule-ref:no-disk-writer",
            "hardline-command-rule-ref:no-network-transfer",
            "hardline-command-rule-ref:no-remote-access",
            "hardline-command-rule-ref:no-privilege-escalation",
            "hardline-command-rule-ref:no-git-mutation",
            "hardline-command-rule-ref:no-package-install",
            "hardline-command-rule-ref:no-production-orchestration",
            "hardline-command-rule-ref:no-browser-or-desktop-automation",
        ],
        blocked_authority_refs=list(RUNTIME_HARDLINE_COMMAND_BLOCKLIST_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            "promotion-path-ref:runtime-command-floor-security-review",
            "promotion-path-ref:runtime-command-floor-test-corpus",
            "promotion-path-ref:runtime-command-floor-route-classification",
            "promotion-path-ref:runtime-command-floor-foundation-gate",
        ],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-command-floor-expand-static-corpus",
            "next-safe-action-ref:runtime-command-floor-bind-foundation-gate",
        ],
        safe_summary=(
            "Hardline command floor is read-only posture. It classifies command shapes, "
            "blocks catastrophic categories before runner use, and grants no new command lane."
        ),
    )


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> AuthorityDecisionCatalogEntry:
    for entry in authority_decision_catalog:
        if entry.lane_ref == RUNTIME_HARDLINE_COMMAND_BLOCKLIST_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_HARDLINE_COMMAND_AUTHORITY_MAPPING_NOT_FOUND")


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _snapshot_hash_ref(payload: object) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-hardline-command-blocklist:{digest}"


def _blocked_corpus_classifications() -> list[RuntimeHardlineCommandClassification]:
    corpus: list[tuple[str, tuple[str, ...]]] = [
        ("hardline-command-candidate-ref:shell-metachar", ("git", "status", "&&", "echo")),
        ("hardline-command-candidate-ref:shell-interpreter", ("bash", "-c", "shape-ref")),
        ("hardline-command-candidate-ref:inline-code", ("python", "-c", "shape-ref")),
        ("hardline-command-candidate-ref:destructive-filesystem", ("rm", "-rf", "shape-ref")),
        ("hardline-command-candidate-ref:disk-writer", ("dd", "if=shape-ref", "of=shape-ref")),
        (
            "hardline-command-candidate-ref:network-transfer",
            ("curl", "https" + "://example.invalid"),
        ),
        ("hardline-command-candidate-ref:remote-access", ("ssh", "host-ref:example")),
        ("hardline-command-candidate-ref:privilege-escalation", ("sudo", "shape-ref")),
        ("hardline-command-candidate-ref:git-mutation", ("git", "push")),
        ("hardline-command-candidate-ref:package-install", ("python", "-m", "pip", "install")),
        ("hardline-command-candidate-ref:production-orchestration", ("kubectl", "apply")),
        ("hardline-command-candidate-ref:browser-automation", ("playwright", "test")),
    ]
    return [
        classify_hardline_command_argv(
            argv,
            source_ref="test-corpus-ref:runtime-hardline-command-blocklist",
            candidate_ref=candidate_ref,
        )
        for candidate_ref, argv in corpus
    ]


def _deny_category(argv: tuple[str, ...]) -> RuntimeHardlineCommandDenialCategory:
    if not argv or any(part == "" for part in argv):
        return RuntimeHardlineCommandDenialCategory.empty_argv
    if any(any(marker in part for marker in _SHELL_METACHARS) for part in argv):
        return RuntimeHardlineCommandDenialCategory.shell_metachar
    executable = _executable_name(argv[0])
    category = _DENIED_EXECUTABLE_CATEGORIES.get(executable)
    if category:
        return RuntimeHardlineCommandDenialCategory(category)
    if executable in _PYTHON_EXECUTABLES and _is_python_package_install(argv):
        return RuntimeHardlineCommandDenialCategory.package_install
    if executable in _PYTHON_EXECUTABLES and any(arg in _INLINE_CODE_ARGS for arg in argv[1:]):
        return RuntimeHardlineCommandDenialCategory.inline_code
    if executable in {"node", "deno", "ruby", "perl"} and any(
        arg in _INLINE_CODE_ARGS for arg in argv[1:]
    ):
        return RuntimeHardlineCommandDenialCategory.inline_code
    if executable == "git" and _git_mutation_requested(argv):
        return RuntimeHardlineCommandDenialCategory.git_mutation
    if executable in _PACKAGE_INSTALL_EXECUTABLES and any(
        arg in _PACKAGE_INSTALL_ARGS for arg in argv[1:]
    ):
        return RuntimeHardlineCommandDenialCategory.package_install
    if executable == "make" and any(arg in {"deploy", "release", "publish"} for arg in argv[1:]):
        return RuntimeHardlineCommandDenialCategory.production_orchestration
    if any(_NETWORK_URI_RE.match(part) for part in argv):
        return RuntimeHardlineCommandDenialCategory.network_transfer
    return RuntimeHardlineCommandDenialCategory.allowed


def _executable_name(value: str) -> str:
    name = Path(value).name.lower()
    if name.endswith(".exe"):
        name = name[:-4]
    return name


def _git_mutation_requested(argv: tuple[str, ...]) -> bool:
    for arg in argv[1:]:
        if arg == "--":
            return False
        if arg.startswith("-"):
            continue
        return arg in _GIT_MUTATION_ARGS
    return False


def _is_python_package_install(argv: tuple[str, ...]) -> bool:
    return len(argv) >= 4 and argv[1:4] == ("-m", "pip", "install")


def _candidate_ref(argv: tuple[str, ...]) -> str:
    digest = hashlib.sha256(
        json.dumps(list(argv), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return f"hardline-command-candidate-ref:{digest}"
