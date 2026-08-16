"""Exact, read-only Git metadata scouting for the local developer queue."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import validate_safe_task_text, validate_task_ref


DeveloperScoutSeverity = Literal["p0", "p1", "p2"]
DEVELOPER_GIT_SCOUT_CONTRACT_REF = "contract-ref:local-developer-git-scout:v1"


@dataclass(frozen=True)
class GitMetadataCommandResult:
    stdout: str
    exit_code: int = 0


class GitMetadataRunner(Protocol):
    def run(self, args: tuple[str, ...], *, cwd: Path) -> GitMetadataCommandResult: ...


class SubprocessGitMetadataRunner:
    """Runs only fixed, read-only Git metadata commands without a shell."""

    def run(self, args: tuple[str, ...], *, cwd: Path) -> GitMetadataCommandResult:
        completed = subprocess.run(
            list(args),
            cwd=cwd,
            env={"PATH": os.environ.get("PATH", ""), "LC_ALL": "C"},
            text=True,
            capture_output=True,
            check=False,
            shell=False,
            timeout=5,
        )
        return GitMetadataCommandResult(
            stdout=completed.stdout if completed.returncode == 0 else "",
            exit_code=completed.returncode,
        )


def _safe_ref(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:sha256:{digest}"


def _display_name_or_redacted(value: str) -> str | None:
    try:
        if "\n" in value or "\r" in value:
            return None
        validate_safe_task_text(value, "developer_git_branch_name")
    except ValueError:
        return None
    return value


class DeveloperUnmergedBranch(BaseModel):
    branch_ref: str
    display_name: str | None = None
    upstream_configured: bool

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_branch(self) -> "DeveloperUnmergedBranch":
        validate_task_ref(self.branch_ref, "developer_unmerged_branch_ref")
        if self.display_name is not None:
            validate_safe_task_text(self.display_name, "developer_unmerged_branch_name")
        return self


class DeveloperScoutRisk(BaseModel):
    risk_ref: str
    severity: DeveloperScoutSeverity
    safe_summary: str
    remediation_ref: str
    automatic_remediation_performed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_risk(self) -> "DeveloperScoutRisk":
        for value in [self.risk_ref, self.remediation_ref]:
            validate_task_ref(value, "developer_scout_risk_ref")
        for value in [self.severity, self.safe_summary]:
            validate_safe_task_text(value, "developer_scout_risk_text")
        if self.automatic_remediation_performed:
            raise ValueError("developer scout cannot remediate automatically")
        return self


class DeveloperWorkspaceScoutReadModel(BaseModel):
    schema_version: Literal["uaa-developer-workspace-scout.v1"] = (
        "uaa-developer-workspace-scout.v1"
    )
    contract_ref: str = DEVELOPER_GIT_SCOUT_CONTRACT_REF
    safe_summary: str
    dirty_entry_count: int = Field(ge=0)
    registered_worktree_count: int = Field(ge=0)
    prunable_worktree_count: int = Field(ge=0)
    unmerged_branches: list[DeveloperUnmergedBranch] = Field(default_factory=list)
    unmerged_branch_count: int = Field(ge=0)
    branch_without_upstream_count: int = Field(ge=0)
    local_main_ahead_count: int | None = Field(default=None, ge=0)
    local_main_behind_count: int | None = Field(default=None, ge=0)
    risks: list[DeveloperScoutRisk] = Field(default_factory=list)
    next_safe_action: str
    git_metadata_inspection_performed: bool = True
    git_mutation_performed: bool = False
    branch_deletion_performed: bool = False
    worktree_prune_performed: bool = False
    merge_performed: bool = False
    remote_dispatch_performed: bool = False
    product_runtime_authority_granted: bool = False
    raw_paths_included: bool = False
    raw_content_included: bool = False
    github_pr_state_inspected: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "DeveloperWorkspaceScoutReadModel":
        validate_task_ref(self.contract_ref, "developer_scout_contract_ref")
        for value in [self.safe_summary, self.next_safe_action]:
            validate_safe_task_text(value, "developer_scout_text")
        if self.unmerged_branch_count != len(self.unmerged_branches):
            raise ValueError("developer scout unmerged branch count mismatch")
        forbidden = {
            "git_mutation_performed": self.git_mutation_performed,
            "branch_deletion_performed": self.branch_deletion_performed,
            "worktree_prune_performed": self.worktree_prune_performed,
            "merge_performed": self.merge_performed,
            "remote_dispatch_performed": self.remote_dispatch_performed,
            "product_runtime_authority_granted": self.product_runtime_authority_granted,
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
            "github_pr_state_inspected": self.github_pr_state_inspected,
        }
        enabled = [name for name, value in forbidden.items() if value]
        if enabled:
            raise ValueError(f"developer scout enabled {enabled[0]}")
        return self


class DeveloperWorkspaceScout:
    """Scouts deterministic Git metadata and emits review-only cleanup gates."""

    _STATUS = ("git", "status", "--porcelain=v1", "--untracked-files=all")
    _WORKTREES = ("git", "worktree", "list", "--porcelain")
    _UNMERGED = (
        "git",
        "branch",
        "--no-merged",
        "main",
        "--format=%(refname:short)|%(upstream:short)",
    )
    _DIVERGENCE = ("git", "rev-list", "--left-right", "--count", "main...origin/main")

    def __init__(self, runner: GitMetadataRunner | None = None) -> None:
        self.runner = runner or SubprocessGitMetadataRunner()

    def inspect(self, *, repository_root: Path) -> DeveloperWorkspaceScoutReadModel:
        status = self.runner.run(self._STATUS, cwd=repository_root)
        worktrees = self.runner.run(self._WORKTREES, cwd=repository_root)
        branches = self.runner.run(self._UNMERGED, cwd=repository_root)
        divergence = self.runner.run(self._DIVERGENCE, cwd=repository_root)

        dirty_entry_count = len([line for line in status.stdout.splitlines() if line.strip()])
        registered_worktree_count = sum(
            1 for line in worktrees.stdout.splitlines() if line.startswith("worktree ")
        )
        prunable_worktree_count = sum(
            1 for line in worktrees.stdout.splitlines() if line.startswith("prunable ")
        )
        unmerged_branches = self._parse_unmerged_branches(branches.stdout)
        local_main_ahead_count, local_main_behind_count = self._parse_divergence(
            divergence
        )
        risks = self._risks(
            dirty_entry_count=dirty_entry_count,
            prunable_worktree_count=prunable_worktree_count,
            unmerged_branches=unmerged_branches,
            local_main_behind_count=local_main_behind_count,
        )
        return DeveloperWorkspaceScoutReadModel(
            safe_summary=(
                "Read-only local Git metadata scout. It counts hygiene risks and emits "
                "review gates without merging, deleting branches, pruning worktrees, or "
                "running developer tasks. GitHub pull-request state is not inspected in v1."
            ),
            dirty_entry_count=dirty_entry_count,
            registered_worktree_count=registered_worktree_count,
            prunable_worktree_count=prunable_worktree_count,
            unmerged_branches=unmerged_branches,
            unmerged_branch_count=len(unmerged_branches),
            branch_without_upstream_count=sum(
                1 for branch in unmerged_branches if not branch.upstream_configured
            ),
            local_main_ahead_count=local_main_ahead_count,
            local_main_behind_count=local_main_behind_count,
            risks=risks,
            next_safe_action=(
                "Review the P0 hygiene gates, reconcile current main only in a clean "
                "worktree, then triage each branch or prunable registration before any "
                "explicit merge, worktree prune, or branch deletion command."
            ),
        )

    @staticmethod
    def _parse_unmerged_branches(stdout: str) -> list[DeveloperUnmergedBranch]:
        branches: list[DeveloperUnmergedBranch] = []
        for line in stdout.splitlines():
            if not line.strip():
                continue
            name, separator, upstream = line.partition("|")
            if not separator:
                continue
            name = name.strip()
            upstream = upstream.strip()
            branches.append(
                DeveloperUnmergedBranch(
                    branch_ref=_safe_ref("branch-ref", name),
                    display_name=_display_name_or_redacted(name),
                    upstream_configured=bool(upstream),
                )
            )
        return branches

    @staticmethod
    def _parse_divergence(
        result: GitMetadataCommandResult,
    ) -> tuple[int | None, int | None]:
        if result.exit_code != 0:
            return None, None
        values = result.stdout.strip().split()
        if len(values) != 2 or not all(value.isdigit() for value in values):
            return None, None
        return int(values[0]), int(values[1])

    @staticmethod
    def _risks(
        *,
        dirty_entry_count: int,
        prunable_worktree_count: int,
        unmerged_branches: list[DeveloperUnmergedBranch],
        local_main_behind_count: int | None,
    ) -> list[DeveloperScoutRisk]:
        risks: list[DeveloperScoutRisk] = []
        if dirty_entry_count:
            risks.append(
                DeveloperScoutRisk(
                    risk_ref="developer-risk-ref:dirty-worktree",
                    severity="p0",
                    safe_summary=(
                        "The current worktree contains uncommitted entries. Do not pull, "
                        "merge, rebase, prune, or reuse it for a new task until it is "
                        "intentionally reviewed."
                    ),
                    remediation_ref="developer-remediation-ref:review-dirty-worktree",
                )
            )
        if prunable_worktree_count:
            risks.append(
                DeveloperScoutRisk(
                    risk_ref="developer-risk-ref:prunable-worktree-registrations",
                    severity="p0",
                    safe_summary=(
                        "Stale worktree registrations require branch-by-branch review; "
                        "pruning them automatically could discard an active recovery path."
                    ),
                    remediation_ref="developer-remediation-ref:triage-worktree-registrations",
                )
            )
        if local_main_behind_count:
            risks.append(
                DeveloperScoutRisk(
                    risk_ref="developer-risk-ref:local-main-behind-origin",
                    severity="p0",
                    safe_summary=(
                        "Local main is behind its tracked remote. Reconcile only after "
                        "the current worktree is clean and active branches are classified."
                    ),
                    remediation_ref="developer-remediation-ref:reconcile-main-in-clean-worktree",
                )
            )
        if unmerged_branches:
            risks.append(
                DeveloperScoutRisk(
                    risk_ref="developer-risk-ref:unmerged-branches",
                    severity="p1",
                    safe_summary=(
                        "Non-merged branches need an explicit PR, verification, conflict, "
                        "and ownership decision before they are merged or retired."
                    ),
                    remediation_ref="developer-remediation-ref:triage-unmerged-branches",
                )
            )
        if any(not branch.upstream_configured for branch in unmerged_branches):
            risks.append(
                DeveloperScoutRisk(
                    risk_ref="developer-risk-ref:unpublished-branches",
                    severity="p1",
                    safe_summary=(
                        "Some non-merged branches have no configured upstream and need a "
                        "local ownership decision before review or cleanup."
                    ),
                    remediation_ref="developer-remediation-ref:classify-unpublished-branches",
                )
            )
        return risks


class GitHubPullRequestRunner(Protocol):
    def run(self, args: tuple[str, ...], *, cwd: Path) -> GitMetadataCommandResult: ...


class SubprocessGitHubPullRequestRunner:
    """Runs one fixed read-only GitHub CLI query without a shell."""

    def run(self, args: tuple[str, ...], *, cwd: Path) -> GitMetadataCommandResult:
        completed = subprocess.run(
            list(args),
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
            timeout=10,
        )
        return GitMetadataCommandResult(
            stdout=completed.stdout if completed.returncode == 0 else "",
            exit_code=completed.returncode,
        )


class DeveloperPullRequestMetadata(BaseModel):
    pull_request_ref: str
    number: int = Field(ge=1)
    title: str
    head_branch_ref: str
    head_branch_display_name: str | None = None
    base_branch_ref: str
    base_branch_display_name: str | None = None
    is_draft: bool
    merge_state_status: str
    review_decision: str | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_pull_request(self) -> "DeveloperPullRequestMetadata":
        for value in [
            self.pull_request_ref,
            self.head_branch_ref,
            self.base_branch_ref,
        ]:
            validate_task_ref(value, "developer_pull_request_ref")
        for value in [
            self.title,
            self.merge_state_status,
            *(
                [self.review_decision] if self.review_decision is not None else []
            ),
            *(
                [self.head_branch_display_name]
                if self.head_branch_display_name is not None
                else []
            ),
            *(
                [self.base_branch_display_name]
                if self.base_branch_display_name is not None
                else []
            ),
        ]:
            validate_safe_task_text(value, "developer_pull_request_text")
        return self


class DeveloperPullRequestScoutReadModel(BaseModel):
    schema_version: Literal["uaa-developer-pull-request-scout.v1"] = (
        "uaa-developer-pull-request-scout.v1"
    )
    contract_ref: str = "contract-ref:local-developer-pull-request-scout:v1"
    available: bool
    open_pull_request_count: int = Field(ge=0)
    pull_requests: list[DeveloperPullRequestMetadata] = Field(default_factory=list)
    risks: list[DeveloperScoutRisk] = Field(default_factory=list)
    safe_summary: str
    next_safe_action: str
    github_read_only_inspection_performed: bool
    github_mutation_performed: bool = False
    git_mutation_performed: bool = False
    remote_dispatch_performed: bool = False
    product_runtime_authority_granted: bool = False
    raw_paths_included: bool = False
    raw_content_included: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "DeveloperPullRequestScoutReadModel":
        validate_task_ref(self.contract_ref, "developer_pull_request_scout_ref")
        for value in [self.safe_summary, self.next_safe_action]:
            validate_safe_task_text(value, "developer_pull_request_scout_text")
        if self.open_pull_request_count != len(self.pull_requests):
            raise ValueError("developer pull request scout count mismatch")
        forbidden = {
            "github_mutation_performed": self.github_mutation_performed,
            "git_mutation_performed": self.git_mutation_performed,
            "remote_dispatch_performed": self.remote_dispatch_performed,
            "product_runtime_authority_granted": self.product_runtime_authority_granted,
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
        }
        enabled = [name for name, value in forbidden.items() if value]
        if enabled:
            raise ValueError(f"developer pull request scout enabled {enabled[0]}")
        return self


class DeveloperPullRequestScout:
    """Opt-in open-PR metadata reader; it has no GitHub mutation capability."""

    _OPEN_PULL_REQUESTS = (
        "gh",
        "pr",
        "list",
        "--state",
        "open",
        "--limit",
        "100",
        "--json",
        "number,title,headRefName,baseRefName,isDraft,mergeStateStatus,reviewDecision",
    )

    def __init__(self, runner: GitHubPullRequestRunner | None = None) -> None:
        self.runner = runner or SubprocessGitHubPullRequestRunner()

    def inspect(self, *, repository_root: Path) -> DeveloperPullRequestScoutReadModel:
        result = self.runner.run(self._OPEN_PULL_REQUESTS, cwd=repository_root)
        if result.exit_code != 0:
            return DeveloperPullRequestScoutReadModel(
                available=False,
                open_pull_request_count=0,
                safe_summary=(
                    "The optional fixed GitHub read-only query was unavailable. No pull "
                    "request state was inferred and no GitHub mutation was attempted."
                ),
                next_safe_action=(
                    "Restore a local GitHub CLI read-only session, then inspect open pull "
                    "requests before making any merge or branch-retirement decision."
                ),
                github_read_only_inspection_performed=False,
                risks=[
                    DeveloperScoutRisk(
                        risk_ref="developer-risk-ref:github-pr-state-unavailable",
                        severity="p1",
                        safe_summary=(
                            "Open pull-request state is unavailable, so no branch can be "
                            "treated as merge-ready from local Git metadata alone."
                        ),
                        remediation_ref="developer-remediation-ref:restore-github-read-only-inspection",
                    )
                ],
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = []
        if not isinstance(payload, list):
            payload = []
        pull_requests = [self._pull_request(item) for item in payload if isinstance(item, dict)]
        risks = self._risks(pull_requests)
        return DeveloperPullRequestScoutReadModel(
            available=True,
            open_pull_request_count=len(pull_requests),
            pull_requests=pull_requests,
            risks=risks,
            safe_summary=(
                "Optional fixed GitHub read-only inspection of open pull-request metadata. "
                "It does not review, merge, close, comment on, push, or alter any pull request."
            ),
            next_safe_action=(
                "Resolve conflict or unstable PRs first, then review verifier evidence "
                "and required approvals before explicitly merging any ready PR."
            ),
            github_read_only_inspection_performed=True,
        )

    @staticmethod
    def _pull_request(item: dict[str, object]) -> DeveloperPullRequestMetadata:
        number = item.get("number")
        if not isinstance(number, int) or number <= 0:
            raise ValueError("DEVELOPER_PULL_REQUEST_NUMBER_INVALID")
        title = str(item.get("title") or "")
        head = str(item.get("headRefName") or "")
        base = str(item.get("baseRefName") or "")
        merge_state = str(item.get("mergeStateStatus") or "UNKNOWN")
        review = str(item.get("reviewDecision") or "") or None
        return DeveloperPullRequestMetadata(
            pull_request_ref=f"pull-request-ref:{number}",
            number=number,
            title=_safe_title_or_redacted(title, f"Pull request {number} title redacted"),
            head_branch_ref=_safe_ref("branch-ref", head),
            head_branch_display_name=_display_name_or_redacted(head),
            base_branch_ref=_safe_ref("branch-ref", base),
            base_branch_display_name=_display_name_or_redacted(base),
            is_draft=bool(item.get("isDraft", False)),
            merge_state_status=_safe_title_or_redacted(merge_state, "UNKNOWN"),
            review_decision=(
                _safe_title_or_redacted(review, "review decision redacted")
                if review is not None
                else None
            ),
        )

    @staticmethod
    def _risks(
        pull_requests: list[DeveloperPullRequestMetadata],
    ) -> list[DeveloperScoutRisk]:
        risks: list[DeveloperScoutRisk] = []
        blocked = [
            pull_request
            for pull_request in pull_requests
            if pull_request.merge_state_status.upper() in {"DIRTY", "UNSTABLE"}
        ]
        if blocked:
            risks.append(
                DeveloperScoutRisk(
                    risk_ref="developer-risk-ref:open-pr-merge-instability",
                    severity="p0",
                    safe_summary=(
                        "One or more open pull requests report unstable or conflicting "
                        "merge state and must be reconciled before they can be merged."
                    ),
                    remediation_ref="developer-remediation-ref:rebase-and-verify-pr-in-isolated-worktree",
                )
            )
        if any(pull_request.is_draft for pull_request in pull_requests):
            risks.append(
                DeveloperScoutRisk(
                    risk_ref="developer-risk-ref:open-draft-prs",
                    severity="p1",
                    safe_summary=(
                        "Draft pull requests remain review-incomplete and should retain a "
                        "clear owner, verifier evidence, and next action."
                    ),
                    remediation_ref="developer-remediation-ref:triage-open-draft-prs",
                )
            )
        if any(not pull_request.review_decision for pull_request in pull_requests):
            risks.append(
                DeveloperScoutRisk(
                    risk_ref="developer-risk-ref:open-prs-without-recorded-review",
                    severity="p1",
                    safe_summary=(
                        "At least one open pull request lacks a recorded review decision; "
                        "do not treat it as merge-ready based on green local evidence alone."
                    ),
                    remediation_ref="developer-remediation-ref:obtain-and-record-pr-review",
                )
            )
        return risks


def _safe_title_or_redacted(value: str, fallback: str) -> str:
    try:
        validate_safe_task_text(value, "developer_pull_request_title")
    except ValueError:
        return fallback
    return value
