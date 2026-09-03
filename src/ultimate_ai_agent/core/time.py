from datetime import datetime

from ultimate_ai_agent.core._compat import UTC


def utc_now() -> datetime:
    return datetime.now(UTC)
