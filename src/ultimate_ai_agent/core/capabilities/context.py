from __future__ import annotations

from typing import Protocol


class NotesStore(Protocol):
    def compact(self, notes: list[str], *, max_items: int = 20) -> list[str]:
        ...


class SimpleNotesStore:
    def compact(self, notes: list[str], *, max_items: int = 20) -> list[str]:
        return [note for note in notes if note.strip()][:max_items]
