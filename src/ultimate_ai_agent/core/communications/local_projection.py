from __future__ import annotations

import json
import os
from pathlib import Path
import stat

from pydantic import ValidationError

from ultimate_ai_agent.core.execution.validation import validate_execution_ref

from .contracts import (
    COMMUNICATIONS_MAX_PAGE_SIZE,
    CommunicationsFreshnessStatus,
    CommunicationsPagination,
    CommunicationsProjectionStatus,
    ReviewedCommunicationThreadDetail,
    ReviewedCommunicationsSnapshot,
    ReviewedCommunicationsThreadPage,
)


COMMUNICATIONS_PROJECTION_STATE_DIR_ENV = "UAA_COMMUNICATIONS_PROJECTION_STATE_DIR"
DEFAULT_COMMUNICATIONS_PROJECTION_STATE_DIR = Path(".uaa") / "communications_projection"
COMMUNICATIONS_PROJECTION_FILENAME = "reviewed_projection.json"
COMMUNICATIONS_PROJECTION_MAX_BYTES = 512_000


class CommunicationsProjectionNotFound(LookupError):
    pass


class CommunicationsProjectionInvalid(ValueError):
    pass


class ReviewedCommunicationsProjectionStore:
    """Read-only loader for operator-reviewed, redacted local projections."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = Path(state_dir)
        self.snapshot_path = self.state_dir / COMMUNICATIONS_PROJECTION_FILENAME

    @classmethod
    def from_env(cls) -> "ReviewedCommunicationsProjectionStore":
        configured = os.environ.get(COMMUNICATIONS_PROJECTION_STATE_DIR_ENV, "").strip()
        return cls(
            Path(configured).expanduser()
            if configured
            else DEFAULT_COMMUNICATIONS_PROJECTION_STATE_DIR
        )

    def load_snapshot(self) -> ReviewedCommunicationsSnapshot | None:
        try:
            state_stat = self.state_dir.lstat()
        except FileNotFoundError:
            return None
        if stat.S_ISLNK(state_stat.st_mode) or not stat.S_ISDIR(state_stat.st_mode):
            raise CommunicationsProjectionInvalid(
                "COMMUNICATIONS_PROJECTION_DIRECTORY_NOT_REAL"
            )
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(self.snapshot_path, flags)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise CommunicationsProjectionInvalid(
                "COMMUNICATIONS_PROJECTION_FILE_NOT_REGULAR"
            ) from exc
        try:
            file_stat = os.fstat(descriptor)
            if not stat.S_ISREG(file_stat.st_mode):
                raise CommunicationsProjectionInvalid(
                    "COMMUNICATIONS_PROJECTION_FILE_NOT_REGULAR"
                )
            if file_stat.st_size > COMMUNICATIONS_PROJECTION_MAX_BYTES:
                raise CommunicationsProjectionInvalid(
                    "COMMUNICATIONS_PROJECTION_FILE_TOO_LARGE"
                )
            with os.fdopen(descriptor, encoding="utf-8") as handle:
                descriptor = -1
                payload = json.load(handle)
            return ReviewedCommunicationsSnapshot.model_validate(payload)
        except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
            raise CommunicationsProjectionInvalid(
                "COMMUNICATIONS_PROJECTION_INVALID"
            ) from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def list_threads(
        self, *, limit: int = 25, needs_attention: bool | None = None
    ) -> ReviewedCommunicationsThreadPage:
        if limit < 1 or limit > COMMUNICATIONS_MAX_PAGE_SIZE:
            raise ValueError("COMMUNICATIONS_PAGE_LIMIT_OUT_OF_BOUNDS")
        snapshot = self.load_snapshot()
        if snapshot is None:
            return ReviewedCommunicationsThreadPage(
                status=CommunicationsProjectionStatus.blocked,
                pagination=CommunicationsPagination(
                    page_size=limit,
                    returned_count=0,
                ),
                reason_codes=["COMMUNICATIONS_REVIEWED_PROJECTION_CONTRACT_AVAILABLE"],
                blocker_codes=["COMMUNICATIONS_REVIEWED_PROJECTION_NOT_CONFIGURED"],
                safe_summary="No reviewed local communication projection is configured.",
            )
        filtered = [
            thread
            for thread in snapshot.threads
            if needs_attention is None or thread.needs_attention is needs_attention
        ]
        items = [thread.model_copy(deep=True) for thread in filtered[:limit]]
        status = (
            CommunicationsProjectionStatus.stale
            if snapshot.source.freshness == CommunicationsFreshnessStatus.stale
            else (
                CommunicationsProjectionStatus.empty
                if not items
                else CommunicationsProjectionStatus.ready
            )
        )
        return ReviewedCommunicationsThreadPage(
            status=status,
            source=snapshot.source.model_copy(deep=True),
            items=items,
            pagination=CommunicationsPagination(
                page_size=limit,
                returned_count=len(items),
                next_cursor_ref=(
                    "cursor-ref:communications:reviewed-projection:next"
                    if len(filtered) > limit
                    else None
                ),
            ),
            reason_codes=["COMMUNICATIONS_REVIEWED_PROJECTION_LOADED"],
            blocker_codes=(
                ["COMMUNICATIONS_REVIEWED_PROJECTION_STALE"]
                if status == CommunicationsProjectionStatus.stale
                else []
            ),
            safe_summary=(
                "Reviewed local communication summaries are stale and read only."
                if status == CommunicationsProjectionStatus.stale
                else "Reviewed local communication summaries are available read only."
            ),
        )

    def get_thread(self, conversation_ref: str) -> ReviewedCommunicationThreadDetail:
        try:
            validate_execution_ref(conversation_ref, "communications_conversation_ref")
        except ValueError as exc:
            raise CommunicationsProjectionNotFound(
                "COMMUNICATIONS_PROJECTION_NOT_FOUND"
            ) from exc
        snapshot = self.load_snapshot()
        if snapshot is None:
            raise CommunicationsProjectionNotFound(
                "COMMUNICATIONS_PROJECTION_NOT_FOUND"
            )
        thread = next(
            (
                item
                for item in snapshot.threads
                if item.conversation_ref == conversation_ref
            ),
            None,
        )
        if thread is None:
            raise CommunicationsProjectionNotFound(
                "COMMUNICATIONS_PROJECTION_NOT_FOUND"
            )
        item_by_ref = {item.item_ref: item for item in snapshot.items}
        items = [
            item_by_ref[item_ref].model_copy(deep=True) for item_ref in thread.item_refs
        ]
        status = (
            CommunicationsProjectionStatus.stale
            if snapshot.source.freshness == CommunicationsFreshnessStatus.stale
            else CommunicationsProjectionStatus.ready
        )
        return ReviewedCommunicationThreadDetail(
            status=status,
            source=snapshot.source.model_copy(deep=True),
            thread=thread.model_copy(deep=True),
            items=items,
            safe_summary="Reviewed local communication detail is available read only.",
        )
