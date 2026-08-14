from __future__ import annotations

import os
from typing import Mapping


CPU_BUDGET_ENV = "UAA_VERIFY_CPU_BUDGET"
DEFAULT_CPU_BUDGET_CAP = 8
MAX_CPU_BUDGET = 256


def resolve_cpu_budget(
    configured: int | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    cpu_count: int | None = None,
) -> int:
    values = os.environ if environ is None else environ
    available = max(1, cpu_count if cpu_count is not None else (os.cpu_count() or 1))
    raw = configured if configured is not None else values.get(CPU_BUDGET_ENV)
    if raw is None or str(raw).strip() == "":
        return min(available, DEFAULT_CPU_BUDGET_CAP)
    try:
        requested = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{CPU_BUDGET_ENV} must be a positive integer") from exc
    if requested <= 0 or requested > MAX_CPU_BUDGET:
        raise ValueError(
            f"{CPU_BUDGET_ENV} must be between 1 and {MAX_CPU_BUDGET}"
        )
    return min(requested, available)


def capped_worker_count(requested: int, budget: int) -> int:
    if requested <= 0:
        raise ValueError("requested workers must be greater than zero")
    if budget <= 0:
        raise ValueError("CPU budget must be greater than zero")
    return min(requested, budget)
