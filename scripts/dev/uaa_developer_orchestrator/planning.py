"""Read the canonical planning queue without turning Markdown into execution authority."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)


DeveloperPlanningStatus = Literal[
    "active",
    "queued",
    "proposed",
    "implemented",
    "blocked",
    "unclear",
]

CANONICAL_QUEUE_DOCUMENTS = (
    "docs/kanban/current_board.md",
    "docs/kanban/founder_command_center_board.md",
    "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
    "docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md",
)

_HEADING = re.compile(
    r"^###\s+(?P<identifier>(?:UAA|FCC|WEB|TAW)(?:-[A-Za-z0-9.]+)+)"
    r"(?P<rest>.*)$",
    re.MULTILINE,
)
_TASK_HEADING = re.compile(
    r"^##\s+Task\s+[0-9]+[a-z]?\s+-\s+"
    r"(?P<identifier>(?:UAA|FCC|WEB|TAW)(?:-[A-Za-z0-9.]+)+)"
    r"(?P<rest>.*)$",
    re.MULTILINE,
)
_STATUS = re.compile(r"^Status:\s*(?P<status>.+)$", re.IGNORECASE | re.MULTILINE)
_PRIORITY = re.compile(r"\bP(?P<priority>[0-3])\b")
_ANY_HEADING = re.compile(r"^(?P<marks>#{1,6})\s+", re.MULTILINE)


def _fingerprint_ref(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"planning-fingerprint-ref:sha256:{digest}"


def _document_slug(relative_path: str) -> str:
    return relative_path.removesuffix(".md").replace("/", "-").replace("_", "-")


def _source_status(*, section: str, block: str) -> DeveloperPlanningStatus:
    status_match = _STATUS.search(block)
    descriptor = (status_match.group("status") if status_match else section).lower()
    if any(
        token in descriptor for token in ("implemented", "complete", "ready for review")
    ):
        return "implemented"
    if "blocked" in descriptor or "parked" in descriptor:
        return "blocked"
    if (
        "queue" in descriptor
        or "backlog" in descriptor
        or "authority-conveyor implementation" in descriptor
    ):
        return "queued"
    if "active" in descriptor or "current" in descriptor:
        return "active"
    if any(token in descriptor for token in ("proposed", "future", "planned")):
        return "proposed"
    return "unclear"


def _task_block_end(text: str, heading: re.Match[str]) -> int:
    heading_level = len(heading.group(0)) - len(heading.group(0).lstrip("#"))
    for candidate in _ANY_HEADING.finditer(text, heading.end()):
        if len(candidate.group("marks")) <= heading_level:
            return candidate.start()
    return len(text)


def _safe_title(identifier: str, heading_title: str) -> str:
    """Keep the durable catalog useful without carrying unsafe heading text."""

    try:
        validate_safe_task_text(heading_title, "developer_planning_heading_title")
    except ValueError:
        return f"Canonical planning item {identifier}"
    return heading_title


class DeveloperPlanningCandidate(BaseModel):
    """A source-indexed candidate. It cannot be claimed until separately triaged."""

    planning_item_ref: str
    canonical_task_ref: str
    title: str
    priority: Literal["p0", "p1", "p2", "p3"] | None = None
    source_status: DeveloperPlanningStatus
    canonical_source_ref: str
    canonical_source_fingerprint_ref: str
    source_anchor_ref: str
    safe_summary: str
    triage_required: bool = True
    dispatch_eligible: bool = False
    raw_paths_included: bool = False
    raw_content_included: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_candidate(self) -> "DeveloperPlanningCandidate":
        for value in [
            self.planning_item_ref,
            self.canonical_task_ref,
            self.canonical_source_ref,
            self.canonical_source_fingerprint_ref,
            self.source_anchor_ref,
        ]:
            validate_task_ref(value, "developer_planning_candidate_ref")
        for value in [self.title, self.safe_summary, self.source_status]:
            validate_safe_task_text(value, "developer_planning_candidate_text")
        if not self.triage_required:
            raise ValueError("planning candidates must require explicit triage")
        if self.dispatch_eligible:
            raise ValueError("planning candidates cannot be dispatch eligible")
        if self.raw_paths_included or self.raw_content_included:
            raise ValueError("planning candidates must omit raw paths and content")
        return self


class DeveloperPlanningCatalog(BaseModel):
    schema_version: Literal["uaa-developer-planning-catalog.v1"] = (
        "uaa-developer-planning-catalog.v1"
    )
    source_document_refs: list[str] = Field(default_factory=list)
    source_document_fingerprint_refs: list[str] = Field(default_factory=list)
    candidates: list[DeveloperPlanningCandidate] = Field(default_factory=list)
    safe_summary: str
    next_safe_action: str
    automatic_queue_mutation_performed: bool = False
    automatic_agent_dispatch_performed: bool = False
    raw_paths_included: bool = False
    raw_content_included: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_catalog(self) -> "DeveloperPlanningCatalog":
        for value in [
            *self.source_document_refs,
            *self.source_document_fingerprint_refs,
        ]:
            validate_task_ref(value, "developer_planning_catalog_ref")
        for value in [self.safe_summary, self.next_safe_action]:
            validate_safe_task_text(value, "developer_planning_catalog_text")
        if (
            self.automatic_queue_mutation_performed
            or self.automatic_agent_dispatch_performed
        ):
            raise ValueError(
                "planning catalog must not mutate or dispatch automatically"
            )
        if self.raw_paths_included or self.raw_content_included:
            raise ValueError("planning catalog must omit raw paths and content")
        planning_refs = [candidate.planning_item_ref for candidate in self.candidates]
        if len(planning_refs) != len(set(planning_refs)):
            raise ValueError("planning catalog item refs must be unique")
        return self


def build_developer_planning_catalog(
    root: Path | None = None,
) -> DeveloperPlanningCatalog:
    """Index the durable UAA planning sources with safe refs only.

    A candidate is deliberately not an executable task: a human still supplies
    its branch/worktree assignment, exact acceptance checks, dependencies, and
    merge gates through the local developer coordinator.
    """

    repository_root = root or Path(__file__).resolve().parents[3]
    candidates: list[DeveloperPlanningCandidate] = []
    document_refs: list[str] = []
    fingerprint_refs: list[str] = []
    for relative_path in CANONICAL_QUEUE_DOCUMENTS:
        path = repository_root / relative_path
        if not path.exists():
            continue
        document_ref = f"canonical:{_document_slug(relative_path)}"
        text = path.read_text(encoding="utf-8")
        document_refs.append(document_ref)
        fingerprint_refs.append(_fingerprint_ref(text))
        headings = sorted(
            [*_HEADING.finditer(text), *_TASK_HEADING.finditer(text)],
            key=lambda match: match.start(),
        )
        identifier_counts: dict[str, int] = {}
        for heading in headings:
            key = heading.group("identifier").lower()
            identifier_counts[key] = identifier_counts.get(key, 0) + 1
        section = ""
        section_start = 0
        sections = list(re.finditer(r"^##\s+(?P<section>.+)$", text, re.MULTILINE))
        for heading in headings:
            while (
                section_start < len(sections)
                and sections[section_start].start() < heading.start()
            ):
                section = sections[section_start].group("section")
                section_start += 1
            block_end = _task_block_end(text, heading)
            block = text[heading.start() : block_end]
            identifier = heading.group("identifier")
            stable_identifier = identifier.lower()
            rest = heading.group("rest").strip(" -–—:\t")
            if identifier_counts[stable_identifier] > 1:
                heading_fingerprint = hashlib.sha256(
                    f"{stable_identifier}\n{section}\n{rest}".encode("utf-8")
                ).hexdigest()[:12]
                stable_identifier = f"{stable_identifier}-{heading_fingerprint}"
            title = _safe_title(
                identifier,
                rest or f"Canonical planning item {identifier}",
            )
            priority_match = _PRIORITY.search(f"{identifier} {rest}")
            priority = (
                f"p{priority_match.group('priority')}"
                if priority_match is not None
                else None
            )
            candidates.append(
                DeveloperPlanningCandidate(
                    planning_item_ref=(
                        f"planning-item-ref:{_document_slug(relative_path)}/{stable_identifier}"
                    ),
                    canonical_task_ref=f"canonical-task-ref:{identifier.lower()}",
                    title=title,
                    priority=priority,
                    source_status=_source_status(section=section, block=block),
                    canonical_source_ref=document_ref,
                    canonical_source_fingerprint_ref=_fingerprint_ref(text),
                    source_anchor_ref=(
                        f"canonical-anchor-ref:{_document_slug(relative_path)}/{stable_identifier}"
                    ),
                    safe_summary=(
                        "Canonical planning candidate indexed for explicit developer "
                        "triage; it is not an assigned task or execution authority."
                    ),
                )
            )
        if relative_path == "docs/kanban/current_board.md" and "UAA-P1-091" in text:
            candidates.append(
                DeveloperPlanningCandidate(
                    planning_item_ref="planning-item-ref:docs-kanban-current-board/authority-conveyor-1",
                    canonical_task_ref="canonical-task-ref:uaa-p1-091",
                    title="UAA-P1-091 governed local runtime pilot",
                    priority="p1",
                    source_status="active",
                    canonical_source_ref=document_ref,
                    canonical_source_fingerprint_ref=_fingerprint_ref(text),
                    source_anchor_ref="canonical-anchor-ref:docs-kanban-current-board/authority-conveyor-1",
                    safe_summary=(
                        "The sole active authority-conveyor candidate. It still requires "
                        "an exact branch, worktree, verifier, and merge-gate triage record "
                        "before developer assignment."
                    ),
                )
            )
    return DeveloperPlanningCatalog(
        source_document_refs=document_refs,
        source_document_fingerprint_refs=fingerprint_refs,
        candidates=candidates,
        safe_summary=(
            "Indexes the existing strategic queue from canonical UAA planning sources. "
            "Candidates remain non-dispatchable until an operator adds exact branch, "
            "worktree, verifier, dependency, and merge-gate metadata."
        ),
        next_safe_action=(
            "Review the highest-priority queued or active candidate, then triage one "
            "bounded work item into the durable Mac/Beast developer queue."
        ),
    )


def find_planning_candidate(
    catalog: DeveloperPlanningCatalog,
    planning_item_ref: str,
) -> DeveloperPlanningCandidate:
    validate_task_ref(planning_item_ref, "developer_planning_item_ref")
    for candidate in catalog.candidates:
        if candidate.planning_item_ref == planning_item_ref:
            return candidate
    raise ValueError("DEVELOPER_PLANNING_ITEM_NOT_FOUND")
