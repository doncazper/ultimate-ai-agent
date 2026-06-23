from __future__ import annotations

from collections import Counter
from collections.abc import Iterable


def operation_id_failures(routes: Iterable[object]) -> list[str]:
    operation_ids = [str(getattr(route, "operation_id", "") or "") for route in routes]
    counts = Counter(operation_ids)
    failures = [
        f"duplicate operation ID: {operation_id}"
        for operation_id, count in sorted(counts.items())
        if operation_id and count > 1
    ]
    if any(not operation_id for operation_id in operation_ids):
        failures.append("missing operation ID")
    return failures


def forbidden_route_fragment_failures(
    routes: Iterable[object],
    forbidden_fragments: Iterable[str],
    *,
    exact_path_exemptions: Iterable[str] = (),
) -> list[str]:
    fragments = tuple(forbidden_fragments)
    exemptions = set(exact_path_exemptions)
    failures: list[str] = []
    for route in routes:
        path = str(getattr(route, "path", "") or "")
        method = str(getattr(route, "method", "") or "")
        if path in exemptions:
            continue
        if any(fragment in path for fragment in fragments):
            failures.append(f"forbidden route: {method} {path}")
    return failures


def unsafe_side_effect_class_failures(
    routes: Iterable[object],
    *,
    forbidden_classes: Iterable[str] = ("production_runtime",),
) -> list[str]:
    forbidden = set(forbidden_classes)
    failures: list[str] = []
    for route in routes:
        side_effect_class = str(getattr(route, "side_effect_class", "") or "")
        if side_effect_class in forbidden:
            path = str(getattr(route, "path", "") or "")
            method = str(getattr(route, "method", "") or "")
            failures.append(f"unsafe side-effect class: {method} {path} -> {side_effect_class}")
    return failures
