"""Small standard-library compatibility helpers for supported Python releases."""

from __future__ import annotations

import datetime as _datetime


UTC = getattr(_datetime, "UTC", _datetime.timezone.utc)


class WeakrefableSlots:
    """Give slotted dataclasses a weak-reference slot on Python 3.10."""

    __slots__ = ("__weakref__",)
