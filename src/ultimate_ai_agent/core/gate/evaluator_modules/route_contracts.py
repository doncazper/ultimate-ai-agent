from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Callable

from ultimate_ai_agent.core.gate.evaluator_modules import route_boundaries


ROUTE_CONTRACT_PATTERN = re.compile(r"^m(?P<milestone>\d+)_openapi_route_failures$")


@dataclass(frozen=True)
class RouteContractEvaluatorRef:
    milestone: int
    name: str
    module: str
    status: str


def route_contract_registry() -> tuple[RouteContractEvaluatorRef, ...]:
    entries: list[RouteContractEvaluatorRef] = []
    for name in dir(route_boundaries):
        match = ROUTE_CONTRACT_PATTERN.match(name)
        if match is None:
            continue
        entries.append(
            RouteContractEvaluatorRef(
                milestone=int(match.group("milestone")),
                name=name,
                module="ultimate_ai_agent.core.gate.evaluator_modules.route_boundaries",
                status="extracted_route_boundary",
            )
        )
    return tuple(sorted(entries, key=lambda entry: entry.milestone))


def evaluate_route_contract(milestone: int, paths: Iterable[str]) -> list[str]:
    function_name = f"m{milestone}_openapi_route_failures"
    evaluator = getattr(route_boundaries, function_name, None)
    if not callable(evaluator):
        raise KeyError(f"unknown route contract milestone: {milestone}")
    typed_evaluator: Callable[[Iterable[str]], list[str]] = evaluator
    return typed_evaluator(paths)
