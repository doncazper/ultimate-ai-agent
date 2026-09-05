from __future__ import annotations

import datetime
import importlib
import weakref

from ultimate_ai_agent.core import _compat
from ultimate_ai_agent.core._compat import UTC, WeakrefableSlots


def test_utc_falls_back_when_datetime_utc_is_unavailable(monkeypatch) -> None:
    monkeypatch.delattr(datetime, "UTC", raising=False)
    module = importlib.reload(_compat)

    assert module.UTC is datetime.timezone.utc


def test_supported_utc_identity_is_timezone_utc() -> None:
    assert UTC is datetime.timezone.utc


def test_weakrefable_slots_supports_slotted_subclasses() -> None:
    class SlottedValue(WeakrefableSlots):
        __slots__ = ("value",)

        def __init__(self) -> None:
            self.value = 1

    value = SlottedValue()

    assert weakref.ref(value)() is value
