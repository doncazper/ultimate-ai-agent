"""Reusable encrypted Boards core for ECO-003.

Boards owns visual placement and standalone board items. Canonical Task cards
retain only a Task reference and resolve current truth through ``TaskRepository``.
The module has no route, UI, scheduler, network, or collaboration runtime.
"""

from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.ecosystem.local_data import (
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    PutRecord,
    UnitOfWorkReceipt,
)
from ultimate_ai_agent.core.ecosystem.tasks import CanonicalTask, TaskRepository
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO_BOARD_SCHEMA_VERSION = "uaa-eco-003-board.v1"
ECO_BOARD_TEMPLATE_SCHEMA_VERSION = "uaa-eco-003-board-template.v1"
ECO_BOARD_MUTATION_ACTION = "ecosystem.boards.apply"
ECO_BOARD_MODULE_REF = "module-ref:boards"
ECO_BOARD_RECORD_KIND_REF = "record-kind-ref:canonical-board"
ECO_BOARD_TEMPLATE_RECORD_KIND_REF = "record-kind-ref:board-template"
ECO_BOARD_RETENTION_REF = "retention-ref:boards-operator-managed"
_ALL_BOARDS_SEARCH_TERM = "entity-kind:canonical-board"
_ALL_TEMPLATES_SEARCH_TERM = "entity-kind:board-template"
_MAX_UNDO_DEPTH = 20
_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")


class BoardError(RuntimeError):
    """Fail-closed Boards error with a stable, non-sensitive code."""


class BoardConflict(BoardError):
    pass


class BoardSubjectKind(str, Enum):
    board_item = "board_item"
    task = "task"


class _BoardModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )


def _validate_ref(value: str, field_name: str) -> str:
    if not _SAFE_REF_RE.fullmatch(value) or contains_obvious_secret(value):
        raise ValueError(f"ECO_BOARD_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _validate_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"ECO_BOARD_{field_name.upper()}_DUPLICATE_REF")
    for value in values:
        _validate_ref(value, field_name)
    return values


def _private_text(value: str, *, maximum: int, code: str) -> str:
    if not value or len(value.encode("utf-8")) > maximum:
        raise ValueError(code)
    if any(ord(character) < 32 and character not in "\n\t" for character in value):
        raise ValueError(code)
    return value


def _stable_ref(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


class BoardLane(_BoardModel):
    lane_ref: str
    name: str = Field(..., repr=False)
    position: int = Field(..., ge=0)
    wip_limit: int | None = Field(default=None, ge=1, le=10_000)
    archived: bool = False

    @field_validator("lane_ref")
    @classmethod
    def validate_lane_ref(cls, value: str) -> str:
        return _validate_ref(value, "lane_ref")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _private_text(value, maximum=256, code="ECO_BOARD_LANE_NAME_INVALID")


class BoardCard(_BoardModel):
    card_ref: str
    subject_kind: BoardSubjectKind
    subject_ref: str
    lane_ref: str
    position: int = Field(..., ge=0)
    title: str | None = Field(default=None, repr=False)
    description: str | None = Field(default=None, repr=False)
    label_refs: tuple[str, ...] = Field(default=(), max_length=64)
    archived: bool = False

    @model_validator(mode="after")
    def validate_card(self) -> "BoardCard":
        for field_name in ("card_ref", "subject_ref", "lane_ref"):
            _validate_ref(getattr(self, field_name), field_name)
        _validate_refs(self.label_refs, "label_ref")
        if self.subject_kind == BoardSubjectKind.board_item:
            if self.title is None:
                raise ValueError("ECO_BOARD_ITEM_TITLE_REQUIRED")
            _private_text(
                self.title, maximum=2_048, code="ECO_BOARD_ITEM_TITLE_INVALID"
            )
            if self.description is not None:
                _private_text(
                    self.description,
                    maximum=65_536,
                    code="ECO_BOARD_ITEM_DESCRIPTION_INVALID",
                )
        elif self.title is not None or self.description is not None:
            raise ValueError("ECO_BOARD_TASK_PROJECTION_CANNOT_COPY_TASK_TRUTH")
        return self


class SavedBoardFilter(_BoardModel):
    filter_ref: str
    name: str = Field(..., repr=False)
    lane_refs: tuple[str, ...] = Field(default=(), max_length=64)
    label_refs: tuple[str, ...] = Field(default=(), max_length=64)
    subject_kinds: tuple[BoardSubjectKind, ...] = Field(default=(), max_length=2)
    include_archived: bool = False

    @model_validator(mode="after")
    def validate_filter(self) -> "SavedBoardFilter":
        _validate_ref(self.filter_ref, "filter_ref")
        _private_text(self.name, maximum=256, code="ECO_BOARD_FILTER_NAME_INVALID")
        _validate_refs(self.lane_refs, "lane_ref")
        _validate_refs(self.label_refs, "label_ref")
        if len(self.subject_kinds) != len(set(self.subject_kinds)):
            raise ValueError("ECO_BOARD_FILTER_DUPLICATE_SUBJECT_KIND")
        return self


class BoardSnapshot(_BoardModel):
    name: str = Field(..., repr=False)
    description: str | None = Field(default=None, repr=False)
    lanes: tuple[BoardLane, ...]
    cards: tuple[BoardCard, ...] = ()
    saved_filters: tuple[SavedBoardFilter, ...] = ()
    template_ref: str | None = None
    archived: bool = False


class Board(_BoardModel):
    schema_version: Literal["uaa-eco-003-board.v1"] = ECO_BOARD_SCHEMA_VERSION
    workspace_ref: str
    board_ref: str
    name: str = Field(..., repr=False)
    description: str | None = Field(default=None, repr=False)
    lanes: tuple[BoardLane, ...]
    cards: tuple[BoardCard, ...] = Field(default=(), max_length=25_000)
    saved_filters: tuple[SavedBoardFilter, ...] = Field(default=(), max_length=256)
    template_ref: str | None = None
    archived: bool = False
    version: int = Field(default=1, ge=1)
    undo_stack: tuple[BoardSnapshot, ...] = Field(
        default=(), max_length=_MAX_UNDO_DEPTH, repr=False
    )

    @model_validator(mode="after")
    def validate_board(self) -> "Board":
        for field_name in ("workspace_ref", "board_ref", "template_ref"):
            value = getattr(self, field_name)
            if value is not None:
                _validate_ref(value, field_name)
        _private_text(self.name, maximum=512, code="ECO_BOARD_NAME_INVALID")
        if self.description is not None:
            _private_text(
                self.description,
                maximum=65_536,
                code="ECO_BOARD_DESCRIPTION_INVALID",
            )
        if not self.lanes:
            raise ValueError("ECO_BOARD_LANE_REQUIRED")
        self._validate_layout(self.lanes, self.cards, self.saved_filters)
        return self

    @staticmethod
    def _validate_layout(
        lanes: tuple[BoardLane, ...],
        cards: tuple[BoardCard, ...],
        filters: tuple[SavedBoardFilter, ...],
    ) -> None:
        lane_refs = [lane.lane_ref for lane in lanes]
        if len(lane_refs) != len(set(lane_refs)):
            raise ValueError("ECO_BOARD_DUPLICATE_LANE_REF")
        active_lanes = [lane for lane in lanes if not lane.archived]
        if sorted(lane.position for lane in active_lanes) != list(
            range(len(active_lanes))
        ):
            raise ValueError("ECO_BOARD_LANE_ORDER_INVALID")
        card_refs = [card.card_ref for card in cards]
        subject_refs = [card.subject_ref for card in cards if not card.archived]
        if len(card_refs) != len(set(card_refs)):
            raise ValueError("ECO_BOARD_DUPLICATE_CARD_REF")
        if len(subject_refs) != len(set(subject_refs)):
            raise ValueError("ECO_BOARD_DUPLICATE_ACTIVE_SUBJECT")
        lane_ref_set = set(lane_refs)
        for card in cards:
            if card.lane_ref not in lane_ref_set:
                raise ValueError("ECO_BOARD_CARD_LANE_NOT_FOUND")
            if (
                not card.archived
                and next(
                    lane for lane in lanes if lane.lane_ref == card.lane_ref
                ).archived
            ):
                raise ValueError("ECO_BOARD_ACTIVE_CARD_IN_ARCHIVED_LANE")
        for lane_ref in lane_refs:
            active_cards = [
                card
                for card in cards
                if card.lane_ref == lane_ref and not card.archived
            ]
            if sorted(card.position for card in active_cards) != list(
                range(len(active_cards))
            ):
                raise ValueError("ECO_BOARD_CARD_ORDER_INVALID")
            lane = next(item for item in lanes if item.lane_ref == lane_ref)
            if lane.wip_limit is not None and len(active_cards) > lane.wip_limit:
                raise ValueError("ECO_BOARD_WIP_LIMIT_EXCEEDED")
        filter_refs = [item.filter_ref for item in filters]
        if len(filter_refs) != len(set(filter_refs)):
            raise ValueError("ECO_BOARD_DUPLICATE_FILTER_REF")
        for item in filters:
            if not set(item.lane_refs).issubset(lane_ref_set):
                raise ValueError("ECO_BOARD_FILTER_LANE_NOT_FOUND")

    @property
    def safe_summary_ref(self) -> str:
        return _stable_ref(
            "board-summary-ref",
            {
                "board_ref": self.board_ref,
                "version": self.version,
                "lane_count": len(self.lanes),
                "card_count": len(self.cards),
                "archived": self.archived,
            },
        )

    def snapshot(self) -> BoardSnapshot:
        return BoardSnapshot(
            name=self.name,
            description=self.description,
            lanes=self.lanes,
            cards=self.cards,
            saved_filters=self.saved_filters,
            template_ref=self.template_ref,
            archived=self.archived,
        )


class BoardTemplate(_BoardModel):
    schema_version: Literal["uaa-eco-003-board-template.v1"] = (
        ECO_BOARD_TEMPLATE_SCHEMA_VERSION
    )
    workspace_ref: str
    template_ref: str
    name: str = Field(..., repr=False)
    lanes: tuple[BoardLane, ...]
    saved_filters: tuple[SavedBoardFilter, ...] = ()
    version: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_template(self) -> "BoardTemplate":
        _validate_ref(self.workspace_ref, "workspace_ref")
        _validate_ref(self.template_ref, "template_ref")
        _private_text(self.name, maximum=512, code="ECO_BOARD_TEMPLATE_NAME_INVALID")
        Board._validate_layout(self.lanes, (), self.saved_filters)
        return self

    @property
    def safe_summary_ref(self) -> str:
        return _stable_ref(
            "board-template-summary-ref",
            {
                "template_ref": self.template_ref,
                "version": self.version,
                "lane_count": len(self.lanes),
            },
        )


class BoardCardProjection(_BoardModel):
    card: BoardCard
    canonical_task: CanonicalTask | None = Field(default=None, repr=False)
    canonical_owner_ref: str
    field_provenance_refs: tuple[str, ...]
    projection_state: Literal["current", "archived", "missing"] = "current"


class BoardReadModel(_BoardModel):
    board: Board
    cards: tuple[BoardCardProjection, ...]
    result_ref: str


class BoardRepository:
    """Exact governed repository for Boards aggregates and Task projections."""

    def __init__(
        self,
        platform: EcosystemLocalDataPlatform,
        *,
        task_repository: TaskRepository | None = None,
    ) -> None:
        if task_repository is not None and task_repository.platform is not platform:
            raise ValueError("ECO_BOARD_TASK_REPOSITORY_PLATFORM_MISMATCH")
        self.platform = platform
        self.task_repository = task_repository

    @staticmethod
    def mutation_resource_refs(
        *,
        workspace_ref: str,
        idempotency_ref: str,
        operation_ref: str,
        record_ref: str,
    ) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys((workspace_ref, idempotency_ref, operation_ref, record_ref))
        )

    def create_board(
        self,
        *,
        board: Board,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        if board.version != 1 or board.undo_stack:
            raise BoardConflict("ECO_BOARD_CREATE_VERSION_INVALID")
        context = self._request_context_ref(
            "create_board",
            {"board": board.model_dump(mode="json"), "operation_ref": operation_ref},
        )
        replay = self._replay(
            workspace_ref=board.workspace_ref,
            record_ref=board.board_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )
        if replay is not None:
            return replay
        self._ensure_missing(board.workspace_ref, board.board_ref)
        self._validate_task_refs(board)
        return self._apply(
            workspace_ref=board.workspace_ref,
            record=board,
            record_ref=board.board_ref,
            record_kind_ref=ECO_BOARD_RECORD_KIND_REF,
            safe_summary_ref=board.safe_summary_ref,
            search_terms=(_ALL_BOARDS_SEARCH_TERM,),
            expected_version=0,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )

    def read(self, *, workspace_ref: str, board_ref: str) -> Board:
        record = self.platform.read(workspace_ref=workspace_ref, record_ref=board_ref)
        try:
            board = Board.model_validate(record.private_payload)
        except Exception as exc:
            raise BoardError("ECO_BOARD_PRIVATE_PAYLOAD_INVALID") from exc
        if (
            record.module_ref != ECO_BOARD_MODULE_REF
            or record.record_kind_ref != ECO_BOARD_RECORD_KIND_REF
            or board.workspace_ref != workspace_ref
            or board.board_ref != board_ref
            or board.version != record.version
            or board.safe_summary_ref != record.safe_summary_ref
        ):
            raise BoardError("ECO_BOARD_RECORD_BINDING_INVALID")
        return board

    def list_boards(
        self, *, workspace_ref: str, include_archived: bool = False
    ) -> tuple[Board, ...]:
        boards = tuple(
            self.read(workspace_ref=workspace_ref, board_ref=ref)
            for ref in self.platform.search(
                workspace_ref=workspace_ref, term=_ALL_BOARDS_SEARCH_TERM
            )
        )
        return tuple(
            sorted(
                (item for item in boards if include_archived or not item.archived),
                key=lambda item: item.board_ref,
            )
        )

    def read_model(
        self,
        *,
        workspace_ref: str,
        board_ref: str,
        filter_ref: str | None = None,
    ) -> BoardReadModel:
        board = self.read(workspace_ref=workspace_ref, board_ref=board_ref)
        saved_filter = None
        if filter_ref is not None:
            saved_filter = next(
                (item for item in board.saved_filters if item.filter_ref == filter_ref),
                None,
            )
            if saved_filter is None:
                raise BoardConflict("ECO_BOARD_FILTER_NOT_FOUND")
        cards = tuple(
            card for card in board.cards if self._matches_filter(card, saved_filter)
        )
        projections = tuple(self._project_card(board, card) for card in cards)
        return BoardReadModel(
            board=board,
            cards=projections,
            result_ref=_stable_ref(
                "board-read-result-ref",
                {
                    "board_ref": board.board_ref,
                    "board_version": board.version,
                    "filter_ref": filter_ref,
                    "task_versions": [
                        (
                            item.card.subject_ref,
                            item.canonical_task.version
                            if item.canonical_task is not None
                            else None,
                        )
                        for item in projections
                    ],
                },
            ),
        )

    def _mutate(
        self,
        *,
        workspace_ref: str,
        board_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        mutation_kind: str,
        mutation_material: dict[str, Any],
        transform: Callable[[Board], BoardSnapshot],
    ) -> UnitOfWorkReceipt:
        context = self._request_context_ref(
            mutation_kind,
            {
                "workspace_ref": workspace_ref,
                "board_ref": board_ref,
                "expected_version": expected_version,
                "operation_ref": operation_ref,
                "mutation": mutation_material,
            },
        )
        replay = self._replay(
            workspace_ref=workspace_ref,
            record_ref=board_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )
        if replay is not None:
            return replay
        current = self.read(workspace_ref=workspace_ref, board_ref=board_ref)
        if current.version != expected_version:
            raise BoardConflict("ECO_BOARD_STALE_VERSION")
        snapshot = transform(current)
        updated = Board(
            workspace_ref=current.workspace_ref,
            board_ref=current.board_ref,
            version=current.version + 1,
            undo_stack=(current.undo_stack + (current.snapshot(),))[-_MAX_UNDO_DEPTH:],
            **snapshot.model_dump(mode="json"),
        )
        self._validate_new_task_refs(current=current, updated=updated)
        return self._apply(
            workspace_ref=workspace_ref,
            record=updated,
            record_ref=board_ref,
            record_kind_ref=ECO_BOARD_RECORD_KIND_REF,
            safe_summary_ref=updated.safe_summary_ref,
            search_terms=(_ALL_BOARDS_SEARCH_TERM,),
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )

    def save(
        self,
        *,
        board: Board,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        if board.version != expected_version + 1:
            raise BoardConflict("ECO_BOARD_NEXT_VERSION_INVALID")
        desired = BoardSnapshot(
            name=board.name,
            description=board.description,
            lanes=board.lanes,
            cards=board.cards,
            saved_filters=board.saved_filters,
            template_ref=board.template_ref,
            archived=board.archived,
        )
        return self._mutate(
            workspace_ref=board.workspace_ref,
            board_ref=board.board_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="save",
            mutation_material={"desired": desired.model_dump(mode="json")},
            transform=lambda _current: desired,
        )

    def add_lane(
        self,
        *,
        workspace_ref: str,
        board_ref: str,
        lane_ref: str,
        name: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        wip_limit: int | None = None,
    ) -> UnitOfWorkReceipt:
        lane = BoardLane(
            lane_ref=lane_ref,
            name=name,
            position=0,
            wip_limit=wip_limit,
        )

        def transform(board: Board) -> BoardSnapshot:
            if lane_ref in {item.lane_ref for item in board.lanes}:
                raise BoardConflict("ECO_BOARD_LANE_ALREADY_EXISTS")
            active = [item for item in board.lanes if not item.archived]
            archived = [item for item in board.lanes if item.archived]
            added = lane.model_copy(update={"position": len(active)})
            return self._snapshot(board, lanes=tuple(active + [added] + archived))

        return self._mutate(
            workspace_ref=workspace_ref,
            board_ref=board_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="add_lane",
            mutation_material={"lane": lane.model_dump(mode="json")},
            transform=transform,
        )

    def add_board_item(
        self,
        *,
        workspace_ref: str,
        board_ref: str,
        card_ref: str,
        board_item_ref: str,
        lane_ref: str,
        title: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        description: str | None = None,
        label_refs: tuple[str, ...] = (),
    ) -> UnitOfWorkReceipt:
        card = BoardCard(
            card_ref=card_ref,
            subject_kind=BoardSubjectKind.board_item,
            subject_ref=board_item_ref,
            lane_ref=lane_ref,
            position=0,
            title=title,
            description=description,
            label_refs=label_refs,
        )
        return self._add_card(
            workspace_ref=workspace_ref,
            board_ref=board_ref,
            card=card,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
        )

    def add_task_projection(
        self,
        *,
        workspace_ref: str,
        board_ref: str,
        card_ref: str,
        task_ref: str,
        lane_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        label_refs: tuple[str, ...] = (),
    ) -> UnitOfWorkReceipt:
        card = BoardCard(
            card_ref=card_ref,
            subject_kind=BoardSubjectKind.task,
            subject_ref=task_ref,
            lane_ref=lane_ref,
            position=0,
            label_refs=label_refs,
        )
        return self._add_card(
            workspace_ref=workspace_ref,
            board_ref=board_ref,
            card=card,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
        )

    def _add_card(
        self,
        *,
        workspace_ref: str,
        board_ref: str,
        card: BoardCard,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        def transform(board: Board) -> BoardSnapshot:
            if card.card_ref in {item.card_ref for item in board.cards}:
                raise BoardConflict("ECO_BOARD_CARD_ALREADY_EXISTS")
            if card.subject_ref in {
                item.subject_ref for item in board.cards if not item.archived
            }:
                raise BoardConflict("ECO_BOARD_SUBJECT_ALREADY_PLACED")
            if card.lane_ref not in {
                lane.lane_ref for lane in board.lanes if not lane.archived
            }:
                raise BoardConflict("ECO_BOARD_TARGET_LANE_NOT_FOUND")
            position = len(
                [
                    item
                    for item in board.cards
                    if item.lane_ref == card.lane_ref and not item.archived
                ]
            )
            return self._snapshot(
                board,
                cards=board.cards + (card.model_copy(update={"position": position}),),
            )

        return self._mutate(
            workspace_ref=workspace_ref,
            board_ref=board_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="add_card",
            mutation_material={"card": card.model_dump(mode="json")},
            transform=transform,
        )

    def save_filter(
        self,
        *,
        workspace_ref: str,
        board_ref: str,
        saved_filter: SavedBoardFilter,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        def transform(board: Board) -> BoardSnapshot:
            filters = [
                item
                for item in board.saved_filters
                if item.filter_ref != saved_filter.filter_ref
            ]
            filters.append(saved_filter)
            return self._snapshot(board, saved_filters=tuple(filters))

        return self._mutate(
            workspace_ref=workspace_ref,
            board_ref=board_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="save_filter",
            mutation_material={"filter": saved_filter.model_dump(mode="json")},
            transform=transform,
        )

    def move_card(
        self,
        *,
        workspace_ref: str,
        board_ref: str,
        card_ref: str,
        lane_ref: str,
        position: int,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        _validate_ref(card_ref, "card_ref")
        _validate_ref(lane_ref, "lane_ref")

        def transform(board: Board) -> BoardSnapshot:
            if lane_ref not in {
                lane.lane_ref for lane in board.lanes if not lane.archived
            }:
                raise BoardConflict("ECO_BOARD_TARGET_LANE_NOT_FOUND")
            target = next(
                (card for card in board.cards if card.card_ref == card_ref), None
            )
            if target is None or target.archived:
                raise BoardConflict("ECO_BOARD_CARD_NOT_FOUND")
            remaining = [card for card in board.cards if card.card_ref != card_ref]
            target_lane = [
                card
                for card in remaining
                if card.lane_ref == lane_ref and not card.archived
            ]
            if position < 0 or position > len(target_lane):
                raise BoardConflict("ECO_BOARD_TARGET_POSITION_INVALID")
            target_lane.insert(
                position,
                target.model_copy(update={"lane_ref": lane_ref, "position": position}),
            )
            active_by_lane: dict[str, list[BoardCard]] = {}
            for card in remaining:
                if not card.archived and card.lane_ref != lane_ref:
                    active_by_lane.setdefault(card.lane_ref, []).append(card)
            normalized: list[BoardCard] = [card for card in remaining if card.archived]
            for current_lane in board.lanes:
                lane_cards = (
                    target_lane
                    if current_lane.lane_ref == lane_ref
                    else sorted(
                        active_by_lane.get(current_lane.lane_ref, []),
                        key=lambda item: item.position,
                    )
                )
                normalized.extend(
                    card.model_copy(update={"position": index})
                    for index, card in enumerate(lane_cards)
                )
            return self._snapshot(board, cards=tuple(normalized))

        return self._mutate(
            workspace_ref=workspace_ref,
            board_ref=board_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="move_card",
            mutation_material={
                "card_ref": card_ref,
                "lane_ref": lane_ref,
                "position": position,
            },
            transform=transform,
        )

    def undo(
        self,
        *,
        workspace_ref: str,
        board_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        context = self._request_context_ref(
            "undo",
            {
                "workspace_ref": workspace_ref,
                "board_ref": board_ref,
                "expected_version": expected_version,
                "operation_ref": operation_ref,
            },
        )
        replay = self._replay(
            workspace_ref=workspace_ref,
            record_ref=board_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )
        if replay is not None:
            return replay
        current = self.read(workspace_ref=workspace_ref, board_ref=board_ref)
        if current.version != expected_version:
            raise BoardConflict("ECO_BOARD_STALE_VERSION")
        if not current.undo_stack:
            raise BoardConflict("ECO_BOARD_UNDO_EMPTY")
        prior = current.undo_stack[-1]
        updated = Board(
            workspace_ref=workspace_ref,
            board_ref=board_ref,
            version=current.version + 1,
            undo_stack=current.undo_stack[:-1],
            **prior.model_dump(mode="json"),
        )
        self._validate_new_task_refs(current=current, updated=updated)
        return self._apply(
            workspace_ref=workspace_ref,
            record=updated,
            record_ref=board_ref,
            record_kind_ref=ECO_BOARD_RECORD_KIND_REF,
            safe_summary_ref=updated.safe_summary_ref,
            search_terms=(_ALL_BOARDS_SEARCH_TERM,),
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )

    def create_template(
        self,
        *,
        template: BoardTemplate,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        if template.version != 1:
            raise BoardConflict("ECO_BOARD_TEMPLATE_CREATE_VERSION_INVALID")
        context = self._request_context_ref(
            "create_template",
            {
                "template": template.model_dump(mode="json"),
                "operation_ref": operation_ref,
            },
        )
        replay = self._replay(
            workspace_ref=template.workspace_ref,
            record_ref=template.template_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )
        if replay is not None:
            return replay
        self._ensure_missing(template.workspace_ref, template.template_ref)
        return self._apply(
            workspace_ref=template.workspace_ref,
            record=template,
            record_ref=template.template_ref,
            record_kind_ref=ECO_BOARD_TEMPLATE_RECORD_KIND_REF,
            safe_summary_ref=template.safe_summary_ref,
            search_terms=(_ALL_TEMPLATES_SEARCH_TERM,),
            expected_version=0,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )

    def read_template(self, *, workspace_ref: str, template_ref: str) -> BoardTemplate:
        record = self.platform.read(
            workspace_ref=workspace_ref, record_ref=template_ref
        )
        try:
            template = BoardTemplate.model_validate(record.private_payload)
        except Exception as exc:
            raise BoardError("ECO_BOARD_TEMPLATE_PRIVATE_PAYLOAD_INVALID") from exc
        if (
            record.module_ref != ECO_BOARD_MODULE_REF
            or record.record_kind_ref != ECO_BOARD_TEMPLATE_RECORD_KIND_REF
            or template.workspace_ref != workspace_ref
            or template.template_ref != template_ref
            or template.version != record.version
            or template.safe_summary_ref != record.safe_summary_ref
        ):
            raise BoardError("ECO_BOARD_TEMPLATE_RECORD_BINDING_INVALID")
        return template

    def instantiate_template(
        self,
        *,
        workspace_ref: str,
        template_ref: str,
        board_ref: str,
        name: str,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        template = self.read_template(
            workspace_ref=workspace_ref, template_ref=template_ref
        )
        board = Board(
            workspace_ref=workspace_ref,
            board_ref=board_ref,
            name=name,
            lanes=template.lanes,
            saved_filters=template.saved_filters,
            template_ref=template_ref,
        )
        return self.create_board(
            board=board,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
        )

    @staticmethod
    def _snapshot(board: Board, **updates: Any) -> BoardSnapshot:
        material = board.snapshot().model_dump(mode="json")
        material.update(updates)
        return BoardSnapshot.model_validate(material)

    @staticmethod
    def _matches_filter(card: BoardCard, saved_filter: SavedBoardFilter | None) -> bool:
        if saved_filter is None:
            return not card.archived
        if card.archived and not saved_filter.include_archived:
            return False
        if saved_filter.lane_refs and card.lane_ref not in saved_filter.lane_refs:
            return False
        if saved_filter.label_refs and not set(saved_filter.label_refs).issubset(
            card.label_refs
        ):
            return False
        if (
            saved_filter.subject_kinds
            and card.subject_kind not in saved_filter.subject_kinds
        ):
            return False
        return True

    def _project_card(self, board: Board, card: BoardCard) -> BoardCardProjection:
        if card.subject_kind == BoardSubjectKind.board_item:
            return BoardCardProjection(
                card=card,
                canonical_owner_ref="canonical-owner-ref:boards",
                field_provenance_refs=(board.board_ref, card.subject_ref),
            )
        if self.task_repository is None:
            raise BoardError("ECO_BOARD_TASK_REPOSITORY_REQUIRED")
        try:
            task = self.task_repository.read(
                workspace_ref=board.workspace_ref, task_ref=card.subject_ref
            )
        except EcosystemLocalDataError as exc:
            if str(exc) != "ECO_RECORD_NOT_FOUND":
                raise
            return BoardCardProjection(
                card=card,
                canonical_owner_ref="canonical-owner-ref:tasks",
                field_provenance_refs=(card.subject_ref,),
                projection_state="missing",
            )
        return BoardCardProjection(
            card=card,
            canonical_task=task,
            canonical_owner_ref="canonical-owner-ref:tasks",
            field_provenance_refs=(task.task_ref, task.safe_summary_ref),
            projection_state="archived" if task.archived else "current",
        )

    def _validate_task_refs(self, board: Board) -> None:
        task_cards = [
            card
            for card in board.cards
            if card.subject_kind == BoardSubjectKind.task and not card.archived
        ]
        if not task_cards:
            return
        if self.task_repository is None:
            raise BoardConflict("ECO_BOARD_TASK_REPOSITORY_REQUIRED")
        for card in task_cards:
            task = self.task_repository.read(
                workspace_ref=board.workspace_ref, task_ref=card.subject_ref
            )
            if task.archived:
                raise BoardConflict("ECO_BOARD_ACTIVE_TASK_PROJECTION_ARCHIVED")

    def _validate_new_task_refs(self, *, current: Board, updated: Board) -> None:
        current_refs = {
            card.subject_ref
            for card in current.cards
            if card.subject_kind == BoardSubjectKind.task and not card.archived
        }
        new_cards = tuple(
            card
            for card in updated.cards
            if card.subject_kind == BoardSubjectKind.task
            and not card.archived
            and card.subject_ref not in current_refs
        )
        if not new_cards:
            return
        candidate = updated.model_copy(update={"cards": new_cards})
        self._validate_task_refs(candidate)

    def _ensure_missing(self, workspace_ref: str, record_ref: str) -> None:
        try:
            self.platform.read(workspace_ref=workspace_ref, record_ref=record_ref)
        except EcosystemLocalDataError as exc:
            if str(exc) == "ECO_RECORD_NOT_FOUND":
                return
            raise
        raise BoardConflict("ECO_BOARD_RECORD_ALREADY_EXISTS")

    def _apply(
        self,
        *,
        workspace_ref: str,
        record: _BoardModel,
        record_ref: str,
        record_kind_ref: str,
        safe_summary_ref: str,
        search_terms: tuple[str, ...],
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        request_context_ref: str,
    ) -> UnitOfWorkReceipt:
        return self.platform._apply_registered_domain(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            operations=(
                PutRecord(
                    operation_ref=operation_ref,
                    module_ref=ECO_BOARD_MODULE_REF,
                    record_ref=record_ref,
                    record_kind_ref=record_kind_ref,
                    safe_summary_ref=safe_summary_ref,
                    private_payload=record.model_dump(mode="json"),
                    search_terms=search_terms,
                    expected_version=expected_version,
                    retention_ref=ECO_BOARD_RETENTION_REF,
                ),
            ),
            approval=approval,
            requested_action=ECO_BOARD_MUTATION_ACTION,
            request_context_ref=request_context_ref,
        )

    def _replay(
        self,
        *,
        workspace_ref: str,
        record_ref: str,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        request_context_ref: str,
    ) -> UnitOfWorkReceipt | None:
        return self.platform.replay_receipt(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            resource_refs=self.mutation_resource_refs(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operation_ref=operation_ref,
                record_ref=record_ref,
            ),
            approval=approval,
            requested_action=ECO_BOARD_MUTATION_ACTION,
            request_context_ref=request_context_ref,
        )

    @staticmethod
    def _request_context_ref(kind: str, material: dict[str, Any]) -> str:
        return _stable_ref(
            "board-request-context-ref", {"kind": kind, "material": material}
        )
